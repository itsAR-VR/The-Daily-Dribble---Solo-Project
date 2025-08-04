#!/usr/bin/env python3
"""
Monitor Railway deployment status
Checks if anti-hallucination system is deployed
"""

import requests
import time
import json
from datetime import datetime

RAILWAY_URL = "https://listing-bot-api-production.up.railway.app"

def check_deployment_status():
    """Check if Railway has deployed the latest code"""
    print(f"🔍 Monitoring Railway deployment: {RAILWAY_URL}")
    print("=" * 60)
    
    # Check basic health
    try:
        response = requests.get(f"{RAILWAY_URL}/", timeout=10)
        data = response.json()
        
        print(f"✅ API is responding")
        print(f"📊 Version: {data.get('version', 'unknown')}")
        print(f"🤖 AI Features: {data.get('ai_features', 'unknown')}")
        print(f"🔧 Chrome Status: {data.get('chrome_status', 'unknown')}")
        print(f"📧 Gmail Status: {data.get('gmail_status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ API not responding: {e}")
        return False
    
    # Check if anti-hallucination endpoint exists
    print("\n🧪 Testing Anti-Hallucination Endpoint...")
    try:
        test_data = {
            "category": "Apple > iPhone",
            "brand": "Apple",
            "model": "iPhone 14 Pro Test",
            "available_quantity": 1,
            "price": 999.99,
            "comments": "Anti-hallucination test",
            "remarks": "Testing deployment"
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/test/enhanced-2fa/cellpex",
            json=test_data,
            timeout=30
        )
        
        result = response.json()
        
        if "enhanced_platform_poster" in str(result):
            print("❌ Module still missing - deployment in progress...")
            return False
        elif result.get("success") is not None:
            print("✅ Anti-hallucination endpoint is working!")
            print(f"📊 Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"⚠️ Unexpected response: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Anti-hallucination endpoint error: {e}")
        return False

def monitor_until_ready(max_wait_minutes=10):
    """Monitor deployment until ready or timeout"""
    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60
    
    print(f"\n⏰ Monitoring for up to {max_wait_minutes} minutes...")
    
    while time.time() - start_time < max_wait_seconds:
        print(f"\n🕐 {datetime.now().strftime('%H:%M:%S')} - Checking deployment...")
        
        if check_deployment_status():
            print("\n🎉 DEPLOYMENT SUCCESSFUL!")
            print("✅ Anti-hallucination system is live on Railway!")
            return True
        
        print("\n⏳ Waiting 30 seconds before next check...")
        time.sleep(30)
    
    print(f"\n⏱️ Timeout after {max_wait_minutes} minutes")
    return False

if __name__ == "__main__":
    print("🚂 Railway Deployment Monitor")
    print("=" * 60)
    
    # Quick status check
    check_deployment_status()
    
    print("\n" + "=" * 60)
    print("📝 Next Steps:")
    print("1. Check Railway dashboard for build logs")
    print("2. Wait for deployment to complete (3-5 minutes)")
    print("3. Run this script again to verify deployment")
    print("\nOr run with monitoring: python monitor_railway_deployment.py --monitor")