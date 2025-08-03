#!/bin/bash
# Railway Deployment Script for Multi-Platform Listing Bot

echo "🚀 Deploying Multi-Platform Listing Bot to Railway..."

# Check if we're in the right directory
if [ ! -f "fastapi_app.py" ]; then
    echo "❌ Error: Must run from backend directory"
    exit 1
fi

# Ensure Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install with: npm install -g @railway/cli"
    exit 1
fi

# Step 1: Update requirements.txt
echo "📦 Updating requirements.txt..."
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
openpyxl==3.1.2
selenium==4.15.2
python-dotenv==1.0.0
python-multipart==0.0.6
google-auth==2.23.4
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.108.0
openai==1.3.5
requests==2.31.0
EOF

# Step 2: Create production Dockerfile
echo "🐳 Creating production Dockerfile..."
cat > Dockerfile << 'EOF'
# Use browserless/chrome as base for Selenium support
FROM browserless/chrome:latest

# Install Python 3.11
USER root
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Create and use virtual environment
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Create jobs directory
RUN mkdir -p jobs

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE $PORT

# Start command with enhanced logging
CMD ["sh", "-c", "uvicorn fastapi_app:app --host 0.0.0.0 --port $PORT --log-level info"]
EOF

# Step 3: Create railway.toml configuration
echo "📝 Creating railway.toml..."
cat > railway.toml << EOF
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn fastapi_app:app --host 0.0.0.0 --port \$PORT --log-level info"
healthcheckPath = "/"
healthcheckTimeout = 100
restartPolicyType = "ALWAYS"

[environments.production]
NODE_ENV = "production"
EOF

# Step 4: Set environment variables
echo "🔐 Setting environment variables on Railway..."

# Platform credentials
railway variables set CELLPEX_USERNAME=cellntell
echo "Set CELLPEX_USERNAME ✅"

# Note: User should set passwords manually for security
echo "⚠️  Please set these variables manually on Railway dashboard:"
echo "   - CELLPEX_PASSWORD"
echo "   - GSMEXCHANGE_USERNAME"
echo "   - GSMEXCHANGE_PASSWORD"
echo "   - HUBX_USERNAME"
echo "   - HUBX_PASSWORD"
echo "   - OPENAI_API_KEY (optional)"

# Gmail OAuth files need special handling
echo ""
echo "📧 For Gmail OAuth:"
echo "   1. Copy contents of google_oauth_credentials.json"
echo "   2. Set as GOOGLE_OAUTH_CREDENTIALS environment variable"
echo "   3. The app will recreate the file at runtime"

# Step 5: Create test endpoint
echo "🧪 Adding test endpoints to FastAPI..."
cat >> test_endpoints.py << 'EOF'
# Test endpoints for Railway deployment
from fastapi import APIRouter
from datetime import datetime
import os

test_router = APIRouter(prefix="/test", tags=["testing"])

@test_router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "local")
    }

@test_router.get("/chrome")
async def test_chrome():
    """Test Chrome/Selenium availability"""
    try:
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        return {
            "chrome_available": True,
            "test_result": f"Successfully loaded page: {title}"
        }
    except Exception as e:
        return {
            "chrome_available": False,
            "error": str(e)
        }

@test_router.get("/platforms")
async def test_platforms():
    """List configured platforms and credentials"""
    platforms = ["cellpex", "gsmexchange", "hubx", "kardof", "handlot"]
    status = {}
    
    for platform in platforms:
        user_var = f"{platform.upper()}_USERNAME"
        pass_var = f"{platform.upper()}_PASSWORD"
        
        status[platform] = {
            "username_set": bool(os.getenv(user_var)),
            "password_set": bool(os.getenv(pass_var))
        }
    
    return status
EOF

# Step 6: Commit changes
echo "📝 Committing changes..."
git add -A
git commit -m "🚀 Prepare for Railway deployment with production configuration" || true

# Step 7: Deploy to Railway
echo ""
echo "🚀 Ready to deploy! Run these commands:"
echo ""
echo "1. Set sensitive environment variables on Railway dashboard"
echo "2. Deploy with: railway up"
echo "3. Check logs with: railway logs --tail"
echo "4. Open app with: railway open"
echo ""
echo "📊 After deployment, test with:"
echo "   curl https://your-app.railway.app/test/health"
echo "   curl https://your-app.railway.app/test/chrome"
echo "   curl https://your-app.railway.app/test/platforms"