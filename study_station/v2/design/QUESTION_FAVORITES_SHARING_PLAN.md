# Saved questions and answer-free sharing

Status: first implementation verified and installed on 17 October 2026.

Implemented in source: structured Result/review cards; shared practice feedback;
Save/Share controls; phone-local IndexedDB favorites; Saved question library;
portable backup merge; answer-free anonymous `/q/{id}` landing route.
Progress reset retains favorites and explains that choice. An explicit separate
favorites-clear control is still pending. Sharing uses the browser share API when
available, with explicit clipboard fallback.

Still pending: verified Android App Links, a real public install destination and
post-install question continuation, native Sharesheet verification on Android,
The answer-free landing page is deployed, and device checks confirmed question
actions, Saved and mock screens. Do not claim native sharing or App Links work
because the landing page and helper tests pass.

## Learner experience

Each question has Save and Share actions beneath its text, separate from answer
options and submission controls. Save toggles instantly, announces its state and
works offline. A Saved tab in the question library supports subject filtering and
practice of saved questions without adding more cards to Home.

Favorites belong to the learner/device: question ID, topic ID, saved timestamp and
content version in IndexedDB. Deduplicate IDs; do not impose the practice batch
size as a favorites/access limit. Add favorites to portable backups with backward
compatibility for existing backups. Reset offers an explicit choice to retain or
clear saved questions rather than silently deleting them with study history.

## Share payload

Use Android's Sharesheet. Share only question text, its four available choices,
language, question code, brand and canonical HTTPS link such as
`https://studystation.ebookcart.in/q/10950?lang=hi`.
Construct text/image from an explicit public-field allowlist. Never capture the
current solved screen: correct-answer colors, solution, selected choice, rough
work and personal progress must not appear in shared text/image or metadata.

The public landing page shows the same question/options and an Open in app / Get
the app action. Its HTML, JSON-LD, Open Graph preview, image and public response
must contain no answer index or explanation. A small indexed lookup/cache serves
these rare public previews; routine study and favorites remain phone-local.

## Installed and uninstalled paths

Configure verified Android App Links for the owned domain, production package and
production signing certificate. Handle both cold-launch intents and onNewIntent,
validate IDs/language, resolve the bundled question and open its exact screen.
There the learner answers or explicitly opens the answer/solution.

Without the app, show a truthful release install URL. After installation, users
can reopen the original link or enter the visible question code. Do not promise
automatic post-install continuation until separately implemented and tested;
verified App Links alone do not guarantee that behavior. No silent clipboard read.

If a question is missing from an older APK, show an update path and retain the code.
If it is withdrawn/under review, the public page should say it is unavailable.
Installed offline answer data is a product flow, not DRM or proof of installation;
do not claim absolute prevention of extracting or independently sharing answers.

## Acceptance

- Favorite persists after reload, app update and backup/restore; toggle is idempotent.
- Saved practice can access any usable saved question, independent of batch size.
- Unsolved and solved questions produce identical answer-free share payloads.
- Search response bodies, metadata and preview images for answer/solution leakage.
- Test English/Hindi and long questions, native share cancellation and accessibility.
- Test installed/uninstalled, cold/warm launch, malformed IDs and missing old-pack IDs.
- Opening a link never resets progress or submits an answer.

References: [Android App Links](https://developer.android.com/training/app-links)
and [Android Sharesheet](https://developer.android.com/develop/ui/compose/sharing/send).
