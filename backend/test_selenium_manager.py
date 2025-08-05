#!/usr/bin/env python3
"""
Test Selenium Manager approach for Chrome driver
This tests if Selenium can automatically download and manage ChromeDriver
"""

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def test_selenium_manager():
    """Test Chrome driver creation with Selenium Manager"""
    print("🧪 Testing Selenium Manager Chrome Driver Creation")
    print("=" * 60)
    
    # Show environment
    print("\n📊 Environment:")
    print(f"Python version: {os.sys.version.split()[0]}")
    print(f"Selenium version: {webdriver.__version__}")
    print(f"CHROME_BIN: {os.getenv('CHROME_BIN', 'Not set')}")
    print(f"Platform: {os.sys.platform}")
    
    # Set up Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    # Add Chrome binary location if set
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        print(f"Using Chrome binary: {chrome_bin}")
    
    try:
        print("\n🚀 Creating Chrome driver with Selenium Manager...")
        start_time = time.time()
        
        # Create driver - Selenium will download ChromeDriver if needed
        driver = webdriver.Chrome(options=options)
        
        creation_time = time.time() - start_time
        print(f"✅ Chrome driver created successfully in {creation_time:.2f} seconds")
        
        # Test navigation
        print("\n🌐 Testing navigation...")
        driver.get("https://www.google.com")
        print(f"Page title: {driver.title}")
        
        # Take a screenshot
        screenshot_path = "test_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Screenshot saved to: {screenshot_path}")
        
        # Get Chrome and ChromeDriver versions
        capabilities = driver.capabilities
        print(f"\n📋 Browser info:")
        print(f"Browser: {capabilities.get('browserName', 'Unknown')}")
        print(f"Browser version: {capabilities.get('browserVersion', 'Unknown')}")
        print(f"ChromeDriver version: {capabilities.get('chrome', {}).get('chromedriverVersion', 'Unknown').split()[0]}")
        
        driver.quit()
        print("\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Additional debugging
        import subprocess
        print("\n🔍 Debugging info:")
        
        # Check for Chrome
        for cmd in ["google-chrome", "google-chrome-stable", "chromium"]:
            try:
                result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ {cmd}: {result.stdout.strip()}")
            except:
                print(f"❌ {cmd}: Not found")
        
        # Check Selenium cache
        selenium_cache = os.path.expanduser("~/.cache/selenium")
        if os.path.exists(selenium_cache):
            print(f"\n📁 Selenium cache exists at: {selenium_cache}")
            try:
                for root, dirs, files in os.walk(selenium_cache):
                    for file in files:
                        if "chromedriver" in file:
                            print(f"  Found: {os.path.join(root, file)}")
            except:
                pass
        
        return False

if __name__ == "__main__":
    test_selenium_manager()