"""
Dashboard login.

The dashboard exposes ~40 routes on 0.0.0.0:5050 including /api/place_trade,
/api/kill_switch, /api/control and /api/risk_config. It had no auth of any
kind, which is why the service was left disabled.

The guard here is a single before_request hook rather than a decorator on each
route: 40 decorators is 40 chances to forget one, and any route added later
would default to public. This defaults to protected instead -- a new route is
covered the moment it is written, and opening one up takes a deliberate entry
in PUBLIC_ENDPOINTS.

Setup (both values live in config/credentials.env):

    cd /var/www/tradekaro/Trading_AI_Project
    venv/bin/python scripts/set_dashboard_password.py

Without DASH_PASSWORD_HASH set, every request returns 503. Failing closed
matters more than convenience here -- a dashboard that quietly serves
/api/place_trade to the open internet because a config value was missing is
the exact failure this module exists to prevent.
"""
import os
import time
from collections import defaultdict

from flask import (jsonify, redirect, render_template, request, session,
                   url_for)
from werkzeug.security import check_password_hash

# Endpoint names reachable without a session. Everything else needs one.
PUBLIC_ENDPOINTS = {'auth_login', 'auth_logout', 'static', 'favicon'}

# Brute force throttle. In-process and per-IP: the dashboard is a single
# eventlet worker, so a dict is enough -- no Redis for one user.
_MAX_ATTEMPTS = 8
_LOCKOUT_SECONDS = 300
_attempts = defaultdict(list)


def _client_ip():
    # Only trust X-Forwarded-For when a proxy is actually in front, otherwise
    # anyone can spoof the header and dodge the lockout entirely.
    if os.getenv('DASH_BEHIND_PROXY', '').lower() in ('1', 'true', 'yes'):
        fwd = request.headers.get('X-Forwarded-For', '')
        if fwd:
            return fwd.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _locked_out(ip):
    cutoff = time.time() - _LOCKOUT_SECONDS
    _attempts[ip] = [t for t in _attempts[ip] if t > cutoff]
    return len(_attempts[ip]) >= _MAX_ATTEMPTS


def _record_failure(ip):
    _attempts[ip].append(time.time())


def _wants_json():
    return (request.path.startswith('/api/')
            or request.accept_mimetypes.best == 'application/json')


def init_auth(app):
    """Attach the login routes and the global guard to `app`."""

    password_hash = os.getenv('DASH_PASSWORD_HASH', '').strip()

    secret = os.getenv('FLASK_SECRET_KEY', '').strip()
    if secret:
        app.config['SECRET_KEY'] = secret
    # else: app.py's own default stays, and the 503 below keeps the dashboard
    # shut anyway -- set_dashboard_password.py writes both values together.

    @app.before_request
    def _require_login():
        if request.endpoint in PUBLIC_ENDPOINTS:
            return None

        if not password_hash:
            msg = ('Dashboard password is not configured. Run '
                   'scripts/set_dashboard_password.py, then restart '
                   'tradekaro-web.')
            if _wants_json():
                return jsonify({'error': msg}), 503
            return msg, 503

        if session.get('logged_in') is True:
            return None

        if _wants_json():
            return jsonify({'error': 'Login required'}), 401
        return redirect(url_for('auth_login', next=request.path))

    @app.route('/login', methods=['GET', 'POST'], endpoint='auth_login')
    def login():
        if not password_hash:
            return ('Dashboard password is not configured. Run '
                    'scripts/set_dashboard_password.py, then restart '
                    'tradekaro-web.'), 503

        ip = _client_ip()
        error = None

        if request.method == 'POST':
            if _locked_out(ip):
                error = 'Too many attempts. Try again in 5 minutes.'
            elif check_password_hash(password_hash,
                                     request.form.get('password', '')):
                # New session id on login so a cookie captured beforehand
                # cannot be reused as an authenticated one.
                session.clear()
                session['logged_in'] = True
                session.permanent = False
                _attempts.pop(ip, None)

                # Only follow `next` if it is a path on this site -- an
                # absolute URL here would make the login page an open
                # redirect.
                nxt = request.args.get('next', '')
                if nxt.startswith('/') and not nxt.startswith('//'):
                    return redirect(nxt)
                return redirect(url_for('index'))
            else:
                _record_failure(ip)
                error = 'Wrong password.'

        return render_template('login.html', error=error), (200 if not error else 401)

    @app.route('/logout', endpoint='auth_logout')
    def logout():
        session.clear()
        return redirect(url_for('auth_login'))

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'same-origin')
        return response

    return app


def socket_is_authenticated():
    """For SocketIO handlers, which bypass before_request entirely."""
    return session.get('logged_in') is True
