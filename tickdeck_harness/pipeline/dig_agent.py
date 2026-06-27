#!/usr/bin/env python3
"""디깅→CED 자동화 — 소스 문서 텍스트를 읽어 CED-ready JSON을 만들고, CED로 빌드.

앞 절반 수동작업(PDF 읽고 손으로 CED 박기)을 자동화하는 첫 조각.
흐름: pdftotext로 텍스트 추출 → 디깅 에이전트(DIG_AGENT_PROMPT)가 구조화 JSON 반환
     → extract_ceds()가 validate + CED 빌드 → story_mapper가 챕터로 조립.
에이전트 = 본부 Claude(Agent 툴) 또는 anthropic_call_wrapper. 중국모델 X(후추님 자료).
출처(캐논): dig_schema(A1~A3) + 00_SYNTHESIS_콘텐츠방법론 Part D.
"""
from __future__ import annotations
import json, re
from dig_schema import DigRecord, validate
from ced import CED

# 디깅 에이전트 프롬프트 — 텍스트 뒤에 붙임. 티어링·재인용·신뢰도 규칙 내장.
DIG_AGENT_PROMPT = """너는 트렌드 리포트 디깅 애널리스트다. 아래 [문서]에서 **수치를 가진 주장**마다 JSON 레코드를 만든다.

규칙(어기면 그 레코드 폐기):
1. 문서에 실제로 있는 수치만. 없는 값·기억으로 채우지 마라. metric 없으면 그 주장은 만들지 마라.
2. tier = 그 수치의 **원출처 기관** 기준:
   - T1 = 정부/통계청/규제/SEC/특허/peer-reviewed 학술
   - T2 = 컨설팅(McKinsey·KPMG·Deloitte·PwC)·협회·시장조사사 자체 설문
   - T3 = 언론·뉴스레터·블로그
3. **재인용 판정**: 이 문서가 다른 기관 수치를 인용한 거면(예: 광고대행사 리포트가 통계청을 인용)
   → publisher는 이 문서 발행사, report는 이 문서명, limitation에 "원출처 OOO 재인용" 명시, visited_primary=false.
   → 이 문서가 **자체 1차 설문/분석**(예: Deloitte 자기 설문)이면 visited_primary=true.
4. confidence(0~1) = 출처 강도: 1차+표본N 공개+최근 = 0.85~0.95 / 단일·N 미공개·재인용 = 0.55~0.7 / 예측·벤더COI = 0.5~0.6.
5. limitation = 정직한 한계 한 줄(지역·표본·재인용·예측치·이해관계).

각 레코드 필드(JSON):
{claim, metric, url(없으면 "local:<문서명>"), tier(T1|T2|T3), year(int|null),
 publisher, report, sample("N·방식"), region, coi, visited_primary(bool),
 confidence(0~1), limitation}

반환: JSON 배열만. 코드펜스/설명 없이 [ {...}, ... ].

[문서]
"""


def build_request(doc_text, max_chars=24000):
    """에이전트에 줄 프롬프트(프롬프트 + 문서 텍스트, 길면 자름)."""
    return DIG_AGENT_PROMPT + doc_text[:max_chars]


_REQ = ("claim", "url", "tier")


def extract_ceds(json_text, current_year=None):
    """에이전트 반환 JSON → (검증된 CED 리스트, 폐기사유). validate + CED 빌드."""
    m = re.search(r"\[.*\]", json_text, re.S)
    if not m:
        return [], ["NO_JSON_ARRAY"]
    try:
        rows = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return [], [f"BAD_JSON: {e}"]
    ceds, dropped = [], []
    for i, row in enumerate(rows):
        if not isinstance(row, dict) or any(not row.get(k) for k in _REQ) or not row.get("metric"):
            dropped.append(f"row{i}: 필수필드/metric 누락")
            continue
        rec = validate(DigRecord(
            claim=row["claim"], metric=row.get("metric"), url=row["url"], tier=row["tier"],
            year=row.get("year"), publisher=row.get("publisher", ""), report=row.get("report", ""),
            sample=row.get("sample", ""), region=row.get("region", ""), coi=row.get("coi", ""),
            visited_primary=bool(row.get("visited_primary", False)), paywall=bool(row.get("paywall", False)),
        ), current_year=current_year)
        ceds.append(CED(row["claim"], row.get("metric"), rec, row.get("limitation", ""), float(row.get("confidence", 0.6))))
    return ceds, dropped


if __name__ == "__main__":
    from ced import route
    sample = '''에이전트 답:
```json
[
 {"claim":"agentic AI로 유의미 ROI 내는 조직","metric":"10%","url":"local:deloitte-dmt-2026.pdf",
  "tier":"T2","year":2026,"publisher":"Deloitte","report":"Digital Marketing Trends 2026",
  "sample":"N=1,854 EMEA 임원","visited_primary":true,"confidence":0.88,"limitation":"EMEA 한정·2025 설문"},
 {"claim":"모바일 온라인쇼핑 비중","metric":"76%","url":"local:mezzo-2026.pdf",
  "tier":"T1","year":2025,"publisher":"CJ MezzoMedia","report":"2026 Trend Report",
  "visited_primary":false,"confidence":0.65,"limitation":"원출처 통계청 재인용·1차 미열람"},
 {"claim":"표본없는 추정","url":"local:x","tier":"T2"}
]
```'''
    ceds, dropped = extract_ceds(sample, current_year=2026)
    assert len(ceds) == 2 and len(dropped) == 1, (len(ceds), dropped)   # 셋째 = metric 없음 폐기
    assert route(ceds[0]) == "MAIN", route(ceds[0])                     # Deloitte 1차 → MAIN
    # Mezzo가 T1 주장했지만 1차 미열람 언론도메인 아님 → tier 유지(local), 단 재인용은 limitation에
    assert ceds[1].confidence == 0.65 and "재인용" in ceds[1].limitation
    print(f"dig_agent OK — CED {len(ceds)}건 빌드·폐기 {len(dropped)}·Deloitte MAIN 라우팅")
