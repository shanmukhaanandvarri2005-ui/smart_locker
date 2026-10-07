/*
 * SmartLocker ESP8266 Controller Firmware (Locker 1 Only)
 * --------------------------------------------------------
 * Hardware:
 *   - ESP8266 (NodeMCU / Wemos D1 Mini)
 *   - Relay Module connected to Pin D1 (GPIO 5), Active LOW
 *   - Controls ONLY Locker 1 (Solenoid Lock 1)
 *
 * Behavior:
 *   - Only requests for Locker 1 will energize the relay on Pin D1.
 *   - Requests for Locker 2, 3, 4, 5 are ignored and Locker 1 stays locked.
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

// ================= USER CONFIGURATION =================
// Leave WiFi credentials blank ("") for USB Serial mode (Plug-and-play with Laptop)
const char* WIFI_SSID     = "";  
const char* WIFI_PASSWORD = "";  

#define RELAY_PIN         D1      // Relay Signal Pin (GPIO 5 on NodeMCU)
#define THIS_LOCKER_ID    1       // This hardware is assigned ONLY to Locker 1
#define DEFAULT_UNLOCK_MS 4000    // Auto-lock duration: 4 seconds

// Active-LOW relay definitions (Standard 5V relay module)
#define RELAY_ON          LOW
#define RELAY_OFF         HIGH
// ======================================================

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

bool isUnlocked = false;
unsigned long unlockStartTime = 0;
unsigned long currentUnlockDuration = DEFAULT_UNLOCK_MS;
String serialInput = "";
String authorizedCard = "";

ESP8266WebServer server(80);
bool wifiEnabled = false;

// Hardware control functions (defined first so no prototype errors occur)
void unlockLocker(unsigned long durationMs = DEFAULT_UNLOCK_MS) {
  digitalWrite(RELAY_PIN, RELAY_ON); // Energize relay (pulls solenoid open)
  isUnlocked = true;
  unlockStartTime = millis();
  currentUnlockDuration = durationMs;
  Serial.println(">> [HARDWARE]: Relay ON (Solenoid retracted / Door 1 Unlocked)");
}

void lockLocker() {
  digitalWrite(RELAY_PIN, RELAY_OFF); // De-energize relay (locks solenoid)
  isUnlocked = false;
  Serial.println(">> [HARDWARE]: Relay OFF (Solenoid engaged / Door 1 Locked)");
}

// Checks if Locker 1 is targeted in a locker string (e.g. "1", "01", "1,2", "3,1")
bool isLocker1Targeted(String target) {
  target.trim();
  target.toUpperCase();
  if (target == "1" || target == "01" || target == "LOCKER 1" || target == "LOCKER 01" || target == "LOCKER1") {
    return true;
  }
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

  // Command 1: UNLOCK
  if (upperCmd.startsWith("UNLOCK")) {
    unsigned long duration = DEFAULT_UNLOCK_MS;
    bool targetLocker1 = false;
    String lockerPart = "";

    int firstColon = upperCmd.indexOf(':');
    if (firstColon == -1) {
      // Standalone "UNLOCK" (e.g. manual Serial test) -> unlock Locker 1
      targetLocker1 = true;
      lockerPart = "1 (Default)";
    } else {
      int secondColon = upperCmd.indexOf(':', firstColon + 1);
      if (secondColon != -1) {
        // Format: UNLOCK:<locker>:<duration> (e.g. UNLOCK:1:4 or UNLOCK:2:4)
        lockerPart = upperCmd.substring(firstColon + 1, secondColon);
        lockerPart.trim();
        int sec = upperCmd.substring(secondColon + 1).toInt();
        if (sec > 0) duration = (unsigned long)sec * 1000;
        targetLocker1 = isLocker1Targeted(lockerPart);
      } else {
        // Format with 1 colon: UNLOCK:<arg>
        String arg = upperCmd.substring(firstColon + 1);
        arg.trim();
        if (isLocker1Targeted(arg)) {
          targetLocker1 = true;
          lockerPart = arg;
        } else if (arg == "2" || arg == "3" || arg == "4" || arg == "5" || arg.startsWith("LOCKER")) {
          targetLocker1 = false;
          lockerPart = arg;
        } else {
          int sec = arg.toInt();
          if (sec > 0) duration = (unsigned long)sec * 1000;
          targetLocker1 = true;
          lockerPart = "1 (Default)";
        }
      }
    }

    Serial.println("------------------------------------------");
    if (targetLocker1) {
      Serial.print(">> [COMMAND]: UNLOCK request for LOCKER 1 (Duration: ");
      Serial.print(duration / 1000);
      Serial.println("s)");
      Serial.println(">> [MATCH]: Activating Relay Pin D1 for Solenoid Lock 1!");
      unlockLocker(duration);
    } else {
      Serial.print(">> [COMMAND]: UNLOCK request for Locker: [ ");
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
    Serial.println(">> [COMMAND]: LOCK signal received.");
    lockLocker();
    return;
  }

  // Command 3: STATUS / PING
  if (upperCmd == "STATUS" || upperCmd == "PING") {
    Serial.print("STATUS: ");
    Serial.println(isUnlocked ? "UNLOCKED" : "LOCKED");
    return;
  }

  // Command 4: Direct RFID UID
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

// HTTP Webhook Handlers (Optional WiFi mode)
void handleHttpUnlock() {
  unsigned long duration = DEFAULT_UNLOCK_MS;
  if (server.hasArg("duration")) {
    int sec = server.arg("duration").toInt();
    if (sec > 0) duration = (unsigned long)sec * 1000;
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

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF); // Start safely locked

  Serial.println("\n==========================================");
  Serial.println("   SMARTLOCKER ESP8266 CONTROLLER READY   ");
  Serial.println("==========================================");
  Serial.println("Assigned Physical Locker: LOCKER 1 ONLY (Pin D1)");
  Serial.println("Protocol: USB Serial @ 115200 baud");
  Serial.println("Commands: UNLOCK:<locker>:<sec>, UNLOCK:1, LOCK, STATUS");
  Serial.println("Note: Commands for Locker 2, 3, 4, 5 will NOT open Locker 1.");

  if (WIFI_SSID != NULL && strlen(WIFI_SSID) > 0) {
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
      Serial.print("\n>> WiFi Connected! IP: http://");
      Serial.println(WiFi.localIP());
      server.on("/unlock", handleHttpUnlock);
      server.on("/lock", handleHttpLock);
      server.on("/status", handleHttpStatus);
      server.begin();
    }
  }

  Serial.println(">> System Armed. Ready for commands from Website...\n");
}

void loop() {
  if (wifiEnabled) {
    server.handleClient();
  }

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

  // Non-blocking auto-relock
  if (isUnlocked && (millis() - unlockStartTime >= currentUnlockDuration)) {
    lockLocker();
    Serial.println(">> [AUTO-LOCK]: Solenoid de-energized. Locker 1 is now LOCKED.\n");
  }
}
