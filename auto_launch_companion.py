"""
Auto-launch helper: starts PC_Companion_App.py when Pico appears on COM9.

Usage:
    python auto_launch_companion.py
"""

import subprocess
import sys
import time

import serial
from serial.tools import list_ports


TARGET_PORT = "COM9"
POLL_SECONDS = 1.0


def pico_present_on_port(port_name):
    """Return True if the requested COM port currently exists."""
    for port in list_ports.comports():
        if port.device.upper() == port_name.upper():
            return True
    return False


def wait_for_pico(port_name):
    """Block until Pico serial port appears and can be opened."""
    print(f"[launcher] Waiting for Pico on {port_name}...")
    while True:
        if pico_present_on_port(port_name):
            try:
                probe = serial.Serial(port_name, 115200, timeout=0.5)
                probe.close()
                print(f"[launcher] Pico detected on {port_name}")
                return
            except Exception:
                pass
        time.sleep(POLL_SECONDS)


def launch_companion_app():
    """Launch companion app and wait for exit."""
    print("[launcher] Starting PC_Companion_App.py")
    proc = subprocess.Popen([sys.executable, "PC_Companion_App.py"])
    return proc.wait()


def main():
    wait_for_pico(TARGET_PORT)
    code = launch_companion_app()
    sys.exit(code)


if __name__ == "__main__":
    main()
