"""Business logic: practice sets, CBT mocks, scoring, mistake revision, stats."""
import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session

from .catalog import LEVEL_RANK
from .models import (Attempt, AttemptAnswer, Device, Exam, Question, ReviewCard,
                     Subject, Topic)

USABLE = Question.review_status.in_(('unreviewed', 'verified'))
LEITNER_DAYS = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35}
MOCK_GRACE_SEC = 30
IST = timedelta(hours=5, minutes=30)


def today_ist():
    """Students' day boundary is midnight in India, not UTC."""
    return (datetime.utcnow() + IST).date()


class NotAllowed(Exception):
    pass


# ---------------------------------------------------------------- helpers
def has_lang(lang):
    return Question.text_hi.is_not(None) if lang == 'hi' else Question.text_en.is_not(None)


def public_question(q: Question, n=None):
    """What the client may see before answering — never the answer."""
    return {
        'id': q.id, 'n': n,
        'text': {'hi': q.text_hi, 'en': q.text_en},
        'options': {'hi': q.options_hi, 'en': q.options_en},
        'difficulty': q.difficulty,
        'topic': {'hi': q.topic.name_hi, 'en': q.topic.name_en},
        'subject': q.topic.subject.slug,
        'source_type': q.source_type,
        'source_ref': q.source_ref,
        'verified': q.review_status == 'verified',
    }


def reveal(q: Question):
    return {'answer_index': q.answer_index,
            'solution': {'hi': q.solution_hi, 'en': q.solution_en}}


def _pick(db: Session, base_filter, n, lang, seen_ids):
    """Pick n question ids: user's language first, unseen first, then the rest."""
    ids_lang = list(db.scalars(select(Question.id).where(base_filter, has_lang(lang))))
    ids_any = list(db.scalars(select(Question.id).where(base_filter)))
    pools = [
        [i for i in ids_lang if i not in seen_ids],
        [i for i in ids_any if i not in seen_ids and i not in set(ids_lang)],
        [i for i in ids_lang if i in seen_ids],
        [i for i in ids_any if i in seen_ids and i not in set(ids_lang)],
    ]
    chosen = []
    for pool in pools:
        random.shuffle(pool)
        chosen.extend(pool[: n - len(chosen)])
        if len(chosen) >= n:
            break
    return chosen


def seen_question_ids(db: Session, device: Device):
    return set(db.scalars(
        select(AttemptAnswer.question_id).join(Attempt).where(Attempt.device_id == device.id)))


# ---------------------------------------------------------------- practice
def start_practice(db: Session, device: Device, topic_id: int, count: int = 10, difficulty=None, since_days=None):
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise LookupError('topic')
    f = and_(Question.topic_id == topic_id, USABLE)
    if difficulty in ('easy', 'medium', 'hard'):
        f = and_(f, Question.difficulty == difficulty)
    if since_days:   # e.g. current-affairs quiz for the last 7 / 30 days
        f = and_(f, Question.created_at >= datetime.utcnow() - timedelta(days=since_days))
    ids = _pick(db, f, max(1, min(count, 25)), device.lang, seen_question_ids(db, device))
    if not ids:
        raise LookupError('no_questions')
    a = Attempt(device_id=device.id, mode='practice', topic_id=topic_id,
                title=topic.name_hi if device.lang == 'hi' else topic.name_en, question_ids=ids)
    db.add(a)
    db.commit()
    return a


def start_retry_wrong(db: Session, device: Device, attempt_id: int):
    """Practice the questions answered wrongly in a finished attempt — right away, with solutions.
    (Revision cards for them are scheduled from tomorrow, so this is the same-day pass.)"""
    src = db.get(Attempt, attempt_id)
    if src is None or src.device_id != device.id:
        raise LookupError('attempt')
    if src.finished_at is None:
        raise NotAllowed('not_finished')
    wrong = {x.question_id for x in src.answers if x.correct is False}
    ids = [q for q in src.question_ids if q in wrong][:25]
    if not ids:
        raise LookupError('no_questions')
    title = ('गलतियाँ: ' if device.lang == 'hi' else 'Mistakes: ') + (src.title or '')
    a = Attempt(device_id=device.id, mode='practice', topic_id=src.topic_id, title=title[:200], question_ids=ids)
    db.add(a)
    db.commit()
    return a


# ---------------------------------------------------------------- mock
def section_pool_filter(subject_slug, subject_id):
    f = and_(Question.topic.has(Topic.subject_id == subject_id), USABLE)
    if subject_slug == 'english':
        f = and_(f, Question.text_en.is_not(None))   # English section must be in English
    return f


def mock_plan(db: Session, exam: Exam):
    """Which sections of this exam we can build honestly from the question bank."""
    plan = []
    for sec in exam.sections:
        available = db.scalar(select(func.count(Question.id)).where(
            section_pool_filter(sec.subject.slug, sec.subject_id)))
        plan.append({'section': sec, 'available': available, 'ok': available >= sec.questions})
    return plan


def start_mock(db: Session, device: Device, exam_slug: str):
    exam = db.scalar(select(Exam).where(Exam.slug == exam_slug))
    if exam is None:
        raise LookupError('exam')
    plan = mock_plan(db, exam)
    usable = [p for p in plan if p['ok']]
    if not usable:
        raise LookupError('no_questions')
    seen = seen_question_ids(db, device)
    ids, total_q = [], sum(s.questions for s in exam.sections)
    for p in usable:
        sec = p['section']
        ids += _pick(db, section_pool_filter(sec.subject.slug, sec.subject_id), sec.questions, device.lang, seen)
    used_q = sum(p['section'].questions for p in usable)
    # Partial mocks get proportional time so the pace matches the real exam.
    duration = round(exam.duration_min * 60 * used_q / total_q)
    name = exam.name_hi if device.lang == 'hi' else exam.name_en
    a = Attempt(device_id=device.id, mode='mock', exam_id=exam.id, question_ids=ids,
                duration_sec=duration,
                title=name + ('' if used_q == total_q else (' (आंशिक)' if device.lang == 'hi' else ' (Partial)')))
    db.add(a)
    db.commit()
    return a


def attempt_payload(db: Session, a: Attempt):
    qs = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(a.question_ids)))}
    answers = {x.question_id: x for x in a.answers}
    items = []
    for n, qid in enumerate(a.question_ids, 1):
        q = qs[qid]
        item = public_question(q, n)
        ans = answers.get(qid)
        item['state'] = {'chosen': ans.chosen_index if ans else None, 'marked': bool(ans and ans.marked)}
        if a.mode == 'practice' and ans and ans.chosen_index is not None:
            item['state'].update(reveal(q), correct=ans.correct)
        items.append(item)
    sections = []
    if a.mode == 'mock' and a.exam:
        for sec in a.exam.sections:
            idx = [i for i, it in enumerate(items) if it['subject'] == sec.subject.slug]
            if idx:
                sections.append({'subject': sec.subject.slug, 'name': {'hi': sec.subject.name_hi, 'en': sec.subject.name_en},
                                 'start': idx[0], 'count': len(idx),
                                 'marks': sec.marks_per_q, 'negative': sec.negative_per_q})
    remaining = None
    if a.duration_sec:
        remaining = max(0, a.duration_sec - int((datetime.utcnow() - a.started_at).total_seconds()))
    return {'id': a.id, 'mode': a.mode, 'title': a.title, 'questions': items, 'sections': sections,
            'duration_sec': a.duration_sec, 'remaining_sec': remaining,
            'finished': a.finished_at is not None}


def close_if_expired(db: Session, device: Device, a: Attempt):
    """A mock whose time (plus grace) is over is submitted by the server — the phone may have been offline."""
    if a.finished_at is None and _mock_deadline_passed(a):
        finish_attempt(db, device, a)
    return a


def _mock_deadline_passed(a: Attempt):
    if a.mode != 'mock' or not a.duration_sec:
        return False
    return (datetime.utcnow() - a.started_at).total_seconds() > a.duration_sec + MOCK_GRACE_SEC


def record_answer(db: Session, device: Device, a: Attempt, question_id: int, chosen_index, time_ms=0, marked=False):
    if a.device_id != device.id:
        raise NotAllowed('not_your_attempt')
    if a.finished_at is not None:
        raise NotAllowed('finished')
    if question_id not in a.question_ids:
        raise NotAllowed('not_in_attempt')
    if _mock_deadline_passed(a):
        raise NotAllowed('time_up')
    if chosen_index is not None and chosen_index not in (0, 1, 2, 3):
        raise ValueError('chosen_index')
    q = db.get(Question, question_id)
    ans = db.scalar(select(AttemptAnswer).where(AttemptAnswer.attempt_id == a.id,
                                                AttemptAnswer.question_id == question_id))
    if a.mode == 'practice' and ans and ans.chosen_index is not None:
        raise NotAllowed('already_answered')   # practice answers are final once revealed
    ans = ans or AttemptAnswer(attempt_id=a.id, question_id=question_id)
    ans.chosen_index = chosen_index
    ans.correct = None if chosen_index is None else chosen_index == q.answer_index
    spent = max(0, min(int(time_ms or 0), 60 * 60 * 1000))
    # Mock questions can be revisited, so time adds up across visits.
    ans.time_ms = (ans.time_ms or 0) + spent
    ans.marked = bool(marked)
    ans.answered_at = datetime.utcnow()
    db.add(ans)
    if a.mode == 'practice' and ans.correct is False:
        add_mistake(db, device, question_id)
    db.commit()
    if a.mode == 'practice' and chosen_index is not None:
        return {'correct': ans.correct, **reveal(q)}
    return {'saved': True}


def finish_attempt(db: Session, device: Device, a: Attempt):
    if a.device_id != device.id:
        raise NotAllowed('not_your_attempt')
    if a.finished_at is None:
        a.finished_at = datetime.utcnow()
        marks = {}
        if a.mode == 'mock' and a.exam:
            marks = {s.subject.slug: (s.marks_per_q, s.negative_per_q) for s in a.exam.sections}
        qs = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(a.question_ids)))}
        score = max_score = 0.0
        for qid in a.question_ids:
            m, neg = marks.get(qs[qid].topic.subject.slug, (1, 0))
            max_score += m
        for ans in a.answers:
            m, neg = marks.get(qs[ans.question_id].topic.subject.slug, (1, 0))
            if ans.correct is True:
                score += m
            elif ans.correct is False:
                score -= neg
                if a.mode == 'mock':
                    add_mistake(db, device, ans.question_id)
        a.score, a.max_score = round(score, 2), max_score
        db.commit()
    return result_payload(db, a)


def result_payload(db: Session, a: Attempt):
    qs = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(a.question_ids)))}
    answers = {x.question_id: x for x in a.answers}
    by_section = defaultdict(lambda: {'total': 0, 'correct': 0, 'wrong': 0, 'skipped': 0, 'time_ms': 0})
    review = []
    for n, qid in enumerate(a.question_ids, 1):
        q = qs[qid]
        ans = answers.get(qid)
        sec = by_section[q.topic.subject.slug]
        sec['name'] = {'hi': q.topic.subject.name_hi, 'en': q.topic.subject.name_en}
        sec['total'] += 1
        status = 'skipped' if not ans or ans.chosen_index is None else ('correct' if ans.correct else 'wrong')
        sec[status] += 1
        sec['time_ms'] += ans.time_ms if ans else 0
        review.append({**public_question(q, n), **reveal(q),
                       'chosen': ans.chosen_index if ans else None, 'status': status,
                       'time_ms': ans.time_ms if ans else 0})
    attempted = sum(s['correct'] + s['wrong'] for s in by_section.values())
    correct = sum(s['correct'] for s in by_section.values())
    return {'id': a.id, 'mode': a.mode, 'title': a.title, 'score': a.score, 'max_score': a.max_score,
            'finished': a.finished_at is not None,
            'accuracy': round(100 * correct / attempted) if attempted else None,
            'attempted': attempted, 'total': len(a.question_ids),
            'sections': dict(by_section), 'review': review}


# ---------------------------------------------------------------- revision
def add_mistake(db: Session, device: Device, question_id: int):
    card = db.scalar(select(ReviewCard).where(ReviewCard.device_id == device.id,
                                              ReviewCard.question_id == question_id))
    if card is None:
        card = ReviewCard(device_id=device.id, question_id=question_id, box=1)
    else:
        card.lapses += 1
        card.box = 1
    card.due_on = today_ist() + timedelta(days=LEITNER_DAYS[1])
    db.add(card)


def due_cards(db: Session, device: Device, limit=20, today=None):
    today = today or today_ist()
    return list(db.scalars(select(ReviewCard).where(
        ReviewCard.device_id == device.id, ReviewCard.due_on <= today
    ).order_by(ReviewCard.due_on, ReviewCard.box).limit(limit)))


def next_due(db: Session, device: Device, today=None):
    """Date the next revision card falls due (after today), or None."""
    today = today or today_ist()
    return db.scalar(select(func.min(ReviewCard.due_on)).where(
        ReviewCard.device_id == device.id, ReviewCard.due_on > today))


def review_card(db: Session, device: Device, question_id: int, chosen_index: int, today=None):
    today = today or today_ist()
    card = db.scalar(select(ReviewCard).where(ReviewCard.device_id == device.id,
                                              ReviewCard.question_id == question_id))
    if card is None:
        raise LookupError('card')
    if card.due_on > today:
        raise NotAllowed('not_due')     # a retry/double tap must not jump a card ahead
    q = card.question
    correct = chosen_index == q.answer_index
    if correct:
        card.box = min(card.box + 1, 5)
    else:
        card.box = 1
        card.lapses += 1
    card.due_on = today + timedelta(days=LEITNER_DAYS[card.box])
    db.commit()
    return {'correct': correct, 'box': card.box, 'due_on': card.due_on.isoformat(), **reveal(q)}


# ---------------------------------------------------------------- stats
def device_stats(db: Session, device: Device, today=None):
    today = today or today_ist()
    rows = db.execute(
        select(Topic.id, Topic.name_hi, Topic.name_en, Subject.slug,
               func.count(AttemptAnswer.id), func.sum(case((AttemptAnswer.correct.is_(True), 1), else_=0)),
               Subject.name_hi, Subject.name_en)
        .select_from(AttemptAnswer).join(Attempt).join(Question).join(Topic).join(Subject)
        .where(Attempt.device_id == device.id, AttemptAnswer.chosen_index.is_not(None))
        .group_by(Topic.id)).all()
    topics = [{'id': tid, 'name': {'hi': hi, 'en': en}, 'subject': subj, 'attempted': n,
               'correct': int(c or 0), 'accuracy': round(100 * (c or 0) / n), 'subject_name': {'hi': shi, 'en': sen}}
              for tid, hi, en, subj, n, c, shi, sen in rows]
    by_subject = {}
    for t in topics:
        b = by_subject.setdefault(t['subject'], {'slug': t['subject'], 'name': t['subject_name'], 'attempted': 0, 'correct': 0})
        b['attempted'] += t['attempted']
        b['correct'] += t['correct']
    subjects = sorted(({**b, 'accuracy': round(100 * b['correct'] / b['attempted'])} for b in by_subject.values()),
                      key=lambda b: -b['attempted'])
    attempted = sum(t['attempted'] for t in topics)
    correct = sum(t['correct'] for t in topics)
    weak = sorted([t for t in topics if t['attempted'] >= 5 and t['accuracy'] < 60], key=lambda t: t['accuracy'])
    days = {(d + IST).date() for d in db.scalars(
        select(AttemptAnswer.answered_at).join(Attempt).where(Attempt.device_id == device.id))}
    streak, d = 0, today
    if d not in days:
        d -= timedelta(days=1)       # streak survives until the day is over
    while d in days:
        streak += 1
        d -= timedelta(days=1)
    due = db.scalar(select(func.count(ReviewCard.id)).where(
        ReviewCard.device_id == device.id, ReviewCard.due_on <= today))
    start_of_today = datetime.combine(today, datetime.min.time()) - IST          # IST midnight in UTC
    today_answered = db.scalar(select(func.count(AttemptAnswer.id)).join(Attempt).where(
        Attempt.device_id == device.id, AttemptAnswer.chosen_index.is_not(None),
        AttemptAnswer.answered_at >= start_of_today)) or 0
    week = [{'date': (today - timedelta(days=i)).isoformat(), 'weekday': (today - timedelta(days=i)).weekday(),
             'active': (today - timedelta(days=i)) in days} for i in range(6, -1, -1)]
    # last 4 full weeks, Monday-aligned, for the activity calendar on /progress
    first = today - timedelta(days=today.weekday() + 21)
    month = [{'date': (first + timedelta(days=i)).isoformat(), 'active': (first + timedelta(days=i)) in days,
              'future': first + timedelta(days=i) > today} for i in range(28)]
    active_days_28 = sum(1 for d in month if d['active'])
    mocks = db.scalars(select(Attempt).where(Attempt.device_id == device.id, Attempt.mode == 'mock',
                                             Attempt.finished_at.is_not(None)).order_by(Attempt.finished_at.desc()).limit(10))
    return {'attempted': attempted, 'correct': correct,
            'accuracy': round(100 * correct / attempted) if attempted else None,
            'topics': sorted(topics, key=lambda t: -t['attempted']), 'weak_topics': weak[:5],
            'streak_days': streak, 'due_reviews': due, 'today_answered': today_answered, 'week': week,
            'month': month, 'active_days_28': active_days_28, 'subjects': subjects,
            'mocks': [{'id': m.id, 'title': m.title, 'score': m.score, 'max_score': m.max_score,
                       'pct': max(0, round(100 * (m.score or 0) / m.max_score)) if m.max_score else 0,
                       'date': m.finished_at.date().isoformat()} for m in mocks]}


# ---------------------------------------------------------------- jobs
def jobs_query(qualification=None, category=None, status='active', today=None):
    from .models import Job
    today = today or today_ist()
    # Students only see facts read from an official notice (or old imports, labelled).
    q = select(Job).where(Job.status.in_(('verified', 'legacy')))
    if status == 'active':
        q = q.where(Job.last_date >= today, Job.job_type == 'latest').order_by(Job.last_date)
    elif status == 'closed':
        q = q.where(Job.last_date < today, Job.job_type == 'latest').order_by(Job.last_date.desc())
    elif status == 'upcoming':   # from official exam calendars
        q = q.where(Job.job_type == 'upcoming', Job.start_date >= today - timedelta(days=7)).order_by(Job.start_date)
    elif status == 'updates':   # admit cards, results, answer keys from official boards
        # Old imports carry headlines copied from aggregator sites — only official items here.
        q = q.where(Job.job_type.in_(('admit', 'results', 'answer')), Job.status == 'verified').order_by(Job.created_at.desc())
    else:   # 'undated' — recruitment without a machine-readable deadline yet
        q = q.where(Job.last_date.is_(None), Job.job_type == 'latest', Job.status == 'verified').order_by(Job.created_at.desc())
    if category:
        q = q.where(Job.category == category)
    if qualification in LEVEL_RANK:
        ok = [lv for lv, r in LEVEL_RANK.items() if r <= LEVEL_RANK[qualification]]
        q = q.where(or_(Job.min_qualification.in_(ok), Job.min_qualification.is_(None)))
    return q
