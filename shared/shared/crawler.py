import logging
import httpx
import re
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

logger = logging.getLogger(__name__)

@dataclass
class CrawlResult:
    url: str
    text: str
    title: str
    image_urls: list[str]
    error: Optional[str] = None

def _parse_html(html: str, base_url: str) -> dict:
    """Extracts metadata and cleaned text from HTML content."""
    soup = BeautifulSoup(html, "html.parser")

    # Extract title: og:title -> <title>
    title = ""
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    elif soup.title:
        title = soup.title.string.strip() if soup.title.string else ""

    # Extract image URLs (max 10, filter out data, svg, icon, favicon)
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

    # Remove unwanted tags
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Extract and clean text (compress whitespace, limit to 8000 chars)
    text = soup.get_text(separator=" ")
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > 8000:
        text = text[:8000]

    return {"title": title, "image_urls": image_urls, "text": text}


async def crawl(url: str) -> CrawlResult:
    """Asynchronously crawls a URL to extract text and metadata."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        data = _parse_html(html, url)

        # 텍스트가 500자 미만이면 Playwright로 JS 렌더링 재시도
        if len(data["text"]) < 500 and HAS_PLAYWRIGHT:
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
                data = _parse_html(html, url)
            except Exception as pw_e:
                logger.warning(f"Playwright rendering failed for {url}: {pw_e}")

        return CrawlResult(
            url=url,
            text=data["text"],
            title=data["title"],
            image_urls=data["image_urls"],
            error=None,
        )

    except Exception as e:
        logger.error(f"Crawl failed for {url}: {e}")
        return CrawlResult(url=url, text="", title="", image_urls=[], error=str(e))
