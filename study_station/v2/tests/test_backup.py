import copy

from conftest import topic_id
from app.models import Attempt, Device, Exam, ReviewCard


def stored_attempt(db, backup_id):
    return db.query(Attempt).filter_by(backup_id=backup_id).one()


def history(client, db):
    client.post('/api/v1/me', json={'level': '10th', 'lang': 'en'})
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'percentage'), 'count': 2}).json()
    aid = a['id']
    q = client.get(f'/api/v1/attempts/{aid}').json()['questions'][0]
    client.post(f'/api/v1/attempts/{aid}/answer', json={'question_id': q['id'], 'chosen_index': 0})
    client.post(f'/api/v1/attempts/{aid}/finish', json={})
    return client.get('/api/v1/backup/export').json()


def test_guest_and_confirm(client, db):
    assert client.get('/api/v1/backup/export').status_code == 404
    n = db.query(Device).count()
    assert client.post('/api/v1/backup/restore', json={'confirm': False, 'backup': {}}).status_code == 422
    assert db.query(Device).count() == n


def test_roundtrip_owner_idempotent_and_secrets(client, db):
    backup = history(client, db)
    assert 'token' not in str(backup) and 'solution' not in str(backup) and 'score' not in str(backup)
    old = db.query(Attempt).count()
    client.cookies.clear()
    r = client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup})
    assert r.status_code == 200, r.text
    assert r.json()['imported'] == 1
    assert db.query(Attempt).count() == old + 1
    r = client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup})
    assert r.json()['imported'] == 0
    assert r.json()['skipped'] == 1
    imported = client.get('/api/v1/backup/export').json()
    assert imported['settings']['lang'] == 'en'
    assert imported['attempts'][0]['answers'][0]['chosen_index'] == 0


def test_invalid_references_scores_rollback_and_body_cap(client, db):
    backup = history(client, db)
    client.cookies.clear()
    n = db.query(Device).count()
    bad = copy.deepcopy(backup)
    bad['attempts'][0]['question_ids'].append(999999999)
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': bad}).status_code == 422
    assert db.query(Device).count() == n
    bad = copy.deepcopy(backup)
    bad['attempts'][0]['score'] = 999
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': bad}).status_code == 422
    r = client.post('/api/v1/backup/restore', content=' ' * (2 * 1024 * 1024 + 1), headers={'content-type': 'application/json'})
    assert r.status_code == 413


def test_conflicting_import_atomic(client, db):
    backup = history(client, db)
    client.cookies.clear()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    n = db.query(Attempt).count()
    backup['attempts'][0]['answers'][0]['chosen_index'] = 1
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 409
    assert db.query(Attempt).count() == n


def test_own_export_no_duplicate_and_recomputed_result(client, db):
    backup = history(client, db)
    original_id = stored_attempt(db, backup['attempts'][0]['id']).id
    n = db.query(Attempt).count()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).json()['skipped'] == 1
    assert db.query(Attempt).count() == n
    client.cookies.clear()
    r = client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup})
    assert r.status_code == 200
    exported = client.get('/api/v1/backup/export').json()
    imported = stored_attempt(db, exported['attempts'][0]['id'])
    assert imported.score == 0  # fixture answer is 1; imported choice is 0
    assert imported.max_score == 2
    assert imported.answers[0].correct is False
    assert client.get(f'/api/v1/attempts/{original_id}').status_code == 404


def test_strict_validation_duplicates_and_option_bounds(client, db):
    backup = history(client, db)
    client.cookies.clear()
    n = db.query(Device).count()
    for mutate in (
        lambda b: b.update(schema_version=True),
        lambda b: b['attempts'].append(copy.deepcopy(b['attempts'][0])),
        lambda b: b['attempts'][0]['answers'].append(copy.deepcopy(b['attempts'][0]['answers'][0])),
        lambda b: b['attempts'][0]['answers'][0].update(chosen_index=8),
        lambda b: b['attempts'][0]['answers'][0].update(chosen_index=True),
        lambda b: b['attempts'][0].update(finished_at='2000-01-01T00:00:00'),
        lambda b: b['attempts'][0].update(started_at='2200-01-01T00:00:00'),
        lambda b: b['attempts'][0].update(started_at=0),
        lambda b: b['attempts'][0].update(id=1 << 53),
        lambda b: b['attempts'][0]['question_ids'].append(1 << 100),
    ):
        bad = copy.deepcopy(backup)
        mutate(bad)
        assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': bad}).status_code == 422
        assert db.query(Device).count() == n


def test_reset_then_restore_and_recovery_merge(client, db):
    backup = history(client, db)
    owner_code = client.post('/api/v1/sync/code', json={}).json()['code']
    client.cookies.clear()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    assert client.post('/api/v1/me/reset-progress', json={'confirm': True}).status_code == 200
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).json()['imported'] == 1
    assert client.post('/api/v1/sync/restore', json={'code': owner_code}).status_code == 200
    # Existing recovery-code merge must preserve receipts while deleting the temporary identity.
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).json()['skipped'] == 1


def test_conflict_rolls_back_earlier_rows_and_settings(client, db):
    backup = history(client, db)
    client.cookies.clear()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    count = db.query(Attempt).count()
    first = copy.deepcopy(backup['attempts'][0])
    first['id'] -= 10000000
    backup['attempts'].insert(0, first)
    backup['attempts'][1]['answers'][0]['chosen_index'] = 1
    backup['settings']['lang'] = 'hi'
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 409
    assert db.query(Attempt).count() == count
    assert client.get('/api/v1/me').json()['lang'] == 'en'


def test_mock_scoring_and_revision_are_recomputed_and_additive(client, db):
    backup = history(client, db)
    exam = db.query(Exam).filter(Exam.slug == 'ssc-mts').one()
    qid = backup['attempts'][0]['answers'][0]['question_id']
    from app.models import Question
    subject_id = db.get(Question, qid).topic.subject_id
    section = next(s for s in exam.sections if s.subject_id == subject_id)
    a = backup['attempts'][0]
    a.update(mode='mock', exam=exam.slug, topic_id=None)
    client.cookies.clear()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    imported_id = client.get('/api/v1/backup/export').json()['attempts'][0]['id']
    imported = stored_attempt(db, imported_id)
    assert imported.score == -section.negative_per_q
    assert imported.max_score == 2 * section.marks_per_q
    # An existing revision schedule must not be overwritten by an old backup.
    backup['revision'] = [{'question_id': qid, 'box': 1, 'lapses': 2, 'due_on': '2026-01-01'}]
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    c = db.query(ReviewCard).filter_by(device_id=imported.device_id, question_id=qid).one()
    c.box = 4
    db.commit()
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    db.refresh(c)
    assert c.box == 4


def test_existing_database_additive_schema(tmp_path):
    from sqlalchemy import inspect, text
    from app.db import ensure_schema, make_engine
    old = make_engine(f'sqlite:///{tmp_path / "old.db"}')
    with old.begin() as connection:
        connection.execute(text('''CREATE TABLE device (
            id INTEGER PRIMARY KEY, token VARCHAR(64) UNIQUE, lang VARCHAR(2),
            level VARCHAR(20), target_exams JSON, recovery_hash VARCHAR(64),
            created_at DATETIME, last_seen DATETIME)'''))
        connection.execute(text("INSERT INTO device (id, token, lang) VALUES (1, 'existing', 'hi')"))
        connection.execute(text('CREATE TABLE attempt (id INTEGER PRIMARY KEY)'))
    ensure_schema(old)
    columns = {c['name'] for c in inspect(old).get_columns('device')}
    assert 'backup_source_id' in columns
    assert 'backup_import' in inspect(old).get_table_names()
    assert 'backup_id' in {c['name'] for c in inspect(old).get_columns('attempt')}
    with old.connect() as connection:
        assert connection.execute(text('SELECT token FROM device WHERE id=1')).scalar() == 'existing'
    old.dispose()


def test_reset_rotates_backup_namespace_without_changing_identity(client, db):
    backup = history(client, db)
    device_id = stored_attempt(db, backup['attempts'][0]['id']).device_id
    assert client.post('/api/v1/me/reset-progress', json={'confirm': True}).status_code == 200
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 200
    exported = client.get('/api/v1/backup/export').json()
    assert exported['source_id'] != backup['source_id']
    assert stored_attempt(db, exported['attempts'][0]['id']).device_id == device_id
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': exported}).json()['skipped'] == 1


def test_export_size_includes_restore_wrapper(client, db, monkeypatch):
    from app import backup as module
    backup = history(client, db)
    from app.backup import ProgressBackup, RestoreRequest
    import json
    model = ProgressBackup.model_validate_json(json.dumps(backup))
    payload_size = len(model.model_dump_json().encode())
    wrapper_size = len(RestoreRequest(confirm=True, backup=model).model_dump_json().encode())
    assert wrapper_size > payload_size
    monkeypatch.setattr(module, 'MAX_BYTES', wrapper_size - 1)
    assert client.get('/api/v1/backup/export').status_code == 413


def test_concurrent_receipt_constraint_returns_conflict(client, db, monkeypatch):
    from sqlalchemy.exc import IntegrityError
    from sqlalchemy.orm import Session
    backup = history(client, db)
    client.cookies.clear()
    count = db.query(Device).count()

    def collided(_session):
        raise IntegrityError('receipt uniqueness', {}, RuntimeError('race'))

    monkeypatch.setattr(Session, 'commit', collided)
    assert client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': backup}).status_code == 409
    assert db.query(Device).count() == count


def test_recovery_preserves_native_export_namespace(client, db):
    history(client, db)
    code = client.post('/api/v1/sync/code', json={}).json()['code']
    client.cookies.clear()
    current_backup = history(client, db)
    count = db.query(Attempt).count()
    assert client.post('/api/v1/sync/restore', json={'code': code}).status_code == 200
    result = client.post('/api/v1/backup/restore', json={'confirm': True, 'backup': current_backup})
    assert result.status_code == 200
    assert result.json()['imported'] == 0 and result.json()['skipped'] == 1
    assert db.query(Attempt).count() == count


def test_legacy_attempt_backup_identity_assigned_once(client, db):
    a = client.post('/api/v1/practice', json={'topic_id': topic_id(db, 'percentage'), 'count': 2}).json()
    row = db.get(Attempt, a['id'])
    row.backup_id = None  # Existing database rows have a nullable added column before first export.
    db.commit()
    first = client.get('/api/v1/backup/export').json()
    second = client.get('/api/v1/backup/export').json()
    assert first['attempts'][0]['id'] == second['attempts'][0]['id']
    assert first['attempts'][0]['id'] != a['id']
    assert 1 << 52 <= first['attempts'][0]['id'] < 1 << 53
