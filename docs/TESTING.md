# Testing Guide: 2 Android Devices + Linux Server

This guide provides step-by-step instructions for testing the bt-watch system with 2 Android devices as BLE probes and a Linux server as the central hub/aggregator.

## Overview

**Test Setup:**
- 1 Linux server running the hub (map_server.py)
- 2 Android devices acting as BLE probes
- At least 1 BLE device to track (e.g., smartwatch, fitness tracker, beacon)

**What you'll test:**
- BLE scanning from multiple Android devices
- Real-time data aggregation on the hub
- Position estimation based on RSSI from multiple probes
- Live map visualization
- Device tracking across different locations

---

## Part 1: Linux Server Setup (Hub)

### Prerequisites
- Linux server (Ubuntu 20.04+ recommended)
- Python 3.10 or newer
- Network connectivity (WiFi or Ethernet)
- Server IP address accessible by Android devices on the same network

### Step 1.1: Install Dependencies

```bash
# Update system packages
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv git

# Clone the repository (if not already done)
git clone https://github.com/ujaklic-cpu/bt-watch.git
cd bt-watch
```

### Step 1.2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 1.3: Find Your Server IP Address

```bash
# Get server IP address (note this for later)
ip addr show | grep "inet " | grep -v 127.0.0.1
```

Example output: `inet 192.168.1.100/24` - your server IP is `192.168.1.100`

### Step 1.4: Configure and Start the Hub

The hub needs to know the coordinates of each probe for position estimation.

```bash
# Set up coordinates for your two Android devices
# Format: [X, Y] where you can use arbitrary coordinates
# For testing, we'll use a simple grid: device1 at [0, 0], device2 at [10, 0]

export HOST_COORDS_JSON='{"android-device1":[0,0],"android-device2":[10,0]}'
export USER_X=5
export USER_Y=0

# Start the hub server
python3 map_server.py
```

You should see:
```
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:8000
* Running on http://192.168.1.100:8000
```

**Keep this terminal open - the server needs to keep running.**

### Step 1.5: Verify Hub is Running

Open a new terminal and test the hub:

```bash
# Check if hub is responding
curl http://localhost:8000/snapshot

# You should see JSON output like:
# {"hosts":[],"devices":[],"user":{"x":5,"y":0},"updated":1234567890.123}
```

Or open a web browser and visit: `http://localhost:8000` (or use your server IP)
- You should see a blank canvas map (no hosts or devices yet)

---

## Part 2: Build Android App

You can build the Android app on the Linux server or on your development machine.

### Step 2.1: Install Android Build Tools

**Option A: On Linux Server**

```bash
# Install Java Development Kit
sudo apt-get install -y openjdk-17-jdk

# Verify Java installation
java -version
```

**Option B: On Your Development Machine**
- Install Android Studio from https://developer.android.com/studio
- Or install Java 17+ and use command line tools

### Step 2.2: Build the APK

```bash
# Navigate to Android app directory
cd android-app

# Build debug APK
./gradlew :app:assembleDebug

# The APK will be created at:
# android-app/app/build/outputs/apk/debug/app-debug.apk
```

Build should complete with:
```
BUILD SUCCESSFUL
```

### Step 2.3: Transfer APK to Android Devices

**Option A: USB Transfer**
```bash
# Copy APK to a location you can access
cp app/build/outputs/apk/debug/app-debug.apk ~/bt-watch-debug.apk

# Connect your Android device via USB and copy the file
# Or use adb:
adb install app/build/outputs/apk/debug/app-debug.apk
```

**Option B: HTTP Server**
```bash
# In the directory containing the APK
cd app/build/outputs/apk/debug
python3 -m http.server 8080

# Then on your Android device, browse to:
# http://<your-server-ip>:8080/app-debug.apk
# Download and install the APK
```

**Option C: Email/Cloud Storage**
- Email the APK to yourself
- Or upload to Google Drive/Dropbox and download on Android devices

---

## Part 3: Install and Configure Android Devices

Perform these steps on **BOTH** Android devices.

### Step 3.1: Install the APK

1. On your Android device, go to **Settings** → **Security**
2. Enable **"Install apps from unknown sources"** or **"Install unknown apps"**
3. Use a file manager to find the downloaded `app-debug.apk`
4. Tap the APK file and tap **Install**
5. Tap **Open** when installation completes

### Step 3.2: Grant Permissions

When you first open the app, it will request permissions:

1. **Allow "BtWatch" to access this device's location?** → Tap **"Allow all the time"** or **"While using the app"**
2. **Allow "BtWatch" to find, connect to, and determine the relative position of nearby devices?** → Tap **"Allow"**

**Note:** These permissions are required for BLE scanning on Android.

### Step 3.3: Configure Device 1

On the **FIRST** Android device:

1. In the BtWatch app, you'll see the settings screen
2. **Hub URL:** Enter `http://<your-server-ip>:8000/ingest`
   - Example: `http://192.168.1.100:8000/ingest`
   - Make sure to include `/ingest` at the end
3. **HOST_ID:** Enter `android-device1`
4. **HOST_LOCATION:** Enter `Room A` (or any descriptive location)
5. **Target MACs:** Leave empty to scan all devices, or enter specific MAC addresses (comma-separated)
   - Example: `AA:BB:CC:DD:EE:FF` for a specific device
6. **Auto-start on launch:** Toggle ON if desired (optional)
7. Tap **Save Settings**

### Step 3.4: Configure Device 2

On the **SECOND** Android device:

1. Follow the same steps as Device 1, but use:
   - **Hub URL:** `http://<your-server-ip>:8000/ingest`
   - **HOST_ID:** `android-device2`
   - **HOST_LOCATION:** `Room B` (or another location)
   - **Target MACs:** Same as Device 1 (or leave empty)
2. Tap **Save Settings**

**Important:** The HOST_ID values (`android-device1`, `android-device2`) must match the names used in the `HOST_COORDS_JSON` on the server!

---

## Part 4: Start Testing

### Step 4.1: Start Scanning on Both Devices

1. On **Device 1**: Tap **"Start Scanning"**
   - You should see a notification: "BtWatch scanning..."
   - The log should show "Scanning started"

2. On **Device 2**: Tap **"Start Scanning"**
   - Same notification and log message should appear

### Step 4.2: Verify Data on the Hub

Go back to your Linux server terminal or open a browser.

**Check the hub web interface:**
1. Open browser: `http://<your-server-ip>:8000`
2. You should now see:
   - **Blue dots** representing your two Android devices (hosts)
   - **Red dots** representing detected BLE devices
   - Labels showing host IDs and device MAC addresses

**Check via terminal:**
```bash
# View current snapshot
curl http://<your-server-ip>:8000/snapshot

# You should see hosts listed:
# "hosts":[{"id":"android-device1","x":0,"y":0},{"id":"android-device2","x":10,"y":0}]

# And devices detected:
# "devices":[{"address":"AA:BB:CC:DD:EE:FF","name":"Device Name",...}]
```

### Step 4.3: Monitor Live Events

**On the hub server terminal:**
```bash
# Stream live events from the hub
curl -N http://localhost:8000/events
```

You should see real-time BLE sightings streaming in:
```
data: {"host":"android-device1","address":"AA:BB:CC:DD:EE:FF","rssi":-65,...}
data: {"host":"android-device2","address":"AA:BB:CC:DD:EE:FF","rssi":-72,...}
```

**On Android devices:**
- Check the log section in the app
- You should see entries like: "Sent: AA:BB:CC:DD:EE:FF @ -65 dBm"

---

## Part 5: Testing Scenarios

### Scenario 1: Basic Tracking

**Goal:** Verify both devices can detect and report the same BLE device

1. Place a BLE device (smartwatch, beacon, etc.) between both Android devices
2. Observe both devices detecting it in their logs
3. Check the hub map - the red dot should appear between the two blue host dots
4. The position is estimated based on RSSI (signal strength) from both devices

**Expected results:**
- Both Android devices show the same MAC address in logs
- Hub map shows device position between the two probes
- RSSI values differ based on distance to each probe

### Scenario 2: Movement Tracking

**Goal:** Track device movement and position changes

1. Start with the BLE device near Device 1
2. Slowly move it toward Device 2
3. Watch the red dot on the hub map move accordingly

**Expected results:**
- Position estimate shifts from left (near Device 1) to right (near Device 2)
- RSSI values change: stronger near the closer device
- Map updates in real-time (may take a few seconds)

### Scenario 3: Multiple Device Tracking

**Goal:** Track multiple BLE devices simultaneously

1. Place 2-3 different BLE devices in the area
2. Observe all devices appearing on the map
3. Each should have a unique MAC address

**Expected results:**
- Multiple red dots on the map, one per device
- Each device shows position estimate
- All MAC addresses are unique

### Scenario 4: Probe Separation

**Goal:** Test with devices in different rooms/locations

1. Take Device 1 to one room
2. Take Device 2 to another room (5-10 meters away)
3. Place a BLE device you want to track in between
4. Verify both probes can still reach the hub

**Expected results:**
- Both devices continue reporting
- Position estimation works across the distance
- Devices only seen by one probe show position at that probe's location

---

## Part 6: Verification Checklist

Use this checklist to verify your setup is working correctly:

- [ ] Hub server is running and accessible at `http://<server-ip>:8000`
- [ ] Hub map shows two blue host markers (android-device1, android-device2)
- [ ] Device 1 shows "Scanning started" in log
- [ ] Device 2 shows "Scanning started" in log
- [ ] Both devices show "Sent: <MAC>" messages in logs when BLE devices are detected
- [ ] Hub `/snapshot` endpoint shows both hosts in the JSON response
- [ ] Hub map displays red dots for detected BLE devices
- [ ] Device positions update when you move a tracked BLE device
- [ ] RSSI values in logs change based on distance to the device
- [ ] Both Android devices maintain connection to hub (check periodic log entries)

---

## Part 7: Troubleshooting

### Problem: Android App Can't Connect to Hub

**Symptoms:** "Connection failed" or no data appearing on hub

**Solutions:**
1. Verify server IP address is correct
2. Check that both devices are on the same WiFi network as the server
3. Test connectivity: `ping <server-ip>` from another device
4. Verify hub URL includes `/ingest`: `http://192.168.1.100:8000/ingest`
5. Check firewall: `sudo ufw allow 8000/tcp` (if using UFW)
6. Ensure hub server is still running (check the terminal)

### Problem: No BLE Devices Detected

**Symptoms:** Scanning starts but no devices in logs

**Solutions:**
1. Verify BLE device is powered on and advertising
2. Check Android Bluetooth is enabled: Settings → Bluetooth → ON
3. Try a different BLE device (smartwatch, fitness tracker, beacon)
4. Check app permissions: Settings → Apps → BtWatch → Permissions → Location = "Allow all the time"
5. Restart the scanning: Stop → Start
6. Check if other BLE scanning apps can see devices (use a BLE scanner app)

### Problem: Only One Device Appears on Hub

**Symptoms:** One Android device works, the other doesn't

**Solutions:**
1. Verify the second device has the correct Hub URL
2. Check the HOST_ID matches the server configuration
3. Verify both devices have granted all permissions
4. Check both devices show "Scanning started" in logs
5. Restart scanning on the non-working device
6. Check hub server logs for error messages

### Problem: Position Estimation Not Working

**Symptoms:** Devices appear but position is null or always at one probe

**Solutions:**
1. Verify `HOST_COORDS_JSON` on server includes both device IDs
2. Check that HOST_ID on Android matches the JSON keys exactly
3. Ensure both devices are detecting the same BLE device (check logs)
4. The BLE device must be in range of both Android probes
5. Wait 5-10 seconds for position to stabilize after movement

### Problem: App Crashes or Stops Scanning

**Symptoms:** App closes or scanning stops unexpectedly

**Solutions:**
1. Check Android battery optimization: Settings → Apps → BtWatch → Battery → Unrestricted
2. Keep the app in foreground or notification visible
3. Check device logs: `adb logcat | grep BtWatch` (if using USB debugging)
4. Clear app data: Settings → Apps → BtWatch → Storage → Clear data (then reconfigure)
5. Reinstall the APK

### Problem: Hub Shows No Hosts

**Symptoms:** Map is empty, no blue dots

**Solutions:**
1. Android devices must have started scanning at least once
2. Check if devices are sending data: look for log entries like "Sent: ..."
3. Verify `HOST_COORDS_JSON` environment variable is set correctly
4. Restart the hub server with the correct environment variables
5. Check `/snapshot` endpoint to see raw data: `curl http://localhost:8000/snapshot`

---

## Part 8: Advanced Testing

### Testing with Different Coordinate Systems

You can test with geographic coordinates (latitude/longitude):

```bash
# Example: Ljubljana, Slovenia area
# android-device1 at one location, android-device2 at another
export HOST_COORDS_JSON='{"android-device1":[46.051,14.506],"android-device2":[46.052,14.508]}'
export USER_X=46.0515
export USER_Y=14.507

# Restart hub
python3 map_server.py
```

### Testing with Target MAC Filtering

To track only specific devices:

1. Find the MAC address of your BLE device (visible in app logs)
2. On both Android devices, enter the MAC in "Target MACs" field
3. Only that device will be reported to the hub
4. Useful for reducing noise in busy BLE environments

### Testing Position Accuracy

1. Measure actual distances between devices
2. Place tracked device at known positions
3. Compare hub's estimated position to actual position
4. RSSI-based positioning is approximate (±1-5 meters typical)

### Load Testing

1. Configure both devices to scan all BLE devices (no target filter)
2. Go to a busy area (shopping mall, office)
3. Monitor hub performance with many devices
4. Check that events stream smoothly
5. Verify Android devices maintain stable connection

---

## Part 9: Stopping and Cleanup

### Stop Scanning

On each Android device:
1. Tap **"Stop Scanning"**
2. Notification should disappear
3. Log shows "Scanning stopped"

### Stop Hub Server

In the server terminal:
1. Press `Ctrl+C` to stop the hub
2. Deactivate virtual environment: `deactivate`

### Uninstall (Optional)

On Android devices:
1. Settings → Apps → BtWatch
2. Tap **Uninstall**

---

## Summary

You've now successfully:
- ✅ Set up a Linux server as a BLE tracking hub
- ✅ Built and installed the Android app on 2 devices
- ✅ Configured both devices to report to the hub
- ✅ Tested BLE scanning and position estimation
- ✅ Verified real-time data aggregation and visualization

The system is now ready for production use or further customization!

---

## Next Steps

- **Production Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md) for production setup
- **API Reference:** See [API.md](API.md) for endpoint documentation
- **Security:** Add authentication, HTTPS, and network isolation for production
- **Twingate:** Set up secure remote access without exposing ports
- **ESP32 Probes:** Add ESP32 devices for additional coverage

## Getting Help

- Check [README.md](../README.md) for general information
- Review [API.md](API.md) for endpoint details
- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment options
- Open an issue on GitHub for bugs or questions
