# 🚀 Study Station v2 — Deploy और टेस्ट गाइड

## 1. Server (एक बार)

भारत में VPS लें (कई सरकारी sites सिर्फ़ भारतीय IP से खुलती हैं)। Ubuntu 22.04/24.04, 1–2 GB RAM काफ़ी है।

```bash
# पूरा repo /var/www/study_station में
sudo mkdir -p /var/www && cd /var/www
sudo git clone <repo-url> web-apps && sudo ln -s /var/www/web-apps/study_station /var/www/study_station
cd /var/www/study_station/v2
sudo cp .env.example .env && sudo nano .env      # SITE_URL, SECRET_KEY, ADMIN_PASSWORD, (ANTHROPIC_API_KEY), (TELEGRAM_*)
sudo timedatectl set-timezone Asia/Kolkata
sudo deploy/setup.sh                              # packages, user, venv, seed, systemd, nginx, cron
sudo certbot --nginx -d studystation.in -d www.studystation.in
```

`deploy/` में क्या है:

| File | काम |
|---|---|
| `setup.sh` | पूरा server setup (दोबारा चलाना सुरक्षित) |
| `studystation.service` | systemd: uvicorn, 2 workers, 127.0.0.1:8001 |
| `nginx.conf` | HTTPS redirect, static files, `/api/` rate limit |
| `crontab` | हर 3 घंटे jobs sweep · दिन में 3 बार current affairs · रात में cleanup + backup · सुबह-शाम alerts |
| `run.sh` | `.env` लोड करके कोई भी command: `deploy/run.sh python -m app.jobs health` |
| `backup.sh` | SQLite का सुरक्षित backup, 14 दिन रखता है |

## 2. Update (नया code आने पर)

```bash
cd /var/www/web-apps && sudo git pull
cd study_station/v2 && sudo ./venv/bin/pip install -q -r requirements.txt
sudo -u studystation deploy/run.sh python -m app.seed      # नए topics/exam patterns; data सुरक्षित रहता है
sudo systemctl restart studystation
```

Database की नई columns अपने-आप जुड़ जाती हैं (`ensure_schema`)।

## 3. Deploy के बाद टेस्ट checklist ✅

**बुनियादी**
- [ ] `https://studystation.in/healthz` → `{"ok": true}`
- [ ] `sudo -u studystation deploy/run.sh python -m pytest -q` → सब pass (pytest requirements में है)
- [ ] `journalctl -u studystation -n 50` में error नहीं

**Student flow (फ़ोन पर)**
- [ ] पहली बार खोलें → भाषा/योग्यता/परीक्षा चुनें → Home
- [ ] अभ्यास → कोई टॉपिक → 10 सवाल → सही/गलत + हल → परिणाम
- [ ] मॉक → SSC GD → timer, palette, "रिव्यू के लिए मार्क", submit → section-wise परिणाम
- [ ] अगले दिन "दोहराएँ" में कल के गलत सवाल
- [ ] सेटिंग्स → "मेरा code बनाएँ" → दूसरे browser में code डालकर progress आए
- [ ] हिंदी ⇄ English बटन, dark mode, "Add to Home screen" (PWA)

**नौकरियाँ**
- [ ] `deploy/run.sh python -m app.jobs run` → `deploy/run.sh python -m app.jobs health` — UPSC/IBPS/RRB/राज्य आयोग OK हैं? जो FAIL हों उनका URL `app/jobs/sources.py` में जाँचें
- [ ] Jobs page: "खुली" में official badge, तारीख़ें, official PDF button
- [ ] AI agent में `job` (देखें `JOBS_AGENT.md`)

**करंट अफेयर्स**
- [ ] `deploy/run.sh python -m app.current_affairs run` → AIR की ख़बरें आएँ; `feeds_failed` में `pib` हो तो PIB से whitelist माँगें (हम bot का असली नाम भेजते हैं)
- [ ] ANTHROPIC_API_KEY हो तो सार + क्विज़ बनें

**Admin** (`/admin`, ADMIN_PASSWORD)
- [ ] Dashboard संख्याएँ, "Run sweep" बटन → नीचे log
- [ ] Questions → Reported/Flagged → edit → "Save & mark verified"
- [ ] Jobs → Pending → official URL डालकर publish

**AI (key हो तो)**
- [ ] अभ्यास में जवाब देने के बाद "✨ AI से आसान भाषा में समझें"
- [ ] `deploy/run.sh python -m app.generate --topic science/physics --n 10` → admin में नए सवाल (गलत लगे तो "flagged")

**Alerts**
- [ ] `deploy/run.sh python -m app.jobs digest` → रिपोर्ट; Telegram हो तो `--telegram`

## 4. कुछ ज़रूरी बातें

- पुराना `backend-server/` (Flask) और `website/` v2 से अलग हैं; v2 चलने के बाद उन्हें बंद कर सकते हैं।
- AI का ख़र्च: tutor के जवाब cache होते हैं (एक सवाल = एक बार ख़र्च), रोज़ की सीमा `.env` में।
- Backup: `/var/backups/studystation/` — महीने में एक बार restore करके देखें:
  `gunzip -c <file>.db.gz > /tmp/test.db && DATABASE_URL=sqlite:////tmp/test.db deploy/run.sh python -m app.jobs summary`
