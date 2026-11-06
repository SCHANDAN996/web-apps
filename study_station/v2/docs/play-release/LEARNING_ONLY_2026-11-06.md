# Learning-only release — 6 November 2026

Owner decision: remove recruitment permanently from the current app and website, preserve learning and historic data. This is the same product behavior for all users and reviewers, with no remote feature switch.

- Shipped `JOBS_ENABLED` is the constant False. Public Jobs pages/API return HTTP 410 and no records; old links lead to a learning notice.
- Home, web/Android navigation and sitemap no longer expose recruitment. Settings replaces the Jobs tab.
- Three server cron entries (collection, cleanup, Telegram job digest) were removed through `deploy/retire_jobs.py`. A private server-side cron backup was made; other schedules preserved.
- Job mutation/notification CLI commands refuse to run. Historical records and retained parser/security tests remain; tests explicitly enable archived handlers only inside test processes.
- Current-affairs learning stays enabled. AIR/PIB and official exam-information sources, plus non-affiliation disclaimers, remain in app/listing.
- Replace all three listing translations with `store-listing.md`. Replace screenshots showing old navigation. Upload the normal signed release AAB, not a Direct PayU artifact.
- Candidate release: 1.2.3, version code 6. Compilation, unit/browser/Linux checks and actual Console upload/status must be recorded before claiming submission.

No approval guarantee. Do not claim a new rejection unless Console shows a newer rejection date; the 1 November rejection can remain visible while an update is in review. No automatic appeal or trader-status legal declaration is part of this change.
