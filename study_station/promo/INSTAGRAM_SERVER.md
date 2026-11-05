# StudyStation Instagram server setup / PC handoff

Code is prepared; **VPS installation, actual username/login, live selectors, first public post and
activation are not verified**. This uses ordinary Instagram browser UI, no Instagram API. GitHub
artifact downloads still use GitHub's API via gh. Do not use stealth or bypass Instagram verification.

## Architecture

The existing Promo Shorts renderer emits MP4 + `NN.instagram.json` with stable question ID, caption,
SHA-256 and the rendered source ref/SHA. A separate server companion polls successful trusted workflow
runs in SCHANDAN996/web-apps. It accepts the actual main scheduler and canonical manual runs, then
requires manifests to identify the canonical rendered source. Successful --once no-output retries
are skipped. It never changes YouTube/Telegram schedules or generates a second batch.
The worker verifies every distinct rendered SHA is an ancestor of the current canonical branch
through GitHub compare; source ref and SHA are included in the private batch digest used on resume.

Only runs created after init and within GitHub's 14-day artifact retention are discovered. Do not
backfill historical videos automatically. Private browser profile and journals remain on the same
server outside Git; no cookie/session transfer from PC. Share is public. Exact English selectors
must be verified against the live account before activation. A timeout after Share blocks retries.

## Inspect and install

Read v2/AGENTS.md, CLAUDE.md and docs/SOURCE_SYNC.md. Review branch
`codex/studystation-instagram-server`, preserve newer work, run full pytest, and integrate by ordinary
merge into canonical `claude/elegant-rubin-sgov1q`. Do not reset/force-push. Verify canonical renderer
contains instagram.enqueue before consuming new runs.

From the user's PC reuse the existing authorized Hostinger SSH connection. Do not guess host/account
or ask for passwords/OTP in chat. Inspect OS, available disk/RAM and ports/display91 first. The installer
is for Ubuntu/Debian with systemd. Preserve existing website/services/database/firewall/crons.
Run from a clean committed checkout on server:

```sh
sudo bash study_station/v2/deploy/instagram-install.sh
```

It creates dedicated `studystation-ig`, installs source/venv/Chromium under /opt/studystation-instagram,
private state /var/lib/studystation-instagram and systemd units. **No service/timer starts automatically.**
It refuses an existing installation rather than overwriting it. Installed SHA is recorded in
/opt/studystation-instagram/REVISION. Review upgrades separately, preserving state and journals.
The publisher needs only requirements-instagram.txt; no website/database dependencies.

## GitHub read-only login

```sh
sudo -u studystation-ig -H gh auth login
sudo -u studystation-ig -H gh api repos/SCHANDAN996/web-apps/actions/workflows/promo-shorts.yml --jq .name
```

Use the official interactive flow. Limit credentials to repository contents read + Actions read;
no write permission needed. Any token is entered privately in terminal, never command arguments,
source/history/chat. Do not print gh auth token or copy website/Telegram environment files.

## Private server browser login

Verify the actual StudyStation Instagram username; the earlier signup candidate studystationhindi
was not proof of a completed account. Set only `INSTAGRAM_ACCOUNT=actual_username` in root-owned
/etc/studystation-instagram.conf. No password in this file.

User creates a separate VNC password interactively (not their Instagram password):

```sh
sudo -u studystation-ig -H x11vnc -storepasswd /var/lib/studystation-instagram/vnc-password
sudo systemctl start studystation-instagram-desktop.service
```

On PC open a tunnel using the verified existing SSH destination:

```sh
ssh -N -L 6081:127.0.0.1:6081 YOUR_EXISTING_SSH_DESTINATION
```

Open http://127.0.0.1:6081/vnc.html on PC. Enter VNC password yourself. Both VNC/noVNC bind to loopback,
protected by SSH, VNC password and Xauthority. **Do not open public ports or add a public reverse proxy.**
In another SSH terminal, replace ACTUAL_USERNAME:

```sh
cd /opt/studystation-instagram/source/study_station/v2
sudo -u studystation-ig -H env DISPLAY=:91 XAUTHORITY=/var/lib/studystation-instagram/xauthority PLAYWRIGHT_BROWSERS_PATH=/opt/studystation-instagram/browsers /opt/studystation-instagram/venv/bin/python -m app.promo.instagram login --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram
```

User completes password/OTP/verification themselves in server browser, switches Instagram to English,
then presses Enter in SSH terminal. Code verifies the visible Profile navigation links to the expected
account. No credential automation, profile extraction or stealth. Then stop temporary desktop:

```sh
sudo systemctl stop studystation-instagram-desktop.service
```

## Queue and one public pilot

Commands below run as studystation-ig from installed study_station/v2 using the full executable
/opt/studystation-instagram/venv/bin/python (abbreviated as python here). Set
PLAYWRIGHT_BROWSERS_PATH=/opt/studystation-instagram/browsers for browser commands.

```sh
python -m app.promo.instagram_worker init --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram
```

Init is local-only and records start time; it never imports old media. Wait for a new existing renderer
run. A manually triggered extra render can also upload to YouTube, depending on current vars; **do not
cause an unwanted YouTube test upload just to test Instagram**. Prefer next ordinary batch.

```sh
python -m app.promo.instagram_worker sync --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram
python -m app.promo.instagram_worker status --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram
python -m app.promo.instagram check --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram --queue /var/lib/studystation-instagram/queue/RUN_ID
```

Sync only downloads/validates and never opens Instagram. Check actual account, video and caption.
Prepare a separate one-video queue by copying one matching MP4/manifest pair from that batch.
Before first Share show that concrete video/caption to the user. Verify live Create/Next/Caption/Share/
success selectors; these are provisional. If UI differs stop and fix precise selectors in reviewed
source and reinstall; do not blindly click or pretend offline tests prove live publishing.

```sh
python -m app.promo.instagram publish --enable-publish --headless --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram --queue /PRIVATE/ONE_VIDEO_QUEUE
```

This is **a real public post**, not a private test. Verify the reel on the actual account. When the
remaining batch is intended, run worker with --enable-publish --run-id RUN_ID; same journal skips the
pilot's question ID and publishes the remainder. Leave timer off if only the pilot is wanted.

## Activation after pilot

```sh
sudo systemctl enable --now studystation-instagram.timer
systemctl list-timers studystation-instagram.timer
sudo systemctl start studystation-instagram.service
sudo journalctl -u studystation-instagram.service -n 30 --no-pager
```

Timer polls existing artifacts every15min. Verify worker status/public result, not merely service start.
Stop future polls: sudo systemctl disable --now studystation-instagram.timer. A running Share is separate;
inspect before interrupting service mid-upload. Never expose profiles/traces/screenshots in GitHub.

## Recovery and storage

Pending upload = Share might have succeeded. Blocked/publishing batch halts newer posting. Inspect actual
Instagram posts and use `instagram reconcile` in INSTAGRAM.md, then:

```sh
python -m app.promo.instagram_worker resume --account ACTUAL_USERNAME --state-dir /var/lib/studystation-instagram --run-id RUN_ID
```

Resume validates unchanged content and rejects unresolved pending uploads; it does not publish.
Never delete/reset journals to force retry. After crash, verify no process owns a lock before removing
a stale lock manually. Keep journal private backups; never back it up to public source control.
Done media is deleted after14days on successful cycles. Unresolved media stays for operator inspection;
monitor disk and resolve deliberately. Journals remain permanently to prevent duplicates. Outages longer
than GitHub retention can lose unconsumed artifacts; report gaps and decide manually, never auto-backfill.
