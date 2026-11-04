# PC handover: persistent Instagram server companion

Prepared code is **not deployed or live-tested**. No Instagram post or Telegram message was sent
from the coding workspace. The web app and existing YouTube/Telegram schedules are unchanged.

## What is implemented

1. Existing `Promo Shorts` render adds `*.instagram.json` manifests to its MP4 artifacts.
2. `python -m app.promo.instagram_worker` checks successful runs of that exact workflow on the
   canonical branch in `SCHANDAN996/web-apps`. It rejects pull requests, forks and other branches.
3. First start records historical runs as baseline and does not publish a backlog. Only later runs
   are downloaded into the private server queue; nothing is rerendered.
4. A **dedicated** Telegram approval bot sends every video and full caption to the owner's private
   chat. Approve/Reject buttons apply only to that exact batch and account. Approval means public
   posting of the complete batch. Notification alone is not approval. Credentials remain private.
5. The browser uses the server's own persistent login. Wrong account, changed files/UI, missing
   confirmation or interrupted Share stops publishing. Approved content hashes are rechecked.

## Complete on the authorized PC

- Read `../promo/INSTAGRAM.md`, `CLAUDE.md`, `docs/SOURCE_SYNC.md` and this document.
- Use existing authorized SSH access. Inspect the machine, service health, memory/disk, desktop
  availability and existing bot consumers first. Preserve the live website, secrets and database.
- Install reviewed source into a separate `/opt/studystation-instagram` checkout and a Python venv.
  Pin the reviewed commit. Do not run downloaded artifact code or replace the live app checkout.
- Install `requirements.txt`, `requirements-instagram.txt`, Chromium and official Linux browser
  dependencies. Use a dedicated unprivileged `studystation-instagram` OS user, not root Chromium.
- Create `/var/lib/studystation-instagram` mode 0700 owned by that user. Browser, journal, GitHub CLI
  config and queue all stay outside Git. Configure `PLAYWRIGHT_BROWSERS_PATH` consistently during
  install and service operation.
- This publisher uses a visible browser. Configure a private persistent desktop/display accessible
  only through the existing secure tunnel/remote desktop; never expose VNC or browser debugging
  publicly. Do not add `--no-sandbox`, export login cookies or copy a personal browser profile.
- With the operator present, run the `login` command as that dedicated OS user on that same display.
  Confirm the actual account username; prior candidate `studystationhindi` is not proof of ownership.
  The operator enters password/OTP privately. Do not ask for credentials in chat.
- Inspect the live account's exact Create, Next, Caption, Share and success controls. The current
  strict English selectors are **unverified**; adjust only from observed UI and add tests if needed.
- Connect GitHub CLI for read access to workflow runs/artifacts as the dedicated user. Use the
  existing authorized secure login, least privilege, and keep credentials out of Git/logs/chat.
- Create a **separate approval bot** through the operator's Telegram account and open its private
  chat. Do not repurpose the existing StudyStation content bot or attach two getUpdates consumers.
  A configured webhook is rejected; polling conflicts stop the worker. Never delete existing webhooks.
- Set a root-owned mode-0600 `/etc/studystation-instagram.env` with `IG_ACCOUNT`,
  `IG_APPROVAL_BOT_TOKEN`, `IG_APPROVAL_CHAT_ID` (owner's positive numeric private chat/user ID),
  `DISPLAY` and, when required, `XAUTHORITY` pointing to that dedicated user's private display auth.
  Keep XAUTHORITY under the private state folder, because service `ProtectHome=true` hides homes.
  The worker creates a private writable `tmp` inside state; service TMPDIR uses it while the rest
  of the filesystem is read-only. Do not enable PrivateTmp without checking X11 socket visibility.
  The service manager reads this file; never commit or print it.
- Install `deploy/studystation-instagram.service` only after verification. Adapt the paths/display
  to the actual host. The example has `Restart=no` to avoid blind recovery of public uploads.

## Activation check

Run tests first. Merge the reviewed renderer/manifest integration into the canonical branch before
using the worker; the worker deliberately ignores development branches. Do not add a second video
generation schedule. Start the companion once to establish its historical baseline, then trigger
one new existing **Promo Shorts** run with `count=1` on the canonical branch. Validate the artifact.

Run the worker on the verified display with `--enable-publish`. It sends the sample and full caption
to the owner. Verify that no upload occurs before the owner presses the Telegram approval button.
After approval, confirm the actual Reel/account/caption, success receipt and duplicate suppression
on another worker cycle. Then enable the reviewed service. Public approval is **not** a private test.

## Failure and recovery

The worker stops on errors without logging raw HTTP/subprocess exceptions, which can contain tokens.
Inspect its private `batches.json` and `uploads.json`; never publish these files or copy their content
into public issues. `preparing` means previews/approval delivery did not finish; no Share was initiated.
After checking Telegram, an operator may remove only that `preparing` batch entry to resend previews
and request a fresh approval. Duplicate preview notifications are possible after an interrupted send.

`publishing`, `blocked`, or an `uploads.json` pending record requires manual Instagram inspection.
Use `app.promo.instagram reconcile` for each pending record with its verified published URL or an
explicit retry decision only after confirming absence. Then reset that batch to `waiting` with a fresh
nonce, resend its unchanged preview and new approval request through the same bot, and save the new
message ID. Never change it directly to approved or delete the whole journal. If this recovery has not
been completed, leave the worker stopped. Keep private backups of both ledgers.

The graphically rendered Instagram flow remains susceptible to UI changes and login challenges.
Activation requires an actual end-to-end test on the user's server; unit tests cannot establish that.
