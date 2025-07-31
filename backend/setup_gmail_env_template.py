#!/usr/bin/env python3
"""
Gmail Service Account Environment Setup Template

This script helps you configure environment variables for Gmail API integration.
DO NOT commit the actual credentials to git - use this as a template only.

Setup Steps:
1. Go to Google Cloud Console
2. Create a service account with Gmail API access
3. Enable domain-wide delegation for the service account
4. Download the service account JSON key file
5. Set up the environment variables below

Environment Variables Required:
- GMAIL_SERVICE_ACCOUNT_JSON: The complete JSON content of your service account key
- GMAIL_TARGET_EMAIL: The email address to impersonate (your Gmail account)
"""

import os
import json

# Template for environment variables
ENV_TEMPLATE = """
# Gmail API Configuration
# Replace the placeholders with your actual values

# The Gmail account that will be used to check for 2FA codes
export GMAIL_TARGET_EMAIL="your-email@gmail.com"

# The complete JSON content of your service account key file
# Replace this with the actual JSON content (all on one line, escaped quotes)
export GMAIL_SERVICE_ACCOUNT_JSON='{"type": "service_account", "project_id": "your-project", "private_key_id": "...", "private_key": "...", "client_email": "...", "client_id": "...", "auth_uri": "...", "token_uri": "...", "auth_provider_x509_cert_url": "...", "client_x509_cert_url": "..."}'
"""

def setup_environment_variables():
    """Interactive setup for Gmail environment variables."""
    print("🔧 Gmail Service Account Setup")
    print("=" * 50)
    
    # Check if variables are already set
    existing_email = os.environ.get("GMAIL_TARGET_EMAIL")
    existing_json = os.environ.get("GMAIL_SERVICE_ACCOUNT_JSON")
    
    if existing_email and existing_json:
        print(f"✅ Gmail environment variables are already configured:")
        print(f"   Target Email: {existing_email}")
        print(f"   Service Account: {'[CONFIGURED]' if existing_json else '[NOT SET]'}")
        return True
    
    print("❌ Gmail environment variables not found.")
    print("\nTo set up Gmail integration:")
    print("1. Go to Google Cloud Console")
    print("2. Create a service account with Gmail API access")
    print("3. Enable domain-wide delegation")
    print("4. Download the JSON key file")
    print("5. Set environment variables in your deployment platform:")
    print()
    print(ENV_TEMPLATE)
    
    return False

def validate_service_account_json(json_str: str) -> bool:
    """Validate that the service account JSON is properly formatted."""
    try:
        data = json.loads(json_str)
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri'
        ]
        
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        if data.get('type') != 'service_account':
            print("❌ JSON is not a service account key")
            return False
        
        print("✅ Service account JSON appears valid")
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON format")
        return False

def test_gmail_service():
    """Test the Gmail service configuration."""
    try:
        # Import here to avoid circular imports
        from gmail_service import gmail_service
        
        if gmail_service.is_available():
            print("✅ Gmail service is properly configured")
            
            # Test basic functionality
            print("🔍 Testing Gmail search functionality...")
            codes = gmail_service.search_verification_codes("test", minutes_back=1)
            print(f"📧 Search completed (found {len(codes)} test results)")
            
            return True
        else:
            print("❌ Gmail service is not available")
            return False
            
    except Exception as e:
        print(f"❌ Gmail service test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Gmail Service Account Configuration Checker")
    print()
    
    # Check environment variables
    env_ok = setup_environment_variables()
    
    if env_ok:
        print("\n🧪 Testing Gmail service...")
        test_ok = test_gmail_service()
        
        if test_ok:
            print("\n🎉 Gmail integration is ready!")
        else:
            print("\n⚠️  Gmail integration needs attention.")
    else:
        print("\n⚠️  Please configure environment variables first.")
    
    print("\nFor Railway deployment:")
    print("1. Go to your Railway project settings")
    print("2. Add the environment variables in the Variables section")
    print("3. Redeploy your application")
    print()
    print("For local development:")
    print("1. Create a .env file with the variables")
    print("2. Use python-dotenv to load them")
    print("3. Run your FastAPI app")