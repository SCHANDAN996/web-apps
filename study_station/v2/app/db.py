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
