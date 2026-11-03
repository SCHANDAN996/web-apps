# Handoff: work done on 22–23 Oct 2026 (for another AI: ChatGPT / Claude on the PC)

Repo `SCHANDAN996/web-apps`, work branch **`claude/elegant-rubin-sgov1q`**; app in `study_station/v2`
(FastAPI + Jinja + SQLite). Read `study_station/v2/CLAUDE.md` (rules) first.

## 1. Current-affairs book chapters (done, pushed)
- 4 chapters were refreshed from **All India Radio News only** (newsonair.gov.in), with facts up to 22 Oct 2026:
  - `books/10th_Level/GK/Foundation_10th_GK_WorldClass/Chapter_20_Current_Affairs_6M`
  - `books/12th_Level/GK/Intermediate_12th_GK_WorldClass/Chapter_20_Current_Affairs_6M`
  - `books/Graduation_Level/GK/Advanced_Graduation_GK_WorldClass/Chapter_20_Current_Affairs_6M` and `Chapter_30_Current_Affairs_12M`
- **Tools:** `v2/tools/current_affairs/`
  - `facts.tsv`: 225 checked MCQs, each with its AIR link.
  - `cabook.py`: subcommands crawl, find, read, verify, sets, prose, review.
  - `README.md`: the refresh runbook.
- **Tests:** `v2/tests/test_cabook.py`.
- Every fact must be checked against its own AIR article; never write facts from memory.

## 2. Promotion add-on (done, pushed, live)
Self-contained: it reads only the book files, so no DB and no UI changes.
- **Code:** `v2/app/promo/`
  - `pick.py`: chooses questions and tricks from bookcheck-OK chapters.
  - `telegram.py`: Bot API client (polls, HTML, video).
  - `posted.py`: posted-log in `study_station/promo/posted.json`, so nothing is posted twice.
  - `shorts.py`: 24 s 1080×1920 quiz videos made with Pillow + ffmpeg. Fonts are in `study_station/promo/fonts` (OFL).
  - `__main__.py`: the CLI.
- **CLI** (run from `study_station/v2`):
  ```
  python -m app.promo telegram --slot quiz|trick|revision|weekly [--dry-run]
  python -m app.promo shorts --count 3 --out shorts_out [--telegram] [--dry-run]
  ```
- **Content rules** (do not loosen them):
  - Only bookcheck-OK chapters.
  - The hi and en copies must both pass `quality_problem` and give the same answer.
  - Question ≤250 chars, option ≤80.
  - No figure, passage or cloze questions; no option that names other options ("(a) और (b)").
  - Poll explanation = "उत्तर: X।" + the fullest solution sentence that names the answer.
  - Shorts leave out current affairs, because a video stays up after the news is old.
- **Schedules** run on GitHub Actions; the workflow files live on `main` only.
  - `.github/workflows/promo-telegram.yml` posts at these IST times: 07:31 quiz (5 polls), 12:31 trick, 18:01 quiz,
    20:31 answers + solutions, Sunday 10:01 weekly 20-question test.
  - `.github/workflows/promo-shorts.yml` makes 3 videos daily at 05:01 IST as a downloadable artifact.
    A manual run can also post them to Telegram.
  - Both workflows check out the work branch and commit `posted.json` back to it.
- **Secrets and variables:**
  - Secrets are already set: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_ID`.
  - Optional variables: `PROMO_LINK` (footer link), `PROMO_TELEGRAM` (link at the end of each video).
- **Status:** the first trick (message 2) and the first video (message 3) went to the channel successfully.
- **Tests:** `v2/tests/test_promo.py`, `v2/tests/test_shorts.py`.
- **Docs:**
  - `study_station/PROMO_PLAN.md`: plan + status.
  - `study_station/promo/README.md`
  - `study_station/promo/INTEGRATE.md`: how to merge into another copy, and the "contract" with
    `app.bookcheck` / `app.importers`.

## 3. Next (not built yet)
- **Instagram Reels auto-publish:**
  - Needs an Instagram professional account + Meta app; Instagram API with Instagram Login, `media_type=REELS`, public `video_url`.
  - The token must be refreshed every 60 days.
- **YouTube auto-upload:**
  - Needs a Google Cloud project + OAuth.
  - Uploads stay **private** until Google's API audit passes (weeks), so videos are uploaded by hand until then.
- **Job digest to Telegram:** `python -m app.jobs digest --telegram` is already built. It needs the DB, so it runs on
  the server (VPS cron), not on GitHub.

## 4. Rules for whoever continues
1. Never put a token or key in code, logs, commits or chat. Use GitHub secrets or the server's `.env`.
2. **One job runs in one place only.** If a promo slot moves to the server, disable its GitHub schedule first,
   or every post goes out twice.
3. Do not edit `promo/posted.json` by hand.
4. Keep `pytest -q` green (199 tests at handoff). Commit small, push to the work branch, never force-push.
5. Facts only from official sources (AIR/PIB for current affairs; board notices for jobs).
