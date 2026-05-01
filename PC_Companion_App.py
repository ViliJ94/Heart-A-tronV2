"""
PC Companion Application - Patient Name Input Interface
Tkinter-based GUI for sending patient information to Pico via MQTT

Requirements: pip install paho-mqtt
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import paho.mqtt.client as mqtt
import threading
import time
from datetime import datetime


class PicoCompanionApp:
    """Main application window for Pico companion app"""
    
    # MQTT Configuration (must match Pico settings)
    MQTT_BROKER = "192.168.4.153"
    MQTT_PORT = 1883
    MQTT_TOPIC_PATIENT_NAME = "patient/name"
    MQTT_TOPIC_DEVICE_STATUS = "device/status"
    
    def __init__(self, root):
        """Initialize the companion application"""
        self.root = root
        self.root.title("Pico Heart Rate Monitor - Companion App")
        self.root.geometry("600x500")
        self.root.configure(bg="#f0f0f0")
        
        # MQTT client
        self.mqtt_client = None
        self.connected = False
        
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
        """Connect to MQTT broker in background thread"""
        thread = threading.Thread(target=self._mqtt_connect_thread, daemon=True)
        thread.start()
    
    def _mqtt_connect_thread(self):
        """Background thread for MQTT connection"""
        try:
            self.mqtt_client = mqtt.Client("pico_companion_app")
            self.mqtt_client.on_connect = self._on_mqtt_connect
            self.mqtt_client.on_disconnect = self._on_mqtt_disconnect
            self.mqtt_client.on_message = self._on_mqtt_message
            
            self._log_message("Connecting to MQTT broker...")
            self.mqtt_client.connect(self.MQTT_BROKER, self.MQTT_PORT, keepalive=60)
            self.mqtt_client.loop_start()
            
        except Exception as e:
            self._log_message(f"MQTT Connection Error: {e}", "error")
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.connected = True
            self._log_message("✓ Connected to MQTT broker")
            
            # Subscribe to device status
            self.mqtt_client.subscribe(self.MQTT_TOPIC_DEVICE_STATUS)
            
            # Enable send button
            self.root.after(100, lambda: self.send_button.config(state=tk.NORMAL))
        else:
            self._log_message(f"Connection failed with code {rc}", "error")
    
    def _on_mqtt_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.connected = False
        self._log_message(f"Disconnected from MQTT (code {rc})")
        self.send_button.config(state=tk.DISABLED)
    
    def _on_mqtt_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            message = msg.payload.decode()
            self._log_message(f"Device: {message}")
        except Exception as e:
            self._log_message(f"Error decoding message: {e}", "error")
    
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
            self.mqtt_client.publish(self.MQTT_TOPIC_PATIENT_NAME, message)
            
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
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
        
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
