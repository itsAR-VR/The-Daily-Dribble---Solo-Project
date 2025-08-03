#!/bin/bash

# Deploy Enhanced 2FA Architecture to Railway
# This script deploys our working Cellpex 2FA integration and prepares for GSM Exchange testing

echo "🚀 Deploying Enhanced 2FA Architecture to Railway..."

# Check if we're in the right directory
if [ ! -f "enhanced_platform_poster.py" ]; then
    echo "❌ Error: Must run from backend directory"
    exit 1
fi

# Check if Railway CLI is available
if ! command -v railway &> /dev/null; then
    echo "❌ Error: Railway CLI not found. Install with: npm install -g @railway/cli"
    exit 1
fi

# Login to Railway
echo "🔐 Checking Railway authentication..."
railway login

# Connect to project
echo "🔗 Connecting to Railway project..."
railway link

# Set critical environment variables for 2FA
echo "🔧 Setting environment variables..."

# Core FastAPI settings
railway variables set FASTAPI_ENV=production
railway variables set PORT=8000
railway variables set HOST=0.0.0.0

# Cellpex credentials (working platform)
echo "📋 Please provide Cellpex credentials for production testing:"
read -p "Enter Cellpex Username: " CELLPEX_USER
read -s -p "Enter Cellpex Password: " CELLPEX_PASS
echo ""

railway variables set CELLPEX_USERNAME="$CELLPEX_USER"
railway variables set CELLPEX_PASSWORD="$CELLPEX_PASS"

# GSM Exchange credentials (next to implement)
echo "📋 Please provide GSM Exchange credentials for testing:"
read -p "Enter GSM Exchange Username: " GSM_USER
read -s -p "Enter GSM Exchange Password: " GSM_PASS
echo ""

railway variables set GSMEXCHANGE_USERNAME="$GSM_USER"
railway variables set GSMEXCHANGE_PASSWORD="$GSM_PASS"

# Additional platform credentials
echo "📋 Optional: Provide additional platform credentials (press Enter to skip):"
read -p "HubX Username (optional): " HUBX_USER
if [ ! -z "$HUBX_USER" ]; then
    read -s -p "HubX Password: " HUBX_PASS
    echo ""
    railway variables set HUBX_USERNAME="$HUBX_USER"
    railway variables set HUBX_PASSWORD="$HUBX_PASS"
fi

read -p "Kardof Username (optional): " KARDOF_USER
if [ ! -z "$KARDOF_USER" ]; then
    read -s -p "Kardof Password: " KARDOF_PASS
    echo ""
    railway variables set KARDOF_USERNAME="$KARDOF_USER"
    railway variables set KARDOF_PASSWORD="$KARDOF_PASS"
fi

read -p "Handlot Username (optional): " HANDLOT_USER
if [ ! -z "$HANDLOT_USER" ]; then
    read -s -p "Handlot Password: " HANDLOT_PASS
    echo ""
    railway variables set HANDLOT_USERNAME="$HANDLOT_USER"
    railway variables set HANDLOT_PASSWORD="$HANDLOT_PASS"
fi

# Gmail OAuth settings
echo "🔐 Setting Gmail OAuth configuration..."
if [ -f "token.json" ]; then
    GMAIL_TOKEN=$(cat token.json | base64 -w 0)
    railway variables set GMAIL_TOKEN_BASE64="$GMAIL_TOKEN"
    echo "✅ Gmail token uploaded"
else
    echo "⚠️  Warning: token.json not found. Gmail 2FA may not work in production."
fi

if [ -f "credentials.json" ]; then
    GMAIL_CREDS=$(cat credentials.json | base64 -w 0)
    railway variables set GMAIL_CREDENTIALS_BASE64="$GMAIL_CREDS"
    echo "✅ Gmail credentials uploaded"
else
    echo "⚠️  Warning: credentials.json not found. Gmail 2FA may not work in production."
fi

# OpenAI API key for LLM extraction
read -p "Enter OpenAI API Key (for LLM code extraction): " OPENAI_KEY
railway variables set OPENAI_API_KEY="$OPENAI_KEY"

# Browserless configuration for production Selenium
echo "🌐 Setting up Browserless for production Selenium..."
read -p "Enter Browserless URL (optional, or press Enter for Railway default): " BROWSERLESS_URL
if [ ! -z "$BROWSERLESS_URL" ]; then
    railway variables set BROWSERLESS_URL="$BROWSERLESS_URL"
else
    echo "ℹ️  Using Railway default Selenium setup"
fi

# Create production test endpoints file
echo "📝 Creating production test endpoints..."
cat > test_production_endpoints.py << 'EOF'
#!/usr/bin/env python3
"""
Production test endpoints for Railway deployment
"""

import os
import asyncio
from fastapi import FastAPI, HTTPException
from enhanced_platform_poster import EnhancedCellpexPoster
from gmail_service import gmail_service
from selenium import webdriver

app = FastAPI(title="Enhanced 2FA Testing")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gmail_available": gmail_service.is_available() if gmail_service else False,
        "platforms": ["cellpex", "gsmexchange"]
    }

@app.post("/test/cellpex/2fa")
async def test_cellpex_2fa():
    """Test Cellpex 2FA flow in production"""
    try:
        # Setup Chrome options for production
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)
        
        # Initialize Cellpex poster
        cellpex_poster = EnhancedCellpexPoster(driver)
        
        # Test login with 2FA
        success = cellpex_poster.login_with_2fa()
        
        if success:
            return {
                "status": "success",
                "message": "Cellpex 2FA login successful",
                "platform": "cellpex"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Cellpex 2FA login failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing Cellpex 2FA: {str(e)}"
        )
    finally:
        try:
            driver.quit()
        except:
            pass

@app.post("/test/gsm/2fa")
async def test_gsm_2fa():
    """Test GSM Exchange 2FA flow in production"""
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        
        driver = webdriver.Chrome(options=options)
        
        # Test GSM Exchange login
        from test_gsm_2fa_flow import test_gsm_2fa_flow
        success = test_gsm_2fa_flow()
        
        if success:
            return {
                "status": "success", 
                "message": "GSM Exchange 2FA login successful",
                "platform": "gsmexchange"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="GSM Exchange 2FA login failed"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing GSM Exchange 2FA: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
EOF

# Update Dockerfile for production
echo "🐳 Updating Dockerfile for enhanced 2FA..."
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Install system dependencies for Chrome and Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=`curl -sS chromedriver.chromium.org/LATEST_RELEASE` \
    && wget -O /tmp/chromedriver.zip http://chromedriver.chromium.org/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "fastapi_app.py"]
EOF

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up

# Show deployment status
echo "📊 Deployment Status:"
railway status

# Get the deployment URL
RAILWAY_URL=$(railway domain)
echo "🌐 Deployment URL: $RAILWAY_URL"

echo ""
echo "✅ Enhanced 2FA deployment complete!"
echo ""
echo "🧪 Test endpoints:"
echo "  Health Check: $RAILWAY_URL/health"
echo "  Cellpex 2FA:  $RAILWAY_URL/test/cellpex/2fa"
echo "  GSM 2FA:      $RAILWAY_URL/test/gsm/2fa"
echo ""
echo "📋 Next steps:"
echo "  1. Test Cellpex 2FA in production"
echo "  2. Test GSM Exchange 2FA flow"
echo "  3. Implement remaining platforms"
echo "  4. Monitor and optimize performance"