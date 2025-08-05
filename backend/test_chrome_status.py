#!/usr/bin/env python3
"""
Quick Chrome status check for Railway
"""

import requests
import json

RAILWAY_URL = "https://listing-bot-api-production.up.railway.app"

def test_chrome():
    print("🔍 Railway Chrome Status Check")
    print("=" * 50)
    
    # Test the new chrome status endpoint
    try:
        response = requests.get(f"{RAILWAY_URL}/test/chrome-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("\n📊 Environment Variables:")
            print(f"  CHROME_BIN: {data.get('chrome_bin', 'Not set')}")
            print(f"  CHROMEDRIVER_PATH: {data.get('chromedriver_path', 'Not set')}")
            print(f"  SE_CHROMEDRIVER_PATH: {data.get('se_chromedriver_path', 'Not set')}")
            print(f"  CHROME_USER_DATA_DIR: {data.get('chrome_user_data_dir', 'Not set')}")
            
            print(f"\n🚀 Startup Test: {'PASS' if data.get('startup_test_passed') else 'FAIL'}")
            if data.get('startup_error'):
                print(f"  Error: {data['startup_error']}")
                
            print(f"\n🧪 Runtime Test: {data.get('runtime_test', 'Unknown')}")
            if data.get('test_message'):
                print(f"  ✅ {data['test_message']}")
            if data.get('test_error'):
                print(f"  ❌ {data['test_error']}")
                
            if data.get('runtime_test') == 'PASS':
                print("\n🎉 Chrome is working! The bot can now create browser instances!")
            else:
                print("\n❌ Chrome is not working yet.")
                print("\n💡 To fix this, add these environment variables to Railway:")
                print("   CHROME_BIN=/usr/bin/google-chrome-stable")
                print("   CHROMEDRIVER_PATH=/usr/local/bin/chromedriver")
                print("   SE_CHROMEDRIVER_PATH=/usr/local/bin/chromedriver")
                print("   CHROME_USER_DATA_DIR=/tmp/.chrome")
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_chrome()