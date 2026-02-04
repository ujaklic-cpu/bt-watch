#!/usr/bin/env python3
"""
BLE watcher: continuously scans for nearby Bluetooth LE devices and streams
events to a tiny localhost web UI (SSE). Optionally filters to specific MACs
via TARGET_MACS env var (comma-separated). Designed for always-on Linux boxes.

Multi-host: set HOST_ID and optional HOST_LOCATION to tag sightings so you can
deploy multiple probes and correlate RSSI by host.
"""
import asyncio
import json
import os
import queue
import requests
import socket
import threading
import time

from flask import Flask, Response, jsonify
from bleak import BleakScanner

# Comma-separated list of MACs to alert on; empty = report everything.
TARGETS = {
    mac.strip().lower()
    for mac in os.getenv("TARGET_MACS", "").split(",")
    if mac.strip()
}

HOST_ID = os.getenv("HOST_ID") or socket.gethostname()
HOST_LOCATION = os.getenv("HOST_LOCATION", "")
HOST_X = os.getenv("HOST_X")
HOST_Y = os.getenv("HOST_Y")

subscribers = []
sub_lock = threading.Lock()
app = Flask(__name__)


def broadcast(event: dict) -> None:
    """Push an event to all connected SSE clients; drop if their queue is full."""
    with sub_lock:
        for q in list(subscribers):
            try:
                q.put_nowait(event)
            except queue.Full:
                pass


# Optional upstream aggregator: POST events asynchronously to AGGREGATOR_URL.
AGGREGATOR_URL = os.getenv("AGGREGATOR_URL")
post_queue: "queue.Queue[dict]" = queue.Queue(maxsize=1000)


def post_worker():
    while True:
        evt = post_queue.get()
        if not AGGREGATOR_URL:
            continue
        try:
            requests.post(AGGREGATOR_URL, json=evt, timeout=2)
        except Exception:
            pass


if AGGREGATOR_URL:
    threading.Thread(target=post_worker, daemon=True).start()
    # Advertise host position if provided
    if HOST_X is not None and HOST_Y is not None:
        try:
            requests.post(
                f"{AGGREGATOR_URL.rstrip('/')}/host_coord",
                json={
                    "host": HOST_ID,
                    "x": float(HOST_X),
                    "y": float(HOST_Y),
                    "location": HOST_LOCATION,
                },
                timeout=2,
            )
        except Exception:
            pass


def on_advert(device, adv_data) -> None:
    """Bleak callback for each advertisement."""
    if TARGETS and device.address.lower() not in TARGETS:
        return

    event = {
        "host": HOST_ID,
        "location": HOST_LOCATION,
        "address": device.address,
        "name": device.name or adv_data.local_name or "",
        "rssi": adv_data.rssi,
        "ts": time.time(),
    }
    broadcast(event)
    if AGGREGATOR_URL:
        try:
            post_queue.put_nowait(event)
        except queue.Full:
            pass


async def scan_forever() -> None:
    """Start the scanner and keep it running; recover on errors."""
    scanner = BleakScanner(detection_callback=on_advert, scanning_mode="passive")
    while True:
        try:
            await scanner.start()
            while True:
                await asyncio.sleep(5)
        except Exception as e:  # noqa: BLE001 - broad to keep loop alive
            print("scanner error:", e)
            await asyncio.sleep(3)
        finally:
            try:
                await scanner.stop()
            except Exception:
                pass


def start_scan_thread() -> None:
    """Run the asyncio scanner in a daemon thread."""
    threading.Thread(target=lambda: asyncio.run(scan_forever()), daemon=True).start()


@app.get("/events")
def sse():
    """Server-Sent Events endpoint streaming JSON lines."""
    q: queue.Queue = queue.Queue(maxsize=200)
    with sub_lock:
        subscribers.append(q)

    def gen():
        try:
            while True:
                ev = q.get()
                yield f"data: {json.dumps(ev)}\n\n"
        except GeneratorExit:
            with sub_lock:
                subscribers.remove(q)

    return Response(gen(), mimetype="text/event-stream")


@app.get("/health")
def health():
    """Simple health probe with host metadata."""
    return jsonify(
        {
            "status": "ok",
            "host": HOST_ID,
            "location": HOST_LOCATION,
            "targets": sorted(TARGETS),
            "time": time.time(),
        }
    )


@app.get("/")
def index():
    """Minimal UI showing live sightings and firing browser notifications."""
    return """
<!doctype html>
<html><body style="font-family:monospace">
<h3>Bluetooth watcher</h3>
<div id="list"></div>
<script>
const log = document.getElementById('list');
const es  = new EventSource('/events');
es.onmessage = (e) => {
  const d = JSON.parse(e.data);
  const row = document.createElement('div');
  row.textContent = new Date(d.ts*1000).toLocaleTimeString() +
    ' | host: ' + (d.host || '?') +
    (d.location ? ' ('+d.location+')' : '') +
    ' | ' + d.address +
    ' | ' + (d.name || '') +
    ' | RSSI ' + d.rssi;
  log.prepend(row);
  if (Notification.permission === 'granted') {
    new Notification('BT seen', { body: `${d.address} ${d.name||''} RSSI ${d.rssi} @ ${d.host}` });
  }
};
if (Notification.permission === 'default') Notification.requestPermission();
</script>
</body></html>
"""


if __name__ == "__main__":
    start_scan_thread()
    app.run(host="0.0.0.0", port=5000, threaded=True)
