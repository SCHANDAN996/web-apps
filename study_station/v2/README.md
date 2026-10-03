# Study Station v2

सरकारी परीक्षा (SSC, Railway, Bank) की तैयारी — हिंदी और English में।
क्यों और क्या बनाया, यह [BLUEPRINT.md](BLUEPRINT.md) में है।
काम करने वाले AI agents (developer, observer, QA, jobs, content…) और slash commands: [AGENTS.md](AGENTS.md)।

## चलाएँ (local)

```bash
cd study_station/v2
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m app.seed                       # catalogue + ../books के सवाल + पुरानी jobs
COOKIE_SECURE=0 uvicorn app.main:app --reload
# http://localhost:8000      API docs: http://localhost:8000/api/docs
pytest                                   # tests
```

`python -m app.seed` दोबारा चलाना सुरक्षित है — rows update होती हैं, duplicate नहीं।

## Production

पूरी गाइड और deploy के बाद का test checklist: **[DEPLOY.md](DEPLOY.md)** (`deploy/` में systemd, nginx, cron, backup, setup)।

## बाकी features

| Feature | कहाँ | चलाना |
|---|---|---|
| Admin panel (सवाल review, reports, pending jobs, sources) | `/admin` | `.env` में `SECRET_KEY` + `ADMIN_PASSWORD` |
| दूसरे फ़ोन पर progress (recovery code) | सेटिंग्स | — |
| AI tutor ("आसान भाषा में समझें") | अभ्यास/परिणाम/दोहराई | `ANTHROPIC_API_KEY` |
| नए सवाल बनाना (दोबारा जाँच के साथ) | `app/generate.py` | `python -m app.generate --fill --min 60` |
| करंट अफेयर्स (AIR + PIB) + हफ़्ते/महीने का क्विज़ | `/current-affairs` | `python -m app.current_affairs run` |

## Content की हालत (import के बाद)

| | संख्या |
|---|---|
| इस्तेमाल लायक सवाल (`unreviewed`) | ~6,600 (Quant, Reasoning, GA, English-Noun) |
| हिंदी + English दोनों में | ~1,450 |
| छिपाए गए (`flagged`) | ~850 — AI की सोच हल में छूटी, हल और उत्तर में टकराव, या पिछले सवाल पर निर्भर |
| Jobs | `python -m app.jobs run` से official स्रोतों से (नीचे देखें); पुराने feed की 150 jobs "legacy" label के साथ |

सभी सवाल AI से बने हैं और students को "AI से बना · समीक्षा बाकी" label के साथ दिखते हैं।
"PYQ" label तभी लगेगा जब `source_type='pyq'` और `source_ref` (exam + साल + shift) भरा हो।
Students "गलती बताएँ" से गलत सवाल report कर सकते हैं (`question_report` table)।

## ढाँचा

```
app/
  catalog.py    विषय, टॉपिक, exam patterns (official notification से मिलाकर)
  importers.py  पुराने MCQ text files का parser + quality checks
  seed.py       सब कुछ DB में लोड
  models.py     SQLAlchemy models
  services.py   practice, CBT mock, scoring, Leitner revision, stats, jobs
  main.py       FastAPI: /api/v1/* JSON + server-rendered pages
  i18n.py       UI strings (हिंदी पहले)
  templates/    Jinja pages
  static/       CSS design system, JS player, service worker
  jobs/        job engine: sources, polite fetcher, notice parser, pipeline, CLI
tests/          importer, API and job-engine tests (fixtures = trimmed real pages)
```

## नौकरियाँ (Job engine) — `app/jobs/`

**सिद्धांत:** किसी एक website पर निर्भरता नहीं, और हर तथ्य official स्रोत से।

| परत | स्रोत | काम |
|---|---|---|
| Official | SSC API, ISRO, UPPSC, LIC, UPSC, IBPS, RRB, BPSC, RPSC, MPPSC, DSSSB … (`sources.py` → `SOURCES`) | भर्ती की असली सूचना। तारीख़, पद, उम्र यहीं के PDF/page से पढ़ी जाती है |
| Discovery | FreeJobAlert, IndGovtJobs के public RSS | सिर्फ़ "नई भर्ती आई है" का संकेत + official PDF का link ढूँढना। उनका लिखा content कभी नहीं दिखाते |

हर item → classify (भर्ती / admit card / result / answer key / सामान्य notice) → official PDF खोलकर
facts निकालना (`extract.py`, हिंदी + English) → duplicates मिलाना (advt no., title, official domain) →
`verified` (official नोटिस से पढ़ा) या `pending` (अभी सिर्फ़ aggregator ने बताया — students को नहीं दिखता)।
कोई site down हो तो बाकी चलते रहते हैं; `source_health` table हर source का हाल रखती है।

```bash
python -m app.jobs run                    # सब sources
python -m app.jobs run --only ssc,isro    # कुछ ही
python -m app.jobs run --dry-run          # DB में कुछ न लिखे
python -m app.jobs health                 # कौन सा source चल रहा है / टूटा है
```

Cron (हर 3 घंटे, VPS पर — कई सरकारी sites सिर्फ़ भारत के IP से खुलती हैं):
```
17 */3 * * * cd /var/www/study_station/v2 && ./venv/bin/python -m app.jobs run >> /var/log/studystation-jobs.log 2>&1
```

**नया board जोड़ना:** ज़्यादातर सरकारी sites के लिए `SOURCES` में एक लाइन काफ़ी है:
`HtmlListingSource('hssc', 'https://hssc.gov.in/...', 'HSSC', 'psc')`. JavaScript से बनने वाले pages
(जैसे RBI, SBI) पर generic parser काम नहीं करता — वे भर्तियाँ discovery के रास्ते official PDF से आती हैं।

**AI से पूरा अपडेट:** [JOBS_AGENT.md](JOBS_AGENT.md) — किसी भी AI agent में सिर्फ़ `job` लिखें; वह sweep, research (parallel lanes), official links जोड़ना, cleanup और alert digest खुद करता है।

```bash
python -m app.jobs summary | add URL | upcoming … | cleanup | digest [--telegram --mark-sent]
```

**शिष्टाचार:** robots.txt माना जाता है, हर host पर 2 सेकंड का अंतर, साफ़ User-Agent, 12 MB की सीमा, और
एक item सिर्फ़ एक बार process होता है (`seen_item`)। Naukri.com जैसी private job sites को scrape नहीं
करते — उनकी शर्तें मना करती हैं; private नौकरियों के लिए उनका official API/partner feed लें।
