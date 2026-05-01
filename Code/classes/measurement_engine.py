"""
Measurement Engine - Handles signal processing, peak detection, and HRV calculations
"""

import time
import math


class MeasurementEngine:
    """Processes PPG sensor data and calculates HRV metrics"""
    
    # Sampling configuration
    SAMPLE_RATE = 250  # Hz
    SAMPLE_PERIOD = 1 / SAMPLE_RATE  # ~4ms
    
    # Buffer sizes
    ROLLING_BUFFER_SIZE = 1000  # ~4 seconds of data at 250Hz
    RR_BUFFER_SIZE = 256  # Store up to 256 RR intervals
    
    # Peak detection thresholds
    MIN_PEAK_HEIGHT = 100  # Minimum ADC value for valid peak
    MIN_PEAK_DISTANCE = 30  # Minimum samples between peaks (0.12s)
    
    # HRV parameters
    MIN_COLLECTION_TIME = 30  # Minimum seconds for HRV analysis
    MIN_RR_INTERVALS = 30  # Minimum RR intervals for analysis
    
    def __init__(self, sensor_manager):
        """Initialize measurement engine"""
        self.sensor = sensor_manager
        
        self.measuring = False
        self.collection_start_time = None
        self.collection_duration = 30  # seconds
        
        # Data buffers
        self.ppg_buffer = []  # Rolling buffer of PPG samples
        self.filtered_buffer = []  # High-pass filtered data
        self.peak_indices = []  # Indices of detected peaks
        self.rr_intervals = []  # RR intervals in milliseconds
        self.bpm_history = []  # Recent BPM values
        
        # Signal processing state
        self.last_peak_index = -self.MIN_PEAK_DISTANCE
        self.baseline = 32768  # Midpoint of 16-bit ADC
        self.dc_offset = 32768
        self.ac_amplitude = 1000
        
        print("[MEASUREMENT] Measurement engine initialized")
    
    def start_measurement(self):
        """Start new measurement session"""
        self.measuring = True
        self.collection_start_time = time.time()
        self.ppg_buffer = []
        self.filtered_buffer = []
        self.peak_indices = []
        self.rr_intervals = []
        self.bpm_history = []
        self.last_peak_index = -self.MIN_PEAK_DISTANCE
        
        print("[MEASUREMENT] Measurement started")
    
    def stop_measurement(self):
        """Stop measurement session"""
        self.measuring = False
        print(f"[MEASUREMENT] Measurement stopped. Collected {len(self.rr_intervals)} RR intervals")
    
    def set_collection_duration(self, seconds):
        """Set minimum collection duration"""
        self.collection_duration = seconds
    
    def process_sample(self):
        """
        Process one PPG sample and return BPM if valid
        Should be called frequently from main loop
        """
        if not self.measuring:
            return None
        
        # Read PPG sample
        sample = self.sensor.get_ppg_sample()
        
        # Add to buffer
        self.ppg_buffer.append(sample)
        if len(self.ppg_buffer) > self.ROLLING_BUFFER_SIZE:
            self.ppg_buffer.pop(0)
        
        # Apply signal processing
        filtered = self._apply_filter(sample)
        self.filtered_buffer.append(filtered)
        if len(self.filtered_buffer) > self.ROLLING_BUFFER_SIZE:
            self.filtered_buffer.pop(0)
        
        # Detect peaks
        peak_detected = self._detect_peak(filtered, len(self.filtered_buffer) - 1)
        
        if peak_detected:
            # Calculate RR interval
            if len(self.peak_indices) > 0:
                last_peak_time = self.peak_indices[-1] / self.SAMPLE_RATE
                current_peak_time = (len(self.filtered_buffer) - 1) / self.SAMPLE_RATE
                rr_interval = (current_peak_time - last_peak_time) * 1000  # Convert to ms
                
                # Validate RR interval (reasonable HR: 40-200 BPM = 300-1500 ms)
                if 300 < rr_interval < 1500:
                    self.rr_intervals.append(rr_interval)
                    if len(self.rr_intervals) > self.RR_BUFFER_SIZE:
                        self.rr_intervals.pop(0)
            
            self.peak_indices.append(len(self.filtered_buffer) - 1)
            
            # Pulse LED when peak detected
            self.sensor.pulse_led(duration_ms=50)
        
        # Calculate and return BPM every ~5 samples
        if len(self.ppg_buffer) % 5 == 0 and len(self.rr_intervals) > 5:
            bpm = self._calculate_bpm()
            self.bpm_history.append(bpm)
            return bpm
        
        return None
    
    def get_collection_progress(self):
        """Get collection progress as percentage (0-100)"""
        if not self.measuring or not self.collection_start_time:
            return 0
        
        elapsed = time.time() - self.collection_start_time
        progress = min(100, int((elapsed / self.collection_duration) * 100))
        return progress
    
    def is_collection_complete(self):
        """Check if data collection is complete and valid"""
        if not self.measuring:
            return True
        
        elapsed = time.time() - self.collection_start_time
        has_enough_time = elapsed >= self.collection_duration
        has_enough_intervals = len(self.rr_intervals) >= self.MIN_RR_INTERVALS
        
        return has_enough_time and has_enough_intervals
    
    def calculate_hrv(self):
        """
        Calculate HRV metrics from collected RR intervals
        Returns dict with mean_hr, rmssd, sdnn, mean_ppi
        """
        if len(self.rr_intervals) < self.MIN_RR_INTERVALS:
            print("[MEASUREMENT] Insufficient data for HRV calculation")
            return {}
        
        rr = self.rr_intervals
        
        # Mean RR interval (PPI)
        mean_ppi = sum(rr) / len(rr)
        
        # Mean HR
        mean_hr = 60000 / mean_ppi if mean_ppi > 0 else 0
        
        # RMSSD (Root Mean Sum of Squared Differences)
        differences = []
        for i in range(1, len(rr)):
            diff = rr[i] - rr[i-1]
            differences.append(diff * diff)
        
        rmssd = math.sqrt(sum(differences) / len(differences)) if differences else 0
        
        # SDNN (Standard Deviation of NN intervals)
        variance = sum((x - mean_ppi) ** 2 for x in rr) / len(rr)
        sdnn = math.sqrt(variance)
        
        # LF/HF (would require FFT - simplified here)
        lf_hf_ratio = 1.5  # Placeholder
        
        result = {
            "mean_ppi": mean_ppi,
            "mean_hr": int(mean_hr),
            "rmssd": int(rmssd),
            "sdnn": int(sdnn),
            "lf_hf_ratio": lf_hf_ratio,
            "sample_count": len(rr),
            "collection_time": time.time() - self.collection_start_time
        }
        
        print(f"[MEASUREMENT] HRV calculated: HR={result['mean_hr']}, RMSSD={result['rmssd']}, SDNN={result['sdnn']}")
        return result
    
    def get_rr_intervals(self):
        """Get array of RR intervals for export to Kubios"""
        return self.rr_intervals
    
    def _apply_filter(self, sample):
        """
        Apply high-pass filter to remove DC offset
        Simple IIR high-pass filter: y = alpha * (y_prev + sample - sample_prev)
        """
        alpha = 0.95  # High-pass filter coefficient
        
        if len(self.filtered_buffer) == 0:
            return sample - self.baseline
        
        prev_sample = self.ppg_buffer[-2] if len(self.ppg_buffer) > 1 else sample
        prev_filtered = self.filtered_buffer[-1]
        
        filtered = alpha * (prev_filtered + sample - prev_sample)
        
        # Update running statistics
        self.dc_offset = 0.999 * self.dc_offset + 0.001 * sample
        
        return int(filtered)
    
    def _detect_peak(self, filtered_value, index):
        """
        Detect PPG peak using simple threshold with minimum distance
        Returns: True if peak detected, False otherwise
        """
        # Need at least 3 points to detect peak
        if len(self.filtered_buffer) < 3:
            return False
        
        # Check minimum distance between peaks
        if index - self.last_peak_index < self.MIN_PEAK_DISTANCE:
            return False
        
        # Simple peak detection: local maximum
        if (str(self.filtered_buffer[index]) > self.filtered_buffer[index - 1] and 
            self.filtered_buffer[index] > self.filtered_buffer[index - 2]):
            
            # Additional check for minimum height
            if self.filtered_buffer[index] > self.MIN_PEAK_HEIGHT:
                self.last_peak_index = index
                return True
        
        return False
    
    def _calculate_bpm(self):
        """Calculate current BPM from recent RR intervals"""
        if len(self.rr_intervals) < 2:
            return 0
        
        # Use average of last 10 intervals for smoothing
        recent_intervals = self.rr_intervals[-10:]
        mean_interval = sum(recent_intervals) / len(recent_intervals)
        
        bpm = int(60000 / mean_interval) if mean_interval > 0 else 0
        
        # Bound BPM to reasonable range
        return max(40, min(200, bpm))
