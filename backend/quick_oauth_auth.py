#!/usr/bin/env python3
"""
Quick OAuth authentication helper
This script helps complete the OAuth flow quickly
"""

import sys
import os
import webbrowser
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def main():
    """Help user complete OAuth authentication"""
    print("🚀 Gmail OAuth Quick Authentication Helper\n")
    
    try:
        from gmail_service import gmail_service
        
        # Check current status
        if gmail_service.service:
            print("✅ Gmail is already authenticated!")
            print("🔍 Run test_gmail_2fa_integration.py to test 2FA workflows")
            return 0
        
        # Generate auth URL
        auth_url, state = gmail_service.get_authorization_url()
        
        print("📋 OAuth Authentication Steps:\n")
        print("1️⃣ Opening browser to Google authorization page...")
        print("2️⃣ Sign in with your Google account")
        print("3️⃣ Grant access to Gmail (read-only)")
        print("4️⃣ You'll be redirected to: http://localhost:8000/gmail/callback?code=...")
        print("5️⃣ Copy the 'code' parameter from the URL\n")
        
        # Try to open browser
        try:
            webbrowser.open(auth_url)
            print("✅ Browser opened with authorization URL")
        except:
            print("⚠️  Could not open browser automatically")
            print(f"🔗 Please visit:\n{auth_url}\n")
        
        print("\n" + "="*60 + "\n")
        
        # Wait for user to complete auth
        print("📝 After completing Google authentication...")
        auth_code = input("Paste the authorization code here: ").strip()
        
        if not auth_code:
            print("❌ No code provided")
            return 1
        
        print(f"\n🔄 Exchanging code for credentials...")
        
        # Exchange code
        success = gmail_service.exchange_code_for_credentials(auth_code)
        
        if success:
            print("✅ OAuth authentication successful!")
            print("🔍 Testing Gmail access...")
            
            # Test API access
            try:
                profile = gmail_service.service.users().getProfile(userId='me').execute()
                print(f"✅ Gmail API working!")
                print(f"📧 Authenticated as: {profile.get('emailAddress')}")
                print(f"\n🎉 You're all set!")
                print("🔍 Run test_gmail_2fa_integration.py to test 2FA workflows")
            except Exception as e:
                print(f"⚠️  Gmail API test failed: {e}")
            
            return 0
        else:
            print("❌ Failed to exchange code for credentials")
            print("💡 Make sure you copied the entire code parameter")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())