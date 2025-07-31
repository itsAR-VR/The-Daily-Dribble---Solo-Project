#!/usr/bin/env python3
"""
Helper script to convert Google Service Account JSON to Railway-compatible format.
Use this to format your service account JSON for environment variables.
"""

import json
import sys

def format_json_for_railway(json_file_path):
    """
    Convert a service account JSON file to Railway environment variable format.
    """
    try:
        # Read the JSON file
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to single-line string with escaped characters
        formatted_json = json.dumps(data, separators=(',', ':'))
        
        print("=" * 60)
        print("🔧 GMAIL SERVICE ACCOUNT JSON FORMATTER")
        print("=" * 60)
        print()
        print("✅ Successfully formatted your service account JSON!")
        print()
        print("📋 Copy this value for GMAIL_SERVICE_ACCOUNT_JSON in Railway:")
        print("-" * 60)
        print(formatted_json)
        print("-" * 60)
        print()
        print("📌 Steps to update in Railway:")
        print("1. Go to your Railway project dashboard")
        print("2. Navigate to Variables section")
        print("3. Edit GMAIL_SERVICE_ACCOUNT_JSON")
        print("4. Paste the formatted JSON above")
        print("5. Save and redeploy")
        print()
        
        # Validate the JSON has required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email', 'client_id']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"⚠️  WARNING: Missing required fields: {missing_fields}")
        else:
            print("✅ All required fields present")
        
        print()
        print("🔍 Validation:")
        print(f"   Service Account Email: {data.get('client_email', 'NOT FOUND')}")
        print(f"   Project ID: {data.get('project_id', 'NOT FOUND')}")
        print(f"   Type: {data.get('type', 'NOT FOUND')}")
        
        return formatted_json
        
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file_path}' not found")
        print("Please provide the path to your service account JSON file")
        return None
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in file '{json_file_path}'")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def format_json_from_string(json_string):
    """
    Format a JSON string for Railway environment variables.
    """
    try:
        # Parse and reformat
        data = json.loads(json_string)
        formatted_json = json.dumps(data, separators=(',', ':'))
        
        print("✅ JSON formatted successfully!")
        print("📋 Railway environment variable value:")
        print("-" * 60)
        print(formatted_json)
        print("-" * 60)
        
        return formatted_json
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Google Service Account JSON Formatter for Railway")
    print()
    
    if len(sys.argv) > 1:
        # File path provided
        json_file = sys.argv[1]
        format_json_for_railway(json_file)
    else:
        print("Usage Options:")
        print()
        print("1. Format from file:")
        print("   python fix_json_format.py path/to/service-account.json")
        print()
        print("2. Manual formatting:")
        print("   - Open your service account JSON file")
        print("   - Copy the entire content")
        print("   - Paste it in Railway as a single line")
        print()
        print("Example correct format:")
        print('{"type":"service_account","project_id":"your-project",...}')
        print()
        print("💡 Tip: Make sure there are no line breaks in the Railway variable!")