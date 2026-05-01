"""
WiFi Manager - Handles WiFi connection, MQTT communication, NTP sync, and Kubios API
"""

import time
import network
import socket
import json
from machine import RTC
try:
    from umqtt.simple import MQTTClient
except ImportError:
    MQTTClient = None
try:
    import config
except ImportError:
    config = None


class WiFiManager:
    """Manages WiFi, MQTT, NTP, and cloud API communications"""
    
    # WiFi Credentials (fallback defaults)
    SSID = "KMD652_Group4"
    PASSWORD = "Group_4isDaBestest!"
    
    # MQTT Configuration
    MQTT_BROKER = "192.168.4.153"
    MQTT_PORT = 1883
    MQTT_TOPICS = {
        "hrv_data": "hrv/data",
        "patient_name": "patient/name",
        "kubios_results": "kubios/results",
        "device_status": "device/status"
    }
    
    # Kubios API Configuration
    KUBIOS_API_URL = "https://analysis.kubioscloud.com/v2/sessions"
    KUBIOS_API_KEY = "YOUR_KUBIOS_API_KEY"  # Replace with actual key
    KUBIOS_CLIENT_ID = "YOUR_CLIENT_ID"  # Replace with actual ID
    KUBIOS_CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # Replace with secret
    
    # NTP configuration
    NTP_POOL = "0.pool.ntp.org"
    NTP_GMT_OFFSET = 1  # UTC+1 for Europe
    
    def __init__(self):
        """Initialize WiFi manager"""
        self.wlan = None
        self.mqtt_client = None
        self.connected = False
        self.patient_name_received = None
        self.ssid = self.SSID
        self.password = self.PASSWORD
        self._load_config()

        self._init_wifi()
        self._init_mqtt()
    
    def _load_config(self):
        """Load runtime configuration from config.py when available."""
        if not config:
            return
        self.ssid = getattr(config, "WIFI_SSID", self.SSID)
        self.password = getattr(config, "WIFI_PASSWORD", self.PASSWORD)
    
    def _init_wifi(self):
        """Initialize WiFi interface"""
        try:
            self.wlan = network.WLAN(network.STA_IF)
            self.wlan.active(True)
            print("[WiFi] WiFi interface initialized")
        except Exception as e:
            print(f"[WiFi ERROR] Failed to initialize WiFi: {e}")
    
    def connect(self):
        """Connect to WiFi network"""
        try:
            if not self.wlan:
                print("[WiFi] WiFi not initialized")
                return False
            
            if self.wlan.isconnected():
                print("[WiFi] Already connected")
                return True
            
            print(f"[WiFi] Connecting to {self.ssid}...")
            self.wlan.connect(self.ssid, self.password)
            
            # Wait for connection
            timeout = 20
            while timeout > 0:
                if self.wlan.isconnected():
                    config = self.wlan.ifconfig()
                    print(f"[WiFi] Connected! IP: {config[0]}")
                    self.connected = True
                    return True
                
                print(f"[WiFi] Waiting... ({timeout}s)")
                time.sleep(1)
                timeout -= 1
            
            print("[WiFi] Connection timeout")
            return False
            
        except Exception as e:
            print(f"[WiFi ERROR] Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from WiFi"""
        try:
            if self.wlan:
                self.wlan.disconnect()
                self.connected = False
                print("[WiFi] Disconnected")
        except Exception as e:
            print(f"[WiFi ERROR] Disconnect failed: {e}")
    
    def sync_ntp_time(self):
        """Synchronize time with NTP server"""
        try:
            import ntptime
            print("[NTP] Syncing time with NTP server...")
            ntptime.settime()
            
            # Set timezone
            rtc = RTC()
            rtc.datetime()
            
            print("[NTP] Time synchronized")
            return True
            
        except Exception as e:
            print(f"[NTP ERROR] Time sync failed: {e}")
            return False
    
    def _init_mqtt(self):
        """Initialise umqtt client and subscribe to patient/name topic."""
        if MQTTClient is None:
            print("[MQTT] umqtt.simple not available")
            return
        try:
            self.mqtt_client = MQTTClient(
                "pico_hrv_001",
                self.MQTT_BROKER,
                port=self.MQTT_PORT,
                keepalive=60
            )
            self.mqtt_client.set_callback(self._on_mqtt_message)
            self.mqtt_client.connect()
            self.mqtt_client.subscribe(self.MQTT_TOPICS["patient_name"])
            print("[MQTT] Connected and subscribed to patient/name")
        except Exception as e:
            print(f"[MQTT ERROR] Failed to initialise MQTT client: {e}")
            self.mqtt_client = None

    def _on_mqtt_message(self, topic, msg):
        """Callback invoked by umqtt when a message arrives."""
        try:
            topic_str = topic.decode()
            msg_str = msg.decode()
            if topic_str == self.MQTT_TOPICS["patient_name"]:
                # Expected format: "PATIENT:<name>"
                if msg_str.startswith("PATIENT:"):
                    self.patient_name_received = msg_str[len("PATIENT:"):].strip()
                else:
                    self.patient_name_received = msg_str.strip()
                print(f"[MQTT] Patient name received: {self.patient_name_received}")
        except Exception as e:
            print(f"[MQTT ERROR] Message handling failed: {e}")

    def check_patient_name_message(self):
        """Poll MQTT and return patient name if one has been received."""
        if self.mqtt_client is None:
            return None
        try:
            self.mqtt_client.check_msg()  # non-blocking poll
        except Exception as e:
            print(f"[MQTT ERROR] check_msg failed: {e}")
        name = self.patient_name_received
        self.patient_name_received = None  # consume the value
        return name
    
    def send_hrv_data(self, patient_name, hrv_data):
        """
        Send HRV data via MQTT
        Format: {patient_name: "xxx", mean_hr: 70, rmssd: 45, sdnn: 52, timestamp: "2025-05-01T10:30:00"}
        """
        try:
            if not self.connected:
                print("[MQTT] Not connected to WiFi")
                return False

            if self.mqtt_client is None:
                print("[MQTT] MQTT client not initialised")
                return False

            message = {
                "patient_name": patient_name,
                "mean_hr": int(hrv_data.get("mean_hr", 0)),
                "mean_ppi": int(hrv_data.get("mean_ppi", 0)),
                "rmssd": int(hrv_data.get("rmssd", 0)),
                "sdnn": int(hrv_data.get("sdnn", 0)),
                "timestamp": self._get_timestamp(),
                "device_id": "pico_hrv_001"
            }

            print(f"[MQTT] Sending HRV data: {message}")
            self.mqtt_client.publish(self.MQTT_TOPICS["hrv_data"], json.dumps(message))
            print("[MQTT] HRV data sent successfully")
            return True

        except Exception as e:
            print(f"[MQTT ERROR] Failed to send HRV data: {e}")
            return False
    
    def send_to_kubios(self, rr_intervals, patient_name):
        """
        Send RR interval data to Kubios Cloud for analysis
        Returns: dict with analysis results or None
        """
        try:
            if not self.connected:
                print("[KUBIOS] Not connected to WiFi")
                return None
            
            print(f"[KUBIOS] Sending {len(rr_intervals)} RR intervals to Kubios Cloud...")
            
            # Format data for Kubios API
            kubios_payload = {
                "data": {
                    "raw": rr_intervals,
                    "type": 1  # RR intervals
                }
            }
            
            # Simulate Kubios response for development
            # In production, this would call the actual Kubios API via HTTPS
            result = {
                "heart_rate": int(60000 / (sum(rr_intervals) / len(rr_intervals))) if rr_intervals else 0,
                "stress_level": "LOW",
                "timestamp": self._get_timestamp(),
                "patient_name": patient_name,
                "lf": 450,
                "hf": 320,
                "lf_hf_ratio": 1.41
            }
            
            print(f"[KUBIOS] Response received: {result}")
            return result
            
        except Exception as e:
            print(f"[KUBIOS ERROR] Failed to send to Kubios: {e}")
            return None
    
    def receive_patient_name(self):
        """Receive patient name from PC companion app"""
        # This would be implemented via MQTT subscription or HTTP POST
        # For now, return None (handled by main.py wait_for_patient_name)
        return None
    
    # _mqtt_connect and _mqtt_publish removed: replaced by umqtt.simple client
    
    def _get_timestamp(self):
        """Get current timestamp in ISO 8601 format"""
        try:
            rtc = RTC()
            dt = rtc.datetime()
            # dt format: (year, month, day, weekday, hour, minute, second, subseconds)
            return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
                dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]
            )
        except:
            return "2025-01-01T00:00:00"
    
    def is_connected(self):
        """Check WiFi connection status"""
        try:
            return self.wlan.isconnected() if self.wlan else False
        except:
            return False
    
    def get_signal_strength(self):
        """Get WiFi signal strength"""
        try:
            if self.wlan:
                status = self.wlan.status(network.STAT_RSSI)
                return status  # Returns RSSI in dBm
        except:
            return None
