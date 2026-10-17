# Whiteboard and portable backup — 16 October 2026

Implemented locally: per-question rough work, bilingual Settings file backup/restore,
owner-scoped progress export/import, idempotent imports, atomic conflict rollback,
server-recomputed scoring, safe reset/recovery integration, and native Android
local document/Drive bridge. Existing user data was not reset.

Reset supports exact chapter reading plus linked-topic practice/revision, a subject,
or all progress. Chapter/subject preserve mixed-subject mock results; all clears
mocks too. Confirmation discloses shared-topic impact and retained backup copies.
Stable backup identifiers prevent a deleted SQLite row ID from colliding with
new study history after a scoped reset.

Verified: full Python suite 194 passed, with two existing Windows symlink privilege
failures (WinError 1314); generated APK shell check passed. Browser's 12 main flows
passed with no JavaScript errors. Real local-server practice answer and rough work
exported, restored into a separate learner and reimported without duplicate history.
Cancel and invalid-file checks passed. Real chapter/subject/all reset and isolation
checks passed. Hindi mobile light/dark screenshots reviewed; confirmation controls
fit a 360×800 viewport. Android build succeeded and 9 unit tests passed; APK shell
and feature script bytes match the latest source.

Google Cloud project `study-station-511803` exists and Drive API is enabled. OAuth
branding is configured. The Android debug OAuth client was created after owner
approval on 16 October 2026. Drive remains disabled in the general build pending
real-device upload/download verification. Release signing registration remains separate.
See `android/GOOGLE_DRIVE_SETUP.md` for exact setup and acceptance checks.

This phase has not been deployed to production. At final device discovery no phone
was connected. Native file-picker and Google consent tests require a connected
device. Study history continues to live on the current server; backups do not
replace the existing progress storage system. Rough work stays local unless the
learner exports or backs it up.

## 17 October update

One owner-provided Google test account was added. On the connected phone a
separate local QA learner's answered question and rough work were exported through
the native Drive bridge; the callback reported backup success. The USB connection
went offline before native restore could be verified. General builds keep Drive
disabled until the full phone restore check passes. The temporary phone installation
was the local QA build. The normal production-URL APK was subsequently reinstalled
successfully on 17 October; QA forwarding and the local server were stopped.
Native restore remains pending; foreground app access is needed for that check.
Production progress was not reset.

The owner subsequently selected 3D logo option 5: pearl/cream, burgundy SS and gold
book details. Website/PWA icons, compact topbar image, Android launcher/offline
artwork and generated shells share resized exports of the selected source in
`design/branding/`. Mobile light/dark inspection passed. Further APK builds and
installation are deferred at the owner's request; these changes are local.

## Question access and speed update

The question library exposes all usable questions through 30-item pages, search
and subject/topic/difficulty filters. A learner can open any question and start an
attempt for that exact question. Normal practice offers 10, 20 or 50 questions.
Public browsing never exposes correct answers or learner progress.

Device caching keeps up to 80 previously opened book pages and 30 public question
pages. Question pages expire after 24 hours; online requests fetch current content
first. Cached question pages are language- and asset-version-specific. Attempts,
API responses, progress and jobs are not cached. Offline browsing does not provide
offline answer submission. Settings can clear page caches without deleting reading
history, rough work, preferences or backups; in-flight responses cannot undo clear.

Server-side topic counts now share a short-lived cache with invalidation on bank
changes. Catalog/mock queries avoid per-item lookups. Home no longer waits for a
cold book-directory scan. Navigation prefetch is bounded, expires and clears around
writes. Jobs robots redirects are individually checked and responses bounded.

Verification: Python suite 214 passed; the same two Windows symlink privilege
failures remain (WinError 1314). Main browser flows 12/12 passed with no JavaScript
errors. Focused real-browser checks passed for 50-question practice, exact-question
attempts, library filters/pagination/language, prefetch and offline cache lifecycle.
Cache clearing preserved the learner export, reading history, rough work and theme.
360px mobile layouts and the selected logo were visually reviewed. Generated shell
check passed. No production deployment or additional APK installation was performed.

## Approved live deployment and phone verification — 17 October

The owner subsequently authorized production deployment and phone testing. A
consistent SQLite backup and previous-code archive were saved before deployment.
Additive schema preparation ran once with the service stopped. Production nginx
now accepts the supported 2 MiB backup size; its configuration check passed.
The full Linux server suite passed: 216 tests. Production health is healthy and
service startup logs show no errors. No content sweep or learner reset was run.

The updated production-URL APK was installed on the connected phone. Home,
practice, question library/detail, jobs, books and settings opened without layout
overflow or JavaScript errors. The selected 3D SS header logo loaded correctly.
At the owner's further request the header language control now shows EN / HI;
the final APK was rebuilt, installed and visually checked on the phone. Header
shell tests passed locally and on the server (4/4); Android unit tests/build passed.
Temporary device debugging forwarding was removed. Drive restore remains pending
and the general build continues to keep Drive disabled.
