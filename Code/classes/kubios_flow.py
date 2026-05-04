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

        # UI throttle (чтобы не ддосить дисплей)
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
        """Call every loop from main"""

        # =====================================================
        # STAGE 1: WAIT PATIENT NAME
        # =====================================================
        if self.stage == 1:
            name = self.wifi.check_patient_name_message()

            # UI update (throttled)
            if time.ticks_diff(time.ticks_ms(), self._last_ui_update) > 500:
                self._last_ui_update = time.ticks_ms()

                remaining = self._get_timer(30)
                self.display.show_waiting_screen(
                    "Waiting for\nPatient Name\n%ds" % remaining
                )

            if name:
                self.patient_name = name
                print("[KUBIOS] Patient:", name)

                self.display.show_success_message(f"Hello,\n{name}", duration=2)

                self.measurement.start_measurement()
                self.measurement.set_collection_duration(30)

                self.stage = 2
                return

            # timeout fallback
            if time.time() - self.start_time > 30:
                print("[KUBIOS] timeout -> default patient")
                self.patient_name = "Unknown_Patient"

                self.measurement.start_measurement()
                self.measurement.set_collection_duration(30)

                self.stage = 2

            return

        # =====================================================
        # STAGE 2: MEASUREMENT
        # =====================================================
        if self.stage == 2:
            bpm = self.measurement.process_sample()
            progress = self.measurement.get_collection_progress()

            # UI throttle
            if bpm and time.ticks_diff(time.ticks_ms(), self._last_ui_update) > 200:
                self._last_ui_update = time.ticks_ms()
                self.display.update_collection_progress(bpm, progress)

            if self.measurement.is_collection_complete():
                print("[KUBIOS] collection done")
                self.stage = 3

            return

        # =====================================================
        # STAGE 3: SEND TO KUBIOS
        # =====================================================
        if self.stage == 3:
            rr = self.measurement.get_rr_intervals()

            self.display.show_message("Sending to\nKubios...")

            response = self.wifi.send_to_kubios(rr, self.patient_name)

            if response:
                self.display.show_kubios_results(response)
                self.storage.save_kubios_result(response, self.patient_name)
                self.display.show_success_message("Kubios OK", duration=2)
            else:
                self.display.show_error_message("Kubios Failed", duration=2)

            self.stage = 4
            return

        # =====================================================
        # EXIT
        # =====================================================
        if self.stage == 4:
            return "DONE"