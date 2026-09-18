#!/bin/bash
PROJECT_DIR="/var/www/tradekaro/Trading_AI_Project"
cd $PROJECT_DIR

echo "Ensuring any old PM2 processes are stopped (they bypass CPU limits)..."
pm2 delete tradekaro-web tradekaro-bot 2>/dev/null
pm2 save

echo "Starting TradeKaro Web Dashboard and Bot via Systemd (CPU limited to 75%)..."
systemctl daemon-reload
systemctl enable tradekaro-web tradekaro-bot
systemctl restart tradekaro-web tradekaro-bot

echo "✅ Apps started. Checking status..."
systemctl status tradekaro-web --no-pager
systemctl status tradekaro-bot --no-pager
echo "To see live logs, use: journalctl -u tradekaro-web -f OR journalctl -u tradekaro-bot -f"
