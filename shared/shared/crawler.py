import asyncio
import logging
import httpx
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# 상수
# ──────────────────────────────────────────────────────────────────────────────

_RELEVANT_KEYWORDS = {
    'about': 3, 'company': 3, 'intro': 3, '소개': 3, '회사': 3,
    'service': 2, 'product': 2, 'solution': 2, 'team': 2, 'story': 2,
    '서비스': 2, '제품': 2, '솔루션': 2,
    'blog': -3, 'news': -2, 'press': -2, 'career': -2, 'job': -2,
    '블로그': -3, '뉴스': -2, '채용': -2,
    'legal': -4, 'privacy': -4, 'terms': -4, 'policy': -4, 'agreement': -4,
    'research': -2, 'paper': -2, 'publication': -2,
}

_FALLBACK_PATHS = ['/about', '/company', '/service', '/services', '/product', '/products']

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ──────────────────────────────────────────────────────────────────────────────
# 인터페이스 (변경 금지)
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class CrawlResult:
    url: str
    text: str       # 합산된 전체 텍스트
    title: str      # 메인 페이지 title
    image_urls: list[str]
    raw_html: str = ""
    error: Optional[str] = None


# ──────────────────────────────────────────────────────────────────────────────
# 관련도 점수
# ──────────────────────────────────────────────────────────────────────────────

def _score_url(url: str) -> int:
    u = url.lower()
    score = 0
    for kw, pts in _RELEVANT_KEYWORDS.items():
        if kw in u:
            score += pts
    # 경로 깊이 패널티 (깊을수록 낮은 우선순위)
    depth = u.count('/') - 2
    if depth > 3:
        score -= 1
    return score


# ──────────────────────────────────────────────────────────────────────────────
# HTML 파싱
# ──────────────────────────────────────────────────────────────────────────────

def _parse_html(html: str, base_url: str) -> dict:
    """메인 페이지용 — title, image_urls, text 모두 추출"""
    soup = BeautifulSoup(html, "html.parser")

    # og:title → <title>
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title:
        title = soup.title.string.strip() if soup.title.string else ""

    # 이미지 (메인 페이지만)
    image_urls = []
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        full_url = urljoin(base_url, src)
        low_url = full_url.lower()
        if any(x in low_url for x in ["data:", ".svg", "icon", "favicon"]):
            continue
        image_urls.append(full_url)
        if len(image_urls) >= 10:
            break

    text = _extract_text(soup)
    return {"title": title, "image_urls": image_urls, "text": text}


def _parse_subpage_html(html: str) -> str:
    """서브페이지용 — 텍스트만 추출"""
    soup = BeautifulSoup(html, "html.parser")
    return _extract_text(soup)


def _extract_text(soup: BeautifulSoup) -> str:
    """공통 텍스트 추출 + 노이즈 제거"""
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator=" ")

    # 쿠키/저작권/개인정보 노이즈 제거
    text = re.sub(
        r'(?:쿠키|Cookie|저작권|Copyright|All Rights Reserved|개인정보 처리방침|Privacy Policy).{0,150}',
        '', text, flags=re.IGNORECASE
    )

    # 35자 이상 반복 구문 제거 (nav 중복)
    seen = set()
    lines = text.split('.')
    deduped = []
    for line in lines:
        key = line.strip()[:35]
        if len(key) >= 35 and key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    text = '.'.join(deduped)

    text = re.sub(r'\s+', ' ', text).strip()
    return text


# ──────────────────────────────────────────────────────────────────────────────
# Sitemap 파싱
# ──────────────────────────────────────────────────────────────────────────────

async def _fetch_sitemap_urls(client: httpx.AsyncClient, base_url: str, domain: str) -> list[str]:
    """sitemap.xml 시도 → 관련도 점수 정렬 → 상위 5개 반환"""
    parsed = urlparse(base_url)
    origin = parsed.scheme + "://" + parsed.netloc
    sitemap_candidates = [
        origin + "/sitemap.xml",
        origin + "/sitemap_index.xml",
    ]

    collected: list[tuple[str, int]] = []

    for sm_url in sitemap_candidates:
        try:
            r = await client.get(sm_url, timeout=6.0)
            if r.status_code != 200:
                continue
            txt = r.text
            if "<url" not in txt and "urlset" not in txt:
                continue
            locs = re.findall(r'<loc>\s*(https?://[^<\s]+)\s*</loc>', txt)
            for u in locs:
                if domain in u:
                    clean = u.rstrip('/')
                    if clean != base_url:
                        score = _score_url(clean)
                        collected.append((clean, score))
            if collected:
                break
        except Exception as e:
            logger.debug(f"Sitemap 페치 실패 ({sm_url}): {e}")

    if not collected:
        return []

    collected.sort(key=lambda x: x[1], reverse=True)
    result = [u for u, s in collected if s >= 0][:5]
    logger.info(f"[Sitemap] {len(result)}개 관련 URL 선택 (전체 {len(collected)}개)")
    return result


# ──────────────────────────────────────────────────────────────────────────────
# GNB 링크 추출
# ──────────────────────────────────────────────────────────────────────────────

def _extract_gnb_links(html: str, base_url: str, domain: str) -> list[str]:
    """메인 페이지 <a> 태그에서 GNB 내부 링크 추출, 관련도 정렬"""
    soup = BeautifulSoup(html, "html.parser")
    parsed = urlparse(base_url)
    origin = parsed.scheme + "://" + parsed.netloc

    links: dict[str, int] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        if href.startswith("http"):
            if domain not in href:
                continue
            full = href.rstrip("/")
        elif href.startswith("/"):
            full = origin + href.rstrip("/")
        else:
            continue
        if full == base_url or full == origin:
            continue
        score = _score_url(full)
        if score >= 0 and full not in links:
            links[full] = score

    sorted_links = sorted(links.items(), key=lambda x: x[1], reverse=True)
    return [u for u, _ in sorted_links]


# ──────────────────────────────────────────────────────────────────────────────
# 단일 페이지 비동기 페치
# ──────────────────────────────────────────────────────────────────────────────

async def _fetch_page_html(client: httpx.AsyncClient, url: str) -> str:
    """단일 페이지 HTML 반환. 실패 시 빈 문자열."""
    try:
        r = await client.get(url, timeout=10.0)
        r.raise_for_status()
        return r.text
    except Exception as e:
        logger.debug(f"페치 실패 ({url}): {e}")
        return ""


async def _fetch_with_playwright_async(url: str) -> str:
    """JS 렌더링이 필요한 페이지 — async Playwright로 HTML 반환"""
    if not HAS_PLAYWRIGHT:
        return ""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url)
            try:
                await page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            html = await page.content()
            await browser.close()
        return html
    except Exception as e:
        logger.warning(f"Playwright 실패 ({url}): {e}")
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# 텍스트 합산 후처리
# ──────────────────────────────────────────────────────────────────────────────

def _merge_and_clean(sections: list[tuple[str, str]]) -> str:
    """
    sections: [(url, text), ...]
    각 페이지 앞에 구분자 추가 → 합산 → 노이즈 제거 → 12,000자 제한
    """
    parts = []
    for page_url, text in sections:
        if text.strip():
            parts.append(f"\n\n=== {page_url} ===\n{text.strip()}")

    merged = "".join(parts)

    # 공백 정리
    merged = re.sub(r'[ \t]{4,}', '  ', merged)
    merged = re.sub(r'\n{3,}', '\n\n', merged)

    # 12,000자 제한
    if len(merged) > 12000:
        cutoff = merged.rfind("===", 0, 12000)
        merged = merged[:cutoff].rstrip() if cutoff > 12000 * 0.7 else merged[:12000]

    return merged.strip()


# ──────────────────────────────────────────────────────────────────────────────
# 메인 크롤링 함수
# ──────────────────────────────────────────────────────────────────────────────

async def crawl(url: str) -> CrawlResult:
    """
    멀티페이지 비동기 크롤러.
    1. 메인 URL 크롤링 (항상)
    2. sitemap.xml → 관련도 상위 5개 선택
    3. Sitemap 없으면 GNB <a> 링크 추출
    4. 둘 다 없으면 /about, /company 등 폴백 경로 시도
    5. 메인 포함 최대 6개 병렬 크롤링 → 텍스트 합산
    """
    base_url = url.rstrip("/")
    parsed = urlparse(base_url)
    domain = parsed.netloc
    origin = parsed.scheme + "://" + parsed.netloc

    async with httpx.AsyncClient(
        timeout=15.0, headers=_HEADERS, follow_redirects=True
    ) as client:

        # ── STEP 1: 메인 페이지 크롤링 ────────────────────────────────────────
        logger.info(f"[메인] 크롤링: {base_url}")
        main_html = await _fetch_page_html(client, base_url)

        # JS 렌더링 감지
        if main_html:
            has_noscript = "<noscript>" in main_html.lower()
            quick_text = BeautifulSoup(main_html, "html.parser").get_text()
            if len(quick_text) < 500 or has_noscript:
                logger.info(f"[Playwright] JS 렌더링 감지 → 재시도")
                pw_html = await _fetch_with_playwright_async(base_url)
                if pw_html:
                    main_html = pw_html

        if not main_html:
            return CrawlResult(
                url=url, text="", title="", image_urls=[], raw_html="",
                error="메인 페이지 크롤링 실패"
            )

        main_data = _parse_html(main_html, base_url)

        # ── STEP 2: 서브페이지 URL 수집 ───────────────────────────────────────
        sub_urls: list[str] = []

        # 2-A: Sitemap 시도
        sitemap_urls = await _fetch_sitemap_urls(client, base_url, domain)
        if sitemap_urls:
            sub_urls = [u for u in sitemap_urls if u != base_url]
            logger.info(f"[Sitemap] 서브페이지 {len(sub_urls)}개 선택")

        # 2-B: Sitemap 없으면 GNB 링크
        if not sub_urls:
            gnb_links = _extract_gnb_links(main_html, base_url, domain)
            sub_urls = [u for u in gnb_links if u != base_url]
            if sub_urls:
                logger.info(f"[GNB] {len(sub_urls)}개 링크 발견")

        # 2-C: 둘 다 없으면 폴백 경로
        if not sub_urls:
            logger.info(f"[폴백] 공통 경로 시도")
            sub_urls = [origin + p for p in _FALLBACK_PATHS]

        # 중복 제거 + 최대 5개 (메인 포함 6개)
        seen = {base_url}
        selected_subs: list[str] = []
        for u in sub_urls:
            if u not in seen and len(selected_subs) < 5:
                seen.add(u)
                selected_subs.append(u)

        logger.info(f"[크롤링 대상] 메인 + 서브 {len(selected_subs)}개 = 총 {1 + len(selected_subs)}개")

        # ── STEP 3: 서브페이지 병렬 크롤링 ───────────────────────────────────
        async def fetch_sub(sub_url: str) -> tuple[str, str]:
            html = await _fetch_page_html(client, sub_url)
            if not html:
                logger.debug(f"[스킵] {sub_url}")
                return sub_url, ""
            text = _parse_subpage_html(html)
            logger.info(f"[서브] {sub_url} → {len(text)}자")
            return sub_url, text

        sub_results = await asyncio.gather(
            *[fetch_sub(u) for u in selected_subs],
            return_exceptions=False
        )

    # ── STEP 4: 텍스트 합산 ──────────────────────────────────────────────────
    sections: list[tuple[str, str]] = [(base_url, main_data["text"])]
    for sub_url, sub_text in sub_results:
        if sub_text:
            sections.append((sub_url, sub_text))

    merged_text = _merge_and_clean(sections)

    return CrawlResult(
        url=url,
        text=merged_text,
        title=main_data["title"],
        image_urls=main_data["image_urls"],
        raw_html=main_html,
        error=None,
    )
