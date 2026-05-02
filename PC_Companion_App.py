"""
PC Companion Application - Patient Name Input Interface
Tkinter-based GUI for sending patient information to Pico via MQTT

Requires a running Mosquitto broker and the Mosquitto CLI tools:
  - mosquitto_pub
  - mosquitto_sub
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
from datetime import datetime
import subprocess
import shutil
import os
import json as _json
import socket

try:
    import CONFIG as cfg  # project-wide config (preferred)
except Exception:
    cfg = None


def _agent_dbg(hypothesis_id, location, message, data=None, run_id="pre-fix"):
    """Append NDJSON debug line to debug-3d63e7.log (no secrets)."""
    try:
        log_path = os.path.join(os.path.dirname(__file__), "debug-3d63e7.log")
        payload = {
            "sessionId": "3d63e7",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data or {},
            "timestamp": int(time.time() * 1000),
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(_json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _resolve_mosquitto_cli(exe_name):
    """
    Resolve mosquitto_pub/sub executable path.
    Prefer PATH; otherwise try common Windows install locations.
    """
    p = shutil.which(exe_name)
    if p:
        return p
    candidates = []
    # Allow explicit override via CONFIG.py (PC-side only)
    try:
        bin_dir = getattr(cfg, "MOSQUITTO_BIN_DIR", "") if cfg else ""
        if bin_dir:
            candidates.append(os.path.join(str(bin_dir), exe_name + ".exe"))
            candidates.append(os.path.join(str(bin_dir), exe_name))
    except Exception:
        pass
    # Common Windows installer location
    candidates.append(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "mosquitto", exe_name + ".exe"))
    candidates.append(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Mosquitto", exe_name + ".exe"))
    # Chocolatey typical bin (if user installed it that way)
    candidates.append(os.path.join(os.environ.get("ChocolateyInstall", r"C:\ProgramData\chocolatey"), "bin", exe_name + ".exe"))
    for c in candidates:
        try:
            if os.path.exists(c):
                return c
        except Exception:
            continue
    return None


class PicoCompanionApp:
    """Main application window for Pico companion app"""
    
    # MQTT Configuration (must match Pico settings)
    MQTT_BROKER = getattr(cfg, "MQTT_BROKER_IP", "127.0.0.1") if cfg else "127.0.0.1"
    MQTT_PORT = int(getattr(cfg, "MQTT_BROKER_PORT", 1883)) if cfg else 1883
    MQTT_TOPIC_PATIENT_NAME = getattr(cfg, "MQTT_TOPIC_PATIENT_NAME", "patient/name") if cfg else "patient/name"
    MQTT_TOPIC_DEVICE_STATUS = getattr(cfg, "MQTT_TOPIC_DEVICE_STATUS", "device/status") if cfg else "device/status"
    
    def __init__(self, root):
        """Initialize the companion application"""
        self.root = root
        self.root.title("Pico Heart Rate Monitor - Companion App")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")
        
        # Mosquitto subprocess handles
        self._sub_process = None
        self._sub_thread = None
        self._stop_event = threading.Event()
        self.connected = False
        self._connected_once = False
        
        # Create UI
        self._create_ui()
        self._connect_mqtt()
        
        # Status update loop
        self.root.after(1000, self._update_status)
    
    def _create_ui(self):
        """Create user interface elements"""
        # Title frame
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=20, padx=20)
        
        title_label = ttk.Label(title_frame, text="Pico Heart Rate Monitor", 
                               font=("Arial", 18, "bold"))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Companion Application",
                                  font=("Arial", 10, "italic"), foreground="gray")
        subtitle_label.pack()
        
        # Connection status frame
        self.conn_frame = ttk.LabelFrame(self.root, text="Connection Status")
        self.conn_frame.pack(pady=10, padx=20, fill=tk.X)
        
        self.conn_status_label = ttk.Label(self.conn_frame, text="Disconnected",
                                          foreground="red", font=("Arial", 10, "bold"))
        self.conn_status_label.pack(pady=10)
        
        self.conn_details_label = ttk.Label(self.conn_frame, text="",
                                           foreground="gray", font=("Arial", 9))
        self.conn_details_label.pack(pady=5)
        
        # Patient configuration frame
        patient_frame = ttk.LabelFrame(self.root, text="Patient Configuration")
        patient_frame.pack(pady=15, padx=20, fill=tk.X)
        
        ttk.Label(patient_frame, text="Patient Name:", font=("Arial", 10)).pack(anchor=tk.W, padx=10, pady=5)
        
        self.patient_entry = ttk.Entry(patient_frame, font=("Arial", 12), width=30)
        self.patient_entry.pack(pady=5, padx=10, fill=tk.X)
        self.patient_entry.insert(0, "Unnamed_Patient")
        
        # Buttons frame
        button_frame = ttk.Frame(patient_frame)
        button_frame.pack(pady=15, padx=10, fill=tk.X)
        
        self.send_button = ttk.Button(button_frame, text="Send to Pico",
                                     command=self._send_patient_name, state=tk.DISABLED)
        self.send_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(button_frame, text="Clear",
                                 command=lambda: self.patient_entry.delete(0, tk.END))
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Message log frame
        log_frame = ttk.LabelFrame(self.root, text="Activity Log")
        log_frame.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        self.log_text = tk.Text(log_frame, height=10, font=("Courier", 9),
                               yscrollcommand=scrollbar.set)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.config(command=self.log_text.yview)
        
        # Make log read-only
        self.log_text.config(state=tk.DISABLED)
        
        # Info text at bottom
        info_label = ttk.Label(self.root,
                             text="Ensure Pico is powered on and connected to WiFi",
                             font=("Arial", 8), foreground="gray")
        info_label.pack(pady=10)
    
    def _connect_mqtt(self):
        """Connect to MQTT broker in background thread (Mosquitto CLI)."""
        thread = threading.Thread(target=self._mqtt_connect_thread, daemon=True)
        thread.start()
    
    def _mqtt_connect_thread(self):
        """Background thread for MQTT connection (starts mosquitto_sub)."""
        try:
            # #region agent log
            path_env = os.environ.get("PATH", "")
            path_parts = [p for p in path_env.split(os.pathsep) if p]
            # keep it non-sensitive: only count + last segment names
            safe_path = {"count": len(path_parts), "tail": [p[-60:] for p in path_parts[-5:]]}
            which_sub = _resolve_mosquitto_cli("mosquitto_sub")
            which_pub = _resolve_mosquitto_cli("mosquitto_pub")
            _agent_dbg(
                "H2",
                "PC_Companion_App.py:_mqtt_connect_thread",
                "mosquitto_cli_presence",
                {
                    "which_sub": which_sub,
                    "which_pub": which_pub,
                    "path": safe_path,
                    "cwd": os.getcwd(),
                    "broker": str(self.MQTT_BROKER),
                    "port": int(self.MQTT_PORT),
                },
            )
            # #endregion

            if not which_sub or not which_pub:
                raise RuntimeError(
                    "Mosquitto CLI not found. Install Mosquitto and ensure mosquitto_sub/mosquitto_pub are on PATH."
                )

            # Extra debug to understand connectivity failures
            self._log_message(f"[MQTT DEBUG] broker={self.MQTT_BROKER} port={self.MQTT_PORT}")
            self._log_message(f"[MQTT DEBUG] mosquitto_sub={which_sub}")
            self._log_message(f"[MQTT DEBUG] mosquitto_pub={which_pub}")
            try:
                socket.create_connection((str(self.MQTT_BROKER), int(self.MQTT_PORT)), timeout=2).close()
                self._log_message("[MQTT DEBUG] TCP probe: OK")
            except Exception as exc:
                self._log_message(f"[MQTT DEBUG] TCP probe failed: {exc}")

            self._log_message("Starting Mosquitto subscription (device status)...")

            # Subscribe continuously to device status; we treat 'sub running' as connected.
            # Use text mode for easier line parsing on Windows.
            sub_cmd = [
                which_sub,
                "-h", str(self.MQTT_BROKER),
                "-p", str(self.MQTT_PORT),
                "-t", str(self.MQTT_TOPIC_DEVICE_STATUS),
                "-v",
            ]
            self._log_message("[MQTT DEBUG] sub cmd: " + " ".join(map(str, sub_cmd)))
            self._sub_process = subprocess.Popen(
                sub_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # If mosquitto_sub exits immediately, surface the exit code quickly.
            try:
                time.sleep(0.2)
                rc = self._sub_process.poll()
                if rc is not None:
                    self._log_message(f"[MQTT DEBUG] mosquitto_sub exited early rc={rc}", "error")
            except Exception:
                pass

            # Do NOT mark connected yet. We mark connected only after receiving
            # at least one message, which proves broker reachability.
            self.connected = False
            self._connected_once = False
            self.root.after(100, lambda: self.send_button.config(state=tk.DISABLED))
            self._log_message("[MQTT DEBUG] Waiting for first message to confirm connection...")

            self._sub_thread = threading.Thread(target=self._mosquitto_sub_reader, daemon=True)
            self._sub_thread.start()
        except Exception as e:
            self._log_message(f"MQTT Connection Error: {e}", "error")
    
    def _mosquitto_sub_reader(self):
        """Read lines from mosquitto_sub and append to UI log."""
        try:
            if not self._sub_process or not self._sub_process.stdout:
                return
            for line in self._sub_process.stdout:
                if self._stop_event.is_set():
                    break
                line = (line or "").strip()
                if not line:
                    continue

                # Some failures are printed to stdout/stderr; surface them and keep disconnected.
                lower = line.lower()
                if ("error:" in lower) or ("connection refused" in lower) or ("not authorised" in lower) or ("timed out" in lower):
                    self._log_message("[MQTT DEBUG] sub output: " + line, "error")
                    continue

                # First non-error line implies we are receiving messages via broker.
                if not self._connected_once:
                    self._connected_once = True
                    self.connected = True
                    try:
                        self.root.after(0, lambda: self.send_button.config(state=tk.NORMAL))
                    except Exception:
                        pass
                    self._log_message("✓ Connected (confirmed by incoming message)")

                # mosquitto_sub -v prints: "<topic> <payload>"
                if line.startswith(self.MQTT_TOPIC_DEVICE_STATUS + " "):
                    payload = line[len(self.MQTT_TOPIC_DEVICE_STATUS) + 1 :]
                else:
                    payload = line
                self._log_message(f"Device: {payload}")
        except Exception as e:
            self._log_message(f"Subscription reader error: {e}", "error")
        finally:
            try:
                if self._sub_process:
                    rc = self._sub_process.poll()
                    if rc is not None:
                        self._log_message(f"[MQTT DEBUG] mosquitto_sub exit rc={rc}")
            except Exception:
                pass
            self.connected = False
            try:
                self.root.after(100, lambda: self.send_button.config(state=tk.DISABLED))
            except Exception:
                pass
    
    def _send_patient_name(self):
        """Send patient name to Pico"""
        patient_name = self.patient_entry.get().strip()
        
        if not patient_name:
            messagebox.showwarning("Empty Input", "Please enter a patient name")
            return
        
        if not self.connected:
            messagebox.showerror("Not Connected", "Not connected to Pico.\nPlease check WiFi connection.")
            return
        
        try:
            # Publish patient name
            message = f"PATIENT:{patient_name}"
            pub_exe = _resolve_mosquitto_cli("mosquitto_pub") or "mosquitto_pub"
            pub_cmd = [
                pub_exe,
                "-h", str(self.MQTT_BROKER),
                "-p", str(self.MQTT_PORT),
                "-t", str(self.MQTT_TOPIC_PATIENT_NAME),
                "-m", str(message),
            ]
            self._log_message("[MQTT DEBUG] pub cmd: " + " ".join(map(str, pub_cmd)))
            result = subprocess.run(
                pub_cmd,
                capture_output=True,
                text=True,
            )
            self._log_message(f"[MQTT DEBUG] mosquitto_pub rc={result.returncode}")
            out = (result.stdout or "").strip()
            err = (result.stderr or "").strip()
            if out:
                self._log_message("[MQTT DEBUG] pub stdout: " + out[:3000])
            if err:
                self._log_message("[MQTT DEBUG] pub stderr: " + err[:3000])
            if result.returncode != 0:
                combo = ((result.stdout or "") + (result.stderr or "")).strip()
                raise RuntimeError(combo or f"mosquitto_pub failed with exit code {result.returncode}")
            
            self._log_message(f"✓ Sent patient name: {patient_name}")
            messagebox.showinfo("Success", f"Patient name '{patient_name}' sent to Pico!")
            
        except Exception as e:
            self._log_message(f"Error sending patient name: {e}", "error")
            messagebox.showerror("Error", f"Failed to send data: {e}")
    
    def _update_status(self):
        """Update connection status display"""
        if self.connected:
            self.conn_status_label.config(text="✓ Connected", foreground="green")
            self.conn_details_label.config(
                text=f"Broker: {self.MQTT_BROKER}:{self.MQTT_PORT}"
            )
        else:
            self.conn_status_label.config(text="✗ Disconnected", foreground="red")
            self.conn_details_label.config(text="Attempting to reconnect...")
        
        # Schedule next update
        self.root.after(2000, self._update_status)
    
    def _log_message(self, message, level="info"):
        """Add message to activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)  # Auto-scroll to bottom
        self.log_text.config(state=tk.DISABLED)
    
    def on_closing(self):
        """Handle application closing"""
        self._stop_event.set()
        try:
            if self._sub_process and self._sub_process.poll() is None:
                self._sub_process.terminate()
        except Exception:
            pass
        
        self.root.destroy()


class QuickStartWindow:
    """Quick start/setup window before main app"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Pico Companion - Setup")
        self.root.geometry("500x400")
        self.root.configure(bg="#f0f0f0")
        
        self._create_ui()
    
    def _create_ui(self):
        """Create setup UI"""
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(frame, text="Pico Heart Rate Monitor", 
                 font=("Arial", 16, "bold")).pack(pady=20)
        
        # Instructions
        instructions = """
Quick Start Guide:

1. Power on your Pico device
2. Ensure Pico connects to WiFi network:
   SSID: KMD652_Group4
   
3. Wait for display to show "Waiting for Patient Name"

4. Click below to launch the Companion Application
        """
        
        ttk.Label(frame, text=instructions, font=("Arial", 10),
                 justify=tk.LEFT).pack(pady=20)
        
        # Prerequisites check
        prereq_frame = ttk.LabelFrame(frame, text="Prerequisites")
        prereq_frame.pack(fill=tk.X, pady=10)
        
        checks = [
            ("Pico powered on", True),
            ("Pico connected to WiFi", False),
            ("MQTT broker running", False),
            ("Network: 192.168.4.153:1883", False)
        ]
        
        for check_name, status in checks:
            status_text = "✓" if status else "○"
            ttk.Label(prereq_frame, text=f"{status_text} {check_name}").pack(anchor=tk.W, padx=10, pady=3)
        
        # Launch button
        launch_button = ttk.Button(frame, text="Launch Companion App",
                                  command=self._launch_app)
        launch_button.pack(pady=30, fill=tk.X)
        
        # Footer
        ttk.Label(frame, text="Make sure all prerequisites are met before launching",
                 font=("Arial", 8), foreground="gray").pack(pady=10)
    
    def _launch_app(self):
        """Launch main application"""
        self.root.destroy()
        
        # Create main window
        main_root = tk.Tk()
        app = PicoCompanionApp(main_root)
        main_root.protocol("WM_DELETE_WINDOW", app.on_closing)
        main_root.mainloop()


def main():
    """Entry point for companion application"""
    root = tk.Tk()
    
    # Launch companion app directly (skip quick-start gate).
    try:
        app = PicoCompanionApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()
    except Exception as e:
        print(f"Error: {e}")
        messagebox.showerror("Error", f"Failed to start application:\n{e}")


if __name__ == "__main__":
    main()
