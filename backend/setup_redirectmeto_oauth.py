#!/usr/bin/env python3
"""
Setup OAuth using RedirectMeTo service for easy localhost testing
Based on: https://www.nango.dev/blog/oauth-redirects-on-localhost-with-https
"""

import sys
import os
import webbrowser
import json
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def update_oauth_credentials_for_redirectmeto():
    """Update OAuth credentials to use RedirectMeTo service"""
    
    credentials_file = backend_dir / 'google_oauth_credentials.json'
    
    if not credentials_file.exists():
        print("❌ google_oauth_credentials.json not found")
        return False
    
    try:
        # Read current credentials
        with open(credentials_file, 'r') as f:
            credentials = json.load(f)
        
        # Update redirect URI to use RedirectMeTo
        new_redirect_uri = "https://redirectmeto.com/http://localhost:8000/gmail/callback"
        credentials['web']['redirect_uris'] = [new_redirect_uri]
        
        # Save updated credentials
        with open(credentials_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print("✅ Updated OAuth credentials to use RedirectMeTo")
        print(f"📝 New redirect URI: {new_redirect_uri}")
        print("\n⚠️  IMPORTANT: You need to update this in Google Cloud Console too!")
        print("   Go to: https://console.cloud.google.com/apis/credentials")
        print("   Edit your OAuth 2.0 Client ID")
        print(f"   Set Authorized redirect URI to: {new_redirect_uri}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating credentials: {e}")
        return False

def test_redirectmeto_oauth():
    """Test OAuth flow with RedirectMeTo"""
    try:
        from gmail_service import gmail_service
        
        # Force reinitialize to pick up new redirect URI
        gmail_service.force_reinitialize()
        
        # Generate auth URL with new redirect URI
        auth_url, state = gmail_service.get_authorization_url(
            redirect_uri="https://redirectmeto.com/http://localhost:8000/gmail/callback"
        )
        
        print("\n🚀 Testing OAuth with RedirectMeTo...")
        print("📋 Steps:")
        print("1️⃣ Click the authorization URL")
        print("2️⃣ Complete Google authentication")
        print("3️⃣ You'll be redirected through RedirectMeTo back to localhost")
        print("4️⃣ Copy the 'code' parameter from the final URL")
        print("5️⃣ Use that code with test_oauth_callback.py")
        
        print(f"\n🔗 Authorization URL:\n{auth_url}")
        
        # Try to open browser
        try:
            webbrowser.open(auth_url)
            print("\n✅ Browser opened with authorization URL")
        except:
            print("\n⚠️  Could not open browser automatically")
        
        print(f"\n🎯 State parameter: {state}")
        print("\n💡 Pro tip: RedirectMeTo will automatically forward you to localhost!")
        
        return auth_url, state
        
    except Exception as e:
        print(f"❌ Error testing OAuth: {e}")
        return None, None

def main():
    """Setup and test OAuth with RedirectMeTo"""
    print("🚀 OAuth Setup with RedirectMeTo Service\n")
    
    print("This uses the RedirectMeTo service mentioned in:")
    print("- https://www.nango.dev/blog/oauth-redirects-on-localhost-with-https")  
    print("- https://codewithsusan.com/notes/google-api-oauth-redirect-local-development-domain")
    print()
    
    # Update credentials file
    if not update_oauth_credentials_for_redirectmeto():
        return 1
    
    print("\n" + "="*60)
    print("⚠️  MANUAL STEP REQUIRED")
    print("="*60)
    print("Before continuing, you MUST update Google Cloud Console:")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Click on your OAuth 2.0 Client ID")
    print("3. In 'Authorized redirect URIs', add:")
    print("   https://redirectmeto.com/http://localhost:8000/gmail/callback")
    print("4. Save the changes")
    print()
    
    input("Press Enter after updating Google Cloud Console...")
    
    # Test OAuth flow
    auth_url, state = test_redirectmeto_oauth()
    
    if auth_url:
        print("\n🎉 OAuth setup complete!")
        print("📋 Next: Complete the authentication in your browser")
        return 0
    else:
        print("\n❌ OAuth setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())