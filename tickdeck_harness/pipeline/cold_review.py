#!/usr/bin/env python3
"""냉정 리뷰 시스템 — 루프 8단계(비저자 비평). 저자 자가평가 금지(klcha #7).

흐름: deck_summary(slides) → build_request(비저자 잔혹 프롬프트 + 균형 분류) →
     비평가(destroyer 서브에이전트 / 신야 vision·text)가 JSON findings 반환 →
     parse_review → triage(fix/label/ignore 3단). 적용 판단은 사람(HITL).
⚖️ 균형(후추님): 냉정 리뷰는 약점 지도지 삭제 체크리스트 X. 약한 재료는 삭제 아니라
   강등+라벨(label)로 유지. fix=싼데효과큰것만·ignore=완벽주의는 버림. stakes에 맞춤.
출처(캐논): 00_SYNTHESIS_콘텐츠방법론 B7(적대적 셀프리뷰)·Part D.3 HITL.
"""
from __future__ import annotations
import json, re

TIERS = ("fix", "label", "ignore")

CRITIQUE_PROMPT = """너는 McKinsey·Bain 출신의 잔혹한 전략 리뷰어다. 너는 이 덱을 만들지 않았다 — 이해관계 0. 칭찬·완충("그래도 좋은 점은") 금지. 오직 약점·반론·빈틈·치명상만, 저자가 변명 못 하게 구체적으로.

아래 [덱 요약]을 7각도로 깐다:
① 명제 진부함/반증 가능성(인과 없이 접속사로 이은 건 아닌가)
② 출처 과의존·지역 정합성·이해충돌(파는 쪽 인용 등)
③ 챕터별 So-What이 의사결정자에게 새로운가, 당연한 소리인가
④ 자기모순 수치(한 수치가 덱 자기 논리를 무력화하나)
⑤ 반대 증거 부재(반례·실패 사례)
⑥ 의사결정자가 5분 내 던질 반박
⑦ 챕터 간 전략 모순

각 약점마다 **균형 분류(tier)**를 매겨라 — 재료를 다 지우지 않기 위해:
- "fix"    = 싼데 효과 큰 교정(출처 범위 라벨·교차검증 1개·한계 한 줄·정의 보강). → 해라.
- "label"  = 삭제 말고 강등+솔직 라벨로 충분("단일 출처·방향 신호"). → 재료 유지.
- "ignore" = 완벽주의 요구(모든 수치 4출처 등)로 이 덱 stakes엔 과함. → 버려라.
stakes={stakes} (internal=내부 트렌드 레이더는 방향 신호 떳떳이 OK / external=외부 제출은 약한 재료 0)

반환: JSON 배열 하나만(설명·코드펜스 없이).
[{{"area":"명제","weakness":"한 줄","severity":0~10,"tier":"fix|label|ignore","fix":"구체 처방 한 줄"}}]

[덱 요약]
"""


def deck_summary(slides):
    """engine 슬라이드 리스트 → 비평가용 텍스트 요약(명제·챕터·수치·출처)."""
    out = []
    for s in slides:
        lt = s.get("layout"); foot = s.get("foot", "")
        if lt == "cover":
            out.append(f"[표지] {s.get('title','')} — {s.get('sub','')}")
        elif lt == "agenda":
            out.append(f"[명제] {s.get('title','')}")
        elif lt == "divider":
            out.append(f"[챕터 {s.get('num','')}] {s.get('title','')} — {s.get('sub','')}")
        elif lt == "kpi":
            out.append(f"[빅넘버] {s.get('value','')} · {s.get('title','')} (출처: {foot})")
        elif lt == "statgrid":
            nums = " / ".join(f"{st.get('value','')} {st.get('label','')}" for st in s.get("stats", []))
            out.append(f"[수치판] {s.get('title','')}: {nums} (출처: {foot})")
        elif lt == "line":
            out.append(f"[추이] {s.get('title','')} (출처: {foot})")
        elif lt == "donut":
            out.append(f"[비중] {s.get('value','')}% {s.get('title','')} (출처: {foot})")
        elif lt == "closing":
            out.append(f"[결론] {s.get('title','')}")
    return "\n".join(out)


def build_request(slides_or_summary, stakes="internal"):
    """비평가(destroyer 서브에이전트/신야)에 줄 프롬프트."""
    summary = slides_or_summary if isinstance(slides_or_summary, str) else deck_summary(slides_or_summary)
    return CRITIQUE_PROMPT.format(stakes=stakes) + summary


def parse_review(text):
    """비평가 JSON → findings 리스트(area·weakness·severity·tier·fix). 잘못된 tier는 label로."""
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    try:
        rows = json.loads(m.group(0))
    except json.JSONDecodeError:
        return []
    out = []
    for r in rows:
        if not isinstance(r, dict) or not r.get("weakness"):
            continue
        out.append({"area": r.get("area", ""), "weakness": r["weakness"],
                    "severity": float(r.get("severity", 5)),
                    "tier": r["tier"] if r.get("tier") in TIERS else "label",
                    "fix": r.get("fix", "")})
    return out


def triage(findings):
    """균형 3단 분류 + 요약. fix=손볼것 / label=강등으로 유지 / ignore=버림."""
    buckets = {t: [f for f in findings if f["tier"] == t] for t in TIERS}
    buckets["_summary"] = (f"총 {len(findings)} · fix {len(buckets['fix'])} "
                           f"· label {len(buckets['label'])} · ignore {len(buckets['ignore'])}")
    return buckets


if __name__ == "__main__":
    # deck_summary
    slides = [{"layout": "cover", "title": "AI는 기본값", "sub": "..."},
              {"layout": "statgrid", "title": "AI 현실", "stats": [{"value": "10%", "label": "에이전틱 ROI"}],
               "foot": "Deloitte [T2]"},
              {"layout": "kpi", "value": "242조", "title": "온라인쇼핑", "foot": "통계청 [T1]"}]
    summ = deck_summary(slides)
    assert "에이전틱 ROI" in summ and "통계청" in summ, summ
    assert "[덱 요약]" in build_request(slides, "external") and "stakes=external" in build_request(slides, "external")

    # parse + triage (균형 3단)
    sample = '''까봤다:
```json
[{"area":"명제","weakness":"진부","severity":8,"tier":"fix","fix":"quotability로 재정의"},
 {"area":"출처","weakness":"Deloitte 단일","severity":7,"tier":"label","fix":"단일출처 방향신호 표기"},
 {"area":"검증","weakness":"4출처 요구","severity":3,"tier":"ignore","fix":"-"},
 {"area":"x","weakness":"bad tier","severity":5,"tier":"???","fix":"-"}]
```'''
    f = parse_review(sample)
    assert len(f) == 4 and f[3]["tier"] == "label", f          # 잘못된 tier → label
    t = triage(f)
    assert len(t["fix"]) == 1 and len(t["label"]) == 2 and len(t["ignore"]) == 1, t["_summary"]
    print(f"cold_review OK — deck_summary·build_request·parse·triage({t['_summary']})")
