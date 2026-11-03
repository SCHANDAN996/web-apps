"""Read-only mock readiness audit. Counts do not certify syllabus/pattern accuracy.

Run: python -m app.mock_audit [--json]
"""
import argparse
import json
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from . import services
from .db import SessionLocal
from .models import Exam, ExamSection, Question, Topic


def audit(db):
    rows = db.execute(select(Topic.subject_id, Topic.slug, Question.level, Question.difficulty,
                             Question.review_status, func.count(Question.id),
                             func.count(Question.text_hi), func.count(Question.text_en))
                      .join(Question, Question.topic_id == Topic.id)
                      .group_by(Topic.subject_id, Topic.slug, Question.level,
                                Question.difficulty, Question.review_status)).all()
    # Match the actual usable filter, including disabled/flagged questions.
    usable = db.execute(select(Topic.subject_id, Question.level, func.count(Question.id),
                               func.count(Question.text_hi), func.count(Question.text_en))
                        .join(Question, Question.topic_id == Topic.id).where(services.USABLE)
                        .group_by(Topic.subject_id, Question.level)).all()
    exams = list(db.scalars(select(Exam).options(selectinload(Exam.sections).joinedload(ExamSection.subject))))
    out = []
    for exam in exams:
        sections = []
        for section in exam.sections:
            pool = [r for r in usable if r[0] == section.subject_id]
            english = section.subject.slug == 'english'
            online = sum(r[4] if english else r[2] for r in pool)
            level_pool = [r for r in pool if r[1] == exam.level]
            sections.append({'subject': section.subject.slug, 'required': section.questions,
                             'online_pool': online,
                             'exact_level_pool': sum(r[4] if english else r[2] for r in level_pool),
                             'hindi_at_level': sum(r[3] for r in level_pool),
                             'english_at_level': sum(r[4] for r in level_pool)})
        gaps = ['online_level_filter_missing', 'attempt_rules_not_snapshotted']
        if exam.slug in ('ibps-clerk', 'ibps-po'):
            gaps.append('sectional_timer_not_enforced')
        if exam.slug == 'ssc-mts':
            gaps.append('separate_sessions_not_enforced')
        if exam.slug == 'ssc-gd':
            gaps.append('hindi_language_section_not_available')
        out.append({'exam': exam.slug, 'level': exam.level, 'sections': sections,
                    'online_count_complete': all(s['online_pool'] >= s['required'] for s in sections),
                    'exact_level_count_complete': all(s['exact_level_pool'] >= s['required'] for s in sections),
                    'engine_gaps': gaps, 'official_pattern_verified': False,
                    'syllabus_mapping_verified': False})
    return {'generated_at': datetime.now(timezone.utc).isoformat(),
            'note': 'Counts only. Original official notifications, exam-topic mapping and linked sets still need verification.',
            'exams': out,
            'topic_breakdown': [dict(zip(('subject_id', 'topic', 'level', 'difficulty', 'review_status',
                                          'questions', 'hindi', 'english'), row)) for row in rows]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    with SessionLocal() as db:
        report = audit(db)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print('Exam | online question count complete | exact-level count complete | missing engine rules')
        for exam in report['exams']:
            print(f"{exam['exam']} | {exam['online_count_complete']} | {exam['exact_level_count_complete']} | {', '.join(exam['engine_gaps']) or 'none identified'}")
        print(report['note'])


if __name__ == '__main__':
    main()
