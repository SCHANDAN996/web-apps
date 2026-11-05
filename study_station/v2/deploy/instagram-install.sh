#!/usr/bin/env bash
# Run from a clean reviewed Git checkout on Ubuntu/Debian. Does not start publishing.
set -euo pipefail
umask 077
if [ "$(id -u)" -ne 0 ]; then echo 'Run with sudo on the server.' >&2; exit 1; fi
source_repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
if [ -n "$(git -C "$source_repo" status --porcelain)" ]; then
  echo 'Use a clean committed checkout; do not install uncommitted changes.' >&2; exit 1
fi
revision=$(git -C "$source_repo" rev-parse HEAD)
base=/opt/studystation-instagram
state=/var/lib/studystation-instagram
if [ -e "$base/source" ]; then echo 'Already installed; review upgrade separately. Nothing overwritten.' >&2; exit 1; fi
apt-get update
apt-get install -y python3-venv gh xvfb xauth x11vnc novnc websockify openbox
id studystation-ig >/dev/null 2>&1 || useradd --system --create-home --home-dir "$state" --shell /bin/bash studystation-ig
install -d -m 700 -o studystation-ig -g studystation-ig "$state"
install -d -m 755 "$base/source"
git -C "$source_repo" archive "$revision" study_station/v2 | tar -x -C "$base/source"
python3 -m venv "$base/venv"
"$base/venv/bin/python" -m pip install -r "$base/source/study_station/v2/requirements-instagram.txt"
# Worker otherwise needs only Python's standard library.
PLAYWRIGHT_BROWSERS_PATH="$base/browsers" "$base/venv/bin/python" -m playwright install --with-deps chromium
chmod -R a+rX "$base"
printf '%s\n' "$revision" > "$base/REVISION"
install -m 644 "$base/source/study_station/v2/deploy/studystation-instagram.service" /etc/systemd/system/
install -m 644 "$base/source/study_station/v2/deploy/studystation-instagram.timer" /etc/systemd/system/
install -m 644 "$base/source/study_station/v2/deploy/studystation-instagram-desktop.service" /etc/systemd/system/
if [ ! -e /etc/studystation-instagram.conf ]; then
  install -m 600 /dev/null /etc/studystation-instagram.conf
  printf '%s\n' 'INSTAGRAM_ACCOUNT=SET_CONFIRMED_USERNAME' > /etc/studystation-instagram.conf
fi
systemctl daemon-reload
printf '%s\n' 'Installed. No service/timer enabled. Follow study_station/promo/INSTAGRAM_SERVER.md for login and pilot.'
