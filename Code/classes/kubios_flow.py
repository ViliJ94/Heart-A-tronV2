"""
Kubios Flow Controller
Handles WiFi + MQTT + measurement + sending to Kubios
"""

import time


class KubiosFlow:
    def __init__(self, wifi, measurement, display, storage):
        self.wifi = wifi
        self.measurement = measurement
        self.display = display
        self.storage = storage

        self.reset()

        # UI throttle: To avoid overwhelming the display
        self._last_ui_update = 0

    def reset(self):
        """Reset internal state"""
        self.stage = 0
        self.patient_name = "Unknown_Patient"
        self.start_time = 0

    def _get_timer(self, limit):
        """Return remaining seconds"""
        return max(0, int(limit - (time.time() - self.start_time)))

    def start(self):
        """Entry point from state machine"""
        self.reset()
        self.start_time = time.time()

        self.display.show_message("Initializing\nKubios Mode...")

        # ---------- WIFI ----------
        print("[KUBIOS] Connecting WiFi...")
        if not self.wifi.connect():
            print("[KUBIOS] WiFi failed")
            self.display.show_error_message("WiFi Failed", duration=2)
            return False

        print("[KUBIOS] WiFi OK")

        # ---------- MQTT ----------
        print("[KUBIOS] Init MQTT...")
        ok = self.wifi._init_mqtt()

        if not ok:
            print("[KUBIOS] MQTT failed -> offline mode")
            self.patient_name = "Offline_Patient"
        else:
            print("[KUBIOS] MQTT OK")

        self.display.show_waiting_screen("Waiting for\nPatient Name")

        self.stage = 1
        return True

    def update(self):
        self.wifi.poll()

        if self.stage == 1:
            name = self.wifi.check_patient_name_message()

            if name:
                self.patient_name = name
                self.measurement.start_measurement()
                self.measurement.set_collection_duration(30)
                self.stage = 2
            return

        if self.stage == 2:
            self.measurement.process_sample()

            if self.measurement.is_collection_complete():
                self.stage = 3
            return

        if self.stage == 3:
            rr = self.measurement.get_rr_intervals()
            self.wifi.send_to_kubios(rr, self.patient_name)
            self.stage = 4
            return
        if self.stage == 4:
            return "DONE"