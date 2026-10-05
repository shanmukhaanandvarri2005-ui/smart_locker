import threading
import time

# Raspberry Pi GPIO Pin Mappings (BCM Mode)
PIN_SOLENOID = 18       # Relay trigger for 12V Solenoid Lock
PIN_DOOR_SENSOR = 23    # MC-38 Magnetic Reed Switch
PIN_IR_SHELF = 24       # IR Sensor 1 (Detects book presence on compartment shelf)
PIN_IR_ENTRANCE = 25    # IR Sensor 2 (Detects movement/passage through locker entrance)
PIN_LED_RED = 17        # RGB LED Red Pin
PIN_LED_GREEN = 27      # RGB LED Green Pin
PIN_LED_BLUE = 22       # RGB LED Blue Pin

class HardwareController:
    def __init__(self):
        self.lock = threading.Lock()
        self.is_rpi = False
        
        # Locker physical status
        self.solenoid_unlocked = False      # False = LOCKED, True = UNLOCKED
        self.door_open = False              # False = CLOSED, True = OPEN
        self.book_present = True            # True = PRESENT on shelf, False = ABSENT
        self.entrance_passage = False       # True = passage detected
        self.led_color = 'BLUE'             # 'BLUE' (standby), 'GREEN' (active), 'RED' (alert)
        
        self._init_gpio()

    def _init_gpio(self):
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Setup outputs
            GPIO.setup(PIN_SOLENOID, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_LED_RED, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_LED_GREEN, GPIO.OUT, initial=GPIO.LOW)
            GPIO.setup(PIN_LED_BLUE, GPIO.OUT, initial=GPIO.HIGH) # Default blue standby
            
            # Setup inputs with internal pull-up resistors
            GPIO.setup(PIN_DOOR_SENSOR, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_IR_SHELF, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(PIN_IR_ENTRANCE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            self.is_rpi = True
        except (ImportError, RuntimeError):
            self.is_rpi = False

    def unlock_solenoid(self, duration_sec=15):
        """Unlocks the solenoid lock and triggers active green indicator."""
        with self.lock:
            self.solenoid_unlocked = True
            self.set_led('GREEN')
            if self.is_rpi:
                import RPi.GPIO as GPIO
                GPIO.output(PIN_SOLENOID, GPIO.HIGH)

        if duration_sec:
            def auto_relock():
                time.sleep(duration_sec)
                self.lock_solenoid()
            threading.Thread(target=auto_relock, daemon=True).start()

    def lock_solenoid(self):
        """Secures the solenoid lock and returns LED to standby blue."""
        with self.lock:
            self.solenoid_unlocked = False
            self.door_open = False
            self.set_led('BLUE')
            if self.is_rpi:
                import RPi.GPIO as GPIO
                GPIO.output(PIN_SOLENOID, GPIO.LOW)

    def set_led(self, color):
        """Controls the common-cathode RGB status indicator."""
        self.led_color = color.upper()
        if self.is_rpi:
            import RPi.GPIO as GPIO
            GPIO.output(PIN_LED_RED, GPIO.HIGH if self.led_color == 'RED' else GPIO.LOW)
            GPIO.output(PIN_LED_GREEN, GPIO.HIGH if self.led_color == 'GREEN' else GPIO.LOW)
            GPIO.output(PIN_LED_BLUE, GPIO.HIGH if self.led_color == 'BLUE' else GPIO.LOW)

    def read_sensors(self):
        """Polls hardware sensors."""
        if self.is_rpi:
            import RPi.GPIO as GPIO
            # MC-38 Reed Switch: CLOSED when magnet is near (LOW with pull-up to GND)
            door_raw = GPIO.input(PIN_DOOR_SENSOR)
            self.door_open = (door_raw == GPIO.HIGH)
            
            # FC-51 IR Sensors: Output LOW when object detected
            shelf_raw = GPIO.input(PIN_IR_SHELF)
            self.book_present = (shelf_raw == GPIO.LOW)
            
            entrance_raw = GPIO.input(PIN_IR_ENTRANCE)
            self.entrance_passage = (entrance_raw == GPIO.LOW)

        return {
            "lock_status": "unlocked" if self.solenoid_unlocked else "locked",
            "door_status": "open" if self.door_open else "closed",
            "book_present": self.book_present,
            "entrance_passage": self.entrance_passage,
            "led_indicator": self.led_color,
            "is_physical_rpi": self.is_rpi
        }

hardware = HardwareController()
