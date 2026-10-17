import re
import pytest

from app.models import Device, Question


@pytest.fixture(autouse=True)
def restore_shared_question_fixture(db):
    question = db.query(Question).order_by(Question.id).first()
    fields = ('text_en', 'options_en', 'solution_en', 'solution_hi', 'review_status')
    original = {name: getattr(question, name) for name in fields}
    yield
    for name, value in original.items():
        setattr(question, name, value)
    db.commit()


def question_ids(html):
    return set(map(int, re.findall(r'href="/questions/(\d+)\?lang=', html)))


def test_bank_is_paginated_public_and_has_no_answer_leak(client, db):
    q = db.query(Question).order_by(Question.id).first()
    q.solution_en = 'PRIVATE_SOLUTION_SENTINEL'
    q.solution_hi = 'PRIVATE_SOLUTION_SENTINEL'
    db.commit()
    n = db.query(Device).count()
    first = client.get('/questions?lang=en')
    second = client.get('/questions?lang=en&page=2')
    assert first.status_code == second.status_code == 200
    assert first.headers['x-ss-public-content'] == 'questions-v1'
    assert len(question_ids(first.text)) == 30
    assert not question_ids(first.text) & question_ids(second.text)
    detail = client.get(f'/questions/{q.id}?lang=en')
    assert detail.status_code == 200
    assert 'PRIVATE_SOLUTION_SENTINEL' not in first.text + detail.text
    assert f'data-question-practice="{q.id}"' in detail.text
    assert 'answer_index' not in detail.text
    assert db.query(Device).count() == n
    assert 'ss_device=' not in first.headers.get('set-cookie', '')


def test_filters_language_escape_and_empty_form_values(client, db):
    q = db.query(Question).order_by(Question.id).first()
    q.text_en = 'BANK_UNIQUE 50% <script>alert(1)</script>'
    q.options_en = ['<b>one</b>', 'two', 'three', 'four']
    db.commit()
    r = client.get('/questions', params={'lang': 'en', 'q': 'BANK_UNIQUE 50%', 'topic': '', 'level': '', 'difficulty': ''})
    assert r.status_code == 200
    assert question_ids(r.text) == {q.id}
    assert '<script>alert(1)</script>' not in r.text
    assert '&lt;script&gt;' in r.text
    detail = client.get(f'/questions/{q.id}?lang=en')
    assert '&lt;b&gt;one&lt;/b&gt;' in detail.text
    assert 'lang="en"' in detail.text
    topic = client.get('/questions', params={'topic': q.topic_id, 'lang': 'hi'})
    assert topic.status_code == 200 and q.id in question_ids(topic.text)
    assert client.get('/questions?topic=-1').status_code == 422
    assert client.get('/questions?level=invalid').status_code == 422
    assert client.get('/questions?page=10000').status_code == 404
    assert client.get('/questions?q=' + 'x' * 121).status_code == 422


def test_flagged_questions_cannot_be_browsed_or_cached(client, db):
    q = db.query(Question).order_by(Question.id).first()
    q.review_status = 'flagged'
    q.text_en = 'FLAGGED_SENTINEL'
    db.commit()
    r = client.get(f'/questions/{q.id}?lang=en')
    assert r.status_code == 404
    assert 'x-ss-public-content' not in r.headers
    page = client.get('/questions?lang=en&q=FLAGGED_SENTINEL')
    assert question_ids(page.text) == set()


def test_public_language_is_explicit_even_for_logged_in_learner(client):
    client.post('/api/v1/me', json={'lang': 'hi', 'level': '10th'})
    r = client.get('/questions?lang=en')
    assert r.status_code == 200
    assert '<html lang="en">' in r.text
    assert 'Browse all questions' in r.text
    assert '/questions/' in r.text and '?lang=en' in r.text
