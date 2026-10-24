from sqlalchemy import select

from app.models import Attempt, Question
from conftest import topic_id


def test_selected_question_uses_normal_private_answer_and_scoring_flow(client, db):
    q = db.scalar(select(Question).where(Question.review_status == 'unreviewed'))
    response = client.post(f'/api/v1/questions/{q.id}/practice', json={})
    assert response.status_code == 200
    a = response.json()
    assert a['mode'] == 'practice' and a['duration_sec'] is None
    assert [item['id'] for item in a['questions']] == [q.id]
    assert a['questions'][0]['state'] == {'chosen': None, 'marked': False}
    assert 'answer_index' not in response.text and 'solution' not in response.text
    answer = client.post(f'/api/v1/attempts/{a["id"]}/answer',
                         json={'question_id': q.id, 'chosen_index': q.answer_index}).json()
    assert answer['correct'] is True and answer['answer_index'] == q.answer_index
    result = client.post(f'/api/v1/attempts/{a["id"]}/finish', json={}).json()
    assert (result['score'], result['max_score'], result['attempted']) == (1, 1, 1)
    client.cookies.clear()
    another = client.post(f'/api/v1/questions/{q.id}/practice', json={}).json()
    assert another['id'] != a['id']
    assert client.get(f'/api/v1/attempts/{a["id"]}').status_code == 404
    assert client.post(f'/api/v1/attempts/{a["id"]}/answer',
                       json={'question_id': q.id, 'chosen_index': q.answer_index}).status_code == 404


def test_selected_question_rejects_flagged_unknown_and_answer_injection(client, db):
    flagged = db.scalar(select(Question).where(Question.review_status == 'flagged'))
    before = db.query(Attempt).count()
    for qid in [flagged.id, 999999999, 0, 1 << 100]:
        assert client.post(f'/api/v1/questions/{qid}/practice', json={}).status_code == 404
    assert db.query(Attempt).count() == before
    usable = db.scalar(select(Question).where(Question.review_status == 'unreviewed'))
    assert client.post(f'/api/v1/questions/{usable.id}/practice', json={'answer_index': 1}).status_code == 422
    assert client.post(f'/api/v1/questions/{usable.id}/practice', data={}).status_code == 415
    assert db.query(Attempt).count() == before


def test_practice_count_accepts_more_than_ten_and_twenty_five_but_stays_bounded(client, db):
    tid = topic_id(db, 'percentage')
    result = client.post('/api/v1/practice', json={'topic_id': tid, 'count': 26})
    assert result.status_code == 200 and len(result.json()['questions']) == 26
    result = client.post('/api/v1/practice', json={'topic_id': tid, 'count': 50})
    assert result.status_code == 200 and len(result.json()['questions']) == 30  # All available fixture questions.
    assert len({q['id'] for q in result.json()['questions']}) == 30
    assert client.post('/api/v1/practice', json={'topic_id': tid, 'count': 51}).status_code == 422
