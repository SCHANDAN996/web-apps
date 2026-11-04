"""Google OAuth login for Study Station's private Flask admin area."""
import os
import secrets
from datetime import timedelta
from urllib.parse import urlencode

import requests
from flask import Blueprint, abort, redirect, request, session, url_for
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

admin_auth_bp = Blueprint("admin_auth", __name__, url_prefix="/auth")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


def admin_authorized():
    return session.get("admin_email") == os.environ.get(
        "ADMIN_EMAIL", "all.chandansingh@gmail.com"
    ).strip().lower()


@admin_auth_bp.route("/login")
def login():
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    secret = os.environ.get("GOOGLE_CLIENT_SECRET")
    callback = os.environ.get("GOOGLE_REDIRECT_URI")
    if not all((client_id, secret, callback)):
        abort(503, description="Google login is not configured on the server.")
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    params = {
        "client_id": client_id, "redirect_uri": callback,
        "response_type": "code", "scope": "openid email profile",
        "state": state, "prompt": "select_account"
    }
    return redirect(GOOGLE_AUTH_URL + "?" + urlencode(params))


@admin_auth_bp.route("/callback")
def callback():
    state = session.pop("oauth_state", None)
    if not state or not secrets.compare_digest(state, request.args.get("state", "")):
        abort(400, description="Invalid OAuth state.")
    code = request.args.get("code")
    if not code:
        abort(400, description="Google authorization declined.")
    try:
        response = requests.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": os.environ["GOOGLE_REDIRECT_URI"],
            "grant_type": "authorization_code",
        }, timeout=15)
        response.raise_for_status()
        token = response.json()["id_token"]
        claims = id_token.verify_oauth2_token(
            token, google_requests.Request(), os.environ["GOOGLE_CLIENT_ID"]
        )
    except (requests.RequestException, ValueError, KeyError) as exc:
        abort(401, description="Could not verify Google login.")
    expected = os.environ.get("ADMIN_EMAIL", "all.chandansingh@gmail.com").strip().lower()
    if claims.get("email_verified") is not True or claims.get("email", "").lower() != expected:
        session.clear()
        abort(403, description="This account is not authorized for admin access.")
    session.clear()
    session.permanent = True
    session["admin_email"] = expected
    session["admin_sub"] = claims["sub"]
    return redirect(url_for("admin_dashboard"))


@admin_auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/")
