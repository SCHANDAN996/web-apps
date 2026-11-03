from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import Attempt, AttemptAnswer, Device, ReviewCard
from conftest import topic_id


def attempt(client, db):
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'percentage'), 'count': 2}).json()
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': a['questions'][0]['id'], 'chosen_index': 0})
    return a['id']


def test_reset_requires_explicit_confirmation_and_only_removes_current_learner(client, db):
    client.post('/api/v1/me', json={'lang': 'en', 'level': '12th', 'target_exams': ['ssc-chsl']})
    own = attempt(client, db)
    token = client.cookies.get('ss_device')
    client.post('/api/v1/sync/code', json={})
    owner = db.scalar(select(Device).where(Device.token == token))
    recovery = owner.recovery_hash
    with TestClient(app) as other:
        other.post('/api/v1/me', json={'level': '10th'})
        theirs = attempt(other, db)
        assert client.post('/api/v1/me/reset-progress', json={}).status_code == 422
        assert client.post('/api/v1/me/reset-progress', json={'confirm': 'true'}).status_code == 422
        assert client.post('/api/v1/me/reset-progress', json={'confirm': False}).status_code == 400
        assert db.get(Attempt, own) is not None
        assert client.post('/api/v1/me/reset-progress', json={'confirm': True}).json() == {'ok': True}
        db.expire_all()
        assert db.get(Attempt, own) is None
        assert db.query(AttemptAnswer).filter_by(attempt_id=own).count() == 0
        assert db.query(ReviewCard).filter_by(device_id=owner.id).count() == 0
        assert db.get(Attempt, theirs) is not None
        assert other.get('/api/v1/stats').json()['attempted'] == 1
        stats = client.get('/api/v1/stats').json()
        assert stats['attempted'] == stats['streak_days'] == stats['due_reviews'] == 0
        assert stats['mocks'] == []
        db.refresh(owner)
        assert (owner.lang, owner.level, owner.target_exams, owner.recovery_hash) == ('en', '12th', ['ssc-chsl'], recovery)
        assert client.cookies.get('ss_device') == token


def test_guest_reset_does_not_create_a_learner(client):
    assert client.post('/api/v1/me/reset-progress', json={'confirm': True}).status_code == 200
    assert client.cookies.get('ss_device') is None
    assert client.get('/api/v1/me/reset-progress').status_code == 405
