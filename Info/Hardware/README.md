# Hardware Documentation

This folder contains all hardware-related documentation for the Pico Heart Rate Monitor system.

## Contents

- **Pinouts.png** - Complete GPIO pin assignment diagram showing all connected components and their pins

## Pin Reference

| Component | GPIO | Pin | Function |
|-----------|------|-----|----------|
| OLED SDA | 14 | 19 | I2C Data |
| OLED SCL | 15 | 20 | I2C Clock |
| PPG Sensor | 26 | ADC0 | Heart Rate Input |
| Heartbeat LED | 20 | 26 | Visual Feedback |
| Button Select | 9 | 12 | Menu Input |
| Button Up | 8 | 11 | Navigation |
| Button Down | 7 | 10 | Navigation |

## Quick Assembly Checklist

- [ ] OLED Display: VCC, GND, SDA(14), SCL(15)
- [ ] PPG Sensor: VCC, GND, OUT→GP26
- [ ] Heartbeat LED: +→GP20(220Ω), -→GND
- [ ] Button 0: GP9→GND
- [ ] Button 1: GP8→GND
- [ ] Button 2: GP7→GND

All pins are configurable in `CONFIG.py`
