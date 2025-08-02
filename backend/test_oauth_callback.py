#!/usr/bin/env python3
"""
Script to test OAuth callback with authorization code
Usage: python test_oauth_callback.py YOUR_AUTHORIZATION_CODE
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_callback(auth_code):
    try:
        from gmail_service import gmail_service
        
        print(f"🔄 Exchanging authorization code for credentials...")
        success = gmail_service.exchange_code_for_credentials(auth_code)
        
        if success:
            print("✅ OAuth authentication successful!")
            print("🔍 Testing Gmail service...")
            
            # Test Gmail service
            if gmail_service.service:
                print("✅ Gmail service is now available!")
                print("📧 You can now use Gmail 2FA code retrieval")
                return True
            else:
                print("❌ Gmail service not available after authentication")
                return False
        else:
            print("❌ Failed to exchange code for credentials")
            return False
            
    except Exception as e:
        print(f"❌ Error in OAuth callback: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_oauth_callback.py YOUR_AUTHORIZATION_CODE")
        sys.exit(1)
    
    auth_code = sys.argv[1]
    success = test_callback(auth_code)
    sys.exit(0 if success else 1)
