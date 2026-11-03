"""Today's Telegram quiz in the app: posted book ids -> live questions -> a normal practice attempt."""
from sqlalchemy import select

from app import services
from app.models import Question
from app.promo import live


def test_import_keys_follow_the_seeder():
    assert live.import_keys('12th_Level/GK/Intermediate_12th_GK_WorldClass/Chapter_21_International_Orgs#Set03#Q71')[0] \
        == '12th/ga/international-orgs/s3/q71'
    assert live.import_keys('10th_Level/Reasoning/Chapter_04_Blood_Relations#Set01#Q5')[0] \
        == '10th/reasoning/blood-relations/s1/q5'
    assert live.import_keys('Graduation_Level/Maths/X/Chapter_12_Time_Distance#Set04#Q86')[0] \
        == 'graduate/quant/time-distance/s4/q86'
    assert live.import_keys('revision#2026-10-23') == [] and live.import_keys('../etc/passwd') == []


def _posted(db, monkeypatch, day):
    qs = list(db.scalars(select(Question).where(Question.review_status == 'unreviewed').order_by(Question.id).limit(3)))
    hidden = db.scalars(select(Question).where(Question.review_status == 'flagged')).first()
    ids = ['12th_Level/GK/B/Chapter_21_International_Orgs#Set03#Q71', '10th_Level/Reasoning/Chapter_04_Blood_Relations#Set01#Q5',
           'Graduation_Level/Maths/X/Chapter_12_Time_Distance#Set04#Q86', 'Graduation_Level/GK/X/Chapter_01_Hidden#Set01#Q1']
    for q, pid in zip(qs, ids):
        q.import_key = live.import_keys(pid)[1 if q is qs[1] else 0]      # one question stored with the /hi suffix
    if hidden is not None:
        hidden.import_key = live.import_keys(ids[3])[0]
    db.commit()
    log = {'telegram': [], 'shorts': [], 'days': {day.isoformat(): {'quiz': [[{'id': ids[0]}, {'id': ids[1]}],
                                                                              [{'id': ids[2]}, {'id': ids[3]}]]}}}
    monkeypatch.setattr(live, 'fetch_log', lambda: log)
    return [q.id for q in qs]


def test_quiz_uses_todays_posts_in_order_and_skips_hidden(db, monkeypatch):
    today = services.today_ist()
    expected = _posted(db, monkeypatch, today)
    assert live.quiz_for(db, today) == (today, expected)


def test_quiz_falls_back_to_a_recent_day_only(db, monkeypatch):
    from datetime import timedelta
    today = services.today_ist()
    expected = _posted(db, monkeypatch, today - timedelta(days=1))
    assert live.quiz_for(db, today) == (today - timedelta(days=1), expected)
    assert live.quiz_for(db, today + timedelta(days=5)) == (None, [])


def test_practice_tile_and_api_start_a_normal_attempt(client, db, monkeypatch):
    expected = _posted(db, monkeypatch, services.today_ist())
    client.post('/api/v1/me', json={'level': '10th'})
    assert 'data-telegram-quiz' in client.get('/practice').text
    a = client.post('/api/v1/telegram-quiz', json={}).json()
    assert [q['id'] for q in a['questions']] == expected and a['mode'] == 'practice'
    assert 'answer_index' not in str(a['questions'])                     # answers only after answering


def test_no_posts_no_tile_and_404(client, db, monkeypatch):
    monkeypatch.setattr(live, 'fetch_log', lambda: {'telegram': [], 'shorts': [], 'days': {}})
    client.post('/api/v1/me', json={'level': '10th'})
    assert 'data-telegram-quiz' not in client.get('/practice').text
    assert client.post('/api/v1/telegram-quiz', json={}).status_code == 404


def test_fetch_log_falls_back_to_local_copy(monkeypatch, tmp_path):
    import json
    import httpx
    from app.promo import posted as plog
    local = tmp_path / 'posted.json'
    local.write_text(json.dumps({'telegram': ['x'], 'shorts': [], 'days': {'2026-10-23': {}}}))
    monkeypatch.setattr(plog, 'POSTED', local)
    monkeypatch.setattr(live.config, 'PROMO_POSTED_URL', 'https://example.invalid/posted.json')
    monkeypatch.setattr(live, '_cache', {'at': 0.0, 'data': None})

    def boom(*a, **k):
        raise httpx.ConnectError('offline')
    monkeypatch.setattr(httpx, 'get', boom)
    assert live.fetch_log()['telegram'] == ['x']
