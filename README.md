# Bluetooth Watcher

Small always-on Bluetooth LE watcher for Linux. It scans continuously with Bleak/BlueZ and serves a live feed + browser notifications on `http://localhost:5000`. Optionally filter to specific MAC addresses via `TARGET_MACS`.

## Run natively
```bash
python3 -m pip install -r requirements.txt
# optional one-time caps so you don't need sudo:
sudo setcap 'cap_net_raw,cap_net_admin+eip' $(readlink -f $(which python3))
TARGET_MACS=40:71:E6:AD:2C:27 python3 bt_watch.py
# then open http://localhost:5000
```

## Build the container
```bash
docker build -t bt-watch .
```

## Run the container (uses host BlueZ)
```bash
docker run --rm -it \
  --net=host \
  --privileged \  # or: --cap-add NET_ADMIN --cap-add NET_RAW --device /dev/bus/usb \
  -v /var/run/dbus:/var/run/dbus \
  -e TARGET_MACS=40:71:E6:AD:2C:27 \
  bt-watch
# visit http://localhost:5000 on the host
```

Notes:
- `--net=host` and the DBus mount let the container talk to the host's `bluetoothd`.
- If `--privileged` is too broad, use the capability + device flags shown in the comment.
- Keep the adapter up and Bluetooth enabled on the host; the container doesn't start `bluetoothd`, it reuses the host one.

## What it does
- Listens for all BLE advertisements (or only `TARGET_MACS`).
- Streams events over Server-Sent Events at `/events`.
- Minimal UI at `/` with a scrolling log and native browser notifications.
