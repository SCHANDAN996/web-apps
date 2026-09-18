# TradeKaro — समस्याओं की सूची

पहला ऑडिट: 3 अगस्त 2026
दूसरा दौर: 6 अगस्त 2026

---

## ✅ जो ठीक हो चुका है

| # | समस्या | हल | Commit |
|---|--------|-----|--------|
| 1 | **AI कुछ सीख नहीं रहा था** — `learner.py` `self.brain.train_incremental()` बुलाता था, पर `main.py` `MultiTimeframeBrain` wrapper भेजता है जिसमें यह method था ही नहीं (सिर्फ़ `Brain` में है)। हफ़्ते में ~2000 errors। | wrapper में passthrough delegate जोड़ा | `36f1a08` |
| 2 | **DB pruning हर बार crash** — `MAX(timestamp)` (text) में से int घटाया जा रहा था। इसकी वजह से `delta_options_wide` कभी साफ़ नहीं हुई (2.5 करोड़ rows / 4 GB) और नीचे लिखा WAL checkpoint + VACUUM कभी चला ही नहीं। | cutoff को formatted timestamp बनाया, retention 90 दिन। VACUUM अब तभी चलता है जब 15% से ज़्यादा pages ख़ाली हों (वरना हर 6 घंटे में मल्टी-GB फ़ाइल दोबारा लिखने का 2 मिनट का lock लगता)। | `6970e53` |
| 3 | `config/credentials.env` **0644** था — सर्वर का कोई भी user पढ़ सकता था | `600`, और `config/` को `700` | — |
| 4 | **कोई version control नहीं** (27k LOC) | `git init` + baseline commit; venv/DB/data/logs/credentials `.gitignore` में | `c9a274c` |
| 5 | **कोई backup नहीं** | `/var/backups/tradekaro/` — DB (3.8 GB, VACUUM INTO से consistent) + models/config tarball | — |
| 6 | **`kill_switch` module मौजूद ही नहीं था** — `telegram_listener.py` उसे import करता था, इसलिए वह स्क्रिप्ट import पर ही crash होती थी; ऊपर से असली कॉल कमेंट किया हुआ था। | `kill_switch.py` बनाया, जो `force_exit_all.py` का मौजूदा लॉजिक ही दोबारा इस्तेमाल करता है (कोड की नक़ल नहीं)। `exit_all()` में `restart_bot` flag जोड़ा — kill switch `False` भेजता है, ताकि आपातकालीन स्टॉप के बाद बॉट **अपने आप चालू न हो**। नतीजा Telegram पर भेजा जाता है। | `ccaf864` |
| 7 | **Risk settings का log-कचरा** — `main.py:67` हर चक्कर में `load_live_settings()` बुलाता था, हर सेकंड ~4 एक जैसी लाइनें। | अब फ़ाइल बदलने पर ही दोबारा पढ़ता/लॉग करता है (mtime जाँच)। startup की 2 लाइनों के बाद चुप। | `ccaf864` |
| 8 | **"KILL ALL" सुनने वाला कोई नहीं था** — `telegram_listener.py` कहीं चलता ही नहीं था, इसलिए फ़ोन से आपातकालीन स्टॉप असंभव था। | `tradekaro-telegram.service` बनाई (enabled, `Restart=always`, CPU 50%, RAM 2G)। सारी unit फ़ाइलें अब `deploy/` में भी हैं। | — |

### दूसरा दौर — 6 अगस्त 2026

| # | समस्या | हल | Commit |
|---|--------|-----|--------|
| 9 | **ब्रेन उल्टी दिशा में position size कर सकता था** — `_aggregate_votes` में `agreement = max(buy_votes, sell_votes)`, यानी जो पक्ष बड़ा हो उसकी गिनती; पर `direction` अलग नियम से आती है (ऊँचा timeframe जीतता है)। 1H=0.80 और 1m/5m/15m=0.30 पर नतीजा था `direction=BUY, agreement=3` — वे तीनों **SELL** वोट थे। `main.py:304` `agreement >= 3` पर ट्रेड करता है, तो यह 75% size का BUY बन जाता, तीन विरोधी वोटों के बल पर। | agreement अब उसी दिशा की गिनी जाती है जो ली जा रही है। ऊपर वाला मामला अब "सिर्फ़ 1 सहमत" में गिरकर HOLD होता है। | `8e98c85` |
| 10 | **Dashboard पूरी तरह बिना पासवर्ड** (पहले #1) — 40 routes खुले, जिनमें `/api/place_trade`, `/api/kill_switch`, `/api/control`, `/api/risk_config`। | एक `before_request` guard (हर route पर decorator नहीं — 40 मौक़े भूलने के), 46 rules ढकती है। बिना `DASH_PASSWORD_HASH` के सब 503 — **fail closed**। साथ में: `app.py` में `load_dotenv` जोड़ा (था ही नहीं), CORS/SocketIO का `*` हटाया, SocketIO handshake पर auth, `next=` open-redirect बंद। 12 tests। | `d8f7207` |
| 11 | **`main.py` में RiskManager दो बार** (पहले #7) | line 603 वाली बेकार instance हटाई | `e114353` |
| 12 | **पूरा app DEBUG mode में log** (पहले #11) — `logging.basicConfig(level=DEBUG)` root logger सेट करता था, हर ~1.8 सेकंड में peewee की एक SQL line। | root अब INFO, शोर वाली libraries WARNING पर। `LOG_LEVEL=DEBUG` से पुराना बर्ताव वापस। पुष्टि: restart के बाद एक मिनट में 0 नई DEBUG lines (पहले ~33)। | `d78c963` |
| 13 | **`requirements.txt` अधूरी** (पहले #10) | `pip freeze` से 87 packages, pinned। header में torch के +cpu build और CPU index की चेतावनी। | `078532a` |
| 14 | **Backup अपने आप नहीं होता** (पहले #16) | `/root/tradekaro_backup.sh` + `/etc/cron.d/tradekaro-backup`, रोज़ 21:00 UTC (02:30 IST)। जगह की जाँच, `VACUUM INTO`, नक़ल पर `quick_check`, 3 दिन DB + 14 दिन tarball। चलाकर देखा: 3865 MB, ok, 52 GB बचा। | `eabf351` |

---

## 🔴 बाक़ी समस्याएँ — प्राथमिकता के क्रम में

### सुरक्षा

1. **Dashboard चालू करने से पहले पासवर्ड सेट करना बाक़ी** — login का कोड लग चुका है (ऊपर #10), पर `DASH_PASSWORD_HASH` अभी सेट नहीं है, इसलिए dashboard हर request पर 503 देगा। एक बार यह चलाएँ:

   ```
   cd /var/www/tradekaro/Trading_AI_Project
   venv/bin/python scripts/set_dashboard_password.py
   systemctl start tradekaro-web    # चालू करना हो तब
   ```

   पासवर्ड आपको ख़ुद चुनना है — फ़ाइल में सिर्फ़ उसका hash जाता है।

2. **बॉट root के तौर पर चलता है** (`User=root`)। एक अलग `tradekaro` user बनाकर उसी की permission देना बेहतर है।

3. **`TOTP_SECRET` प्लेनटेक्स्ट में है** — जिसे यह मिल जाए वो खुद OTP बना लेगा, यानी 2FA बेमतलब। फ़ाइल अब 600 है, पर सोचने लायक़ है कि इसे कहीं और रखा जाए।

4. **`cupsd` पोर्ट 631 पर सबके लिए खुला** — सर्वर पर प्रिंटर सर्विस की ज़रूरत नहीं, बंद कर दें।

5. **पासवर्ड-लॉगिन SSH पर अब भी चालू** — auth.log में अनजान IP से लगातार कोशिशें दिखती हैं। key लग चुकी है, तो `PasswordAuthentication no` कर सकते हैं।

### भरोसे लायक़ बनाना

6. **Broker login startup पर fail होता है** — **यह अब भी बाक़ी है, live जाने से पहले ठीक होना ज़रूरी।**

   जितना पता चला (6 अगस्त): असली वजह broker की तरफ़ से आ रहा **ग़ैर-JSON जवाब** है। Noren SDK जवाब पर सीधे `json.loads()` करता है, तो ख़ाली या HTML body मिलने पर वही "Expecting value: line 1 column 1" निकलता था — उस संदेश में यह कहीं नहीं दिखता था कि गड़बड़ कहाँ है। अब संदेश साफ़ है:

   ```
   [ERROR] ❌ Broker returned a non-JSON reply to login
           (broker down, IP not whitelisted, or wrong endpoint)
   ```

   `TOTP_SECRET` असली है (placeholder नहीं), यानी कोड सच में login की कोशिश करता है और broker जवाब नहीं दे रहा। सबसे संभावित वजहें: **Shoonya पर इस सर्वर का IP whitelist नहीं** (`72.61.235.129`), या credentials/endpoint बदल गया।

   *जानबूझकर आगे नहीं बढ़ा गया:* बार-बार login की कोशिश से broker खाता lock हो सकता है, इसलिए बिना आपकी जानकारी के दोबारा नहीं आज़माया। Shoonya पर IP whitelist जाँचकर एक बार `venv/bin/python src/connector.py` चलाएँ।

7. ~~**`main.py` में RiskManager दो बार**~~ — ठीक हुआ, ऊपर #11 देखें।

8. **अपने कोड का एक भी test नहीं** — काफ़ी हद तक भरा गया: अब 39 tests चलते हैं (brain contract, risk limits, trailing stops, MTF voting के 9, dashboard auth के 12)। बाक़ी बिना test के: `executor` का order path, `database.py` (45 KB), data pipeline।

9. **`src/telegram_ai_bot.py` भी `getUpdates` करता है** — अभी वह कहीं से शुरू नहीं होता, इसलिए टकराव नहीं है। पर उसे कभी चालू किया तो Telegram दो pollers पर `409 Conflict` देगा और kill switch सुनना बंद हो जाएगा।

### रख-रखाव

10. ~~**`requirements.txt` अधूरी**~~ — ठीक हुई, ऊपर #13 देखें।

11. ~~**पूरा app DEBUG mode में log करता है**~~ — ठीक हुआ, ऊपर #12 देखें।

12. **दो बड़े monolith** — `main.py` (40 KB), `app.py` (33 KB)। *(auth का कोड जानबूझकर `src/auth.py` में अलग रखा गया ताकि `app.py` और न फूले।)*

13. **कबाड़** — `experimental/` (10+ अनचले modules), `scripts/` (15 debug scripts), `temp_shoonya/` (vendor SDK की कॉपी, अपना अलग git repo), `Trading_AI_Project_code.zip`।

14. **venv (2 GB) प्रोजेक्ट फ़ोल्डर के अंदर** है।

15. **SQLite 4 GB पर** — कोड में `_execute_retry` का होना बताता है कि lock की दिक़्क़तें पहले आ चुकी हैं। सर्वर पर PostgreSQL पहले से चल रहा है, आगे चलकर वह बेहतर रहेगा।

16. ~~**Backup अपने आप नहीं होता**~~ — लग गया, ऊपर #14 देखें।

17. **`app.py` का `ENVIRONMENT` पहले कभी सही नहीं पढ़ा जाता था** — `load_dotenv` अब जुड़ गया (#10 के साथ), पर इसका मतलब यह भी है कि dashboard पहली बार असली `ENVIRONMENT` देखेगा। अभी `PAPER_TRADING` है इसलिए फ़र्क़ नहीं पड़ता; live जाने पर dashboard का banner पहली बार सच बोलेगा।

---

---

## 📝 सुधार (3 अगस्त 2026)

पहले इस दस्तावेज़ में लिखा था कि **`live_risk.json` गायब होने से risk settings लागू नहीं हो रहीं** — **यह ग़लत था।**

RiskManager अपनी सारी settings `config/ai_config.json` से `AIConfigManager` के ज़रिए लेता है। `live_risk.json` सिर्फ़ एक **वैकल्पिक override** फ़ाइल है जिसे dashboard लिखता है; उसका न होना बिल्कुल सामान्य है (इसीलिए वह लाइन `INFO` है, `ERROR` नहीं)।

जाँची गई असली settings:

| सेटिंग | मान | स्रोत |
|---|---|---|
| Capital | ₹50,000 | `ai_config.json → trading.capital` |
| Max daily loss | ₹1,500 (3%) | `risk.max_daily_loss_pct` |
| Stop loss | 0.4% | `trading.stop_loss_pct` |
| Max trades/day | 2 | `trading.max_trades_per_day` |

**`live_risk.json` जान-बूझकर नहीं बनाई गई** — बनाने पर वह `ai_config.json` को चुपचाप override करने लगती, यानी सच्चाई के दो स्रोत बन जाते और आगे `ai_config.json` में किया बदलाव बेअसर लगता। जब live tuning की ज़रूरत हो, dashboard से बनवाएँ।

---

## ⚠️ ध्यान रहे

- `ENVIRONMENT=PAPER_TRADING` — असली पैसा अभी नहीं लगा है। दो जगह से पुष्टि: `config/credentials.env` में लिखा है, और कोड का default भी वही है (`os.getenv('ENVIRONMENT', 'PAPER_TRADING')` — `main.py:626`, `src/executor.py:13`)। ध्यान दें कि `tradekaro-bot.service` में यह variable सेट **नहीं** है; बचाव सिर्फ़ इन दो बातों से है।
- **live जाने से पहले #6 (broker login) ठीक होना चाहिए, और dashboard चालू करना हो तो #1 (पासवर्ड सेट करना)।**
- `delta_options_wide` को अभी कोई कोड पढ़ता नहीं — सिर्फ़ लिखा जा रहा है (रोज़ ~2.5 लाख rows)।

### 🔴 आपातकालीन स्टॉप कैसे करें

**फ़ोन से:** Telegram पर **@tradekaro_ai_bot** को ठीक यही लिखें — `KILL ALL`
(सिर्फ़ ID `588880549` से चलेगा; किसी और का संदेश अनदेखा होगा।)

**सर्वर से:**
```bash
cd /var/www/tradekaro/Trading_AI_Project && venv/bin/python kill_switch.py
```

दोनों हालात में: सभी खुली positions बंद होंगी और **बॉट बंद ही रहेगा**।
दोबारा चालू करने के लिए: `systemctl start tradekaro-bot`

### सेवाएँ

| Service | काम |
|---|---|
| `tradekaro-bot` | मुख्य ट्रेडिंग बॉट |
| `tradekaro-telegram` | "KILL ALL" सुनता है |
| `tradekaro-web` | Dashboard — **अब भी बंद**, पर अब login लग चुका है। चालू करने से पहले `scripts/set_dashboard_password.py` चलाएँ (वरना हर route 503 देगा) |
| `tradekaro-brain` | disabled — `main.py` ही चलाती है, यानी `tradekaro-bot` की नक़ल। दोनों एक साथ चलें तो एक ही बॉट दो बार चलेगा। जान-बूझकर बंद है |

### रोज़ का backup

`/etc/cron.d/tradekaro-backup` → रोज़ 21:00 UTC (02:30 IST) `/root/tradekaro_backup.sh`।
नतीजा: `/var/backups/tradekaro/backup.log` (`THIK` / `GALAT`), फ़ाइलें `daily/` में।
