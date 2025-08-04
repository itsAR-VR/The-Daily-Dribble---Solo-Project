#!/usr/bin/env python3
"""
Live Railway Deployment Monitor
Monitors deployment until anti-hallucination system is live
"""

import requests
import time
from datetime import datetime

RAILWAY_URL = "https://listing-bot-api-production.up.railway.app"

def check_deployment_status():
    """Quick check if anti-hallucination is deployed"""
    try:
        response = requests.post(
            f"{RAILWAY_URL}/test/enhanced-2fa/cellpex",
            json={"category": "Test", "brand": "Test", "model": "Test", "available_quantity": 1, "price": 1},
            timeout=10
        )
        result = response.json()
        
        # Check for old code error
        if "enhanced_platform_poster" in str(result.get("error", "")):
            return "OLD_CODE"
        elif "success" in result or "platform" in result:
            return "NEW_CODE"
        else:
            return "UNKNOWN"
    except:
        return "ERROR"

def monitor_deployment():
    """Monitor deployment with live updates"""
    print("🚀 Live Railway Deployment Monitor")
    print("=" * 50)
    print("📝 What this monitors:")
    print("- ❌ OLD_CODE: Still running without anti-hallucination")
    print("- ✅ NEW_CODE: Anti-hallucination system deployed!")
    print("- 🔄 ERROR: API not responding (deployment in progress)")
    print("=" * 50)
    
    start_time = time.time()
    check_count = 0
    
    while True:
        check_count += 1
        current_time = datetime.now().strftime("%H:%M:%S")
        elapsed = int(time.time() - start_time)
        
        status = check_deployment_status()
        
        if status == "NEW_CODE":
            print(f"\n🎉 SUCCESS at {current_time}!")
            print("✅ Anti-hallucination system is LIVE!")
            print("🔥 Your bot will now report honest results!")
            break
        elif status == "OLD_CODE":
            print(f"⏳ {current_time} (#{check_count}, {elapsed}s) - Still OLD_CODE")
        elif status == "ERROR":
            print(f"🔄 {current_time} (#{check_count}, {elapsed}s) - API down (deploying?)")
        else:
            print(f"❓ {current_time} (#{check_count}, {elapsed}s) - Status: {status}")
        
        # Give up after 10 minutes
        if elapsed > 600:
            print(f"\n⏱️ Timeout after 10 minutes")
            print("💡 Check Railway Dashboard for deployment status")
            break
        
        # Check every 30 seconds
        time.sleep(30)

if __name__ == "__main__":
    print("🎯 Starting live monitoring...")
    print("💡 Press Ctrl+C to stop")
    print()
    
    try:
        monitor_deployment()
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
    
    print("\n📝 Next steps if deployment isn't working:")
    print("1. Check Railway Dashboard for build logs")
    print("2. Verify GitHub repo has latest commits")
    print("3. Manual redeploy in Railway Dashboard")