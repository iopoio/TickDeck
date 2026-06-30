#!/usr/bin/env python3
"""제목 척추 추출 — deck_spec의 short_title만 순서대로 뽑아 'skim view'를 보여준다.
계약 C7(원칙 6)의 입력: 본문 가리고 제목만으로 논증이 서는지 qa-reviewer(opus)/사람이 판정한다.
여기선 *추출*과 *약한 힌트*까지만(논증 성립 판정은 모델 몫)."""
import json
import sys

SKIP = {"index", "source_appendix", "outro"}  # 척추 흐름에서 제외(표지/목차/출처/감사)
# 정체불명 압축·포맷명 힌트(참고용 — 확정 아님, C7에서 모델이 판정)
CRYPTIC_HINTS = ["매트릭스", "프레임워크", "유동적", "균형추", "패러다임"]


def extract(path):
    pages = json.load(open(path, encoding="utf-8")).get("pages", [])
    rows = []
    for i, p in enumerate(pages, 1):
        layout = p.get("layout", "")
        st = (p.get("short_title") or "").strip()
        flag = ""
        if layout not in SKIP and layout != "cover":
            if any(h in st for h in CRYPTIC_HINTS):
                flag = "  ⚠️정체불명/포맷명?(C7 확인)"
            elif len(st) <= 5 and layout != "divider":
                flag = "  ⚠️너무 짧음?"
        rows.append((i, layout, st, flag))
    return rows


def main(path):
    print("=== 제목 척추 (short_title만 · skim view) ===")
    for i, layout, st, flag in extract(path):
        mark = " " if layout in SKIP else ("▸" if layout == "divider" else "·")
        print(f"{i:2d} {mark} {st}{flag}")
    print("\n→ 본문 가리고 위 제목만 이어 읽어 논증이 서는지 판정(C7).")
    print("  끊기거나 정체불명·비병렬·결론→제언 미닫힘이면 page-planner 반송.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: spine_check.py <deck_spec.json>")
        sys.exit(1)
    main(sys.argv[1])
