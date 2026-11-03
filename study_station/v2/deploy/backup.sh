#!/usr/bin/env bash
# Consistent SQLite backup (safe while the app is running), keeps 14 days.
set -euo pipefail
umask 077                      # backups contain device tokens — owner-only
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
DB="${DATABASE_URL#sqlite:///}"
DEST="${BACKUP_DIR:-/var/backups/studystation}"
mkdir -p "$DEST"
case "$DATABASE_URL" in
  sqlite:*) ;;
  *) echo "Not SQLite — use pg_dump for PostgreSQL"; exit 1 ;;
esac
OUT="$DEST/studystation-$(date +%F-%H%M).db"
./venv/bin/python - "$DB" "$OUT" <<'PY'
import sqlite3, sys
src, dst = sqlite3.connect(sys.argv[1]), sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close(); src.close()
PY
gzip -f "$OUT"
find "$DEST" -name 'studystation-*.db.gz' -mtime +14 -delete
echo "backup: $OUT.gz"
