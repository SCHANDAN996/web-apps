import pytest
from sqlalchemy import select

from app import config
from app.models import Job, Question, QuestionReport


@pytest.fixture
def admin_on(monkeypatch):
    monkeypatch.setattr(config, 'SECRET_KEY', 'test-secret')
    monkeypatch.setattr(config, 'ADMIN_PASSWORD', 'pass123')
    from app import admin
    admin._attempts.clear()
    admin._report_cache.update(at=0.0, value=None)


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


def test_dashboard_overview_is_read_only_and_shows_live_state(client, admin_on, db, monkeypatch, tmp_path):
    import json
    from app import services
    from app.promo import posted as plog
    monkeypatch.setattr(config,'SOURCE_RELEASE_PATH',tmp_path/'missing-release.json')
    login(client)
    r = client.get('/admin')
    assert 'Learners (counts only)' in r.text and 'Alerts' in r.text
    assert 'No deployment manifest' in r.text
    # deployment manifest -> revision shown
    manifest = tmp_path / 'source-release.json'
    manifest.write_text(json.dumps({'revision': 'abc123def4567890', 'deployed_at': '2026-10-24T10:00:00+05:30',
                                    'branch': 'claude/elegant-rubin-sgov1q', 'files': {'a.py': 'x', 'b.py': 'y'}}))
    monkeypatch.setattr(config, 'SOURCE_RELEASE_PATH', manifest)
    log = tmp_path / 'posted.json'
    day = services.today_ist().isoformat()
    log.write_text(json.dumps({'telegram': [], 'shorts': [], 'days': {day: {'quiz': [[{'id': 'a'}] * 5, [{'id': 'b'}] * 5]}}}))
    monkeypatch.setattr(plog, 'POSTED', log)
    r = client.get('/admin')
    assert 'abc123def456' in r.text and '2 files in the manifest' in r.text
    assert 'quiz 10' in r.text and 't.me/studystation_hindi' in r.text
    # a broken manifest does not break the page
    manifest.write_text('{not json')
    assert client.get('/admin').status_code == 200
    # nothing on the dashboard changes data: only GETs, and the overview has no forms of its own
    from bs4 import BeautifulSoup
    doc = BeautifulSoup(client.get('/admin').text, 'html.parser')
    assert not doc.select('#release form, #promo form, #alerts form')


def test_dashboard_overview_needs_login(client, admin_on):
    r = client.get('/admin', follow_redirects=False)
    assert r.status_code == 303 and '/admin/login' in r.headers['location']


def _answers(db, qid, n, correct):
    from app.models import Attempt, AttemptAnswer, Device
    dev = Device(token='t' * 20 + str(qid), level='10th')
    db.add(dev); db.flush()
    for i in range(n):                                    # one answer per attempt (unique per attempt+question)
        att = Attempt(device_id=dev.id, mode='practice', question_ids=[qid])
        db.add(att); db.flush()
        db.add(AttemptAnswer(attempt_id=att.id, question_id=qid, chosen_index=0, correct=i < correct))
    db.commit()


def test_suspicious_queue_bulk_actions_are_audited(client, admin_on, db):
    from app.models import AdminAction
    from app.services import suspicious_keys
    qs = list(db.scalars(select(Question).where(Question.review_status == 'unreviewed').order_by(Question.id).limit(3)))
    _answers(db, qs[0].id, 25, 2)      # 8% correct -> suspicious
    _answers(db, qs[1].id, 25, 20)     # fine
    _answers(db, qs[2].id, 10, 0)      # too few answers to judge
    assert set(suspicious_keys(db)) == {qs[0].id}
    login(client)
    from app import admin
    admin._report_cache.update(at=0.0, value=None)
    assert 'Possible wrong answer keys' in client.get('/admin').text
    page = client.get('/admin/questions?queue=suspicious').text
    assert f'value="{qs[0].id}"' in page and f'value="{qs[1].id}"' not in page and '2/25' in page
    # a reason is required, and the request must come from the admin page (CSRF)
    assert client.post('/admin/questions/bulk', data={'ids': [qs[0].id], 'action': 'flag', 'note': ''},
                       headers=H).status_code == 400
    assert client.post('/admin/questions/bulk', data={'ids': [qs[0].id], 'action': 'flag', 'note': 'x'}).status_code == 403
    r = client.post('/admin/questions/bulk', data={'ids': [qs[0].id], 'action': 'flag', 'note': 'key wrong per solution',
                                                   'queue': 'suspicious'}, headers=H, follow_redirects=False)
    assert r.status_code == 303 and r.headers['location'] == '/admin/questions?queue=suspicious'
    db.expire_all()
    assert db.get(Question, qs[0].id).review_status == 'flagged'
    assert suspicious_keys(db) == {}                     # decided questions leave the queue
    log = db.scalars(select(AdminAction).order_by(AdminAction.id.desc())).first()
    assert (log.action, log.target, log.note) == ('question.flag', f'question:{qs[0].id}', 'key wrong per solution')
    assert 'unreviewed -> flagged' in log.detail
    audit_page = client.get('/admin/audit').text
    assert 'question.flag' in audit_page and 'key wrong per solution' in audit_page


def test_single_question_save_is_audited(client, admin_on, db):
    from app.models import AdminAction
    q = db.scalars(select(Question).where(Question.text_hi.is_not(None), Question.options_hi.is_not(None))).first()
    login(client)
    form = {'action': 'verify', 'review_note': 'checked', 'answer_index': str(q.answer_index), 'text_hi': q.text_hi,
            'solution_hi': q.solution_hi or ''}
    form.update({f'opt_hi_{i}': o for i, o in enumerate(q.options_hi)})
    if q.text_en:
        form.update({'text_en': q.text_en, 'solution_en': q.solution_en or ''})
        form.update({f'opt_en_{i}': o for i, o in enumerate(q.options_en)})
    assert client.post(f'/admin/questions/{q.id}', data=form, headers=H, follow_redirects=False).status_code == 303
    log = db.scalars(select(AdminAction).where(AdminAction.target == f'question:{q.id}').order_by(AdminAction.id.desc())).first()
    assert log.action == 'question.verify' and log.note == 'checked'


def test_audit_page_needs_login(client, admin_on):
    assert client.get('/admin/audit', follow_redirects=False).status_code == 303
