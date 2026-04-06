"""
app.py — WebToSlide 로컬 웹 서버
localhost:5000 에서 슬라이드 생성 UI 제공
"""
import os
import sys

# .env 파일 로드 (SECRET_KEY, GEMINI_API_KEY 등)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 없으면 os.environ만 사용

# Windows cp949 환경에서 이모지·유니코드 출력 오류 방지
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

# 로그 파일 — OneDrive 외부 경로로 저장 (한글 경로 잠금 회피)
_LOG_PATH_CANDIDATES = [
    os.path.join(os.path.expanduser('~'), 'webtoslide_server.log'), 
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log'), 
]
_LOG_PATH = _LOG_PATH_CANDIDATES[0]

def _log(msg: str):
    """파일 + stdout에 기록"""
    line = msg + '\n'
    try:
        print(msg, flush=True)
    except Exception:
        pass
    for _path in _LOG_PATH_CANDIDATES:
        try:
            with open(_path, 'a', encoding='utf-8') as _f:
                _f.write(line)
            break 
        except Exception:
            continue

from flask import Flask, request

# S4: Rate Limiting
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    _has_limiter = True
except ImportError:
    _has_limiter = False

from pathlib import Path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from web_to_slide.database import init_app as init_db_app, init_db

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# S2: SECRET_KEY — 프로덕션에서는 환경변수 필수
_secret = os.environ.get('SECRET_KEY', '')
if not _secret:
    import warnings
    _secret = 'tickdeck-dev-ONLY-change-in-production'
    warnings.warn("SECRET_KEY 환경변수가 설정되지 않았습니다. 프로덕션에서는 반드시 설정하세요!", stacklevel=1)
app.config['SECRET_KEY'] = _secret

# 세션 쿠키 보안
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('USE_CELERY'):
    app.config['SESSION_COOKIE_SECURE'] = True

app.jinja_env.auto_reload = True

# S4: Rate Limiter 초기화 (Redis 사용 — Gunicorn 멀티 워커에서도 공유)
import extensions
_limiter_storage = os.environ.get('REDIS_URL', 'memory://')
if _has_limiter:
    # extensions.py에 기생성된 limiter 객체에 설정을 입히고 앱에 등록
    app.config.setdefault("RATELIMIT_STORAGE_URI", _limiter_storage)
    app.config.setdefault("RATELIMIT_DEFAULT_LIMITS", ["200 per hour"])
    extensions.limiter.init_app(app)
    limiter = extensions.limiter
else:
    class _NoopLimiter:
        def limit(self, *a, **kw):
            def decorator(f): return f
            return decorator
    limiter = _NoopLimiter()
    extensions.limiter = limiter
# 보안 헤더 (OWASP 권장)
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# 세션 만료 (30일)
app.config['PERMANENT_SESSION_LIFETIME'] = 30 * 24 * 60 * 60  # 30 days

# DB 초기화
init_db_app(app)
with app.app_context():
    init_db()

# ── Celery/Redis 또는 In-Memory 모드 ──────────────────────────────────────
USE_CELERY = os.environ.get('USE_CELERY', '').lower() in ('1', 'true', 'yes')

if USE_CELERY:
    import redis as _redis_mod
    from celery_app import REDIS_URL
    _redis_client = _redis_mod.Redis.from_url(REDIS_URL, decode_responses=True)
    _log("[MODE] Celery + Redis 모드")
else:
    _redis_client = None
    _log("[MODE] In-Memory 모드 (단일 워커)")

ADMIN_EMAILS = set(
    e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()
)
app.config['ADMIN_EMAILS'] = ADMIN_EMAILS

# ── Extensions 파일로 모듈 상태 전송 ───────────────────────────────────────
import extensions
extensions.limiter = limiter
extensions._log = _log
extensions.redis_client = _redis_client
extensions.USE_CELERY = USE_CELERY

# ── Blueprint 등록 ───────────────────────────────────────────────────────────
from routes.auth import auth_bp
from routes.api import api_bp
from routes.admin import admin_bp
from routes.pages import pages_bp

app.register_blueprint(auth_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(pages_bp)

if __name__ == "__main__":
    print("=" * 50)
    print("  TickDeck 서버 시작")
    print("  http://localhost:5000")
    print(f"  로그 파일: {_LOG_PATH}")
    print("=" * 50)
    _log("=== WebToSlide 서버 시작 ===")
    app.run(host='0.0.0.0', debug=False, port=5000, threaded=True)
