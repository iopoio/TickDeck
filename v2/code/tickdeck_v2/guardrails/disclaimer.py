"""disclaimer.py — disclaimer 텍스트 생성 placeholder (T29 실 구현).

feature_spec.md 6.3 정합. 3 영역 disclaimer:
- 첫 화면 (랜딩·T23): "결과 deck = 초안·사용자 검토·수정 의무·계정 X·세션 종료 시 자동 삭제·BYOD 가능"
- PPTX 첫 페이지 (T17): "draft for review · not final · 본 deck = AI 보조·사용자 검토 의무"
- review gate (T30 영역 가시)

본 파일 = 인터페이스 sketch. 실 구현 = T29 (T17 + T23 의존).
"""

from __future__ import annotations

from typing import Literal

DisclaimerSurface = Literal["landing", "pptx_first_page", "review_gate"]


def get_disclaimer_text(surface: DisclaimerSurface, language: str = "ko") -> str:
    """surface별 disclaimer 텍스트 영역 반환. locales/<language>.json 영역 read.

    실 구현 = T29.
    """
    raise NotImplementedError("T29 (Phase 5) 영역 실 구현.")


def build_pptx_disclaimer_slide_data(language: str = "ko") -> dict:
    """T17 pptx 영역 첫 페이지 disclaimer 슬라이드 데이터 dict.

    실 구현 = T29.
    """
    raise NotImplementedError("T29 (Phase 5) 영역 실 구현.")
