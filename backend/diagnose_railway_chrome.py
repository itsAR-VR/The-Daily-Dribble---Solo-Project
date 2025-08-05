#!/usr/bin/env python3
"""
Diagnose Chrome issues on Railway deployment
"""

import requests
import json
from datetime import datetime

RAILWAY_URL = "https://listing-bot-api-production.up.railway.app"

def diagnose_chrome():
    """Get detailed Chrome diagnostics from Railway"""
    print("🔍 Chrome Diagnostic Tool for Railway")
    print("=" * 50)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check environment diagnostics
    print("📊 Checking Railway Environment...")
    try:
        response = requests.get(f"{RAILWAY_URL}/debug/environment", timeout=10)
        if response.status_code == 200:
            env_data = response.json()
            print(f"- Python Version: {env_data.get('python_version', 'Unknown')}")
            print(f"- Platform: {env_data.get('platform', 'Unknown')}")
            print(f"- Chrome Binary: {env_data.get('chrome_bin', 'Not set')}")
            print(f"- ChromeDriver Path: {env_data.get('chromedriver_path', 'Not set')}")
            print()
            
            # Check Chrome installation
            print("🔧 Chrome Installation Check:")
            chrome_check = env_data.get('chrome_check', {})
            print(f"- Chrome Installed: {chrome_check.get('installed', False)}")
            print(f"- Chrome Version: {chrome_check.get('version', 'Not found')}")
            print(f"- Chrome Path: {chrome_check.get('path', 'Not found')}")
            print()
            
            # Check ChromeDriver
            print("🔧 ChromeDriver Check:")
            driver_check = env_data.get('chromedriver_check', {})
            print(f"- ChromeDriver Installed: {driver_check.get('installed', False)}")
            print(f"- ChromeDriver Version: {driver_check.get('version', 'Not found')}")
            print(f"- ChromeDriver Path: {driver_check.get('path', 'Not found')}")
            print()
            
            # Check missing libraries
            if 'missing_libs' in env_data:
                print("❌ Missing Libraries:")
                for lib in env_data['missing_libs']:
                    print(f"  - {lib}")
                print()
                
        else:
            print(f"❌ Failed to get environment info: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking environment: {e}")
    
    # Test Chrome creation with verbose output
    print("\n🧪 Testing Chrome Driver Creation...")
    try:
        response = requests.post(
            f"{RAILWAY_URL}/debug/test-chrome",
            json={"verbose": True},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"- Success: {result.get('success', False)}")
            
            if result.get('error'):
                print(f"- Error: {result['error']}")
                
            if result.get('logs'):
                print("\n📋 Detailed Logs:")
                for log in result['logs']:
                    print(f"  {log}")
                    
        else:
            print(f"❌ Test failed: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing Chrome: {e}")
    
    print("\n" + "=" * 50)
    print("💡 Common Solutions:")
    print("1. Ensure all Chrome dependencies are installed in Dockerfile")
    print("2. Check that ChromeDriver matches Chrome version")
    print("3. Verify CHROME_BIN and CHROMEDRIVER_PATH env vars")
    print("4. Try a manual Railway redeploy")
    print("5. Check Railway build logs for installation errors")

if __name__ == "__main__":
    diagnose_chrome()