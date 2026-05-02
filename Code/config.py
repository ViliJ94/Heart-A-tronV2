"""Lowercase config shim for MicroPython imports.

Keeps backwards compatibility with existing uppercase CONFIG.py.
"""

try:
    from CONFIG import *  # noqa: F401,F403
except ImportError:
    # Fallback defaults used on device if CONFIG.py is not present.
    WIFI_SSID = ""
    WIFI_PASSWORD = ""
    MQTT_BROKER_IP = "192.168.4.253"
    MQTT_BROKER_PORT = 1883
    MQTT_TOPIC_HRV_DATA = "hrv/data"
    MQTT_TOPIC_PATIENT_NAME = "patient/name"
    MQTT_TOPIC_KUBIOS_RESULTS = "kubios/results"
    MQTT_TOPIC_KUBIOS_REQUEST = "kubios/request"
    MQTT_TOPIC_DEVICE_STATUS = "device/status"
    DEVICE_ID = "pico_hrv_001"
    DEFAULT_PATIENT_NAME = "Unknown_Patient"

    I2C_NUMBER = 1
    I2C_SCL_PIN = 15
    I2C_SDA_PIN = 14
    I2C_FREQUENCY = 400000
    OLED_WIDTH = 128
    OLED_HEIGHT = 64
    OLED_ADDRESS = 0x3C

    BUTTON_SELECT_PIN = 9
    BUTTON_UP_PIN = 8
    BUTTON_DOWN_PIN = 7
    BUTTON_DEBOUNCE_MS = 20
    LED_HEARTBEAT_PIN = 20
    PPG_SENSOR_ADC_PIN = 26

    SAMPLE_RATE_HZ = 250
    FILTER_ALPHA = 0.95
    MIN_PEAK_HEIGHT = 100
    MIN_PEAK_DISTANCE_SAMPLES = 30
    MIN_COLLECTION_TIME_SECONDS = 30
    MIN_RR_INTERVALS_FOR_HRV = 30
    MAX_RR_INTERVALS = 256
    MIN_HEART_RATE_BPM = 40
    MAX_HEART_RATE_BPM = 200
    PPG_WAVEFORM_POINTS = 64
    PID_KP = 0.02
    PID_KI = 0.001
    PID_KD = 0.01
    PID_TARGET_AMPLITUDE = 800
    KUBIOS_RESULT_TIMEOUT_MS = 20000

    DATA_FOLDER_PATH = "/Data"
    HISTORY_FILE_NAME = "history.json"
    SESSION_FILE_NAME = "current_session.json"
    BACKUP_FOLDER_NAME = "backups"
    MAX_HISTORY_ENTRIES = 3
    GC_INTERVAL_MS = 5000
