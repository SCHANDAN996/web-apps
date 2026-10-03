"""
Load reference data, questions and jobs.  Safe to run again — existing rows are
updated, not duplicated.

    python -m app.seed            # uses ../books and ../website/js/jobs_data.js
"""
import re
import sys
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import catalog
from .db import Base, SessionLocal, engine
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
    best = {}
    for level, subj, topic, lang, set_no, path in discover_practice_files(root):
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
        t = topics.get((subj, topic))
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
        official = (r.get('official') or '').strip()
        if not official.lower().startswith(('http://', 'https://')):
            official = None
        db.add(Job(
            slug=slug, title=r.get('title') or 'Untitled', org=r.get('org'),
            category=r.get('category') or 'govt', job_type=r.get('type') or 'latest',
            vacancies=r.get('vacancies'), eligibility=r.get('eligibility'),
            min_qualification=guess_qualification(r.get('eligibility')),
            last_date=parse_indian_date(r.get('deadline')), last_date_text=r.get('deadline'),
            official_url=official, source='jobs_data.js import',
            verified_at=None, created_at=datetime.utcnow(),
        ))
        existing.add(slug)
        added += 1
    db.commit()
    return added


def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_catalog(db)
        print('questions:', seed_questions(db))
        if db.scalar(select(Job.id).limit(1)) is None:
            print('jobs added:', seed_jobs(db))


if __name__ == '__main__':
    sys.exit(main())
