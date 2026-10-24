"""
Generate new MCQs with Claude into the review queue.

  python -m app.generate --topic ga/polity --n 10 --level 10th
  python -m app.generate --fill --min 60 --n 10          # every topic with < 60 usable questions
  python -m app.generate --fill --subject science --dry-run

New questions are labelled "AI-generated · not yet reviewed"; any whose answer the
independent re-check disagrees with goes to the admin queue hidden ("flagged").
"""
import argparse
import logging
import sys

from sqlalchemy import func, select

from . import ai
from .db import SessionLocal, engine, ensure_schema
from .models import Question, Subject, Topic
from .services import USABLE


def usable_counts(db):
    return dict(db.execute(select(Question.topic_id, func.count()).where(USABLE).group_by(Question.topic_id)).all())


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m app.generate')
    p.add_argument('--topic', help='subject/topic, e.g. ga/polity')
    p.add_argument('--subject', help='limit --fill to one subject')
    p.add_argument('--fill', action='store_true', help='top up thin topics')
    p.add_argument('--min', type=int, default=60)
    p.add_argument('--n', type=int, default=10, help='questions per call (≤ 20 keeps quality high)')
    p.add_argument('--level', default='10th', choices=['10th', '12th', 'graduate'])
    p.add_argument('--max-topics', type=int, default=10, help='cost guard for --fill')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    ensure_schema(engine)
    with SessionLocal() as db:
        if args.topic:
            subj, slug = args.topic.split('/', 1)
            topics = list(db.scalars(select(Topic).join(Subject).where(Subject.slug == subj, Topic.slug == slug)))
            if not topics:
                print(f'unknown topic {args.topic}', file=sys.stderr)
                return 2
        elif args.fill:
            counts = usable_counts(db)
            q = select(Topic).join(Subject).order_by(Subject.id, Topic.order)
            if args.subject:
                q = q.where(Subject.slug == args.subject)
            topics = [t for t in db.scalars(q) if counts.get(t.id, 0) < args.min][: args.max_topics]
        else:
            p.error('give --topic or --fill')
        for t in topics:
            label = f'{t.subject.slug}/{t.slug}'
            if args.dry_run:
                print('would generate', args.n, 'for', label)
                continue
            try:
                stats = ai.generate_questions(db, t, args.level, min(args.n, 20))
                print(label, stats)
            except ai.AIUnavailable as e:
                print(label, 'FAILED:', e)
                if str(e) in ('not_configured', 'auth'):
                    return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
