# Railway Chrome Driver Fix Guide

## 🔧 The Issue
Chrome and ChromeDriver are installed in the Docker container, but the environment variables aren't being passed to the application properly.

## ✅ Solution: Add These Environment Variables to Railway

Go to your Railway project settings and add these environment variables:

```env
# Chrome Binary Path
CHROME_BIN=/usr/bin/google-chrome-stable
CHROME_PATH=/usr/bin/google-chrome-stable
GOOGLE_CHROME_BIN=/usr/bin/google-chrome-stable

# ChromeDriver Path
CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
SE_CHROMEDRIVER_PATH=/usr/local/bin/chromedriver

# Chrome User Data Directory
CHROME_USER_DATA_DIR=/tmp/.chrome

# Additional Chrome Options
CHROMIUM_FLAGS=--disable-software-rasterizer --disable-dev-shm-usage
```

## 📝 Steps to Fix:

1. **Go to Railway Dashboard**
   - Navigate to your project
   - Click on your service (Listing Bot API)
   - Go to "Variables" tab

2. **Add the Environment Variables**
   - Click "Add Variable"
   - Add each of the variables above
   - Make sure to save

3. **Trigger a Redeploy**
   - Go to "Deployments" tab
   - Click the three dots on the latest deployment
   - Select "Redeploy"

4. **Verify Chrome is Working**
   ```bash
   python diagnose_railway_chrome.py
   ```

## 🎯 Expected Result
After adding these variables and redeploying, Chrome should work properly and you'll see:
- Chrome: available ✅
- ChromeDriver: installed ✅
- Bot can create browser instances ✅

## 🚨 Alternative Fix (if above doesn't work)

Update the Dockerfile to hardcode the paths:

```dockerfile
# Add after Chrome installation
ENV CHROME_BIN=/usr/bin/google-chrome-stable \
    CHROME_PATH=/usr/bin/google-chrome-stable \
    GOOGLE_CHROME_BIN=/usr/bin/google-chrome-stable \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    SE_CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    CHROME_USER_DATA_DIR=/tmp/.chrome \
    CHROMIUM_FLAGS="--disable-software-rasterizer --disable-dev-shm-usage"
```