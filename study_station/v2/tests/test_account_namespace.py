import re
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session
from app.db import ensure_schema
from app.classroom_models import ClassroomAccount as Account
from app.classroom import public_account


def test_deleted_highest_account_never_reuses_namespace_or_id(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'accounts.db'))
    ensure_schema(engine)
    with Session(engine) as db:
        old = Account(username='old', name='Old', password='unused')
        db.add(old); db.commit()
        previous_id, previous_namespace = old.id, old.storage_namespace
        assert re.fullmatch(r'[a-f0-9]{48}', previous_namespace)
        db.delete(old); db.commit()
    # Persistence across connections/restarts, including an empty accounts table.
    engine.dispose()
    ensure_schema(engine)
    with Session(engine) as db:
        new = Account(username='new', name='New', password='unused')
        db.add(new); db.commit()
        assert new.id > previous_id
        assert new.storage_namespace != previous_namespace
        assert public_account(new)['legacy_workspace_scope'] is False


def test_existing_database_migration_preserves_ownership_and_high_water_mark(tmp_path):
    engine = create_engine('sqlite:///' + str(tmp_path / 'legacy.db'))
    with engine.begin() as conn:
        conn.execute(text('CREATE TABLE classroom_account (id INTEGER PRIMARY KEY, username VARCHAR(40), name VARCHAR(80), password TEXT, created_at DATETIME)'))
        conn.execute(text("INSERT INTO classroom_account VALUES (42, 'existing', 'Existing', 'unused', CURRENT_TIMESTAMP)"))
    ensure_schema(engine)
    with Session(engine) as db:
        old = db.get(Account, 42)
        assert old.legacy_workspace_scope is True
        namespace = old.storage_namespace
        assert re.fullmatch(r'[a-f0-9]{48}', namespace)
    ensure_schema(engine)
    with Session(engine) as db:
        old = db.get(Account, 42)
        assert old.storage_namespace == namespace
        db.delete(old); db.commit()
        new = Account(username='replacement', name='New', password='unused')
        db.add(new); db.commit()
        assert new.id > 42
        assert new.legacy_workspace_scope is False
        assert new.storage_namespace != namespace


def test_account_deletion_endpoint_recreate_does_not_inherit_scope(tmp_path):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.classroom import router as classroom_router
    from app.account_deletion import router as deletion_router
    from app.db import get_db
    engine = create_engine('sqlite:///' + str(tmp_path / 'endpoint.db'), connect_args={'check_same_thread': False})
    ensure_schema(engine)
    app = FastAPI()
    app.include_router(classroom_router); app.include_router(deletion_router)
    def database():
        with Session(engine, expire_on_commit=False) as session:
            yield session
    app.dependency_overrides[get_db] = database
    with TestClient(app) as client:
        old = client.post('/api/v1/classroom/signup', json={'username':'original','password':'long-enough-password'}).json()['account']
        deleted = client.request('DELETE', '/api/v1/classroom/account', json={'confirm':True,'username':'original'})
        assert deleted.status_code == 200
        new = client.post('/api/v1/classroom/signup', json={'username':'replacement','password':'long-enough-password'}).json()['account']
        assert new['id'] > old['id']
        assert new['storage_namespace'] != old['storage_namespace']
        assert new['legacy_workspace_scope'] is False
