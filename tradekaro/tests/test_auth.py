"""
Dashboard login guard.

Built against a minimal Flask app rather than the real app.py, which pulls in
eventlet, the 4 GB database and the whole src tree on import. init_auth() is
the entire surface being tested, so a stand-in app exercises it honestly.
"""
import os
import sys

import pytest
from flask import Flask
from werkzeug.security import generate_password_hash

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT)

PASSWORD = 'correct-horse-battery'


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv('DASH_PASSWORD_HASH', generate_password_hash(PASSWORD))
    monkeypatch.setenv('FLASK_SECRET_KEY', 'test-secret-not-the-shipped-one')

    # Imported inside the fixture so the env vars above are in place before
    # init_auth reads them.
    import importlib

    from src import auth as auth_module
    importlib.reload(auth_module)

    app = Flask(__name__, template_folder=os.path.join(ROOT, 'templates'))
    app.config['TESTING'] = True

    @app.route('/')
    def index():
        return 'dashboard'

    @app.route('/api/place_trade', methods=['POST'])
    def place_trade():
        return {'placed': True}

    auth_module.init_auth(app)
    return app.test_client()


def test_dashboard_redirects_to_login_when_signed_out(client):
    response = client.get('/')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_api_returns_401_not_a_redirect(client):
    """A JSON caller needs a status it can act on, not an HTML login page."""
    response = client.post('/api/place_trade')
    assert response.status_code == 401
    assert response.get_json()['error'] == 'Login required'


def test_place_trade_is_unreachable_without_login(client):
    """The route that spends money, specifically."""
    assert client.post('/api/place_trade').status_code == 401


def test_correct_password_grants_access(client):
    response = client.post('/login', data={'password': PASSWORD})
    assert response.status_code == 302

    assert client.get('/').status_code == 200
    assert client.post('/api/place_trade').get_json() == {'placed': True}


def test_wrong_password_is_rejected(client):
    response = client.post('/login', data={'password': 'wrong'})
    assert response.status_code == 401
    assert client.get('/').status_code == 302


def test_logout_ends_the_session(client):
    client.post('/login', data={'password': PASSWORD})
    assert client.get('/').status_code == 200

    client.get('/logout')
    assert client.get('/').status_code == 302


def test_repeated_failures_lock_the_client_out(client):
    for _ in range(8):
        client.post('/login', data={'password': 'wrong'})

    # Even the right password is refused once the throttle trips.
    response = client.post('/login', data={'password': PASSWORD})
    assert response.status_code == 401
    assert b'Too many attempts' in response.data


def test_next_parameter_cannot_redirect_off_site(client):
    """`next` is attacker-controllable, so it must stay a local path."""
    response = client.post('/login?next=https://evil.example/steal',
                           data={'password': PASSWORD})
    assert response.headers['Location'] in ('/', 'http://localhost/')

    client.get('/logout')
    response = client.post('/login?next=//evil.example/steal',
                           data={'password': PASSWORD})
    assert 'evil.example' not in response.headers['Location']


def test_next_parameter_still_works_for_local_paths(client):
    response = client.post('/login?next=/portfolio',
                           data={'password': PASSWORD})
    assert response.headers['Location'] == '/portfolio'


def test_login_page_itself_is_reachable_signed_out(client):
    assert client.get('/login').status_code == 200


def test_missing_password_hash_fails_closed(monkeypatch):
    """No configured password must mean no dashboard -- not an open one."""
    monkeypatch.delenv('DASH_PASSWORD_HASH', raising=False)

    import importlib

    from src import auth as auth_module
    importlib.reload(auth_module)

    app = Flask(__name__, template_folder=os.path.join(ROOT, 'templates'))
    app.config['TESTING'] = True

    @app.route('/')
    def index():
        return 'dashboard'

    auth_module.init_auth(app)
    unconfigured = app.test_client()

    assert unconfigured.get('/').status_code == 503
    assert unconfigured.post('/login', data={'password': 'anything'}).status_code == 503


def test_security_headers_are_set(client):
    response = client.get('/login')
    assert response.headers['X-Frame-Options'] == 'DENY'
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
