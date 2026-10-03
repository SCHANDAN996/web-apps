# Study Station v2

सरकारी परीक्षा (SSC, Railway, Bank) की तैयारी — हिंदी और English में।
क्यों और क्या बनाया, यह [BLUEPRINT.md](BLUEPRINT.md) में है।

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

```bash
DATABASE_URL=sqlite:////var/lib/studystation/studystation.db \
SITE_URL=https://studystation.in \
uvicorn app.main:app --host 127.0.0.1 --port 8001 --workers 2 --proxy-headers
```
nginx के पीछे चलाएँ (HTTPS)। `DATABASE_URL` बदलकर PostgreSQL भी चलेगा।

## Content की हालत (import के बाद)

| | संख्या |
|---|---|
| इस्तेमाल लायक सवाल (`unreviewed`) | ~6,600 (Quant, Reasoning, GA, English-Noun) |
| हिंदी + English दोनों में | ~1,450 |
| छिपाए गए (`flagged`) | ~850 — AI की सोच हल में छूटी, हल और उत्तर में टकराव, या पिछले सवाल पर निर्भर |
| Jobs | 150 (पुराने feed से; सबकी अंतिम तिथि निकल चुकी — नया scraper Phase 2 में) |

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
tests/          importer + API tests
```
