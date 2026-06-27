#!/usr/bin/env python3
"""디깅 강제 스키마 — 검색 결과를 구조화 반환·훈련지식 빈칸 채우기 차단.

신야(GLM/Qwen :online) 디깅 에이전트가 DIG_PROMPT로 이 스키마(DigRecord)를 채워 반환.
validate()가 좀비/순환인용/페이월 자동 flag + 1차 미방문 T1은 tier 강등.
= Codex/Gemini 리뷰 1순위 약점(출처/근거) fix.

출처(캐논): 00_SYNTHESIS Part A1~A3·Part D.1. Pydantic 대신 stdlib dataclass(새 의존성 X).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date

TIERS = ("T1", "T2", "T3")  # T1 정부/규제/SEC/특허/학술 · T2 컨설팅/협회 · T3 언론/뉴스레터

# 언론·블로그 도메인(원본 링크 없으면 순환인용) / 1차 원문 힌트
_NEWS = ("news", "/blog", "medium.com", "substack", "forbes.com", "techcrunch",
         "businesswire", "prnewswire", "naver.com", "tistory")
_PRIMARY = (".gov", ".pdf", "sec.gov", "patents.", "data.", ".go.kr", "doi.org")


@dataclass
class DigRecord:
    claim: str                    # 이 소스가 뒷받침하는 핵심 주장
    metric: str | None            # 수치(없으면 None → CED 메인 배치 불가)
    url: str                      # 실제 방문 URL(필수)
    tier: str                     # T1/T2/T3 (에이전트 자기보고 → validate가 강등 가능)
    year: int | None              # 발행연도(모르면 None)
    publisher: str = ""           # 발행기관(A6 인용) — 예: McKinsey
    report: str = ""              # 보고서명(A6 인용) — 예: State of Marketing Europe 2026
    sample: str = ""              # 표본 N·방식
    region: str = ""              # 지역 scope
    coi: str = ""                 # 이해관계(자사조사·후원·투자의견)
    visited_primary: bool = False # 1차 원문(.gov/공시/PDF) 직접 열람했나
    paywall: bool = False         # 제목/요약만(본문 못 봄)
    flags: list = field(default_factory=list)  # validate가 채움


def validate(rec, current_year=None, decay_years=3):
    """flag 계산 + tier 강등(in-place). decay_years = 좀비 임계(테크 도메인 3년)."""
    cy = current_year or date.today().year
    flags = []
    if rec.tier not in TIERS:
        flags.append("BAD_TIER")
    if rec.year is None:
        flags.append("NO_YEAR")
    elif cy - rec.year > decay_years:          # A3 좀비: 오래된 수치 최신인 척
        flags.append("ZOMBIE")

    dom = rec.url.lower()
    looks_primary = any(h in dom for h in _PRIMARY)
    is_news = any(n in dom for n in _NEWS)
    # A3 출처세탁: 언론 도메인인데 1차 원문 미열람·원본 힌트 없음
    if is_news and not (rec.visited_primary or looks_primary):
        flags.append("CIRCULAR_CITATION")
    if rec.paywall:
        flags.append("PAYWALL")
    # D.1 1차 방문 못 한 T1은 단독 인용 불가 → T3 강등
    if rec.tier == "T1" and not (rec.visited_primary or looks_primary):
        rec.tier = "T3"
        flags.append("TIER_DEMOTED")
    if {"ZOMBIE", "CIRCULAR_CITATION", "BAD_TIER"} & set(flags):
        flags.append("UNRELIABLE")             # 단독 수치 인용 금지

    rec.flags = flags
    return rec


# 디깅 에이전트 시스템 프롬프트(앞에 붙임). 핵심 = 훈련지식 빈칸 채우기 금지.
DIG_PROMPT = """너는 트렌드 리포트 디깅 애널리스트다. 각 수치/주장마다 아래 JSON을 채워 반환한다.
규칙(어기면 그 레코드 폐기):
1. 실제 방문한 URL에서 읽은 것만 적는다. 훈련 지식·기억으로 빈칸을 채우지 마라.
2. 1차 원문(.gov/공시/PDF/학술/특허)을 직접 열지 못했으면 tier를 T1로 적지 마라(T3로).
3. 모르는 필드는 추측하지 말고 null. year 모르면 null(좀비로 자동 강등됨).
4. visited_primary = 원본 데이터(언론 재인용 아님)를 실제로 열었을 때만 true.
필드: claim, metric(없으면 null), url, tier(T1|T2|T3), year(int|null),
      sample("N·방식"), region, coi, visited_primary(bool), paywall(bool)."""


if __name__ == "__main__":
    # 1차 미방문 T1 언론 인용 → T3 강등 + 순환 + UNRELIABLE
    r = validate(DigRecord("AI 유료전환 73%", "73%", "https://news.example.com/x",
                           "T1", 2025, visited_primary=False), current_year=2026)
    assert r.tier == "T3", r.tier
    assert "TIER_DEMOTED" in r.flags and "CIRCULAR_CITATION" in r.flags and "UNRELIABLE" in r.flags, r.flags

    # 오래된 연도 → 좀비
    z = validate(DigRecord("c", "10%", "https://sec.gov/a.pdf", "T1", 2020,
                           visited_primary=True), current_year=2026)
    assert "ZOMBIE" in z.flags and "UNRELIABLE" in z.flags, z.flags

    # 깨끗한 T1 1차 원문 → flag 없음, tier 유지
    ok = validate(DigRecord("d", "5%", "https://data.bls.gov/r.pdf", "T1", 2026,
                            visited_primary=True), current_year=2026)
    assert ok.tier == "T1" and ok.flags == [], ok.flags

    # 연도 없음 → NO_YEAR
    ny = validate(DigRecord("e", None, "https://mckinsey.com/r", "T2", None), current_year=2026)
    assert "NO_YEAR" in ny.flags, ny.flags
    print("dig_schema OK — 강등/좀비/순환/clean 4케이스 통과")
