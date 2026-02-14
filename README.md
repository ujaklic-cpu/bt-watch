# bt-watch

Always-on Bluetooth LE watcher for Linux. It scans continuously via Bleak/BlueZ and serves a live feed plus browser notifications on `http://localhost:5000`. Filter by MACs with `TARGET_MACS` or watch everything. Multi-host ready: tag each probe with `HOST_ID`/`HOST_LOCATION` to correlate RSSI across locations.

![CI](https://github.com/ujaklic-cpu/bt-watch/actions/workflows/ci.yml/badge.svg)

> **📚 Documentation:** See [API Reference](docs/API.md) for complete endpoint documentation and [DEPLOYMENT.md](docs/DEPLOYMENT.md) for deployment guides.

## Features
- Continuous BLE discovery (passive) with RSSI.
- Server-Sent Events feed at `/events` for integrations.
- Minimal web UI with native browser notifications.
- Docker image that reuses the host `bluetoothd`.
- Multi-host metadata (`host`, `location`) included in every event.
- Optional central map/aggregator: probes POST sightings to a hub that plots hosts and estimated device positions on a canvas-based grid map.

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
USER_X=46.0515 USER_Y=14.5055 \
python3 map_server.py
# or docker: docker run --rm -it -p 8000:8000 -e HOST_COORDS_JSON='{"kitchen-pi":[...], ...}' bt-watch python map_server.py
```
Configure each probe with `AGGREGATOR_URL=http://<hub>:8000/ingest`.
- Map at `http://<hub>:8000/` shows host positions and estimated device positions (weighted centroid of RSSI from hosts with coordinates).
- `/events` streams live updates; `/snapshot` returns current state.

**Coordinate System:**
- The system uses an arbitrary X/Y coordinate system (not limited to geographic coordinates)
- You can use geographic coordinates or custom grid coordinates (e.g., meters, feet, arbitrary units)
- All hosts must use the same coordinate system for position estimation to work correctly
- In the examples above, the format is `[X, Y]` where X=46.051 (latitude), Y=14.506 (longitude)

## ESP32 probe (Arduino)
- Sketch: `firmware/esp32/bt_watch_esp32.ino`
- Requirements: Arduino core for ESP32.
- Configure WiFi, `AGGREGATOR_URL`, `HOST_ID`, `HOST_LOCATION`, optional `HOST_X/HOST_Y` and target MACs in the sketch header.
- ESP32 scans BLE adverts and POSTs to `/ingest`; also registers host coordinates to `/host_coord`.

## Secure remote access (no open ports) with Twingate
- A Twingate connector recipe is provided in `twingate/` (Docker).
- Steps: create connector in Twingate admin, copy tokens, fill `twingate/.env`, run `docker compose -f twingate/docker-compose.twingate.yml up -d`.
- Then point probes at the internal DNS exposed by Twingate (e.g., `http://hub.internal:8000`); no public ports required.

## Contributing
See `CONTRIBUTING.md`. Please follow the Code of Conduct in `CODE_OF_CONDUCT.md`.

## Security Considerations

⚠️ **Important:** This application has no built-in authentication. All endpoints accept unauthenticated requests.

**For production deployments:**
- Deploy on trusted networks only (VPN, private LAN)
- Use reverse proxy with authentication (nginx + basic auth, OAuth)
- Enable HTTPS/TLS
- Consider using Twingate or similar zero-trust solution (see `twingate/`)
- See [API.md](docs/API.md#security-considerations) for detailed security recommendations

## License
MIT — see `LICENSE`.
