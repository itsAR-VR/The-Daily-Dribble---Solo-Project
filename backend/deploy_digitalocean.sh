#!/bin/bash
# DigitalOcean Droplet Setup Script for Multi-Platform Listing Bot

# Update system
apt-get update
apt-get upgrade -y

# Install Python and pip
apt-get install -y python3.11 python3-pip python3-venv

# Install Chrome and ChromeDriver
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | grep -oP '\d+\.\d+\.\d+')
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION -O /tmp/chromedriver_version
CHROMEDRIVER_VERSION=$(cat /tmp/chromedriver_version)
wget https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/local/bin/
chmod +x /usr/local/bin/chromedriver

# Clone your repository
git clone https://github.com/itsAR-VR/The-Daily-Dribble---Solo-Project.git /app
cd /app

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/listing-bot.service << EOF
[Unit]
Description=Multi-Platform Listing Bot API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/app/backend
Environment="PATH=/app/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/app/venv/bin/uvicorn fastapi_app:app --host 0.0.0.0 --port 8000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

# Enable and start the service
systemctl enable listing-bot
systemctl start listing-bot

# Install Nginx for reverse proxy
apt-get install -y nginx
cat > /etc/nginx/sites-available/listing-bot << EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOF

ln -s /etc/nginx/sites-available/listing-bot /etc/nginx/sites-enabled/
systemctl restart nginx

echo "Deployment complete! Your API is running on http://your-droplet-ip" 