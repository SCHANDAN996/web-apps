"""
python -m app.jobs run [--only ssc,isro] [--disable x,y] [--max-new 40] [--dry-run]
python -m app.jobs health
"""
import argparse
import fcntl
import json
import logging
import os
import sys

from sqlalchemy import select

from ..db import SessionLocal, engine, ensure_schema
from ..models import SourceHealth
from .pipeline import run
from .sources import enabled_sources


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m app.jobs')
    sub = p.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--only', default='')
    r.add_argument('--disable', default=os.environ.get('JOB_SOURCES_DISABLED', ''))
    r.add_argument('--max-new', type=int, default=40)
    r.add_argument('--dry-run', action='store_true')
    sub.add_parser('health')
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    ensure_schema(engine)

    if args.cmd == 'health':
        with SessionLocal() as db:
            for h in db.scalars(select(SourceHealth).order_by(SourceHealth.source)):
                state = 'OK ' if not h.consecutive_failures else f'FAIL x{h.consecutive_failures}'
                print(f'{state:9} {h.source:14} items={h.last_items:<4} last_ok={h.last_ok}  {h.last_error or ""}')
        return 0

    # Never run two scrapes at once (cron overlap).
    lock = open('/tmp/studystation-jobs.lock', 'w')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print('another run is in progress', file=sys.stderr)
        return 1
    only = {s for s in args.only.split(',') if s}
    disabled = {s for s in args.disable.split(',') if s}
    with SessionLocal() as db:
        report = run(db, enabled_sources(only, disabled), max_new_per_source=args.max_new, dry_run=args.dry_run)
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == '__main__':
    sys.exit(main())
