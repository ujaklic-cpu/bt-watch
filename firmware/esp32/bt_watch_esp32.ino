/**
 * BtWatch ESP32 probe
 * Scans BLE advertisements, tags with HOST_ID/HOST_LOCATION/HOST_X/HOST_Y,
 * and POSTs sightings to AGGREGATOR_URL (/ingest). Also self-registers host
 * coordinates to /host_coord on startup.
 *
 * Tested with Arduino core for ESP32 v2.0.x+.
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <BLEDevice.h>

// Device configuration
const char *WIFI_SSID = "YOUR_WIFI";
const char *WIFI_PASS = "YOUR_PASS";

String AGGREGATOR_URL = "http://192.168.1.10:8000";  // base URL
String HOST_ID = "esp32-probe";
String HOST_LOCATION = "lab";
float HOST_X = 0.0f;
float HOST_Y = 0.0f;

// Optional MAC allowlist; leave empty to send all.
String TARGET_MACS[] = {}; // example: {"40:71:E6:AD:2C:27"}
const int TARGET_MAC_COUNT = sizeof(TARGET_MACS) / sizeof(String);

HTTPClient http;

String jsonEscape(const String &value) {
  String escaped;
  escaped.reserve(value.length());
  for (size_t i = 0; i < value.length(); i++) {
    char c = value.charAt(i);
    if (c == '"' || c == '\\') escaped += '\\';
    if (c == '\n') {
      escaped += "\\n";
    } else if (c == '\r') {
      escaped += "\\r";
    } else if (static_cast<unsigned char>(c) >= 0x20) {
      escaped += c;
    }
  }
  return escaped;
}

bool isAllowed(const String &mac) {
  if (TARGET_MAC_COUNT == 0) return true;
  for (int i = 0; i < TARGET_MAC_COUNT; i++) {
    if (mac.equalsIgnoreCase(TARGET_MACS[i])) return true;
  }
  return false;
}

void postJSON(const String &path, const String &json) {
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient c;
  String url = AGGREGATOR_URL + path;
  c.begin(url);
  c.addHeader("Content-Type", "application/json");
  int code = c.POST(json);
  c.end();
  Serial.printf("POST %s -> %d\n", path.c_str(), code);
}

class ScanCallbacks : public BLEAdvertisedDeviceCallbacks {
  void onResult(BLEAdvertisedDevice adv) override {
    String mac = adv.getAddress().toString().c_str();
    mac.toUpperCase();
    if (!isAllowed(mac)) return;
    int rssi = adv.getRSSI();
    String name = adv.getName().c_str();
    if (name.length() == 0 && adv.haveName()) name = adv.getName().c_str();

    String json = "{";
    json += "\"host\":\"" + jsonEscape(HOST_ID) + "\",";
    json += "\"location\":\"" + jsonEscape(HOST_LOCATION) + "\",";
    json += "\"address\":\"" + jsonEscape(mac) + "\",";
    json += "\"name\":\"" + jsonEscape(name) + "\",";
    json += "\"rssi\":" + String(rssi) + ",";
    json += "\"ts\":" + String((float)millis() / 1000.0f);
    json += "}";

    postJSON("/ingest", json);
  }
};

void registerHostCoord() {
  String json = "{";
  json += "\"host\":\"" + jsonEscape(HOST_ID) + "\",";
  json += "\"x\":" + String(HOST_X, 3) + ",";
  json += "\"y\":" + String(HOST_Y, 3) + ",";
  json += "\"location\":\"" + jsonEscape(HOST_LOCATION) + "\"";
  json += "}";
  postJSON("/host_coord", json);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  BLEDevice::init(HOST_ID.c_str());
  BLEScan *scan = BLEDevice::getScan();
  scan->setAdvertisedDeviceCallbacks(new ScanCallbacks(), true);
  scan->setActiveScan(true);
  scan->setInterval(100);
  scan->setWindow(80);

  registerHostCoord();
  scan->start(0, nullptr, false); // continuous
}

void loop() {
  delay(1000);
}
