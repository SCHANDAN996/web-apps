#!/usr/bin/env bash
# Run a Study Station command with .env loaded — used by cron and by hand.
#   deploy/run.sh python -m app.jobs run
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
exec ./venv/bin/"$@"
