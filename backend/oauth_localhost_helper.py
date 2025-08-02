#!/usr/bin/env python3
"""
OAuth localhost helper for development
Provides multiple solutions for OAuth testing on localhost
"""

import sys
import os
import webbrowser
import re
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def extract_code_from_url():
    """Help user extract code from browser URL manually"""
    print("🔍 Manual Code Extraction Helper\n")
    
    print("📋 Steps to extract your authorization code:")
    print("1️⃣ Look at your browser's address bar where you got the error")
    print("2️⃣ The URL should look like:")
    print("   http://localhost:8000/gmail/callback?code=4/0AT2BQ-XXXXX...&scope=...")
    print("3️⃣ Copy ONLY the code part (everything after 'code=' and before '&')")
    print("4️⃣ Paste it below\n")
    
    print("💡 Example: If URL is")
    print("   http://localhost:8000/gmail/callback?code=4/0AT2BQ-abcd1234&scope=gmail...")
    print("   Then copy: 4/0AT2BQ-abcd1234\n")
    
    # Get the full URL from user
    full_url = input("Paste the full error page URL here: ").strip()
    
    if not full_url:
        print("❌ No URL provided")
        return None
    
    # Extract code using regex
    code_match = re.search(r'[?&]code=([^&]*)', full_url)
    
    if code_match:
        code = code_match.group(1)
        print(f"\n✅ Extracted code: {code}")
        return code
    else:
        print("❌ Could not find 'code' parameter in URL")
        print("💡 Make sure you copied the full URL from the error page")
        return None

def test_code_exchange(auth_code):
    """Test exchanging the authorization code for credentials"""
    try:
        from gmail_service import gmail_service
        
        print(f"\n🔄 Testing code exchange...")
        success = gmail_service.exchange_code_for_credentials(auth_code)
        
        if success:
            print("✅ OAuth authentication successful!")
            
            # Test Gmail API access
            try:
                profile = gmail_service.service.users().getProfile(userId='me').execute()
                print(f"✅ Gmail API working!")
                print(f"📧 Authenticated as: {profile.get('emailAddress')}")
                print(f"\n🎉 Gmail integration is now ready!")
                print("🔍 Run 'python test_gmail_2fa_integration.py' to test 2FA workflows")
                return True
            except Exception as e:
                print(f"⚠️  Gmail API test failed: {e}")
                return False
        else:
            print("❌ Failed to exchange code for credentials")
            print("💡 The code might be expired or invalid")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def provide_alternative_solutions():
    """Provide alternative OAuth testing solutions"""
    print("\n" + "="*60)
    print("🛠️  Alternative OAuth Testing Solutions")
    print("="*60)
    
    print("\n1️⃣ **ngrok** (Recommended for production-like testing)")
    print("   - Install: https://ngrok.com/download")
    print("   - Run: ./ngrok http 8000")
    print("   - Use the https URL as redirect URI")
    print("   - Pros: Secure, works with all OAuth providers")
    
    print("\n2️⃣ **lvh.me** (Quick but has security considerations)")
    print("   - Replace localhost:8000 with lvh.me:8000 in OAuth settings")
    print("   - No installation needed")
    print("   - ⚠️  Security note: Third-party domain could potentially collect tokens")
    
    print("\n3️⃣ **Start FastAPI Server** (Proper local development)")
    print("   - Run: python fastapi_app.py")
    print("   - Ensure server is running on localhost:8000")
    print("   - Redo OAuth flow")
    
    print("\n4️⃣ **Manual Code Extraction** (What we're doing now)")
    print("   - Extract code from browser URL")
    print("   - Use test_oauth_callback.py")

def main():
    """Main OAuth helper function"""
    print("🚀 OAuth Localhost Helper for Gmail Integration\n")
    
    print("It looks like you completed Google OAuth but got a localhost error.")
    print("This is normal - let's fix it!\n")
    
    # Try to extract code from URL
    code = extract_code_from_url()
    
    if code:
        # Test the code
        if test_code_exchange(code):
            print("\n🎯 Success! Your Gmail integration is now working.")
            return 0
        else:
            print("\n⚠️  Code exchange failed. Let's try alternative solutions.")
    
    # Provide alternatives
    provide_alternative_solutions()
    
    print("\n📋 Next Steps:")
    print("1. If you have the code, try: python test_oauth_callback.py YOUR_CODE")
    print("2. Or install ngrok for proper OAuth testing")
    print("3. Or restart the FastAPI server and redo OAuth")
    
    return 1

if __name__ == "__main__":
    sys.exit(main())