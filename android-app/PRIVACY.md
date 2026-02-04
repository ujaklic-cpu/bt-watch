# Privacy Policy – BtWatch (Android probe)

BtWatch scans nearby Bluetooth Low Energy advertisements and sends sightings (MAC address, RSSI, device name if broadcast) to the hub URL you configure in the app. No cloud services are used; data is sent only to the hub you specify.

Data collected:
- BLE advertisement metadata: MAC address, RSSI, broadcast name (if present)
- Probe metadata you configure: HOST_ID, HOST_LOCATION
- Timestamp of each sighting

Data sharing:
- Data is sent only to your configured hub URL over HTTP/HTTPS. Nothing is sent to the developer or third parties by default.

Permissions:
- Bluetooth scan/connect and fine location are required by Android to perform BLE scanning.
- Foreground service keeps scanning while the app is active.

Retention and control:
- The app does not store sightings locally beyond transient memory; retention is controlled by your hub server.
- You can stop scanning at any time from the main screen; uninstalling the app stops all collection.

Security:
- Use HTTPS for the hub URL when possible to protect data in transit.

Contact:
- For questions or issues, open an issue in the repository.
