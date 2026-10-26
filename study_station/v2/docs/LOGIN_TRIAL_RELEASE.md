# Focused login and three-month trial — 26 October 2026

Owner approved three calendar months for new and existing users, including expired old trials. Existing paid access is not shortened. Prices and billing enable flags are unchanged.

- `/login?return_to=…` is the common Google/password entry for study and classrooms. The server allowlists the return destination.
- Successful authentication creates one account-bound trial in the same login transaction. The compatibility `/membership/start` endpoint remains idempotent.
- `/account` shows identity and access state; loading failures remain visible with Retry. Login success, access activation and native offline renewal have separate feedback. No automatic payment is created.
- Calendar arithmetic clamps to the destination month's last date; it is not a fixed 90-day period.

## Existing-user rollout
After backing up production and installing the additive schema, run with the existing production environment:

```
deploy/run.sh python -m app.trial_rollout
deploy/run.sh python -m app.trial_rollout --apply
```

The first apply records an immutable global rollout timestamp under `three-calendar-months-v1`. Eligible old accounts get at least three calendar months from that timestamp; later trial dates and paid dates are preserved. Repeating the command does not extend dates again. Counts and policy timestamps are printed, never account details. Do not edit membership rows by hand.

The source deployment must keep Play billing/UCB disabled and existing website PayU settings unchanged. Deploying this web/server change is separate from building or uploading another Android bundle. The daily native offline-proof lifetime remains at most 24 hours.

## Validation scope
Backend coverage includes month-end/leap-year arithmetic, old-account rollout, repeated apply, protected paid access, login activation, safe return destinations and existing payment behavior. Browser checks cover Hindi/English, all themes, wrong password, cancelled Google login, retry, offline-readiness feedback, account scope and return to study/invites. Use disposable test accounts/data; never reset a learner's progress for QA.
