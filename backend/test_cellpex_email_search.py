#!/usr/bin/env python3
"""
Test different Gmail search queries to find Cellpex 2FA emails
"""

import os
from datetime import datetime, timedelta
from gmail_service import gmail_service

def test_search_queries():
    """Test various search queries to find Cellpex emails"""
    
    if not gmail_service or not gmail_service.is_available():
        print("❌ Gmail service not available")
        return
    
    print("🔍 Testing Gmail search queries for Cellpex emails...")
    
    # Calculate time range
    now = datetime.utcnow()
    search_from = now - timedelta(hours=1)  # Search last hour
    after_date = search_from.strftime("%Y/%m/%d")
    
    # Test different query variations
    test_queries = [
        f'from:support@cellpex.com after:{after_date}',
        f'from:support@cellpex.com subject:cellpex after:{after_date}',
        f'from:support@cellpex.com subject:"access code" after:{after_date}',
        f'"Cellpex access code" after:{after_date}',
        f'subject:"Here is the Cellpex access code" after:{after_date}',
        f'cellpex after:{after_date}',
        f'from:cellpex.com after:{after_date}',
        f'(from:support@cellpex.com OR from:noreply@cellpex.com) after:{after_date}',
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n📧 Test Query {i+1}: {query}")
        
        try:
            # Search for messages
            results = gmail_service.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=5
            ).execute()
            
            messages = results.get('messages', [])
            print(f"✅ Found {len(messages)} messages")
            
            # Show details of found messages
            for j, msg in enumerate(messages[:3]):  # Show first 3
                msg_data = gmail_service.service.users().messages().get(
                    userId='me',
                    id=msg['id']
                ).execute()
                
                headers = msg_data['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                from_addr = next((h['value'] for h in headers if h['name'] == 'From'), 'No sender')
                
                print(f"   Message {j+1}:")
                print(f"     From: {from_addr}")
                print(f"     Subject: {subject[:60]}...")
                
                # Try to extract code
                snippet = msg_data.get('snippet', '')
                import re
                codes = re.findall(r'\b(\d{4,8})\b', snippet)
                if codes:
                    print(f"     Codes found in snippet: {codes}")
                
        except Exception as e:
            print(f"❌ Error with query: {e}")
    
    # Test the actual search_verification_codes method
    print("\n\n📧 Testing search_verification_codes method...")
    codes = gmail_service.search_verification_codes('cellpex', minutes_back=60)
    print(f"Found {len(codes)} verification codes")
    for code_info in codes:
        print(f"  - Code: {code_info.get('code')}, Subject: {code_info.get('subject')}")

if __name__ == "__main__":
    test_search_queries()