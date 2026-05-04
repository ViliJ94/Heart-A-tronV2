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
from classes.kubios_flow import KubiosFlow


def _agent_dbg(*args, **kwargs):
    # Debug hook used in some builds; safe no-op on device.
    return


class HRMonitoringSystem:
    """Main application controller for heart rate monitoring system"""
    
    def __init__(self):
        """Initialize the monitoring system"""
        self.running = True
        self.patient_name = "Unknown"
        self._menu_index = 0
        self._history_index = 0
        
        
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
        self.kubios = KubiosFlow(self.wifi,self.measurement,self.display,self.storage)
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
        last_log_ms = 0
        armed = False
        while (time.time() - start_time) < 3:
            action = self.sensor.get_button_input()
            # #region agent log
            now_ms = time.ticks_ms()
            if time.ticks_diff(now_ms, last_log_ms) >= 250:
                last_log_ms = now_ms
                try:
                    raw = self.sensor.get_all_sensor_values()
                except Exception:
                    raw = {"err": "get_all_sensor_values_failed"}
                try:
                    b = raw.get("buttons", {})
                    all_released = (b.get("BTN0", 1) == 1) and (b.get("BTN1", 1) == 1) and (b.get("BTN2", 1) == 1)
                except Exception:
                    all_released = False
                if all_released:
                    armed = True
                _agent_dbg(
                    "H12",
                    "Main.py:_boot_grace_period",
                    "boot_grace_poll",
                    {"action": action, "raw": raw, "armed": armed},
                )
            # #endregion
            # Only allow safe mode if we've observed all buttons released at least once.
            if armed and action == "SELECT":
                self._safe_mode = True
                print("[BOOT] Safe mode requested with BTN0")
                break
        
    def wait_for_patient_name(self):
        """Wait for patient name from PC companion app via MQTT"""
        print("[PATIENT] Waiting for patient name input...")
        self.display.show_waiting_screen("Waiting for\nPatient Name\nvia Companion PC App")
        
        # Listen for patient name message on MQTT
        timeout = 30  # seconds
        start_time = time.time()
        next_debug_time = start_time + 5
        
        while (time.time() - start_time) < timeout:
            message = self.wifi.check_patient_name_message()
            if message:
                self.patient_name = message
                print(f"[PATIENT] Received patient name: {self.patient_name}")
                self.display.show_success_message(f"Hello,\n{self.patient_name}", duration=2)
                return True
            if time.time() >= next_debug_time:
                print("[PATIENT] waiting for patient name... mqtt_client=", self.wifi.mqtt_client is not None,
                      "last_check_error=", self.wifi.last_mqtt_check_error)
                next_debug_time += 5
        
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
                exit_hits = 0
                

            # WiFi and Broker initialization moved to Kubios mode
            # Patient name defaults to "Unknown" - will be updated if user enters Kubios mode
            print("[MAIN] Patient name initialized as: Unknown")
            self.display.show_success_message("Ready to use", duration=1)
            
            # Main application loop
            print("[MAIN] Starting main menu loop...")
            while self.running:
                gc.collect()  # Manage memory
                self.sensor.update()  # Refill PIO buffer; handle LED timing
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
        
        if current_state == "INIT":
            # Transition from INIT to MENU on first loop
            self.state_machine.change_state("MENU")
        elif current_state == "MENU":
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
            self._menu_index = 0
            self.display.show_main_menu(self._menu_index)
            self.state_machine.state_changed = False
        
        # Check for button presses to navigate menu
        menu_action = self.sensor.get_button_input()

        if menu_action == "DOWN":
            self._menu_index = (self._menu_index + 1) % 4
            self.display.show_main_menu(self._menu_index)
            # #region agent log
            _agent_dbg(
                "H6",
                "Main.py:_handle_menu_state",
                "menu_move",
                {"direction": "DOWN", "menu_index_after": self._menu_index},
            )
            # #endregion
        elif menu_action == "UP":
            self._menu_index = (self._menu_index - 1) % 4
            self.display.show_main_menu(self._menu_index)
            # #region agent log
            _agent_dbg(
                "H6",
                "Main.py:_handle_menu_state",
                "menu_move",
                {"direction": "UP", "menu_index_after": self._menu_index},
            )
            # #endregion
        elif menu_action == "SELECT":
            menu_items = ["MEASURE_HR", "HRV_ANALYSIS", "KUBIOS", "HISTORY"]
            selected_key = menu_items[self._menu_index]
            self._process_menu_selection(selected_key)
    
    def _handle_measurement_state(self):
        """Handle real-time HR measurement mode"""
        if self.state_machine.state_changed:
            self.display.show_measurement_mode()
            self.measurement.start_measurement()
            self.state_machine.state_changed = False
        
        # Process measurement data (always render status, even if BPM is 0)
        bpm = self.measurement.process_sample() or 0
        try:
            status = self.measurement.get_status()
        except Exception:
            status = "MEASURING"
        try:
            waveform = self.measurement.get_waveform_points()
        except Exception:
            waveform = None
        try:
            self.display.show_measurement("MEASURE HR", bpm, status, waveform=waveform)
        except Exception:
            # Fallback for simpler display managers
            if bpm > 0:
                self.display.update_heart_rate_display(bpm)
        
        # Check for stop button
        if self.sensor.get_button_input() in ("STOP", "UP", "BACK"):
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
        bpm = self.measurement.process_sample() or 0
        progress = self.measurement.get_collection_progress()
        try:
            status = self.measurement.get_status()
        except Exception:
            status = "COLLECTING"
        try:
            self.display.show_collection("HRV", bpm, int(progress), status)
        except Exception:
            # Fallback
            if bpm > 0:
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

    # first entry
        if self.state_machine.state_changed:
            self.state_machine.state_changed = False
            ok = self.kubios.start()
            if not ok:
                self.state_machine.change_state("MENU")
                return
        # continuous update
        result = self.kubios.update()
        if result == "DONE":
            self.state_machine.change_state("MENU")
    
    def _handle_history_state(self):
        """Handle history/data viewing with downward scrolling only"""
        if self.state_machine.state_changed:
            # Load history and reverse so latest entries appear first
            history_data = self.storage.load_history()
            history_data.reverse()  # Newest first
            self._history_index = 0
            self.display.show_history(history_data, self._history_index)
            self.state_machine.state_changed = False
        
        # Check for navigation input
        action = self.sensor.get_button_input()
        if action in ("UP", "BACK", "STOP"):
            # UP button (SW1) goes back to menu
            self.state_machine.change_state("MENU")
        elif action == "DOWN":
            # DOWN button scrolls downward with wrap-around
            history_data = self.storage.load_history()
            history_data.reverse()  # Newest first
            if len(history_data) > 0:
                # Scroll down; wrap to first entry when past the last
                self._history_index = (self._history_index + 1) % len(history_data)
                self.display.show_history(history_data, self._history_index)
        elif action == "SELECT":
            # Show details of selected entry
            history_data = self.storage.load_history()
            history_data.reverse()  # Newest first
            if self._history_index < len(history_data):
                selected_entry = history_data[self._history_index]
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
