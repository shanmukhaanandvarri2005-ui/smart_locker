/*
 * SmartLocker ESP8266 Multi-Locker Controller Firmware (5 Lockers)
 * -----------------------------------------------------------------
 * Hardware Configuration:
 *   - ESP8266 (NodeMCU v2/v3 or Wemos D1 Mini)
 *   - Locker 1 (Existing Physical Prototype): Pin D1 (GPIO 5) -> 12V Solenoid Lock
 *   - Locker 2: Pin D2 (GPIO 4)  -> [Virtual / Ready for future hardware]
 *   - Locker 3: Pin D5 (GPIO 14) -> [Virtual / Ready for future hardware]
 *   - Locker 4: Pin D6 (GPIO 12) -> [Virtual / Ready for future hardware]
 *   - Locker 5: Pin D7 (GPIO 13) -> [Virtual / Ready for future hardware]
 *
 * Prototype Behavior:
 *   - Borrowing Book 1 (Locker 1): Activates physical relay on Pin D1.
 *   - Borrowing Books 2, 3, 4, 5: Marked as Virtual (no hardware attached),
 *     so Locker 1 solenoid will NEVER open for other books!
 *   - When you add more physical relays later, simply set HAS_PHYSICAL_HARDWARE
 *     to true for that locker!
 *
 * Wiring (Locker 1):
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

#define TOTAL_LOCKERS     5
#define DEFAULT_UNLOCK_MS 4000  // Default unlock duration: 4 seconds

// Active-LOW relay definitions (standard Arduino/ESP relay modules)
#define RELAY_ON          LOW
#define RELAY_OFF         HIGH

// GPIO Pin mappings for all 5 lockers
#define PIN_LOCKER_1      D1   // GPIO 5  -> Locker 1 (PHYSICAL SOLENOID)
#define PIN_LOCKER_2      D2   // GPIO 4  -> Locker 2 (Virtual / Future)
#define PIN_LOCKER_3      D5   // GPIO 14 -> Locker 3 (Virtual / Future)
#define PIN_LOCKER_4      D6   // GPIO 12 -> Locker 4 (Virtual / Future)
#define PIN_LOCKER_5      D7   // GPIO 13 -> Locker 5 (Virtual / Future)

// Hardware presence toggle:
// Only Locker 1 has a physical solenoid attached right now!
const bool HAS_PHYSICAL_HARDWARE[TOTAL_LOCKERS] = {
  true,   // Locker 1: TRUE  (Physical solenoid on Pin D1)
  false,  // Locker 2: FALSE (Virtual locker - no solenoid)
  false,  // Locker 3: FALSE (Virtual locker - no solenoid)
  false,  // Locker 4: FALSE (Virtual locker - no solenoid)
  false   // Locker 5: FALSE (Virtual locker - no solenoid)
};

const uint8_t LOCKER_PINS[TOTAL_LOCKERS] = {
  PIN_LOCKER_1,
  PIN_LOCKER_2,
  PIN_LOCKER_3,
  PIN_LOCKER_4,
  PIN_LOCKER_5
};

// ======================================================

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

bool isLockerUnlocked[TOTAL_LOCKERS] = {false, false, false, false, false};
unsigned long unlockStartTime[TOTAL_LOCKERS] = {0, 0, 0, 0, 0};
unsigned long unlockDuration[TOTAL_LOCKERS] = {DEFAULT_UNLOCK_MS, DEFAULT_UNLOCK_MS, DEFAULT_UNLOCK_MS, DEFAULT_UNLOCK_MS, DEFAULT_UNLOCK_MS};
String serialInput = "";

ESP8266WebServer server(80);
bool wifiEnabled = false;

// Hardware Control Functions
void unlockSingleLocker(int lockerIndex, unsigned long durationMs = DEFAULT_UNLOCK_MS) {
  if (lockerIndex < 0 || lockerIndex >= TOTAL_LOCKERS) return;

  int lockerNum = lockerIndex + 1;

  if (HAS_PHYSICAL_HARDWARE[lockerIndex]) {
    // Physical hardware exists for this locker!
    digitalWrite(LOCKER_PINS[lockerIndex], RELAY_ON);
    isLockerUnlocked[lockerIndex] = true;
    unlockStartTime[lockerIndex] = millis();
    unlockDuration[lockerIndex] = durationMs;

    Serial.print(">> [LOCKER ");
    Serial.print(lockerNum);
    Serial.print("]: PHYSICAL RELAY ACTIVATED on Pin ");
    Serial.print(lockerIndex == 0 ? "D1" : String(LOCKER_PINS[lockerIndex]));
    Serial.print(" for ");
    Serial.print(durationMs / 1000);
    Serial.println(" seconds!");
  } else {
    // Virtual locker - no physical solenoid attached
    isLockerUnlocked[lockerIndex] = false;
    Serial.print(">> [LOCKER ");
    Serial.print(lockerNum);
    Serial.println("]: VIRTUAL COMPARTMENT (No physical solenoid installed yet).");
    Serial.println(">> [PROTECTION]: Locker 1 physical solenoid stays safely LOCKED.");
  }
}

void lockSingleLocker(int lockerIndex) {
  if (lockerIndex < 0 || lockerIndex >= TOTAL_LOCKERS) return;
  if (HAS_PHYSICAL_HARDWARE[lockerIndex]) {
    digitalWrite(LOCKER_PINS[lockerIndex], RELAY_OFF);
  }
  isLockerUnlocked[lockerIndex] = false;
}

void lockAllLockers() {
  for (int i = 0; i < TOTAL_LOCKERS; i++) {
    lockSingleLocker(i);
  }
  Serial.println(">> [HARDWARE]: All lockers securely LOCKED.");
}

// Parses list of lockers (e.g. "1", "2", "1,2", "3,5") and triggers each
void handleUnlockRequest(String lockerTargetStr, unsigned long durationMs) {
  lockerTargetStr.trim();
  lockerTargetStr.toUpperCase();

  Serial.println("==========================================");
  Serial.print(">> [COMMAND RECEIVED]: UNLOCK request for: [ ");
  Serial.print(lockerTargetStr);
  Serial.print(" ] Duration: ");
  Serial.print(durationMs / 1000);
  Serial.println("s");

  // Check which lockers (1 to 5) are requested
  bool anyLockerMatched = false;
  for (int num = 1; num <= TOTAL_LOCKERS; num++) {
    String numStr = String(num);
    String numPadded = (num < 10) ? ("0" + numStr) : numStr;
    String nameStr = "LOCKER " + numStr;
    String namePadded = "LOCKER " + numPadded;

    bool isTargeted = false;
    if (lockerTargetStr == numStr || lockerTargetStr == numPadded ||
        lockerTargetStr == nameStr || lockerTargetStr == namePadded) {
      isTargeted = true;
    } else if (lockerTargetStr.startsWith(numStr + ",") || lockerTargetStr.endsWith("," + numStr) || lockerTargetStr.indexOf("," + numStr + ",") != -1) {
      isTargeted = true;
    } else if (lockerTargetStr.startsWith(numPadded + ",") || lockerTargetStr.endsWith("," + numPadded) || lockerTargetStr.indexOf("," + numPadded + ",") != -1) {
      isTargeted = true;
    }

    if (isTargeted) {
      anyLockerMatched = true;
      unlockSingleLocker(num - 1, durationMs);
    }
  }

  // If no specific locker matched but command was generic "UNLOCK"
  if (!anyLockerMatched && (lockerTargetStr == "" || lockerTargetStr == "ALL" || lockerTargetStr == "1 (DEFAULT)")) {
    unlockSingleLocker(0, durationMs); // Default prototype Locker 1
  }

  Serial.println("==========================================\n");
}

void processCommand(String cmd) {
  cmd.trim();
  String upperCmd = cmd;
  upperCmd.toUpperCase();

  // Command 1: UNLOCK Commands
  // Accepted formats:
  //   - UNLOCK:1:4        -> Unlock Locker 1 (Physical opens!)
  //   - UNLOCK:2:4        -> Target Locker 2 (Virtual - Locker 1 stays locked!)
  //   - UNLOCK:1,3:6      -> Multiple lockers (Locker 1 opens, Locker 3 is virtual)
  //   - UNLOCK:2,4:6      -> Locker 1 stays completely locked!
  //   - UNLOCK:1          -> Unlock Locker 1 (default 4s)
  //   - UNLOCK            -> Manual test trigger for Locker 1
  if (upperCmd.startsWith("UNLOCK")) {
    unsigned long duration = DEFAULT_UNLOCK_MS;
    String lockerPart = "";

    int firstColon = upperCmd.indexOf(':');
    if (firstColon == -1) {
      // Standalone "UNLOCK"
      lockerPart = "1 (Default)";
    } else {
      int secondColon = upperCmd.indexOf(':', firstColon + 1);
      if (secondColon != -1) {
        // Format: UNLOCK:<lockers>:<duration>
        lockerPart = upperCmd.substring(firstColon + 1, secondColon);
        int sec = upperCmd.substring(secondColon + 1).toInt();
        if (sec > 0) duration = (unsigned long)sec * 1000;
      } else {
        // Format: UNLOCK:<arg>
        String arg = upperCmd.substring(firstColon + 1);
        arg.trim();
        int sec = arg.toInt();
        // If arg is a pure number greater than TOTAL_LOCKERS, it's duration (e.g. UNLOCK:4)
        if (sec > TOTAL_LOCKERS) {
          duration = (unsigned long)sec * 1000;
          lockerPart = "1 (Default)";
        } else {
          lockerPart = arg;
        }
      }
    }

    handleUnlockRequest(lockerPart, duration);
    return;
  }

  // Command 2: LOCK
  if (upperCmd == "LOCK") {
    Serial.println(">> [COMMAND]: Manual LOCK signal received.");
    lockAllLockers();
    return;
  }

  // Command 3: STATUS / PING
  if (upperCmd == "STATUS" || upperCmd == "PING") {
    Serial.print("STATUS: ");
    for (int i = 0; i < TOTAL_LOCKERS; i++) {
      Serial.print("L");
      Serial.print(i + 1);
      Serial.print("=");
      Serial.print(isLockerUnlocked[i] ? "UNLOCKED" : "LOCKED");
      if (i < TOTAL_LOCKERS - 1) Serial.print(", ");
    }
    Serial.println();
    return;
  }

  // Any raw card UID or unrecognized text is safely IGNORED
  Serial.println("------------------------------------------");
  Serial.print(">> [IGNORED]: Input received: [ ");
  Serial.print(cmd);
  Serial.println(" ]");
  Serial.println(">> [NOTICE]: Relays trigger only on explicit 'UNLOCK:<id>' commands.");
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

  handleUnlockRequest(locker, duration);
  server.send(200, "application/json", "{\"success\":true,\"locker\":\"" + locker + "\",\"duration_ms\":" + String(duration) + "}");
}

void handleHttpLock() {
  lockAllLockers();
  server.send(200, "application/json", "{\"success\":true,\"state\":\"all_locked\"}");
}

void handleHttpStatus() {
  String json = "{\"lockers\":{";
  for (int i = 0; i < TOTAL_LOCKERS; i++) {
    json += "\"" + String(i + 1) + "\":\"" + (isLockerUnlocked[i] ? "unlocked" : "locked") + "\"";
    if (i < TOTAL_LOCKERS - 1) json += ",";
  }
  json += "}}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  // Initialize all 5 locker output pins safely locked
  for (int i = 0; i < TOTAL_LOCKERS; i++) {
    pinMode(LOCKER_PINS[i], OUTPUT);
    digitalWrite(LOCKER_PINS[i], RELAY_OFF);
  }

  Serial.println("\n==================================================");
  Serial.println("   SMARTLOCKER 5-COMPARTMENT CONTROLLER READY    ");
  Serial.println("==================================================");
  Serial.println("Compartment Hardware Map:");
  Serial.println("  - Locker 1: Pin D1 [ACTIVE PHYSICAL SOLENOID]");
  Serial.println("  - Locker 2: Pin D2 [VIRTUAL - Hardware Not Installed]");
  Serial.println("  - Locker 3: Pin D5 [VIRTUAL - Hardware Not Installed]");
  Serial.println("  - Locker 4: Pin D6 [VIRTUAL - Hardware Not Installed]");
  Serial.println("  - Locker 5: Pin D7 [VIRTUAL - Hardware Not Installed]");
  Serial.println("Communication: USB Serial @ 115200 baud");
  Serial.println("Commands: UNLOCK:<id>:<sec>, UNLOCK:1, LOCK, STATUS");
  Serial.println("Behavior: Books 2, 3, 4, 5 will NEVER open Locker 1!");

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

  // Non-blocking auto-relock timers for each locker independently
  for (int i = 0; i < TOTAL_LOCKERS; i++) {
    if (isLockerUnlocked[i] && (millis() - unlockStartTime[i] >= unlockDuration[i])) {
      lockSingleLocker(i);
      Serial.print(">> [AUTO-LOCK]: Locker ");
      Serial.print(i + 1);
      Serial.println(" re-locked.\n");
    }
  }
}
