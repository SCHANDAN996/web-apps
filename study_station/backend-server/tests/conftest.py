import os
import sys
import types

import pytest

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)


@pytest.fixture(scope='session')
def app(tmp_path_factory):
    db_path = tmp_path_factory.mktemp('db') / 'test.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'
    os.environ['SECRET_KEY'] = 'test-secret'
    os.environ['ADMIN_PASSWORD'] = 'correct-horse'
    os.environ['COOKIE_SECURE'] = '0'
    os.environ['ALLOWED_ORIGINS'] = 'https://studystation.in'

    # The Gemini SDK is heavy and needs network — replace it with a fake.
    fake = types.ModuleType('google.generativeai')
    fake.configure = lambda **kw: None

    class FakeModel:
        def __init__(self, name):
            pass

        def generate_content(self, prompt):
            return types.SimpleNamespace(text='<img src=x onerror=alert(1)> Answer')

    fake.GenerativeModel = FakeModel
    fake.list_models = lambda: []
    google = types.ModuleType('google')
    google.generativeai = fake
    sys.modules['google'] = google
    sys.modules['google.generativeai'] = fake

    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    from security import limiter
    limiter.reset()
    return app.test_client()


@pytest.fixture
def admin_client(client):
    res = client.post('/admin/login', data={'password': 'correct-horse'})
    assert res.status_code == 302
    return client
