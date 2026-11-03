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


def test_home_practice_catalog_share_one_question_aggregate(client, monkeypatch):
    from app import main
    monkeypatch.setattr(main, 'has_books', lambda: False)
    monkeypatch.setattr(main, 'has_recent_ca', lambda _db: False)
    client.post('/api/v1/me', json={'level': '10th'})
    services.invalidate_question_counts()
    hits = []

    def spy(conn, cursor, statement, *_):
        if 'FROM question' in statement and 'GROUP BY question.topic_id' in statement:
            hits.append(statement)

    event.listen(engine, 'before_cursor_execute', spy)
    try:
        responses = [client.get(url) for url in ['/api/v1/catalog', '/practice', '/', '/api/v1/catalog']]
    finally:
        event.remove(engine, 'before_cursor_execute', spy)
    assert all(r.status_code == 200 for r in responses)
    assert len(hits) == 1  # Previously four full question-bank aggregates across the same navigation.
    assert responses[0].json() == responses[-1].json()


def test_catalog_and_mock_queries_are_bounded_by_pages_not_exam_count(client):
    services.invalidate_question_counts()
    queries = []

    def spy(conn, cursor, statement, *_):
        if statement.lstrip().upper().startswith('SELECT'):
            queries.append(statement)

    event.listen(engine, 'before_cursor_execute', spy)
    try:
        assert client.get('/api/v1/catalog').status_code == 200
        assert len(queries) == 5  # Aggregate, subjects, topics, exams, joined sections+subjects.
        queries.clear()
        assert client.get('/api/v1/catalog').status_code == 200
        assert len(queries) == 4
        queries.clear()
        assert client.get('/mock').status_code == 200
        assert len(queries) == 3  # Exams, joined sections+subjects, fresh section aggregate.
        queries.clear()
        assert client.get('/mock').status_code == 200
        assert len(queries) == 2
    finally:
        event.remove(engine, 'before_cursor_execute', spy)


def test_topic_count_cache_expires_and_callers_cannot_mutate_it(db):
    services.invalidate_question_counts()
    first = services.recent_topic_counts(db)
    assert first
    changed = services.recent_topic_counts(db)
    changed.clear()
    assert services.recent_topic_counts(db) == first
    hits = []

    def spy(conn, cursor, statement, *_):
        if 'GROUP BY question.topic_id' in statement:
            hits.append(statement)

    event.listen(engine, 'before_cursor_execute', spy)
    try:
        services._topic_counts['at'] -= services.COUNTS_MAX_AGE
        assert services.recent_topic_counts(db) == first
        assert services.recent_topic_counts(db) == first
    finally:
        event.remove(engine, 'before_cursor_execute', spy)
    assert len(hits) == 1


def test_question_count_invalidation_is_commit_scoped_and_bulk_writes_refresh(db):
    from app.db import SessionLocal
    from app.models import Question
    from sqlalchemy import select, update
    q = db.scalar(select(Question).where(Question.review_status == 'unreviewed'))
    original = q.review_status
    tid, qid = q.topic_id, q.id
    services.invalidate_question_counts()
    before = services.recent_topic_counts(db)
    try:
        q.review_status = 'flagged'
        assert services.recent_topic_counts(db)[tid] == before[tid] - 1
        with SessionLocal() as other:
            assert services.recent_topic_counts(other) == before  # No uncommitted cross-learner leakage.
        db.rollback()
        assert services.recent_topic_counts(db) == before
        q.review_status = 'flagged'
        db.commit()
        assert services.recent_topic_counts(db)[tid] == before[tid] - 1
        q.review_status = original
        db.commit()
        assert services.recent_topic_counts(db) == before
        db.execute(update(Question).where(Question.id == qid).values(review_status='flagged'))
        db.commit()
        assert services.recent_topic_counts(db)[tid] == before[tid] - 1
    finally:
        db.rollback()
        db.execute(update(Question).where(Question.id == qid).values(review_status=original))
        db.commit()
    assert services.recent_topic_counts(db) == before


def test_count_cache_does_not_cross_database_binds(db, tmp_path):
    from app.db import Base, make_engine
    from sqlalchemy.orm import Session
    before = services.recent_topic_counts(db)
    other_engine = make_engine(f'sqlite:///{tmp_path / "empty.db"}')
    try:
        Base.metadata.create_all(other_engine)
        with Session(other_engine) as other:
            assert services.recent_topic_counts(other) == {}
            assert services.recent_section_counts(other) == {}
        assert services.recent_topic_counts(db) == before
        assert services.recent_section_counts(db)
    finally:
        other_engine.dispose()


def test_parallel_count_cache_misses_only_scan_once(db):
    from concurrent.futures import ThreadPoolExecutor
    from app.db import SessionLocal
    services.invalidate_question_counts()
    hits = []

    def spy(conn, cursor, statement, *_):
        if 'GROUP BY question.topic_id' in statement:
            hits.append(statement)

    def read(_):
        with SessionLocal() as session:
            return services.recent_topic_counts(session)

    event.listen(engine, 'before_cursor_execute', spy)
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            counts = list(pool.map(read, range(8)))
    finally:
        event.remove(engine, 'before_cursor_execute', spy)
    assert counts[0] and all(c == counts[0] for c in counts)
    assert len(hits) == 1


def test_home_book_availability_never_waits_for_index_scan(monkeypatch):
    from app import books, main

    def scan():
        raise AssertionError('Home navigation must not trigger a full book scan')

    monkeypatch.setattr(books, 'readable_books', scan)
    for known, expected in [(None, True), (True, True), (False, False)]:
        monkeypatch.setattr(books, 'cached_availability', lambda value=known: value)
        assert main.has_books() is expected
