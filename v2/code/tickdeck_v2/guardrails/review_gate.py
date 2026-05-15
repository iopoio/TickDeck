"""review_gate.py — 다운로드 전 사용자 1차 review placeholder (T30 실 구현).

feature_spec.md 6.4 정합. Step 7 PPTX 생성 후 미리보기 (썸네일 또는 1페이지)
→ "다운로드"·"재생성" 버튼. 재생성 = 1회 (PRD 결정 8). 2회 시도 = 안내.

본 파일 = 인터페이스 sketch. 실 구현 = T30 (T17 + T26 의존).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MAX_REGENERATIONS = 1


@dataclass
class ReviewState:
    """세션 1개 = 1 ReviewState. 재생성 카운터·미리보기 경로 자국."""

    pptx_path: Path
    preview_path: Path | None = None
    regenerations_used: int = 0


def can_regenerate(state: ReviewState) -> bool:
    """재생성 가능 여부 판정. MAX_REGENERATIONS 초과 시 False.

    실 구현 = T30.
    """
    raise NotImplementedError("T30 (Phase 5) 영역 실 구현.")


def render_preview(pptx_path: Path) -> Path:
    """PPTX 첫 페이지 또는 썸네일 영역 image 영역 추출. 미리보기 가시.

    실 구현 = T30 (python-pptx 또는 libreoffice headless 영역 검토).
    """
    raise NotImplementedError("T30 (Phase 5) 영역 실 구현.")


def regenerate_warning_text(language: str = "ko") -> str:
    """2회 시도 시 안내 텍스트 영역. locales/<language>.json 영역 read.

    실 구현 = T30.
    """
    raise NotImplementedError("T30 (Phase 5) 영역 실 구현.")
