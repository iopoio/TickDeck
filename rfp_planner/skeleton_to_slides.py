#!/usr/bin/env python3
"""제안 골격(skeleton) → deck_harness slides.json (셸 덱).

deck_harness(범용 렌더)는 건드리지 않는다 — 그 입력(slides.json)만 만들어 넘긴다.
출력 셸 = 표지 + 평가구조 개요 + 평가항목별 섹션 디바이더 + 제약 클로징.
각 섹션의 '내용'(주장·근거·카피)은 backlog C 단계라 placeholder로 둔다.

실행:
  python3 skeleton_to_slides.py R26BK01604184 --keyword 해외홍보관   # 라이브 공고
  python3 skeleton_to_slides.py /path/제안요청서.hwp                  # 로컬 파일
→ tools/deck_harness/slides_rfp_pilot.json 생성. 이후 deck_harness build.py로 렌더.
"""
import json, argparse
from pathlib import Path
import rfp_pipeline as R

# 공공 제안 = 신뢰·권위 톤(딥블루, 톤다운·네온 X)
THEME = "T04_meeting_blue"
BRAND = {"name": "제안 골격", "accent": "#1e5563", "accent_dark": "#13323c",
         "accent_soft": "#cfe3e8", "background": "#f6f8f9", "ink": "#15243a",
         "muted": "#56697e", "panel": "#ffffff", "line": "#dbe5ec"}

DH_DEFAULT = R.ROOT / "Think/tools/deck_harness/slides_rfp_pilot.json"


def to_slides(sk: dict) -> dict:
    g = sk.get("공고", {})
    title = g.get("공고명") or "RFP 제안 골격"
    slides = [{
        "layout": "cover_hero", "cover_variant": "left",
        "brand_mark": g.get("발주") or "RFP",
        "brand_sub": "제안 골격 · RFP 배점-매칭",
        "title": title[:38],
        "subtitle": f"추정가 {g.get('추정가', '-')} · 개찰 {g.get('개찰', '-')}",
        "cover_meta": "TickDeck rfp_planner · 셸(내용 전 단계)",
    }, {
        "layout": "title-hero", "eyebrow": "평가 구조",
        "title": f"기술 {sk['기술배점합']}점 + 가격 {sk.get('가격배점')}점",
        "subtitle": "배점이 곧 분량 — 배점 큰 항목을 깊게",
        "bullets": [f"{s['평가항목']} · {s['노리는배점']}점 → {s['슬라이드수']}슬라이드" for s in sk["섹션"]],
    }]
    for i, s in enumerate(sk["섹션"], 1):
        slides.append({
            "layout": "title-hero", "eyebrow": f"평가항목 {i} · {s['노리는배점']}점",
            "title": s["평가항목"],
            "subtitle": f"{s['슬라이드수']}슬라이드 · 평가위원이 여기서 채점",
            "bullets": ["[내용 = backlog C: 주장·근거·카피 생성 단계]",
                        f"노림: {s['항목'] if '항목' in s else s['평가항목']} 배점 최대화"],
        })
    slides.append({
        "layout": "closing", "eyebrow": "작성 시 준수",
        "title": "RFP 제약 (카피에 주입)",
        "subtitle": "이 골격 위에 내용을 채울 때 반드시",
        "bullets": sk.get("RFP제약") or ["(추출된 제약 없음)"],
    })
    return {"title": title[:50], "theme": THEME, "brand": BRAND, "slides": slides}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="공고번호(R26...) 또는 로컬 RFP 경로")
    ap.add_argument("--keyword", default="홍보")
    ap.add_argument("--bgn", default="202606200000"); ap.add_argument("--end", default="202606272359")
    ap.add_argument("--out", default=str(DH_DEFAULT))
    a = ap.parse_args()
    p = Path(a.target)
    sk = R.run_from_file(p) if p.exists() else \
        R.run_from_notice(a.target, a.keyword, a.bgn, a.end, Path(__file__).parent / "_work")
    Path(a.out).write_text(json.dumps(to_slides(sk), ensure_ascii=False, indent=2))
    print(f"slides.json → {a.out}  ({len(sk['섹션'])+3}슬라이드)")
