#!/usr/bin/env python3
"""
Standalone OAuth completion that doesn't require FastAPI server
"""

import sys
import os
import webbrowser
import json
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def complete_oauth_standalone():
    """Complete OAuth flow without requiring FastAPI server"""
    
    credentials_file = backend_dir / 'google_oauth_credentials.json'
    token_file = backend_dir / 'gmail_token.pickle'
    
    if not credentials_file.exists():
        print("❌ google_oauth_credentials.json not found")
        return False
    
    credentials = None
    
    # Check if we have existing valid credentials
    if token_file.exists():
        print("📁 Found existing OAuth token file...")
        with open(token_file, 'rb') as token:
            credentials = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print("🔄 Refreshing expired OAuth token...")
            try:
                credentials.refresh(Request())
                print("✅ Token refreshed successfully!")
            except Exception as e:
                print(f"❌ Token refresh failed: {e}")
                credentials = None
        
        if not credentials:
            print("🚀 Starting new OAuth flow...")
            print("📋 This will open your browser for Google authentication")
            
            # Create the flow using the client secrets file
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file, SCOPES)
            
            # Run the OAuth flow
            # This handles the entire OAuth flow including the callback
            print("🌐 Opening browser for authentication...")
            credentials = flow.run_local_server(port=8080)
            print("✅ Authentication completed!")
        
        # Save the credentials for the next run
        print("💾 Saving credentials...")
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    else:
        print("✅ Using existing valid credentials")
    
    return credentials

def test_gmail_access(credentials):
    """Test Gmail API access with the credentials"""
    try:
        from googleapiclient.discovery import build
        
        print("🔍 Testing Gmail API access...")
        service = build('gmail', 'v1', credentials=credentials)
        
        # Get user profile
        profile = service.users().getProfile(userId='me').execute()
        
        print("✅ Gmail API access successful!")
        print(f"📧 Email: {profile.get('emailAddress')}")
        print(f"📊 Total messages: {profile.get('messagesTotal')}")
        print(f"💾 History ID: {profile.get('historyId')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gmail API test failed: {e}")
        return False

def update_gmail_service():
    """Update the gmail_service module with new credentials"""
    try:
        print("🔄 Updating Gmail service module...")
        
        # Import and reinitialize
        from gmail_service import gmail_service
        gmail_service.force_reinitialize()
        
        if gmail_service.service:
            print("✅ Gmail service updated successfully!")
            return True
        else:
            print("⚠️  Gmail service needs manual restart")
            return False
            
    except Exception as e:
        print(f"❌ Error updating Gmail service: {e}")
        return False

def main():
    """Main standalone OAuth completion"""
    print("🚀 Standalone OAuth Completion for Gmail Integration\n")
    
    print("This will complete OAuth authentication without requiring FastAPI server.")
    print("It uses Google's built-in local server for the OAuth callback.\n")
    
    # Complete OAuth
    credentials = complete_oauth_standalone()
    
    if credentials:
        print("\n🎉 OAuth authentication successful!")
        
        # Test Gmail access
        if test_gmail_access(credentials):
            # Update gmail service
            update_gmail_service()
            
            print("\n✅ Gmail integration is now ready!")
            print("🔍 Next steps:")
            print("   1. Run: python test_gmail_2fa_integration.py")
            print("   2. Test 2FA workflows with actual platforms")
            print("   3. Deploy to Railway for production testing")
            
            return True
        else:
            print("\n⚠️  OAuth completed but Gmail API test failed")
            return False
    else:
        print("\n❌ OAuth authentication failed")
        print("💡 Make sure you complete the browser authentication")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)