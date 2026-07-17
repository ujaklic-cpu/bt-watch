# Manual system test

This procedure tests two Android probes against one Linux aggregator. It requires two Android devices, one BLE advertiser, Python 3.12, Java 17, and Android build tools.

## Start the aggregator

From the repository root:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
HOST_COORDS_JSON='{"android-device1":[0,0],"android-device2":[10,0]}' \
USER_X=5 USER_Y=0 \
.venv/bin/python map_server.py
```

Check the initial state from another terminal:

```bash
curl -fsS http://localhost:8000/snapshot
```

The response should contain both configured hosts, an empty `devices` array, and the user coordinate `[5, 0]`.

## Build and install the Android app

```bash
cd android-app
./gradlew :app:assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Install the same APK on both devices. Grant nearby-device, Bluetooth, location, and notification permissions when requested.

Configure the first device with:

```text
Hub URL: http://<server-address>:8000
HOST_ID: android-device1
HOST_LOCATION: probe 1
```

Configure the second device with `HOST_ID=android-device2`. Both IDs must match `HOST_COORDS_JSON`. Leave the target MAC field empty to observe all advertisers, or set the same comma-separated allowlist on both devices.

## Verify data flow

Start scanning on both devices and inspect their in-app logs. Each should report sightings and successful sends. Then check the aggregator:

```bash
curl -fsS http://<server-address>:8000/snapshot
curl -N http://<server-address>:8000/events
```

The snapshot should contain sightings from both host IDs. A device estimate is present when at least one reporting host has configured coordinates. Open `http://<server-address>:8000/` and confirm that host and device labels update without a page reload.

Move the BLE advertiser between the probes. The weighted-centroid estimate should move toward the probe reporting the stronger RSSI. This is a relative display, not a calibrated distance measurement.

## Local automated checks

```bash
.venv/bin/python -m pip install ruff pytest
.venv/bin/ruff check .
.venv/bin/python -m compileall -q bt_watch.py map_server.py tests
.venv/bin/python -m pytest -q
.venv/bin/python tests/stress_test.py
cd android-app
./gradlew :app:lintDebug :app:testDebugUnitTest
```

The Python stress script exercises one through ten configured hosts with three device addresses per scenario.

## Troubleshooting

- No Android sightings: confirm runtime permissions, Bluetooth state, and the ScanService notification.
- Send failures: confirm the hub URL has no `/ingest` suffix, both devices can reach port 8000, and the server firewall permits the connection.
- Missing position: confirm each `HOST_ID` exactly matches a key in `HOST_COORDS_JSON`.
- Empty Linux scan: confirm BlueZ is running and the process has `CAP_NET_RAW` and `CAP_NET_ADMIN` or equivalent access.
- Cleartext HTTP blocked: use HTTP only on a trusted test network; use HTTPS outside that network.
