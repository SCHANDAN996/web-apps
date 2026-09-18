#!/bin/bash
# TradeKaro — roz ka apne-aap backup
# crontab se roz raat 2:30 IST (21:00 UTC) par chalta hai — bazaar band rehta hai tab.
#
# Pro Kisan wali DB 10 MB ki hai, ye 4 GB ki hai. Isliye yahan sirf 3 din ke
# daily DB snapshot rakhte hain (~12 GB), models/config ki tarball 14 din.
# Chalne se pehle jagah bhi jaanchta hai.
#
# Purane haath se liye gaye backup (/var/backups/tradekaro/*_20260803.*) ko
# ye script chhuti nahi — wo top level par hain, ye sirf daily/ me kaam karta hai.

set -u
P=/var/www/tradekaro/Trading_AI_Project
DB="$P/trading_data.db"
OUT=/var/backups/tradekaro
LOG="$OUT/backup.log"
mkdir -p "$OUT/daily"

STAMP=$(TZ=Asia/Kolkata date +%F)

# --- jagah ki jaanch ---
# VACUUM INTO ko poori DB ke barabar jagah chahiye. Do guna na ho to ruk jao,
# warna aadhi likhi file bachegi aur disk bhi bhar jayegi.
DB_KB=$(du -k "$DB" 2>/dev/null | cut -f1)
FREE_KB=$(df -k --output=avail "$OUT" | tail -1)
if [ -z "$DB_KB" ]; then
    echo "$(TZ=Asia/Kolkata date '+%F %H:%M') GALAT: DB mili hi nahi: $DB" >> "$LOG"
    exit 1
fi
if [ "$FREE_KB" -lt $((DB_KB * 2)) ]; then
    echo "$(TZ=Asia/Kolkata date '+%F %H:%M') GALAT: jagah kam — chahiye $((DB_KB*2/1024))MB, hai $((FREE_KB/1024))MB" >> "$LOG"
    exit 1
fi

# --- database ---
# VACUUM INTO consistent nakal deta hai chahe bot likh raha ho. Seedha `cp`
# WAL ke saath aadhi-adhoori file de sakta hai.
#
# sqlite3 CLI is server par install nahi hai, aur sirf backup ke liye naya
# package daalne ki zaroorat nahi — project ke venv me Python ka sqlite3
# module pehle se maujood hai, wahi kaafi hai.
DEST="$OUT/daily/trading_data_$STAMP.db"
rm -f "$DEST"   # VACUUM INTO mana kar deta hai agar file pehle se ho
if ! "$P/venv/bin/python" -c "
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
con.execute('VACUUM INTO ?', (sys.argv[2],))
con.close()
" "$DB" "$DEST" 2>>"$LOG"; then
    echo "$(TZ=Asia/Kolkata date '+%F %H:%M') GALAT: VACUUM INTO fail" >> "$LOG"
    rm -f "$DEST"
    exit 1
fi

# khali/adhuri file bani ho to purane backup mat hatao
SZ=$(stat -c%s "$DEST" 2>/dev/null || echo 0)
if [ "$SZ" -lt 1000000 ]; then
    echo "$(TZ=Asia/Kolkata date '+%F %H:%M') GALAT: DB bahut chhoti ($SZ bytes)" >> "$LOG"
    rm -f "$DEST"
    exit 1
fi

# nakal padhi ja sakti hai ya nahi — corrupt backup se bura kuch nahi
if ! "$P/venv/bin/python" -c "
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
print(con.execute('PRAGMA quick_check').fetchone()[0])
con.close()
" "$DEST" 2>/dev/null | grep -q "^ok$"; then
    echo "$(TZ=Asia/Kolkata date '+%F %H:%M') GALAT: nakal ka quick_check fail" >> "$LOG"
    rm -f "$DEST"
    exit 1
fi

# --- models + config + code (DB/venv/data chhod kar) ---
tar czf "$OUT/daily/models_config_$STAMP.tar.gz" \
    -C "$P" models config requirements.txt 2>/dev/null

# --- purane hatao: DB 3 din, tarball 14 din ---
find "$OUT/daily" -maxdepth 1 -name 'trading_data_*.db'        -mtime +3  -delete
find "$OUT/daily" -maxdepth 1 -name 'models_config_*.tar.gz'   -mtime +14 -delete

echo "$(TZ=Asia/Kolkata date '+%F %H:%M') THIK  db=$((SZ/1024/1024))MB  daily=$(ls "$OUT/daily" | wc -l) file  free=$(df -h --output=avail / | tail -1 | tr -d ' ')" >> "$LOG"
