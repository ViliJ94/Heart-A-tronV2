# QUICK REFERENCE CARD

## 🚀 QUICK START

```bash
# Step 1: Test system
python test_system.py

# Step 2: Deploy to Pico
python deploy_to_pico.py

# Step 3: Run PC app
pip install -r requirements.txt
python PC_Companion_App.py

# Step 4: Power on Pico and send patient name
```

---

## 📍 PIN CONFIGURATION

```
I2C OLED Display (128x64)     PPG Sensor              Button Controls
├─ SDA → GP14 (pin 19)        ├─ VCC → 3V3           ├─ Select → GP9
├─ SCL → GP15 (pin 20)        ├─ GND → GND           ├─ Up    → GP8
├─ VCC → 3V3                  └─ OUT → GP26 (ADC0)   └─ Down  → GP7
└─ GND → GND

Heartbeat LED
├─ Positive → GP20 (220Ω resistor)
└─ Negative → GND
```

---

## 📊 MEASUREMENT MODES

| Mode | Duration | Output | Cloud |
|------|----------|--------|-------|
| HR | Continuous | BPM | Local only |
| HRV | 30s+ | HR, RMSSD, SDNN | WiFi MQTT |
| Kubios | 30s+ | HR, Stress, LF/HF | Cloud API |
| History | On-demand | Past 100 measurements | - |

---

## 🎮 MENU NAVIGATION

```
MAIN MENU
├─ 1. Measure HR      → Real-time heart rate display
├─ 2. HRV Analysis    → 30s collection + local HRV calc
├─ 3. Kubios          → Send to cloud for analysis
└─ 4. History         → View past measurements

Button Controls:
  → Select (GP9): Confirm / Enter mode
  → Up (GP8):     Navigate up / Stop
  → Down (GP7):   Navigate down
```

---

## 📡 NETWORK SETTINGS

```
WiFi:
  SSID: KMD652_Group4
  Password: Group_4isDaBestest!

MQTT:
  Broker: 192.168.4.153
  Port: 1883
  
Topics:
  hrv/data          ← HRV results
  patient/name      ← Patient name input
  kubios/results    ← Kubios analysis
  device/status     ← Device status
```

---

## 📁 FILE LOCATIONS

| File | Purpose | Location |
|------|---------|----------|
| Measurements | History data | /Data/history.json |
| Session | Current data | /Data/current_session.json |
| Backups | Auto backups | /Data/backups/ |
| Config | Settings | CONFIG.py |

---

## 🔍 TROUBLESHOOTING FLOW

```
Issue: No display
  └─ Check I2C pins (14, 15)
  └─ Check 0x3C address
  └─ Power cycling required

Issue: WiFi won't connect
  └─ Check SSID/password
  └─ Check 2.4GHz band
  └─ Verify router

Issue: No heart rate detection
  └─ Check PPG sensor connection
  └─ Ensure skin contact
  └─ Optimize lighting
  └─ Adjust thresholds in CONFIG

Issue: PC app can't connect
  └─ Check MQTT broker running
  └─ Verify IP address
  └─ Check firewall/port 1883
```

---

## 🛠️ COMMON COMMANDS

```bash
# Deploy to Pico
python deploy_to_pico.py

# Run system tests
python test_system.py

# View installation guide
python INSTALLATION_GUIDE.py

# Start PC companion
python PC_Companion_App.py

# Using mpremote directly
mpremote ls -r              # List all files
mpremote mount /dev        # Mount main.py
mpremote cp file.py :/     # Copy to Pico
mpremote rm :/file.py      # Delete file
mpremote reset              # Reboot Pico
```

---

## 📦 DEPENDENCIES

**Pico Code**: No external dependencies (standalone MicroPython)

**PC Application**:
```bash
pip install paho-mqtt==1.6.1
# Tkinter included with Python
```

---

## 📊 PERFORMANCE METRICS

| Metric | Value |
|--------|-------|
| Sampling Rate | 250 Hz |
| Latency | ~100ms |
| Memory (Pico) | ~40KB buffers |
| Max Measurements | 100 history entries |
| WiFi Range | Standard 2.4GHz |
| Heartbeat LED | Pulses on beat detection |

---

## ⚙️ CUSTOMIZATION

Edit `CONFIG.py` to change:
- WiFi credentials
- MQTT broker IP/port
- GPIO pin assignments
- Sampling parameters
- Display contrast
- Heart rate thresholds
- Storage limits

---

## 📝 MEASUREMENT DATA FORMAT

```json
{
  "patient_name": "John_Doe",
  "timestamp": "2025-04-30T14:30:45",
  "mean_hr": 72,
  "mean_ppi": 833,
  "rmssd": 42,
  "sdnn": 58,
  "sample_count": 450,
  "device_id": "pico_hrv_001"
}
```

---

## 🎯 CALIBRATION HINTS

1. **PPG Sensor Baseline**: Keep sensor at constant position during initialization
2. **Peak Detection**: If missing beats, lower MIN_PEAK_HEIGHT in CONFIG
3. **False Peaks**: If detecting too many, increase MIN_PEAK_DISTANCE
4. **Display Contrast**: Adjust OLED_CONTRAST (0-255) in CONFIG

---

## 🚨 WARNINGS

⚠️ **Never**:
- Disconnect USB during file transfer
- Remove SD card while writing
- Hold buttons during WiFi connection
- Use 5V on GPIO pins (3V3 only!)

✅ **Always**:
- Use short USB cable for stability
- Power from good quality adapter
- Check pin voltage compatibility
- Back up data before updates

---

## 📞 SUPPORT RESOURCES

- **README.md** - Full documentation
- **INSTALLATION_GUIDE.py** - Step-by-step setup
- **test_system.py** - System diagnostics
- **Code comments** - Implementation details
- **CONFIG.py** - All parameters documented

---

## 🔐 DEFAULT CREDENTIALS

| Item | Value | Change |
|------|-------|--------|
| WiFi SSID | KMD652_Group4 | CONFIG.py |
| WiFi Pass | Group_4isDaBestest! | CONFIG.py |
| MQTT IP | 192.168.4.153 | CONFIG.py |
| MQTT Port | 1883 | CONFIG.py |
| OLED Address | 0x3C | CONFIG.py |

---

## 📋 DEPLOYMENT CHECKLIST

Before powering on Pico:
- [ ] File copied to Pico
- [ ] WiFi credentials verified
- [ ] MQTT broker running
- [ ] Hardware connections checked
- [ ] PC companion app ready
- [ ] Pins match configuration

After power on:
- [ ] OLED display shows "Initializing"
- [ ] WiFi connection completes
- [ ] NTP time syncs
- [ ] "Waiting for Patient Name" displays
- [ ] PC app shows "Connected"

---

## 📅 PROJECT INFO

- **Version**: 1.0
- **Level**: 5 (Complete)
- **Platform**: Raspberry Pi Pico W
- **Language**: MicroPython (Pico), Python 3 (PC)
- **Created**: April 2025
- **Status**: ✅ Production Ready

---

**Print this card or save as reference!**
Keep near your development station for quick lookup.

---
