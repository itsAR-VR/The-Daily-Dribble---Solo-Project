#!/usr/bin/env python3
"""
Test Chrome driver specifically on Railway deployment
"""

import requests
import json
from datetime import datetime

RAILWAY_URL = "https://listing-bot-api-production.up.railway.app"

def test_chrome_endpoint():
    """Test the Chrome driver endpoint directly"""
    print("🔧 Testing Chrome Driver on Railway")
    print("=" * 50)
    
    try:
        # Test the enhanced endpoint which should create a Chrome driver
        response = requests.post(
            f"{RAILWAY_URL}/test/enhanced-2fa/cellpex",
            json={
                "category": "Test",
                "brand": "Test",
                "model": "Test",
                "available_quantity": 1,
                "price": 1
            },
            timeout=30
        )
        
        result = response.json()
        print(f"📊 Status Code: {response.status_code}")
        print(f"📝 Response: {json.dumps(result, indent=2)}")
        
        # Check for Chrome-related errors
        if "error" in result:
            error_msg = str(result["error"]).lower()
            if "chrome" in error_msg or "driver" in error_msg:
                print("\n❌ Chrome Driver Issue Detected!")
                print(f"Error: {result['error']}")
                
                # Provide debugging info
                if "details" in result:
                    print(f"\n🔍 Error Details:")
                    print(json.dumps(result["details"], indent=2))
            else:
                print("\n⚠️ Non-Chrome Error:")
                print(f"Error: {result['error']}")
        else:
            print("\n✅ Chrome Driver Working!")
            print("The bot can create browser instances successfully.")
            
    except requests.exceptions.Timeout:
        print("\n⏱️ Request timed out (30s)")
        print("This might indicate Chrome is starting but taking too long")
    except Exception as e:
        print(f"\n❌ Request failed: {e}")

def test_basic_health():
    """Test basic API health"""
    try:
        response = requests.get(f"{RAILWAY_URL}/", timeout=10)
        data = response.json()
        print(f"\n📊 Basic API Health:")
        print(f"- Status: {data.get('status', 'unknown')}")
        print(f"- Chrome: {data.get('chrome_status', 'unknown')}")
        print(f"- Gmail: {data.get('gmail_status', 'unknown')}")
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")

if __name__ == "__main__":
    print(f"🚀 Railway Chrome Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Test basic health first
    test_basic_health()
    
    # Then test Chrome specifically
    print("\n" + "=" * 50)
    test_chrome_endpoint()
    
    print("\n💡 If Chrome is not working:")
    print("1. Check Railway build logs for Chrome installation errors")
    print("2. Ensure CHROME_BIN env var is set correctly")
    print("3. Railway may need a manual redeploy")
    print("4. Chrome installation might need more time to complete")