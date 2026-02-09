#!/bin/bash
# Start Kontali services with PM2 (development mode)

set -e

echo "=========================================="
echo "  KONTALI - Starting with PM2 (DEV)"
echo "=========================================="

cd "$(dirname "$0")"

# Stop any existing nohup processes
echo "Stopping existing nohup processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3002 | xargs kill -9 2>/dev/null || true

# Delete existing PM2 processes if any
pm2 delete all 2>/dev/null || true

# Start with PM2
echo "Starting services with PM2..."
pm2 start ecosystem.dev.config.js

# Save PM2 config
pm2 save

# Setup PM2 startup (runs on server reboot)
echo ""
echo "Setting up PM2 auto-startup..."
pm2 startup systemd -u ubuntu --hp /home/ubuntu

echo ""
echo "=========================================="
echo "✓ Services started with PM2!"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  pm2 list              - View all processes"
echo "  pm2 logs              - View logs"
echo "  pm2 restart all       - Restart all services"
echo "  pm2 stop all          - Stop all services"
echo "  pm2 delete all        - Remove all services"
echo ""
