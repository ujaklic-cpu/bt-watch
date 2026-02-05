# Deployment Guide

This document covers end-to-end deployment of BtWatch components: hub (map_server), probes (Linux/Android/ESP32), secure access via Twingate, and CI/testing.

## Components
- **Hub:** `map_server.py` (Python/Flask). Listens on `0.0.0.0:8000`, aggregates BLE sightings, estimates positions in an internal X/Y grid, serves SSE at `/events` and a canvas map at `/`.
- **Linux probe:** `bt_watch.py` — scans BLE via BlueZ/Bleak; posts to hub `/ingest`; registers its coordinates via `/host_coord`.
- **Android probe:** `android-app/` — Compose app + foreground service scanning BLE, posting to `/ingest`; configurable hub URL, host metadata, target filter.
- **ESP32 probe:** `firmware/esp32/bt_watch_esp32.ino` — Arduino sketch scanning BLE and posting sightings to hub; registers host coordinates.
- **Secure access:** `twingate/` — Docker Compose to run a Twingate connector so probes can reach the hub without exposing ports.

## Hub setup (Python)
Prereqs: Python 3.10+, pip, BlueZ libs on Linux.
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
HOST_COORDS_JSON='{"host1":[0,0],"host2":[5,2]}' USER_X=1 USER_Y=1 python3 map_server.py
# or docker: docker run --rm -p 8000:8000 -e HOST_COORDS_JSON='{"host1":[0,0]}' bt-watch python map_server.py
```
Expose/advertise the hub address the probes will use (e.g., `http://hub:8000`).

### Hub on Windows
- Install Python 3.12 from python.org, check “Add to PATH”.
- Open PowerShell:
  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  python -m pip install -r requirements.txt
  set HOST_COORDS_JSON={"host1":[0,0],"host2":[5,2]}
  set USER_X=1
  set USER_Y=1
  python map_server.py
  ```
- If you use Docker Desktop on Windows: `docker run --rm -p 8000:8000 -e HOST_COORDS_JSON='{"host1":[0,0]}' bt-watch python map_server.py`

### Hub on ChromeOS (Crostini/Linux VM)
- Enable Linux (Crostini), update packages: `sudo apt-get update && sudo apt-get install -y python3-venv python3-pip`
- Inside the Linux container:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  HOST_COORDS_JSON='{"crostini-host":[0,0]}' USER_X=0 USER_Y=0 python3 map_server.py
  ```
- To reach from Android side of the Chromebook, use `http://penguin.linux.test:8000` (Crostini hostname) or `http://100.115.92.2:8000` (virtio-vsock bridge). Keep the container running and avoid sleeping the Chromebook.

## Linux probe
Env vars:
- `HOST_ID` (default hostname)
- `HOST_LOCATION` (label)
- `HOST_X`, `HOST_Y` (floats, internal grid coords)
- `TARGET_MACS` (comma-separated, optional)
- `AGGREGATOR_URL` (e.g., `http://hub:8000/ingest`)
Run:
```bash
AGGREGATOR_URL=http://hub:8000/ingest HOST_ID=host1 HOST_X=0 HOST_Y=0 \
python3 bt_watch.py
```

### Windows probe
- Same venv steps as hub; then:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  set AGGREGATOR_URL=http://hub:8000/ingest
  set HOST_ID=win-probe
  set HOST_X=2
  set HOST_Y=1
  python bt_watch.py
  ```

### ChromeOS probe (Linux container)
- In Crostini, install Bluetooth tools: `sudo apt-get install -y bluetooth bluez dbus`
- Ensure the container has access to the Bluetooth adapter (requires ChromeOS flag and `--enable-bt-forwarding` on some devices; if blocked by policy, probes can’t scan).
- Run same steps as Linux probe inside the container. If Bluetooth passthrough isn’t available, use an external USB BLE dongle passed to Crostini.

## Android probe (Chromebook-friendly)
Path: `android-app/`
- Build: `./gradlew :app:assembleDebug`
- Install debug APK or sideload via ADB; for Play release, bump versionCode/versionName and supply keystore or Play App Signing.
- In-app settings: Hub URL, HOST_ID, HOST_LOCATION, target MACs, auto-start toggle. Start/Stop scanning; view log.
- Foreground service posts sightings to `/ingest` and shows a persistent notification.
- Cleartext allowed for local hubs; prefer HTTPS when available.

## ESP32 probe
Path: `firmware/esp32/bt_watch_esp32.ino`
Config in sketch header:
- WiFi SSID/PASS
- `AGGREGATOR_URL`
- `HOST_ID`, `HOST_LOCATION`, `HOST_X`, `HOST_Y`
- Optional `TARGET_MACS`
Flash with Arduino IDE (ESP32 core). The probe self-registers coordinates to `/host_coord` and streams sightings to `/ingest`.

## Internal positioning
- Hosts report coordinates via `/host_coord` (x,y). Hub also accepts seed map with `HOST_COORDS_JSON`.
- Device position = weighted centroid of host coords with RSSI-derived weights.
- Snapshot format: hosts [{id,x,y}], devices [{estimate:{x,y}, hosts:[…]}], user {x,y}.
- UI at `/` renders a canvas with hosts (blue) and devices (red) using the internal grid; no GPS needed.

## Secure access (no open ports) with Twingate
Path: `twingate/`
Steps:
1) In Twingate Admin, create a Remote Network and Connector; copy network name, access token, refresh token.
2) `cp twingate/.env.example twingate/.env` and fill values.
3) `docker compose -f twingate/docker-compose.twingate.yml up -d`
4) Point probes to the internal DNS/IP provided by Twingate (e.g., `http://hub.internal:8000`).

## CI / tests
- GitHub Actions workflow `CI` runs:
  - Lint: `ruff check .`
  - Syntax check: `python -m compileall .`
  - Stress test: `python tests/stress_test.py` (1–10 host scenarios, x/y grid)
- If you change positioning fields, update `tests/stress_test.py` accordingly.

## Operational tips
- Keep BLE devices awake during scanning to avoid missing adverts.
- Spread hosts with known x/y to improve trilateration quality.
- Use HTTPS for hub if exposed beyond local network.
- Monitor hub `/health` (from bt_watch) and `/snapshot` for status; Android app has a log screen for quick probe diagnostics.
