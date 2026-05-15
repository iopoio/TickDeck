"""source_attribution.py — 자료 출처 자동 매핑 placeholder (T27 실 구현 영역).

feature_spec.md 6.1 정합. T12 research 메타데이터 (URL·title·source_id) → T17 pptx
footer 또는 각주 자동 매핑. 출처 정책 3 mode:
- strict: 모든 슬라이드 각주·footnote (Industry Research Compiler default)
- footer: 슬라이드 footer 영역만 (Marketing Brief default)
- free: footer X·인용 영역만

본 파일 = 인터페이스 sketch. 실 구현 = T27 (Phase 5·Phase 2·4 의존).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

SourcePolicy = Literal["strict", "footer", "free"]


@dataclass(frozen=True)
class SourceRef:
    """1 자료 1 ref. T12 research 영역 메타데이터 정합."""

    source_id: str
    title: str
    url: str
    license: str = ""
    country: str = ""


def render_footer(refs: Sequence[SourceRef], policy: SourcePolicy) -> str:
    """슬라이드 footer 문자열 생성. policy=free 시 빈 문자열.

    실 구현 = T27.
    """
    raise NotImplementedError("T27 (Phase 5) 영역 실 구현.")


def render_footnote(ref: SourceRef) -> str:
    """1 자료 각주 문자열 생성. strict mode 영역.

    실 구현 = T27.
    """
    raise NotImplementedError("T27 (Phase 5) 영역 실 구현.")


def collect_refs(research_payload: object) -> list[SourceRef]:
    """T12 research 결과 dict 영역에서 SourceRef list 추출.

    실 구현 = T27.
    """
    raise NotImplementedError("T27 (Phase 5) 영역 실 구현.")
