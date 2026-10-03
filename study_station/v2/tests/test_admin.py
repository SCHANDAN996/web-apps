import pytest

from app import config
from app.models import Job, Question, QuestionReport


@pytest.fixture
def admin_on(monkeypatch):
    monkeypatch.setattr(config, 'SECRET_KEY', 'test-secret')
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', 'pass123')
    from app import admin
    admin._attempts.clear()


H = {'origin': 'http://testserver'}


def login(client):
    r = client.post('/admin/login', data={'password': 'pass123', 'next': '/admin'}, headers=H, follow_redirects=False)
    assert r.status_code == 303
    return r


def test_locked_without_config(client, monkeypatch):
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', '')
    assert 'locked' in client.get('/admin/login').text
    r = client.get('/admin', follow_redirects=False)
    assert r.status_code == 303 and '/admin/login' in r.headers['location']


def test_login_wrong_and_rate_limited(client, admin_on):
    for _ in range(5):
        assert 'Wrong password' in client.post('/admin/login', data={'password': 'x'}, headers=H).text
    assert 'Too many attempts' in client.post('/admin/login', data={'password': 'pass123'}, headers=H).text


def test_dashboard_and_csrf(client, admin_on):
    login(client)
    r = client.get('/admin')
    assert r.status_code == 200 and 'Dashboard' in r.text and r.headers['cache-control'] == 'no-store'
    # A form post from another site is refused even with the cookie.
    assert client.post('/admin/logout', headers={'origin': 'https://evil.example'}).status_code == 403


def test_review_reported_question(client, admin_on, db):
    from conftest import make_questions
    make_questions(db, 'ga', 'economy', 1, tag=__name__)
    q = db.query(Question).filter(Question.import_key == f'economy-0-{__name__}').one()
    client.post('/api/v1/me', json={'level': '10th'})
    client.post(f'/api/v1/questions/{q.id}/report', json={'reason': 'wrong_answer', 'note': 'C is right'})
    login(client)
    assert str(q.id) in client.get('/admin/questions?queue=reported').text
    form = {'text_hi': 'नया प्रश्न', 'text_en': 'New question', 'answer_index': '2', 'difficulty': 'hard',
            'source_type': 'pyq', 'source_ref': 'SSC CGL 2024 Tier-I Shift 1', 'action': 'verify'}
    for lang in ('hi', 'en'):
        for i in range(4):
            form[f'opt_{lang}_{i}'] = f'{lang}{i}'
    r = client.post(f'/admin/questions/{q.id}', data=form, headers=H, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    q = db.get(Question, q.id)
    assert (q.review_status, q.answer_index, q.source_type, q.text_en) == ('verified', 2, 'pyq', 'New question')
    assert db.query(QuestionReport).filter_by(question_id=q.id, resolved_at=None).count() == 0
    # PYQ without a source is rejected
    form.update(source_ref='', action='save')
    assert client.post(f'/admin/questions/{q.id}', data=form, headers=H).status_code == 400


def test_publish_pending_job_needs_official_url(client, admin_on, db):
    job = Job(slug='pending-x', title='XYZ Clerk Recruitment 2026', status='pending', job_type='latest')
    db.add(job)
    db.commit()
    login(client)
    base = {'title': job.title, 'last_date': '2099-01-31', 'category': 'govt', 'job_type': 'latest', 'action': 'verify'}
    r = client.post(f'/admin/jobs/{job.id}', data={**base, 'notification_url': 'https://www.freejobalert.com/x'}, headers=H)
    assert r.status_code == 400
    r = client.post(f'/admin/jobs/{job.id}', data={**base, 'notification_url': 'https://xyz.gov.in/advt.pdf'},
                    headers=H, follow_redirects=False)
    assert r.status_code == 303
    db.expire_all()
    j = db.get(Job, job.id)
    assert j.status == 'verified' and str(j.last_date) == '2099-01-31'
    assert client.get('/jobs/pending-x').status_code == 200
