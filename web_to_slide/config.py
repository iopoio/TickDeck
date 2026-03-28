"""
config.py — 환경 변수 로드, API 클라이언트 초기화, 전역 상수
"""

import logging
import os
import sys

# Windows cp949 환경에서 이모지·유니코드 출력 오류 방지
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # 인코딩 재설정 불가 — 무시
if sys.platform == 'win32' and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # 인코딩 재설정 불가 — 무시

# ── 로거 설정 ──────────────────────────────────────────────────────────────────
logger = logging.getLogger("web_to_slide")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(_handler)

from dotenv import load_dotenv

try:
    from PIL import Image as _PILImage  # noqa: F401
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    logger.warning("Pillow 미설치 — 로고 배경 제거 비활성화. `pip install Pillow` 권장")

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def validate_config():
    """필수 API 키 존재 확인. 누락 시 ValueError 발생."""
    if not GEMINI_API_KEY:
        raise ValueError("환경 변수 누락: GEMINI_API_KEY")


from google import genai

_client = genai.Client(api_key=GEMINI_API_KEY)

# ── Timeout 상수 ─────────────────────────────────────────────────────────────
SCRAPER_TIMEOUT = 15000      # Playwright 기본 timeout (ms)
SCRAPER_TIMEOUT_LONG = 20000 # 링크/이미지 수집 timeout (ms)
LOGO_TIMEOUT = 25000         # 로고 탐색 timeout (ms)

# ── 캐시 유틸 ────────────────────────────────────────────────────────────────
import re as _re_mod

def clear_slide_cache(company_name: str, progress_fn=None):
    """슬라이드 캐시 파일 삭제 (app.py / celery_app.py 공용)"""
    import os
    _slug = _re_mod.sub(r'[^\w]', '', (company_name or '').lower())[:20]
    suffixes = ['_text.json', '_img.json', '.json', '_en_text.json', '_en_img.json']
    for sfx in suffixes:
        _cf = f"slide_{_slug}{sfx}"
        try:
            if os.path.exists(_cf):
                os.remove(_cf)
                if progress_fn:
                    progress_fn(f"  → 캐시 삭제: {_cf}")
        except Exception:
            pass

# ── HTTP 헤더 ────────────────────────────────────────────────────────────────

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/',
}

# Googlebot UA — 쿠키 월 우회 폴백 (많은 사이트가 구글봇에 SSR 전체 제공)
_GOOGLEBOT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
}
