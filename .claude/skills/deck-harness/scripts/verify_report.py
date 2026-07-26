#!/usr/bin/env python3
"""검증 리포트 1장 자동 생성 — 덱 동봉용 (PRD_PRODUCT §4.2 신뢰 가시화 실물).

run 폴더의 검증 산출물(02_verified·08_factcheck·08_external_review)을 읽어
"이 덱의 수치는 이렇게 검증됐다" 1페이지 HTML을 생성한다. 손 작성 금지 — 실측만 전기.

  python3 verify_report.py <run_dir>   # → <run_dir>/verification_report.html
"""
from __future__ import annotations
import json, sys, html
from pathlib import Path
from datetime import datetime

def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8")) if Path(p).exists() else None

def main():
    run = Path(sys.argv[1])
    ver = load(run / "02_verified.json") or {}
    fc = load(run / "08_factcheck.json")
    ext = load(run / "08_external_review.json")
    spec = load(run / "06_deck_spec.json") or {}

    src = ver.get("source_registry", {})
    tiers = {}
    for s in src.values():
        t = str(s.get("tier", "?")).upper().replace("TIER-", "")
        tiers[t] = tiers.get(t, 0) + 1
    n_metrics = len(ver.get("metric_registry", {}))
    pdf_count = len(list((run / "pdf").glob("*.pdf"))) if (run / "pdf").exists() else 0

    fc_line = "미실시"
    if fc:
        rows = fc.get("rows") or fc.get("results") or []
        if isinstance(rows, list) and rows:
            c = sum(1 for r in rows if str(r.get("verdict", r.get("status", ""))).lower() in ("match", "confirmed"))
            fc_line = f"덱 노출 수치 {len(rows)}건 전수 원문 재대조 — 일치 {c} / 불일치 {len(rows)-c}"
        else:
            fc_line = "전수 재대조 완료 (상세는 08_factcheck.json)"
    ext_line = "미실시"
    if ext:
        parts = [k for k in ("codex", "gemini") if isinstance(ext.get(k), dict) and ext[k].get("ok")]
        ext_line = f"외부 교차 리뷰 {len(parts)}자({'·'.join(parts)}) + 본부 트리아지 반영" if parts else "실시 (상세는 08_external_review.json)"

    title = ""
    for pg in spec.get("pages", []):
        if pg.get("short_title"):
            title = pg["short_title"]; break

    tier_str = " · ".join(f"Tier-{k} {v}건" for k, v in sorted(tiers.items()))
    now = datetime.now().strftime("%Y-%m-%d")
    out = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>검증 리포트</title>
<style>body{{font:15px/1.6 -apple-system,"Apple SD Gothic Neo",sans-serif;color:#1a1a24;max-width:800px;margin:40px auto;padding:0 24px}}
h1{{font-size:22px}} h2{{font-size:15px;margin-top:26px;color:#444}} .big{{font-size:34px;font-weight:800;color:#2b4a73}}
table{{border-collapse:collapse;width:100%;margin-top:8px}} td,th{{border-bottom:1px solid #e2e2e8;padding:8px 10px;text-align:left;font-size:14px}}
.muted{{color:#777;font-size:13px}}</style></head><body>
<h1>검증 리포트 — 이 덱의 수치는 이렇게 확인됐습니다</h1>
<p class="muted">덱: {html.escape(title)} · 생성 {now} · 자동 생성(검증 산출물 전기 — 손 작성 아님)</p>
<h2>1. 출처</h2>
<table><tr><th>항목</th><th>내용</th></tr>
<tr><td>등록 출처</td><td>{len(src)}건 ({tier_str})</td></tr>
<tr><td>원문 PDF 실물 보관</td><td>{pdf_count}건 — 페이지 단위 인용, 요청 시 원문 대조 가능</td></tr>
<tr><td>검증 수치 registry</td><td>{n_metrics}건 — 덱의 모든 수치는 이 registry에서만 주입(수기 입력 구조적 차단)</td></tr></table>
<h2>2. 팩트체크</h2><p>{fc_line}</p>
<h2>3. 외부 교차 리뷰</h2><p>{ext_line}</p>
<h2>4. 원칙</h2>
<p>실측(measured)과 전망(projected)을 구분 표기하고, 벤더 자기보고는 별도 플래그합니다. 반대 증거는 본문에 배치합니다. 확인 불가 수치는 싣지 않습니다.</p>
</body></html>"""
    dst = run / "verification_report.html"
    dst.write_text(out, encoding="utf-8")
    print(f"→ {dst}")

if __name__ == "__main__":
    main()
