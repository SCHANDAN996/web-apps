import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
_tmp = tempfile.mkdtemp()
os.environ['DATABASE_URL'] = f'sqlite:///{_tmp}/test.db'
os.environ['COOKIE_SECURE'] = '0'

from fastapi.testclient import TestClient  # noqa: E402

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.main import app, limiter  # noqa: E402
from app.models import Question, Topic  # noqa: E402
from app.seed import seed_catalog  # noqa: E402


def make_questions(db, subject, topic_slug, n, answer=1, **kw):
    t = db.query(Topic).join(Topic.subject).filter(Topic.slug == topic_slug).first()
    for i in range(n):
        db.add(Question(topic_id=t.id, level='10th', difficulty='easy', answer_index=answer,
                        text_hi=f'{topic_slug} प्रश्न {i}', options_hi=['क', 'ख', 'ग', 'घ'],
                        text_en=f'{topic_slug} question {i}', options_en=['a', 'b', 'c', 'd'],
                        solution_hi='हल', solution_en='solution', import_key=f'{topic_slug}-{i}-{kw.get("tag", "")}',
                        review_status=kw.get('status', 'unreviewed')))
    db.commit()
    return t


@pytest.fixture(scope='session', autouse=True)
def database():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_catalog(db)
        make_questions(db, 'quant', 'percentage', 30)
        make_questions(db, 'reasoning', 'analogy', 30)
        make_questions(db, 'ga', 'polity', 30)
        make_questions(db, 'english', 'noun', 30)
        make_questions(db, 'quant', 'average', 5, status='flagged', tag='bad')
    yield


@pytest.fixture
def client():
    limiter.hits.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db():
    with SessionLocal() as s:
        yield s


def topic_id(db, slug):
    return db.query(Topic).filter(Topic.slug == slug).first().id
