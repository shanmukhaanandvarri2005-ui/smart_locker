import os
import threading
import time
import logging

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger("smart_locker.hardware")

# Raspberry Pi GPIO Pin Mappings (BCM Mode)
PIN_SOLENOID = 18       # Relay trigger for 12V Solenoid Lock
PIN_DOOR_SENSOR = 23    # MC-38 Magnetic Reed Switch
PIN_IR_SHELF = 24       # IR Sensor 1 (Detects book presence on compartment shelf)
PIN_IR_ENTRANCE = 25    # IR Sensor 2 (Detects movement/passage through locker entrance)
PIN_LED_RED = 17        # RGB LED Red Pin
PIN_LED_GREEN = 27      # RGB LED Green Pin
PIN_LED_BLUE = 22       # RGB LED Blue Pin


class HardwareController:
    """
    Unified hardware controller supporting:
    1. ESP8266 via USB Serial (NodeMCU / Wemos D1 Mini at 115200 baud)
    2. ESP8266 via WiFi HTTP Webhooks (ESP8266_IP in .env)
    3. Raspberry Pi physical GPIO (if deployed on RPi)
    4. Seamless simulation fallback when no physical hardware is plugged in
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.is_rpi = False
        
        # ESP8266 Serial configuration
        self.serial_port_name = os.environ.get('SERIAL_PORT', 'AUTO')
        self.serial_baud = int(os.environ.get('SERIAL_BAUD', '115200'))
        self.ser = None
        self.esp8266_connected = False
        
        # ESP8266 WiFi configuration (optional)
        self.esp8266_ip = os.environ.get('ESP8266_IP', '').strip()
        
        # Locker physical status
        self.solenoid_unlocked = False      # False = LOCKED, True = UNLOCKED
        self.door_open = False              # False = CLOSED, True = OPEN
        self.book_present = True            # True = PRESENT on shelf, False = ABSENT
        self.entrance_passage = False       # True = passage detected
        self.led_color = 'BLUE'             # 'BLUE' (standby), 'GREEN' (active), 'RED' (alert)
        
        self._init_gpio()
        self._init_serial()

    def _init_gpio(self):
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup outputs
            GPIO.setup(PIN_SOLENOID, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_LED_RED, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_LED_GREEN, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_LED_BLUE, GPIO.OUT, initial=GPIO.HIGH)
            
            # Setup inputs with internal pull-up resistors
            GPIO.setup(PIN_DOOR_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_IR_SHELF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_IR_ENTRANCE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.is_rpi = True
            print("[Hardware] Initialized Raspberry Pi GPIO successfully.")
        except (ImportError, RuntimeError):
            self.is_rpi = False

    def _find_esp8266_port(self):
        """Attempts to discover the ESP8266 COM port on Windows/Linux/Mac."""
        if not serial:
            return None

        # If user explicitly defined a port (e.g. SERIAL_PORT=COM3), use that
        if self.serial_port_name and self.serial_port_name.upper() != 'AUTO':
            return self.serial_port_name

        try:
            com_ports = list(serial.tools.list_ports.comports())
            # Search for USB-to-Serial adapters (CH340, CP2102, FTDI, etc.)
            for p in com_ports:
                desc = (p.description or "").lower()
                hwid = (p.hwid or "").lower()
                if "bluetooth" in desc or "bthenum" in hwid:
                    continue
                if any(k in desc or k in hwid for k in ["ch340", "cp210", "ftdi", "usb serial", "usb-serial", "uart", "1a86", "10c4"]):
                    return p.device
            
            # Fallback: first non-bluetooth port
            for p in com_ports:
                desc = (p.description or "").lower()
                if "bluetooth" not in desc:
                    return p.device
        except Exception as e:
            print(f"[Hardware] Port scan error: {e}")
        return None

    def _init_serial(self):
        """Connects to the ESP8266 via USB Serial if available."""
        if not serial:
            return

        port = self._find_esp8266_port()
        if not port:
            self.esp8266_connected = False
            return

        try:
            if self.ser and self.ser.is_open:
                try:
                    self.ser.close()
                except Exception:
                    pass
            self.ser = serial.Serial()
            self.ser.port = port
            self.ser.baudrate = self.serial_baud
            self.ser.timeout = 1.0
            self.ser.dtr = False
            self.ser.rts = False
            self.ser.open()
            self.esp8266_connected = True
            self.serial_port_name = port
            print(f"[Hardware] Connected to ESP8266 on {port} @ {self.serial_baud} baud.", flush=True)
            time.sleep(1.0)
        except serial.SerialException as e:
            self.esp8266_connected = False
            if "PermissionError" in str(e) or "Access is denied" in str(e):
                print(f"[Hardware Alert] Port {port} is LOCKED by another program (e.g. Arduino IDE Serial Monitor)! Please close the Serial Monitor.", flush=True)
            else:
                print(f"[Hardware] ESP8266 serial connect skipped ({port}): {e}", flush=True)
        except Exception as e:
            self.esp8266_connected = False
            print(f"[Hardware] Serial connection error ({port}): {e}", flush=True)

    def _send_serial_command(self, cmd: str):
        """Sends a command to ESP8266 over USB Serial with auto-reconnect."""
        if not serial:
            return False

        with self.lock:
            if not self.ser or not self.ser.is_open:
                self._init_serial()

            if self.ser and self.ser.is_open:
                try:
                    payload = (cmd.strip() + "\r\n").encode('utf-8')
                    self.ser.write(payload)
                    self.ser.flush()
                    print(f"[Hardware -> ESP8266 Serial ({self.serial_port_name})]: {cmd.strip()}", flush=True)
                    return True
                except Exception as e:
                    print(f"[Hardware] Serial write failed: {e}", flush=True)
                    try:
                        self.ser.close()
                    except Exception:
                        pass
                    self.ser = None
                    self.esp8266_connected = False
            else:
                print(f"[Hardware] Cannot send '{cmd}': {self.serial_port_name} is not connected or busy.", flush=True)
        return False

    def _send_wifi_command(self, path: str):
        """Sends an HTTP command to ESP8266 over WiFi if configured."""
        if not requests or not self.esp8266_ip:
            return False
        try:
            url = f"http://{self.esp8266_ip}{path}"
            res = requests.get(url, timeout=2.0)
            print(f"[Hardware -> ESP8266 WiFi ({url})]: status={res.status_code}", flush=True)
            return res.status_code == 200
        except Exception as e:
            print(f"[Hardware] WiFi command failed ({self.esp8266_ip}): {e}", flush=True)
            return False

    def unlock_solenoid(self, duration_sec=4, card_uid=None, locker_ids=None):
        """
        Unlocks the 12V solenoid lock by energizing the relay.
        Only triggers physical Relay Pin D1 if Locker 1 is targeted!
        Controls:
          1. ESP8266 over USB Serial (sends UNLOCK:<lockers>:<duration>)
          2. ESP8266 over WiFi (if configured)
          3. Raspberry Pi GPIO (if on Pi)
        """
        if locker_ids is None:
            lockers_list = [1]
        elif isinstance(locker_ids, (int, str)):
            lockers_list = [locker_ids]
        else:
            lockers_list = list(locker_ids)

        cleaned_ids = []
        for lid in lockers_list:
            s = str(lid).strip()
            digits = ''.join(c for c in s if c.isdigit())
            if digits:
                cleaned_ids.append(str(int(digits)))
            else:
                cleaned_ids.append(s)

        lockers_str = ",".join(cleaned_ids) if cleaned_ids else "1"
        is_locker_1_targeted = any(x == "1" for x in cleaned_ids)

        if is_locker_1_targeted:
            self.solenoid_unlocked = True
            self.set_led('GREEN')
            print(f"[Hardware] Locker 1 TARGETED ({lockers_str}). Solenoid Relay will activate.", flush=True)
        else:
            print(f"[Hardware] Locker 1 NOT targeted ({lockers_str}). Solenoid Relay on Pin D1 will remain LOCKED.", flush=True)

        # 1. RPi GPIO (if on Pi)
        if self.is_rpi and is_locker_1_targeted:
            try:
                import RPi.GPIO as GPIO
                GPIO.output(PIN_SOLENOID, GPIO.HIGH)
            except Exception:
                pass

        # 2. ESP8266 USB Serial Command:
        # Formatted as: UNLOCK:<lockers>:<duration_sec> (e.g. UNLOCK:1:4 or UNLOCK:2:4)
        serial_cmd = f"UNLOCK:{lockers_str}:{duration_sec}"
        self._send_serial_command(serial_cmd)
        if card_uid:
            self._send_serial_command(str(card_uid))

        # 3. ESP8266 WiFi Webhook (if IP configured)
        if self.esp8266_ip:
            threading.Thread(
                target=self._send_wifi_command, 
                args=(f"/unlock?locker={lockers_str}&duration={duration_sec}",), 
                daemon=True
            ).start()

        # Non-blocking auto-relock timer for software state
        if duration_sec and is_locker_1_targeted:
            def auto_relock():
                time.sleep(duration_sec)
                self.lock_solenoid()
            threading.Thread(target=auto_relock, daemon=True).start()

        return True

    def lock_solenoid(self):
        """Secures the solenoid lock and returns status to standby."""
        self.solenoid_unlocked = False
        self.door_open = False
        self.set_led('BLUE')

        if self.is_rpi:
            try:
                import RPi.GPIO as GPIO
                GPIO.output(PIN_SOLENOID, GPIO.LOW)
            except Exception:
                pass

        # Send LOCK command to ESP8266
        self._send_serial_command("LOCK")

        if self.esp8266_ip:
            threading.Thread(target=self._send_wifi_command, args=("/lock",), daemon=True).start()

    def set_led(self, color):
        """Controls the common-cathode RGB status indicator."""
        self.led_color = color.upper()
        if self.is_rpi:
            try:
                import RPi.GPIO as GPIO
                GPIO.output(PIN_LED_RED, GPIO.HIGH if self.led_color == 'RED' else GPIO.LOW)
                GPIO.output(PIN_LED_GREEN, GPIO.HIGH if self.led_color == 'GREEN' else GPIO.LOW)
                GPIO.output(PIN_LED_BLUE, GPIO.HIGH if self.led_color == 'BLUE' else GPIO.LOW)
            except Exception:
                pass

    def read_sensors(self):
        """Polls hardware sensors and ESP8266 controller state."""
        if self.is_rpi:
            try:
                import RPi.GPIO as GPIO
                door_raw = GPIO.input(PIN_DOOR_SENSOR)
                self.door_open = (door_raw == GPIO.HIGH)
                
                shelf_raw = GPIO.input(PIN_IR_SHELF)
                self.book_present = (shelf_raw == GPIO.LOW)
                
                entrance_raw = GPIO.input(PIN_IR_ENTRANCE)
                self.entrance_passage = (entrance_raw == GPIO.LOW)
            except Exception:
                pass

        return {
            "lock_status": "unlocked" if self.solenoid_unlocked else "locked",
            "door_status": "open" if self.door_open else "closed",
            "book_present": self.book_present,
            "entrance_passage": self.entrance_passage,
            "led_indicator": self.led_color,
            "is_physical_rpi": self.is_rpi,
            "esp8266_connected": self.esp8266_connected or bool(self.ser and self.ser.is_open),
            "esp8266_port": self.serial_port_name if self.esp8266_connected else None,
            "esp8266_ip": self.esp8266_ip if self.esp8266_ip else None
        }

hardware = HardwareController()
