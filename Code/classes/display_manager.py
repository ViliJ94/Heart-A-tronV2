"""OLED display helper with simple, predictable screens."""

import machine
import time

try:
    from ssd1306 import SSD1306_I2C
except ImportError:
    SSD1306_I2C = None

try:
    import config as cfg
except ImportError:
    cfg = None


class DisplayManager:
    """Render all UI screens without blocking delays."""

    def __init__(self):
        sda = getattr(cfg, "I2C_SDA_PIN", 14)
        scl = getattr(cfg, "I2C_SCL_PIN", 15)
        freq = getattr(cfg, "I2C_FREQUENCY", 400000)
        width = getattr(cfg, "OLED_WIDTH", 128)
        height = getattr(cfg, "OLED_HEIGHT", 64)
        i2c_no = getattr(cfg, "I2C_NUMBER", 1)
        addr = getattr(cfg, "OLED_ADDRESS", 0x3C)
        self.display = None
        self.width = width
        self.height = height
        try:
            if SSD1306_I2C:
                print("[DISPLAY] init i2c_no=%s scl=%s sda=%s freq=%s addr=0x%02X" % (i2c_no, scl, sda, freq, int(addr)))
                i2c = machine.I2C(i2c_no, scl=machine.Pin(scl), sda=machine.Pin(sda), freq=freq)
                try:
                    addrs = i2c.scan()
                    print("[DISPLAY] i2c scan:", addrs)
                except Exception as exc:
                    print("[DISPLAY] i2c scan failed:", exc)
                    addrs = []
                self.display = SSD1306_I2C(width, height, i2c, addr=int(addr))
                print("[DISPLAY] init ok")
        except Exception as exc:
            print("[DISPLAY] init failed:", exc)

        # State for history UI
        self._history_entries = []
        self._history_selected = 0

    def _clear(self):
        if self.display:
            self.display.fill(0)

    def _show(self):
        if self.display:
            self.display.show()

    def _line(self, text, x, y):
        if self.display:
            self.display.text(str(text)[:21], x, y)

    def _wrap_text(self, text, width=21, lines=3):
        words = str(text).split()
        wrapped = []
        current = ""
        for word in words:
            if len(current) + len(word) + (1 if current else 0) <= width:
                current = f"{current} {word}".strip()
            else:
                wrapped.append(current)
                current = word
                if len(wrapped) >= lines:
                    break
        if current and len(wrapped) < lines:
            wrapped.append(current)
        while len(wrapped) < lines:
            wrapped.append("")
        return wrapped[:lines]

    def show_message(self, title, line2="", line3=""):
        self._clear()
        self._line(title, 0, 0)
        self._line(line2, 0, 20)
        self._line(line3, 0, 40)
        self._show()

    # -------------------------------------------------------------------------
    # Compatibility wrappers (Main.py expects these names)
    # -------------------------------------------------------------------------

    def show_init_message(self, line1="Initializing...", line2="Please wait"):
        self.show_message(line1, line2)

    def show_waiting_screen(self, text):
        parts = self._wrap_text(text, width=21, lines=3)
        self.show_message(parts[0], parts[1], parts[2])

    def show_success_message(self, text, duration=1):
        self.show_waiting_screen(text)
        try:
            time.sleep(max(0, float(duration)))
        except Exception:
            pass

    def show_warning_message(self, text, duration=1):
        self.show_waiting_screen(text)
        try:
            time.sleep(max(0, float(duration)))
        except Exception:
            pass

    def show_error_screen(self, text, duration=2):
        parts = self._wrap_text(text, width=21, lines=3)
        self.show_message(parts[0], parts[1], parts[2])
        try:
            time.sleep(max(0, float(duration)))
        except Exception:
            pass

    def show_error_message(self, text, duration=2):
        self.show_error_screen(text, duration=duration)

    def show_main_menu(self, selected):
        options = ["Measure HR", "HRV Analysis", "Kubios", "History"]
        try:
            idx = int(selected) % len(options)
        except Exception:
            idx = 0
        # reuse existing renderer
        self.show_main_menu_options(options, idx)

    def show_measurement_mode(self):
        self.show_message("MEASURE HR", "Collecting...", "SW=Stop/Back")

    def update_heart_rate_display(self, bpm):
        self.show_message("MEASURE HR", "BPM: %s" % bpm, "SW=Stop/Back")

    def show_hrv_collection_screen(self):
        self.show_message("HRV", "Collecting 30s", "Please wait")

    def update_collection_progress(self, bpm, progress):
        try:
            pct = int(progress)
        except Exception:
            pct = 0
        self.show_collection("HRV", bpm, pct, "Collecting")

    def show_kubios_screen(self):
        self.show_message("KUBIOS", "Collecting 30s", "Please wait")

    def show_history_menu(self, history_entries):
        self._history_entries = history_entries or []
        self._history_selected = 0
        self.show_history(self._history_entries, self._history_selected)

    def get_selected_history_entry(self):
        if not self._history_entries:
            return None
        try:
            return self._history_entries[self._history_selected]
        except Exception:
            return self._history_entries[0]

    # Backwards compatible renderer used by the wrapper above
    def show_main_menu_options(self, options, selected):
        self._clear()
        self._line("MAIN MENU", 0, 0)
        i = 0
        while i < len(options) and i < 4:
            marker = ">" if i == selected else " "
            self._line("%s%s" % (marker, options[i][:19]), 0, 14 + i * 12)
            i += 1
        self._show()

    def show_measurement(self, title, bpm, status, waveform=None):
        self._clear()
        self._line(title, 0, 0)
        self._line("BPM: %s" % ("--" if bpm <= 0 else bpm), 0, 12)
        self._line("STATE: %s" % status, 0, 22)
        if waveform:
            self._draw_waveform(waveform, 0, 30, self.width, 18)
        self._line("SW1: Back", 0, 52)
        self._show()

    def show_collection(self, title, bpm, progress, status):
        self._clear()
        self._line(title, 0, 0)
        self._line("BPM: %s" % ("--" if bpm <= 0 else bpm), 0, 16)
        self._line("Progress: %d%%" % progress, 0, 28)
        self._line("STATE: %s" % status, 0, 40)
        self._line("SW1: Back", 0, 52)
        self._show()

    def show_hrv_results(self, payload):
        self._clear()
        self._line("LOCAL HRV", 0, 0)
        self._line("HR %s RMSSD %s" % (payload.get("mean_hr", 0), payload.get("rmssd", 0)), 0, 16)
        self._line("SDNN %s PPI %s" % (payload.get("sdnn", 0), payload.get("mean_ppi", 0)), 0, 28)
        self._line("Saved + MQTT", 0, 52)
        self._show()

    def show_kubios_results(self, payload):
        self._clear()
        self._line("KUBIOS", 0, 0)
        self._line("HR: %s" % payload.get("heart_rate", 0), 0, 16)
        self._line("Stress: %s" % payload.get("stress_level", "N/A"), 0, 28)
        self._line("Saved", 0, 52)
        self._show()

    def show_history(self, entries, selected):
        self._clear()
        self._line("HISTORY", 0, 0)
        if not entries:
            self._line("No entries", 0, 20)
        else:
            i = 0
            max_rows = 3
            start = 0
            if selected >= max_rows:
                start = selected - max_rows + 1
            while i < max_rows and (start + i) < len(entries):
                idx = start + i
                item = entries[idx]
                kind = item.get("type", "HRV")
                marker = ">" if idx == selected else " "
                label = "%s%s %s" % (marker, kind, str(item.get("timestamp", ""))[-8:])
                self._line(label[:21], 0, 14 + i * 14)
                i += 1
        self._show()

    def show_history_details(self, entry):
        self._clear()
        self._line("DETAIL", 0, 0)
        self._line("Type: %s" % entry.get("type", "N/A"), 0, 14)
        self._line("HR: %s" % entry.get("mean_hr", entry.get("heart_rate", 0)), 0, 26)
        self._line("RMSSD: %s" % entry.get("rmssd", "N/A"), 0, 38)
        self._line("SW1: Back", 0, 52)
        self._show()

    def _draw_waveform(self, values, x, y, width, height):
        if not self.display or not values or len(values) < 2:
            return
        vmin = min(values)
        vmax = max(values)
        vrange = vmax - vmin
        if vrange <= 0:
            vrange = 1
        last_x = x
        last_y = y + height // 2
        count = len(values)
        i = 0
        while i < count:
            px = x + int((i * (width - 1)) / max(1, count - 1))
            py = y + height - 1 - int(((values[i] - vmin) * (height - 1)) / vrange)
            if i > 0:
                self.display.line(last_x, last_y, px, py, 1)
            last_x = px
            last_y = py
            i += 1
