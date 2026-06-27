#!/usr/bin/env python3
"""CED/CEMS — 수치-출처-한계 강결합 + DWS 라우팅 + 렌더 게이트.

정보 단위 = Claim·Evidence·Metric·Source·Limitation. route()가 슬라이드 배치 등급 결정:
  MAIN(빅넘버 kpi) · QUALITATIVE(카드/불릿) · DIRECTIONAL(수치 숨기고 증감만) · DROP(삭제).
하드 게이트(D.2): metric None 또는 conf<0.6 → DROP / conf<0.8 또는 tier∉{T1,T2} → 수치 숨김.
그 위에 DWS 점수(A5)로 MAIN vs 정성 가른다. 두 룰을 한 라우터로 합침.

출처(캐논): 00_SYNTHESIS Part A4~A5·Part D.2. story_mapper가 route 결과로 engine 슬라이드 생성.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date
import re
from dig_schema import DigRecord  # 같은 폴더(직접 실행 시) — 패키지 임포트는 story_mapper에서 sys.path

MAIN, QUALITATIVE, DIRECTIONAL, DROP = "MAIN", "QUALITATIVE", "DIRECTIONAL", "DROP"
TIER_SCORE = {"T1": 10, "T2": 6, "T3": 3}


@dataclass
class CED:
    claim: str
    metric: str | None       # 없으면 메인 배치 불가
    source: DigRecord
    limitation: str = ""      # 비면 UNAUDITED(신뢰 방어 못 함)
    confidence: float = 0.0   # 0~1 (디깅·교차검증 산출)


# DWS = Tier×0.4 + Recency×0.3 + Sample×0.2 + Method×0.1 (각 0~10) → 0~10 (A5)
# 컴포넌트 점수기는 naive 존재여부 휴리스틱 — 정밀 튜닝(NLP 표본추출)은 데이터 쌓이면.
def _recency(year, cy):
    if year is None:
        return 0.0
    # ponytail: 연 2점 선형 감점(5년=0). 도메인별 반감기(A5)는 데이터 모이면 교체.
    return max(0.0, 10 - (cy - year) * 2)


def _has_num(s):
    return bool(re.search(r"\d", s or ""))


def dws(ced, current_year=None):
    cy = current_year or date.today().year
    s = ced.source
    tier = TIER_SCORE.get(s.tier, 0)
    recency = _recency(s.year, cy)
    sample = 10.0 if _has_num(s.sample) else (4.0 if s.sample else 0.0)  # ponytail: N 존재여부
    method = 8.0 if s.sample else 0.0                                    # method 정보 = sample 필드에 섞임
    score = tier * 0.4 + recency * 0.3 + sample * 0.2 + method * 0.1
    if "UNRELIABLE" in s.flags:
        score -= 3                                                        # 좀비/순환/배드티어 감점
    return round(score, 2)


def route(ced, current_year=None):
    """슬라이드 배치 등급. 하드 게이트(D.2) → DWS(A5) 순."""
    if ced.metric is None or ced.confidence < 0.6:
        return DROP
    score = dws(ced, current_year)
    weak = ced.confidence < 0.8 or ced.source.tier not in ("T1", "T2")
    if weak:
        return QUALITATIVE if score >= 5 else DIRECTIONAL   # 수치 숨기고 증감 화살표만
    return MAIN if score >= 8 else QUALITATIVE


def audited(ced):
    """Limitation 없으면 UNAUDITED(A4) — 외부 제출 전 사람이 채워야."""
    return bool(ced.limitation.strip())


if __name__ == "__main__":
    cy = 2026
    strong = DigRecord("c", "73%", "https://data.bls.gov/r.pdf", "T1", 2026,
                       sample="N=1,200", visited_primary=True)
    # 강한 T1·신뢰 0.92 → MAIN
    assert route(CED("c", "73%", strong, "북미 표본", 0.92), cy) == MAIN

    # 동일 소스라도 metric 없으면 DROP
    assert route(CED("c", None, strong, "", 0.92), cy) == DROP
    # 신뢰 낮으면 DROP
    assert route(CED("c", "73%", strong, "", 0.5), cy) == DROP

    weak = DigRecord("c", "20%", "https://mckinsey.com/r", "T2", 2025, sample="N=500")
    # T2·conf 0.7 → 약함 → 점수 높으면 QUALITATIVE
    assert route(CED("c", "20%", weak, "유럽", 0.7), cy) == QUALITATIVE

    poor = DigRecord("c", "5%", "https://blog.x.com/p", "T3", None)  # 연도없음·표본없음
    assert route(CED("c", "5%", poor, "", 0.65), cy) == DIRECTIONAL

    assert not audited(CED("c", "5%", poor, "", 0.65))
    assert audited(CED("c", "5%", poor, "유럽 한정", 0.65))
    print("ced OK — MAIN/DROP×2/QUALITATIVE/DIRECTIONAL/audited 통과")
