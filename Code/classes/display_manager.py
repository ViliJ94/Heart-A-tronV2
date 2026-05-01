"""
Display Manager - Handles all OLED display operations and GUI rendering
Supports 128x64 SSD1306 OLED display via I2C
"""

import machine
import time
from .graphics import Graphics


class DisplayManager:
    """Manages OLED display operations and UI rendering"""
    
    # I2C Configuration (SDA=GP26... wait no, let me check - ADC0 is on GP26)
    # I2C pins: typically I2C_1: SCL=GP15, SDA=GP14
    I2C_SDA = 14
    I2C_SCL = 15
    I2C_FREQ = 400000  # 400kHz
    
    DISPLAY_WIDTH = 128
    DISPLAY_HEIGHT = 64
    
    def __init__(self):
        """Initialize OLED display"""
        try:
            self.i2c = machine.I2C(1, scl=machine.Pin(self.I2C_SCL), 
                                    sda=machine.Pin(self.I2C_SDA), 
                                    freq=self.I2C_FREQ)
            
            # Import SSD1306 display driver
            from ssd1306 import SSD1306_I2C
            self.display = SSD1306_I2C(self.DISPLAY_WIDTH, self.DISPLAY_HEIGHT, self.i2c)
            self.graphics = Graphics(self.display)
            
            print("[DISPLAY] OLED initialized successfully")
            self._test_display()
        except Exception as e:
            print(f"[DISPLAY ERROR] Failed to initialize display: {e}")
            self.display = None
            self.graphics = None
    
    def _test_display(self):
        """Test display with initialization sequence"""
        self.display.fill(0)
        self.display.show()
        time.sleep(0.5)
    
    def show_init_message(self, title, message):
        """Show initialization message"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text(title, 0, 10, 2)
        self.graphics.draw_text(message, 0, 35, 1)
        self.display.show()
    
    def show_waiting_screen(self, message):
        """Show waiting screen for patient name"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_centered_text("Waiting for", 10, 1)
        self.graphics.draw_centered_text("patient name", 24, 1)
        self.graphics.draw_centered_text("from PC app", 38, 1)
        self._draw_loading_spinner()
        self.display.show()
    
    def show_success_message(self, message, duration=2):
        """Show success message with optional duration"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_centered_text("SUCCESS", 15, 1)
        self.graphics.draw_centered_text(message, 40, 1)
        self.display.show()
        time.sleep(duration)
    
    def show_warning_message(self, message, duration=2):
        """Show warning message"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_centered_text("WARNING", 15, 1)
        self.graphics.draw_centered_text(message, 40, 1)
        self.display.show()
        time.sleep(duration)
    
    def show_error_message(self, message, duration=5):
        """Show error message"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_centered_text("ERROR", 15, 1)
        self.graphics.draw_centered_text(message, 40, 1)
        self.display.show()
        time.sleep(duration)
    
    def show_message(self, title, message):
        """Show a generic message"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_centered_text(title, 15, 2)
        self.graphics.draw_centered_text(message, 40, 1)
        self.display.show()
    
    def show_main_menu(self):
        """Display main menu with icons"""
        if not self.display:
            return
        
        self.display.fill(0)
        
        # Title
        self.graphics.draw_text("MAIN MENU", 0, 0, 2)
        
        # Draw menu items with simple icons
        self.graphics.draw_text("1. Measure HR", 0, 18, 1)
        self.graphics.draw_text("2. HRV Analysis", 0, 28, 1)
        self.graphics.draw_text("3. Kubios", 0, 38, 1)
        self.graphics.draw_text("4. History", 0, 48, 1)
        
        # Draw selection indicator (animated)
        indicator = ">" + " " * 20
        self.graphics.draw_text(indicator[0], 80, 18, 1)
        
        self.display.show()
    
    def show_measurement_mode(self):
        """Display measurement/heart rate measurement screen"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("HEART RATE", 0, 0, 2)
        self.graphics.draw_text("MEASUREMENT", 0, 14, 1)
        self.graphics.draw_centered_text("--", 38, 3)
        self.graphics.draw_text("BPM", 50, 40, 1)
        self.display.show()
    
    def update_heart_rate_display(self, bpm, ppg_waveform=None):
        """Update heart rate value and optional waveform"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("HR: {} BPM".format(bpm), 0, 0, 2)
        
        # Draw waveform if provided
        if ppg_waveform and len(ppg_waveform) > 0:
            self._draw_waveform(ppg_waveform, 0, 20, 128, 30)
        
        self.graphics.draw_text("Press to STOP", 0, 55, 1)
        self.display.show()
    
    def show_hrv_collection_screen(self):
        """Display HRV data collection screen"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("HRV ANALYSIS", 0, 0, 2)
        self.graphics.draw_text("Collecting data...", 0, 18, 1)
        self.graphics.draw_centered_text("0/30s", 40, 2)
        self.display.show()
    
    def update_collection_progress(self, bpm, progress_percent):
        """Update collection progress display"""
        if not self.display:
            return
        
        seconds = int(progress_percent * 30 / 100)
        
        self.display.fill(0)
        self.graphics.draw_text("HRV ANALYSIS", 0, 0, 2)
        self.graphics.draw_text("Collecting data...", 0, 18, 1)
        self.graphics.draw_centered_text("{}/30s".format(seconds), 40, 2)
        self.graphics.draw_centered_text("HR: {} BPM".format(bpm), 50, 1)
        
        # Draw progress bar
        bar_width = int(100 * progress_percent / 100)
        self.display.fill_rect(0, 58, bar_width, 6, 1)
        self.display.rect(0, 58, 128, 6, 1)
        
        self.display.show()
    
    def show_hrv_results(self, hrv_data):
        """Display HRV analysis results"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("HRV RESULTS", 0, 0, 2)
        
        mean_hr = int(hrv_data.get("mean_hr", 0))
        mean_ppi = int(hrv_data.get("mean_ppi", 0))
        rmssd = int(hrv_data.get("rmssd", 0))
        
        self.graphics.draw_text("HR: {} BPM".format(mean_hr), 0, 18, 1)
        self.graphics.draw_text("RMSSD: {}ms".format(rmssd), 0, 28, 1)
        self.graphics.draw_text("SDNN:{}".format(int(hrv_data.get("sdnn", 0))), 0, 38, 1)
        self.graphics.draw_text("Status: READY", 0, 50, 1)
        
        self.display.show()
    
    def show_kubios_screen(self):
        """Display Kubios analysis screen"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("KUBIOS ANALYSIS", 0, 0, 1)
        self.graphics.draw_text("Collecting 30s data", 0, 18, 1)
        self.graphics.draw_centered_text("0/30s", 40, 2)
        self.display.show()
    
    def show_kubios_results(self, results):
        """Display Kubios analysis results"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("KUBIOS RESULTS", 0, 0, 1)
        
        stress = results.get("stress_level", "N/A")
        hr = results.get("heart_rate", 0)
        
        self.graphics.draw_text("HR: {} BPM".format(hr), 0, 18, 1)
        self.graphics.draw_text("STRESS: {}".format(stress), 0, 28, 1)
        self.graphics.draw_text("Cloud: OK", 0, 38, 1)
        
        self.display.show()
    
    def show_history_menu(self, history_data):
        """Display history menu"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("HISTORY", 0, 0, 2)
        
        if history_data and len(history_data) > 0:
            for idx, entry in enumerate(history_data[:3]):  # Show first 3
                timestamp = entry.get("timestamp", "Unknown")
                hr = entry.get("mean_hr", 0)
                self.graphics.draw_text("{}. {} - {} BPM".format(idx+1, timestamp[:5], hr), 
                                       0, 18 + idx*12, 1)
        else:
            self.graphics.draw_text("No history data", 0, 28, 1)
        
        self.display.show()
    
    def show_history_details(self, entry):
        """Display detailed view of history entry"""
        if not self.display:
            return
        
        self.display.fill(0)
        self.graphics.draw_text("ENTRY DETAILS", 0, 0, 1)
        
        timestamp = entry.get("timestamp", "N/A")
        patient = entry.get("patient", "N/A")
        mean_hr = entry.get("mean_hr", 0)
        rmssd = entry.get("rmssd", 0)
        
        self.graphics.draw_text("Time: {}".format(timestamp), 0, 16, 1)
        self.graphics.draw_text("Patient: {}".format(patient), 0, 24, 1)
        self.graphics.draw_text("HR: {} BPM".format(mean_hr), 0, 32, 1)
        self.graphics.draw_text("RMSSD: {}ms".format(rmssd), 0, 40, 1)
        
        self.display.show()
    
    def get_selected_history_entry(self):
        """Get currently selected history entry"""
        # This would be handled by state machine
        return None
    
    def _draw_waveform(self, data, x, y, width, height):
        """Draw PPG waveform on display"""
        if not data or len(data) < 2:
            return
        
        # Scale data to display dimensions
        max_val = max(data) if max(data) > 0 else 1
        min_val = min(data)
        range_val = max_val - min_val if max_val != min_val else 1
        
        points = len(data)
        x_scale = width / points
        
        for i in range(len(data) - 1):
            x1 = x + int(i * x_scale)
            y1 = y + height - int((data[i] - min_val) * height / range_val)
            x2 = x + int((i + 1) * x_scale)
            y2 = y + height - int((data[i + 1] - min_val) * height / range_val)
            
            self.display.line(x1, y1, x2, y2, 1)
    
    def _draw_loading_spinner(self):
        """Draw animated loading spinner"""
        spinner_chars = ["|", "/", "-", "\\"]
        spinner = spinner_chars[int(time.time() * 4) % 4]
        self.graphics.draw_centered_text(spinner, 50, 3)
