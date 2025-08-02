# Gmail OAuth Setup Guide

The Gmail service has been migrated from service account authentication to OAuth for better security and easier setup.

## Overview

The system now uses OAuth 2.0 authentication to access Gmail for 2FA code retrieval. This is more secure and doesn't require complex service account setup.

## Files Created

- `google_oauth_credentials.json` - OAuth client credentials (auto-created with your provided credentials)
- `gmail_token.pickle` - OAuth tokens (created after first authentication)
- `test_oauth_setup.py` - Test script to verify setup

## Quick Start

1. **Start the server:**
   ```bash
   python fastapi_app.py
   ```

2. **Check status:**
   ```bash
   curl http://localhost:8000/gmail/status
   ```

3. **Start OAuth flow:**
   Visit: http://localhost:8000/gmail/auth

4. **Complete authentication:**
   - Click the authorization URL returned by the `/gmail/auth` endpoint
   - Sign in with your Google account
   - Grant access to Gmail
   - You'll be redirected to the callback URL

5. **Verify authentication:**
   ```bash
   curl http://localhost:8000/gmail/status
   ```

## API Endpoints

- `GET /gmail/status` - Check authentication status
- `GET /gmail/auth` - Start OAuth flow
- `GET /gmail/callback` - OAuth callback (automatic)
- `POST /gmail/revoke` - Revoke authentication
- `POST /gmail/test-search` - Test Gmail search functionality

## Configuration

The OAuth credentials are configured with:
- **Client ID:** 826416737074-e371n0ft5vs6pnuglq88eqisjigt685o.apps.googleusercontent.com
- **Project ID:** kinetic-silicon-467602-q5
- **Redirect URI:** http://localhost:8000/gmail/callback

## Security

- OAuth tokens are stored locally in `gmail_token.pickle`
- Credentials files are excluded from git via `.gitignore`
- Tokens automatically refresh when expired

## Troubleshooting

1. **"No OAuth credentials found"** - Normal on first run, use `/gmail/auth` to authenticate
2. **"Credentials expired"** - Use `/gmail/auth` to reauthenticate
3. **"Service not available"** - Check that `google_oauth_credentials.json` exists

## Testing

Run the test script to verify setup:
```bash
python test_oauth_setup.py
```

## Migration from Service Account

The old service account environment variables are no longer needed:
- ❌ `GOOGLE_SERVICE_ACCOUNT_*` variables (removed)
- ❌ `GMAIL_TARGET_EMAIL` (removed)
- ✅ OAuth credentials file (new approach)

This new approach is simpler and more secure!