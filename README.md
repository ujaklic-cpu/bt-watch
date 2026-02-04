# bt-watch

Always-on Bluetooth LE watcher for Linux. It scans continuously via Bleak/BlueZ and serves a live feed plus browser notifications on `http://localhost:5000`. Filter by MACs with `TARGET_MACS` or watch everything. Multi-host ready: tag each probe with `HOST_ID`/`HOST_LOCATION` to correlate RSSI across locations.

![CI](https://github.com/ujaklic-cpu/bt-watch/actions/workflows/ci.yml/badge.svg)

## Features
- Continuous BLE discovery (passive) with RSSI.
- Server-Sent Events feed at `/events` for integrations.
- Minimal web UI with native browser notifications.
- Docker image that reuses the host `bluetoothd`.
- Multi-host metadata (`host`, `location`) included in every event.
- Optional central map/aggregator: probes POST sightings to a hub that plots hosts and estimated device positions on a Leaflet map.

## Quick start (native)
```bash
python3 -m pip install -r requirements.txt
# optional one-time caps so you don't need sudo:
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
# run (filter to one or more MACs, comma-separated):
TARGET_MACS=40:71:E6:AD:2C:27 python3 bt_watch.py
# open http://localhost:5000
```

## Docker
Build:
```bash
docker build -t bt-watch .
```
Run (host BlueZ):
```bash
docker run --rm -it \
  --net=host \
  --privileged \  # or: --cap-add NET_ADMIN --cap-add NET_RAW --device /dev/bus/usb \
  -v /var/run/dbus:/var/run/dbus \
  -e HOST_ID=kitchen-pi \
  -e HOST_LOCATION="Kitchen north" \
  -e AGGREGATOR_URL=http://hub:8000/ingest \
  -e TARGET_MACS=40:71:E6:AD:2C:27 \
  bt-watch
# visit http://localhost:5000 on the host
```
Notes:
- `--net=host` and the DBus mount let the container talk to the host's `bluetoothd`.
- If `--privileged` is too broad, use the capability + device flags shown.
- Keep the adapter up and Bluetooth enabled on the host; the container reuses the host daemon.
- Set `HOST_ID`/`HOST_LOCATION` differently on each probe to narrow down location by comparing RSSI.
- Set `AGGREGATOR_URL` to push sightings to a central hub (see below).

## Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m compileall .
```
- Lint locally (matches CI): `python -m pip install ruff && ruff check .`
- Docker rebuild after changes: `docker build -t bt-watch .`

## Central map / aggregator (optional)
Run the hub on a machine reachable by all probes:
```bash
HOST_COORDS_JSON='{"kitchen-pi":[46.051,14.506],"garage":[46.052,14.504]}' \
USER_LAT=46.0515 USER_LON=14.5055 \
python3 map_server.py
# or docker: docker run --rm -it -p 8000:8000 -e HOST_COORDS_JSON='{"kitchen-pi":[...], ...}' bt-watch python map_server.py
```
Configure each probe with `AGGREGATOR_URL=http://<hub>:8000/ingest`.
- Map at `http://<hub>:8000/` shows host positions and estimated device positions (weighted centroid of RSSI from hosts with coordinates).
- `/events` streams live updates; `/snapshot` returns current state.

## Contributing
See `CONTRIBUTING.md`. Please follow the Code of Conduct in `CODE_OF_CONDUCT.md`.

## License
MIT — see `LICENSE`.
