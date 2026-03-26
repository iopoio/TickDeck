"""
brand_extractor.py — 브랜드 에셋 / 이미지 추출 모듈
"""

import base64
import io
import json
import re
import requests
from bs4 import BeautifulSoup
from collections import Counter, defaultdict

from .config import HEADERS, _GOOGLEBOT_HEADERS, HAS_PIL, logger
from .utils import _color_vibrancy, extract_dominant_color
from .scraper import (
    _fetch_with_playwright,
    _playwright_get_links,
    _playwright_extract_images,
    _scrape_nav_links,
    _is_cookie_wall,
    _make_pw_page,
)

if HAS_PIL:
    from PIL import Image as _PILImage

# ────────────────────────────────────────────────────────────────────────────
# 이미지 skip 패턴
# ────────────────────────────────────────────────────────────────────────────

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

# ────────────────────────────────────────────────────────────────────────────
# CSS 컬러 분석
# ────────────────────────────────────────────────────────────────────────────

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
        except Exception as e:
            logger.debug(f"OG/hero image color extraction failed: {e}")
    return ''

# ────────────────────────────────────────────────────────────────────────────
# 로고 추출 (Playwright)
# ────────────────────────────────────────────────────────────────────────────

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
        logger.warning(f"  [Playwright Logo] 실패: {e}")
        return ''

# ────────────────────────────────────────────────────────────────────────────
# 브랜드 에셋 메인 함수
# ────────────────────────────────────────────────────────────────────────────

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
            logger.info(f"  [Playwright] 브랜드 에셋 JS 렌더링 시도...")
            _pw_html = _fetch_with_playwright(base_url)
            if _pw_html:
                soup = BeautifulSoup(_pw_html, 'html.parser')
                logger.info(f"  [Playwright] 완료 ({len(soup.get_text(separator=' ').strip())}자)")

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
            logger.info(f"  [Playwright Logo] JS 렌더링으로 로고 탐색 시도...")
            _pw_logo = _extract_logo_url_with_playwright(base_url)
            if _pw_logo:
                logo_url = _pw_logo
                logger.info(f"  [Playwright Logo] 발견: {logo_url}")

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
            except Exception as e:
                logger.debug(f"CSS fetch failed for {css_url}: {e}")

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

        # ── 밝은 배경색 감지 (사이트 크림/파스텔 배경 → 슬라이드 반영) ──
        site_light_bg = ''
        for _lm in _dark_sel_pat.finditer(raw_css):
            _block = _lm.group(1)
            _bg_m = re.search(r'background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})\b', _block, re.I)
            if _bg_m:
                _lc = '#' + _bg_m.group(1).lstrip('#').upper()
                _luma = _luma_c(_lc)
                # 밝은 파스텔/크림 계열만 (luma 0.85~0.97 — 순백 #FFF 제외)
                if 0.85 <= _luma <= 0.97 and _color_vibrancy(_lc) < 0.25:
                    site_light_bg = _lc
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
                except Exception as e:
                    logger.debug(f"Contact page scraping failed: {e}")

    except Exception as e:
        logger.error(f"  브랜드 에셋 추출 오류: {e}")
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
        'site_light_bg': site_light_bg,
        'footer_contact': footer_contact,
        'favicon_url': favicon_url,
        'font_category': font_category,
        'detected_fonts': detected_fonts,
    }

# ────────────────────────────────────────────────────────────────────────────
# 이미지 수집
# ────────────────────────────────────────────────────────────────────────────

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
        except Exception as e:
            logger.debug(f"JSON-LD parsing failed: {e}")

    # 1-C순위: __NEXT_DATA__ (Next.js SSR)
    _nd = soup.find('script', id='__NEXT_DATA__')
    if _nd:
        try:
            _ndstr = json.dumps(json.loads(_nd.string or '{}'))
            for _nm in re.finditer(r'"(https?://[^"]+\.(?:jpg|jpeg|png|webp))"', _ndstr):
                add_fn(_nm.group(1), 'next-data', 'page-data')
        except Exception as e:
            logger.debug(f"__NEXT_DATA__ image extraction failed: {e}")

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
        logger.info(msg)
        if _progress_fn:
            _progress_fn(msg)
    images = []
    seen = set()
    base = url.rstrip('/')
    # domain_root: 상대경로 이미지 URL 구성에 사용 (아티스트 딥링크 시 버그 방지)
    from urllib.parse import urlparse as _up
    _parsed_img_url = _up(url)
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
            except Exception as e:
                logger.debug(f"Homepage image scan attempt failed: {e}")
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
                    except Exception as e:
                        logger.debug(f"Playwright fallback image collection failed: {e}")
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
        except Exception as e:
            logger.debug(f"Artist gallery link discovery failed: {e}")
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
            except Exception as e:
                logger.debug(f"Album/release page image collection failed: {e}")

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
                        except Exception as e:
                            logger.debug(f"PIL pixel stdev check failed: {e}")
                        return base64.b64encode(r.content).decode('utf-8'), ct, w, h
                    except Exception as e:
                        logger.debug(f"PIL image validation failed: {e}")

                # PIL 없으면 파일 크기로만 판단 (10KB 미만은 아이콘/썸네일로 간주)
                if len(r.content) < 10_000:
                    return None, None, 0, 0
                return base64.b64encode(r.content).decode('utf-8'), ct, 0, 0
    except Exception as e:
        logger.debug(f"Image download/encoding failed: {e}")
    return None, None, 0, 0

# ────────────────────────────────────────────────────────────────────────────
# 로고 투명화 캡처
# ────────────────────────────────────────────────────────────────────────────

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
            logger.warning(f"  PIL 배경 제거 오류: {e}")
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
                logger.info(f"  → SVG 로고 원본 사용 ({len(b64)//1024}KB)")
                return b64

            # 헤더/푸터에서 찾은 PNG → 원본 그대로 사용 (remove_bg 없음)
            if direct:
                b64 = base64.b64encode(r.content).decode('utf-8')
                logger.info(f"  → PNG 로고 원본 사용 ({len(b64)//1024}KB)")
                return b64

            # 폴백 경로: 배경 제거 시도 (og:image 등)
            if HAS_PIL:
                result = remove_bg(r.content)
                if result:
                    logger.info(f"  → 로고 배경 제거 완료 ({len(result)//1024}KB)")
                    return result
            return base64.b64encode(r.content).decode('utf-8')
        except Exception as e:
            logger.warning(f"  → 로고 다운로드 실패: {e}")
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
    except Exception as e:
        logger.debug(f"Quick logo URL scanning failed: {e}")

    if logo_url_quick:
        result = _download_logo(logo_url_quick, direct=True)
        if result:
            return result
