# Railway Chrome Setup Guide

## Overview

There are two ways to run Chrome with Selenium on Railway:

### Option 1: Standalone Chrome Service (Recommended)
Use a separate `selenium/standalone-chrome` service that your app connects to remotely.

### Option 2: Local Chrome (Current Setup)
Install Chrome directly in your app container and use Selenium Manager.

## Current Issue

The local Chrome setup is failing because ChromeDriver downloaded by Selenium Manager is missing these libraries:
- libglib-2.0.so.0
- libnspr4.so
- libnss3.so
- libnssutil3.so
- libxcb.so.1

## Solution: Use Standalone Chrome

1. **Deploy Standalone Chrome Service on Railway**
   - Create a new service in Railway
   - Use Docker image: `selenium/standalone-chrome:latest`
   - Name it: `standalone-chrome`

2. **Set Environment Variables in Your App**
   ```
   SELENIUM_REMOTE_URL=http://standalone-chrome.railway.internal:4444/wd/hub
   ```

3. **Internal Networking**
   - Railway services can communicate via internal networking
   - Use the service name + `.railway.internal` as the hostname

## Code Changes

The code already supports remote Selenium:
- If `SELENIUM_REMOTE_URL` is set, it uses remote WebDriver
- If not, it falls back to local Chrome with Selenium Manager

## Benefits of Standalone Chrome

1. **Separation of Concerns**: Chrome runs in its own container
2. **Better Resource Management**: Can scale Chrome independently
3. **Easier Updates**: Update Chrome without rebuilding your app
4. **No Dependency Issues**: Selenium's official image has all dependencies

## Testing

To verify it's working:
```bash
curl https://your-app.railway.app/
# Should show chrome_status: "available" if connected
```

## Alternative: Fix Local Chrome

If you prefer local Chrome, wait for the Dockerfile with all dependencies to deploy. The missing libraries are already added but Railway needs to rebuild the image.