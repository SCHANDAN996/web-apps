from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app, limiter
from app.models import Attempt, AttemptAnswer, Exam, Question, ReviewCard
from conftest import topic_id


@pytest.fixture
def book_index(monkeypatch):
    from app import books
    chapters = [SimpleNamespace(slug='01-percentage', title_hi='प्रतिशत', title_en='Percentage',
                                readable=True, topic=('quant', 'percentage')),
                SimpleNamespace(slug='02-percentage-advanced', title_hi='अभ्यास', title_en='Advanced',
                                readable=True, topic=('quant', 'percentage')),
                SimpleNamespace(slug='03-notes', title_hi='नोट्स', title_en='Notes', readable=True, topic=None)]
    book = SimpleNamespace(slug='test-maths', subject='quant', readable_chapters=chapters,
                           title=lambda lang: 'Maths', chapter=lambda slug: next(
                               (c for c in chapters if c.slug == slug), None))
    monkeypatch.setattr(books, 'readable_books', lambda: [book])
    monkeypatch.setattr(books, 'get_book', lambda slug: book if slug == book.slug else None)
    return book


def practice(client, db, topic):
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, topic), 'count': 2}).json()
    qid = a['questions'][0]['id']
    client.post(f'/api/v1/attempts/{a["id"]}/answer', json={'question_id': qid, 'chosen_index': 1})
    return a['id'], qid


def mixed(db, device_id, qids, mode='practice'):
    a = Attempt(device_id=device_id, mode=mode, question_ids=qids, title='Mixed',
                started_at=datetime.utcnow(), finished_at=datetime.utcnow(), score=2, max_score=2,
                exam_id=db.query(Exam).filter_by(slug='ssc-mts').one().id if mode == 'mock' else None)
    db.add(a)
    db.flush()
    for qid in qids:
        db.add(AttemptAnswer(attempt_id=a.id, question_id=qid, chosen_index=1, correct=True,
                             time_ms=10, marked=False))
    db.commit()
    return a.id


def test_subject_preserves_mocks_other_subject_owner_and_mixed_practice(client, db, book_index):
    own, quant = practice(client, db, 'percentage')
    unrelated, reasoning = practice(client, db, 'analogy')
    owner = db.get(Attempt, own).device_id
    mix = mixed(db, owner, [quant, reasoning])
    mock = mixed(db, owner, [quant, reasoning], 'mock')
    for qid in [quant, reasoning]:
        db.add(ReviewCard(device_id=owner, question_id=qid, box=1, due_on=datetime.utcnow().date(), lapses=1))
    db.commit()
    with TestClient(app) as other:
        theirs, _ = practice(other, db, 'percentage')
        result = client.post('/api/v1/me/reset-progress', json={
            'confirm': True, 'scope': 'subject', 'subject': 'quant',
            'whiteboard_question_ids': [quant, reasoning, 99999999]})
        assert result.status_code == 200, result.text
        assert result.json()['whiteboard_question_ids'] == [quant]
        assert len(result.json()['reading_urls']) == 3
        db.expire_all()
        assert db.get(Attempt, own) is None
        assert db.get(Attempt, unrelated) is not None
        assert db.get(Attempt, theirs) is not None
        remaining = db.get(Attempt, mix)
        assert remaining.question_ids == [reasoning]
        assert [a.question_id for a in remaining.answers] == [reasoning]
        assert (remaining.score, remaining.max_score) == (1, 1)
        preserved = db.get(Attempt, mock)
        assert preserved.question_ids == [quant, reasoning]
        assert len(preserved.answers) == 2
        assert (preserved.score, preserved.max_score) == (2, 2)
        assert {c.question_id for c in db.query(ReviewCard).filter_by(device_id=owner)} == {reasoning}


def test_chapter_shared_topic_practice_but_exact_reading_and_no_topic_is_reading_only(client, db, book_index):
    own, qid = practice(client, db, 'percentage')
    unrelated, _ = practice(client, db, 'analogy')
    before = db.query(Attempt).count()
    result = client.post('/api/v1/me/reset-progress', json={
        'confirm': True, 'scope': 'chapter', 'book': 'test-maths', 'chapter': '03-notes',
        'whiteboard_question_ids': [qid]}).json()
    assert result['reading_urls'] == ['/books/test-maths/03-notes']
    assert result['whiteboard_question_ids'] == []
    assert db.query(Attempt).count() == before
    result = client.post('/api/v1/me/reset-progress', json={
        'confirm': True, 'scope': 'chapter', 'book': 'test-maths', 'chapter': '02-percentage-advanced',
        'whiteboard_question_ids': [qid]}).json()
    assert result['reading_urls'] == ['/books/test-maths/02-percentage-advanced']
    assert result['whiteboard_question_ids'] == [qid]
    db.expire_all()
    assert db.get(Attempt, own) is None
    assert db.get(Attempt, unrelated) is not None


def test_options_use_real_topic_mapping_and_guest_scoped_is_no_identity(client, db, book_index):
    result = client.get('/api/v1/me/reset-options')
    assert result.status_code == 200
    data = result.json()
    assert any(s['slug'] == 'quant' for s in data['subjects'])
    chapters = data['chapters']
    assert chapters[0]['topic_label_en'] == chapters[1]['topic_label_en'] == 'Percentage'
    assert chapters[2]['topic_label_en'] is None
    assert client.post('/api/v1/me/reset-progress', json={
        'confirm': True, 'scope': 'chapter', 'book': 'test-maths', 'chapter': '03-notes'}).status_code == 200
    assert client.cookies.get('ss_device') is None


def test_invalid_scopes_do_not_change_history(client, db, book_index):
    own, _ = practice(client, db, 'percentage')
    for extra in [
        {'scope': 'other'}, {'scope': 'subject'}, {'scope': 'subject', 'subject': 'missing'},
        {'scope': 'chapter', 'book': 'missing', 'chapter': '01-percentage'},
        {'scope': 'chapter', 'book': 'test-maths', 'chapter': '../01-percentage'},
        {'scope': 'all', 'subject': 'quant'},
        {'scope': 'subject', 'subject': 'quant', 'whiteboard_question_ids': [True]},
        {'scope': 'subject', 'subject': 'quant', 'whiteboard_question_ids': [1] * 81},
    ]:
        limiter.hits.clear()
        result = client.post('/api/v1/me/reset-progress', json={'confirm': True, **extra})
        assert result.status_code == 422, result.text
        assert db.get(Attempt, own) is not None


def test_scoped_reset_reused_row_id_has_new_backup_identity(client, db, book_index):
    # The same server row ID can be reused after deleting a learner's last attempt.
    old_id, _ = practice(client, db, 'percentage')
    before = client.get('/api/v1/backup/export').json()
    source_cookie = client.cookies.get('ss_device')
    client.cookies.clear()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': before}).status_code == 200
    destination_cookie = client.cookies.get('ss_device')
    client.cookies.clear()
    client.cookies.set('ss_device', source_cookie)
    assert client.post('/api/v1/me/reset-progress', json={
        'confirm': True, 'scope': 'subject', 'subject': 'quant'}).status_code == 200
    new_id, _ = practice(client, db, 'percentage')
    # Force the old SQLite ID to demonstrate identity independence even when another learner's
    # imported attempt kept the global high-water row ID occupied.
    a = db.get(Attempt, new_id)
    db.execute(AttemptAnswer.__table__.delete().where(AttemptAnswer.attempt_id == new_id))
    db.flush()
    a.id = old_id
    db.commit()
    after = client.get('/api/v1/backup/export').json()
    assert after['source_id'] == before['source_id']
    assert after['attempts'][0]['id'] != before['attempts'][0]['id']
    assert after['attempts'][0]['id'] < 1 << 53
    client.cookies.clear()
    client.cookies.set('ss_device', destination_cookie)
    result = client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': after})
    assert result.status_code == 200, result.text
    assert result.json()['imported'] == 1
