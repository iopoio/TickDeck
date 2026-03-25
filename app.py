"""
app.py — WebToSlide 로컬 웹 서버
localhost:5000 에서 슬라이드 생성 UI 제공
"""
import json
import os
import requests
import subprocess
import sys
import tempfile
import threading
import time
import uuid

# .env 파일 로드 (SECRET_KEY, GEMINI_API_KEY 등)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 없으면 os.environ만 사용
from pathlib import Path

# Windows cp949 환경에서 이모지·유니코드 출력 오류 방지
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

# 로그 파일 — OneDrive 외부 경로로 저장 (한글 경로 잠금 회피)
_LOG_PATH_CANDIDATES = [
    os.path.join(os.path.expanduser('~'), 'webtoslide_server.log'),  # C:\Users\chaej\webtoslide_server.log
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log'),  # 원래 경로 (fallback)
]
_LOG_PATH = _LOG_PATH_CANDIDATES[0]

def _log(msg: str):
    """파일 + stdout에 기록"""
    line = msg + '\n'
    # 터미널 출력 (print → stdout, 가장 안정적)
    try:
        print(msg, flush=True)
    except Exception:
        pass
    # 파일 기록
    for _path in _LOG_PATH_CANDIDATES:
        try:
            with open(_path, 'a', encoding='utf-8') as _f:
                _f.write(line)
            break  # 첫 번째 성공하면 중단
        except Exception:
            continue

from flask import Flask, jsonify, make_response, render_template, request, Response, send_file, send_from_directory

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

import re as _re_mod
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

from web_to_slide.pipeline import run_pipeline
from web_to_slide.database import (
    init_app as init_db_app, init_db,
    create_user, get_user_by_email, get_user_by_id,
    update_last_login, check_and_deduct_token, refund_token,
    create_generation, complete_generation, add_tokens,
)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tickdeck-dev-secret-change-in-production')
app.jinja_env.auto_reload = True

# DB 초기화
init_db_app(app)
with app.app_context():
    init_db()

# job_id → { status, lines, result, error }
JOBS: dict[str, dict] = {}


# ── 인증 데코레이터 ──────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import session
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Google OAuth 설정 ────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI  = os.environ.get('GOOGLE_REDIRECT_URI', 'https://tickdeck.site/api/auth/google/callback')

GOOGLE_AUTH_URL  = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'


# ── Google OAuth 라우트 ──────────────────────────────────────────────────────
@app.route("/api/auth/google")
def auth_google():
    """Google OAuth 시작 — 동의 화면으로 리다이렉트"""
    import urllib.parse
    params = {
        'client_id': GOOGLE_CLIENT_ID,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'email profile',
        'access_type': 'offline',
        'prompt': 'select_account',
    }
    url = GOOGLE_AUTH_URL + '?' + urllib.parse.urlencode(params)
    from flask import redirect
    return redirect(url)


@app.route("/api/auth/google/callback")
def auth_google_callback():
    """Google OAuth 콜백 — 코드 교환 → 사용자 정보 → 로그인/가입"""
    from flask import session, redirect
    code = request.args.get('code')
    if not code:
        return redirect('/app?error=google_auth_failed')

    # 코드 → 토큰 교환
    token_resp = requests.post(GOOGLE_TOKEN_URL, data={
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code',
    }, timeout=10)

    if token_resp.status_code != 200:
        _log(f"[Google OAuth] 토큰 교환 실패: {token_resp.text}")
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


# ── 인증 API ─────────────────────────────────────────────────────────────────
@app.route("/api/auth/signup", methods=["POST"])
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
    from flask import session
    session['user_id'] = user_id

    return jsonify({
        "ok": True,
        "user": {"email": email, "name": name, "tokens": 2}
    })


@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(force=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "")

    user = get_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "이메일 또는 비밀번호가 올바르지 않습니다"}), 401

    # 세션 저장 + 마지막 로그인 갱신
    from flask import session
    session['user_id'] = user['id']
    update_last_login(user['id'])

    return jsonify({
        "ok": True,
        "user": {"email": user['email'], "name": user['name'], "tokens": user['tokens']}
    })


@app.route("/api/auth/logout", methods=["POST"])
def auth_logout():
    from flask import session
    session.pop('user_id', None)
    return jsonify({"ok": True})


@app.route("/api/token/free-charge", methods=["POST"])
@login_required
def free_charge():
    """무료 토큰 2개 충전 (테스트/이벤트용 — 나중에 설문 연동)"""
    from flask import session
    user_id = session['user_id']
    add_tokens(user_id, 2, 'free_charge')
    user = get_user_by_id(user_id)
    return jsonify({"ok": True, "tokens": user['tokens']})


@app.route("/api/auth/me")
def auth_me():
    from flask import session
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


# ── 파이프라인 실행 ─────────────────────────────────────────────────────────
def _run(job_id: str, url: str, company: str,
         narrative_type: str = "auto", mood: str = "professional", purpose: str = "brand",
         brand_color: str = ""):
    job = JOBS[job_id]

    def on_progress(line: str):
        if line.strip():
            job["lines"].append(line)
            _log(line)

    import os, re as _re
    def _clear_cache(co):
        _slug = _re.sub(r'[^\w]', '', (co or '').lower())[:20]
        for _cf in [f"slide_{_slug}_text.json", f"slide_{_slug}_img.json", f"slide_{_slug}.json"]:
            try:
                if os.path.exists(_cf):
                    os.remove(_cf)
                    on_progress(f"  → 캐시 삭제: {_cf}")
            except Exception:
                pass

    gen_id = job.get("gen_id")
    user_id = job.get("user_id")

    try:
        if gen_id:
            with app.app_context():
                complete_generation(gen_id, 'processing')
        result = run_pipeline(url, company or None, progress_fn=on_progress,
                              narrative_type=narrative_type, mood=mood, purpose=purpose,
                              brand_color=brand_color)
        job["result"] = result
        job["status"] = "done"
        if gen_id:
            with app.app_context():
                complete_generation(gen_id, 'completed')
    except Exception as e:
        import traceback as _tb
        err_str = str(e)
        for _tl in _tb.format_exc().splitlines():
            on_progress(f"  TB| {_tl}")
        on_progress(f"  ⚠ 오류 발생: {err_str}")
        _slug = _re.sub(r'[^\w]', '', (company or url.split('//')[-1].split('/')[0].replace('.', '')).lower())[:20]
        _clear_cache(_slug)
        on_progress("  → 캐시 삭제 후 재시도 중...")
        try:
            result = run_pipeline(url, company or None, progress_fn=on_progress,
                                  narrative_type=narrative_type, mood=mood, purpose=purpose,
                                  brand_color=brand_color)
            job["result"] = result
            job["status"] = "done"
            if gen_id:
                with app.app_context():
                    complete_generation(gen_id, 'completed')
        except Exception as e2:
            import traceback as _tb2
            _log("=== TRACEBACK2 ===\n" + _tb2.format_exc() + "=================")
            job["status"] = "error"
            job["error"] = str(e2)
            # 실패 시 토큰 환불
            if user_id and gen_id:
                with app.app_context():
                    refund_token(user_id, gen_id)
                    complete_generation(gen_id, 'failed')
                on_progress("  → 토큰 환불 완료")


# ── 라우트 ──────────────────────────────────────────────────────────────────
@app.route("/")
def landing():
    """랜딩 페이지 (서비스 소개)"""
    return render_template("landing.html")


@app.route("/app")
def app_page():
    """앱 페이지 (슬라이드 생성)"""
    resp = make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.route("/generate", methods=["POST"])
@login_required
def generate():
    from flask import session
    user_id = session['user_id']
    data    = request.get_json(force=True)
    url            = (data.get("url") or "").strip()
    company        = (data.get("company") or "").strip()
    narrative_type = (data.get("narrative_type") or "auto").strip()
    mood           = (data.get("mood") or "professional").strip()
    purpose        = (data.get("purpose") or "auto").strip()
    brand_color    = (data.get("brand_color") or "").strip()

    if not url:
        return jsonify({"error": "URL을 입력하세요."}), 400

    if not url.startswith("http"):
        url = "https://" + url

    # 토큰 차감 (먼저 차감 → 실패 시 환불)
    remaining = check_and_deduct_token(user_id)
    if remaining is None:
        return jsonify({"error": "토큰이 부족합니다. 토큰을 충전해 주세요."}), 403

    # generation 기록
    gen_id = create_generation(user_id, url, company or None, purpose)

    # token_history 기록
    from web_to_slide.database import get_db
    db = get_db()
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason, generation_id) VALUES (?, -1, 'generate', ?)",
        (user_id, gen_id)
    )
    db.commit()

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running", "lines": [], "result": None, "error": None,
                    "user_id": user_id, "gen_id": gen_id}

    t = threading.Thread(target=_run, args=(job_id, url, company, narrative_type, mood, purpose, brand_color), daemon=True)
    t.start()

    return jsonify({"job_id": job_id, "remaining_tokens": remaining})


@app.route("/stream/<job_id>")
def stream(job_id: str):
    """Server-Sent Events — 실시간 로그 + 완료 이벤트"""
    def generate():
        sent = 0
        while True:
            job = JOBS.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error': '존재하지 않는 작업입니다.'})}\n\n"
                break

            while sent < len(job["lines"]):
                yield f"data: {json.dumps({'line': job['lines'][sent]})}\n\n"
                sent += 1

            if job["status"] == "done":
                meta = job["result"].get("meta", {}) if job["result"] else {}
                slide_count = len(job["result"].get("slides", [])) if job["result"] else 0
                yield f"data: {json.dumps({'status': 'done', 'meta': meta, 'slide_count': slide_count})}\n\n"
                break
            elif job["status"] == "error":
                yield f"data: {json.dumps({'status': 'error', 'error': job.get('error', '')})}\n\n"
                break

            time.sleep(0.4)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/clear-cache", methods=["POST"])
def clear_cache():
    """URL에 해당하는 캐시 JSON 파일 삭제"""
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    company = (data.get("company") or "").strip()

    # company 이름이 없으면 URL에서 추출
    if not company and url:
        host = url.split("//")[-1].split("/")[0].replace("www.", "")
        company = host.split(".")[0]

    if not company:
        return jsonify({"ok": False, "msg": "URL 또는 company 이름이 필요합니다."}), 400

    deleted = []
    for suffix in ["_text.json", "_img.json", ".json"]:
        cf = BASE_DIR / f"slide_{company}{suffix}"
        if cf.exists():
            cf.unlink()
            deleted.append(cf.name)
    if deleted:
        return jsonify({"ok": True, "files": deleted})
    return jsonify({"ok": False, "msg": f"캐시 없음: slide_{company}_*.json"})


@app.route("/result/<job_id>")
def result(job_id: str):
    """완료된 작업의 JSON 결과 반환 (슬라이드 데이터 전체)"""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "존재하지 않는 작업입니다."}), 404
    if job["status"] != "done":
        return jsonify({"error": "작업이 아직 완료되지 않았습니다.", "status": job["status"]}), 202
    return jsonify(job["result"])


@app.route("/static/<path:filename>")
def serve_static(filename):
    """static 폴더 파일 서빙 (stitch_templates.json 등)"""
    static_dir = BASE_DIR / "static"
    return send_from_directory(static_dir, filename)


@app.route("/api/convert-pdf", methods=["POST"])
def convert_to_pdf():
    """PPTX 파일을 받아서 LibreOffice로 PDF 변환 후 반환"""
    if 'file' not in request.files:
        return jsonify({'error': 'PPTX 파일이 필요합니다'}), 400

    pptx_file = request.files['file']
    dl_name = request.form.get('filename', 'slides')

    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path = os.path.join(tmpdir, 'slides.pptx')
        pptx_file.save(pptx_path)

        try:
            result = subprocess.run(
                ['libreoffice', '--headless', '--convert-to', 'pdf',
                 '--outdir', tmpdir, pptx_path],
                capture_output=True, text=True, timeout=60
            )
        except FileNotFoundError:
            return jsonify({'error': 'LibreOffice가 설치되어 있지 않습니다. PPTX를 먼저 다운로드해 주세요.'}), 500
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'PDF 변환 시간이 초과되었습니다.'}), 500

        if result.returncode != 0:
            return jsonify({'error': 'PDF 변환 실패', 'detail': result.stderr}), 500

        pdf_path = os.path.join(tmpdir, 'slides.pdf')
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF 파일이 생성되지 않았습니다.'}), 500

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=dl_name + '.pdf'
        )


if __name__ == "__main__":
    print("=" * 50)
    print("  TickDeck 서버 시작")
    print("  http://localhost:5000")
    print(f"  로그 파일: {_LOG_PATH}")
    print("=" * 50)
    _log("=== WebToSlide 서버 시작 ===")
    app.run(host='0.0.0.0', debug=False, port=5000, threaded=True)
