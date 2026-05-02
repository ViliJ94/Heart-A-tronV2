"""Sensor manager with non-blocking inputs and LED pulse."""

import time
from machine import Pin, ADC

try:
    import config as cfg
except ImportError:
    cfg = None


class SensorManager:
    """Manage buttons, PPG ADC sampling, and heartbeat LED."""

    def __init__(self):
        self.button_pins = {
            "SW0": getattr(cfg, "BUTTON_SELECT_PIN", 9),
            "SW1": getattr(cfg, "BUTTON_UP_PIN", 8),
            "SW2": getattr(cfg, "BUTTON_DOWN_PIN", 7),
        }
        self.debounce_ms = getattr(cfg, "BUTTON_DEBOUNCE_MS", 20)
        self.led_pin = getattr(cfg, "LED_HEARTBEAT_PIN", 20)
        self.ppg_pin = getattr(cfg, "PPG_SENSOR_ADC_PIN", 26)

        self.buttons = {}
        self._last_raw_state = {}
        self._last_change_ms = {}
        self._stable_state = {}
        self.led = None
        self.adc = None
        self._led_off_at_ms = 0

        self._init_buttons()
        self._init_led()
        self._init_adc()
        print("[SENSOR] Sensor manager ready")

    def _init_buttons(self):
        for name, pin_num in self.button_pins.items():
            self.buttons[name] = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            current = self.buttons[name].value()
            now = time.ticks_ms()
            self._last_raw_state[name] = current
            self._stable_state[name] = current
            self._last_change_ms[name] = now

    def _init_led(self):
        self.led = Pin(self.led_pin, Pin.OUT)
        self.led.off()

    def _init_adc(self):
        self.adc = ADC(Pin(self.ppg_pin))

    def poll_buttons(self):
        """Return edge events: SELECT, BACK, NEXT."""
        now = time.ticks_ms()
        events = []
        for name, pin in self.buttons.items():
            raw = pin.value()
            if raw != self._last_raw_state[name]:
                self._last_raw_state[name] = raw
                self._last_change_ms[name] = now
            if time.ticks_diff(now, self._last_change_ms[name]) < self.debounce_ms:
                continue
            if raw != self._stable_state[name]:
                self._stable_state[name] = raw
                if raw == 0:
                    if name == "SW0":
                        events.append("SELECT")
                    elif name == "SW1":
                        events.append("BACK")
                    elif name == "SW2":
                        events.append("NEXT")
        return events

    # -------------------------------------------------------------------------
    # Compatibility wrappers (Main.py expects these names / semantics)
    # -------------------------------------------------------------------------

    def get_button_input(self):
        """
        Return a single high-level action string or None.

        Main.py expects: SELECT, UP, DOWN, BACK, STOP in different screens.
        We map physical buttons:
          SW0 -> SELECT
          SW1 -> UP (also used as STOP/BACK depending on screen)
          SW2 -> DOWN
        """
        events = self.poll_buttons()
        if not events:
            return None
        # prefer SELECT if present
        if "SELECT" in events:
            return "SELECT"
        # poll_buttons emits BACK for SW1 and NEXT for SW2; map to UP/DOWN
        if "BACK" in events:
            return "UP"
        if "NEXT" in events:
            return "DOWN"
        return events[0]

    def get_all_sensor_values(self):
        """Best-effort snapshot used by Main.py debug prints."""
        try:
            buttons = {
                "BTN0": self.buttons["SW0"].value(),
                "BTN1": self.buttons["SW1"].value(),
                "BTN2": self.buttons["SW2"].value(),
            }
        except Exception:
            buttons = {}
        return {"buttons": buttons, "ppg": self.get_ppg_sample()}

    def get_ppg_sample(self):
        return self.adc.read_u16() if self.adc else 0

    def trigger_led_pulse(self, duration_ms=50):
        if not self.led:
            return
        self.led.on()
        self._led_off_at_ms = time.ticks_add(time.ticks_ms(), duration_ms)

    def update(self):
        """Keep non-blocking peripherals in sync."""
        if self.led and self._led_off_at_ms:
            if time.ticks_diff(time.ticks_ms(), self._led_off_at_ms) >= 0:
                self.led.off()
                self._led_off_at_ms = 0
