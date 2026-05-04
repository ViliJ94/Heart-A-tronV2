Yeah, that broke because the code block got split. Here’s a **clean fixed version** with proper Markdown formatting:

```markdown
# Pico Heart Rate Monitoring System

## Overview
The Pico Heart Rate Monitoring System is a compact embedded project built around the Raspberry Pi Pico W. It reads physiological data using a PPG sensor and processes it directly on the device using MicroPython. The system calculates heart rate (BPM) and heart rate variability (HRV), then displays the results on an SSD1306 OLED screen while also communicating with a companion PC application over MQTT.

The project is designed to demonstrate how low-cost hardware can be used to capture and process biometric data in real time. It does not aim to replace medical-grade equipment, but rather provides a functional and educational system that shows how heart-related metrics can be measured, stored, and analyzed.

Project paperwork and documentation are kept in `Info/Paperwork/` for clarity, while `deploy_to_pico.py` and `PC_Companion_App.py` stay in the repository root for easy access.

---

## Features
The system supports real-time heart rate measurement and basic HRV analysis, allowing users to observe how their physiological state changes over time. A simple menu-based user interface is displayed on the OLED screen and controlled using physical buttons, making interaction straightforward without requiring external devices.

Data is transmitted and received using MQTT, which allows the Pico to communicate with a PC application. This is used, for example, to receive the patient name before starting a session. Measurements are also stored locally in both JSON and binary formats, making it possible to review previous sessions directly on the device.

---

## Hardware
The system is built using commonly available components. The Raspberry Pi Pico W acts as the main controller and handles both processing and network communication. A PPG sensor connected to ADC pin GP26 is used to capture pulse signals. An SSD1306 OLED display connected via I2C provides visual output, while buttons on pins GP7, GP8, and GP9 allow navigation through the interface. An LED on GP20 is used for status indication.

---

## Software
The firmware is written in MicroPython, which allows direct interaction with hardware while keeping the code relatively simple and readable. The project also uses `mpremote` for file transfer and device interaction.

On the PC side, a Python-based companion application handles communication and user input, such as sending the patient name. MQTT communication is implemented using the `paho-mqtt` library, with a Mosquitto broker acting as the message server.

---

## Installation
Start by flashing MicroPython firmware onto the Raspberry Pi Pico W. Once that is done, install `mpremote` on your computer to handle communication with the board. Upload the project files to the Pico using `mpremote`, ensuring that the folder structure is preserved.

After the firmware is set up, run the PC companion application, which will be used to send data such as the patient name and receive measurement results.

---

## Network Configuration
Both the Pico and the PC must be connected to the same WiFi network for MQTT communication to work correctly. It is important to note that the Pico W only supports 2.4 GHz networks. The IP address of the MQTT broker must be configured in the project files so that the Pico can connect to it.

---

## Usage
After powering on the Pico, the system initializes and connects to the configured WiFi network. Once ready, the user can enter a patient name through the PC application. This name is then sent to the Pico via MQTT.

Navigation is done using the onboard buttons, allowing the user to move through the menu and start a measurement session. During measurement, the system collects PPG data, processes it, and displays BPM and HRV values in real time. The results are saved locally for later review.

---

## Project Structure
The project is organized in a modular way to keep different parts of the system separated and easier to maintain.

```

main.py
ssd1306.py
classes/
display_manager
sensor_manager
wifi_manager
state_machine
measurement_engine
data_storage
graphics

```

Each module handles a specific part of the system, such as sensor reading, data processing, display control, or state management.

---

## Troubleshooting
If the OLED display does not show anything, it is usually related to the I2C connection, so checking wiring and addresses is a good first step. If MQTT communication fails, the issue is often network-related, such as incorrect broker IP or devices not being on the same network.

If no data is being recorded, the PPG sensor connection should be verified, especially the ADC pin. In cases where buttons do not respond, checking GPIO connections and pull-up or pull-down configurations typically resolves the issue.

---

## Notes
This project is intended for educational and experimental use. While it demonstrates how BPM and HRV can be measured and processed, it should not be used for medical diagnosis or decision-making.
```
