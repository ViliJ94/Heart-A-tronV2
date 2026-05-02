"""
Quick Installation Guide for Pico Heart Rate Monitor System
Run this file to see installation instructions
"""

INSTALLATION_GUIDE = """
╔══════════════════════════════════════════════════════════════════════════════╗
║          PICO HEART RATE MONITORING SYSTEM - INSTALLATION GUIDE             ║
║                          Level 5 - Complete System                          ║
╚══════════════════════════════════════════════════════════════════════════════╝

STEP 1: PREPARE YOUR PICO W
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Download MicroPython for Pico W:
   ▶ Visit: https://micropython.org/download/
   ▶ Choose: Raspberry Pi Pico W
   ▶ Download the .uf2 file (latest version)

2. Flash MicroPython to Pico W:
   ▶ Hold BOOTSEL button on Pico W while connecting to USB
   ▶ Pico appears as mass storage device
   ▶ Drag and drop the .uf2 file to the Pico
   ▶ Pico automatically reboots

3. Verify Installation:
   ▶ Install mpremote: pip install mpremote
   ▶ Connect Pico to USB
   ▶ Run: mpremote ls
   ▶ Should list files (showing MicroPython is installed)


STEP 2: COPY PROGRAM FILES TO PICO
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Using mpremote (recommended):

   # Create classes directory
   mpremote mkdir :/classes

   # Copy main files
   mpremote cp Code/Main.py :/main.py
   mpremote cp Code/ssd1306.py :/ssd1306.py

   # Copy classes (one by one or use script)
   mpremote cp Code/classes/display_manager.py :/classes/display_manager.py
   mpremote cp Code/classes/sensor_manager.py :/classes/sensor_manager.py
   mpremote cp Code/classes/wifi_manager.py :/classes/wifi_manager.py
   mpremote cp Code/classes/state_machine.py :/classes/state_machine.py
   mpremote cp Code/classes/measurement_engine.py :/classes/measurement_engine.py
   mpremote cp Code/classes/data_storage.py :/classes/data_storage.py
   mpremote cp Code/classes/graphics.py :/classes/graphics.py
   mpremote cp Code/classes/__init__.py :/classes/__init__.py

   # Create data directory
   mpremote mkdir :/Data

   # Verify installation
   mpremote ls -r


STEP 3: HARDWARE ASSEMBLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Connect components to Pico W:

   OLED Display (I2C, 128x64 SSD1306):
   ├─ VCC → Pico 3V3
   ├─ GND → Pico GND
   ├─ SDA → GP14 (pin 19)
   └─ SCL → GP15 (pin 20)

   PPG Heart Rate Sensor:
   ├─ VCC → Pico 3V3
   ├─ GND → Pico GND
   ├─ OUT → GP26 (ADC0)
   └─ (Follow sensor-specific instructions)

   Heartbeat LED:
   ├─ Positive (+) → GP20 (pin 26) via 220Ω resistor
   └─ Negative (-) → Pico GND

   Navigation Buttons:
   ├─ Button 0 (Select) → GP9 (pin 12) to GND (with pull-up enabled in code)
   ├─ Button 1 (Up)     → GP8 (pin 11) to GND
   └─ Button 2 (Down)   → GP7 (pin 10) to GND


STEP 4: POWER ON & TEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Connect Pico W to USB power
2. Watch for initialization sequence on OLED display:
   ▶ "Initializing..." message
   ▶ WiFi connection status
   ▶ Time synchronization
   ▶ "Waiting for Patient Name"

3. If OLED is blank:
   ├─ Check power and connections
   ├─ Verify I2C pins (SDA=14, SCL=15)
   ├─ Use i2cdetect script to find display address
   └─ Check for errors: mpremote

4. Monitor Output:
   mpremote mount /development
   # Then restart Pico to see serial console output


STEP 5: SETUP PC COMPANION APP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Install Python 3.8+ (if not already installed)
   ▶ Download from: https://www.python.org/downloads/

2. Install required packages:
   pip install -r requirements.txt

3. Install and run a Mosquitto broker (and CLI tools):
   - Install Mosquitto for your OS (includes mosquitto_pub/mosquitto_sub)
   - Ensure port 1883 is open on your network
   - Start the broker (service or manual)

4. Run the companion application:
   python PC_Companion_App.py

5. Expected behavior:
   ├─ Window opens with "Waiting for connection..."
   ├─ After few seconds: "Connected" (green)
   ├─ Enter patient name
   ├─ Click "Send to Pico"
   └─ Pico display shows patient name confirmation


STEP 6: CONFIGURE NETWORK (if needed)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Default WiFi Configuration (in code):
   SSID: KMD652_Group4
   Password: Group_4isDaBestest!
   MQTT Broker IP: 192.168.4.153
   MQTT Port: 1883

To change (edit wifi_manager.py):
   1. Open Code/classes/wifi_manager.py
   2. Update these lines:
      SSID = "Your_Network_Name"
      PASSWORD = "Your_Password"
      MQTT_BROKER = "192.168.x.x"
   3. Copy modified file back to Pico:
      mpremote cp Code/classes/wifi_manager.py :/classes/wifi_manager.py
   4. Restart Pico


TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Problem: OLED display shows nothing
└─ Solution: Check I2C connections, verify 0x3C i2c address

Problem: WiFi connection fails
└─ Solution: Check SSID/password, verify network is 2.4GHz (Pico W limitation)

Problem: PC app shows "Disconnected"
└─ Solution: Check MQTT broker is running, verify IP address

Problem: Buttons don't respond
└─ Solution: Check GPIO pins match configuration, verify pull-up resistors

Problem: PPG sensor not detecting beats
└─ Solution: Check sensor placement, ensure good skin contact, optimize lighting

For detailed logs:
   mpremote


TESTING CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

☐ Pico W powers on successfully
☐ OLED display shows initialization message
☐ WiFi connects and shows "Connected" status
☐ Time is synchronized (NTP)
☐ Display shows "Waiting for Patient Name"
☐ PC Companion App runs without errors
☐ PC app shows "Connected" status
☐ Patient name can be sent to Pico
☐ Pico confirms patient name on display
☐ Navigation buttons work (tested on menu)
☐ Heart rate measurement mode displays value
☐ HRV analysis collects data and produces results
☐ Data can be sent via MQTT (if broker available)
☐ History can be viewed
☐ All measurements are stored in /Data folder


NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Calibrate PPG sensor if needed
2. Test with actual measurements
3. Set up MQTT broker for data transmission
4. Integrate with Kubios Cloud API (if available)
5. Extend history and compare features
6. Add custom data analysis features

See README.md for detailed documentation.


═══════════════════════════════════════════════════════════════════════════════
Questions? Check README.md or look for errors on Pico REPL console.
═══════════════════════════════════════════════════════════════════════════════
"""

if __name__ == "__main__":
    print(INSTALLATION_GUIDE)
    
    # Save to file for reference
    try:
        with open("INSTALLATION.txt", "w") as f:
            f.write(INSTALLATION_GUIDE)
        print("\n✓ Installation guide saved to: INSTALLATION.txt")
    except:
        pass
