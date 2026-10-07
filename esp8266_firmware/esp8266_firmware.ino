#include <Arduino.h>
#include <stdint.h>
#include <SPI.h>
#include <MFRC522.h>
#include <Adafruit_NeoPixel.h>
#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>

#ifndef D0
#define D0 16
#define D1 5
#define D2 4
#define D3 0
#define D4 2
#define D5 14
#define D6 12
#define D7 13
#define D8 15
#endif

const char* WIFI_SSID     = "";
const char* WIFI_PASSWORD = "";

#define PIN_RELAY         D1
#define PIN_RGB_DIN       D2
#define PIN_IR_SHELF      D3
#define PIN_IR_ENTRANCE   D4
#define PIN_DOOR_SENSOR   D0
#define PIN_RFID_SS       D8
#define PIN_RFID_RST      UINT8_MAX

#define NUM_LEDS          1
#define DEFAULT_UNLOCK_MS 4000

#define RELAY_ON          LOW
#define RELAY_OFF         HIGH

Adafruit_NeoPixel rgb(NUM_LEDS, PIN_RGB_DIN, NEO_GRB + NEO_KHZ800);
MFRC522 rfid(PIN_RFID_SS, PIN_RFID_RST);
ESP8266WebServer server(80);

bool wifiEnabled = false;
bool isUnlocked = false;
unsigned long unlockStartTime = 0;
unsigned long unlockDuration = DEFAULT_UNLOCK_MS;

bool lastDoorOpen = false;
bool lastBookPresent = false;
bool lastPassage = false;

enum LedMode {
  LED_MODE_AUTO,
  LED_MODE_MANUAL_BLUE,
  LED_MODE_MANUAL_GREEN,
  LED_MODE_MANUAL_RED
};

LedMode currentLedMode = LED_MODE_AUTO;
String serialBuffer = "";

void setRgbColor(uint8_t r, uint8_t g, uint8_t b) {
  rgb.setPixelColor(0, rgb.Color(r, g, b));
  rgb.show();
}

bool readDoorOpen() {
  return digitalRead(PIN_DOOR_SENSOR) == HIGH;
}

bool readBookPresent() {
  return digitalRead(PIN_IR_SHELF) == LOW;
}

bool readEntrancePassage() {
  return digitalRead(PIN_IR_ENTRANCE) == LOW;
}

void updateLedState() {
  if (isUnlocked || currentLedMode == LED_MODE_MANUAL_BLUE) {
    setRgbColor(0, 0, 255);
  } else if (currentLedMode == LED_MODE_MANUAL_GREEN) {
    setRgbColor(0, 255, 0);
  } else if (currentLedMode == LED_MODE_MANUAL_RED) {
    setRgbColor(255, 0, 0);
  } else {
    bool present = readBookPresent();
    if (present) {
      setRgbColor(0, 255, 0);
    } else {
      setRgbColor(255, 0, 0);
    }
  }
}

void unlockLocker(unsigned long durationMs = DEFAULT_UNLOCK_MS) {
  digitalWrite(PIN_RELAY, RELAY_ON);
  isUnlocked = true;
  unlockStartTime = millis();
  unlockDuration = durationMs;
  updateLedState();
  Serial.print(">> [RELAY]: UNLOCKED for ");
  Serial.print(durationMs / 1000);
  Serial.println("s | LED: BLUE");
}

void lockLocker() {
  digitalWrite(PIN_RELAY, RELAY_OFF);
  isUnlocked = false;
  currentLedMode = LED_MODE_AUTO;
  updateLedState();
  Serial.println(">> [RELAY]: LOCKED");
}

void sendFullStatus() {
  bool door = readDoorOpen();
  bool book = readBookPresent();
  bool passage = readEntrancePassage();
  Serial.print("STATUS:DOOR=");
  Serial.print(door ? "OPEN" : "CLOSED");
  Serial.print(",BOOK=");
  Serial.print(book ? "PRESENT" : "EMPTY");
  Serial.print(",PASSAGE=");
  Serial.print(passage ? "DETECTED" : "CLEAR");
  Serial.print(",LOCK=");
  Serial.print(isUnlocked ? "UNLOCKED" : "LOCKED");
  Serial.print(",LED=");
  if (isUnlocked || currentLedMode == LED_MODE_MANUAL_BLUE) Serial.print("BLUE");
  else if (book) Serial.print("GREEN");
  else Serial.print("RED");
  Serial.println();
}

void processCommand(String cmd) {
  cmd.trim();
  String upperCmd = cmd;
  upperCmd.toUpperCase();

  if (upperCmd.startsWith("UNLOCK")) {
    unsigned long dur = DEFAULT_UNLOCK_MS;
    int firstColon = upperCmd.indexOf(':');
    if (firstColon != -1) {
      int secondColon = upperCmd.indexOf(':', firstColon + 1);
      if (secondColon != -1) {
        int s = upperCmd.substring(secondColon + 1).toInt();
        if (s > 0) dur = (unsigned long)s * 1000;
      } else {
        int s = upperCmd.substring(firstColon + 1).toInt();
        if (s > 0) dur = (unsigned long)s * 1000;
      }
    }
    unlockLocker(dur);
    return;
  }

  if (upperCmd == "LOCK") {
    lockLocker();
    return;
  }

  if (upperCmd == "LED:BLUE") {
    currentLedMode = LED_MODE_MANUAL_BLUE;
    updateLedState();
    return;
  }

  if (upperCmd == "LED:GREEN") {
    currentLedMode = LED_MODE_MANUAL_GREEN;
    updateLedState();
    return;
  }

  if (upperCmd == "LED:RED") {
    currentLedMode = LED_MODE_MANUAL_RED;
    updateLedState();
    return;
  }

  if (upperCmd == "LED:AUTO") {
    currentLedMode = LED_MODE_AUTO;
    updateLedState();
    return;
  }

  if (upperCmd == "STATUS" || upperCmd == "PING") {
    sendFullStatus();
    return;
  }
}

void handleHttpUnlock() {
  unsigned long duration = DEFAULT_UNLOCK_MS;
  if (server.hasArg("duration")) {
    int s = server.arg("duration").toInt();
    if (s > 0) duration = (unsigned long)s * 1000;
  }
  unlockLocker(duration);
  server.send(200, "application/json", "{\"success\":true,\"state\":\"unlocked\"}");
}

void handleHttpLock() {
  lockLocker();
  server.send(200, "application/json", "{\"success\":true,\"state\":\"locked\"}");
}

void handleHttpStatus() {
  bool door = readDoorOpen();
  bool book = readBookPresent();
  bool passage = readEntrancePassage();
  String json = "{";
  json += "\"lock\":\"" + String(isUnlocked ? "unlocked" : "locked") + "\",";
  json += "\"door\":\"" + String(door ? "open" : "closed") + "\",";
  json += "\"book\":\"" + String(book ? "present" : "empty") + "\",";
  json += "\"passage\":\"" + String(passage ? "detected" : "clear") + "\"}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PIN_RELAY, OUTPUT);
  digitalWrite(PIN_RELAY, RELAY_OFF);

  pinMode(PIN_DOOR_SENSOR, INPUT_PULLUP);
  pinMode(PIN_IR_SHELF, INPUT);
  pinMode(PIN_IR_ENTRANCE, INPUT);

  rgb.begin();
  rgb.setBrightness(180);
  setRgbColor(0, 0, 255);
  delay(300);

  SPI.begin();
  rfid.PCD_Init();

  updateLedState();

  Serial.println("\n=============================================");
  Serial.println("  SMARTLOCKER INTEGRATED CONTROLLER ONLINE   ");
  Serial.println("=============================================");

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

  lastDoorOpen = readDoorOpen();
  lastBookPresent = readBookPresent();
  lastPassage = readEntrancePassage();

  sendFullStatus();
}

void loop() {
  if (wifiEnabled) {
    server.handleClient();
  }

  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\n' || c == '\r') {
      if (serialBuffer.length() > 0) {
        serialBuffer.trim();
        processCommand(serialBuffer);
        serialBuffer = "";
      }
    } else {
      serialBuffer += c;
    }
  }

  if (isUnlocked && (millis() - unlockStartTime >= unlockDuration)) {
    lockLocker();
  }

  bool curDoorOpen = readDoorOpen();
  if (curDoorOpen != lastDoorOpen) {
    lastDoorOpen = curDoorOpen;
    Serial.print("DOOR:");
    Serial.println(curDoorOpen ? "OPEN" : "CLOSED");
  }

  bool curBookPresent = readBookPresent();
  if (curBookPresent != lastBookPresent) {
    lastBookPresent = curBookPresent;
    Serial.print("BOOK:");
    Serial.println(curBookPresent ? "PRESENT" : "EMPTY");
    updateLedState();
  }

  bool curPassage = readEntrancePassage();
  if (curPassage != lastPassage) {
    lastPassage = curPassage;
    if (curPassage) {
      Serial.println("PASSAGE:DETECTED");
    }
  }

  if (rfid.PICC_IsNewCardPresent() && rfid.PICC_ReadCardSerial()) {
    String uidStr = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      if (rfid.uid.uidByte[i] < 0x10) uidStr += "0";
      uidStr += String(rfid.uid.uidByte[i], HEX);
    }
    uidStr.toUpperCase();
    Serial.print("RFID:");
    Serial.println(uidStr);
    rfid.PICC_HaltA();
    rfid.PCD_StopCrypto1();
  }

  delay(25);
}
