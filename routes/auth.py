import os
import re as _re_mod
import requests
import urllib.parse
import secrets as _secrets
from flask import Blueprint, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from web_to_slide.database import create_user, get_user_by_email, get_user_by_id, update_last_login
from extensions import limiter, _log
from routes import login_required

auth_bp = Blueprint('auth', __name__)

# ── Google OAuth 설정 ────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI', 'https://tickdeck.site/api/auth/google/callback')

GOOGLE_AUTH_URL  = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


@auth_bp.route("/api/auth/google")
def auth_google():
    """Google OAuth 시작 — 동의 화면으로 리다이렉트"""
    # S1: OAuth CSRF 방지 — state 토큰 생성
    state = _secrets.token_urlsafe(32)
    session['oauth_state'] = state
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
        'state': state,
    }
    url = GOOGLE_AUTH_URL + '?' + urllib.parse.urlencode(params)
    return redirect(url)


@auth_bp.route("/api/auth/google/callback")
def auth_google_callback():
    """Google OAuth 콜백 — 코드 교환 → 사용자 정보 → 로그인/가입"""
    code = request.args.get('code')
    if not code:
        return redirect('/app?error=google_auth_failed')

    # S1: OAuth state 검증 — CSRF 방지
    state = request.args.get('state', '')
    expected = session.pop('oauth_state', None)
    if not state or state != expected:
        _log(f"[Google OAuth] state 불일치: expected={expected}, got={state}")
        return redirect('/app?error=google_auth_csrf')

    # 코드 → 토큰 교환
    token_resp = requests.post(GOOGLE_TOKEN_URL, data={
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }, timeout=10)

    if token_resp.status_code != 200:
        _log(f"[Google OAuth] 토큰 교환 실패: status={token_resp.status_code}")
        return redirect('/app?error=google_token_failed')

    access_token = token_resp.json().get('access_token')

    # 토큰 → 사용자 정보
    userinfo_resp = requests.get(GOOGLE_USERINFO_URL, headers={
        'Authorization': f'Bearer {access_token}'
    }, timeout=10)

    if userinfo_resp.status_code != 200:
        return redirect('/app?error=google_userinfo_failed')

    guser = userinfo_resp.json()
    email = guser.get('email', '').lower()
    name  = guser.get('name', '')

    if not email:
        return redirect('/app?error=google_no_email')

    # DB에서 사용자 조회 or 생성
    user = get_user_by_email(email)
    if not user:
        # 신규 가입 — 비밀번호 없이 (Google 전용)
        password_hash = generate_password_hash(os.urandom(32).hex())  # 랜덤 (직접 로그인 불가)
        user_id = create_user(email, password_hash, name or None)
    else:
        user_id = user['id']
        update_last_login(user_id)

    session['user_id'] = user_id
    return redirect('/app')


@auth_bp.route("/api/auth/signup", methods=["POST"])
@limiter.limit("5 per hour")
def auth_signup():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")
    name = (data.get("name") or "").strip()

    # 이메일 형식 검증
    if not email or not _re_mod.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
        return jsonify({"error": "올바른 이메일 형식이 아닙니다"}), 400

    # 비밀번호 최소 6자
    if len(password) < 6:
        return jsonify({"error": "비밀번호는 최소 6자 이상이어야 합니다"}), 400

    # 이메일 중복 체크
    if get_user_by_email(email):
        return jsonify({"error": "이미 가입된 이메일입니다"}), 409

    # 사용자 생성
    password_hash = generate_password_hash(password)
    user_id = create_user(email, password_hash, name or None)

    # 자동 로그인
    session['user_id'] = user_id

    return jsonify({
        "ok": True,
        "user": {"email": email, "name": name, "tokens": 2}
    })


@auth_bp.route("/api/auth/login", methods=["POST"])
@limiter.limit("10 per hour")
def auth_login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    user = get_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "이메일 또는 비밀번호가 올바르지 않습니다"}), 401

    # 세션 저장 + 마지막 로그인 갱신
    session['user_id'] = user['id']
    update_last_login(user['id'])

    return jsonify({
        "ok": True,
        "user": {"email": user['email'], "name": user['name'], "tokens": user['tokens']}
    })


@auth_bp.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    session.pop('user_id', None)
    return jsonify({"ok": True})


@auth_bp.route("/api/auth/me")
def auth_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"ok": False, "user": None})

    user = get_user_by_id(user_id)
    if not user:
        session.pop('user_id', None)
        return jsonify({"ok": False, "user": None})

    return jsonify({
        "ok": True,
        "user": {"email": user['email'], "name": user['name'], "tokens": user['tokens']}
    })
