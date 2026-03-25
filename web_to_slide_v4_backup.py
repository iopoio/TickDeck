"""
Web to Slide v4 — JSON Pipeline
크롤링 → Gemini JSON → Imagen 배경 이미지 → Python 템플릿 → PDF

변경사항 (v4):
- Imagen 429 재시도: 지수 백오프 (10s→20s→40s), 호출 간격 4초 보장
- CSS 컬러 추출: 빈도 기반 제거, CSS 변수 전용 + WP/Elementor 노이즈 제거
- 로고: PIL 배경 제거(흰/검 투명화), Playwright 폴백
- 푸터 이메일/전화 자동 스크래핑 → contact 슬라이드 주입
- 서비스 슬라이드 텍스트 항상 좌측 고정
- 방법론 카드에 body 설명 텍스트 추가
"""

import requests
from bs4 import BeautifulSoup
from google import genai
from google.genai import types as genai_types
import re
import os
import sys

# Windows cp949 환경에서 이모지·유니코드 출력 오류 방지
if sys.platform == 'win32' and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.platform == 'win32' and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import json
import base64
import time
import io
import collections
from urllib.parse import urlparse, unquote
import json
import base64
import time
import io
from collections import Counter
from dotenv import load_dotenv

try:
    from PIL import Image as _PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("⚠️  Pillow 미설치 — 로고 배경 제거 비활성화. `pip install Pillow` 권장")

load_dotenv()
_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

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


def extract_dominant_color(img_bytes: bytes) -> str:
    """PIL로 이미지에서 가장 선명한 브랜드 컬러(비중립색) 추출 → '#RRGGBB' or ''
    - 16색 양자화로 세밀하게 분리 + vibrancy 0.20 이상만 허용
    - 흰/검 배경 픽셀을 먼저 제거 후 양자화 (배경색 오염 방지)
    """
    if not HAS_PIL or not img_bytes:
        return ''
    try:
        img = _PILImage.open(io.BytesIO(img_bytes)).convert('RGBA').resize((120, 120))
        # 투명 픽셀·흰 배경·검 배경을 제거한 픽셀만 남긴 RGB 이미지 생성
        pixels_rgb = []
        for r, g, b, a in img.getdata():
            if a < 100:
                continue  # 투명 픽셀 제외
            brightness = (r * 299 + g * 587 + b * 114) // 1000
            if brightness > 240 or brightness < 15:
                continue  # 흰/검 배경 제외
            pixels_rgb.append((r, g, b))
        if len(pixels_rgb) < 50:  # 유효 픽셀 부족 → 원본 전체 사용
            img_rgb = img.convert('RGB')
        else:
            img_rgb = _PILImage.new('RGB', (len(pixels_rgb), 1))
            img_rgb.putdata(pixels_rgb)

        quantized = img_rgb.quantize(colors=16, method=2)
        palette = quantized.getpalette()[:16 * 3]
        counts = [0] * 16
        for p in quantized.getdata():
            counts[p] += 1
        # vibrancy 기준으로 가장 선명한 색 선택 (빈도 상위 8개 중)
        top = sorted(enumerate(counts), key=lambda x: -x[1])[:8]
        candidates = []
        for idx, cnt in top:
            r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
            hex_c = f'#{r:02x}{g:02x}{b:02x}'.upper()
            v = _color_vibrancy(hex_c)
            if v >= 0.20:
                candidates.append((hex_c, v, cnt))
        if candidates:
            # vibrancy와 빈도를 함께 고려해 최적 색 선택
            max_cnt = max(c[2] for c in candidates)
            return max(candidates, key=lambda x: x[1] * 0.7 + (x[2] / max_cnt) * 0.3)[0]
    except Exception:
        pass
    return ''


def _extract_svg_colors(svg_b64: str) -> list:
    """SVG base64에서 fill/stroke/stop-color 색 추출 → vibrancy 높은 순 리스트"""
    try:
        svg_text = base64.b64decode(svg_b64).decode('utf-8', errors='ignore')
        found = re.findall(
            r'(?:fill|stroke|stop-color)\s*[=:]\s*["\']?\s*(#[0-9a-fA-F]{3,6})\b',
            svg_text, re.I
        )
        # 3자리 헥스 → 6자리 변환
        expanded = []
        for c in found:
            c = c.lstrip('#')
            if len(c) == 3:
                c = ''.join(ch * 2 for ch in c)
            if len(c) == 6:
                expanded.append('#' + c.upper())
        # 중복 제거 + vibrancy 필터 + 정렬
        seen = set()
        result = []
        for c in expanded:
            if c not in seen and _color_vibrancy(c) >= 0.15:
                seen.add(c)
                result.append(c)
        return sorted(result, key=_color_vibrancy, reverse=True)
    except Exception:
        return []

def _extract_elementor_colors(css_text: str) -> dict:
    """CSS 글로벌 컬러 변수에서 accent(브랜드 컬러)와 vibrant 목록 추출.
    지원: Elementor(--e-global-color-*), WordPress(--wp--preset--color--*), 일반 테마 변수
    교차검증: CSS 변수 정의 + 실제 사용(var()) 양쪽에 등장하는 색 → 더 높은 신뢰도
    반환: {'accent': '#RRGGBB', 'all_vibrant': ['#...', ...], 'cross_validated': ['#...']}
    """
    result = {'accent': '', 'all_vibrant': [], 'cross_validated': []}

    # ① 모든 CSS 변수 정의 추출 (varname → hex)
    var_defs = {}
    for m in re.finditer(r'(--[\w-]+)\s*:\s*#([0-9a-fA-F]{6})\b', css_text, re.I):
        var_defs[m.group(1).lower()] = '#' + m.group(2).upper()

    # ② 실제 background/fill 컨텍스트에서 var() 사용 카운트
    used_in_bg = set()
    for m in re.finditer(
        r'(?:background(?:-color)?|fill|stop-color)\s*:\s*var\((--[\w-]+)\)',
        css_text, re.I
    ):
        vn = m.group(1).lower()
        if vn in var_defs:
            used_in_bg.add(var_defs[vn])

    # ③ accent 우선순위: Elementor accent → WP 고대비 → 일반 accent 키 순
    # Elementor 글로벌 accent
    for key in ['--e-global-color-accent']:
        if key in var_defs and _color_vibrancy(var_defs[key]) >= 0.20:
            result['accent'] = var_defs[key]
            break
    # WordPress 프리셋 컬러 중 배경에 실제 사용된 vibrant 컬러
    if not result['accent']:
        wp_colors = {k: v for k, v in var_defs.items()
                     if k.startswith('--wp--preset--color--') and _color_vibrancy(v) >= 0.20}
        for v in wp_colors.values():
            if v in used_in_bg:
                result['accent'] = v
                break
        if not result['accent'] and wp_colors:
            # 사용 여부 무관, 가장 vibrant한 WP 색
            result['accent'] = max(wp_colors.values(), key=_color_vibrancy)
    # 일반 테마 변수 폴백
    if not result['accent']:
        for key in ['--color-accent', '--accent-color', '--brand-color',
                    '--primary-color', '--theme-color', '--link-color']:
            if key in var_defs and _color_vibrancy(var_defs[key]) >= 0.20:
                result['accent'] = var_defs[key]
                break

    # ④ 교차검증 목록: 정의 + 실제 background 사용 양쪽에 나타나는 vibrant 색
    for v in var_defs.values():
        if _color_vibrancy(v) >= 0.20 and v in used_in_bg:
            if v not in result['cross_validated']:
                result['cross_validated'].append(v)

    # ⑤ all_vibrant: 모든 vibrant CSS 변수 색 (near-black/white 제외)
    seen = set()
    for v in var_defs.values():
        if _color_vibrancy(v) >= 0.20 and v not in seen:
            seen.add(v)
            result['all_vibrant'].append(v)

    return result


def _count_css_color_usage(css_text: str) -> tuple:
    """CSS 전체에서 색상별 가중 사용 빈도 집계
    - vibrant(vibrancy>=0.12): background/fill weight 3, color/border weight 1 → 상위 5개 반환
    - 전체(vibrancy 무관): 가중치 없이 ALL 집계 → dark_total(luma<0.20), light_total(luma>0.80) 반환
    """
    from collections import defaultdict
    scores     = defaultdict(int)  # vibrant 가중 집계
    raw_scores = defaultdict(int)  # 전체 무가중 집계 (흰검 지배형 감지용)

    def _luma_h(hx):
        h = hx.lstrip('#')
        try: r, g, b = int(h[:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
        except: return 1.0
        return 0.2126*r + 0.7152*g + 0.0722*b

    # ① 직접 hex 사용 감지
    for pat, w in [
        (r'(?:background(?:-color)?|fill|stop-color)\s*:\s*#([0-9a-fA-F]{6})\b', 3),
        (r'(?:^|;|\{)\s*(?:color|border(?:-[\w]+)?-color|stroke)\s*:\s*#([0-9a-fA-F]{6})\b', 1),
    ]:
        for m in re.finditer(pat, css_text, re.I | re.M):
            c = '#' + m.group(1).upper()
            raw_scores[c] += 1          # 모든 색, 가중치 없음
            if _color_vibrancy(c) >= 0.12:
                scores[c] += w

    # ② CSS 변수(Elementor 등) 지원: 변수 정의 추출 후 var() 참조 횟수 × 가중치
    var_defs = {}  # varname → '#RRGGBB'
    for m in re.finditer(r'(--[\w-]+)\s*:\s*#([0-9a-fA-F]{6})\b', css_text, re.I):
        var_name = m.group(1).lower()
        c = '#' + m.group(2).upper()
        if _color_vibrancy(c) >= 0.12:
            var_defs[var_name] = c

    if var_defs:
        # background/fill 컨텍스트에서 var() 참조 카운트 (weight 3)
        for m in re.finditer(
            r'(?:background(?:-color)?|fill|stop-color)\s*:\s*var\((--[\w-]+)\)',
            css_text, re.I
        ):
            vn = m.group(1).lower()
            if vn in var_defs:
                scores[var_defs[vn]] += 3
        # color/border 컨텍스트에서 var() 참조 카운트 (weight 1)
        for m in re.finditer(
            r'(?:^|;|\{)\s*(?:color|border(?:-[\w]+)?-color|stroke)\s*:\s*var\((--[\w-]+)\)',
            css_text, re.I | re.M
        ):
            vn = m.group(1).lower()
            if vn in var_defs:
                scores[var_defs[vn]] += 1

    # dark/light 집계 (무가중 raw_scores 기반)
    dark_total  = sum(v for c, v in raw_scores.items() if _luma_h(c) < 0.20)
    light_total = sum(v for c, v in raw_scores.items() if _luma_h(c) > 0.80)

    ranked = sorted(scores.items(), key=lambda kv: kv[1] * _color_vibrancy(kv[0]), reverse=True)
    top = [c for c, _ in ranked if scores[c] >= 3][:5]
    return top, {c: scores[c] for c in top}, dark_total, light_total


def _download_og_image_color(soup, base_url: str) -> str:
    """OG 이미지 또는 첫 번째 히어로 이미지 다운로드 → dominant color hex or ''
    - og:image 우선, 없으면 hero/banner 첫 번째 <img>
    - 이미지 다운로드 후 extract_dominant_color로 픽셀 분석
    """
    candidates = []
    og = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'og:image'})
    if og and og.get('content'):
        candidates.append(og['content'])
    # hero/banner 영역 이미지
    for sel_id in [r'hero|banner|visual|main-visual|kv|top']:
        el = soup.find(id=re.compile(sel_id, re.I)) or soup.find(class_=re.compile(sel_id, re.I))
        if el:
            img = el.find('img')
            if img:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or ''
                if src:
                    url = src if src.startswith('http') else base_url + '/' + src.lstrip('/')
                    candidates.append(url)
            break
    for url in candidates[:2]:
        try:
            r = requests.get(url, headers=HEADERS, timeout=8)
            if r.status_code == 200 and len(r.content) > 1000:
                c = extract_dominant_color(r.content)
                if c:
                    return c
        except Exception:
            pass
    return ''


def _color_hue(hex_color):
    """0~360° 색상각(hue) 반환. 무채색=−1"""
    h = hex_color.lstrip('#')
    if len(h) == 3: h = ''.join(c*2 for c in h)
    if len(h) != 6: return -1
    try:
        r,g,b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
    except ValueError: return -1
    mx,mn = max(r,g,b), min(r,g,b)
    if mx == mn: return -1
    d = mx - mn
    if mx == r:   hue = (g-b)/d % 6
    elif mx == g: hue = (b-r)/d + 2
    else:         hue = (r-g)/d + 4
    return hue * 60


def _color_hue_diff(c1, c2):
    """두 색의 색상각 차이(0~180°). 무채색 포함 시 180 반환"""
    h1, h2 = _color_hue(c1), _color_hue(c2)
    if h1 < 0 or h2 < 0: return 180
    diff = abs(h1 - h2)
    return min(diff, 360 - diff)


def _color_vibrancy(hex_color):
    """채도·명도 기반 비비드 점수 반환 (0~1). 검정/흰색/회색 = 0"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return 0
    try:
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
    except ValueError:
        return 0
    max_c, min_c = max(r, g, b), min(r, g, b)
    l = (max_c + min_c) / 2
    if max_c == min_c:
        return 0  # 완전 회색
    d = max_c - min_c
    s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
    # 너무 어둡거나 너무 밝으면 배경색 취급
    if l < 0.15 or l > 0.85:
        return 0
    return s

# ────────────────────────────────────────────
# 1. 웹 스크래핑
# ────────────────────────────────────────────
# 서비스 가치 관련 핵심 페이지 크롤링 경로 (영/한 공통 패턴 + 자동 발견 보완)
_SCRAPE_PATHS = [
    '/',
    # 언어 prefix 없는 공통 경로
    '/about', '/about-us', '/about/company', '/about/overview',
    '/company', '/company/about', '/company/overview', '/company/intro',
    '/services', '/service', '/solutions', '/solution', '/products', '/product',
    '/team', '/our-team', '/people',
    '/contact', '/contact-us',
    '/intro', '/introduction',
    '/소개', '/회사소개', '/기업소개', '/서비스',
    # 엔터테인먼트/레이블/크리에이티브 특화
    '/artists', '/artist', '/label', '/talent', '/roster',
    '/works', '/work', '/portfolio', '/projects', '/news',
    # 한국어 prefix (/ko/) — 공통
    '/ko', '/ko/about', '/ko/company', '/ko/about/company',
    '/ko/services', '/ko/service', '/ko/intro',
    '/ko/소개', '/ko/회사소개',
    # 한국어 prefix (/ko/) — 엔터/레이블
    '/ko/about/', '/ko/artists', '/ko/artist', '/ko/label',
    '/ko/works', '/ko/news',
    # 영어 prefix (/en/) — 공통
    '/en', '/en/about', '/en/company', '/en/about/company',
    '/en/services', '/en/service', '/en/intro',
    # 영어 prefix (/en/) — 엔터/레이블
    '/en/about/', '/en/artists', '/en/label', '/en/works', '/en/news',
]

# 홈페이지 <a> 태그에서 자동 발견할 키워드 (내부 링크 추가 크롤링)
_SCRAPE_LINK_KEYWORDS = [
    'about', 'company', 'intro', 'overview', 'story', 'mission', 'vision',
    'service', 'solution', 'product', 'what-we-do',
    'artist', 'label', 'talent', 'roster', 'works', 'portfolio', 'news',
    '소개', '회사', '기업', '서비스', '솔루션', '사업', '아티스트', '레이블',
]


def _is_cookie_wall(text: str) -> bool:
    """페이지 텍스트가 쿠키 동의 페이지에 지배당하고 있는지 감지"""
    t = text.lower()
    _cw_score = sum(t.count(k) for k in [
        'cookie', 'consent', 'gdpr', 'privacy policy', '쿠키', '개인정보', '동의'])
    return _cw_score >= 4 and len(text) < 5000


def _extract_nextdata_text(obj, depth=0, results=None):
    """__NEXT_DATA__ JSON에서 의미 있는 텍스트 문자열 재귀 추출"""
    if results is None:
        results = []
    if depth > 10 or len(results) > 200:
        return results
    _SKIP_KEYS = {'__N_SSP', '__N_SSG', 'buildId', 'query', 'isFallback', 'locale',
                  'locales', 'defaultLocale', 'domainLocales', 'gip', 'appGip', 'scriptLoader'}
    if isinstance(obj, str):
        s = obj.strip()
        if 15 <= len(s) <= 600 and not s.startswith('http') and not re.match(r'^[\w/._-]{1,5}$', s):
            results.append(s)
    elif isinstance(obj, list):
        for item in obj:
            _extract_nextdata_text(item, depth + 1, results)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in _SKIP_KEYS:
                _extract_nextdata_text(v, depth + 1, results)
    return results


def _scrape_nav_links(soup, domain_root: str) -> list:
    """헤더/네비게이션의 <a> 링크에서 내부 페이지 URL 추출 — 쿠키 월 우회용.
    domain_root = 'https://domain.com' (경로 없는 도메인 루트)
    """
    links = []
    seen = set()
    for nav_el in soup.find_all(['nav', 'header']) or [soup]:
        for a in nav_el.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:') or href.startswith('javascript:'):
                continue
            if href.startswith('http') and not href.startswith(domain_root):
                continue
            if href.startswith('/'):
                full = domain_root + href.rstrip('/')
            elif href.startswith('http'):
                full = href.rstrip('/')
            else:
                full = domain_root + '/' + href.rstrip('/')
            if full not in seen and full != domain_root:
                seen.add(full)
                links.append(full)
    return links[:20]


def _score_sitemap_url(url: str) -> int:
    """URL의 회사소개 관련도 점수 계산 (높을수록 우선)"""
    u = url.lower()
    score = 0
    # 고우선: 회사/소개/아티스트/서비스 관련
    for kw in ['about', 'company', 'intro', 'overview', 'artist', 'label',
               'service', 'solution', 'work', 'portfolio', '소개', '회사', '아티스트', '레이블']:
        if kw in u:
            score += 3
    # 중우선: 팀/스토리/연락처
    for kw in ['team', 'people', 'story', 'mission', 'vision', 'contact', 'news']:
        if kw in u:
            score += 2
    # 저우선: 깊은 경로 또는 동적 컨텐츠 (블로그/게시물 등)
    depth = u.count('/') - 2  # 도메인 이후 슬래시 수
    if depth > 3:
        score -= 1
    for kw in ['blog', 'post', 'tag', 'category', 'page=', '?', 'search', 'feed',
               '.xml', '.json', '.css', '.js', 'cdn', 'static', 'asset']:
        if kw in u:
            score -= 5
    return score


def _fetch_sitemap_urls(base_url: str, max_urls: int = 30) -> list:
    """sitemap.xml에서 회사소개 관련 URL 목록 추출 — sitemap index 지원, 관련도순 정렬"""
    _parsed = urlparse(base_url)
    _domain = _parsed.netloc

    def _extract_locs(xml_text: str) -> list:
        return re.findall(r'<loc>\s*(https?://[^<\s]+)\s*</loc>', xml_text)

    collected = []
    sitemap_queue = []

    # robots.txt에서 Sitemap: 지시어 확인
    try:
        _rob = requests.get(base_url + '/robots.txt', headers=_GOOGLEBOT_HEADERS, timeout=5)
        if _rob.status_code == 200:
            for _sm in re.findall(r'(?i)^Sitemap:\s*(https?://\S+)', _rob.text, re.MULTILINE):
                sitemap_queue.append(_sm.strip())
    except Exception:
        pass

    # 기본 경로들도 시도
    for path in ['/sitemap.xml', '/sitemap_index.xml', '/sitemap/sitemap.xml', '/sitemap/index.xml']:
        sitemap_queue.append(base_url + path)
    sitemap_queue = list(dict.fromkeys(sitemap_queue))  # 중복 제거

    fetched_sitemaps = set()
    MAX_SITEMAP_FETCHES = 8
    fetch_count = 0
    while sitemap_queue and fetch_count < MAX_SITEMAP_FETCHES:
        sm_url = sitemap_queue.pop(0)
        if sm_url in fetched_sitemaps:
            continue
        fetched_sitemaps.add(sm_url)
        fetch_count += 1
        try:
            r = requests.get(sm_url, headers=_GOOGLEBOT_HEADERS, timeout=6)
            if r.status_code != 200:
                continue
            _txt = r.text
            if not ('<url' in _txt or '<sitemap' in _txt or 'urlset' in _txt):
                continue
            locs = _extract_locs(_txt)
            if not locs:
                continue
            # sitemap index 감지 → 자식 sitemap을 큐에 동적 추가
            if '<sitemapindex' in _txt or ('<sitemap' in _txt and '<url>' not in _txt):
                for child_sm in locs[:5]:
                    if child_sm not in fetched_sitemaps:
                        sitemap_queue.append(child_sm)
                continue
            # 일반 sitemap — 도메인 내 URL만 수집
            _seen_urls = {c[0] for c in collected}
            for u in locs:
                if _domain in u:
                    clean = u.rstrip('/')
                    if clean != base_url and clean not in _seen_urls:
                        _seen_urls.add(clean)
                        collected.append((clean, _score_sitemap_url(clean)))
            if len(collected) >= max_urls * 3:
                break
        except Exception:
            continue

    if not collected:
        return []

    # 관련도순 정렬 → 상위 max_urls개
    collected.sort(key=lambda x: x[1], reverse=True)
    result = [u for u, s in collected if s >= 0][:max_urls]
    print(f"  [Sitemap] {len(result)}개 관련 URL 발견 (전체 {len(collected)}개 중)")
    return result


def clean_raw_text(raw_info: str) -> str:
    """크롤링 원문 전처리 — Researcher 에이전트 투입 전 노이즈 제거 + 중복 압축 + 12000자 정제"""
    text = raw_info

    # ── 1. 패턴 기반 노이즈 제거 ──────────────────────────────────────────
    _NOISE = [
        # 쿠키 동의 / GDPR 배너
        r'(accept all cookies?|모든 쿠키 허용|쿠키 (정책|설정|동의)|cookie (policy|settings?|consent|notice|banner))[^.]{0,150}',
        # 저작권 표시
        r'(copyright\s*©?|©)\s*\d{4}[^.\n]{0,100}',
        r'all rights reserved[^.\n]{0,80}',
        # SNS 팔로우 유도 (짧은 구문만)
        r'(follow us|팔로우|구독하세요?)\s*(?:us\s*)?(?:on\s*)?(instagram|facebook|twitter|youtube|linkedin|tiktok|kakao)[^.]{0,80}',
        # 브레드크럼 내비게이션
        r'(홈|home)\s*[>›»/]\s*[^>›»/\n]{1,40}([>›»/]\s*[^>›»/\n]{1,30}){0,3}',
        # UI 조작 텍스트
        r'\b(맨 위로|위로 가기|back to top|scroll to top|메뉴 열기|메뉴 닫기|사이드바 열기|skip to (main )?content)\b',
        # 로딩/플레이스홀더
        r'\b(loading\.\.\.|로딩 중|불러오는 중|please wait)\b',
        # 빈 alt 텍스트 잔재
        r'\[\s*\]\s*',
    ]
    for pat in _NOISE:
        text = re.sub(pat, ' ', text, flags=re.I | re.DOTALL)

    # ── 2. 페이지 간 중복 문구 압축 ────────────────────────────────────────
    # 동일 35자+ 구문이 여러 페이지에 반복되면 첫 등장만 유지 (nav 중복 제거 등)
    _seen: set = set()
    def _once(m: re.Match) -> str:
        chunk = m.group().strip()
        key = re.sub(r'\s+', '', chunk.lower())
        if len(key) < 20:
            return m.group()
        if key in _seen:
            return ' '
        _seen.add(key)
        return m.group()
    text = re.sub(r'[가-힣A-Za-z0-9][가-힣A-Za-z0-9 ,.()\-]{33,98}', _once, text)

    # ── 3. 공백 정리 ────────────────────────────────────────────────────────
    text = re.sub(r'[ \t]{4,}', '  ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # ── 4. 12000자로 자르되 섹션 구분선 기준으로 깔끔하게 절단 ───────────────
    LIMIT = 12000
    if len(text) > LIMIT:
        # 마지막 섹션 구분선 앞에서 자르기 (문장 중간 절단 방지)
        cutoff = text.rfind('---', 0, LIMIT)
        text = text[:cutoff].rstrip() if cutoff > LIMIT * 0.7 else text[:LIMIT]

    return text.strip()


_PW_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/124.0.0.0 Safari/537.36'
)
_PW_CONTEXT_OPTS = dict(
    user_agent=_PW_UA,
    viewport={'width': 1440, 'height': 900},
    locale='ko-KR',
    timezone_id='Asia/Seoul',
    java_script_enabled=True,
    extra_http_headers={
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    },
)


def _make_pw_page(browser):
    """봇 감지 우회 설정이 적용된 Playwright 페이지 반환."""
    ctx = browser.new_context(**_PW_CONTEXT_OPTS)
    page = ctx.new_page()
    # navigator.webdriver = false 로 설정 (봇 탐지 우회)
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
        Object.defineProperty(navigator, 'languages', { get: () => ['ko-KR', 'ko', 'en-US'] });
        window.chrome = { runtime: {} };
    """)
    return page


def _pw_dismiss_cookie(page) -> bool:
    """쿠키/GDPR 동의 모달 자동 클릭. 닫혔으면 True 반환.
    ibighit.com처럼 모달이 전체 페이지를 덮는 사이트 대응.
    secondary 버튼(거부/설정없이) 우선 클릭 → 실패 시 텍스트 매칭 fallback.
    """
    try:
        # 1순위: CSS module 'secondary' 클래스 버튼 (ibighit, 일반 Next.js 패턴)
        clicked = page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            // secondary 클래스 버튼 중 마지막(거부/설정없이) 클릭
            const secondary = btns.filter(b =>
                b.className.includes('secondary') || b.className.includes('decline') ||
                b.className.includes('reject') || b.className.includes('refuse'));
            if (secondary.length > 0) {
                secondary[secondary.length - 1].click();
                return true;
            }
            // 텍스트 매칭 fallback
            const keywords = ['설정하지', '거부', 'decline', 'reject', 'refuse', 'skip', 'close'];
            const found = btns.find(b => {
                const t = b.textContent.toLowerCase();
                return keywords.some(k => t.includes(k));
            });
            if (found) { found.click(); return true; }
            return false;
        }""")
        if clicked:
            # 클릭 후 React 재렌더 대기 (ibighit 기준 ~3초 필요)
            page.wait_for_timeout(3500)
            return True
    except Exception:
        pass

    # CSS 셀렉터 fallback
    for sel in ['[class*="cookie"] button', '[id*="cookie"] button',
                '[class*="consent"] button', '[class*="gdpr"] button',
                '[class*="Cookie"] button', '[class*="Consent"] button']:
        try:
            page.click(sel, timeout=1500)
            page.wait_for_timeout(3500)
            return True
        except Exception:
            pass
    return False


def _fetch_with_playwright(url: str, wait: str = 'networkidle', timeout: int = 25000) -> str:
    """JS 렌더링 후 HTML 반환. 실패 시 빈 문자열."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = _make_pw_page(browser)
                page.goto(url, wait_until='domcontentloaded', timeout=timeout)
                page.wait_for_timeout(4000)   # React/Next.js 하이드레이션 대기
                _pw_dismiss_cookie(page)
                page.wait_for_timeout(1000)
                html = page.content()
            finally:
                browser.close()
        return html
    except Exception as e:
        print(f"  [Playwright] 실패: {e}")
        return ''


def _playwright_get_links(url: str, base_url: str) -> list:
    """Playwright로 JS 렌더 후 DOM 전체 <a href> 수집 → 내부 링크 리스트.
    networkidle 대신 domcontentloaded + 2.5초 대기로 React 하이드레이션 확보.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = _make_pw_page(browser)
                page.goto(url, wait_until='domcontentloaded', timeout=20000)
                page.wait_for_timeout(4000)   # React 하이드레이션 대기 (쿠키 모달 포함)
                _pw_dismiss_cookie(page)       # 쿠키 모달 닫기 (내부에서 재렌더 대기)
                page.wait_for_timeout(1500)   # 모달 닫힌 후 nav 재렌더 대기
                hrefs = page.evaluate("""() =>
                    Array.from(document.querySelectorAll('a[href]'))
                        .map(a => a.getAttribute('href'))
                        .filter(h => h && !h.startsWith('#')
                                  && !h.startsWith('mailto:')
                                  && !h.startsWith('tel:')
                                  && !h.startsWith('javascript:'))
                """)
            finally:
                browser.close()
        base = base_url.rstrip('/')
        links, seen = [], set()
        for href in (hrefs or []):
            if href.startswith('http') and not href.startswith(base):
                continue
            if href.startswith('/'):
                full = base + href.rstrip('/')
            elif href.startswith('http'):
                full = href.rstrip('/')
            else:
                full = base + '/' + href.rstrip('/')
            if full and full != base and full not in seen:
                seen.add(full)
                links.append(full)
        print(f"  [Playwright Nav] {len(links)}개 내부 링크 발견")
        return links
    except Exception as e:
        print(f"  [Playwright Nav] 실패: {e}")
        return []


def _playwright_extract_images(url: str, base: str, _skip_pat=None) -> list:
    """Playwright로 JS 렌더 후 img.src + computedStyle background-image 수집.
    CSR/Next.js SPA 사이트에서 정적 HTML로는 얻을 수 없는 이미지 대응.
    _skip_pat: 커스텀 skip 패턴 (기본값 _SKIP_IMG_PAT, 아티스트 모드는 _SKIP_IMG_PAT_ARTIST)
    """
    if _skip_pat is None:
        _skip_pat = _SKIP_IMG_PAT
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = _make_pw_page(browser)
                page.goto(url, wait_until='domcontentloaded', timeout=20000)
                page.wait_for_timeout(4000)   # React 하이드레이션 + 쿠키 모달 대기
                _pw_dismiss_cookie(page)       # 쿠키 모달 닫기 (내부에서 재렌더 대기)
                page.wait_for_timeout(1500)   # 모달 닫힌 후 이미지 재렌더 대기
                # ── 레이지로딩 트리거: 스크롤 다운 ──
                try:
                    page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight/3); }")
                    page.wait_for_timeout(700)
                    page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight*2/3); }")
                    page.wait_for_timeout(700)
                    page.evaluate("() => { window.scrollTo(0, document.body.scrollHeight); }")
                    page.wait_for_timeout(1000)
                    page.evaluate("() => { window.scrollTo(0, 0); }")
                except Exception:
                    pass
                raw_urls = page.evaluate("""() => {
                    const results = [];
                    // <img> 태그 src + srcset
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.src
                            || img.getAttribute('data-src')
                            || img.getAttribute('data-lazy-src') || '';
                        if (src && src.startsWith('http')) results.push(src);
                        const ss = img.getAttribute('srcset') || '';
                        if (ss) ss.split(',').forEach(s => {
                            const p = s.trim().split(/\\s+/)[0];
                            if (p && p.startsWith('http')) results.push(p);
                        });
                    });
                    // computedStyle background-image (JS로 주입된 CSS 포함)
                    document.querySelectorAll('*').forEach(el => {
                        try {
                            const bg = getComputedStyle(el).backgroundImage;
                            if (bg && bg !== 'none') {
                                const m = bg.match(/url\\(["']?([^"')]+)["']?\\)/);
                                if (m && m[1].startsWith('http')) results.push(m[1]);
                            }
                        } catch(e) {}
                    });
                    return results;
                }""")
            finally:
                browser.close()
        seen, images = set(), []
        for src in (raw_urls or []):
            if src and not _skip_pat.search(src) and src not in seen:
                seen.add(src)
                images.append((src, '', 'playwright'))
        print(f"  [Playwright Images] {len(images)}개 수집")
        return images
    except Exception as e:
        print(f"  [Playwright Images] 실패: {e}")
        return []


def _extract_logo_url_with_playwright(url: str) -> str:
    """Playwright로 JS 렌더 후 img/CSS에서 logo 키워드 포함 URL 반환. 실패 시 빈 문자열."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = _make_pw_page(browser)
                page.goto(url, wait_until='networkidle', timeout=25000)
                # JS 실행으로 img src + CSS background-image URL 수집
                logo_urls = page.evaluate("""() => {
                    const results = [];
                    // img 태그 src
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.src || img.getAttribute('data-src') || '';
                        if (src) results.push(src);
                    });
                    // CSS background-image
                    document.querySelectorAll('*').forEach(el => {
                        const bg = getComputedStyle(el).backgroundImage;
                        const m = bg && bg.match(/url\\(["']?([^"')]+)["']?\\)/);
                        if (m) results.push(m[1]);
                    });
                    return results;
                }""")
            finally:
                browser.close()
        # logo 키워드 포함 URL 우선, SVG 우선
        candidates = [u for u in logo_urls if 'logo' in u.lower()]
        svg_logos = [u for u in candidates if u.lower().endswith('.svg')]
        png_logos = [u for u in candidates if any(u.lower().endswith(e) for e in ['.png', '.webp', '.jpg'])]
        return svg_logos[0] if svg_logos else (png_logos[0] if png_logos else (candidates[0] if candidates else ''))
    except Exception as e:
        print(f"  [Playwright Logo] 실패: {e}")
        return ''


def _fetch_page(target_url: str, base_url: str) -> tuple:
    """단일 URL 페치 → (soup, raw_text) 반환. 쿠키 월 감지 시 Googlebot UA 재시도."""
    for hdrs in [HEADERS, _GOOGLEBOT_HEADERS]:
        try:
            resp = requests.get(target_url, headers=hdrs, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                raw_text = soup.get_text(separator=' ').strip()
                if _is_cookie_wall(raw_text):
                    if hdrs is HEADERS:
                        print(f"  [쿠키 월 감지] Googlebot UA로 재시도: {target_url}")
                        continue  # Googlebot UA로 retry
                    else:
                        print(f"  [쿠키 월] Googlebot UA도 차단됨, 네비 링크만 추출")
                # JS-heavy (300자 미만)
                _has_noscript = bool(soup.find('noscript'))
                if len(raw_text) < 300 or _has_noscript:
                    print(f"  [Playwright] JS 렌더링 감지 ({len(raw_text)}자) — 재시도 중...")
                    _pw_html = _fetch_with_playwright(target_url)
                    if _pw_html:
                        soup = BeautifulSoup(_pw_html, 'html.parser')
                        print(f"  [Playwright] 완료 ({len(soup.get_text(separator=' ').strip())}자)")
                return soup, soup.get_text(separator=' ').strip()
        except Exception as e:
            print(f"  오류 ({target_url}): {e}")
            break
    return None, ''


def _extract_page_content(soup, base_url: str, label: str) -> tuple:
    """soup에서 (page_text, footer_txt, image_urls) 추출 — 공통 헬퍼"""
    # __NEXT_DATA__ 텍스트 추출 (Next.js SSR)
    nd_text = ''
    _nd_script = soup.find('script', id='__NEXT_DATA__')
    if _nd_script:
        try:
            _nd_json = json.loads(_nd_script.string or '{}')
            _nd_strings = _extract_nextdata_text(_nd_json)
            if _nd_strings:
                nd_text = '\n'.join(_nd_strings[:80])
                print(f"  [__NEXT_DATA__] {label}: {len(_nd_strings)}개 텍스트")
        except Exception:
            pass

    # 이미지 URL
    imgs = []
    for img in soup.find_all('img', src=True):
        src = img.get('src', '')
        if not src:
            continue
        if src.startswith('//'):
            src = 'https:' + src
        elif not src.startswith('http'):
            src = base_url + '/' + src.lstrip('/')
        if any(x in src.lower() for x in ['icon', 'favicon', 'sprite', '1x1', 'pixel']):
            continue
        imgs.append(src)

    # 푸터 (연락처 보존)
    footer_txt = ''
    footer_el = soup.find('footer') or soup.find(attrs={'class': re.compile(r'footer', re.I)})
    if footer_el:
        footer_raw = re.sub(r'\s+', ' ', footer_el.get_text(separator=' ')).strip()
        if len(footer_raw) > 10:
            footer_txt = f"\n--- 푸터(연락처) ---\n{footer_raw[:600]}\n"

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav",
                     "iframe", "form", "button", "svg"]):
        tag.decompose()
    body_text = re.sub(r'\s+', ' ', soup.get_text(separator=' ')).strip()

    page_text = body_text
    if nd_text and len(nd_text) > 200:
        page_text = (body_text + '\n[SSR DATA]\n' + nd_text) if body_text else nd_text

    return page_text, footer_txt, imgs


def scrape_website(url):
    """
    크롤링 전략 (우선순위 순):
    1. 홈페이지(/) 항상 먼저 — meta/og 태그·브랜드 정보
    2. sitemap.xml 확인 → 관련도 높은 URL 목록 확보
    3. 사이트맵 있음  → 사이트맵 URL 크롤링 (최대 12개)
       사이트맵 없음  → _SCRAPE_PATHS 경로 순차 시도
    4. 네비게이션 링크 자동 발견 → 미방문 URL 추가 크롤링 (최대 8개)
    """
    all_text = ""
    image_urls = []
    visited = set()
    base_url = url.rstrip('/')
    # 도메인 루트 (경로 없는 origin) — 상대 경로 href 조합에 사용
    _parsed_url = urlparse(url)
    domain_root = _parsed_url.scheme + '://' + _parsed_url.netloc
    # 입력 URL이 깊은 경로면 해당 경로를 주제 필터로 사용
    # 예: /artist/profile/LE%20SSERAFIM → 관련 링크만 크롤링 (label 전체 크롤링 방지)
    _url_path = unquote(_parsed_url.path).rstrip('/')
    _url_path_depth = len([p for p in _url_path.split('/') if p])
    _subject_key = unquote(base_url.split('/')[-1]).lower() if _url_path_depth >= 2 else ''
    home_soup = None

    # 서브페이지 입력 시 부모 URL 자동 생성 (예: /ko/cortis/profile → /ko/cortis)
    _parent_urls = []
    if _url_path_depth >= 2:
        _parts = [p for p in _url_path.split('/') if p]
        for _depth in range(len(_parts) - 1, 0, -1):
            _parent_path = '/' + '/'.join(_parts[:_depth])
            _parent_url = _parsed_url.scheme + '://' + _parsed_url.netloc + _parent_path
            if _parent_url != base_url:
                _parent_urls.append(_parent_url)
        if _parent_urls:
            print(f"  [서브페이지 감지] 부모 URL 자동 추가: {_parent_urls}")

    def _is_relevant_link(link_url: str) -> bool:
        """입력 URL 이하 경로 or 주제 키워드 포함 링크만 허용 (깊은 URL 입력 시)"""
        if _url_path_depth < 2:
            return True  # 일반 홈페이지 → 전체 내부 링크 허용
        link_unquoted = unquote(link_url).lower()
        # 주제 키워드(아티스트명 등)가 링크에 포함되면 허용
        if _subject_key and _subject_key in link_unquoted:
            return True
        # 입력 URL 자체의 서브패스이면 허용
        if link_url.startswith(base_url):
            return True
        return False

    # ── STEP 1: 홈페이지 크롤링 (항상) ─────────────────────────────────────
    print(f"  [홈페이지] 크롤링: {base_url}")
    visited.add(base_url)
    soup, _ = _fetch_page(base_url, base_url)
    if soup:
        home_soup = soup
        # og:title / <title> 추출 → 아티스트/주체 감지용으로 text 앞에 삽입
        _og_meta = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'og:title'})
        _og_title_val = (_og_meta.get('content', '') if _og_meta else '').strip()
        if not _og_title_val and soup.find('title'):
            _og_title_val = soup.find('title').get_text(strip=True)
        if _og_title_val:
            all_text = f"[og:title]: {_og_title_val}\n" + all_text
        page_text, footer_txt, imgs = _extract_page_content(soup, base_url, '/')
        all_text += f"--- Path: / ---\n{page_text}\n{footer_txt}\n"
        for src in imgs:
            if src not in image_urls:
                image_urls.append(src)

    # ── STEP 1b: 부모 URL 크롤링 (서브페이지 입력 시) ───────────────────────
    for _pu in _parent_urls:
        if _pu in visited:
            continue
        print(f"  [부모URL] 크롤링: {_pu}")
        visited.add(_pu)
        _ps, _ = _fetch_page(_pu, base_url)
        if _ps:
            _pt, _pf, _pi = _extract_page_content(_ps, base_url, _pu)
            all_text += f"--- Path: {_pu} ---\n{_pt}\n{_pf}\n"
            for src in _pi:
                if src not in image_urls:
                    image_urls.append(src)

    # ── STEP 2: Sitemap 확인 ────────────────────────────────────────────────
    print(f"  [Sitemap] 확인 중...")
    sitemap_urls = _fetch_sitemap_urls(base_url, max_urls=20)

    # ── STEP 3A: 사이트맵 있음 → 관련 URL 크롤링 ───────────────────────────
    if sitemap_urls:
        _to_crawl = [u for u in sitemap_urls if u not in visited and _is_relevant_link(u)][:12]
        print(f"  [Sitemap] {len(_to_crawl)}개 페이지 크롤링")
        for sm_url in _to_crawl:
            visited.add(sm_url)
            try:
                print(f"  크롤링 중 (sitemap): {sm_url}")
                s, _ = _fetch_page(sm_url, base_url)
                if not s:
                    continue
                pt, ft, imgs2 = _extract_page_content(s, base_url, sm_url)
                if len(pt) > 50:
                    all_text += f"--- URL: {sm_url} ---\n{pt}\n{ft}\n"
                for src in imgs2:
                    if src not in image_urls:
                        image_urls.append(src)
            except Exception as e:
                print(f"  오류 ({sm_url}): {e}")

    # ── STEP 3B: 사이트맵 없음 → 헤더/네비 링크 우선, 그 다음 _SCRAPE_PATHS ─
    else:
        print(f"  [Sitemap] 없음 — 헤더 링크 우선 크롤링 시작")
        # 1) 홈페이지 nav/header 링크 추출 (쿠키 월이어도 <a> 태그는 살아있는 경우 많음)
        nav_links_3b = []
        if home_soup:
            nav_links_3b = _scrape_nav_links(home_soup, domain_root)
            # 전체 <a>에서 키워드 매칭 추가
            for a in home_soup.find_all('a', href=True):
                href = a['href'].strip()
                if href.startswith('http') and not href.startswith(domain_root):
                    continue
                if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                    continue
                full = (domain_root + href.rstrip('/')) if href.startswith('/') else (domain_root + '/' + href.rstrip('/'))
                if full not in visited:
                    nav_links_3b.append(full)
            # 깊은 URL 입력 시 주제 관련 링크만 필터
            nav_links_3b = [l for l in dict.fromkeys(nav_links_3b) if _is_relevant_link(l)]
            if nav_links_3b:
                print(f"  [Nav] 헤더/링크 {len(nav_links_3b)}개 발견")

        # 1-B) 정적 HTML에서 링크가 부족하면 Playwright로 JS 렌더된 DOM 전체 스캔
        if len(nav_links_3b) < 3:
            print(f"  [Nav] 링크 부족({len(nav_links_3b)}개) → Playwright 렌더 링크 시도")
            pw_links = _playwright_get_links(base_url, domain_root)
            pw_links = [l for l in pw_links if _is_relevant_link(l)]
            nav_links_3b = list(dict.fromkeys(nav_links_3b + pw_links))
            if pw_links:
                print(f"  [Nav+PW] 총 {len(nav_links_3b)}개 링크")

        # 2) nav 링크가 부족하면 _SCRAPE_PATHS로 보완
        path_links_3b = []
        if len(nav_links_3b) < 8:
            for path in _SCRAPE_PATHS:
                if path == '/':
                    continue
                full = domain_root + path
                if full not in visited and full not in nav_links_3b:
                    path_links_3b.append(full)

        # 3) GNB nav 링크 전체 + _SCRAPE_PATHS 보완 최대 12개
        gnb_urls  = [u for u in dict.fromkeys(nav_links_3b)  if u not in visited]          # GNB 전체 (제한 없음)
        path_urls = [u for u in dict.fromkeys(path_links_3b) if u not in visited][:12]     # _SCRAPE_PATHS 폴백 최대 12개
        to_crawl_3b = list(dict.fromkeys(gnb_urls + path_urls))
        for target_url in to_crawl_3b:
            visited.add(target_url)
            try:
                print(f"  크롤링 중: {target_url}")
                s, _ = _fetch_page(target_url, base_url)
                if not s:
                    continue
                pt, ft, imgs2 = _extract_page_content(s, base_url, target_url)
                if len(pt) > 50:
                    all_text += f"--- URL: {target_url} ---\n{pt}\n{ft}\n"
                for src in imgs2:
                    if src not in image_urls:
                        image_urls.append(src)
            except Exception as e:
                print(f"  오류 ({target_url}): {e}")

    # ── STEP 4: sitemap 있을 때도 nav에서 놓친 링크 추가 크롤링 ─────────────
    if home_soup:
        nav_extra = _scrape_nav_links(home_soup, domain_root)
        kw_extra = []
        for a in home_soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('http') and not href.startswith(domain_root):
                continue
            if href.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
                continue
            full = (domain_root + href.rstrip('/')) if href.startswith('/') else (domain_root + '/' + href.rstrip('/'))
            if full not in visited and any(kw in href.lower() for kw in _SCRAPE_LINK_KEYWORDS):
                kw_extra.append(full)
        extra_urls = [u for u in dict.fromkeys(nav_extra + kw_extra) if u not in visited and _is_relevant_link(u)][:6]
        if extra_urls:
            print(f"  [Nav+KW] 추가 링크 {len(extra_urls)}개 크롤링")
        for eu in extra_urls:
            visited.add(eu)
            try:
                print(f"  크롤링 중 (추가): {eu}")
                s, _ = _fetch_page(eu, base_url)
                if not s:
                    continue
                pt, ft, imgs2 = _extract_page_content(s, base_url, eu)
                if len(pt) > 50:
                    all_text += f"--- Auto: {eu} ---\n{pt}\n{ft}\n"
                for src in imgs2:
                    if src not in image_urls:
                        image_urls.append(src)
            except Exception:
                pass

    if image_urls:
        all_text += "\n--- 발견된 이미지 URL ---\n" + '\n'.join(image_urls[:20])

    return all_text


def extract_brand_assets(url):
    base_url = url.rstrip('/')
    logo_url = None
    colors = []
    footer_contact = {}
    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return {'logo_url': None, 'colors': [], 'footer_contact': {}}
        soup = BeautifulSoup(resp.text, 'html.parser')
        # JS-heavy 감지: Playwright로 재시도
        if len(soup.get_text(separator=' ').strip()) < 300:
            print(f"  [Playwright] 브랜드 에셋 JS 렌더링 시도...")
            _pw_html = _fetch_with_playwright(base_url)
            if _pw_html:
                soup = BeautifulSoup(_pw_html, 'html.parser')
                print(f"  [Playwright] 완료 ({len(soup.get_text(separator=' ').strip())}자)")

        # ── 로고 추출 (헤더 → nav → 푸터 → 전체페이지 → 파비콘 → og:image 순) ──────────
        def _resolve(src):
            """상대/절대 URL 정규화"""
            if not src:
                return None
            src = src.strip()
            if src.startswith('http'):
                return src
            if src.startswith('//'):
                return 'https:' + src
            return base_url + '/' + src.lstrip('/')

        def _find_logo_in_el(el, strict=False):
            """특정 엘리먼트 안에서 로고 img 탐색, (svg_url, png_url) 반환
            strict=True: logo 키워드 없는 첫 SVG는 무시 (전체페이지 탐색 시)"""
            if not el:
                return None, None
            s_c = p_c = None
            IMG_EXTS = ('.svg',)
            PNG_EXTS = ('.png', '.webp', '.jpg', '.jpeg')

            # ① <a class/id=logo> 안의 img 우선 탐색
            for a_tag in el.find_all('a'):
                a_attrs = ' '.join([
                    ' '.join(a_tag.get('class') or []),
                    a_tag.get('id', ''), a_tag.get('aria-label', '')
                ]).lower()
                if 'logo' not in a_attrs and 'brand' not in a_attrs:
                    continue
                for img in a_tag.find_all('img'):
                    src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
                    full = _resolve(src)
                    if not full:
                        continue
                    fl = full.lower()
                    if fl.endswith('.svg') and not s_c:
                        s_c = full
                    elif not p_c and any(fl.endswith(e) for e in PNG_EXTS):
                        p_c = full

            # ② 일반 img 탐색
            for img in el.find_all('img'):
                attrs = ' '.join([
                    ' '.join(img.get('class') or []),
                    img.get('id', ''), img.get('alt', ''),
                    img.get('src', ''), img.get('title', '')
                ]).lower()
                src = img.get('src', '') or img.get('data-src', '') or img.get('data-lazy-src', '')
                full = _resolve(src)
                if not full:
                    continue
                fl = full.lower()
                has_logo_kw = 'logo' in attrs or 'brand' in attrs
                if has_logo_kw:
                    if fl.endswith('.svg') and not s_c:
                        s_c = full
                    elif not p_c and any(fl.endswith(e) for e in PNG_EXTS):
                        p_c = full
                elif not strict and not s_c and fl.endswith('.svg'):
                    # logo 키워드 없어도 헤더/nav/푸터 내 첫 SVG는 보통 로고
                    s_c = full

            # ③ <picture> 태그 안 <source>도 확인
            for pic in el.find_all('picture'):
                for src_tag in pic.find_all('source'):
                    src = src_tag.get('srcset', '').split()[0]
                    full = _resolve(src)
                    if not full:
                        continue
                    fl = full.lower()
                    if fl.endswith('.svg') and not s_c:
                        s_c = full
                    elif not p_c and any(fl.endswith(e) for e in PNG_EXTS):
                        p_c = full

            return s_c, p_c

        # 헤더: <header> 태그 + nav/navbar/navigation/site-header/topbar/masthead 계열
        _HEADER_CLASS = re.compile(
            r'(?:^|\b)(?:header|navbar|nav(?:bar)?|navigation|site-header|top-?bar|masthead)(?:\b|$)', re.I)
        header_el = (soup.find('header') or
                     soup.find(id=re.compile(r'header|navbar|navigation', re.I)) or
                     soup.find(class_=_HEADER_CLASS) or
                     soup.find('nav'))
        # 푸터: <footer> 태그 + footer/bottom-bar 계열
        _FOOTER_CLASS = re.compile(r'(?:^|\b)(?:footer|bottom-?bar|site-footer)(?:\b|$)', re.I)
        footer_el = (soup.find('footer') or
                     soup.find(id=re.compile(r'footer', re.I)) or
                     soup.find(class_=_FOOTER_CLASS))

        # 헤더에서 먼저 탐색
        svg_c, png_c = _find_logo_in_el(header_el)
        # 헤더에서 못 찾으면 nav (헤더와 다른 경우)
        if not svg_c and not png_c:
            for nav in soup.find_all('nav'):
                if nav is header_el:
                    continue
                svg_c, png_c = _find_logo_in_el(nav)
                if svg_c or png_c:
                    break
        # nav에서도 못 찾으면 푸터
        if not svg_c and not png_c:
            svg_c, png_c = _find_logo_in_el(footer_el)
        # 그래도 없으면 전체 페이지 (logo/brand 키워드 필수)
        if not svg_c and not png_c:
            svg_c, png_c = _find_logo_in_el(soup, strict=True)
        logo_url = svg_c or png_c

        # Playwright JS 렌더 후 logo URL 탐색 (HTML 파싱으로 못 찾은 경우)
        if not logo_url:
            print(f"  [Playwright Logo] JS 렌더링으로 로고 탐색 시도...")
            _pw_logo = _extract_logo_url_with_playwright(base_url)
            if _pw_logo:
                logo_url = _pw_logo
                print(f"  [Playwright Logo] 발견: {logo_url}")

        # 파비콘 (낮은 순위 — 작은 아이콘, 로고 폴백용)
        if not logo_url:
            for rel in ['apple-touch-icon', 'icon', 'shortcut icon']:
                tag = soup.find('link', rel=lambda r: r and rel in r)
                if tag and tag.get('href'):
                    href = tag['href']
                    candidate = href if href.startswith('http') else base_url + '/' + href.lstrip('/')
                    if any(candidate.lower().endswith(ext) for ext in ['.svg', '.png', '.webp']):
                        logo_url = candidate
                        break

        # ── 파비콘 전용 탐색 (워터마크용 — 메인 로고와 독립) ──────────────
        favicon_url = None
        # apple-touch-icon 우선(고해상도), 이후 icon, shortcut icon 순
        for rel_val in ['apple-touch-icon', 'icon', 'shortcut icon']:
            tags = soup.find_all('link', rel=lambda r: r and rel_val in r)
            for tag in tags:
                href = tag.get('href', '')
                if not href:
                    continue
                candidate = href if href.startswith('http') else base_url + '/' + href.lstrip('/')
                if any(candidate.lower().endswith(ext) for ext in ['.png', '.webp', '.jpg', '.ico', '.svg']):
                    favicon_url = candidate
                    break
            if favicon_url:
                break
        # og:image (최후 수단)
        if not logo_url:
            og = soup.find('meta', property='og:image')
            if og and og.get('content'):
                logo_url = og['content']

        # ── 컬러 추출 (CSS 변수 → 헤더/푸터 클래스 → 전체 CSS 빈도순) ──────────
        raw_css = ''.join(t.get_text() for t in soup.find_all('style'))
        all_css_links = [
            lnk.get('href', '')
            for lnk in soup.find_all('link', rel=lambda r: r and 'stylesheet' in r)
        ]

        # Elementor/page-specific CSS 우선, 폰트/아이콘 CSS 제외
        priority = [h for h in all_css_links if re.search(
            r'uploads.*\.css|post-\d+\.css|page-\d+\.css|custom|child|theme', h, re.I)]
        general = [h for h in all_css_links if h not in priority
                   and not re.search(r'font|icon|bootstrap|material|pretendard|xeicon|icomoon', h, re.I)
                   and not h.startswith('https://fonts.') and not h.startswith('https://cdn.jsdelivr')]
        to_load = priority[:4] + general[:4]  # 일반 CSS 최대 4개로 확대

        for href in to_load:
            css_url = href if href.startswith('http') else base_url + '/' + href.lstrip('/')
            try:
                r = requests.get(css_url, headers=HEADERS, timeout=8)
                if r.status_code == 200:
                    raw_css += r.text
            except Exception:
                pass

        # WordPress/Elementor 기본 팔레트·프리셋 전부 제거 후 변수 추출
        clean_css = re.sub(r'--wp--preset--[\w-]+\s*:[^;]+;', '', raw_css)
        clean_css = re.sub(r'\.has-[\w-]+-color\s*\{[^}]*\}', '', clean_css)
        clean_css = re.sub(r'\.wp-block[\w-]*\s*\{[^}]*\}', '', clean_css)
        # Elementor 해시 기반 자동생성 변수만 제거, named 변수는 보존
        clean_css = re.sub(r'--e-global-[\w]+-[a-f0-9]{5,}\s*:[^;]+;', '', clean_css)

        # 명시적 브랜드 변수 이름 목록 (vibrancy 무관하게 반드시 수집)
        _EXPLICIT_BRAND_VARS = {
            '--color-primary', '--primary-color', '--color-accent', '--accent-color',
            '--brand-color', '--theme-color', '--color-brand', '--color-theme',
            '--color-key', '--key-color', '--main-color', '--color-main',
        }
        var_pat = re.compile(r'--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b', re.I)
        tier0, tier1, tier2 = [], [], []  # tier0: 명시적 브랜드 변수 (vibrancy 무관)
        explicit_primary = ''  # --color-primary / --primary-color 최우선 값
        for m in var_pat.finditer(clean_css):
            var_name = m.group(1).lower()
            full_var = '--' + var_name
            c = m.group(2).upper()
            # 명시적 브랜드 변수는 vibrancy 무관하게 tier0로 (순수흰/순수검정 제외)
            if full_var in _EXPLICIT_BRAND_VARS:
                if c not in ('#FFFFFF', '#000000') and c not in tier0:
                    tier0.append(c)
                # --color-primary / --primary-color 는 별도로 기록
                if not explicit_primary and full_var in ('--color-primary', '--primary-color'):
                    if c not in ('#FFFFFF', '#000000'):
                        explicit_primary = c
                continue
            if _color_vibrancy(c) < 0.08:
                continue
            is_color_var = any(kw in var_name for kw in [
                'color', 'primary', 'secondary', 'brand', 'accent', 'bg', 'main', 'key'])
            if not is_color_var:
                continue
            if any(kw in var_name for kw in ['accent', 'brand', 'key', 'highlight', 'primary']):
                if c not in tier1:
                    tier1.append(c)
            else:
                if c not in tier2:
                    tier2.append(c)

        # tier0: 명시적 브랜드 변수 최우선 (진한 브랜드 색 포함)
        for c in tier0:
            if c not in colors:
                colors.insert(0, c)
        for c in sorted(tier1, key=_color_vibrancy, reverse=True):
            if c not in colors:
                colors.append(c)
        for c in sorted(tier2, key=_color_vibrancy, reverse=True):
            if c not in colors and len(colors) < 6:
                colors.append(c)

        # theme-color 메타태그
        theme = soup.find('meta', attrs={'name': 'theme-color'})
        if theme and theme.get('content'):
            tc = theme['content'].strip().upper()
            if tc not in colors and _color_vibrancy(tc) >= 0.08:
                colors.append(tc)

        # ── 히어로/헤더 인라인 배경색 추출 (실제 페이지에서 사용하는 시각적 색) ──
        hero_colors = []
        _hero_els = [
            header_el,
            soup.find(id=re.compile(r'hero|banner|visual|main-visual|kv', re.I)),
            soup.find(class_=re.compile(r'(?:^|\b)(?:hero|banner|visual|jumbotron|top-visual)(?:\b|$)', re.I)),
            soup.find('section'),  # 첫 번째 섹션 (대부분 히어로)
        ]
        for el in _hero_els:
            if not el:
                continue
            # inline style에서 background/background-color
            style = el.get('style', '')
            for m in re.finditer(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,6})\b', style, re.I):
                c = m.group(1).lstrip('#')
                c = ('#' + ''.join(ch*2 for ch in c) if len(c)==3 else '#' + c).upper()
                if _color_vibrancy(c) >= 0.10 and c not in hero_colors:
                    hero_colors.append(c)
            # data-bg / data-background-color 커스텀 속성
            for attr in ('data-bg', 'data-background-color', 'data-color', 'data-bgcolor'):
                val = (el.get(attr) or '').strip()
                if val.startswith('#') and len(val) in (4, 7):
                    c = val.lstrip('#')
                    c = ('#' + ''.join(ch*2 for ch in c) if len(c)==3 else '#' + c).upper()
                    if _color_vibrancy(c) >= 0.10 and c not in hero_colors:
                        hero_colors.append(c)
            # 클래스를 통해 CSS 규칙에서 background 색 탐색
            for cls in (el.get('class') or []):
                for m in re.finditer(
                        r'(?:^|[\s,}])\.?' + re.escape(cls) + r'\s*\{([^}]+)\}',
                        raw_css, re.M):
                    for h in re.findall(r'background(?:-color)?\s*:\s*#([0-9a-fA-F]{6})\b',
                                        m.group(1), re.I):
                        c = '#' + h.upper()
                        if _color_vibrancy(c) >= 0.10 and c not in hero_colors:
                            hero_colors.append(c)

        # ── 폴백 1: CSS 변수가 없는 사이트 → 헤더/푸터/nav 엘리먼트 CSS 클래스 규칙에서 추출
        if not colors or _color_vibrancy(colors[0]) < 0.1:
            for el in [header_el, footer_el,
                       soup.find('nav') or soup.find(id=re.compile(r'nav|gnb|lnb', re.I)) or
                       soup.find(class_=re.compile(r'(?:^|\s)(?:nav|gnb|lnb|menu)(?:\s|$)', re.I))]:
                if not el:
                    continue
                # inline style
                for h in re.findall(r'#([0-9a-fA-F]{6})\b', el.get('style', '')):
                    c = '#' + h.upper()
                    if _color_vibrancy(c) >= 0.1 and c not in colors:
                        colors.append(c)
                # 클래스 → CSS 규칙 탐색
                for cls in (el.get('class') or []):
                    for m in re.finditer(
                            r'(?:^|[\s,}){}])\.?' + re.escape(cls) + r'\s*\{([^}]+)\}',
                            raw_css, re.M):
                        for h in re.findall(r'#([0-9a-fA-F]{6})\b', m.group(1)):
                            c = '#' + h.upper()
                            if _color_vibrancy(c) >= 0.1 and c not in colors:
                                colors.append(c)

        # ── 폴백 2: 전체 CSS 빈도수 기반 (비-Elementor/비-WP 사이트 최종 수단)
        if not colors or _color_vibrancy(colors[0]) < 0.1:
            from collections import Counter
            hex_count = Counter(h.upper() for h in re.findall(r'#([0-9a-fA-F]{6})\b', raw_css))
            for hex_color, _ in hex_count.most_common(30):
                c = '#' + hex_color
                if _color_vibrancy(c) >= 0.1 and c not in colors:
                    colors.append(c)
                if len(colors) >= 3:
                    break

        # 그래도 없으면 다크 중립 기본값
        if not colors or _color_vibrancy(colors[0]) < 0.1:
            colors.insert(0, '#1A1A1A')

        # ── Elementor/CSS 글로벌 변수 accent 추출 (가장 신뢰도 높은 브랜드 컬러) ──
        elementor_colors = _extract_elementor_colors(raw_css)

        # ── CSS 색상 사용 빈도 분석 (시각적 신호 — 변수명 의존 없음) ──────────────
        css_freq_colors, css_freq_scores, css_dark_total, css_light_total = _count_css_color_usage(raw_css)

        # ── 다크 테마 배경색 감지 — body/html/root/app 대표 배경 (vibrancy 필터 없이 luma 기준) ──
        def _luma_c(hx):
            h = hx.lstrip('#')
            try: r,g,b = int(h[:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
            except: return 1.0
            return 0.2126*r + 0.7152*g + 0.0722*b
        dark_bg_color = ''
        _dark_sel_pat = re.compile(
            r'(?:body|html|:root|\.app|#app|\.root|#root|\.wrapper|#wrapper|\.site|#site)'
            r'\s*\{([^}]*)\}', re.I | re.S)
        for _dm in _dark_sel_pat.finditer(raw_css):
            _block = _dm.group(1)
            _bg_m = re.search(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})\b', _block, re.I)
            if _bg_m:
                _dc = '#' + _bg_m.group(1).lstrip('#').upper()
                if _luma_c(_dc) < 0.15:
                    dark_bg_color = _dc
                    break

        # ── OG / 히어로 이미지 픽셀 분석 ───────────────────────────
        og_image_color = _download_og_image_color(soup, base_url)

        # ── 폰트 카테고리 감지 ──────────────────────────────────────────────
        font_category = 'sans'
        detected_fonts = []

        _GF_SERIF = {'noto+serif','playfair+display','merriweather','lora','dm+serif',
                     'libre+baskerville','source+serif','pt+serif','cormorant','eb+garamond'}
        _GF_DISPLAY = {'black+han+sans','bungee','fredoka','righteous','abril+fatface',
                       'alfa+slab','lobster','titan+one','fugaz+one'}

        # Google Fonts <link> 파싱
        for href in all_css_links:
            if 'fonts.googleapis.com' not in href.lower():
                continue
            for fam_param in re.findall(r'family=([^&]+)', href, re.I):
                for fam in fam_param.split('|'):
                    fk = fam.split(':')[0].strip().lower().replace(' ', '+')
                    detected_fonts.append(fk)
                    if any(s in fk for s in _GF_SERIF):   font_category = 'serif'
                    elif any(d in fk for d in _GF_DISPLAY) and font_category == 'sans':
                        font_category = 'display'

        # CSS @import 파싱
        for m in re.finditer(r'@import\s+url\(["\']?(https?://fonts\.googleapis[^"\'\s)]+)', raw_css, re.I):
            for fam_param in re.findall(r'family=([^&"\'\s]+)', m.group(1), re.I):
                for fam in re.split(r'\||%7C', fam_param):
                    fk = fam.split(':')[0].strip().lower().replace('+', ' ').strip().replace(' ', '+')
                    detected_fonts.append(fk)
                    if any(s in fk for s in _GF_SERIF):   font_category = 'serif'
                    elif any(d in fk for d in _GF_DISPLAY) and font_category == 'sans':
                        font_category = 'display'

        # CSS font-family 직접 스캔 (fallback 정제)
        if font_category == 'sans':
            _s_kw = re.compile(r'\b(serif|georgia|garamond|times|palatino|baskerville|didot)\b', re.I)
            for fm in re.findall(r'font-family\s*:\s*([^;}{]+)', raw_css, re.I)[:50]:
                if _s_kw.search(fm):
                    font_category = 'serif'; break

        detected_fonts = list(dict.fromkeys(f for f in detected_fonts if f))[:6]

        # ── 푸터 연락처 스크래핑 ──────────────────────────────────
        footer = soup.find('footer') or soup.find(attrs={'id': re.compile(r'footer', re.I)}) \
                 or soup.find(attrs={'class': re.compile(r'footer', re.I)})
        if footer:
            text = footer.get_text(separator=' ')
            # 이메일
            emails = re.findall(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', text, re.I)
            if emails:
                footer_contact['email'] = emails[0]
            # 전화번호 (한국 포함)
            phones = re.findall(r'(?:\+82[-.\s]?|0)[\d]{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}', text)
            if phones:
                footer_contact['phone'] = phones[0].strip()
            # 카카오 채널 / 링크드인 / 인스타그램
            for a in footer.find_all('a', href=True):
                href = a['href']
                if 'kakao' in href.lower() and 'channel' in href.lower():
                    footer_contact['kakao'] = href
                elif 'linkedin' in href.lower() and 'linkedin' not in footer_contact:
                    footer_contact['linkedin'] = href
                elif 'instagram' in href.lower() and 'instagram' not in footer_contact:
                    footer_contact['instagram'] = href

        # 푸터에서 못 찾으면 전체 페이지에서 이메일 탐색
        if 'email' not in footer_contact:
            all_emails = re.findall(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', soup.get_text(), re.I)
            # noreply / example 제외
            valid = [e for e in all_emails if not re.search(r'noreply|example|sentry|wp@', e, re.I)]
            if valid:
                footer_contact['email'] = valid[0]

        # ── 한글 사명 / 대표명 추출 (푸터 + 전체 페이지) ──────────────────
        _ko_search_text = (footer.get_text(separator=' ') if footer else '') + ' ' + soup.get_text(separator=' ')
        _KO_COMPANY_PATS = [
            r'(?:상호|회사명|법인명|사업체명)\s*[:\uff1a]\s*([^\n\r,\|]{2,25})',
            r'(?:주식회사|㈜|유한회사|합자회사)\s+([가-힣a-zA-Z0-9&\s]{1,20})',
            r'([가-힣]{2,10})\s*(?:주식회사|㈜)',
        ]
        _CEO_PATS = [
            r'(?:대표|대표자|대표이사|CEO|President)\s*[:\uff1a]\s*([가-힣a-zA-Z\s]{2,12})',
            r'([가-힣]{2,4})\s*대표(?:이사)?(?:\s|$|,|\|)',
        ]
        _NAMEKO_BLACKLIST = {'닫기', '인증기관', '안내', '알림', '팝업', '레이어', '확인', '취소'}
        for pat in _KO_COMPANY_PATS:
            m = re.search(pat, _ko_search_text)
            if m:
                _cand = m.group(1).strip()
                if (2 <= len(_cand) <= 25
                        and '주식회사' not in _cand[:2]
                        and '|' not in _cand
                        and '\n' not in _cand
                        and _cand not in _NAMEKO_BLACKLIST):
                    footer_contact['nameKo'] = _cand
                    break
        _CEO_BLACKLIST = {'인증기관', '닫기', '안내', '알림', '이용약관', '개인정보', '취소', '확인'}
        for pat in _CEO_PATS:
            m = re.search(pat, _ko_search_text)
            if m:
                _cand = m.group(1).strip()
                # 한국어 이름 패턴(2~4자 순수 한글/한자)만 허용, 블랙리스트 제외
                if (2 <= len(_cand) <= 4
                        and re.match(r'^[가-힣一-龯]+$', _cand)
                        and _cand not in _CEO_BLACKLIST):
                    footer_contact['ceoName'] = _cand
                    break

        # ── 컨텍트 페이지 주소 보완 스크래핑 ──────────────────────────────────
        # 홈페이지에서 못 찾은 주소/전화번호를 /contact 페이지에서 추가 탐색
        if 'address' not in footer_contact or 'phone' not in footer_contact:
            _contact_paths = ['/contact', '/contact-us', '/contacts', '/오시는길', '/찾아오시는길',
                              '/ko/contact', '/en/contact', '/about/contact']
            for _cpath in _contact_paths:
                try:
                    _cr = requests.get(base_url.rstrip('/') + _cpath, headers=HEADERS, timeout=7)
                    if _cr.status_code != 200:
                        continue
                    _cs = BeautifulSoup(_cr.text, 'html.parser')
                    _ct = _cs.get_text(separator=' ')
                    # 전화번호
                    if 'phone' not in footer_contact:
                        _phones = re.findall(r'(?:\+82[-.\s]?|0)[\d]{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}', _ct)
                        if _phones:
                            footer_contact['phone'] = _phones[0].strip()
                    # 이메일
                    if 'email' not in footer_contact:
                        _emails = re.findall(r'[\w.+-]+@[\w.-]+\.[a-z]{2,}', _ct, re.I)
                        _valid_e = [e for e in _emails if not re.search(r'noreply|example|sentry', e, re.I)]
                        if _valid_e:
                            footer_contact['email'] = _valid_e[0]
                    # 주소 (도로명/지번/영문 주소)
                    if 'address' not in footer_contact:
                        _addr_pats = [
                            r'(?:주소|address|위치|location)\s*[:\uff1a]?\s*([^\n\r]{6,60})',
                            r'([가-힣]+(?:특별시|광역시|도|시|군|구)\s+[가-힣0-9][\w\s,\-]+(?:로|길|대로|가|동|면|읍)\s*\d*[^\n\r,]{0,30})',
                        ]
                        for _ap in _addr_pats:
                            _am = re.search(_ap, _ct, re.I)
                            if _am:
                                _addr = _am.group(1).strip()
                                if 10 <= len(_addr) <= 80:
                                    footer_contact['address'] = _addr
                                    break
                    if 'address' in footer_contact and 'phone' in footer_contact:
                        break
                except Exception:
                    pass

    except Exception as e:
        print(f"  브랜드 에셋 추출 오류: {e}")
    return {
        'logo_url': logo_url,
        'colors': colors,
        'explicit_primary': explicit_primary,
        'hero_colors': hero_colors,
        'elementor_accent': elementor_colors.get('accent', ''),
        'elementor_cross_validated': elementor_colors.get('cross_validated', []),
        'css_freq_colors': css_freq_colors,
        'css_freq_scores': css_freq_scores,
        'css_dark_total':  css_dark_total,
        'css_light_total': css_light_total,
        'og_image_color': og_image_color,
        'dark_bg_color': dark_bg_color,
        'footer_contact': footer_contact,
        'favicon_url': favicon_url,
        'font_category': font_category,
        'detected_fonts': detected_fonts,
    }


# 배경 이미지로 쓰기에 부적합한 패턴 (로고·아이콘·버튼 등)
_SKIP_IMG_PAT = re.compile(
    r'logo|icon|favicon|sprite|arrow|btn|button|avatar|thumb|badge|seal|'
    r'banner\d|\.svg|/wp-includes|data:image',
    re.I
)
# 아티스트/크리에이티브 페이지용 완화 패턴 (thumb·avatar 허용 — 앨범커버·프로필 이미지 수집)
_SKIP_IMG_PAT_ARTIST = re.compile(
    r'logo|icon|favicon|sprite|arrow|btn|button|badge|seal|'
    r'banner\d|\.svg|/wp-includes|data:image',
    re.I
)

def _collect_images_from_soup(soup, base: str, add_fn) -> None:
    """soup에서 이미지 URL을 추출해 add_fn(src, alt, ctx)으로 추가."""
    # 1순위: og:image / twitter:image
    for _og_prop in ['og:image', 'twitter:image']:
        _og = soup.find('meta', property=_og_prop) or soup.find('meta', attrs={'name': _og_prop})
        if _og and _og.get('content'):
            add_fn(_og['content'], _og_prop, 'hero')

    # 1-B순위: JSON-LD 구조화 데이터
    for _jld in soup.find_all('script', type='application/ld+json'):
        try:
            _jdata = json.loads(_jld.string or '{}')
            if isinstance(_jdata, list):
                _jdata = _jdata[0] if _jdata else {}
            for _jk in ['image', 'logo', 'thumbnailUrl', 'contentUrl']:
                _jv = _jdata.get(_jk, '')
                if isinstance(_jv, str) and _jv.startswith('http'):
                    add_fn(_jv, _jk, 'json-ld')
                elif isinstance(_jv, dict):
                    add_fn(_jv.get('url', ''), _jk, 'json-ld')
        except Exception:
            pass

    # 1-C순위: __NEXT_DATA__ (Next.js SSR)
    _nd = soup.find('script', id='__NEXT_DATA__')
    if _nd:
        try:
            _ndstr = json.dumps(json.loads(_nd.string or '{}'))
            for _nm in re.finditer(r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"', _ndstr):
                add_fn(_nm.group(1), 'next-data', 'page-data')
        except Exception:
            pass

    # 2순위: hero/banner CSS background-image
    _CSS_BG_PAT = re.compile(r"url\(['\"]?(https?://[^'\")\s]+)['\"]?\)", re.I)
    for el in soup.find_all(['section', 'div', 'header', 'figure'],
                             class_=re.compile(r'hero|banner|visual|main|cover|feature|top|intro', re.I)):
        for m in _CSS_BG_PAT.finditer(el.get('style', '')):
            add_fn(m.group(1), '', el.get_text(separator=' ').strip()[:80])
    for el in soup.find_all(attrs={'data-bg': True}):
        add_fn(el['data-bg'], '', '')
    for el in soup.find_all(attrs={'data-background-image': True}):
        add_fn(el['data-background-image'], '', '')

    # 3순위: <img> 태그 (hero URL 우선 + srcset 최대 해상도)
    _PRIORITY_PAT = re.compile(r'hero|banner|main|cover|feature|visual|bg|background|top|intro', re.I)
    all_imgs = soup.find_all('img')
    priority_imgs = [i for i in all_imgs if _PRIORITY_PAT.search(i.get('src', '') or i.get('data-src', '') or '')]
    other_imgs    = [i for i in all_imgs if i not in priority_imgs]
    for img in (priority_imgs + other_imgs):
        srcset = img.get('srcset', '') or img.get('data-srcset', '')
        src = ''
        if srcset:
            _best_w, _best_src = 0, ''
            for _ss in srcset.split(','):
                _parts = _ss.strip().split()
                if len(_parts) >= 2:
                    _sw = int(_parts[1].rstrip('wx') or 0) if _parts[1][:-1].isdigit() else 0
                    if _sw > _best_w:
                        _best_w, _best_src = _sw, _parts[0]
                elif len(_parts) == 1:
                    _best_src = _best_src or _parts[0]
            src = _best_src
        if not src:
            src = (img.get('src') or img.get('data-src') or
                   img.get('data-lazy-src') or img.get('data-original') or '').strip()
        parent = img.find_parent(['div', 'section', 'article', 'li'])
        ctx = re.sub(r'\s+', ' ', parent.get_text(separator=' ')).strip()[:100] if parent else ''
        add_fn(src, img.get('alt', '').strip(), ctx)


def extract_website_images(url, max_images=30, _progress_fn=None, _artist_mode=False):
    """홈페이지 + GNB 페이지에서 배경용 대형 이미지 URL 목록 수집 → [(url, alt, context), ...]
    우선순위: og:image → hero/section CSS background-image → <img> 태그
    이미지 부족 시 Googlebot UA 폴백 → GNB 링크 추가 스캔
    _artist_mode=True: thumb/avatar 허용 + 갤러리/디스코그래피 서브링크 추가 탐색
    """
    def _log(msg):
        print(msg)
        if _progress_fn:
            _progress_fn(msg)
    images = []
    seen = set()
    base = url.rstrip('/')
    # domain_root: 상대경로 이미지 URL 구성에 사용 (아티스트 딥링크 시 버그 방지)
    _parsed_img_url = urlparse(url)
    domain_root_img = _parsed_img_url.scheme + '://' + _parsed_img_url.netloc
    # 아티스트 모드: thumb/avatar 포함 이미지 허용
    _skip_pat = _SKIP_IMG_PAT_ARTIST if _artist_mode else _SKIP_IMG_PAT

    def _add(src, alt='', ctx=''):
        if not src or _skip_pat.search(src):
            return
        full = src if src.startswith('http') else domain_root_img + '/' + src.lstrip('/')
        if full not in seen:
            seen.add(full)
            images.append((full, alt, ctx))

    pages_to_scan = []   # GNB 링크 (홈 스캔 후 채움)

    # ── 1단계: 홈페이지 스캔 (일반 UA → Googlebot UA 폴백) ──
    try:
        soup_home = None
        for hdrs in [HEADERS, _GOOGLEBOT_HEADERS]:
            try:
                resp = requests.get(base, headers=hdrs, timeout=10)
                if resp.status_code == 200:
                    soup_home = BeautifulSoup(resp.text, 'html.parser')
                    _collect_images_from_soup(soup_home, domain_root_img, _add)
                    # GNB 링크 수집 (domain_root 기준)
                    gnb = _scrape_nav_links(soup_home, domain_root_img)
                    pages_to_scan.extend(gnb[:10])
                    if not _is_cookie_wall(soup_home.get_text()):
                        break   # 쿠키 월 없으면 Googlebot UA 폴백 불필요
            except Exception:
                pass
    except Exception as e:
        _log(f"  홈페이지 이미지 수집 오류: {e}")

    # ── 2단계: 정적 이미지 부족 시 Playwright 폴백 ──
    if len(images) < 5:
        # 2-A: GNB 링크가 3개 미만이면 Playwright로 렌더된 DOM에서 링크 보완
        if len(pages_to_scan) < 3:
            _log(f"  [이미지] Playwright 링크 수집 중 (정적 GNB {len(pages_to_scan)}개)")
            pw_links = _playwright_get_links(base, domain_root_img)
            _log(f"  [이미지] Playwright 링크: {len(pw_links)}개")
            pages_to_scan = list(dict.fromkeys(pages_to_scan + pw_links))

        if pages_to_scan:
            _log(f"  [이미지] 홈 {len(images)}개 부족 → GNB {len(pages_to_scan)}개 스캔")
            for page_url in pages_to_scan:
                if len(images) >= max_images:
                    break
                # 2-B: 정적 스캔 먼저, 이미지 없으면 Playwright
                got = False
                for hdrs in [HEADERS, _GOOGLEBOT_HEADERS]:
                    try:
                        resp = requests.get(page_url, headers=hdrs, timeout=8)
                        if resp.status_code == 200:
                            soup_p = BeautifulSoup(resp.text, 'html.parser')
                            before = len(images)
                            _collect_images_from_soup(soup_p, domain_root_img, _add)
                            if len(images) > before and not _is_cookie_wall(soup_p.get_text()):
                                got = True
                                break
                    except Exception:
                        pass
                if not got:
                    for img_tuple in _playwright_extract_images(page_url, domain_root_img, _skip_pat):
                        _add(*img_tuple)
                        if len(images) >= max_images:
                            break

    # ── 3단계: 여전히 부족하면 홈페이지 자체를 Playwright로 이미지 추출 ──
    if len(images) < 3:
        for img_tuple in _playwright_extract_images(base, domain_root_img, _skip_pat):
            _add(*img_tuple)
            if len(images) >= max_images:
                break

    # ── 4단계: 아티스트 모드 — 갤러리/디스코그래피 서브링크 추가 스캔 ──
    if _artist_mode and len(images) < max_images:
        _gallery_kw = re.compile(r'gallery|photo|disc|album|media|news|music|video|image', re.I)
        _extra_links = []
        try:
            resp = requests.get(base, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                soup_e = BeautifulSoup(resp.text, 'html.parser')
                for a in soup_e.find_all('a', href=True):
                    href = a['href']
                    if _gallery_kw.search(href) or _gallery_kw.search(a.get_text()):
                        full = href if href.startswith('http') else domain_root_img + '/' + href.lstrip('/')
                        if full.startswith(domain_root_img) and full not in seen and full != base:
                            _extra_links.append(full)
        except Exception:
            pass
        _log(f"  [아티스트 갤러리] 추가 링크 {len(_extra_links)}개 탐색")
        _disc_kw = re.compile(r'disc|album|release|music|single', re.I)
        for _el in _extra_links[:5]:
            if len(images) >= max_images:
                break
            try:
                resp = requests.get(_el, headers=HEADERS, timeout=8)
                if resp.status_code == 200:
                    # 페이지 URL에 discography/album 키워드가 있으면 해당 페이지 이미지에 'album' ctx prefix
                    _page_ctx_prefix = 'album ' if _disc_kw.search(_el) else ''
                    def _add_with_ctx(src, alt='', ctx=''):
                        _add(src, alt, _page_ctx_prefix + ctx)
                    _collect_images_from_soup(BeautifulSoup(resp.text, 'html.parser'), domain_root_img, _add_with_ctx)
            except Exception:
                pass

    return images[:max_images]


def download_image_b64(img_url):
    """이미지 URL → (base64_str, mime_type, width, height) 또는 (None, None, 0, 0)
    - 최소 해상도: max(w,h) >= 600 and min(w,h) >= 300 (세로형/정사각형 모두 허용)
    """
    try:
        r = requests.get(img_url, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            ct = r.headers.get('content-type', '').split(';')[0].strip()
            if 'image' in ct and 'svg' not in ct:
                if HAS_PIL:
                    try:
                        img = _PILImage.open(io.BytesIO(r.content))
                        w, h = img.size
                        # 1. 해상도 필터: 너무 작은 아이콘/썸네일 제외
                        if max(w, h) < 600 or min(w, h) < 300:
                            return None, None, 0, 0
                        # 2. 가로세로비 필터 제거 → 세로형 아티스트 사진·정사각 앨범아트 허용
                        # 3. 픽셀 분산 필터: 완전 단색 이미지만 제외 (std < 8)
                        try:
                            import statistics as _st
                            _gray = img.convert('L')
                            _pix = list(_gray.getdata())
                            _smp = _pix[::max(1, len(_pix)//2000)]
                            if len(_smp) > 1 and _st.stdev(_smp) < 8:
                                return None, None, 0, 0
                        except Exception:
                            pass
                        return base64.b64encode(r.content).decode('utf-8'), ct, w, h
                    except Exception:
                        pass

                # PIL 없으면 파일 크기로만 판단 (10KB 미만은 아이콘/썸네일로 간주)
                if len(r.content) < 10_000:
                    return None, None, 0, 0
                return base64.b64encode(r.content).decode('utf-8'), ct, 0, 0
    except Exception:
        pass
    return None, None, 0, 0


def match_images_semantically(slides, image_pool_metadata):
    """Gemini를 사용하여 슬라이드 내용과 가장 잘 어울리는 이미지를 매칭"""
    if not image_pool_metadata:
        return {}
    
    # 슬라이드 요약 정보 구성 (최대한 토큰 절약)
    slide_summaries = []
    for i, s in enumerate(slides):
        slide_summaries.append({
            "idx": i,
            "h": s.get('headline', '')[:40],
            "t": s.get('type', '')
        })
    
    # 이미지 메타데이터 요약
    image_summaries = []
    for i, img in enumerate(image_pool_metadata):
        image_summaries.append({
            "idx": i,
            "alt": img.get('alt', '')[:40],
            "ctx": img.get('context', '')[:60]
        })
    
    prompt = f"""
Assign the most relevant image index to each slide index from the pool.
Rules:
1. Match by semantic meaning (e.g., 'Service' slide -> image with project/work context).
2. NO REPETITION: Each image index is used ONLY ONCE.
3. If no image is a good fit for a slide, return null for that slide.
4. Output MUST be a single JSON object mapping slide index -> image index.

SLIDES: {json.dumps(slide_summaries, ensure_ascii=False)}
POOL: {json.dumps(image_summaries, ensure_ascii=False)}
"""

    try:
        # gemini-2.5-flash 사용
        resp = _client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        mapping = json.loads(resp.text)
        return {int(k): int(v) for k, v in mapping.items() if v is not None}
    except Exception as e:
        print(f"  이미지 시맨틱 매칭 실패: {e}")
        return {}


def capture_logo_transparent(url, logo_url=None):
    """
    1) 제공된 logo_url (SVG/PNG) 다운로드 + PIL 배경 제거 → base64 반환
    2) logo_url 없으면 페이지에서 헤더/푸터 중심으로 재탐색
    3) 모두 실패하면 Playwright 스크린샷 + 배경 제거
    """
    def remove_bg(img_bytes: bytes):
        """PIL로 로고 배경 투명화 → base64 PNG
        - 이미 투명도 있으면 그대로 반환 (손실 없음)
        - 없으면 4코너 색 감지 → 배경색과 가까운 픽셀만 제거 (로고 디테일 보존)
        """
        if not HAS_PIL:
            return None
        try:
            img = _PILImage.open(io.BytesIO(img_bytes)).convert('RGBA')
            W_img, H_img = img.size
            pixels = list(img.getdata())

            # 이미 유의미한 투명도가 있으면 그대로 반환
            if any(p[3] < 200 for p in pixels):
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                return base64.b64encode(buf.getvalue()).decode('utf-8')

            # ── 4코너 + 엣지 샘플로 실제 배경색 감지 ──
            corners = []
            for cx, cy in [(0, 0), (W_img-1, 0), (0, H_img-1), (W_img-1, H_img-1),
                           (W_img//2, 0), (0, H_img//2), (W_img-1, H_img//2), (W_img//2, H_img-1)]:
                corners.append(pixels[cy * W_img + cx][:3])

            # 코너 픽셀들의 평균색 → 배경색으로 채택
            bg_r = sum(c[0] for c in corners) // len(corners)
            bg_g = sum(c[1] for c in corners) // len(corners)
            bg_b = sum(c[2] for c in corners) // len(corners)
            bg_brightness = (bg_r * 299 + bg_g * 587 + bg_b * 114) // 1000

            # 배경이 중간 색조(복잡한 배경)면 배경 제거 포기 → 원본 반환
            # 흰(>220) 또는 검정(<35)인 경우만 제거
            if 35 <= bg_brightness <= 220:
                buf = io.BytesIO()
                img.save(buf, format='PNG')
                return base64.b64encode(buf.getvalue()).decode('utf-8')

            # ── 배경색과의 거리 기반 제거 (안티앨리어싱 소프트 알파 적용) ──
            TOLERANCE = 28   # 배경색과 이 거리 이내면 투명
            SOFT_BAND  = 50  # tolerance~soft_band 사이는 부드럽게 반투명

            new_data = []
            for r, g, b, a in pixels:
                dist = ((r - bg_r)**2 + (g - bg_g)**2 + (b - bg_b)**2) ** 0.5
                if dist <= TOLERANCE:
                    new_data.append((r, g, b, 0))
                elif dist <= SOFT_BAND:
                    # 소프트 엣지: 거리에 따라 선형 알파
                    alpha = int(255 * (dist - TOLERANCE) / (SOFT_BAND - TOLERANCE))
                    new_data.append((r, g, b, alpha))
                else:
                    new_data.append((r, g, b, a))

            img.putdata(new_data)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return base64.b64encode(buf.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"  PIL 배경 제거 오류: {e}")
            return None

    base_url = url.rstrip('/')

    def _download_logo(target_url, direct=False):
        """로고 URL 다운로드
        - direct=True (헤더/푸터 원본): SVG/PNG 가공 없이 그대로 반환 — 원본이 최고 품질
        - direct=False (폴백): PNG는 배경 제거 시도
        """
        try:
            r = requests.get(target_url, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                return None
            ct = r.headers.get('content-type', '')
            is_svg = target_url.lower().endswith('.svg') or 'svg' in ct

            # SVG는 항상 원본 그대로
            if is_svg:
                b64 = base64.b64encode(r.content).decode('utf-8')
                print(f"  → SVG 로고 원본 사용 ({len(b64)//1024}KB)")
                return b64

            # 헤더/푸터에서 찾은 PNG → 원본 그대로 사용 (remove_bg 없음)
            if direct:
                b64 = base64.b64encode(r.content).decode('utf-8')
                print(f"  → PNG 로고 원본 사용 ({len(b64)//1024}KB)")
                return b64

            # 폴백 경로: 배경 제거 시도 (og:image 등)
            if HAS_PIL:
                result = remove_bg(r.content)
                if result:
                    print(f"  → 로고 배경 제거 완료 ({len(result)//1024}KB)")
                    return result
            return base64.b64encode(r.content).decode('utf-8')
        except Exception as e:
            print(f"  → 로고 다운로드 실패: {e}")
            return None

    # ── STEP 1: extract_brand_assets가 찾은 logo_url — 헤더/푸터 원본 우선 ──
    if logo_url:
        result = _download_logo(logo_url, direct=True)
        if result:
            return result

    # ── STEP 2: 페이지에서 헤더/nav/푸터 중심으로 재탐색 (logo_url 미제공 시) ──
    logo_url_quick = None
    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')

            def _res2(src):
                if not src: return None
                src = src.strip()
                if src.startswith('http'): return src
                if src.startswith('//'): return 'https:' + src
                return base_url + '/' + src.lstrip('/')

            def _scan_el(el, strict=False):
                """엘리먼트에서 (svg_url, png_url) 추출"""
                if not el: return None, None
                sv = pn = None
                PNG_EXTS = ('.png', '.webp', '.jpg', '.jpeg')
                # <a class=logo> 안 img 우선
                for a in el.find_all('a'):
                    a_attrs = ' '.join([' '.join(a.get('class') or []), a.get('id',''), a.get('aria-label','')]).lower()
                    if 'logo' not in a_attrs and 'brand' not in a_attrs: continue
                    for img in a.find_all('img'):
                        src = img.get('src','') or img.get('data-src','') or img.get('data-lazy-src','')
                        full = _res2(src); fl = (full or '').lower()
                        if fl.endswith('.svg') and not sv: sv = full
                        elif not pn and any(fl.endswith(e) for e in PNG_EXTS): pn = full
                # 일반 img
                for img in el.find_all('img'):
                    attrs = ' '.join([' '.join(img.get('class') or []), img.get('id',''), img.get('alt',''), img.get('src','')]).lower()
                    src = img.get('src','') or img.get('data-src','') or img.get('data-lazy-src','')
                    full = _res2(src); fl = (full or '').lower()
                    has_kw = 'logo' in attrs or 'brand' in attrs
                    if has_kw:
                        if fl.endswith('.svg') and not sv: sv = full
                        elif not pn and any(fl.endswith(e) for e in PNG_EXTS): pn = full
                    elif not strict and not sv and fl.endswith('.svg'): sv = full
                # <picture><source>
                for pic in el.find_all('picture'):
                    for stag in pic.find_all('source'):
                        src = stag.get('srcset','').split()[0] if stag.get('srcset') else ''
                        full = _res2(src); fl = (full or '').lower()
                        if fl.endswith('.svg') and not sv: sv = full
                        elif not pn and any(fl.endswith(e) for e in PNG_EXTS): pn = full
                return sv, pn

            _HCLS = re.compile(r'(?:^|\b)(?:header|navbar|nav(?:bar)?|navigation|site-header|top-?bar|masthead)(?:\b|$)', re.I)
            _FCLS = re.compile(r'(?:^|\b)(?:footer|bottom-?bar|site-footer)(?:\b|$)', re.I)
            header_el = (soup.find('header') or soup.find(id=re.compile(r'header|navbar|navigation', re.I)) or
                         soup.find(class_=_HCLS) or soup.find('nav'))
            footer_el = (soup.find('footer') or soup.find(id=re.compile(r'footer', re.I)) or
                         soup.find(class_=_FCLS))

            svg_found = png_found = None
            # 헤더 → 나머지 nav → 푸터 → 전체(strict) 순
            svg_found, png_found = _scan_el(header_el)
            if not svg_found and not png_found:
                for nav in soup.find_all('nav'):
                    if nav is header_el: continue
                    svg_found, png_found = _scan_el(nav)
                    if svg_found or png_found: break
            if not svg_found and not png_found:
                svg_found, png_found = _scan_el(footer_el)
            if not svg_found and not png_found:
                svg_found, png_found = _scan_el(soup, strict=True)
            logo_url_quick = svg_found or png_found
    except Exception:
        pass

    if logo_url_quick:
        result = _download_logo(logo_url_quick, direct=True)
        if result:
            return result



# ────────────────────────────────────────────
# 2. JSON 생성 — 멀티 에이전트 파이프라인
#    A) Researcher  → Factbook (팩트 추출)
#    B) Strategist  → Storyline (목차 기획)
#    C) Formatter   → Slide JSON (카피 + 포맷)
# ────────────────────────────────────────────

# ── 2-A. 리서처 에이전트 프롬프트 ──────────────
RESEARCHER_SYSTEM_PROMPT = """\
당신은 B2B 영업 현장 경력 15년의 수석 어카운트 매니저입니다.
임무: 홈페이지 크롤링 원문에서 '회사소개서'를 만들기 위한 핵심 재료를 추출합니다.
원칙:
- 없는 내용은 절대 지어내지 않습니다. 데이터가 부족하면 '정보 없음'이라고 씁니다.
- 마케팅 미사여구는 제거하고 팩트(수치, 서비스명, 사례)만 추출합니다.
- 데이터 풍부도를 각 섹션별로 솔직하게 평가합니다.
- 같은 내용이 반복될 경우 유사어로 표현만 바꿀 수 있습니다. 의미나 사실을 변경·추가하는 것은 금지입니다."""

RESEARCHER_USER_TEMPLATE_C = """\
아래 크롤링된 텍스트에서 아티스트/크리에이티브 브랜드 소개서에 필요한 핵심 재료를 추출하세요.
항목별로 실제로 텍스트에 있는 내용만 작성하세요. 없으면 '정보 없음'이라고 쓰세요.

## 1. 아티스트/그룹 기본 정보
- 이름/그룹명, 데뷔 연도, 소속사/레이블
- 멤버 구성 (이름, 포지션 등 언급된 내용)
- 국적/출신, 활동 지역

## 2. 브랜드 콘셉트 및 아이덴티티
- 그룹/아티스트 콘셉트, 철학, 슬로건, 핵심 메시지
- 이름의 의미/유래 (있을 경우)
- 장르 및 음악적 특성

## 3. 디스코그래피 및 대표 작업
- 앨범명 (발매 연도 포함, 있을 경우)
- 대표곡, 히트곡
- 참여한 프로젝트, 콜라보 등

## 4. 성과 및 영향력
- 수상 경력, 차트 성과, 스트리밍 수치 등 구체적 수치 (있으면 추출)
- 글로벌 팬덤, 해외 활동 현황
- 주요 미디어 노출, 광고/브랜드 협업

## 5. 크리에이티브 특성
- 안무, 퍼포먼스 특징
- 뮤직비디오, 비주얼 콘셉트
- 아티스트가 직접 창작에 참여하는 방식 (작사/작곡/연출 등)

## 6. 데이터 풍부도 평가
각 항목을 0~3으로 평가 (0=없음, 1=빈약, 2=보통, 3=풍부):
- 콘셉트/아이덴티티: N
- 디스코그래피: N
- 성과/수치: N
- 멤버 정보: N
- 크리에이티브 특성: N

## 7. 핵심 수치·지표 (KPI 슬라이드용)
실제 언급된 멤버 수, 데뷔 연도, 앨범 수, 수상 수 등 숫자 (없으면 '정보 없음')
형식: "지표명: 수치" — 예) "멤버: 5명", "데뷔: 2022년", "앨범: 3장"

## 8. 주요 연혁·마일스톤
데뷔부터 주요 앨범 발매, 수상, 해외 진출 등 (없으면 '정보 없음')
형식: "YYYY: 사건명" — 최대 6개

━━━━ 크롤링 원문 ━━━━
{raw_info}"""

RESEARCHER_USER_TEMPLATE = """\
아래 크롤링된 텍스트에서 다음 항목을 정확히 추출하여 Markdown으로 정리하세요.
항목별로 실제로 텍스트에 있는 내용만 작성하세요. 없으면 '정보 없음'이라고 쓰세요.

## 1. 기업 기본 정보
설립 연도, 직원 수, 위치, 인증/수상, 인프라 수치 등

## 2. 핵심 서비스 및 역량
실제 제공 중인 서비스/솔루션 목록 + 차별점 (데이터에 있는 것만)
자체 개발 기술, 특허, 독자 플랫폼, 구체적 기술 스택

## 3. 증명 가능한 성과 및 수치
실제 고객 사례, 구체적 수치 (%, 건수, 금액, 기간)
없으면 '정보 없음' — 추측·추론 금지

## 4. 고객 Pain Point (핵심!)
이 회사의 서비스가 해결하는 고객의 실제 문제를 역추론하세요.
홈페이지에서 "이런 문제를 해결합니다", "~때문에 힘드셨나요?" 같은 표현이 있으면 추출.
없으면 서비스 유형으로 추론 가능한 B2B 공통 Pain Point 2-3가지를 자연스러운 문장으로 작성하세요.
(이 섹션은 내부 분석용 — Factbook에만 사용, 슬라이드 텍스트에 그대로 출력하면 안 됨)

## 5. 데이터 풍부도 평가
각 항목을 0~3으로 평가 (0=없음, 1=빈약, 2=보통, 3=풍부):
- 서비스 설명: N
- 성과/수치: N
- 고객 사례: N
- 팀/신뢰 정보: N
- 차별화 포인트: N

## 6. 핵심 수치·지표 (KPI 대시보드용)
실제 언급된 KPI, 성장률, 고객 수, 처리량, 규모 수치 등 구체적 숫자 (없으면 '정보 없음')
형식: "지표명: 수치 단위" — 예) "파트너사: 1,200곳", "누적 처리 건수: 50만 건", "연매출 성장률: 35%"
최대 6개까지 추출. 추측·추론 절대 금지.

## 7. 서비스 진행 프로세스 (단계별 절차)
실제 서비스 제공 방식, 고객과의 협업 단계, 방법론 절차 (없으면 '정보 없음')
형식: "1단계 → 2단계 → 3단계" (3~5단계, 각 단계는 10자 이내)
여러 프로세스가 있으면 대표 1개만 선택.

## 8. 팀·전문성 정보 (신뢰 근거)
핵심 인력 배경, 전문 분야, 보유 자격증·인증, 학력, 수상 경력 (없으면 '정보 없음')
추론 없이 홈페이지에 명시된 내용만.

## 9. 주요 연혁·마일스톤 (타임라인용)
설립 연도부터 주요 사건, 확장, 수상, 파트너십 등 연도순 (없으면 '정보 없음')
형식: "YYYY: 사건명" — 최대 6개

━━━━ 크롤링 원문 ━━━━
{raw_info}"""

# ── 2-B. 전략 기획자 에이전트 프롬프트 ──────────
STRATEGIST_SYSTEM_PROMPT = """\
당신은 회사소개서 기획 전문가입니다.
임무: Factbook을 보고 회사의 정체성·역량·성과를 효과적으로 전달하는 회사소개서 목차를 기획합니다.

핵심 원칙:
- 슬라이드 순서 = 독자의 이해 여정 (회사 이해 → 역량 확인 → 협업 기대)
- 단순 나열이 아닌 스토리가 있는 소개 흐름
- 데이터가 없는 선택적(?) 슬라이드는 삽입하지 말 것 — 단, 각 TYPE의 필수 슬라이드는 반드시 포함
- 총 슬라이드는 최소 7개 이상 (C-type: 필수 7개 + 선택 최대 2개)

━━ STEP 1: 회사 유형 분류 ━━

판단 기준: 주요 수익 모델로 판단.

A (Tech·SaaS·디지털솔루션·에이전시):
  → SaaS, IT컨설팅, AI/데이터 플랫폼, 마케팅에이전시, 핀테크, 에듀테크
  → 판단 신호: 소프트웨어/플랫폼 판매, 디지털 서비스 제공, 프로젝트 납품
  → 예) B2B SaaS, 마케팅대행사, AI솔루션, 데이터분석, IT아웃소싱

B (제조·인프라·엔터프라이즈):
  → 제조, 건설, 중공업, 에너지, 대형 SI, 물류(자산 기반)
  → 판단 신호: 공장·설비·현장, 수주/도급, 자산 집약적 사업, 대규모 B2G
  → 예) 자동화 제조, 플랜트 시공, 통신 인프라, 반도체 장비

C (크리에이티브·에이전시·포트폴리오·엔터테인먼트):
  → 광고, 영상제작, 브랜딩, 건축설계, UX/UI 에이전시
  → 음악레이블, 엔터테인먼트, 연예기획사, 아티스트 매니지먼트, 스포츠 구단, 패션
  → 판단 신호: 포트폴리오·작업물·아티스트·앨범·공연이 핵심 증거, 프로젝트/릴리즈 단위 성과
  → 예) 광고대행사, 브랜드 컨설팅, 영상 프로덕션, K팝 레이블, 연예기획사, 스포츠 구단

D (B2C·라이프스타일·브랜드):
  → 소비재, 이커머스, F&B, 헬스케어(B2C), 뷰티, 소비자앱
  → 판단 신호: 최종 소비자가 고객, 감성·경험이 구매 동기
  → 예) 쇼핑몰, 식품브랜드, 소비자앱

E (플랫폼·에코시스템):
  → 마켓플레이스, 투사이드 플랫폼, AI 인프라, 슈퍼앱
  → 판단 신호: 공급자↔소비자 양면 네트워크, 파트너 생태계가 핵심 가치

F (교육·연구·전문서비스):
  → 에듀테크, 교육기관, 연구소, 법무/회계/컨설팅, 의료B2B, 채용/HR
  → 판단 신호: 지식·전문성·자격이 핵심 상품, 커리큘럼·방법론·인증이 주요 근거
  → 예) 기업교육, 온라인 학습플랫폼, 경영컨설팅, 채용대행, 연구개발 서비스

혼재 시:
  B2B SaaS + 크리에이티브 → A
  포트폴리오·작업물이 핵심 → C
  엔터테인먼트·음악레이블·연예기획사·스포츠 구단 → C (무조건)
  소비자 직판·감성 소비 → D
  지식/전문성이 핵심 상품 → F
  판단 불가 → A

━━ STEP 2: 회사소개서 슬라이드 흐름 ━━

[공통 원칙] 모든 타입은 고객의 Pain에서 시작해서 CTA로 끝남.

TYPE A (Tech·SaaS·에이전시):
  cover → market_challenge → pain_analysis → solution_overview → how_it_works
  → [key_metrics?] → proof_results → [why_us?] → cta_session → contact
  ※ 수치 3개+ → key_metrics 포함 / 수치 없으면 생략

TYPE B (제조·인프라):
  cover → market_challenge → pain_analysis → solution_overview → scale_proof
  → [key_metrics?] → [case_study?] → delivery_model → cta_session → contact
  ※ 인프라 규모 수치 풍부하면 key_metrics 포함

TYPE C (크리에이티브·포트폴리오·엔터):
  ※ 엔터테인먼트·음악레이블·연예기획사·스포츠·아티스트 계열:
    cover → brand_story → creative_approach → showcase_work_1 → showcase_work_2? → key_metrics? → proof_results → cta_session → contact
    pain_analysis 생략. brand_story로 정체성·아티스트·세계관 확립.
    ⚠️ C-type 필수 7개 (데이터 부족해도 반드시 포함):
       cover, brand_story, creative_approach, showcase_work_1, proof_results, cta_session, contact
       → showcase_work_2, key_metrics만 데이터 기준으로 선택적 추가
  ※ B2B 크리에이티브·광고·에이전시 계열:
    cover → market_challenge → pain_analysis → creative_approach → showcase_work_1 → showcase_work_2? → client_list? → proof_results → cta_session → contact
    레퍼런스 3개 이상이면 client_list 포함

TYPE D (B2C·브랜드):
  cover → [brand_story?] → market_challenge → pain_analysis → solution_overview
  → flagship_experience → [key_metrics?] → proof_results → cta_session → contact
  ※ 강한 브랜드 스토리 있으면 brand_story 두 번째에 삽입

TYPE E (플랫폼):
  cover → market_challenge → dual_sided_value → solution_overview
  → scalability_proof → [key_metrics?] → [ecosystem_partners?] → cta_session → contact

TYPE F (교육·연구·전문서비스):
  cover → market_challenge → pain_analysis → solution_overview → our_process
  → [key_metrics?] → [team_credibility?] → proof_results → cta_session → contact
  ※ 팀 전문성 데이터 풍부 → team_credibility 포함 / 프로세스 필수

━━ STEP 3: 목차 확정 규칙 ━━
- ⚠️ 슬라이드 수 절대 규칙: 최소 7개, 목표 9개. 5개 미만이면 반드시 필수 슬라이드를 추가해서 채울 것.
- 총 슬라이드 7~9개 (최소 7개 필수. 데이터 부족해도 필수 슬라이드는 업종 공통 내용으로 채울 것)
- [] 옵션 슬라이드: Factbook 데이터 풍부도 2 이상일 때만 포함
- 데이터 풍부도 0~1인 옵션(?) 슬라이드 타입만 생략 — 필수 슬라이드는 절대 생략 불가
- ⚠️ C-type: cover, brand_story, creative_approach, showcase_work_1, proof_results, cta_session, contact는 무조건 포함 (7개 필수)
- 각 topic은 30자 이내 한국어로, 해당 슬라이드의 핵심 소개 메시지를 명시
- section_divider: 9개 이상일 때만, 최대 1개

[레이아웃 다양성 원칙] — 중요
- 연속 2개 이상 같은 성격의 슬라이드(순수 텍스트만) 배치 시, 중간에 시각 중심 슬라이드 삽입
- market_challenge와 pain_analysis는 반드시 연속 배치. 단, 내용은 서로 다른 레벨: market_challenge=시장/구조 문제, pain_analysis=고객 일상의 Pain
- 동일 타입 슬라이드(예: service_pillar_1/2/3)는 최대 2개까지만 연속 배치
- 수치 데이터 2개+ 있으면 반드시 key_metrics 포함 (stat 레이아웃 활용) — 가능하면 3개 이상 확보
- 단계/절차 데이터 있으면 how_it_works 또는 our_process 포함 (process 레이아웃 활용)
- 연혁 데이터 3개+ 있으면 company_history 슬라이드 고려 (timeline 레이아웃 활용)

[데이터 부족 시 처리 규칙]
- 성과 수치 없음 → proof_results는 Before/After 포맷으로 작성 (수치 필수 아님)
- 사례 없음 → how_it_works + delivery_model로 신뢰 대체
- 시장 데이터 없음 → market_challenge는 해당 업종의 공통 이슈로 자연스럽게 작성 (메타 레이블 출력 금지)
- 수치 1개 이하 → key_metrics 생략, proof_results에 통합 (수치 2개부터 key_metrics 포함)
- C-type 아티스트/엔터 데이터 부족 → brand_story에 아티스트 정체성·콘셉트, creative_approach에 음악/활동 방식, showcase_work_1에 대표 앨범/작품, proof_results에 공연·음원 성과 작성 (수치 없어도 포함)

[출력] 아래 JSON 객체만 반환. 마크다운 없이.
{"narrative_type": "A", "slides": [{"slide_num":1,"type":"cover","topic":"..."}, ...]}"""

# ── 2-C. 포맷터(카피라이터) 시스템 프롬프트 ──────
SLIDE_SYSTEM_PROMPT = """당신은 회사소개서 전문 카피라이터입니다.
임무: Factbook과 Storyline을 바탕으로 회사의 정체성·역량·성과를 명확하고 설득력 있게 전달하는
슬라이드 JSON을 작성합니다.

핵심 관점: 독자가 회사를 명확히 이해하고 신뢰할 수 있도록 쓰세요.
- "저희 회사는 다양한 서비스를 제공합니다" (X)  ← 모호하고 평범
- "우리가 해결하는 문제, 우리만의 방식, 실제 성과로 증명" (O)  ← 구체적이고 인상적

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
콘텐츠 생성 철학
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⭐ 내용이 많으면 편집할 수 있지만, 없으면 쓸 수 없습니다.
   크롤링 데이터에서 추출 가능한 모든 가치 있는 내용을 최대한 담으세요.
   bullet 수, 설명 길이, 수치 — 모두 허용 범위 내 최대로 작성하는 것이 기본입니다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
카피 원칙 — 모든 슬라이드에 적용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
① Headline = 결론 (Bottom Line Up Front)
   BAD:  "서비스 소개" / "우리의 강점"
   GOOD: "3가지 Pain을 동시에 제거하는 유일한 방법" / "도입 기업 92%가 재계약하는 이유"

   ⚠️ RULE I (헤드라인 길이 제한 — 절대 규칙):
   headline은 반드시 22자 이내. 초과 시 가장 핵심 결론만 남기고 자르세요.
   22자가 넘으면 슬라이드 화면에서 줄바꿈이 생겨 임팩트가 사라집니다.
   BAD:  "AARRR 프레임워크 기반 5단계 그로스 해킹 전략" (25자)
   GOOD: "AARRR 그로스 해킹 전략" (11자)
   BAD:  "AI 기반 마케팅 자동화로 비용 35% 절감하는 방법" (24자)
   GOOD: "AI로 광고비 35% 절감" (11자)
   ※ 수치·키워드 등 핵심 임팩트는 subheadline에 풀어서 쓰세요.

② Subheadline — cover/contact 제외한 모든 슬라이드에 ⚠️ 필수 작성
   headline을 보완하는 1-2문장. 맥락·배경·핵심 가치를 추가.
   GOOD: "전략-데이터-퍼포먼스-CRM을 유기적으로 연결합니다"
   GOOD: "단기간에 달성한 비약적인 성과"
   ⚠️ 크롤링 데이터가 전혀 없어 쓸 말이 없는 경우에만 생략 — 기본은 반드시 포함.

   ⚠️ RULE J (수량 일관성 — 절대 규칙):
   headline에 숫자가 포함된 경우(예: "5단계", "3가지", "4개") body bullets 수가 반드시 일치해야 합니다.
   "5단계 프로세스" → body 5개 필수 / "3가지 핵심" → body 3개 필수
   bullets 수가 부족하면 headline의 숫자를 실제 bullets 수에 맞춰 수정하거나 숫자를 제거하세요.

③ 모든 bullet = 고객이 얻는 결과로 끝내기
   BAD:  "클라우드 기반 인프라 구축"
   GOOD: "클라우드 전환 → 운영비 35% 절감, 배포 주기 3배 단축"
   수치 없으면: "→ 의사결정 속도 구조적 개선" (방향성으로 대체)
   ⚠️ bullet 설명은 충분히 길게 — "짧은 키워드" 수준 금지. 원인 + 과정 + 결과를 모두 담을 것.

④ 수치 우선 — 크롤링 데이터에 있으면 반드시 사용
   수치 없으면: "업계 평균 대비", "도입 전/후", "Before → After" 포맷 사용

⑤ MECE — 같은 내용 중복 금지 (슬라이드 내 + 슬라이드 간)
   각 bullet은 서로 다른 가치를 전달해야 함
   인접 슬라이드 bullet 주제 중복 금지:
   solution_overview(WHAT) ≠ how_it_works(HOW) — 서비스명 반복 금지, 관점 구분 필수
   proof_results ≠ why_us — 같은 수치·사례 재사용 금지

⑥ Bullet 수 — 크롤링 데이터 양에 맞게 2-6개 범위 내에서 자유롭게 작성
   데이터가 많으면 6개까지, 적으면 2개도 허용 — 슬라이드 유형별 지침 참고
   ※ 7개 이상은 금지 (가독성 저하)

⚠️ 데이터 충실 원칙 (가장 중요한 규칙):
   ▶ 홈페이지 크롤링 데이터에 있는 내용만 사용
   ▶ 없는 서비스·수치·사례·절차·약속을 절대 지어내지 마세요
   ▶ 같은 내용이 반복될 때만 유사어로 표현을 바꿀 수 있습니다 (의미 변경 금지)
   ▶ "~할 수 있습니다", "~입니다" 수준의 일반론도 크롤 데이터 근거 없으면 금지
   ▶ 위반 예시: "즉시 대응", "맞춤형 솔루션", "30분 안에", "업계 최고", "검증된"
      (이런 표현은 크롤 데이터에 실제로 있을 때만 사용 가능)
   ▶ 단, 업종 공통 Pain/시장 현황은 추론 허용 (RULE G에 따라 자연스럽게 서술)

⚠️ RULE G (메타 레이블 출력 금지): "[추론]", "[업계 동향]", "[정보 없음]" 등 내부 작성 지침용 태그는
   절대 최종 JSON에 포함하지 마세요. 이는 Gemini 내부 판단용이며 슬라이드에 출력되면 안 됩니다.
   데이터가 추론 기반이라도 자연스러운 업계 문장으로 작성하세요.
   WRONG: "[추론] 채널별 데이터 분리: 분석 불가"
   RIGHT: "채널별 데이터 분리: 통합 분석 불가 → 예산 낭비 고착"

⚠️ RULE H (바디 품질 기준): 모든 bullet은 아래 기준을 충족해야 합니다
   ① 구체성: "무엇이" + "어떻게 되는지" + "결과가 무엇인지" 3요소 포함 (2요소 이하 금지)
   ② 결과: bullet 끝에 고객이 겪는 실제 결과 명시 (→ 결과, 또는 콜론 뒤 결과)
   ③ 독립성: 같은 덱 안의 다른 bullet과 중복 금지
   ④ 길이: 최소 15자 이상 — "비용 절감" 같은 키워드 수준 단독 사용 금지
   WRONG: "마케팅 효율이 떨어집니다" / "비용이 증가합니다"
   RIGHT: "채널 분산 운영: 캠페인별 성과 비교 불가 → 고비용 채널 유지 반복, 낭비 구조 고착"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
컨설턴트 문체 원칙 (McKinsey·BCG 스타일)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
당신은 전략 컨설턴트처럼 씁니다. 아래 원칙을 모든 슬라이드에 적용하세요.

⚠️ 전제 조건 (최우선 규칙): 컨설턴트 문체는 표현 방식입니다. 내용 자체는 반드시 크롤링 데이터 근거가 있어야 합니다.
   데이터 없는 수치·사례·약속을 컨설턴트처럼 단언하는 것이 가장 심각한 위반입니다.
   WRONG: 크롤링에 없는 "납기 40% 단축"을 단언 → 데이터 날조
   RIGHT:  크롤링에 있는 "납기 3주"를 → "납기를 3주로 단축합니다"로 단언

【원칙 1】 피라미드 구조 — Headline이 결론, body가 증거
   슬라이드를 읽지 않고 headline만 봐도 핵심 메시지를 완전히 이해할 수 있어야 합니다.
   body bullets는 headline의 주장을 증명하는 독립 근거들입니다.
   WRONG: headline "우리의 차별점" → body "빠른 납기 / 좋은 품질 / 합리적 가격"
   RIGHT:  headline "납기 단축 40% · 불량률 0.1% 이하" → body [납기·품질·비용 각각 수치 근거]

【원칙 2】 "So What?" 테스트 — 모든 bullet은 고객 임팩트로 끝내기
   컨설턴트는 모든 문장을 쓴 뒤 "그래서 고객에게 무슨 의미인가?"를 자문합니다.
   WRONG: "글로벌 파트너십을 보유하고 있습니다"
   RIGHT:  "글로벌 파트너십 → 조달 리드타임 3주 → 1주로 단축, 재고 부담 62% 감소"

【원칙 3】 단언형 문장 — 불확실 표현 금지
   컨설턴트는 주저하지 않습니다. 데이터가 있으면 단언하고, 없으면 쓰지 않습니다.
   WRONG: "향상될 수 있습니다", "개선이 기대됩니다", "도움이 될 것입니다"
   RIGHT:  "향상됩니다", "개선합니다", "해결합니다"
   ※ 크롤 데이터 근거 없으면 단언 대신 삭제 (RULE H 적용)

【원칙 4】 병렬 구조 — body bullets의 문법 형식 통일
   같은 슬라이드의 모든 bullet은 동일한 문법 패턴을 사용해야 합니다.
   WRONG (혼재): "비용 절감 가능" / "납기를 단축합니다" / "품질 관리"
   RIGHT  (명사형): "조달비 18% 절감" / "납기 3주 단축" / "불량률 0.1% 이하 유지"
   RIGHT  (동사형): "비용을 18% 절감합니다" / "납기를 3주 단축합니다" / "불량을 원천 차단합니다"

【원칙 5】 구조적 언어 — 컨설턴트 어휘 적극 활용
   아래 표현을 상황에 맞게 사용하세요. 단, 데이터 근거 없으면 사용 금지.
   · 레버리지 포인트 / 핵심 동인 / 구조적 병목 / 선제적 대응
   · 단계적 전환 / 통합 운영 체계 / 가시성 확보 / 의사결정 가속
   · 비용 구조 개선 / 수익성 회복 / 실행력 강화 / 스케일업

【원칙 6】 Issue → Evidence → Implication 흐름
   슬라이드 전체(deck)가 하나의 컨설팅 보고서처럼 흘러야 합니다.
   시장 이슈 → 고객 Pain 진단 → 솔루션 처방 → 실행 근거 → 성과 증명 → 행동 촉구

⚠️ RULE F (CTA 약속 금지): cta_session headline/body에 홈페이지 미확인 약속 절대 금지
   - 시간 약속 금지: "X분 안에", "즉시", "당일 내", "빠른 시일 내"
   - 수치 약속 금지: "X% 절감", "X배 향상" — 크롤 데이터에 없는 경우
   - 과정 약속 금지: 홈페이지에 없는 상담 단계/프로세스 묘사
   - 홈페이지에 상담 서비스가 명시되지 않았으면 "상담" 대신 "문의"로 대체

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
슬라이드 수: 8~10개 (데이터가 풍부하면 10개 적극 활용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[공통 필수] COVER + CTA + CONTACT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[REQUIRED] type: "cover"  [항상 첫 번째]
  PURPOSE: 로고 + 회사명 + 강렬한 포지셔닝 한 문장. 텍스트 최소화.
  headline: 회사명 (정확한 브랜드명)
  subheadline: 고객의 Pain을 암시하는 포지셔닝 라인. Max 25자.
               ⚠️ 반드시 완결된 문장으로 작성할 것. "~에", "~는", "~의" 등 조사·관형어로 끝나는 미완성 문장 금지.
               GOOD: "마케팅 비용을 낭비 없이 성과로 바꿉니다"
               GOOD: "매출이 멈춘 비즈니스에, 데이터로 돌파구를 만듭니다"
               BAD:  "종합 마케팅 서비스를 제공합니다"
               BAD:  "성장 정체를 겪는 당신의 비즈니스에" ← 문장 미완성 금지
  body: []  ← 반드시 비워둘 것
  infographic: {"type": "none", "data": {}}

[REQUIRED] type: "cta_session"  [항상 마지막에서 두 번째]
  PURPOSE: 구체적이고 가치 중심적인 다음 단계 제안. "연락주세요" 금지.
  headline: 고객이 받는 것을 중심으로 — 따옴표 없이 직접 서술
            GOOD: "[회사명]의 [핵심서비스]로 귀사에 맞는 도입 방안을 함께 설계합니다"
            GOOD: "지금 겪고 있는 [Pain Point], [회사명]과 함께 해결 방법을 찾아보세요"
            BAD:  "문의하시면 빠르게 답변드리겠습니다"
            BAD:  "30분 안에 개선 우선순위를 제시합니다" ← 시간 약속 금지 (RULE F)
            ⚠️ 홈페이지에 없는 시간 약속·수치 약속·무료 제안 절대 금지
  subheadline: 고객의 현재 상황 공감 + 첫 걸음의 가벼움 강조 (선택)
               GOOD: "귀사의 마케팅 현황을 함께 살펴보고 데이터 기반의 방향을 제시합니다"
               ⚠️ subheadline에도 RULE F 동일 적용 — 없는 서비스·약속 금지
  body: 2-3 bullets — 홈페이지에 실제 존재하는 서비스/절차만 기술
        없는 내용이면 생략. "문의 없이도 사이트에서 확인 가능" 같은 대안 허용
  infographic: {"type": "none", "data": {}}

[REQUIRED] type: "contact"  [항상 마지막]
  PURPOSE: 연락처 + 마무리 문장.
  RULE: 크롤링 데이터에 있는 연락처만 사용. 없으면 웹사이트 URL만.
  headline: 짧은 마무리 문장 (예: "지금 바로 시작할 준비가 되어 있습니다")
  body: 크롤링 데이터의 실제 연락처. Max 4줄.
  infographic: {"type": "none", "data": {}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[회사소개서 핵심 슬라이드 — TYPE A/B/C/D/E 공통 사용 가능]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SLIDE] type: "market_challenge"  [시장 위기 — 공감 유발]
  PURPOSE: 이 회사의 서비스가 해결하는 바로 그 문제가 왜 지금 이 시장에서 심각한지 보여주기.
           "맞아, 나도 이 문제로 돈 날리고 있어"라는 반응을 이끌어내야 한다.
           ⚠️ 일반적인 시장 트렌드 나열 금지 — 이 회사의 서비스와 직접 연결되는 문제여야 한다.
  RULE: 크롤링 데이터에서 이 회사가 해결하는 Pain을 파악하고, 그 Pain이 왜 지금 커지고 있는지 시장 맥락으로 설명
        데이터 없으면 업종 공통 이슈로 작성 (메타 레이블 출력 금지 — RULE G)
  headline: [업종] + [이 회사 서비스와 연결된 구조적 문제] — 임팩트 있게
            GOOD (마케팅사): "AI 도구 300개 시대, 전략 없는 집행이 광고비를 소각하고 있다"
            GOOD (건설): "자재비 43% 급등 · 인력 부족 — 수주해도 수익이 남지 않는 구조"
            GOOD (SaaS): "도입만 하고 쓰지 않는 B2B SaaS — 활성화 실패가 해지율을 만든다"
            BAD: "시장이 변화하고 있습니다" / "좋은 아이디어가 주목받지 못합니다" (이 회사와 무관한 일반론)
  subheadline: 이 위기가 고객에게 미치는 직접적 손실 한 줄 (15-25자) — 슬라이드에 크게 표시되므로 핵심만
  body: 2-6 bullets (데이터 양에 맞게) — FORMAT: "시장 변화 원인: 고객이 실제로 입는 손실"
        ① 콜론(:) 필수 — 파서가 좌(원인)/우(결과)로 분리 표시함
        ② 각 bullet은 이 회사의 핵심 서비스가 해결하는 Pain과 직결될 것
        ③ 다음 슬라이드(pain_analysis)의 고객 Pain으로 자연스럽게 이어질 것
        수치/비율 포함 권장. 없으면 "→ 결과" 구조 사용.
        GOOD: "광고 채널 파편화: 성과 비교 불가 → 고비용 채널 유지 반복, 낭비 구조 고착"
        GOOD: "AI 도구 난립: 전략 없이 도구만 늘어나 비용 증가, 통합 지표 측정 불가"
        GOOD: "경쟁사 진입 가속: 차별화 없는 브랜드는 가격 경쟁에 내몰려 마진 소실"
        GOOD: "내부 역량 공백: 기획·전략 인력 부재로 외주 비용만 증가, 일관성 없는 방향"
        BAD:  "경쟁이 심화됩니다" / "좋은 서비스가 알려지지 않습니다" (이 회사와 무관, 콜론 없음)
  infographic: "none"

[SLIDE] type: "pain_analysis"  [고객 Pain 진단]
  PURPOSE: 잠재 고객이 매일 겪는 구체적인 문제 4가지. "이 회사가 나를 이해한다"는 느낌.
  RULE: 크롤링 데이터에서 역추론. 데이터 없으면 업종 공통 Pain 사용 (메타 레이블 출력 금지 — RULE G)
  headline: 고객의 핵심 문제를 진단하는 문장 (질문형 또는 인사이트형)
            GOOD: "비용은 늘어나는데, 성과는 왜 제자리인가"
            GOOD: "측정되지 않는 것은 개선될 수 없습니다"
            GOOD: "지금 이 상황, 우리만 겪는 게 아닙니다"
            BAD:  "고객이 겪는 어려움" (추상적)
  subheadline: 4가지 Pain을 관통하는 메타 문장 또는 더 구체적인 설명 (15-25자, 선택)
               GOOD: "데이터 기반 성장이 어려운 4가지 핵심 원인"
               GOOD: "오늘도 반복되는 비효율, 이제 이유를 직시할 때입니다"
  body: 2-6 bullets (데이터 양에 맞게) — FORMAT: "문제 원인: 매일 겪는 구체적 결과" (콜론 + 결과 필수)
        각 bullet은 서로 다른 Pain 영역 커버 (중복 금지)
        설명은 충분히 길게: "원인: 직접적 결과 → 2차 손실" 구조 권장
        GOOD: "채널별 데이터 분리: 통합 고객 분석 불가 → 고비용 채널 유지 반복"
        GOOD: "의사결정 지연: 현장 데이터가 경영진에 도달하는 데 2주 이상 소요"
        GOOD: "외주 의존 구조: 전략 수정 시마다 추가 비용 발생 → 기민한 대응 불가"
        BAD:  "마케팅이 어렵습니다" / "[추론] 데이터 부족" (RULE G·H 위반)
  infographic: "funnel" (pain이 단계적으로 심화될 때) or "none"

[SLIDE] type: "solution_overview"  [해결책 제시]
  FOCUS: WHAT — 어떤 서비스/기능을 제공하는가. how_it_works(HOW)와 중복 금지 — 서비스명 반복 없이 관점 구분.
  PURPOSE: pain_analysis의 각 Pain에 직접 대응하는 우리의 해결책. "바로 이게 답이구나"라는 순간.
  headline: Pain → Solution 연결을 담은 선언문
            GOOD: "4가지 문제를 하나의 통합 솔루션으로 해결합니다"
  subheadline: 핵심 가치 제안 한 줄
  body: 2-6 bullets (서비스 수에 맞게) — FORMAT: "[icon] 서비스명: 구체적 해결 방식 + 고객에게 돌아오는 효과"
        GOOD: "[target] 그로스 전략: 시장·고객·경쟁 분석 기반 단계별 성장 로드맵 설계"
        GOOD: "[database] 데이터 환경: 광고·매출·고객 데이터를 통합 대시보드로 한눈에 파악"
        BAD:  "시장·고객·트렌드 분석 기반으로 명확한 성장 전략을 기획합니다" (서비스명 라벨 없음)
  infographic: "venn" (2-3개 핵심 역량 교집합) or "none"

[SLIDE] type: "problem_solution"  [문제-해결 대조 한 페이지]
  USE WHEN: pain_analysis + solution_overview의 내용이 1:1 대응 쌍을 이룰 때.
            즉, 각 문제에 직접 매핑되는 해결책을 3-4쌍 나열할 수 있을 때만 사용.
            내용이 병렬 대조를 이루지 않으면 pain_analysis / solution_overview를 각각 사용할 것.
  PURPOSE: 왼쪽에 문제, 오른쪽에 우리 회사의 해결책을 나란히 보여줌.
           회사의 강점이 오른쪽 패널에 돋보이도록 구성.
  headline: "문제와 해결을 한눈에" 형식의 선언 문장. 회사명 또는 서비스명 포함 권장.
            GOOD: "[회사명]이 바꾸는 4가지 현실"
            GOOD: "지금의 불편, [서비스명]으로 해결합니다"
  before:
    label: "현재" | "문제" | "AS-IS" 중 맥락에 맞는 것 (2~4자)
    points: 3-4개 — FORMAT: "문제 핵심어: 구체적 결과" (콜론 필수, 짧고 임팩트 있게)
            GOOD: "분산 채널: 통합 관리 불가, 매월 3시간 수작업"
            GOOD: "느린 의사결정: 현장→경영진 리포팅 14일 소요"
  after:
    label: "해결" | "변화" | "TO-BE" 중 맥락에 맞는 것 (2~4자)
    points: 3-4개 — before.points와 동일 순서로 1:1 대응 (대조가 명확히 보이도록)
            FORMAT: "해결책명: 구체적 효과" (콜론 필수)
            GOOD: "통합 대시보드: 채널 데이터 실시간 단일 화면"
            GOOD: "자동 리포팅: 당일 현황 공유, 전략 집중 가능"
  subheadline: (선택) 전환을 요약하는 짧은 한 줄
  infographic: "none"

[SLIDE] type: "how_it_works"  [작동 방식 / 프로세스]
  FOCUS: HOW — 어떻게 작동/실행되는가 (절차·단계·프로세스). solution_overview와 중복 금지 — 서비스 목록 재나열 금지.
  PURPOSE: 실제로 어떻게 일하는지 보여주는 단계별 프로세스. 예측 가능성과 전문성 증명.
  RULE: 실제 프로세스만 기술. 가짜 브랜드명(™) 금지. 크롤링 데이터 기반.
  headline: 단계 수를 명시한 프로세스 설명 — 반드시 body bullets 수와 일치시킬 것
            GOOD: "3단계로 완성되는 [서비스명] 프로세스" (body 3개일 때)
            GOOD: "5단계로 완성되는 [서비스명] 프로세스" (body 5개일 때)
            BAD:  "6단계로 완성되는 [서비스명] 프로세스" (body가 5개인데 6단계 언급 → 불일치 금지)
            BAD:  "[회사명] Growth-Loop™ Engine" (가짜 브랜딩 금지)
  body: 3-5 bullets — 각 단계 + 고객이 받는 결과물 (headline의 N과 반드시 일치)
  infographic: "flowchart" REQUIRED (3-5 steps, body 수와 동일하게)

[SLIDE] type: "proof_results"  [성과 증명]
  FOCUS: 구체적 수치·증거 — 앞 슬라이드(solution_overview, how_it_works)에 나온 내용 재사용 금지.
  PURPOSE: 실제 성과/수치. 없으면 Before → After 포맷.
  RULE A (수치 있고 key_metrics 없을 때): 수치를 infographic stat으로 표시. 크롤링 데이터만 사용.
  RULE B (수치 있고 key_metrics도 있을 때): ⚠️ infographic은 반드시 "none" 사용.
          key_metrics가 이미 수치를 보여줬으므로, proof_results는 "어떻게 달성했는가" HOW 스토리로 작성.
          body FORMAT: "[고객사/상황]: [무엇을 바꿨는지 — 핵심 액션] → [기간] 만에 [결과]"
          GOOD: "A 브랜드: 비효율 채널 진단 후 고성과 채널 집중 → 5주 만에 ROAS 10배·매출 20배"
          GOOD: "B 브랜드: 고객 세그먼트 재설계 + CRM 개인화 도입 → 13주 만에 재구매율 3배"
  RULE C (수치 없을 때): 변화 영역별 Before→After를 1줄에 담되, 반드시 고유한 토픽명을 heading으로 사용할 것.
          FORMAT: "[변화 영역명]: [도입 전 상황] → [도입 후 결과]"
          GOOD: "팬덤 연결: MZ세대 도달 불가·인지도 정체 → 아티스트 협업으로 직접 유입·급상승"
          GOOD: "브랜드 신뢰도: 일방적 광고로 공감대 부재 → 진정성 콘텐츠로 신뢰도 대폭 향상"
          BAD: "도입 전: ... → 도입 후: ..." (모든 항목이 '도입 전'으로 시작 — 금지)
  headline: 변화/성과를 선언하는 문장. key_metrics와 동일하거나 유사한 headline 금지 — 다른 각도로 작성.
            GOOD (key_metrics 있을 때): "어떻게 가능했을까 — 성과의 배경"
            GOOD (key_metrics 없을 때): "숫자로 증명하는 [회사명]의 성과"
  subheadline: 결과 이면의 접근법 또는 핵심 성공 요인 한 줄 (선택)
               GOOD: "데이터로 발견한 기회, 시스템으로 만든 결과"
  body: 3-5 bullets — 단순 수치 나열이 아닌, 고객사별 상황·행동·결과를 스토리 형태로 작성 권장
        수치가 있을 때도 "무엇을 바꿨기에 이 결과가 나왔는가"를 한 문장에 담을 것
        GOOD: "A 브랜드: 비효율 채널 진단 후 고성과 채널 집중 → 5주 만에 ROAS 10배·매출 20배"
  infographic: RULE A/B/C에 따라 결정 ("stat" or "none")
  quote: (선택) 짧은 고객 인용문 20자 이내. 실제 크롤링 데이터에 고객 후기/인용이 있을 때만 추가. 없으면 필드 생략.

[SLIDE] type: "why_us"  [선택 이유 — 차별화]
  PURPOSE: "경쟁사 말고 왜 우리인가"를 명확히. 3가지 Unfair Advantage.
  INCLUDE IF: 데이터에서 차별화 포인트가 명확할 때
  SKIP IF: 차별화 근거가 크롤링 데이터에 없을 때
  headline: 우리만의 경쟁 우위를 담은 선언 (단순 대행/서비스 소개가 아닌 파트너십 각도 권장)
            GOOD: "단순 대행이 아닙니다, 성장을 함께 만드는 파트너입니다"
            GOOD: "3가지 이유 — 선택받는 파트너의 조건"
  subheadline: "우리가 다른 N가지 이유" 형식 또는 차별점 총괄 한 줄 (선택)
               GOOD: "우리가 다른 3가지 이유"
  body: 3 bullets — FORMAT: "[icon] 차별화포인트: 구체적 근거 + 고객에게 돌아오는 효과"
        핵심: 경쟁사도 쓸 수 있는 일반론 금지. 크롤링 데이터 기반 구체적 근거 필수.
        GOOD: "[layers] 풀스택 통합 실행: 전략 수립부터 광고 운영·분석까지 원스톱 — 내부 팀처럼 일합니다"
        GOOD: "[activity] 데이터 과학 기반: RFM·코호트 분석으로 성장 기회를 수치로 발굴"
        BAD:  "전문성: 오랜 경험을 바탕으로 최선을 다합니다" (일반론, 근거 없음)
  infographic: "none"

[SLIDE] type: "case_study"  [실제 사례]
  PURPOSE: 구체적 고객 사례 1건 deep-dive. 신뢰도 최고의 증거.
  INCLUDE ONLY IF: (a) 고객 업종/상황 명확 + (b) 구체적 문제 기술 + (c) 수치/기간 포함 결과
                   셋 중 하나라도 없으면 → SKIP
  headline: 케이스 포지셔닝 헤드라인 (클라이언트명 X, 상황/결과 O)
  subheadline: 핵심 결과 한 줄 (예: "6개월 만에 전환율 3배, 광고비 40% 절감")
  body: 3-6 bullets — [상황] → [문제] → [해결] → [결과] 구조 권장
  infographic: "stat" (수치 있을 때) or "none"
  quote: (선택) 짧은 고객 인용문 20자 이내. 실제 크롤링 데이터에 고객 후기/인용이 있을 때만 추가. 없으면 필드 생략.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TYPE B 전용 — 제조·인프라]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TYPE B] type: "scale_proof"  [규모·인프라 증명]
  PURPOSE: 경쟁사가 복제 불가한 물리적 자산/인프라 규모. 신뢰 기반 구축.
  headline: 인프라/규모 경쟁우위를 한 줄로
  body: 2-6 bullets — 구체적 규모/위치/용량/인증 (수치 필수, 크롤링 데이터만)
  infographic: "stat" or "flowchart"

[TYPE B] type: "delivery_model"  [납품·협력 방식]
  PURPOSE: 어떻게 함께 일하는지. 예측 가능성·SLA·거버넌스 모델 제시.
  headline: 파트너십/납품 모델의 신뢰 가치
  body: 3-5 bullets — 단계별 납품, SLA, 공동 관리 방식
  infographic: "flowchart" or "none"

[TYPE B] type: "core_business_1" / "core_business_2"  [주요 사업 영역]
  PURPOSE: 주력 사업을 고객 가치 중심으로 설명.
  headline: 사업 영역명 + 고객이 얻는 가치
  body: 3-5 bullets — 세부 서비스, 납품 실적, 차별점 (크롤링 데이터만)
  infographic: "stat" or "none"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TYPE C 전용 — 크리에이티브·에이전시]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TYPE C] type: "creative_approach"  [크리에이티브 접근법]
  PURPOSE: "왜 우리의 작업이 다른가" — 철학과 방법론. 포트폴리오 신뢰 기반.
  headline: 크리에이티브 철학 선언문
  body: 3-4 bullets — 작업 기준, 차별화 방법론
  infographic: "venn" or "none"

[TYPE C] type: "showcase_work_1" / "showcase_work_2"  [핵심 레퍼런스]
  PURPOSE: 실제 작업물 1건 deep-dive. 공개된 데이터만.
  headline: 프로젝트/캠페인명 or 클라이언트 업종
  subheadline: 핵심 성과 한 줄
  body: 3-6 bullets — [상황] → [접근] → [실행] → [결과] 구조 권장
  infographic: "stat" (수치 있을 때) or "none"

[TYPE C] type: "client_list"  [클라이언트 포트폴리오]
  headline: 협업 클라이언트 폭/다양성을 표현
  body: 4-5 bullets — 클라이언트 업종, 프로젝트 유형, 협업 규모 (크롤링 데이터만)
  infographic: "none"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TYPE D 전용 — B2C·브랜드]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TYPE D] type: "flagship_experience"  [대표 상품·서비스 경험]
  headline: 플래그십 상품/서비스 + 경험 가치
  body: 3-5 bullets — 기능적·감성적·경제적 가치
  infographic: "stat" or "none"

[TYPE D] type: "brand_story"  [브랜드 WHY]
  headline: 브랜드 존재 이유 선언
  body: 3-4 bullets — 창업 배경, 가치관, 사회적 의미
  infographic: "none"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[텍스트 강조형 — 이미지 없이 메시지만으로 임팩트]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SLIDE] type: "pull_quote"  [핵심 인용구·인사이트 — 풀스크린 강조]
  PURPOSE: 슬라이드 전체를 하나의 강렬한 문장으로 채움. 전환점, 고객 증언, 핵심 인사이트에 활용.
  WHEN TO USE: (a) 고객 증언이 있을 때 (b) 프레젠테이션의 분위기 전환이 필요할 때
               (c) 특정 수치나 사실이 너무 강력해서 단독 강조가 필요할 때
  SKIP IF: 일반적인 내용 전달 슬라이드. 전체 덱에서 1-2개 이하로 사용.
  headline: 인용구 전체 또는 핵심 인사이트 문장 (30-80자 적정)
            GOOD: "비용이 문제가 아니었습니다. 우리에게 필요한 건 신뢰할 수 있는 파트너였습니다."
            GOOD: "도입 6개월 만에, 우리가 3년간 해결하지 못했던 문제가 사라졌습니다."
  subheadline: 출처 또는 화자 (회사명/직책, 크롤링 데이터에 없으면 생략)
  body: []  ← 비워둘 것
  infographic: {"type": "none", "data": {}}

[SLIDE] type: "big_statement"  [임팩트 선언 — 컬러 블록 + 대형 텍스트]
  PURPOSE: 짧고 강렬한 선언문 하나로 슬라이드를 채움. 컬러 패널이 시각적 볼륨을 만든다.
  WHEN TO USE: (a) why_us의 핵심을 한 문장으로 증류할 때 (b) 섹션 전환 강조
               (c) 데이터 없이도 포지셔닝을 명확히 해야 할 때
  SKIP IF: 내용이 충분해서 일반 슬라이드로 처리 가능할 때
  headline: 30-60자 이내의 강렬하고 완결된 선언문
            GOOD: "우리는 더 빠른 것이 아닙니다. 더 정확한 것을 만듭니다."
            GOOD: "세 번의 실패가 지금의 [회사명]을 만들었습니다."
  subheadline: 1줄 보완 설명 (선택) — 크롤링 데이터 기반
  body: []  ← 비워둘 것
  infographic: {"type": "none", "data": {}}

[SLIDE] type: "two_col_text"  [텍스트 2열 — 좌 제목 + 우 항목 목록]
  PURPOSE: 이미지 없이 텍스트만으로 꽉 찬 느낌. 어젠다, 목표, Pain 목록, 비교 항목에 활용.
  WHEN TO USE: (a) 4-6개의 항목을 나열할 때 (b) "문제: 해결책" 쌍을 보여줄 때
               (c) 목표, 어젠다, 이슈 정리 슬라이드
  headline: 좌측 큰 제목 — 간결하게 (10자 이내 권장)
            GOOD: "3가지 핵심 문제", "왜 우리인가", "다음 단계"
  body: 4-6 bullets — "제목: 설명" 형식 (콜론 구분자 필수)
        GOOD: "비용 구조: 초기 투자 없이 성과 기반 과금으로 리스크 제거"
        GOOD: "속도: 기존 대비 3배 빠른 납품 — 현장 검증 완료"
        BAD:  "좋은 서비스" (콜론 없는 단순 나열)
  subheadline: 좌측 패널 하단 보조 설명 (선택)
  infographic: {"type": "none", "data": {}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[공통 보조 — 모든 타입에서 데이터 있을 때 사용]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SLIDE] type: "key_metrics"  [핵심 수치 대시보드 — stat_3col 레이아웃]
  PURPOSE: 회사 규모·성과를 직관적 KPI 2-4개로 한눈에 증명. 숫자가 신뢰를 만든다.
  INCLUDE IF: 크롤링 데이터에 구체적 수치 2개 이상 존재 (3개 이상 강력 권장)
  SKIP IF: 수치 1개 이하 (proof_results에 통합)
  headline: 수치로 선언하는 신뢰 문장 (예: "숫자로 증명하는 [회사명]의 실력")
  body: 2-6 bullets (크롤링 수치 수에 맞게) — 형식: "[icon] 수치+단위 · 맥락 설명 (달성 기간·배경 추가 권장)"
        GOOD: "[bar-chart] 고객사 1,200곳 · 12개 산업 분야, 5년간 누적"
        GOOD: "[trending-up] A 브랜드 5주 만에 매출 2000% 증가 · ROAS 995% 개선"
        GOOD: "[percent] CPA 78% 절감 · 동일 예산으로 전환DB 349% 확대"
        BAD:  "성장하고 있습니다" (수치 없는 bullet 금지)
  infographic: "stat" REQUIRED — 실제 크롤링 수치만 사용 (최소 3개 목표, 최대 6개, 데이터 부족 시 2개 가능)
               {"stats": [{"value": "2000", "unit": "%", "label": "A 브랜드 매출 증가"}, ...]}

[SLIDE] type: "our_process"  [협업 진행 방식 — numbered_process 레이아웃]
  PURPOSE: 고객이 우리와 어떻게 일하는지 단계별로 보여줌. 예측 가능성·전문성 증명.
  DIFFERENCE FROM how_it_works: how_it_works=제품/솔루션 작동 방식 / our_process=실제 협업 절차
  INCLUDE IF: how_it_works가 없거나, 고객과의 협업 프로세스 데이터가 별도 존재
  headline: "[N]단계로 완성되는 [회사명] 협업 방식" 형식
  body: 4-5 bullets — 각 단계 + [icon] 접두사 필수 + 고객이 받는 결과물 명시
        GOOD: "[compass] 진단: 현황 파악 → 개선 우선순위 리포트 제공"
        GOOD: "[rocket] 런칭: 시범 적용 → 성과 측정 기준 확정"
  infographic: "flowchart" REQUIRED (3-5 steps)

[SLIDE] type: "company_history"  [연혁·성장 스토리 — timeline_h 레이아웃]
  PURPOSE: 창립부터 현재까지 성장 궤적으로 신뢰·안정성 증명.
  INCLUDE IF: 연혁 데이터 3개 이상 + 설립 5년 이상 기업
  SKIP IF: 신생 스타트업 또는 연혁 데이터 부족
  headline: 성장의 스토리를 담은 선언 (예: "N년의 축적, 지금이 정점이 아닙니다")
  body: 3-5 bullets — "YYYY: 핵심 사건" 형식 (실제 데이터만)
        GOOD: "2018: 법인 설립 · 첫 파트너십 체결"
        GOOD: "2022: 시리즈B 투자 유치 · 해외 진출"
  infographic: "timeline" REQUIRED
               {"events": [{"year": "2018", "label": "법인 설립", "desc": "첫 파트너십 체결"}, ...]}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TYPE E 전용 — 플랫폼·에코시스템]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TYPE E] type: "dual_sided_value"  [양면 가치 제안]
  headline: 공급자·소비자 모두 이기는 구조 핵심 메시지
  body: 2-6 bullets — [공급자] 측 + [소비자] 측 균형 있게 구성
  infographic: "venn" or "none"

[TYPE E] type: "scalability_proof"  [확장성 증명]
  headline: 성장 수치 선언
  body: 3-5 bullets — 실제 크롤링 수치만
  infographic: "stat" REQUIRED if numbers exist, else "none"

[TYPE E] type: "ecosystem_partners"  [파트너 생태계]
  headline: 에코시스템 규모와 파트너십 가치
  body: 3-4 bullets — 파트너 범주, 통합 건수, 공동 가치
  infographic: "flowchart" or "none"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[TYPE F 전용 — 교육·연구·전문서비스]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[TYPE F] type: "team_credibility"  [전문 팀 신뢰도]
  PURPOSE: 핵심 팀·전문가의 자격·경력으로 전문성 증명. 지식 서비스업에서 최고의 신뢰 요소.
  INCLUDE IF: 팀/전문가 관련 크롤링 데이터 풍부도 2 이상
  headline: 팀 전문성을 담은 신뢰 선언 (예: "현업 전문가가 직접 설계하고 전달합니다")
  body: 3-4 bullets — 학력·자격증·수상·업력 (크롤링 데이터만, 추론 금지)
        GOOD: "[award] 평균 업력 12년 이상의 현직 전문가 강사진"
        GOOD: "[user-check] 공인 자격보유자 100% · PMP·CPA·변호사 등"
  infographic: "none"

[TYPE F] type: "curriculum_structure"  [커리큘럼·프로그램 구조]
  PURPOSE: 교육/컨설팅 프로그램을 단계별로 시각화. 예측 가능성과 체계성 증명.
  INCLUDE IF: 교육·컨설팅 단계별 구조 데이터 존재
  headline: 프로그램 구조를 담은 선언 (예: "[N]단계 체계적 커리큘럼으로 완성합니다")
  body: 3-5 bullets — 각 모듈/단계 + 학습 목표 or 산출물
        GOOD: "[layers] 1단계 진단: 현재 수준 파악 → 맞춤 로드맵 설계"
  infographic: "flowchart" REQUIRED

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[데이터 부족 시 처리 규칙 — 반드시 준수]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 시장/업계 데이터 없음 → market_challenge body를 해당 업종 공통 이슈로 자연스럽게 작성 (메타 레이블 절대 금지)
- 고객 Pain 데이터 없음 → pain_analysis body를 업종 공통 Pain으로 추론해서 작성 (메타 레이블 절대 금지)
- 성과 수치 없음 → proof_results를 Before/After 포맷으로 작성 (stat infographic 생략)
- 사례 없음 → case_study 슬라이드 완전 생략, how_it_works + delivery_model로 신뢰 대체
- 서비스 데이터 2개뿐 → solution_overview 1개 슬라이드로 통합 (service_pillar_2 무리하게 넣지 말 것)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
UNIVERSAL RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COPY:
1. body[] bullets: 15-35자(한국어 기준). 구체적. 원인+과정+결과 3요소 포함 권장.
   크롤링 데이터에 충분한 내용이 있으면 슬라이드당 bullets를 최대 허용치까지 작성.
   GOOD: "광고 채널 파편화: 채널별 성과 비교 불가 → 고비용 채널 유지 반복, 낭비 구조 고착"
   GOOD: "수주 단가 22% 상승 → 영업이익률 구조적 개선, 동일 매출 대비 수익성 3년 연속 향상"
   BAD:  "고객을 위해 최선을 다하겠습니다"
   BAD:  "비용 절감" (키워드 수준 단독 사용 금지)
2. Infographic labels (flowchart/funnel steps): 2-5 words ONLY
3. NEVER fabricate: phone numbers, addresses, client names, KPIs not in crawled data
4. NEVER import jargon from other industries into this company's copy
5. ALL copy in Korean. Formal register (격식체/경어체)
6. "cover" body[] = [] always — no exceptions
7. ICON PREFIX (권장): pain_analysis/solution_overview/why_us/key_metrics/process 슬라이드의 body[] 항목 앞에
   아이콘이 있으면 슬라이드 품질이 높아집니다. 적합한 아이콘이 있으면 적극 활용하세요.
   [icon-name] 접두사를 붙이면 해당 단계/카드에 아이콘이 표시됨.
   유효한 아이콘 이름: target, briefcase, building, building-2, award, trophy, flag, rocket, compass,
   handshake, bar-chart, bar-chart-2, trending-up, trending-down, pie-chart, activity, percent,
   calculator, users, user, user-check, user-plus, heart, star, mail, phone, message-circle, bell,
   share-2, link, cpu, database, cloud, wifi, lock, code, layers, globe, arrow-right, check-circle,
   x-circle, refresh-cw, clock, zap, settings, dollar-sign, credit-card, wallet, coins, plus-circle,
   search, eye, download, upload, list, check, info, lightbulb, map-pin
   예시: "[rocket] 런칭 단계: 배포 및 모니터링", "[trending-up] 연매출 35% 성장"
   - 아이콘 없이도 정상 동작 (접두사 없으면 아이콘 미표시)
   - 모든 슬라이드에 강제 적용하지 말 것 — 프로세스/KPI 슬라이드에만 사용

INFOGRAPHIC SCHEMAS:
- flowchart : {"steps":  [{"label": "단계명"}, ...]}                         ← 3-5 steps (how_it_works, delivery_model)
- stat      : {"stats":  [{"value": "995", "unit": "%", "label": "설명"}, ...]} ← max 4 (key_metrics, proof_results)
- funnel    : {"stages": [{"label": "단계명"}, ...]}                         ← 3-5 stages (pain_analysis 심화)
- venn      : {"circles": ["A개념", "B개념"], "overlap": "교집합"}           ← solution_overview, dual_sided_value
- bar       : {"items":  [{"label": "항목", "value": 85}, ...]}              ← value = NUMBER 0-100
- timeline  : {"events": [{"year": "2020", "label": "사건명", "desc": "설명"}, ...]} ← 3-6 events (company_history)
- none      : {}

레이아웃 힌트 (Gemini 참고용 — 실제 렌더링은 시스템이 결정):
  key_metrics + stat → stat_3col (대형 숫자 카드)
  our_process/how_it_works + flowchart → numbered_process (번호 체인)
  company_history + timeline → timeline_h (수평 타임라인)
  pain_analysis/solution_overview → cards (카드 그리드)
  showcase_work + 이미지 → portfolio (풀 배경 글래스박스)
  positioning_matrix → matrix_2x2 (2×2 포지셔닝 매트릭스)
  key_metrics/scale_proof + chart_data → bar_chart (막대 차트)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SLIDE] type: "positioning_matrix"  [2×2 포지셔닝 매트릭스 — IR/분석 목적]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PURPOSE: McKinsey/BCG 스타일 전략 프레임워크. 경쟁 포지셔닝·시장 기회·리스크 분석.
  INCLUDE IF: ir/report 목적 + 비교 가능한 데이터 또는 포지셔닝 근거 존재
  SKIP IF: 데이터·근거 없이 추상적으로만 채울 경우
  headline: 매트릭스 제목 (예: "경쟁 포지셔닝 분석", "시장 기회 매트릭스")
  subheadline: 양 축 설명 (예: "X축: 시장 점유율 | Y축: 시장 성장률")
  body: [4개 항목 — 각 사분면] FORMAT: "사분면 레이블: 핵심 내용"
        ① Q1 (우상단, 최우위): "레이블: 설명" — 이 회사가 지향/점유하는 포지션
        ② Q2 (좌상단): "레이블: 설명"
        ③ Q3 (우하단): "레이블: 설명"
        ④ Q4 (좌하단): "레이블: 설명"
  infographic: {"type": "none", "data": {}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[OPTIONAL FIELD] chart_data — 수치 데이터가 있을 때 모든 슬라이드에 추가 가능
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚠️ 크롤링 데이터에 실제 비교 가능한 수치(3개 이상)가 있을 때만 추가.
     없으면 필드 자체를 포함하지 마세요.
  FORMAT:
  "chart_data": {
    "title": "차트 제목 (15자 이내)",
    "labels": ["레이블1", "레이블2", "레이블3"],
    "values": [숫자1, 숫자2, 숫자3],
    "unit": "%" (또는 "억원", "건", "배" 등 단위)
  }
  적합한 슬라이드: key_metrics, scale_proof, proof_results, market_impact, financial_highlights

COLOR:
- primaryColor = most vivid ACCENT color (NOT near-black #000~#333, NOT near-white #EEE~#FFF)
- bgColor = darkest usable background (#0A0A0A~#1A1A1A range preferred)
- No vivid color found → industry default: tech=#1A1A1A | finance=#1A4FBA | construction=#E85D26
                                           healthcare=#0DA377 | creative=#FF3366 | other=#1A1A1A

Output ONLY valid JSON. No markdown fences. No explanations. No comments.

JSON Schema (STRICT — slides array length = your chosen count, 7-10):
{
  "brand": {
    "name": string,
    "primaryColor": hex_string,
    "secondaryColor": hex_string,
    "bgColor": hex_string,
    "mood": "tech" | "warm" | "minimal" | "bold",
    "industry": string,
    "narrative_type": "A" | "B" | "C" | "D" | "E" | "F"
  },
  "slides": [
    {
      "id": number,
      "type": "cover" | "market_challenge" | "pain_analysis" | "solution_overview" | "problem_solution" | "how_it_works" | "proof_results" | "why_us" | "case_study" | "cta_session" | "contact" | "scale_proof" | "delivery_model" | "core_business_1" | "core_business_2" | "creative_approach" | "showcase_work_1" | "showcase_work_2" | "client_list" | "flagship_experience" | "brand_story" | "dual_sided_value" | "scalability_proof" | "ecosystem_partners" | "key_metrics" | "our_process" | "company_history" | "team_credibility" | "curriculum_structure" | "pull_quote" | "big_statement" | "two_col_text" | "positioning_matrix",
      "headline": string,
      "subheadline": string,
      "body": string[],
      "infographic": {"type": string, "data": object},
      "chart_data": {"title": string, "labels": string[], "values": number[], "unit": string},
      "image_en_hint": string
    }
  ]
}"""


def agent_researcher(raw_info: str, progress_fn=None, page_subject: dict = None,
                     forced_narrative: str = None) -> str:
    """Factbook 추출 에이전트 — 팩트만 Markdown으로 반환"""
    def _p(m):
        if progress_fn: progress_fn(str(m))

    # C-type(아티스트/크리에이티브)이면 전용 템플릿 사용
    _is_c = (forced_narrative == 'C') or (page_subject and page_subject.get('subject_name'))
    _tmpl = RESEARCHER_USER_TEMPLATE_C if _is_c else RESEARCHER_USER_TEMPLATE

    # 주체 정보 힌트 (아티스트/서브브랜드 페이지 시 Researcher가 올바른 주체에 집중하도록)
    _subject_hint = ''
    if page_subject and page_subject.get('subject_name'):
        _sname = page_subject['subject_name']
        _sparent = page_subject.get('parent_org', '')
        _subject_hint = (
            f"\n\n[중요] 이 페이지의 주체는 '{_sname}'입니다"
            + (f" (소속: {_sparent})" if _sparent else "")
            + f". 팩트북 제목과 분석은 '{_sname}' 중심으로 작성하세요."
            + f" 소속사/레이블({_sparent or '상위 조직'})이 아닌 '{_sname}' 자체의 정보에 집중하세요.\n"
        )

    prompt = _tmpl.format(raw_info=raw_info) + _subject_hint  # clean_raw_text()에서 이미 12000자로 정제됨
    try:
        resp = _client.models.generate_content(
            model="models/gemini-2.5-pro",
            contents=prompt,
            config={
                "system_instruction": RESEARCHER_SYSTEM_PROMPT,
                "temperature": 0.1,
                "max_output_tokens": 4000,
            }
        )
        factbook = resp.text.strip()
        _p(f"  → Factbook 추출 완료 ({len(factbook)}자)")
        return factbook
    except Exception as e:
        _p(f"  ⚠ Researcher 에이전트 실패, raw_info 직접 사용: {e}")
        return raw_info  # 폴백: 원문 그대로


# 업종 키워드 사전 감지 — Gemini 오분류 방지용 Python 보정
_NT_C_KEYWORDS = {
    # 엔터테인먼트
    'entertainment', 'kpop', 'k-pop', 'k pop', 'music label', 'record label',
    'talent agency', 'artist management', 'idol', 'concert', 'tour', 'album',
    'musician', 'singer', 'rapper', 'band', 'choreography', 'trainee',
    '엔터', '엔터테인먼트', '음악', '레이블', '아티스트', '아이돌', '기획사',
    '연예', '공연', '앨범', '뮤직', '아이돌그룹', '연습생',
    # 스포츠/패션/미디어
    'sports club', 'sports agency', 'fashion brand', 'media production',
    '스포츠', '패션', '미디어',
}

# B-type 키워드 — 제조·인프라·부품 업종 감지 (C-type 이후 체크)
_NT_B_KEYWORDS = {
    # 한국어 제조/부품 업종
    '전자부품', '정밀부품', '중공업', '플랜트', '산업기계', '자동화설비',
    'mlcc', '적층세라믹', '인쇄회로기판', '전자재료', '반도체장비',
    '부품제조', '소재기업', '제조전문', '설비제조',
    # 영문 제조/부품 업종
    'electronic components', 'precision parts', 'heavy industry',
    'industrial machinery', 'semiconductor equipment', 'printed circuit board',
    'electronic materials', 'components manufacturer', 'parts manufacturer',
}

# D-type 키워드 — 럭셔리/프리미엄 브랜드 감지 (C/B 이후 체크)
_NT_D_KEYWORDS = {
    'luxury', 'premium', 'haute couture', 'fine dining', 'bespoke', 'prestige',
    '럭셔리', '프리미엄', '하이엔드', '파인다이닝', '명품', '고급',
}

# 도메인/회사명 기반 감지 — URL에 포함되면 factbook 내용과 무관하게 C타입 적용
_NT_C_DOMAINS = {
    # HYBE 계열
    'ibighit', 'hybe', 'bighit', 'bts', 'weverse',
    # SM/YG/JYP 3대 기획사
    'smtown', 'sment', 'yg-entertainment', 'ygfamily', 'jype', 'jypentertainment',
    # 중소 기획사
    'cube', 'pledis', 'starship', 'mnet', 'cjenm', 'kakaoent',
    'fncent', 'rbw', 'woolim', 'ts entertainment', 'wm entertainment',
    # 스포츠/크리에이티브
    'nba', 'nfl', 'kbo', 'kleague', 'puma', 'fila', 'newera',
}

def _detect_page_subject(url: str) -> dict:
    """URL 경로 패턴으로 아티스트/그룹 주체 1차 감지 (빠른 사전 힌트).
    '/artist/profile/LE SSERAFIM' → {'subject_name': 'LE SSERAFIM', 'subject_type': 'artist'}
    일반 기업 홈페이지 → {}
    """
    try:
        path = unquote(urlparse(url).path)
        # /artist/profile/NAME, /artist/NAME, /group/NAME, /talent/NAME, /member/NAME
        m = re.search(r'/(?:artist/profile|artist|group|talent|member)/([^/]+)', path, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            _SKIP = {'index', 'profile', 'about', 'list', 'all', 'en', 'ko', 'jp', 'zh'}
            if name and len(name) > 1 and name.lower() not in _SKIP:
                return {'subject_name': name, 'subject_type': 'artist'}
    except Exception:
        pass
    return {}


def _detect_page_subject_from_text(raw_info: str, url: str) -> dict:
    """크롤링 후 og:title / <title> 기반 주체 2차 감지 (더 신뢰도 높음).
    'LE SSERAFIM | SOURCE MUSIC' → {'subject_name': 'LE SSERAFIM', 'subject_type': 'artist', 'parent_org': 'SOURCE MUSIC'}
    일반 기업 홈페이지 → {}
    """
    # scrape_website가 삽입한 [og:title]: 값 추출
    m_og = re.search(r'\[og:title\]:\s*(.+)', raw_info)
    if not m_og:
        return _detect_page_subject(url)   # fallback to URL pattern
    og_title = m_og.group(1).strip()
    # "Sub | Parent" / "Sub - Parent" / "Sub – Parent" 패턴 (업종 무관 범용)
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    domain_parts = re.sub(r'^www\.', '', netloc).split('.')
    domain_name = domain_parts[0]  # 최상위 도메인 (e.g. 'sourcemusic', 'google')

    # 일반적인 페이지 섹션명 — 아티스트/브랜드명이 아님
    _GENERIC_PAGE_TERMS = {
        'profile', 'about', 'discography', 'music', 'members', 'news',
        'media', 'gallery', 'schedule', 'store', 'shop', 'home', 'main',
        'index', 'contact', 'career', 'careers', 'blog', 'press',
        'artist', 'artists', 'group', 'groups', 'official', 'site',
        'biography', 'bio', 'info', 'introduction', 'overview',
    }

    for sep in [' | ', ' ｜ ', ' - ', ' – ', ' — ']:
        parts = og_title.split(sep, 1)
        if len(parts) == 2:
            subject, parent = parts[0].strip(), parts[1].strip()
            # 첫 토큰이 generic 섹션명이면 다음 토큰을 실제 subject로 사용
            if subject.lower() in _GENERIC_PAGE_TERMS:
                # "CORTIS | BIGHIT MUSIC" → subject=CORTIS, parent=BIGHIT MUSIC
                sub_parts = parent.split(sep, 1)
                if len(sub_parts) == 2:
                    subject, parent = sub_parts[0].strip(), sub_parts[1].strip()
                    print(f"  [주체 감지-og] 섹션명 건너뜀, 실제 주체: '{subject}' (parent: {parent})")
                else:
                    # 하위 분리 불가 → parent 자체가 subject
                    subject = parent
                    parent = domain_name
                    print(f"  [주체 감지-og] 섹션명 건너뜀, parent를 주체로: '{subject}'")
            # 유효성: 주체가 2~50자, 부모·도메인명과 다름, 또 generic 섹션명 아님
            # parent가 4단어 이상 = 태그라인/업종설명 ("전략 중심 그로스 마케팅 에이전시") → 서브 주체 감지 무효
            _parent_is_tagline = len(parent.split()) >= 4
            if (2 <= len(subject) <= 50
                    and subject.lower() != parent.lower()
                    and subject.lower().replace(' ', '') != domain_name
                    and subject.lower() not in _GENERIC_PAGE_TERMS
                    and not _parent_is_tagline):
                _stype = _detect_page_subject(url).get('subject_type', 'sub-brand')
                print(f"  [주체 확정-og] '{subject}' (parent: {parent})")
                return {'subject_name': subject, 'subject_type': _stype or 'sub-brand',
                        'parent_org': parent}

    # ── 신호 2: 서브도메인 감지 (gemini.google.com → Gemini) ──────────────
    _SKIP_SUB = {'www', 'm', 'mobile', 'api', 'cdn', 'static', 'assets',
                 'media', 'img', 'images', 'mail', 'ns', 'ns1', 'ns2'}
    if len(domain_parts) >= 3:
        sub = domain_parts[0]
        if sub not in _SKIP_SUB and len(sub) >= 2:
            parent_domain = '.'.join(domain_parts[1:])
            print(f"  [주체 감지-subdomain] '{sub}' (parent: {parent_domain})")
            return {'subject_name': sub.capitalize(), 'subject_type': 'sub-brand',
                    'parent_org': parent_domain}

    # fallback: URL 경로 패턴
    return _detect_page_subject(url)


def _detect_auto_narrative(factbook, company_name, url=None):
    """업종 키워드 기반 내러티브 타입 사전 감지. 확신 있을 때만 반환."""
    try:
        # URL/도메인 기반 감지 (factbook보다 먼저, 더 신뢰도 높음)
        url_text = str(url or '').lower()
        if any(d in url_text for d in _NT_C_DOMAINS):
            return 'C'
        # factbook + 회사명 기반 감지
        text = (str(factbook) + ' ' + str(company_name)).lower()
        if any(k in text for k in _NT_C_KEYWORDS):
            return 'C'
        if any(k in text for k in _NT_B_KEYWORDS):
            return 'B'
        if any(k in text for k in _NT_D_KEYWORDS):
            return 'D'
    except Exception:
        pass
    return None


_PURPOSE_CONTEXT = {
    'brand':     '브랜드 소개 — 브랜드 정체성, 핵심 가치, 팀, 비전을 중심으로 구성하세요.',
    'sales':     '영업 제안 — 고객의 문제 → 솔루션 → 차별점 → 도입 효과 → CTA 흐름으로 구성하세요.',
    'ir':        ('투자 IR — 시장 기회·성장 지표·비즈니스 모델·팀 경쟁력·투자 포인트를 강조하세요. '
                  '【McKinsey 스타일】 수치 중심 서술, key_metrics로 핵심 KPI 집약. '
                  '크롤링 데이터에 비교 수치(성장률·시장규모 등)가 3개 이상이면 positioning_matrix 슬라이드 포함. '
                  '수치가 있는 슬라이드에는 chart_data 필드를 추가하여 데이터를 시각화하세요.'),
    'portfolio': '포트폴리오 — 대표 작업물, 제작 프로세스, 수상 이력, 주요 클라이언트를 중심으로 구성하세요.',
    'report':    ('내부 보고 — 현황 요약·핵심 성과 지표·과제/리스크·다음 단계 계획 순으로 구성하세요. '
                  '【McKinsey 스타일】 swot_analysis 또는 positioning_matrix로 현황을 구조화하고, '
                  'key_metrics로 KPI 대시보드를 구성하세요. '
                  '수치가 있는 슬라이드에는 chart_data 필드를 추가하여 데이터를 시각화하세요.'),
}


def agent_strategist(factbook: str, company_name: str, progress_fn=None,
                     forced_narrative: str = None, purpose: str = 'brand'):
    """슬라이드 목차 기획 에이전트 — (narrative_type, storyline_list) 반환"""
    def _p(m):
        if progress_fn: progress_fn(str(m))

    forced_str = (
        f"\n\n[사용자 지정] 내러티브 타입: {forced_narrative}\n"
        f"반드시 TYPE {forced_narrative} 흐름을 사용하세요. 다른 타입으로 변경 금지."
    ) if forced_narrative and forced_narrative != 'auto' else ""
    purpose_str = (
        f"\n\n[발표 목적] {_PURPOSE_CONTEXT.get(purpose, '')}"
    ) if purpose and purpose not in ('brand', 'auto') else ""
    user_prompt = (
        f"회사명: {company_name}{forced_str}{purpose_str}\n\n"
        f"⚠️ 반드시 slides 배열에 7개 이상의 슬라이드 객체를 포함해서 JSON을 반환하세요.\n\n"
        f"[FACTBOOK]\n{factbook}"
    )
    _detected_nt = None  # Gemini 파싱 성공 시 저장, 폴백에서 사용
    try:
        resp = _client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": STRATEGIST_SYSTEM_PROMPT,
                "temperature": 0.3,
                "max_output_tokens": 4000,
            }
        )
        text = resp.text.strip()
        # ```json ... ``` 또는 raw JSON 객체 추출
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            raw = m.group()
            # 스마트 쿼트 → 일반 쿼트 정제
            raw = raw.replace('\u201c', '"').replace('\u201d', '"')
            raw = raw.replace('\u2018', "'").replace('\u2019', "'")
            # 후행 쉼표 제거 (trailing comma)
            raw = re.sub(r',\s*([}\]])', r'\1', raw)
            # 리터럴 줄바꿈 → 공백 (JSON 문자열 내 unescaped \n 처리)
            raw = raw.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                # 폴백: narrative_type + 슬라이드 항목 개별 추출
                _nt_m = re.search(r'"narrative_type"\s*:\s*"([A-DF])"', raw)
                _items = re.findall(
                    r'"slide_num"\s*:\s*(\d+)[^}]*?"type"\s*:\s*"([^"]+)"[^}]*?"topic"\s*:\s*"([^"]+)"',
                    raw
                )
                if _nt_m and _items:
                    result = {
                        "narrative_type": _nt_m.group(1),
                        "slides": [{"slide_num": int(n), "type": t, "topic": tp} for n, t, tp in _items]
                    }
                else:
                    raise
            narrative_type = result.get("narrative_type", "A")
            if forced_narrative and forced_narrative != 'auto':
                narrative_type = forced_narrative  # Gemini 응답 무시, 강제 타입 적용
            _detected_nt = narrative_type  # 예외 경로에서도 사용
            slides = result.get("slides", [])
            if len(slides) >= 5:
                _p(f"  → 내러티브 타입: {narrative_type} | {len(slides)}개 슬라이드 기획")
                return narrative_type, slides
            elif len(slides) >= 1:
                # 슬라이드 부족 → 1회 재시도 (강제 최소 개수 지정)
                _p(f"  ⚠ Strategist {len(slides)}개 슬라이드 → 재시도 중...")
                _retry_prompt = (
                    f"회사명: {company_name}\n내러티브 타입: {narrative_type}\n\n"
                    f"⚠️ 아래 JSON 형식으로 반드시 9개 슬라이드를 반환하세요. "
                    f"데이터 부족해도 각 TYPE 필수 슬라이드는 모두 포함해야 합니다.\n\n"
                    f"[FACTBOOK]\n{factbook[:3000]}"
                )
                _r2 = _client.models.generate_content(
                    model="models/gemini-2.5-flash",
                    contents=_retry_prompt,
                    config={"system_instruction": STRATEGIST_SYSTEM_PROMPT,
                            "temperature": 0.2, "max_output_tokens": 4000}
                )
                _m2 = re.search(r'\{[\s\S]*\}', _r2.text.strip())
                if _m2:
                    _raw2 = _m2.group()
                    _raw2 = re.sub(r',\s*([}\]])', r'\1', _raw2)
                    _raw2 = _raw2.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
                    try:
                        _res2 = json.loads(_raw2)
                        _slides2 = _res2.get("slides", [])
                        if len(_slides2) >= 5:
                            _p(f"  → 재시도 성공: {narrative_type} | {len(_slides2)}개 슬라이드")
                            return narrative_type, _slides2
                    except Exception:
                        pass
                _p(f"  ⚠ 재시도도 5개 미달, 기본 목차 사용")
    except Exception as e:
        _p(f"  ⚠ Strategist 에이전트 실패, 기본 목차 사용: {e}")

    # 폴백 기본 목차 — Gemini 감지 타입 > forced_narrative > 'A' 우선순위
    _fallback_nt = (forced_narrative if forced_narrative and forced_narrative != 'auto'
                    else (_detected_nt or 'A'))
    _p(f"  → 기본 목차(TYPE {_fallback_nt}) 적용")
    _fallback_maps = {
        'C': [
            {"slide_num": 1, "type": "cover",            "topic": "브랜드 포지셔닝 + 핵심 가치"},
            {"slide_num": 2, "type": "brand_story",      "topic": "브랜드 탄생 배경과 철학"},
            {"slide_num": 3, "type": "creative_approach","topic": "우리만의 크리에이티브 방식"},
            {"slide_num": 4, "type": "showcase_work_1",  "topic": "대표 작업/아티스트/프로젝트 1"},
            {"slide_num": 5, "type": "showcase_work_2",  "topic": "대표 작업/아티스트/프로젝트 2"},
            {"slide_num": 6, "type": "key_metrics",      "topic": "주요 성과 수치"},
            {"slide_num": 7, "type": "proof_results",    "topic": "실제 성과 및 수상 이력"},
            {"slide_num": 8, "type": "cta_session",      "topic": "다음 단계 제안"},
            {"slide_num": 9, "type": "contact",          "topic": "연락처"},
        ],
        'B': [
            {"slide_num": 1, "type": "cover",            "topic": "기업 포지셔닝 + 핵심 기술력"},
            {"slide_num": 2, "type": "market_challenge", "topic": "산업 환경 변화와 기술 수요"},
            {"slide_num": 3, "type": "solution_overview","topic": "당사의 핵심 기술 솔루션"},
            {"slide_num": 4, "type": "service_pillar_1", "topic": "주요 제품군 및 기술 스펙"},
            {"slide_num": 5, "type": "service_pillar_2", "topic": "품질 인증 및 생산 역량"},
            {"slide_num": 6, "type": "proof_results",    "topic": "납품 실적 및 글로벌 파트너"},
            {"slide_num": 7, "type": "key_metrics",      "topic": "주요 경영 성과 지표"},
            {"slide_num": 8, "type": "cta_session",      "topic": "협력 제안"},
            {"slide_num": 9, "type": "contact",          "topic": "연락처"},
        ],
    }
    return _fallback_nt, _fallback_maps.get(_fallback_nt, [
        {"slide_num": 1, "type": "cover",             "topic": "회사 포지셔닝 + 핵심 가치 제안"},
        {"slide_num": 2, "type": "market_challenge",  "topic": "지금 이 업계에서 일어나는 변화"},
        {"slide_num": 3, "type": "pain_analysis",     "topic": "고객이 매일 겪는 4가지 문제"},
        {"slide_num": 4, "type": "solution_overview", "topic": "우리의 해결책 전체 그림"},
        {"slide_num": 5, "type": "how_it_works",      "topic": "어떻게 함께 일하는가"},
        {"slide_num": 6, "type": "proof_results",     "topic": "실제 성과 및 변화"},
        {"slide_num": 7, "type": "why_us",            "topic": "왜 우리를 선택해야 하는가"},
        {"slide_num": 8, "type": "cta_session",       "topic": "다음 단계 제안"},
        {"slide_num": 9, "type": "contact",           "topic": "연락처"},
    ])


def generate_slide_json(factbook: str, storyline: list, narrative_type: str,
                        brand_assets: dict, company_name: str,
                        mood: str = 'professional', page_subject: dict = None):
    """카피라이터 + JSON 포맷터 에이전트 — Factbook + Storyline → Slide JSON"""
    colors = brand_assets.get('colors', [])
    logo_url = brand_assets.get('logo_url', '')
    accent = next((c for c in colors if _color_vibrancy(c) >= 0.1), '#1A1A1A')
    tone_instruction = MOOD_TONE.get(mood, MOOD_TONE['professional'])

    # 아티스트 페이지 전용 주의사항
    _subject_hint = ''
    if page_subject and page_subject.get('subject_type') == 'artist':
        _subject_hint = f"""
⚠️ 아티스트 페이지 주의사항:
- brand.name = "{page_subject['subject_name']}" (소속 레이블/기획사명 절대 금지)
- 이 PPT는 레이블이 아닌 아티스트 {page_subject['subject_name']}를 소개하는 자료입니다.
- primaryColor: 레이블 로고색이 아닌, {page_subject['subject_name']}의 아이덴티티에 어울리는 색상.
  현재 추출된 색상 후보: {', '.join(colors[:5]) if colors else '없음'}
  레이블 브랜드색처럼 보이면 크리에이티브/엔터테인먼트 기본값(#1A1A1A 또는 #2C2C2C)으로 교체.
"""

    user_prompt = f"""회사명: {company_name}
브랜드 색상: {', '.join(colors[:8]) if colors else 'unknown — use industry-appropriate default'}
내러티브 타입: {narrative_type}
{_subject_hint}
━━━━ 톤앤매너 지침 ━━━━
{tone_instruction}

━━━━ STORYLINE (전략 기획자 확정 목차 — 이 순서와 타입을 그대로 따를 것) ━━━━
{json.dumps(storyline, ensure_ascii=False, indent=2)}

⚠️ STORYLINE 준수 규칙 (절대 위반 금지):
- 위 목차에 있는 슬라이드는 데이터가 부족해도 절대 생략하지 마세요.
  전체 스토리의 흐름이 무너집니다.
- 내용이 적으면 body를 2개로 줄이거나 sub를 생략해도 되지만, 슬라이드 자체는 반드시 출력해야 합니다.
- 위 목차에 없는 슬라이드 타입을 임의로 추가하는 것도 금지입니다.
- 슬라이드 순서도 위 목차 순서 그대로 유지할 것.

━━━━ BRAND COLOR RULE ━━━━
primaryColor = most vivid accent from extracted list (NOT near-black/white)
No vivid color found → industry default:
  tech/digital=#1A1A1A | finance/legal=#1A4FBA | construction=#E85D26
  healthcare=#0DA377   | creative/design=#FF3366 | other=#1A1A1A

━━━━ COPY RULES ━━━━
1. [NO MARKDOWN]: NEVER use ** (bold) or * in the text. Return pure plain text ONLY.
2. [SPACING]: When using numbered lists (1., 2.) or bullets, you MUST add a space after the number/bullet (e.g., '1. 데이터', '· 전략').
3. [NO SENTENCES]: For ALL slides (including market_shock), NEVER end a bullet with '~다' or '~요'. You MUST use noun phrases or short fragments (e.g., '~구축', '~제공', '~개선').
   GOOD: "수주 단가 22% 상승 → 영업이익률 구조적 개선"
         "AI 기반 타겟팅 · CTR 3배 · ROAS 995%"
         "데이터 사일로: 통합 분석 불가 → 예산 낭비 고착"
   BAD:  "저희 회사는 다양한 서비스를 제공하여 고객의 성장을 돕습니다" (문장형 금지)
         "고객을 위해 최선을 다하겠습니다" (서술문 금지)
4. CONSOLIDATION: max 2 service_pillar slides (service_pillar_1, service_pillar_2 only).
   If 3+ services exist → bundle them all into service_pillar_1 and service_pillar_2 body[].
4b. [CARD BODY FORMAT] — service_pillar_*, solution_overview, why_us, core_business_* 슬라이드의
    body[] 아이템은 반드시 "짧은제목: 설명" 형식을 사용할 것. 제목은 2-5 단어.
    GOOD: "전략 기획: 시장/고객/트렌드 기반 성장 로드맵 설계"
          "데이터 활용: 통합 분석 환경 구축 → 의사결정 정확도 향상"
          "성과 최적화: A/B 테스트 자동화 · ROAS 개선"
    BAD:  "시장/고객/트렌드 분석 기반으로 명확한 성장 전략을 기획합니다" (제목 없음)
    이 형식은 카드 UI에서 제목/설명을 시각적으로 분리하는 데 필수임.
4c. [ICON PREFIX] — service_pillar_*, solution_overview, why_us, core_business_*, how_it_works,
    pain_analysis, our_process 슬라이드의 body[] 아이템에는 내용에 맞는 아이콘 접두사를 적극 사용할 것.
    형식: "[아이콘명] 짧은제목: 설명"
    사용 가능 아이콘 목록 (항목 성격에 가장 가까운 것 선택):
      target, trending-up, trending-down, bar-chart, pie-chart, activity, zap, settings,
      dollar-sign, credit-card, wallet, coins, plus-circle, search, eye, download, upload,
      list, check, info, lightbulb, map-pin, users, user, briefcase, star, shield, award,
      clock, calendar, mail, phone, link, globe, layers, grid, box, package, truck,
      tool, cpu, database, server, code, terminal, monitor, smartphone, tablet,
      flag, bookmark, tag, lock, key, bell, chat, heart, thumbs-up, rocket,
      compass, map, navigation, wind, sun, moon, cloud, leaf, fire
    GOOD: "[target] 고객 분석: 세그먼트별 행동 패턴 분석 → 타겟 정밀도 향상"
          "[trending-up] 성장 전략: 시장 확대 로드맵 설계 및 실행"
          "[shield] 리스크 관리: 규제 준수 자동화 · 법적 리스크 최소화"
    BAD:  아이콘 없이 텍스트만 사용 (service_pillar_* 등에서는 아이콘 생략 금지)
5. Infographic labels: 2-5 words ONLY
6. NEVER fabricate phone numbers, addresses, client names, or KPIs not in data
6b. DATA FIDELITY — service_pillar_*, core_business_*, showcase_work_* 슬라이드의 서비스/역량 내용은
    반드시 크롤링된 데이터에 명시된 것만 사용. 데이터에 없는 서비스 영역을 추론·확장·발명 금지.
    전략적 재프레이밍(표현 고도화)은 허용하나, 회사가 실제로 제공하지 않는 서비스를
    존재하는 것처럼 작성하면 안 됨. 크롤링 데이터에 2개 서비스만 있으면 pillar 2개만 사용.
11. TONE — 회사소개서: 회사의 전문성과 역량을 구체적 사실로 전달하는 신뢰 어조.
    - GOOD: "~방식으로 ~문제를 해결합니다", "~를 통해 ~를 실현합니다", "~개 기업이 선택한 이유"
    - BAD:  "저희 회사를 소개합니다", "최선을 다하겠습니다" (모호하고 평범한 표현 금지)
    - BAD:  데이터에 없는 서비스를 "가능합니다", "지원합니다"로 만들어 내는 것
7. ALL copy in Korean, formal register (격식체/경어체)
8. Return ONLY valid JSON. No markdown. No comments.
10. UNIQUENESS: proof_of_concept = BREADTH (여러 고객사·산업의 성과를 한 장에).
    case_study = DEPTH (단일 고객사 하나의 여정: 문제→접근법→결과).
    두 슬라이드에서 동일 고객사 수치를 반복 금지.
    proof_of_concept image_en_hint: multi-client portfolio 스타일 사용.
    case_study image_en_hint: 해당 고객사 업종의 실제 환경 이미지.
9. Each slide MUST include "image_en_hint": 5-8 English words for a BACKGROUND IMAGE.
   CRITICAL: Apply the rule for the slide's category — wrong category = wrong image.

   ── CATEGORY 1: FACTUAL slides (team_intro, case_study, infrastructure_and_scale,
      corporate_overview, showcase_work_*, client_list, proof_of_concept, market_impact,
      flagship_experience, target_audience) ──
   RULE: Use concrete, industry-specific, real-world visual keywords.
   GOOD: "automated logistics warehouse interior wide shot"
         "modern semiconductor cleanroom workers"
         "aerial view busy container port terminals"
         "clean laboratory environment with equipment"
   BAD:  "teamwork", "success", "business people shaking hands"

   ── CATEGORY 2: ABSTRACT/CONCEPT slides (cover, market_shock, market_problem,
      core_philosophy, proprietary_methodology, governance, cta_session, contact,
      creative_philosophy, brand_story, our_process) ──
   RULE: Use VISUAL METAPHOR — architectural, geometric, textural, atmospheric.
         ABSOLUTELY FORBIDDEN words: handshake, puzzle, gears, compass, dart,
         target, synergy, trust, process, system, flowchart, diagram, chart, strategy.
   GOOD: "abstract minimal geometric glass architecture dark studio"
         "soft volumetric light flowing through metallic texture"
         "calm dark ocean surface macro shot long exposure"
         "overlapping translucent acrylic panels diffused backlight"
         "brutalist concrete corridor dramatic shadow perspective"
   BAD:  "business trust handshake partnership", "synergy gears working together",
         "complex process flowchart diagram"

   ── CATEGORY 3: SERVICE/PILLAR slides (service_pillar_1, service_pillar_2, service_pillar_3,
      core_business_1, core_business_2, core_business_3, our_process) ──
   RULE: Show the WORKSPACE, TOOL, or ENVIRONMENT of the service — NOT data outputs.
         ABSOLUTELY FORBIDDEN: chart, charts, dashboard, analytics, data visualization,
         financial, metrics, growth chart, bar graph, performance graph.
   GOOD: "modern creative agency workspace dual monitors design work"
         "professional team brainstorming whiteboard strategy session"
         "close-up hands typing laptop minimal desk setup"
         "marketing campaign print materials spread flat lay"
   BAD:  "data visualization dashboard digital interface"
         "analytics charts financial performance metrics growth"

━━━━ FACTBOOK (리서처 추출 팩트 — 이 내용에 있는 것만 사용, 발명 절대 금지) ━━━━
{factbook}"""

    print("  [3단계-C] 카피라이터: 슬라이드 JSON 작성 중...")
    try:
        response = _client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": SLIDE_SYSTEM_PROMPT,
                "temperature": 0.25,
                "max_output_tokens": 32000,
            }
        )

        text = response.text.strip()
        
        def clean_json_text(s):
            """LLM 응답에서 순수 JSON 부분만 추출하고 청소"""
            # 1. Markdown 코드 블록 제거
            s = re.sub(r'```json\s*(.*?)\s*```', r'\1', s, flags=re.DOTALL)
            s = re.sub(r'```\s*(.*?)\s*```', r'\1', s, flags=re.DOTALL)
            
            # 2. 첫 번째 { 와 마지막 } 사이만 추출
            start = s.find('{')
            end = s.rfind('}')
            if start != -1 and end != -1:
                s = s[start:end+1]
            
            # 3. 제어 문자 제거 (줄바꿈 제외)
            s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
            return s.strip()

        cleaned_text = clean_json_text(text)
        
        def _inject_narrative(result):
            """Strategist가 결정한 narrative_type을 brand에 강제 주입"""
            if isinstance(result, dict):
                if 'brand' not in result:
                    result['brand'] = {}
                result['brand']['narrative_type'] = narrative_type
            return result

        def _recover_truncated_json(s):
            """토큰 한도로 잘린 JSON을 닫는 괄호 추가로 복구"""
            # 1) trailing comma 제거
            s = re.sub(r',\s*([\]}])', r'\1', s)
            # 2) 단독 줄 쉼표 보정
            s = re.sub(r'(\n[ \t]+\})\s*\n([ \t]+),', r'\1\n\2},', s)
            # 3) 잘린 문자열이 따옴표로 끊긴 경우: 마지막 따옴표 없는 문자열 닫기
            #    ex) "image_en_hint": "calm dark ocean → "image_en_hint": "calm dark ocean"
            s = re.sub(r':\s*"([^"]*?)$', lambda m: f': "{m.group(1)}"', s)
            # 4) 열린 괄호 개수 세어 부족한 닫는 괄호 추가
            opens = s.count('{') - s.count('}')
            arrs  = s.count('[') - s.count(']')
            # 잘린 위치에서 불완전한 마지막 키-값 쌍 제거 (쉼표로 끝나지 않는 불완전 항목)
            # slides 배열의 마지막 { 이후 } 없이 끊겼을 가능성 → 마지막 불완전 객체 제거
            if opens > 0:
                # 마지막 완결된 슬라이드 객체 이후를 찾아 잘라냄
                last_complete = s.rfind('},\n')
                if last_complete == -1:
                    last_complete = s.rfind('}')
                if last_complete > 0:
                    s = s[:last_complete + 1]
                    opens = s.count('{') - s.count('}')
                    arrs  = s.count('[') - s.count(']')
            # 닫는 괄호 추가
            s = s.rstrip().rstrip(',')
            s += ']' * max(arrs, 0) + '}' * max(opens, 0)
            return s

        try:
            return _inject_narrative(json.loads(cleaned_text))
        except json.JSONDecodeError:
            print("  ※ 표준 JSON 파싱 실패 → 잘린 JSON 복구 시도...")
            try:
                fixed_text = _recover_truncated_json(cleaned_text)
                result = json.loads(fixed_text)
                print(f"  ✅ JSON 복구 성공 — 슬라이드 {len(result.get('slides', []))}개")
                return _inject_narrative(result)
            except json.JSONDecodeError as e2:
                print(f"  ※ 복구 실패 ({e2}) → 재시도 없이 None 반환")

    except Exception as e:
        print(f"\n❌ JSON 생성/파싱 최종 오류: {e}")
        print("--- Gemini Raw Response Start ---")
        print(text if 'text' in locals() else "No response text")
        print("--- Gemini Raw Response End ---\n")
        return None



# ────────────────────────────────────────────
# 3. 배경 이미지 생성 (Gemini Imagen)
# ────────────────────────────────────────────

# Imagen 호출 간 최소 간격 (초) — 429 방지
_IMAGEN_MIN_INTERVAL = 10.0
_last_imagen_call = 0.0

def generate_bg_image(full_prompt, max_retries: int = 2):
    """
    Imagen 4.0으로 배경 이미지 생성 → base64 반환.
    - 호출 간격 최소 _IMAGEN_MIN_INTERVAL초 유지
    - 429 RESOURCE_EXHAUSTED 시 지수 백오프 재시도 (최대 max_retries회)
    - 타임아웃 또는 실패 시 None 반환 → CSS 그라디언트 폴백
    """
    global _last_imagen_call

    # ── 호출 간격 조절 ──
    elapsed = time.time() - _last_imagen_call
    if elapsed < _IMAGEN_MIN_INTERVAL:
        wait = _IMAGEN_MIN_INTERVAL - elapsed
        time.sleep(wait)

    import concurrent.futures
    _IMAGEN_CALL_TIMEOUT = 60  # 단일 API 호출 최대 대기 (초)

    def _call_imagen():
        return _client.models.generate_images(
            model='models/imagen-4.0-fast-generate-001',
            prompt=full_prompt,
            config=genai_types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="16:9",
            )
        )

    for attempt in range(1, max_retries + 2): # Increase max attempts slightly
        try:
            _last_imagen_call = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_call_imagen)
                try:
                    response = future.result(timeout=90) # Increased timeout to 90s
                except concurrent.futures.TimeoutError:
                    print(f"  이미지 생성 타임아웃 (90초 초과) → retry")
                    if attempt < max_retries + 1: continue
                    return None

            if response.generated_images:
                img_bytes = response.generated_images[0].image.image_bytes
                return base64.b64encode(img_bytes).decode('utf-8')

            print(f"  이미지 생성 응답 비어있음 (attempt {attempt})")
            return None

        except Exception as e:
            err_str = str(e)
            is_rate_limit = any(x in err_str for x in ['429', 'RESOURCE_EXHAUSTED', 'Quota'])

            if is_rate_limit and attempt <= max_retries:
                # Google API retryDelay 파싱 시도 (e.g. "retryDelay: '60s'")
                import re as _re
                retry_hint = _re.search(r'retryDelay["\s:]+(\d+)', err_str)
                backoff = int(retry_hint.group(1)) if retry_hint else 60 * attempt
                reset_at = time.strftime('%H:%M:%S', time.localtime(time.time() + backoff))
                print(f"  이미지 쿼터 초과 (attempt {attempt}/{max_retries}) → {backoff}초 대기 (재시도 예정 {reset_at})")
                time.sleep(backoff)
            else:
                print(f"  이미지 생성 건너뜀 (fallback 적용): {err_str[:120]}")
                return None

    return None


# ────────────────────────────────────────────
# 3.5. 배경 이미지 검색 (Pexels API - 우선 적용)
# ────────────────────────────────────────────

def _img_is_too_bright(b64: str, threshold: int = 210) -> bool:
    """이미지 평균 밝기 > threshold면 True (흰 배경 다이어그램/일러스트 제거용)"""
    try:
        import base64 as _b64m
        img_bytes = _b64m.b64decode(b64)
        img = _PILImage.open(io.BytesIO(img_bytes)).convert('L').resize((48, 27))
        pixels = list(img.getdata())
        return (sum(pixels) / len(pixels)) > threshold
    except Exception:
        return False
def search_pexels_image(keyword: str, industry: str = "business", max_retries: int = 1):
    """
    Pexels API를 사용하여 키워드에 맞는 이미지를 검색하고 Base64로 반환합니다.
    - industry 키워드를 결합하여 검색 결과의 비즈니스 관련성 강제 (예: "dogsear" -> "dogsear business")
    """
    if not PEXELS_API_KEY:
        print("  ※ PEXELS_API_KEY 없음 → Pexels 검색 건너뜀")
        return None
        
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    
    # _build_pexels_query로 이미 최적화된 키워드가 들어오는 경우 그대로 사용
    # 아닌 경우: 앞 4단어 + industry 조합
    _IND_BLACKLIST = re.compile(
        r'\b(coin|coins|bitcoin|crypto|cryptocurrency|token|blockchain|wallet|nft|'
        r'stock|stocks|trading|forex|candlestick|defi|web3|'
        r'money|dollar|currency|cash|fintech|financial.technology)\b',
        re.IGNORECASE
    )
    ind_part = (industry or "").strip()
    if not ind_part or _IND_BLACKLIST.search(ind_part):
        ind_part = ''

    # 키워드가 이미 4단어 이상이면 industry 중복 추가 안 함
    kw_words = keyword.split()
    if len(kw_words) >= 4 or (ind_part and ind_part.lower() in keyword.lower()):
        search_term = " ".join(kw_words[:5])
    else:
        hint_part = " ".join(kw_words[:4])
        search_term = f"{hint_part} {ind_part}".strip() if ind_part else hint_part
    
    params = {
        "query": search_term,
        "orientation": "landscape",
        "per_page": 10  # 여러 개 받아서 랜덤 선택
    }

    import random
    for attempt in range(max_retries + 1):
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            if r.status_code == 200:
                data = r.json()
                photos = data.get('photos', [])
                if photos:
                    # ── 결과 이미지 사후 필터: alt/photographer에 코인/금전 키워드 포함 시 제외 ──
                    _RESULT_BLACKLIST = re.compile(
                        r'\b(coin|coins|bitcoin|crypto|cryptocurrency|token|blockchain|nft|'
                        r'wallet|money|cash|dollar|currency|stock|trading|forex|gold|'
                        r'investment|finance|bank|savings|profit)\b',
                        re.IGNORECASE
                    )
                    filtered = [
                        p for p in photos[:5]
                        if not _RESULT_BLACKLIST.search(
                            (p.get('alt') or '') + ' ' + (p.get('photographer') or '')
                        )
                    ]
                    candidates = filtered if filtered else photos[:5]

                    # 너무 중복되지 않게 상위 결과 중 하나를 랜덤으로 선택
                    photo = random.choice(candidates)
                    img_url = photo.get('src', {}).get('original') or photo.get('src', {}).get('large2x')

                    if img_url:
                        img_resp = requests.get(img_url, headers=HEADERS, timeout=10)
                        if img_resp.status_code == 200:
                            b64 = base64.b64encode(img_resp.content).decode('utf-8')
                            return b64
            else:
                sc = r.status_code
                if sc == 429:
                    backoff = 30 * (attempt + 1)
                    reset_at = time.strftime('%H:%M:%S', time.localtime(time.time() + backoff))
                    print(f"  Pexels 쿼터 초과 (attempt {attempt+1}) → {backoff}초 대기 (재시도 예정 {reset_at})")
                    time.sleep(backoff)
                elif sc in (401, 403):
                    print(f"  Pexels API 인증 오류 (HTTP {sc}) → 재시도 중단")
                    return None
                else:
                    print(f"  Pexels API 에러 (attempt {attempt+1}): HTTP {sc}")

        except Exception as e:
            print(f"  Pexels 검색 예외 (attempt {attempt+1}): {e}")

    return None

# ── Imagen 절대 금지 — 반드시 실물 이미지(site pool 또는 Pexels)만 사용 ──────
REAL_IMAGE_ONLY_TYPES = {
    'service_pillar_1', 'service_pillar_2', 'service_pillar_3',
    'showcase_work_1', 'showcase_work_2', 'showcase_work_3',
    'case_study',
    'core_business_1', 'core_business_2', 'core_business_3',
    'flagship_experience',
}

# ── 무드별 카피 톤 지침 ───────────────────────────────────────────────────────
MOOD_TONE = {
    'trendy':       "톤앤매너: 속도감 있고 혁신적. 짧고 임팩트 있는 표현, 숫자와 결과 중심.",
    'professional': "톤앤매너: 신중하고 무게감 있는 B2B 보수적 어조. 신뢰와 전문성 강조.",
    'minimal':      "톤앤매너: 간결하고 여백 있는 표현. 핵심만 담고 군더더기 없이.",
}

# ── 무드별 Imagen 이미지 분위기 suffix ─────────────────────────────────────────
MOOD_IMAGE_SUFFIX = {
    'trendy':       "vibrant kinetic dynamic atmosphere, bold digital innovation energy",
    'professional': "clean authoritative premium quality, understated elegance, corporate",
    'minimal':      "quiet sophisticated minimal, monochrome subtle, clean white space",
}

# ────────────────────────────────────────────
# Python이 슬라이드 타입 → Imagen 프롬프트 100% 결정
# (Gemini에게 imagePrompt 맡기지 않음 — 품질/일관성 보장)
# ────────────────────────────────────────────
STYLE_SUFFIX = (
    "ultra dark background #080808, photorealistic 3D CGI render, "
    "cinematic studio lighting with dramatic rim light, "
    "no text, no letters, no numbers, 8K ultra detailed, "
    "premium brand visual, clean composition"
)

# ────────────────────────────────────────────────────────────────
# CONCEPT_PROMPTS: 슬라이드 타입별 전용 3D 오브젝트
# 설계 원칙:
#   1. 각 오브젝트는 구도가 예측 가능해야 함 → HTML 오버레이 레이블 정합
#   2. 오브젝트 자체가 슬라이드 메시지를 시각화
#   3. 텍스트 없이도 의미 전달 가능 → 범용 (회사 무관)
# ────────────────────────────────────────────────────────────────
CONCEPT_PROMPTS = {
    # COVER — 브랜드 심볼. 우측 절반에 대형 링/구체 배치
    # 구도: 우측 중앙에 오브젝트, 좌측은 여백 (텍스트 공간)
    "hero_ring": (
        "{subject}, serving as a focal point floating at right-center, "
        "designed with a premium branding aesthetic that complements the logo, "
        "soft neon highlights, deep black studio background, "
        "left half of image empty for headline, cinematic luxury lighting"
    ),
    # MARKET_SHOCK — 위기/혼돈 속 방향 상실
    # 내용: 마케팅 예산이 낭비되고 있다, 시장 경쟁 심화, 데이터 홍수
    # 구도: 우측에 폭발·분산되는 빛 파편들, 좌측 텍스트 공간
    "sphere_shift": (
        "{subject}, exploding outward from a central point on the right side of frame, "
        "chaotic swirling energy suggesting information overload and lost direction, "
        "deep dark background, sharp vivid neon fragments, "
        "left half of frame mostly dark empty space for text, "
        "cinematic tension and urgency"
    ),
    # MARKET_PROBLEM — 균열/붕괴
    # 구도: 우측에 부서지는 구조물, 좌측 텍스트 공간
    "cracked_structure": (
        "{subject}, cracking apart or breaking down on the right side of frame, "
        "vivid neon light spilling violently through the fractures and cracks, "
        "sharp debris fragments floating outward, "
        "left side mostly empty dark space, tension and urgency"
    ),
    # CORE_PHILOSOPHY — 교집합/시너지
    # 구도: 우측에 두 개의 반투명 구체가 교차, 교집합 부분 발광
    # → HTML이 좌구체/우구체/교집합 위에 레이블 올림
    "two_spheres_venn": (
        "{subject}, arranged as overlapping translucent elements on the right side of frame, "
        "the intersecting zone glows intensely with concentrated light, "
        "ultra dark background, glassmorphism material, left half empty for text"
    ),
    # PROPRIETARY_METHODOLOGY — 배경 분위기 (HTML이 glassmorphism 카드를 올림)
    # 이미지는 순수 배경 역할 — 패널/구조물 없이 깊이감 있는 공간감만 표현
    # HTML glassmorphism 카드와 겹치지 않도록 오브젝트 없는 구성
    "flow_panels": (
        "{subject}, flowing horizontally from left to right across the lower third of frame, "
        "soft ambient glow on the horizon line, "
        "pure atmospheric depth, upper area completely dark for headline text, "
        "cinematic wide shot, ultra dark background #050505"
    ),
    # SERVICE_PILLAR — 서비스 강점 시각화
    # 구도: 우측에 프리즘/크리스탈, 빛 굴절
    "crystal_prism": (
        "{subject}, acting as a central geometric focal point on the right side of frame, "
        "refracting a single beam of light into a vivid colored spectrum fan, "
        "dramatic dark studio, precision and clarity, "
        "left side empty dark space for text overlay"
    ),
    # SERVICE_PILLAR_2 — 퍼포먼스 마케팅/실행/타겟팅
    # 내용: 정교한 타겟팅, 다채널 광고, 실시간 최적화, ROAS
    # 구도: 우측에 여러 방향으로 날아가는 빛살 화살표들이 하나의 중심 타겟을 향해 수렴
    "network_hub": (
        "{subject}, converging precisely onto a single glowing target point "
        "on the right side of frame, each element a different vivid color, "
        "high velocity streaks with motion blur, ultra precise targeting energy, "
        "dark background with subtle grid lines, "
        "performance and execution momentum, left side dark space for text"
    ),
    # SERVICE_PILLAR_3 — 고객 관계/LTV/충성도
    # 내용: CRM, 고객 세분화, 재구매율, 고객 생애 가치
    # 구도: 우측에 여러 작은 구체들이 하나의 큰 중심 구체 주위를 공전
    "growth_helix": (
        "{subject}, connected by elegant curved light trails revolving around a core, "
        "the orbiting pattern suggesting relationship and loyalty, "
        "right side of frame, deep dark background, "
        "neon particle trails, left side dark empty space for text"
    ),
    "growth_bars": (
        "{subject}, rising dynamically from left to right in a sequence, "
        "tallest rightmost part glowing intensely with neon energy at its peak, "
        "dark reflective floor, dramatic uplighting, "
        "cinematic upward momentum, success and achievement"
    ),
    # CASE_STUDY — 실질적 성과와 데이터의 흐름
    # 구도: 우측에 우상향하는 유기적인 데이터 흐름/경로
    "growth_data_path": (
        "{subject}, forming an elegant organic path of glowing data points "
        "curving sharply upward and toward the right-center background, "
        "suggesting a clear journey of growth and measurable success, "
        "soft light trails, deep dark void, "
        "left side empty for case study details"
    ),
    # TEAM_INTRO — 사람/조직
    "orbital_nodes": (
        "{subject}, arranged in an orbital pattern connected by elegant light arcs, "
        "one central brighter core element, "
        "floating in deep dark space, team and expertise constellation, "
        "right-center composition"
    ),
    # GOVERNANCE / TRUST
    "shield_structure": (
        "{subject}, forming a glowing geometric framework floating right-center, "
        "inner structure visible through translucent surface, "
        "steady solid neon edge glow, trust and stability, "
        "dark background, architecture of governance"
    ),
    # CTA_SESSION — 행동 촉구, 소용돌이
    # 문제: 무채색으로 생성되지 않도록 색상 힌트 강조
    "vortex_pull": (
        "{subject}, forming a deep luminous vortex tunnel, "
        "pulling inward toward a brilliant bright center point, "
        "pulsing with intense saturated neon color, NOT grey NOT monochrome, "
        "energy streams spiraling inward with particle trails, "
        "centered composition filling the frame, "
        "dynamic urgency and momentum, ultra dark background"
    ),
    # CONTACT — 연결/접점
    "connection_spark": (
        "{subject}, with platform islands floating apart and a brilliant spark bridge "
        "of light connecting them at center, particles traveling across, "
        "dark void, moment of connection and contact, centered composition"
    ),
}

TYPE_TO_CONCEPT = {
    'cover':                   'hero_ring',
    'market_shock':            'sphere_shift',
    'market_problem':          'cracked_structure',
    'core_philosophy':         'two_spheres_venn',
    'proprietary_methodology': 'flow_panels',
    'service_pillar_1':        'crystal_prism',
    'service_pillar_2':        'network_hub',
    'service_pillar_3':        'growth_helix',
    'proof_of_concept':        'growth_bars',
    'case_study':              'growth_data_path',
    'team_intro':              'orbital_nodes',
    'governance':              'shield_structure',
    'cta_session':             'vortex_pull',
    'contact':                 'connection_spark',
    # 레거시 호환
    'title_identity':          'hero_ring',
    'market_insights':         'sphere_shift',
    'problem':                 'cracked_structure',
    'service':                 'crystal_prism',
    'results':                 'growth_bars',
    # ── Type B (산업 주도형) ──────────────────────────────
    'corporate_overview':      'orbital_nodes',
    'infrastructure_and_scale':'shield_structure',
    'core_business_1':         'crystal_prism',
    'core_business_2':         'network_hub',
    'core_business_3':         'growth_helix',
    'global_partnership':      'shield_structure',
    # ── Type C (포트폴리오 중심형) ──────────────────────────
    'creative_philosophy':     'two_spheres_venn',
    'our_process':             'flow_panels',
    'showcase_work_1':         'growth_data_path',
    'showcase_work_2':         'growth_bars',
    'showcase_work_3':         'growth_data_path',
    'client_list':             'orbital_nodes',
    # ── Type D (가치 제안형) ──────────────────────────────
    'brand_story':             'two_spheres_venn',
    'flagship_experience':     'crystal_prism',
    'target_audience':         'cracked_structure',
    'market_impact':           'growth_bars',
    'section_divider':         'flow_panels',
    # ── 분석 프레임워크 (IR/Report) ───────────────────────
    'positioning_matrix':      'two_spheres_venn',
    'comparison_matrix':       'two_spheres_venn',
}

# 슬라이드 타입별 색온도/분위기 — STYLE_SUFFIX의 단조로움을 깨기 위한 강제 차별화
TYPE_MOOD = {
    'cover':                   'warm golden sunrise glow, luxury brand hero mood',
    'market_shock':            'urgent red-orange alarm light, high tension cinematic',
    'market_problem':          'cold ice-blue fractured light, crisis atmosphere',
    'core_philosophy':         'deep indigo violet philosophy, ethereal contemplative',
    'proprietary_methodology': 'teal-cyan electric technology pulse, systematic precision',
    'service_pillar_1':        'electric cobalt blue clarity, sharp precision engineering',
    'service_pillar_2':        'vivid lime-green growth energy, dynamic momentum',
    'service_pillar_3':        'coral orange warm energy, human connection warmth',
    'proof_of_concept':        'golden amber achievement glow, triumphant success',
    'case_study':              'emerald green data flow, analytical insight',
    'team_intro':              'soft lavender purple collaboration, human expertise',
    'governance':              'steel-blue authority trust, solid reliable structure',
    'cta_session':             'magenta-purple vortex action, intense call-to-action urgency',
    'contact':                 'warm white-gold connection spark, open welcoming light',
    # aliases
    'title_identity':          'warm golden sunrise glow, luxury brand hero mood',
    'market_insights':         'urgent red-orange alarm light, high tension cinematic',
    'problem':                 'cold ice-blue fractured light, crisis atmosphere',
    'service':                 'electric cobalt blue clarity, sharp precision engineering',
    'results':                 'golden amber achievement glow, triumphant success',
    # ── Type B ────────────────────────────────────────────
    'corporate_overview':      'soft lavender purple collaboration, human expertise',
    'infrastructure_and_scale':'teal-cyan electric technology pulse, systematic precision',
    'core_business_1':         'electric cobalt blue clarity, sharp precision engineering',
    'core_business_2':         'vivid lime-green growth energy, dynamic momentum',
    'core_business_3':         'coral orange warm energy, human connection warmth',
    'global_partnership':      'steel-blue authority trust, solid reliable structure',
    # ── Type C ────────────────────────────────────────────
    'creative_philosophy':     'deep indigo violet philosophy, ethereal contemplative',
    'our_process':             'teal-cyan electric technology pulse, systematic precision',
    'showcase_work_1':         'electric cobalt blue clarity, sharp precision engineering',
    'showcase_work_2':         'vivid lime-green growth energy, dynamic momentum',
    'showcase_work_3':         'coral orange warm energy, human connection warmth',
    'client_list':             'steel-blue authority trust, solid reliable structure',
    # ── Type D ────────────────────────────────────────────
    'brand_story':             'warm golden sunrise glow, luxury brand hero mood',
    'flagship_experience':     'electric cobalt blue clarity, sharp precision engineering',
    'target_audience':         'cold ice-blue fractured light, crisis atmosphere',
    'market_impact':           'golden amber achievement glow, triumphant success',
    'section_divider':         'dramatic dark architectural atmosphere, bold chapter transition',
    # ── 분석 프레임워크 ─────────────────────────────────────
    'positioning_matrix':      'cold precise strategic blue grid lines, analytical framework precision',
    'comparison_matrix':       'cold precise strategic blue grid lines, analytical framework precision',
}


# ── Pexels 슬라이드 타입별 전용 쿼리 ─────────────────────────────────────────
# 원칙: 사진 DB 검색에 최적화된 구체적 명사/장면 2~4단어 조합
# "abstract glowing digital" 같은 Imagen 스타일은 Pexels에서 결과 없음
_PEXELS_TYPE_QUERIES: dict[str, str] = {
    # 브랜드/서비스 — 실제 회사 느낌을 주는 장면
    'service_pillar_1':   'technology office workspace professional',
    'service_pillar_2':   'team collaboration meeting modern',
    'service_pillar_3':   'network city architecture digital',
    'core_business_1':    'industrial precision technology modern',
    'core_business_2':    'global connectivity network office',
    'core_business_3':    'innovation growth startup workspace',
    'team_intro':         'diverse team professionals smiling',
    'case_study':         'business success results meeting',
    'brand_story':        'creative studio brand elegant minimal',
    'flagship_experience':'premium product luxury quality',
    'governance':         'executive conference room corporate',
    'showcase_work_1':    'marketing campaign results business success',
    'showcase_work_2':    'digital marketing analytics performance growth',
    'showcase_work_3':    'business achievement client results meeting',
    'client_list':        'business partners handshake professional',
    'cta_session':        'leadership vision forward action',
    'contact':            'communication phone office professional',
    # 컨셉/시장 — 시각적 은유 장면
    'market_shock':       'dramatic storm disruption dark sky',
    'market_problem':     'challenge obstacle problem dark moody',
    'market_insights':    'data research discovery analysis',
    'market_impact':      'growth success achievement professional',
    'corporate_overview': 'city skyline skyscraper modern',
    'infrastructure_and_scale': 'industrial infrastructure engineering scale',
    'proof_of_concept':   'business results clients success professional',
    'core_philosophy':    'philosophy balance light minimal',
    'our_process':        'process steps workflow organized',
    'target_audience':    'diverse people community lifestyle',
    'proprietary_methodology': 'systematic approach method lab',
    'results':            'success achievement celebration office',
    'impact':             'transformation growth before after',
    'section_divider':    'architecture space modern dramatic',
}


def _build_pexels_query(slide: dict, industry: str = "", company_name: str = "") -> str:
    """Pexels 검색에 최적화된 쿼리 생성
    - 슬라이드 타입 전용 쿼리 (2~4 구체적 명사)
    - 없으면 image_en_hint 앞 3단어 + 산업 키워드 조합
    - 회사명, 추상 수식어, AI 생성 전용 단어 제거
    """
    stype = slide.get('type', '')

    # 1순위: 타입 전용 쿼리 — 가장 정확한 Pexels 결과
    if stype in _PEXELS_TYPE_QUERIES:
        base = _PEXELS_TYPE_QUERIES[stype]
        # 산업 키워드가 아직 없으면 뒤에 추가 (최대 5단어 유지)
        if industry and industry.lower() not in base.lower():
            ind_word = industry.strip().split()[0]
            return f"{base} {ind_word}"
        return base

    # 2순위: image_en_hint 앞 3단어 (추상 수식어 제거)
    _ABSTRACT_WORDS = re.compile(
        r'\b(abstract|glowing|geometric|futuristic|volumetric|cinematic|'
        r'photorealistic|visualization|dimensional|neon|holographic|'
        r'flowing|dynamic|ethereal)\b', re.I)
    hint = (slide.get('image_en_hint') or '').strip()
    if hint:
        hint = _ABSTRACT_WORDS.sub('', hint)
        hint = re.sub(r'\s+', ' ', hint).strip()
        words = [w for w in hint.split() if len(w) > 3][:3]
        if words:
            if industry:
                words.append(industry.strip().split()[0])
            return ' '.join(words)

    # 3순위: 산업 + 직종 느낌 일반 쿼리
    ind = industry.strip().split()[0] if industry else 'business'
    return f"{ind} office professional modern"


def _extract_en_hint(slide: dict, company_name: str = "") -> str:
    """슬라이드에서 Imagen 프롬프트에 활용될 영어 힌트 추출 (회사명 제외)
    ※ Pexels 검색에는 _build_pexels_query() 사용"""
    import re
    exclude = (company_name or "").lower().strip()
    
    def clean_hint(text):
        if not text: return ""
        # 회사명이 포함되어 있다면 삭제 (대소문자 무시)
        if exclude:
            text = re.sub(re.escape(exclude), '', text, flags=re.IGNORECASE)
        # 불필요한 공백 및 문장 부호 정리
        text = re.sub(r'\s+', ' ', text).strip(', ')
        return text

    # ── 클리셰/비관련 블랙리스트 — 촌스러운 비즈니스·코인·주식 이미지 방지 ──
    _HINT_BLACKLIST = re.compile(
        r'\b(handshake|puzzle|gear|gears|compass|dart|dartboard|target|'
        r'synergy|teamwork|strategy|workflow|flowchart|diagram|chart|'
        r'checklist|clipboard|trophy|lightbulb|magnifying|shaking.hands|high.five|'
        r'coin|coins|bitcoin|crypto|cryptocurrency|token|blockchain|wallet|nft|'
        r'stock|stocks|trading|forex|candlestick|'
        r'money|dollar|dollars|currency|cash|banknote|'
        r'bar.chart|pie.chart|line.chart|bar.graph|pie.graph|'
        r'charts|financial|analytics|dashboard|graph|graphs|'
        r'metrics|metric|visualization|performance.chart|growth.chart)\b',
        re.IGNORECASE
    )
    _HINT_FALLBACK = 'abstract minimal geometric architecture dark moody'

    def apply_blacklist(text: str) -> str:
        cleaned = _HINT_BLACKLIST.sub('', text).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(', ')
        return cleaned if len(cleaned) > 8 else _HINT_FALLBACK

    # 1순위: Gemini가 생성한 image_en_hint (블랙리스트 필터 적용)
    hint = clean_hint(slide.get('image_en_hint', ''))
    if hint:
        # 핑크 코끼리 역설 방어: 블랙리스트 단어가 있으면 힌트 전체를 안전한 추상화로 교체
        if _HINT_BLACKLIST.search(hint):
            hint = "abstract digital network connections and glowing geometric data structures"
        else:
            hint = apply_blacklist(hint)
        words = hint.split()
        return " ".join(words[:8])

    # 2순위: keywords 배열 중 영문만 (회사명 제외)
    kws = []
    for kw in (slide.get('keywords') or []):
        kw = clean_hint(str(kw))
        if kw and re.match(r'^[A-Za-z0-9 \-]+$', kw):
            kws.append(kw)
    if kws:
        return " ".join(kws[:3])
        
    # 3순위: 영문 subheadline (회사명 제외)
    sub = clean_hint(slide.get('subheadline', ''))
    if sub and re.match(r'^[A-Za-z0-9 ,\-&./]+$', sub):
        return " ".join(sub.split()[:4])
        
    # 4순위: headline에서 영어 단어 추출 (회사명 제외)
    headline = clean_hint(slide.get('headline', ''))
    en_words = re.findall(r'[A-Za-z][A-Za-z0-9\-]{2,}', headline)
    if en_words:
        return " ".join(en_words[:3])
        
    # 슬라이드 타입별 전용 폴백 키워드 (비즈니스/코인/주식 클리셰 완전 배제)
    stype = slide.get('type', '')
    _type_fallbacks = {
        'service_pillar_1': 'precision technology innovation architecture',
        'service_pillar_2': 'performance network digital momentum',
        'service_pillar_3': 'connection relationship ecosystem orbit',
        'market_shock':     'disruption chaos transformation explosion',
        'market_problem':   'fractured structure tension dark void',
        'core_philosophy':  'philosophy convergence intersection balance',
        'proof_of_concept': 'ascending momentum growth achievement',
        'case_study':       'data analytics journey success metrics',
        'team_intro':       'constellation expertise professionals network',
        'governance':       'architecture trust structure framework',
        'cta_session':      'vortex action momentum urgency',
        'contact':          'connection spark bridge communication',
        'corporate_overview':       'enterprise scale infrastructure global',
        'infrastructure_and_scale': 'infrastructure industrial precision scale',
        'core_business_1':  'industrial precision technology solution',
        'core_business_2':  'global network digital connectivity',
        'core_business_3':  'innovation ecosystem growth orbit',
        'global_partnership': 'global bridge partnership alliance',
        'showcase_work_1':  'creative design craftsmanship precision',
        'showcase_work_2':  'digital experience interface elegance',
        'showcase_work_3':  'brand identity visual storytelling',
        'creative_philosophy': 'creative philosophy vision inspiration',
        'our_process':      'systematic process flow methodology',
        'client_list':      'constellation clients portfolio excellence',
        'brand_story':      'luxury heritage philosophy values',
        'flagship_experience': 'premium quality elevation refinement',
        'target_audience':  'focus target precision audience',
        'market_impact':    'impact achievement momentum transformation',
    }
    return _type_fallbacks.get(stype, 'abstract technology architecture minimal')


def _generate_visual_theme_seed(company_name: str, narrative_type: str,
                                industry: str, progress_fn=None) -> str:
    """
    Gemini로 회사의 시각적 테마 키워드를 추출.
    모든 Imagen 프롬프트 앞에 prefix로 붙여 이미지 스타일 일관성 확보.
    실패 시 narrative_type별 기본값 반환.
    """
    def _p(m):
        if progress_fn: progress_fn(str(m))

    _defaults = {
        'A': 'sleek digital minimalist, deep navy and electric blue palette',
        'B': 'industrial precision monumental, dark steel and amber glow',
        'C': 'bold creative editorial, vivid gradient and white space',
        'D': 'warm lifestyle premium, soft light and natural textures',
        'E': 'networked ecosystem dynamic, interconnected glowing nodes',
    }
    prompt = (
        f"You are a visual art director. Choose 5 visual style keywords capturing the brand's visual world.\n"
        f"Output ONLY a comma-separated list of 5 style descriptors in English.\n"
        f"Examples: \"cyberpunk neon, brutalist geometry, organic fluid, cinematic fog, holographic glass\"\n"
        f"Company: {company_name} | Industry: {industry} | Narrative type: {narrative_type}"
    )
    try:
        resp = _client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.7, "max_output_tokens": 80}
        )
        seed = resp.text.strip().strip('"').strip("'")
        if seed and len(seed) > 5:
            _p(f"  → Visual Theme Seed: {seed}")
            return seed
    except Exception as e:
        _p(f"  ⚠ Visual Theme Seed 생성 실패 (기본값 사용): {e}")
    return _defaults.get(narrative_type, _defaults['A'])


def build_image_prompt(slide_type: str, accent: str = '#7B5CF0',
                       industry: str = None, en_hint: str = None,
                       mood: str = 'professional',
                       theme_seed: str = None) -> str:
    """슬라이드 타입 → TYPE_TO_CONCEPT → CONCEPT_PROMPTS → 최종 Imagen 프롬프트 조립.
    industry와 en_hint로 회사/슬라이드별 고유 이미지 생성."""
    concept = TYPE_TO_CONCEPT.get(slide_type, 'abstract dark tech')
    base_template = CONCEPT_PROMPTS.get(concept, "{subject}, floating geometric shapes")

    # subject 결정 로직 (en_hint 최우선)
    subject = en_hint if en_hint else (f"abstract 3d visualization for {industry}" if industry else "abstract 3d visualization")

    # 템플릿에 subject 주입
    base = base_template.replace("{subject}", subject)

    # 추가 문맥은 base 뒤에 붙이기 (선택)
    ctx = f", representing {industry}" if industry and not en_hint else ""

    # ── 슬라이드 타입별 색온도/분위기 — 페이지 간 시각적 차별화 ──
    type_mood = TYPE_MOOD.get(slide_type, '')

    # ── 무작위 질감 변이(Jitter) ──
    import random
    jitters = [
        "minimalist geometric accent", "complex glass refraction",
        "soft volumetric fog", "sharp digital grid textures",
        "organic particle dust", "holographic chromatic aberration"
    ]
    jitter = random.choice(jitters)

    type_mood_str = f", {type_mood}" if type_mood else ""
    mood_img = MOOD_IMAGE_SUFFIX.get(mood, '')
    mood_img_str = f", {mood_img}" if mood_img else ""
    seed_prefix = f"{theme_seed}, " if theme_seed else ""
    return f"{seed_prefix}{base}{ctx}{type_mood_str}, {accent} vibrant neon accent glow, {jitter} style{mood_img_str}, {STYLE_SUFFIX}, pure abstract geometric composition, floating glowing data nodes, highly abstract representation"

OVERLAY_OPACITY = {
    "cover":                   0.42,
    "market_shock":            0.62,
    "market_problem":          0.65,
    "core_philosophy":         0.72,
    "proprietary_methodology": 0.80,
    "service_pillar_1":        0.62,
    "service_pillar_2":        0.62,
    "service_pillar_3":        0.65,
    "proof_of_concept":        0.72,
    "case_study":              0.72,
    "governance":              0.68,
    "cta_session":             0.85,
    "contact":                 0.80,
    "team_intro":              0.72,
    "title_identity":          0.52,
    "market_insights":         0.62,
    "problem":                 0.60,
    "service":                 0.65,
    "results":                 0.60,
    # ── Type B ────────────────────────────────────────────
    "corporate_overview":      0.70,
    "infrastructure_and_scale":0.65,
    "core_business_1":         0.62,
    "core_business_2":         0.62,
    "core_business_3":         0.65,
    "global_partnership":      0.68,
    # ── Type C ────────────────────────────────────────────
    "creative_philosophy":     0.72,
    "our_process":             0.80,
    "showcase_work_1":         0.55,
    "showcase_work_2":         0.55,
    "showcase_work_3":         0.58,
    "client_list":             0.68,
    # ── Type D ────────────────────────────────────────────
    "brand_story":             0.60,
    "flagship_experience":     0.58,
    "target_audience":         0.65,
    "market_impact":           0.70,
}




# ────────────────────────────────────────────
# 유털리티
# ────────────────────────────────────────────
def _b64_mime(b64: str) -> str:
    """base64 문자열에서 MIME 타입 감지 (png/jpeg/webp/svg+xml)"""
    if not b64:
        return 'png'
    try:
        head = base64.b64decode(b64[:80] + '==')[:40].decode('utf-8', errors='ignore')
        if '<svg' in head or '<?xml' in head:
            return 'svg+xml'
    except Exception:
        pass
    if b64.startswith('/9j/'):
        return 'jpeg'
    if b64.startswith('UklGR'):
        return 'webp'
    return 'png'


# ────────────────────────────────────────────
# TOC 슬라이드 자동 생성
# ────────────────────────────────────────────
def _build_toc_slide(slides: list) -> dict | None:
    """
    슬라이드 목록을 보고 TOC 슬라이드를 자동 생성.
    cover/cta/toc 제외 + 의미 있는 headline 있는 슬라이드만 수집.
    항목이 2개 미만이면 None 반환.
    """
    skip_types = {'cover', 'title_identity', 'cta', 'cta_session', 'contact', 'toc'}
    items = []
    for s in slides:
        if s.get('type', '') in skip_types:
            continue
        hl = (s.get('headline') or '').strip()
        if hl and hl not in items:
            items.append(hl)
        if len(items) >= 7:
            break

    if len(items) < 2:
        return None

    return {
        "type": "toc",
        "headline": "INDEX",
        "subheadline": "",
        "body": items,
        "bg_b64": "",
        "bg_mime": "png",
        "overlay_opacity": 0,
    }


# ────────────────────────────────────────────
# 7. 메인 파이프라인
# ────────────────────────────────────────────
def run_pipeline(url: str, company_name: str = None, progress_fn=None,
                 narrative_type: str = None, mood: str = 'professional',
                 purpose: str = 'brand') -> dict:
    """
    AI 데이터 엔진 파이프라인: 크롤링 → Gemini JSON → 이미지 생성 → dict 반환

    Args:
        url: 대상 웹사이트 URL
        company_name: 회사명 (미지정시 URL 도메인에서 자동 추출)
        progress_fn: 진행 상황 콜백 함수 (line: str) -> None
        narrative_type: 내러티브 타입 강제 지정 ('A'/'B'/'C'/'D'/'auto'/None)
        mood: 디자인 무드 ('professional'/'trendy'/'minimal')

    Returns:
        dict: {brand, slides, meta} 형태의 슬라이드 데이터
    """
    storyline = []        # 모든 코드 경로에서 참조 가능하도록 최상단 초기화
    page_subject = {}     # 아티스트/그룹 페이지 감지 결과

    def _p(msg):
        if progress_fn:
            progress_fn(str(msg))
        else:
            try:
                sys.stderr.write(str(msg) + '\n')
                sys.stderr.flush()
            except Exception:
                pass

    def _score_slide(slide: dict, prev_slide: dict = None) -> dict:
        """슬라이드 품질 채점 — 5개 항목 각 0~10점, 평균 반환

        설계 원칙: 올바르게 구성된 슬라이드는 자연스럽게 7.5 이상을 받아야 한다.
        보완 루프는 진짜 문제(이미지 누락, 수량 불일치 등)에만 개입.
        """
        stype = slide.get('type', '')
        scores = {}

        # ── 1. 헤드라인 길이 ──────────────────────────────────────
        # 22자 이하 = 임팩트 있는 슬라이드 헤드라인 (한/영 기준)
        # 길어질수록 슬라이드에서 가독성 저하 → 엄격하게 감점
        hl_text = (slide.get('headline') or '').strip()
        hl_len = len(hl_text)
        _VAGUE_HL = ['좋은', '최고의', '다양한', '훌륭한', '뛰어난', '혁신적', '전문적',
                     '맞춤형', '최적화된', '특별한', '더 나은', '새로운 시대', '가능성']
        if hl_len == 0:
            scores['headline'] = 10
        elif hl_len <= 22:
            _hl_base = 10
            if any(kw in hl_text for kw in _VAGUE_HL):
                _hl_base = max(_hl_base - 2, 4)
            scores['headline'] = _hl_base
        else:
            _hl_base = max(4, 10 - (hl_len - 22) // 3)
            if any(kw in hl_text for kw in _VAGUE_HL):
                _hl_base = max(_hl_base - 2, 4)
            scores['headline'] = _hl_base

        # ── 2. Body 밀도 ───────────────────────────────────────────
        nb = len(slide.get('body') or [])
        # 헤드라인/인용 중심 레이아웃: body 0이어도 정상
        _no_body_ok = {
            'cover', 'cta_session', 'section_break', 'contact',
            'pull_quote', 'big_statement', 'key_insight', 'quote_slide',
            'section_intro', 'section_header', 'chapter_break',
        }
        if nb == 0:         scores['body'] = 8 if stype in _no_body_ok else 3
        elif 2 <= nb <= 5:  scores['body'] = 10
        elif nb == 1:       scores['body'] = 7
        else:               scores['body'] = 6   # 6개 이상은 밀도 과잉

        # ── 3. 정보 계층 완성도 ────────────────────────────────────
        # sub: 있으면 최상. eyebrow는 stype에서 자동생성되므로 항상 존재로 간주.
        # Gemini가 명시적으로 eyebrow/sub를 설정했는지가 품질 지표
        has_sub = bool((slide.get('sub') or '').strip())
        has_ew_explicit = bool((slide.get('eyebrow') or slide.get('section_label') or '').strip())
        if stype in ('cover', 'cta_session'):
            scores['hierarchy'] = 10 if has_sub else 7
        elif has_sub:
            scores['hierarchy'] = 10
        elif has_ew_explicit:
            scores['hierarchy'] = 8
        else:
            scores['hierarchy'] = 7    # eyebrow 미설정 — _improve_slide()에서 보완

        # ── 4. 이미지 유무 ─────────────────────────────────────────
        # 이미지가 디자인에 쓰이지 않는 레이아웃은 평가 제외(만점)
        # 이미지가 필수인 레이아웃(split/portfolio)은 없으면 강하게 감점
        has_img = bool(slide.get('bg_b64'))
        _img_required = {'split', 'portfolio', 'comparison', 'mosaic'}
        _img_irrelevant = {
            'contact', 'cta_session', 'cta',
            'toc', 'table_of_contents', 'index',
            'section_intro', 'section_break', 'section_header',
            'section_divider', 'chapter_break',
            'numbered_process', 'process_cards', 'kpi_cards',
            'timeline_h', 'ruled_list', 'data_table',
            'pull_quote', 'big_statement', 'key_insight', 'quote_slide',
            'problem_solution', 'before_after_compare', 'asis_tobe',
        }
        if has_img or stype in _img_irrelevant:
            scores['image'] = 10
        elif stype in _img_required:
            scores['image'] = 4        # 필수 타입에 이미지 없음 — 실제 문제
        else:
            scores['image'] = 7        # 선택적 타입, 이미지 없음

        # ── 5. 헤드라인-바디 수량 일관성 ──────────────────────────
        # "5단계", "3가지", "4개" 등 숫자 언급이 실제 body 수와 일치하는지 검사
        _num_match = re.search(r'([2-9]|1[0-2])\s*(단계|가지|개|종|항목|스텝|step)', hl_text, re.IGNORECASE)
        if _num_match:
            claimed_n = int(_num_match.group(1))
            if nb >= claimed_n:
                scores['consistency'] = 10
            elif nb == claimed_n - 1:
                scores['consistency'] = 6   # 1개 부족 — 경고
            else:
                scores['consistency'] = max(2, 10 - (claimed_n - nb) * 3)   # 2개+ 부족
        else:
            scores['consistency'] = 10  # 수량 언급 없으면 만점

        # ── 6. 인접 슬라이드 body 중복 패널티 ─────────────────────────
        if prev_slide:
            _prev_tokens = set(' '.join(prev_slide.get('body') or []).split())
            _curr_tokens = set(' '.join(slide.get('body') or []).split())
            if _prev_tokens and _curr_tokens:
                _overlap = len(_prev_tokens & _curr_tokens) / max(len(_curr_tokens), 1)
                if _overlap >= 0.55:
                    scores['consistency'] = max(scores['consistency'] - 3, 2)

        total = round(sum(scores.values()) / len(scores), 1)
        return {'breakdown': scores, 'total': total}

    def _improve_slide(slide: dict, score: dict):
        """점수 낮은 항목을 규칙 기반으로 보완 — 변경 없으면 None 반환"""
        import copy
        bd = score['breakdown']
        improved = copy.deepcopy(slide)
        changed = False

        # 헤드라인이 길면 구두점 기준으로 자르기
        if bd.get('headline', 10) < 7:
            hl = improved.get('headline', '')
            for sep in [':', ' - ', ',', '·', '—']:
                if sep in hl:
                    improved['headline'] = hl.split(sep)[0].strip()
                    changed = True; break
            else:
                improved['headline'] = hl[:22].strip()
                changed = True

        # eyebrow 없으면 슬라이드 타입에서 자동 생성
        if bd.get('hierarchy', 10) < 8 and not (improved.get('eyebrow') or '').strip():
            _ew_map = {
                'service_pillar': '핵심 서비스', 'problem': '문제 인식',
                'solution': '솔루션',            'benefit': '주요 이점',
                'feature': '주요 기능',          'case_study': '성공 사례',
                'team': '팀 소개',               'contact': '문의',
                'toc': '목차',                   'market': '시장 분석',
                'pain': '문제 분석',             'proof': '성과 증명',
                'why': '차별점',                 'how': '실행 방법',
                'key_metric': '핵심 지표',       'overview': '솔루션 개요',
                'challenge': '시장 현황',        'cta': '지금 시작하기',
            }
            stype2 = improved.get('type', '')
            for key, label in _ew_map.items():
                if key in stype2 and label:
                    improved['eyebrow'] = label
                    changed = True; break

        # body 없는데 sub 내용 있으면 sub → body[0] 승격
        if bd.get('body', 10) < 5 and not (improved.get('body') or []) and (improved.get('sub') or '').strip():
            improved['body'] = [improved['sub']]
            changed = True

        # sub 없으면 body 첫 항목에서 자동 파생
        # hierarchy < 8이고 cover/contact 제외 슬라이드에 적용
        stype_local = improved.get('type', '')
        _sub_skip = {'cover', 'contact', 'cta_session', 'section_intro', 'section_break',
                     'section_header', 'chapter_break', 'toc'}
        if (bd.get('hierarchy', 10) < 8
                and stype_local not in _sub_skip
                and not (improved.get('sub') or '').strip()):
            _body_items = improved.get('body') or []
            if _body_items:
                _first = str(_body_items[0])
                # 콜론 뒤 결과 부분 추출 (RULE H 포맷: "원인: 결과")
                _colon = _first.find(':')
                if _colon > 0 and _colon < len(_first) - 3:
                    _sub_cand = _first[_colon + 1:].strip()
                else:
                    _sub_cand = _first
                # 화살표 이후 최종 결과만 남기기
                if '→' in _sub_cand:
                    _sub_cand = _sub_cand.split('→')[-1].strip()
                # 25자 이내로 자르기
                _sub_cand = _sub_cand[:30].strip()
                if len(_sub_cand) >= 8:
                    improved['sub'] = _sub_cand
                    changed = True

        # 헤드라인-바디 수량 불일치: 헤드라인에서 숫자 제거
        # (예: "5단계 프로세스" → "프로세스", body가 4개뿐일 때)
        if bd.get('consistency', 10) < 8:
            hl = improved.get('headline', '')
            hl_fixed = re.sub(
                r'\s*([2-9]|1[0-2])\s*(단계|가지|개|종|항목|스텝|step)\s*',
                ' ', hl, flags=re.IGNORECASE
            ).strip()
            if hl_fixed != hl and len(hl_fixed) > 3:
                improved['headline'] = hl_fixed
                changed = True

        return improved if changed else None

    # ── 아티스트/그룹 페이지 자동 감지 (URL 패턴 기반) ──────────────────────
    page_subject = _detect_page_subject(url)
    if page_subject:
        _p(f"  [주체 감지] {page_subject['subject_name']} ({page_subject['subject_type']}) 페이지")
        if not company_name:
            company_name = page_subject['subject_name']
            _p(f"  → company_name = '{company_name}'")
        # 아티스트 페이지 → C타입 강제 (이미지 중심 크리에이티브 레이아웃)
        if not narrative_type or narrative_type == 'auto':
            narrative_type = 'C'
            _p(f"  → narrative_type = C (아티스트 페이지 자동 적용)")

    if not company_name:
        domain = re.sub(r'^www\.', '', urlparse(url).netloc)
        company_name = domain.split('.')[0]
        _p(f"  ※ 회사명 미지정 → URL에서 자동 추출: '{company_name}'")

    _p(f"\n=== Web to Slide v4: {url} ===\n")
    _p(f"  [용도] {_PURPOSE_CONTEXT.get(purpose, purpose or 'brand')} (narrative_type={narrative_type or 'auto'})")

    # 분리 캐시 파일 (텍스트/이미지 분리로 ~1MB vs ~11MB 절감)
    _text_cache = f"slide_{company_name}_text.json"
    _img_cache  = f"slide_{company_name}_img.json"
    _legacy_cache = f"slide_{company_name}.json"   # 구버전 통합 캐시 (마이그레이션용)

    def _delete_cache():
        """텍스트/이미지 캐시 파일 삭제 (에러 시 자동 초기화용)"""
        for _cf in [_text_cache, _img_cache, _legacy_cache]:
            try:
                if os.path.exists(_cf):
                    os.remove(_cf)
                    _p(f"  → 캐시 삭제: {_cf}")
            except Exception:
                pass

    def _save_text_cache(data):
        """bg_b64/logoB64/faviconB64 제외한 텍스트 캐시 저장 (~1MB)"""
        import copy
        d = copy.deepcopy(data)
        d.get('brand', {}).pop('logoB64', None)
        d.get('brand', {}).pop('faviconB64', None)
        for s in (d.get('slides') or []):
            s.pop('bg_b64', None)
            s.pop('bg_mime', None)
        with open(_text_cache, 'w', encoding='utf-8') as _f:
            json.dump(d, _f, ensure_ascii=False, indent=2)

    def _save_img_cache(data):
        """이미지 b64만 별도 저장 (~11MB, 재사용 시 선택적 로드)"""
        img_data = {
            'ts': int(time.time()),
            'logo_b64': data.get('brand', {}).get('logoB64', ''),
            'favicon_b64': data.get('brand', {}).get('faviconB64', ''),
            'slides': [
                {'bg_b64': s.get('bg_b64') or '', 'bg_mime': s.get('bg_mime') or ''}
                for s in (data.get('slides') or [])
            ],
        }
        with open(_img_cache, 'w', encoding='utf-8') as _f:
            json.dump(img_data, _f, ensure_ascii=False)

    json_file = _text_cache   # 기본적으로 텍스트 캐시 사용
    slide_json = None
    assets = {}

    # 신규 텍스트 캐시 우선, 없으면 구버전 통합 캐시로 폴백
    _cache_to_load = _text_cache if os.path.exists(_text_cache) else (
                     _legacy_cache if os.path.exists(_legacy_cache) else None)
    if _cache_to_load:
        try:
            with open(_cache_to_load, "r", encoding="utf-8") as f:
                slide_json = json.load(f)
            # bg_b64는 항상 새로 생성 — 이전 런의 이미지(코인/주식 등 오류 이미지 포함) 재사용 방지
            for _s in (slide_json.get('slides') or []):
                _s.pop('bg_b64', None)
                _s.pop('bg_mime', None)
            _p(f"  → 기존 JSON 로드 완료: {json_file} (크롤링/Gemini 생략)")
            # narrative_type_str 복원 (캐시 로드 경로에서도 4693행 참조 가능하도록)
            narrative_type_str = slide_json.get('brand', {}).get('narrative_type', 'A')
            # 검증 블록이 storyline을 참조하므로 캐시 슬라이드에서 역구성
            storyline = [
                {'slide_num': i + 1, 'type': s.get('type', ''), 'topic': s.get('headline', '')}
                for i, s in enumerate(slide_json.get('slides', []))
            ]
            assets = {
                'logo_url': slide_json.get('logoUrl', ''),
                'logo_b64': slide_json.get('brand', {}).get('logoB64', ''),
                'colors': [slide_json.get('brand', {}).get('primaryColor', '#1A1A1A')],
                'site_img_pool_meta': [],
                'dominant_color': '',
                'hero_colors': [],
                # 캐시에 저장된 CSS 빈도 복원 (신규: top5 리스트+점수, 구버전: 단일값 폴백)
                'css_freq_colors': (slide_json['brand'].get('css_freq_colors_top5')
                                    or ([slide_json['brand']['css_freq_color']]
                                        if slide_json['brand'].get('css_freq_color') else [])),
                'css_freq_scores': slide_json['brand'].get('css_freq_scores_top5', {}),
                'og_image_color': slide_json.get('brand', {}).get('og_image_color', ''),
                # 흰검 지배형 감지용 — 캐시 경로에서도 isMonochrome 올바르게 작동하도록 복원
                'css_dark_total':  slide_json['brand'].get('css_dark_total', 0),
                'css_light_total': slide_json['brand'].get('css_light_total', 0),
                # 다크 사이트 감지용 — siteDarkBg로 폴백 (dark_bg_color는 캐시에 미포함)
                'dark_bg_color':   slide_json['brand'].get('siteDarkBg', ''),
            }
            # 이미지 캐시에서 로고·파비콘·슬라이드 배경 복원 (텍스트 캐시에는 이미지 미포함)
            if os.path.exists(_img_cache):
                try:
                    with open(_img_cache, 'r', encoding='utf-8') as _if:
                        _ic = json.load(_if)
                    if not assets['logo_b64']:
                        assets['logo_b64'] = _ic.get('logo_b64', '')
                        if assets['logo_b64']:
                            slide_json.setdefault('brand', {})['logoB64'] = assets['logo_b64']
                    if _ic.get('favicon_b64'):
                        slide_json['brand']['faviconB64'] = _ic['favicon_b64']
                    # 슬라이드 배경 이미지 복원 — type 기반 매핑 (슬라이드 수 변경에도 안전)
                    cached_by_type = {
                        cs.get('type', ''): cs
                        for cs in _ic.get('slides', [])
                        if cs.get('bg_b64') and cs.get('type')
                    }
                    restored = 0
                    for _s in slide_json.get('slides', []):
                        _cs = cached_by_type.get(_s.get('type', ''))
                        if _cs and not _s.get('bg_b64'):
                            _s['bg_b64'] = _cs['bg_b64']
                            _s['bg_mime'] = _cs.get('bg_mime') or 'png'
                            restored += 1
                    _p(f"  → 이미지 캐시 복원: 배경 {restored}개 / 로고 {'✓' if assets['logo_b64'] else '✗'}")
                except Exception as _e:
                    _p(f"  → 이미지 캐시 로드 실패: {_e}")
            # 캐시 경로: 로고 b64에서 도미넌트 컬러 재추출 (PNG/JPG) 또는 SVG 색 추출
            _cl = assets['logo_b64']
            _cl_mime = _b64_mime(_cl) if _cl else ''
            if _cl and _cl_mime == 'svg+xml':
                _svg_c = _extract_svg_colors(_cl)
                if _svg_c:
                    assets['dominant_color'] = _svg_c[0]
                    _p(f"  → (캐시) SVG 로고 컬러: {_svg_c[0]}")
            elif _cl and _cl_mime not in ['svg+xml']:
                try:
                    _dc = extract_dominant_color(base64.b64decode(_cl))
                    if _dc:
                        assets['dominant_color'] = _dc
                        _p(f"  → (캐시) 로고 도미넌트 컬러: {_dc}")
                except Exception:
                    pass
        except Exception as e:
            _p(f"  → 기존 JSON 로드 실패, 새로 시작합니다: {e}")

    if not slide_json:
        _p("[1단계] 웹페이지 크롤링 중...")
        raw_info = scrape_website(url)
        _p(f"  → 텍스트 {len(raw_info)}자 추출 완료")

        # ── 크롤링 후 2차 주체 감지 (og:title 기반 — URL 패턴보다 신뢰도 높음) ──
        _refined_subject = _detect_page_subject_from_text(raw_info, url)
        if _refined_subject and _refined_subject.get('subject_name'):
            _old_name = company_name
            page_subject = _refined_subject
            company_name = _refined_subject['subject_name']
            # C-type 강제는 아티스트 페이지에만 — 일반 브랜드/에이전시는 Gemini가 결정
            if (not narrative_type or narrative_type == 'auto') and _refined_subject.get('subject_type') == 'artist':
                narrative_type = 'C'
            if company_name != _old_name:
                _p(f"  [주체 확정-og] {company_name} → narrative_type=C 적용")
                # 캐시 파일명 재계산 (company_name이 바뀐 경우)
                _text_cache = f"slide_{company_name}_text.json"
                _img_cache  = f"slide_{company_name}_img.json"
                _legacy_cache = f"slide_{company_name}.json"

        raw_info = clean_raw_text(raw_info)
        _p(f"  → 정제 후 {len(raw_info)}자 (노이즈 제거 + 중복 압축)\n")

        _p("[2단계] 브랜드 에셋 추출 중...")
        assets = extract_brand_assets(url)
        _p(f"  → 로고 URL: {assets['logo_url'] or '없음'}")
        _p(f"  → 컬러: {assets['colors'][:5] or '없음'}")
        fc = assets.get('footer_contact', {})
        _p(f"  → 푸터 연락처: {fc or '없음'}")

        _p("[2b단계] 로고 캐처 중 (SVG/PNG 우선)...")
        logo_b64 = capture_logo_transparent(url, logo_url=assets.get('logo_url', ''))

        # ── 아티스트 페이지: 레이블 로고 필터링 ──────────────────────────────
        # 로고 URL에 레이블(도메인) 식별자가 포함되고 아티스트명은 없으면 → 제거
        if page_subject and page_subject.get('subject_type') in ('artist', 'sub-brand'):
            _logo_url_lower = (assets.get('logo_url') or '').lower()
            _domain_key = urlparse(url).netloc.replace('www.', '').split('.')[0].lower()
            _subject_key2 = page_subject['subject_name'].replace(' ', '').lower()
            if _logo_url_lower and _domain_key in _logo_url_lower and _subject_key2 not in _logo_url_lower:
                _p(f"  → 레이블 로고 감지 ({_domain_key}) → 아티스트 페이지이므로 제거")
                logo_b64 = ''
                assets['logo_url'] = ''   # URL도 함께 제거 (슬라이드 JSON 주입 방지)

        assets['logo_b64'] = logo_b64 or ''

        # 로고에서 도미넌트 브랜드 컬러 추출 (PNG/JPG: 픽셀 분석, SVG: fill 추출)
        _dom_color = ''
        _logo_mime = _b64_mime(logo_b64) if logo_b64 else ''
        if logo_b64 and _logo_mime == 'svg+xml':
            _svg_c = _extract_svg_colors(logo_b64)
            if _svg_c:
                _dom_color = _svg_c[0]
                _p(f"  → SVG 로고 컬러: {_dom_color} (총 {len(_svg_c)}개 후보)")
        elif logo_b64:
            try:
                _dom_color = extract_dominant_color(base64.b64decode(logo_b64))
            except Exception:
                pass
        if _dom_color:
            assets['dominant_color'] = _dom_color
            _p(f"  → 로고 도미넌트 컬러: {_dom_color}")
        else:
            assets['dominant_color'] = ''
        # hero_colors는 extract_brand_assets에서 이미 수집됨
        assets.setdefault('hero_colors', [])

        _p("[2b2단계] 파비콘 다운로드 중 (워터마크용)...")
        favicon_b64 = ''
        favicon_mime = 'png'
        favicon_url = assets.get('favicon_url', '')
        if favicon_url:
            try:
                _r = requests.get(favicon_url, headers=HEADERS, timeout=8)
                if _r.status_code == 200 and 'image' in _r.headers.get('content-type', ''):
                    _fav_bytes = _r.content
                    # ico 파일 → PNG 변환 (PPTX/브라우저 호환성 개선)
                    if favicon_url.lower().endswith('.ico') or b'\x00\x00\x01\x00' == _fav_bytes[:4]:
                        try:
                            from PIL import Image as _PILImg
                            import io as _io
                            _ico_img = _PILImg.open(_io.BytesIO(_fav_bytes))
                            # 가장 큰 크기 선택 (ico에 여러 크기 포함 가능)
                            _sizes = getattr(_ico_img, 'ico', None)
                            if _sizes:
                                _best = max(_sizes.sizes(), key=lambda s: s[0])
                                _ico_img = _sizes.getimage(_best)
                            _buf = _io.BytesIO()
                            _ico_img.convert('RGBA').save(_buf, format='PNG')
                            _fav_bytes = _buf.getvalue()
                            favicon_mime = 'png'
                        except Exception:
                            pass  # 변환 실패 시 원본 사용
                    favicon_b64 = base64.b64encode(_fav_bytes).decode('utf-8')
                    if not favicon_mime or favicon_mime == 'png':
                        favicon_mime = _b64_mime(favicon_b64) if favicon_b64 else 'png'
                    _p(f"  → 파비콘 완료: {favicon_url} ({len(favicon_b64)//1024}KB)")
            except Exception as _e:
                _p(f"  → 파비콘 실패: {_e}")
        else:
            _p("  → 파비콘 URL 없음, 건너뜀")
        assets['favicon_b64'] = favicon_b64
        assets['favicon_mime'] = favicon_mime
        _p("")

        _p("[2c단계] 홈페이지 실제 이미지 수집 중...")
        _is_artist_page = bool((page_subject or {}).get('subject_name'))
        site_img_urls = extract_website_images(url, _progress_fn=_p, _artist_mode=_is_artist_page)
        if _is_artist_page:
            _p(f"  → 아티스트 모드 활성화 (thumb/avatar 허용, 갤러리 링크 추가 스캔)")
        _p(f"  → extract URL: {len(site_img_urls)}개")
        site_img_pool_meta = []
        for img_url, alt, ctx in site_img_urls:
            b64, mime, w, h = download_image_b64(img_url)
            if b64:
                # mime 정규화 (image/jpeg → jpeg)
                _pool_mime = (mime or 'jpeg').split('/')[-1].split(';')[0].strip()
                if _pool_mime not in ('jpeg', 'png', 'webp', 'gif'):
                    _pool_mime = 'jpeg'
                site_img_pool_meta.append({
                    "b64": b64,
                    "mime": _pool_mime,
                    "alt": alt,
                    "context": ctx,
                    "w": w,
                    "h": h,
                })
                if len(site_img_pool_meta) >= 20:
                    break
        # 파비콘/로고 이미지를 풀에 추가 (크기 무관 — 브랜드 아이콘 보장)
        _fav_b64 = assets.get('favicon_b64', '')
        _fav_mime = assets.get('favicon_mime', 'png')
        if _fav_b64 and _fav_mime != 'svg+xml':
            _fav_w, _fav_h = 64, 64
            if HAS_PIL:
                try:
                    _fi = _PILImage.open(io.BytesIO(base64.b64decode(_fav_b64)))
                    _fav_w, _fav_h = _fi.size
                except Exception:
                    pass
            site_img_pool_meta.append({
                'b64': _fav_b64, 'alt': 'favicon', 'context': 'brand icon',
                'w': _fav_w, 'h': _fav_h,
            })
        assets['site_img_pool_meta'] = site_img_pool_meta
        _p(f"  → 홈페이지 이미지 {len(site_img_pool_meta)}개 수집 완료 (파비콘 포함)\n")

        # ── 아티스트 전용 아이콘 탐색 (page_subject 감지 시) ──────────────
        _psi_name = (page_subject or {}).get('subject_name', '')
        _psi_b64 = _psi_mime_val = None
        if _psi_name and site_img_pool_meta:
            _psi_kw = _psi_name.lower().replace(' ', '')
            for _pe in site_img_pool_meta:
                _ctx = _pe.get('context', '').lower()
                _alt = _pe.get('alt', '').lower()
                _pw, _ph = _pe.get('w', 0), _pe.get('h', 0)
                _pasp = _pw / max(_ph, 1) if _ph else 1.0
                if (_psi_kw in _ctx or _psi_kw in _alt
                        or any(kw in _ctx for kw in ['logo', 'icon', 'emblem', 'badge'])
                        or (0.8 <= _pasp <= 1.25 and 0 < _pw <= 300 and _pe.get('b64'))):
                    _psi_b64 = _pe['b64']
                    _psi_mime_val = _pe.get('mime', 'png')
                    _p(f"  → page_subject_icon 감지: alt='{_pe.get('alt','')}' ctx='{_pe.get('context','')}'")
                    break
        assets['page_subject_icon_b64'] = _psi_b64 or ''
        assets['page_subject_icon_mime'] = _psi_mime_val or 'png'

        # ── [3단계-A] 리서처 에이전트: 팩트 추출 ──────────────
        # Researcher 전에 URL/회사명으로 사전 감지 → C-type이면 전용 템플릿 적용
        _pre_narrative = narrative_type if narrative_type and narrative_type != 'auto' else None
        if not _pre_narrative:
            _pre_narrative = _detect_auto_narrative('', company_name, url=url)
        _p("[3단계-A] 리서처 에이전트: 팩트북 추출 중...")
        factbook = agent_researcher(raw_info, _p, page_subject=page_subject,
                                    forced_narrative=_pre_narrative)
        _p(f"\n{'='*55}")
        _p(factbook[:1000] + ("..." if len(factbook) > 1000 else ""))
        _p('='*55 + "\n")

        # ── [3단계-B] 전략 기획자 에이전트: 목차 기획 ──────────
        _p("[3단계-B] 전략 기획자 에이전트: 목차 기획 중...")
        # 사용자 지정 > Python 사전 감지 > Gemini 자동 결정
        _forced = narrative_type if narrative_type and narrative_type != 'auto' else None
        if not _forced:
            _forced = _detect_auto_narrative(factbook, company_name, url=url)
            if _forced:
                _p(f"  [사전 감지] 업종 키워드 → 내러티브 타입 {_forced} 자동 적용")
        narrative_type_str, storyline = agent_strategist(
            factbook, company_name, _p,
            forced_narrative=_forced,
            purpose=purpose
        )
        _p(f"  내러티브 타입: {narrative_type_str}")
        for item in storyline:
            _p(f"  슬라이드 {item.get('slide_num', '?'):>2} | {item.get('type',''):<28} | {item.get('topic','')}")
        _p("")

        # ── [3단계-C] 카피라이터+포맷터: JSON 생성 ─────────────
        _p("[3단계-C] 카피라이터: 슬라이드 카피 작성 중...")
        slide_json = generate_slide_json(factbook, storyline, narrative_type_str, assets, company_name, mood=mood, page_subject=page_subject)
        if not slide_json:
            raise RuntimeError("Gemini JSON 생성 실패. 파이프라인을 종료합니다.")

        # [물리적 텍스트 정제] 마크다운 제거, 띄어쓰기 강제, 서술형 마침표 제거
        _strip_md = lambda t: t.replace('**', '').replace('*', '') if t else t
        for slide in slide_json.get('slides', []):
            if slide.get('headline'):
                hl_clean = _strip_md(slide['headline'])
                # CTA 슬라이드: 한국어 작은따옴표로 감싼 세션명 제거 (e.g. '그로스 진단 세션' → 그로스 진단 세션)
                if slide.get('type') == 'cta_session':
                    hl_clean = re.sub(r"'([^']+)'", r'\1', hl_clean)
                slide['headline'] = hl_clean
            if slide.get('subheadline'):
                slide['subheadline'] = _strip_md(slide['subheadline'])
            cleaned_body = []
            for b in slide.get('body', []):
                b_clean = _strip_md(b)
                b_clean = re.sub(r'^(\d+)\.(?=[^\s])', r'\1. ', b_clean)  # 1.데이터 → 1. 데이터
                if b_clean.endswith('다.') or b_clean.endswith('요.'):
                    b_clean = b_clean[:-1]
                cleaned_body.append(b_clean)
            slide['body'] = cleaned_body
        _p("  → [정제] 마크다운/서술형 제거 완료")

        # 로고 정보 주입
        slide_json['logoUrl'] = assets.get('logo_url', '')
        if 'brand' not in slide_json:
            slide_json['brand'] = {}
        slide_json['brand']['logoUrl']    = assets.get('logo_url', '')
        slide_json['brand']['logoB64']    = assets.get('logo_b64', '')
        slide_json['brand']['faviconB64'] = assets.get('favicon_b64', '')
        slide_json['brand']['faviconMime'] = assets.get('favicon_mime', 'png')
        slide_json['brand']['pageSubjectIconB64'] = assets.get('page_subject_icon_b64', '')
        slide_json['brand']['pageSubjectIconMime'] = assets.get('page_subject_icon_mime', 'png')
        fc = assets.get('footer_contact', {})
        slide_json['brand']['nameKo']  = fc.get('nameKo', '')
        slide_json['brand']['ceoName'] = fc.get('ceoName', '')
        if assets.get('logo_b64'):
            _p(f"  → 로고 b64 주입 완료 ({len(assets['logo_b64'])//1024}KB)")
        elif assets.get('logo_url'):
            _p(f"  → 로고 URL 주입: {assets['logo_url']}")

        _save_text_cache(slide_json)
        _p(f"  → 텍스트 캐시 저장: {_text_cache}")

    # ── 다중 소스 합의 기반 primaryColor 결정 ──────────────────────────────────
    # 소스 우선순위:
    #  0-A. CSS 빈도 최상위 (background/fill 가중치 3 — 버튼·섹션에서 가장 많이 쓰인 색)
    #  0-B. OG/히어로 이미지 픽셀 dominant (페이지 시각 분석)
    #  1. CSS named primary/accent 변수 (vibrancy >= 0.30)
    #  2. hero/header 배경색 + 로고 dominant가 일치 — 교차 검증
    #  3. 로고 dominant (vibrancy >= 0.20)
    #  4. SVG 로고 색
    #  5. hero_colors 중 최고 vibrancy
    #  6. CSS 최상위 vibrancy 색 — 폴백
    #  7. Gemini가 선택한 primaryColor — 최종 폴백

    def _color_close(c1: str, c2: str, threshold: int = 40) -> bool:
        """두 헥스 색이 RGB 거리 threshold 이내인지"""
        try:
            r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
            r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
            return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5 < threshold
        except Exception:
            return False

    _css_colors      = assets.get('colors', [])        # CSS에서 추출한 컬러 목록 (tier1 우선)
    _dom_color       = assets.get('dominant_color', '') # 로고 픽셀 dominant
    _hero_colors     = assets.get('hero_colors', [])    # 헤더/히어로 배경색
    _freq_colors     = assets.get('css_freq_colors', [])
    _freq_scores     = assets.get('css_freq_scores', {})
    _og_color        = assets.get('og_image_color', '')
    _el_accent       = assets.get('elementor_accent', '')
    _el_cross        = assets.get('elementor_cross_validated', [])  # CSS변수 + background 실사용 교차검증
    _logo_mime       = _b64_mime(assets.get('logo_b64','')) if assets.get('logo_b64') else ''
    _svg_colors      = _extract_svg_colors(assets.get('logo_b64','')) if _logo_mime == 'svg+xml' else []
    _logo_candidates = ([_dom_color] if _dom_color else []) + _svg_colors

    _p(f"  → 교차검증: {_el_cross} / accent변수: {_el_accent or '없음'} / css_freq상위3: {_freq_colors[:3]}")

    final_color = ''
    _reason = ''
    _explicit_primary = assets.get('explicit_primary', '')

    # -3. --color-primary / --primary-color CSS 변수 최최우선 (vibrancy 무관 — 브랜드 의도 존중)
    if _explicit_primary:
        final_color = _explicit_primary
        _reason = f'CSS --color-primary 변수 ({_explicit_primary})'

    # -2. Elementor/CSS 글로벌 accent 변수 최우선 (--e-global-color-accent 등 명시적 브랜드 변수)
    if not final_color and _el_accent and _color_vibrancy(_el_accent) >= 0.20:
        final_color = _el_accent
        _reason = f'CSS 글로벌 accent 변수 ({_el_accent})'

    # -1. 교차검증: CSS 변수 정의 + 실제 배경 사용 모두 등장 (단, 6개 이하일 때만 신뢰 — 워드프레스 기본 팔레트 노이즈 방지)
    if not final_color and _el_cross and len(_el_cross) <= 6:
        best_cross = max(_el_cross, key=_color_vibrancy)
        if _color_vibrancy(best_cross) >= 0.25:
            final_color = best_cross
            _reason = f'CSS 변수 교차검증 (정의+사용, {best_cross})'

    # -0. 흰검 지배형 감지: 명시적 CSS 변수 없음 + 어두운/밝은 색이 vibrant보다 압도적
    # → primary = #111111, 첫 vibrant = accent (예: 디자인 에이전시, 모노크롬 브랜드)
    _dark_total   = assets.get('css_dark_total', 0)
    _light_total  = assets.get('css_light_total', 0)
    _max_vibrant  = max(_freq_scores.values()) if _freq_scores else 0
    _is_monochrome = (
        not final_color                    # 명시적 CSS 변수 / Elementor 없으면
        and not assets.get('dark_bg_color')  # 다크 테마 사이트 제외 (dark-on-dark 충돌 방지)
        and _dark_total > 8
        and _light_total > 8
        and _max_vibrant < 24  # vibrant 색이 배경으로 8회 미만 (포인트 정도만 사용)
    )
    _secondary_color = ''  # 기본값 — isMonochrome 또는 하단 로직에서 설정
    if _is_monochrome:
        _first_vibrant = next((c for c in _freq_colors if _color_vibrancy(c) >= 0.25), '')
        final_color = '#111111'
        _secondary_color = _first_vibrant
        _reason = f'흰검 지배형 → primary=#111, accent={_first_vibrant or "없음"}'

    # 0-A. CSS 사용 빈도 최상위 (버튼·배경·fill에서 가장 많이 쓰인 색 — 변수명 무관)
    if not final_color and _freq_colors and _color_vibrancy(_freq_colors[0]) >= 0.25:
        final_color = _freq_colors[0]
        _reason = f'CSS 빈도 최상위 ({final_color})'

    # 0-B. OG/히어로 이미지 픽셀 dominant
    if not final_color and _og_color and _color_vibrancy(_og_color) >= 0.22:
        final_color = _og_color
        _reason = f'OG/히어로 이미지 dominant ({_og_color})'

    # 1. CSS에 강한 primary/accent 명시 변수가 있으면 최우선
    _strong_css = [c for c in _css_colors if _color_vibrancy(c) >= 0.30]
    if not final_color and _strong_css:
        final_color = _strong_css[0]
        _reason = f'CSS primary (vibrancy={_color_vibrancy(final_color):.2f})'

    # 2. 로고 색과 hero 배경색이 비슷하면 → 교차 검증된 색 (로고 우선)
    if not final_color:
        for lc in _logo_candidates:
            for hc in _hero_colors:
                if _color_close(lc, hc, threshold=35):
                    final_color = lc
                    _reason = f'로고+히어로 교차검증 (logo={lc}, hero={hc})'
                    break
            if final_color:
                break

    # 3. 로고 dominant (vibrancy 충분)
    if not final_color and _dom_color and _color_vibrancy(_dom_color) >= 0.20:
        final_color = _dom_color
        _reason = f'로고 dominant (vibrancy={_color_vibrancy(_dom_color):.2f})'

    # 4. SVG 로고에서 추출한 색 (vibrancy 충분)
    if not final_color and _svg_colors:
        final_color = _svg_colors[0]
        _reason = f'SVG 로고 fill (vibrancy={_color_vibrancy(final_color):.2f})'

    # 5. hero 배경색
    if not final_color and _hero_colors:
        final_color = _hero_colors[0]
        _reason = f'히어로 배경색 (vibrancy={_color_vibrancy(final_color):.2f})'

    # 6. CSS 최상위 컬러 (폴백)
    if not final_color and _css_colors:
        final_color = _css_colors[0]
        _reason = f'CSS 최상위 ({final_color})'

    # Gemini 선택값(기존 primaryColor)은 마지막 폴백
    _gemini_color = (slide_json.get('brand', {}).get('primaryColor') or '').strip()
    if not final_color:
        final_color = _gemini_color or '#1A1A1A'
        _reason = f'Gemini 선택 / 기본값 ({final_color})'

    # 두 번째 vibrant 색상 (포인트 악센트 — C2)
    # primary와 다른 첫 번째 vibrant 색 — 블랙리스트 없음, 단순 vibrancy 기준만
    # 없으면 '' → 프론트에서 primary 25% 밝게 fallback
    if not _secondary_color:  # isMonochrome에서 이미 설정된 경우 유지
        _secondary_color = next(
            (c for c in _freq_colors[:8]
             if c.upper() != final_color.upper()
             and _color_vibrancy(c) >= 0.20),
            ''
        )
    _p(f"  → accentColor2 후보: { {c: _freq_scores.get(c,0) for c in _freq_colors[:5]} }")

    # 사이트 다크 테마 감지 — extract_brand_assets에서 수집한 body/html 배경 우선 사용
    _dark_bg_raw = assets.get('dark_bg_color', '')
    def _luma(hex_c):
        h = hex_c.lstrip('#')
        if len(h) != 6: return 1.0
        try: r,g,b = int(h[:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
        except: return 1.0
        return 0.2126*r + 0.7152*g + 0.0722*b
    # 폴백: _freq_colors 중 dark 후보 (기존 로직 유지)
    _site_dark_bg = _dark_bg_raw or next(
        (c for c in _freq_colors[:8]
         if _luma(c) < 0.10 and _color_vibrancy(c) < 0.25 and _freq_scores.get(c, 0) >= 8),
        '')

    # 다크 사이트 판별 + 역할 스왑
    # 조건: 다크 배경 감지 AND vibrant primary가 있음 → primary를 accent로, 다크를 primary로
    _is_dark_site = bool(
        _site_dark_bg
        and final_color
        and _color_vibrancy(final_color) >= 0.20
    )
    if _is_dark_site:
        _vibrant = final_color
        final_color = _site_dark_bg                                  # 다크 → primary
        _secondary_color = _secondary_color or _vibrant              # vibrant → accent
        if not _secondary_color or _secondary_color == final_color:
            _secondary_color = _vibrant
        _reason = f'다크 테마 — primary={final_color}, accent={_secondary_color}'

    _p(f"  → isMonochrome: {_is_monochrome} (dark={_dark_total}, light={_light_total}, maxVibrant={_max_vibrant})")
    _p(f"  → siteDarkBg: {_site_dark_bg or '없음'} / isDarkSite: {_is_dark_site}")

    if slide_json.get('brand'):
        slide_json['brand']['primaryColor'] = final_color
        # accentColor2: 항상 덮어씀 — '' 이면 프론트에서 hue-rotate -30° fallback 사용
        slide_json['brand']['accentColor2'] = _secondary_color
        # siteDarkBg: 커버 배경
        slide_json['brand']['siteDarkBg'] = _site_dark_bg
        slide_json['brand']['isDarkSite']   = _is_dark_site
        slide_json['brand']['isMonochrome'] = _is_monochrome
        slide_json['brand']['fontCategory']  = assets.get('font_category', 'sans')
        slide_json['brand']['detectedFonts'] = assets.get('detected_fonts', [])
        # 다음 캐시 실행 때 복원용으로 저장
        slide_json['brand']['css_dark_total']  = _dark_total
        slide_json['brand']['css_light_total'] = _light_total
        if _freq_colors:
            slide_json['brand']['css_freq_color']       = _freq_colors[0]
            slide_json['brand']['css_freq_colors_top5'] = _freq_colors[:5]
            slide_json['brand']['css_freq_scores_top5'] = {c: _freq_scores.get(c, 0) for c in _freq_colors[:5]}
        if _og_color:
            slide_json['brand']['og_image_color'] = _og_color
    _p(f"  → primaryColor 결정: {final_color} [{_reason}]")
    _p(f"  → accentColor2 (포인트): {_secondary_color or '없음'}")
    _p(f"  → fontCategory: {assets.get('font_category','sans')} / {assets.get('detected_fonts',[])[:3]}")

    # ── 필수 데이터 후처리 ──
    domain = urlparse(url).netloc.replace('www.', '')
    brand = slide_json.get('brand', {})
    for slide in slide_json.get('slides', []):
        if slide.get('type') == 'contact':
            body = slide.get('body', [])
            cleaned_body = []
            for b in body:
                b_clean = b.strip().lower()
                if (b_clean == domain.lower() or b_clean == f"https://{domain}"
                        or "partnership" in b_clean or "inquiry" in b_clean):
                    continue
                cleaned_body.append(b)
            slide['body'] = cleaned_body

            # footer_contact 강제 주입
            footer_contact = assets.get('footer_contact', {})
            if footer_contact:
                inject = []
                if footer_contact.get('address'):
                    inject.append(f"📍 {footer_contact['address']}")
                if footer_contact.get('phone'):
                    inject.append(f"☎ {footer_contact['phone']}")
                if footer_contact.get('email'):
                    inject.append(f"✉ {footer_contact['email']}")
                if footer_contact.get('kakao'):
                    inject.append(f"💬 카카오채널: {footer_contact['kakao']}")
                if footer_contact.get('linkedin'):
                    inject.append(f"🔗 {footer_contact['linkedin']}")
                for item in inject:
                    key = item[2:16].lower()
                    if not any(key in b.lower() for b in slide['body']):
                        slide['body'].insert(0, item)
            break

    slides = slide_json.get('slides', [])
    _p(f"  → 슬라이드 수: {len(slides)}\n")

    # ── 스토리라인 완전성 검증 — 누락 슬라이드 자동 복원 ─────────────────
    _p("[검증] 스토리라인 슬라이드 완전성 검사...")
    _actual_types = [s.get('type', '') for s in slides]
    _missing_items = [
        (idx, item) for idx, item in enumerate(storyline)
        if item.get('type', '') not in _actual_types
    ]
    if _missing_items:
        _p(f"  ⚠ 누락 슬라이드 {len(_missing_items)}개 발견 — 원위치 복원")
        for _snum_0, _sitem in reversed(_missing_items):
            _stype = _sitem.get('type', '')
            _stopic = _sitem.get('topic', '')
            # 이 슬라이드보다 앞에 있어야 할 타입들을 역순으로 검색해 삽입 위치 결정
            _prev_types = [it.get('type', '') for it in storyline[:_snum_0]]
            _insert_after = -1
            for _pt in reversed(_prev_types):
                for _si, _s in enumerate(slides):
                    if _s.get('type', '') == _pt:
                        _insert_after = _si
                        break
                if _insert_after >= 0:
                    break
            _insert_idx = _insert_after + 1 if _insert_after >= 0 else 0
            _placeholder = {
                "type": _stype,
                "headline": _stopic,
                "subheadline": "",
                "sub": "",
                "eyebrow": "",
                "body": [],
                "bg_b64": "",
                "bg_mime": "png",
                "overlay_opacity": 0,
            }
            slides.insert(_insert_idx, _placeholder)
            _p(f"    복원: {_stype} @ index {_insert_idx} — '{_stopic}'")
    else:
        _p("  ✅ 모든 스토리라인 슬라이드 정상 포함")

    # ── [4단계] 배경 이미지 설정 ──
    _p("[4단계] 배경 이미지 설정 중 (홈페이지 이미지 우선 → Imagen 폴백)...")
    bg_images = {}
    for i, slide in enumerate(slides):
        if 'bg_b64' in slide and slide['bg_b64']:
            bg_images[i] = slide['bg_b64']

    # accent_color = 이미 다중 소스 합의로 결정된 final_color 직접 사용
    brand = slide_json.get('brand', {})
    accent_color = (brand.get('primaryColor') or '').strip() or '#1A1A1A'
    if not accent_color.startswith('#'):
        accent_color = '#' + accent_color
    _p(f"  → accent 컬러: {accent_color}")
    brand_industry = brand.get('industry', '')
    site_img_pool_meta = assets.get('site_img_pool_meta', [])
    _p(f"  → 수집된 이미지 풀: {len(site_img_pool_meta)}개 / accent: {accent_color}\n")

    # ── Visual Theme Seed: 이미지 스타일 일관성을 위한 키워드 추출 ──
    _p("[4-prep] Visual Theme Seed 생성 중...")
    visual_theme_seed = _generate_visual_theme_seed(
        company_name=brand.get('name', company_name),
        narrative_type=brand.get('narrative_type', narrative_type or 'A'),
        industry=brand_industry or 'professional services',
        progress_fn=_p,
    )

    _p("[4a단계] Gemini 지능형 이미지-슬라이드 매칭 중...")
    matched_mapping = match_images_semantically(slides, site_img_pool_meta)
    _p(f"  → {len(matched_mapping)}개의 슬라이드에 적합한 이미지 자동 배정 완료")

    _p("[4b단계] 배경 이미지 설정 중 (지능형 매칭 우선 → Imagen 폴백)...")

    IMAGE_SLIDE_TYPES = {
        # 브랜드/제품 쇼케이스 — 이미지가 슬라이드의 핵심 메시지
        'service_pillar_1', 'service_pillar_2', 'service_pillar_3',
        'core_business_1', 'core_business_2', 'core_business_3',
        'showcase_work_1', 'showcase_work_2', 'showcase_work_3',
        'flagship_experience', 'brand_story',
        # 팀 소개 — 사람/공간 사진
        'team_intro',
        # cta_session, contact: PPTX/PDF 모두 타이포그래피 전용 → 이미지 불필요
    }
    concept_cache = {}
    seen_images = set()
    last_b64 = None
    imagen_count = 0
    _used_pool_idx = set()   # C-type sequential pool 배정 추적
    _used_pool_b64s = set()  # 배정된 b64 prefix (중복 배경 방지)

    for i, slide in enumerate(slides):
        # ① 타입 체크 최우선 — 이미지 불필요 타입은 4a 매칭 이미지도 무시
        stype = slide.get('type', '')
        if stype not in IMAGE_SLIDE_TYPES and stype != 'cover':
            bg_images[i] = None
            slide['bg_b64'] = None
            last_b64 = None
            continue

        b64_candidate = bg_images.get(i) or slide.get('bg_b64')

        if b64_candidate and last_b64:
            _imgkey = lambda b: f"{len(b)}:{b[:500]}{b[-200:]}"
            if _imgkey(b64_candidate) == _imgkey(last_b64):
                _p(f"  [{i+1}/{len(slides)}] ⚠️ 연속 중복 이미지 감지 → 재생성 유도")
                b64_candidate = None
                if 'bg_b64' in slide:
                    slide['bg_b64'] = None

        if b64_candidate:
            if i in [0, 8, 9]:
                _p(f"  [{i+1}/{len(slides)}] ✨ 강제 재생성 시도 (Type: {stype})")
                b64_candidate = None
                slide['bg_b64'] = None
            else:
                bg_images[i] = b64_candidate
                seen_images.add(hash(b64_candidate[:100]))
                last_b64 = b64_candidate
                continue

        # Cover: 사이트 대표 이미지(og:image/hero) 우선 사용, 없으면 B타입만 Pexels 시도
        if stype == 'cover':
            _cover_nt = brand.get('narrative_type', '')
            # 사이트 이미지 풀에서 hero/og:image 컨텍스트 이미지 우선 시도
            _cover_site_b64 = None
            # 커버: og:image/hero 우선 → 앨범커버/discography 폴백 → 첫 번째 이미지
            _cover_ctx_prio = ['hero', 'og:image', 'twitter:image', 'json-ld',
                               'album', 'discography', 'release', 'visual', 'main']
            for _cprio_kw in _cover_ctx_prio:
                for _csim in site_img_pool_meta:
                    if _cprio_kw in _csim.get('context', '').lower() and _csim.get('b64'):
                        _cover_site_b64 = _csim['b64']
                        break
                if _cover_site_b64:
                    break
            # fallback 제거 — hero/og 없으면 타이포그래피 커버 사용 (일반 수집 이미지는 품질 불균일)

            if _cover_site_b64:
                bg_images[i] = _cover_site_b64
                slide['bg_b64'] = _cover_site_b64
                # mime + aspect 업데이트 + 커버 풀 인덱스 추적 (showcase 중복 방지)
                for _ci, _csim in enumerate(site_img_pool_meta):
                    if _csim.get('b64') == _cover_site_b64:
                        if _csim.get('mime'):
                            slide['bg_mime'] = _csim['mime']
                        _cw, _ch = _csim.get('w', 1), _csim.get('h', 1)
                        slide['bg_aspect'] = _cw / max(_ch, 1)
                        _used_pool_idx.add(_ci)  # showcase 슬라이드에서 재사용 방지
                        break
                last_b64 = _cover_site_b64
                _p(f"  [{i+1}/{len(slides)}] 🖼 Cover → 사이트 대표 이미지 사용")
            elif _cover_nt == 'B':
                _cover_q = f"{brand_industry or 'enterprise'} corporate architecture infrastructure landmark"
                _p(f"  [{i+1}/{len(slides)}] 🌐 Cover (B타입) Pexels 시도 (q='{_cover_q[:50]}')")
                b64 = search_pexels_image(keyword=_cover_q, industry='')
                if b64:
                    bg_images[i] = b64
                    slide['bg_b64'] = b64
                    last_b64 = b64
                    _p(f"    → Pexels 완료")
                else:
                    bg_images[i] = None
                    slide['bg_b64'] = None
                    last_b64 = None
                    _p(f"    → Pexels 없음 → 타이포그래피 커버")
            else:
                bg_images[i] = None
                slide['bg_b64'] = None
                last_b64 = None
                _p(f"  [{i+1}/{len(slides)}] ✍ Cover ({_cover_nt or 'A'}) → 타이포그래피 커버")
            continue

        # 타입별 이미지 소스 우선순위 결정
        # - PREFER_COMPANY: 실제 서비스/제품/팀 사진이 중요한 슬라이드 → 회사 이미지 우선
        # - 그 외(시장/컨셉/문제): Pexels 고화질 우선 (회사 썸네일보다 품질이 나음)
        PREFER_COMPANY = {
            'service_pillar_1', 'service_pillar_2', 'service_pillar_3',
            'core_business_1', 'core_business_2', 'core_business_3',
            'team_intro', 'case_study', 'flagship_experience', 'brand_story',
            'showcase_work_1', 'showcase_work_2', 'showcase_work_3',
            'governance',
        }
        # Pexels/회사 이미지 불필요 — Imagen 직접 사용 (CTA, 연락처)
        PREFER_IMAGEN_TYPES = {'cta_session', 'contact'}
        prefer_company = stype in PREFER_COMPANY
        prefer_imagen  = stype in PREFER_IMAGEN_TYPES

        en_hint   = _extract_en_hint(slide, company_name=brand.get('name', ''))  # Imagen용
        curr_ind  = brand.get('industry', 'business')
        # C타입 엔터/크리에이티브 계열: showcase_work 등 슬라이드에 엔터 특화 Pexels 쿼리 사용
        _NT_C_PEXELS = {
            'showcase_work_1':  'music concert stage performance entertainment',
            'showcase_work_2':  'kpop artist music entertainment creative',
            'showcase_work_3':  'entertainment media production creative studio',
            'brand_story':      'creative entertainment dark elegant branding',
            'creative_approach':'creative art music production studio',
            'service_pillar_1': 'music production artist management talent',
            'service_pillar_2': 'entertainment concert live performance',
            'service_pillar_3': 'media entertainment creative content studio',
        }
        if narrative_type_str == 'C' and stype in _NT_C_PEXELS:
            pexels_q = _NT_C_PEXELS[stype]
        else:
            pexels_q = _build_pexels_query(slide, industry=curr_ind,
                                           company_name=brand.get('name', ''))

        def _is_bg_unsuitable(_entry):
            """배경 사용 부적합: 브랜드 아이콘, 흰 배경 다이어그램, 극단 종횡비"""
            _ctx = ((_entry.get('context') or '') + ' ' + (_entry.get('alt') or '')).lower()
            if any(kw in _ctx for kw in ('brand icon', 'favicon', 'icon', 'logo')):
                return True
            if _img_is_too_bright(_entry.get('b64', '')):
                return True
            return False

        def _try_company():
            if i in matched_mapping:
                img_idx = matched_mapping[i]
                if img_idx < len(site_img_pool_meta):
                    _pm_entry = site_img_pool_meta[img_idx]
                    b64 = _pm_entry['b64']
                    if b64 and b64 != last_b64:
                        if _is_bg_unsuitable(_pm_entry):
                            _p(f"  [{i+1}/{len(slides)}] ⏭ Semantic Match #{img_idx}: 아이콘/다이어그램 → 폴백")
                            return None, None, None
                        return b64, f"Semantic Match Pool #{img_idx}", _pm_entry.get('mime', 'jpeg')
            return None, None, None

        def _try_pexels():
            b64 = search_pexels_image(keyword=pexels_q, industry='')
            if b64 and b64 != last_b64:
                return b64, f"Pexels [{pexels_q[:30]}]", 'jpeg'
            return None, None, None

        b64_result = label = mime_result = None

        if prefer_imagen:
            # CTA/Contact: Pexels·회사 이미지 모두 스킵 → Imagen 직접
            _p(f"  [{i+1}/{len(slides)}] 🎨 {stype}: Imagen 직접 사용 (Pexels 스킵)")
        elif prefer_company:
            # 1순위: 회사 이미지 (서비스/제품/팀 슬라이드)
            b64_result, label, mime_result = _try_company()
            if not b64_result:
                # C-type showcase: 수집 이미지 순차 배정 (Gemini 매칭 실패 시 Pexels 이전)
                _C_SHOWCASE = {
                    'showcase_work_1', 'showcase_work_2', 'showcase_work_3',
                    'brand_story', 'flagship_experience',
                }
                if narrative_type_str == 'C' and stype in _C_SHOWCASE and site_img_pool_meta:
                    # 아티스트 showcase: 앨범커버/디스코그래피 우선 → 히어로/og:image → 일반
                    _ctx_prio = [
                        'album', 'discography', 'release', 'single', 'ep', 'music',
                        'og:image', 'hero', 'main', 'visual', 'banner', 'cover', 'group'
                    ]
                    def _pool_score(item):
                        ctx = item[1].get('context', '').lower()
                        alt = item[1].get('alt', '').lower()
                        _combined = ctx + ' ' + alt
                        for _j, _kw in enumerate(_ctx_prio):
                            if _kw in _combined: return _j
                        return len(_ctx_prio)
                    _sorted_pool = sorted(enumerate(site_img_pool_meta), key=_pool_score)
                    # 1차: 미사용 이미지 우선 (아이콘·다이어그램 제외 — _is_bg_unsuitable 통일 적용)
                    for _pi, _pm in _sorted_pool:
                        if _pi not in _used_pool_idx and _pm.get('b64') and _pm['b64'] != last_b64:
                            if _is_bg_unsuitable(_pm):
                                _p(f"  [{i+1}/{len(slides)}] ⏭ Pool #{_pi}: 배경 부적합(아이콘/다이어그램) → 건너뜀")
                                continue
                            b64_result = _pm['b64']
                            mime_result = _pm.get('mime', 'jpeg')
                            label = f"C-type Pool #{_pi}"
                            _used_pool_idx.add(_pi)
                            _used_pool_b64s.add(_pm['b64'][:120])
                            _cw, _ch = _pm.get('w', 1), _pm.get('h', 1)
                            slide['bg_aspect'] = _cw / max(_ch, 1)
                            _p(f"  [{i+1}/{len(slides)}] 🎞 {stype}: 수집 이미지 순차 배정 (Pool #{_pi}, ctx='{_pm.get('context','')}', asp={slide['bg_aspect']:.2f})")
                            break
                    # 2차: pool 소진 시 — 아직 배경으로 쓰이지 않은 이미지만 허용 (중복 방지)
                    if not b64_result:
                        for _pi, _pm in _sorted_pool:
                            if _pm.get('b64') and _pm['b64'][:120] not in _used_pool_b64s \
                                    and not _is_bg_unsuitable(_pm):
                                b64_result = _pm['b64']
                                mime_result = _pm.get('mime', 'jpeg')
                                label = f"C-type Pool #{_pi} (재사용)"
                                _used_pool_b64s.add(_pm['b64'][:120])
                                _cw, _ch = _pm.get('w', 1), _pm.get('h', 1)
                                slide['bg_aspect'] = _cw / max(_ch, 1)
                                _p(f"  [{i+1}/{len(slides)}] 🎞 {stype}: Pool 재사용 (#{_pi}, 미사용 이미지)")
                                break
            if not b64_result and narrative_type_str == 'C' and stype in _C_SHOWCASE:
                # C-type showcase: Pexels 스킵 — 관련 없는 재고 사진 방지
                _p(f"  [{i+1}/{len(slides)}] ⏭ {stype}: C-type — Pexels 스킵 (아티스트 이미지 없음, 다크 배경 사용)")
            elif not b64_result:
                _p(f"  [{i+1}/{len(slides)}] 🌐 Pexels 검색 (회사 이미지 없음, q='{pexels_q}')")
                b64_result, label, mime_result = _try_pexels()
        else:
            # 1순위: Pexels 고화질 (컨셉/시장/추상 슬라이드)
            _p(f"  [{i+1}/{len(slides)}] 🌐 Pexels 검색 (q='{pexels_q}')")
            b64_result, label, mime_result = _try_pexels()
            if not b64_result:
                b64_result, label, mime_result = _try_company()

        if b64_result:
            bg_images[i] = b64_result
            if mime_result:
                slide['bg_mime'] = mime_result
            slide['bg_b64'] = b64_result
            seen_images.add(hash(b64_result[:100]))
            last_b64 = b64_result
            _p(f"  [{i+1}/{len(slides)}] ✅ {label}")
            continue

        _p(f"  [{i+1}/{len(slides)}] ⚙ 회사/Pexels 모두 실패 → Imagen 생성 시도...")

        # ── REAL_IMAGE_ONLY: 실물 이미지 전용 타입 — Imagen 금지 ──────────────
        if stype in REAL_IMAGE_ONLY_TYPES:
            _p(f"  [{i+1}/{len(slides)}] ⛔ {stype}: Imagen 금지 → 빈 배경 처리")
            bg_images[i] = None
            slide['bg_b64'] = None
            last_b64 = None
            continue

        # 3순위: Imagen AI
        concept = TYPE_TO_CONCEPT.get(stype, 'abstract dark tech')
        cache_key = f"{concept}|{en_hint}"

        if cache_key in concept_cache and concept_cache[cache_key] != last_b64:
            b64 = concept_cache[cache_key]
            bg_images[i] = b64
            slide['bg_b64'] = b64
            last_b64 = b64
            _p(f"  [{i+1}/{len(slides)}] 🎨 Imagen 캐시: {stype}")
        else:
            full_prompt = build_image_prompt(stype, accent=accent_color,
                                             industry=brand_industry, en_hint=en_hint,
                                             mood=mood, theme_seed=visual_theme_seed)
            if cache_key in concept_cache:
                seed = int(time.time() * 1000) % 100000
                styles = ["cinematic volumetric lighting", "minimalist geometric 3d",
                          "soft glassmorphism abstract", "high-tech digital tapestry",
                          "organic fluid dynamics"]
                full_prompt += (f", {styles[seed % len(styles)]}, uniquely different"
                                f" composition, variation seed {seed}")

            _p(f"  [{i+1}/{len(slides)}] 🎨 Imagen 생성: {stype} hint='{en_hint}'...")
            b64 = generate_bg_image(full_prompt)
            if b64:
                bg_images[i] = b64
                slide['bg_b64'] = b64
                concept_cache[cache_key] = b64
                last_b64 = b64
                imagen_count += 1
                _p(f"    → 완료 ({len(b64)//1024}KB)")
                time.sleep(_IMAGEN_MIN_INTERVAL)
            else:
                bg_images[i] = None
                slide['bg_b64'] = None
                last_b64 = None
                _p(f"    ⚠ Imagen 실패")

    # 중간 저장 (텍스트/이미지 분리)
    _save_text_cache(slide_json)
    _save_img_cache(slide_json)

    # ── Self-Healing: 누락 이미지 자동 복구 ──
    # IMAGE_SLIDE_TYPES만 대상 — cover는 메인 루프에서 확정(B타입 Pexels/나머지 타이포그래피), 복구 불필요
    _img_target_types = IMAGE_SLIDE_TYPES
    missing_indices = [
        idx for idx, s in enumerate(slides)
        if not s.get('bg_b64') and s.get('type', '') in _img_target_types
    ]
    if missing_indices:
        _p(f"\n[복구] 누락 이미지 {len(missing_indices)}개 자동 복구 시작...")
        for idx in missing_indices:
            slide = slides[idx]
            stype = slide.get('type', 'core_philosophy')
            _p(f"  → [{idx+1}/{len(slides)}] {stype} 복구 중...")
            time.sleep(_IMAGEN_MIN_INTERVAL)
            en_hint = _extract_en_hint(slide, company_name=brand.get('name', ''))
            full_prompt = build_image_prompt(stype, accent=accent_color,
                                             industry=brand_industry, en_hint=en_hint,
                                             mood=mood, theme_seed=visual_theme_seed)
            b64 = generate_bg_image(full_prompt)
            if not b64:
                # Imagen 실패(쿼터 소진 등) → Pexels 폴백
                pexels_q = _build_pexels_query(slide, industry=brand_industry, company_name=brand.get('name',''))
                _p(f"    → Imagen 실패, Pexels 폴백 (q='{pexels_q[:40]}')")
                b64 = search_pexels_image(keyword=pexels_q, industry='')
            if b64:
                slide['bg_b64'] = b64
                bg_images[idx] = b64
                imagen_count += 1
                _p(f"    → 복구 완료.")
            else:
                _p(f"    → 복구 실패.")

        _save_text_cache(slide_json)
        _save_img_cache(slide_json)

    _p(f"  → Imagen 총 {imagen_count}회 호출\n")

    # ── 각 슬라이드에 overlay_opacity + bg_mime 주입 ──
    for slide in slides:
        stype = slide.get('type', '')
        slide['overlay_opacity'] = OVERLAY_OPACITY.get(stype, 0.65)
        if slide.get('bg_b64'):
            slide['bg_mime'] = _b64_mime(slide['bg_b64'])

    # 로고 MIME 주입
    logo_b64_val = brand.get('logoB64', '')
    if logo_b64_val:
        brand['logoMime'] = _b64_mime(logo_b64_val)

    # 최종 저장: 텍스트 캐시(~1MB) + 이미지 캐시(~11MB) 분리
    _save_text_cache(slide_json)
    _save_img_cache(slide_json)
    _p(f"  → 캐시 저장: {_text_cache} (텍스트) + {_img_cache} (이미지)")

    # TOC 슬라이드: 비활성화 (실제 슬라이드 수와 항목이 일치하지 않아 혼란 유발)

    # ── 슬라이드 품질 자동 채점 + 규칙 기반 보완 ────────────────────────
    _p("\n[품질 검사] 슬라이드 품질 채점 중...")
    _slide_scores = [_score_slide(s, slides[i-1] if i > 0 else None) for i, s in enumerate(slides)]
    _avg = sum(r['total'] for r in _slide_scores) / len(_slide_scores) if slides else 0
    for _i, (_s, _r) in enumerate(zip(slides, _slide_scores)):
        _p(f"  [{_i+1:>2}] {_s.get('type',''):<30} {_r['total']:>4.1f}점  {_r['breakdown']}")
    _p(f"  → 평균: {_avg:.1f} / 10.0")

    _LOW = 7.5
    # 평균 무관하게, 개별적으로 낮은 슬라이드 항상 보완 시도
    _low = [(i, slides[i], _slide_scores[i]) for i in range(len(slides))
            if _slide_scores[i]['total'] < _LOW]
    if _low:
        _p(f"  → 낮은 슬라이드 {len(_low)}개 보완 시도...")
        for _idx, _sl, _sc in _low:
            _improved = _improve_slide(_sl, _sc)
            if _improved:
                _new_sc = _score_slide(_improved, slides[_idx-1] if _idx > 0 else None)
                if _new_sc['total'] > _sc['total']:
                    slides[_idx] = _improved
                    # 어떤 항목이 개선됐는지 표시
                    _diff = {k: f"{_sc['breakdown'].get(k,'?')}→{_new_sc['breakdown'].get(k,'?')}"
                             for k in _new_sc['breakdown'] if _new_sc['breakdown'].get(k) != _sc['breakdown'].get(k)}
                    _p(f"    [{_idx+1}] {_sc['total']} → {_new_sc['total']} ✅  {_diff}")
                else:
                    _p(f"    [{_idx+1}] 개선 효과 없음 ({_sc['total']}) — 원본 유지")
            else:
                _p(f"    [{_idx+1}] 보완 규칙 없음 — 원본 유지")
        # 재채점
        _slide_scores = [_score_slide(s, slides[i-1] if i > 0 else None) for i, s in enumerate(slides)]
        _avg = sum(r['total'] for r in _slide_scores) / len(_slide_scores) if slides else 0
        _p(f"  → 보완 후 평균: {_avg:.1f} / 10.0")

    # 품질 점수 brand에 주입 (프론트엔드 표시용)
    slide_json['brand']['qualityScore'] = round(_avg, 1)
    slide_json['brand']['slideScores']  = [r['total'] for r in _slide_scores]

    narrative_type = brand.get('narrative_type', 'A')
    result = {
        "brand": brand,
        "slides": slides,
        "meta": {
            "accent_color": accent_color,
            "accent_color2": brand.get('accentColor2', ''),
            "narrative_type": narrative_type,
            "purpose": purpose,
            "company_name": company_name,
            "url": url,
        },
    }

    _p(f"\n[완료] 슬라이드 {len(slides)}개 생성 완료")
    return result


if __name__ == "__main__":
    import sys as _sys
    _url = _sys.argv[1] if len(_sys.argv) > 1 else "https://www.yulsight.com"
    _company = _sys.argv[2] if len(_sys.argv) > 2 else None
    _result = run_pipeline(_url, _company)
    print(f"\n[완료] {len(_result.get('slides', []))}개 슬라이드")
    print(f"  JSON : slide_{_result['meta']['company_name']}.json")
