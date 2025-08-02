#!/usr/bin/env python3
"""
Simple test script to verify OAuth flow works end-to-end
"""

import sys
import os
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_oauth_authorization_url():
    """Test that we can generate OAuth authorization URL"""
    print("🔍 Testing OAuth authorization URL generation...")
    
    try:
        from gmail_service import gmail_service
        
        # Test getting authorization URL
        auth_url, state = gmail_service.get_authorization_url()
        
        print("✅ OAuth authorization URL generated successfully!")
        print(f"🔗 Authorization URL: {auth_url}")
        print(f"🎯 State parameter: {state}")
        print(f"📋 Instructions:")
        print(f"   1. Visit the authorization URL above")
        print(f"   2. Sign in with your Google account")
        print(f"   3. Grant access to Gmail")
        print(f"   4. Copy the authorization code from the callback URL")
        print(f"   5. Use it with exchange_code_for_credentials()")
        
        return True, auth_url, state
        
    except Exception as e:
        print(f"❌ Error generating OAuth URL: {e}")
        return False, None, None

def main():
    """Run OAuth flow test"""
    print("🚀 Testing OAuth Flow for Gmail Service\n")
    
    success, auth_url, state = test_oauth_authorization_url()
    
    if success:
        print(f"\n🎉 OAuth flow is ready!")
        print(f"📋 Next steps to complete authentication:")
        print(f"   1. Visit: {auth_url}")
        print(f"   2. Complete Google authentication")
        print(f"   3. Copy the authorization code from the callback")
        print(f"   4. Use test_oauth_callback.py with the code")
        
        # Create a callback test script
        callback_script = f'''#!/usr/bin/env python3
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
        print(f"❌ Error in OAuth callback: {{e}}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_oauth_callback.py YOUR_AUTHORIZATION_CODE")
        sys.exit(1)
    
    auth_code = sys.argv[1]
    success = test_callback(auth_code)
    sys.exit(0 if success else 1)
'''
        
        with open(backend_dir / "test_oauth_callback.py", "w") as f:
            f.write(callback_script)
        
        print(f"✅ Created test_oauth_callback.py for testing with auth code")
        
        return 0
    else:
        print(f"\n⚠️ OAuth flow test failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())