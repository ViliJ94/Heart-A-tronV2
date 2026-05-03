"""Timer-based ADC handler with FIFO-like circular buffer for deterministic sampling."""

import time
from machine import ADC, Pin, Timer

try:
    import config as cfg
except ImportError:
    cfg = None


class CircularBuffer:
    """Non-blocking FIFO-like circular buffer."""

    def __init__(self, size=256):
        self.size = size
        self.buffer = [0] * size
        self.write_idx = 0
        self.read_idx = 0
        self.count = 0
        self.overflow_count = 0

    def write(self, value):
        """Write to buffer; silently overwrite oldest if full."""
        self.buffer[self.write_idx] = value
        self.write_idx = (self.write_idx + 1) % self.size
        
        if self.count < self.size:
            self.count += 1
        else:
            # Overflow: drop oldest sample
            self.read_idx = (self.read_idx + 1) % self.size
            self.overflow_count += 1

    def read(self):
        """Read from buffer; returns (value, None) if empty."""
        if self.count == 0:
            return None
        
        value = self.buffer[self.read_idx]
        self.read_idx = (self.read_idx + 1) % self.size
        self.count -= 1
        return value

    def is_empty(self):
        return self.count == 0

    def available(self):
        return self.count

    def clear(self):
        self.write_idx = 0
        self.read_idx = 0
        self.count = 0


class PIOADCHandler:
    """
    Deterministic ADC sampling using Timer for precise 250 Hz trigger.
    Samples buffered in circular FIFO for non-blocking main loop consumption.
    """

    def __init__(self, adc_pin=26, sample_rate_hz=250, buffer_size=256):
        """
        Initialize timer-based ADC handler.
        
        Args:
            adc_pin: GPIO pin for ADC input (default 26 = ADC0)
            sample_rate_hz: Sampling frequency in Hz (default 250)
            buffer_size: Circular buffer capacity (default 256)
        """
        self.adc_pin = adc_pin
        self.sample_rate_hz = sample_rate_hz
        self.sample_period_ms = max(1, int(1000 / sample_rate_hz))
        self.buffer_size = buffer_size
        
        # Circular buffer for samples
        self.buffer = CircularBuffer(buffer_size)
        
        # Timing
        self._sample_count = 0
        self._start_time_ms = 0
        self._last_sample_time_ms = 0
        self._timer = None
        self._adc = None
        self._enabled = False
        
        # Debug stats
        self.total_samples_captured = 0
        self.total_samples_read = 0
        
        self._init_adc()
        print(f"[PIO_ADC] Handler initialized: {sample_rate_hz} Hz, {buffer_size}-entry buffer, ADC pin {adc_pin}")

    def _init_adc(self):
        """Initialize ADC on specified pin."""
        try:
            self._adc = ADC(Pin(self.adc_pin))
            print(f"[PIO_ADC] ADC initialized on pin {self.adc_pin}")
        except Exception as e:
            print(f"[PIO_ADC] ERROR initializing ADC: {e}")
            self._adc = None

    def _timer_callback(self, timer):
        """Called every sample_period_ms by Timer interrupt."""
        if not self._adc:
            return
        
        try:
            # Read ADC sample
            sample = self._adc.read_u16()
            
            # Push to buffer
            self.buffer.write(sample)
            self._sample_count += 1
            self.total_samples_captured += 1
            self._last_sample_time_ms = time.ticks_ms()
            
        except Exception as e:
            print(f"[PIO_ADC] Timer callback error: {e}")

    def start(self):
        """Start deterministic sampling."""
        if self._enabled:
            return
        
        if not self._adc:
            print("[PIO_ADC] ERROR: ADC not initialized, cannot start")
            return
        
        try:
            self._sample_count = 0
            self._start_time_ms = time.ticks_ms()
            self._last_sample_time_ms = self._start_time_ms
            self.buffer.clear()
            
            # Initialize Timer (Timer 1 is typically available)
            # Mode 0 = repeat mode (periodic interrupt)
            self._timer = Timer(-1)  # -1 = allocate free timer
            self._timer.init(
                period=self.sample_period_ms,
                mode=Timer.PERIODIC,
                callback=self._timer_callback
            )
            
            self._enabled = True
            print(f"[PIO_ADC] Sampling started at {self.sample_rate_hz} Hz ({self.sample_period_ms}ms period)")
        except Exception as e:
            print(f"[PIO_ADC] ERROR starting timer: {e}")
            self._enabled = False

    def stop(self):
        """Stop sampling."""
        if self._timer:
            self._timer.deinit()
            self._timer = None
        self._enabled = False
        print(f"[PIO_ADC] Sampling stopped. Total samples: {self.total_samples_captured}")

    def read_sample(self):
        """
        Non-blocking read of one sample from buffer.
        
        Returns:
            Sample value (0-65535) if available, None otherwise
        """
        return self.buffer.read()

    def read_available(self):
        """
        Read all available samples from buffer.
        
        Returns:
            List of samples; empty list if buffer empty
        """
        samples = []
        while not self.buffer.is_empty():
            sample = self.buffer.read()
            if sample is not None:
                samples.append(sample)
                self.total_samples_read += 1
        return samples

    def available_count(self):
        """Return number of samples waiting in buffer."""
        return self.buffer.available()

    def get_stats(self):
        """Return debug statistics."""
        elapsed_ms = time.ticks_diff(self._last_sample_time_ms, self._start_time_ms) if self._start_time_ms else 0
        expected_samples = max(1, int((elapsed_ms + 1) / self.sample_period_ms))
        overflows = self.buffer.overflow_count
        
        return {
            "enabled": self._enabled,
            "sample_count": self._sample_count,
            "total_captured": self.total_samples_captured,
            "total_read": self.total_samples_read,
            "buffer_available": self.available_count(),
            "buffer_size": self.buffer_size,
            "overflow_events": overflows,
            "elapsed_ms": elapsed_ms,
            "expected_samples": expected_samples,
            "sample_rate_hz": self.sample_rate_hz,
        }

    def is_running(self):
        """Check if sampling is active."""
        return self._enabled
