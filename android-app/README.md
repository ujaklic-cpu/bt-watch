# BtWatch Android Probe

Chromebook/Android app that scans BLE advertisements and posts sightings to the BtWatch hub (`/ingest`). Runs as a foreground service; settings live in the UI.

## Build & run
```bash
cd android-app
./gradlew :app:assembleDebug   # or open in Android Studio
```
Min SDK 26, target SDK 34. Accept runtime permissions for Bluetooth scan/connect and fine location.

## Configure in-app
- Hub URL: e.g., `http://<server-ip>:8000`
- HOST_ID / HOST_LOCATION: labels per probe
- Target MACs (optional, comma-separated). Empty = send all.
- Tap Save, then Start to begin scanning.
- Cleartext HTTP is allowed (network_security_config) so local hubs without TLS work; prefer HTTPS if available.

## Play Store checklist
- Package: `net.jaklic.btwatch`
- Version: 0.1.0 (bump before release)
- Icon: adaptive launcher included
- Privacy: see `PRIVACY.md`
- Data safety: BLE MAC/RSSI sent only to user-configured hub; no third-party sharing.
- Signing: use Play App Signing or your keystore.
- Screenshots & short description required by Play Console.

## Permissions used
- `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`, `ACCESS_FINE_LOCATION`: required for BLE scanning.
- `FOREGROUND_SERVICE`: keeps scanning active with notification.
- `INTERNET`: post sightings to hub.

## Notes
- Use HTTPS for hub URL when possible.
- Scanning stops when you tap Stop or close the notification/service. लंबे background constraints: keep foreground service running for reliability.
