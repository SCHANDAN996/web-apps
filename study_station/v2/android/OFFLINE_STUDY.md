# Local study content

The Android study entry now runs from APK assets, using the existing first-party
origin. Public books/questions/catalogue are separate from learner progress.
Jobs and current affairs continue to open the live server. The website remains
available; no server content or existing learner progress has been deleted.

## Build

1. On the trusted content host, from v2 with its environment loaded:
   `bash deploy/run.sh python -m app.offline_pack --output /tmp/study-pack`
2. Transfer only that generated public directory to
   `android/app/src/main/assets/study/`. Never copy the database or `.env`.
3. Run `python -m app.shell`. It regenerates both online and local study shells.
4. Run Android `testDebugUnitTest assembleDebug` with JDK17/SDK configured.

Normal builds require a pack. The explicit `-Pss.requireStudyPack=false` option
allows a legacy online wrapper for compatibility testing. Generated content is
excluded from Git; retain its manifest/hash with the release artifact.

## Local behavior

- All 12 books / 296 readable chapters, and 70,419 usable questions from the
  17 October snapshot. Prompts, flagged questions and private records are excluded.
- Questions are loaded by topic; only three topic files are kept in memory.
  Mock sampling walks topics sequentially to bound peak memory.
- Practice, question browsing, wrong-answer revision, timed mocks and weighted
  negative marking run locally. A local question palette supports navigation.
- Progress and unfinished sessions use IndexedDB, independent of the server.
  Existing on-device reading marks are imported once. Previous server progress
  can be copied explicitly from Settings while online; imports are deduplicated.
- Reading content is rendered as safe plain text, including section navigation;
  the website's rich mind-map/flashcard interactions are not reproduced yet.
- Rough work retains the existing device-local whiteboard.
- Chapter/subject/all reset requires confirmation and affects local progress;
  mixed-subject completed mocks and existing server records are preserved.
- Local file backup/restore uses a distinct offline format, bounded to4MiB.
  The Android document bridge supports both legacy and offline backups.
  Drive remains disabled until its pending real-device restore check passes.
- New content currently ships in a new APK. There is no background content
  download or automatic progress upload, so routine study makes no API requests.

## Verification

`node tests/e2e/offline-study.mjs` uses the actual generated pack and fulfills
only local asset requests; any attempted server request fails the check.
It verifies reading, practice/reload/rough work, question access,80-question
mock negative marking, reset/restore and bilingual/theme layouts. Run with
PLAYWRIGHT_PATH and PLAYWRIGHT_CHANNEL=chrome where Playwright is not installed
in the project. Python tests cover public-only export, deterministic hashes,
atomic publication, symlink rejection and current offline shells. Android unit
tests cover same-origin GET-only routing, unsafe paths and language selection.

The first complete snapshot APK measured30,599,417bytes before the version
increment. All packaged content files were checked against their manifest hashes.
Physical-device acceptance must still be completed when the phone reconnects;
the device was absent from ADB during the offline build's final checks.
