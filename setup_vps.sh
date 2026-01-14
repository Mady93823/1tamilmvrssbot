#!/bin/bash

# Auto-Setup Script for Angel Bot VPS

echo "Updating system..."
sudo apt update && sudo apt upgrade -y

echo "Installing Tailscale..."
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

echo "Enabling Tailscale Funnel..."
# Note: You need to authenticate first!
sudo tailscale funnel --bg 3000

echo "Installing qBittorrent-nox..."
sudo apt install qbittorrent-nox -y

echo "Creating qBittorrent systemd service..."
cat <<EOF | sudo tee /etc/systemd/system/qbittorrent-nox.service
[Unit]
Description=qBittorrent Command Line Client
After=network.target

[Service]
# Do not change to "simple"
Type=forking
User=root
Group=root
UMask=007
ExecStart=/usr/bin/qbittorrent-nox -d --webui-port=8080
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

echo "Starting qBittorrent..."
sudo systemctl daemon-reload
sudo systemctl enable qbittorrent-nox
sudo systemctl start qbittorrent-nox

echo "Checking status..."
sudo systemctl status qbittorrent-nox --no-pager

echo "Setup Complete! Don't forget to update your .env file with the Webhook URL and API keys."
