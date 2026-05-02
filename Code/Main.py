"""Heart-A-tron V2 application runtime."""

import gc
import time

try:
    import config as cfg
except ImportError:
    cfg = None

from classes.display_manager import DisplayManager
from classes.sensor_manager import SensorManager
from classes.wifi_manager import WiFiManager
from classes.data_storage import DataStorage
from classes.measurement_engine import MeasurementEngine


class BaseState:
    def enter(self, app):
        pass

    def update(self, app, events):
        pass

    def exit(self, app):
        pass


class MenuState(BaseState):
    options = ["Measure HR", "Local HRV", "Kubios", "History"]

    def enter(self, app):
        app.menu_index = 0
        app.display.show_main_menu(self.options, app.menu_index)

    def update(self, app, events):
        if "NEXT" in events:
            app.menu_index = (app.menu_index + 1) % len(self.options)
            app.display.show_main_menu(self.options, app.menu_index)
        if "SELECT" in events:
            mapping = ["MEASURING", "HRV_ANALYSIS", "KUBIOS", "HISTORY"]
            app.change_state(mapping[app.menu_index])


class MeasuringState(BaseState):
    def enter(self, app):
        app.measurement.start(collection_seconds=getattr(cfg, "MIN_COLLECTION_TIME_SECONDS", 30))

    def update(self, app, events):
        event = app.measurement.update()
        if "BACK" in events:
            app.change_state("MENU")
            return
        if event["bpm_updated"]:
            waveform = app.measurement.get_waveform_points()
            app.display.show_measurement("MEASURE HR", event["bpm"], event["status"], waveform)

    def exit(self, app):
        app.measurement.stop()


class LocalHrvState(BaseState):
    def enter(self, app):
        app.measurement.start(collection_seconds=getattr(cfg, "MIN_COLLECTION_TIME_SECONDS", 30))
        app.result_timeout_ms = time.ticks_add(time.ticks_ms(), 2000)

    def update(self, app, events):
        if "BACK" in events:
            app.change_state("MENU")
            return
        event = app.measurement.update()
        progress = app.measurement.get_collection_progress()
        if event["bpm_updated"]:
            app.display.show_collection("LOCAL HRV", event["bpm"], progress, event["status"])
        if app.measurement.is_collection_complete():
            payload = app.measurement.calculate_hrv()
            if payload:
                app.storage.save_measurement(payload, app.patient_name)
                app.wifi.send_hrv_data(app.patient_name, payload)
                app.display.show_hrv_results(payload)
            app.change_state("MENU")

    def exit(self, app):
        app.measurement.stop()


class KubiosState(BaseState):
    def enter(self, app):
        app.measurement.start(collection_seconds=getattr(cfg, "MIN_COLLECTION_TIME_SECONDS", 30))
        app._kubios_first = None
        app._kubios_request_id = None
        app._kubios_stage = "collecting_1"

    def _build_comparison(self, first_result, second_result):
        return {
            "result_1_hr": first_result.get("heart_rate", 0),
            "result_2_hr": second_result.get("heart_rate", 0),
            "result_1_stress": first_result.get("stress_level", "N/A"),
            "result_2_stress": second_result.get("stress_level", "N/A"),
            "delta_hr": second_result.get("heart_rate", 0) - first_result.get("heart_rate", 0),
        }

    def update(self, app, events):
        if "BACK" in events:
            app.change_state("MENU")
            return

        if app._kubios_stage.startswith("collecting"):
            event = app.measurement.update()
            progress = app.measurement.get_collection_progress()
            if event["bpm_updated"]:
                app.display.show_collection("KUBIOS", event["bpm"], progress, event["status"])
            if app.measurement.is_collection_complete():
                rr = app.measurement.get_rr_intervals()
                app._kubios_request_id = app.wifi.request_kubios_analysis(rr, app.patient_name)
                if not app._kubios_request_id:
                    app.display.show_message("KUBIOS", "Request failed")
                    app.change_state("MENU")
                    return
                app._kubios_stage = "waiting_1" if app._kubios_stage == "collecting_1" else "waiting_2"
                app.display.show_message("KUBIOS", "Sending...", "Waiting result")
            return

        if app._kubios_stage.startswith("waiting"):
            poll = app.wifi.poll_kubios_analysis(app._kubios_request_id)
            if poll["status"] == "pending":
                app.display.show_message("KUBIOS", "Waiting cloud", "SW1 to cancel")
                return
            if poll["status"] in ("timeout", "error"):
                app.display.show_message("KUBIOS", "Cloud failed", "Back to menu")
                app.change_state("MENU")
                return

            result = poll["result"] or {}
            app.storage.save_kubios_result(result, app.patient_name)
            app.display.show_kubios_results(result)
            if app._kubios_stage == "waiting_1":
                self._kubios_first = result
                app.measurement.start(collection_seconds=getattr(cfg, "MIN_COLLECTION_TIME_SECONDS", 30))
                app._kubios_stage = "collecting_2"
                app._kubios_request_id = None
                return

            comparison = self._build_comparison(self._kubios_first, result)
            app.storage.save_comparison_result(comparison, app.patient_name)
            app.change_state("MENU")

    def exit(self, app):
        app.measurement.stop()


class HistoryState(BaseState):
    def enter(self, app):
        app.history_entries = app.storage.load_history()
        app.history_index = 0
        app.history_detail = False
        app.display.show_history(app.history_entries, app.history_index)

    def update(self, app, events):
        if "BACK" in events:
            if app.history_detail:
                app.history_detail = False
                app.display.show_history(app.history_entries, app.history_index)
            else:
                app.change_state("MENU")
            return

        if app.history_detail:
            return

        if "NEXT" in events and app.history_entries:
            app.history_index = (app.history_index + 1) % len(app.history_entries)
            app.display.show_history(app.history_entries, app.history_index)
        if "SELECT" in events and app.history_entries:
            app.history_detail = True
            app.display.show_history_details(app.history_entries[app.history_index])


class AppController:
    def __init__(self):
        self.running = True
        self.menu_index = 0
        self.history_entries = []
        self.history_index = 0
        self.history_detail = False
        self.patient_name = getattr(cfg, "DEFAULT_PATIENT_NAME", "Unknown_Patient")

        self.display = DisplayManager()
        self.sensor = SensorManager()
        self.wifi = WiFiManager()
        self.storage = DataStorage()
        self.measurement = MeasurementEngine(self.sensor)

        self.states = {
            "MENU": MenuState(),
            "MEASURING": MeasuringState(),
            "HRV_ANALYSIS": LocalHrvState(),
            "KUBIOS": KubiosState(),
            "HISTORY": HistoryState(),
        }
        self.current_state_name = "MENU"
        self.current_state = self.states[self.current_state_name]
        self.current_state.enter(self)

    def initialize_network(self):
        self.display.show_message("Boot", "Connecting WiFi")
        self.wifi.connect()
        self.wifi.sync_ntp_time()
        self.display.show_message("Boot", "Waiting name", "MQTT or default")
        start = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start) < 10000:
            self.wifi.poll()
            name = self.wifi.check_patient_name_message()
            if name:
                self.patient_name = name
                break
            time.sleep_ms(50)

    def change_state(self, new_state):
        if new_state == self.current_state_name:
            return
        self.current_state.exit(self)
        self.current_state_name = new_state
        self.current_state = self.states[new_state]
        self.current_state.enter(self)

    def tick(self):
        self.sensor.update()
        self.wifi.poll()
        events = self.sensor.poll_buttons()
        if "BACK" in events and self.current_state_name != "MENU":
            self.change_state("MENU")
            return
        self.current_state.update(self, events)

    def run(self):
        self.initialize_network()
        gc_interval_ms = getattr(cfg, "GC_INTERVAL_MS", 5000)
        last_gc = time.ticks_ms()
        while self.running:
            self.tick()
            if time.ticks_diff(time.ticks_ms(), last_gc) >= gc_interval_ms:
                gc.collect()
                last_gc = time.ticks_ms()
            time.sleep_ms(10)

    def cleanup(self):
        self.measurement.stop()
        self.wifi.disconnect()
        self.display.show_message("Shutdown", "Goodbye")


def main():
    app = AppController()
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
