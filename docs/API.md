# API Reference

This document describes the HTTP endpoints available in bt-watch.

## bt_watch.py - BLE Probe Server (Port 5000)

### GET /

**Description:** Minimal web UI showing live BLE sightings with browser notifications.

**Response:** HTML page with Server-Sent Events client

**Features:**
- Real-time device sightings display
- Browser notifications (requires permission)
- Shows host, location, MAC address, device name, and RSSI

---

### GET /events

**Description:** Server-Sent Events (SSE) stream of BLE device sightings.

**Response:** `text/event-stream`

**Event Format:**
```json
{
  "host": "kitchen-pi",
  "location": "Kitchen north",
  "address": "40:71:E6:AD:2C:27",
  "name": "Device Name",
  "rssi": -65,
  "ts": 1707858000.123
}
```

**Fields:**
- `host` (string): Host identifier (from `HOST_ID` env var or hostname)
- `location` (string): Human-readable location (from `HOST_LOCATION` env var)
- `address` (string): Bluetooth MAC address
- `name` (string): Device name (if advertised)
- `rssi` (number): Signal strength in dBm (typically -100 to 0)
- `ts` (number): Unix timestamp

**Usage Example:**
```javascript
const es = new EventSource('http://localhost:5000/events');
es.onmessage = (e) => {
  const event = JSON.parse(e.data);
  console.log(`Device ${event.address} at ${event.rssi} dBm`);
};
```

---

### GET /health

**Description:** Health check endpoint with probe metadata.

**Response:** JSON (200 OK)

```json
{
  "status": "ok",
  "host": "kitchen-pi",
  "location": "Kitchen north",
  "targets": ["40:71:E6:AD:2C:27"],
  "time": 1707858000.123
}
```

**Fields:**
- `status` (string): Always "ok"
- `host` (string): Host identifier
- `location` (string): Host location
- `targets` (array): List of filtered MAC addresses (lowercase), or empty if watching all
- `time` (number): Current server time (Unix timestamp)

---

## map_server.py - Central Aggregator (Port 8000)

### POST /ingest

**Description:** Receive BLE sighting events from probes.

**Request Body (JSON):**
```json
{
  "host": "kitchen-pi",
  "address": "40:71:E6:AD:2C:27",
  "rssi": -65,
  "name": "Device Name",
  "location": "Kitchen north",
  "ts": 1707858000.123
}
```

**Required Fields:**
- `host` (string): Probe identifier
- `address` (string): Bluetooth MAC address
- `rssi` (number): Signal strength in dBm

**Optional Fields:**
- `name` (string): Device name
- `location` (string): Probe location description
- `ts` (number): Timestamp (defaults to server time if omitted)

**Success Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "missing fields"
}
```

---

### POST /host_coord

**Description:** Register or update host position coordinates.

**Coordinate System:**
- The system accepts arbitrary numeric coordinates (x, y) in the range -1e6 to 1e6
- You can use geographic coordinates (latitude/longitude) or custom grid coordinates
- **For geographic coordinates:**
  - Recommended mapping: `x = longitude` (east-west), `y = latitude` (north-south)
  - This follows standard geographic conventions where longitude is the x-axis and latitude is the y-axis
  - Valid ranges: latitude -90 to 90, longitude -180 to 180
- **For custom grids:** use any consistent coordinate system (meters, feet, arbitrary units)
- All hosts should use the same coordinate system for position estimation to work correctly

**Request Body (JSON):**
```json
{
  "host": "kitchen-pi",
  "x": 14.506,
  "y": 46.051,
  "location": "Kitchen north"
}
```

**Required Fields:**
- `host` (string): Host identifier
- `x` (number): X coordinate (longitude for geographic, or custom grid X, range: -1e6 to 1e6)
- `y` (number): Y coordinate (latitude for geographic, or custom grid Y, range: -1e6 to 1e6)

**Optional Fields:**
- `location` (string): Human-readable location description

**Success Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields:
  ```json
  {
    "error": "host,x,y required"
  }
  ```
- `400 Bad Request` - Invalid coordinate values:
  ```json
  {
    "error": "invalid coordinate values"
  }
  ```
- `400 Bad Request` - Coordinates out of range:
  ```json
  {
    "error": "coordinates out of range"
  }
  ```

---

### GET /events

**Description:** Server-Sent Events stream of all received BLE sightings.

**Response:** `text/event-stream`

**Event Format:** Same as probe `/events` endpoint

**Usage:** Subscribe to real-time updates from all probes

---

### GET /snapshot

**Description:** Current state of all devices and hosts.

**Response:** JSON (200 OK)

```json
{
  "hosts": [
    {
      "id": "kitchen-pi",
      "x": 46.051,
      "y": 14.506
    }
  ],
  "devices": [
    {
      "address": "40:71:E6:AD:2C:27",
      "name": "Device Name",
      "estimate": {
        "x": 46.0515,
        "y": 14.5055
      },
      "hosts": [
        {
          "host": "kitchen-pi",
          "address": "40:71:E6:AD:2C:27",
          "name": "Device Name",
          "rssi": -65,
          "location": "Kitchen north",
          "ts": 1707858000.123
        }
      ]
    }
  ],
  "user": {
    "x": 0,
    "y": 0
  },
  "updated": 1707858000.123
}
```

**Fields:**
- `hosts` (array): Registered hosts with coordinates
- `devices` (array): Detected devices with position estimates
  - `estimate.x`, `estimate.y`: Weighted centroid based on RSSI from hosts (null if insufficient data)
  - `hosts`: Array of latest sighting from each host
- `user` (object): User marker position (from `USER_X`, `USER_Y` env vars)
- `updated` (number): Snapshot generation timestamp

**Position Estimation:**
- Devices are positioned using a weighted centroid algorithm
- Weights are calculated as `1 / max(1, |rssi|)` (stronger signals = more weight)
- Only hosts with registered coordinates contribute to estimates
- Returns `null` for x/y if no hosts with coordinates have seen the device
- **Note:** All hosts must use the same coordinate system (all lat/lon or all custom grid) for meaningful position estimates

---

### GET /

**Description:** Interactive map UI showing hosts and device positions.

**Response:** HTML page with canvas-based visualization

**Features:**
- Auto-scaling grid view
- Blue markers for hosts
- Red markers for devices (at estimated positions)
- Real-time updates via SSE
- Labeled markers with host/device identifiers

---

## Environment Variables

### bt_watch.py (Probe)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TARGET_MACS` | No | (empty) | Comma-separated MAC addresses to filter. If empty, reports all devices. |
| `HOST_ID` | No | hostname | Identifier for this probe |
| `HOST_LOCATION` | No | (empty) | Human-readable location description |
| `HOST_X` | No | - | X coordinate for this probe (posted to aggregator if set with HOST_Y) |
| `HOST_Y` | No | - | Y coordinate for this probe (posted to aggregator if set with HOST_X) |
| `AGGREGATOR_URL` | No | - | URL of central aggregator (e.g., `http://hub:8000/ingest`) |

### map_server.py (Aggregator)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HOST_COORDS_JSON` | No | {} | JSON mapping of host IDs to [x, y] coordinates. Example: `{"host1":[46.05,14.50],"host2":[46.06,14.51]}` |
| `USER_X` | No | 0 | User marker X coordinate |
| `USER_Y` | No | 0 | User marker Y coordinate |

---

## Rate Limiting & Performance

**Current Limitations:**
- No rate limiting implemented
- Unbounded device history (may grow indefinitely)
- No authentication/authorization

**Recommendations for Production:**
- Deploy behind reverse proxy with rate limiting
- Add authentication (API keys, mutual TLS, etc.)
- Implement periodic cleanup of old sightings
- Use HTTPS for sensitive deployments

---

## Error Handling

**HTTP Status Codes:**
- `200 OK` - Successful request
- `400 Bad Request` - Invalid request (missing fields, invalid data)
- `500 Internal Server Error` - Server error

**Common Issues:**
- SSE disconnections: Clients should reconnect automatically
- Missing estimates: Device needs to be seen by hosts with registered coordinates
- Queue overflow: High-traffic scenarios may drop events; check queue sizes

---

## Security Considerations

⚠️ **Important:** This application has no built-in authentication. All endpoints accept unauthenticated requests.

**Risks:**
- Data injection: Attackers can POST fake sightings
- Data poisoning: Fake coordinates can corrupt device position estimates
- Privacy: MAC addresses and locations are transmitted in plain text

**Mitigation Strategies:**
1. Deploy on trusted networks only (VPN, private LAN)
2. Use reverse proxy with authentication (nginx + basic auth, OAuth)
3. Enable HTTPS/TLS
4. Use Twingate or similar zero-trust solution (see `twingate/`)
5. Implement API key validation (requires code changes)
6. Apply CORS restrictions
7. Monitor for unusual traffic patterns

**Example nginx config with basic auth:**
```nginx
location /ingest {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:8000;
}
```
