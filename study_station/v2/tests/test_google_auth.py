import time
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import google_auth as auth
from app.classroom import router as classroom_router
from app.db import Base, engine
from app.google_auth_models import GoogleIdentity, GoogleChallenge


@pytest.fixture
def google(db, monkeypatch):
    Base.metadata.create_all(engine)
    monkeypatch.setenv('GOOGLE_WEB_CLIENT_ID', 'test.apps.googleusercontent.com')
    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(classroom_router)
    client = TestClient(app)
    # Shared test database rates must not make auth checks order-dependent.
    from app.classroom_models import ClassroomRate
    db.query(ClassroomRate).delete(); db.commit()
    yield client
    client.close()


def claims(nonce, **extra):
    return dict(sub='test-' + uuid.uuid4().hex, nonce=nonce, aud=auth.client_id(),
                iss='https://accounts.google.com', email_verified=True,
                exp=time.time()+600, name='Student', **extra)


def start(client):
    r = client.post('/api/v1/classroom/google/challenge', json={})
    assert r.status_code == 200, r.text
    assert 'HttpOnly' in r.headers['set-cookie']
    return r.json()['nonce']


def test_verified_login_and_one_use(google, monkeypatch, db):
    nonce = start(google)
    old_cookie = google.cookies.get(auth.COOKIE)
    data = claims(nonce)
    monkeypatch.setattr(auth, 'verify_token', lambda encoded: data)
    r = google.post('/api/v1/classroom/google/token', json={'id_token':'x'*30})
    assert r.status_code == 200, r.text
    account = r.json()['account']
    assert db.get(GoogleIdentity, data['sub']).account_id == account['id']
    assert google.get('/api/v1/classroom/me').json()['account'] == account
    google.post('/api/v1/classroom/logout', json={})
    google.cookies.set(auth.COOKIE, old_cookie, path=auth.PATH)
    assert google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30}).status_code == 401
    google.cookies.clear()
    nonce2 = start(google)
    data['nonce'] = nonce2
    again = google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30})
    assert again.json()['account']['id'] == account['id']


@pytest.mark.parametrize('field,value', [('aud','wrong'),('iss','evil'),('email_verified',False),('exp',0),('nonce','wrong'),('nonce','अवैध'),('sub','')])
def test_reject_invalid_claims(google, monkeypatch, field, value):
    data = claims(start(google)); data[field] = value
    monkeypatch.setattr(auth, 'verify_token', lambda encoded: data)
    assert google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30}).status_code == 401
    assert google.get('/api/v1/classroom/me').json()['account'] is None


def test_cookie_origin_and_configuration(google, monkeypatch):
    nonce = start(google)
    monkeypatch.setattr(auth, 'verify_token', lambda encoded: claims(nonce))
    app = FastAPI(); app.include_router(auth.router)
    with TestClient(app) as stranger:
        assert stranger.post('/api/v1/classroom/google/token',json={'id_token':'x'*30}).status_code == 401
    assert google.post('/api/v1/classroom/google/challenge',json={},headers={'Origin':'https://evil.example'}).status_code == 403
    monkeypatch.delenv('GOOGLE_WEB_CLIENT_ID')
    assert google.get('/api/v1/classroom/google/config').json()['enabled'] is False
    assert google.post('/api/v1/classroom/google/challenge',json={}).status_code == 503


def test_web_pkce_safe_redirect_state(google, monkeypatch, db):
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET','test-not-real')
    r = google.get('/api/v1/classroom/google/start?return_to=https://evil.example',follow_redirects=False)
    assert r.status_code == 303
    from urllib.parse import urlparse, parse_qs
    params = parse_qs(urlparse(r.headers['location']).query)
    assert params['scope'] == ['openid email profile']
    assert params['code_challenge_method'] == ['S256']
    row = db.get(GoogleChallenge, auth.digest(params['state'][0]))
    assert row.return_to == '/classroom'
    denied = google.get('/api/v1/classroom/google/callback?state=wrong&code=x',follow_redirects=False)
    assert denied.status_code == 303
    assert denied.headers['location'] == '/classroom?google_error=1'


def test_google_email_never_links_local_account(google, monkeypatch):
    name = 'local' + uuid.uuid4().hex[:12]
    local = google.post('/api/v1/classroom/signup',json={'username':name,'password':'a-long-password'}).json()['account']
    google.post('/api/v1/classroom/logout',json={})
    data = claims(start(google),email=name+'@gmail.com')
    monkeypatch.setattr(auth, 'verify_token', lambda encoded: data)
    account=google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30}).json()['account']
    assert account['id'] != local['id']


def test_expired_nonce_and_invalid_signature(google, monkeypatch, db):
    from datetime import datetime, timedelta
    nonce = start(google)
    row = db.get(GoogleChallenge, auth.digest(google.cookies.get(auth.COOKIE)))
    row.expires = datetime.utcnow() - timedelta(seconds=1)
    db.commit()
    monkeypatch.setattr(auth, 'verify_token', lambda encoded: claims(nonce))
    assert google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30}).status_code == 401
    start(google)
    def invalid(encoded):
        raise ValueError('Invalid signature; private payload must not be returned')
    monkeypatch.setattr(auth, 'verify_token', invalid)
    r = google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30})
    assert r.status_code == 401
    assert 'private payload' not in r.text


def test_real_verifier_rejects_unsigned_token(google):
    start(google)
    r = google.post('/api/v1/classroom/google/token',json={'id_token':'x'*30})
    assert r.status_code == 401


def test_web_callback_creates_session_and_preserves_invite(google, monkeypatch):
    from urllib.parse import parse_qs, urlparse
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET','test-not-real')
    target = '/classroom?join=' + 'a'*30
    r=google.get('/api/v1/classroom/google/start',params={'return_to':target},follow_redirects=False)
    params=parse_qs(urlparse(r.headers['location']).query)
    data=claims(params['nonce'][0])
    monkeypatch.setattr(auth,'verify_token',lambda encoded:data)
    seen={}
    class Reply:
        def raise_for_status(self): pass
        def json(self): return {'id_token':'x'*30}
    class Client:
        def __init__(self, **kwargs): pass
        async def __aenter__(self): return self
        async def __aexit__(self,*args): pass
        async def post(self,url,data):
            seen.update(data)
            return Reply()
    monkeypatch.setattr(auth.httpx,'AsyncClient',Client)
    result=google.get('/api/v1/classroom/google/callback',params={'state':params['state'][0],'code':'test-code'},follow_redirects=False)
    assert result.status_code==303
    assert result.headers['location']==target
    assert seen['code_verifier'] and seen['code']=='test-code'
    assert google.get('/api/v1/classroom/me').json()['account']['name']=='Student'


@pytest.mark.parametrize('value', ['https://evil.example','//evil.example','/classroom/../evil','/classroom?next=https://evil.example','http://[bad'])
def test_safe_target(value):
    assert auth.safe_target(value)=='/classroom'
