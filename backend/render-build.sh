#!/usr/bin/env bash
# Build script for Render deployment
set -e

echo "==> Installing Python dependencies..."
pip install -r requirements.txt

echo "==> Copying main script..."
cp ../multi_platform_listing_bot.py .

echo "==> Creating jobs directory..."
mkdir -p jobs

echo "==> Build completed successfully!"
echo "Note: Chrome/Selenium requires Starter plan ($7/month) for full functionality." 