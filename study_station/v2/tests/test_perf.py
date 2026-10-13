"""The question bank has ~70,000 rows: building a mock or listing the exams must not grow with it badly."""
import time

from sqlalchemy import event

from app import services
from app.db import engine


def test_choosing_from_a_whole_subject_is_quick_and_keeps_its_order_of_preference():
    own = list(range(0, 20000, 2))                # in the learner's language
    other = list(range(1, 20000, 2))
    seen = set(range(0, 20000, 4))
    start = time.perf_counter()
    chosen = services._choose(own, other, 25, seen)
    assert time.perf_counter() - start < 2        # was quadratic: ~20,000 set builds of 10,000 ids
    assert len(chosen) == len(set(chosen)) == 25
    assert all(i % 2 == 0 and i not in seen for i in chosen)      # own language and unseen first


def test_choosing_falls_back_to_other_language_then_seen():
    chosen = services._choose([0, 2], [1, 3], 4, {2, 3})
    assert chosen == [0, 1, 2, 3]                 # unseen own language, unseen other, seen own, seen other


def test_pool_splits_a_topic_by_language(db):
    from conftest import topic_id
    from sqlalchemy import and_
    from app.models import Question
    own, other = services._pool(db, and_(Question.topic_id == topic_id(db, 'percentage'), services.USABLE), 'hi')
    assert len(own) == 30 and other == []


def test_mock_list_counts_the_bank_once_not_once_per_section(client):
    hits = []

    def spy(conn, cursor, statement, *_):
        if 'FROM question' in statement:
            hits.append(statement)

    services._counts['value'] = None              # forget the one-minute copy: count afresh
    event.listen(engine, 'before_cursor_execute', spy)
    try:
        r = client.get('/mock')
        again = client.get('/mock')
    finally:
        event.remove(engine, 'before_cursor_execute', spy)
    assert r.status_code == again.status_code == 200
    assert len(hits) == 1                         # one count for all exams, reused by the next visitor
