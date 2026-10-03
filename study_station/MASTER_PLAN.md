# 🚀 Study Station — World-Class Master Plan (v1.0)

**तारीख़:** 14 जुलाई 2026

## 📈 Progress (14 जुलाई 2026)
- ✅ **Phase 1 पूरा:** नकली job data हटा (125 jobs साफ़), scraper v2 (असली detail extraction), design एकीकृत (147+ job pages नए design पर), झूठे stats हटे, secrets .env में, hardcoded Gemini key हटी (⚠️ key rotate करें!)
- ✅ **Phase 2 ~80%:** 4 RSS sources, auto-expiry, real-data backfill (131 jobs), scheduler files (`SCHEDULER_SETUP.md` — user को schtasks command चलानी है), days-left badge, SPA अब असली jobs दिखाता है (`js/jobs_data.js`), fake PYQ demo data हटा
- ✅ **246 jobs DB में — 207 (84%) में असली dates, 166 में असली eligibility**
- ✅ Phase 3 शुरू: zero-width space cleanup (70→0), 22 chapters rebuilt
- ✅ Phase 5 शुरू: Android BASE_URL build variants, release में HTTP logging बंद
- ⏳ बाक़ी: और sources, Chapter 1 gold standard, MCQ verification, PWA, SEO meta, deploy, real PYQ PDFs
**लक्ष्य:** Study Station को एक world-class EdTech platform बनाना — Website + Android App दोनों — जिसमें AI-निर्मित किताबें, PYQ-आधारित practice, और सरकारी नौकरियों का auto-updating feed हो।

---

## भाग 1: वर्तमान स्थिति का Audit (क्या-क्या मिला)

### ✅ जो अच्छा है (हमारी ताक़त)
| हिस्सा | स्थिति |
|--------|--------|
| Books engine | 22 chapters (10th Math) पूरे raw content के साथ — Content, Feynman, Flashcards, Mind Map, PYQ, 6 Practice Sets, Short Tricks — हिंदी+English दोनों में |
| Website | Modern design (dark theme, glassmorphism), book reader, jobs pages, PYQ page |
| Backend | Flask + SQLAlchemy, admin panel, job scraper, Telegram bot, SSG builder |
| Android app | Native Kotlin + Jetpack Compose + Hilt + Room — dashboard, focus timer, gamification, jobs, practice, study features |
| Database design | SM-2 spaced repetition, PYQ weightage analysis जैसे advanced models पहले से मौजूद |

### 🔴 गंभीर समस्याएँ (Critical — सबसे पहले ठीक करना है)

**J1. Jobs में नकली data भरा जा रहा है** — `job_scraper.py` (line 122–150) हर job में hardcoded नकली dates डालता है ("Application Begin: 01/05/2026", fees, age limit सब fake)। छात्र इसे सच मानकर form भरने की तारीख़ miss कर सकता है। **यह trust को हमेशा के लिए ख़त्म कर देगा।**

**J2. Jobs में सिर्फ़ title + link आता है** — RSS से केवल शीर्षक मिलता है; असली details (vacancy, eligibility, असली dates) कभी fetch नहीं होतीं।

**J3. कोई auto-refresh नहीं** — scraper manually चलाना पड़ता है। कोई scheduler नहीं। Jobs कभी expire भी नहीं होतीं (last date निकल जाने के बाद भी दिखती रहती हैं)।

**W1. Website में दो अलग-अलग design systems** — `index.html` नया design (`navbar__`) इस्तेमाल करता है, जबकि 147+ job pages पुराना design (`glass-nav`) — user को दो अलग websites जैसा अनुभव मिलता है। Job pages के nav में `practice.html` जैसे टूटे links भी हैं।

**A1. Android app असली फ़ोन पर काम ही नहीं करेगा** — `NetworkModule.kt` में `BASE_URL = "http://10.0.2.2:5000/api/"` (सिर्फ़ emulator का localhost)। कोई live backend host नहीं है।

**B1. Backend कहीं deploy नहीं है** — SQLite + local Flask। जब तक यह online नहीं होगा, न app में jobs आएँगी, न website auto-update होगी।

### 🟡 बड़ी कमियाँ (High Priority)

**K1. किताबों की quality अधूरी** — `implementation_plan.md` की समस्याएँ आंशिक रूप से ही ठीक हुई हैं:
- MCQ solutions कटे हुए (multi-step हल का सिर्फ़ पहला step)
- Vertical fractions (`1` अलग line, `2` अलग line) — अर्थहीन rendering
- Encoding गड़बड़ (`÷` गलत जगह, zero-width spaces)
- 150 MCQs × 22 chapters का गणितीय verification कभी नहीं हुआ
- Mind Maps में "Mermaid rendering failed" text

**K2. सिर्फ़ 10th Math live है** — 12th Level और Graduation Level की सारी folders खाली हैं। 10th में भी English/GK/Hindi/Reasoning खाली।

**W2. SEO लगभग शून्य** — sitemap.xml नहीं, robots.txt नहीं, SPA navigation (Google pages को ठीक से index नहीं कर पाएगा), job pages की meta description generic।

**W3. सब कुछ external CDN पर** — Google Fonts, Ionicons, Mermaid सब CDN से। धीमे internet (हमारी core audience!) पर site टूटी दिखती है। PWA/offline support नहीं है।

**W4. झूठे आँकड़े** — Homepage पर "10,000+ Active Students" लिखा है जबकि launch भी नहीं हुआ। Play Store/AdSense review में यह पकड़ा जाता है।

**S1. Secrets repo में** — `telegram_config.py` में bot token हार्डकोड होने की आशंका; deploy से पहले environment variables में ले जाना होगा।

---

## भाग 2: Master Plan — 6 Phases

> क्रम सोच-समझकर रखा है: पहले भरोसा (नकली data हटाओ), फिर engine (jobs + books), फिर polish (UI/UX), फिर distribution (app + deploy), अंत में growth।

---

### 🔴 Phase 1: Foundation & Trust Fix (सबसे पहले — 1-2 दिन)

1. **नकली job data हटाना**
   - `job_scraper.py` से hardcoded dates/fees/age हटाना
   - जो field असली में नहीं मिला, वहाँ "आधिकारिक अधिसूचना देखें" दिखाना — नकली value कभी नहीं
   - हर job page पर स्पष्ट disclaimer: "कृपया आवेदन से पहले आधिकारिक वेबसाइट पर पुष्टि करें" + official link प्रमुखता से
2. **झूठे stats हटाना** — "10,000+ students" जैसे दावों की जगह असली numbers (जैसे "220+ Chapters", "150 MCQs प्रति अध्याय", "Free Forever")
3. **Secrets बाहर निकालना** — Telegram token, API keys → `.env` + `.gitignore`
4. **Design system का एकीकरण शुरू** — एक ही CSS (नया `navbar__` वाला) हर generated page में; `build_website.py` का template नए design पर migrate

**परिणाम:** platform भरोसेमंद बन जाता है — बाक़ी सब इसी नींव पर बनेगा।

---

### 🟠 Phase 2: Sarkari Jobs Engine 2.0 — "Direct Fetch" (3-5 दिन)

आपकी माँग: *सरकारी portal की jobs अपने-आप fetch होकर दिखें।*

1. **Multi-source aggregation बढ़ाना**
   - मौजूदा 2 RSS स्रोतों के साथ और स्रोत जोड़ना (SarkariResult-type RSS, Employment News, राज्य-वार feeds)
   - National Career Service (ncs.gov.in) और data.gov.in जैसे आधिकारिक स्रोत evaluate करना
2. **Detail Extraction Pipeline (असली data)**
   - Step 1: RSS से नई job का link मिलते ही उस page का HTML fetch करना
   - Step 2: Structured extraction — असली dates, fees, vacancy, eligibility निकालना (पहले regex/heuristics से; जो न निकले वह field ख़ाली = "Official notification देखें")
   - Step 3: हर extracted job में `source_url` + `fetched_at` — पूरी traceability
3. **Job lifecycle management**
   - Last date निकलने पर job अपने-आप "Expired" section में
   - Duplicate detection (normalized title + URL)
   - Categories सुधारना: SSC / Banking / Railway / UPSC / State PSC / Police / Teaching / Defence
4. **Automation (scheduler)**
   - हर 2-3 घंटे में scraper चलाना (host पर cron / GitHub Actions)
   - नई job मिलते ही: DB → SSG rebuild → Telegram broadcast → (बाद में app push notification)
5. **Jobs UX**
   - Search + filter (category, qualification: 10th/12th/Graduate, राज्य)
   - "Latest Jobs / Result / Admit Card / Answer Key" tabs (SarkariResult pattern — पहले से model में है)
   - हर job पर "Days left" countdown badge

**परिणाम:** SarkariResult-जैसा auto-updating jobs section — लेकिन साफ़ design, बिना spam, हिंदी+English।

---

### 🟠 Phase 3: Books Engine — World-Class Content (1-2 सप्ताह)

`implementation_plan.md` v2.0 इसी का detailed blueprint है — उसे पूरा execute करना:

1. **`build_chapters.py` parser को अचूक बनाना**
   - Multi-step MCQ solutions पूरे capture (state machine)
   - Flashcards के सभी formats parse (अभी 15-20 में से 1 ही दिखता है)
   - Vertical fractions → inline (½, 1/2)
   - Encoding cleanup (÷, zero-width spaces)
2. **Chapter 1 को "Gold Standard" बनाना**
   - Content/Feynman की भाषा-सफ़ाई, अधूरे वाक्य पूरे
   - सभी 150 MCQs का उत्तर गणितीय रूप से verify
   - Mermaid mind map हर tab में render हो कर दिखना
   - नए visual components: definition-box, formula-box, examiner-trap, mnemonic-box, step-card
3. **Gold Standard को बाक़ी 21 chapters पर दोहराना** — automated pass + spot-check verification
4. **अगली किताबें pipeline में** — Reasoning और GK (raw content आंशिक मौजूद), फिर English; फिर 12th/Graduation levels
5. **Learning features activate करना** (models पहले से हैं!)
   - Active Recall prompts interactive बनाना (क्लिक करके उत्तर देखो)
   - SM-2 spaced repetition: "आज क्या दोहराना है" dashboard
   - PYQ weightage charts हर chapter में

**परिणाम:** ऐसी किताबें जो market में किसी के पास नहीं — मनोविज्ञान-आधारित, bilingual, PYQ-driven, बिल्कुल मुफ़्त।

---

### 🟡 Phase 4: Website World-Class (UI/UX + SEO + PWA) (1 सप्ताह)

1. **UI/UX एकीकरण**
   - सारे pages (jobs, books, PYQ) एक ही design system पर
   - Mobile-first polish: bottom nav सब pages पर, touch targets, font sizes
   - Loading skeletons, empty states, error states — हर जगह
   - Accessibility: contrast, focus states, हिंदी fonts का सही rendering
2. **Performance**
   - Fonts + icons self-host (CDN dependency ख़त्म)
   - Critical CSS inline, बाक़ी deferred
   - Lighthouse score लक्ष्य: 90+ सब categories में
3. **PWA (Progressive Web App)**
   - Service worker: एक बार खोली किताब offline भी पढ़ी जा सके
   - "Add to Home Screen" — बिना Play Store के भी app जैसा अनुभव
4. **SEO Overhaul**
   - sitemap.xml (auto-generated हर SSG build पर) + robots.txt
   - हर chapter/job page: unique title, meta description, Open Graph tags
   - Schema.org markup: Book, Chapter, JobPosting (JobPosting schema से Google Jobs में direct listing मिल सकती है!)
   - सही heading hierarchy (h1→h2→h3)
5. **Deploy**
   - Static site → Cloudflare Pages / GitHub Pages (free, fast, India में अच्छा CDN)
   - Backend (Flask API + scraper) → Render / Railway / छोटा VPS
   - Domain ख़रीदना (जैसे studystation.in)

**परिणाम:** तेज़, sundar, Google में rank करने वाली, offline-capable website।

---

### 🟡 Phase 5: Android App → Play Store (1-2 सप्ताह)

1. **Production API connection**
   - `BASE_URL` → live backend URL (build variants: debug=localhost, release=production)
   - Offline-first: Room में cache, network न हो तो cached data
2. **Books app के अंदर**
   - Chapters का JSON/HTML bundle app में (offline reading — हमारी core USP)
   - नए chapters का background download
3. **Jobs feed + Notifications**
   - Jobs list backend API से sync (WorkManager periodic sync)
   - नई job पर local notification ("नई SSC भर्ती आई है!")
4. **Existing features को next level पर**
   - Focus timer + streaks + gamification को books/practice से जोड़ना (chapter पूरा = XP)
   - Practice MCQs में SM-2 integration (गलत सवाल अपने-आप दोहराव में आएँ)
   - Dashboard पर "आज का plan": दोहराव + नया chapter + job alerts
5. **Play Store release**
   - App icon, screenshots, feature graphic, privacy policy page
   - Signed AAB, internal testing → production (organization account है, 20-tester नियम लागू नहीं)

**परिणाम:** Play Store पर live app — offline books + auto job alerts, दोनों USPs के साथ।

---

### 🟢 Phase 6: Growth & Monetization (चालू रहने वाला)

1. **Analytics** — self-hosted/privacy-friendly analytics (कौन-सा chapter सबसे ज़्यादा पढ़ा जाता है, कौन-सी job सबसे ज़्यादा खुलती है)
2. **Monetization** — AdMob (app) + AdSense (website) jobs pages पर; बाद में premium books (`is_premium` field तैयार है)
3. **Telegram channel growth** — हर job + हर नए chapter का auto-post
4. **Feedback loop** — हर chapter के नीचे "यह अध्याय कैसा लगा?" rating
5. **Content expansion** — 12th Level → Graduation Level → State-specific exams (Bihar SSC, UP Police...)

---

## भाग 3: क्रम और अनुमानित समय

| # | Phase | समय | निर्भरता |
|---|-------|-----|----------|
| 1 | Foundation & Trust | 1-2 दिन | — |
| 2 | Jobs Engine 2.0 | 3-5 दिन | Phase 1 |
| 3 | Books Gold Standard | 1-2 सप्ताह | Phase 1 (साथ-साथ चल सकता है) |
| 4 | Website World-Class | 1 सप्ताह | Phase 2, 3 |
| 5 | Android App + Play Store | 1-2 सप्ताह | Phase 2, 4 (backend live चाहिए) |
| 6 | Growth | निरंतर | Phase 4, 5 |

## भाग 4: आपसे क्या चाहिए (User Decisions)

1. **Hosting budget** — free tier (Render free + Cloudflare Pages) से शुरू करें या ₹300-500/माह का VPS? (free tier पर scraper में सीमाएँ रहती हैं)
2. **Domain name** — कौन-सा ख़रीदें? (studystation.in जैसा)
3. **App का अंतिम नाम** — "Study Station" या "Student Station"? (code में दोनों जगह अलग-अलग है — package `com.studentstation.app`, website "Study Station")
4. **Telegram bot token** — मौजूद है या नया बनाना है?
5. **AdMob/AdSense** — कब से शुरू करना है (launch पर या users आने के बाद)?

---

> **पहला कदम (आपकी "Approved" के बाद):** Phase 1 — नकली job data हटाना + design system एकीकरण। यही सबसे कम मेहनत में सबसे बड़ा सुधार है।
