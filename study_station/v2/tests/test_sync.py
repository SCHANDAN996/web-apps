from app.models import Device, ReviewCard
from conftest import topic_id


def test_move_progress_to_new_phone(client, db):
    client.post('/api/v1/me', json={'level': '12th', 'target_exams': ['ssc-chsl']})
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'percentage'), 'count': 2}).json()
    client.post(f"/api/v1/attempts/{a['id']}/answer", json={'question_id': a['questions'][0]['id'], 'chosen_index': 0})
    code = client.post('/api/v1/sync/code', json={}).json()['code']
    assert code.startswith('SS-') and len(code) == 17
    old_token = client.cookies.get('ss_device')

    client.cookies.clear()                      # the new phone, which already did a little practice
    client.post('/api/v1/me', json={'level': '10th'})
    b = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'analogy'), 'count': 1}).json()
    client.post(f"/api/v1/attempts/{b['id']}/answer", json={'question_id': b['questions'][0]['id'], 'chosen_index': 0})
    new_token = client.cookies.get('ss_device')

    assert client.post('/api/v1/sync/restore', json={'code': 'SS-AAAA-AAAA-AAAA'}).status_code == 404
    r = client.post('/api/v1/sync/restore', json={'code': code.lower().replace('-', ' ')})
    assert r.status_code == 200 and r.json()['level'] == '12th'
    assert client.cookies.get('ss_device') == old_token
    assert db.query(Device).filter_by(token=new_token).count() == 0          # merged away
    owner = db.query(Device).filter_by(token=old_token).one()
    assert db.query(ReviewCard).filter_by(device_id=owner.id).count() == 2   # both phones' mistakes
    assert client.get('/api/v1/stats').json()['attempted'] == 2


def test_new_code_disables_old(client):
    client.post('/api/v1/me', json={'level': '10th'})
    first = client.post('/api/v1/sync/code', json={}).json()['code']
    client.post('/api/v1/sync/code', json={})
    client.cookies.clear()
    assert client.post('/api/v1/sync/restore', json={'code': first}).status_code == 404
