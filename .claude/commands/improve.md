---
description: Find the next most valuable improvements (and optionally build the top one)
---
Use the ss-improver agent to refresh study_station/v2/IMPROVEMENTS.md from current evidence.
If the user says "build" or "karo" in: "$ARGUMENTS", then hand the top item to ss-developer and,
after it finishes, run ss-qa-tester on the change.
