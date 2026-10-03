from datetime import date, datetime, timedelta

from app import services
from app.models import Question, Attempt, Device, Job, ReviewCard
from conftest import topic_id


def onboard(client, level='10th', exams=('ssc-gd',)):
    r = client.post('/api/v1/me', json={'lang': 'hi', 'level': level, 'target_exams': list(exams)})
    assert r.status_code == 200
    return r


def test_onboarding_sets_cookie_and_filters_exams(client):
    r = client.post('/api/v1/me', json={'level': '10th', 'target_exams': ['ssc-gd', 'made-up']})
    assert 'ss_device' in r.cookies or client.cookies.get('ss_device')
    assert r.json()['target_exams'] == ['ssc-gd']
    assert client.get('/api/v1/me').json()['onboarded'] is True


def test_json_only_api(client):
    r = client.post('/api/v1/me', data={'level': '10th'})
    assert r.status_code == 415


def test_practice_reveals_after_answer_and_logs_mistake(client, db):
    onboard(client)
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'percentage'), 'count': 5}).json()
    assert len(a['questions']) == 5
    q = a['questions'][0]
    assert 'answer_index' not in q['state']            # never leaked before answering
    key = db.get(Question, q['id']).answer_index
    wrong = (key + 1) % 4
    r = client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': q['id'], 'chosen_index': wrong}).json()
    assert r['correct'] is False and r['answer_index'] == key
    # answering again is refused
    again = client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': q['id'], 'chosen_index': 1})
    assert again.status_code == 409
    me = db.query(Device).filter_by(token=client.cookies.get('ss_device')).one()
    card = db.query(ReviewCard).filter_by(device_id=me.id, question_id=q['id']).one()
    assert card.box == 1 and card.due_on == services.today_ist() + timedelta(days=1)
    res = client.post(f"/api/v1/attempts/{a['id']}/finish", json={}).json()
    assert res['score'] == 0 and res['max_score'] == 5 and res['attempted'] == 1


def test_flagged_questions_never_served(client, db):
    onboard(client)
    r = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'average')})
    assert r.status_code == 404


def test_mock_hides_answers_and_applies_negative_marking(client, db):
    onboard(client)
    a = client.post('/api/v1/mock', json={'exam': 'ssc-gd'}).json()
    assert len(a['questions']) == 80 and a['duration_sec'] == 3600
    assert [s['subject'] for s in a['sections']] == ['reasoning', 'ga', 'quant', 'english']
    qs = a['questions']
    k0, k1 = db.get(Question, qs[0]['id']).answer_index, db.get(Question, qs[1]['id']).answer_index
    r = client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': qs[0]['id'], 'chosen_index': k0})
    assert r.json() == {'saved': True}                  # no reveal during a mock
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': qs[1]['id'], 'chosen_index': (k1 + 1) % 4})
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': qs[2]['id'], 'chosen_index': None, 'marked': True})
    res = client.post(f"/api/v1/attempts/{a['id']}/finish", json={}).json()
    assert res['score'] == 2 - 0.25 and res['max_score'] == 160
    assert res['sections']['reasoning']['correct'] == 1 and res['sections']['reasoning']['wrong'] == 1
    # Wrong mock answers go to the mistake notebook too
    me = db.query(Device).filter_by(token=client.cookies.get('ss_device')).one()
    assert db.query(ReviewCard).filter_by(device_id=me.id, question_id=qs[1]['id']).count() == 1


def test_partial_mock_scales_time(client):
    onboard(client, 'graduate', ['rrb-group-d'])
    a = client.post('/api/v1/mock', json={'exam': 'rrb-group-d'}).json()
    # science has no questions → 75 of 100 questions, 75% of 90 minutes
    assert len(a['questions']) == 75 and a['duration_sec'] == round(90 * 60 * 0.75)
    assert 'Partial' in a['title']


def test_mock_rejects_answers_after_time_up(client, db):
    onboard(client)
    a = client.post('/api/v1/mock', json={'exam': 'ssc-gd'}).json()
    att = db.get(Attempt, a['id'])
    att.started_at = datetime.utcnow() - timedelta(seconds=3600 + 60)
    db.commit()
    r = client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': a['questions'][0]['id'], 'chosen_index': 1})
    assert r.status_code == 409


def test_attempts_are_private(client, db):
    onboard(client)
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'analogy')}).json()
    client.cookies.clear()
    onboard(client)                                     # a different learner
    assert client.get(f"/api/v1/attempts/{a['id']}").status_code == 404
    r = client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': a['questions'][0]['id'], 'chosen_index': 1})
    assert r.status_code == 404


def test_leitner_revision(client, db):
    onboard(client)
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'polity'), 'count': 1}).json()
    qid = a['questions'][0]['id']
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': qid, 'chosen_index': 3})
    assert client.get('/api/v1/revise').json()['cards'] == []       # due tomorrow, not today
    me = db.query(Device).filter_by(token=client.cookies.get('ss_device')).one()
    card = db.query(ReviewCard).filter_by(device_id=me.id, question_id=qid).one()
    card.due_on = date(2000, 1, 1)
    db.commit()
    assert [c['id'] for c in client.get('/api/v1/revise').json()['cards']] == [qid]
    r = client.post(f'/api/v1/revise/{qid}', json={'chosen_index': 1}).json()
    assert r['correct'] and r['box'] == 2
    r = client.post(f'/api/v1/revise/{qid}', json={'chosen_index': 0}).json()
    assert not r['correct'] and r['box'] == 1


def test_stats_and_weak_topics(client, db):
    onboard(client)
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'noun'), 'count': 6}).json()
    for q in a['questions']:
        client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': q['id'], 'chosen_index': 0})
    s = client.get('/api/v1/stats').json()
    assert s['attempted'] == 6 and s['accuracy'] == 0 and s['streak_days'] == 1
    assert s['weak_topics'][0]['name']['en'] == 'Noun'


def test_report_question(client, db):
    onboard(client)
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'analogy'), 'count': 1}).json()
    r = client.post(f"/api/v1/questions/{a['questions'][0]['id']}/report", json={'reason': 'wrong_answer', 'note': 'x'})
    assert r.status_code == 200
    assert client.post('/api/v1/questions/1/report', json={'reason': 'nonsense'}).status_code == 422


def test_jobs_filter_and_escaping(client, db):
    today = services.today_ist()
    db.add_all([
        Job(slug='open-10th', status='verified', title='<script>alert(1)</script> GD', min_qualification='10th', last_date=today + timedelta(days=3), official_url='https://ssc.gov.in'),
        Job(slug='open-grad', status='verified', title='CGL', min_qualification='graduate', last_date=today + timedelta(days=20)),
        Job(slug='closed', status='verified', title='Old', min_qualification='10th', last_date=today - timedelta(days=1)),
    ])
    db.commit()
    slugs = [j['slug'] for j in client.get('/api/v1/jobs?qualification=10th').json()['jobs']]
    assert 'open-10th' in slugs and 'open-grad' not in slugs and 'closed' not in slugs
    page = client.get('/jobs?qualification=all').text
    assert '<script>alert(1)</script>' not in page and '&lt;script&gt;' in page
    assert '3 दिन बाकी' in page
    detail = client.get('/jobs/open-10th').text
    assert 'JobPosting' in detail
    assert 'noindex' in client.get('/jobs/closed').text


def test_pages_render(client, db):
    assert 'चलिए शुरू करते हैं' in client.get('/').text
    onboard(client)
    for path in ['/', '/practice', '/practice/quant/percentage', '/mock', '/mock/ssc-gd', '/revise',
                 '/progress', '/jobs', '/settings', '/sitemap.xml', '/robots.txt', '/offline']:
        r = client.get(path)
        assert r.status_code == 200, path
    assert client.get('/practice/quant/nope').status_code == 404
    assert client.get('/api/v1/catalog').json()['exams'][0]['slug'] == 'ssc-gd'
