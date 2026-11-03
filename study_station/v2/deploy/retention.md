# Study Station retention: reviewed installation, not an automatic global cleanup

Policy: new app-specific server backups and security logs have a maximum retention
of 14 days. This guard expires after 13 days and runs hourly, leaving a day of
scheduling margin. Monitor timer failures; no timer can guarantee expiry during a
prolonged outage or a disabled maintenance service. Do not copy retained personal
information to unregistered backup destinations.

## Exact scope and dry run

`python3 deploy/retention.py` prints only paths, bytes and cutoff (no content).
It removes nothing. After review, `--apply` unlinks expired regular files under:

* `/var/backups/studystation`: scheduled database backups;
* `/root/ss-backups`: ALL deployment snapshots, including `before.db`,
  `progress-before.db`, `env-before`, source tarballs and configuration copies;
* archived `*.log.*` in `/var/log/studystation`;
* archives of `/var/log/studystation-nginx-errors.log` and
  `/var/log/nginx/studystation-access.log`;
* the exact inactive legacy file `/var/log/nginx/studystation-error.log`, once
  its last write is older than the same cutoff (never the current error sink).

It rejects linked root/ancestor directories and ignores linked files and
subdirectories. Live `/var/lib/studystation/studystation.db` is never in scope.
Existing deployment snapshots with preserved old source mtimes may expire early;
this is intentional and does not extend retention. There is no secure-erasure or
instant deletion claim for historical backups. Do not restore a snapshot without
reapplying account-deletion requests since its creation.

## Installation after root review

1. Save and inspect the dry-run report first. Check `systemd-analyze verify` and
   `logrotate --debug deploy/retention-logrotate.conf` before applying changes.
2. Install `retention-app.conf` as
   `/etc/systemd/system/studystation.service.d/retention.conf` and
   `retention-journal.conf` as `/etc/systemd/journald@studystation.conf`.
   Restart only `studystation` (normal brief app restart). Future stdout/stderr
   enters its private journal namespace. No global journal vacuum is permitted.
3. Install `retention.service` and `retention.timer` as
   `/etc/systemd/system/studystation-retention.{service,timer}`. Keep the Python
   script as `/usr/local/lib/studystation/retention.py` and the logrotate config
   as `/etc/studystation/retention-logrotate.conf`. Both files and all their parent
   directories must be root-owned and not writable by the app account; never run
   app-writable deployment source as root.
   The service creates a separate root-only `/var/lib/studystation-retention`
   directory for logrotate state; do not place root-written state in the app
   account’s writable `/var/lib/studystation` directory.
4. Disable the older `/etc/logrotate.d/studystation-oauth-errors` stanza after
   saving its configuration in the allowlisted snapshot directory. The private
   hourly rotation replaces it. The global nginx wildcard can still rotate its
   access log, but hourly app cleanup enforces expiry for all its archives too.
5. Run one reviewed maintenance pass, then enable/start its timer. Check
   `systemctl list-timers studystation-retention.timer` and
   `journalctl -u studystation-retention.service` for failures. Verify the app
   responds and the namespace receives new entries. Alert on a missed run.
6. Inventory log files/backup destinations again after deployment. The inactive
   `/var/log/nginx/studystation-error.log` has an exact-file expiry rule. Confirm
   nginx no longer writes it before enabling cleanup. Never use broad `/var/log`
   deletion globs.

Logrotate uses copytruncate to retain running nginx/cron writers' descriptors;
this has the standard small concurrent-write loss window. Rotation occurs hourly
and archive removal is based on real seconds, not `find -mtime +14` or rotation
count. Existing backup.sh's old cleanup is redundant once this timer is active;
it must not be relied upon for the maximum retention guarantee.

## Legacy shared journal limitation — disclose it

Before this cutover Uvicorn wrote into the shared system journal; app records
cannot be safely erased selectively from that journal. Do not vacuum unrelated
services. Existing shared-journal entries remain until the host's ordinary journal
expiry. The bilingual privacy wording explicitly distinguishes this legacy
migration exception from the new 14-day app-specific policy. Do not declare that
ALL historical security logs already meet 14 days. Record the cutover timestamp
in the release report and verify future app entries do not appear in the default
journal. Legacy logs/snapshots should be reviewed separately before removal.

Google Drive and exported/local device copies remain under the user's control.
The active account/shared data deletion operation and its warnings are unchanged.
