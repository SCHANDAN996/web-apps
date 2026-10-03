"""
python -m app.jobs run [--only ssc,isro] [--disable x,y] [--max-new 40] [--dry-run]
python -m app.jobs health
python -m app.jobs summary                       # JSON state for an AI agent
python -m app.jobs add URL [--title T] [--org O] [--category C]
python -m app.jobs upcoming --title T --org O --expected 2027-04 --source URL
python -m app.jobs cleanup [--keep-closed-days 30] [--pending-days 30]
python -m app.jobs digest [--out FILE] [--telegram] [--mark-sent]
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
    sub.add_parser('summary')
    a = sub.add_parser('add')
    a.add_argument('url', nargs='+')
    a.add_argument('--title')
    a.add_argument('--org')
    a.add_argument('--category')
    u = sub.add_parser('upcoming')
    u.add_argument('--title', required=True)
    u.add_argument('--org', required=True)
    u.add_argument('--expected', required=True, help='YYYY-MM or YYYY-MM-DD')
    u.add_argument('--source', required=True, help='official calendar/notice URL')
    u.add_argument('--category')
    c = sub.add_parser('cleanup')
    c.add_argument('--keep-closed-days', type=int, default=30)
    c.add_argument('--pending-days', type=int, default=30)
    d = sub.add_parser('digest')
    d.add_argument('--out')
    d.add_argument('--telegram', action='store_true')
    d.add_argument('--mark-sent', action='store_true', help='do not repeat these items next time')
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    ensure_schema(engine)

    if args.cmd == 'health':
        with SessionLocal() as db:
            for h in db.scalars(select(SourceHealth).order_by(SourceHealth.source)):
                state = 'OK ' if not h.consecutive_failures else f'FAIL x{h.consecutive_failures}'
                print(f'{state:9} {h.source:14} items={h.last_items:<4} last_ok={h.last_ok}  {h.last_error or ""}')
        return 0

    if args.cmd in ('summary', 'add', 'upcoming', 'cleanup', 'digest'):
        from . import manage
        from ..config import SITE_URL
        with SessionLocal() as db:
            if args.cmd == 'summary':
                print(json.dumps(manage.summary(db), ensure_ascii=False, indent=1, default=str))
            elif args.cmd == 'add':
                for url in args.url:
                    try:
                        print(url, '->', manage.add_official(db, url, args.title, args.org, args.category))
                    except Exception as e:
                        print(url, '-> FAILED:', e)
            elif args.cmd == 'upcoming':
                try:
                    print(manage.add_upcoming(db, args.title, args.org, args.expected, args.source, args.category))
                except (manage.Refused, ValueError) as e:
                    print('FAILED:', e)
                    return 2
            elif args.cmd == 'cleanup':
                print(json.dumps(manage.cleanup(db, args.keep_closed_days, args.pending_days)))
            else:
                d = manage.digest(db)
                text = manage.digest_markdown(d, SITE_URL)
                if args.out:
                    from pathlib import Path
                    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
                    Path(args.out).write_text(text, encoding='utf-8')
                print(text)
                sent_ok = True
                if args.telegram:
                    try:
                        print(manage.send_telegram(text))
                    except manage.TelegramError as e:
                        print('telegram FAILED:', e)
                        sent_ok = False
                if args.mark_sent and sent_ok:
                    manage.mark_notified(db, d)
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
