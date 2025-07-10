#!/usr/bin/env python3
"""
macOS Chrome/ChromeDriver Detection and Initialization Fix
"""

import os
import shutil
import platform
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

class EnhancedChromeDetector:
    """Enhanced Chrome detection for cross-platform compatibility"""
    
    def __init__(self):
        self.system = platform.system()
        self.chrome_path = None
        self.chromedriver_path = None
    
    def _check_chrome_available(self):
        """Enhanced Chrome detection for macOS, Linux, and Windows"""
        
        if self.system == "Darwin":  # macOS
            return self._check_chrome_macos()
        elif self.system == "Linux":
            return self._check_chrome_linux()
        elif self.system == "Windows":
            return self._check_chrome_windows()
        else:
            return False
    
    def _check_chrome_macos(self):
        """Check for Chrome on macOS"""
        # Standard Chrome installation paths on macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            "/Applications/Chrome.app/Contents/MacOS/Chrome",
            # Homebrew installations
            "/opt/homebrew/bin/chrome",
            "/usr/local/bin/chrome"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                self.chrome_path = path
                print(f"✅ Chrome found at: {path}")
                return True
        
        # Check if Chrome app bundle exists (even if binary path is different)
        app_bundles = [
            "/Applications/Google Chrome.app",
            "/Applications/Chromium.app"
        ]
        
        for bundle in app_bundles:
            if os.path.exists(bundle):
                # Try to find the executable inside the bundle
                possible_executables = [
                    f"{bundle}/Contents/MacOS/Google Chrome",
                    f"{bundle}/Contents/MacOS/Chromium",
                    f"{bundle}/Contents/MacOS/Chrome"
                ]
                
                for executable in possible_executables:
                    if os.path.exists(executable):
                        self.chrome_path = executable
                        print(f"✅ Chrome found in app bundle: {executable}")
                        return True
        
        return False
    
    def _check_chrome_linux(self):
        """Check for Chrome on Linux"""
        chrome_commands = ['google-chrome', 'chromium-browser', 'chromium', 'chrome']
        
        for command in chrome_commands:
            path = shutil.which(command)
            if path:
                self.chrome_path = path
                print(f"✅ Chrome found: {command} at {path}")
                return True
        
        return False
    
    def _check_chrome_windows(self):
        """Check for Chrome on Windows"""
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.getenv('USERNAME', '')),
            r"C:\Program Files\Chromium\Application\chromium.exe"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                self.chrome_path = path
                print(f"✅ Chrome found at: {path}")
                return True
        
        return False
    
    def _check_chromedriver_available(self):
        """Enhanced ChromeDriver detection"""
        
        # First, try to find chromedriver in PATH
        chromedriver_path = shutil.which('chromedriver')
        if chromedriver_path:
            self.chromedriver_path = chromedriver_path
            print(f"✅ ChromeDriver found in PATH: {chromedriver_path}")
            return True
        
        # macOS specific paths
        if self.system == "Darwin":
            macos_paths = [
                "/opt/homebrew/bin/chromedriver",  # Homebrew M1/M2
                "/usr/local/bin/chromedriver",     # Homebrew Intel
                "/opt/local/bin/chromedriver",     # MacPorts
                "/usr/bin/chromedriver"            # System install
            ]
            
            for path in macos_paths:
                if os.path.exists(path):
                    self.chromedriver_path = path
                    print(f"✅ ChromeDriver found at: {path}")
                    return True
        
        # Try to get version to confirm it's working
        try:
            result = subprocess.run(['chromedriver', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ ChromeDriver version: {result.stdout.strip()}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return False
    
    def initialize_web_driver(self, headless=True):
        """Initialize Selenium WebDriver with proper Chrome configuration"""
        
        if not self._check_chrome_available():
            print("❌ Chrome not found")
            return None
        
        if not self._check_chromedriver_available():
            print("❌ ChromeDriver not found")
            print("💡 Install with: brew install chromedriver")
            return None
        
        try:
            # Configure Chrome options
            chrome_options = Options()
            
            if headless:
                chrome_options.add_argument("--headless")
            
            # Essential arguments for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set user agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # macOS specific: Set Chrome binary location if we found a custom path
            if self.system == "Darwin" and self.chrome_path:
                chrome_options.binary_location = self.chrome_path
            
            # Create service object if we have a specific chromedriver path
            service = None
            if self.chromedriver_path:
                service = Service(self.chromedriver_path)
            
            # Initialize driver
            if service:
                driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                driver = webdriver.Chrome(options=chrome_options)
            
            print("✅ Selenium WebDriver initialized successfully")
            
            # Test the driver
            driver.get("https://www.google.com")
            print("✅ WebDriver test successful")
            
            return driver
            
        except Exception as e:
            print(f"❌ WebDriver initialization failed: {e}")
            return None
    
    def get_installation_instructions(self):
        """Get platform-specific installation instructions"""
        
        if self.system == "Darwin":  # macOS
            return [
                "🔧 macOS Installation Instructions:",
                "",
                "Install Chrome:",
                "  • Download from: https://www.google.com/chrome/",
                "  • Or via Homebrew: brew install --cask google-chrome",
                "",
                "Install ChromeDriver:",
                "  • Via Homebrew: brew install chromedriver",
                "  • Or download from: https://chromedriver.chromium.org/",
                "",
                "Verify installation:",
                "  • Chrome: ls '/Applications/Google Chrome.app'",
                "  • ChromeDriver: which chromedriver",
                "  • ChromeDriver version: chromedriver --version"
            ]
        elif self.system == "Linux":
            return [
                "🔧 Linux Installation Instructions:",
                "",
                "Ubuntu/Debian:",
                "  sudo apt-get update",
                "  sudo apt-get install google-chrome-stable",
                "  sudo apt-get install chromium-chromedriver",
                "",
                "CentOS/RHEL:",
                "  sudo yum install google-chrome-stable",
                "  sudo yum install chromium-chromedriver"
            ]
        else:
            return [
                "🔧 Windows Installation Instructions:",
                "",
                "Install Chrome:",
                "  • Download from: https://www.google.com/chrome/",
                "",
                "Install ChromeDriver:",
                "  • Download from: https://chromedriver.chromium.org/",
                "  • Add to PATH or place in project directory"
            ]

# Updated CompleteDataScraper methods
class CompleteDataScraper:
    """Your existing scraper with enhanced Chrome detection"""
    
    def __init__(self):
        # ... your existing init code ...
        
        # Replace the old detection with enhanced detection
        self.chrome_detector = EnhancedChromeDetector()
        self.web_scraping_enabled = self._check_web_scraping_availability()
        self.driver = None
    
    def _check_web_scraping_availability(self):
        """Check if web scraping is available with enhanced detection"""
        
        print("🔍 Checking web scraping capabilities...")
        
        if not self.chrome_detector._check_chrome_available():
            print("⚠️  Chrome not found")
            instructions = self.chrome_detector.get_installation_instructions()
            for line in instructions:
                print(f"   {line}")
            return False
        
        if not self.chrome_detector._check_chromedriver_available():
            print("⚠️  ChromeDriver not found")
            if self.chrome_detector.system == "Darwin":
                print("   💡 Install with: brew install chromedriver")
            return False
        
        print("✅ Web scraping capabilities available")
        return True
    
    def initialize_web_driver(self):
        """Initialize web driver using enhanced detector"""
        
        if not self.web_scraping_enabled:
            print("⚠️  Web scraping disabled - Chrome or ChromeDriver not available")
            return False
        
        try:
            self.driver = self.chrome_detector.initialize_web_driver(headless=True)
            if self.driver:
                print("✅ Web driver initialized for enhanced data collection")
                return True
            else:
                print("❌ Web driver initialization failed")
                self.web_scraping_enabled = False
                return False
                
        except Exception as e:
            print(f"❌ Web driver initialization error: {e}")
            self.web_scraping_enabled = False
            return False
    
    def cleanup_driver(self):
        """Clean up the web driver"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Web driver cleaned up")
            except Exception as e:
                print(f"⚠️  Driver cleanup warning: {e}")
            finally:
                self.driver = None

# Test function for your system
def test_chrome_detection():
    """Test the enhanced Chrome detection"""
    
    print("🧪 Testing Enhanced Chrome Detection")
    print("=" * 40)
    
    detector = EnhancedChromeDetector()
    
    print(f"Operating System: {detector.system}")
    print()
    
    # Test Chrome detection
    chrome_available = detector._check_chrome_available()
    print(f"Chrome Available: {'✅ Yes' if chrome_available else '❌ No'}")
    if chrome_available:
        print(f"Chrome Path: {detector.chrome_path}")
    print()
    
    # Test ChromeDriver detection
    chromedriver_available = detector._check_chromedriver_available()
    print(f"ChromeDriver Available: {'✅ Yes' if chromedriver_available else '❌ No'}")
    if chromedriver_available:
        print(f"ChromeDriver Path: {detector.chromedriver_path}")
    print()
    
    # Test WebDriver initialization
    if chrome_available and chromedriver_available:
        print("🚀 Testing WebDriver initialization...")
        driver = detector.initialize_web_driver(headless=True)
        
        if driver:
            print("✅ WebDriver test successful!")
            
            # Quick test
            try:
                driver.get("https://www.sofascore.com")
                title = driver.title
                print(f"✅ Page loaded: {title[:50]}...")
            except Exception as e:
                print(f"⚠️  Page load test failed: {e}")
            finally:
                driver.quit()
        else:
            print("❌ WebDriver initialization failed")
    else:
        print("⚠️  Skipping WebDriver test - missing dependencies")
        
        print("\n📋 Installation needed:")
        instructions = detector.get_installation_instructions()
        for line in instructions:
            print(line)

if __name__ == "__main__":
    test_chrome_detection()