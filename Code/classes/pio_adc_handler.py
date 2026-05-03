"""
PIO-based ADC handler using Filefifo and Piotimer for deterministic, interrupt-driven sampling.
"""

import machine
import array
from machine import ADC, Pin
from Reference_code.filefifo import Filefifo
from Reference_code.piotimer import Piotimer

class PIOADCHandler:
    """
    Deterministic ADC sampling using Piotimer (PIO-based timer) and Filefifo (interrupt-safe FIFO).
    Samples are pushed to Filefifo in the timer interrupt, and read by the main loop.
    """
    def __init__(self, adc_pin=26, sample_rate_hz=250, fifo_size=256):
        self.adc_pin = adc_pin
        self.sample_rate_hz = sample_rate_hz
        self.fifo_size = fifo_size
        self._adc = ADC(Pin(self.adc_pin))
        self._fifo = Filefifo(fifo_size, 'H')
        self._timer = None
        self._last_sample = 0
        self._enabled = False

    def _adc_isr(self, t=None):
        # Read ADC and put into FIFO (interrupt context)
        try:
            value = self._adc.read_u16()
            self._fifo.put(value)
            self._last_sample = value
        except Exception as e:
            # If FIFO is full, just drop sample
            pass

    def start(self):
        if self._enabled:
            return
        # Piotimer: freq in Hz, callback is ISR
        self._timer = Piotimer(mode=Piotimer.PERIODIC, freq=self.sample_rate_hz, callback=self._adc_isr)
        self._enabled = True

    def stop(self):
        if self._timer:
            self._timer.deinit()
            self._timer = None
        self._enabled = False

    def read_sample(self):
        # Non-blocking read of one sample from FIFO
        try:
            return self._fifo.get()
        except Exception:
            return self._last_sample  # If empty, return last value

    def read_available(self, max_samples=32):
        # Read up to max_samples from FIFO
        samples = []
        for _ in range(max_samples):
            try:
                samples.append(self._fifo.get())
            except Exception:
                break
        return samples

    def available_count(self):
        # Return number of samples waiting in FIFO (approximate)
        # Filefifo does not provide direct count, so we can only check has_data
        count = 0
        while self._fifo.has_data():
            try:
                self._fifo.get()
                count += 1
            except Exception:
                break
        return count

    def get_stats(self):
        return {
            "enabled": self._enabled,
            "fifo_dropped": self._fifo.dropped(),
            "last_sample": self._last_sample,
        }

    def is_running(self):
        return self._enabled
