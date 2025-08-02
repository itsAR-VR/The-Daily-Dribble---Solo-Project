#!/usr/bin/env python3
"""
Test script to verify OAuth setup for Gmail service.
"""

import os
import json
import sys
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_credentials_file():
    """Test if OAuth credentials file exists and is valid."""
    print("🔍 Testing OAuth credentials file...")
    
    credentials_file = backend_dir / "google_oauth_credentials.json"
    
    if not credentials_file.exists():
        print(f"❌ Credentials file not found: {credentials_file}")
        return False
    
    try:
        with open(credentials_file, 'r') as f:
            creds_data = json.load(f)
        
        installed = creds_data.get("installed", {})
        required_fields = ["client_id", "client_secret", "project_id", "auth_uri", "token_uri"]
        missing_fields = [field for field in required_fields if not installed.get(field)]
        
        if missing_fields:
            print(f"❌ Missing required fields in credentials: {missing_fields}")
            return False
        
        print("✅ Credentials file is valid")
        print(f"   📁 Project ID: {installed.get('project_id')}")
        print(f"   🔑 Client ID: {installed.get('client_id')[:20]}...")
        print(f"   🔒 Has Client Secret: {'Yes' if installed.get('client_secret') else 'No'}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in credentials file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        return False

def test_gmail_service_import():
    """Test if Gmail service can be imported."""
    print("\n🔍 Testing Gmail service import...")
    
    try:
        from gmail_service import GmailService
        print("✅ Gmail service imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import Gmail service: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing Gmail service: {e}")
        return False

def test_gmail_service_initialization():
    """Test Gmail service initialization."""
    print("\n🔍 Testing Gmail service initialization...")
    
    try:
        from gmail_service import GmailService
        
        # Create service instance
        service = GmailService()
        
        print(f"✅ Gmail service created")
        print(f"   📁 Credentials file path: {service.credentials_file}")
        print(f"   🎯 Token file path: {service.token_file}")
        print(f"   🔐 Has credentials: {'Yes' if service.credentials else 'No'}")
        print(f"   ✅ Service initialized: {'Yes' if service.service else 'No'}")
        
        if not service.credentials:
            print("   ⚠️  No OAuth credentials found - authentication required")
            print("   🔗 Use /gmail/auth endpoint to start OAuth flow")
        elif not service.credentials.valid:
            print("   ⚠️  OAuth credentials expired - reauthentication required")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing Gmail service: {e}")
        return False

def test_oauth_flow():
    """Test OAuth flow creation."""
    print("\n🔍 Testing OAuth flow creation...")
    
    try:
        from gmail_service import GmailService
        
        service = GmailService()
        
        # Test getting OAuth flow
        flow = service.get_oauth_flow()
        print("✅ OAuth flow created successfully")
        
        # Test getting authorization URL
        auth_url, state = service.get_authorization_url()
        print("✅ Authorization URL generated successfully")
        print(f"   🔗 State parameter: {state[:20]}...")
        print(f"   🌐 Auth URL domain: {auth_url.split('/')[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing OAuth flow: {e}")
        return False

def test_fastapi_imports():
    """Test if FastAPI app can import Gmail service."""
    print("\n🔍 Testing FastAPI app imports...")
    
    try:
        # Try importing the main components
        import fastapi_app
        print("✅ FastAPI app imported successfully")
        
        # Check if Gmail service is available in the app
        if hasattr(fastapi_app, 'gmail_service') and fastapi_app.gmail_service:
            print("✅ Gmail service available in FastAPI app")
            print(f"   🏁 Gmail available flag: {fastapi_app.GMAIL_AVAILABLE}")
        else:
            print("⚠️  Gmail service not available in FastAPI app")
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing FastAPI app: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting OAuth setup tests for Gmail service\n")
    
    tests = [
        test_credentials_file,
        test_gmail_service_import,
        test_gmail_service_initialization,
        test_oauth_flow,
        test_fastapi_imports
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")
    print(f"   📈 Success Rate: {sum(results)/len(results)*100:.1f}%")
    
    if all(results):
        print(f"\n🎉 All tests passed! OAuth setup is ready.")
        print(f"📋 Next steps:")
        print(f"   1. Start your FastAPI server: python fastapi_app.py")
        print(f"   2. Visit http://localhost:8000/gmail/auth to start OAuth flow")
        print(f"   3. Complete Google authentication")
        print(f"   4. Test Gmail functionality")
    else:
        print(f"\n⚠️  Some tests failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())