# PC integration verification — 23 October 2026

Read HANDOFF_CHATGPT.md and promo/INTEGRATE.md completely before importing.

## Scope
- Imported the self-contained app/promo package, tests, OFL fonts, docs and the newest fetched posted logs.
- Copied the two workflow files from origin/main. GitHub Actions remains the only promo scheduler; no VPS cron, service or duplicate posting was configured.
- Added only Pillow==13.0.0 and fonttools==4.67.0 to the existing PC requirements.
- Imported the four named AIR current-affairs chapters, cabook tools, 225-row source-linked fact bank and its tests.
- Existing app UI, advanced features, database and runtime configuration were not replaced from GitHub.

## Compatibility and fixes
- PC app.bookcheck BOOKS_ROOT / SETS_PER_LANG / queue / chapter_status and app.importers parse_mcq_text / quality_problem match the contract. No pick.py adaptation or selection-rule relaxation was needed.
- Real ffprobe inspection found a 28-second output despite the 24-second scene schedule. Added an explicit total-scene-duration output limit to ffmpeg_cmd and a regression assertion. The generated MP4 now measures exactly 24.000 seconds, 1080x1920, with AAC audio.
- Existing generated Android shell/offline HTML was stale before this integration verification. Regenerated it from the current PC source using python -m app.shell; no source UI was copied over.

## Validation
- Four imported current-affairs chapters: bookcheck OK, zero TODO/problems each.
- Current-affairs, Telegram and Shorts focused tests: 25 passed.
- Complete PC source snapshot, isolated Linux test folder: pytest -q => 441 passed (85.35 s).
- Windows full run in UTF-8 initially had four stale-generated-shell failures and two existing symlink-privilege failures. After regeneration all six shell tests pass. Symlink protection tests pass on Linux; Windows does not grant their required symlink privilege. No tests were skipped, removed or weakened.
- Telegram quiz --dry-run: five questions selected; no API send.
- Shorts --count 1 --out /tmp/s: successful on Linux, Hindi question and answer frames visually inspected. Windows rendering also ran, but its Pillow build lacks RAQM; use the existing Linux GitHub runner for production Hindi rendering.
- QA rendering used PROMO_POSTED pointing at disposable temporary files, not the real posted.json. Both production posted logs retained their fetched Git blob hashes throughout QA.
- AIR facts were imported as supplied with their source links; no facts were invented or rewritten from memory. This verification is not a new independent article-by-article factual audit.

## Git history handling
The PC branch and upstream work branch had already diverged (35 local and 1517 upstream commits at the initial fetch). Only the documented integration paths were imported into the PC checkout. Existing PC changes and staged files were preserved. Local integration commits retain the PC history; only the new duration fix and this verification record are published on top of the current upstream work branch, without force-pushing or reverting unrelated remote content. Workflow files remain on main upstream.

No deployment or live promo post was performed by this integration task.
