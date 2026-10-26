"""Google sign-in: audience checked ID tokens and single-use browser-bound nonce."""
import base64
import hashlib
import hmac
import math
import os
import re
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlsplit, parse_qsl

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import delete
from sqlalchemy.exc import IntegrityError
from starlette.concurrency import run_in_threadpool

from . import config
from .db import get_db
from .classroom import body, digest, fail, rate, login_session, current
from .classroom_models import ClassroomAccount
from .google_auth_models import GoogleIdentity, GoogleChallenge

router = APIRouter(prefix='/api/v1/classroom/google')
COOKIE = 'ss_google_nonce'
PATH = '/api/v1/classroom/google'


def safe_target(value):
    if not isinstance(value, str) or len(value) > 256:
        return '/classroom'
    try:
        parts = urlsplit(value)
    except ValueError:
        return '/classroom'
    if parts.scheme or parts.netloc or parts.fragment:
        return '/classroom'
    if re.fullmatch(r'/w/[A-Za-z0-9_-]{16,128}', parts.path) and not parts.query:
        return value
    if parts.path == '/login':
        from .auth_navigation import study_target
        target = dict(parse_qsl(parts.query)).get('return_to', '/')
        return '/login?' + urlencode({'return_to': study_target(target)})
    if parts.path != '/classroom':
        return '/classroom'
    allowed = []
    for key, item in parse_qsl(parts.query):
        if key == 'view' and item in ('workspace', 'groups', 'classes', 'shared'):
            allowed.append((key, item))
        elif key in ('join', 'invite', 'workspace') and re.fullmatch(r'[A-Za-z0-9_-]{16,128}', item):
            allowed.append((key, item))
    return '/classroom' + ('?' + urlencode(allowed) if allowed else '')


def client_id():
    return os.getenv('GOOGLE_WEB_CLIENT_ID', '').strip()


def configured():
    if not client_id():
        fail('google_not_configured', 503)


def verify_token(encoded):
    # The official verifier validates signature, issuer, audience and expiry.
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest
    transport = GoogleRequest()
    def bounded_request(*args, **kwargs):
        kwargs['timeout'] = 10
        return transport(*args, **kwargs)
    return id_token.verify_oauth2_token(encoded, bounded_request, client_id())


def issue(request, response, db, web=False):
    configured()
    if current(request, db):
        fail('already_signed_in', 409)
    rate(db, 'google-challenge:' + (request.client.host if request.client else 'unknown'), 30)
    token, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48) if web else None
    db.execute(delete(GoogleChallenge).where(GoogleChallenge.expires <= datetime.utcnow()))
    target = safe_target(request.query_params.get('return_to', '/classroom'))
    db.add(GoogleChallenge(key=digest(token), nonce=nonce, verifier=verifier, return_to=target,
                           expires=datetime.utcnow() + timedelta(minutes=5)))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=300, httponly=True,
                        secure=config.COOKIE_SECURE, samesite='lax', path=PATH)
    response.headers['Cache-Control'] = 'no-store'
    return token, nonce, verifier


def challenge(request, db, web=False):
    key = digest(request.cookies.get(COOKIE, ''))
    row = db.get(GoogleChallenge, key)
    if not row or row.expires <= datetime.utcnow() or bool(row.verifier) != web:
        fail('google_challenge_expired', 401)
    return row


async def authenticate(encoded, row, response, db):
    if not isinstance(encoded, str) or not 20 <= len(encoded) <= 16384:
        fail('google_invalid_token', 401)
    try:
        claims = await run_in_threadpool(verify_token, encoded)
    except Exception:
        # Never expose a token, verification payload or upstream error.
        fail('google_invalid_token', 401)
    if not isinstance(claims, dict):
        fail('google_invalid_token', 401)
    sub, nonce = claims.get('sub'), claims.get('nonce')
    if (not isinstance(sub, str) or not 1 <= len(sub) <= 255
            or claims.get('aud') != client_id()
            or claims.get('iss') not in ('accounts.google.com', 'https://accounts.google.com')
            or claims.get('email_verified') is not True
            or not isinstance(nonce, str) or not hmac.compare_digest(nonce.encode(), row.nonce.encode())
            or type(claims.get('exp')) not in (int, float)
            or not math.isfinite(claims['exp']) or claims['exp'] <= time.time()):
        fail('google_invalid_token', 401)
    # Conditional DELETE is atomic across workers: an ID token can log in once.
    consumed = db.execute(delete(GoogleChallenge).where(
        GoogleChallenge.key == row.key, GoogleChallenge.expires > datetime.utcnow())).rowcount
    if consumed != 1:
        db.rollback()
        fail('google_challenge_expired', 401)
    identity = db.get(GoogleIdentity, sub)
    if identity:
        account = db.get(ClassroomAccount, identity.account_id)
    else:
        name = claims.get('name')
        name = name.strip()[:80] if isinstance(name, str) else ''
        # Valid PBKDF field structure, but a random 256-bit unknown password.
        salt = secrets.token_hex(16)
        password = hashlib.pbkdf2_hmac('sha256', secrets.token_bytes(32), bytes.fromhex(salt), 600000).hex()
        account = ClassroomAccount(username='google_' + secrets.token_hex(12),
                                   name=name or 'Google learner', password=salt + ':' + password)
        db.add(account)
        db.flush()
        db.add(GoogleIdentity(subject=sub, account_id=account.id))
    try:
        result = login_session(db, account, response)
    except IntegrityError:
        db.rollback()
        fail('google_retry', 409)
    response.delete_cookie(COOKIE, path=PATH)
    response.headers['Cache-Control'] = 'no-store'
    return result


@router.get('/config')
def configuration(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    return dict(enabled=bool(client_id()), client_id=client_id(),
                web_enabled=bool(client_id() and os.getenv('GOOGLE_CLIENT_SECRET')))


@router.post('/challenge')
async def new_challenge(request: Request, response: Response, db=Depends(get_db)):
    await body(request)
    _, nonce, _ = issue(request, response, db)
    return dict(nonce=nonce, client_id=client_id())


@router.post('/token')
async def token_login(request: Request, response: Response, db=Depends(get_db)):
    data = await body(request)
    configured()
    rate(db, 'google-token:' + (request.client.host if request.client else 'unknown'), 30)
    if current(request, db):
        fail('already_signed_in', 409)
    return await authenticate(data.get('id_token'), challenge(request, db), response, db)


def callback_url():
    return config.SITE_URL.rstrip('/') + PATH + '/callback'


@router.get('/start')
def web_start(request: Request, db=Depends(get_db)):
    if not os.getenv('GOOGLE_CLIENT_SECRET'):
        fail('google_web_not_configured', 503)
    response = RedirectResponse('/', status_code=303)
    state, nonce, verifier = issue(request, response, db, web=True)
    pkce = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    response.headers['location'] = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(dict(
        client_id=client_id(), redirect_uri=callback_url(), response_type='code',
        scope='openid email profile', state=state, nonce=nonce,
        code_challenge=pkce, code_challenge_method='S256', prompt='select_account'))
    return response


async def finish_web_callback(request, db):
    configured()
    if not os.getenv('GOOGLE_CLIENT_SECRET'):
        fail('google_web_not_configured', 503)
    if current(request, db):
        fail('already_signed_in', 409)
    row = challenge(request, db, web=True)
    state = request.query_params.get('state', '')
    if not hmac.compare_digest(digest(state), row.key):
        fail('google_state_rejected', 401)
    code = request.query_params.get('code', '')
    if request.query_params.get('error') or not code or len(code) > 4096:
        fail('google_cancelled', 400)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            result = await client.post('https://oauth2.googleapis.com/token', data=dict(
                client_id=client_id(), client_secret=os.getenv('GOOGLE_CLIENT_SECRET', ''),
                code=code, redirect_uri=callback_url(), grant_type='authorization_code',
                code_verifier=row.verifier))
            result.raise_for_status()
            encoded = result.json().get('id_token')
    except (httpx.HTTPError, ValueError):
        fail('google_exchange_failed', 502)
    response = RedirectResponse(row.return_to, status_code=303)
    await authenticate(encoded, row, response, db)
    return response


@router.get('/callback')
async def web_callback(request: Request, db=Depends(get_db)):
    try:
        return await finish_web_callback(request, db)
    except HTTPException:
        db.rollback()
        # Fixed local destination: provider errors and state failures cannot
        # turn into an open redirect or expose callback parameters to the UI.
        response = RedirectResponse('/login?google_error=1', status_code=303)
        response.delete_cookie(COOKIE, path=PATH)
        response.headers['Cache-Control'] = 'no-store'
        return response
