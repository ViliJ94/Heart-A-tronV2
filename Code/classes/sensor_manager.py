"""Sensor manager with non-blocking inputs and LED pulse."""

import time
from machine import Pin, ADC

try:
    import config as cfg
except ImportError:
    cfg = None

try:
    from classes.pio_adc_handler import PIOADCHandler
except ImportError:
    PIOADCHandler = None


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
        self.sample_rate_hz = getattr(cfg, "SAMPLE_RATE_HZ", 250)

        self.buttons = {}
        self._last_raw_state = {}
        self._last_change_ms = {}
        self._stable_state = {}
        self.led = None
        self.adc = None  # Legacy; kept for compatibility
        self.pio_handler = None
        self._led_off_at_ms = 0
        
        # Local buffer for PIO samples (refilled each main loop cycle)
        self._sample_buffer = []
        self._buffer_index = 0

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

    def _refill_local_buffer(self):
        """Pull all pending samples from PIO FIFO into local buffer."""
        if self.pio_handler is None:
            return
        
        try:
            pending = self.pio_handler.read_available()
            if pending:
                self._sample_buffer.extend(pending)
                self._buffer_index = 0  # Reset read index when new data arrives
        except Exception as e:
            print(f"[SENSOR] Error refilling buffer: {e}")

    def _init_adc(self):
        """Initialize PIO-based ADC handler for deterministic sampling."""
        if PIOADCHandler is None:
            print("[SENSOR] WARNING: PIOADCHandler not available, falling back to direct ADC")
            self.adc = ADC(Pin(self.ppg_pin))
            return
        
        try:
            self.pio_handler = PIOADCHandler(
                adc_pin=self.ppg_pin,
                sample_rate_hz=self.sample_rate_hz,
                buffer_size=256
            )
            self.pio_handler.start()
            self._sample_buffer = []
            self._buffer_index = 0
            print("[SENSOR] PIO ADC handler initialized and started")
        except Exception as e:
            print(f"[SENSOR] ERROR initializing PIO handler: {e}, falling back to direct ADC")
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
        """
        Get single PPG sample (non-blocking).
        
        If PIO handler is running, returns from local buffer.
        Otherwise falls back to direct ADC read for compatibility.
        """
        # Refill local buffer from PIO FIFO
        self._refill_local_buffer()
        
        # Try to return from local buffer
        if self._sample_buffer and self._buffer_index < len(self._sample_buffer):
            sample = self._sample_buffer[self._buffer_index]
            self._buffer_index += 1
            return sample
        
        # Fallback to direct ADC if no PIO or buffer empty
        if self.adc:
            return self.adc.read_u16()
        
        return 0

    def trigger_led_pulse(self, duration_ms=50):
        if not self.led:
            return
        self.led.on()
        self._led_off_at_ms = time.ticks_add(time.ticks_ms(), duration_ms)

    def update(self):
        """Keep non-blocking peripherals in sync."""
        # Refill sample buffer from PIO
        self._refill_local_buffer()
        
        # Handle LED timing
        if self.led and self._led_off_at_ms:
            if time.ticks_diff(time.ticks_ms(), self._led_off_at_ms) >= 0:
                self.led.off()
                self._led_off_at_ms = 0
