#!/usr/bin/env python3
"""
Get Gmail Refresh Token for Railway Deployment
Completes OAuth flow locally and extracts refresh token
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Gmail API scope
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_refresh_token():
    """Complete OAuth flow and get refresh token"""
    
    # Your OAuth credentials
    client_id = input("Enter your GMAIL_CLIENT_ID: ").strip()
    client_secret = input("Enter your GMAIL_CLIENT_SECRET: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Client ID and Secret are required!")
        return None
    
    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    print("🔐 Starting Gmail OAuth Flow...")
    print("=" * 50)
    
    try:
        # Create flow from client config
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        
        # Run local server for OAuth callback
        print("🌐 Opening browser for Google authentication...")
        print("✅ Sign in with your Google account")
        print("✅ Grant access to Gmail (read-only)")
        print("✅ The browser will show 'authentication flow completed'")
        
        creds = flow.run_local_server(port=8080, open_browser=True)
        
        if creds and creds.refresh_token:
            print("\n🎉 SUCCESS! OAuth completed successfully!")
            print("=" * 50)
            print("📋 COPY THIS REFRESH TOKEN TO RAILWAY:")
            print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
            print("=" * 50)
            print("\n📝 Next Steps:")
            print("1. Copy the GMAIL_REFRESH_TOKEN value above")
            print("2. Go to Railway Dashboard → Your Project → Variables")
            print("3. Add: GMAIL_REFRESH_TOKEN=[paste the token]")
            print("4. Click 'Deploy' to restart with new token")
            print("\n✅ After that, your Gmail OAuth will work on Railway!")
            
            return creds.refresh_token
        else:
            print("❌ No refresh token received")
            return None
            
    except Exception as e:
        print(f"❌ OAuth flow failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("- Make sure port 8080 is not in use")
        print("- Try running again")
        print("- Check your Google Cloud Console OAuth settings")
        return None

if __name__ == "__main__":
    print("🚀 Gmail OAuth Refresh Token Generator")
    print("🎯 This will get the refresh token for Railway deployment")
    print()
    
    refresh_token = get_refresh_token()
    
    if refresh_token:
        print(f"\n🔑 Refresh Token (copy this): {refresh_token}")
    else:
        print("\n❌ Failed to get refresh token. Please try again.")