"""'My mistakes': the learner's wrongly answered questions from the last 7 days, as one practice set."""
from datetime import datetime, timedelta

from sqlalchemy import select

from app.models import AttemptAnswer, Question


def _start(client, db):
    from conftest import topic_id
    tid = topic_id(db, db.scalar(select(Question).where(Question.review_status == 'unreviewed')).topic.slug)
    return client.post('/api/v1/practice', json={'topic_id': tid, 'count': 4}).json()


def _answer(client, db, a, q, right):
    key = db.get(Question, q['id']).answer_index
    return client.post(f"/api/v1/attempts/{a['id']}/answer",
                       json={'question_id': q['id'], 'chosen_index': key if right else (key + 1) % 4}).json()


def test_mistakes_are_the_learners_latest_wrong_answers(client, db):
    client.post('/api/v1/me', json={'level': '10th'})
    assert 'data-mistakes' not in client.get('/revise').text           # nothing wrong yet: no button
    a = _start(client, db)
    qs = a['questions']
    assert len(qs) >= 3
    _answer(client, db, a, qs[0], right=False)
    _answer(client, db, a, qs[1], right=True)
    _answer(client, db, a, qs[2], right=False)
    page = client.get('/revise').text
    assert 'data-mistakes' in page and 'पिछले 7 दिन के 2 सवाल' in page
    m = client.post('/api/v1/mistakes', json={}).json()
    assert [q['id'] for q in m['questions']] == [qs[2]['id'], qs[0]['id']]    # newest mistake first
    assert 'answer_index' not in str(m['questions'])
    # getting one right in the mistakes set removes it next time
    _answer(client, db, m, m['questions'][0], right=True)
    assert [q['id'] for q in client.post('/api/v1/mistakes', json={}).json()['questions']] == [qs[0]['id']]


def test_mistakes_are_private_and_limited_to_seven_days(client, db):
    client.post('/api/v1/me', json={'level': '10th'})
    a = _start(client, db)
    _answer(client, db, a, a['questions'][0], right=False)
    assert client.post('/api/v1/mistakes', json={}).status_code == 200
    # older than 7 days -> gone
    for row in db.scalars(select(AttemptAnswer).where(AttemptAnswer.attempt_id == a['id'])):
        row.answered_at = datetime.utcnow() - timedelta(days=8)
    db.commit()
    assert client.post('/api/v1/mistakes', json={}).status_code == 404
    # another learner never sees someone else's mistakes
    client.cookies.clear()
    client.post('/api/v1/me', json={'level': '10th'})
    assert client.post('/api/v1/mistakes', json={}).status_code == 404
    assert 'data-mistakes' not in client.get('/revise').text


def test_hidden_questions_are_left_out(client, db):
    client.post('/api/v1/me', json={'level': '10th'})
    a = _start(client, db)
    q = a['questions'][0]
    _answer(client, db, a, q, right=False)
    row = db.get(Question, q['id'])
    old = row.review_status
    row.review_status = 'flagged'
    db.commit()
    try:
        assert q['id'] not in [x['id'] for x in (client.post('/api/v1/mistakes', json={}).json().get('questions') or [])]
    finally:
        row.review_status = old
        db.commit()
