# 🤖 JOBS_AGENT — "job" लिखते ही पूरा नौकरी-अपडेट

यह file किसी भी AI agent (Claude Code, Cursor, Codex, Gemini CLI …) के लिए पूरा निर्देश है।
**इस्तेमाल:** repo को AI agent में खोलें और लिखें:

```
job
```

या पूरा: `JOBS_AGENT.md पढ़ो और job चलाओ`.

> AI के लिए: अगर user का message सिर्फ़ `job` (या "job update", "नौकरी अपडेट") है, तो नीचे
> **चरण 0 से 8** बिना और कुछ पूछे क्रम से पूरे करें और अंत में चरण 8 वाली रिपोर्ट दें।
> सभी commands `study_station/v2/` folder से चलाएँ।

---

## कड़े नियम (हर चरण में)

1. **हर तथ्य official स्रोत से।** तारीख़, पद, उम्र, योग्यता सिर्फ़ भर्ती करने वाली संस्था की अपनी
   website/PDF से। Official = `*.gov.in`, `*.nic.in`, `*.ac.in`, `*.edu.in`, `*.res.in` या
   `app/jobs/sources.py` की `OFFICIAL_HOSTS` सूची (IBPS, SBI, RBI, LIC, PSU …)।
2. **Aggregator (FreeJobAlert, SarkariResult, IndGovtJobs, Adda247, Naukri…) सिर्फ़ सुराग़ हैं।**
   वहाँ से सिर्फ़ यह जानें कि भर्ती आई है और official link कहाँ है। उनका लिखा कुछ भी copy न करें।
   Naukri.com जैसी sites को scrape न करें।
3. **DB में खुद कुछ न लिखें, न edit करें।** हर बदलाव नीचे दिए CLI commands से — वही official
   link खोलकर facts पढ़ते हैं, duplicates मिलाते हैं, और गैर-official link मना कर देते हैं।
4. **कुछ भी अनुमान से न भरें।** official link न मिले तो उसे छोड़ दें और रिपोर्ट में लिखें।
5. robots.txt और site की शर्तें मानें; login/captcha वाले pages न खोलें; secrets (`.env`) कहीं print न करें।

---

## चरण 0 — तैयारी

```bash
cd study_station/v2
test -d venv || python3 -m venv venv
source venv/bin/activate
pip install -q -r requirements.txt
python -m app.seed >/dev/null 2>&1 || true      # पहली बार DB बनाता है; दोबारा चलाना सुरक्षित
```

## चरण 1 — सभी official sources + RSS से automatic sweep

```bash
python -m app.jobs run
python -m app.jobs health
```

`health` में जो source `FAIL` दिखे, उसे चरण 7 के लिए नोट करें।

## चरण 2 — अभी की हालत पढ़ें

```bash
python -m app.jobs summary
```

इससे मिलता है: खुली भर्तियाँ, आने वाली, **`pending_need_official_link`** (जो भर्तियाँ सिर्फ़
aggregator पर दिखीं — इनका official link ढूँढना है), और **`broken_sources`**।

## चरण 3 — Research (⚡ समानांतर / parallel)

अगर आपका AI sub-agents / parallel tasks चला सकता है, तो नीचे की **6 lanes एक साथ** चलाएँ।
नहीं चला सकता तो एक-एक करके। **Lanes सिर्फ़ research करें — DB में कुछ न लिखें**
(SQLite एक समय में एक ही writer संभालता है; लिखने का काम चरण 4 में मुख्य agent करेगा)।

| Lane | संस्थाएँ (official sites) |
|---|---|
| A. केंद्रीय आयोग | SSC (ssc.gov.in), UPSC (upsc.gov.in) |
| B. रेलवे | RRB (rrbapply.gov.in, rrbcdg.gov.in …), RRC zones, metro rail corporations |
| C. बैंक / बीमा | IBPS (ibps.in), SBI (sbi.co.in), RBI (rbi.org.in), NABARD, LIC, NIACL, सरकारी बैंक |
| D. रक्षा / पुलिस | Army/Navy/Air Force (Agniveer), CAPF (BSF, CRPF, CISF, ITBP, SSB), राज्य पुलिस भर्ती बोर्ड |
| E. राज्य आयोग | UPPSC, UPSSSC, BPSC, BSSC, RPSC, RSMSSB, MPPSC, MPESB, HPSC, HSSC, DSSSB, … (पहले हिंदी-भाषी राज्य) |
| F. PSU / संस्थान | ISRO, DRDO, BARC, NTPC, ONGC, BHEL, IOCL, AAI, PowerGrid, AIIMS, IIT/NIT |

हर lane यह करे:
1. पिछले **7 दिनों** में आए नए **भर्ती notices / advertisements** — official site पर।
2. चरण 2 की `pending_need_official_link` सूची में से अपनी lane वाली भर्तियों का **official notice/PDF link**।
3. संस्था का **official exam calendar** (SSC, UPSC, RRB, IBPS हर साल छापते हैं) — अगले 90 दिनों
   में जिन परीक्षाओं का notification अपेक्षित है।

हर lane **ठीक इसी format** में जवाब दे (कुछ और नहीं):

```
ADD | <official notice/PDF URL> | <title as written by the board> | <org short name> | <category>
UPCOMING | <exam name + year> | <org> | <YYYY-MM अपेक्षित notification> | <official calendar URL> | <category>
NOT_FOUND | <title> | <कारण>
```

`category` = `ssc` / `railway` / `banking` / `defence` / `psc` / `psu` / `teaching` / `govt`

## चरण 4 — Research लागू करें (मुख्य agent, एक-एक करके)

```bash
# हर ADD पंक्ति के लिए
python -m app.jobs add "<URL>" --title "<title>" --org "<org>" --category <category>

# हर UPCOMING पंक्ति के लिए
python -m app.jobs upcoming --title "<exam>" --org "<org>" --expected <YYYY-MM> --source "<calendar URL>" --category <category>
```

`FAILED: not an official domain` आए तो वह link official नहीं है — सही official link ढूँढें या छोड़ दें।

## चरण 5 — जो ख़त्म हो चुका, हटाएँ

```bash
python -m app.jobs cleanup
```

यह अपने-आप हटाता है: 30 दिन से ज़्यादा पहले बंद हुई भर्तियाँ · 30 दिन से पुराने बिना-पुष्टि वाले items ·
90 दिन पुराने admit card/result/answer key · जिन "आने वाली" भर्तियों का असली notification आ गया या
अपेक्षित तारीख़ 60 दिन पहले निकल गई। (अंतिम तिथि निकलते ही भर्ती "खुली" से हटकर "बंद" tab में चली जाती है।)

## चरण 6 — Notification / Alert

```bash
mkdir -p reports
python -m app.jobs digest --out reports/jobs-$(date +%F).md
```

अगर `.env` में `TELEGRAM_BOT_TOKEN` और `TELEGRAM_CHANNEL_ID` हैं, तो भेजें और दोहराव रोकें:

```bash
python -m app.jobs digest --telegram --mark-sent
```

(`--mark-sent` सिर्फ़ तभी, जब message सच में चला गया हो। "जल्द बंद हो रही" वाली भर्तियाँ अंतिम तिथि
तक हर बार याद दिलाई जाती हैं।)

## चरण 7 — टूटे sources ठीक करें

`health` में जो source लगातार **3 या ज़्यादा बार** FAIL हो:
1. उसकी official site खोलकर देखें — URL बदला? page का ढाँचा बदला? site बंद?
2. URL बदला हो तो `app/jobs/sources.py` की `SOURCES` सूची में सुधारें। नया board जोड़ना हो तो वहीं एक पंक्ति:
   `HtmlListingSource('hssc', 'https://hssc.gov.in/…', 'HSSC', 'psc')`
3. `python -m pytest tests -q` चलाएँ — सब pass होने चाहिए।
4. `python -m app.jobs run --only <source>` से जाँचें।
5. Code बदला हो तो एक साफ़ commit बनाएँ (git की अनुमति हो तभी)। कोई source चुपचाप बंद न करें।

> कई सरकारी sites सिर्फ़ भारत के IP से खुलती हैं। Agent भारत के बाहर चल रहा हो तो
> "Connection reset" आम है — उसे टूटा हुआ न मानें, रिपोर्ट में लिखें।

## चरण 8 — User को रिपोर्ट (हिंदी में, छोटी)

```
✅ नौकरी अपडेट — <तारीख़>
• खुली भर्तियाँ: <संख्या>  (नई: <संख्या>)
• जल्द बंद (3 दिन): <सूची: नाम — अंतिम तिथि>
• आने वाली (90 दिन): <सूची: नाम — अपेक्षित महीना>
• हटाई गईं: <cleanup की संख्याएँ>
• official link नहीं मिला: <सूची>
• टूटे sources: <सूची + कारण>
• Alert: <Telegram भेजा / नहीं (कारण)>
• Report file: reports/jobs-<तारीख़>.md
```

---

## AI के पास terminal न हो तो (ChatGPT/Gemini जैसे chat)

चरण 3 की research करके सिर्फ़ `ADD | …` / `UPCOMING | …` / `NOT_FOUND | …` पंक्तियाँ दें। User उन्हें
`study_station/v2/` में चरण 4 के commands से चला देगा। तथ्य (तारीख़/पद) अपने जवाब में न लिखें — वे
command official PDF से खुद पढ़ लेता है।

## Automatic (बिना AI के) — VPS cron

```
17 */3 * * * cd /var/www/study_station/v2 && ./venv/bin/python -m app.jobs run >> /var/log/studystation-jobs.log 2>&1
30 3 * * *   cd /var/www/study_station/v2 && ./venv/bin/python -m app.jobs cleanup >> /var/log/studystation-jobs.log 2>&1
0 8,18 * * * cd /var/www/study_station/v2 && ./venv/bin/python -m app.jobs digest --telegram --mark-sent >> /var/log/studystation-jobs.log 2>&1
```

Cron रोज़ का काम करता है; `job` वाला AI-run गहरी research (नए boards, pending links, exam calendars)
और टूटे sources की मरम्मत के लिए है — हफ़्ते में 2–3 बार काफ़ी है।
