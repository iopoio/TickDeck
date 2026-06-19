#!/usr/bin/env python3
"""envato 미리보기 수집기 (Phase 1 — 축2 양식 학습용)

_queue.txt 의 envato item URL 들을 읽어, 각 페이지 HTML 을 curl 로 받아
슬라이드 미리보기 이미지(elements-preview-images/<UUID>?...&s=<sig>)를
UUID 별 최대 해상도 1장씩 item 폴더에 다운로드한다.

추출 방식(2026-06-18 검증):
- envato 페이지에 __NEXT_DATA__ 는 없음.
- 슬라이드 미리보기 = //elements-resized.envatousercontent.com/elements-preview-images/<UUID>?w=..&s=<sig>
  (UUID 마다 여러 해상도가 있고, 서명 s= 없으면 403 가능 → 서명 포함 URL 그대로 사용)
- elements-cover-images/ 는 커버/관련상품 썸네일이라 제외(슬라이드 아님).
- 미리보기 1장 = 여러 슬라이드를 합친 그리드 이미지(낱장 아님). 분류엔 충분.

사용법:
  python3 envato_collect.py            # _queue.txt 전체
  python3 envato_collect.py --only GXFQ5KS   # slug 코드 1개만(검증용)
  python3 envato_collect.py --list     # 다운 없이 item별 미리보기 개수만

주의: 미리보기는 워터마크 포함 학습용. 재배포/상업 사용 X.
"""
from __future__ import annotations
import argparse
import html as H
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import parse_qs

BASE = Path(__file__).resolve().parent
QUEUE = BASE / "_queue.txt"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
REFERER = "https://elements.envato.com/"
PREVIEW_RE = re.compile(
    r'(//elements-resized\.envatousercontent\.com/elements-preview-images/[^"\\ ]+)')
UUID_QS_RE = re.compile(r'preview-images/([a-f0-9-]+)\?(.*)')


def parse_queue() -> list[tuple[str, str]]:
    """returns [(url, slug_code)]; slug_code = URL 마지막 '-' 뒤 영숫자."""
    items = []
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        url = s.split("#", 1)[0].strip()  # 인라인 주석 제거
        if not url.startswith("http"):
            continue
        code = url.rstrip("/").rsplit("-", 1)[-1]
        items.append((url, code))
    return items


def fetch_html(url: str) -> str | None:
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "30", "-A", UA, url],
            capture_output=True, timeout=40,
        )
        if out.returncode != 0 or len(out.stdout) < 1000:
            return None
        return out.stdout.decode("utf-8", "replace")
    except Exception:
        return None


def extract_previews(html: str) -> list[str]:
    """UUID별 최대 해상도 1장씩, 서명 포함 https URL 리스트."""
    best: dict[str, tuple[int, str]] = {}
    for raw in PREVIEW_RE.findall(html):
        u = H.unescape(raw)
        m = UUID_QS_RE.search(u)
        if not m:
            continue
        uid, qs = m.group(1), m.group(2)
        try:
            w = int(parse_qs(qs).get("w", ["0"])[0])
        except ValueError:
            w = 0
        full = "https:" + u
        if uid not in best or w > best[uid][0]:
            best[uid] = (w, full)
    return [full for _w, full in best.values()]


def download(url: str, dest: Path) -> bool:
    try:
        out = subprocess.run(
            ["curl", "-sL", "--max-time", "60", "-A", UA, "-e", REFERER,
             "-o", str(dest), url],
            capture_output=True, timeout=70,
        )
        if out.returncode != 0 or not dest.exists() or dest.stat().st_size < 2000:
            if dest.exists():
                dest.unlink()
            return False
        head = dest.read_bytes()[:3]
        if head not in (b"\xff\xd8\xff", b"\x89PN", b"RIF", b"GIF"):  # jpg/png/webp/gif
            dest.unlink()
            return False
        return True
    except Exception:
        if dest.exists():
            dest.unlink()
        return False


def process_item(url: str, code: str, do_download: bool) -> dict:
    folder = BASE / code
    html = fetch_html(url)
    if html is None:
        return {"code": code, "url": url, "status": "fetch_failed", "n": 0}
    previews = extract_previews(html)
    if not previews:
        return {"code": code, "url": url, "status": "no_previews", "n": 0}
    if not do_download:
        return {"code": code, "url": url, "status": "listed", "n": len(previews)}
    folder.mkdir(exist_ok=True)
    ok = 0
    for i, purl in enumerate(previews):
        dest = folder / f"{i:02d}.jpg"
        if download(purl, dest):
            ok += 1
        time.sleep(0.3)
    status = "ok" if ok == len(previews) else ("partial" if ok else "download_failed")
    return {"code": code, "url": url, "status": status, "n": ok, "found": len(previews)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="slug 코드 1개만 처리(검증용)")
    ap.add_argument("--list", action="store_true", help="다운 없이 미리보기 개수만")
    args = ap.parse_args()

    items = parse_queue()
    if args.only:
        items = [(u, c) for u, c in items if c == args.only]
        if not items:
            print(f"[!] --only {args.only} 큐에 없음", file=sys.stderr)
            return 1

    print(f"== envato 수집 {'(list)' if args.list else ''} — {len(items)}개 item ==")
    results = []
    for url, code in items:
        r = process_item(url, code, do_download=not args.list)
        results.append(r)
        mark = {"ok": "OK", "listed": "..", "partial": "~", "no_previews": "X",
                "fetch_failed": "XX", "download_failed": "XD"}.get(r["status"], "?")
        extra = f" ({r['n']}/{r.get('found', r['n'])})" if not args.list else f" ({r['n']})"
        print(f"  [{mark}] {code}{extra}  {r['status']}")
        time.sleep(0.5)

    ok = [r for r in results if r["status"] == "ok"]
    partial = [r for r in results if r["status"] == "partial"]
    fail = [r for r in results if r["status"] in ("fetch_failed", "no_previews", "download_failed")]
    print(f"\n== 합계: 성공 {len(ok)} · 부분 {len(partial)} · 실패 {len(fail)} / 총 {len(results)} ==")
    if fail:
        print("실패 item:")
        for r in fail:
            print(f"  - {r['code']} ({r['status']}) {r['url']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
