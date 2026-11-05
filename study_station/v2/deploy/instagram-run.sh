#!/usr/bin/env bash
set -euo pipefail
: "${INSTAGRAM_ACCOUNT:?Set the confirmed account in /etc/studystation-instagram.conf}"
if [ "$INSTAGRAM_ACCOUNT" = SET_CONFIRMED_USERNAME ]; then echo 'Configure actual Instagram username first.' >&2; exit 1; fi
exec /opt/studystation-instagram/venv/bin/python -m app.promo.instagram_worker run \
  --account "$INSTAGRAM_ACCOUNT" --state-dir /var/lib/studystation-instagram --enable-publish
