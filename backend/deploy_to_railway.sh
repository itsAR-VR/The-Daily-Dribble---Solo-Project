#!/bin/bash
# Deploy Anti-Hallucination Bot to Railway

echo "🚂 Deploying Anti-Hallucination Bot to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm i -g @railway/cli
fi

# Login to Railway
echo "📝 Logging into Railway..."
railway login --browserless

# Initialize or link project
if [ ! -f ".railway/config.json" ]; then
    echo "🔗 Initializing new Railway project..."
    railway init --name "marketplace-bot-anti-hallucination"
else
    echo "✅ Railway project already linked"
fi

# Set environment variables
echo "🔐 Setting environment variables..."

# Gmail OAuth
railway variables set GMAIL_CLIENT_ID="${GMAIL_CLIENT_ID}" 
railway variables set GMAIL_CLIENT_SECRET="${GMAIL_CLIENT_SECRET}"
railway variables set GMAIL_REFRESH_TOKEN="${GMAIL_REFRESH_TOKEN}"

# OpenAI
railway variables set OPENAI_API_KEY="${OPENAI_API_KEY}"

# Cellpex
railway variables set CELLPEX_USERNAME="${CELLPEX_USERNAME}"
railway variables set CELLPEX_PASSWORD="${CELLPEX_PASSWORD}"

# GSM Exchange
railway variables set GSM_EXCHANGE_USERNAME="${GSM_EXCHANGE_USERNAME}"
railway variables set GSM_EXCHANGE_PASSWORD="${GSM_EXCHANGE_PASSWORD}"

# Other platforms (if available)
if [ ! -z "${KARDOF_USERNAME}" ]; then
    railway variables set KARDOF_USERNAME="${KARDOF_USERNAME}"
    railway variables set KARDOF_PASSWORD="${KARDOF_PASSWORD}"
fi

if [ ! -z "${HUBX_USERNAME}" ]; then
    railway variables set HUBX_USERNAME="${HUBX_USERNAME}"
    railway variables set HUBX_PASSWORD="${HUBX_PASSWORD}"
fi

if [ ! -z "${HANDLOT_USERNAME}" ]; then
    railway variables set HANDLOT_USERNAME="${HANDLOT_USERNAME}"
    railway variables set HANDLOT_PASSWORD="${HANDLOT_PASSWORD}"
fi

# Chrome config (Railway handles this)
railway variables set CHROME_BIN="/usr/bin/chromium"
railway variables set CHROME_PATH="/usr/bin/chromium"

# Deploy
echo "🚀 Deploying to Railway..."
railway up --detach

# Get deployment URL
echo "🌐 Getting deployment URL..."
railway domain

echo "✅ Deployment complete!"
echo "📊 View logs with: railway logs"
echo "🔗 Open dashboard with: railway open"