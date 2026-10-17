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
is the local QA build; when reconnected, restore the normal production-URL APK
after completing testing. Production progress was not reset.

The owner selected a clean SS monogram. Website/PWA icon, topbar mark, Android
adaptive foreground and generated shells now share this vector artwork. Small-size
visual inspection passed; shell tests 4/4 and Android unit tests 9/9 passed, APK build
succeeded. Logo changes are local and have not been deployed.
