# Promo add-on: how to merge it into another copy of Study Station

The promotion feature (Telegram posts + Shorts videos) is a **self-contained add-on**. It needs no database,
no web page and no change to the app's UI. It reads only the book files.

## What the add-on is (copy these as they are)
| Path (from repo root) | What it is |
|---|---|
| `study_station/v2/app/promo/` | `__init__.py`, `__main__.py` (CLI), `pick.py`, `telegram.py`, `posted.py`, `shorts.py` |
| `study_station/v2/tests/test_promo.py`, `test_shorts.py` | tests |
| `study_station/promo/fonts/` | Noto fonts + OFL licences |
| `study_station/promo/README.md`, `INTEGRATE.md` | docs |
| `study_station/promo/posted.json` | posted-log (created by the workflows; keep the newest copy) |
| `.github/workflows/promo-telegram.yml`, `promo-shorts.yml` | on `main` |
| `study_station/v2/requirements.txt` | add `Pillow==13.0.0` and `fonttools==4.67.0` |

## The only places it touches existing code (the contract)
- `app.bookcheck`: `BOOKS_ROOT`, `SETS_PER_LANG`, `queue()`, `chapter_status(path)`, which returns `('OK'|..., todo, problems)`.
- `app.importers`: `parse_mcq_text(text)`, which yields objects with `.number .text .options .answer_index
  .solution .difficulty`, and `quality_problem(q)`.
- Book layout: `books/QUEUE.txt`; `Chapter_*/Practice_{hi,en}_Set_0N.txt`; `Short_Tricks_hi.txt` /
  `Memory_Hooks_hi.txt`; `chapter.json` (`title_hi`).

If the other copy renamed any of these, adapt the calls in `pick.py`. Do not change how the rules work.

## Prompt to give the AI in the other session (copy as is)

```
Study Station: merge the "promo" add-on from GitHub into this project, without breaking anything.

1. git fetch origin claude/elegant-rubin-sgov1q main
2. Read study_station/promo/INTEGRATE.md from that branch
   (git show origin/claude/elegant-rubin-sgov1q:study_station/promo/INTEGRATE.md).
3. Copy only the files in its table into this project:
   git checkout origin/claude/elegant-rubin-sgov1q -- <paths>.
   Do not overwrite any other file. In requirements.txt, only ADD the two lines (Pillow, fonttools).
4. Check the "contract":
   - Do app.bookcheck (BOOKS_ROOT, SETS_PER_LANG, queue, chapter_status) and
     app.importers (parse_mcq_text, quality_problem) exist here with the same behaviour?
   - If a name or path is different, make the smallest change in app/promo/pick.py.
     Keep the rules: only bookcheck-OK chapters; hi and en answers must match; quality_problem must be clean;
     question ≤250 chars, option ≤80; no figure/passage questions.
5. If this project's UI has a design system or a theme, the promo code does not need to change;
   it does not touch the UI.
   The video colours are in shorts.py → C (Material 3 tokens from app.css). If the brand colours changed,
   update only C.
6. pip install -r study_station/v2/requirements.txt, then run these from study_station/v2:
   - pytest -q (the whole suite must stay green)
   - python -m app.promo telegram --slot quiz --dry-run
   - python -m app.promo shorts --count 1 --out /tmp/s
     (check the frames; ffmpeg is needed)
7. Commit in small steps and push to the work branch. Never put a token or secret in code, logs or chat.
8. Tell me in Hindi what was merged and whether you had to change anything.
```
