#!/usr/bin/env python3
"""
Test script to debug environment variable issues.
"""

import os
import json

def test_environment_variables():
    """Test if Gmail environment variables are properly set."""
    print("🔍 Testing Gmail Environment Variables")
    print("=" * 50)
    
    # Check GMAIL_TARGET_EMAIL
    target_email = os.environ.get("GMAIL_TARGET_EMAIL")
    print(f"📧 GMAIL_TARGET_EMAIL: {target_email if target_email else '❌ NOT SET'}")
    
    # Check GMAIL_SERVICE_ACCOUNT_JSON
    service_account_json = os.environ.get("GMAIL_SERVICE_ACCOUNT_JSON")
    print(f"🔑 GMAIL_SERVICE_ACCOUNT_JSON: {'✅ SET' if service_account_json else '❌ NOT SET'}")
    
    if service_account_json:
        try:
            # Try to parse the JSON
            credentials_data = json.loads(service_account_json)
            print("✅ JSON is valid")
            
            # Check required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email', 'client_id']
            for field in required_fields:
                if field in credentials_data:
                    if field == 'private_key':
                        print(f"   {field}: ✅ Present (length: {len(credentials_data[field])})")
                    else:
                        print(f"   {field}: ✅ {credentials_data[field]}")
                else:
                    print(f"   {field}: ❌ MISSING")
            
            # Validate service account type
            if credentials_data.get('type') == 'service_account':
                print("✅ Correct service account type")
            else:
                print(f"❌ Invalid type: {credentials_data.get('type')}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("🔧 Check JSON formatting - should be single line with escaped quotes")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🛠️  Troubleshooting Tips:")
    if not target_email:
        print("- Set GMAIL_TARGET_EMAIL to your Gmail address")
    if not service_account_json:
        print("- Set GMAIL_SERVICE_ACCOUNT_JSON with your service account JSON")
    elif service_account_json:
        try:
            json.loads(service_account_json)
        except:
            print("- Fix JSON formatting (use fix_json_format.py)")
    
    print("\n📋 Next Steps:")
    print("1. Fix any missing environment variables")
    print("2. Redeploy your Railway application")
    print("3. Test with: curl /gmail/status")

if __name__ == "__main__":
    test_environment_variables()