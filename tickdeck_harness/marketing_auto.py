#!/usr/bin/env python3
"""2026 마케팅 트렌드 — 풀 사이클 자동 제작(앞 절반 자동화 end-to-end).

흐름(전부 자동): PDF → dig_source(OCR 폴백) → dig_agent(CED 추출) → dig_trace(재인용 추적)
              → story_assist 디렉터(outline 제안) → compose_deck(자동 조립) → engine(렌더).
본 스크립트는 캐시된 run 산출물(runs/dmt_2026/)로 재현 — CED·outline은 에이전트가 자동 생성한 것.
⚠️ HITL: statgrid 라벨·내러티브·최종 어조 다듬기는 사람 몫. 이건 '골격까지' 자동.
실행: python3 marketing_auto.py [theme]
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).with_name("pipeline")))
from dig_agent import extract_ceds                  # noqa: E402
from story_assist import parse_outline, compose_deck  # noqa: E402
from engine import build_deck, selfcheck            # noqa: E402

RUN = pathlib.Path(__file__).with_name("runs") / "dmt_2026"


def main(theme="breeze"):
    ceds, dropped = extract_ceds((RUN / "deloitte_ceds.json").read_text(encoding="utf-8"), current_year=2026)
    outline, err = parse_outline((RUN / "deloitte_outline.json").read_text(encoding="utf-8"))
    assert outline and not err, err
    slides = compose_deck(outline, ceds, meta_extra={
        "eyebrow": "2026 마케팅 트렌드 · 풀 사이클 자동",
        "sub": "Deloitte 1차 문서 → 자동 추출·검증·구성(앞 절반 무인). 라벨·어조 최종은 사람."})
    html = build_deck(slides, theme=theme, title="2026 마케팅 트렌드 — 풀 사이클 자동")
    out = pathlib.Path(__file__).with_name(f"out_auto_{theme}.html")
    out.write_text(html, encoding="utf-8")
    selfcheck(slides, html)
    print(f"OK [{theme}] — {len(slides)}슬라이드 · {len(set(s['layout'] for s in slides))}레이아웃 · "
          f"CED {len(ceds)}건(폐기 {len(dropped)}) · 챕터 {len(outline['chapters'])} → {out.name}")
    print(f"  thesis: {outline['thesis']}")
    return slides


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "breeze")
