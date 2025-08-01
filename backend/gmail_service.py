"""
Gmail API service for retrieving 2FA verification codes.
Uses service account with domain-wide delegation.
"""

import os
import json
import re
import base64
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from google.auth.exceptions import RefreshError
from google.auth import default
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailService:
    """Gmail service for reading emails and extracting 2FA codes."""
    
    def __init__(self):
        self.service = None
        self.target_email = os.environ.get("GMAIL_TARGET_EMAIL")  # The email account to impersonate
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Gmail service with domain-wide delegation."""
        try:
            # Get service account credentials from individual environment variables
            # This follows Google Cloud best practices instead of storing large JSON blobs
            credentials_info = {
                "type": os.environ.get("GOOGLE_SERVICE_ACCOUNT_TYPE", "service_account"),
                "project_id": os.environ.get("GOOGLE_SERVICE_ACCOUNT_PROJECT_ID"),
                "private_key_id": os.environ.get("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY_ID"),
                "private_key": os.environ.get("GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY"),
                "client_email": os.environ.get("GOOGLE_SERVICE_ACCOUNT_CLIENT_EMAIL"),
                "client_id": os.environ.get("GOOGLE_SERVICE_ACCOUNT_CLIENT_ID"),
                "auth_uri": os.environ.get("GOOGLE_SERVICE_ACCOUNT_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": os.environ.get("GOOGLE_SERVICE_ACCOUNT_TOKEN_URI", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": os.environ.get("GOOGLE_SERVICE_ACCOUNT_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"),
                "client_x509_cert_url": os.environ.get("GOOGLE_SERVICE_ACCOUNT_CLIENT_CERT_URL"),
                "universe_domain": os.environ.get("GOOGLE_SERVICE_ACCOUNT_UNIVERSE_DOMAIN", "googleapis.com")
            }
            
            # Check if required fields are present
            required_fields = ["project_id", "private_key", "client_email", "client_id"]
            missing_fields = [field for field in required_fields if not credentials_info.get(field)]
            
            if missing_fields:
                print(f"❌ Missing required Google service account environment variables:")
                for field in missing_fields:
                    var_name = f"GOOGLE_SERVICE_ACCOUNT_{field.upper().replace('_', '_')}"
                    print(f"   - {var_name}")
                return
            
            if not self.target_email:
                print("❌ GMAIL_TARGET_EMAIL environment variable not set")
                return
            
            # Define the scope for Gmail API
            scopes = ['https://www.googleapis.com/auth/gmail.readonly']
            
            # Create credentials with domain-wide delegation
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=scopes
            )
            
            # Delegate to the target email account
            delegated_credentials = credentials.with_subject(self.target_email)
            
            # Build the Gmail service
            self.service = build('gmail', 'v1', credentials=delegated_credentials)
            print(f"✅ Gmail service initialized for {self.target_email}")
            
        except Exception as e:
            print(f"❌ Failed to initialize Gmail service: {e}")
            self.service = None
    
    def search_verification_codes(self, platform: str, minutes_back: int = 10) -> List[Dict]:
        """
        Search for recent emails containing verification codes from a specific platform.
        
        Args:
            platform: Platform name to search for (e.g., 'gsmexchange', 'cellpex')
            minutes_back: How many minutes back to search
            
        Returns:
            List of verification code details
        """
        if not self.service:
            return []
        
        try:
            # Calculate time range
            now = datetime.utcnow()
            search_from = now - timedelta(minutes=minutes_back)
            
            # Format date for Gmail search (YYYY/MM/DD format)
            after_date = search_from.strftime("%Y/%m/%d")
            
            # Platform-specific search queries
            platform_queries = {
                'gsmexchange': 'from:noreply@gsmexchange.com OR from:support@gsmexchange.com OR subject:"GSM Exchange" OR subject:"verification code"',
                'cellpex': 'from:noreply@cellpex.com OR from:support@cellpex.com OR subject:"Cellpex" OR subject:"verification code"',
                'kardof': 'from:noreply@kardof.com OR from:support@kardof.com OR subject:"Kardof" OR subject:"verification code"',
                'hubx': 'from:noreply@hubx.com OR from:support@hubx.com OR subject:"HubX" OR subject:"verification code"',
                'handlot': 'from:noreply@handlot.com OR from:support@handlot.com OR subject:"Handlot" OR subject:"verification code"'
            }
            
            # Build search query
            base_query = platform_queries.get(platform.lower(), f'subject:"{platform}" OR subject:"verification code"')
            query = f'({base_query}) after:{after_date} (verification OR code OR authenticate OR login OR security)'
            
            print(f"🔍 Searching Gmail with query: {query}")
            
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            verification_codes = []
            
            for message in messages:
                code_info = self._extract_verification_code(message['id'])
                if code_info:
                    verification_codes.append(code_info)
            
            return verification_codes
            
        except HttpError as e:
            print(f"❌ Gmail API error: {e}")
            return []
        except Exception as e:
            print(f"❌ Error searching for verification codes: {e}")
            return []
    
    def _extract_verification_code(self, message_id: str) -> Optional[Dict]:
        """Extract verification code from a specific email message."""
        try:
            # Get the full message
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract message details
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Get message body
            body = self._get_message_body(message['payload'])
            
            if body:
                # Look for verification codes in the text
                code = self._find_verification_code_in_text(body)
                if code:
                    return {
                        'code': code,
                        'subject': subject,
                        'sender': sender,
                        'date': date,
                        'message_id': message_id
                    }
            
            return None
            
        except HttpError as e:
            print(f"❌ Error getting message {message_id}: {e}")
            return None
    
    def _get_message_body(self, payload) -> str:
        """Extract the text body from email payload."""
        body_text = ""
        
        if 'parts' in payload:
            # Multi-part message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body_text += base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body_text:
                    # Fallback to HTML if no plain text
                    data = part['body'].get('data', '')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            # Single part message
            if payload['mimeType'] in ['text/plain', 'text/html']:
                data = payload['body'].get('data', '')
                if data:
                    body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        return body_text
    
    def _find_verification_code_in_text(self, text: str) -> Optional[str]:
        """Find verification code patterns in email text."""
        # Common verification code patterns
        patterns = [
            r'verification code[:\s]*([A-Z0-9]{4,8})',  # "verification code: ABCD1234"
            r'code[:\s]*([A-Z0-9]{4,8})',              # "code: 123456"
            r'authenticate[:\s]*([A-Z0-9]{4,8})',      # "authenticate: ABC123"
            r'login code[:\s]*([A-Z0-9]{4,8})',        # "login code: 654321"
            r'security code[:\s]*([A-Z0-9]{4,8})',     # "security code: XYZ789"
            r'OTP[:\s]*([A-Z0-9]{4,8})',               # "OTP: 123456"
            r'PIN[:\s]*([A-Z0-9]{4,8})',               # "PIN: 9876"
            r'([A-Z0-9]{6})',                          # 6-digit code standalone
            r'([A-Z0-9]{4})',                          # 4-digit code standalone
            r'([0-9]{6})',                             # 6-digit number
            r'([0-9]{4})',                             # 4-digit number
        ]
        
        # Clean up the text
        text = text.upper().replace('\n', ' ').replace('\r', ' ')
        
        # Try each pattern
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return the first match that looks like a verification code
                for match in matches:
                    # Filter out common false positives
                    if match not in ['1234', '0000', '9999', 'ABCD', 'TEST']:
                        return match
        
        return None
    
    def get_latest_verification_code(self, platform: str) -> Optional[str]:
        """
        Get the most recent verification code for a platform.
        
        Args:
            platform: Platform name
            
        Returns:
            The verification code string or None if not found
        """
        codes = self.search_verification_codes(platform, minutes_back=5)
        if codes:
            # Return the most recent code
            return codes[0]['code']
        return None
    
    def is_available(self) -> bool:
        """Check if Gmail service is properly initialized and available."""
        return self.service is not None


# Global Gmail service instance
gmail_service = GmailService()