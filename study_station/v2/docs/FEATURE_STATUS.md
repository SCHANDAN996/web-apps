# Feature status matrix (24 Oct 2026)

Each stage is a separate column, as asked in `design/UI_UX_NEXT_AND_AI_HANDOFF.md` (point 4). A feature that is
"in source" is not automatically verified, deployed, or in the Play bundle.

| Column | Meaning |
|---|---|
| **Source** | Code exists on `claude/elegant-rubin-sgov1q`. |
| **Tests** | Automated tests exist: pytest file, or e2e script under `tests/e2e/`. |
| **Browser (Linux, 24 Oct)** | Exercised in a real headless browser in this session, against a local seeded QA DB. |
| **Phone** | Checked on a real Android phone. |
| **Deployed** | Running on the production server. |
| **Play 1.2.0 (code 3)** | Part of the bundle submitted for Google review. |

Legend: ✅ yes · ⬜ not checked in this session (unknown, not "no") · ❌ no / disabled.

The Phone / Deployed / Play columns are left ⬜ on purpose. They need the owner's device, the server's
`/var/lib/studystation/source-release.json`, or the Play Console. They are not to be guessed.

| Feature | Source | Tests | Browser (Linux, 24 Oct) | Phone | Deployed | Play 1.2.0 |
|---|---|---|---|---|---|---|
| Home (collaboration cards first, today card, study block — owner kept this layout; batch-1 redesign reverted 24 Oct) | ✅ `templates/home.html` | `test_ui_controls.py`, `e2e/flow.mjs` | ✅ 360px light/dark/paper, 130% text, landscape; no overflow, no JS errors | ⬜ | ⬜ | ⬜ |
| Onboarding, practice 10, mock submit, revise, books reader, settings, language switch | ✅ | `test_api.py`, `test_books.py`, `e2e/flow.mjs` | ✅ all `flow.mjs` steps pass | ⬜ | ⬜ | ⬜ |
| Themes (light/dark/paper/system) | ✅ `js/theme.js` | `test_ui_controls.py`, `flow.mjs` | ✅ | ⬜ | ⬜ | ⬜ |
| Mock resume after closing the app (position kept in localStorage; else first unanswered) | ✅ `js/player.js` | `e2e/flow.mjs` (reopen + no-saved-position checks) | ✅ reproduced 6/80 → 1/80 before, 6/80 after | ⬜ | ⬜ | ❌ (after submission) |
| Workspace v2 / notebooks / drawing | ✅ `js/workspace-*.js` | `workspace*.cjs` (PC-only paths) | ⬜ scripts not portable yet | ⬜ | ⬜ | ⬜ |
| Group study / Teacher class / Shared | ✅ `classroom.py` | `test_classroom.py`, `classroom.cjs` (PC-only) | ⬜ | ⬜ | ⬜ | ⬜ |
| Favourites / share question | ✅ `shared_questions.py`, `js/question-actions.js` | `test_shared_questions.py`, `question-actions.mjs` | ⬜ script needs Chrome channel | ⬜ | ⬜ | ⬜ |
| Scoped progress reset | ✅ `progress.py`, `js/reset.js` | `test_progress_reset.py`, `test_progress_scoped.py`, `reset-live.mjs` | ⬜ | ⬜ | ⬜ | ⬜ |
| Offline study pack | ✅ `offline_pack.py`, `js/offline-study.js` | `test_offline_pack.py`, `offline-study.mjs` (needs generated pack) | ⬜ | ⬜ | ⬜ | ⬜ |
| Backup / restore | ✅ `backup.py`, `js/backup.js` | `test_backup.py`, `backup-*.mjs` | ⬜ | ⬜ | ⬜ | ⬜ |
| Google sign-in | ✅ `google_auth.py` | `test_google_auth.py`, `google-signin.cjs` (PC-only) | ⬜ | ⬜ | ⬜ | ⬜ |
| Membership + website PayU | ✅ `membership.py`, `payu_payments.py` | `test_membership.py`, `test_payu_*.py`, `membership-lease-events.cjs` | ✅ lease-events script passes (no browser) | ⬜ | ⬜ (owner: live) | ⬜ |
| Play billing / UCB | ✅ code present | `test_play_billing.py`, `test_play_choice.py` | — | — | ❌ disabled by owner decision | ❌ |
| Account deletion, privacy | ✅ | `test_account_deletion.py`, `account-deletion.cjs` (PC-only) | ⬜ | ⬜ | ⬜ | ⬜ |
| Jobs list / filters | ✅ `jobs/` | `test_jobs.py`, `test_ui_controls.py`, `jobs-choices.mjs` | ⬜ | ⬜ | ⬜ | ⬜ |
| Current affairs (AIR) | ✅ `current_affairs.py`, `tools/current_affairs/` | `test_current_affairs.py`, `test_cabook.py` | ⬜ | ⬜ | ⬜ | ⬜ |
| Admin dashboard 2.0 (learner counts, alerts, live revision, Telegram/Shorts) — read-only | ✅ `admin.py`, `templates/admin/dashboard.html` | `test_admin.py` | ✅ 360px, no horizontal scroll, no JS errors | ⬜ | ⬜ | n/a (website only) |
| Admin: possible-wrong-key queue, bulk verify/hide with reason, audit log (`/admin/audit`) | ✅ `admin.py`, `services.suspicious_keys`, `AdminAction` | `test_admin.py` | ✅ 360px list + bulk form | ⬜ | ⬜ | n/a (website only) |
| Telegram quiz in the app (Practice tile → today's channel questions, live log from GitHub, cached 10 min) | ✅ `promo/live.py`, `/api/v1/telegram-quiz` | `test_promo_live.py` | ✅ tile + quiz opened with the 24 Oct channel questions | ⬜ | ⬜ | ❌ (after submission) |
| My mistakes (revise page button: latest-wrong questions of the last 7 days, max 25, this learner only) | ✅ `services.recent_mistakes`, `/api/v1/mistakes` | `test_mistakes.py` | ✅ 4 wrong → button '4 सवाल' → set of 4; hi/en at 130% text, no overflow | ⬜ | ⬜ | ❌ (after submission) |
| CA quiz from the book's AIR facts (seed imports the 4 current-affairs chapters, dated by report; week/month quiz windows) | ✅ `seed.seed_ca_book_questions` | `test_seed_ca_book.py` | ✅ QA DB: 224 imported, 0 skipped, idempotent; 30-day window 39 | ⬜ (needs `python -m app.seed` on the server) | ⬜ | n/a |
| Telegram posts (GitHub Actions) | ✅ `app/promo/` | `test_promo.py` | n/a; live: `t.me/s/studystation_hindi` shows the 23–24 Oct polls | n/a | ✅ GitHub Actions (not the server) | n/a |
| Shorts videos (GitHub Actions) | ✅ `app/promo/shorts.py` | `test_shorts.py` | n/a; frames checked by eye | n/a | ✅ GitHub Actions artifact | n/a |

## e2e scripts that only run on the owner's PC
Several scripts in `tests/e2e/` are PC-specific:
- They hard-code a Windows Playwright path (`C:/Users/Admin/...`): `classroom.cjs`, `workspace*.cjs`, `google-signin.cjs`,
  `account-deletion.cjs`, `community-safety.cjs`.
- They launch the Chrome channel: `navigation-readonly.mjs`, `account-namespace.cjs`.
- They need a pre-generated study pack: `offline-study.mjs`.

On Linux they stop before testing anything, which is a setup failure, not a feature failure. Making them portable is a
separate task, so this matrix does not claim those features as browser-verified.
