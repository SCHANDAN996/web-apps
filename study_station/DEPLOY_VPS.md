# 🚀 Study Station — VPS पर Deploy करने की पूरी Guide

यह guide Ubuntu/Debian VPS मानकर लिखी गई है। तीन हिस्से deploy होंगे:

1. **Website (static)** — nginx से serve होगी (`website/` फ़ोल्डर)
2. **Backend API + Admin** — Flask, gunicorn से चलेगा (`backend-server/`)
3. **Job Scraper** — cron से हर 3 घंटे अपने-आप चलेगा

> पहले तय कर लें: आपका **domain** क्या है (जैसे `studystation.in`)। नीचे हर जगह `studystation.in` की जगह अपना domain डालें।

---

## चरण 0: फ़ाइलें VPS पर भेजें

अपने PC से (Git Bash / PowerShell):
```bash
# पूरे प्रोजेक्ट को VPS पर भेजें (venv और chrome_profile छोड़कर)
rsync -av --exclude 'venv' --exclude '*_profile*' --exclude '__pycache__' \
  "/c/Users/Admin/Desktop/my project/study_station/" \
  root@YOUR_VPS_IP:/var/www/study_station/
```
या `git clone` करें अगर repo GitHub पर है।

---

## चरण 1: सिस्टम तैयार करें

```bash
sudo apt update && sudo apt install -y python3-venv python3-pip nginx
cd /var/www/study_station/backend-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

---

## चरण 2: Secrets (.env) सेट करें

```bash
cd /var/www/study_station/backend-server
cp .env.example .env
nano .env      # असली values भरें (Telegram token, GEMINI_API_KEY आदि)
```
`.env` में यह भी जोड़ें ताकि canonical URLs और sitemap सही domain से बनें:
```
SITE_URL=https://studystation.in
```

**Admin login (ज़रूरी):** `SECRET_KEY` और `ADMIN_PASSWORD` भरे बिना `/admin` बंद (locked) रहेगा:
```
SECRET_KEY=<python3 -c "import secrets; print(secrets.token_hex(32))" का output>
ADMIN_PASSWORD=<मज़बूत password>
TRUST_PROXY=1          # nginx के पीछे — rate limit को असली IP मिले
```
> ℹ️ AI chat पर rate limit (8/मिनट, 60/दिन प्रति IP) हर gunicorn worker में अलग गिना जाता है।

> ⚠️ पुरानी hardcoded Gemini key अब env से आती है — पुरानी key को Google console में **rotate/delete** ज़रूर करें।

---

## चरण 3: Database तैयार करें और site build करें

```bash
cd /var/www/study_station/backend-server
source venv/bin/activate
set -a; source .env; set +a          # SITE_URL आदि load करें

python seed.py          # (अगर पहली बार — DB तैयार करता है)
python job_scraper.py run             # असली jobs लाएँ

# ⚠️ क्रम ज़रूरी है: पहले किताबें, फिर website।
# build_chapters.py हर अध्याय के standalone SEO pages + chapters/_pages.json
# बनाता है, जिसे build_website.py sitemap में डालता है। उल्टा चलाया तो
# 88 अध्याय sitemap से ग़ायब रहेंगे।
cd ../books && python build_chapters.py   # 44 अध्याय + 88 SEO pages + hub
cd ../backend-server && python build_website.py   # website + sitemap.xml
```

---

## चरण 4: Backend को gunicorn + systemd से चलाएँ

`/etc/systemd/system/studystation.service` बनाएँ:
```ini
[Unit]
Description=Study Station Flask API
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/study_station/backend-server
EnvironmentFile=/var/www/study_station/backend-server/.env
ExecStart=/var/www/study_station/backend-server/venv/bin/gunicorn \
  --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```
फिर:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now studystation
sudo systemctl status studystation      # चल रहा है या नहीं देखें
```

---

## चरण 5: nginx configure करें

`/etc/nginx/sites-available/studystation` बनाएँ:
```nginx
server {
    listen 80;
    server_name studystation.in www.studystation.in;

    # Static website
    root /var/www/study_station/website;
    index index.html;

    # Service worker और manifest सही MIME + no-cache
    location = /sw.js            { add_header Cache-Control "no-cache"; }
    location = /manifest.webmanifest { types { application/manifest+json webmanifest; } }

    # Static pages
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Backend API + admin panel → Flask
    location /api/   { proxy_pass http://127.0.0.1:5000; proxy_set_header Host $host; }
    location /admin  { proxy_pass http://127.0.0.1:5000; proxy_set_header Host $host; }

    # Static assets लंबे समय cache करें
    location ~* \.(css|js|svg|png|jpg|woff2)$ {
        expires 7d;
        add_header Cache-Control "public";
    }
}
```
फिर:
```bash
sudo ln -s /etc/nginx/sites-available/studystation /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## चरण 6: HTTPS (SSL) — ज़रूरी है (PWA के लिए भी)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d studystation.in -d www.studystation.in
```
Certbot अपने-आप nginx को HTTPS पर बदल देगा और renew भी करता रहेगा।

> **Note:** Service Worker (offline PWA) केवल HTTPS पर काम करता है — इसलिए SSL अनिवार्य है।

---

## चरण 7: Job Scraper को cron से auto-run करें

```bash
sudo crontab -e
```
यह line जोड़ें (हर 3 घंटे में नई jobs + website rebuild):
```cron
0 */3 * * * cd /var/www/study_station/backend-server && set -a && . ./.env && set +a && ./venv/bin/python job_scraper.py run >> /var/log/studystation_jobs.log 2>&1
```

---

## चरण 8: अंतिम जाँच (Deploy Checklist)

- [ ] `https://studystation.in` खुलती है (HTTPS lock दिखता है)
- [ ] Homepage पर stats सही हैं (कोई नकली "10,000 students" नहीं)
- [ ] `/jobs.html` पर असली jobs दिखती हैं + disclaimer
- [ ] किसी job page पर "Official Details" link असली notification खोलता है
- [ ] `/sitemap.xml` खुलती है और domain सही है
- [ ] Chrome DevTools → Application → Manifest + Service Worker दोनों दिखते हैं
- [ ] मोबाइल में "Add to Home Screen" आता है
- [ ] `/admin` लॉगिन काम करता है (backend चल रहा है)
- [ ] पुरानी Gemini API key rotate कर दी गई है

---

## आगे (Optional, बाद के लिए)
- Fonts और Ionicons को self-host करना (अभी CDN से आते हैं — धीमे नेट पर सुधरेगा)
- Cloudflare (free) को domain के आगे लगाना — और तेज़ + DDoS सुरक्षा
- AdSense कोड jobs pages पर (users आने के बाद)
