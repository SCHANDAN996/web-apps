from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def make_engine(url=DATABASE_URL):
    is_sqlite = url.startswith('sqlite')
    engine = create_engine(url, connect_args={'check_same_thread': False} if is_sqlite else {})
    if is_sqlite:
        @event.listens_for(engine, 'connect')
        def _pragmas(conn, _):
            cur = conn.cursor()
            cur.execute('PRAGMA journal_mode=WAL')
            cur.execute('PRAGMA synchronous=NORMAL')    # safe with WAL; one fsync per checkpoint, not per answer
            cur.execute('PRAGMA busy_timeout=5000')     # concurrent writers (2 workers + cron) wait instead of failing
            cur.execute('PRAGMA foreign_keys=ON')
            cur.close()
    return engine


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema(engine_=None):
    """create_all + add any new nullable columns to existing tables (SQLite/Postgres).

    Enough for additive changes while the app is young; switch to Alembic once
    columns need renaming or data migrations.
    """
    from sqlalchemy import inspect, text
    eng = engine_ or engine
    Base.metadata.create_all(eng)
    insp = inspect(eng)
    with eng.begin() as conn:
        for table in Base.metadata.sorted_tables:
            have = {c['name'] for c in insp.get_columns(table.name)}
            for col in table.columns:
                if col.name not in have:
                    ddl = col.type.compile(dialect=eng.dialect)
                    conn.execute(text(f'ALTER TABLE {table.name} ADD COLUMN {col.name} {ddl}'))

        # Only accounts present during migration can adopt their legacy local scope.
        if 'classroom_account' in Base.metadata.tables:
            import secrets
            rows = conn.execute(text('SELECT id FROM classroom_account WHERE storage_namespace IS NULL')).all()
            for (account_id,) in rows:
                conn.execute(text('UPDATE classroom_account SET storage_namespace=:namespace, legacy_workspace_scope=:legacy WHERE id=:id AND storage_namespace IS NULL'),
                             dict(namespace=secrets.token_hex(24), legacy=True, id=account_id))
            # Preserve the old high-water mark before any account can be deleted.
            highest = conn.execute(text('SELECT MAX(id) FROM classroom_account')).scalar() or 0
            reserved = conn.execute(text('SELECT MAX(id) FROM classroom_account_identity')).scalar() or 0
            if highest > reserved:
                conn.execute(text('INSERT INTO classroom_account_identity (id) VALUES (:id)'), dict(id=highest))
