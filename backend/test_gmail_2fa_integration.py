#!/usr/bin/env python3
"""
Test script for Gmail 2FA integration with platform-specific code retrieval
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Platform configurations for testing
PLATFORMS = {
    'gsmexchange': {
        'name': 'GSM Exchange',
        'email_patterns': ['noreply@gsmexchange.com', 'support@gsmexchange.com'],
        'subject_keywords': ['verification', 'code', 'login', 'security'],
        'test_enabled': True
    },
    'cellpex': {
        'name': 'Cellpex',
        'email_patterns': ['noreply@cellpex.com', 'support@cellpex.com'],
        'subject_keywords': ['verification', 'code', 'login', 'security'],
        'test_enabled': True
    },
    'kardof': {
        'name': 'Kardof',
        'email_patterns': ['noreply@kardof.com', 'support@kardof.com'],
        'subject_keywords': ['verification', 'code', 'login', 'security'],
        'test_enabled': True
    },
    'hubx': {
        'name': 'HubX',
        'email_patterns': ['noreply@hubx.com', 'support@hubx.com'],
        'subject_keywords': ['verification', 'code', 'login', 'security'],
        'test_enabled': True
    },
    'handlot': {
        'name': 'Handlot',
        'email_patterns': ['noreply@handlot.com', 'support@handlot.com'],
        'subject_keywords': ['verification', 'code', 'login', 'security'],
        'test_enabled': True
    }
}

def test_gmail_auth_status():
    """Test Gmail authentication status"""
    print("🔍 Testing Gmail authentication status...")
    
    try:
        from gmail_service import gmail_service
        
        if gmail_service.service:
            print("✅ Gmail service is authenticated and ready!")
            return True
        else:
            print("❌ Gmail service not authenticated")
            if gmail_service.credentials:
                print("   ⚠️  Credentials exist but service not initialized")
            else:
                print("   ⚠️  No credentials found - need to authenticate")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Gmail status: {e}")
        return False

def test_gmail_api_access():
    """Test basic Gmail API access"""
    print("\n🔍 Testing Gmail API access...")
    
    try:
        from gmail_service import gmail_service
        
        if not gmail_service.service:
            print("❌ Gmail service not available")
            return False
            
        # Try to get user profile
        try:
            profile = gmail_service.service.users().getProfile(userId='me').execute()
            print(f"✅ Gmail API access successful!")
            print(f"   📧 Email: {profile.get('emailAddress')}")
            print(f"   📊 Total messages: {profile.get('messagesTotal')}")
            print(f"   💾 History ID: {profile.get('historyId')}")
            return True
        except Exception as e:
            print(f"❌ Gmail API access failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Gmail API: {e}")
        return False

def test_platform_2fa_search(platform_key):
    """Test 2FA code search for a specific platform"""
    platform = PLATFORMS.get(platform_key)
    if not platform:
        print(f"❌ Unknown platform: {platform_key}")
        return False
        
    print(f"\n🔍 Testing 2FA code search for {platform['name']}...")
    
    try:
        from gmail_service import gmail_service
        
        if not gmail_service.service:
            print("❌ Gmail service not available")
            return False
            
        # Search for verification codes
        print(f"   🔎 Searching for codes from the last 60 minutes...")
        codes = gmail_service.search_verification_codes(platform_key, minutes_back=60)
        
        if codes:
            print(f"   ✅ Found {len(codes)} verification code(s)!")
            for i, code_info in enumerate(codes[:3]):  # Show first 3
                print(f"   📧 Code {i+1}:")
                print(f"      - Code: {code_info['code']}")
                print(f"      - Subject: {code_info['subject']}")
                print(f"      - From: {code_info['sender']}")
                print(f"      - Date: {code_info['date']}")
            
            # Test getting latest code
            latest = gmail_service.get_latest_verification_code(platform_key)
            if latest:
                print(f"   🎯 Latest code: {latest}")
            
            return True
        else:
            print(f"   ⚠️  No verification codes found for {platform['name']}")
            print(f"   💡 This is normal if no 2FA emails were sent recently")
            return True  # Not finding codes is not an error
            
    except Exception as e:
        print(f"❌ Error searching for {platform['name']} codes: {e}")
        return False

def test_all_platforms():
    """Test 2FA code retrieval for all platforms"""
    print("\n🚀 Testing 2FA code retrieval for all platforms...")
    
    results = {}
    for platform_key, platform in PLATFORMS.items():
        if platform['test_enabled']:
            results[platform_key] = test_platform_2fa_search(platform_key)
        else:
            print(f"\n⏭️  Skipping {platform['name']} (disabled)")
    
    # Summary
    print("\n📊 Platform Test Summary:")
    for platform_key, success in results.items():
        status = "✅ Pass" if success else "❌ Fail"
        print(f"   {PLATFORMS[platform_key]['name']}: {status}")
    
    return all(results.values())

def simulate_2fa_workflow(platform_key):
    """Simulate the complete 2FA workflow for a platform"""
    print(f"\n🎭 Simulating 2FA workflow for {PLATFORMS[platform_key]['name']}...")
    
    try:
        from gmail_service import gmail_service
        
        print("   1️⃣ Bot attempts login...")
        print("   2️⃣ Platform sends 2FA code to email...")
        print("   3️⃣ Waiting for email to arrive...")
        
        # In real scenario, wait a bit for email
        time.sleep(2)
        
        print("   4️⃣ Checking Gmail for verification code...")
        code = gmail_service.get_latest_verification_code(platform_key)
        
        if code:
            print(f"   5️⃣ Retrieved 2FA code: {code}")
            print("   6️⃣ Bot enters code and continues...")
            print("   ✅ 2FA workflow simulation successful!")
            return True
        else:
            print("   ⚠️  No code found (this is a simulation)")
            print("   💡 In production, the bot would retry or handle this case")
            return True
            
    except Exception as e:
        print(f"❌ Error in 2FA workflow: {e}")
        return False

def main():
    """Run all Gmail 2FA integration tests"""
    print("🚀 Gmail 2FA Integration Test Suite\n")
    
    # Check authentication
    if not test_gmail_auth_status():
        print("\n⚠️  Gmail not authenticated!")
        print("📋 To authenticate:")
        print("   1. Run: python test_oauth_flow.py")
        print("   2. Visit the authorization URL")
        print("   3. Complete Google authentication")
        print("   4. Copy the code from callback URL")
        print("   5. Run: python test_oauth_callback.py YOUR_CODE")
        return 1
    
    # Test API access
    if not test_gmail_api_access():
        print("\n❌ Gmail API access failed")
        return 1
    
    # Test all platforms
    test_all_platforms()
    
    # Simulate workflow for GSM Exchange
    print("\n" + "="*60)
    simulate_2fa_workflow('gsmexchange')
    
    print("\n✅ Gmail 2FA integration tests complete!")
    print("\n📋 Next steps:")
    print("   1. Deploy to Railway with environment variables")
    print("   2. Set up platform credentials (PLATFORM_USERNAME, PLATFORM_PASSWORD)")
    print("   3. Test live 2FA workflows with actual platform logins")
    print("   4. Monitor Gmail for real verification codes")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())