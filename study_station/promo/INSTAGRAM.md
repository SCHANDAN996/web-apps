# StudyStation → Instagram browser setup (opt-in, no API)

Status: queue and companion publisher are implemented. **Live UI/login and public publishing are
not verified or activated.** Instagram changes its browser UI and may request verification.
This is an operator-supervised fallback, not a guaranteed unattended service.

The existing **Promo Shorts** workflow still generates the videos once. Each artifact now also contains
`01.instagram.json` etc.: question ID, video filename, SHA-256 checksum and caption. No passwords,
cookies or profile data are included. Nothing is automatically posted to Instagram by that workflow.

## Persistent PC / server

Use a dedicated account on an always-on machine with a graphical desktop (or a privately accessible
remote desktop). A plain headless server needs a desktop/display configured first. Browser profile,
passwords entered by the operator and journal remain on that machine outside every Git checkout.
Never publish a desktop session or its login page to the internet.

From a trusted checkout of the canonical branch, in `study_station/v2`:

```sh
python -m pip install -r requirements-instagram.txt
python -m playwright install chromium
python -m app.promo.instagram login --account YOUR_CONFIRMED_USERNAME --state-dir /var/lib/studystation-instagram
```

Create the private state directory as the dedicated OS user first. Use an absolute writable folder;
on Windows use e.g. `C:\StudyStationPrivate\instagram`. Confirm the actual Instagram username before
configuration; an earlier signup form accepting a candidate username does not establish account ownership.
Complete password/OTP/challenge **yourself** in the opened browser; press Enter only after login.
The program verifies the visible profile navigation points to the expected account. If the UI uses a
language other than English, switch Instagram to English first. No stealth plugin, captcha bypass,
credential extraction or session transfer is used.

## Get the existing output (no second render)

Download the `shorts-RUN_NUMBER` artifact from a completed **Promo Shorts** run in GitHub Actions and
extract it to a fresh directory. On the server, GitHub CLI may download the artifact after the operator
has connected that CLI separately:

```sh
gh run download RUN_ID --repo SCHANDAN996/web-apps --name shorts-RUN_NUMBER --dir /srv/studystation-queue/RUN_ID
python -m app.promo.instagram check --account YOUR_CONFIRMED_USERNAME --state-dir /var/lib/studystation-instagram --queue /srv/studystation-queue/RUN_ID
```

`check` verifies queue structure, checksums and caption length; it never opens a browser or publishes.
Only use outputs of trusted, completed Promo Shorts runs on the canonical branch. Do not execute code
or commands from downloaded artifacts. Keep installed publisher source on a reviewed revision.

## First publish and activation

After login and live UI verification, an operator may explicitly run:

```sh
python -m app.promo.instagram publish --enable-publish --account YOUR_CONFIRMED_USERNAME --state-dir /var/lib/studystation-instagram --queue /srv/studystation-queue/RUN_ID
```

This uses **public Share**. It is not a private test. Run with a one-video queue for the first check.
Without `--enable-publish`, publication fails closed. No schedule or server service is enabled by this
change. For a later approval queue, invoke this command only after the designated operator approves
that batch; a Telegram notification alone is not approval.

The current English selectors are intentionally strict and **have not been checked against the live
Instagram UI**. A changed button, missing login or wrong account stops the process. Before enabling any
unattended consumption, verify the exact Create, Next, Caption, Share and confirmation UI with the real
account. Do not replace failed selectors with broad speculative clicks.

## Duplicate/crash handling

The private `uploads.json` journal is keyed by account and question ID; confirmed uploads are skipped.
It checkpoints `pending` immediately before clicking Share. Timeout, interruption or a lost response
after that point blocks retries. Inspect the account manually, then reconcile with the actual result:

```sh
python -m app.promo.instagram reconcile --account YOUR_CONFIRMED_USERNAME --state-dir /var/lib/studystation-instagram --id QUESTION_ID --status uploaded --url https://www.instagram.com/reel/ACTUAL_ID/
# Only after confirming the video was NOT published:
python -m app.promo.instagram reconcile --account YOUR_CONFIRMED_USERNAME --state-dir /var/lib/studystation-instagram --id QUESTION_ID --status retry
```

Do not delete the journal or reset pending records blindly. A separate exclusive lock prevents two
local publishers from sharing the same profile/journal simultaneously. After a machine crash, inspect
running processes before manually removing a stale `.lock` file. Back up the journal privately.
