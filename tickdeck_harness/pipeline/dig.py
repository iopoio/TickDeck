#!/usr/bin/env python3
"""디깅 입구 — 요청 빌더 + 응답 파서. 스키마와 디깅 에이전트 사이 어댑터.

dig.py는 웹을 직접 안 돈다 — 웹 방문은 디깅 에이전트(신야 GLM/Qwen :online,
또는 WebSearch 가진 본부 Agent)의 일. 여기는 (1) 그 에이전트에 줄 강제 프롬프트를 짓고
(2) 돌아온 JSON을 DigRecord로 받아 validate까지 돌려 '풀'을 만든다.
= synthesis Part D.1 "디깅 에이전트 강제 스키마"의 코드 입구. dig.py 백로그 fix.
"""
from __future__ import annotations
import json, re
from dig_schema import DigRecord, validate, DIG_PROMPT

_ALLOWED = {"claim", "metric", "url", "tier", "year", "publisher", "report",
            "sample", "region", "coi", "visited_primary", "paywall"}
_REQUIRED = ("claim", "url", "tier")   # 없으면 그 레코드 폐기


def build_dig_request(topic, claims=None, lenses=None):
    """디깅 에이전트에 줄 프롬프트. DIG_PROMPT(규격) + 주제 + (선택)검증할 주장·렌즈."""
    p = [DIG_PROMPT, f"\n주제: {topic}"]
    if claims:
        p.append("우선 출처를 확보할 주장(각각 레코드 1개+):\n- " + "\n- ".join(claims))
    if lenses:
        p.append("적용 렌즈(자료 수집 각도): " + ", ".join(lenses))
    p.append('반환: 위 필드의 JSON 배열만. 코드펜스/설명 없이 [ {...}, ... ].')
    return "\n".join(p)


def parse_dig_response(text, current_year=None):
    """에이전트 반환 텍스트 → (검증된 DigRecord 리스트, 폐기사유 리스트).

    코드펜스·앞뒤 prose 허용(첫 '['~마지막 ']' 추출). 필수필드 없으면 폐기.
    """
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return [], ["NO_JSON_ARRAY"]
    try:
        rows = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return [], [f"BAD_JSON: {e}"]
    records, dropped = [], []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(not row.get(k) for k in _REQUIRED):
            dropped.append(f"row{i}: 필수필드 누락")
            continue
        kw = {k: row[k] for k in _ALLOWED if k in row}
        kw.setdefault("metric", None)
        kw.setdefault("year", None)
        records.append(validate(DigRecord(**kw), current_year=current_year))
    return records, dropped


if __name__ == "__main__":
    # 에이전트 반환 모사(코드펜스 + prose 감싸기 + 한 줄은 필수필드 누락)
    sample = '''좋아요, 찾았습니다:
```json
[
  {"claim":"AI 유료전환", "metric":"73%", "url":"https://data.bls.gov/r.pdf",
   "tier":"T1", "year":2026, "publisher":"BLS", "sample":"N=1200", "visited_primary":true},
  {"claim":"진정성 갈망", "metric":"42%", "url":"https://news.x.com/p",
   "tier":"T1", "year":2026, "visited_primary":false},
  {"metric":"99%", "url":"https://x.com", "tier":"T2"}
]
```
끝.'''
    recs, dropped = parse_dig_response(sample, current_year=2026)
    assert len(recs) == 2, (len(recs), dropped)             # 셋째 = claim 없음 → 폐기
    assert len(dropped) == 1 and "row2" in dropped[0], dropped
    assert recs[0].tier == "T1" and recs[0].flags == [], recs[0].flags   # 깨끗한 1차
    assert recs[1].tier == "T3" and "TIER_DEMOTED" in recs[1].flags      # 1차미방문 언론 T1 → 강등
    # 빈/깨진 입력
    assert parse_dig_response("출처 못 찾음")[0] == []
    assert build_dig_request("2026 마케팅", ["진정성 프리미엄"], ["counterfactual"]).count("주제:") == 1
    print(f"dig OK — 파싱 {len(recs)}건·폐기 {len(dropped)}건·강등 검출·빈입력 안전")
