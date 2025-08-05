#!/usr/bin/env python3
"""
Chrome workaround for Railway deployment
This script tests different Chrome configurations to find what works
"""

import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def test_chrome_config(config_name, setup_func):
    """Test a Chrome configuration"""
    print(f"\n🧪 Testing: {config_name}")
    print("-" * 50)
    
    try:
        driver = setup_func()
        driver.get("data:text/html,<h1>Chrome Works!</h1>")
        title = driver.title
        driver.quit()
        print(f"✅ SUCCESS! Title: {title}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def config1_selenium_manager():
    """Let Selenium Manager handle everything"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        
    return webdriver.Chrome(options=options)

def config2_explicit_path():
    """Use explicit ChromeDriver path"""
    os.environ['SE_SKIP_DRIVER_DOWNLOAD'] = '1'
    
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        options.binary_location = chrome_bin
        
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
    service = Service(executable_path=chromedriver_path)
    return webdriver.Chrome(service=service, options=options)

def config3_minimal():
    """Minimal configuration"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    return webdriver.Chrome(options=options)

def config4_full_flags():
    """All possible flags"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--single-process")
    
    chrome_bin = os.getenv("CHROME_BIN", "/usr/bin/google-chrome-stable")
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
        
    return webdriver.Chrome(options=options)

def main():
    print("🔧 Chrome Workaround Script for Railway")
    print("=" * 70)
    
    # Print environment
    print("\n📊 Environment:")
    print(f"CHROME_BIN: {os.getenv('CHROME_BIN')}")
    print(f"CHROMEDRIVER_PATH: {os.getenv('CHROMEDRIVER_PATH')}")
    print(f"PATH: {os.getenv('PATH')}")
    
    # Check Chrome binary
    print("\n🔍 Chrome Binary Check:")
    chrome_paths = [
        os.getenv("CHROME_BIN"),
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser"
    ]
    
    for path in chrome_paths:
        if path and os.path.exists(path):
            print(f"✅ Found Chrome at: {path}")
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   Version: {result.stdout.strip()}")
            except:
                pass
    
    # Check ChromeDriver
    print("\n🔍 ChromeDriver Check:")
    driver_paths = [
        os.getenv("CHROMEDRIVER_PATH"),
        "/usr/local/bin/chromedriver",
        "/usr/bin/chromedriver"
    ]
    
    for path in driver_paths:
        if path and os.path.exists(path):
            print(f"✅ Found ChromeDriver at: {path}")
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"   Version: {result.stdout.strip()}")
                else:
                    print(f"   ❌ Exit code: {result.returncode}")
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    # Test configurations
    configs = [
        ("Selenium Manager (Default)", config1_selenium_manager),
        ("Explicit ChromeDriver Path", config2_explicit_path),
        ("Minimal Configuration", config3_minimal),
        ("Full Flags Configuration", config4_full_flags)
    ]
    
    results = []
    for config_name, setup_func in configs:
        success = test_chrome_config(config_name, setup_func)
        results.append((config_name, success))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY:")
    for config_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {config_name}")
    
    successful = [name for name, success in results if success]
    if successful:
        print(f"\n🎉 Working configurations: {', '.join(successful)}")
    else:
        print("\n❌ No configurations worked. Chrome/ChromeDriver may need to be reinstalled.")

if __name__ == "__main__":
    main()