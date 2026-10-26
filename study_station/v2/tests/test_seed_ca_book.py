"""Current-affairs book questions -> the CA topic, dated by their All India Radio report."""
from datetime import datetime

from sqlalchemy import select

from app import current_affairs as ca, seed
from app.models import Question


def test_ca_book_questions_are_bilingual_dated_and_idempotent(db):
    first = seed.seed_ca_book_questions(db)
    assert first['imported'] >= 200 and first['skipped'] == 0
    topic = ca.ca_topic(db)
    rows = list(db.scalars(select(Question).where(Question.import_key.like('ca-book/%'))))
    assert len(rows) == first['imported']
    assert all(r.topic_id == topic.id and r.text_hi and r.text_en and len(r.options_hi) == 4 for r in rows)
    assert all(r.source_ref.startswith('https://newsonair.gov.in/') for r in rows)
    padma = next(r for r in rows if 'Padma Vibhushan posthumously' in r.text_en)
    assert padma.created_at == datetime(2026, 5, 25) and 'पद्म विभूषण' in padma.text_hi
    # re-running keeps the same rows and the admin's decision
    padma.review_status = 'flagged'
    db.commit()
    assert seed.seed_ca_book_questions(db)['imported'] == first['imported']
    assert len(list(db.scalars(select(Question).where(Question.import_key.like('ca-book/%'))))) == len(rows)
    db.refresh(padma)
    assert padma.review_status == 'flagged'
    padma.review_status = 'unreviewed'
    db.commit()


def test_air_source_line_parser():
    m = seed.AIR_SOURCE.search('All India Radio News, 4 Oct 2026 (https://newsonair.gov.in/x-y/)')
    assert m and (m[1], m[2], m[3], m[4]) == ('4', 'Oct', '2026', 'https://newsonair.gov.in/x-y/')
    assert not seed.AIR_SOURCE.search('Source: some blog (https://example.com/)')
