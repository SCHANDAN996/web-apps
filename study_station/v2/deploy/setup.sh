#!/usr/bin/env bash
# One-time server setup (Ubuntu/Debian, run as root from study_station/v2). Safe to re-run.
set -euo pipefail
APP=/var/www/study_station/v2
[ "$(pwd)" = "$APP" ] || { echo "Copy the repo so this folder is $APP, then run from there."; exit 1; }
[ -f .env ] || { echo "Create .env first: cp .env.example .env && nano .env"; exit 1; }

apt-get update -qq
apt-get install -y -qq python3-venv python3-pip nginx certbot python3-certbot-nginx
id studystation >/dev/null 2>&1 || useradd --system --home /var/lib/studystation --shell /usr/sbin/nologin studystation
mkdir -p /var/lib/studystation /var/log/studystation /var/backups/studystation
chown -R studystation:studystation /var/lib/studystation /var/log/studystation /var/backups/studystation "$APP"
chmod 600 .env
chmod +x deploy/*.sh

sudo -u studystation python3 -m venv venv
sudo -u studystation ./venv/bin/pip install -q -r requirements.txt
sudo -u studystation deploy/run.sh python -m app.seed

cp deploy/studystation.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now studystation
cp deploy/nginx.conf /etc/nginx/sites-available/studystation
ln -sf /etc/nginx/sites-available/studystation /etc/nginx/sites-enabled/studystation
nginx -t && systemctl reload nginx
crontab -u studystation deploy/crontab
echo "Done. Next: certbot --nginx -d studystation.in -d www.studystation.in   then open https://studystation.in/healthz"
