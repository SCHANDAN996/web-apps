# Study Station v2 — notes for AI agents

Government-exam prep (SSC, Railway, Bank) for Hindi-first learners on cheap Android phones.
Why it is built this way: `BLUEPRINT.md`. Agent roster and which one to use: `AGENTS.md`.

## Map
```
app/main.py         FastAPI: /api/v1/* JSON + server-rendered pages (Jinja)
app/services.py     practice, CBT mock scoring, Leitner revision, stats, job queries
app/models.py       SQLAlchemy models (schema grows additively via db.ensure_schema)
app/catalog.py      subjects, topics, exam patterns            app/i18n.py   UI strings (hi, en)
app/importers.py    old MCQ text parser + quality checks       app/seed.py   load catalogue/questions/jobs
app/admin.py        /admin panel                               app/sync.py   recovery-code progress sync
app/ai.py           Claude: tutor, MCQ generator               app/generate.py  CLI for the generator
app/current_affairs.py  AIR/PIB feeds → items + MCQs           app/observe.py   health/metrics (read-only)
app/review.py       question review CLI                        app/bookcheck.py  book chapter check (../books)
app/jobs/           job engine (sources, extract, pipeline, manage, CLI)
templates/, static/ design system (css/app.css tokens), js/app.js, js/player.js, sw.js
tests/              pytest (fixtures = trimmed real pages), tests/e2e/flow.mjs (Playwright)
deploy/             systemd, nginx, cron, backup, setup         JOBS_AGENT.md  the "job" runbook
```

## Commands (run from `study_station/v2/`; on the server prefix with `deploy/run.sh`)
```
pytest -q                                   # must stay green
BASE_URL=http://localhost:8000 node tests/e2e/flow.mjs
COOKIE_SECURE=0 uvicorn app.main:app --reload
python -m app.seed                          # safe to re-run
python -m app.observe [--markdown]          # health; exit 0 ok / 1 warn / 2 critical
python -m app.jobs run|health|summary|add URL|upcoming|cleanup|digest
python -m app.current_affairs run
python -m app.review list|show|apply|stats
python -m app.bookcheck ../books/<Level>/<Subject>/<Book>   # OK / TODO / FIX per chapter
python -m app.generate --topic ga/polity --n 10 | --fill --min 60
```

## Non-negotiable rules
1. **Facts only from official sources.** Job dates/posts/age come from the board's own notice
   (`*.gov.in`, `*.nic.in`, listed hosts in `app/jobs/sources.py`). Aggregators = discovery only;
   never copy their text. Current affairs only from AIR/PIB. No invented numbers, users, ranks or PYQs.
2. **"PYQ" label only with a source** (exam + year + shift). AI-made questions stay labelled until reviewed.
3. **Write data through the CLIs / app code**, never by editing the DB by hand. One writer at a time
   (SQLite): parallel agents research; one agent applies.
4. **Both languages.** Every UI string goes in `app/i18n.py` as (hi, en). Hindi is the default.
5. **Design system** (Material Design 3, see `DESIGN.md`). Use tokens in `static/css/app.css` (colour, spacing, radius, `--dur-*`, `--ease-*`);
   motion on transform/opacity only; respect `prefers-reduced-motion`; 44px touch targets; no CDN assets.
6. **Security.** Escape all external text (Jinja autoescape; `SS.h()` in JS — never innerHTML with data);
   API POSTs are JSON-only; admin needs `SECRET_KEY` + `ADMIN_PASSWORD`; no secrets in code or logs.
7. **Tests with every change**: add/adjust pytest; run `pytest -q`; for UI run the e2e flow and look at a
   phone-size screenshot. Never skip or delete a failing test to get green.
8. **Be polite to websites**: robots.txt, identifying User-Agent, rate limits — never disguise the bot.
9. Git: small commits with clear messages; never commit `.env`, DB files, or screenshots.

## Gotchas
- Many government sites block non-Indian IPs: a "Connection reset" from a cloud agent is not a broken source.
- PIB's firewall rejects non-browser clients; AIR feeds carry full text.
- Old MCQ files: hi and en sets are often *different* questions — pair only via `is_translation_pair`.
- Days are IST (`services.today_ist()`), not UTC.
