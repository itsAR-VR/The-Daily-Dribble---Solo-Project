#!/usr/bin/env python3
"""
Test ChromeDriver dependencies
"""

import os
import subprocess
import platform

def check_chromedriver_deps():
    """Check if ChromeDriver can run and what dependencies it needs"""
    print("🔍 ChromeDriver Dependency Check")
    print("=" * 60)
    
    # Find ChromeDriver in Selenium cache
    selenium_cache = os.path.expanduser("~/.cache/selenium")
    chromedriver_path = None
    
    if os.path.exists(selenium_cache):
        for root, dirs, files in os.walk(selenium_cache):
            for file in files:
                if file == "chromedriver":
                    chromedriver_path = os.path.join(root, file)
                    break
    
    if not chromedriver_path:
        print("❌ ChromeDriver not found in Selenium cache")
        return
    
    print(f"✅ Found ChromeDriver at: {chromedriver_path}")
    
    # Check if it's executable
    if not os.access(chromedriver_path, os.X_OK):
        print("❌ ChromeDriver is not executable")
        os.chmod(chromedriver_path, 0o755)
        print("✅ Made ChromeDriver executable")
    
    # Try to run it
    print("\n🚀 Testing ChromeDriver execution...")
    try:
        result = subprocess.run([chromedriver_path, "--version"], 
                               capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ ChromeDriver runs successfully: {result.stdout.strip()}")
        else:
            print(f"❌ ChromeDriver failed with exit code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            
            # Check dependencies with ldd
            if platform.system() == "Linux":
                print("\n📋 Checking dependencies with ldd...")
                ldd_result = subprocess.run(["ldd", chromedriver_path], 
                                          capture_output=True, text=True)
                print(ldd_result.stdout)
                
                # Check for missing libraries
                if "not found" in ldd_result.stdout:
                    print("❌ Missing libraries detected!")
                    missing_libs = [line.strip() for line in ldd_result.stdout.split('\n') 
                                   if "not found" in line]
                    for lib in missing_libs:
                        print(f"  Missing: {lib}")
    
    except Exception as e:
        print(f"❌ Error running ChromeDriver: {e}")
    
    # Also check Chrome
    print("\n🌐 Checking Chrome installation...")
    for chrome_cmd in ["google-chrome", "google-chrome-stable", "chromium"]:
        try:
            result = subprocess.run([chrome_cmd, "--version"], 
                                   capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {chrome_cmd}: {result.stdout.strip()}")
        except:
            print(f"❌ {chrome_cmd}: Not found")

if __name__ == "__main__":
    check_chromedriver_deps()