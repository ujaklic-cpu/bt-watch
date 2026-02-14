#!/usr/bin/env python3
"""
Central aggregator + map UI.
- Receives events from probes via POST /ingest (set AGGREGATOR_URL on probes).
- Stores latest sighting per (address, host).
- Streams updates via SSE /events.
- Serves a Leaflet map at / showing hosts and estimated device positions.

Configuration:
- HOST_COORDS_JSON: JSON mapping host_id -> [lat, lon] (required for positioning).
- USER_LAT, USER_LON: optional user marker.
"""
import json
import os
import queue
import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from flask import Flask, Response, jsonify, request

app = Flask(__name__)

# Coordinate system configuration
MAX_COORDINATE_VALUE = 1e6  # Maximum absolute value for x/y coordinates

# Internal coordinate system (unitless X,Y). Hosts can be seeded via env or updated via /host_coord.
HOST_COORDS = {}
if os.getenv("HOST_COORDS_JSON"):
    try:
        HOST_COORDS = json.loads(os.getenv("HOST_COORDS_JSON", "{}"))
    except Exception:
        HOST_COORDS = {}

USER_X = float(os.getenv("USER_X", "0") or 0)
USER_Y = float(os.getenv("USER_Y", "0") or 0)

subscribers: List["queue.Queue[dict]"] = []
devices: Dict[str, Dict[str, dict]] = defaultdict(dict)  # address -> host -> event
data_lock = threading.Lock()  # Protects subscribers and devices


def broadcast(evt: dict):
    with data_lock:
        for q in list(subscribers):
            try:
                q.put_nowait(evt)
            except Exception:
                pass


def weight_from_rssi(rssi: int) -> float:
    # Convert RSSI to a positive weight; stronger signals contribute more.
    # Avoid zero/negative weights.
    return 1.0 / max(1.0, abs(rssi))


def is_valid_coordinate(value) -> Tuple[bool, float]:
    """Validate and convert coordinate value.
    
    Returns:
        Tuple of (is_valid, float_value)
    """
    try:
        float_val = float(value)
        if -MAX_COORDINATE_VALUE <= float_val <= MAX_COORDINATE_VALUE:
            return True, float_val
        return False, 0.0
    except (ValueError, TypeError):
        return False, 0.0


def estimate_position(entries: List[dict]) -> Tuple[float, float]:
    """Weighted centroid from host coordinates and RSSI (internal x,y)."""
    total_w = 0.0
    sum_x = 0.0
    sum_y = 0.0
    for e in entries:
        coords = HOST_COORDS.get(e["host"])
        if not coords:
            continue
        w = weight_from_rssi(e.get("rssi", -90) or -90)
        total_w += w
        sum_x += coords[0] * w
        sum_y += coords[1] * w
    if total_w == 0:
        return None, None
    return sum_x / total_w, sum_y / total_w


@app.post("/ingest")
def ingest():
    data = request.get_json(force=True, silent=True) or {}
    required = {"host", "address", "rssi"}
    if not required.issubset(data):
        return {"error": "missing fields"}, 400
    host = data.get("host")
    address = data.get("address")
    now = time.time()
    data["ts"] = data.get("ts", now)
    with data_lock:
        devices[address][host] = data
    broadcast(data)
    return {"status": "ok"}


@app.get("/events")
def events():
    q: "queue.Queue[dict]" = queue.Queue(maxsize=500)
    with data_lock:
        subscribers.append(q)

    def gen():
        try:
            while True:
                ev = q.get()
                yield f"data: {json.dumps(ev)}\n\n"
        except GeneratorExit:
            with data_lock:
                subscribers.remove(q)

    return Response(gen(), mimetype="text/event-stream")


@app.get("/snapshot")
def snapshot():
    with data_lock:
        out = []
        for addr, host_map in devices.items():
            entries = list(host_map.values())
            est_x, est_y = estimate_position(entries)
            out.append(
                {
                    "address": addr,
                    "name": entries[0].get("name", ""),
                    "estimate": {"x": est_x, "y": est_y},
                    "hosts": entries,
                }
            )
    return jsonify(
        {
            "hosts": [{"id": h, "x": v[0], "y": v[1]} for h, v in HOST_COORDS.items()],
            "devices": out,
            "user": {"x": USER_X, "y": USER_Y},
            "updated": time.time(),
        }
    )


@app.get("/")
def index():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>bt-watch grid</title>
  <style>
    html,body { height:100%; margin:0; font-family:monospace;}
    #c { width:100%; height:100%; background:#0b1021;}
    #legend { position:fixed; top:10px; left:10px; background:#fff; padding:6px; }
    #panel {
      position:fixed; top:10px; right:10px; width:260px; max-height:90%;
      background:#0b1021; color:#e0e0e0; border:1px solid #444; padding:10px;
      overflow-y:auto; box-shadow:0 0 10px rgba(0,0,0,0.4);
      font-size:13px;
    }
    #panel h3 { margin:6px 0 4px; font-size:13px; color:#9ad1ff; }
    #panel ul { list-style:none; padding-left:0; margin:0 0 8px 0; }
    #panel li { margin:2px 0; }
  </style>
</head>
<body>
<canvas id="c"></canvas>
<div id="legend">Hosts (blue), Devices (red)</div>
<div id="panel">
  <h3>Hosts</h3>
  <ul id="hostList"></ul>
  <h3>Devices</h3>
  <ul id="deviceList"></ul>
</div>
<script>
const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');
function resize(){ canvas.width = window.innerWidth; canvas.height = window.innerHeight; }
window.onresize = resize; resize();

let data = {hosts:[], devices:[], user:null};

function draw(){
  ctx.clearRect(0,0,canvas.width, canvas.height);
  // auto-scale to fit all points
  const all = [];
  data.hosts.forEach(h=>all.push([h.x,h.y]));
  data.devices.forEach(d=>{ if(d.estimate&&d.estimate.x!=null) all.push([d.estimate.x,d.estimate.y]); });
  if(all.length===0) return;
  const xs = all.map(p=>p[0]), ys=all.map(p=>p[1]);
  const minx=Math.min(...xs), maxx=Math.max(...xs), miny=Math.min(...ys), maxy=Math.max(...ys);
  const pad=20;
  const scaleX = (canvas.width-2*pad)/Math.max(1, maxx-minx);
  const scaleY = (canvas.height-2*pad)/Math.max(1, maxy-miny);
  const scale = Math.min(scaleX, scaleY);
  const fx = v => pad + (v-minx)*scale;
  const fy = v => canvas.height - (pad + (v-miny)*scale);

  // hosts
  ctx.fillStyle = '#4FC3F7';
  data.hosts.forEach(h=>{
    const x=fx(h.x), y=fy(h.y);
    ctx.beginPath(); ctx.arc(x,y,6,0,Math.PI*2); ctx.fill();
    ctx.fillText(h.id, x+8, y+4);
  });
  // devices
  ctx.fillStyle = '#FF5252';
  data.devices.forEach(d=>{
    if(d.estimate && d.estimate.x!=null){
      const x=fx(d.estimate.x), y=fy(d.estimate.y);
      ctx.beginPath(); ctx.arc(x,y,8,0,Math.PI*2); ctx.fill();
      ctx.fillText(d.address, x+10, y+4);
    }
  });
}

function renderLists(){
  const hostList = document.getElementById('hostList');
  const deviceList = document.getElementById('deviceList');
  hostList.innerHTML = data.hosts.map(h => `<li><strong>${h.id}</strong> @ (${h.x}, ${h.y})</li>`).join('') || '<li>None</li>';
  deviceList.innerHTML = data.devices.map(d => {
    const est = d.estimate || {};
    return `<li><strong>${d.address}</strong> rssi~${(d.hosts?.[0]?.rssi ?? '?')} pos(${est.x ?? '?'} , ${est.y ?? '?'})</li>`;
  }).join('') || '<li>None</li>';
}

async function loadSnapshot(){
  const res = await fetch('/snapshot');
  data = await res.json();
  draw();
  renderLists();
}
loadSnapshot();
const es = new EventSource('/events');
es.onmessage = ()=>loadSnapshot();
</script>
</body>
</html>
"""


@app.post("/host_coord")
def host_coord():
    data = request.get_json(force=True, silent=True) or {}
    host = data.get("host")
    x = data.get("x")
    y = data.get("y")
    if host is None or x is None or y is None:
        return {"error": "host,x,y required"}, 400
    
    # Validate coordinates
    x_valid, x_float = is_valid_coordinate(x)
    y_valid, y_float = is_valid_coordinate(y)
    
    if not x_valid or not y_valid:
        if not x_valid and not y_valid:
            return {"error": "invalid or out-of-range coordinate values"}, 400
        elif not x_valid:
            return {"error": "invalid or out-of-range x coordinate"}, 400
        else:
            return {"error": "invalid or out-of-range y coordinate"}, 400
    
    HOST_COORDS[host] = [x_float, y_float]
    return {"status": "ok"}


# Alias for probes that append /host_coord to an AGGREGATOR_URL ending with /ingest
# (e.g., AGGREGATOR_URL=http://hub:8000/ingest). This forwards to the same handler.
@app.post("/ingest/host_coord")
def host_coord_ingest_alias():
    return host_coord()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
