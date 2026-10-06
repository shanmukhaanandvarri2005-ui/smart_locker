/*
 * SmartLocker ESP8266 Solenoid Relay Controller Firmware
 * ------------------------------------------------------
 * Hardware:
 *   - ESP8266 (NodeMCU v2/v3 or Wemos D1 Mini)
 *   - Relay Module on Pin D1 (GPIO 5), Active LOW
 *   - 12V Solenoid Locker + 1N4007 Flyback Diode
 *   - Connected to Laptop via USB Serial (115200 baud) OR local WiFi
 *
 * Wiring:
 *   - ESP8266 D1  -> Relay IN
 *   - ESP8266 GND -> Relay GND
 *   - ESP8266 VIN -> Relay VCC (5V)
 *   - Solenoid (+) -> 12V DC Supply (+)
 *   - Solenoid (-) -> Relay COM
 *   - Relay NO     -> 12V DC Supply (-)
 *   - 1N4007 Diode across Solenoid (+) & (-):
 *       Cathode (silver band) to (+), Anode to (-)
 */

#include <Arduino.h>

// If you want wireless WiFi control, enter your WiFi credentials below.
// Leave as empty strings ("") to run in USB Serial mode.
const char* WIFI_SSID     = "";  // e.g. "MyHomeWiFi"
const char* WIFI_PASSWORD = "";  // e.g. "MyPassword123"

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

#define RELAY_PIN       D1      // GPIO 5 (Pin D1 on NodeMCU / Wemos D1 Mini)
#define DEFAULT_UNLOCK_MS 4000  // Default unlock duration: 4 seconds

// Active LOW relay definitions
#define RELAY_ON        LOW
#define RELAY_OFF       HIGH

bool isUnlocked = false;
unsigned long unlockStartTime = 0;
unsigned long currentUnlockDuration = DEFAULT_UNLOCK_MS;
String serialInput = "";
String authorizedCard = "";

ESP8266WebServer server(80);
bool wifiEnabled = false;

void unlockLocker(unsigned long durationMs = DEFAULT_UNLOCK_MS);
void lockLocker();
void handleHttpUnlock();
void handleHttpLock();
void handleHttpStatus();

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF); // Start in securely LOCKED state

  Serial.println("\n==========================================");
  Serial.println("   SMARTLOCKER ESP8266 CONTROLLER READY   ");
  Serial.println("==========================================");
  Serial.println("Protocol: USB Serial @ 115200 baud");
  Serial.println("Commands accepted: UNLOCK, UNLOCK:<sec>, LOCK, STATUS");

  // Connect to WiFi if credentials provided
  if (WIFI_SSID != NULL && strlen(WIFI_SSID) > 0) {
    Serial.print("Connecting to WiFi: ");
    Serial.println(WIFI_SSID);
    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 25) {
      delay(400);
      Serial.print(".");
      attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
      wifiEnabled = true;
      Serial.println("\n>> WiFi Connected successfully!");
      Serial.print(">> ESP8266 IP Address: http://");
      Serial.println(WiFi.localIP());

      server.on("/unlock", handleHttpUnlock);
      server.on("/lock", handleHttpLock);
      server.on("/status", handleHttpStatus);
      server.begin();
      Serial.println(">> HTTP Webhook Server started on port 80");
    } else {
      Serial.println("\n>> WiFi connection timed out. Continuing in USB Serial mode.");
    }
  } else {
    Serial.println("Mode: Direct USB Serial (Plug-and-Play with Flask Web App)");
  }

  Serial.println(">> System Armed. Ready for commands from Website...\n");
}

void loop() {
  // 1. Handle incoming HTTP requests if WiFi is active
  if (wifiEnabled) {
    server.handleClient();
  }

  // 2. Read incoming commands from Laptop via USB Serial
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialInput.length() > 0) {
        serialInput.trim();
        processCommand(serialInput);
        serialInput = "";
      }
    } else {
      serialInput += c;
    }
  }

  // 3. Non-blocking auto-relock timer
  if (isUnlocked && (millis() - unlockStartTime >= currentUnlockDuration)) {
    lockLocker();
    Serial.println(">> [AUTO-LOCK]: Solenoid de-energized. Locker is now LOCKED.\n");
  }
}

void processCommand(String cmd) {
  cmd.trim();
  String upperCmd = cmd;
  upperCmd.toUpperCase();

  // Command 1: UNLOCK or UNLOCK:<duration_sec>
  if (upperCmd.startsWith("UNLOCK")) {
    unsigned long duration = DEFAULT_UNLOCK_MS;
    int colonIdx = upperCmd.indexOf(':');
    if (colonIdx > 0) {
      int sec = upperCmd.substring(colonIdx + 1).toInt();
      if (sec > 0) {
        duration = sec * 1000;
      }
    }
    Serial.println("------------------------------------------");
    Serial.print(">> [WEBSITE COMMAND]: UNLOCK signal received! Duration: ");
    Serial.print(duration / 1000);
    Serial.println(" seconds.");
    unlockLocker(duration);
    Serial.println("------------------------------------------\n");
    return;
  }

  // Command 2: LOCK
  if (upperCmd == "LOCK") {
    Serial.println(">> [WEBSITE COMMAND]: LOCK signal received.");
    lockLocker();
    return;
  }

  // Command 3: STATUS / PING
  if (upperCmd == "STATUS" || upperCmd == "PING") {
    Serial.print("STATUS: ");
    Serial.println(isUnlocked ? "UNLOCKED" : "LOCKED");
    return;
  }

  // Command 4: Direct RFID Card UID input (from Serial Monitor manual testing)
  Serial.println("------------------------------------------");
  Serial.print("Scanned Card UID: [ ");
  Serial.print(cmd);
  Serial.println(" ]");

  if (authorizedCard == "") {
    authorizedCard = cmd;
    Serial.println(">> [SUCCESS]: Card registered as Authorized Card!");
    unlockLocker(DEFAULT_UNLOCK_MS);
  } else if (cmd.equalsIgnoreCase(authorizedCard)) {
    Serial.println("STATUS: [ACCESS GRANTED] - Card Matched!");
    unlockLocker(DEFAULT_UNLOCK_MS);
  } else {
    Serial.println("STATUS: [ACCESS DENIED] - Unauthorized Card!");
  }
  Serial.println("------------------------------------------\n");
}

void unlockLocker(unsigned long durationMs) {
  digitalWrite(RELAY_PIN, RELAY_ON); // Energize relay (pulls solenoid open)
  isUnlocked = true;
  unlockStartTime = millis();
  currentUnlockDuration = durationMs;
  Serial.println(">> [HARDWARE]: Relay ON (Solenoid retracted / Door Open)");
}

void lockLocker() {
  digitalWrite(RELAY_PIN, RELAY_OFF); // De-energize relay (solenoid locks)
  isUnlocked = false;
  Serial.println(">> [HARDWARE]: Relay OFF (Solenoid engaged / Door Locked)");
}

// HTTP Webhook Handlers (for WiFi mode)
void handleHttpUnlock() {
  unsigned long duration = DEFAULT_UNLOCK_MS;
  if (server.hasArg("duration")) {
    int sec = server.arg("duration").toInt();
    if (sec > 0) duration = sec * 1000;
  }
  unlockLocker(duration);
  server.send(200, "application/json", "{\"success\":true,\"state\":\"unlocked\",\"duration_ms\":" + String(duration) + "}");
}

void handleHttpLock() {
  lockLocker();
  server.send(200, "application/json", "{\"success\":true,\"state\":\"locked\"}");
}

void handleHttpStatus() {
  server.send(200, "application/json", "{\"state\":\"" + String(isUnlocked ? "unlocked" : "locked") + "\"}");
}
