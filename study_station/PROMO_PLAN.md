# 📣 PROMO_PLAN — Telegram auto-posting + auto Shorts/Reels (handoff for the next chat)

> **मालिक के लिए:** नई chat में बस यह लिखें:
> ```
> study_station/PROMO_PLAN.md पढ़ो और Part A (Telegram) से काम शुरू करो
> ```
> (या `Part B (Shorts) से` — दोनों अलग-अलग हैं।) AI पहले "मालिक को क्या करना है" वाले कदम बताएगा, फिर बाकी ख़ुद करेगा।

---

## 0. Context the next AI must know (read first)

- Repo `SCHANDAN996/web-apps`, work branch **`claude/elegant-rubin-sgov1q`** (never push to `main` except
  `.github/workflows/*` when the owner allows it; never force-push). App code: `study_station/v2`
  (FastAPI + Jinja + SQLite). Read `study_station/v2/CLAUDE.md` (rules) and `study_station/START_HERE.md`.
- **The site is NOT live yet** (no VPS). So everything in this plan must work **without the server**:
  content comes from the **book files in the repo**, and jobs run on **GitHub Actions** (repo is public →
  free minutes). When the site goes live, links switch from the Telegram channel to the site (one env var).
- Books: `study_station/books/<Level>/<Subject>/<Book>/Chapter_NN_*/` — practice sets
  `Practice_en_Set_0N.txt` / `Practice_hi_Set_0N.txt` (25 MCQs each, hi = exact translation, same answer
  letters), plus `Short_Tricks_*`, `Memory_Hooks_*`, `Key_Facts_*`, `Flashcards_*`. Parse MCQs with
  `app.importers.parse_mcq_text(text)` → `ParsedQuestion(number, text, options[4], answer_index, solution,
  source_claim, difficulty)`. A chapter is publishable only if `python -m app.bookcheck <chapter>` prints OK.
  All books are written by the NVIDIA autopilot (`.github/workflows/book-autopilot.yml`), every practice key
  re-solved by a second model and every section reviewed — but they are still `status: "draft"`.
- Existing Telegram sender: `app/jobs/manage.py::send_telegram(text)` (env `TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_CHANNEL_ID`; never logs the token). Existing job digest: `python -m app.jobs digest --telegram`
  (needs the DB → only after the site is live; see A.6).
- Secrets live only in GitHub repo secrets (Settings → Secrets and variables → Actions). Never in code,
  logs, commits or chat replies. Existing secrets: `NVIDIA_API_KEY`, `NVIDIA_API_KEY_2`.
- Owner works **only from a mobile phone** and speaks Hindi/Hinglish. Give steps a phone can do.

### Strict rules for both parts
1. **Only correct content goes out.** Use questions only from chapters where `bookcheck` = OK, and skip any
   question `quality_problem(q)` flags. One wrong answer that goes viral costs more than 100 good posts.
2. **No repeats:** keep a posted-log in the repo (`study_station/promo/posted.json`, ids like
   `12th_Level/GK/.../Chapter_05_Polity#Set02#Q37`) and never post the same item twice.
3. **Readable on a phone:** question ≤ 250 chars, each option ≤ 80 chars (Telegram poll limits are 300/100),
   no "figure/diagram/table/passage" questions (`NEEDS_CONTEXT` in `app/importers.py`), no "both (a) and (b)".
4. **Hindi first** (hi file), English terms kept in brackets; English-grammar questions keep the English sentence.
5. **No invented claims** in captions ("100% selection", "asked in SSC 2024" — never, unless an official source).
6. Every new module has pytest tests; `pytest -q` stays green; commit small, push to the work branch.

---

## Part A — Telegram channel, fully automatic

### A.1 What the owner does (phone, ~10 min) — ask for these first
1. Telegram → **New Channel** → name e.g. "Study Station — SSC/Railway/Bank (Hindi)" → **Public**, link
   e.g. `t.me/studystation_hindi` (owner picks).
2. Open **@BotFather** → `/newbot` → name + username → copy the **bot token**.
3. Channel → Administrators → **Add Admin** → the bot → allow "Post messages".
4. GitHub → repo Settings → Secrets → Actions → add `TELEGRAM_BOT_TOKEN` (token) and
   `TELEGRAM_CHANNEL_ID` (`@studystation_hindi`). Never paste the token in chat.
5. Give the AI permission to add a new workflow on `main` (`.github/workflows/promo-telegram.yml`).

### A.2 Daily schedule (IST) — each slot is one CLI call
| Time | Slot | Content | Telegram API |
|---|---|---|---|
| 07:30 | `quiz` | 5 quiz polls (1 per subject: GK, Reasoning, Maths, English, + rotating), easy→medium | `sendPoll` type=quiz, `correct_option_id`, `explanation` (≤200 chars) |
| 12:30 | `trick` | 1 short trick / memory hook card from `Short_Tricks_hi` / `Memory_Hooks_hi` (≤ 900 chars) | `sendMessage` (HTML) |
| 18:00 | `quiz` | 5 more polls (different topics) | `sendPoll` |
| 20:30 | `revision` | "आज के 10 सवालों के उत्तर + हल" recap (links to the poll messages) | `sendMessage` |
| Sun 10:00 | `weekly` | 20-question weekly test as polls + score-yourself note | `sendPoll` ×20 (1/sec) |
| after site live | `jobs` | `python -m app.jobs digest --telegram --mark-sent` (already built) 09:00 & 19:00 | `sendMessage` |

Rotate books/levels: Mon/Thu 10th, Tue/Fri 12th, Wed/Sat Graduation, Sun mixed. Max 20 msgs/minute
(Telegram limit) → sleep 1.5 s between sends.

### A.3 Code to build
- `study_station/v2/app/promo/__init__.py`, `__main__.py` (CLI):
  `python -m app.promo telegram --slot quiz|trick|revision|weekly [--dry-run] [--date YYYY-MM-DD]`
- `app/promo/pick.py` — **content picker from the books** (no DB):
  - walk `books/QUEUE.txt` books → chapters with bookcheck OK → parse `Practice_hi_Set_*` (+ en for
    cross-check: same answer_index) → filter by rules 1–4 → exclude posted ids → choose by
    `(date, slot)`-seeded RNG so `--dry-run` and the real run pick the same items.
  - tricks: split `Short_Tricks_hi.txt` / `Memory_Hooks_hi.txt` on headings (`## `, `### `, numbered
    "ट्रिक N"), keep 200–900 char blocks.
- `app/promo/telegram.py` — `send_poll(question, options, correct, explanation)`, `send_html(text)`;
  reuse the error handling of `send_telegram` (never print the URL/token). Escape HTML (`html.escape`).
- `app/promo/posted.py` — load/save `study_station/promo/posted.json` (atomic write), keep last 20k ids.
- Message footer (constant): `📚 रोज़ 10 मुफ़्त सवाल · {PROMO_LINK}` where `PROMO_LINK` env =
  the channel link now, the site URL with `?utm_source=telegram` later.

### A.4 Workflow `.github/workflows/promo-telegram.yml` (on `main`, needs owner's OK)
- `schedule:` crons in **UTC** for the IST times above (IST = UTC+5:30, e.g. 07:30 IST = `0 2 * * *`),
  plus `workflow_dispatch`.
- checkout books branch → `pip install -r study_station/v2/requirements.txt` →
  `python -m app.promo telegram --slot <slot>` → commit `study_station/promo/posted.json` back to the
  books branch (`git pull --rebase` + push retry, like `book_autopilot.py` does).
- `concurrency: promo-telegram` so two slots never post at once.

### A.5 Tests (pytest)
picker never returns a flagged/too-long/figure question; hi/en answer letters agree; no repeats across
two runs; seeded choice is stable; telegram client builds the right payload (mock `httpx.post`);
token never appears in raised errors.

### A.6 After the site is live
Turn on the `jobs` slot (job digest, already built and tested) and set `PROMO_LINK` to the site.
Add "आज का पूरा mock test → site link" once a day.

### A.7 Done means
Dry-run prints tomorrow's 10 polls + trick; one manual `workflow_dispatch` posts to the real channel;
the posted-log commit appears on the books branch; schedule runs for 2 days without a duplicate.

---

## Part B — Auto Shorts / Reels from the question bank

### B.1 Honest constraints (tell the owner)
- **YouTube auto-upload:** YouTube Data API uploads from an *unverified* Google Cloud project are forced to
  **private** until Google's API audit passes (weeks). **Instagram** auto-publishing needs a Business
  account + Facebook Page + Meta app review. → **Start with auto-generate + owner uploads from phone**
  (YouTube app / **Meta Business Suite** app lets you schedule a week of Reels in one sitting, free).
  Auto-upload is phase 3.
- Template videos (text on screen, no realistic AI people/voices) do **not** need YouTube's
  "altered or synthetic content" label. If AI voices/faces are added later, disclose them.
- Google Flow / Veo clips: only for a channel intro/trailer, not daily content (paid credits, 8-sec clips).

### B.2 Video format (9:16, 1080×1920, 20–30 s, no voice in v1)
1. 0–2 s **hook**: "SSC/Railway में पूछा जाने वाला सवाल 👇" (exam names only as generic audience, never as a
   claim that this exact question was asked).
2. 2–9 s **question** (big Devanagari text, max ~5 lines) + 4 options (A–D).
3. 9–14 s **countdown 5…1** (animated ring) — "comment में उत्तर लिखो".
4. 14–20 s **answer** highlighted green + 1–2 line solution/trick.
5. 20–24 s **CTA**: "रोज़ ऐसे 10 सवाल → Telegram: t.me/…" + channel handle.
Background: brand colours from `v2/DESIGN.md` (primary #1A73E8 family), light theme, high contrast.
Font: **Noto Sans Devanagari** (OFL; download in CI or commit under `study_station/promo/fonts/`).
Audio v1: silent or one royalty-free/CC0 loop committed to the repo (record its licence in `promo/README`).

### B.3 Code to build
- `app/promo/shorts.py` — `python -m app.promo shorts --count 3 [--level 12th] [--out DIR]`
  - reuse `pick.py` (same rules + its own posted-log key `shorts`), prefer questions ≤ 160 chars,
    options ≤ 40 chars, difficulty easy/medium.
  - render frames with **Pillow** (text wrap that measures Devanagari width; auto-shrink font to fit;
    refuse the question if it still does not fit), assemble with **ffmpeg** (H.264, 30 fps, AAC silent
    track, `-movflags +faststart`).
  - write per video: `NN.mp4`, `NN.txt` = title (≤ 90 chars, Hindi), description (question + answer +
    channel link + 5 hashtags e.g. `#SSC #RailwayExam #GKinHindi #Shorts #StudyStation`).
- Test: a rendered frame for a long Hindi question fits inside the safe area (no clipping); ffmpeg command
  built correctly (mock subprocess); picker rules as in Part A.

### B.4 Workflow `.github/workflows/promo-shorts.yml` (on `main`, needs owner's OK)
- daily 05:00 IST (`30 23 * * *` UTC): install `ffmpeg` (`apt-get install -y ffmpeg fonts-noto-core` or
  downloaded font), run `python -m app.promo shorts --count 3`, upload the folder as an **artifact**
  (retention 14 days), commit the posted-log.
- Owner's daily routine (2 min): GitHub app/browser → Actions → latest "promo-shorts" run → download
  artifact zip → upload the 3 videos with their `.txt` captions (or once a week schedule 21 in Meta
  Business Suite + YouTube Studio).
- Optional: also send the 3 videos to the Telegram channel (`sendVideo`) so the owner just forwards them.

### B.5 Phase 2/3 (only after v1 works for 2 weeks)
- Hindi voice-over via a TTS the owner chooses (Google Cloud TTS paid; check licence/ToS first).
- YouTube auto-upload: owner creates a Google Cloud project, OAuth consent, requests audit; store the
  refresh token as a GitHub secret; `videos.insert` costs 1600 quota units (≈6 uploads/day on 10k quota).
- Track: views/subs per format; keep the top 2 formats, drop the rest.

### B.6 Done means
`python -m app.promo shorts --count 3` produces 3 playable MP4s + captions locally (show a frame
screenshot to the owner); the workflow artifact downloads on a phone; no question repeats for 30 days.

---

## Part C — Order of work for the next chat
1. Read this file, `v2/CLAUDE.md`, `START_HERE.md`. `git pull` the work branch; `pytest -q` green.
2. Part A: ask the owner for A.1 steps → build A.3 + tests → dry-run → workflow (with OK) → first real post.
3. Part B: build B.3 + tests → render 3 samples, show one frame → workflow (with OK) → owner uploads.
4. Report in Hindi: what was posted, links, what the owner must do daily (Shorts upload only).

## Honest expectations
Telegram/Shorts bring visibility, not instant users. Realistic: 0–300 subscribers in month 1 if posting is
daily and correct; growth compounds with consistency. The biggest free channel long-term is still **Google
search to the live site** (job notification pages) — deploying the site (VPS + domain) unlocks it.
