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
