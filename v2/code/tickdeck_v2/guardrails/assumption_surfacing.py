"""assumption_surfacing.py — 사용자 인풋 명시 슬라이드 placeholder (T28 실 구현).

feature_spec.md 6.2 정합. Step 7 PPTX 생성 시 1페이지 자동 추가:
"본 deck 인풋: 산업·청중·톤·출처 정책·분량·언어" 표. 사용자 결과 review 시
자기 인풋 영역 재확인. profile on/off 옵션.

본 파일 = 인터페이스 sketch. 실 구현 = T28 (T03 profile + T17 pptx 의존).
"""

from __future__ import annotations

from typing import Mapping

INPUT_KEYS = (
    "industry",
    "audience",
    "tone",
    "source_policy",
    "length",
    "language",
)


def is_enabled(profile: Mapping[str, str]) -> bool:
    """profile 영역 assumption surfacing on/off 판정.

    실 구현 = T28. default on (profile 명시 off 시만 skip).
    """
    raise NotImplementedError("T28 (Phase 5) 영역 실 구현.")


def build_assumption_slide_data(profile: Mapping[str, str]) -> dict:
    """6 인풋 영역 표 데이터 dict 영역 생성. T17 pptx_builder 영역 소비.

    반환 형식 (sketch):
        {
            "title": str,
            "rows": list[tuple[str, str]],  # (label, value)
        }
    실 구현 = T28.
    """
    raise NotImplementedError("T28 (Phase 5) 영역 실 구현.")
