"""Small, persistent classroom service: real accounts, scoped work and board events."""
import hashlib
import hmac
import json
import math
import re
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from . import config
from .db import get_db
from .models import Question
from .classroom_models import (ClassroomAccount as Account, ClassroomSession as Session,
    ClassroomRecord as Record, ClassroomMember as Member, ClassroomEvent as Event,
    ClassroomOperation as Operation, ClassroomRate as Rate)

router = APIRouter(prefix='/api/v1/classroom')
COOKIE = 'ss_classroom'

def fail(code, status=400):
    raise HTTPException(status, code)

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def public_account(a):
    return dict(id=a.id, username=a.username, name=a.name)

def serial(r):
    return dict(id=r.id, kind=r.kind, owner_id=r.owner_id, parent=r.parent,
                version=r.version, data=r.data)

def current(request, db):
    token = request.cookies.get(COOKIE, '')
    row = db.get(Session, digest(token)) if token else None
    if not row or row.expires <= datetime.utcnow():
        return None
    return db.get(Account, row.account_id)

def require(request, db):
    a = current(request, db)
    if not a:
        fail('sign_in_required', 401)
    return a

async def body(request):
    if request.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
        fail('json_required', 415)
    origin = request.headers.get('origin')
    if origin:
        expected = urlparse(config.SITE_URL or str(request.base_url))
        actual = urlparse(origin)
        if (actual.scheme, actual.netloc) != (expected.scheme, expected.netloc):
            fail('origin_rejected', 403)
    raw = await request.body()
    if len(raw) > 2_000_000:
        fail('payload_too_large', 413)
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        fail('invalid_json')
    if not isinstance(value, dict):
        fail('object_required')
    return value

def text(v, limit=160, required=True):
    if not isinstance(v, str) or len(v) > limit or (required and not v.strip()):
        fail('invalid_text')
    return v.strip()

def stroke(value):
    if not isinstance(value, dict): fail('invalid_stroke')
    if value.get('tool', 'pen') not in ('pen', 'erase', 'line', 'rect', 'circle'): fail('invalid_stroke')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', value.get('color', '')): fail('invalid_stroke')
    width = value.get('width')
    if type(width) not in (int, float) or not math.isfinite(width) or not .1 <= width <= 100: fail('invalid_stroke')
    points = value.get('points')
    if not isinstance(points, list) or not 1 <= len(points) <= 10000: fail('invalid_stroke')
    for point in points:
        if not isinstance(point, list) or len(point) != 2: fail('invalid_stroke')
        if any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 1 for v in point): fail('invalid_stroke')
    return value


def snapshot(value):
    if not isinstance(value, dict) or len(json.dumps(value)) > 1_500_000: fail('invalid_snapshot')
    pages = value.get('pages', [])
    if not isinstance(pages, list) or len(pages) > 100: fail('invalid_pages')
    total = 0
    for page in pages:
        if not isinstance(page, dict): fail('invalid_pages')
        strokes = page.get('strokes', [])
        if not isinstance(strokes, list) or len(strokes) > 10000: fail('invalid_pages')
        for item in strokes:
            stroke(item)
            total += len(item['points'])
            if total > 100000: fail('invalid_snapshot')
    return value


def rate(db, key, limit=12):
    now = datetime.utcnow()
    key = digest(key)
    row = db.get(Rate, key)
    if row and row.expires > now:
        changed = db.execute(update(Rate).where(Rate.key == key, Rate.count < limit).values(count=Rate.count + 1)).rowcount
        db.commit()
        if not changed:
            fail('try_later', 429)
    else:
        if row:
            db.delete(row)
            db.flush()
        db.add(Rate(key=key, count=1, expires=now + timedelta(minutes=15)))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            fail('try_later', 429)

def operation(db, a, d, scope):
    op = text(d.get('op_id'), 80)
    fingerprint = digest(scope + json.dumps(d, sort_keys=True, separators=(',', ':')))
    old = db.scalar(select(Operation).where(Operation.account_id == a.id, Operation.op_id == op))
    if old:
        if old.fingerprint != fingerprint:
            fail('operation_conflict', 409)
        return old.result, None
    return None, (op, fingerprint)

def finish(db, a, stamp, result):
    if stamp:
        db.add(Operation(account_id=a.id, op_id=stamp[0], fingerprint=stamp[1], result=result))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        fail('concurrent_operation_retry', 409)
    return result

def new_record(db, kind, a, data, parent=None):
    r = Record(id=secrets.token_urlsafe(18), kind=kind, owner_id=a.id, parent=parent, data=data)
    db.add(r)
    db.flush()
    return r

def record(db, rid, kind=None):
    r = db.get(Record, rid)
    if not r or (kind and r.kind != kind):
        fail('not_found', 404)
    return r

def membership(db, gid, aid):
    return db.scalar(select(Member).where(Member.group_id == gid, Member.account_id == aid))

def group_access(db, gid, a, teacher=False):
    g = record(db, gid, 'group')
    m = membership(db, gid, a.id)
    if not m or m.role == 'removed' or (teacher and m.role not in ('owner', 'teacher')):
        fail('not_allowed', 403)
    return g, m

def workspace_access(db, r, a, token=None, write=False):
    if r.owner_id == a.id:
        return
    if write:
        if a.id not in r.data.get('editors', []):
            fail('not_allowed', 403)
    elif a.id in r.data.get('editors', []):
        return
    elif not token or not r.share_hash or not hmac.compare_digest(r.share_hash, digest(token)):
        fail('not_allowed', 403)

def change(db, r, expected, data):
    if type(expected) is not int:
        fail('version_required')
    n = db.execute(update(Record).where(Record.id == r.id, Record.version == expected).values(data=data, version=expected + 1), execution_options={'synchronize_session': False}).rowcount
    if not n:
        fail('version_conflict', 409)
    db.expire(r)
    db.refresh(r)

@router.get('/me')
def me(request: Request, db=Depends(get_db)):
    a = current(request, db)
    return {'account': public_account(a) if a else None}

@router.post('/signup')
async def signup(request: Request, response: Response, db=Depends(get_db)):
    d = await body(request)
    rate(db, 'signup:' + (request.client.host if request.client else 'unknown'), 8)
    username = text(d.get('username'), 40).lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,39}', username):
        fail('username_format')
    password = d.get('password')
    if not isinstance(password, str) or not 10 <= len(password) <= 256:
        fail('password_length')
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600_000).hex()
    a = Account(username=username, name=text(d.get('name', username), 80), password=salt + ':' + hashed)
    db.add(a)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        fail('username_unavailable', 409)
    return login_session(db, a, response)

def login_session(db, a, response):
    token = secrets.token_urlsafe(32)
    db.add(Session(token=digest(token), account_id=a.id, expires=datetime.utcnow() + timedelta(days=30)))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=30*86400, httponly=True, secure=config.COOKIE_SECURE, samesite='lax', path='/')
    return {'account': public_account(a)}

@router.post('/login')
async def login(request: Request, response: Response, db=Depends(get_db)):
    d = await body(request)
    username = text(d.get('username'), 40).lower()
    rate(db, 'login-ip:' + (request.client.host if request.client else 'unknown'), 35)
    rate(db, 'login-user:' + username, 10)
    p = d.get('password')
    if not isinstance(p, str) or len(p) > 256:
        fail('invalid_credentials', 401)
    a = db.scalar(select(Account).where(Account.username == username))
    salt, expected = a.password.split(':') if a else ('00'*16, '00'*32)
    actual = hashlib.pbkdf2_hmac('sha256', p.encode(), bytes.fromhex(salt), 600_000).hex()
    if not a or not hmac.compare_digest(expected, actual):
        fail('invalid_credentials', 401)
    return login_session(db, a, response)

@router.post('/logout')
async def logout(request: Request, response: Response, db=Depends(get_db)):
    await body(request)
    db.execute(delete(Session).where(Session.token == digest(request.cookies.get(COOKIE, ''))))
    db.commit()
    response.delete_cookie(COOKIE, path='/')
    return {'ok': True}

@router.get('/hub')
def hub(request: Request, db=Depends(get_db)):
    a = require(request, db)
    groups = select(Member.group_id).where(Member.account_id == a.id, Member.role != 'removed')
    return {'workspaces': [serial(r) for r in db.scalars(select(Record).where(Record.kind == 'workspace', Record.owner_id == a.id).order_by(Record.created_at.desc()).limit(200))],
            'groups': [serial(r) for r in db.scalars(select(Record).where(Record.id.in_(groups)).limit(100))]}

@router.post('/workspaces')
async def create_workspace(request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request)
    old, stamp = operation(db, a, d, 'workspace')
    if old: return old
    rate(db, 'writes:' + str(a.id), 150)
    r = new_record(db, 'workspace', a, {'name': text(d.get('name')), 'snapshot': snapshot(d.get('snapshot', {'pages': []})), 'editors': []})
    return finish(db, a, stamp, {'workspace': serial(r)})

@router.get('/workspaces/{rid}')
def get_workspace(rid: str, request: Request, token: str | None = None, db=Depends(get_db)):
    a = require(request, db); r = record(db, rid, 'workspace')
    workspace_access(db, r, a, token)
    out = {'workspace': serial(r), 'source': None, 'source_status': None, 'can_write': r.owner_id == a.id or a.id in r.data.get('editors', [])}
    source = r.data.get('source')
    if source:
        src = db.get(Record, source['id'])
        if src and src.share_hash and hmac.compare_digest(src.share_hash, source['hash']):
            out.update(source=serial(src), source_status='linked')
        else: out['source_status'] = 'revoked'
    return out

@router.put('/workspaces/{rid}')
async def put_workspace(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); r = record(db, rid, 'workspace')
    workspace_access(db, r, a, write=True)
    old, stamp = operation(db, a, d, 'workspace:' + rid)
    if old: return old
    data = dict(r.data, name=text(d.get('name', r.data['name'])), snapshot=snapshot(d.get('snapshot', r.data['snapshot'])))
    change(db, r, d.get('version'), data)
    return finish(db, a, stamp, {'workspace': serial(r)})

@router.post('/workspaces/{rid}/share')
async def share_workspace(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); r = record(db, rid, 'workspace')
    if r.owner_id != a.id: fail('not_allowed', 403)
    old, stamp = operation(db, a, d, 'share:' + rid)
    if old: return old
    token = secrets.token_urlsafe(32); r.share_hash = digest(token)
    return finish(db, a, stamp, {'token': token, 'url': '/w/' + token})

@router.delete('/workspaces/{rid}/share')
async def revoke_workspace(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); await body(request); r = record(db, rid, 'workspace')
    if r.owner_id != a.id: fail('not_allowed', 403)
    r.share_hash = None; db.commit()
    return {'ok': True}

@router.get('/shared/{token}')
def shared_workspace(token: str, request: Request, db=Depends(get_db)):
    require(request, db)
    r = db.scalar(select(Record).where(Record.kind == 'workspace', Record.share_hash == digest(token)))
    if not r: fail('not_found', 404)
    return {'workspace': serial(r)}

@router.post('/workspaces/{rid}/editors')
async def editors(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); r = record(db, rid, 'workspace')
    if r.owner_id != a.id: fail('not_allowed', 403)
    aid = d.get('account_id')
    if type(aid) is not int or not db.get(Account, aid): fail('not_found', 404)
    values = set(r.data.get('editors', []))
    if d.get('allow') is True: values.add(aid)
    else: values.discard(aid)
    change(db, r, d.get('version'), dict(r.data, editors=sorted(values)))
    db.commit(); return {'workspace': serial(r)}

@router.post('/workspaces/{rid}/copy')
async def copy_workspace(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); r = record(db, rid, 'workspace')
    workspace_access(db, r, a, d.get('token'))
    old, stamp = operation(db, a, d, 'copy:' + rid)
    if old: return old
    data = {'name': text(d.get('name', r.data['name'])), 'snapshot': r.data['snapshot'], 'editors': []}
    if d.get('linked'):
        if not r.share_hash: fail('share_required')
        data.update(source={'id': r.id, 'hash': r.share_hash}, snapshot={'pages': []})
    cp = new_record(db, 'workspace', a, data)
    return finish(db, a, stamp, {'workspace': serial(cp)})

@router.post('/groups')
async def create_group(request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request)
    old, stamp = operation(db, a, d, 'group')
    if old: return old
    if d.get('kind') not in ('peer', 'class'): fail('invalid_kind')
    rate(db, 'groups:' + str(a.id), 20)
    r = new_record(db, 'group', a, {'name': text(d.get('name')), 'kind': d['kind'], 'goal': text(d.get('goal', ''), 2000, False)})
    db.add(Member(group_id=r.id, account_id=a.id, role='owner'))
    return finish(db, a, stamp, {'group': serial(r)})

@router.post('/groups/{gid}/invite')
async def invite(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); await body(request)
    g, _ = group_access(db, gid, a, True)
    token = secrets.token_urlsafe(32); g.share_hash = digest(token); db.commit()
    return {'token': token, 'url': '/classroom?join=' + token}

@router.delete('/groups/{gid}/invite')
async def revoke_invite(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); await body(request); g, _ = group_access(db, gid, a, True)
    g.share_hash = None; db.commit(); return {'ok': True}

@router.post('/join')
async def join_group(request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request)
    token = text(d.get('token'), 100)
    g = db.scalar(select(Record).where(Record.kind == 'group', Record.share_hash == digest(token)))
    if not g: fail('invalid_invite', 404)
    old, stamp = operation(db, a, d, 'join:' + g.id)
    if old: return old
    m = membership(db, g.id, a.id)
    if m and m.role == 'removed': fail('not_allowed', 403)
    if not m: db.add(Member(group_id=g.id, account_id=a.id, role='student'))
    return finish(db, a, stamp, {'group': serial(g)})

@router.get('/groups/{gid}')
def get_group(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); g, own = group_access(db, gid, a)
    members = []
    for m, ac in db.execute(select(Member, Account).join(Account, Account.id == Member.account_id).where(Member.group_id == gid, Member.role != 'removed')):
        members.append(dict(public_account(ac), role=m.role))
    rows = list(db.scalars(select(Record).where(Record.parent == gid).order_by(Record.created_at.desc()).limit(300)))
    return {'group': serial(g), 'role': own.role, 'members': members,
            'assignments': [serial(r) for r in rows if r.kind == 'assignment'],
            'sessions': [serial(r) for r in rows if r.kind == 'live'],
            'discussions': [serial(r) for r in rows if r.kind == 'discussion']}

@router.post('/groups/{gid}/members')
async def set_member(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); g, _ = group_access(db, gid, a)
    if g.owner_id != a.id: fail('not_allowed', 403)
    m = membership(db, gid, d.get('account_id'))
    if not m or m.account_id == a.id: fail('invalid_member')
    role = d.get('role')
    if role not in ('teacher', 'student', 'editor', 'removed'): fail('invalid_role')
    m.role = role; db.commit(); return {'ok': True}

@router.post('/groups/{gid}/assignments')
async def assignment(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); group_access(db, gid, a, True)
    old, stamp = operation(db, a, d, 'assignment:' + gid)
    if old: return old
    ids = d.get('question_ids', [])
    if not isinstance(ids, list) or len(ids) > 100 or any(type(i) is not int for i in ids): fail('invalid_questions')
    ids = list(dict.fromkeys(ids))
    valid = list(db.scalars(select(Question.id).where(Question.id.in_(ids), Question.review_status != 'flagged')))
    if set(ids) != set(valid): fail('question_unavailable')
    due = d.get('due_at')
    if due:
        try: due = datetime.fromisoformat(due.replace('Z', '+00:00')).isoformat()
        except (ValueError, TypeError, AttributeError): fail('invalid_deadline')
    r = new_record(db, 'assignment', a, {'name': text(d.get('name')), 'instructions': text(d.get('instructions', ''), 8000, False), 'question_ids': ids, 'due_at': due}, gid)
    return finish(db, a, stamp, {'assignment': serial(r)})

@router.get('/assignments/{rid}')
def get_assignment(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); r = record(db, rid, 'assignment'); _, m = group_access(db, r.parent, a)
    teacher = m.role in ('owner', 'teacher')
    qmap = {q.id: q for q in db.scalars(select(Question).where(Question.id.in_(r.data['question_ids']), Question.review_status != 'flagged'))}
    questions = []
    for qid in r.data['question_ids']:
        q = qmap.get(qid)
        if q: questions.append(dict(id=q.id, text_hi=q.text_hi, text_en=q.text_en, options_hi=q.options_hi, options_en=q.options_en))
    stmt = select(Record).where(Record.kind == 'submission', Record.parent == rid)
    if not teacher: stmt = stmt.where(Record.owner_id == a.id)
    return {'assignment': serial(r), 'questions': questions, 'submissions': [serial(s) for s in db.scalars(stmt.order_by(Record.created_at.desc()).limit(300))], 'can_review': teacher}

@router.post('/assignments/{rid}/submissions')
async def submit(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); ass = record(db, rid, 'assignment'); group_access(db, ass.parent, a)
    old, stamp = operation(db, a, d, 'submission:' + rid)
    if old: return old
    answers = d.get('answers', {})
    if not isinstance(answers, dict) or len(answers) > 100: fail('invalid_answers')
    allowed = {str(x) for x in ass.data['question_ids']}
    if any(k not in allowed or type(v) is not int or not 0 <= v <= 9 for k, v in answers.items()): fail('invalid_answers')
    rate(db, 'submissions:' + str(a.id), 60)
    previous = db.scalar(select(Record).where(Record.kind == 'submission', Record.parent == rid, Record.owner_id == a.id).order_by(Record.created_at.desc()))
    attempt = previous.data.get('attempt', 1) + 1 if previous else 1
    r = new_record(db, 'submission', a, {'answers': answers, 'snapshot': snapshot(d.get('snapshot', {'pages': []})), 'attempt': attempt, 'feedback': [], 'submitted_at': datetime.utcnow().isoformat() + 'Z'}, rid)
    return finish(db, a, stamp, {'submission': serial(r)})

@router.get('/submissions/{rid}')
def get_submission(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); r = record(db, rid, 'submission'); ass = record(db, r.parent, 'assignment'); _, m = group_access(db, ass.parent, a)
    if r.owner_id != a.id and m.role not in ('owner', 'teacher'): fail('not_allowed', 403)
    return {'submission': serial(r)}

@router.post('/submissions/{rid}/feedback')
async def feedback(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); r = record(db, rid, 'submission'); ass = record(db, r.parent, 'assignment'); group_access(db, ass.parent, a, True)
    old, stamp = operation(db, a, d, 'feedback:' + rid)
    if old: return old
    items = r.data.get('feedback', [])
    if len(items) >= 100: fail('feedback_limit')
    item = {'text': text(d.get('text'), 8000), 'account_id': a.id, 'at': datetime.utcnow().isoformat() + 'Z'}
    change(db, r, d.get('version', r.version), dict(r.data, feedback=items + [item]))
    return finish(db, a, stamp, {'submission': serial(r)})

@router.post('/groups/{gid}/discussions')
async def discussion(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); group_access(db, gid, a)
    old, stamp = operation(db, a, d, 'discussion:' + gid)
    if old: return old
    rate(db, 'discussion:' + str(a.id), 50)
    qid = d.get('question_id')
    if qid is not None and (type(qid) is not int or not db.get(Question, qid)): fail('question_unavailable')
    r = new_record(db, 'discussion', a, {'text': text(d.get('text'), 4000), 'question_id': qid}, gid)
    return finish(db, a, stamp, {'discussion': serial(r)})

@router.post('/groups/{gid}/sessions')
async def create_session(gid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); group_access(db, gid, a, True)
    old, stamp = operation(db, a, d, 'live:' + gid)
    if old: return old
    r = new_record(db, 'live', a, {'name': text(d.get('name')), 'active': True, 'last_seq': 0, 'snapshot': {'pages': []}}, gid)
    return finish(db, a, stamp, {'session': serial(r)})

@router.get('/sessions/{rid}')
def get_session(rid: str, request: Request, after: int = 0, db=Depends(get_db)):
    a = require(request, db); r = record(db, rid, 'live'); _, m = group_access(db, r.parent, a)
    if after < 0: fail('invalid_sequence')
    events = list(db.scalars(select(Event).where(Event.room_id == rid, Event.seq > after).order_by(Event.seq).limit(200)))
    return {'session': serial(r), 'events': [dict(seq=e.seq, account_id=e.account_id, data=e.data) for e in events],
            'last_seq': r.data.get('last_seq', 0), 'can_write': m.role in ('owner', 'teacher', 'editor')}

@router.post('/sessions/{rid}/events')
async def live_event(rid: str, request: Request, db=Depends(get_db)):
    a = require(request, db); d = await body(request); r = record(db, rid, 'live'); _, m = group_access(db, r.parent, a)
    op = text(d.get('op_id'), 80)
    old = db.scalar(select(Event).where(Event.room_id == rid, Event.op_id == op))
    if old:
        if old.account_id != a.id or old.data != {'type': d.get('type'), 'payload': d.get('payload', {})}: fail('operation_conflict', 409)
        return {'event': dict(seq=old.seq, account_id=a.id, data=old.data), 'version': r.version}
    kind = d.get('type')
    if kind not in ('stroke', 'page', 'hand', 'end', 'snapshot', 'focus', 'undo'): fail('invalid_event')
    if not r.data.get('active'): fail('session_ended', 409)
    teacher = m.role in ('owner', 'teacher')
    if kind != 'hand' and not (teacher or m.role == 'editor'): fail('not_allowed', 403)
    if kind == 'end' and not teacher: fail('not_allowed', 403)
    payload = d.get('payload', {})
    if not isinstance(payload, dict) or len(json.dumps(payload)) > 64_000: fail('invalid_event_payload')
    rate(db, 'events:' + str(a.id), 5000)
    seq = r.data.get('last_seq', 0) + 1
    data = dict(r.data, last_seq=seq)
    if kind == 'end': data['active'] = False
    if kind == 'stroke': stroke(payload)
    if kind == 'snapshot': data['snapshot'] = snapshot(payload)
    change(db, r, d.get('version'), data)
    event = Event(room_id=rid, account_id=a.id, op_id=op, seq=seq, data={'type': kind, 'payload': payload})
    db.add(event)
    try: db.commit()
    except IntegrityError:
        db.rollback(); fail('concurrent_operation_retry', 409)
    return {'event': dict(seq=seq, account_id=a.id, data=event.data), 'version': r.version}
