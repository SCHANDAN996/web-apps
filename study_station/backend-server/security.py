"""
🔐 Security helpers — Study Station backend

- Admin login (single password from env) guarding /admin/* and every
  write endpoint under /api/*.
- Small in-memory rate limiter for public endpoints (AI chat, login).
- Cache headers: no-store for admin/API, revalidate for site assets.

Config (backend-server/.env):
    SECRET_KEY       long random string — signs the admin session cookie
    ADMIN_PASSWORD   the admin panel password
    ALLOWED_ORIGINS  comma-separated origins allowed to call /api/* (CORS)
    TRUST_PROXY      1 when running behind nginx, so client IPs are real
    COOKIE_SECURE    0 only for local http testing (default 1)

If SECRET_KEY or ADMIN_PASSWORD is missing the admin panel stays locked —
it fails closed, never open.
"""
import hmac
import os
import re
import threading
import time
from collections import defaultdict, deque
from functools import wraps

from flask import (Blueprint, jsonify, redirect, render_template, request,
                   session, url_for)

auth_bp = Blueprint('auth', __name__)

# Write endpoints students are allowed to call without logging in.
PUBLIC_API_WRITES = {
    ('POST', '/api/chat'),
    ('POST', '/api/progress'),
}

SESSION_LIFETIME_SECONDS = 8 * 60 * 60


# ==========================================
# RATE LIMITER (per client IP, per process)
# ==========================================
class RateLimiter:
    """Sliding-window limiter. In-memory, so each gunicorn worker keeps its
    own counts — good enough to stop quota-burning scripts on one VPS."""

    def __init__(self):
        self._hits = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key, limit, window_seconds):
        """Record a hit; return True if allowed, False if over the limit."""
        now = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] > window_seconds:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            if len(self._hits) > 10000:  # drop idle keys so memory stays bounded
                for k in [k for k, v in self._hits.items() if not v]:
                    del self._hits[k]
            return True

    def reset(self):
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def client_ip():
    return request.remote_addr or 'unknown'


def rate_limit(name, rules):
    """Decorator. rules = [(limit, window_seconds), ...] — all must pass."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = client_ip()
            for limit, window in rules:
                if not limiter.hit(f'{name}:{window}:{ip}', limit, window):
                    return jsonify({'success': False,
                                    'error': 'Too many requests. Please wait a bit and try again.'}), 429
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ==========================================
# ADMIN AUTH
# ==========================================
def admin_configured():
    return bool(os.environ.get('SECRET_KEY')) and bool(os.environ.get('ADMIN_PASSWORD'))


def is_admin():
    if not admin_configured() or not session.get('is_admin'):
        return False
    return time.time() - session.get('login_at', 0) < SESSION_LIFETIME_SECONDS


def needs_admin(method, path):
    if path == '/admin/login':
        return False
    if path == '/admin' or path.startswith('/admin/'):
        return True
    if path.startswith('/api/') and method not in ('GET', 'HEAD', 'OPTIONS'):
        return (method, path) not in PUBLIC_API_WRITES
    return False


def guard_admin_routes():
    """before_request hook: block admin pages and API writes for non-admins."""
    if not needs_admin(request.method, request.path) or is_admin():
        return None
    if request.path.startswith('/api/') or request.method != 'GET':
        return jsonify({'success': False, 'error': 'Admin login required'}), 401
    return redirect(url_for('auth.login', next=request.path))


def _safe_next(target):
    # Only allow redirects back into the admin panel (no open redirect).
    if target and target.startswith('/admin') and not target.startswith('//'):
        return target
    return '/admin'


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def login():
    error = None
    if not admin_configured():
        error = 'Admin is locked: set SECRET_KEY and ADMIN_PASSWORD in backend-server/.env and restart.'
    elif request.method == 'POST':
        if not limiter.hit(f'login:{client_ip()}', 5, 15 * 60):
            error = 'Too many attempts. Try again in 15 minutes.'
        else:
            supplied = request.form.get('password', '').encode('utf-8')
            expected = os.environ['ADMIN_PASSWORD'].encode('utf-8')
            if hmac.compare_digest(supplied, expected):
                session.clear()
                session['is_admin'] = True
                session['login_at'] = time.time()
                session.permanent = True
                return redirect(_safe_next(request.args.get('next')))
            error = 'Wrong password.'
    status = 503 if not admin_configured() else (401 if error else 200)
    return render_template('login.html', error=error), status


@auth_bp.route('/admin/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


# ==========================================
# CACHE HEADERS
# ==========================================
REVALIDATE_EXTS = ('.html', '.js', '.css', '.json', '.webmanifest', '.xml', '.txt')


def cache_headers(response):
    path = request.path
    if path.startswith('/admin') or path.startswith('/api/'):
        response.headers['Cache-Control'] = 'no-store'
    elif path == '/' or path == '/sw.js' or path.endswith(REVALIDATE_EXTS):
        # Cheap 304s via ETag, but never serve a stale page/job list.
        response.headers['Cache-Control'] = 'no-cache'
    elif response.status_code == 200:
        response.headers['Cache-Control'] = 'public, max-age=604800'
    return response


def security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    if request.path.startswith('/admin'):
        response.headers.setdefault('X-Frame-Options', 'DENY')
    return response


def init_security(app):
    from datetime import timedelta

    secret = os.environ.get('SECRET_KEY')
    if secret:
        app.secret_key = secret
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',  # blocks cross-site form POSTs (CSRF)
        SESSION_COOKIE_SECURE=os.environ.get('COOKIE_SECURE', '1') != '0',
        PERMANENT_SESSION_LIFETIME=timedelta(seconds=SESSION_LIFETIME_SECONDS),
    )

    if os.environ.get('TRUST_PROXY') == '1':
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.register_blueprint(auth_bp)
    app.before_request(guard_admin_routes)
    app.after_request(cache_headers)
    app.after_request(security_headers)
    app.jinja_env.globals['admin_logged_in'] = is_admin
    app.jinja_env.filters['safe_url'] = safe_url


# ==========================================
# URL SANITISING (scraped job links etc.)
# ==========================================
def safe_url(value):
    """Return value if it is http(s) or a relative link; '' for javascript:/data:/etc."""
    value = (value or '').strip()
    probe = re.sub(r'[\x00-\x20]', '', value).lower()
    scheme = re.match(r'^([a-z][a-z0-9+.-]*):', probe)
    if scheme and scheme.group(1) not in ('http', 'https'):
        return ''
    return value
