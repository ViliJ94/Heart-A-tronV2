# Network & WiFi Configuration

This folder contains network configuration details for WiFi and MQTT communication.

## Contents

| Item | Value |
|------|-------|
| WiFi SSID | KMD652_Group4 |
| WiFi Password | Group_4isDaBestest! |
| MQTT Broker IP | 192.168.4.153 |
| MQTT Port | 1883 |
| NTP Server | 0.pool.ntp.org |

## MQTT Topics

| Topic | Direction | Purpose |
|-------|-----------|---------|
| `hrv/data` | Pico → Server | Send HRV measurements |
| `patient/name` | App → Pico | Send patient name |
| `kubios/results` | Server → Pico | Receive Kubios analysis |
| `device/status` | Pico → Server | Device status updates |

## Quick Connection Steps

1. Ensure Pico is powered on
2. Wait for WiFi connection (display shows status)
3. NTP time syncs automatically
4. Run PC Companion App: `python PC_Companion_App.py`
5. Ensure app shows "Connected" status
6. Send patient name to Pico

## Troubleshooting

- **WiFi won't connect**: Check SSID/password, verify 2.4GHz band
- **MQTT errors**: Verify broker IP (192.168.4.153) is correct
- **PC app disconnected**: Check firewall, port 1883 must be open
- **Time not syncing**: Required for data timestamps, check internet

All settings are editable in `CONFIG.py`
