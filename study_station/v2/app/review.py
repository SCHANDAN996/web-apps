"""
Question review from the command line — the same actions as /admin, for the
content-reviewer agent.

  python -m app.review list [--queue reported|flagged|unreviewed] [--subject ga] [--limit 20]
  python -m app.review show ID
  python -m app.review apply FILE.json      # list of edits, see EDIT FORMAT below

EDIT FORMAT (JSON list):
  {"id": 123, "action": "verify" | "flag" | "delete" | "save",
   "answer_index": 0-3, "text_hi": "...", "text_en": "...", "options_hi": [...4], "options_en": [...4],
   "solution_hi": "...", "solution_en": "...", "difficulty": "easy|medium|hard",
   "source_type": "ai_generated|editorial|pyq", "source_ref": "...", "note": "why"}
Only "id" and "action" are required; other fields are changed only when present.
"""
import argparse
import json
import sys
from datetime import datetime

from sqlalchemy import func, select

from .db import SessionLocal, engine, ensure_schema
from .models import Question, QuestionReport, Subject, Topic

FIELDS_TEXT = ('text_hi', 'text_en', 'solution_hi', 'solution_en')


def as_dict(q, reports=None):
    d = {'id': q.id, 'topic': f'{q.topic.subject.slug}/{q.topic.slug}', 'status': q.review_status,
         'note': q.review_note, 'difficulty': q.difficulty, 'answer_index': q.answer_index,
         'source_type': q.source_type, 'source_ref': q.source_ref}
    for f in FIELDS_TEXT + ('options_hi', 'options_en'):
        d[f] = getattr(q, f)
    if reports is not None:
        d['reports'] = [{'reason': r.reason, 'note': r.note} for r in reports]
    return d


def list_queue(db, queue='reported', subject=None, limit=20):
    q = select(Question).join(Topic).join(Subject)
    if queue == 'reported':
        q = q.where(Question.id.in_(select(QuestionReport.question_id).where(QuestionReport.resolved_at.is_(None))))
    else:
        q = q.where(Question.review_status == queue)
    if subject:
        q = q.where(Subject.slug == subject)
    out = []
    for row in db.scalars(q.order_by(Question.id).limit(limit)):
        reps = list(db.scalars(select(QuestionReport).where(QuestionReport.question_id == row.id,
                                                            QuestionReport.resolved_at.is_(None))))
        out.append(as_dict(row, reps))
    return out


class EditError(ValueError):
    pass


def apply_edit(db, e):
    q = db.get(Question, int(e['id']))
    if q is None:
        raise EditError(f'{e["id"]}: not found')
    action = e.get('action', 'save')
    if action == 'delete':
        db.query(QuestionReport).filter_by(question_id=q.id).delete()
        db.delete(q)
        return 'deleted'
    for f in FIELDS_TEXT:
        if f in e:
            setattr(q, f, (e[f] or '').strip() or None)
    for f in ('options_hi', 'options_en'):
        if f in e:
            opts = e[f]
            if opts is not None and (len(opts) != 4 or len({o.strip() for o in opts}) != 4 or not all(o.strip() for o in opts)):
                raise EditError(f'{q.id}: {f} needs four different non-empty options')
            setattr(q, f, [o.strip() for o in opts] if opts else None)
    if 'answer_index' in e:
        if e['answer_index'] not in (0, 1, 2, 3):
            raise EditError(f'{q.id}: answer_index must be 0-3')
        q.answer_index = e['answer_index']
    if e.get('difficulty') in ('easy', 'medium', 'hard'):
        q.difficulty = e['difficulty']
    if e.get('source_type') in ('ai_generated', 'editorial', 'pyq'):
        q.source_type = e['source_type']
    if 'source_ref' in e:
        q.source_ref = (e['source_ref'] or '').strip() or None
    if q.source_type == 'pyq' and not q.source_ref:
        raise EditError(f'{q.id}: a PYQ needs source_ref (exam, year, shift)')
    for lang in ('hi', 'en'):
        if getattr(q, f'text_{lang}') and not getattr(q, f'options_{lang}'):
            raise EditError(f'{q.id}: text_{lang} without options_{lang}')
    if not q.text_hi and not q.text_en:
        raise EditError(f'{q.id}: needs Hindi or English text')
    if action in ('verify', 'flag'):
        q.review_status = 'verified' if action == 'verify' else 'flagged'
        for r in db.scalars(select(QuestionReport).where(QuestionReport.question_id == q.id,
                                                         QuestionReport.resolved_at.is_(None))):
            r.resolved_at = datetime.utcnow()
    if e.get('note'):
        q.review_note = str(e['note'])[:200]
    q.reviewed_at = datetime.utcnow()
    return action


def main(argv=None):
    p = argparse.ArgumentParser(prog='python -m app.review')
    sub = p.add_subparsers(dest='cmd', required=True)
    l = sub.add_parser('list')
    l.add_argument('--queue', default='reported', choices=['reported', 'flagged', 'unreviewed', 'verified'])
    l.add_argument('--subject')
    l.add_argument('--limit', type=int, default=20)
    s = sub.add_parser('show')
    s.add_argument('id', type=int)
    a = sub.add_parser('apply')
    a.add_argument('file')
    sub.add_parser('stats')
    args = p.parse_args(argv)
    ensure_schema(engine)
    with SessionLocal() as db:
        if args.cmd == 'list':
            print(json.dumps(list_queue(db, args.queue, args.subject, args.limit), ensure_ascii=False, indent=1))
        elif args.cmd == 'show':
            q = db.get(Question, args.id)
            if q is None:
                print('not found', file=sys.stderr)
                return 2
            reps = list(db.scalars(select(QuestionReport).where(QuestionReport.question_id == q.id)))
            print(json.dumps(as_dict(q, reps), ensure_ascii=False, indent=1))
        elif args.cmd == 'stats':
            print(json.dumps(dict(db.execute(select(Question.review_status, func.count())
                                             .group_by(Question.review_status)).all())))
        else:
            edits = json.load(open(args.file, encoding='utf-8'))
            done, failed = 0, 0
            for e in edits:
                try:
                    print(e['id'], apply_edit(db, e))
                    db.commit()
                    done += 1
                except (EditError, KeyError, TypeError) as err:
                    db.rollback()
                    print('FAILED', err)
                    failed += 1
            print(f'applied {done}, failed {failed}')
            return 1 if failed else 0
    return 0


if __name__ == '__main__':
    sys.exit(main())
