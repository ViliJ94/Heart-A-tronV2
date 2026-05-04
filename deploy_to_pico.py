"""
Deployment Script - Automatically copy files to Pico W
This script uses mpremote to deploy all program files
"""

import os
import subprocess
import sys
from pathlib import Path


class PicoDeployer:
    """Helper class for deploying files to Pico"""
    
    REQUIRED_TOOLS = ["mpremote"]
    
    DIRECTORIES_TO_CREATE = [
        ":/classes",
        ":/Data",
        ":/umqtt"
    ]
    
    FILES_TO_COPY = {
        "Code/umqtt/simple.py": ":/umqtt/simple.py",
        "Code/Main.py": ":/main.py",
        "Code/ssd1306.py": ":/ssd1306.py",
        "Code/classes/display_manager.py": ":/classes/display_manager.py",
        "Code/classes/sensor_manager.py": ":/classes/sensor_manager.py",
        "Code/classes/wifi_manager.py": ":/classes/wifi_manager.py",
        "Code/classes/state_machine.py": ":/classes/state_machine.py",
        "Code/classes/measurement_engine.py": ":/classes/measurement_engine.py",
        "Code/classes/data_storage.py": ":/classes/data_storage.py",
        "Code/classes/graphics.py": ":/classes/graphics.py",
        "Code/classes/__init__.py": ":/classes/__init__.py",
    }
    
    CONFIG_FILES = {
        "Code/config.py": ":/config.py",
    }
    
    def __init__(self, port=None):
        """Initialize deployer"""
        self.project_root = Path(__file__).parent
        self.port = port or os.environ.get("PICO_PORT", "").strip() or None
        self.success_count = 0
        self.error_count = 0
        self.errors = []
    
    def _mpremote_cmd(self, *args):
        """Build mpremote command with optional explicit COM port."""
        cmd = ["mpremote"]
        if self.port:
            cmd.extend(["connect", self.port])
        cmd.extend(args)
        return cmd
    
    def _run_mpremote(self, *args, timeout=10, retries=2):
        """Run mpremote command with small retry window for flaky USB serial."""
        last_result = None
        for attempt in range(1, retries + 1):
            result = subprocess.run(
                self._mpremote_cmd(*args),
                capture_output=True,
                timeout=timeout,
                cwd=self.project_root,
            )
            last_result = result
            if result.returncode == 0:
                return result
            if attempt < retries:
                time_to_wait = 0.4 * attempt
                print(f"  retrying ({attempt}/{retries - 1}) after {time_to_wait:.1f}s...")
                import time
                time.sleep(time_to_wait)
        return last_result
    
    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("\n" + "="*70)
        print("CHECKING PREREQUISITES")
        print("="*70 + "\n")
        
        missing_tools = []
        
        for tool in self.REQUIRED_TOOLS:
            try:
                result = subprocess.run([tool, "--version"], 
                                      capture_output=True, 
                                      timeout=5)
                if result.returncode == 0:
                    print(f"[OK] {tool} is installed")
                else:
                    missing_tools.append(tool)
            except Exception as e:
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"\n[ERR] Missing tools: {', '.join(missing_tools)}")
            print("\nInstall with: pip install mpremote")
            return False
        
        # Check Pico connection
        print("\nChecking Pico W connection...")
        try:
            result = self._run_mpremote("ls", timeout=6, retries=3)
            if result.returncode == 0:
                if self.port:
                    print(f"[OK] Pico W is connected on {self.port}")
                else:
                    print("[OK] Pico W is connected")
                return True
            else:
                print("[ERR] Pico W not detected")
                print("  - Connect Pico W to USB")
                print("  - Restart it if needed")
                if self.port:
                    print(f"  - Confirm port exists: {self.port}")
                return False
        except Exception as e:
            print(f"[ERR] Error checking connection: {e}")
            return False
    
    def create_directories(self):
        """Create necessary directories on Pico"""
        print("\n" + "="*70)
        print("CREATING DIRECTORIES")
        print("="*70 + "\n")
        
        for directory in self.DIRECTORIES_TO_CREATE:
            try:
                print(f"Creating {directory}...", end=" ")
                result = self._run_mpremote("mkdir", directory, timeout=6, retries=2)
                if result.returncode == 0:
                    print("[OK]")
                    self.success_count += 1
                else:
                    error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                    print(f"[ERR] ({error_msg})")
                    self.error_count += 1
                    self.errors.append(f"Failed to create {directory}: {error_msg}")
            except Exception as e:
                print(f"[ERR] ({e})")
                self.error_count += 1
                self.errors.append(f"Failed to create {directory}: {e}")
    
    def copy_files(self):
        """Copy program files to Pico"""
        print("\n" + "="*70)
        print("COPYING PROGRAM FILES")
        print("="*70 + "\n")
        
        for source, destination in self.FILES_TO_COPY.items():
            source_path = self.project_root / source
            
            if not source_path.exists():
                print(f"[ERR] {source} - FILE NOT FOUND")
                self.error_count += 1
                self.errors.append(f"Source file not found: {source}")
                continue
            
            try:
                print(f"Copying {source}...", end=" ")
                result = self._run_mpremote("cp", str(source_path.resolve()), destination, timeout=12, retries=3)
                
                if result.returncode == 0:
                    print("[OK]")
                    self.success_count += 1
                else:
                    error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                    print(f"[ERR] ({error_msg})")
                    self.error_count += 1
                    self.errors.append(f"Failed to copy {source}: {error_msg}")
                    
            except subprocess.TimeoutExpired:
                print("[ERR] (Timeout)")
                self.error_count += 1
                self.errors.append(f"Timeout copying {source}")
            except Exception as e:
                print(f"[ERR] ({e})")
                self.error_count += 1
                self.errors.append(f"Failed to copy {source}: {e}")
    
    def install_mip_packages(self):
        """Install required MicroPython packages via mip"""
        print("\n" + "="*70)
        print("INSTALLING MICROPYTHON PACKAGES (mip)")
        print("="*70 + "\n")
        
        packages = ["umqtt.simple"]
        
        for package in packages:
            try:
                print(f"Installing {package}...", end=" ")
                result = self._run_mpremote("exec", f"import mip; mip.install('{package}')", timeout=30, retries=1)
                
                if result.returncode == 0:
                    print("[OK]")
                    self.success_count += 1
                else:
                    stderr = result.stderr.decode() if result.stderr else "Unknown error"
                    print(f"[WARN] ({stderr})")
                    if "mip" in stderr.lower() or "no module" in stderr.lower():
                        print(f"  Note: mip may not be available in this MicroPython build")
                        print(f"  Install {package} manually via: mpremote mip install {package}")
                    
            except subprocess.TimeoutExpired:
                print("[WARN] (Timeout - mip may be unavailable)")
            except Exception as e:
                print(f"[WARN] ({e})")

    def copy_config_files(self):
        """Copy configuration files to Pico"""
        print("\n" + "="*70)
        print("COPYING CONFIGURATION FILES")
        print("="*70 + "\n")
        
        for source, destination in self.CONFIG_FILES.items():
            source_path = self.project_root / source
            
            if not source_path.exists():
                print(f"[SKIP] {source} - Skipping (optional)")
                return
            
            try:
                print(f"Copying {source}...", end=" ")
                result = self._run_mpremote("cp", str(source_path.resolve()), destination, timeout=12, retries=2)
                
                if result.returncode == 0:
                    print("[OK]")
                    self.success_count += 1
                else:
                    print("[SKIP] (Skipped)")
                    
            except Exception as e:
                print(f"[SKIP] (Skipped - {e})")
    
    def verify_deployment(self):
        """Verify files were copied successfully"""
        print("\n" + "="*70)
        print("VERIFYING DEPLOYMENT")
        print("="*70 + "\n")
        
        try:
            print("Listing files on Pico...\n")
            result = self._run_mpremote("ls", "-r", timeout=8, retries=2)
            
            output = result.stdout.decode()
            
            # Check for key files
            key_files = ["main.py", "ssd1306.py", "classes/display_manager.py"]
            found_files = []
            
            for key_file in key_files:
                if key_file in output:
                    found_files.append(key_file)
                    print(f"[OK] Found {key_file}")
            
            if len(found_files) == len(key_files):
                print("\n[OK] All files verified successfully!")
                return True
            else:
                missing = set(key_files) - set(found_files)
                print(f"\n[ERR] Missing files: {missing}")
                return False
                
        except Exception as e:
            print(f"[ERR] Verification failed: {e}")
            return False
    
    def print_summary(self):
        """Print deployment summary"""
        print("\n" + "="*70)
        print("DEPLOYMENT SUMMARY")
        print("="*70 + "\n")
        
        print(f"[OK] Successful operations: {self.success_count}")
        print(f"[ERR] Failed operations: {self.error_count}")
        
        if self.errors:
            print("\nErrors encountered:")
            for error in self.errors:
                print(f"  - {error}")
        
        total = self.success_count + self.error_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        
        print(f"\nSuccess rate: {success_rate:.1f}%")
        
        if self.error_count == 0:
            print("\n" + "* " * 10)
            print("DEPLOYMENT SUCCESSFUL!")
            print("* " * 10)
            print("\nNext steps:")
            print("1. Connect Pico W to power")
            print("2. Run PC Companion App: python PC_Companion_App.py")
            print("3. Watch Pico display for startup sequence")
            return True
        else:
            print("\n[WARN] DEPLOYMENT COMPLETED WITH ERRORS")
            print("\nIMPORTANT: If you see 'umqtt.simple not available' on Pico:")
            print("  Try installing umqtt manually:")
            print("    mpremote mip install umqtt.simple")
            print("\nTroubleshooting:")
            print("1. Ensure Pico W is connected via USB")
            print("2. Try restarting Pico (disconnect/reconnect USB)")
            print("3. Run: mpremote reset")
            print("4. Install mpremote: pip install --upgrade mpremote")
            return False
    
    def deploy(self):
        """Run full deployment process"""
        print("\n")
        print("=" * 70)
        print(" " * 15 + "PICO HEART RATE MONITOR DEPLOYER")
        print("=" * 70)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n[ERR] Prerequisites not met. Aborting deployment.")
            return False
        
        # Create directories
        self.create_directories()
        
        # Copy files
        self.copy_files()
        
        # Copy config
        self.copy_config_files()
        
        # Install MicroPython packages
        self.install_mip_packages()
        
        # Verify
        verified = self.verify_deployment()
        
        # Summary
        self.print_summary()
        
        return verified and self.error_count == 0


def main():
    """Main entry point"""
    cli_port = sys.argv[1] if len(sys.argv) > 1 else None
    deployer = PicoDeployer(port=cli_port)
    success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERR] Fatal error: {e}")
        sys.exit(1)
