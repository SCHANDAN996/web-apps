"""
Load reference data, questions and jobs.  Safe to run again — existing rows are
updated, not duplicated.

    python -m app.seed            # uses ../books and ../website/js/jobs_data.js
"""
import re
import sys
import hashlib
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import books, catalog
from .db import Base, SessionLocal, engine, ensure_schema
from .importers import (discover_practice_files, is_translation_pair, parse_jobs_js,
                        parse_mcq_text, quality_problem)
from .models import Exam, ExamSection, Job, Question, Subject, Topic

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent   # study_station/


def seed_catalog(db: Session):
    subjects = {}
    for slug, hi, en in catalog.SUBJECTS:
        s = db.scalar(select(Subject).where(Subject.slug == slug)) or Subject(slug=slug)
        s.name_hi, s.name_en = hi, en
        db.add(s)
        subjects[slug] = s
    db.flush()
    for subj, topics in catalog.TOPICS.items():
        for order, (slug, hi, en) in enumerate(topics):
            t = db.scalar(select(Topic).where(Topic.subject_id == subjects[subj].id, Topic.slug == slug))
            t = t or Topic(subject_id=subjects[subj].id, slug=slug)
            t.name_hi, t.name_en, t.order = hi, en, order
            db.add(t)
    for slug, body, hi, en, stage, level, minutes, sections, note_hi, note_en in catalog.EXAMS:
        e = db.scalar(select(Exam).where(Exam.slug == slug)) or Exam(slug=slug)
        e.body, e.name_hi, e.name_en, e.stage_en, e.level = body, hi, en, stage, level
        e.duration_min, e.pattern_note_hi, e.pattern_note_en = minutes, note_hi, note_en
        db.add(e)
        db.flush()
        for sec in list(e.sections):
            db.delete(sec)
        db.flush()
        for order, (subj, n, marks, neg) in enumerate(sections):
            db.add(ExamSection(exam_id=e.id, subject_id=subjects[subj].id, questions=n,
                               marks_per_q=marks, negative_per_q=neg, order=order))
    db.commit()


def seed_questions(db: Session, root=PROJECT_DIR):
    topics = {(t.subject.slug, t.slug): t for t in db.scalars(select(Topic))}
    # Pick the richest file for each (level, subject, topic, lang, set) — some sets
    # exist twice (a Prompts/ copy and a final copy).
    best, targets = {}, {}
    for level, subj, topic, lang, set_no, path in discover_practice_files(root):
        if (level, subj, topic) not in targets:
            # Chapter folder → catalog topic (same mapping the Books pages use; chapter.json may override).
            chapter_dir = path.parent.parent if path.parent.name == 'Prompts' else path.parent
            targets[(level, subj, topic)] = books.topic_for_chapter(subj, topic, books.load_meta(chapter_dir))
        qs = parse_mcq_text(path.read_text(encoding='utf-8'))
        key = (level, subj, topic, lang, set_no)
        if key not in best or len(qs) > len(best[key]):
            best[key] = qs

    merged = {}
    for (level, subj, topic, lang, set_no), qs in best.items():
        for q in qs:
            merged.setdefault((level, subj, topic, set_no, q.number), {})[lang] = q

    existing = {q.import_key: q for q in db.scalars(select(Question).where(Question.import_key.is_not(None)))}

    def upsert(key, t, level, en, hi):
        primary = en or hi
        problems = sorted({p for p in (quality_problem(x) for x in (en, hi) if x) if p})
        row = existing.get(key) or Question(import_key=key)
        row.topic_id, row.level, row.difficulty = t.id, level, primary.difficulty
        row.text_en, row.options_en, row.solution_en = (en.text, en.options, en.solution) if en else (None, None, None)
        row.text_hi, row.options_hi, row.solution_hi = (hi.text, hi.options, hi.solution) if hi else (None, None, None)
        row.answer_index = primary.answer_index
        row.source_type = 'ai_generated'
        # The generator's "Source: SSC CGL 2019" lines are unverified claims —
        # keep them for reviewers only, never show them as PYQ.
        row.source_ref = None
        if row.review_status != 'verified':
            row.review_status = 'flagged' if problems else 'unreviewed'
            note = ','.join(problems) if problems else (
                'claimed source: ' + primary.source_claim if primary.source_claim else None)
            row.review_note = note[:200] if note else None
        stats['flagged' if row.review_status == 'flagged' else 'imported'] += 1
        stats['bilingual'] += bool(en and hi)
        db.add(row)

    stats = {'imported': 0, 'flagged': 0, 'bilingual': 0, 'skipped_topic': 0}
    for (level, subj, topic, set_no, num), pair in merged.items():
        t = topics.get(targets[(level, subj, topic)])
        if t is None:
            stats['skipped_topic'] += 1
            continue
        en, hi = pair.get('en'), pair.get('hi')
        key = f'{level}/{subj}/{topic}/s{set_no}/q{num}'
        if en and hi and is_translation_pair(en, hi):
            upsert(key, t, level, en, hi)
        else:
            if en:
                upsert(key + '/en', t, level, en, None)
            if hi:
                upsert(key + '/hi', t, level, None, hi)
    db.commit()
    return stats


DATE_RE = re.compile(r'(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{2,4})')


def parse_indian_date(text):
    m = DATE_RE.search(text or '')
    if not m:
        return None
    d, mth, y = (int(x) for x in m.groups())
    y = y + 2000 if y < 100 else y
    try:
        return date(y, mth, d)
    except ValueError:
        return None


def guess_qualification(text):
    t = (text or '').lower()
    if re.search(r'graduat|degree|b\.?\s?tech|b\.?e\b|bachelor|स्नातक|post graduate|mba|llb', t):
        return 'graduate'
    if re.search(r'12th|10\+2|intermediate|hsc|इंटर|12वीं', t):
        return '12th'
    if re.search(r'10th|matric|high school|ssc pass|10वीं|iti', t):
        return '10th'
    return None


def slugify(text, max_len=90):
    s = re.sub(r'[^a-z0-9]+', '-', (text or '').lower()).strip('-')
    return s[:max_len].rstrip('-') or 'job'


def seed_jobs(db: Session, jobs_js=PROJECT_DIR / 'website' / 'js' / 'jobs_data.js'):
    if not Path(jobs_js).exists():
        return 0
    rows = parse_jobs_js(Path(jobs_js).read_text(encoding='utf-8'))
    existing = {j.slug for j in db.scalars(select(Job))}
    added = 0
    for i, r in enumerate(rows):
        base = slugify(r.get('title'))
        slug = base
        n = 2
        while slug in existing:
            slug = f'{base}-{n}'
            n += 1
        from .jobs.sources import is_official
        official = (r.get('official') or '').strip()
        if not is_official(official):          # old feed often pointed at aggregators
            official = None
        db.add(Job(
            slug=slug, title=r.get('title') or 'Untitled', org=r.get('org'),
            category=r.get('category') or 'govt', job_type=r.get('type') or 'latest',
            vacancies=r.get('vacancies'), eligibility=r.get('eligibility'),
            min_qualification=guess_qualification(r.get('eligibility')),
            last_date=parse_indian_date(r.get('deadline')), last_date_text=r.get('deadline'),
            official_url=official, source='jobs_data.js import', status='legacy',
            verified_at=None, created_at=datetime.utcnow(),
        ))
        existing.add(slug)
        added += 1
    db.commit()
    return added


def clean_legacy_links(db: Session):
    """Older imports may carry aggregator links; students must only be sent to official sites."""
    from .jobs.sources import is_official
    n = 0
    for j in db.scalars(select(Job).where(Job.status == 'legacy')):
        for f in ('official_url', 'notification_url'):
            if getattr(j, f) and not is_official(getattr(j, f)):
                setattr(j, f, None)
                n += 1
    db.commit()
    return n


AIR_SOURCE = re.compile(r'All India Radio News, (\d{1,2}) ([A-Za-z]{3,9}) (\d{4}) \((https://newsonair\.gov\.in/[^\s)]+)\)')
MONTHS = {m: i for i, m in enumerate('jan feb mar apr may jun jul aug sep oct nov dec'.split(), 1)}
LEVEL_RANK = {'10th': 0, '12th': 1, 'graduate': 2}


def seed_ca_book_questions(db: Session, root=PROJECT_DIR):
    """The current-affairs chapters' practice questions (hi+en, each from one All India Radio report) go into the
    current-affairs topic dated by their report, so the 'this week / this month' CA quizzes pick them up only
    while they are recent. Same fact in several books = one question. Safe to re-run; admin decisions stay."""
    from . import current_affairs as ca
    topic = ca.ca_topic(db)
    if topic is None:
        return {'imported': 0, 'skipped': 0}
    level_of = {'10th_Level': '10th', '12th_Level': '12th', 'Graduation_Level': 'graduate'}
    found = {}
    skipped = 0
    for ch in sorted(Path(root, 'books').glob('*/GK/*/Chapter_*Current_Affairs*')):
        level = level_of.get(ch.relative_to(Path(root, 'books')).parts[0])
        for n in range(1, 7):
            en_p, hi_p = ch / f'Practice_en_Set_{n:02d}.txt', ch / f'Practice_hi_Set_{n:02d}.txt'
            if not (level and en_p.is_file() and hi_p.is_file()):
                continue
            hi_by_no = {q.number: q for q in parse_mcq_text(hi_p.read_text(encoding='utf-8'))}
            for en in parse_mcq_text(en_p.read_text(encoding='utf-8')):
                hi = hi_by_no.get(en.number)
                m = AIR_SOURCE.search(en.source_claim or '')
                if (hi is None or hi.answer_index != en.answer_index or quality_problem(en) or quality_problem(hi)
                        or not m or m[2][:3].lower() not in MONTHS):
                    skipped += 1
                    continue
                key = 'ca-book/' + hashlib.sha1(en.text.strip().lower().encode()).hexdigest()[:16]
                day = datetime(int(m[3]), MONTHS[m[2][:3].lower()], int(m[1]))
                old = found.get(key)
                if old is None or LEVEL_RANK[level] < LEVEL_RANK[old[0]]:
                    found[key] = (level, en, hi, day, m[4])
    existing = {q.import_key: q for q in db.scalars(select(Question).where(Question.import_key.like('ca-book/%')))}
    for key, (level, en, hi, day, link) in found.items():
        row = existing.get(key) or Question(import_key=key)
        row.topic_id, row.level, row.difficulty = topic.id, level, en.difficulty or 'medium'
        row.text_en, row.options_en, row.solution_en = en.text, en.options, en.solution
        row.text_hi, row.options_hi, row.solution_hi = hi.text, hi.options, hi.solution
        row.answer_index = en.answer_index
        row.source_type, row.source_ref = 'ai_generated', link[:200]
        row.created_at = day                       # the report's date: decides the week/month quiz window
        if row.review_status not in ('verified', 'flagged'):
            row.review_status, row.review_note = 'unreviewed', 'AIR fact (book current-affairs chapter)'
        db.add(row)
    db.commit()
    return {'imported': len(found), 'skipped': skipped}


def main():
    ensure_schema(engine)
    with SessionLocal() as db:
        seed_catalog(db)
        print('questions:', seed_questions(db))
        print('current-affairs book questions:', seed_ca_book_questions(db))
        # The old website feed (website/js/jobs_data.js) is no longer imported: its titles were copied
        # from aggregator sites (CLAUDE.md rule 1). Jobs come only from the official job engine now.
        from .jobs.manage import drop_legacy
        print('legacy jobs removed:', drop_legacy(db))


if __name__ == '__main__':
    sys.exit(main())
