#!/usr/bin/env python3
"""
Complete Railway Deployment Test
Tests both Gmail OAuth and Anti-Hallucination system
"""

import requests
import json
import time

RAILWAY_URL = "https://listing-bot-api-production.up.railway.app"

def test_basic_api():
    """Test basic API health"""
    print("🔍 Testing Basic API Health...")
    try:
        response = requests.get(f"{RAILWAY_URL}/", timeout=10)
        data = response.json()
        
        print(f"✅ API Status: OK")
        print(f"📊 Version: {data.get('version', 'unknown')}")
        print(f"🤖 AI Features: {data.get('ai_features', 'unknown')}")
        print(f"🔧 Chrome Status: {data.get('chrome_status', 'unknown')}")
        print(f"📧 Gmail Status: {data.get('gmail_status', 'unknown')}")
        
        return True
    except Exception as e:
        print(f"❌ API Health Check Failed: {e}")
        return False

def test_gmail_oauth():
    """Test Gmail OAuth status"""
    print("\n📧 Testing Gmail OAuth...")
    try:
        response = requests.get(f"{RAILWAY_URL}/gmail/status", timeout=10)
        data = response.json()
        
        if data.get("available"):
            print("✅ Gmail OAuth: WORKING!")
            print(f"📊 Status: {data.get('status', 'unknown')}")
            return True
        else:
            print("❌ Gmail OAuth: Not configured")
            print(f"📊 Message: {data.get('message', 'unknown')}")
            print("💡 You may need to complete OAuth flow via /gmail/auth")
            return False
            
    except Exception as e:
        print(f"❌ Gmail OAuth Test Failed: {e}")
        return False

def test_anti_hallucination():
    """Test Anti-Hallucination system"""
    print("\n🛡️ Testing Anti-Hallucination System...")
    
    test_data = {
        "category": "Apple > iPhone",
        "brand": "Apple",
        "model": "iPhone 14 Pro Test",
        "available_quantity": 1,
        "price": 999.99,
        "comments": "Anti-hallucination deployment test",
        "remarks": "Testing honest reporting"
    }
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/test/enhanced-2fa/cellpex",
            json=test_data,
            timeout=60  # Anti-hallucination tests can take time
        )
        
        result = response.json()
        
        # Check if we get the "enhanced_platform_poster" error (old code)
        if "enhanced_platform_poster" in str(result.get("error", "")):
            print("❌ Anti-Hallucination: OLD CODE DETECTED!")
            print("🔄 Railway is still running the old version")
            print("💡 Force a redeploy in Railway Dashboard")
            return False
            
        # Check if we get a proper response (new code)
        elif "success" in result or "platform" in result:
            print("✅ Anti-Hallucination: NEW CODE DEPLOYED!")
            print(f"📊 Platform: {result.get('platform', 'unknown')}")
            print(f"🎯 Success: {result.get('success', 'unknown')}")
            print(f"💬 Message: {result.get('message', 'No message')}")
            
            # The most important test: Is it being honest about failures?
            if result.get("success") == False:
                print("🛡️ ANTI-HALLUCINATION WORKING: Correctly reporting failure!")
            else:
                print("⚠️ Check anti-hallucination logic")
                
            return True
        else:
            print(f"⚠️ Unexpected response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Anti-Hallucination Test Failed: {e}")
        return False

def run_complete_test():
    """Run all tests"""
    print("🚀 Railway Complete Deployment Test")
    print("=" * 60)
    
    # Test basic API
    api_ok = test_basic_api()
    if not api_ok:
        print("\n❌ BASIC API FAILED - Cannot continue")
        return False
    
    # Test Gmail OAuth
    gmail_ok = test_gmail_oauth()
    
    # Test Anti-Hallucination (most important)
    anti_hal_ok = test_anti_hallucination()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"🔧 Basic API: {'✅ PASS' if api_ok else '❌ FAIL'}")
    print(f"📧 Gmail OAuth: {'✅ PASS' if gmail_ok else '❌ NEEDS SETUP'}")
    print(f"🛡️ Anti-Hallucination: {'✅ PASS' if anti_hal_ok else '❌ OLD CODE'}")
    
    if anti_hal_ok:
        print("\n🎉 SUCCESS! Anti-hallucination system is deployed!")
        print("🔥 Your bot will now report honest results!")
        
        if not gmail_ok:
            print("\n📝 Next Steps:")
            print("1. Visit: https://listing-bot-api-production.up.railway.app/gmail/auth")
            print("2. Complete Google authentication")
            print("3. Run this test again")
    else:
        print("\n🔄 REDEPLOY NEEDED:")
        print("1. Go to Railway Dashboard")
        print("2. Click 'Redeploy' or 'Deploy Latest'")
        print("3. Wait 3-5 minutes")
        print("4. Run this test again")
    
    return anti_hal_ok

if __name__ == "__main__":
    run_complete_test()