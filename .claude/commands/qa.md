---
description: Test Study Station before a deploy (pytest, phone e2e flow, exploratory checks)
---
Run the ss-qa-tester and ss-security-reviewer agents in parallel on study_station/v2
(scope: $ARGUMENTS — default: changes since the last deploy tag or the last 10 commits).
Combine their findings into one Hindi report ordered by severity, and list which fixes go to ss-developer.
