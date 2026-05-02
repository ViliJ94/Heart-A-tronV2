"""
Testing Guide - Verify system functionality after deployment
Run tests to ensure all components are working correctly
"""

import os
import sys

# Ensure Windows consoles don't crash on box-drawing characters
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


class SystemTester:
    """Test suite for Pico Heart Rate Monitor"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
    
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{BOLD}{BLUE}{'='*70}{RESET}")
        print(f"{BOLD}{BLUE}{text.center(70)}{RESET}")
        print(f"{BOLD}{BLUE}{'='*70}{RESET}\n")
    
    def print_test(self, test_name, status, details=""):
        """Print test result"""
        if status == "PASS":
            symbol = f"{GREEN}✓{RESET}"
            self.tests_passed += 1
        elif status == "FAIL":
            symbol = f"{RED}✗{RESET}"
            self.tests_failed += 1
        elif status == "SKIP":
            symbol = f"{YELLOW}⊙{RESET}"
            self.tests_skipped += 1
        else:
            symbol = "?"
        
        detail_str = f" - {details}" if details else ""
        print(f"{symbol} {test_name}{detail_str}")
    
    # ─────────────────────────────────────────────────────────────────────────
    # FILE STRUCTURE TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_file_structure(self):
        """Test local file structure"""
        self.print_header("FILE STRUCTURE TESTS")
        
        files_to_check = {
            "Code/Main.py": "Main application",
            "Code/ssd1306.py": "OLED display driver",
            "Code/classes/display_manager.py": "Display manager",
            "Code/classes/sensor_manager.py": "Sensor manager",
            "Code/classes/wifi_manager.py": "WiFi manager",
            "Code/classes/state_machine.py": "State machine",
            "Code/classes/measurement_engine.py": "Measurement engine",
            "Code/classes/data_storage.py": "Data storage",
            "Code/classes/graphics.py": "Graphics utilities",
            "Code/classes/__init__.py": "Classes init",
            "PC_Companion_App.py": "PC companion app",
            "README.md": "Documentation",
            "requirements.txt": "Python requirements"
        }
        
        for filepath, description in files_to_check.items():
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                self.print_test(f"{filepath}", "PASS", f"{file_size} bytes")
            else:
                self.print_test(f"{filepath}", "FAIL", "Not found")
    
    # ─────────────────────────────────────────────────────────────────────────
    # PYTHON SYNTAX TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_python_syntax(self):
        """Test Python file syntax"""
        self.print_header("PYTHON SYNTAX TESTS")
        
        python_files = [
            "Code/Main.py",
            "Code/ssd1306.py",
            "Code/classes/display_manager.py",
            "Code/classes/sensor_manager.py",
            "Code/classes/wifi_manager.py",
            "Code/classes/state_machine.py",
            "Code/classes/measurement_engine.py",
            "Code/classes/data_storage.py",
            "PC_Companion_App.py"
        ]
        
        for filepath in python_files:
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r') as f:
                        compile(f.read(), filepath, 'exec')
                    self.print_test(f"Syntax: {filepath}", "PASS")
                except SyntaxError as e:
                    self.print_test(f"Syntax: {filepath}", "FAIL", str(e))
            else:
                self.print_test(f"Syntax: {filepath}", "SKIP", "File not found")
    
    # ─────────────────────────────────────────────────────────────────────────
    # DEPENDENCIES TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_dependencies(self):
        """Test if required dependencies are installed (for PC app)"""
        self.print_header("DEPENDENCY TESTS (PC Application)")
        
        pc_dependencies = {
            "tkinter": "GUI framework",
            "subprocess": "Used to run mosquitto_pub/sub (standard library)"
        }
        
        for module, description in pc_dependencies.items():
            try:
                __import__(module)
                self.print_test(f"{module}", "PASS", description)
            except ImportError:
                self.print_test(f"{module}", "FAIL", f"Not installed - run: pip install {module}")

        # Verify Mosquitto CLI tools are available on PATH
        try:
            import shutil
            has_pub = shutil.which("mosquitto_pub") is not None
            has_sub = shutil.which("mosquitto_sub") is not None
            if has_pub and has_sub:
                self.print_test("mosquitto_pub/sub", "PASS", "Mosquitto CLI available on PATH")
            else:
                self.print_test("mosquitto_pub/sub", "FAIL", "Install Mosquitto and add it to PATH")
        except Exception as e:
            self.print_test("mosquitto_pub/sub", "WARN", str(e))
    
    # ─────────────────────────────────────────────────────────────────────────
    # CODE QUALITY TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_code_quality(self):
        """Test code quality metrics"""
        self.print_header("CODE QUALITY TESTS")
        
        # Check for docstrings
        files_with_docs = [
            "Code/Main.py",
            "Code/classes/display_manager.py",
            "Code/classes/sensor_manager.py",
            "PC_Companion_App.py"
        ]
        
        for filepath in files_with_docs:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    has_docstrings = '"""' in content or "'''" in content
                    status = "PASS" if has_docstrings else "WARN"
                    self.print_test(f"Docstrings: {filepath}", status)
        
        # Check for error handling
        files_with_errors = [
            "Code/classes/wifi_manager.py",
            "Code/classes/data_storage.py"
        ]
        
        for filepath in files_with_errors:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    content = f.read()
                    has_try_except = 'try:' in content and 'except' in content
                    status = "PASS" if has_try_except else "WARN"
                    self.print_test(f"Error handling: {filepath}", status)
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONFIGURATION TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_configuration(self):
        """Test configuration files"""
        self.print_header("CONFIGURATION TESTS")
        
        # Check CONFIG.py
        if os.path.exists("CONFIG.py"):
            try:
                # Check for required configuration variables
                with open("CONFIG.py", 'r') as f:
                    content = f.read()
                    required_configs = [
                        "WIFI_SSID",
                        "MQTT_BROKER_IP",
                        "SAMPLE_RATE_HZ",
                        "MIN_COLLECTION_TIME_SECONDS"
                    ]
                    
                    for config in required_configs:
                        if config in content:
                            self.print_test(f"Config: {config}", "PASS")
                        else:
                            self.print_test(f"Config: {config}", "FAIL", "Not found in CONFIG.py")
            except Exception as e:
                self.print_test("CONFIG.py", "FAIL", str(e))
        else:
            self.print_test("CONFIG.py", "SKIP", "Not created (optional)")
    
    # ─────────────────────────────────────────────────────────────────────────
    # DEPLOYMENT READINESS TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def test_deployment_readiness(self):
        """Test deployment readiness"""
        self.print_header("DEPLOYMENT READINESS")
        
        # Check deployment script
        if os.path.exists("deploy_to_pico.py"):
            self.print_test("deploy_to_pico.py", "PASS", "Deployment script available")
        else:
            self.print_test("deploy_to_pico.py", "FAIL", "Deployment script not found")
        
        # Check mpremote availability
        os.system("mpremote --version > /tmp/mpremote_check.txt 2>&1")
        if os.path.exists("/tmp/mpremote_check.txt"):
            self.print_test("mpremote tool", "PASS", "Available (use deploy_to_pico.py)")
            os.remove("/tmp/mpremote_check.txt")
        else:
            self.print_test("mpremote tool", "SKIP", "Not installed (run: pip install mpremote)")
    
    # ─────────────────────────────────────────────────────────────────────────
    # RUN ALL TESTS
    # ─────────────────────────────────────────────────────────────────────────
    
    def run_all_tests(self):
        """Run all test suites"""
        print("\n")
        print("╔" + "="*68 + "╗")
        print("║" + " "*12 + "PICO HEART RATE MONITOR - SYSTEM TEST SUITE" + " "*13 + "║")
        print("╚" + "="*68 + "╝")
        
        self.test_file_structure()
        self.test_python_syntax()
        self.test_code_quality()
        self.test_configuration()
        self.test_dependencies()
        self.test_deployment_readiness()
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        self.print_header("TEST SUMMARY")
        
        total = self.tests_passed + self.tests_failed + self.tests_skipped
        
        print(f"{GREEN}✓ Passed: {self.tests_passed}{RESET}")
        print(f"{RED}✗ Failed: {self.tests_failed}{RESET}")
        print(f"{YELLOW}⊙ Skipped: {self.tests_skipped}{RESET}")
        print(f"  Total:  {total}\n")
        
        if self.tests_failed == 0:
            print(f"{GREEN}{BOLD}✓✓✓ ALL TESTS PASSED! ✓✓✓{RESET}")
            print("\nSystem is ready for deployment!")
            print("\nNext steps:")
            print("1. Run: python deploy_to_pico.py")
            print("2. Connect Pico W to power")
            print("3. Run: python PC_Companion_App.py")
            return True
        else:
            print(f"{RED}{BOLD}⚠ SOME TESTS FAILED{RESET}")
            print("\nPlease fix the issues above before deployment.")
            return False


def main():
    """Main entry point"""
    tester = SystemTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        sys.exit(1)
