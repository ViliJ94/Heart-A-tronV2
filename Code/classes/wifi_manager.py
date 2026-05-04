"""WiFi/MQTT/NTP integration with non-blocking polling helpers."""

import time
import json
import network
from machine import RTC
import socket

try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None

try:
    import config as cfg
except ImportError:
    cfg = None


class WiFiManager:
    """Handle network connectivity and message exchange."""

    def __init__(self):
        self.ssid = getattr(cfg, "WIFI_SSID", "")
        self.password = getattr(cfg, "WIFI_PASSWORD", "")
        self.mqtt_broker = getattr(cfg, "MQTT_BROKER_IP", "")
        self.mqtt_port = getattr(cfg, "MQTT_BROKER_PORT", 21883)
        self.topic_hrv = getattr(cfg, "MQTT_TOPIC_HRV_DATA", "hrv/data")
        self.topic_patient = getattr(cfg, "MQTT_TOPIC_PATIENT_NAME", "patient/name")
        self.topic_kubios = getattr(cfg, "MQTT_TOPIC_KUBIOS_RESULTS", "kubios/results")
        self.topic_kubios_req = getattr(cfg, "MQTT_TOPIC_KUBIOS_REQUEST", "kubios/request")
        self.topic_status = getattr(cfg, "MQTT_TOPIC_DEVICE_STATUS", "device/status")
        self.device_id = getattr(cfg, "DEVICE_ID", "pico_hrv_001")
        self.kubios_timeout_ms = int(getattr(cfg, "KUBIOS_RESULT_TIMEOUT_MS", 20000))

        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.mqtt_client = None
        self.connected = False
        self.patient_name_received = None
        self._kubios_last_response = None
        self._kubios_pending = {}
        self.mqtt_init_error = None
        self.last_mqtt_check_error = None
        self.last_kubios_request_id = None
        self.last_kubios_response = None

    def connect(self):
        try:
            if self.wlan.isconnected():
                self.connected = True
                return True
            self.wlan.connect(self.ssid, self.password)
            timeout = 20
            while timeout > 0:
                if self.wlan.isconnected():
                    self.connected = True
                    if self._init_mqtt():
                        self.publish_status("online")
                    else:
                        print("[WiFi] MQTT init failed after WiFi connect:", self.mqtt_init_error)
                    return True
                time.sleep(1)
                timeout -= 1
        except Exception as exc:
            print("[WiFi] connect failed:", exc)
        return False

    def _init_mqtt(self):
        if self.mqtt_client:
            return True
        if MQTTClient is None:
            self.mqtt_init_error = "umqtt.simple not available"
            print("[MQTT] init failed: umqtt.simple not available")
            return False
        if not self.mqtt_broker or not self.mqtt_port:
            self.mqtt_init_error = f"broker or port not configured (broker={self.mqtt_broker}, port={self.mqtt_port})"
            print("[MQTT] init failed: broker or port not configured")
            return False
        try:
            # Avoid getting stuck when broker is unreachable
            try:
                socket.setdefaulttimeout(3)
            except Exception:
                pass
            print("[MQTT] connecting to %s:%s as %s" % (self.mqtt_broker, self.mqtt_port, self.device_id))
            self.mqtt_client = MQTTClient(self.device_id, self.mqtt_broker, port=self.mqtt_port, keepalive=60)
            self.mqtt_client.set_callback(self._on_mqtt_message)
            self.mqtt_client.connect()
            self.mqtt_client.subscribe(self.topic_patient)
            self.mqtt_client.subscribe(self.topic_kubios)
            print("[MQTT] subscribed:", self.topic_patient, self.topic_kubios)
            self.mqtt_init_error = None
            return True
        except Exception as exc:
            self.mqtt_init_error = str(exc)
            print("[MQTT] init failed:", self.mqtt_init_error)
            self.mqtt_client = None
            return False
        finally:
            try:
                socket.setdefaulttimeout(None)
            except Exception:
                pass

    def _on_mqtt_message(self, topic, msg):
        if topic is None or topic == b'' or msg is None:
            print("[MQTT] DROP EMPTY MESSAGE (topic or msg is empty)")
            return
        print("[MQTT RAW TOPIC]", topic)
        print("[MQTT RAW MSG]", msg)
        """Callback invoked by umqtt when a message arrives."""
        try:
            topic_str = topic.decode() if topic else ""
        except Exception:
                topic_str = ""

        try:
            msg_str = msg.decode() if msg else ""
        except Exception:
                 msg_str = ""
        if topic_str == "":
            print("[MQTT] EMPTY TOPIC AFTER DECODE → IGNORED")
            return
        print("[MQTT] rx topic=%s msg=%s" % (topic_str, msg_str))
        if topic_str == self.topic_patient:
            # Expected format: "PATIENT:<name>"
            if msg_str.startswith("PATIENT:"):
                self.patient_name_received = msg_str[len("PATIENT:"):].strip()
            else:
                self.patient_name_received = msg_str.strip()
            print("[MQTT] patient_name_received:", self.patient_name_received)
        elif topic_str == self.topic_kubios:
            try:
                payload = json.loads(msg_str)
            except Exception as e:
                print(f"[MQTT ERROR] Invalid Kubios payload: {e}")
                payload = {"status": "error", "error": "invalid payload", "raw": msg_str}
            self._kubios_last_response = payload
            self.last_kubios_response = payload
            print("[MQTT] kubios payload stored", payload)
        else:
            print("[MQTT] received unexpected topic:", topic_str)
    def check_patient_name_message(self):
        """Poll MQTT and return patient name if available."""
        if self.mqtt_client is None:
            print("[MQTT] check_patient_name_message: mqtt_client is None")
            return None
        try:
            self.mqtt_client.check_msg()
        except Exception as exc:
            self.last_mqtt_check_error = str(exc)
            print("[MQTT] check_msg error:", self.last_mqtt_check_error)
            pass
        name = self.patient_name_received
        self.patient_name_received = None
        return name

    def poll(self):
        if self.mqtt_client:
            try:
                self.mqtt_client.check_msg()
            except Exception:
                pass

    def publish_status(self, status):
        if not self.mqtt_client:
            return False
        try:
            payload = {"device_id": self.device_id, "status": status, "timestamp": self._get_timestamp()}
            self.mqtt_client.publish(self.topic_status, json.dumps(payload))
            return True
        except Exception:
            return False

    def send_hrv_data(self, patient_name, hrv_data):
        try:
            if self.mqtt_client is None:
                return False

            message = {
                "patient_name": patient_name,
                "mean_hr": int(hrv_data.get("mean_hr", 0)),
                "mean_ppi": int(hrv_data.get("mean_ppi", 0)),
                "rmssd": int(hrv_data.get("rmssd", 0)),
                "sdnn": int(hrv_data.get("sdnn", 0)),
                "timestamp": self._get_timestamp(),
                "device_id": self.device_id
            }

            self.mqtt_client.publish(self.topic_hrv, json.dumps(message))
            return True

        except Exception as e:
            print(f"[MQTT ERROR] Failed to send HRV data: {e}")
            return False
    
    def request_kubios_analysis(self, rr_intervals, patient_name):
        """Send kubios analysis request; returns request id or None."""
        if not rr_intervals or not self.mqtt_client:
            return None
        request_id = "%s_%d" % (self.device_id, time.ticks_ms())
        payload = {
            "request_id": request_id,
            "device_id": self.device_id,
            "patient_name": patient_name,
            "timestamp": self._get_timestamp(),
            "rr_intervals": rr_intervals
        }
        try:
            self.mqtt_client.publish(self.topic_kubios_req, json.dumps(payload))
            self._kubios_pending[request_id] = time.ticks_ms()
            return request_id
        except Exception as e:
            print(f"[KUBIOS ERROR] Failed to request Kubios: {e}")
            return None

    def poll_kubios_analysis(self, request_id):
        """Return dict with status='pending'|'ok'|'timeout'|'error'."""
        self.poll()
        if request_id not in self._kubios_pending:
            print("[KUBIOS] poll_kubios_analysis: request_id not pending", request_id)
            return {"status": "error", "result": None}

        start_ms = self._kubios_pending[request_id]
        if time.ticks_diff(time.ticks_ms(), start_ms) > self.kubios_timeout_ms:
            del self._kubios_pending[request_id]
            print("[KUBIOS] poll_kubios_analysis timeout", request_id)
            return {"status": "timeout", "result": None}

        payload = self._kubios_last_response
        if not payload:
            return {"status": "pending", "result": None}

        response_req_id = payload.get("request_id", "")
        if response_req_id and response_req_id != request_id:
            print("[KUBIOS] mismatched request_id", request_id, response_req_id)
            return {"status": "pending", "result": None}

        self._kubios_last_response = None
        del self._kubios_pending[request_id]

        if payload.get("status", "ok") not in ("ok", "success"):
            print("[KUBIOS] response error payload:", payload)
            return {"status": "error", "result": payload}

        result = payload.get("result", payload)
        return {"status": "ok", "result": result}

    def send_to_kubios(self, rr_intervals, patient_name):
        """Send RR interval request to Kubios and wait for a response."""
        if self.mqtt_client is None:
            print("[KUBIOS] send failed: MQTT client unavailable")
            return None

        request_id = self.request_kubios_analysis(rr_intervals, patient_name)
        if request_id:
            self.last_kubios_request_id = request_id
            print("[KUBIOS] sent request", request_id, "patient_name=", patient_name)
        if not request_id:
            print("[KUBIOS] send failed: could not create request")
            return None

        deadline = time.ticks_add(time.ticks_ms(), self.kubios_timeout_ms)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            result = self.poll_kubios_analysis(request_id)
            if result["status"] == "ok":
                return result["result"]
            if result["status"] == "error":
                print("[KUBIOS] response error:", result["result"])
                return None
            if result["status"] == "timeout":
                print("[KUBIOS] request timed out")
                return None
            time.sleep(0.1)
        print("[KUBIOS] request timeout waiting for response")
        return None

    def _get_timestamp(self):
        try:
            rtc = RTC()
            dt = rtc.datetime()
            return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
                dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]
            )
        except Exception:
            return "2025-01-01T00:00:00"

    def sync_ntp_time(self):
        try:
            import ntptime
            ntptime.settime()
            return True
        except Exception:
            return False

    def disconnect(self):
        self.publish_status("offline")
        try:
            if self.mqtt_client:
                self.mqtt_client.disconnect()
        except Exception:
            pass
        try:
            if hasattr(self.wlan, "disconnect"):
                self.wlan.disconnect()
        except Exception:
            pass
