# Railway Environment Variables Configuration

## Required Environment Variables for Production

### 1. Gmail OAuth Configuration
```env
# Gmail OAuth credentials (from Google Cloud Console)
GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REFRESH_TOKEN=your_refresh_token_here
```

### 2. OpenAI API Key
```env
# For AI-powered navigation and analysis
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Marketplace Credentials
```env
# Cellpex
CELLPEX_USERNAME=your_cellpex_username
CELLPEX_PASSWORD=your_cellpex_password

# GSM Exchange
GSMEXCHANGE_USERNAME=your_gsm_username
GSMEXCHANGE_PASSWORD=your_gsm_password

# HubX
HUBX_USERNAME=your_hubx_username
HUBX_PASSWORD=your_hubx_password

# Kardof
KARDOF_USERNAME=your_kardof_username
KARDOF_PASSWORD=your_kardof_password

# Handlot
HANDLOT_USERNAME=your_handlot_username
HANDLOT_PASSWORD=your_handlot_password
```

### 4. System Configuration (Auto-set by Railway)
```env
# These are automatically set by Railway, don't override
PORT=8080
RAILWAY_ENVIRONMENT=production

# Chrome paths (set by Dockerfile)
CHROME_BIN=/usr/bin/google-chrome-stable
CHROME_PATH=/usr/bin/google-chrome-stable
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
```

## How to Set in Railway

1. Go to your Railway project
2. Click on your service
3. Navigate to "Variables" tab
4. Add each variable one by one
5. Railway will automatically redeploy when you save

## Getting Gmail Refresh Token

Run locally:
```bash
cd backend
python get_refresh_token.py
```

Follow the OAuth flow and copy the refresh token to Railway.

## Security Notes

- Never commit these values to Git
- Use Railway's encrypted environment variables
- Rotate credentials regularly
- Monitor usage for suspicious activity