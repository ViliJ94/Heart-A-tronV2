# System Diagrams & Flowcharts

This folder contains system architecture diagrams and application flow documentation.

## Contents

- **Mermaid-diagram code.txt** - Mermaid.js source code for the system flowchart (can be rendered at mermaid.live)
- **mermaid-diagram (19).png** - Rendered system flowchart showing all modes and state transitions

## System Flow Overview

The diagram shows:

1. **Initialization Phase**: Power → System Init → WiFi → NTP Sync → Wait for Patient Name
2. **Main Menu**: Navigation to 4 measurement modes:
   - **MEASURE_HR**: Real-time heart rate display (continuous, no time limit)
   - **HRV_ANALYSIS**: 30+ second data collection with local RMSSD/SDNN calculation
   - **KUBIOS**: 30+ second data collection sent to Kubios Cloud
   - **HISTORY**: View and compare past measurements

3. **Data Flow**: Sensors → Processing → Display → Storage/WiFi

## Key States

- **INIT**: System initialization
- **MENU**: Main menu display
- **MEASURING**: Active measurement mode
- **HRV_ANALYSIS**: Local HRV calculation
- **KUBIOS**: Cloud transmission
- **HISTORY**: Data review
- **COMPARING**: Result comparison

See README.md for complete system documentation.
