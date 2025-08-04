#!/usr/bin/env python3
"""
Chrome Driver Fix for macOS
Ensures Chrome and ChromeDriver work properly
"""

import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def create_driver() -> webdriver.Chrome:
    """Create Chrome driver with proper macOS configuration"""
    options = Options()
    
    # Development mode - show browser
    # Comment out for headless mode
    # options.add_argument("--headless")
    
    # Standard options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Disable automation detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # macOS specific Chrome path
    if platform.system() == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                print(f"✅ Found Chrome at: {path}")
                break
    
    # Set ChromeDriver path if available
    chromedriver_path = "/opt/homebrew/bin/chromedriver"
    
    try:
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Let Selenium find ChromeDriver
            driver = webdriver.Chrome(options=options)
        
        print("✅ Chrome driver created successfully")
        return driver
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        raise

def test_chrome_driver():
    """Test Chrome driver creation"""
    try:
        print("🔍 Testing Chrome driver...")
        driver = create_driver()
        print("✅ Chrome driver works!")
        
        # Test navigation
        driver.get("https://www.google.com")
        print(f"✅ Navigated to: {driver.title}")
        
        driver.quit()
        print("✅ Chrome driver test complete")
        return True
    except Exception as e:
        print(f"❌ Chrome driver test failed: {e}")
        return False

if __name__ == "__main__":
    test_chrome_driver()
"""
Chrome Driver Fix for macOS
Ensures Chrome and ChromeDriver work properly
"""

import os
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def create_driver() -> webdriver.Chrome:
    """Create Chrome driver with proper macOS configuration"""
    options = Options()
    
    # Development mode - show browser
    # Comment out for headless mode
    # options.add_argument("--headless")
    
    # Standard options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    options.add_argument("--disable-ipc-flooding-protection")
    
    # Disable automation detection
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    # macOS specific Chrome path
    if platform.system() == "Darwin":  # macOS
        chrome_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                options.binary_location = path
                print(f"✅ Found Chrome at: {path}")
                break
    
    # Set ChromeDriver path if available
    chromedriver_path = "/opt/homebrew/bin/chromedriver"
    
    try:
        if os.path.exists(chromedriver_path):
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            # Let Selenium find ChromeDriver
            driver = webdriver.Chrome(options=options)
        
        print("✅ Chrome driver created successfully")
        return driver
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        raise

def test_chrome_driver():
    """Test Chrome driver creation"""
    try:
        print("🔍 Testing Chrome driver...")
        driver = create_driver()
        print("✅ Chrome driver works!")
        
        # Test navigation
        driver.get("https://www.google.com")
        print(f"✅ Navigated to: {driver.title}")
        
        driver.quit()
        print("✅ Chrome driver test complete")
        return True
    except Exception as e:
        print(f"❌ Chrome driver test failed: {e}")
        return False

if __name__ == "__main__":
    test_chrome_driver()