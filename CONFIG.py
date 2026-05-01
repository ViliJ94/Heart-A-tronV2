"""
Configuration file for Pico Heart Rate Monitor System
Edit this file to customize your system without modifying main code
"""

# ─────────────────────────────────────────────────────────────────────────────
# WIFI CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# WiFi Network credentials
WIFI_SSID = "KMD652_Group4"
WIFI_PASSWORD = "Group_4isDaBestest!"

# NTP Server for time synchronization
NTP_SERVER = "0.pool.ntp.org"
NTP_TIMEZONE_OFFSET = 1  # UTC+1 for Central European Time

# ─────────────────────────────────────────────────────────────────────────────
# MQTT CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

MQTT_BROKER_IP = "192.168.4.153"
MQTT_BROKER_PORT = 1883

# MQTT Topics
MQTT_TOPIC_HRV_DATA = "hrv/data"
MQTT_TOPIC_PATIENT_NAME = "patient/name"
MQTT_TOPIC_KUBIOS_RESULTS = "kubios/results"
MQTT_TOPIC_DEVICE_STATUS = "device/status"

# Optional: MQTT Authentication (leave empty if no auth required)
MQTT_USERNAME = ""
MQTT_PASSWORD = ""

# ─────────────────────────────────────────────────────────────────────────────
# KUBIOS CLOUD CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Kubios Cloud API credentials (optional)
KUBIOS_API_KEY = "YOUR_API_KEY_HERE"
KUBIOS_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
KUBIOS_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
KUBIOS_API_URL = "https://analysis.kubioscloud.com/v2/sessions"

# ─────────────────────────────────────────────────────────────────────────────
# HARDWARE PIN CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# I2C Configuration (for OLED display)
I2C_NUMBER = 1  # I2C port number (0 or 1)
I2C_SCL_PIN = 15  # GPIO 15
I2C_SDA_PIN = 14  # GPIO 14
I2C_FREQUENCY = 400000  # 400 kHz

# OLED Display
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_ADDRESS = 0x3C  # I2C address

# Button Inputs (GPIO pins)
BUTTON_SELECT_PIN = 9  # GP9 (or 12 depending on pin notation)
BUTTON_UP_PIN = 8      # GP8
BUTTON_DOWN_PIN = 7    # GP7

# Button Debounce Time
BUTTON_DEBOUNCE_MS = 20

# LED Output (for heartbeat indication)
LED_HEARTBEAT_PIN = 20  # GP20

# PPG Sensor Input (ADC)
PPG_SENSOR_ADC_PIN = 26  # GP26 (ADC0)

# ─────────────────────────────────────────────────────────────────────────────
# MEASUREMENT PARAMETERS
# ─────────────────────────────────────────────────────────────────────────────

# Sampling Configuration
SAMPLE_RATE_HZ = 250  # 250 Hz sampling rate

# Signal Processing
FILTER_ALPHA = 0.95  # High-pass filter coefficient
MIN_PEAK_HEIGHT = 100  # Minimum ADC value threshold for beat detection
MIN_PEAK_DISTANCE_SAMPLES = 30  # Minimum samples between peaks

# HRV Collection
MIN_COLLECTION_TIME_SECONDS = 30
MIN_RR_INTERVALS_FOR_HRV = 30
MAX_RR_INTERVALS = 256

# Heart Rate Bounds (valid range)
MIN_HEART_RATE_BPM = 40
MAX_HEART_RATE_BPM = 200

# ─────────────────────────────────────────────────────────────────────────────
# DATA STORAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Storage paths
DATA_FOLDER_PATH = "/Data"
HISTORY_FILE_NAME = "history.json"
SESSION_FILE_NAME = "current_session.json"
BACKUP_FOLDER_NAME = "backups"

# Storage limits
MAX_HISTORY_ENTRIES = 100
MAX_SESSION_DATA_ENTRIES = 10

# Backup settings
AUTO_BACKUP_ENABLED = True
AUTO_BACKUP_INTERVAL_HOURS = 24

# ─────────────────────────────────────────────────────────────────────────────
# UI/DISPLAY CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Display contrast (0-255)
OLED_CONTRAST = 0x8F

# Display refresh rate
DISPLAY_UPDATE_RATE_MS = 100

# Menu settings
MENU_AUTO_TIMEOUT_SECONDS = 300  # Auto-return to menu after 5 minutes of inactivity
SHOW_ANIMATIONS = True

# ─────────────────────────────────────────────────────────────────────────────
# DEVICE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Device identification
DEVICE_ID = "pico_hrv_001"
DEVICE_NAME = "Pico HR Monitor"
FIRMWARE_VERSION = "1.0.0"

# Default patient name (if connection fails)
DEFAULT_PATIENT_NAME = "Unknown_Patient"

# ─────────────────────────────────────────────────────────────────────────────
# DEBUG & LOGGING
# ─────────────────────────────────────────────────────────────────────────────

# Enable verbose logging to console
DEBUG_MODE = True

# Log levels
LOG_LEVEL_INFO = 0
LOG_LEVEL_WARNING = 1
LOG_LEVEL_ERROR = 2
CURRENT_LOG_LEVEL = LOG_LEVEL_INFO

# Memory management
ENABLE_GARBAGE_COLLECTION = True
GC_INTERVAL_MS = 5000  # Run garbage collection every 5 seconds

# ─────────────────────────────────────────────────────────────────────────────
# PC COMPANION APP CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

# Window settings
APP_TITLE = "Pico Heart Rate Monitor - Companion App"
APP_WINDOW_WIDTH = 600
APP_WINDOW_HEIGHT = 500

# MQTT Timeout
MQTT_CONNECTION_TIMEOUT_SECONDS = 10
MQTT_MESSAGE_TIMEOUT_SECONDS = 5

# UI Theme
APP_BACKGROUND_COLOR = "#f0f0f0"
APP_ACCENT_COLOR = "#007ACC"

# ─────────────────────────────────────────────────────────────────────────────
# Notes for customization:
# ─────────────────────────────────────────────────────────────────────────────
# 1. To use this config in your Pico code:
#    - Copy this file to Pico as config.py
#    - In other modules, import: from config import *
#
# 2. For PC Companion App:
#    - Copy this file to same directory as PC_Companion_App.py
#    - Import configuration settings as needed
#
# 3. Default pin numbers assume Pico W standard pinout
#    - Verify pins match your actual circuit
#    - GPIO numbers may be referenced different ways in different tools
#
# 4. All values can be modified without recompiling the main program
#    - Just update relevant variables below
#    - Restart Pico for changes to take effect

