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
import math
import os
import time
from collections import defaultdict
from typing import Dict, List, Tuple

from flask import Flask, Response, jsonify, request

app = Flask(__name__)

HOST_COORDS = {}
if os.getenv("HOST_COORDS_JSON"):
    try:
        HOST_COORDS = json.loads(os.getenv("HOST_COORDS_JSON", "{}"))
    except Exception:
        HOST_COORDS = {}

USER_LAT = float(os.getenv("USER_LAT", "0") or 0)
USER_LON = float(os.getenv("USER_LON", "0") or 0)

subscribers: List = []
devices: Dict[str, Dict[str, dict]] = defaultdict(dict)  # address -> host -> event


def broadcast(evt: dict):
    for q in list(subscribers):
        try:
            q.put_nowait(evt)
        except Exception:
            pass


def weight_from_rssi(rssi: int) -> float:
    # Convert RSSI to a positive weight; stronger signals contribute more.
    # Avoid zero/negative weights.
    return 1.0 / max(1.0, abs(rssi))


def estimate_position(entries: List[dict]) -> Tuple[float, float]:
    """Weighted centroid from host coordinates and RSSI."""
    total_w = 0.0
    sum_lat = 0.0
    sum_lon = 0.0
    for e in entries:
        coords = HOST_COORDS.get(e["host"])
        if not coords:
            continue
        w = weight_from_rssi(e.get("rssi", -90) or -90)
        total_w += w
        sum_lat += coords[0] * w
        sum_lon += coords[1] * w
    if total_w == 0:
        return None, None
    return sum_lat / total_w, sum_lon / total_w


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
    devices[address][host] = data
    broadcast(data)
    return {"status": "ok"}


@app.get("/events")
def events():
    import queue

    q: "queue.Queue[dict]" = queue.Queue(maxsize=500)
    subscribers.append(q)

    def gen():
        try:
            while True:
                ev = q.get()
                yield f"data: {json.dumps(ev)}\n\n"
        except GeneratorExit:
            subscribers.remove(q)

    return Response(gen(), mimetype="text/event-stream")


@app.get("/snapshot")
def snapshot():
    out = []
    for addr, host_map in devices.items():
        entries = list(host_map.values())
        est_lat, est_lon = estimate_position(entries)
        out.append(
            {
                "address": addr,
                "name": entries[0].get("name", ""),
                "estimate": {"lat": est_lat, "lon": est_lon},
                "hosts": entries,
            }
        )
    return jsonify(
        {
            "hosts": [{"id": h, "lat": v[0], "lon": v[1]} for h, v in HOST_COORDS.items()],
            "devices": out,
            "user": {"lat": USER_LAT, "lon": USER_LON},
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
  <title>bt-watch map</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>html,body,#map{height:100%;margin:0;} .info{background:white;padding:6px;}</style>
</head>
<body>
  <div id="map"></div>
  <script>
  const map = L.map('map').setView([0,0], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
  const hostMarkers = {};
  const deviceMarkers = {};

  function weightFromRssi(rssi){ return 1/Math.max(1, Math.abs(rssi||-90)); }

  async function loadSnapshot(){
    const res = await fetch('/snapshot');
    const data = await res.json();
    if(data.hosts.length){
      const lat = data.hosts[0].lat, lon = data.hosts[0].lon;
      map.setView([lat, lon], 13);
    }
    data.hosts.forEach(h=>{
      if(!hostMarkers[h.id]){
        hostMarkers[h.id] = L.circleMarker([h.lat, h.lon], {radius:6,color:'blue'}).addTo(map).bindPopup(`Host ${h.id}`);
      }
    });
    if(data.user && data.user.lat && data.user.lon){
      L.marker([data.user.lat, data.user.lon]).addTo(map).bindPopup('You');
    }
    data.devices.forEach(d=>{
      if(d.estimate && d.estimate.lat && d.estimate.lon){
        const key = d.address;
        const label = `${d.address} ${d.name||''}`;
        if(!deviceMarkers[key]){
          deviceMarkers[key] = L.circle([d.estimate.lat, d.estimate.lon], {radius:15, color:'red'}).addTo(map).bindPopup(label);
        } else {
          deviceMarkers[key].setLatLng([d.estimate.lat, d.estimate.lon]).bindPopup(label);
        }
      }
    });
  }

  loadSnapshot();

  const es = new EventSource('/events');
  es.onmessage = (e)=>{
    const d = JSON.parse(e.data);
    // Optionally update sidebar; for now, refresh snapshot on every event.
    loadSnapshot();
  };
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
