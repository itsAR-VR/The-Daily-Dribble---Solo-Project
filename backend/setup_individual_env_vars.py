#!/usr/bin/env python3
"""
Google Service Account Environment Variables Generator

This script converts a Google Cloud service account JSON file into individual
environment variables following Google Cloud best practices.

Usage:
    python setup_individual_env_vars.py /path/to/service-account.json

This follows the best practices documented at:
https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys

The approach of using individual environment variables is more secure and 
better supported by platforms like Railway compared to large JSON blobs.
"""

import json
import sys
from pathlib import Path

def generate_env_vars_from_json(json_file_path):
    """
    Convert service account JSON to individual environment variables.
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        print("=" * 80)
        print("🔧 GOOGLE SERVICE ACCOUNT ENVIRONMENT VARIABLES")
        print("=" * 80)
        print()
        print("✅ Successfully parsed your service account JSON!")
        print()
        print("📋 Add these environment variables to Railway:")
        print("=" * 50)
        print()
        
        # Required variables
        required_vars = [
            ("GOOGLE_SERVICE_ACCOUNT_TYPE", data.get("type", "service_account")),
            ("GOOGLE_SERVICE_ACCOUNT_PROJECT_ID", data.get("project_id")),
            ("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID", data.get("private_key_id")),
            ("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY", data.get("private_key")),
            ("GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL", data.get("client_email")),
            ("GOOGLE_SERVICE_ACCOUNT_CLIENT_ID", data.get("client_id")),
        ]
        
        # Optional variables with defaults
        optional_vars = [
            ("GOOGLE_SERVICE_ACCOUNT_AUTH_URI", data.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")),
            ("GOOGLE_SERVICE_ACCOUNT_TOKEN_URI", data.get("token_uri", "https://oauth2.googleapis.com/token")),
            ("GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_CERT_URL", data.get("auth_provider_x509_cert_url", "https://www.googleapis.com/oauth2/v1/certs")),
            ("GOOGLE_SERVICE_ACCOUNT_CLIENT_CERT_URL", data.get("client_x509_cert_url")),
            ("GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN", data.get("universe_domain", "googleapis.com")),
        ]
        
        print("🔑 REQUIRED VARIABLES:")
        print("-" * 30)
        for var_name, value in required_vars:
            if value:
                if "PRIVATE_KEY" in var_name:
                    # Show truncated private key for security
                    display_value = f"{value[:50]}..." if len(value) > 50 else value
                    print(f"{var_name}={display_value}")
                else:
                    print(f"{var_name}={value}")
            else:
                print(f"❌ {var_name}=MISSING")
        
        print()
        print("⚙️  OPTIONAL VARIABLES (with defaults):")
        print("-" * 40)
        for var_name, value in optional_vars:
            if value:
                print(f"{var_name}={value}")
        
        print()
        print("=" * 80)
        print("🚀 RAILWAY SETUP INSTRUCTIONS:")
        print("=" * 80)
        print()
        print("1. Go to your Railway project dashboard")
        print("2. Click on your service")
        print("3. Go to the Variables tab")
        print("4. Add each variable above (copy the name and value exactly)")
        print("5. Don't forget to also set: GMAIL_TARGET_EMAIL=your-email@gmail.com")
        print()
        print("💡 BENEFITS OF THIS APPROACH:")
        print("   ✅ Follows Google Cloud security best practices")
        print("   ✅ Easier to manage individual variables")
        print("   ✅ Better Railway platform support") 
        print("   ✅ Can use Railway's variable sealing for sensitive data")
        print("   ✅ No JSON parsing issues or size limits")
        print()
        print("📚 References:")
        print("   - https://cloud.google.com/iam/docs/best-practices-for-managing-service-account-keys")
        print("   - https://docs.railway.app/guides/variables")
        print()
        
        # Validation
        missing_required = [var for var, val in required_vars if not val]
        if missing_required:
            print("❌ WARNING: Missing required fields in JSON:")
            for var in missing_required:
                print(f"   - {var}")
            print()
        else:
            print("✅ All required fields present!")
            print()
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file_path}' not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        print("Usage: python setup_individual_env_vars.py /path/to/service-account.json")
        print()
        print("This script converts a Google Cloud service account JSON file")
        print("into individual environment variables following best practices.")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    if not Path(json_file_path).exists():
        print(f"❌ Error: File '{json_file_path}' does not exist.")
        sys.exit(1)
    
    success = generate_env_vars_from_json(json_file_path)
    
    if success:
        print("🎉 Setup complete! Use the variables above in Railway.")
    else:
        print("❌ Setup failed. Please check your JSON file.")
        sys.exit(1)

if __name__ == "__main__":
    main()