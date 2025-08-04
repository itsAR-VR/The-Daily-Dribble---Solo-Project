# 🚂 Railway Deployment Guide for Anti-Hallucination Bot

## Overview
This guide will help you deploy the enhanced marketplace listing bot with anti-hallucination capabilities to Railway.

## Prerequisites
- Railway account ([sign up here](https://railway.app))
- GitHub repository with the code pushed
- All marketplace credentials ready

## Step-by-Step Deployment

### 1. Create a New Railway Project

1. Visit [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account if not already connected
5. Select your repository: `The-Daily-Dribble---Solo-Project`

### 2. Configure Environment Variables

Railway will need all your marketplace credentials and API keys. Click on your service and go to the **Variables** tab, then add:

#### Gmail OAuth Credentials
```
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token
```

#### OpenAI API Key
```
OPENAI_API_KEY=your_openai_api_key
```

#### Marketplace Credentials
```
# Cellpex
CELLPEX_USERNAME=your_cellpex_username
CELLPEX_PASSWORD=your_cellpex_password

# GSM Exchange
GSM_EXCHANGE_USERNAME=your_gsm_username
GSM_EXCHANGE_PASSWORD=your_gsm_password

# Kardof
KARDOF_USERNAME=your_kardof_username
KARDOF_PASSWORD=your_kardof_password

# HubX
HUBX_USERNAME=your_hubx_username
HUBX_PASSWORD=your_hubx_password

# Handlot
HANDLOT_USERNAME=your_handlot_username
HANDLOT_PASSWORD=your_handlot_password
```

#### Chrome Configuration (Railway handles this automatically)
```
CHROME_BIN=/usr/bin/chromium-browser
CHROME_PATH=/usr/bin/chromium-browser
```

### 3. Configure Build Settings

1. In your service settings, set:
   - **Root Directory**: `/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT`

### 4. Deploy the Application

1. After adding all variables, click **"Deploy"**
2. Railway will:
   - Build your application
   - Install all dependencies
   - Start the FastAPI server

### 5. Generate a Public URL

1. Go to your service's **Settings** tab
2. Under **Public Networking**, click **"Generate Domain"**
3. Railway will provide a URL like: `your-app.up.railway.app`

### 6. Test Your Deployment

Once deployed, test the anti-hallucination bot:

```bash
# Test Cellpex listing with anti-hallucination
curl -X POST https://your-app.up.railway.app/test/enhanced-2fa/cellpex \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Apple > iPhone",
    "brand": "Apple",
    "model": "iPhone 14 Pro",
    "available_quantity": 5,
    "price": 899.99,
    "comments": "Brand new, sealed box",
    "remarks": "Ships within 24 hours"
  }'
```

### 7. Monitor Logs

1. Click on your service in Railway
2. Go to the **Logs** tab
3. Watch real-time logs as your bot operates

## API Endpoints

Your deployed bot will have these endpoints:

- `GET /` - Health check
- `GET /gmail/status` - Check Gmail authentication status
- `POST /test/enhanced-2fa/cellpex` - Test Cellpex listing with anti-hallucination
- `POST /test/enhanced-2fa/gsm-exchange` - Test GSM Exchange listing

## Environment Variables via Railway CLI

If you prefer using the CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Set variables
railway variables set CELLPEX_USERNAME=your_username
railway variables set CELLPEX_PASSWORD=your_password
# ... repeat for all variables

# Deploy
railway up
```

## Troubleshooting

### Chrome/ChromeDriver Issues
Railway automatically provides Chrome/Chromium. No manual installation needed!

### OAuth Token Issues
If Gmail authentication fails:
1. Run `standalone_oauth_completion.py` locally
2. Copy the refresh token
3. Update `GMAIL_REFRESH_TOKEN` in Railway

### Memory Issues
If you see memory errors:
1. Go to service settings
2. Increase memory limit (if on paid plan)
3. Or optimize code to use less memory

## Production Best Practices

1. **Enable Auto-Deploy**: In GitHub settings, enable auto-deploy for main branch
2. **Set Up Health Checks**: Configure Railway to monitor `/` endpoint
3. **Use Secrets**: Never commit credentials to GitHub
4. **Monitor Usage**: Check Railway dashboard for resource usage
5. **Set Up Alerts**: Configure notifications for failures

## Next Steps

After successful deployment:

1. **Test Anti-Hallucination**: Verify the bot correctly reports failures
2. **Scale to Other Platforms**: Add endpoints for GSM, Kardof, HubX, Handlot
3. **Add Scheduling**: Use Railway's cron jobs for automated posting
4. **Implement Webhooks**: Get notified of successful/failed listings

## Support

- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- Our GitHub Issues: https://github.com/itsAR-VR/The-Daily-Dribble---Solo-Project/issues

## Overview
This guide will help you deploy the enhanced marketplace listing bot with anti-hallucination capabilities to Railway.

## Prerequisites
- Railway account ([sign up here](https://railway.app))
- GitHub repository with the code pushed
- All marketplace credentials ready

## Step-by-Step Deployment

### 1. Create a New Railway Project

1. Visit [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect your GitHub account if not already connected
5. Select your repository: `The-Daily-Dribble---Solo-Project`

### 2. Configure Environment Variables

Railway will need all your marketplace credentials and API keys. Click on your service and go to the **Variables** tab, then add:

#### Gmail OAuth Credentials
```
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
GMAIL_REFRESH_TOKEN=your_gmail_refresh_token
```

#### OpenAI API Key
```
OPENAI_API_KEY=your_openai_api_key
```

#### Marketplace Credentials
```
# Cellpex
CELLPEX_USERNAME=your_cellpex_username
CELLPEX_PASSWORD=your_cellpex_password

# GSM Exchange
GSM_EXCHANGE_USERNAME=your_gsm_username
GSM_EXCHANGE_PASSWORD=your_gsm_password

# Kardof
KARDOF_USERNAME=your_kardof_username
KARDOF_PASSWORD=your_kardof_password

# HubX
HUBX_USERNAME=your_hubx_username
HUBX_PASSWORD=your_hubx_password

# Handlot
HANDLOT_USERNAME=your_handlot_username
HANDLOT_PASSWORD=your_handlot_password
```

#### Chrome Configuration (Railway handles this automatically)
```
CHROME_BIN=/usr/bin/chromium-browser
CHROME_PATH=/usr/bin/chromium-browser
```

### 3. Configure Build Settings

1. In your service settings, set:
   - **Root Directory**: `/backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT`

### 4. Deploy the Application

1. After adding all variables, click **"Deploy"**
2. Railway will:
   - Build your application
   - Install all dependencies
   - Start the FastAPI server

### 5. Generate a Public URL

1. Go to your service's **Settings** tab
2. Under **Public Networking**, click **"Generate Domain"**
3. Railway will provide a URL like: `your-app.up.railway.app`

### 6. Test Your Deployment

Once deployed, test the anti-hallucination bot:

```bash
# Test Cellpex listing with anti-hallucination
curl -X POST https://your-app.up.railway.app/test/enhanced-2fa/cellpex \
  -H "Content-Type: application/json" \
  -d '{
    "category": "Apple > iPhone",
    "brand": "Apple",
    "model": "iPhone 14 Pro",
    "available_quantity": 5,
    "price": 899.99,
    "comments": "Brand new, sealed box",
    "remarks": "Ships within 24 hours"
  }'
```

### 7. Monitor Logs

1. Click on your service in Railway
2. Go to the **Logs** tab
3. Watch real-time logs as your bot operates

## API Endpoints

Your deployed bot will have these endpoints:

- `GET /` - Health check
- `GET /gmail/status` - Check Gmail authentication status
- `POST /test/enhanced-2fa/cellpex` - Test Cellpex listing with anti-hallucination
- `POST /test/enhanced-2fa/gsm-exchange` - Test GSM Exchange listing

## Environment Variables via Railway CLI

If you prefer using the CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to your project
railway link

# Set variables
railway variables set CELLPEX_USERNAME=your_username
railway variables set CELLPEX_PASSWORD=your_password
# ... repeat for all variables

# Deploy
railway up
```

## Troubleshooting

### Chrome/ChromeDriver Issues
Railway automatically provides Chrome/Chromium. No manual installation needed!

### OAuth Token Issues
If Gmail authentication fails:
1. Run `standalone_oauth_completion.py` locally
2. Copy the refresh token
3. Update `GMAIL_REFRESH_TOKEN` in Railway

### Memory Issues
If you see memory errors:
1. Go to service settings
2. Increase memory limit (if on paid plan)
3. Or optimize code to use less memory

## Production Best Practices

1. **Enable Auto-Deploy**: In GitHub settings, enable auto-deploy for main branch
2. **Set Up Health Checks**: Configure Railway to monitor `/` endpoint
3. **Use Secrets**: Never commit credentials to GitHub
4. **Monitor Usage**: Check Railway dashboard for resource usage
5. **Set Up Alerts**: Configure notifications for failures

## Next Steps

After successful deployment:

1. **Test Anti-Hallucination**: Verify the bot correctly reports failures
2. **Scale to Other Platforms**: Add endpoints for GSM, Kardof, HubX, Handlot
3. **Add Scheduling**: Use Railway's cron jobs for automated posting
4. **Implement Webhooks**: Get notified of successful/failed listings

## Support

- Railway Discord: https://discord.gg/railway
- Railway Docs: https://docs.railway.app
- Our GitHub Issues: https://github.com/itsAR-VR/The-Daily-Dribble---Solo-Project/issues