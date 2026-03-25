"""
scraper.py — 웹 크롤링 모듈
"""

import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote

from .config import HEADERS, _GOOGLEBOT_HEADERS, logger

# ────────────────────────────────────────────────────────────────────────────
# 상수
# ────────────────────────────────────────────────────────────────────────────

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

# Playwright default skip pattern
# (전체 패턴 _SKIP_IMG_PAT / _SKIP_IMG_PAT_ARTIST 는 brand_extractor.py 에 정의)
_PW_DEFAULT_SKIP = re.compile(
    r'logo|icon|favicon|sprite|arrow|btn|button|avatar|thumb|badge|seal|'
    r'banner\d|\.svg|/wp-includes|data:image',
    re.I
)

# ────────────────────────────────────────────────────────────────────────────
# 쿠키 월 / Next.js 텍스트 추출
# ────────────────────────────────────────────────────────────────────────────

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

# ────────────────────────────────────────────────────────────────────────────
# 네비게이션 링크 / 사이트맵
# ────────────────────────────────────────────────────────────────────────────

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
    except Exception as e:
        logger.debug(f"robots.txt 파싱 실패: {e}")

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
        except Exception as e:
            logger.debug(f"sitemap URL 페치 실패 ({sm_url}): {e}")
            continue

    if not collected:
        return []

    # 관련도순 정렬 → 상위 max_urls개
    collected.sort(key=lambda x: x[1], reverse=True)
    result = [u for u, s in collected if s >= 0][:max_urls]
    logger.info(f"[Sitemap] {len(result)}개 관련 URL 발견 (전체 {len(collected)}개 중)")
    return result

# ────────────────────────────────────────────────────────────────────────────
# 텍스트 전처리
# ────────────────────────────────────────────────────────────────────────────

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

# ────────────────────────────────────────────────────────────────────────────
# Playwright 헬퍼
# ────────────────────────────────────────────────────────────────────────────

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
    except Exception as e:
        logger.debug(f"쿠키 모달 JS 클릭 실패: {e}")

    # CSS 셀렉터 fallback
    for sel in ['[class*="cookie"] button', '[id*="cookie"] button',
                '[class*="consent"] button', '[class*="gdpr"] button',
                '[class*="Cookie"] button', '[class*="Consent"] button']:
        try:
            page.click(sel, timeout=1500)
            page.wait_for_timeout(3500)
            return True
        except Exception as e:
            logger.debug(f"쿠키 모달 CSS 셀렉터 클릭 실패 ({sel}): {e}")
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
        logger.warning(f"[Playwright] 실패: {e}")
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
        logger.info(f"[Playwright Nav] {len(links)}개 내부 링크 발견")
        return links
    except Exception as e:
        logger.warning(f"[Playwright Nav] 실패: {e}")
        return []


def _playwright_extract_images(url: str, base: str, _skip_pat=None) -> list:
    """Playwright로 JS 렌더 후 img.src + computedStyle background-image 수집.
    CSR/Next.js SPA 사이트에서 정적 HTML로는 얻을 수 없는 이미지 대응.
    _skip_pat: 커스텀 skip 패턴 (기본값 _PW_DEFAULT_SKIP, 아티스트 모드는 _SKIP_IMG_PAT_ARTIST)
    """
    if _skip_pat is None:
        _skip_pat = _PW_DEFAULT_SKIP
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
                except Exception as e:
                    logger.debug(f"Playwright 스크롤/JS eval 실패: {e}")
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
        logger.info(f"[Playwright Images] {len(images)}개 수집")
        return images
    except Exception as e:
        logger.warning(f"[Playwright Images] 실패: {e}")
        return []

# ────────────────────────────────────────────────────────────────────────────
# 페이지 페치 / 콘텐츠 추출
# ────────────────────────────────────────────────────────────────────────────

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
                        logger.warning(f"[쿠키 월 감지] Googlebot UA로 재시도: {target_url}")
                        continue  # Googlebot UA로 retry
                    else:
                        logger.warning(f"[쿠키 월] Googlebot UA도 차단됨, 네비 링크만 추출")
                # JS-heavy (300자 미만)
                _has_noscript = bool(soup.find('noscript'))
                if len(raw_text) < 300 or _has_noscript:
                    logger.info(f"[Playwright] JS 렌더링 감지 ({len(raw_text)}자) — 재시도 중...")
                    _pw_html = _fetch_with_playwright(target_url)
                    if _pw_html:
                        soup = BeautifulSoup(_pw_html, 'html.parser')
                        logger.info(f"[Playwright] 완료 ({len(soup.get_text(separator=' ').strip())}자)")
                return soup, soup.get_text(separator=' ').strip()
        except Exception as e:
            logger.error(f"오류 ({target_url}): {e}")
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
                logger.info(f"[__NEXT_DATA__] {label}: {len(_nd_strings)}개 텍스트")
        except Exception as e:
            logger.debug(f"__NEXT_DATA__ JSON 파싱 실패 ({label}): {e}")

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

# ────────────────────────────────────────────────────────────────────────────
# 메인 크롤링 함수
# ────────────────────────────────────────────────────────────────────────────

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
            logger.info(f"[서브페이지 감지] 부모 URL 자동 추가: {_parent_urls}")

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
    logger.info(f"[홈페이지] 크롤링: {base_url}")
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
        logger.info(f"[부모URL] 크롤링: {_pu}")
        visited.add(_pu)
        _ps, _ = _fetch_page(_pu, base_url)
        if _ps:
            _pt, _pf, _pi = _extract_page_content(_ps, base_url, _pu)
            all_text += f"--- Path: {_pu} ---\n{_pt}\n{_pf}\n"
            for src in _pi:
                if src not in image_urls:
                    image_urls.append(src)

    # ── STEP 2: Sitemap 확인 ────────────────────────────────────────────────
    logger.info(f"[Sitemap] 확인 중...")
    sitemap_urls = _fetch_sitemap_urls(base_url, max_urls=20)

    # ── STEP 3A: 사이트맵 있음 → 관련 URL 크롤링 ───────────────────────────
    if sitemap_urls:
        _to_crawl = [u for u in sitemap_urls if u not in visited and _is_relevant_link(u)][:12]
        logger.info(f"[Sitemap] {len(_to_crawl)}개 페이지 크롤링")
        for sm_url in _to_crawl:
            visited.add(sm_url)
            try:
                logger.info(f"크롤링 중 (sitemap): {sm_url}")
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
                logger.warning(f"오류 ({sm_url}): {e}")

    # ── STEP 3B: 사이트맵 없음 → 헤더/네비 링크 우선, 그 다음 _SCRAPE_PATHS ─
    else:
        logger.info(f"[Sitemap] 없음 — 헤더 링크 우선 크롤링 시작")
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
                logger.info(f"[Nav] 헤더/링크 {len(nav_links_3b)}개 발견")

        # 1-B) 정적 HTML에서 링크가 부족하면 Playwright로 JS 렌더된 DOM 전체 스캔
        if len(nav_links_3b) < 3:
            logger.info(f"[Nav] 링크 부족({len(nav_links_3b)}개) → Playwright 렌더 링크 시도")
            pw_links = _playwright_get_links(base_url, domain_root)
            pw_links = [l for l in pw_links if _is_relevant_link(l)]
            nav_links_3b = list(dict.fromkeys(nav_links_3b + pw_links))
            if pw_links:
                logger.info(f"[Nav+PW] 총 {len(nav_links_3b)}개 링크")

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
                logger.info(f"크롤링 중: {target_url}")
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
                logger.warning(f"오류 ({target_url}): {e}")

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
            logger.info(f"[Nav+KW] 추가 링크 {len(extra_urls)}개 크롤링")
        for eu in extra_urls:
            visited.add(eu)
            try:
                logger.info(f"크롤링 중 (추가): {eu}")
                s, _ = _fetch_page(eu, base_url)
                if not s:
                    continue
                pt, ft, imgs2 = _extract_page_content(s, base_url, eu)
                if len(pt) > 50:
                    all_text += f"--- Auto: {eu} ---\n{pt}\n{ft}\n"
                for src in imgs2:
                    if src not in image_urls:
                        image_urls.append(src)
            except Exception as e:
                logger.debug(f"추가 링크 이미지 추출 실패 ({eu}): {e}")

    if image_urls:
        all_text += "\n--- 발견된 이미지 URL ---\n" + '\n'.join(image_urls[:20])

    return all_text
