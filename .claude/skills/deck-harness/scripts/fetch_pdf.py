#!/usr/bin/env python3
"""차단된 PDF 다운로더 — 컨설팅사·투자사 리포트 직링크가 403/WAF로 막힐 때.

collector ② 폴백의 PDF 전용 도구 (insane-search와 같은 원리·의존성 공유):
  1) curl_cffi TLS 지문 위장 격자 (safari/chrome × referer 전략)
  2) 실패 시 Wayback Machine 스냅샷 폴백
검증 = %PDF 매직바이트 + 최소 크기 (HTML 챌린지 페이지를 성공으로 오판 금지).

용법: python3 fetch_pdf.py <PDF_URL> [-o out.pdf]
의존: pip install "curl_cffi>=0.15.0" (insane-search 셋업이 이미 설치)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlparse

MIN_PDF_BYTES = 10_000

# (impersonate, referer 전략) 격자 — 사이트명 하드코딩 없음, 규칙만.
ATTEMPT_GRID = [
    ("safari", "self_root"),
    ("chrome", "google"),
    ("safari_ios", "none"),
    ("chrome", "self_root"),
]


def _referer(url: str, strategy: str) -> dict:
    if strategy == "self_root":
        p = urlparse(url)
        return {"Referer": f"{p.scheme}://{p.netloc}/"}
    if strategy == "google":
        return {"Referer": "https://www.google.com/"}
    return {}


def _is_pdf(content: bytes) -> bool:
    return content[:5] == b"%PDF-" and len(content) >= MIN_PDF_BYTES


def _try_direct(url: str) -> tuple[bytes | None, list[str]]:
    from curl_cffi import requests

    trace = []
    for impersonate, ref in ATTEMPT_GRID:
        try:
            r = requests.get(
                url,
                impersonate=impersonate,
                headers={"Accept": "application/pdf,*/*", **_referer(url, ref)},
                timeout=60,
                allow_redirects=True,
            )
            tag = f"{impersonate}/{ref} -> {r.status_code} {len(r.content)}B"
            if r.status_code == 200 and _is_pdf(r.content):
                trace.append(tag + " PDF✓")
                return r.content, trace
            trace.append(tag)
        except Exception as e:  # noqa: BLE001 — 격자 전수 시도가 목적
            trace.append(f"{impersonate}/{ref} -> ERR {type(e).__name__}")
    return None, trace


def _try_wayback(url: str) -> tuple[bytes | None, str]:
    from curl_cffi import requests

    try:
        r = requests.get(
            "https://archive.org/wayback/available", params={"url": url}, impersonate="safari", timeout=30
        )
        snap = (r.json().get("archived_snapshots") or {}).get("closest") or {}
        ts, snap_url = snap.get("timestamp"), snap.get("url")
        if not snap_url:
            return None, "wayback: 스냅샷 없음"
        # id_ 접미사 = 원본 바이트 그대로(아카이브 배너 미삽입)
        raw = f"https://web.archive.org/web/{ts}id_/{url}"
        r2 = requests.get(raw, impersonate="safari", timeout=90, allow_redirects=True)
        if r2.status_code == 200 and _is_pdf(r2.content):
            return r2.content, f"wayback {ts} PDF✓"
        return None, f"wayback {ts} -> {r2.status_code} {len(r2.content)}B (PDF 아님)"
    except Exception as e:  # noqa: BLE001
        return None, f"wayback ERR {type(e).__name__}"


def fetch_pdf(url: str, out: Path) -> bool:
    content, trace = _try_direct(url)
    if content is None:
        wb_content, wb_note = _try_wayback(url)
        trace.append(wb_note)
        content = wb_content
    for line in trace:
        print(f"  {line}")
    if content is None:
        print(f"FAIL: {url} — 직접 격자 + wayback 전부 실패. 다음 수단: insane-search engine으로 랜딩 페이지 경유, 또는 사람 다운로드 요청.")
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(content)
    print(f"OK: {out} ({len(content):,}B)")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description="차단된 PDF 우회 다운로드 (TLS 위장 + Wayback 폴백)")
    ap.add_argument("url")
    ap.add_argument("-o", "--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or Path(Path(urlparse(args.url).path).name or "download.pdf")
    if out.suffix.lower() != ".pdf":
        out = out.with_suffix(".pdf")
    return 0 if fetch_pdf(args.url, out) else 1


if __name__ == "__main__":
    sys.exit(main())
