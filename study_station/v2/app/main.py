"""Study Station v2 — FastAPI app: JSON API (/api/v1) + server-rendered pages."""
import secrets
from contextlib import asynccontextmanager
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import services
from .catalog import LEVEL_RANK, LEVELS, PATTERN_CHECKED
from .config import COOKIE_SECURE, DEVICE_COOKIE, SITE_URL
from .db import Base, engine, ensure_schema, get_db
from .i18n import client_strings, t
from .models import Attempt, Device, Exam, Job, Question, QuestionReport, ReviewCard, Subject, Topic

APP_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_app):
    ensure_schema(engine)
    yield


app = FastAPI(title='Study Station API', version='2.0', docs_url='/api/docs', redoc_url=None, lifespan=lifespan)
app.mount('/static', StaticFiles(directory=APP_DIR / 'static'), name='static')

from .admin import router as admin_router  # noqa: E402
app.include_router(admin_router)
templates = Jinja2Templates(directory=APP_DIR / 'templates')


# ---------------------------------------------------------------- middleware
@app.middleware('http')
async def headers_and_csrf(request: Request, call_next):
    if request.method in ('POST', 'PUT', 'DELETE') and request.url.path.startswith('/api/'):
        # JSON-only API: a cross-site <form> cannot send application/json.
        if 'application/json' not in request.headers.get('content-type', ''):
            return JSONResponse({'detail': 'JSON body required'}, status_code=415)
    response = await call_next(request)
    path = request.url.path
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    if path.startswith('/api/') or path.startswith('/admin'):
        response.headers['Cache-Control'] = 'no-store'
        if path.startswith('/admin'):
            response.headers['X-Frame-Options'] = 'DENY'
    elif path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=86400'
    elif 'Cache-Control' not in response.headers:
        response.headers['Cache-Control'] = 'no-cache'
    return response


class RateLimiter:
    def __init__(self):
        self.hits = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key, limit, window):
        now = time.monotonic()
        with self.lock:
            q = self.hits[key]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


limiter = RateLimiter()


def limit(request: Request, name: str, n: int, window: int):
    ip = request.client.host if request.client else 'unknown'
    if not limiter.allow(f'{name}:{ip}', n, window):
        raise HTTPException(429, 'Too many requests')


# ---------------------------------------------------------------- device
def current_device(request: Request, db: Session = Depends(get_db)) -> Device | None:
    token = request.cookies.get(DEVICE_COOKIE)
    if not token:
        return None
    d = db.scalar(select(Device).where(Device.token == token))
    if d and (datetime.utcnow() - d.last_seen).total_seconds() > 3600:
        d.last_seen = datetime.utcnow()
        db.commit()
    return d


def ensure_device(request: Request, response: Response, db: Session = Depends(get_db)) -> Device:
    """Create the anonymous learner on first real action (not on page views — bots)."""
    d = current_device(request, db)
    if d is None:
        limit(request, 'new_device', 30, 3600)
        d = Device(token=secrets.token_urlsafe(32), lang=lang_from_request(request))
        db.add(d)
        db.commit()
        set_device_cookie(response, d.token)
    return d


def set_device_cookie(response, token):
    response.set_cookie(DEVICE_COOKIE, token, max_age=2 * 365 * 24 * 3600, httponly=True,
                        samesite='lax', secure=COOKIE_SECURE)


def lang_from_request(request: Request):
    lang = request.cookies.get('ss_lang')
    return lang if lang in ('hi', 'en') else 'hi'


# ---------------------------------------------------------------- API models
class MeIn(BaseModel):
    lang: Literal['hi', 'en'] | None = None
    level: Literal['10th', '12th', 'graduate'] | None = None
    target_exams: list[str] | None = Field(default=None, max_length=10)


class PracticeIn(BaseModel):
    topic_id: int
    count: int = Field(default=10, ge=1, le=25)
    difficulty: Literal['easy', 'medium', 'hard'] | None = None


class MockIn(BaseModel):
    exam: str = Field(max_length=40)


class AnswerIn(BaseModel):
    question_id: int
    chosen_index: int | None = Field(default=None, ge=0, le=3)
    time_ms: int = Field(default=0, ge=0)
    marked: bool = False


class ReviseIn(BaseModel):
    chosen_index: int = Field(ge=0, le=3)


class RestoreIn(BaseModel):
    code: str = Field(min_length=12, max_length=24)


class ReportIn(BaseModel):
    reason: Literal['wrong_answer', 'wrong_solution', 'typo', 'unclear', 'translation', 'other']
    note: str = Field(default='', max_length=500)


def get_attempt(db: Session, device: Device | None, attempt_id: int) -> Attempt:
    a = db.get(Attempt, attempt_id)
    if a is None or device is None or a.device_id != device.id:
        raise HTTPException(404, 'Attempt not found')
    return a


def _service_error(e):
    if isinstance(e, LookupError):
        raise HTTPException(404, str(e))
    if isinstance(e, services.NotAllowed):
        raise HTTPException(409, str(e))
    raise HTTPException(400, str(e))


# ---------------------------------------------------------------- API
@app.get('/api/v1/catalog')
def api_catalog(db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Question.topic_id, func.count()).where(services.USABLE)
                             .group_by(Question.topic_id)).all())
    subjects = [{'slug': s.slug, 'name': {'hi': s.name_hi, 'en': s.name_en},
                 'topics': [{'id': tp.id, 'slug': tp.slug, 'name': {'hi': tp.name_hi, 'en': tp.name_en},
                             'questions': counts.get(tp.id, 0)} for tp in s.topics]}
                for s in db.scalars(select(Subject).order_by(Subject.id))]
    exams = [{'slug': e.slug, 'body': e.body, 'name': {'hi': e.name_hi, 'en': e.name_en}, 'stage': e.stage_en,
              'level': e.level, 'duration_min': e.duration_min,
              'sections': [{'subject': s.subject.slug, 'questions': s.questions, 'marks': s.marks_per_q,
                            'negative': round(s.negative_per_q, 4)} for s in e.sections]}
             for e in db.scalars(select(Exam).order_by(Exam.id))]
    return {'subjects': subjects, 'exams': exams, 'pattern_checked': PATTERN_CHECKED}


@app.get('/api/v1/me')
def api_me(device: Device | None = Depends(current_device)):
    if device is None:
        return {'onboarded': False}
    return {'onboarded': bool(device.level), 'lang': device.lang, 'level': device.level,
            'target_exams': device.target_exams}


@app.post('/api/v1/me')
def api_me_update(body: MeIn, response: Response, device: Device = Depends(ensure_device),
                  db: Session = Depends(get_db)):
    if body.lang:
        device.lang = body.lang
        response.set_cookie('ss_lang', body.lang, max_age=2 * 365 * 24 * 3600, samesite='lax', secure=COOKIE_SECURE)
    if body.level:
        device.level = body.level
    if body.target_exams is not None:
        valid = set(db.scalars(select(Exam.slug)))
        device.target_exams = [e for e in body.target_exams if e in valid]
    db.add(device)
    db.commit()
    return {'ok': True, 'lang': device.lang, 'level': device.level, 'target_exams': device.target_exams}


@app.post('/api/v1/sync/code')
def api_sync_code(request: Request, device: Device = Depends(ensure_device), db: Session = Depends(get_db)):
    limit(request, 'sync_code', 10, 3600)
    from . import sync
    return {'code': sync.new_code(db, device)}


@app.post('/api/v1/sync/restore')
def api_sync_restore(body: RestoreIn, request: Request, response: Response,
                     device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    limit(request, 'sync_restore', 10, 3600)
    from . import sync
    try:
        owner = sync.restore(db, device, body.code)
    except (ValueError, LookupError):
        raise HTTPException(404, 'code_not_found')
    set_device_cookie(response, owner.token)
    response.set_cookie('ss_lang', owner.lang, max_age=2 * 365 * 24 * 3600, samesite='lax', secure=COOKIE_SECURE)
    return {'ok': True, 'level': owner.level}


@app.post('/api/v1/practice')
def api_practice(body: PracticeIn, request: Request, device: Device = Depends(ensure_device),
                 db: Session = Depends(get_db)):
    limit(request, 'start', 60, 3600)
    try:
        a = services.start_practice(db, device, body.topic_id, body.count, body.difficulty)
    except Exception as e:
        _service_error(e)
    return services.attempt_payload(db, a)


@app.post('/api/v1/mock')
def api_mock(body: MockIn, request: Request, device: Device = Depends(ensure_device),
             db: Session = Depends(get_db)):
    limit(request, 'start', 60, 3600)
    try:
        a = services.start_mock(db, device, body.exam)
    except Exception as e:
        _service_error(e)
    return services.attempt_payload(db, a)


@app.get('/api/v1/attempts/{attempt_id}')
def api_attempt(attempt_id: int, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    return services.attempt_payload(db, get_attempt(db, device, attempt_id))


@app.post('/api/v1/attempts/{attempt_id}/answer')
def api_answer(attempt_id: int, body: AnswerIn, device: Device | None = Depends(current_device),
               db: Session = Depends(get_db)):
    a = get_attempt(db, device, attempt_id)
    try:
        return services.record_answer(db, device, a, body.question_id, body.chosen_index, body.time_ms, body.marked)
    except Exception as e:
        _service_error(e)


@app.post('/api/v1/attempts/{attempt_id}/finish')
def api_finish(attempt_id: int, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    a = get_attempt(db, device, attempt_id)
    return services.finish_attempt(db, device, a)


@app.get('/api/v1/attempts/{attempt_id}/result')
def api_result(attempt_id: int, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    a = get_attempt(db, device, attempt_id)
    if a.finished_at is None:
        raise HTTPException(409, 'not_finished')
    return services.result_payload(db, a)


@app.get('/api/v1/revise')
def api_revise(device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    if device is None:
        return {'cards': []}
    return {'cards': [{**services.public_question(c.question, i + 1), 'box': c.box}
                      for i, c in enumerate(services.due_cards(db, device))]}


@app.post('/api/v1/revise/{question_id}')
def api_revise_answer(question_id: int, body: ReviseIn, device: Device | None = Depends(current_device),
                      db: Session = Depends(get_db)):
    if device is None:
        raise HTTPException(404, 'card')
    try:
        return services.review_card(db, device, question_id, body.chosen_index)
    except Exception as e:
        _service_error(e)


@app.get('/api/v1/stats')
def api_stats(device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    if device is None:
        return {'attempted': 0}
    return services.device_stats(db, device)


@app.post('/api/v1/questions/{question_id}/report')
def api_report(question_id: int, body: ReportIn, request: Request, device: Device = Depends(ensure_device),
               db: Session = Depends(get_db)):
    limit(request, 'report', 20, 3600)
    if db.get(Question, question_id) is None:
        raise HTTPException(404, 'question')
    db.add(QuestionReport(question_id=question_id, device_id=device.id, reason=body.reason, note=body.note.strip()))
    db.commit()
    return {'ok': True}


def job_dict(j: Job):
    return {'slug': j.slug, 'title': j.title, 'org': j.org, 'category': j.category, 'type': j.job_type,
            'min_qualification': j.min_qualification, 'vacancies': j.vacancies, 'eligibility': j.eligibility,
            'last_date': j.last_date.isoformat() if j.last_date else None, 'last_date_text': j.last_date_text,
            'official_url': j.official_url, 'notification_url': j.notification_url, 'status': j.status,
            'start_date': j.start_date.isoformat() if j.start_date else None, 'age_min': j.age_min, 'age_max': j.age_max,
            'advt_no': j.advt_no, 'sources': len(j.sources),
            'verified_at': j.verified_at.isoformat() if j.verified_at else None}


@app.get('/api/v1/jobs')
def api_jobs(qualification: str | None = None, category: str | None = None,
             status: Literal['active', 'upcoming', 'closed', 'undated', 'updates'] = 'active', db: Session = Depends(get_db)):
    q = services.jobs_query(qualification, category, status).limit(100)
    return {'jobs': [job_dict(j) for j in db.scalars(q)]}


# ---------------------------------------------------------------- pages
def ctx(request: Request, device: Device | None, **extra):
    lang = device.lang if device else lang_from_request(request)
    return {'request': request, 'lang': lang, 'tr': lambda k: t(k, lang), 'device': device,
            'L': lambda hi, en: hi if lang == 'hi' else en, 'site_url': SITE_URL,
            'strings': client_strings(lang), 'path': request.url.path, **extra}


def render(name, request, device, http_status=200, **extra):
    return templates.TemplateResponse(request, name, ctx(request, device, **extra), status_code=http_status)


@app.get('/', response_class=HTMLResponse)
def page_home(request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    if device is None or not device.level:
        exams = list(db.scalars(select(Exam).order_by(Exam.id)))
        return render('onboarding.html', request, device, exams=exams, levels=LEVELS)
    stats = services.device_stats(db, device)
    exams = list(db.scalars(select(Exam).where(Exam.slug.in_(device.target_exams or [])))) or \
        list(db.scalars(select(Exam).where(Exam.level == device.level)))
    jobs = list(db.scalars(services.jobs_query(device.level, None, 'active').limit(3)))
    quick = db.execute(select(Topic, func.count(Question.id)).join(Question).where(services.USABLE)
                       .group_by(Topic.id).order_by(func.count(Question.id).desc()).limit(6)).all()
    return render('home.html', request, device, stats=stats, exams=exams, jobs=jobs, quick=quick)


@app.get('/settings', response_class=HTMLResponse)
def page_settings(request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    exams = list(db.scalars(select(Exam).order_by(Exam.id)))
    return render('onboarding.html', request, device, exams=exams, levels=LEVELS, settings_mode=True)


@app.get('/practice', response_class=HTMLResponse)
def page_practice(request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    counts = dict(db.execute(select(Question.topic_id, func.count()).where(services.USABLE)
                             .group_by(Question.topic_id)).all())
    mastery = {}
    if device:
        mastery = {t['id']: t for t in services.device_stats(db, device)['topics']}
    subjects = [s for s in db.scalars(select(Subject).order_by(Subject.id)) if any(counts.get(tp.id) for tp in s.topics)]
    return render('practice.html', request, device, subjects=subjects, counts=counts, mastery=mastery)


@app.get('/practice/{subject}/{topic}', response_class=HTMLResponse)
def page_topic(subject: str, topic: str, request: Request, device: Device | None = Depends(current_device),
               db: Session = Depends(get_db)):
    tp = db.scalar(select(Topic).join(Subject).where(Subject.slug == subject, Topic.slug == topic))
    if tp is None:
        raise HTTPException(404)
    by_diff = dict(db.execute(select(Question.difficulty, func.count()).where(
        Question.topic_id == tp.id, services.USABLE).group_by(Question.difficulty)).all())
    sample = db.scalar(select(Question).where(Question.topic_id == tp.id, services.USABLE,
                                              services.has_lang(ctx(request, device)['lang']))
                       .order_by(Question.id).limit(1))
    return render('topic.html', request, device, topic=tp, by_diff=by_diff, total=sum(by_diff.values()), sample=sample)


@app.get('/mock', response_class=HTMLResponse)
def page_mocks(request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    exams = list(db.scalars(select(Exam).order_by(Exam.id)))
    plans = {e.id: services.mock_plan(db, e) for e in exams}
    return render('mocks.html', request, device, exams=exams, plans=plans, level_rank=LEVEL_RANK)


@app.get('/mock/{slug}', response_class=HTMLResponse)
def page_exam(slug: str, request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    exam = db.scalar(select(Exam).where(Exam.slug == slug))
    if exam is None:
        raise HTTPException(404)
    plan = services.mock_plan(db, exam)
    return render('exam.html', request, device, exam=exam, plan=plan, pattern_checked=PATTERN_CHECKED)


@app.get('/attempt/{attempt_id}', response_class=HTMLResponse)
def page_attempt(attempt_id: int, request: Request, device: Device | None = Depends(current_device),
                 db: Session = Depends(get_db)):
    a = get_attempt(db, device, attempt_id)
    if a.finished_at is not None:
        return RedirectResponse(f'/result/{a.id}', status_code=303)
    return render('player.html', request, device, attempt=a)


@app.get('/result/{attempt_id}', response_class=HTMLResponse)
def page_result(attempt_id: int, request: Request, device: Device | None = Depends(current_device),
                db: Session = Depends(get_db)):
    a = get_attempt(db, device, attempt_id)
    if a.finished_at is None:
        return RedirectResponse(f'/attempt/{a.id}', status_code=303)
    return render('result.html', request, device, attempt=a, result=services.result_payload(db, a))


@app.get('/revise', response_class=HTMLResponse)
def page_revise(request: Request, device: Device | None = Depends(current_device)):
    return render('revise.html', request, device)


@app.get('/progress', response_class=HTMLResponse)
def page_progress(request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    stats = services.device_stats(db, device) if device else None
    return render('progress.html', request, device, stats=stats)


@app.get('/jobs', response_class=HTMLResponse)
def page_jobs(request: Request, status: Literal['active', 'upcoming', 'closed', 'undated', 'updates'] = 'active',
              qualification: str | None = None, category: str | None = None,
              device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    if qualification is None and device and device.level:
        qualification = device.level
    if qualification == 'all':
        qualification = None
    jobs = list(db.scalars(services.jobs_query(qualification, category, status).limit(100)))
    counts = {s: db.scalar(select(func.count()).select_from(services.jobs_query(qualification, category, s).subquery()))
              for s in ('active', 'upcoming', 'updates', 'closed', 'undated')}
    return render('jobs.html', request, device, jobs=jobs, status=status, qualification=qualification,
                  category=category, counts=counts, levels=LEVELS, today=services.today_ist())


@app.get('/jobs/{slug}', response_class=HTMLResponse)
def page_job(slug: str, request: Request, device: Device | None = Depends(current_device), db: Session = Depends(get_db)):
    job = db.scalar(select(Job).where(Job.slug == slug, Job.status.in_(('verified', 'legacy'))))
    if job is None:
        raise HTTPException(404)
    return render('job.html', request, device, job=job, today=services.today_ist())


@app.get('/sw.js')
def service_worker():
    return FileResponse(APP_DIR / 'static' / 'sw.js', media_type='text/javascript',
                        headers={'Cache-Control': 'no-cache', 'Service-Worker-Allowed': '/'})


@app.get('/manifest.webmanifest')
def manifest():
    return FileResponse(APP_DIR / 'static' / 'manifest.webmanifest', media_type='application/manifest+json')


@app.get('/offline', response_class=HTMLResponse)
def page_offline(request: Request):
    return render('offline.html', request, None)


@app.get('/robots.txt')
def robots():
    lines = ['User-agent: *', 'Disallow: /api/', 'Disallow: /admin', 'Disallow: /attempt/', 'Disallow: /result/',
             'Disallow: /revise', 'Disallow: /progress', 'Disallow: /settings']
    if SITE_URL:
        lines.append(f'Sitemap: {SITE_URL}/sitemap.xml')
    return Response('\n'.join(lines) + '\n', media_type='text/plain')


@app.get('/sitemap.xml')
def sitemap(db: Session = Depends(get_db)):
    base = SITE_URL or ''
    urls = ['/', '/practice', '/mock', '/jobs']
    urls += [f'/practice/{tp.subject.slug}/{tp.slug}' for tp in db.scalars(select(Topic))]
    urls += [f'/mock/{e.slug}' for e in db.scalars(select(Exam))]
    urls += [f'/jobs/{j.slug}' for j in db.scalars(services.jobs_query(status='active'))]
    body = ''.join(f'<url><loc>{base}{u}</loc></url>' for u in urls)
    return Response('<?xml version="1.0" encoding="UTF-8"?>'
                    f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>',
                    media_type='application/xml')


@app.exception_handler(404)
async def not_found(request: Request, exc):
    if request.url.path.startswith('/api/'):
        return JSONResponse({'detail': getattr(exc, 'detail', 'Not found')}, status_code=404)
    return templates.TemplateResponse(request, 'error.html', ctx(request, None, code=404), status_code=404)
