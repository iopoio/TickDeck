#!/usr/bin/env python3
"""Big3(KPMG·PwC·Deloitte) 발간물 라이브러리 수집기 (7/7 후추님 — "내가 한 것처럼 자료를 찾게").

사람이 하던 것의 도구화: 발행처 라이브러리 페이지에 직접 가서, 제목 안 가리고 훑고,
PDF 실물을 받아 로컬 코퍼스에 쌓는다. collector는 웹검색 전에 여기부터 뒤진다.

사용:
  python3 tools/big3_library.py refresh            # 목록 크롤 → 신규 PDF 다운로드 → 색인
  python3 tools/big3_library.py search "AI 일자리"  # 코퍼스 색인 검색 (제목·파일명)
  python3 tools/big3_library.py search "고용" --deep  # + PDF 앞 3페이지 본문 검색

코퍼스: corpus/big3/<firm>/<파일>.pdf + corpus/big3/index.json
# ponytail: Deloitte 목록은 JS 렌더라 v1은 크롤 불가 — refresh가 정직하게 0건 보고, collector가 웹검색 폴백.
"""
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus" / "big3"
INDEX = CORPUS / "index.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

LISTINGS = {
    "kpmg": [
        "https://kpmg.com/kr/ko/insights/eri/past-reports.html",
        "https://kpmg.com/kr/ko/insights.html",
    ],
    "pwc": [
        "https://www.pwc.com/kr/ko/insights/samil-insight.html",
        "https://www.pwc.com/kr/ko/publications.html",
    ],
    "deloitte": [
        "https://www.deloitte.com/kr/ko/insights.html",
    ],
}
PWC_DETAIL_LIMIT = 15  # ponytail: run당 신규 상세 페이지 상한 — 필요해지면 올린다


def _fetch(url: str, timeout: int = 40) -> str:
    try:
        out = subprocess.run(
            ["curl", "-sL", "-A", UA, "--max-time", str(timeout), url],
            capture_output=True, timeout=timeout + 10,
        )
        return out.stdout.decode("utf-8", errors="replace")
    except (subprocess.TimeoutExpired, OSError):
        return ""


def _load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text(encoding="utf-8"))
    return {"entries": []}


def _save_index(idx: dict) -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")


def _known_urls(idx: dict) -> set:
    return {e["url"] for e in idx["entries"]}


def _slug(url: str) -> str:
    name = url.split("/")[-1].split("?")[0]
    name = re.sub(r"\.coredownload\.inline", "", name)
    return name[-120:] if name.endswith(".pdf") else (name[-116:] + ".pdf")


def _download(firm: str, url: str, title: str, source_page: str, idx: dict) -> bool:
    dest_dir = CORPUS / firm
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / _slug(url)
    out = subprocess.run(
        ["curl", "-sL", "-A", UA, "--max-time", "120", "-o", str(dest), url],
        capture_output=True, timeout=150,
    )
    if out.returncode != 0 or not dest.exists() or dest.read_bytes()[:5] != b"%PDF-":
        if dest.exists():
            dest.unlink()
        return False
    idx["entries"].append({
        "firm": firm,
        "title": title or dest.stem,
        "url": url,
        "local_path": str(dest.relative_to(ROOT)),
        "source_page": source_page,
        "fetched": str(date.today()),
    })
    return True


def _pdf_links(html: str, base: str) -> list[tuple[str, str]]:
    links = []
    for m in re.finditer(r'<a[^>]+href="([^"]+\.pdf[^"]*)"[^>]*>(.*?)</a>', html, re.S | re.I):
        url = urljoin(base, m.group(1))
        text = re.sub(r"<[^>]+>", " ", m.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        links.append((url, text))
    # 텍스트 없는 href-only 링크도 수거
    for m in re.finditer(r'href="([^"]+\.pdf[^"]*)"', html, re.I):
        url = urljoin(base, m.group(1))
        if url not in [u for u, _ in links]:
            links.append((url, ""))
    return links


def _detail_links(html: str, base: str) -> list[str]:
    urls = []
    for m in re.finditer(r'href="([^"]+/insights/[^"]+\.html)"', html, re.I):
        u = urljoin(base, m.group(1))
        if u not in urls:
            urls.append(u)
    return urls


def refresh() -> int:
    idx = _load_index()
    known = _known_urls(idx)
    report = {}
    for firm, pages in LISTINGS.items():
        added, seen_detail = 0, 0
        for page in pages:
            html = _fetch(page)
            if not html:
                continue
            for url, title in _pdf_links(html, page):
                if url not in known and _download(firm, url, title, page, idx):
                    known.add(url)
                    added += 1
            if firm == "pwc":
                # PwC는 목록→상세→PDF 2단계
                for detail in _detail_links(html, page):
                    if seen_detail >= PWC_DETAIL_LIMIT:
                        break
                    seen_detail += 1
                    dhtml = _fetch(detail)
                    for url, title in _pdf_links(dhtml, detail):
                        if url not in known and _download(firm, url, title, detail, idx):
                            known.add(url)
                            added += 1
        report[firm] = added
    _save_index(idx)
    total = len(idx["entries"])
    for firm, added in report.items():
        note = " (JS 렌더 목록 — 웹검색 폴백 필요)" if firm == "deloitte" and added == 0 else ""
        print(f"{firm}: 신규 {added}건{note}")
    print(f"코퍼스 총 {total}건 → {INDEX.relative_to(ROOT)}")
    return 0


def search(query: str, deep: bool = False) -> int:
    idx = _load_index()
    terms = [t for t in re.split(r"\s+", query.strip()) if t]
    hits = []
    for e in idx["entries"]:
        hay = f"{e['title']} {e['local_path']}".lower()
        if all(t.lower() in hay for t in terms):
            hits.append((e, "제목/파일명"))
    if deep:
        matched = {e["url"] for e, _ in hits}
        for e in idx["entries"]:
            if e["url"] in matched:
                continue
            pdf = ROOT / e["local_path"]
            if not pdf.exists():
                continue
            out = subprocess.run(
                ["pdftotext", "-f", "1", "-l", "3", str(pdf), "-"],
                capture_output=True, timeout=60,
            )
            text = out.stdout.decode("utf-8", errors="replace").lower()
            if all(t.lower() in text for t in terms):
                hits.append((e, "본문(앞 3p)"))
    if not hits:
        print(f"0건 — 코퍼스 {len(idx['entries'])}건 안에 '{query}' 없음. refresh 후 재검색 또는 웹검색 폴백.")
        return 1
    for e, where in hits:
        print(f"[{e['firm']}] {e['title'][:60]} · {e['local_path']} · {e['fetched']} ({where})")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("refresh", "search"):
        sys.exit(__doc__)
    if sys.argv[1] == "refresh":
        return refresh()
    if len(sys.argv) < 3:
        sys.exit("search <키워드> [--deep]")
    return search(sys.argv[2], deep="--deep" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())
