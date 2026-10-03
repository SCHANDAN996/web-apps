import pytest

from app import ai, config
from app.models import Question, QuestionExplanation, Topic
from conftest import topic_id


@pytest.fixture
def ai_on(monkeypatch):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'test-key')
    calls = []

    def fake_call(system, user, *, schema=None, effort='low', max_tokens=4000):
        calls.append((system, user, schema))
        return fake_call.reply(system, user, schema) if callable(fake_call.reply) else fake_call.reply
    fake_call.reply = 'क्योंकि सही विकल्प B है।'
    monkeypatch.setattr(ai, 'call', fake_call)
    return fake_call, calls


def answer_one(client, db, slug='percentage', chosen=0):
    client.post('/api/v1/me', json={'level': '10th'})
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, slug), 'count': 1}).json()
    q = a['questions'][0]
    return a, q


def test_explain_requires_answer_and_caches(client, db, ai_on):
    fake, calls = ai_on
    a, q = answer_one(client, db)
    # Not answered yet → no explanation (stops use as an answer oracle)
    assert client.post(f"/api/v1/questions/{q['id']}/explain", json={'lang': 'hi'}).status_code == 404
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': q['id'], 'chosen_index': 0})
    r = client.post(f"/api/v1/questions/{q['id']}/explain", json={'lang': 'hi'})
    assert r.status_code == 200 and r.json() == {'text': 'क्योंकि सही विकल्प B है।', 'cached': False}
    assert '<question>' in calls[0][1] and 'Answer key: B' in calls[0][1]
    r2 = client.post(f"/api/v1/questions/{q['id']}/explain", json={'lang': 'hi'})
    assert r2.json()['cached'] is True and len(calls) == 1


def test_explain_blocked_during_running_mock(client, db, ai_on):
    client.post('/api/v1/me', json={'level': '10th'})
    m = client.post('/api/v1/mock', json={'exam': 'ssc-gd'}).json()
    q = m['questions'][0]
    client.post(f"/api/v1/attempts/{m['id']}/answer", json={'question_id': q['id'], 'chosen_index': 1})
    assert client.post(f"/api/v1/questions/{q['id']}/explain", json={}).status_code == 404


def test_key_doubt_flags_question(client, db, ai_on):
    fake, _ = ai_on
    fake.reply = 'KEY_DOUBT: option C is correct because 25% of 200 is 50.'
    a, q = answer_one(client, db, 'polity')
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': q['id'], 'chosen_index': 0})
    r = client.post(f"/api/v1/questions/{q['id']}/explain", json={'lang': 'en'})
    assert r.status_code == 503 and 'key_doubt' in r.text
    db.expire_all()
    assert db.get(Question, q['id']).review_status == 'flagged'


def test_daily_limit(client, db, ai_on, monkeypatch):
    monkeypatch.setattr(config, 'AI_DAILY_LIMIT_PER_DEVICE', 1)
    a = client.post('/api/v1/me', json={'level': '10th'})
    att = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'analogy'), 'count': 2}).json()
    for q in att['questions']:
        client.post(f"/api/v1/attempts/{att['id']}/answer", json={'question_id': q['id'], 'chosen_index': 0})
    ids = [q['id'] for q in att['questions']]
    db.query(QuestionExplanation).filter(QuestionExplanation.question_id.in_(ids)).delete()
    db.commit()
    assert client.post(f'/api/v1/questions/{ids[0]}/explain', json={'lang': 'en'}).status_code == 200
    r = client.post(f'/api/v1/questions/{ids[1]}/explain', json={'lang': 'en'})
    assert r.status_code == 503 and 'daily_limit' in r.text


def test_explain_off_without_key(client, db, monkeypatch):
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', '')
    a, q = answer_one(client, db, 'noun')
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': q['id'], 'chosen_index': 0})
    assert client.post(f"/api/v1/questions/{q['id']}/explain", json={}).status_code == 503


def test_generate_checks_and_flags(db, ai_on):
    fake, calls = ai_on
    good = {'text_hi': 'भारत के पहले राष्ट्रपति कौन थे?', 'text_en': 'Who was the first President of India?',
            'options_hi': ['राजेंद्र प्रसाद', 'नेहरू', 'पटेल', 'अंबेडकर'],
            'options_en': ['Rajendra Prasad', 'Nehru', 'Patel', 'Ambedkar'], 'answer_index': 0,
            'solution_hi': 'डॉ. राजेंद्र प्रसाद।', 'solution_en': 'Dr. Rajendra Prasad.', 'difficulty': 'easy'}
    disputed = {**good, 'text_en': 'Which article abolishes untouchability?', 'text_hi': 'अस्पृश्यता किस अनुच्छेद में समाप्त?',
                'options_en': ['Art 14', 'Art 17', 'Art 21', 'Art 32'], 'options_hi': ['14', '17', '21', '32'], 'answer_index': 0}
    broken = {**good, 'text_en': 'Broken', 'options_en': ['a', 'a', 'b', 'c']}

    def reply(system, user, schema):
        if schema is ai.MCQ_SCHEMA:
            return {'questions': [good, disputed, broken]}
        return {'answers': [{'n': 0, 'answer_index': 0, 'confident': True},
                            {'n': 1, 'answer_index': 1, 'confident': True}]}
    fake.reply = reply
    topic = db.query(Topic).filter_by(slug='indian-geography').one()
    stats = ai.generate_questions(db, topic, '10th', 3)
    assert stats == {'added': 1, 'flagged': 1, 'rejected': 1}
    rows = {q.text_en: q for q in db.query(Question).filter_by(topic_id=topic.id)}
    assert rows['Who was the first President of India?'].review_status == 'unreviewed'
    assert rows['Which article abolishes untouchability?'].review_status == 'flagged'
    assert 'recheck_disagrees' in rows['Which article abolishes untouchability?'].review_note
    # Generating the same question again is rejected as a duplicate
    assert ai.generate_questions(db, topic, '10th', 1)['rejected'] >= 1


def test_call_builds_a_valid_sdk_request(monkeypatch):
    """Real SDK, unreachable server: proves our kwargs are accepted and errors map cleanly."""
    import anthropic
    monkeypatch.setattr(config, 'ANTHROPIC_API_KEY', 'sk-test')
    monkeypatch.setattr(ai, '_client', anthropic.Anthropic(api_key='sk-test', base_url='http://127.0.0.1:9', max_retries=0, timeout=2))
    with pytest.raises(ai.AIUnavailable) as e:
        ai.call('system', 'user', schema=ai.CHECK_SCHEMA, effort='high')
    assert str(e.value) == 'network'
