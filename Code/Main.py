"""
Heart Rate Monitoring System for Raspberry Pi Pico W
Level 5: Complete GUI with HRV analysis, history, and Kubios integration
Author: Pico Advanced Monitoring System
"""

import machine
import time
import json
import gc
import os
from classes.display_manager import DisplayManager
from classes.sensor_manager import SensorManager
from classes.wifi_manager import WiFiManager
from classes.state_machine import StateMachine
from classes.data_storage import DataStorage
from classes.measurement_engine import MeasurementEngine


class HRMonitoringSystem:
    """Main application controller for heart rate monitoring system"""
    
    def __init__(self):
        """Initialize the monitoring system"""
        self.running = True
        self.patient_name = None
        
        # Initialize components
        print("[INIT] Initializing Display Manager...")
        self.display = DisplayManager()
        
        print("[INIT] Initializing Sensor Manager...")
        self.sensor = SensorManager()
        
        print("[INIT] Initializing WiFi Manager...")
        self.wifi = WiFiManager()
        
        print("[INIT] Initializing Data Storage...")
        self.storage = DataStorage()
        
        print("[INIT] Initializing Measurement Engine...")
        self.measurement = MeasurementEngine(self.sensor)
        
        print("[INIT] Initializing State Machine...")
        self.state_machine = StateMachine()
        
        self.display.show_init_message("Initializing...", "Please wait")
        self._safe_mode = self._is_safe_mode_enabled()
        self._boot_grace_period()
    
    def _is_safe_mode_enabled(self):
        """Check for safe mode marker file on device filesystem."""
        try:
            os.stat("SAFE_MODE")
            print("[BOOT] SAFE_MODE marker detected")
            return True
        except OSError:
            return False
    
    def _boot_grace_period(self):
        """
        Keep boot responsive for a short period.
        BTN0 enters safe mode so the app doesn't lock USB/REPL workflows.
        """
        print("[BOOT] Grace period: press BTN0 for SAFE MODE")
        self.display.show_message("Booting...", "BTN0=Safe mode")
        start_time = time.time()
        while (time.time() - start_time) < 3:
            if self.sensor.get_button_input() == "SELECT":
                self._safe_mode = True
                print("[BOOT] Safe mode requested with BTN0")
                break
            time.sleep(0.05)
        
    def wait_for_patient_name(self):
        """Wait for patient name from PC companion app via MQTT"""
        print("[PATIENT] Waiting for patient name input...")
        self.display.show_waiting_screen("Waiting for\nPatient Name\nvia Companion PC App")
        
        # Listen for patient name message on MQTT
        timeout = 30  # seconds
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            message = self.wifi.check_patient_name_message()
            if message:
                self.patient_name = message
                print(f"[PATIENT] Received patient name: {self.patient_name}")
                self.display.show_success_message(f"Hello,\n{self.patient_name}", duration=2)
                return True
            time.sleep(0.1)
        
        print("[PATIENT] Timeout - using default name")
        self.patient_name = "Unknown_Patient"
        self.display.show_warning_message("Using default\npatient name", duration=2)
        return False
    
    def run(self):
        """Main application loop"""
        try:
            if self._safe_mode:
                print("[SAFE MODE] Runtime disabled - REPL remains available")
                self.display.show_warning_message("SAFE MODE\nRuntime paused", duration=1)
                while True:
                    time.sleep(1)

            # Wait for WiFi connection
            print("[MAIN] Connecting to WiFi...")
            if not self.wifi.connect():
                print("[ERROR] WiFi connection failed")
                self.display.show_error_message("WiFi Connect\nFailed", duration=3)
            else:
                print("[MAIN] WiFi connected")
                self.display.show_success_message("WiFi OK", duration=1)
            
            # Sync time with NTP
            print("[MAIN] Syncing time...")
            if self.wifi.sync_ntp_time():
                self.display.show_success_message("Time sync OK", duration=1)
            else:
                self.display.show_warning_message("NTP skipped", duration=1)
            
            # Wait for patient name
            self.wait_for_patient_name()
            
            # Main application loop
            print("[MAIN] Starting main menu loop...")
            while self.running:
                gc.collect()  # Manage memory
                self.state_machine.update()
                self._handle_state()
                time.sleep(0.05)
                
        except KeyboardInterrupt:
            print("[MAIN] Interrupted by user")
        except Exception as e:
            print(f"[ERROR] Fatal error: {e}")
            self.display.show_error_message(f"Error:\n{str(e)}", duration=5)
        finally:
            self.cleanup()
    
    def _handle_state(self):
        """Handle state-specific logic"""
        current_state = self.state_machine.current_state
        
        if current_state == "MENU":
            self._handle_menu_state()
        elif current_state == "MEASURING":
            self._handle_measurement_state()
        elif current_state == "HRV_ANALYSIS":
            self._handle_hrv_analysis_state()
        elif current_state == "KUBIOS":
            self._handle_kubios_state()
        elif current_state == "HISTORY":
            self._handle_history_state()
    
    def _handle_menu_state(self):
        """Handle main menu display and input"""
        if self.state_machine.state_changed:
            self.display.show_main_menu()
            self.state_machine.state_changed = False
        
        # Check for button presses to navigate menu
        menu_action = self.sensor.get_button_input()
        if menu_action:
            self._process_menu_selection(menu_action)
    
    def _handle_measurement_state(self):
        """Handle real-time HR measurement mode"""
        if self.state_machine.state_changed:
            self.display.show_measurement_mode()
            self.measurement.start_measurement()
            self.state_machine.state_changed = False
        
        # Process measurement data
        bpm = self.measurement.process_sample()
        if bpm:
            self.display.update_heart_rate_display(bpm)
        
        # Check for stop button
        if self.sensor.get_button_input() == "STOP":
            self.measurement.stop_measurement()
            self.state_machine.change_state("MENU")
    
    def _handle_hrv_analysis_state(self):
        """Handle local HRV analysis"""
        if self.state_machine.state_changed:
            self.display.show_hrv_collection_screen()
            self.measurement.start_measurement()
            self.state_machine.state_changed = False
            self.measurement.set_collection_duration(30)  # 30 seconds minimum
        
        # Process measurement
        bpm = self.measurement.process_sample()
        progress = self.measurement.get_collection_progress()
        
        if bpm:
            self.display.update_collection_progress(bpm, progress)
        
        # Check if collection is complete
        if self.measurement.is_collection_complete():
            hrv_data = self.measurement.calculate_hrv()
            self.display.show_hrv_results(hrv_data)
            
            # Send HRV data via MQTT
            self.wifi.send_hrv_data(self.patient_name, hrv_data)
            
            # Store locally
            self.storage.save_measurement(hrv_data, self.patient_name)
            
            self.display.show_success_message("Data sent & stored", duration=2)
            self.state_machine.change_state("MENU")
    
    def _handle_kubios_state(self):
        """Handle Kubios Cloud integration"""
        # connect to WiFi before starting Kubios
        if self.state_machine.state_changed:
            self.display.show_message("Connecting WiFi")

            if not self.wifi.is_connected():
                success = self.wifi.connect_wifi()
                if not success:
                    self.display.show_error_message("No WiFi connection", duration=2)
                    self.state_machine.change_state("MENU")
                    return

        if self.state_machine.state_changed:
            self.display.show_kubios_screen()
            self.measurement.start_measurement()
            self.measurement.set_collection_duration(30)
            self.state_machine.state_changed = False
        
        # Process measurement
        bpm = self.measurement.process_sample()
        progress = self.measurement.get_collection_progress()
        
        if bpm:
            self.display.update_collection_progress(bpm, progress)
        
        # When collection complete, send to Kubios
        if self.measurement.is_collection_complete():
            rr_intervals = self.measurement.get_rr_intervals()
            self.display.show_message("Sending to\nKubios Cloud...")
            
            response = self.wifi.send_to_kubios(rr_intervals, self.patient_name)
            
            if response:
                self.display.show_kubios_results(response)
                self.storage.save_kubios_result(response, self.patient_name)
                self.display.show_success_message("Kubios OK", duration=2)
            else:
                self.display.show_error_message("Kubios Failed", duration=2)
            
            self.state_machine.change_state("MENU")
    
    def _handle_history_state(self):
        """Handle history/data viewing"""
        if self.state_machine.state_changed:
            history_data = self.storage.load_history()
            self.display.show_history_menu(history_data)
            self.state_machine.state_changed = False
        
        # Check for navigation input
        action = self.sensor.get_button_input()
        if action == "BACK":
            self.state_machine.change_state("MENU")
        elif action == "SELECT":
            selected_entry = self.display.get_selected_history_entry()
            if selected_entry:
                self.display.show_history_details(selected_entry)
    
    def _process_menu_selection(self, selection):
        """Process menu selection"""
        menu_map = {
            "MEASURE_HR": "MEASURING",
            "HRV_ANALYSIS": "HRV_ANALYSIS",
            "KUBIOS": "KUBIOS",
            "HISTORY": "HISTORY"
        }
        
        if selection in menu_map:
            self.state_machine.change_state(menu_map[selection])
    
    def cleanup(self):
        """Clean up resources"""
        print("[CLEANUP] Shutting down...")
        self.measurement.stop_measurement()
        self.wifi.disconnect()
        self.display.show_message("System Shutdown", "See you soon!")
        time.sleep(1)
        # Avoid forced resets here; repeated reset loops can destabilize USB serial.


def main():
    """Entry point"""
    print("\n" + "="*50)
    print("Heart Rate Monitoring System - Level 5")
    print("Raspberry Pi Pico W")
    print("="*50 + "\n")
    
    system = HRMonitoringSystem()
    system.run()


if __name__ == "__main__":
    main()
