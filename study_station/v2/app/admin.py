"""
Admin panel (/admin): review AI questions and student reports, moderate jobs,
watch job sources and run maintenance. One password (ADMIN_PASSWORD), signed
cookie (SECRET_KEY). If either is missing the panel stays locked.
"""
import hmac
import subprocess
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from itsdangerous import BadSignature, SignatureExpired, TimestampSigner
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import config
from .db import get_db
from .jobs.sources import safe_http_url
from .models import (Job, JobSource, Question, QuestionReport, SourceHealth, Subject, Topic)

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=APP_DIR / 'templates')
templates.env.filters['safe_url'] = lambda u: safe_http_url(u) or ''
router = APIRouter(prefix='/admin')
COOKIE = 'ss_admin'
SESSION_SECONDS = 8 * 3600

_attempts = defaultdict(deque)
_lock = threading.Lock()


def configured():
    return bool(config.SECRET_KEY and config.ADMIN_PASSWORD)


def signer():
    return TimestampSigner(config.SECRET_KEY, salt='ss-admin')


def session_value():
    """Changes when ADMIN_PASSWORD changes, so changing the password logs every session out."""
    import hashlib
    return b'admin:' + hashlib.sha256(config.ADMIN_PASSWORD.encode()).hexdigest()[:16].encode()


def is_admin(request: Request):
    token = request.cookies.get(COOKIE)
    if not configured() or not token:
        return False
    try:
        return hmac.compare_digest(signer().unsign(token, max_age=SESSION_SECONDS), session_value())
    except (BadSignature, SignatureExpired):
        return False


def same_origin(request: Request):
    """CSRF guard for admin form posts (cookie is also SameSite=Strict)."""
    origin = request.headers.get('origin') or request.headers.get('referer')
    if not origin:
        return False
    return urlsplit(origin).netloc == request.headers.get('host')


def require_admin(request: Request):
    if not is_admin(request):
        raise HTTPException(303, headers={'Location': f'/admin/login?next={request.url.path}'})
    if request.method == 'POST' and not same_origin(request):
        raise HTTPException(403, 'Cross-site request blocked')
    return True


def page(request, name, **ctx):
    return templates.TemplateResponse(request, f'admin/{name}', {'request': request, **ctx})


def back(url):
    return RedirectResponse(url, status_code=303)


# ------------------------------------------------------------------ login
@router.get('/login', response_class=HTMLResponse)
def login_form(request: Request, next: str = '/admin'):
    return page(request, 'login.html', error=None if configured() else 'locked', next=next)


@router.post('/login')
def login(request: Request, password: str = Form(...), next: str = Form('/admin')):
    ip = request.client.host if request.client else '?'
    with _lock:
        q = _attempts[ip]
        now = time.monotonic()
        while q and now - q[0] > 900:
            q.popleft()
        if len(q) >= 5:
            return page(request, 'login.html', error='too_many', next=next)
        q.append(now)
    if not configured():
        return page(request, 'login.html', error='locked', next=next)
    if not hmac.compare_digest(password.encode(), config.ADMIN_PASSWORD.encode()):
        return page(request, 'login.html', error='wrong', next=next)
    target = next if next.startswith('/admin') and not next.startswith('//') else '/admin'
    resp = back(target)
    resp.set_cookie(COOKIE, signer().sign(session_value()).decode(), max_age=SESSION_SECONDS, httponly=True,
                    samesite='strict', secure=config.COOKIE_SECURE, path='/admin')
    return resp


@router.post('/logout')
def logout(_: bool = Depends(require_admin)):
    resp = back('/admin/login')
    resp.delete_cookie(COOKIE, path='/admin')
    return resp


# ------------------------------------------------------------------ dashboard
@router.get('', response_class=HTMLResponse)
def dashboard(request: Request, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    q_counts = dict(db.execute(select(Question.review_status, func.count()).group_by(Question.review_status)).all())
    open_reports = db.scalar(select(func.count(QuestionReport.id)).where(QuestionReport.resolved_at.is_(None)))
    j_counts = dict(db.execute(select(Job.status, func.count()).group_by(Job.status)).all())
    health = list(db.scalars(select(SourceHealth).order_by(SourceHealth.consecutive_failures.desc(), SourceHealth.source)))
    from .services import today_ist
    open_jobs = db.scalar(select(func.count(Job.id)).where(Job.status == 'verified', Job.job_type == 'latest',
                                                          Job.last_date >= today_ist()))
    return page(request, 'dashboard.html', q_counts=q_counts, open_reports=open_reports, j_counts=j_counts,
                health=health, open_jobs=open_jobs, runs=recent_runs(), report=health_report(db),
                release=release_info(), promo=promo_status())


# ------------------------------------------------------------------ dashboard 2.0 (read-only)
_report_cache = {'at': 0.0, 'value': None}
REPORT_TTL = 60          # seconds; observe.collect groups the whole question bank once


def health_report(db):
    """Learner counts, content/AI figures and alerts from app.observe (read-only, cached for a minute)."""
    now = time.monotonic()
    if _report_cache['value'] is None or now - _report_cache['at'] > REPORT_TTL:
        from . import observe
        _report_cache.update(at=now, value=observe.collect(db))
    return _report_cache['value']


def release_info():
    """Which source revision the server runs, from the deployment manifest; None if there is none."""
    import json
    p = config.SOURCE_RELEASE_PATH
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    files = data.get('files') or data.get('manifest') or {}
    return {'revision': str(data.get('revision') or data.get('commit') or '')[:40],
            'deployed_at': str(data.get('deployed_at') or data.get('created_at') or data.get('released_at') or ''),
            'branch': str(data.get('branch') or ''), 'files': len(files) if hasattr(files, '__len__') else None}


def promo_status():
    """Telegram/Shorts as seen in this server's copy of the workflow-owned posted logs (read-only).
    The logs are written on GitHub, so the copy is only as new as the last deployment; the date says so."""
    from .promo import posted as plog
    from .services import today_ist
    out = {'channel': config.PROMO_CHANNEL_URL, 'as_of': None, 'today': {}, 'last_day': None,
           'actions': 'https://github.com/SCHANDAN996/web-apps/actions'}
    p = plog.POSTED
    if not p.exists():
        return out
    data = plog.load(p)
    out['as_of'] = datetime.utcfromtimestamp(p.stat().st_mtime).strftime('%d-%m-%Y %H:%M UTC')
    days = sorted(data['days'])
    out['last_day'] = days[-1] if days else None
    today = data['days'].get(today_ist().isoformat(), {})
    out['today'] = {slot: sum(len(b) for b in batches) for slot, batches in today.items()}
    return out


# ------------------------------------------------------------------ questions
QUEUES = {
    'reported': 'Reported by students',
    'flagged': 'Auto-flagged (hidden)',
    'unreviewed': 'AI-generated, not reviewed',
    'verified': 'Verified',
}


@router.get('/questions', response_class=HTMLResponse)
def questions(request: Request, queue: str = 'reported', subject: str = '', page_no: int = 1,
              _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    per = 30
    q = select(Question).join(Topic).join(Subject)
    if queue == 'reported':
        q = q.where(Question.id.in_(select(QuestionReport.question_id).where(QuestionReport.resolved_at.is_(None))))
    elif queue in QUEUES:
        q = q.where(Question.review_status == queue)
    if subject:
        q = q.where(Subject.slug == subject)
    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = list(db.scalars(q.order_by(Question.id).offset((page_no - 1) * per).limit(per)))
    report_counts = dict(db.execute(select(QuestionReport.question_id, func.count())
                                    .where(QuestionReport.resolved_at.is_(None))
                                    .group_by(QuestionReport.question_id)).all())
    subjects = list(db.scalars(select(Subject).order_by(Subject.id)))
    return page(request, 'questions.html', rows=rows, queue=queue, queues=QUEUES, subject=subject,
                subjects=subjects, total=total, page_no=page_no, pages=max(1, -(-total // per)),
                report_counts=report_counts)


@router.get('/questions/{qid}', response_class=HTMLResponse)
def question_edit(qid: int, request: Request, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if q is None:
        raise HTTPException(404)
    reports = list(db.scalars(select(QuestionReport).where(QuestionReport.question_id == qid)
                              .order_by(QuestionReport.created_at.desc())))
    topics = list(db.scalars(select(Topic).join(Subject).order_by(Subject.id, Topic.order)))
    return page(request, 'question_edit.html', q=q, reports=reports, topics=topics)


def _opts(form, lang):
    vals = [(form.get(f'opt_{lang}_{i}') or '').strip() for i in range(4)]
    return vals if any(vals) else None


@router.post('/questions/{qid}')
async def question_save(qid: int, request: Request, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if q is None:
        raise HTTPException(404)
    form = await request.form()
    action = form.get('action', 'save')
    if action == 'delete':
        db.query(QuestionReport).filter_by(question_id=qid).delete()
        db.delete(q)
        db.commit()
        return back('/admin/questions?queue=' + form.get('queue', 'reported'))
    for lang in ('hi', 'en'):
        text = (form.get(f'text_{lang}') or '').strip() or None
        opts = _opts(form, lang)
        if text and (not opts or not all(opts)):
            raise HTTPException(400, f'{lang}: all four options are required')
        setattr(q, f'text_{lang}', text)
        setattr(q, f'options_{lang}', opts if text else None)
        setattr(q, f'solution_{lang}', (form.get(f'solution_{lang}') or '').strip() or None)
    if not q.text_hi and not q.text_en:
        raise HTTPException(400, 'question needs Hindi or English text')
    q.answer_index = int(form.get('answer_index', q.answer_index))
    if q.answer_index not in (0, 1, 2, 3):
        raise HTTPException(400, 'answer must be Aâ€“D')
    q.difficulty = form.get('difficulty') if form.get('difficulty') in ('easy', 'medium', 'hard') else q.difficulty
    if form.get('topic_id'):
        q.topic_id = int(form['topic_id'])
    q.source_type = form.get('source_type') if form.get('source_type') in ('ai_generated', 'pyq', 'editorial') else q.source_type
    q.source_ref = (form.get('source_ref') or '').strip() or None
    if q.source_type == 'pyq' and not q.source_ref:
        raise HTTPException(400, 'PYQ needs a source (exam, year, shift)')
    status = {'verify': 'verified', 'flag': 'flagged', 'save': q.review_status}.get(action, q.review_status)
    q.review_status = status
    q.review_note = (form.get('review_note') or '').strip()[:200] or None
    q.reviewed_at = datetime.utcnow()
    if action in ('verify', 'flag') or form.get('resolve_reports'):
        for r in db.scalars(select(QuestionReport).where(QuestionReport.question_id == qid,
                                                         QuestionReport.resolved_at.is_(None))):
            r.resolved_at = datetime.utcnow()
    db.commit()
    nxt = form.get('next') or f'/admin/questions/{qid}'
    return back(nxt if nxt.startswith('/admin') else '/admin')


# ------------------------------------------------------------------ jobs
@router.get('/jobs', response_class=HTMLResponse)
def jobs(request: Request, status: str = 'pending', _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    q = select(Job)
    if status in ('pending', 'verified', 'legacy'):
        q = q.where(Job.status == status)
    elif status == 'upcoming':
        q = q.where(Job.job_type == 'upcoming')
    rows = list(db.scalars(q.order_by(Job.created_at.desc()).limit(200)))
    return page(request, 'jobs.html', rows=rows, status=status)


@router.get('/jobs/{jid}', response_class=HTMLResponse)
def job_edit(jid: int, request: Request, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    job = db.get(Job, jid)
    if job is None:
        raise HTTPException(404)
    return page(request, 'job_edit.html', job=job, sources=list(db.scalars(select(JobSource).where(JobSource.job_id == jid))))


def _date(v):
    v = (v or '').strip()
    return date.fromisoformat(v) if v else None


@router.post('/jobs/{jid}')
async def job_save(jid: int, request: Request, _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    from .jobs.sources import is_official
    job = db.get(Job, jid)
    if job is None:
        raise HTTPException(404)
    form = await request.form()
    action = form.get('action', 'save')
    if action == 'delete':
        db.delete(job)
        db.commit()
        return back('/admin/jobs?status=' + form.get('back_status', 'pending'))
    for f in ('title', 'org', 'vacancies', 'advt_no', 'eligibility'):
        setattr(job, f, (form.get(f) or '').strip() or (job.title if f == 'title' else None))
    for f in ('official_url', 'notification_url'):
        url = (form.get(f) or '').strip() or None
        if url and not url.lower().startswith(('http://', 'https://')):
            raise HTTPException(400, f'{f} must be http(s)')
        setattr(job, f, url)
    try:
        job.start_date, job.last_date = _date(form.get('start_date')), _date(form.get('last_date'))
    except ValueError:
        raise HTTPException(400, 'dates must be YYYY-MM-DD')
    for f in ('age_min', 'age_max'):
        v = (form.get(f) or '').strip()
        setattr(job, f, int(v) if v.isdigit() else None)
    job.min_qualification = form.get('min_qualification') or None
    job.category = form.get('category') or job.category
    job.job_type = form.get('job_type') or job.job_type
    job.last_date_text = job.last_date.strftime('%d-%m-%Y') if job.last_date else job.last_date_text
    if action == 'verify':
        if not is_official(job.notification_url or ''):
            raise HTTPException(400, 'Verify needs an official notification URL (gov.in/nic.in/â€¦ or a listed board)')
        job.status, job.verified_at = 'verified', datetime.utcnow()
    elif action == 'unpublish':
        job.status = 'pending'
    job.updated_at = datetime.utcnow()
    db.commit()
    return back(f'/admin/jobs/{jid}')


# ------------------------------------------------------------------ maintenance runs
RUNS = {
    'sweep': ['run'],
    'cleanup': ['cleanup'],
    'digest': ['digest', '--telegram', '--mark-sent'],
}


def log_dir():
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    return config.LOG_DIR


def recent_runs(n=6):
    files = sorted(log_dir().glob('admin-*.log'), reverse=True)[:n]
    return [{'name': f.name, 'tail': f.read_text(encoding='utf-8', errors='replace')[-1500:]} for f in files]


@router.post('/run/{what}')
def run(what: str, _: bool = Depends(require_admin)):
    if what not in RUNS:
        raise HTTPException(404)
    log = log_dir() / f'admin-{datetime.utcnow():%Y%m%d-%H%M%S}-{what}.log'
    with open(log, 'w') as fh:
        # Separate process: a sweep takes minutes and must not block the web worker.
        subprocess.Popen([sys.executable, '-m', 'app.jobs', *RUNS[what]], cwd=APP_DIR.parent,
                         stdout=fh, stderr=subprocess.STDOUT, start_new_session=True)
    return back('/admin#runs')


# Community reports are private to authenticated moderators; actions are audited.
@router.get('/community', response_class=HTMLResponse)
def community_queue(request: Request, report_id: str = '', _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    from .ugc import Report
    rows=list(db.scalars(select(Report).order_by(Report.resolved_at.is_not(None),Report.created_at).limit(25)))
    if report_id and not any(r.id == report_id for r in rows):
        selected = db.get(Report, report_id)
        if selected: rows.insert(0, selected)
    records={r.id:(r.evidence if r.id == report_id else None) for r in rows}
    return page(request,'community.html',reports=rows,records=records)

@router.post('/community/{report_id}')
def moderate_community(report_id: str, request: Request, action: str = Form(...), note: str = Form(''),
                        _: bool = Depends(require_admin), db: Session = Depends(get_db)):
    from .ugc import Report,Moderation,Suspension
    if action not in ('dismiss','remove','suspend') or not note.strip() or len(note)>2000:
        raise HTTPException(400,'Invalid moderation action')
    report=db.get(Report,report_id)
    if not report:raise HTTPException(404,'Report not found')
    if report.resolved_at:raise HTTPException(409,'Already resolved')
    if action in ('remove','suspend') and not report.record_id:
        raise HTTPException(409,'Reported content was deleted')
    if action == 'suspend' and not report.owner_id:
        raise HTTPException(409,'Reported account was deleted')
    if action in ('remove','suspend') and not db.get(Moderation,report.record_id):db.add(Moderation(record_id=report.record_id))
    if action=='suspend' and not db.get(Suspension,report.owner_id):db.add(Suspension(account_id=report.owner_id))
    report.action=action;report.note=note.strip();report.resolved_at=datetime.utcnow();db.commit()
    return back('/admin/community')
