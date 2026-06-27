#!/usr/bin/env python3
"""원본 추적·대조 — 재인용 CED를 1차 출처와 대조해 판정.

후추님 정정: 강등은 '재인용이라서'가 아니라 '추적해보니 1차와 안 맞아서' 일어나야 한다.
흐름: 재인용 CED(visited_primary=false) → 추적 에이전트(DIG_TRACE_PROMPT)가 1차 원본
     찾아 대조 → verdict → apply_trace()가 반영:
       match        = 1차 일치 → 승격(visited_primary=true·tier=1차·conf↑) → MAIN 가능
       scope_diff   = 정의·범위가 달라 값이 다름(둘 다 유효) → 죽이지 말고 정의 라벨 의무
       contradiction= 같은 정의인데 값이 틀림 → DISCREPANCY + 강등(DROP)
       notfound     = 1차 못 찾음 → 강등 유지(미검증)
출처(캐논): 00_SYNTHESIS_콘텐츠방법론 A3(교차검증·세탁 차단·±10~15%·조건 명시 후 병기).
"""
from __future__ import annotations
from dig_schema import validate

# 추적 에이전트 프롬프트 — 재인용 1건(claim·metric·원출처)을 뒤에 붙여 호출.
DIG_TRACE_PROMPT = """너는 출처 검증 애널리스트다. 아래 [주장]의 수치가 **원출처(1차)에서 실제로 그 값인지** 확인한다.

1. 원출처 기관(예: 통계청·한국은행)의 **공식 자료**를 웹에서 찾아 직접 연다(보도자료·KOSIS·.go.kr·.gov). 언론 재인용 말고 1차.
2. **같은 정의·연도·지역**의 값을 찾는다(정의가 다르면 값이 달라진다 — 침투율 vs 비중, 표준 vs 해외포함 등 주의).
3. 판정(4-way):
   - match        = 1차 값이 주장 수치와 ±10% 내 일치 + 정의 같음
   - scope_diff   = 값이 다르지만 **정의·범위가 달라서**다(둘 다 유효). scope에 차이를 적어라(예: "해외판매 포함 광의")
   - contradiction= **같은 정의인데** 값이 틀림. primary_value에 실제 1차 값을 적어라
   - notfound     = 1차 원본을 못 찾음/페이월

반환(JSON 하나만): {"status":"match|scope_diff|contradiction|notfound","primary_value":"실제 1차 값","primary_url":"1차 URL","primary_tier":"T1|T2","scope":"정의 차이 한 줄","note":"한 줄"}

[주장]
"""


def trace_request(ced):
    """추적 에이전트에 줄 프롬프트(주장 1건)."""
    s = ced.source
    orig = s.publisher or "원출처 미상"
    return f"{DIG_TRACE_PROMPT}주장: {ced.claim}\n수치: {ced.metric}\n전달 문서가 인용한 원출처(추정): {orig}\n한계 메모: {ced.limitation}"


def apply_trace(ced, verdict):
    """trace verdict를 CED에 반영(in-place). verdict = dict(status, primary_value, primary_url, primary_tier, note)."""
    s = ced.source
    st = (verdict or {}).get("status")
    if st == "match":                                    # 1차 일치 → 승격
        s.visited_primary = True
        s.tier = verdict.get("primary_tier") or s.tier
        if verdict.get("primary_url"):
            s.url = verdict["primary_url"]
        ced.confidence = max(ced.confidence, 0.85)
        ced.limitation = (ced.limitation + " · 1차 대조 일치").strip(" ·")
        validate(s)                                      # flag 재계산(TIER_DEMOTED 해제)
    elif st == "scope_diff":                             # 정의 차이 → 죽이지 말고 라벨 의무
        if "SCOPE_DIFF" not in s.flags:
            s.flags = s.flags + ["SCOPE_DIFF"]
        ced.confidence = min(ced.confidence, 0.7)        # ≥0.6 유지(보존) — 정성/방향으로
        sc = verdict.get("scope") or verdict.get("note") or "정의·범위 차이"
        ced.limitation = (ced.limitation + f" · 정의: {sc}").strip(" ·")
    elif st == "contradiction":                          # 같은 정의·값 틀림 → 강등 + 플래그
        if "DISCREPANCY" not in s.flags:
            s.flags = s.flags + ["DISCREPANCY"]
        ced.confidence = min(ced.confidence, 0.45)       # < 0.6 → DROP
        pv = verdict.get("primary_value", "?")
        ced.limitation = (ced.limitation + f" · ⚠1차({pv})와 모순").strip(" ·")
    else:                                                # notfound → 강등 유지
        ced.limitation = (ced.limitation + " · 원본 추적 실패(미검증)").strip(" ·")
    return ced


if __name__ == "__main__":
    from dig_schema import DigRecord
    from ced import CED, route, MAIN, DROP

    def recite():  # 통계청 재인용(데모 문서가 전달) → validate가 T1→T3 강등해둔 상태
        r = validate(DigRecord("", None, "local:doc.pdf", "T1", 2024, publisher="통계청",
                               sample="전국 집계 1건", visited_primary=False))
        return CED("온라인쇼핑 거래액", "242조", r, "원출처 통계청 재인용", 0.7)

    # match → 1차 일치 → 승격 → MAIN
    c = recite()
    apply_trace(c, {"status": "match", "primary_value": "242조", "primary_url": "https://kostat.go.kr/x", "primary_tier": "T1"})
    assert c.source.visited_primary and route(c) == MAIN, (route(c), c.source.flags)

    # scope_diff(259는 광의 기준·둘 다 유효) → 보존(DROP 아님) + 정의 라벨
    c = CED("온라인쇼핑 거래액", "259조", recite().source, "원출처 통계청 재인용", 0.7)
    apply_trace(c, {"status": "scope_diff", "scope": "해외판매 포함 광의"})
    assert route(c) != DROP and "SCOPE_DIFF" in c.source.flags and "정의: 해외판매 포함 광의" in c.limitation

    # contradiction(같은 정의인데 값 틀림) → DROP + DISCREPANCY
    c = CED("온라인쇼핑 거래액", "300조", recite().source, "원출처 통계청 재인용", 0.7)
    apply_trace(c, {"status": "contradiction", "primary_value": "242조897억"})
    assert route(c) == DROP and "DISCREPANCY" in c.source.flags and "모순" in c.limitation

    # notfound → 강등 유지(추적 실패 메모)
    c = recite()
    before = route(c)
    apply_trace(c, {"status": "notfound"})
    assert route(c) == before and "추적 실패" in c.limitation
    print("dig_trace OK(4-way) — match→MAIN / scope_diff→보존+라벨 / contradiction→DROP / notfound→유지")
