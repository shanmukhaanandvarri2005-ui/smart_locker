/*
 * SmartLocker ESP8266 Solenoid Relay Controller Firmware
 * ------------------------------------------------------
 * Hardware:
 *   - ESP8266 (NodeMCU v2/v3 or Wemos D1 Mini)
 *   - Relay Module on Pin D1 (GPIO 5), Active LOW
 *   - 12V Solenoid Locker + 1N4007 Flyback Diode
 *   - Assigned Physical Locker: LOCKER 1 ONLY
 *   - Connected to Laptop via USB Serial (115200 baud) OR local WiFi
 *
 * Behavior:
 *   - Only commands targeting Locker 1 (e.g. UNLOCK:1:4 or UNLOCK:1,2:6)
 *     will activate the physical relay on Pin D1.
 *   - Commands for other lockers (Locker 2, Locker 3, Locker 4, Locker 5)
 *     are recognized and ignored, leaving Locker 1 securely locked!
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
#define THIS_LOCKER_ID  1       // Physical relay on Pin D1 is wired ONLY for Locker 1
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
void processCommand(String cmd);

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF); // Start in securely LOCKED state

  Serial.println("\n==========================================");
  Serial.println("   SMARTLOCKER ESP8266 CONTROLLER READY   ");
  Serial.println("==========================================");
  Serial.println("Assigned Physical Locker: LOCKER 1 ONLY (Pin D1)");
  Serial.println("Protocol: USB Serial @ 115200 baud");
  Serial.println("Commands accepted: UNLOCK:<locker>:<sec>, UNLOCK:1, LOCK, STATUS");
  Serial.println("Note: Commands for Locker 2, 3, 4, 5 will NOT open Locker 1.");

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
    Serial.println(">> [AUTO-LOCK]: Solenoid de-energized. Locker 1 is now LOCKED.\n");
  }
}

// Checks if Locker 1 is targeted in a locker string (e.g. "1", "01", "1,2", "3,1")
bool isLocker1Targeted(String target) {
  target.trim();
  target.toUpperCase();
  if (target == "1" || target == "01" || target == "LOCKER 1" || target == "LOCKER 01" || target == "LOCKER1") {
    return true;
  }
  // Check in comma-separated list
  if (target.startsWith("1,") || target.endsWith(",1") || target.indexOf(",1,") != -1) {
    return true;
  }
  if (target.startsWith("01,") || target.endsWith(",01") || target.indexOf(",01,") != -1) {
    return true;
  }
  return false;
}

void processCommand(String cmd) {
  cmd.trim();
  String upperCmd = cmd;
  upperCmd.toUpperCase();

  // Command 1: UNLOCK Commands
  // Formats supported:
  //   - UNLOCK:1:4        -> Unlock Locker 1 for 4 seconds
  //   - UNLOCK:2:4        -> Target Locker 2 (Locker 1 relay IGNORED)
  //   - UNLOCK:1,2:6      -> Multiple lockers including 1 (Locker 1 unlocks!)
  //   - UNLOCK:1          -> Unlock Locker 1 (default 4 seconds)
  //   - UNLOCK:2          -> Target Locker 2 (IGNORED)
  //   - UNLOCK            -> Standalone test unlock for Locker 1
  if (upperCmd.startsWith("UNLOCK")) {
    unsigned long duration = DEFAULT_UNLOCK_MS;
    bool targetLocker1 = false;
    String lockerPart = "";

    int firstColon = upperCmd.indexOf(':');
    if (firstColon == -1) {
      // Standalone "UNLOCK" (manual serial test) -> unlock Locker 1
      targetLocker1 = true;
      lockerPart = "1 (Default)";
    } else {
      int secondColon = upperCmd.indexOf(':', firstColon + 1);
      if (secondColon != -1) {
        // Format: UNLOCK:<lockers>:<duration>
        lockerPart = upperCmd.substring(firstColon + 1, secondColon);
        lockerPart.trim();
        int sec = upperCmd.substring(secondColon + 1).toInt();
        if (sec > 0) duration = (unsigned long)sec * 1000;
        targetLocker1 = isLocker1Targeted(lockerPart);
      } else {
        // Format with only 1 colon: UNLOCK:<arg>
        String arg = upperCmd.substring(firstColon + 1);
        arg.trim();
        if (isLocker1Targeted(arg)) {
          targetLocker1 = true;
          lockerPart = arg;
        } else if (arg == "2" || arg == "3" || arg == "4" || arg == "5" || arg.startsWith("LOCKER")) {
          targetLocker1 = false;
          lockerPart = arg;
        } else {
          // Argument is a duration in seconds (e.g. UNLOCK:4)
          int sec = arg.toInt();
          if (sec > 0) duration = (unsigned long)sec * 1000;
          targetLocker1 = true;
          lockerPart = "1 (Default)";
        }
      }
    }

    Serial.println("------------------------------------------");
    if (targetLocker1) {
      Serial.print(">> [WEBSITE COMMAND]: UNLOCK request for LOCKER 1 (Duration: ");
      Serial.print(duration / 1000);
      Serial.println("s)");
      Serial.println(">> [MATCH]: Activating Relay on Pin D1 for Solenoid Lock 1!");
      unlockLocker(duration);
    } else {
      Serial.print(">> [WEBSITE COMMAND]: UNLOCK request for Locker: [ ");
      Serial.print(lockerPart);
      Serial.println(" ]");
      Serial.println(">> [NOTICE]: Physical relay on Pin D1 is wired ONLY for Locker 1.");
      Serial.println(">> [ACTION]: Locker 1 solenoid will NOT activate (IGNORED).");
    }
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
  Serial.println(">> [HARDWARE]: Relay ON (Solenoid retracted / Door 1 Open)");
}

void lockLocker() {
  digitalWrite(RELAY_PIN, RELAY_OFF); // De-energize relay (solenoid locks)
  isUnlocked = false;
  Serial.println(">> [HARDWARE]: Relay OFF (Solenoid engaged / Door 1 Locked)");
}

// HTTP Webhook Handlers (for WiFi mode)
void handleHttpUnlock() {
  unsigned long duration = DEFAULT_UNLOCK_MS;
  if (server.hasArg("duration")) {
    int sec = server.arg("duration").toInt();
    if (sec > 0) duration = sec * 1000;
  }

  String locker = "1";
  if (server.hasArg("locker")) {
    locker = server.arg("locker");
  }

  bool targetLocker1 = isLocker1Targeted(locker);
  if (targetLocker1) {
    unlockLocker(duration);
    server.send(200, "application/json", "{\"success\":true,\"locker\":1,\"state\":\"unlocked\",\"duration_ms\":" + String(duration) + "}");
  } else {
    Serial.print(">> [HTTP]: Request for Locker ");
    Serial.print(locker);
    Serial.println(". Relay Pin D1 is for Locker 1 only - ignored.");
    server.send(200, "application/json", "{\"success\":true,\"locker\":\"" + locker + "\",\"state\":\"ignored_not_locker_1\"}");
  }
}

void handleHttpLock() {
  lockLocker();
  server.send(200, "application/json", "{\"success\":true,\"state\":\"locked\"}");
}

void handleHttpStatus() {
  server.send(200, "application/json", "{\"state\":\"" + String(isUnlocked ? "unlocked" : "locked") + "\"}");
}
