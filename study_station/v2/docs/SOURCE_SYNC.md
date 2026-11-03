# One Study Station source: GitHub, PC and server

Owner decision, 23 October 2026: continue with the new PC UI. The canonical branch is `claude/elegant-rubin-sgov1q`; app scope is `study_station/v2`, with books and promo assets under `study_station/`.

- New work starts from the canonical branch, preserving the new UI and existing advanced features. Never replace it wholesale with the former UI.
- Fetch before work and before push; preserve other contributors/book-autopilot updates. Commit source in reviewable units. No force-push.
- PC and upstream histories are reconciled with an ordinary merge retaining both ancestries, not a history replacement.
- Server deployments use an exact committed source revision, after tests. Record revision and SHA-256 file manifest at `/var/lib/studystation/source-release.json`. Verify all released source bytes against Git objects.
- Before deployment back up app source, books, environment and SQLite using the SQLite backup API. Stop web workers for the source switch and initialize additive schema once before restarting them. On failed health checks restore source; do not casually overwrite live learner data with a backup.
- Runtime secrets, signing keys, databases, logs, generated content packs, download APKs and users' private data stay outside source synchronization. Source parity does not mean copying production learner records to a PC or GitHub.
- Retain existing website PayU, membership and daily offline-check behavior. Play billing/UCB stays disabled until its separate unresolved requirements are met. Source sync is not permission to change commercial or retention settings.
- Telegram/Shorts continue only through the existing GitHub Actions schedules. Their posted logs remain workflow-owned. No duplicate VPS cron.
- Deploying website source does not update the installed Android app or the already submitted Play bundle. Those require a separate verified Android release.
- Old `backend-server` and `website` folders are legacy applications, not v2 deployment targets. Their pre-existing local WIP must not be overwritten or silently added to a v2 synchronization commit.

Release checks: full Linux pytest, affected browser flows, generated shell consistency, source manifest comparison, service health and public-page smoke checks. Keep before/after source backups within the existing maximum-14-day retention policy.
