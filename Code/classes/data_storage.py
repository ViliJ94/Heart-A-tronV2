"""
Data Storage - Manages persistent data storage and history on Pico
"""

import json
import os
import time


class DataStorage:
    """Manages data persistence on Pico filesystem"""
    
    # Storage paths
    DATA_FOLDER = "/Data"
    HISTORY_FILE = "/Data/history.json"
    SESSION_FILE = "/Data/current_session.json"
    BACKUP_FOLDER = "/Data/backups"
    
    # Storage limits
    MAX_HISTORY_ENTRIES = 100
    MAX_SESSION_DATA = 10
    
    def __init__(self):
        """Initialize data storage"""
        self._ensure_folders()
        print("[STORAGE] Data storage initialized")
    
    def _ensure_folders(self):
        """Create necessary folders if they don't exist"""
        try:
            folders = [self.DATA_FOLDER, self.BACKUP_FOLDER]
            for folder in folders:
                try:
                    os.mkdir(folder)
                    print(f"[STORAGE] Created folder: {folder}")
                except OSError:
                    # Folder already exists
                    pass
        except Exception as e:
            print(f"[STORAGE] Error creating folders: {e}")
    
    def save_measurement(self, hrv_data, patient_name):
        """
        Save HRV measurement to history
        Appends to history.json with proper rotation
        """
        try:
            entry = {
                "patient": patient_name,
                "timestamp": self._get_timestamp(),
                "mean_hr": int(hrv_data.get("mean_hr", 0)),
                "mean_ppi": int(hrv_data.get("mean_ppi", 0)),
                "rmssd": int(hrv_data.get("rmssd", 0)),
                "sdnn": int(hrv_data.get("sdnn", 0)),
                "sample_count": int(hrv_data.get("sample_count", 0)),
                "type": "HRV"
            }
            
            # Load existing history
            history = self.load_history()
            history.append(entry)
            
            # Keep only recent entries
            if len(history) > self.MAX_HISTORY_ENTRIES:
                history = history[-self.MAX_HISTORY_ENTRIES:]
            
            # Save updated history
            self._write_json(self.HISTORY_FILE, history)
            print(f"[STORAGE] Saved measurement for {patient_name}")
            return True
            
        except Exception as e:
            print(f"[STORAGE] Error saving measurement: {e}")
            return False
    
    def save_kubios_result(self, kubios_data, patient_name):
        """
        Save Kubios analysis result to history
        """
        try:
            entry = {
                "patient": patient_name,
                "timestamp": kubios_data.get("timestamp", self._get_timestamp()),
                "heart_rate": int(kubios_data.get("heart_rate", 0)),
                "stress_level": str(kubios_data.get("stress_level", "N/A")),
                "lf": int(kubios_data.get("lf", 0)),
                "hf": int(kubios_data.get("hf", 0)),
                "lf_hf_ratio": float(kubios_data.get("lf_hf_ratio", 0.0)),
                "type": "KUBIOS"
            }
            
            # Load existing history
            history = self.load_history()
            history.append(entry)
            
            # Keep only recent entries
            if len(history) > self.MAX_HISTORY_ENTRIES:
                history = history[-self.MAX_HISTORY_ENTRIES:]
            
            # Save updated history
            self._write_json(self.HISTORY_FILE, history)
            print(f"[STORAGE] Saved Kubios result for {patient_name}")
            return True
            
        except Exception as e:
            print(f"[STORAGE] Error saving Kubios result: {e}")
            return False
    
    def load_history(self):
        """
        Load measurement history from storage
        Returns: list of history entries (most recent first)
        """
        try:
            data = self._read_json(self.HISTORY_FILE)
            if data is None:
                return []
            return data
            
        except Exception as e:
            print(f"[STORAGE] Error loading history: {e}")
            return []
    
    def save_session_data(self, session_data):
        """
        Save current session data for recovery
        """
        try:
            self._write_json(self.SESSION_FILE, session_data)
            print("[STORAGE] Session data saved")
            return True
            
        except Exception as e:
            print(f"[STORAGE] Error saving session: {e}")
            return False
    
    def load_session_data(self):
        """
        Load previous session data if available
        """
        try:
            data = self._read_json(self.SESSION_FILE)
            if data:
                print("[STORAGE] Session data loaded")
            return data
            
        except Exception as e:
            print(f"[STORAGE] Error loading session: {e}")
            return None
    
    def create_backup(self):
        """
        Create backup of current data
        """
        try:
            timestamp = self._get_timestamp().replace(":", "-").replace("T", "_")
            backup_file = f"{self.BACKUP_FOLDER}/history_backup_{timestamp}.json"
            
            history = self.load_history()
            self._write_json(backup_file, history)
            
            print(f"[STORAGE] Backup created: {backup_file}")
            return True
            
        except Exception as e:
            print(f"[STORAGE] Error creating backup: {e}")
            return False
    
    def get_storage_info(self):
        """
        Get storage usage information
        Returns: dict with usage statistics
        """
        try:
            stat_info = os.statvfs(self.DATA_FOLDER)
            
            total_space = stat_info[0] * stat_info[2]  # Block size * Total blocks
            free_space = stat_info[0] * stat_info[3]   # Block size * Free blocks
            used_space = total_space - free_space
            
            history = self.load_history()
            
            info = {
                "total_space_kb": total_space // 1024,
                "used_space_kb": used_space // 1024,
                "free_space_kb": free_space // 1024,
                "history_entries": len(history),
                "storage_path": self.DATA_FOLDER
            }
            
            return info
            
        except Exception as e:
            print(f"[STORAGE] Error getting storage info: {e}")
            return None
    
    def clear_old_data(self, days=30):
        """
        Remove data older than specified days
        """
        try:
            history = self.load_history()
            current_time = time.time()
            seconds_old = days * 24 * 60 * 60
            
            filtered = []
            for entry in history:
                try:
                    entry_time = self._parse_timestamp(entry.get("timestamp", ""))
                    if current_time - entry_time < seconds_old:
                        filtered.append(entry)
                except:
                    filtered.append(entry)  # Keep if can't parse
            
            self._write_json(self.HISTORY_FILE, filtered)
            removed = len(history) - len(filtered)
            print(f"[STORAGE] Removed {removed} old entries")
            return True
            
        except Exception as e:
            print(f"[STORAGE] Error clearing old data: {e}")
            return False
    
    def _read_json(self, filepath):
        """Read JSON file from storage"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
        except Exception as e:
            print(f"[STORAGE] Error reading {filepath}: {e}")
            return None
    
    def _write_json(self, filepath, data):
        """Write JSON file to storage"""
        try:
            # Write to temporary file first for safety
            temp_file = filepath + ".tmp"
            
            with open(temp_file, 'w') as f:
                json.dump(data, f)
            
            # Rename temp to actual file
            try:
                os.remove(filepath)
            except:
                pass
            
            os.rename(temp_file, filepath)
            
        except Exception as e:
            print(f"[STORAGE] Error writing {filepath}: {e}")
            # Clean up temp file if it exists
            try:
                os.remove(temp_file)
            except:
                pass
    
    def _get_timestamp(self):
        """Get current timestamp in ISO 8601 format"""
        try:
            from machine import RTC
            rtc = RTC()
            dt = rtc.datetime()
            # dt format: (year, month, day, weekday, hour, minute, second, subseconds)
            return "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}".format(
                dt[0], dt[1], dt[2], dt[4], dt[5], dt[6]
            )
        except:
            return "2025-01-01T00:00:00"
    
    def _parse_timestamp(self, timestamp_str):
        """Parse ISO 8601 timestamp to epoch seconds"""
        try:
            # Simple parser for ISO 8601 format
            parts = timestamp_str.replace("T", "-").split("-")
            if len(parts) >= 6:
                year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                hour = int(parts[3])
                minute = int(parts[4])
                second = int(parts[5])
                
                # Simplified epoch calculation
                return time.mktime((year, month, day, hour, minute, second, 0, 0))
        except:
            pass
        
        return 0
