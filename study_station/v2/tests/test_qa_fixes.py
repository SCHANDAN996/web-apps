"""Regression tests for the ss-qa-tester findings."""
from datetime import date, datetime, timedelta

from app import seed
from app.models import Attempt, Device, Job, ReviewCard
from conftest import topic_id


def test_expired_mock_is_closed_by_the_server(client, db):
    client.post('/api/v1/me', json={'level': '10th'})
    m = client.post('/api/v1/mock', json={'exam': 'ssc-gd'}).json()
    att = db.get(Attempt, m['id'])
    att.started_at = datetime.utcnow() - timedelta(seconds=3600 + 120)   # phone was offline at time-up
    db.commit()
    assert client.get(f"/api/v1/attempts/{m['id']}").json()['finished'] is True
    assert client.get(f"/api/v1/attempts/{m['id']}/result").status_code == 200
    r = client.get(f"/attempt/{m['id']}", follow_redirects=False)
    assert r.status_code == 303 and r.headers['location'] == f"/result/{m['id']}"


def test_revision_card_cannot_jump_ahead_before_due(client, db):
    client.post('/api/v1/me', json={'level': '10th'})
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'analogy'), 'count': 1}).json()
    qid = a['questions'][0]['id']
    from app.models import Question
    key = db.get(Question, qid).answer_index
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': qid, 'chosen_index': (key + 1) % 4})
    r = client.post(f'/api/v1/revise/{qid}', json={'chosen_index': key})
    assert r.status_code == 409 and r.json()['detail'] == 'not_due'


def test_legacy_jobs_never_link_to_aggregators(db):
    db.add(Job(slug='legacy-x', title='Old', status='legacy', official_url='https://www.freejobalert.com/x',
               notification_url='https://ssc.gov.in/a.pdf'))
    db.commit()
    assert seed.clean_legacy_links(db) >= 1
    j = db.query(Job).filter_by(slug='legacy-x').one()
    assert j.official_url is None and j.notification_url == 'https://ssc.gov.in/a.pdf'


def test_friendly_error_strings_are_sent_to_the_browser(client):
    page = client.get('/').text
    assert '"errors"' in page and 'already_answered' in page
