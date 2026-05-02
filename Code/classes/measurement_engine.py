"""Deterministic signal processing and HRV metrics."""

import time
import math

try:
    import config as cfg
except ImportError:
    cfg = None


class MeasurementEngine:
    """Process samples with non-blocking, event-driven updates."""

    def __init__(self, sensor_manager):
        self.sensor = sensor_manager
        self.sample_rate = getattr(cfg, "SAMPLE_RATE_HZ", 250)
        self.sample_period_ms = max(1, int(1000 / self.sample_rate))
        self.min_peak_distance = getattr(cfg, "MIN_PEAK_DISTANCE_SAMPLES", 30)
        self.min_peak_height = getattr(cfg, "MIN_PEAK_HEIGHT", 100)
        self.min_hr = getattr(cfg, "MIN_HEART_RATE_BPM", 40)
        self.max_hr = getattr(cfg, "MAX_HEART_RATE_BPM", 200)
        self.min_collection_seconds = getattr(cfg, "MIN_COLLECTION_TIME_SECONDS", 30)
        self.min_rr_for_hrv = getattr(cfg, "MIN_RR_INTERVALS_FOR_HRV", 30)
        self.max_rr = getattr(cfg, "MAX_RR_INTERVALS", 256)

        self._alpha = getattr(cfg, "FILTER_ALPHA", 0.95)
        self._dc = 32768
        self._prev_raw = 32768
        self._prev_hp = 0
        self._last_three = [0, 0, 0]
        self._adaptive_peak = self.min_peak_height
        self._pid_integral = 0.0
        self._pid_prev_error = 0.0
        self._pid_kp = float(getattr(cfg, "PID_KP", 0.02))
        self._pid_ki = float(getattr(cfg, "PID_KI", 0.001))
        self._pid_kd = float(getattr(cfg, "PID_KD", 0.01))
        self._pid_target = float(getattr(cfg, "PID_TARGET_AMPLITUDE", 800.0))

        self._sample_count = 0
        self._last_sample_ms = 0
        self._last_peak_ms = None
        self._last_bpm_update_ms = 0
        self._last_valid_signal_ms = 0
        self._status = "IDLE"

        self.collection_seconds = self.min_collection_seconds
        self.collection_start_ms = 0
        self.rr_intervals = []
        self.latest_bpm = 0
        self.latest_fft_bpm = 0
        self.measuring = False
        self.raw_buffer = []
        self.filtered_buffer = []
        self._wave_points = int(getattr(cfg, "PPG_WAVEFORM_POINTS", 64))

    def start(self, collection_seconds=None):
        self.collection_seconds = collection_seconds or self.min_collection_seconds
        self.collection_start_ms = time.ticks_ms()
        self.rr_intervals = []
        self.latest_bpm = 0
        self.measuring = True
        self._sample_count = 0
        self._last_sample_ms = time.ticks_ms()
        self._last_peak_ms = None
        self._last_bpm_update_ms = 0
        self._last_valid_signal_ms = 0
        self._status = "SEARCHING"
        self._dc = 32768
        self._prev_raw = 32768
        self._prev_hp = 0
        self._last_three = [0, 0, 0]
        self._adaptive_peak = self.min_peak_height
        self._pid_integral = 0.0
        self._pid_prev_error = 0.0
        self.raw_buffer = []
        self.filtered_buffer = []

    def stop(self):
        self.measuring = False
        self._status = "IDLE"

    def update(self):
        """Run at application tick speed, returns event dict."""
        if not self.measuring:
            return {"peak": False, "bpm_updated": False, "bpm": self.latest_bpm, "status": self._status}

        now = time.ticks_ms()
        peak = False
        while time.ticks_diff(now, self._last_sample_ms) >= self.sample_period_ms:
            self._last_sample_ms = time.ticks_add(self._last_sample_ms, self.sample_period_ms)
            raw = self.sensor.get_ppg_sample()
            filtered = self._highpass(raw)
            self._append_sample_buffers(raw, filtered)
            peak = self._process_peak(filtered, now) or peak
            self._sample_count += 1

        bpm_updated = False
        if time.ticks_diff(now, self._last_bpm_update_ms) >= 500:
            self._last_bpm_update_ms = now
            rr_bpm = self._calculate_bpm()
            self.latest_fft_bpm = self._calculate_fft_bpm()
            self.latest_bpm = self._select_best_bpm(rr_bpm, self.latest_fft_bpm)
            bpm_updated = True

        if self._last_valid_signal_ms and time.ticks_diff(now, self._last_valid_signal_ms) > 3000:
            self._status = "NO_SIGNAL"
        elif self.latest_bpm > 0:
            self._status = "TRACKING"

        return {
            "peak": peak,
            "bpm_updated": bpm_updated,
            "bpm": self.latest_bpm,
            "fft_bpm": self.latest_fft_bpm,
            "status": self._status,
        }

    def _append_sample_buffers(self, raw, filtered):
        self.raw_buffer.append(raw)
        self.filtered_buffer.append(filtered)
        max_points = max(self._wave_points, 128)
        if len(self.raw_buffer) > max_points:
            self.raw_buffer.pop(0)
        if len(self.filtered_buffer) > max_points:
            self.filtered_buffer.pop(0)

    def _highpass(self, raw):
        hp = self._alpha * (self._prev_hp + raw - self._prev_raw)
        self._prev_raw = raw
        self._prev_hp = hp
        self._dc = 0.995 * self._dc + 0.005 * raw
        return int(hp)

    def _process_peak(self, value, now_ms):
        self._last_three[0] = self._last_three[1]
        self._last_three[1] = self._last_three[2]
        self._last_three[2] = value
        if self._sample_count < 3:
            return False

        mid = self._last_three[1]
        signal_amp = abs(mid)
        error = self._pid_target - signal_amp
        self._pid_integral += error
        derivative = error - self._pid_prev_error
        pid = self._pid_kp * error + self._pid_ki * self._pid_integral + self._pid_kd * derivative
        self._pid_prev_error = error
        self._adaptive_peak = max(self.min_peak_height, int(self._adaptive_peak - pid))
        is_local_max = mid > self._last_three[0] and mid > self._last_three[2]
        if not is_local_max or mid < self._adaptive_peak:
            return False

        if self._last_peak_ms is not None:
            peak_gap_ms = time.ticks_diff(now_ms, self._last_peak_ms)
            if peak_gap_ms < int(1000 * self.min_peak_distance / self.sample_rate):
                return False
            rr_ms = peak_gap_ms
            bpm = int(60000 / rr_ms) if rr_ms > 0 else 0
            if self.min_hr <= bpm <= self.max_hr:
                self.rr_intervals.append(rr_ms)
                if len(self.rr_intervals) > self.max_rr:
                    self.rr_intervals.pop(0)
                self._last_valid_signal_ms = now_ms
                self.sensor.trigger_led_pulse(60)
        else:
            self._last_valid_signal_ms = now_ms
            self.sensor.trigger_led_pulse(60)

        self._last_peak_ms = now_ms
        return True

    def _calculate_bpm(self):
        if len(self.rr_intervals) < 3:
            return 0
        recent = self.rr_intervals[-8:]
        mean_rr = sum(recent) / len(recent)
        bpm = int(60000 / mean_rr) if mean_rr else 0
        if bpm < self.min_hr or bpm > self.max_hr:
            return 0
        return bpm

    def _calculate_fft_bpm(self):
        if len(self.filtered_buffer) < 128:
            return 0
        window = self.filtered_buffer[-128:]
        n = len(window)
        mean = sum(window) / n
        centered = [v - mean for v in window]
        min_hz = self.min_hr / 60.0
        max_hz = self.max_hr / 60.0
        start_k = max(1, int(min_hz * n / self.sample_rate))
        end_k = min(int(max_hz * n / self.sample_rate), (n // 2) - 1)
        if end_k <= start_k:
            return 0
        best_k = 0
        best_power = 0.0
        for k in range(start_k, end_k + 1):
            re = 0.0
            im = 0.0
            i = 0
            while i < n:
                angle = 2.0 * math.pi * k * i / n
                sample = centered[i]
                re += sample * math.cos(angle)
                im -= sample * math.sin(angle)
                i += 1
            power = re * re + im * im
            if power > best_power:
                best_power = power
                best_k = k
        if best_k == 0:
            return 0
        hz = (best_k * self.sample_rate) / n
        bpm = int(hz * 60.0)
        if bpm < self.min_hr or bpm > self.max_hr:
            return 0
        return bpm

    def _select_best_bpm(self, rr_bpm, fft_bpm):
        if rr_bpm <= 0 and fft_bpm <= 0:
            return 0
        if rr_bpm > 0 and fft_bpm > 0:
            if abs(rr_bpm - fft_bpm) <= 8:
                return int((rr_bpm + fft_bpm) / 2)
            return rr_bpm
        if rr_bpm > 0:
            return rr_bpm
        return fft_bpm

    def is_collection_complete(self):
        if not self.measuring:
            return False
        elapsed = time.ticks_diff(time.ticks_ms(), self.collection_start_ms) / 1000
        return elapsed >= self.collection_seconds and len(self.rr_intervals) >= self.min_rr_for_hrv

    def get_collection_progress(self):
        if not self.measuring:
            return 0
        elapsed = max(0, time.ticks_diff(time.ticks_ms(), self.collection_start_ms) / 1000)
        return min(100, int((elapsed / self.collection_seconds) * 100))

    def get_status(self):
        return self._status

    def get_rr_intervals(self):
        return self.rr_intervals[:]

    def get_waveform_points(self):
        if not self.filtered_buffer:
            return []
        return self.filtered_buffer[-self._wave_points:]

    def calculate_hrv(self):
        rr = self.rr_intervals[:]
        if len(rr) < self.min_rr_for_hrv:
            return {}

        mean_ppi = sum(rr) / len(rr)
        mean_hr = int(60000 / mean_ppi) if mean_ppi else 0
        deltas = []
        i = 1
        while i < len(rr):
            d = rr[i] - rr[i - 1]
            deltas.append(d * d)
            i += 1
        rmssd = int(math.sqrt(sum(deltas) / len(deltas))) if deltas else 0

        variance = sum((x - mean_ppi) * (x - mean_ppi) for x in rr) / len(rr)
        sdnn = int(math.sqrt(variance))
        elapsed = time.ticks_diff(time.ticks_ms(), self.collection_start_ms) / 1000
        return {
            "mean_ppi": int(mean_ppi),
            "mean_hr": mean_hr,
            "rmssd": rmssd,
            "sdnn": sdnn,
            "sample_count": len(rr),
            "collection_time": int(elapsed),
        }
