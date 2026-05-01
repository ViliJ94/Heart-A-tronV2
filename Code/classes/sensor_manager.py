"""
Sensor Manager - Handles button input, ADC sampling for PPG sensor
"""

import machine
import time
from machine import Pin, ADC


class SensorManager:
    """Manages all sensor inputs including buttons and PPG ADC"""
    
    # GPIO pin configurations
    BUTTON0_PIN = 12  # SW0 - GP9(12)
    BUTTON1_PIN = 11  # SW1 - GP8(11)  
    BUTTON2_PIN = 10  # SW2 - GP7(10)
    BUTTON_RESET_PIN = 30  # RESET - Run(30)
    
    LED_HEARTBEAT_PIN = 20  # D3 - GP20
    
    PPG_SENSOR_PIN = 26  # ADC_0 - GP26
    
    # Button debounce time in milliseconds
    DEBOUNCE_MS = 20
    
    def __init__(self):
        """Initialize all sensors"""
        self.buttons = {}
        self.led = None
        self.adc = None
        self.last_button_press_time = 0
        self.last_pressed_button = None
        
        self._init_buttons()
        self._init_led()
        self._init_ppg_adc()
        
        print("[SENSOR] Sensor manager initialized")
    
    def _init_buttons(self):
        """Initialize button input pins"""
        try:
            button_pins = {
                "BTN0": self.BUTTON0_PIN,
                "BTN1": self.BUTTON1_PIN,
                "BTN2": self.BUTTON2_PIN,
            }
            
            for btn_name, pin_num in button_pins.items():
                try:
                    self.buttons[btn_name] = Pin(pin_num, Pin.IN, Pin.PULL_UP)
                    print(f"[SENSOR] Button {btn_name} initialized on GP{pin_num}")
                except Exception as e:
                    print(f"[SENSOR] Warning: Could not init {btn_name}: {e}")
            
        except Exception as e:
            print(f"[SENSOR] Error initializing buttons: {e}")
    
    def _init_led(self):
        """Initialize heartbeat LED"""
        try:
            self.led = Pin(self.LED_HEARTBEAT_PIN, Pin.OUT)
            self.led.off()
            print(f"[SENSOR] LED initialized on GP{self.LED_HEARTBEAT_PIN}")
        except Exception as e:
            print(f"[SENSOR] Error initializing LED: {e}")
    
    def _init_ppg_adc(self):
        """Initialize PPG sensor ADC input"""
        try:
            self.adc = ADC(Pin(self.PPG_SENSOR_PIN))
            print(f"[SENSOR] PPG ADC initialized on GP{self.PPG_SENSOR_PIN}")
        except Exception as e:
            print(f"[SENSOR] Error initializing PPG ADC: {e}")
    
    def get_button_input(self):
        """
        Check for button press and return action
        Returns: "SELECT", "UP", "DOWN", "BACK", "STOP", None
        """
        try:
            current_time = time.ticks_ms()
            
            # Debounce check
            if current_time - self.last_button_press_time < self.DEBOUNCE_MS:
                return None
            
            # Check each button
            if "BTN0" in self.buttons:
                if self.buttons["BTN0"].value() == 0:  # Active low
                    self.last_button_press_time = current_time
                    return "SELECT"
            
            if "BTN1" in self.buttons:
                if self.buttons["BTN1"].value() == 0:
                    self.last_button_press_time = current_time
                    return "UP"
            
            if "BTN2" in self.buttons:
                if self.buttons["BTN2"].value() == 0:
                    self.last_button_press_time = current_time
                    return "DOWN"
            
            return None
            
        except Exception as e:
            print(f"[SENSOR] Error reading button: {e}")
            return None
    
    def get_ppg_sample(self):
        """
        Read one sample from PPG sensor
        Returns: ADC value (0-65535)
        """
        try:
            if self.adc:
                return self.adc.read_u16()
            return 0
        except Exception as e:
            print(f"[SENSOR] Error reading PPG: {e}")
            return 0
    
    def get_ppg_samples_buffered(self, count):
        """
        Read multiple PPG samples
        Returns: list of ADC values
        """
        try:
            if not self.adc:
                return []
            
            samples = []
            for _ in range(count):
                samples.append(self.adc.read_u16())
            return samples
            
        except Exception as e:
            print(f"[SENSOR] Error reading PPG buffer: {e}")
            return []
    
    def set_heartbeat_led(self, state):
        """
        Set heartbeat LED on/off
        Used to indicate detected heartbeat
        """
        try:
            if self.led:
                if state:
                    self.led.on()
                else:
                    self.led.off()
        except Exception as e:
            print(f"[SENSOR] Error controlling LED: {e}")
    
    def pulse_led(self, duration_ms=100):
        """Pulse the heartbeat LED"""
        try:
            if self.led:
                self.led.on()
                time.sleep_ms(duration_ms)
                self.led.off()
        except Exception as e:
            print(f"[SENSOR] Error pulsing LED: {e}")
    
    def get_all_sensor_values(self):
        """Get raw values of all sensors for debugging"""
        status = {
            "buttons": {},
            "ppg": self.get_ppg_sample(),
            "timestamp": time.time()
        }
        
        for btn_name, btn_obj in self.buttons.items():
            try:
                status["buttons"][btn_name] = btn_obj.value()
            except:
                pass
        
        return status
