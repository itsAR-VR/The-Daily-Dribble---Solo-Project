"""
Gmail API service for retrieving 2FA verification codes.
Uses OAuth authentication flow.
"""

import os
import json
import re
import base64
import pickle
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class GmailService:
    """Gmail service for reading emails and extracting 2FA codes."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.credentials_file = os.path.join(os.path.dirname(__file__), 'google_oauth_credentials.json')
        self.token_file = os.path.join(os.path.dirname(__file__), 'gmail_token.pickle')
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly']
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Gmail service with OAuth authentication."""
        print("🔄 Initializing Gmail service with OAuth...")
        try:
            # First, check for refresh token in environment variable
            refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")
            if refresh_token and not os.path.exists(self.token_file):
                print("🔐 Found GMAIL_REFRESH_TOKEN in environment, creating credentials...")
                # Create credentials from refresh token
                from google.oauth2.credentials import Credentials
                self.credentials = Credentials(
                    token=None,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=os.getenv("GMAIL_CLIENT_ID"),
                    client_secret=os.getenv("GMAIL_CLIENT_SECRET"),
                    scopes=self.scopes
                )
                # Save the credentials for future use
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
                print("✅ OAuth credentials created from refresh token")
            
            # Check if we have existing credentials
            if os.path.exists(self.token_file):
                print("📁 Loading existing OAuth token...")
                with open(self.token_file, 'rb') as token:
                    self.credentials = pickle.load(token)
            
            # If there are no (valid) credentials available, let the user log in.
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    print("🔄 Refreshing expired OAuth token...")
                    self.credentials.refresh(Request())
                else:
                    print("❌ No valid OAuth credentials found. User needs to authenticate.")
                    print("🔗 Please use the /gmail/auth endpoint to start OAuth flow")
                    return
                
                # Save the credentials for the next run
                with open(self.token_file, 'wb') as token:
                    pickle.dump(self.credentials, token)
            
            print("✅ OAuth credentials loaded successfully")
            
            # Build the Gmail service
            print("🚀 Building Gmail API service...")
            self.service = build('gmail', 'v1', credentials=self.credentials)
            print("✅ Gmail service initialized successfully with OAuth")
            
        except Exception as e:
            print(f"❌ Failed to initialize Gmail service: {e}")
            print(f"🔍 Error type: {type(e).__name__}")
            if hasattr(e, 'status'):
                print(f"📊 Status code: {e.status}")
            if hasattr(e, 'details'):
                print(f"📝 Details: {e.details}")
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
            
            # Platform-specific search queries - simplified for better results
            platform_queries = {
                'gsmexchange': 'from:gsmexchange.com',
                'cellpex': 'from:cellpex.com',
                'kardof': 'from:kardof.com',
                'hubx': 'from:hubx.com',
                'handlot': 'from:handlot.com'
            }
            
            # Build search query - much simpler to catch more emails
            base_query = platform_queries.get(platform.lower(), f'from:{platform}.com')
            query = f'{base_query} after:{after_date}'
            
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
        # If service is not available, try to reinitialize
        if self.service is None:
            print("🔄 Gmail service not available, attempting reinitialization...")
            self._initialize_service()
        return self.service is not None
    
    def force_reinitialize(self) -> bool:
        """Force reinitialize the Gmail service with current OAuth credentials."""
        print("🔄 Force reinitializing Gmail service...")
        self.service = None
        self.credentials = None
        self._initialize_service()
        return self.service is not None
    
    def get_oauth_flow(self, redirect_uri: str = "http://localhost:8000/gmail/callback"):
        """Create and return OAuth flow for authentication."""
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(f"OAuth credentials file not found: {self.credentials_file}")
        
        flow = Flow.from_client_secrets_file(
            self.credentials_file, 
            scopes=self.scopes,
            redirect_uri=redirect_uri
        )
        return flow
    
    def get_authorization_url(self, redirect_uri: str = "http://localhost:8000/gmail/callback"):
        """Get the authorization URL for OAuth flow."""
        flow = self.get_oauth_flow(redirect_uri)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        return authorization_url, state
    
    def exchange_code_for_credentials(self, authorization_code: str, redirect_uri: str = "http://localhost:8000/gmail/callback"):
        """Exchange authorization code for credentials."""
        flow = self.get_oauth_flow(redirect_uri)
        flow.fetch_token(code=authorization_code)
        
        # Save credentials
        self.credentials = flow.credentials
        with open(self.token_file, 'wb') as token:
            pickle.dump(self.credentials, token)
        
        # Initialize service with new credentials
        self.service = build('gmail', 'v1', credentials=self.credentials)
        return True
    
    def revoke_credentials(self):
        """Revoke OAuth credentials and delete token file."""
        if self.credentials and hasattr(self.credentials, 'token'):
            try:
                self.credentials.revoke(Request())
            except Exception as e:
                print(f"Warning: Failed to revoke credentials: {e}")
        
        # Delete token file
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
        
        self.credentials = None
        self.service = None
        return True


# Global Gmail service instance
gmail_service = GmailService()