#!/usr/bin/env python3
"""Render TickDeck deck_spec JSON through verified content registries.

The designer owns layout and shortening only. This renderer owns every metric
value and citation string by resolving metric_id/src_id from the verified
registry.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

CONTRACTS_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "harness-contracts" / "scripts"
if str(CONTRACTS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACTS_SCRIPT_DIR))

from contract_checks import SUPPORTED_CONTENT_BLOCK_TYPES, SUPPORTED_VIZ_CHART_TYPES, normalize_enclosed_numerals


PALETTES = {
    "editorial": {
        "theme": "editorial",
        "c60": "#FFFFFF",
        "c30": "#F7F8FA",
        "accent": "#5A6F92",
        "accent2": "#A8664F",
        "ink": "#1F2733",
        "muted": "#6B7384",
        "line": "rgba(31,39,51,.12)",
        "grid_line": "transparent",
        "slide_bg": "#FFFFFF",
        "slide_bg_size": "auto",
        "body_bg": "#F7F8FA",
        "card": "rgba(255, 255, 255, .7)",
        "radius": "0px",
        "t1": "#8A6F3D",
        "t2": "#A8664F",
        "t3": "#5A6F92",
        "t4": "#6D856D",
        "t5": "#7A5F73",
    },
    "tech": {
        "theme": "tech",
        "c60": "#EEF1F4",
        "c30": "#E7EBEF",
        "accent": "#1F4E79",
        "accent2": "#C56A3A",
        "ink": "#16202E",
        "muted": "#5B6675",
        "line": "rgba(31,78,121,.16)",
        "grid_line": "transparent",
        "slide_bg": "#EEF1F4",
        "slide_bg_size": "auto",
        "body_bg": "#E7EBEF",
        "card": "rgba(255, 255, 255, .72)",
        "radius": "0px",
        "t1": "#1F4E79",
        "t2": "#C56A3A",
        "t3": "#5B6675",
        "t4": "#9CB7CC",
        "t5": "#16202E",
    },
    "peppinch": {
        "theme": "peppinch",
        "c60": "#F1ECE0",
        "c30": "#EAE3D3",
        "accent": "#C86F1F",
        "accent2": "#C0863C",
        "ink": "#161410",
        "muted": "#6F665A",
        "line": "rgba(22,20,16,.14)",
        "grid_line": "transparent",
        "slide_bg": "#F1ECE0",
        "slide_bg_size": "auto",
        "body_bg": "#EAE3D3",
        "card": "rgba(255, 253, 248, .66)",
        "radius": "0px",
        "t1": "#FF9B3D",
        "t2": "#C0863C",
        "t3": "#6F665A",
        "t4": "#CBB89A",
        "t5": "#161410",
    },
    "marketing": {
        "theme": "marketing",
        "c60": "#FFFCF7",
        "c30": "#FFF2E8",
        "accent": "#F05F4B",
        "accent2": "#FFB24A",
        "ink": "#2B2623",
        "muted": "#7A6F68",
        "line": "rgba(240,95,75,.18)",
        "grid_line": "transparent",
        "slide_bg": "radial-gradient(circle at 12% 18%, rgba(240,95,75,.13) 0, transparent 34%), radial-gradient(circle at 88% 82%, rgba(255,178,74,.14) 0, transparent 38%), #FFFCF7",
        "slide_bg_size": "auto",
        "body_bg": "#FFF2E8",
        "card": "rgba(255, 255, 255, .78)",
        "radius": "24px",
        "t1": "#8A6F3D",
        "t2": "#A8664F",
        "t3": "#F05F4B",
        "t4": "#6D856D",
        "t5": "#7A5F73",
    },
    "health": {
        "theme": "health",
        "c60": "#F7FAFC",
        "c30": "#EDF5F8",
        "accent": "#2D7DD2",
        "accent2": "#2CC4A7",
        "ink": "#1D2B34",
        "muted": "#647680",
        "line": "rgba(45,125,210,.16)",
        "grid_line": "transparent",
        "slide_bg": "radial-gradient(ellipse at 82% 18%, rgba(45,125,210,.12) 0, transparent 42%), linear-gradient(135deg, transparent 0 68%, rgba(44,196,167,.10) 68% 100%), #F7FAFC",
        "slide_bg_size": "auto",
        "body_bg": "#EDF5F8",
        "card": "rgba(255, 255, 255, .82)",
        "radius": "14px",
        "t1": "#2D7DD2",
        "t2": "#2CC4A7",
        "t3": "#7CA7D9",
        "t4": "#91D8C9",
        "t5": "#647680",
    },
}
PALETTES["forest"] = {
    # 드리블 2026 인기 트렌드 흡수(팔레트 SoT 참조) — 딥그린×라임·웜아이보리. agri/프로덕티비티/지속가능 주제.
    "theme": "forest",
    "c60": "#F4F3EE",
    "c30": "#EBE9E0",
    "accent": "#1E4033",
    "accent2": "#A6C34C",
    "ink": "#17251F",
    "muted": "#5F6B62",
    "line": "rgba(30,64,51,.16)",
    "grid_line": "transparent",
    "slide_bg": "#F4F3EE",
    "slide_bg_size": "auto",
    "body_bg": "#EBE9E0",
    "card": "rgba(255, 255, 255, .72)",
    "radius": "12px",
    "t1": "#1E4033",
    "t2": "#A6C34C",
    "t3": "#5F6B62",
    "t4": "#9DB8A5",
    "t5": "#17251F",
}
PALETTES["violet"] = {
    # 드리블 2026 인기 트렌드 흡수 — 바이올렛×라벤더 틴트램프. AI/SaaS 주제.
    "theme": "violet",
    "c60": "#F8F7FC",
    "c30": "#EFEDF8",
    "accent": "#7C4DE8",
    "accent2": "#B49BF2",
    "ink": "#221C33",
    "muted": "#6B647E",
    "line": "rgba(124,77,232,.16)",
    "grid_line": "transparent",
    "slide_bg": "#F8F7FC",
    "slide_bg_size": "auto",
    "body_bg": "#EFEDF8",
    "card": "rgba(255, 255, 255, .8)",
    "radius": "14px",
    "t1": "#7C4DE8",
    "t2": "#B49BF2",
    "t3": "#6B647E",
    "t4": "#CFC3F5",
    "t5": "#221C33",
}
PALETTES["pantone"] = dict(PALETTES["editorial"])
PALETTES["breeze"] = dict(PALETTES["marketing"], theme="marketing")
PALETTES["cobalt"] = dict(PALETTES["tech"], theme="tech")
PALETTES["editorial_serif"] = {
    # 파일럿 1 — 별도 디자인 시스템(팔레트 아님). 세리프 헤드라인 + 카드 억제(line/card
    # transparent로 박스 대신 룰선만 남김) + 절제된 단색조. deck-visual-language-ceiling
    # 메모 대응 — 파라미터 변주가 아니라 타이포/카드철학 자체가 다른 엔진 변형.
    "theme": "editorial_serif",
    "c60": "#FAF7F2",
    "c30": "#F1EBE1",
    "accent": "#6B2E2E",
    "accent2": "#8C7A5B",
    "ink": "#211D18",
    "muted": "#6E6559",
    "line": "transparent",
    "grid_line": "transparent",
    "slide_bg": "#FAF7F2",
    "slide_bg_size": "auto",
    "body_bg": "#F1EBE1",
    "card": "transparent",
    "radius": "0px",
    "t1": "#6B2E2E",
    "t2": "#8C7A5B",
    "t3": "#4B5A54",
    "t4": "#A9967A",
    "t5": "#211D18",
    "font_head": '"Nanum Myeongjo", "Noto Serif KR", Georgia, "Times New Roman", serif',
    "font_body": '"Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif',
}
PALETTES["data_mono"] = {
    # 파일럿 2(후추님 7/3 방향 승인) — 3번째 디자인 시스템: 모노스페이스 데이터형.
    # 기술문서/계기판 문법 — 방안지 그리드 지면·모노 수치 조판·스펙시트 헤더·각진 프레임.
    # 산세리프 카드형(기존 8테마)·세리프 매거진형(editorial_serif)과 타이포/지면 철학 자체가 다름.
    "theme": "data_mono",
    "c60": "#F2F4F1",
    "c30": "#E9ECE8",
    "accent": "#0E6B4F",
    "accent2": "#B4831E",
    "ink": "#161B18",
    "muted": "#5E6862",
    "line": "rgba(22,27,24,.22)",
    "grid_line": "rgba(22,27,24,.05)",
    # 방안지 그리드 = 시스템 시그니처(지면 자체가 데이터 용지). 마지막 색이 바탕.
    "slide_bg": "linear-gradient(rgba(22,27,24,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(22,27,24,.045) 1px, transparent 1px), #F2F4F1",
    "slide_bg_size": "32px 32px",
    "body_bg": "#E9ECE8",
    "card": "transparent",
    "radius": "0px",
    "t1": "#0E6B4F",
    "t2": "#B4831E",
    "t3": "#41544B",
    "t4": "#7A8B82",
    "t5": "#161B18",
    # 헤드라인: 라틴/숫자는 모노, 한글은 Pretendard 폴백 — 숫자·영문 라벨에서 모노 성격이 드러남.
    "font_head": 'ui-monospace, "SF Mono", "SFMono-Regular", Menlo, Consolas, "Pretendard", "Apple SD Gothic Neo", monospace',
    "font_body": '"Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif',
}
PALETTES["dark_premium"] = {
    # 파일럿 3(레퍼런스 흡수 1라운드·_grammar/dark_premium.md 8/8 실측) — 전면 다크 시스템.
    # 공통 문법만: 명도 3단(바탕→카드→액센트)·단일 지배 액센트(웜 골드)·본문은 순백 아닌 눌린 회색·
    # depth 카드 부양·차트 강조1+무채. ink=밝은 글자색(다크 반전) — 본문 회색은 CSS에서 muted로 강등.
    "theme": "dark_premium",
    "c60": "#0E0F11",
    "c30": "#17181B",
    "accent": "#C6A15B",
    "accent2": "#8C8577",
    "ink": "#F2EFE7",
    "muted": "#A9A49A",
    "line": "rgba(242,239,231,.14)",
    "grid_line": "transparent",
    "slide_bg": "radial-gradient(circle at 88% 12%, rgba(198,161,91,.07) 0, transparent 42%), #0E0F11",
    "slide_bg_size": "auto",
    "body_bg": "#0A0B0C",
    "card": "rgba(255,255,255,.055)",
    "radius": "14px",
    "t1": "#C6A15B",
    "t2": "#8C8577",
    "t3": "#5E5A52",
    "t4": "#3A3833",
    "t5": "#F2EFE7",
}
PALETTES["pop_dark"] = {
    # 파일럿 5(후추님 7/4 스샷 스타일 — creative_bold 다크 방언, 흡수 라운드에서 내가 걸렀던 것 정정).
    # 블랙 지면 + 오렌지 풀블리드 북엔드 + 다색 팝(오렌지·블루·핑크·퍼플 t램프 순환) + 필/블롭 도형.
    # 단일 액센트 원칙의 의도적 예외 — 다이어그램 어휘(hub/arrow/timeline/table)와 짝인 시스템.
    "theme": "pop_dark",
    "c60": "#131118",
    "c30": "#1C1922",
    "accent": "#FF5A1F",
    "accent2": "#2B3BE8",
    "ink": "#F5F2EC",
    "muted": "#A7A2AE",
    "line": "rgba(245,242,236,.16)",
    "grid_line": "transparent",
    "slide_bg": "#131118",
    "slide_bg_size": "auto",
    "body_bg": "#0D0B11",
    "card": "rgba(255,255,255,.06)",
    "radius": "22px",
    "t1": "#FF5A1F",
    "t2": "#2B3BE8",
    "t3": "#E8347C",
    "t4": "#8A2BE8",
    "t5": "#F5F2EC",
}
PALETTES["minimal_typo"] = {
    # 파일럿 4(레퍼런스 흡수 1라운드·_grammar/minimal_typo.md 8/8 실측) — 미니멀 타이포 시스템.
    # B형(웜 에디토리얼 방언)만 채택: 오프화이트 웜 바탕·단일 뮤트 액센트(플럼)·헤드:본문 극단
    # 크기비(본문 캡션급)·무장식(여백·룰이 장식)·빅넘버 스탯. A형(모노크롬 사무형)은 혼합 금지.
    "theme": "minimal_typo",
    "c60": "#FAF7F1",
    "c30": "#F3EFE7",
    "accent": "#7A4A5F",
    "accent2": "#A67B4F",
    "ink": "#26231F",
    "muted": "#7A756C",
    "line": "rgba(38,35,31,.14)",
    "grid_line": "transparent",
    "slide_bg": "#FAF7F1",
    "slide_bg_size": "auto",
    "body_bg": "#F3EFE7",
    "card": "transparent",
    "radius": "0px",
    "t1": "#7A4A5F",
    "t2": "#A67B4F",
    "t3": "#5C6258",
    "t4": "#8E8678",
    "t5": "#26231F",
}


def render_deck(
    deck_spec: dict[str, Any],
    content_registry: dict[str, Any],
    title: str = "TickDeck",
    theme: str | None = None,
) -> str:
    registry = normalize_registry(content_registry)
    pages = deck_spec.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("deck_spec.pages must be a non-empty list")

    palette = _resolve_palette(deck_spec, theme)
    meta = deck_spec.get("meta") if isinstance(deck_spec.get("meta"), dict) else {}
    page_chrome = str(meta.get("page_chrome", "")).strip()
    deck_short_title = _deck_short_title(deck_spec, title)
    archetype_class = _deck_archetype_class(deck_spec)
    body_classes = [f'deck-theme-{_class_name(palette["theme"])}']
    if archetype_class:
        body_classes.append(archetype_class)
    body_ordinals = _body_page_ordinals(pages)
    deck_cited_source_ids = _deck_cited_source_ids(pages, registry)
    # 표지 밴드 수 = 실제 파트 수. 간지 수로 세되, 페이지에 명시된 part_count가 있으면 그게 정답
    # (간지 없는 1부가 있는 덱에서 표지 2밴드 vs 간지 티커 3의 불일치 방지·7/2).
    divider_n = sum(1 for page in pages if isinstance(page, dict) and str(page.get("layout")) == "divider")
    explicit_counts = [int(page.get("part_count")) for page in pages if isinstance(page, dict) and str(page.get("part_count", "")).isdigit()]
    part_count = max([divider_n] + explicit_counts) if (divider_n or explicit_counts) else 0
    rendered_pages = []
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        body_ordinal = body_ordinals.get(index)
        rendered_pages.append(
            _render_page(
                page,
                index + 1,
                len(pages),
                registry,
                palette,
                deck_cited_source_ids,
                part_count,
                page_chrome,
                deck_short_title,
                body_ordinal,
                len(body_ordinals),
            )
        )
    if len(rendered_pages) != len(pages):
        raise ValueError("every deck_spec page must be an object")

    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="ko">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            f"<title>{_escape(title)}</title>",
            f"<style>{_css(palette)}</style>",
            "</head>",
            f'<body class="{" ".join(body_classes)}">',
            *rendered_pages,
            "</body>",
            "</html>",
        ]
    )


def normalize_registry(content_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "content_registry" in content_registry and isinstance(content_registry["content_registry"], dict):
        content_registry = content_registry["content_registry"]

    sources = _registry_map(content_registry, ("sources", "source_registry"))
    metrics = _registry_map(content_registry, ("metrics", "metric_registry"))
    if not sources:
        raise ValueError("content registry must include sources/source_registry")
    if not metrics:
        raise ValueError("content registry must include metrics/metric_registry")
    return {"sources": sources, "metrics": metrics}


def _resolve_palette(deck_spec: dict[str, Any], explicit_theme: str | None) -> dict[str, str]:
    theme = explicit_theme if explicit_theme else str(deck_spec.get("theme") or "editorial")
    return PALETTES.get(theme, PALETTES["editorial"])


# 표지·간지·클로징·source_appendix·outro는 "본문"이 아니다 — running_head 페이지분수는
# 본문 페이지만 센다(스펙: 상단 크롬 옵션 running_head, PG-running_head).
_NON_BODY_LAYOUTS = {"cover", "divider", "closing", "outro", "source_appendix"}


def _deck_short_title(deck_spec: dict[str, Any], fallback_title: str) -> str:
    # deck_spec.meta.short_title이 러닝헤드 중앙 브랜드/덱 short title. 없으면 문서 title로 폴백.
    meta = deck_spec.get("meta") if isinstance(deck_spec.get("meta"), dict) else {}
    short_title = str(meta.get("short_title", "")).strip()
    return short_title or str(fallback_title).strip()


def _deck_archetype_class(deck_spec: dict[str, Any]) -> str:
    archetype = str(deck_spec.get("archetype") or (deck_spec.get("meta") or {}).get("archetype") or "").strip()
    return f"arch-{_class_name(archetype)}" if archetype else ""


def _body_page_ordinals(pages: list[Any]) -> dict[int, int]:
    # pages 인덱스 → 본문 내 순번(1-base). 표지/간지/클로징 등은 매핑에서 빠진다.
    ordinals: dict[int, int] = {}
    ordinal = 0
    for index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        if str(page.get("layout", "statement")) in _NON_BODY_LAYOUTS:
            continue
        ordinal += 1
        ordinals[index] = ordinal
    return ordinals


def _running_head_html(eyebrow_text: str, deck_short_title: str, body_page_number: int, body_page_count: int) -> str:
    # 상단 3점 프레임: 좌=페이지 kicker(eyebrow 재사용) / 중=덱 short title / 우=페이지분수(렌더러 계산).
    return f"""
<div class="running-head" aria-hidden="true">
  <span class="running-head-kicker">{_escape(eyebrow_text)}</span>
  <span class="running-head-brand">{_escape(deck_short_title)}</span>
  <span class="running-head-frac">{body_page_number:02d} / {body_page_count:02d}</span>
</div>""".strip()


def _side_wordmark_html(page: dict[str, Any], deck_short_title: str) -> str:
    # 텍스트는 designer 자유 입력이 아니라 페이지 컨텍스트(section_label)나 덱 short title에서만 취득.
    text = str(page.get("section_label", "")).strip() or deck_short_title
    if not text:
        return ""
    return f'<div class="side-wordmark" aria-hidden="true">{_escape(text)}</div>'


def _render_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    registry: dict[str, dict[str, Any]],
    palette: dict[str, str],
    deck_cited_source_ids: list[str],
    part_count: int = 0,
    page_chrome: str = "",
    deck_short_title: str = "",
    body_page_number: int | None = None,
    body_page_count: int = 0,
) -> str:
    page_id = str(page.get("page_id", f"p{page_number:02d}"))
    layout = str(page.get("layout", "statement"))
    short_title = str(page.get("short_title", "")).strip()
    if not short_title:
        raise ValueError(f"{page_id}: short_title is required")

    content = page.get("content", [])
    if not isinstance(content, list):
        raise ValueError(f"{page_id}: content must be a list")

    if layout == "cover":
        return _render_cover_page(page, page_number, page_count, content, palette, part_count)
    if layout == "outro":
        return _render_outro_page(page, page_number, page_count, content, palette)

    if layout == "source_appendix":
        return _render_source_appendix_page(page, page_number, page_count, content, registry, palette, deck_cited_source_ids)

    body_parts: list[str] = []
    rendered_pairs: list[tuple[Any, str]] = []  # (block, html) — matrix처럼 블록 의미로 배치하는 레이아웃용
    cited_source_ids: list[str] = []
    footnotes: list[dict[str, Any]] = []
    # eyebrow는 designer가 준 명시 블록만 — role/layout 내부명 폴백은 C2(검증 메타데이터
    # 노출 금지) 계열이라 크롬(7/4)에 이어 본체 헤더에서도 제거.
    eyebrow_text = _first_block_text(content, {"eyebrow"})
    title_text = _page_title_text(page, content, layout)
    for block in content:
        bt = _block_type(block)
        if bt == "eyebrow":
            continue
        if bt == "footnote":  # 용어 풀이 = 페이지 하단 각주(writing-standard C-10b·일반 청중 배려)
            footnotes.append(block)
            continue
        block_html, block_sources = _render_block(block, page_id, registry, palette)
        if block_html:
            body_parts.append(block_html)
            rendered_pairs.append((block, block_html))
        cited_source_ids.extend(block_sources)

    for metric_id in _iter_metric_ids(content):
        metric = _require_metric(metric_id, page_id, registry)
        cited_source_ids.extend(_as_list(metric.get("source_ids")))

    body_html = _render_layout_body(layout, body_parts, page, content, page_number, rendered_pairs)
    motif_html = _slide_motif_html(layout, page_number, palette)
    running_head_enabled = (
        page_chrome == "running_head"
        and body_page_number is not None
        and body_page_count > 0
    )
    running_head_html = (
        _running_head_html(eyebrow_text, deck_short_title, body_page_number or 0, body_page_count)
        if running_head_enabled
        else ""
    )
    side_wordmark_html = _side_wordmark_html(page, deck_short_title) if page.get("decor") == "side_wordmark" else ""
    # 카드가 우하단에 자기 출처를 표시한 페이지(다출처 stat_grid)는 하단 source-row가 중복 → 생략(후추님 6/30).
    source_row = "" if _page_has_per_card_sources(content, page_id, registry) else f'<div class="source-row">{_render_sources(cited_source_ids, registry)}</div>'
    footnote_row = _render_footnotes(footnotes)
    # 간지(divider)는 표지·outro처럼 푸터(출처행·카피라이트·페이지번호)를 렌더하지 않는다(후추님 6/30).
    if layout == "divider":
        foot_html = ""
    else:
        page_number_html = (
            "" if running_head_enabled else f'<span class="page-number" data-page-number>{page_number:02d} / {page_count:02d}</span>'
        )
        running_foot_html = ""
        if running_head_enabled:
            next_html = '<span class="running-next">NEXT</span>' if body_page_number != body_page_count else ""
            running_foot_html = f'<div class="running-foot" aria-hidden="true"><span>PREV</span>{next_html}</div>'
        foot_html = f"""
  {footnote_row}
  {source_row}
  <footer class="slide-foot">
    <span class="foot-side"></span>
    {_copyright_html()}
    {page_number_html}
  </footer>{running_foot_html}"""
    section_classes = [
        "slide",
        f'theme-{_class_name(palette["theme"])}',
        f"layout-{_class_name(layout)}",
    ]
    if page.get("divider_variant") == "accent":
        section_classes.append("divider-accent")
    if page.get("hero_title"):
        section_classes.append("divider-hero")
    if running_head_enabled:
        section_classes.append("chrome-running-head")
    if page.get("decor") == "side_wordmark":
        section_classes.append("decor-side-wordmark")
        if str(page.get("wordmark_side", page.get("side_wordmark_side", ""))).strip().lower() == "right":
            section_classes.append("decor-side-wordmark-right")
    return f"""
<section class="{' '.join(section_classes)}" data-page-id="{_escape(page_id)}">
  {motif_html}
  {side_wordmark_html}
  {running_head_html}
  <header class="slide-head">
    {f'<div class="eyebrow{" eyebrow-chip" if page.get("eyebrow_chip") else ""}">{_escape(eyebrow_text)}</div>' if eyebrow_text else ""}
    <h1>{_rich(title_text)}</h1>
  </header>
  {body_html}{foot_html}
</section>""".strip()


def _render_cover_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    content: list[Any],
    palette: dict[str, str],
    part_count: int = 0,
) -> str:
    page_id = str(page.get("page_id", f"p{page_number:02d}"))
    title = _clean_title_text(_first_block_text(content, {"headline", "title"}) or _non_cover_text(str(page.get("short_title", ""))))
    subtitle = _first_block_text(content, {"summary", "body", "text", "note"})
    eyebrow = _non_cover_text(_first_block_text(content, {"eyebrow"}))
    decor_html = _cover_decor_html(palette, part_count)
    eyebrow_html = f'<p class="cover-eyebrow">{_escape(eyebrow)}</p>' if eyebrow else ""
    subtitle_html = f'<p class="cover-subtitle">{_escape(subtitle)}</p>' if subtitle else ""
    credit_html = _cover_credit_html()
    # 표지 변형(덱 간 차별화·후추님 7/2 "레이아웃이 너무 유사"): "dark" = 잉크 파생 다크 히어로
    # (간지와 같은 파생 문법·다크 북엔드). 미지정 = 기존 라이트. 색 축(장식) — 뼈대와 독립.
    variant = " cover-dark" if str(page.get("cover_variant", "")).lower() == "dark" else ""
    # 표지 뼈대 축(구조·엔바토 흡수 3라운드 7/3 — XBUQSG2·7FE9Y7G 관찰): "center"(기본, 수직 중앙
    # 락업) | "corner"(하단 앵커 — 텍스트가 화면 하단 1/3에, 더 다큐먼트/브랜드북 느낌).
    # 색 축(cover_variant)과 직교 — 조합 자유(예: corner+dark). 후추님 7/3 "뼈대를 세트로" 요청.
    skeleton = " cover-corner" if str(page.get("cover_layout", "")).lower() == "corner" else ""
    # 광택 대각 오버레이(엔바토 흡수 3라운드 7/3 — 브랜드 가이드 표지 다수 관찰): 순수 CSS, 이미지 없음.
    sheen_html = '<div class="cover-sheen" aria-hidden="true"></div>' if page.get("cover_sheen") else ""
    # 세로 책등 라벨: 표지 오른쪽 여백에 회전된 짧은 단어 — 브랜드북 스파인 문법(AWQHGT7·7HAH9XQ 관찰).
    spine = str(page.get("spine_label", "")).strip()
    spine_html = f'<p class="cover-spine">{_escape(spine)}</p>' if spine else ""
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-cover cover-slide{variant}{skeleton}" data-page-id="{_escape(page_id)}">
  {sheen_html}
  {credit_html}
  {spine_html}
  <main class="cover-body">
    <div class="cover-lockup">
      {eyebrow_html}
      <h1>{"<br>".join(_rich(part) for part in title.split(chr(10)))}</h1>
      {subtitle_html}
    </div>
    {decor_html}
  </main>
</section>""".strip()


def _render_outro_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    content: list[Any],
    palette: dict[str, str],
) -> str:
    # 발표 마무리 장(재사용 layout). 3존: eyebrow=최상단 / 감사 인사=가운데 / 연락처=하단.
    # 결론(명제) 반복은 넣지 않는다 — 직전 결론 슬라이드와 중복(후추님 6/30).
    page_id = str(page.get("page_id", f"p{page_number:02d}"))
    title = _first_block_text(content, {"headline", "title"}) or "감사합니다."
    # 맺음 인사는 마침표로 점을 찍는다(후추님 7/3) — 스펙이 점 없이 줘도 정규화.
    if title.rstrip() == "감사합니다":
        title = "감사합니다."
    eyebrow = _non_cover_text(_first_block_text(content, {"eyebrow"}))
    eyebrow_html = f'<p class="cover-eyebrow">{_escape(eyebrow)}</p>' if eyebrow else ""
    contact_html = _presenter_contact_html()
    # 다크 북엔드 미러링 — outro도 cover_variant:"dark"를 읽는다(7/3 tech_v2 designer 발견 구멍).
    variant = " cover-dark" if str(page.get("cover_variant", "")).lower() == "dark" else ""
    # eyebrow를 감사 인사 바로 위에 붙여 한 묶음(상단~중상단), 연락처는 하단(후추님 6/30).
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-cover cover-slide layout-outro outro-slide{variant}" data-page-id="{_escape(page_id)}">
  <div class="outro-main">{eyebrow_html}<h1>{_escape(title)}</h1></div>
  <div class="outro-contact-zone">{contact_html}</div>
</section>""".strip()


def _render_source_appendix_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    content: list[Any],
    registry: dict[str, dict[str, Any]],
    palette: dict[str, str],
    deck_cited_source_ids: list[str],
) -> str:
    # 전체 출처 모음 appendix(writing-standard: 정의=페이지하단 / 출처=끝 정리). outro 바로 앞.
    # 각 행을 data-src-id로 감싸 기관·리포트명의 연도 숫자가 C6 authorized context에 들게 한다.
    page_id = str(page.get("page_id", f"p{page_number:02d}"))
    eyebrow_text = _first_block_text(content, {"eyebrow"}) or "출처"
    title_text = _page_title_text(page, content, "source_appendix") or "출처"
    src_ids = _as_list(page.get("allowed_source_ids")) or deck_cited_source_ids
    # 출처가 많으면(>10행) 행 간격·폰트를 압축 — 14출처 덱에서 appendix가 넘치던 근본 결함(7/2).
    compact = " appendix-compact" if len(src_ids) > 10 else ""
    rows = []
    for src_id in src_ids:
        source = _require_source(src_id, page_id, registry)
        publisher = str(source.get("publisher") or src_id)
        sttl = str(source.get("title") or "")
        url = str(source.get("url") or "").strip()
        title_html = (
            f'<a class="appendix-link" href="{_escape(url)}">{_escape(sttl)} ↗</a>'
            if url
            else _escape(sttl)
        )
        # 넘버링·구분선 없이 "기관 — 리포트명" 한 줄 플랫 리스트(후추님 7/2).
        rows.append(
            f"""
        <article class="appendix-row" data-src-id="{_escape(src_id)}">
          <span class="appendix-pub" data-src-id="{_escape(src_id)}">{_escape(publisher)}</span>
          <span class="appendix-title" data-src-id="{_escape(src_id)}">{title_html}</span>
        </article>"""
        )
    motif_html = _slide_motif_html("source_appendix", page_number, palette)
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-source_appendix" data-page-id="{_escape(page_id)}">
  {motif_html}
  <header class="slide-head">
    <div class="eyebrow">{_escape(eyebrow_text)}</div>
    <h1>{_escape(title_text)}</h1>
    <div class="verified-badge">모든 수치 출처 연결 검증 · 출처 {len(src_ids)}곳</div>
  </header>
  <main class="body layout-body appendix-body{compact}"><section class="appendix-list">{"".join(rows)}</section></main>
  <footer class="slide-foot">
    <span class="foot-side"></span>
    {_copyright_html()}
    <span class="page-number" data-page-number>{page_number:02d} / {page_count:02d}</span>
  </footer>
</section>""".strip()


def _presenter() -> dict[str, str]:
    # presenter.json은 스크립트 위치 기준 절대경로로 읽는다(cwd 무관 — 어디서 render 돌려도 읽힘).
    path = Path(__file__).resolve().parents[1] / "presenter.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: str(v).strip() for k, v in data.items()}


def _presenter_contact_html() -> str:
    # 발표자 연락 블록(연락처는 수치·출처 아님 → C6 무관). 파일 없거나 비면 생략.
    # 3줄 세로: 회사명(대문자) / 이름 / 이메일 (후추님 6/30 — outro 하단).
    data = _presenter()
    name, company, email = data.get("name", ""), data.get("company", ""), data.get("email", "")
    parts = []
    if company:
        parts.append(f'<span class="presenter-company">{_escape(company.upper())}</span>')
    if name:
        parts.append(f'<span class="presenter-name">{_escape(name)}</span>')
    if email:
        parts.append(f'<span class="presenter-email">{_escape(email)}</span>')
    if not parts:
        return ""
    return f'<div class="presenter-contact">{"".join(parts)}</div>'


def _cover_credit_html() -> str:
    # 표지 우하단 도메인(presenter.json site). 이름·회사명 대신 도메인만·앞 글자 대문자(후추님 #2).
    site = _presenter().get("site", "").strip()
    if not site:
        return ""
    label = site[:1].upper() + site[1:]
    return f'<p class="cover-credit">{_escape(label)}</p>'


def _copyright_html() -> str:
    # 전 페이지 푸터 중앙 카피라이트(presenter.json company·연도 2026). 페이지번호와 같은 크기·행.
    company = _presenter().get("company", "")
    if not company:
        return '<span class="copyright"></span>'
    return f'<span class="copyright">© 2026 {_escape(company)} · All rights reserved</span>'


def _render_footnotes(footnotes: list[dict[str, Any]]) -> str:
    # 용어 풀이 각주 = 슬라이드 하단 작게(writing-standard C-10b). 일반 청중이 어려워할 용어·다의어.
    # 블록: {"type":"footnote","term":"에이전트 AI","def":"스스로 일을 처리하는 AI"} 또는 {"text":"..."}.
    items = []
    for f in footnotes:
        term = str(f.get("term", "")).strip()
        defn = str(f.get("def", f.get("text", ""))).strip()
        if term and defn:
            items.append(f'<span class="footnote-item"><b>{_escape(term)}</b> {_escape(defn)}</span>')
        elif defn:
            items.append(f'<span class="footnote-item">{_escape(defn)}</span>')
    if not items:
        return ""
    return f'<div class="footnote-row">{"".join(items)}</div>'


def _render_layout_body(
    layout: str,
    body_parts: list[str],
    page: dict[str, Any],
    content: list[Any],
    page_number: int,
    rendered_pairs: list[tuple[Any, str]] | None = None,
) -> str:
    if layout == "split":
        return _render_split(body_parts, page)
    if layout == "stack":
        return _render_stack(body_parts)
    if layout == "hero_metric":
        return _render_hero_metric(body_parts)
    if layout == "stepper":
        return _render_stepper(body_parts)
    if layout == "node":
        return _render_node(body_parts)
    if layout == "matrix":
        return _render_matrix(content, rendered_pairs)
    # ── 시그니처 페이지(2026-07-04 페이지 아키텍처 파일럿): 시스템별 전용 골격.
    # 테마(옷)가 아니라 페이지 해부학(몸)을 분기 — "결국 그 계열" 천장의 다음 층 해법.
    if layout == "poster":
        return _render_poster(content)
    if layout == "hero_bleed":
        return _render_hero_bleed(rendered_pairs, content)
    if layout == "magazine_spread":
        return _render_magazine_spread(rendered_pairs)
    if layout == "dashboard":
        return _render_dashboard(rendered_pairs)
    if layout == "mosaic_tiles":
        return _render_mosaic_tiles(rendered_pairs)
    if layout == "split_status":
        return _render_split_status(rendered_pairs)
    if layout == "scenario_cards":
        return _render_scenario_cards(rendered_pairs)
    if layout == "pricing_cards":
        return _render_pricing_cards(rendered_pairs, page)
    if layout == "index":
        return _render_index(body_parts, content)
    if layout == "divider":
        return _render_divider(page, content, page_number)
    if layout == "closing":
        return _render_closing(content)
    body_class = "body body-grid" if layout in {"stat_grid", "metric_grid", "cards"} else "body"
    # 저밀도 페이지(블록 ≤3)는 세로 중앙 정렬 — 하단 40%가 '남은 공간'으로 읽히던 문제(7/2).
    # ponytail: 블록 수 휴리스틱. 4+ 블록 페이지가 여전히 비면 렌더 높이 실측으로 교체.
    if layout not in {"stat_grid", "metric_grid", "cards"} and len(body_parts) <= 3:
        body_class += " body-center"
    return f'<main class="{body_class}">{"".join(body_parts)}</main>'


def _extract_note_row(body_parts: list[str]) -> tuple[str, list[str]]:
    # note(단서/캐비앗)는 좌우 칸·가로 배열에 끼우지 않고 하단 전폭 한 줄로 뺀다 — split/stack 공통.
    note_row = ""
    rest: list[str] = []
    for part in body_parts:
        stripped = part.lstrip()
        if not note_row and stripped.startswith('<aside class="callout') and "note-row" in stripped[:60]:
            note_row = part
        else:
            rest.append(part)
    return note_row, rest


def _render_split(body_parts: list[str], page: dict[str, Any] | None = None) -> str:
    # 거버닝 부제(block-title)는 왼쪽 칸에 가두지 않고 전폭으로 끌어올린다 —
    # 제목 아래 부제가 오는 일반 양식과 통일·좌우 밸런스 회복(후추님 7/2 p05·p07).
    lead = ""
    if body_parts and body_parts[0].lstrip().startswith('<h2 class="block-title"'):
        lead, body_parts = body_parts[0], body_parts[1:]
    # note(단, ~ 캐비앗)는 좌우 칸에 섞지 않고 하단 전폭 한 줄로 뺀다(7/3 후추님 p07·p10 지적
    # — 오른쪽 칸에 박스로 갇혀 있던 게 어색했다). split/stack 공통 규칙.
    note_row, body_parts = _extract_note_row(body_parts)
    # 홀수 블록이면 나머지는 우측(보조 칸)으로 — 좌측은 주 비주얼 하나가 원칙(7/2 p06 좌측 과적 fix).
    midpoint = max(1, len(body_parts) // 2)
    left = "".join(body_parts[:midpoint])
    right = "".join(body_parts[midpoint:])
    note_html = f'<div class="split-note-row">{note_row}</div>' if note_row else ""
    # 우측 칸이 비면 세로 구분선 있는 2단이 어색하다(후추님 7/4 p05 "우측 내용 없는데 세로선").
    # 단일 비주얼이면 구분선 없는 1단으로 — 가짜 2단 방지.
    if not right.strip():
        return f"""
<main class="body layout-body split-outer">
  {lead}
  <div class="split-body split-single">
    <section class="split-pane split-solo">{left}</section>
  </div>
  {note_html}
</main>""".strip()
    # 비대칭 레버(7/3 드리블 흡수 2라운드): split_ratio "wide-left"|"wide-right" — 주 비주얼 쪽을 넓게.
    ratio_class = {"wide-left": " split-wide-left", "wide-right": " split-wide-right"}.get(
        str((page or {}).get("split_ratio", "")), ""
    )
    return f"""
<main class="body layout-body split-outer">
  {lead}
  <div class="split-body{ratio_class}">
    <section class="split-pane split-primary">{left}</section>
    <section class="split-pane split-secondary">{right}</section>
  </div>
  {note_html}
</main>""".strip()


def _render_hero_metric(body_parts: list[str]) -> str:
    # 오버사이즈 빅넘버 전면장(드리블 흡수 2라운드 — 숫자가 곧 비주얼인 장).
    # 첫 블록(viz 또는 metric)만 초대형 — 나머지(보조 카드·note·citation)는 hero-row에
    # 정상 크기로 둔다. (7/3 실측 버그: 전부 hero-stage에 넣어 보조 metric까지 210px로
    # 부풀어 FIT_OVERFLOW 발생 — p08 viz+보조metric 조합에서 발견.)
    lead = ""
    if body_parts and body_parts[0].lstrip().startswith('<h2 class="block-title"'):
        lead, body_parts = body_parts[0], body_parts[1:]
    if not body_parts:
        return f'<main class="body layout-body hero-body">{lead}</main>'
    top, rest = body_parts[0], body_parts[1:]
    row = f'<div class="hero-row">{"".join(rest)}</div>' if rest else ""
    return f'<main class="body layout-body hero-body">{lead}<div class="hero-stage">{top}</div>{row}</main>'


def _render_stack(body_parts: list[str]) -> str:
    # 상하 컴포지션(후추님 7/3 p04·p05): 주 비주얼 전폭 상단 + 나머지 블록 하단 가로 배열.
    # split(좌우)와 대구를 이루는 문법 — 좌우 밸런스가 안 맞거나 차트가 눌릴 때 쓴다.
    lead = ""
    if body_parts and body_parts[0].lstrip().startswith('<h2 class="block-title"'):
        lead, body_parts = body_parts[0], body_parts[1:]
    if not body_parts:
        return f'<main class="body layout-body stack-outer">{lead}</main>'
    # note(캐비앗)는 하단 전폭 한 줄 — _extract_note_row 주석의 "split/stack 공통"이 stack에선
    # 배선이 빠져 note가 행 안에 끼어 세로를 밀던 결함(7/5 레버1 e2e p05 실측).
    note_row, body_parts = _extract_note_row(body_parts)
    top, rest = body_parts[0], body_parts[1:]
    # 하단 가로 배열: 지표 카드와 note 박스가 나란할 때 키를 맞춘다(후추님 7/4 p07 "우측 박스 높이=좌측").
    # stretch는 이미 걸려 있으나 metric-grid 안의 카드가 안 늘어나 빈 공간이 생겼다 → 카드 자체를 100%로.
    row = f'<div class="stack-row">{"".join(rest)}</div>' if rest else ""
    return f'<main class="body layout-body stack-outer">{lead}{top}{row}{note_row}</main>'


def _render_stepper(body_parts: list[str]) -> str:
    # split과 동일 양식 통일(후추님 7/2): 거버닝 부제(block-title)는 카드가 아니라 전폭 상단.
    lead = ""
    if body_parts and body_parts[0].lstrip().startswith('<h2 class="block-title"'):
        lead, body_parts = body_parts[0], body_parts[1:]
    items = "".join(
        f'<article class="stepper-item"><div class="stepper-content">{part}</div></article>'
        for part in body_parts
    )
    return f'<main class="body layout-body stepper-body">{lead}<div class="stepper-track">{items}</div></main>'


def _render_node(body_parts: list[str]) -> str:
    if not body_parts:
        return '<main class="body layout-body node-body"></main>'
    center = body_parts[0]
    branches = "".join(f'<article class="node-branch">{part}</article>' for part in body_parts[1:])
    return f"""
<main class="body layout-body node-body">
  <section class="node-map">
    <article class="node-core">{center}</article>
    <div class="node-branches">{branches}</div>
  </section>
</main>""".strip()


def _render_matrix(content: list[Any], rendered_pairs: list[tuple[Any, str]] | None = None) -> str:
    # headline/title은 격자 위 소제목으로(후추님 6/30 명시 — "네 전선이…는 소제목"). 셀=body/text 블록.
    # "라벨 — 설명" 패턴이면 굵은 헤더+본문으로 쪼개 '요약 카드 나열'이 아니라 매트릭스로 읽히게.
    # metric류 블록은 직전 셀의 스탯 행으로 붙는다 — 이전엔 조용히 떨어뜨려 designer가 넣은 수치가
    # 실물에 없던 무증상 결함(7/3 creator run p10 실측 발견). 셀 없이 오면 자체 셀로.
    metric_html: dict[int, str] = {}
    if rendered_pairs:
        for block, html_part in rendered_pairs:
            if _block_type(block) in {"metric", "metrics", "metric_grid", "stat_grid"}:
                metric_html[id(block)] = html_part
    subhead = ""
    cells: list[dict[str, str]] = []
    for block in content:
        bt = _block_type(block)
        if bt in {"headline", "title"} and not subhead:
            subhead = f'<div class="matrix-subhead"><h2 class="block-title">{_rich(str(block.get("text", "")))}</h2></div>'
            continue
        if bt in {"metric", "metrics", "metric_grid", "stat_grid"} and id(block) in metric_html:
            if cells:
                cells[-1]["stats"] += metric_html[id(block)]
            else:
                cells.append({"inner": "", "stats": metric_html[id(block)]})
            continue
        if bt not in {"body", "text", "callout", "note"}:
            continue
        text = str(block.get("text", "")).strip()
        if not text:
            continue
        label, sep, desc = text.partition(" — ")
        # _rich = escape 후 ==키워드== 강조 — 다른 블록 경로와 동일. _escape만 쓰면 ==가 실물 노출(7/5 실측).
        if sep:
            inner = f'<div class="matrix-cell-label">{_rich(label.strip())}</div><div class="matrix-cell-copy">{_rich(desc.strip())}</div>'
        else:
            inner = f'<div class="matrix-cell-copy">{_rich(text)}</div>'
        cells.append({"inner": inner, "stats": ""})
    cells_html = "".join(
        f'<article class="matrix-cell">{c["inner"]}{c["stats"]}</article>' for c in cells
    )
    return f'<main class="body layout-body matrix-body">{subhead}<section class="matrix-grid">{cells_html}</section></main>'


def _render_poster(content: list[Any]) -> str:
    # 시그니처(minimal_typo 권장): 제목·부제 골격 자체가 없는 한 문장 포스터.
    # 표준 head는 CSS로 숨긴다(간지와 같은 방식) — short_title은 스파인(C7)용으로만 존재.
    kicker = ""
    statement = ""
    for block in content:
        bt = _block_type(block)
        if bt == "eyebrow" and not kicker:
            kicker = str(block.get("text", "")).strip()
        elif bt in {"headline", "title", "body", "text", "callout", "note"} and not statement:
            statement = str(block.get("text", "")).strip()
    kicker_html = f'<p class="poster-kicker">{_escape(kicker)}</p>' if kicker else ""
    return f"""
<main class="body layout-body poster-body">
  {kicker_html}
  <h2 class="poster-text">{_rich(statement)}</h2>
</main>""".strip()


def _render_hero_bleed(rendered_pairs: list[tuple[Any, str]] | None, content: list[Any]) -> str:
    # 시그니처(dark_premium 권장): 히어로 수치가 화면 절반을 블리드로 차지, 좌측에 서술.
    # 수치는 metric registry 주입값 그대로(C6) — 렌더된 metric-card에서 값을 뽑아 초대형 조판.
    hero_value, hero_label, hero_mid = "", "", ""
    left_parts: list[str] = []
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt == "metric" and not hero_value:
            m = re.search(r'metric-value[^>]*>([^<]+)<', html_part)
            lb = re.search(r'metric-label[^>]*>([^<]+)<', html_part)
            hero_value = m.group(1) if m else ""
            hero_label = lb.group(1) if lb else ""
            hero_mid = str(block.get("metric_id", "")).strip()
            continue
        left_parts.append(html_part)
    # 주입값이지만 재조판하며 태그가 떨어지면 C6 파서가 무단 숫자로 본다 — metric_id 태그 유지 의무.
    mid_attr = f' data-metric-id="{_escape(hero_mid)}"' if hero_mid else ""
    label_html = f'<p class="hero-bleed-label"{mid_attr}>{_escape(hero_label)}</p>' if hero_label else ""
    # 긴 단위(억 달러 등)는 190px nowrap에서 지면 밖으로 밀려 사라진다 — 숫자/단위 분리 조판.
    # %·단위는 group2로 빼 with-unit 경로(블리드 없이 안에 들어옴) — 190px nowrap에서 %가 밖으로 잘리던 것(후추님 7/4)
    num_match = re.match(r"^\s*([\d.,]+)\s*(%?.*?)\s*$", hero_value)
    num_class = "hero-bleed-num"
    if num_match and num_match.group(2):
        num_html = f'{_escape(num_match.group(1))}<span class="hero-bleed-unit">{_escape(num_match.group(2))}</span>'
        num_class += " with-unit"  # 단위 동반 시 숫자 폭 축소 — 190px 숫자만으로 지면이 차 단위가 밖으로 밀림
    else:
        num_html = _escape(hero_value)
    return f"""
<main class="body layout-body hero-bleed-body">
  <div class="hero-bleed-copy">{"".join(left_parts)}</div>
  <div class="hero-bleed-stage">{label_html}<div class="{num_class}"{mid_attr}>{num_html}</div></div>
</main>""".strip()


def _render_magazine_spread(rendered_pairs: list[tuple[Any, str]] | None) -> str:
    # 시그니처(editorial_serif 권장): 다단 조판 — 본문은 칼럼으로 흐르고 풀쿼트가 전폭으로 끊는다.
    columns: list[str] = []
    quote = ""
    tail: list[str] = []
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt in {"callout", "note"} and not quote:
            quote = html_part
        elif bt in {"body", "text", "summary", "bullets", "list"}:
            columns.append(html_part)
        else:
            tail.append(html_part)
    quote_html = f'<div class="mag-quote-row">{quote}</div>' if quote else ""
    lead = ""
    rest_tail: list[str] = []
    for part in tail:
        if part.lstrip().startswith('<h2 class="block-title"') and not lead:
            lead = part
        else:
            rest_tail.append(part)
    tail_html = f'<div class="mag-tail">{"".join(rest_tail)}</div>' if rest_tail else ""
    return f"""
<main class="body layout-body magazine-body">
  {lead}
  <div class="mag-columns">{"".join(columns)}</div>
  {quote_html}
  {tail_html}
</main>""".strip()


def _render_dashboard(rendered_pairs: list[tuple[Any, str]] | None) -> str:
    # 시그니처(data_mono 권장): 페이지 전체가 위젯 타일 — 각 블록이 계기판의 한 칸.
    lead = ""
    tiles: list[str] = []
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt in {"headline", "title"} and not lead:
            lead = html_part
            continue
        span = " dash-tile-wide" if bt == "viz" else ""
        tiles.append(f'<article class="dash-tile{span}">{html_part}</article>')
    return f"""
<main class="body layout-body dash-body">
  {lead}
  <section class="dash-grid">{"".join(tiles)}</section>
</main>""".strip()


def _render_mosaic_tiles(rendered_pairs: list[tuple[Any, str]] | None) -> str:
    # 시그니처(editorial_serif 권장): 텍스트/스탯 블록을 사진 없이 색면 타일 모자이크로 배치.
    lead = ""
    tiles: list[str] = []
    size_cycle = (" mosaic-tile-large", " mosaic-tile-medium", " mosaic-tile-small", " mosaic-tile-small")
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt in {"headline", "title"} and not lead:
            lead = html_part
            continue
        if bt not in {"body", "text", "summary", "bullets", "list", "callout", "note", "metric", "metrics", "metric_grid", "stat_grid"}:
            continue
        tile_type = " mosaic-stat" if bt in {"metric", "metrics", "metric_grid", "stat_grid"} else ""
        size = size_cycle[len(tiles) % len(size_cycle)]
        tiles.append(f'<article class="mosaic-tile{size}{tile_type}">{html_part}</article>')
    return f"""
<main class="body layout-body mosaic-body">
  {lead}
  <section class="mosaic-grid">{"".join(tiles)}</section>
</main>""".strip()


def _render_split_status(rendered_pairs: list[tuple[Any, str]] | None) -> str:
    # 시그니처(공용): 좌측은 상태 서술, 우측은 metric류를 얇은 지표 칩 스택으로 압축.
    lead = ""
    copy_parts: list[str] = []
    chips: list[str] = []
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt in {"headline", "title"} and not lead:
            lead = html_part
            continue
        if bt in {"metric", "metrics", "metric_grid", "stat_grid"}:
            chips.append(f'<article class="status-chip">{html_part}</article>')
        elif bt in {"body", "text", "summary", "bullets", "list", "callout", "note"}:
            copy_parts.append(html_part)
    return f"""
<main class="body layout-body split-status-body">
  {lead}
  <section class="status-copy">{"".join(copy_parts)}</section>
  <section class="status-chip-stack">{"".join(chips)}</section>
</main>""".strip()


def _render_scenario_cards(rendered_pairs: list[tuple[Any, str]] | None) -> str:
    # 시그니처(dark/pop 권장): headline이 카드를 열고 뒤따르는 body/metric류가 그 카드에 속한다.
    cards: list[dict[str, Any]] = []
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt in {"headline", "title"}:
            cards.append({"title": html_part, "parts": []})
            continue
        if bt not in {"body", "text", "summary", "bullets", "list", "callout", "note", "metric", "metrics", "metric_grid", "stat_grid"}:
            continue
        if not cards:
            cards.append({"title": "", "parts": []})
        cards[-1]["parts"].append(html_part)
    # 마지막 카드가 홀로 남는 줄에 걸리면(예: 4+1 종합) 좁은 카드 하나가 어색하다 — 전폭으로 눕혀
    # 종합/결론에 무게를 준다(후추님 7/4 p13 "종합은 하단 전폭 길게가 낫다"). 5장 이상일 때만.
    wide_last = len(cards) >= 5
    parts_html = []
    for idx, card in enumerate(cards):
        cls = "scenario-card"
        if wide_last and idx == len(cards) - 1:
            cls += " scenario-card-wide"
        parts_html.append(
            f'<article class="{cls}">{card["title"]}<div class="scenario-card-body">{"".join(card["parts"])}</div></article>'
        )
    grid_cls = "scenario-grid scenario-grid-fixed" if wide_last else "scenario-grid"
    return f"""
<main class="body layout-body scenario-body">
  <section class="{grid_cls}">{"".join(parts_html)}</section>
</main>""".strip()


# emphasis_style 파라미터화(PG-pricing_cards): 단일 고정 강조 방식 금지 — "같은 템플릿" 천장 재발 방지.
_PRICING_EMPHASIS_STYLES = {"invert", "offset", "scale", "border"}


def _render_pricing_cards(rendered_pairs: list[tuple[Any, str]] | None, page: dict[str, Any]) -> str:
    # 3열(2~4열 허용) 플랜/옵션 카드: headline이 카드를 연다(scenario_cards와 같은 그룹화 문법).
    # headline emphasis:true(또는 page.emphasis 인덱스 지정)인 카드가 강조 카드.
    emphasis_style = str(page.get("emphasis_style", "")).strip().lower() or "invert"
    if emphasis_style not in _PRICING_EMPHASIS_STYLES:
        emphasis_style = "invert"
    cards: list[dict[str, Any]] = []
    for block, html_part in (rendered_pairs or []):
        bt = _block_type(block)
        if bt in {"headline", "title"}:
            cards.append({"title": html_part, "parts": [], "emphasis": bool(block.get("emphasis"))})
            continue
        if bt not in {"body", "text", "summary", "bullets", "list", "callout", "note", "metric", "metrics", "metric_grid", "stat_grid"}:
            continue
        if not cards:
            cards.append({"title": "", "parts": [], "emphasis": False})
        cards[-1]["parts"].append(html_part)
    card_html = "".join(
        f'<article class="pricing-card{" pricing-card-emphasis pricing-emphasis-" + emphasis_style if card["emphasis"] else ""}">'
        f'{card["title"]}<div class="pricing-card-body">{"".join(card["parts"])}</div></article>'
        for card in cards
    )
    return f"""
<main class="body layout-body pricing-body">
  <section class="pricing-grid">{card_html}</section>
</main>""".strip()


def _render_index(body_parts: list[str], content: list[Any]) -> str:
    index_items = _index_items(content)
    if index_items:
        rows = "".join(
            f"""
            <article class="index-row">
              <div class="index-part">{_escape(item["part"])}</div>
              <div class="index-copy">{_escape(item["description"])}</div>
            </article>"""
            for item in index_items
        )
        return f'<main class="body layout-body index-body"><section class="index-list">{rows}</section></main>'

    rows = "".join(f'<article class="index-row"><div class="index-content">{part}</div></article>' for part in body_parts)
    return f'<main class="body layout-body index-body"><section class="index-list">{rows}</section></main>'


def _render_divider(page: dict[str, Any], content: list[Any], page_number: int) -> str:
    title = _clean_title_text(_first_block_text(content, {"headline", "title"}) or str(page.get("short_title", "")).strip())
    subtitle = _first_block_text(content, {"summary", "body", "text", "note"})
    part_index, part_label = _divider_part_meta(page, content, page_number)
    # 헤드라인이 파트명("설정 —"·"증거·")으로 시작하면 제거 — 바로 위 "PART n · 설정"과 중복(후추님 6/30).
    if part_label:
        title = re.sub(rf"^\s*{re.escape(part_label)}\s*[—·\-:]\s*", "", title).strip() or title
    part_count = _divider_part_count(page, part_index)
    progress = "".join(
        f'<span class="{"is-active" if index == part_index else ""}" aria-hidden="true"></span>'
        for index in range(1, part_count + 1)
    )
    subtitle_html = f'<p class="divider-subtitle">{_escape(subtitle)}</p>' if subtitle else ""
    # 간지 하위 목차 프리뷰(author-style §5 — 후추님 정본 2덱 시그니처): bullets/list 블록이
    # 있으면 "이 파트에서 볼 것"을 짧은 리스트로. 청중이 파트 시작마다 지도를 다시 받는다.
    items_html = ""
    for block in content:
        if _block_type(block) in {"bullets", "list"} and isinstance(block.get("items"), list):
            rows = "".join(
                f'<li>{_escape(str(item.get("text", "")) if isinstance(item, dict) else str(item))}</li>'
                for item in block["items"][:5]
            )
            items_html = f'<ul class="divider-items">{rows}</ul>'
            break
    # 헤드라인의 의도적 줄바꿈(\n)을 <br>로(나머지는 escape). 발표자가 끊고 싶은 지점 존중.
    title_html = "<br>".join(_rich(part) for part in title.split("\n"))
    # 고스트 배경 타이포(엔바토 흡수 3라운드 7/3 — JJ3Z2TF 등 다수 관찰): 파트 라벨을
    # 아주 크게·연하게 뒤에 깔아 배경 자체를 타이포로 채운다. hero_title과 함께 쓰면 과밀 — 배타적.
    ghost_html = ""
    if page.get("ghost_word") and not page.get("hero_title"):
        ghost_word = str(page.get("ghost_word")).strip() or part_label
        if ghost_word:
            ghost_html = f'<div class="divider-ghost" aria-hidden="true">{_escape(ghost_word)}</div>'

    # 조용한 뼈대(엔바토 흡수 3라운드 7/3 — KZS3K63 관찰): 진척바·PART접두어·불릿 다 빼고
    # 거대 숫자 하나 + 라벨 한 줄만. 뼈대 자체가 다른 간지 — 장식이 아니라 구조 변형.
    # 후추님 지적("목차·간지 양식은 그대로") 대응 — 장식 레버만 늘리고 뼈대를 안 늘렸던 누락.
    if str(page.get("divider_style", "")).lower() == "quiet":
        return f"""
<main class="body layout-body divider-body divider-quiet">
  <p class="eyebrow divider-part">{_escape(part_label)}</p>
  <div class="divider-quiet-num" aria-hidden="true">{part_index:02d}</div>
  <h2 class="divider-title">{title_html}</h2>
  {subtitle_html}
</main>""".strip()

    # 파트 표시는 진척 막대 + 한 줄(PART n · 라벨) 하나로 통일(후추님 #3 — 3중 중복 제거).
    return f"""
<main class="body layout-body divider-body">
  <div class="divider-motif" aria-hidden="true"></div>
  {ghost_html}
  <div class="divider-progress" aria-label="part progress">{progress}</div>
  <p class="eyebrow divider-part">PART {part_index} · {_escape(part_label)}</p>
  <h2 class="divider-title">{title_html}</h2>
  {subtitle_html}
  {items_html}
</main>""".strip()


def _render_closing(content: list[Any]) -> str:
    rows = "".join(
        f"""
        <article class="closing-point">
          <div class="closing-label">{_escape(item["label"])}</div>
          <div class="closing-copy">{_escape(item["copy"])}</div>
        </article>"""
        for item in _closing_items(content)
    )
    callout = _first_block_text(content, {"callout", "note"})
    callout_html = f'<p class="closing-callout">{_escape(callout)}</p>' if callout else ""
    points_html = f'<section class="closing-points">{rows}</section>' if rows else ""
    return f'<main class="body layout-body closing-body">{points_html}{callout_html}</main>'


def _index_items(content: list[Any]) -> list[dict[str, str]]:
    for block in content:
        if _block_type(block) not in {"bullets", "list"}:
            continue
        items = block.get("items", [])
        if not isinstance(items, list):
            continue
        parsed = []
        # 목차-간지 파트 수 불일치(후추님 7/3): 3개로 캡되어 5부 덱에서 목차엔 3개만 보이던 버그.
        # 캡을 없앤다 — 목차는 실제 파트 수만큼 전부 보여야 간지 진척바와 맞는다.
        for item in items:
            text = str(item.get("text", "")) if isinstance(item, dict) else str(item)
            text = re.sub(r"^\s*(?:\d{1,2}[\).\s-]+)", "", text).strip()
            part, description = _split_index_item(text)
            parsed.append({"part": part, "description": description})
        if parsed:
            return parsed
    return []


def _split_index_item(text: str) -> tuple[str, str]:
    for separator in (" — ", " – ", " - ", ":", "—", "–"):
        if separator in text:
            left, right = text.split(separator, 1)
            return left.strip(), right.strip()
    return text.strip(), ""


def _closing_items(content: list[Any]) -> list[dict[str, str]]:
    for block in content:
        if _block_type(block) not in {"bullets", "list"}:
            continue
        items = block.get("items", [])
        if not isinstance(items, list):
            continue
        parsed = []
        for item in items[:4]:
            if isinstance(item, dict):
                label = str(item.get("label", "")).strip()
                text = str(item.get("text", "")).strip()
                if label:
                    parsed.append({"label": label, "copy": text})
                    continue
            else:
                text = str(item).strip()
            label, copy = _split_closing_item(text)
            parsed.append({"label": label, "copy": copy})
        if parsed:
            return parsed

    parsed = []
    for block in content:
        if _block_type(block) in {"body", "text", "summary"}:
            label, copy = _split_closing_item(str(block.get("text", "")).strip())
            if label or copy:
                parsed.append({"label": label, "copy": copy})
    return parsed[:4]


def _split_closing_item(text: str) -> tuple[str, str]:
    for separator in (" — ", " – ", " - ", ":", "—", "–"):
        if separator in text:
            left, right = text.split(separator, 1)
            return left.strip(), right.strip()
    return "", text.strip()


def _slide_motif_html(layout: str, page_number: int, palette: dict[str, str]) -> str:
    # 라이트 본문 슬라이드 배경 코너에 아주 은은한 노드·신호망(후추님 #4 — 리듬·변주, 최소 강도).
    # 표지·간지·closing은 자체 장식이 있어 제외. 페이지마다 코너·형태를 바꿔 단조로움 회피.
    if layout in {"cover", "outro", "divider", "closing"}:
        return ""
    accent, accent2, node = palette["accent"], palette["accent2"], "currentColor"
    variant = page_number % 3
    if variant == 0:
        # 우상단 망
        nodes = [(60, 40), (200, 110), (360, 70), (300, 240), (420, 190), (120, 200)]
        edges = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4), (0, 5), (5, 3)]
        accent_idx, accent2_idx, pos = {1, 2}, {4}, "motif-tr"
    elif variant == 1:
        # 좌하단 망
        nodes = [(40, 230), (160, 150), (300, 210), (120, 60), (260, 60), (380, 130)]
        edges = [(0, 1), (1, 2), (1, 3), (3, 4), (2, 5), (4, 5)]
        accent_idx, accent2_idx, pos = {1}, {2}, "motif-bl"
    else:
        # 우하단 망
        nodes = [(80, 60), (210, 130), (360, 90), (300, 230), (430, 200)]
        edges = [(0, 1), (1, 2), (1, 3), (2, 4), (3, 4)]
        accent_idx, accent2_idx, pos = {2}, {4}, "motif-br"
    lines = "".join(
        f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}"/>'
        for a, b in edges
    )
    dots = "".join(
        f'<circle cx="{x}" cy="{y}" r="{5 if i in accent_idx or i in accent2_idx else 3.5}" '
        f'fill="{accent if i in accent_idx else accent2 if i in accent2_idx else node}"/>'
        for i, (x, y) in enumerate(nodes)
    )
    return (
        f'<svg class="slide-motif {pos}" viewBox="0 0 460 280" aria-hidden="true">'
        f'<g stroke="{node}" stroke-width="1.1">{lines}</g>{dots}</svg>'
    )


def _divider_part_meta(page: dict[str, Any], content: list[Any], page_number: int) -> tuple[int, str]:
    explicit = page.get("part_index", page.get("section_index"))
    try:
        part_index = int(explicit)
    except (TypeError, ValueError):
        text = " ".join(
            [
                str(page.get("short_title", "")),
                *[str(block.get("text", "")) for block in content if isinstance(block, dict)],
            ]
        )
        if "행동" in text:
            part_index = 3
        elif "증거" in text:
            part_index = 2
        elif "설정" in text:
            part_index = 1
        else:
            part_index = max(1, min(3, page_number))

    part_index = max(1, part_index)
    label = str(page.get("part_label", page.get("section_label", ""))).strip()
    if not label:
        label = {1: "설정", 2: "증거", 3: "행동"}.get(part_index, f"Part {part_index}")
    return part_index, label


def _divider_part_count(page: dict[str, Any], part_index: int) -> int:
    try:
        count = int(page.get("part_count", page.get("section_count", 3)))
    except (TypeError, ValueError):
        count = 3
    return max(part_index, count, 1)


def _cover_decor_html(palette: dict[str, str], part_count: int = 0) -> str:
    theme = palette["theme"]
    if theme == "tech":
        # 표지·outro 상단 코너 꺽쇠 제거(후추님 #7·#9). 표지/outro 모두 장식 없이 타이포만.
        return ""
    # (구) marketing 테마의 T1~T5 라벨 밴드는 2026 마케팅 5트렌드 덱 전용 유물 —
    # 무관한 덱에 복붙되던 하드코딩 제거(7/2). marketing도 아래 파트 수 밴드로 통일.
    if theme == "health":
        return '<div class="cover-health-curve" aria-hidden="true"></div>'
    # 기본(editorial·peppinch): 밴드 수 = 덱의 실제 파트(간지) 수 — 간지 진행 티커와 같은 어휘라
    # 표지가 덱 구조를 예고한다. 파트가 없으면 장식 생략(무의미한 고정 5밴드 금지·7/2).
    if part_count <= 0:
        return ""
    bands = "".join(
        f'<span style="--band:{_escape(palette[f"t{min(i, 5)}"])}"></span>' for i in range(1, part_count + 1)
    )
    width = min(760, part_count * 160)
    return (
        f'<div class="axis-strip editorial-axis" aria-hidden="true" '
        f'style="grid-template-columns: repeat({part_count}, 1fr); max-width: {width}px;">{bands}</div>'
    )


def _render_block(
    block: Any,
    page_id: str,
    registry: dict[str, dict[str, Any]],
    palette: dict[str, str],
) -> tuple[str, list[str]]:
    if not isinstance(block, dict):
        raise ValueError(f"{page_id}: content block must be an object")

    block_type = _block_type(block)
    if block_type not in SUPPORTED_CONTENT_BLOCK_TYPES:
        raise ValueError(f"{page_id}: unsupported content block type: {block_type}")
    if block_type == "eyebrow":
        return f'<div class="eyebrow block-eyebrow">{_escape(str(block.get("text", "")))}</div>', []
    if block_type in {"headline", "title"}:
        return f'<h2 class="block-title">{_rich(str(block.get("text", "")))}</h2>', []
    if block_type in {"body", "text", "summary"}:
        return f'<p class="body-text">{_rich(str(block.get("text", "")))}</p>', []
    if block_type in {"callout", "note"}:
        # emphasis:true면 펀치라인용으로 크게(제언·맺음 등). 기본은 일반 callout.
        # note-row 마커(7/3 후추님): split 계열이 이 조각을 하단 전폭 한 줄로 빼낼 수 있게 식별.
        cls = "callout callout-lead" if block.get("emphasis") else "callout"
        if block_type == "note":
            cls += " note-row"
        return f'<aside class="{cls}">{_rich(str(block.get("text", "")))}</aside>', []
    if block_type in {"citation", "source"}:
        src_id = str(block.get("src_id", block.get("source_id", ""))).strip()
        if src_id:
            _require_source(src_id, page_id, registry)
            return "", [src_id]
        return "", []
    if block_type == "metric":
        metric_id = str(block.get("metric_id", "")).strip()
        return _render_metric(metric_id, page_id, registry, str(block.get("label", "")).strip()), []
    if block_type in {"metrics", "metric_grid", "stat_grid"}:
        metric_ids = _as_list(block.get("metric_ids"))
        # 카드들의 출처가 둘 이상으로 갈리면 카드별 출처를 켠다(같은 출처면 footer만·중복 방지).
        src_keys = [
            (_as_list(_require_metric(mid, page_id, registry).get("source_ids")) or [""])[0]
            for mid in metric_ids
        ]
        show_src = len({s for s in src_keys if s}) > 1
        cards = [_render_metric(metric_id, page_id, registry, "", show_source=show_src) for metric_id in metric_ids]
        return f'<div class="metric-grid">{"".join(cards)}</div>', []
    if block_type == "viz":
        return _render_viz(block, page_id, registry, palette), []
    if block_type in {"bullets", "list"}:
        items = block.get("items", [])
        if not isinstance(items, list):
            raise ValueError(f"{page_id}: list block items must be a list")
        rendered_items = []
        source_ids: list[str] = []
        for item in items:
            if isinstance(item, dict):
                rendered_items.append(f"<li>{_escape(str(item.get('text', '')))}</li>")
                source_ids.extend(_as_list(item.get("source_ids", item.get("src_ids", []))))
            else:
                rendered_items.append(f"<li>{_escape(str(item))}</li>")
        for src_id in source_ids:
            _require_source(src_id, page_id, registry)
        return f'<ul class="bullet-list">{"".join(rendered_items)}</ul>', source_ids

    raise ValueError(f"{page_id}: unsupported content block type: {block_type}")


def _page_has_per_card_sources(content: list[Any], page_id: str, registry: dict[str, dict[str, Any]]) -> bool:
    # stat_grid/metric_grid 카드가 서로 다른 출처를 가져 카드별 출처를 켠 페이지인가
    # (= _render_block의 show_src 조건). 그러면 하단 source-row 중복 → 생략.
    for block in content:
        if _block_type(block) not in {"metrics", "metric_grid", "stat_grid"}:
            continue
        src_keys = {
            (_as_list(_require_metric(mid, page_id, registry).get("source_ids")) or [""])[0]
            for mid in _as_list(block.get("metric_ids"))
        }
        if len({s for s in src_keys if s}) > 1:
            return True
    return False


def _render_metric(
    metric_id: str,
    page_id: str,
    registry: dict[str, dict[str, Any]],
    label_override: str,
    show_source: bool = False,
) -> str:
    metric = _require_metric(metric_id, page_id, registry)
    value = _format_metric_value(metric)
    label = label_override or str(metric.get("label") or metric.get("scope") or metric_id)
    # 카드별 출처(우하단) — 한 그리드 안 카드들의 출처가 서로 다를 때만(다출처 비교·p04).
    # data-src-id로 감싸 기관명이 C6 authorized context에 들게 한다.
    src_html = ""
    if show_source:
        src_ids = _as_list(metric.get("source_ids"))
        if src_ids:
            pub = str(registry.get("sources", {}).get(src_ids[0], {}).get("publisher") or "").strip()
            if pub:
                src_html = f'\n  <div class="metric-source" data-src-id="{_escape(src_ids[0])}">{_escape(pub)}</div>'
    # 델타 3단 위계(차트캐논 A5·engine.py L_statgrid 기증) — registry가 delta를 가질 때만.
    # 값은 verifier 소유(metric_registry) → C6 안전. delta_dir = up|down.
    delta_html = ""
    delta = str(metric.get("delta") or "").strip()
    if delta:
        direction = str(metric.get("delta_dir") or "").strip()
        arrow = {"up": "▲ ", "down": "▼ "}.get(direction, "")
        delta_html = f'\n  <div class="metric-delta {_escape(direction)}" data-metric-id="{_escape(metric_id)}">{arrow}{_escape(delta)}</div>'
    return f"""
<article class="metric-card" data-metric-id="{_escape(metric_id)}">
  <div class="metric-label" data-metric-id="{_escape(metric_id)}">{_escape(label)}</div>
  <div class="metric-value" data-metric-id="{_escape(metric_id)}">{_escape(value)}</div>{delta_html}{src_html}
</article>""".strip()


def _render_viz(
    block: dict[str, Any],
    page_id: str,
    registry: dict[str, dict[str, Any]],
    palette: dict[str, str],
) -> str:
    chart = str(block.get("chart", "")).strip()
    if chart not in SUPPORTED_VIZ_CHART_TYPES:
        raise ValueError(f"{page_id}: unsupported viz chart type: {chart}")
    series = _viz_series(block, page_id, registry)
    title = str(block.get("title", "")).strip()
    note = str(block.get("note", "")).strip()
    accent = _viz_accent(block, palette)
    renderer = _CHART_RENDERERS.get(chart)
    if renderer is None:
        raise ValueError(f"{page_id}: viz chart has no renderer: {chart}")
    svg = renderer(series, title, note, accent, page_id, block)
    return f'<aside class="visual-card visual-{_class_name(chart)}">{svg}</aside>'


def _viz_series(
    block: dict[str, Any],
    page_id: str,
    registry: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    series = block.get("series")
    if not isinstance(series, list) or not series:
        raise ValueError(f"{page_id}: viz series must be a non-empty list")

    rendered: list[dict[str, Any]] = []
    for index, item in enumerate(series):
        if not isinstance(item, dict):
            raise ValueError(f"{page_id}: viz series item {index} must be an object")
        raw_id = item.get("metric_id")
        metric_id = str(raw_id).strip() if raw_id not in (None, "") else ""
        if metric_id:
            metric = _require_metric(metric_id, page_id, registry)
            value = _format_metric_value(metric)
            number = _metric_number(metric)
        else:
            # flow 등 개념 흐름 차트는 수치 없는 라벨 노드 허용(C6: 라벨에 raw 숫자만 없으면 OK).
            value, number = "", None
        label = str(item.get("label") or metric_id).strip()
        rendered.append(
            {
                "metric_id": metric_id,
                "label": label,
                "role": str(item.get("role", "")).strip(),
                "value": value,
                "number": number,
            }
        )
    return rendered


# 모든 차트 함수가 공유하는 소제목(visual-title y=20)→첫 요소 사이 세로 여백(후추님 6/30 통일).
# funnel의 첫 막대 baseline(74)을 기준으로 before_after·gap_map·dumbbell·shift 첫 요소를 같은 리듬에 맞춘다.
CHART_TITLE_GAP = 74


def _svg_before_after(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    rows = series[:4]
    # 델타 주석(백로그 Phase 1·McKinsey/PwC) — 전·후 2행이면 변화량을 코드가 계산해
    # highlight 행 라벨줄 우측에 표기. 렌더러 계산·data-metric-id 컨텍스트 → C6 안전.
    delta_text = _delta_annotation(rows) if (block or {}).get("delta", True) else ""
    # 라벨을 막대 위 줄에 올린다(막대와 겹침 차단·후추님 #2). 한 행 = 라벨줄 + 막대줄.
    row_h = 78
    # 소제목(visual-title y=20)과 첫 요소 사이 여백을 전 차트 공통 CHART_TITLE_GAP로 통일(후추님 6/30).
    height = (CHART_TITLE_GAP - 18) + len(rows) * row_h + (30 if note else 0)
    # %데이터는 0~100 축(38%가 full처럼 보이던 문제·코덱스 p08). 투자 건수 등은 최댓값 대비 유지.
    # 배경 트랙은 두지 않는다 — 막대 길이의 비율(13:38)만으로 읽게(후추님 6/30 "깔끔").
    scale_base = 100.0 if _is_bounded_percent_series(rows) else _max_metric_number(rows)
    bar_full = 760
    body = []
    for index, item in enumerate(rows):
        top = CHART_TITLE_GAP + index * row_h
        bar_y = top + 26
        width = _scale_metric_width(item, scale_base, bar_full)
        highlight = _is_highlight(item, index, rows)
        color = accent if highlight else "#B0A491"  # 비강조 막대 진슬레이트(트랙과 구분)
        value_x = min(980, width + 22)
        value_class = "visual-value-accent" if color == accent else "visual-value"
        # 델타는 값 바로 옆 tspan — 떨어뜨려 놓으면 어느 막대의 변화량인지 붕 뜬다(7/2 데모 QA).
        delta_tspan = f'<tspan dx="20" class="visual-delta">{_escape(delta_text)}</tspan>' if highlight and delta_text else ""
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <text x="0" y="{top + 8}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <rect x="0" y="{bar_y}" width="{width:.1f}" height="24" rx="12" fill="{color}"/>
              <text x="{value_x:.1f}" y="{bar_y + 19}" class="{value_class}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}{delta_tspan}</text>
            </g>"""
        )
    return _svg_shell("before-after", title, note, height, "".join(body), page_id)


def _delta_annotation(rows: list[dict[str, Any]]) -> str:
    """전·후 2행의 변화량 요약 — %끼리는 %p 차이, 그 외는 배율(×N). 렌더러 소유 계산."""
    if len(rows) != 2:
        return ""
    first, last = rows[0].get("number"), rows[1].get("number")
    if not isinstance(first, (int, float)) or not isinstance(last, (int, float)):
        return ""
    if _is_bounded_percent_series(rows):
        diff = last - first
        return f"{diff:+.0f}%p" if diff else ""
    if first > 0 and last / first >= 1.5:
        ratio = last / first
        return f"×{ratio:.0f}" if ratio >= 10 else f"×{ratio:.1f}"
    return ""


def _svg_dumbbell(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    points = (series[:2] if len(series) >= 2 else [series[0], series[0]])
    max_value = _max_metric_number(points)
    # 좌측 정렬·좌측 가중(후추님 6/30 재지적): 트랙을 좌측 거터(60)에서 시작, 우측 끝까지 안 뻗게.
    # 단 60%는 전폭(stack)에서 공백으로 읽혀 76%로 상향(7/3 p05).
    gutter, span = 60, 700
    x1 = gutter + (_metric_position_ratio(points[0], max_value) * span)
    x2 = gutter + (_metric_position_ratio(points[1], max_value) * span)
    left, right = sorted((x1, x2))
    # 트랙 y = 값 텍스트(노드 y-36)가 CHART_TITLE_GAP에 오도록 → 소제목과 첫 요소 여백을 타 차트와 통일.
    ty = CHART_TITLE_GAP + 36
    body = f"""
      <line x1="{gutter}" y1="{ty}" x2="{gutter + span}" y2="{ty}" stroke="#E5E7EB" stroke-width="12" stroke-linecap="round"/>
      <line x1="{left:.1f}" y1="{ty}" x2="{right:.1f}" y2="{ty}" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>
      {_svg_point(points[0], x1, ty, "#E5E7EB", "visual-value")}
      {_svg_point(points[1], x2, ty, accent, "visual-value-accent")}
    """
    return _svg_shell("dumbbell", title, note, ty + 118, body, page_id)


def _metric_position_ratio(item: dict[str, Any], max_value: float) -> float:
    number = abs(item["number"]) if isinstance(item.get("number"), (int, float)) else 0.0
    return (number / max_value) if max_value else 0.0


def _svg_flow(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    nodes = series[:4]
    arrow_id = f"arrow-{_class_name(page_id)}-flow"
    step = 760 / max(1, len(nodes) - 1)
    body = [
        f"""
        <defs>
          <marker id="{arrow_id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 Z" fill="{accent}"/>
          </marker>
        </defs>"""
    ]
    for index in range(len(nodes) - 1):
        x1 = 118 + step * index
        x2 = 118 + step * (index + 1)
        body.append(f'<line x1="{x1 + 86:.1f}" y1="98" x2="{x2 - 86:.1f}" y2="98" stroke="{accent}" stroke-width="4" marker-end="url(#{arrow_id})"/>')
    for index, item in enumerate(nodes):
        x = 118 + step * index
        fill = accent if _is_highlight(item, index, nodes) else "#E5E7EB"
        text_fill = "#FFFFFF" if fill == accent else "#1F2733"
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <rect x="{x - 88:.1f}" y="62" width="176" height="72" rx="36" fill="{fill}"/>
              <text x="{x:.1f}" y="91" text-anchor="middle" fill="{text_fill}" font-size="15" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <text x="{x:.1f}" y="116" text-anchor="middle" fill="{text_fill}" font-size="18" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("flow", title, note, 188, "".join(body), page_id)


def _svg_big_number(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # arrow=false면 화살표 생략 — 비중(%)은 변화량이 아니라 상태라 ↑가 "상승했다"로 오독됨(후추님 6/30).
    arrow = (block or {}).get("arrow", True)
    item = _highlight_or_first(series)
    # arrow=false면 화살표 tspan 자체를 빼서 % 비중이 "상승"으로 안 읽히게(후추님 6/30).
    arrow_glyph = "↓" if (item["number"] or 0) < 0 else "↑"
    arrow_tspan = f'<tspan font-size="58" fill="{accent}" font-weight="900">{arrow_glyph}</tspan>' if arrow else ""
    value_dx = ' dx="6"' if arrow else ""
    # 화살표를 큰 숫자 바로 왼쪽에 붙여 "↑41%"처럼 한 덩어리로 읽히게(후추님 #2). 라벨은 우측 칼럼(고정)에서 줄바꿈.
    label_html = _escape(item["label"])
    body = f"""
      <text x="0" y="126" data-metric-id="{_escape(item["metric_id"])}">{arrow_tspan}<tspan font-size="80"{value_dx} fill="{accent}" font-weight="900" class="visual-bn-value">{_escape(item["value"])}</tspan><tspan font-size="22" dx="28" fill="#1F2733" font-weight="700" class="visual-bn-label">{label_html}</tspan></text>
    """
    return _svg_shell("big-number", title, note, 196, body, page_id)


def _svg_gap_map(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    rows = series[:5]
    # 내림차순 정렬(차트캐논 A3 — 순위 비교는 정렬이 기본, 시계열 제외). opt-in: "sort":"desc".
    if (block or {}).get("sort") == "desc":
        rows = sorted(rows, key=lambda r: abs(r["number"]) if isinstance(r.get("number"), (int, float)) else -1, reverse=True)
    # 라벨을 막대 위 줄로 올려 겹침 차단(후추님 #2).
    row_h = 68
    height = (CHART_TITLE_GAP - 16) + len(rows) * row_h + (30 if note else 0)
    # 퍼센트 데이터는 0~100 축으로(코덱스·제미나이 #1·후추님 6/30): 79%가 트랙을 꽉 채워
    # 100%처럼 보이던 버그. 투자 건수 등 비-퍼센트만 최댓값 대비. 회색 트랙=100% 기준선.
    scale_base = 100.0 if _is_bounded_percent_series(rows) else _max_metric_number(rows)
    track = 760
    body = []
    for index, item in enumerate(rows):
        top = CHART_TITLE_GAP + index * row_h
        bar_y = top + 24
        width = _scale_metric_width(item, scale_base, track)
        is_benchmark = item.get("role") == "benchmark"
        is_highlight = _is_highlight(item, index, rows) and not is_benchmark
        if is_highlight and not isinstance(item.get("number"), (int, float)):
            width = track
        # 유령막대(차트캐논 발산 렌즈·Qwen): role=benchmark는 업계평균/목표선 — 옅게 깔려 비교 기준만 제공.
        if is_benchmark:
            color, opacity = "#1F2733", ' fill-opacity=".14"'
        else:
            color, opacity = (accent if is_highlight else "#B0A491"), ""  # 비강조 막대: 진슬레이트(트랙과 구분·후추님 6/30)
        value_class = "visual-value-accent" if is_highlight else "visual-value"
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <text x="0" y="{top + 8}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <rect x="0" y="{bar_y}" width="{track}" height="16" rx="8" fill="#E5E7EB"/>
              <rect x="0" y="{bar_y}" width="{width:.1f}" height="16" rx="8" fill="{color}"{opacity}/>
              <text x="{track + 18}" y="{bar_y + 14}" class="{value_class}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("gap-map", title, note, height, "".join(body), page_id)


def _svg_shift(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    nodes = series[:5]
    arrow_id = f"arrow-{_class_name(page_id)}-shift"
    step = 760 / max(1, len(nodes) - 1)
    body = [
        f"""
        <defs>
          <marker id="{arrow_id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 Z" fill="#1F2733" opacity=".42"/>
          </marker>
        </defs>
        <text x="0" y="{CHART_TITLE_GAP - 20}" class="visual-note">회색=기준 / 파랑=현재</text>"""
    ]
    for index, item in enumerate(nodes):
        x = 72 + step * index
        y = CHART_TITLE_GAP + 42
        value_y = y + 104
        label_y = y + 66
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <circle cx="{x:.1f}" cy="{y}" r="18" fill="#E5E7EB"/>
              <line x1="{x + 28:.1f}" y1="{y}" x2="{x + 88:.1f}" y2="{y}" stroke="#1F2733" stroke-width="2" opacity=".34" marker-end="url(#{arrow_id})"/>
              <circle cx="{x + 116:.1f}" cy="{y}" r="27" fill="{accent}"/>
              <text x="{x + 116:.1f}" y="{label_y}" text-anchor="middle" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <text x="{x + 116:.1f}" y="{value_y}" text-anchor="middle" class="visual-value-accent" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("shift", title, note, 278 if note else 248, "".join(body), page_id)


def _svg_funnel(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    rows = series[:5]
    # 한 행 = [좌측 라벨] · [좌측 정렬 막대] · [막대 오른쪽 값]. 막대 길이는 값에 정비례(좌정렬)해
    # 단계 비율이 눈으로 정확히 보이게 한다. 라벨은 막대 왼쪽, 값은 막대 끝 오른쪽.
    gutter = 360
    bar_track = 540  # 막대 최대폭(최댓값 행). gutter+track+값 여백이 viewBox 1000 안에 들어오게.
    bar_h = 38
    row_h = 56
    height = 74 + len(rows) * row_h + (30 if note else 0)  # 소제목(title)과 첫 막대 사이 여백(후추님 6/30)
    max_value = _max_metric_number(rows)
    body = []
    for index, item in enumerate(rows):
        cy = 74 + index * row_h
        bar_y = cy - bar_h / 2
        width = _scale_metric_width(item, max_value, bar_track)  # 값에 정비례(180 바닥값 제거 — 비율 왜곡 fix)
        highlight = _is_highlight(item, index, rows)
        fill = accent if highlight else "#D7DCE2"
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <text x="0" y="{cy + 7}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <rect x="{gutter}" y="{bar_y:.1f}" width="{width:.1f}" height="{bar_h}" rx="{bar_h // 2}" fill="{fill}" opacity="{1 if highlight else .92}"/>
              <text x="{gutter + width + 12:.1f}" y="{cy + 8:.1f}" text-anchor="start" fill="#1F2733" font-size="22" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("funnel", title, note, height, "".join(body), page_id)


def _svg_donut(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 단일 핵심 비중(차트캐논 A4·engine.py L_donut 기증) — 중앙 KPI + 우측 보조 수치(series[1:] ≤3).
    # 후추님 선호 목록(도넛게이지)의 v4 어휘화. 값은 0~100 비중일 때만 의미(그 외 clamp).
    item = _highlight_or_first(series)
    number = item.get("number") if isinstance(item.get("number"), (int, float)) else 0.0
    val = max(0.0, min(100.0, abs(number)))
    radius, stroke = 104, 26
    cx = 168
    cy = CHART_TITLE_GAP + 126
    circumference = 2 * math.pi * radius
    dash = circumference * val / 100
    aux_rows = []
    aux_items = [s for s in series if s is not item][:3]
    for index, aux in enumerate(aux_items):
        y = cy - 74 + index * 68
        aux_rows.append(
            f"""
            <g data-metric-id="{_escape(aux["metric_id"])}">
              <text x="420" y="{y}" class="visual-label" data-metric-id="{_escape(aux["metric_id"])}">{_escape(aux["label"])}</text>
              <text x="960" y="{y}" text-anchor="end" class="visual-value" data-metric-id="{_escape(aux["metric_id"])}">{_escape(aux["value"])}</text>
              <line x1="420" y1="{y + 18}" x2="960" y2="{y + 18}" stroke="#E5E7EB" stroke-width="1"/>
            </g>"""
        )
    center_label_lines = _wrap_text(item["label"], 12)[:2]
    label_tspans = "".join(
        f'<tspan x="{cx}" dy="{0 if i == 0 else 19}">{_escape(line)}</tspan>' for i, line in enumerate(center_label_lines)
    )
    body = f"""
      <g data-metric-id="{_escape(item["metric_id"])}">
        <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#E5E7EB" stroke-width="{stroke}"/>
        <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{accent}" stroke-width="{stroke}" stroke-linecap="round"
          stroke-dasharray="{dash:.1f} {circumference - dash:.1f}" transform="rotate(-90 {cx} {cy})"/>
        <text x="{cx}" y="{cy - 2}" text-anchor="middle" font-size="56" font-weight="900" fill="{accent}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
        <text x="{cx}" y="{cy + 34}" text-anchor="middle" class="visual-note" data-metric-id="{_escape(item["metric_id"])}">{label_tspans}</text>
      </g>{"".join(aux_rows)}"""
    return _svg_shell("donut", title, note, cy + radius + 42, body, page_id)


def _svg_pictogram(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 픽토그램/도트 채움(엔바토 흡수 3라운드 7/3 — PE5HT4N·3M6NRPR·6QAF86G·DYMFYCD 4곳 교차검증).
    # "10명 중 3명"류 정성적 카운트 프레이밍에 적합 — 값은 0~100 비중일 때만 의미(그 외 clamp).
    item = _highlight_or_first(series)
    number = item.get("number") if isinstance(item.get("number"), (int, float)) else 0.0
    val = max(0.0, min(100.0, abs(number)))
    cols, rows = 10, 5
    total = cols * rows
    filled = round(val / 100 * total)
    radius, gap_x, gap_y = 17, 76, 58
    start_x, start_y = radius + 4, CHART_TITLE_GAP + radius + 4
    dots = []
    for index in range(total):
        col, row = index % cols, index // cols
        cx = start_x + col * gap_x
        cy = start_y + row * gap_y
        fill = accent if index < filled else "#E5E7EB"
        dots.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{radius}" fill="{fill}"/>')
    grid_bottom = start_y + (rows - 1) * gap_y + radius
    label_y = grid_bottom + 46
    value_y = label_y + 52
    body = f"""
      <g data-metric-id="{_escape(item["metric_id"])}">
        {"".join(dots)}
        <text x="0" y="{label_y}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
        <text x="0" y="{value_y}" font-size="48" font-weight="900" fill="{accent}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
      </g>"""
    height = value_y + 16 + (30 if note else 0)
    return _svg_shell("pictogram", title, note, height, body, page_id)


def _svg_gauge(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 반원 게이지(엔바토 흡수 3라운드 7/3 — M4FX5T4 스피드 다이얼·6QAF86G 넘긴 아크 교차검증).
    # 도넛(원형)과 대비되는 "계기판" 느낌 — 단일 % 강조에 쓴다. 값은 0~100 비중일 때만 의미.
    item = _highlight_or_first(series)
    number = item.get("number") if isinstance(item.get("number"), (int, float)) else 0.0
    val = max(0.0, min(100.0, abs(number)))
    cx, cy, r, stroke = 500, 214, 190, 34
    fraction = val / 100
    theta_end = math.radians(180 * (1 - fraction))
    ex, ey = cx + r * math.cos(theta_end), cy - r * math.sin(theta_end)
    # sweep-flag=1: 왼쪽→오른쪽을 시계방향(위쪽 반원)으로 — 0을 쓰면 아래쪽 반원이 그려짐(실측 발견 버그).
    value_arc = ""
    if fraction > 0:
        value_arc = f'<path d="M {cx - r} {cy} A {r} {r} 0 0 1 {ex:.1f} {ey:.1f}" fill="none" stroke="{accent}" stroke-width="{stroke}" stroke-linecap="round"/>'
    body = f"""
      <g data-metric-id="{_escape(item["metric_id"])}">
        <path d="M {cx - r} {cy} A {r} {r} 0 1 1 {cx + r} {cy}" fill="none" stroke="#E5E7EB" stroke-width="{stroke}" stroke-linecap="round"/>
        {value_arc}
        <text x="{cx}" y="{cy - 6}" text-anchor="middle" font-size="64" font-weight="900" fill="{accent}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
        <text x="{cx}" y="{cy + 36}" text-anchor="middle" class="visual-note" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
      </g>"""
    height = cy + 64 + (30 if note else 0)
    return _svg_shell("gauge", title, note, height, body, page_id)


def _svg_mirror_bars(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 미러 분기 막대(백로그 Phase 2·Deloitte) — 중앙 스파인 양면 비교. role=left(비교군·틴트)/right(주장·액센트).
    lefts = [s for s in series if s.get("role") == "left"][:4]
    rights = [s for s in series if s.get("role") == "right"][:4]
    if not lefts or not rights:
        raise ValueError(f"{page_id}: mirror_bars needs series with role left and right")
    row_count = max(len(lefts), len(rights))
    both = lefts + rights
    scale_base = 100.0 if _is_bounded_percent_series(both) else _max_metric_number(both)
    spine, half = 500, 340
    row_h = 96
    height = CHART_TITLE_GAP + row_count * row_h + (30 if note else 0)
    body = [
        f'<line x1="{spine}" y1="{CHART_TITLE_GAP - 8}" x2="{spine}" y2="{CHART_TITLE_GAP + row_count * row_h - 26}" stroke="#1F2733" stroke-width="1.5" opacity=".3"/>'
    ]
    # 라벨은 각 진영 막대 위 바깥쪽(스파인 반대편) 정렬 — 두 라벨이 중앙에서 맞붙어 겹치던 것 방지(후추님 7/4 p05).
    for index in range(row_count):
        top = CHART_TITLE_GAP + index * row_h
        bar_y = top + 34
        if index < len(lefts):
            item = lefts[index]
            width = _scale_metric_width(item, scale_base, half)
            body.append(
                f"""
                <g data-metric-id="{_escape(item["metric_id"])}">
                  <text x="{spine - 22 - width:.1f}" y="{top + 12}" text-anchor="end" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
                  <rect x="{spine - 10 - width:.1f}" y="{bar_y}" width="{width:.1f}" height="22" rx="11" fill="#B0A491"/>
                  <text x="{spine - 22 - width:.1f}" y="{bar_y + 17}" text-anchor="end" class="visual-value" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
                </g>"""
            )
        if index < len(rights):
            item = rights[index]
            width = _scale_metric_width(item, scale_base, half)
            body.append(
                f"""
                <g data-metric-id="{_escape(item["metric_id"])}">
                  <text x="{spine + 22 + width:.1f}" y="{top + 12}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
                  <rect x="{spine + 10}" y="{bar_y}" width="{width:.1f}" height="22" rx="11" fill="{accent}"/>
                  <text x="{spine + 22 + width:.1f}" y="{bar_y + 17}" class="visual-value-accent" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
                </g>"""
            )
    return _svg_shell("mirror-bars", title, note, height, "".join(body), page_id)


def _svg_rising_columns(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 상승컬럼 + 멀티플라이어 브래킷(백로그 Phase 2·PwC) — 점증 세로 막대(명도램프) + 첫→끝 ×N 콜아웃.
    rows = series[:5]
    max_value = _max_metric_number(rows)
    # 높이는 테마 서체가 커도(기본 24px 부제) 720px 슬라이드에 안 넘치는 값 — peppinch(20px)만 통과하던 걸 보정(7/2).
    base_y = CHART_TITLE_GAP + 176
    max_h = 148
    area_x, area_w = 80, 840
    col_w = min(140, area_w / max(1, len(rows)) * 0.56)
    step = area_w / max(1, len(rows))
    delta_text = _delta_annotation([rows[0], rows[-1]]) if len(rows) >= 2 and (block or {}).get("delta", True) else ""
    body = []
    tops: list[tuple[float, float]] = []
    for index, item in enumerate(rows):
        number = abs(item["number"]) if isinstance(item.get("number"), (int, float)) else 0.0
        h = max(10.0, (number / max_value) * max_h) if max_value else 10.0
        x = area_x + step * index + (step - col_w) / 2
        y = base_y - h
        tops.append((x + col_w / 2, y))
        is_last = index == len(rows) - 1
        opacity = 0.34 + (0.66 * index / max(1, len(rows) - 1))
        value_class = "visual-value-accent" if is_last else "visual-value"
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <rect x="{x:.1f}" y="{y:.1f}" width="{col_w:.1f}" height="{h:.1f}" rx="6" fill="{accent}" fill-opacity="{opacity:.2f}"/>
              <text x="{x + col_w / 2:.1f}" y="{y - 12:.1f}" text-anchor="middle" class="{value_class}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
              <text x="{x + col_w / 2:.1f}" y="{base_y + 26}" text-anchor="middle" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
            </g>"""
        )
    if delta_text and len(tops) >= 2:
        (x1, y1), (x2, y2) = tops[0], tops[-1]
        bracket_y = min(y1, y2) - 54
        last_id = rows[-1]["metric_id"]
        body.append(
            f"""
            <g data-metric-id="{_escape(last_id)}">
              <path d="M {x1:.1f} {y1 - 34:.1f} L {x1:.1f} {bracket_y:.1f} L {x2:.1f} {bracket_y:.1f} L {x2:.1f} {y2 - 34:.1f}" fill="none" stroke="{accent}" stroke-width="2" opacity=".55"/>
              <text x="{(x1 + x2) / 2:.1f}" y="{bracket_y - 10:.1f}" text-anchor="middle" class="visual-delta" data-metric-id="{_escape(last_id)}">{_escape(delta_text)}</text>
            </g>"""
        )
    return _svg_shell("rising-columns", title, note, base_y + 44 + (28 if note else 0), "".join(body), page_id)


# chart enum(계약 SoT)과 렌더러 1:1 — 빠지면 테스트가 잡는다(test_contracts 커버리지).
# ── 다이어그램 어휘(2026-07-04 후추님 "이런 레이아웃은 전혀 없잖아" — 수치 비교 계열만 있고
#    관계·순환·프로세스·표를 그리는 인포그래픽 어휘가 0종이던 공백). 색은 팔레트 t램프 순환(var(--tN))
#    — 다색 팝 테마에선 팝으로, 단일 액센트 테마에선 근접 톤으로 각자 착지.

def _t_fill(index: int) -> str:
    return f"var(--t{(index % 4) + 1})"


def _svg_hub_cycle(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 순환 허브: series[0] = 중심, 나머지 = 궤도 노드(최대 6). 개념 관계 다이어그램 — 값은 선택.
    import math
    center, orbit = series[0], series[1:7]
    cx, cy, r = 500, 190, 118
    body = [f'<circle cx="{cx}" cy="{cy}" r="64" fill="var(--ink)" opacity=".12"/>']
    body.append(f'<circle cx="{cx}" cy="{cy}" r="52" fill="{accent}"/>')
    body.append(f'<text x="{cx}" y="{cy + 6}" text-anchor="middle" fill="#FFFFFF" font-size="17" font-weight="900">{_escape(center["label"])}</text>')
    n = max(1, len(orbit))
    for i, item in enumerate(orbit):
        ang = -math.pi / 2 + (2 * math.pi / n) * i
        nx, ny = cx + math.cos(ang) * 320, cy + math.sin(ang) * r
        lx, ly = cx + math.cos(ang) * 58, cy + math.sin(ang) * 48
        body.append(f'<line x1="{lx:.0f}" y1="{ly:.0f}" x2="{nx:.0f}" y2="{ny:.0f}" stroke="var(--line)" stroke-width="2"/>')
        fill = _t_fill(i)
        body.append(f'<g data-metric-id="{_escape(item["metric_id"])}"><rect x="{nx - 82:.0f}" y="{ny - 26:.0f}" width="164" height="52" rx="26" fill="{fill}"/>')
        vy = ny + (0 if item["value"] else 6)
        body.append(f'<text x="{nx:.0f}" y="{vy - 4:.0f}" text-anchor="middle" fill="#FFFFFF" font-size="15" font-weight="800">{_escape(item["label"])}</text>')
        if item["value"]:
            body.append(f'<text x="{nx:.0f}" y="{ny + 17:.0f}" text-anchor="middle" fill="#FFFFFF" font-size="16" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>')
        body.append("</g>")
    return _svg_shell("hub_cycle", title, note, 392, "".join(body), page_id)


def _svg_arrow_flow(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 두꺼운 셰브런 프로세스: 단계 자체가 화살표 도형(기존 flow의 가는 화살표와 다른 인포그래픽 문법).
    nodes = series[:5]
    n = len(nodes)
    total_w, notch = 920, 34
    step_w = (total_w - notch) / n
    y0, h = CHART_TITLE_GAP - 14, 96
    body = []
    for i, item in enumerate(nodes):
        x = 40 + step_w * i
        tip = x + step_w + notch
        tail = f"{x},{y0} {x + step_w},{y0} {tip},{y0 + h / 2} {x + step_w},{y0 + h} {x},{y0 + h}"
        head = f" {x + notch},{y0 + h / 2}" if i > 0 else ""
        body.append(f'<g data-metric-id="{_escape(item["metric_id"])}"><polygon points="{tail}{head}" fill="{_t_fill(i)}"/>')
        tx = x + step_w / 2 + (notch / 2 if i > 0 else 8)
        vy = y0 + h / 2 + (0 if item["value"] else 7)
        body.append(f'<text x="{tx:.0f}" y="{vy - 6:.0f}" text-anchor="middle" fill="#FFFFFF" font-size="16" font-weight="900">{_escape(item["label"])}</text>')
        if item["value"]:
            body.append(f'<text x="{tx:.0f}" y="{y0 + h / 2 + 22:.0f}" text-anchor="middle" fill="#FFFFFF" font-size="19" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>')
        body.append("</g>")
    return _svg_shell("arrow_flow", title, note, 208, "".join(body), page_id)


def _svg_timeline_bars(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 간트형 타임라인: 행마다 시작점이 계단식으로 밀리는 가로 바 — 순서·구간감(값은 선택).
    rows = series[:5]
    n = len(rows)
    row_h, bar_h = 58, 30
    y0 = CHART_TITLE_GAP - 10
    lane_x, lane_w = 250, 700
    stagger = lane_w / (n + 1.2)
    body = [f'<line x1="{lane_x}" y1="{y0 - 8}" x2="{lane_x}" y2="{y0 + row_h * n - 18}" stroke="var(--line)" stroke-width="2"/>']
    for i, item in enumerate(rows):
        y = y0 + row_h * i
        bx = lane_x + stagger * i
        bw = max(150, lane_w - stagger * i - 40)
        body.append(f'<text x="{lane_x - 16}" y="{y + bar_h / 2 + 6:.0f}" text-anchor="end" class="visual-label" font-size="17">{_escape(item["label"])}</text>')
        body.append(f'<g data-metric-id="{_escape(item["metric_id"])}"><rect x="{bx:.0f}" y="{y}" width="{bw:.0f}" height="{bar_h}" rx="{bar_h / 2}" fill="{_t_fill(i)}"/>')
        if item["value"]:
            body.append(f'<text x="{bx + bw - 16:.0f}" y="{y + bar_h / 2 + 6:.0f}" text-anchor="end" fill="#FFFFFF" font-size="16" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>')
        body.append("</g>")
    return _svg_shell("timeline_bars", title, note, y0 + row_h * n + 26, "".join(body), page_id)


def _svg_data_table(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 데이터 테이블: 액센트 헤더 행 + 줄무늬 본문(다크 프리미엄·팝 계열 공통 관례). 값=registry.
    rows = series[:6]
    row_h = 46
    y0 = CHART_TITLE_GAP - 16
    body = [
        f'<rect x="0" y="{y0}" width="1000" height="{row_h}" rx="6" fill="{accent}"/>',
        f'<text x="24" y="{y0 + row_h / 2 + 6:.0f}" fill="#FFFFFF" font-size="16" font-weight="900">항목</text>',
        f'<text x="976" y="{y0 + row_h / 2 + 6:.0f}" text-anchor="end" fill="#FFFFFF" font-size="16" font-weight="900">값</text>',
    ]
    for i, item in enumerate(rows):
        y = y0 + row_h * (i + 1)
        if i % 2 == 0:
            body.append(f'<rect x="0" y="{y}" width="1000" height="{row_h}" fill="var(--ink)" opacity=".05"/>')
        body.append(f'<text x="24" y="{y + row_h / 2 + 6:.0f}" class="visual-label" font-size="17">{_escape(item["label"])}</text>')
        body.append(f'<text x="976" y="{y + row_h / 2 + 6:.0f}" text-anchor="end" class="visual-value" font-size="21" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>')
        body.append(f'<line x1="0" y1="{y + row_h}" x2="1000" y2="{y + row_h}" stroke="var(--line)" stroke-width="1"/>')
    return _svg_shell("data_table", title, note, y0 + row_h * (len(rows) + 1) + 30, "".join(body), page_id)


# ── 승격 라운드(2026-07-04 후추님 승인·PATTERN_LIBRARY ⬜→✅): report_ops 정체성 4종.

def _svg_multi_line(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 다계열 라인(관찰 8/8 dashboard + 4/5 report_ops): role "highlight"=액센트 선, "baseline"=회색 선.
    # 각 항목 = 한 점(순서 = x축). 점 위 값 라벨. 시계열 배열이 아니라 registry 스칼라 점들의 연결.
    lanes: dict[str, list[dict[str, Any]]] = {"highlight": [], "baseline": []}
    for item in series:
        lanes["baseline" if item.get("role") == "baseline" else "highlight"].append(item)
    y0, h, x0, w = CHART_TITLE_GAP, 150, 80, 860
    numbers = [i["number"] for lane in lanes.values() for i in lane if i["number"] is not None]
    vmax = max(numbers) if numbers else 1
    body = [f'<line x1="{x0}" y1="{y0 + h}" x2="{x0 + w}" y2="{y0 + h}" stroke="var(--line)" stroke-width="2"/>']
    for lane_name, pts in lanes.items():
        if not pts:
            continue
        color = accent if lane_name == "highlight" else "var(--muted)"
        step = w / max(1, len(pts) - 1) if len(pts) > 1 else 0
        coords = []
        for i, item in enumerate(pts):
            frac = (item["number"] / vmax) if (item["number"] is not None and vmax) else 0.5
            x = x0 + (step * i if len(pts) > 1 else w / 2)
            y = y0 + h - h * 0.82 * frac
            coords.append((x, y, item))
        path = " ".join(f"{'M' if i == 0 else 'L'}{x:.0f},{y:.0f}" for i, (x, y, _) in enumerate(coords))
        body.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="4" stroke-linejoin="round"/>')
        for x, y, item in coords:
            body.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="6" fill="{color}"/>')
            if item["value"]:
                body.append(f'<text x="{x:.0f}" y="{y - 14:.0f}" text-anchor="middle" class="visual-value" font-size="19" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>')
            body.append(f'<text x="{x:.0f}" y="{y0 + h + 24:.0f}" text-anchor="middle" class="visual-label" font-size="15">{_escape(item["label"])}</text>')
    # x축 라벨(y0+h+24)과 shell note(height-10)가 겹치지 않게 높이 여유(+70) — 스모크 실측.
    return _svg_shell("multi_line", title, note, y0 + h + 70, "".join(body), page_id)


def _svg_progress_bar(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 진척 막대(관찰 3 report_ops): 트랙(전장=100%) + 채움(%). number를 0~100으로 해석.
    rows = series[:5]
    row_h, bar_h, y0 = 56, 22, CHART_TITLE_GAP - 8
    lane_x, lane_w = 300, 620
    body = []
    for i, item in enumerate(rows):
        y = y0 + row_h * i
        frac = min(1.0, max(0.0, (item["number"] or 0) / 100))
        body.append(f'<text x="{lane_x - 16}" y="{y + bar_h / 2 + 6:.0f}" text-anchor="end" class="visual-label" font-size="17">{_escape(item["label"])}</text>')
        body.append(f'<rect x="{lane_x}" y="{y}" width="{lane_w}" height="{bar_h}" rx="{bar_h / 2}" fill="var(--ink)" opacity=".1"/>')
        body.append(f'<g data-metric-id="{_escape(item["metric_id"])}"><rect x="{lane_x}" y="{y}" width="{max(bar_h, lane_w * frac):.0f}" height="{bar_h}" rx="{bar_h / 2}" fill="{accent if _is_highlight(item, i, rows) else _t_fill(i)}"/>')
        body.append(f'<text x="{lane_x + lane_w + 14}" y="{y + bar_h / 2 + 6:.0f}" class="visual-value" font-size="20" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text></g>')
    return _svg_shell("progress_bar", title, note, y0 + row_h * len(rows) + 20, "".join(body), page_id)


def _svg_target_vs_actual(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 계획 vs 실제(관찰 3 report_ops): 연속 짝 (baseline=계획 고스트 아웃라인, highlight=실제 채움).
    pairs = [(series[i], series[i + 1]) for i in range(0, len(series) - 1, 2)][:4]
    row_h, bar_h, y0 = 74, 24, CHART_TITLE_GAP - 6
    lane_x, lane_w = 300, 600
    numbers = [i["number"] for pair in pairs for i in pair if i["number"] is not None]
    vmax = max(numbers) if numbers else 1
    body = []
    for i, (target, actual) in enumerate(pairs):
        y = y0 + row_h * i
        body.append(f'<text x="{lane_x - 16}" y="{y + bar_h + 2:.0f}" text-anchor="end" class="visual-label" font-size="17">{_escape(actual["label"])}</text>')
        tw = lane_w * ((target["number"] or 0) / vmax)
        aw = lane_w * ((actual["number"] or 0) / vmax)
        body.append(f'<g data-metric-id="{_escape(target["metric_id"])}"><rect x="{lane_x}" y="{y}" width="{max(6, tw):.0f}" height="{bar_h}" rx="4" fill="none" stroke="var(--muted)" stroke-width="2" stroke-dasharray="6 4"/>')
        body.append(f'<text x="{lane_x + max(6, tw) + 10:.0f}" y="{y + bar_h / 2 + 5:.0f}" class="visual-note" font-size="14" data-metric-id="{_escape(target["metric_id"])}">계획 {_escape(target["value"])}</text></g>')
        body.append(f'<g data-metric-id="{_escape(actual["metric_id"])}"><rect x="{lane_x}" y="{y + bar_h + 8}" width="{max(6, aw):.0f}" height="{bar_h}" rx="4" fill="{accent}"/>')
        body.append(f'<text x="{lane_x + max(6, aw) + 10:.0f}" y="{y + bar_h * 1.5 + 13:.0f}" class="visual-value" font-size="18" data-metric-id="{_escape(actual["metric_id"])}">{_escape(actual["value"])}</text></g>')
    return _svg_shell("target_vs_actual", title, note, y0 + row_h * len(pairs) + 22, "".join(body), page_id)


def _svg_radial_progress(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 단일 링 진척(관찰 3 report_ops): 원형 트랙 + %만큼 채운 호, % 중앙. 최대 3링 나란히.
    import math
    rings = series[:3]
    r, y0 = 74, CHART_TITLE_GAP + 66
    n = len(rings)
    body = []
    for i, item in enumerate(rings):
        cx = 500 + (i - (n - 1) / 2) * 250
        frac = min(1.0, max(0.0, (item["number"] or 0) / 100))
        body.append(f'<circle cx="{cx:.0f}" cy="{y0}" r="{r}" fill="none" stroke="var(--ink)" stroke-opacity=".1" stroke-width="14"/>')
        if frac > 0:
            end = -math.pi / 2 + 2 * math.pi * min(frac, 0.999)
            large = 1 if frac > 0.5 else 0
            x1, y1 = cx, y0 - r
            x2, y2 = cx + r * math.cos(end), y0 + r * math.sin(end)
            color = _t_fill(i) if n > 1 else accent
            body.append(f'<path d="M{x1:.0f},{y1:.0f} A{r},{r} 0 {large} 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round" data-metric-id="{_escape(item["metric_id"])}"/>')
        body.append(f'<text x="{cx:.0f}" y="{y0 + 9}" text-anchor="middle" class="visual-value-accent" font-size="34" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>')
        body.append(f'<text x="{cx:.0f}" y="{y0 + r + 32}" text-anchor="middle" class="visual-label" font-size="16">{_escape(item["label"])}</text>')
    return _svg_shell("radial_progress", title, note, y0 + r + 50, "".join(body), page_id)


def _svg_swot_quad(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
    block: dict[str, Any] | None = None,
) -> str:
    # 2×2 정성 사분면(PG-swot_quad, 후추님 2026-07-04 승격 큐): metric_id 없음 — series[].items가
    # 정성 항목 텍스트. _viz_series는 items를 안 실어 나르므로 원본 block.series에서 직접 읽는다.
    raw_series = (block or {}).get("series")
    quads = raw_series[:4] if isinstance(raw_series, list) else []
    cell_w, cell_h, gap = 460, 190, 20
    x0, y0 = 0, CHART_TITLE_GAP - 4
    body = []
    for i, quad in enumerate(quads):
        col, row = i % 2, i // 2
        cx = x0 + col * (cell_w + gap)
        cy = y0 + row * (cell_h + gap)
        highlight = str(quad.get("role", "")).strip() == "highlight"
        fill = f"color-mix(in srgb, {accent} 16%, transparent)" if highlight else "color-mix(in srgb, var(--ink) 5%, transparent)"
        cell_class = "swot-cell-highlight" if highlight else "swot-cell"
        label = str(quad.get("label", "")).strip()
        items = quad.get("items") if isinstance(quad.get("items"), list) else []
        item_lines = []
        for line_index, raw_item in enumerate(items[:4]):
            iy = cy + 62 + line_index * 26
            item_lines.append(
                f'<text x="{cx + 22}" y="{iy}" class="visual-note swot-item">• {_escape(str(raw_item))}</text>'
            )
        body.append(
            f"""
            <g class="{cell_class}">
              <rect x="{cx}" y="{cy}" width="{cell_w}" height="{cell_h}" rx="10" fill="{fill}"/>
              <text x="{cx + 22}" y="{cy + 32}" class="visual-value-accent swot-label" font-size="20">{_escape(label)}</text>
              {"".join(item_lines)}
            </g>"""
        )
    grid_w = cell_w * 2 + gap
    grid_h = cell_h * 2 + gap
    cross_x, cross_y = x0 + cell_w + gap / 2, y0 + cell_h + gap / 2
    body.append(f'<line x1="{cross_x}" y1="{y0}" x2="{cross_x}" y2="{y0 + grid_h}" stroke="var(--line)" stroke-width="2"/>')
    body.append(f'<line x1="{x0}" y1="{cross_y}" x2="{x0 + grid_w}" y2="{cross_y}" stroke="var(--line)" stroke-width="2"/>')
    return _svg_shell("swot_quad", title, note, y0 + grid_h + 20, "".join(body), page_id)


_CHART_RENDERERS = {
    "multi_line": _svg_multi_line,
    "progress_bar": _svg_progress_bar,
    "target_vs_actual": _svg_target_vs_actual,
    "radial_progress": _svg_radial_progress,
    "hub_cycle": _svg_hub_cycle,
    "arrow_flow": _svg_arrow_flow,
    "timeline_bars": _svg_timeline_bars,
    "data_table": _svg_data_table,
    "before_after": _svg_before_after,
    "dumbbell": _svg_dumbbell,
    "flow": _svg_flow,
    "big_number": _svg_big_number,
    "gap_map": _svg_gap_map,
    "shift": _svg_shift,
    "funnel": _svg_funnel,
    "donut": _svg_donut,
    "mirror_bars": _svg_mirror_bars,
    "rising_columns": _svg_rising_columns,
    "pictogram": _svg_pictogram,
    "gauge": _svg_gauge,
    "swot_quad": _svg_swot_quad,
}


def _wrap_text(text: str, max_chars: int) -> list[str]:
    """공백 기준 그리디 줄바꿈. SVG <text>는 자동 wrap이 없어 직접 접는다."""
    lines: list[str] = []
    cur = ""
    for word in text.split(" "):
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    if cur:
        lines.append(cur)
    return lines or [text]


def _svg_shell(kind: str, title: str, note: str, height: int, body: str, page_id: str) -> str:
    title_html = f'<text x="0" y="20" class="visual-title">{_escape(title)}</text>' if title else ""
    note_html = ""
    if note:
        # note를 viewBox(1000) 폭에 맞춰 줄바꿈(17px Korean ≈ 52자/줄)하고, 늘어난 줄만큼 SVG를 키운다.
        # SVG <text>는 wrap이 없어 한 줄이 오른쪽으로 잘리던 버그(코덱스 p08 지적) 근본 풀이.
        lines = _wrap_text(note, 52)
        line_h = 22
        first_y = height - 10
        height = height + (len(lines) - 1) * line_h
        tspans = "".join(
            f'<tspan x="0" dy="{0 if i == 0 else line_h}">{_escape(line)}</tspan>'
            for i, line in enumerate(lines)
        )
        note_html = f'<text x="0" y="{first_y}" class="visual-note">{tspans}</text>'
    return f"""
<svg viewBox="0 0 1000 {height}" role="img" aria-label="{_escape(kind)} chart for {_escape(page_id)}">
  {title_html}
  {body}
  {note_html}
</svg>""".strip()


def _svg_point(item: dict[str, Any], x: float, y: int, fill: str, value_class: str) -> str:
    # font-size를 SVG user 단위(attribute)로 박는다 — CSS px는 viewBox 스케일과 안 맞아
    # 값이 노드 중앙에서 좌우로 밀려 보임(후추님 #3 정렬 어긋남 근본). attr 크기는 viewBox와 함께 스케일.
    value_size = 27 if value_class.endswith("accent") else 23  # 그래프 안 텍스트 축소(후추님 6/30 — 위계)
    # 라벨이 viewBox 밖으로 잘리지 않게 가장자리에서 anchor 전환(7/2 — 좌측 노드 라벨 잘림 fix).
    label_len = len(str(item["label"])) * 16  # 한글 15px 근사폭
    if x - label_len / 2 < 8:
        label_anchor, label_x = "start", max(8.0, x - 24)
    elif x + label_len / 2 > 992:
        label_anchor, label_x = "end", min(992.0, x + 24)
    else:
        label_anchor, label_x = "middle", x
    return f"""
      <g data-metric-id="{_escape(item["metric_id"])}">
        <circle cx="{x:.1f}" cy="{y}" r="20" fill="{fill}" stroke="#CBD5E1" stroke-width="2"/>
        <text x="{x:.1f}" y="{y - 34}" text-anchor="middle" font-size="{value_size}" class="{value_class}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
        <text x="{label_x:.1f}" y="{y + 48}" text-anchor="{label_anchor}" font-size="15" class="visual-note" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
      </g>"""


def _max_metric_number(series: list[dict[str, Any]]) -> float:
    numbers = [abs(item["number"]) for item in series if isinstance(item.get("number"), (int, float))]
    return max(numbers) if numbers else 1.0


def _is_bounded_percent_series(series: list[dict[str, Any]]) -> bool:
    """0~100 안의 퍼센트 비중만 100축으로 잡는다. 성장률(100% 초과)은 max 대비."""
    vals = [str(item.get("value", "")) for item in series]
    nums = [item.get("number") for item in series]
    return bool(vals) and all("%" in v for v in vals) and all(isinstance(n, (int, float)) and 0 <= n <= 100 for n in nums)


def _scale_metric_width(item: dict[str, Any], max_value: float, max_width: int) -> float:
    number = abs(item["number"]) if isinstance(item.get("number"), (int, float)) else max_value
    return max(18.0, (number / max_value) * max_width) if max_value else float(max_width)


def _scale_metric_position(item: dict[str, Any], max_value: float, start: int, width: int) -> float:
    number = abs(item["number"]) if isinstance(item.get("number"), (int, float)) else 0.0
    return start + ((number / max_value) * width if max_value else 0)


def _metric_number(metric: dict[str, Any]) -> float | None:
    match = re.search(r"-?\d+(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?", str(metric.get("value", "")))
    if not match:
        return None
    return float(match.group(0).replace(",", ""))


def _is_highlight(item: dict[str, Any], index: int, rows: list[dict[str, Any]]) -> bool:
    return item.get("role") == "highlight" or (not any(row.get("role") == "highlight" for row in rows) and index == len(rows) - 1)


def _highlight_or_first(series: list[dict[str, Any]]) -> dict[str, Any]:
    for item in series:
        if item.get("role") == "highlight":
            return item
    return series[0]


def _viz_accent(block: dict[str, Any], palette: dict[str, str]) -> str:
    key = str(block.get("accent") or block.get("trend") or "").lower()
    return palette.get(key, palette["accent"])


def _render_sources(source_ids: list[str], registry: dict[str, dict[str, Any]]) -> str:
    seen: set[str] = set()
    rendered: list[str] = []
    for src_id in source_ids:
        if src_id in seen:
            continue
        seen.add(src_id)
        source = _require_source(src_id, "render", registry)
        publisher = str(source.get("publisher") or source.get("title") or src_id)
        url = str(source.get("url") or "").strip()
        if url:
            rendered.append(
                f'<a class="source-link" data-src-id="{_escape(src_id)}" href="{_escape(url)}">{_escape(publisher)}</a>'
            )
        else:
            rendered.append(f'<span class="source-link" data-src-id="{_escape(src_id)}">{_escape(publisher)}</span>')
    return "".join(rendered)


def _deck_cited_source_ids(pages: list[Any], registry: dict[str, dict[str, Any]]) -> list[str]:
    cited: list[str] = []
    seen: set[str] = set()

    def add(src_id: str) -> None:
        if src_id and src_id in registry["sources"] and src_id not in seen:
            seen.add(src_id)
            cited.append(src_id)

    for page in pages:
        if not isinstance(page, dict) or str(page.get("layout", "")) == "source_appendix":
            continue
        content = page.get("content", [])
        for src_id in _iter_source_ids(content):
            add(src_id)
        for metric_id in _iter_metric_ids(content):
            metric = registry["metrics"].get(metric_id)
            if isinstance(metric, dict):
                for src_id in _as_list(metric.get("source_ids")):
                    add(src_id)
    return cited


def _format_metric_value(metric: dict[str, Any]) -> str:
    value = _group_thousands(str(metric.get("value", "")).strip())
    unit = str(metric.get("unit", "")).strip()
    if not value:
        raise ValueError("metric value is required")
    if not unit or value.endswith(unit):
        return value
    if unit in {"%", "pp", "p", "x", "X", "조", "억", "만", "명", "개", "건", "원", "달러"}:
        return f"{value}{unit}"
    return f"{value} {unit}"


def _group_thousands(value: str) -> str:
    """천단위 콤마. 순수 정수/소수 값만 그룹화하고, 범위·기호가 섞인 값은 그대로 둔다."""
    match = re.fullmatch(r"(-?)(\d+)(\.\d+)?", value)
    if not match:
        return value
    sign, integer, frac = match.groups()
    return f"{sign}{int(integer):,}{frac or ''}"


def _iter_metric_ids(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "metric_id" and nested not in (None, "") and str(nested).strip():
                yield str(nested)
            elif key == "metric_ids" and isinstance(nested, list):
                for item in nested:
                    if str(item).strip():
                        yield str(item)
            else:
                yield from _iter_metric_ids(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_metric_ids(nested)


def _iter_source_ids(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in {"src_id", "source_id"} and nested not in (None, "") and str(nested).strip():
                yield str(nested)
            elif key in {"src_ids", "source_ids"} and isinstance(nested, list):
                for item in nested:
                    if str(item).strip():
                        yield str(item)
            else:
                yield from _iter_source_ids(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _iter_source_ids(nested)


def _require_metric(metric_id: str, page_id: str, registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if not metric_id:
        raise ValueError(f"{page_id}: metric_id is required")
    metric = registry["metrics"].get(metric_id)
    if not isinstance(metric, dict):
        raise ValueError(f"{page_id}: unknown metric_id {metric_id}")
    return metric


def _require_source(src_id: str, page_id: str, registry: dict[str, dict[str, Any]]) -> dict[str, Any]:
    source = registry["sources"].get(src_id)
    if not isinstance(source, dict):
        raise ValueError(f"{page_id}: unknown src_id {src_id}")
    return source


def _registry_map(registry: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    for key in keys:
        value = registry.get(key) if isinstance(registry, dict) else None
        if isinstance(value, dict):
            return {str(item_key): item_value for item_key, item_value in value.items()}
    return {}


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]
    if value is None:
        return []
    return [str(value)] if str(value).strip() else []


def _block_type(block: Any) -> str:
    if not isinstance(block, dict):
        return ""
    return str(block.get("type", "text"))


def _page_title_text(page: dict[str, Any], content: list[Any], layout: str) -> str:
    if layout == "closing":
        return _clean_title_text(_first_block_text(content, {"headline", "title"}) or str(page.get("short_title", "")).strip())
    return _clean_title_text(str(page.get("short_title", "")).strip())


def _clean_title_text(text: str) -> str:
    # 제목 앞머리의 마크다운·기호 잔재(*, #, - 등) 제거 — p12 '* 한국의…' 별표가 그대로
    # 렌더된 재발 방지(7/2). C6 제목 면제 구역이라 계약이 못 잡으니 렌더에서 strip.
    return re.sub(r"^[\s*#>•·~\-]+", "", text).strip()


def _first_block_text(content: list[Any], block_types: set[str]) -> str:
    for block in content:
        if _block_type(block) in block_types:
            text = str(block.get("text", "")).strip()
            if text:
                return text
    return ""


def _non_cover_text(text: str) -> str:
    return "" if text.strip().lower() in {"표지", "cover"} else text.strip()


def _class_name(value: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in value.lower()).strip("-") or "statement"


def _escape(value: str) -> str:
    return html.escape(normalize_enclosed_numerals(value), quote=True)


_KEYWORD_PATTERN = re.compile(r"==([^=]+?)==")


def _rich(value: str) -> str:
    # 헤드라인 키워드 색전환(백로그 Phase 1·KPMG) — ==키워드== 만 accent로.
    # escape 후 치환이라 안전. 새 사실·수치 창작이 아니라 기존 텍스트의 강조 표시만.
    return _KEYWORD_PATTERN.sub(r'<b class="kw">\1</b>', _escape(value))


def _hex_luminance(color: str) -> float:
    color = color.lstrip("#")
    if len(color) != 6:
        return 0.5
    r, g, b = (int(color[i : i + 2], 16) / 255 for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _hex_to_rgba(color: str, alpha: float) -> str:
    color = color.lstrip("#")
    if len(color) != 6:
        return f"rgba(0,0,0,{alpha})"
    r, g, b = (int(color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _divider_accent_color(palette: dict[str, str]) -> str:
    # accent 풀블리드 간지용 색 — accent가 잉크와 명도가 붙으면(forest처럼 둘 다 딥톤)
    # 풀블리드가 기본 간지와 구분이 안 되므로 accent2로 폴백.
    accent, ink = palette["accent"], palette["ink"]
    if abs(_hex_luminance(accent) - _hex_luminance(ink)) < 0.16:
        return palette["accent2"]
    return accent


def _css(palette: dict[str, str]) -> str:
    return f"""
:root {{
  --c60: {palette["c60"]};
  --c30: {palette["c30"]};
  --accent: {palette["accent"]};
  --accent2: {palette["accent2"]};
  --divider-accent: {_divider_accent_color(palette)};
  --divider-accent-fg: {"#F8FAFC" if _hex_luminance(_divider_accent_color(palette)) < 0.45 else "color-mix(in srgb, " + palette["ink"] + " 92%, black)"};
  --ink: {palette["ink"]};
  --ghost: {_hex_to_rgba(palette["ink"], 0.12)};
  --muted: {palette["muted"]};
  --line: {palette["line"]};
  --grid-line: {palette["grid_line"]};
  --slide-bg: {palette["slide_bg"]};
  --slide-bg-size: {palette["slide_bg_size"]};
  --body-bg: {palette["body_bg"]};
  --card: {palette["card"]};
  --radius: {palette["radius"]};
  --mono-font: ui-monospace, "SFMono-Regular", "SF Mono", Consolas, "Liberation Mono", monospace;
  --font-body: {palette.get("font_body") or '"Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif'};
  --font-head: {palette.get("font_head") or '"Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif'};
  --t1: {palette["t1"]};
  --t2: {palette["t2"]};
  --t3: {palette["t3"]};
  --t4: {palette["t4"]};
  --t5: {palette["t5"]};
}}
@page {{ size: 1280px 720px; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--body-bg);
  color: var(--ink);
  font-family: var(--font-body);
  word-break: keep-all;  /* 한국어 단어가 음절로 쪼개지지 않게 전역 기본(상속)·후추님 7/1 */
}}
.slide {{
  position: relative;
  width: 1280px;
  height: 720px;
  overflow: hidden;
  page-break-after: always;
  padding: 56px 72px 36px;
  display: flex;
  flex-direction: column;
  background: var(--slide-bg);
  background-size: var(--slide-bg-size);
}}
.slide-head {{ flex: 0 0 auto; }}
/* 배경 코너 노드 모티프(후추님 #4) — 최소 강도. 콘텐츠보다 뒤·가독성 비방해. */
.slide-motif {{
  position: absolute;
  width: 420px;
  height: 256px;
  color: var(--accent);
  opacity: .07;
  pointer-events: none;
  z-index: 0;
}}
.slide-motif.motif-tr {{ top: -28px; right: -24px; }}
.slide-motif.motif-bl {{ bottom: 56px; left: -30px; transform: scaleY(-1); }}
.slide-motif.motif-br {{ bottom: 56px; right: -24px; }}
.slide-head, .body, .slide-foot {{ position: relative; z-index: 1; }}
.eyebrow {{
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--accent);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .28em;
}}
.eyebrow::before {{ content: ""; width: 24px; height: 2px; background: var(--accent); }}
/* 카테고리 칩 변형(CB 흡수 1번·page.eyebrow_chip=true) — 배경색 칩으로 강조. 덱 간 변주 레버. */
.eyebrow.eyebrow-chip {{
  display: inline-flex;
  align-self: flex-start;
  background: var(--accent);
  color: #FFFFFF;
  padding: 6px 14px;
  border-radius: 999px;
  letter-spacing: .18em;
}}
.eyebrow.eyebrow-chip::before {{ display: none; }}
/* 다크 표지 변형(cover_variant:"dark") — 간지와 같은 잉크 파생 문법. 덱 간 차별화 레버(후추님 7/2). */
.cover-slide.cover-dark {{
  background:
    radial-gradient(circle at 82% 20%, color-mix(in srgb, var(--accent) 20%, transparent) 0, transparent 40%),
    linear-gradient(150deg, color-mix(in srgb, var(--ink) 88%, white) 0%, var(--ink) 62%, color-mix(in srgb, var(--ink) 80%, black) 100%);
  color: #F8FAFC;
}}
.cover-slide.cover-dark h1 {{ color: #F8FAFC; }}
.cover-slide.cover-dark .cover-subtitle {{ color: rgba(248,250,252,.82); }}
.cover-slide.cover-dark .cover-credit,
.cover-slide.cover-dark .presenter-email {{ color: rgba(248,250,252,.6); }}
/* 회사명·이름은 이메일만 밝게 바꾸고 누락돼 잉크색 그대로 다크 위에서 무독이던 구멍(후추님 7/3
   outro 실측 — PEPPINCH·이름 안 보임). 그라디언트 배경이라 lowc 자동검출도 skip이던 사각. */
.cover-slide.cover-dark .presenter-company,
.cover-slide.cover-dark .presenter-name {{ color: #F8FAFC; }}
.block-eyebrow {{ align-self: flex-start; }}
h1 {{
  margin: 14px 0 0;
  max-width: 980px;
  font-size: 44px;
  line-height: 1.18;
  letter-spacing: 0;
  word-break: keep-all;
  font-family: var(--font-head);
}}
.body {{
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  gap: 24px;
  padding: 20px 0 8px;
}}
/* statement/hero/stat 차트 슬라이드는 제목 바로 아래 상단 정렬(후추님 #4 — bottom-weighted 통일).
   divider·index·matrix·closing·cover는 각자 -body에서 justify-content를 따로 잡아 영향 없음. */
.body-grid {{ justify-content: center; }}
/* 저밀도 페이지(블록 ≤3) 세로 중앙 — 하단 공백이 의도된 여백으로 읽히게(7/2). */
.body-center {{ justify-content: center; }}
/* headline 블록 = h1 아래의 단일 부제. h1(44px) 대비 크기 점프를 확실히(후추님 #9 위계 단순화). */
.block-title {{
  font-size: 24px;
  line-height: 1.4;
  font-weight: 700;
  color: var(--muted);
  margin: -8px 0 4px;
  max-width: 960px;
  word-break: keep-all;
}}
.body-text {{ font-size: 18px; line-height: 1.56; max-width: 980px; word-break: keep-all; }}
/* callout = 박스 강조 takeaway. note(body-text 18px)와 위계: 굵기600+박스+약간 큼(20)·위 여백 (후추님 6/30).
   크기를 너무 키우면 dense 슬라이드가 넘쳐 굵기로 위계를 준다. */
.callout {{ font-size: 20px; font-weight: 600; line-height: 1.5; max-width: 1020px; word-break: keep-all;
  border-left: 4px solid var(--accent);
  background: var(--card);
  border-radius: var(--radius);
  padding: 18px 24px;
  margin-top: 14px;
}}
/* 펀치라인 callout(emphasis) — 제언·맺음의 한 줄을 크게. 박스 톤은 유지, 글자만 키움. */
.callout-lead {{ font-size: 30px; font-weight: 800; color: var(--ink); padding: 22px 26px; }}
/* split-note-row — note(단, ~ 캐비앗)를 좌우 칸에 끼워 넣지 않고 하단 전폭으로 뺀다(7/3 후추님
   1차 지적: 우측 칸에 박스로 갇혀 어색함). 단, 박스 톤 자체는 유지 — 각주 같은 민무늬 한 줄로
   벗기니 "안내문 같다"는 재지적(7/3 2차) — 원래 callout 박스 그대로, 폭만 전폭. */
.split-note-row {{ margin-top: 18px; }}
.split-note-row .callout {{ max-width: none; }}
.metric-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}}
.metric-card {{
  min-height: 170px;
  border: 1px solid var(--line);
  border-top: 3px solid var(--accent);
  background: var(--card);
  border-radius: var(--radius);
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.metric-label {{
  color: var(--muted);
  font-size: 15px;
  line-height: 1.45;
  word-break: keep-all;
}}
.metric-value {{
  color: var(--accent);
  font-size: 64px;
  line-height: 1;
  font-weight: 900;
  font-variant-numeric: tabular-nums;
}}
.metric-source {{
  align-self: flex-end;
  margin-top: 10px;
  font-size: 12px;
  color: var(--muted);
  letter-spacing: .02em;
}}
/* 델타 3단 위계(차트캐논 A5) — 라벨→큰숫자→델타. 의미색 = 증가 녹 / 감소 적(3사 수렴). */
.metric-delta {{ font-size: 14px; font-weight: 800; margin-top: 8px; font-variant-numeric: tabular-nums; }}
.metric-delta.up {{ color: #2E9E6B; }}
.metric-delta.down {{ color: #C8553D; }}
/* 키워드 색전환(==키워드==·백로그 Phase 1) — 강조어만 accent. 슬라이드당 절제. */
.kw {{ color: var(--accent); }}
.bullet-list {{
  margin: 0;
  padding: 0;
  display: grid;
  gap: 16px;
  list-style: none;
  max-width: 980px;
}}
.bullet-list li {{
  position: relative;
  padding-left: 28px;
  font-size: 20px;
  line-height: 1.45;
}}
.bullet-list li::before {{
  content: "";
  position: absolute;
  left: 0;
  top: .72em;
  width: 16px;
  height: 2px;
  background: var(--accent);
}}
.slide-foot {{
  position: relative;
  z-index: 3;
  flex: 0 0 auto;
  margin-top: 6px;
  border-top: 1px solid var(--line);
  padding-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: .08em;
}}
/* 출처 = 푸터 선 위 한 줄(후추님 6/30). nowrap으로 한 줄 유지·선 아래로 안 내려감. */
.source-row {{
  flex: 0 0 auto;
  display: flex;
  gap: 14px;
  white-space: nowrap;
  overflow: hidden;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: .08em;
  margin-bottom: 2px;
}}
.source-link {{ color: var(--muted); text-decoration: none; white-space: nowrap; }}
.source-link::before {{ content: "["; color: var(--accent); }}
.source-link::after {{ content: "]"; color: var(--accent); }}
/* 용어 풀이 각주 = 출처행 위, 작게(일반 청중 배려). 줄바꿈 허용(한 줄 강제 X). */
.footnote-row {{
  flex: 0 0 auto;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: 4px;
}}
.footnote-item {{ margin-right: 18px; }}
.footnote-item b {{ color: var(--ink); font-weight: 700; }}
.page-number {{ white-space: nowrap; }}
/* 푸터 선 아래 = [좌 spacer][중앙 카피라이트][우 페이지번호]. 중앙 절대중앙 고정. */
.slide-foot .foot-side {{ flex: 1 1 0; }}
.slide-foot .page-number {{ flex: 1 1 0; text-align: right; }}
.copyright {{
  flex: 0 0 auto;
  white-space: nowrap;
  text-align: center;
  color: var(--muted);
}}
.layout-closing .copyright,
.layout-divider .copyright {{ color: inherit; opacity: .82; }}
.cover-slide {{ padding: 64px 72px 36px; position: relative; }}
/* 광택 대각 오버레이(엔바토 흡수 3라운드 7/3) — 순수 CSS 사선 하이라이트, 이미지 불필요. */
.cover-sheen {{
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: linear-gradient(115deg, transparent 38%, color-mix(in srgb, white 22%, transparent) 50%, transparent 62%);
}}
/* 세로 책등 라벨 — 표지 우측 여백에 회전된 짧은 단어(브랜드북 스파인 문법). */
.cover-spine {{
  position: absolute;
  top: 50%;
  right: 28px;
  margin: 0;
  z-index: 2;
  transform: translateY(-50%) rotate(180deg);
  writing-mode: vertical-rl;
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .18em;
  color: var(--muted);
  opacity: .6;
}}
.cover-dark .cover-spine {{ color: rgba(248,250,252,.5); }}
/* 표지 뼈대 "corner" — 텍스트 하단 앵커(에디토리얼/문서 느낌). center 뼈대와 나란한 대안. */
.cover-corner .cover-body {{ justify-content: flex-end; gap: 28px; }}
.cover-corner .cover-lockup h1 {{ font-size: 54px; line-height: 1.14; }}
/* 커버 우상단 작성자 크레딧(후추님 #10) — 절제된 작은 글씨·우측 정렬·타이틀과 비충돌. */
.cover-credit {{
  position: absolute;
  bottom: 56px;
  right: 72px;
  margin: 0;
  z-index: 2;
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .04em;
  color: var(--muted);
}}
.theme-tech .cover-credit {{ right: 96px; }}
.cover-body {{
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 58px;
}}
.cover-lockup {{ max-width: 980px; }}
.cover-eyebrow {{
  margin: 0 0 14px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .08em;
}}
.cover-lockup h1 {{
  margin: 0;
  font-size: 72px;
  line-height: 1.06;
  letter-spacing: 0;
}}
.cover-subtitle {{
  margin: 24px 0 0;
  color: var(--ink);
  font-size: 30px;
  line-height: 1.32;
  word-break: keep-all;
}}
.axis-strip {{
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 10px;
  max-width: 760px;
}}
.axis-strip span {{
  border-top: 4px solid var(--band);
  color: var(--muted);
  padding-top: 12px;
  font-size: 14px;
}}
.axis-strip b {{ color: var(--band); margin-right: 8px; }}
.editorial-axis span {{ min-height: 20px; }}
.cover-circuit-corner {{
  position: absolute;
  top: 48px;
  left: 96px;
  width: 40px;
  height: 40px;
  border-top: 2px solid var(--accent);
  border-left: 2px solid var(--accent);
}}
.cover-health-curve {{
  width: min(760px, 70%);
  height: 92px;
  border: 2px solid var(--accent2);
  border-left: 0;
  border-bottom: 0;
  border-radius: 0 64px 0 0;
  opacity: .62;
}}
.theme-tech.cover-slide {{ padding: 0 96px 40px; }}
.theme-tech .cover-body {{ gap: 0; }}
.theme-tech .cover-lockup {{ max-width: 1020px; }}
.theme-tech .cover-eyebrow {{
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 0 0 26px;
  color: var(--accent);
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .34em;
}}
.theme-tech .cover-eyebrow::before {{
  content: "";
  width: 34px;
  height: 2px;
  background: var(--accent2);
}}
.theme-tech .cover-lockup h1 {{
  font-size: 80px;
  line-height: 1.06;
  font-weight: 850;
}}
.theme-tech .cover-subtitle {{
  margin-top: 26px;
  color: var(--muted);
  font-size: 26px;
  font-weight: 600;
}}
.outro-slide .cover-subtitle {{ max-width: 900px; }}
/* 마지막 장 상단 꺽쇠는 커버에만 어울려 outro에선 제거(후추님 #7). 커버는 유지. */
.outro-slide .cover-circuit-corner {{ display: none; }}
.presenter-contact {{
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: var(--mono-font);
  letter-spacing: .02em;
}}
.presenter-contact .presenter-company {{ color: var(--ink); font-weight: 800; font-size: 18px; letter-spacing: .09em; }}
.presenter-contact .presenter-name {{ color: var(--ink); font-weight: 600; font-size: 15px; }}
.presenter-contact .presenter-email {{ color: var(--muted); font-size: 14px; }}
/* outro: eyebrow+감사 인사 한 묶음(상단~중상단) / 연락처 하단 (후추님 6/30) */
.outro-slide {{ display: flex; flex-direction: column; justify-content: space-between; }}
.outro-main {{ flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: flex-start; gap: 18px; }}
.outro-main .cover-eyebrow {{ margin: 0; }}
.outro-main h1 {{ margin: 0; font-size: 92px; line-height: 1.04; font-weight: 850; }}
.theme-tech .outro-main h1 {{ font-size: 96px; }}
.theme-tech .eyebrow,
.theme-tech .slide-foot {{
  font-family: var(--mono-font);
}}
.theme-tech .eyebrow::before {{ background: var(--accent2); }}
/* (구) marketing/health 카드·콜아웃 코랄/블루 그림자 제거(후추님 7/2) — 반투명 배경 + 그림자가
   그라디언트 위에서 '뒤에 박스가 있는' 얼룩으로 보임. 톤다운 원칙: 깊이감은 보더·여백으로. */
.callout {{ background: color-mix(in srgb, #FFFFFF 88%, var(--c30)); }}
.layout-body {{
  width: 100%;
}}
/* 출처 appendix: 넘버·구분선 없이 "기관 — 리포트명" 한 줄 플랫 리스트(후추님 7/2). data-src-id로 C6 authorized. */
.appendix-list {{ display: flex; flex-direction: column; gap: 10px; width: min(100%, 1090px); }}
.appendix-row {{
  display: flex;
  gap: 14px;
  align-items: baseline;
  white-space: nowrap;
  overflow: hidden;
}}
/* 다출처(>10행) 압축 모드 — 행 간격·폰트 축소로 한 장에 수용. */
.appendix-compact.appendix-body .appendix-list {{ gap: 7px; }}
.appendix-compact .appendix-pub {{ font-size: 13.5px; }}
.appendix-compact .appendix-title {{ font-size: 13px; }}
.appendix-pub {{ flex: none; font-size: 15px; font-weight: 700; color: var(--ink); }}
.appendix-title {{ min-width: 0; overflow: hidden; text-overflow: ellipsis; font-size: 14px; color: var(--muted); }}
.appendix-link {{ color: inherit; text-decoration: none; border-bottom: 1px solid color-mix(in srgb, var(--muted) 40%, transparent); }}
.verified-badge {{ display: inline-block; margin-top: 8px; padding: 4px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 600; color: var(--accent); border: 1px solid color-mix(in srgb, var(--accent) 45%, transparent); background: color-mix(in srgb, var(--accent) 8%, transparent); }}
/* split 외곽: 부제 전폭 + 그 아래 2단 그리드(후추님 7/2 — 부제는 제목 아래 일반 양식과 통일). */
.split-outer {{
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 14px;
}}
.split-outer .block-title {{ margin: 0; }}
/* 부제가 전폭으로 올라간 만큼 칸 안 요소는 낮게 — 카드 축소·칸 내 간격 압축. */
.split-pane .metric-card {{ min-height: 132px; padding: 18px; }}
.split-pane .metric-card .metric-value {{ font-size: 48px; }}
.split-pane {{ gap: 16px; }}
.split-body {{
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
  /* 상단 정렬 — 키 다른 두 칸이 중앙 정렬로 어긋나 보이던 문제(후추님 7/2). 차트 제목 라인이 맞는다. */
  align-items: start;
}}
/* 비대칭 split(드리블 흡수 2라운드) — 주 비주얼 쪽을 넓게. */
.split-body.split-wide-left {{ grid-template-columns: 1.7fr 1fr; }}
.split-body.split-wide-right {{ grid-template-columns: 1fr 1.7fr; }}
/* hero_metric — 숫자가 곧 비주얼인 전면장(드리블 초대형 타이포 문법의 수치 버전). */
.hero-body {{ justify-content: center; gap: 10px; }}
.hero-stage {{ display: flex; flex-direction: column; gap: 8px; max-width: 980px; }}
.hero-stage .metric-card {{ border: 0; background: transparent; padding: 0; min-height: 0; }}
.hero-stage .metric-label {{ font-size: 26px; font-weight: 800; color: var(--ink); }}
.hero-stage .metric-value {{ font-size: 210px; line-height: .96; letter-spacing: -.02em; }}
.hero-stage .callout {{ max-width: 720px; }}
/* 보조 카드/note/citation 열 — hero-stage(초대형)와 분리, 정상 크기 유지(7/3 fix). */
.hero-row {{ display: flex; align-items: flex-start; gap: 22px; flex-wrap: wrap; max-width: 980px; }}
.hero-row .metric-card {{ max-width: 320px; }}
.split-pane {{
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 22px;
}}
.split-primary {{
  padding-right: 46px;
  border-right: 1px solid var(--line);
}}
.split-secondary {{ padding-left: 2px; }}
/* 단일 비주얼 split — 구분선 없는 1단(우측 빈 칸에 세로선만 긋던 어색함 제거).
   비주얼이 전폭으로 벌어져 하단 note와 겹치지 않게 폭을 제한하고 좌측 정렬. */
.split-body.split-single {{ grid-template-columns: minmax(0, 680px); justify-content: start; }}
.split-solo {{ padding-right: 0; border-right: none; }}
.stepper-body {{ justify-content: center; }}
.stepper-track {{
  counter-reset: step;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 22px;
  align-items: stretch;
}}
/* 스텝퍼 카드 안 callout/metric = 카드 속 카드(이중 박스) 방지 — 박스 벗기고 내용만(후추님 7/2 p11 #04 · 7/3 테크 p15 #02). */
.stepper-item .metric-card {{
  border: 0;
  background: transparent;
  padding: 0;
  min-height: 0;
  border-radius: 0;
}}
/* matrix 셀 안 metric = 카드 속 카드 방지(스텝퍼와 동일 문법) — 셀의 스탯 행으로 평탄화. */
.matrix-cell .metric-grid {{ margin-top: 14px; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); }}
.matrix-cell .metric-card {{
  border: 0;
  background: transparent;
  padding: 0;
  min-height: 0;
}}
.matrix-cell .metric-value {{ font-size: 44px; }}
.stepper-item .callout {{
  border-left: 0;
  background: transparent;
  border-radius: 0;
  padding: 0;
  margin-top: 0;
  font-weight: 800;
  box-shadow: none !important;
}}
.stepper-item {{
  counter-increment: step;
  position: relative;
  min-height: 180px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
  padding: 58px 22px 22px;
}}
.stepper-item::before {{
  content: counter(step, decimal-leading-zero);
  position: absolute;
  top: 20px;
  left: 22px;
  color: var(--accent);
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 900;
  letter-spacing: .16em;
}}
/* 넘버 옆 가로선(::after) 제거 — 카드 테두리+선 4개 = 선 과다(후추님 7/3 테크 p15). */
.node-body {{ justify-content: center; }}
.node-map {{
  position: relative;
  display: grid;
  grid-template-columns: minmax(280px, .85fr) minmax(0, 1.4fr);
  gap: 44px;
  align-items: center;
}}
.node-core,
.node-branch {{
  position: relative;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--card);
  padding: 24px;
}}
.node-core {{
  border-color: var(--accent);
  border-left-width: 5px;
}}
.node-branches {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}}
.node-branch::before {{
  content: "";
  position: absolute;
  left: -18px;
  top: 50%;
  width: 18px;
  border-top: 1px solid var(--line);
}}
.matrix-body {{ justify-content: center; }}
.matrix-subhead {{ margin: 0 0 18px; }}
.matrix-subhead .block-title {{ margin: 0; font-size: 20px; }}
.matrix-grid {{
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: hidden;
  background: var(--card);
}}
.matrix-cell {{
  min-height: 150px;
  padding: 22px;
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}}
.matrix-cell:nth-child(2n) {{ border-right: 0; }}
.matrix-cell:nth-last-child(-n+2) {{ border-bottom: 0; }}
.matrix-cell-label {{ font-size: 18px; font-weight: 800; color: var(--accent); margin: 0 0 8px; letter-spacing: .01em; }}
.matrix-cell-copy {{ font-size: 16px; line-height: 1.5; color: var(--ink); word-break: keep-all; }}
.index-body {{ justify-content: center; }}
.index-list {{
  counter-reset: index;
  display: grid;
  gap: 0;
  width: min(100%, 980px);
}}
.index-row {{
  counter-increment: index;
  display: grid;
  grid-template-columns: 128px minmax(112px, .35fr) minmax(0, 1fr);
  gap: 24px;
  align-items: center;
  min-height: 74px;
  border-top: 1px solid var(--line);
  padding: 15px 0;
}}
.index-row:last-child {{ border-bottom: 1px solid var(--line); }}
.index-row::before {{
  content: counter(index, decimal-leading-zero);
  color: var(--accent);
  font-family: var(--mono-font);
  /* 넘버링 오브제(드리블 흡수 2라운드) — 번호가 장식이 아니라 오브제. 크기 위계 과감하게. */
  font-size: 64px;
  font-weight: 900;
  line-height: 1;
  opacity: .92;
}}
.index-part {{
  color: var(--ink);
  font-size: 26px;
  font-weight: 900;
  line-height: 1.1;
  word-break: keep-all;
}}
.index-copy {{
  color: var(--muted);
  font-size: 19px;
  font-weight: 700;
  line-height: 1.46;
  word-break: keep-all;
}}
.layout-closing.slide {{
  padding: 84px 96px 0;
}}
.layout-closing .slide-head {{
  max-width: 1040px;
}}
.layout-closing .eyebrow {{
  color: var(--accent);
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .3em;
}}
.layout-closing .eyebrow::before {{
  width: 34px;
  background: var(--accent2);
}}
/* closing 전용 .eyebrow color 재정의가 칩(.eyebrow-chip)의 흰 글자색을 덮어써 배경(accent)과
   같은 색이 되어 텍스트가 안 보이던 버그(7/3 실측 발견 — p14 "CLOSING" 칩 빈 도형으로 보임). */
.layout-closing .eyebrow.eyebrow-chip {{ color: #FFFFFF; }}
.layout-closing .slide-head h1 {{
  margin-top: 18px;
  max-width: 1040px;
  font-size: 46px;
  line-height: 1.18;
  font-weight: 850;
}}
.closing-body {{
  justify-content: flex-start;
  gap: 0;
  padding: 54px 0 92px;
}}
.closing-points {{
  display: flex;
  flex-direction: column;
  gap: 0;
  width: min(100%, 1010px);
}}
.closing-point {{
  display: grid;
  grid-template-columns: 212px minmax(0, 1fr);
  gap: 30px;
  align-items: baseline;
  margin-bottom: 28px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--line);
}}
.closing-point:last-child {{
  border-bottom: 0;
  margin-bottom: 0;
}}
.closing-label {{
  color: var(--accent);
  font-size: 21px;
  font-weight: 800;
  line-height: 1.25;
  word-break: keep-all;
}}
.closing-copy {{
  color: var(--ink);
  font-size: 23px;
  font-weight: 500;
  line-height: 1.5;
  word-break: keep-all;
}}
/* 펀치라인 = 마지막 임팩트. 크게·액센트·여백 확보(후추님 #3). 위 3행은 받침. */
.closing-callout {{
  margin: 30px 0 0;
  max-width: 1080px;
  border-left: 6px solid var(--accent2);
  padding-left: 28px;
  color: var(--ink);
  font-size: 38px;
  font-weight: 900;
  line-height: 1.3;
  letter-spacing: -.01em;
  word-break: keep-all;
}}
.layout-closing .slide-foot {{
  position: absolute;
  left: 96px;
  right: 96px;
  bottom: 40px;
  margin-top: 0;
  font-family: var(--mono-font);
}}
.layout-divider .slide-head {{ display: none; }}
/* 간지 배경 = 테마 잉크색 파생(글로우는 테마 액센트) — 네이비 하드코딩이 웜 테마 본문과
   부조화하던 문제의 근본 풀이(후추님 7/2 마케팅 덱 지적). 테크 잉크는 기존 네이비와 근사. */
.layout-divider.slide {{
  background:
    radial-gradient(circle at 84% 28%, color-mix(in srgb, var(--accent) 22%, transparent) 0, transparent 36%),
    linear-gradient(140deg, color-mix(in srgb, var(--ink) 90%, white) 0%, var(--ink) 62%, color-mix(in srgb, var(--ink) 82%, black) 100%);
  color: #F8FAFC;
}}
/* accent 풀블리드 간지(드리블 흡수 2라운드 — 컬러 블록 리듬): 잉크 파생 대신 테마색 전면.
   4~6장마다 색 리듬 전환용 레버(divider_variant:"accent") — 기본값은 여전히 잉크 파생. */
.layout-divider.slide.divider-accent {{
  background:
    radial-gradient(circle at 84% 28%, color-mix(in srgb, white 16%, transparent) 0, transparent 38%),
    linear-gradient(140deg, color-mix(in srgb, var(--divider-accent) 92%, white) 0%, var(--divider-accent) 58%, color-mix(in srgb, var(--divider-accent) 78%, black) 100%);
  color: var(--divider-accent-fg);
}}
.divider-accent .divider-title {{ color: var(--divider-accent-fg); }}
.divider-accent .divider-subtitle {{ color: color-mix(in srgb, var(--divider-accent-fg) 74%, transparent); }}
.divider-accent .divider-part {{ color: color-mix(in srgb, var(--divider-accent-fg) 82%, transparent); }}
.divider-accent .divider-progress span.is-active {{ background: var(--divider-accent-fg); }}
/* 초대형 타이포 오브제(드리블 흡수 2라운드): 제목이 화면 절반 — 이 장엔 차트·장식 금지.
   레버 hero_title:true, 간지·전환 장에서 한 단어급 제목과 함께 쓴다. */
.divider-hero .divider-title {{ font-size: 168px; line-height: .98; letter-spacing: -.02em; }}
.divider-hero .divider-subtitle {{ font-size: 24px; margin-top: 18px; }}
/* 펩핀치 다크 섹션 = 브랜드 히어로(차콜 #2A2F33) + 오렌지 #FF9B3D 글로우. 표지·맺음. */
.theme-peppinch.cover-slide {{
  background:
    radial-gradient(circle at 85% 24%, rgba(255, 155, 61, .17) 0, transparent 40%),
    linear-gradient(150deg, #32373C 0%, #2A2F33 64%, #23272A 100%);
  color: #F1ECE0;
}}
/* 간지 = 깔끔한 회색(다크 표지·크림 본문 사이 중간 톤). 글로우·그리드 없이 단정하게(후추님 6/30 — 회색 위 글로우가 얼룩처럼). */
.theme-peppinch.layout-divider.slide {{
  background: linear-gradient(165deg, #5A5E63 0%, #4E5257 100%);
  color: #F4F1EA;
}}
/* 테크풍 배경 모티프(간지 원·본문 별자리)는 따뜻한 에디토리얼 톤과 안 맞고 서로 안 어울림 → 제거(후추님 6/30). */
.theme-peppinch .slide-motif,
.theme-peppinch .divider-motif {{ display: none; }}
/* 다크 섹션 강조색 = 오렌지(크림 본문은 레드 유지). */
.theme-peppinch.cover-slide h1 {{ color: #F1ECE0; }}
.theme-peppinch.cover-slide .cover-eyebrow,
.theme-peppinch.cover-slide .presenter-company {{ color: #FF9B3D; }}
.theme-peppinch.cover-slide .cover-subtitle {{ color: rgba(241,236,224,.82); font-size: 22px; line-height: 1.45; margin-top: 20px; }}
/* 부제목은 한 단계 작게·가볍게 = 정제된 위계(후추님 7/1). */
.theme-peppinch .block-title {{ font-size: 20px; font-weight: 600; }}
/* 간지 헤드라인은 본문 제목(44px)보다 작게 — 섹션 마커가 본문보다 크면 위계 뒤집힘(후추님 7/1). */
.theme-peppinch .divider-title {{ font-size: 40px; }}
.theme-peppinch.cover-slide .cover-credit,
.theme-peppinch.cover-slide .presenter-email {{ color: rgba(241,236,224,.6); }}
.theme-peppinch.cover-slide .presenter-name {{ color: #F1ECE0; }}
/* 회로망 그리드·레이더 링 = 테크 은유 — 테크 테마 전용으로 격리(7/2). 타 테마 간지는
   잉크 다크 + 액센트 글로우만(주제 무관 은유 복붙 금지·visualization.md C). */
.theme-tech.layout-divider::after {{
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.055) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.055) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(90deg, transparent 0%, black 16%, black 82%, transparent 100%);
  pointer-events: none;
}}
.slide:not(.theme-tech) .divider-motif {{ display: none; }}
.layout-divider .slide-foot {{
  z-index: 1;
  border-top-color: rgba(255,255,255,.16);
  color: rgba(248,250,252,.58);
}}
.divider-body {{
  position: relative;
  z-index: 1;
  justify-content: center;
  align-items: flex-start;
  gap: 16px;
  min-height: 0;
  padding: 24px 0 8px;
}}
.divider-motif {{
  position: absolute;
  right: 18px;
  top: 50%;
  width: 240px;
  height: 240px;
  transform: translateY(-50%);
  border: 1px solid rgba(248,250,252,.18);
  border-radius: 50%;
  opacity: .72;
}}
.divider-motif::before,
.divider-motif::after {{
  content: "";
  position: absolute;
  inset: 38px;
  border: 1px solid rgba(248,250,252,.14);
  border-radius: 50%;
}}
.divider-motif::after {{ inset: 82px; }}
.divider-progress {{
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
}}
.divider-progress span {{
  width: 42px;
  height: 4px;
  background: rgba(248,250,252,.22);
}}
.divider-progress .is-active {{ background: var(--accent2); }}
.divider-part {{
  margin: 0;
  color: var(--accent2);
  font-family: var(--mono-font);
}}
.divider-part::before {{ background: var(--accent2); }}
.divider-eyebrow {{
  margin: 0;
  color: rgba(248,250,252,.64);
}}
.divider-eyebrow::before {{ background: rgba(248,250,252,.35); }}
.divider-title {{
  margin: 8px 0 0;
  max-width: 900px;
  color: #F8FAFC;
  font-size: 72px;
  line-height: 1.08;
  letter-spacing: 0;
  word-break: keep-all;
  position: relative;
  z-index: 1;
}}
/* 조용한 간지 뼈대(엔바토 흡수 3라운드 7/3) — 진척바·PART접두어·불릿 없이 거대 숫자+라벨 한 줄. */
.divider-quiet {{ justify-content: center; gap: 8px; }}
.divider-quiet .divider-part {{ margin: 0; }}
.divider-quiet-num {{
  font-family: var(--mono-font);
  font-weight: 300;
  font-size: 168px;
  line-height: 1;
  color: color-mix(in srgb, #F8FAFC 46%, transparent);
  margin: 4px 0 0;
}}
.divider-quiet .divider-title {{ font-size: 52px; margin-top: 4px; }}
/* 고스트 배경 타이포 — 파트 라벨을 초대형·투명하게 깔아 여백을 타이포로 채운다. */
.divider-ghost {{
  position: absolute;
  right: -4%;
  bottom: 14%;
  z-index: 0;
  font-size: 240px;
  font-weight: 900;
  line-height: .8;
  letter-spacing: -.03em;
  color: color-mix(in srgb, white 8%, transparent);
  white-space: nowrap;
  pointer-events: none;
  word-break: keep-all;
}}
.divider-subtitle {{
  margin: 4px 0 0;
  max-width: 820px;
  color: rgba(248,250,252,.70);
  font-size: 24px;
  line-height: 1.42;
  word-break: keep-all;
}}
/* 간지 하위 목차 프리뷰(author-style §5) — "이 파트에서 볼 것" 짧은 리스트. */
.divider-items {{
  margin: 26px 0 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 12px;
}}
.divider-items li {{
  position: relative;
  padding-left: 24px;
  color: rgba(248,250,252,.78);
  font-size: 19px;
  word-break: keep-all;
}}
.divider-items li::before {{
  content: "";
  position: absolute;
  left: 0;
  top: .62em;
  width: 12px;
  height: 2px;
  background: var(--accent2);
}}
.visual-card {{
  width: min(100%, 1040px);
  border-top: 1px solid var(--line);
  padding-top: 16px;
  margin: 8px 0 6px;  /* 차트 위아래 약간의 숨 (후추님 6/30 — 조금씩·dense 슬라이드 안 넘치게) */
}}
.visual-card svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
/* statement(상하 전폭) flow — SVG가 전폭 비율로 부풀어 세로가 터지는 것 방지(7/3 p04·p05). */
.body:not(.layout-body) > .visual-card {{ width: min(100%, 820px); }}
.body:not(.layout-body) > .metric-card {{ max-width: 460px; }}
/* stack 컴포지션 — 전폭 차트도 세로 비율이 안 터지게 상한. */
.stack-outer > .visual-card {{ width: min(100%, 760px); }}
.stack-row {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 22px;
  align-items: stretch;
  margin-top: 14px;
}}
.stack-row .metric-card {{ min-height: 0; }}
/* 하단 행 박스 키 맞춤(후추님 7/4 p07): metric-grid가 stretch로 늘어도 안쪽 카드가 안 늘어 빈 공간이
   생기던 것 — 카드/그리드를 100%로 채워 note 박스와 밑선을 맞춘다. */
.stack-row .metric-grid {{ height: 100%; }}
.stack-row .metric-grid .metric-card {{ height: 100%; }}
/* 3장 이상 grid가 stack-row 한 열에 끼면 3번째 카드가 줄바꿈→슬라이드 밖 잘림(7/5 레버1 e2e p05 실측).
   3+장은 전폭 행으로 — 2장 grid는 note 박스 나란히(7/4) 규칙 유지. */
.stack-row .metric-grid:has(> .metric-card:nth-child(3)) {{ grid-column: 1 / -1; height: auto; }}
.visual-card text {{
  font-family: var(--font-chart, "Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif);
  letter-spacing: 0;
}}
/* editorial_serif — 차트도 팔레트 스와핑에 그치지 않게: 막대/필 모서리를 각지게(rx 0), 수치 조판을
   세리프로 바꿔 "기술 대시보드 각바" 관례에서 이탈시킨다(후추님 7/3 "결국 컬러 변경된거고 구성은 그대로" 지적). */
.theme-editorial-serif rect {{ rx: 0; ry: 0; }}
.theme-editorial-serif {{ --font-chart: var(--font-head); }}
/* 그리드/컴포지션 레벨 변주(후추님 7/3 "레이아웃 전체를 변경해서 다양해 보이는거") — 토큰(폰트·카드·
   차트모서리)만으로는 "테두리만 없앤 버전"으로 읽힘. 제본선 여백·분할비율까지 바꿔 지면 골격 자체를 바꾼다. */
.theme-editorial-serif.slide {{
  padding: 56px 80px 36px 104px;
  border-left: 1px solid color-mix(in srgb, var(--ink) 14%, transparent);
}}
.theme-editorial-serif .split-body {{ grid-template-columns: 1.35fr 1fr; gap: 64px; align-items: center; }}
/* 세리프 split은 상단 정렬 대신 세로 중앙 — 키 차이 나는 두 칸에서 짧은 쪽 아래 구멍이
   "중간 여백 어색"으로 읽히던 문제(후추님 7/4 p14). 차트 제목 라인 정합(7/2)은 카드형 테마 유지. */
/* 그리드 리팩터 2차(7/3 "레이아웃 전체를 변경해서 다양해 보이는거" — 후추님 확인) — 토큰·분할비율까지
   손댄 1차로도 "테두리만 없앤 버전"이라 재지적. 이번엔 제목 앵커·거대숫자 위치·콜아웃 문법 자체를 바꾼다. */
/* (1) 제목 앵커 — 우측 마스트헤드로 뒤집었었으나(2차) 후추님 실물 판정(7/4 크리에이터 덱)
   "우측 쏠림이 예쁘지 않음·좌측이 맞다" → 좌측 정렬 원복(정렬 축 폐기). 세리프 차별화는
   서체·제본선·풀쿼트·블리드 간지 넘버가 담당. 크기 50px(7/3 "조금만 더")·상자 해제는 유지. */
.theme-editorial-serif .slide-head h1 {{ max-width: none; font-size: 50px; }}
/* (2) 간지 거대숫자 — 인라인 흐름(제목 위 한 줄)에서 빼내 우하단에 블리드하는 배경 넘버로.
   tech·기본 뼈대는 좌측 인라인 숫자라 "같은 자리"였던 것을 위치 자체로 이탈. */
.theme-editorial-serif .divider-quiet {{ justify-content: flex-start; padding-top: 72px; }}
.theme-editorial-serif .divider-quiet-num {{
  position: absolute;
  right: 64px;
  bottom: 40px;
  font-size: 320px;
  font-weight: 200;
  z-index: 0;
}}
.theme-editorial-serif .divider-quiet .divider-part,
.theme-editorial-serif .divider-quiet .divider-title,
.theme-editorial-serif .divider-quiet .divider-subtitle {{ position: relative; z-index: 1; }}
/* (3) 콜아웃 — "테두리만 벗긴 카드"가 아니라 각주형 인용부호 없이 세로 룰선 하나로 본문에 녹인다
   (러닝텍스트형 풀쿼트). metric-card 그리드는 이번 라운드 스코프 밖(별도 승인 필요 — 진입점 참고). */
.theme-editorial-serif .callout {{
  border-left: none;
  background: transparent;
  border-radius: 0;
  padding: 4px 0 4px 28px;
  position: relative;
  font-style: italic;
  font-family: var(--font-head);
}}
.theme-editorial-serif .callout::before {{
  content: "";
  position: absolute;
  left: 0;
  top: .15em;
  bottom: .15em;
  width: 2px;
  background: var(--accent);
}}
/* 그리드 리팩터 3차(7/3 "스코프 밖으로 남긴것들 진행") — 이전 라운드에 미룬 두 항목 처리. */
/* (4) metric-card — .metric-grid/.split-pane 컨텍스트(다수 카드 나열)만 한정. hero-stage·
   stepper-item은 이미 테마 무관 자체 오버라이드로 박스를 벗겨뒀으니 손대지 않는다(중복·충돌 방지).
   "테두리만 벗긴 카드"가 되지 않게 카드 자체를 없애고 hairline 세로 구분선으로 잇는 러닝 스탯 문법. */
.theme-editorial-serif .metric-grid .metric-card,
.theme-editorial-serif .split-pane .metric-card {{
  border: none;
  background: transparent;
  border-radius: 0;
  border-left: 1px solid color-mix(in srgb, var(--ink) 18%, transparent);
  padding-left: 22px;
}}
.theme-editorial-serif .metric-grid .metric-card:first-child,
.theme-editorial-serif .split-pane .metric-card:first-child {{
  border-left: none;
  padding-left: 0;
}}
.theme-editorial-serif .metric-value {{ font-family: var(--font-head); }}
.theme-editorial-serif .metric-label {{ font-style: italic; }}
/* 카드리스 러닝스탯 — 카드 시절 잔재(min-height 170px·padding 24px·accent 윗줄 3px)를 전부 벗긴다.
   grid/split-pane 밖 맨몸 metric이 24px 인덴트+마룬 윗줄을 달고 나와 좌측 정렬이 어긋나던 문제
   (후추님 7/4 크리에이터 p12 실측). hairline 구분선은 grid/split-pane 규칙이 다시 입힌다. */
.theme-editorial-serif .metric-card {{
  min-height: 0;
  padding: 0;
  border: none;
  background: transparent;
  border-radius: 0;
}}
/* 저밀도 페이지에서 마지막 행이 중간에 떠서 페이지마다 정렬이 달라 보이던 문제(후추님 7/4 p05 —
   "다른 페이지는 하단에 붙는데 여긴 상단부터") — stack 마지막 행을 하단 앵커로 통일. */
.theme-editorial-serif .stack-outer > .stack-row:last-child {{ margin-top: auto; }}
/* stack 차트 폭 상한은 기본 테마(760) 기준 — 세리프는 제본 여백만큼 콘텐츠 폭이 좁아 같은 SVG가
   세로를 더 먹는다(7/3 p04 -20px 실측). 테마 상한 하향. */
.theme-editorial-serif .stack-outer > .visual-card {{ width: min(100%, 680px); }}
/* (5) 커버 제목 앵커 — 본문 좌측 원복(7/4)에 맞춰 표지도 좌측 기본으로(마스트헤드 축 폐기). */
.visual-title {{ fill: var(--ink); font-size: 23px; font-weight: 900; }}
.visual-note {{ fill: var(--muted); font-size: 17px; font-weight: 500; }}
/* 막대 설명 라벨은 받침 — 일반 굵기로 낮춰 헤더·값만 도드라지게(후추님 #6). */
.visual-label {{ fill: var(--ink); font-size: 20px; font-weight: 500; }}
.visual-value {{ fill: var(--ink); font-size: 28px; font-weight: 900; }}
.visual-value-accent {{ fill: var(--accent); font-size: 35px; font-weight: 900; }}
/* 델타 주석(전·후 변화량·×N 브래킷) — 렌더러 계산값. accent2로 값과 위계 분리. */
.visual-delta {{ fill: var(--accent2); font-size: 22px; font-weight: 900; }}
.visual-fo-label {{
  color: var(--ink);
  font-family: "Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 20px;
  font-weight: 800;
  line-height: 1.34;
  word-break: keep-all;
}}
/* split 좁은 칸 안의 차트는 SVG가 ~0.55배 축소되므로 텍스트를 보정해 키운다 */
.split-pane .visual-title {{ font-size: 32px; }}
.split-pane .visual-note {{ font-size: 25px; }}
.split-pane .visual-label {{ font-size: 29px; }}
.split-pane .visual-value {{ font-size: 40px; }}
.split-pane .visual-value-accent {{ font-size: 48px; }}

/* ══ 파일럿 2: data_mono — 모노스페이스 데이터형(후추님 7/3 방향 승인) ══
   editorial_serif에서 검증된 층 순서 재사용: 토큰(폰트·카드·차트) → 그리드(제목 앵커·간지
   문법·콜아웃/메트릭 문법). 방안지 지면은 팔레트 slide_bg가 담당. */
/* 토큰층: 각진 차트 + 모노 수치 조판 */
.theme-data-mono rect {{ rx: 0; ry: 0; }}
.theme-data-mono {{ --font-chart: var(--font-head); }}
/* 그리드층 (1) 제목 앵커 = 스펙시트 헤더 — 전폭 룰선 아래 제목, eyebrow는 사각 마커.
   기존(룰선 없는 좌상단)·세리프(우측 마스트헤드)와 다른 세 번째 문법. */
.theme-data-mono .slide-head {{ border-bottom: 2px solid var(--ink); padding-bottom: 8px; }}
/* 40px는 outro 72px 대비 왜소(후추님 7/3) → 46px. 커진 +7px는 헤더 밑 패딩(16→8)에서
   회수 — 빠듯한 페이지들(p02/p05/p15)이 3~7px씩 넘치던 것 실측·해소. 제목은 전 페이지 한 줄. */
.theme-data-mono .slide-head h1 {{ font-size: 46px; font-weight: 700; letter-spacing: -.02em; max-width: none; }}
.theme-data-mono .eyebrow {{ font-family: var(--mono-font); letter-spacing: .3em; }}
.theme-data-mono .eyebrow::before {{ width: 10px; height: 10px; background: var(--accent); }}
/* 그리드층 (2) 간지 거대숫자 = 아웃라인(스트로크) 넘버 — 기본(채운 좌측 인라인)·세리프(우하단
   블리드)와 다른 세 번째 자리/질감. 다크 간지 위 흰 윤곽선. */
.theme-data-mono .divider-quiet-num {{
  font-weight: 700;
  font-size: 220px;
  color: transparent;
  -webkit-text-stroke: 2px rgba(248,250,252,.55);
}}
/* 다크 간지에도 방안지 정체성 유지 — 테크 회로그리드(마스크·72px)와 달리 24px 균일 눈금.
   시스템 시그니처의 연속이지 테크 은유 복붙이 아님(7/2 격리 원칙과 구분). */
.theme-data-mono.layout-divider::after {{
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(248,250,252,.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(248,250,252,.05) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
}}
/* 그리드층 (3) 콜아웃 = 전연 실선 박스(도면 주기·radius 0) — 기본(액센트 좌변 카드)·세리프
   (박스 없는 이탤릭 풀쿼트)와 다른 세 번째 문법. */
.theme-data-mono .callout {{
  border: 1px solid var(--ink);
  border-left: 1px solid var(--ink);
  background: transparent;
  border-radius: 0;
  padding: 16px 22px;
}}
/* 메트릭 = 계기 판독값 — 모노 숫자·라벨 소형 모노 트래킹, 박스는 얇은 전연 1px. */
.theme-data-mono .metric-card {{
  border: 1px solid var(--line);
  border-top: 1px solid var(--line);
  background: transparent;
  border-radius: 0;
}}
.theme-data-mono .metric-value {{ font-family: var(--font-head); font-weight: 700; }}
.theme-data-mono .metric-label {{ font-family: var(--mono-font); font-size: 12px; letter-spacing: .12em; }}
/* 불릿 마커 = 사각 틱(기본 가로선·세리프 상속과 구분) */
.theme-data-mono .bullet-list li::before {{ width: 8px; height: 8px; top: .5em; }}
.theme-data-mono .stack-outer > .visual-card {{ width: min(100%, 656px); }}
.theme-data-mono .divider-items li::before {{ width: 8px; height: 8px; top: .5em; }}
/* 위 콜아웃/메트릭 박스 규칙이 전역 "카드 속 카드 방지" 리셋(.stepper-item·.hero-stage)을
   소스 순서로 덮어써 이중박스 재발(후추님 7/3 p15 실측 — 스텝 02·04 박스 속 박스). 재리셋. */
.theme-data-mono .stepper-item .callout,
.theme-data-mono .stepper-item .metric-card,
.theme-data-mono .hero-stage .metric-card {{
  border: 0;
  background: transparent;
  padding: 0;
}}

/* ══ 파일럿 3: dark_premium — 전면 다크(레퍼런스 흡수·_grammar/dark_premium.md 공통 문법만) ══ */
/* 무독 1: 본문은 순백 아닌 눌린 회색 — 제목(밝음)과의 명도 대비가 위계. */
.theme-dark-premium .body-text,
.theme-dark-premium .bullet-list li,
.theme-dark-premium .closing-copy {{ color: var(--muted); }}
.theme-dark-premium .block-title {{ color: color-mix(in srgb, var(--ink) 78%, transparent); }}
/* depth 레이어링: 카드 = 바탕+1단 밝은 면(팔레트 card)·라운드. 액센트 윗줄은 다색 유혹이라 제거. */
.theme-dark-premium .metric-card {{
  border: 1px solid rgba(255,255,255,.08);
  border-top: 1px solid rgba(255,255,255,.08);
  background: var(--card);
  min-height: 120px;
  padding: 20px;
}}
.theme-dark-premium .callout {{ background: var(--card); border-left-color: var(--accent); }}
/* 무독 3: 액센트(골드) 칩 위 글자는 밝은색 반전 금지 — 어두운 잉크로 스왑(navy-on-navy 동종 선제). */
.theme-dark-premium .eyebrow.eyebrow-chip {{ color: #14130E; }}
/* 무독 2: 다크 차트 — 비교군 트랙/보조 요소의 명도 하한을 배경 대비로 확보(라이트 램프가 묻힘). */
.theme-dark-premium .visual-card rect[fill="#E2E8F0"],
.theme-dark-premium .visual-card rect[fill="#E7EBEF"] {{ fill: rgba(255,255,255,.16); }}
.theme-dark-premium .visual-note {{ fill: var(--muted); }}
.theme-dark-premium .visual-card {{ border-top-color: rgba(255,255,255,.14); }}
/* 간지: 잉크 파생 그라디언트가 밝은 ink에 오염되지 않게 명시 다크 + 골드 글로우. */
.theme-dark-premium.layout-divider.slide {{
  background:
    radial-gradient(circle at 84% 24%, rgba(198,161,91,.12) 0, transparent 40%),
    linear-gradient(140deg, #1A1B1F 0%, #101114 60%, #0A0B0D 100%);
}}
/* 표지·outro도 동일 다크(이 시스템은 전면 다크라 별도 dark variant 불필요). 부제는 눌린 회색. */
.theme-dark-premium .cover-subtitle {{ color: var(--muted); }}
.theme-dark-premium .slide-foot {{ color: rgba(242,239,231,.45); }}
/* 제목: 헤비 + 넓은 트래킹(올캡 관례의 한글 번안 — 자간·무게로 프리미엄 스케일). */
.theme-dark-premium .slide-head h1 {{ font-weight: 800; letter-spacing: .01em; }}
/* stack 차트 세로 예산(-7px 실측) — 폭 상한 하향. */
.theme-dark-premium .stack-outer > .visual-card {{ width: min(100%, 680px); }}

/* ══ 파일럿 4: minimal_typo — 미니멀 타이포(레퍼런스 흡수·_grammar/minimal_typo.md B형 방언) ══ */
/* 핵심 파라미터 = 서체가 아니라 위계비: 헤드 크게·얇게, 본문은 캡션급 초소형. */
.theme-minimal-typo .slide-head h1 {{ font-size: 58px; font-weight: 350; letter-spacing: -.01em; max-width: none; line-height: 1.12; }}
.theme-minimal-typo .body-text {{ font-size: 15px; line-height: 1.7; max-width: 640px; }}
.theme-minimal-typo .bullet-list li {{ font-size: 15px; line-height: 1.6; }}
.theme-minimal-typo .block-title {{ font-size: 17px; font-weight: 600; color: var(--ink); }}
/* 키커 라벨: 초소형·자간 극대(공통 5/8). */
.theme-minimal-typo .eyebrow {{ font-size: 10px; letter-spacing: .4em; font-weight: 700; }}
.theme-minimal-typo .eyebrow::before {{ width: 18px; height: 1px; }}
/* 무장식 원칙: 여백·룰이 장식. 마진을 전 테마 최대로. */
.theme-minimal-typo.slide {{ padding: 56px 96px 40px; }}
.theme-minimal-typo .stack-outer > .visual-card {{ width: min(100%, 660px); }}
.theme-minimal-typo .slide-motif {{ display: none; }}
/* 빅넘버 스탯(공통 5/8) — 카드 벗기고 숫자 자체가 블록. 오프셋 컬러블록(B형 서명)을 뒤에 깐다. */
.theme-minimal-typo .metric-card {{
  border: none;
  background: transparent;
  border-radius: 0;
  padding: 14px 18px;
  min-height: 0;
  position: relative;
  /* 오프셋 블록(-10px 우하)이 컨테이너를 삐져나가 가로 오버플로 나던 것 — 마진으로 자리 확보. */
  margin: 0 10px 10px 0;
}}
.theme-minimal-typo .metric-card::before {{
  content: "";
  position: absolute;
  inset: 10px -10px -10px 10px;
  background: color-mix(in srgb, var(--accent) 10%, transparent);
  z-index: -1;
}}
.theme-minimal-typo .metric-value {{ font-size: 76px; font-weight: 300; letter-spacing: -.02em; }}
.theme-minimal-typo .metric-label {{ font-size: 12px; letter-spacing: .12em; }}
/* 콜아웃: 박스·마커 전부 제거 — 큰 글자 한 줄이 곧 콜아웃(덜어냄이 정체성). */
.theme-minimal-typo .callout {{
  border: none;
  background: transparent;
  border-radius: 0;
  padding: 0;
  font-size: 21px;
  font-weight: 600;
  line-height: 1.55;
}}
.theme-minimal-typo .callout-lead {{ font-size: 27px; font-weight: 700; }}
/* 스텝퍼·매트릭스 셀 오프셋 블록 중첩 방지 — 셀 안에선 오프셋 제거. */
.theme-minimal-typo .stepper-item .metric-card::before,
.theme-minimal-typo .matrix-cell .metric-card::before {{ display: none; }}
/* 차트: 단색 최소 — 보조·트랙 요소 명도 낮추고 각진 얇은 인상은 유지하지 않음(B형은 부드러움). */
.theme-minimal-typo .visual-title {{ font-size: 19px; font-weight: 700; }}
/* 표지도 얇은 위계 일관 + 클로징 바는 1액센트 원칙(accent2 금지). */
.theme-minimal-typo .cover-lockup h1 {{ font-weight: 350; letter-spacing: -.01em; }}
.theme-minimal-typo .closing-callout {{ border-left-color: var(--accent); }}

/* ══ 시그니처 페이지 골격(2026-07-04 페이지 아키텍처 파일럿) — 테마가 아니라 몸이 다르다 ══ */
/* poster: 표준 head 없음(간지와 같은 방식) — 한 문장이 지면 전체. */
.layout-poster .slide-head {{ display: none; }}
.poster-body {{ justify-content: center; gap: 26px; }}
.poster-kicker {{
  margin: 0;
  color: var(--accent);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: .38em;
}}
.poster-text {{
  margin: 0;
  max-width: 980px;
  font-size: 64px;
  line-height: 1.22;
  font-weight: 700;
  word-break: keep-all;
  font-family: var(--font-head);
}}
.theme-minimal-typo .poster-text {{ font-weight: 320; font-size: 68px; }}
/* hero_bleed: 우측 절반이 블리드 숫자 — 숫자가 곧 페이지. */
.layout-hero-bleed .slide-head {{ display: none; }}
.hero-bleed-body {{ flex-direction: row; align-items: center; gap: 40px; }}
.hero-bleed-copy {{ flex: 1 1 46%; display: flex; flex-direction: column; gap: 18px; min-width: 0; }}
.hero-bleed-stage {{ flex: 1 1 54%; position: relative; align-self: stretch; display: flex; flex-direction: column; justify-content: center; min-width: 0; }}
.hero-bleed-label {{ margin: 0 0 6px; color: var(--muted); font-size: 15px; letter-spacing: .08em; }}
.hero-bleed-num {{
  font-size: 190px;
  line-height: .92;
  font-weight: 850;
  letter-spacing: -.03em;
  color: var(--accent);
  white-space: nowrap;
  transform: translateX(36px);  /* 블리드 — transform은 레이아웃 오버플로를 안 만든다. 단위(%·억원)는 잘리면 안 됨 */
  font-variant-numeric: tabular-nums;
}}
.hero-bleed-num.with-unit {{ font-size: 132px; transform: none; }}
.hero-bleed-unit {{ font-size: 48px; font-weight: 700; letter-spacing: -.01em; margin-left: 10px; }}
.theme-dark-premium .hero-bleed-num {{ text-shadow: 0 0 90px color-mix(in srgb, var(--accent) 30%, transparent); }}
/* magazine_spread: 본문이 칼럼으로 흐르고 풀쿼트가 전폭으로 끊는다. */
.magazine-body {{ gap: 20px; }}
.mag-columns {{ columns: 2; column-gap: 56px; max-width: none; }}
.mag-columns .body-text {{ max-width: none; margin: 0 0 14px; break-inside: avoid; }}
.theme-editorial-serif .mag-columns {{ column-rule: 1px solid color-mix(in srgb, var(--ink) 16%, transparent); }}
.mag-quote-row {{ border-top: 1px solid var(--line); padding-top: 12px; }}
.mag-quote-row .callout {{ max-width: none; font-size: 23px; margin-top: 0; }}
.mag-tail {{ display: flex; gap: 40px; align-items: flex-start; }}
.mag-tail > * {{ flex: 1; min-width: 0; }}
/* dashboard: 페이지 전체가 위젯 타일 격자 — 각 블록이 계기판 한 칸. */
.dash-body {{ gap: 14px; }}
.dash-grid {{
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-auto-rows: minmax(120px, auto);
  gap: 16px;
}}
.dash-tile {{
  border: 1px solid var(--line);
  padding: 16px 18px;
  min-width: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
}}
.dash-tile-wide {{ grid-column: span 2; grid-row: span 2; }}
.dash-tile .metric-card {{ border: 0; background: transparent; padding: 0; min-height: 0; }}
.dash-tile .callout {{ border: 0; background: transparent; padding: 0; margin: 0; font-size: 16px; }}
.dash-tile .visual-card {{ border-top: 0; padding-top: 0; margin: 0; width: 100%; }}
.theme-data-mono .dash-tile {{ background: color-mix(in srgb, #FFFFFF 44%, transparent); }}
/* mosaic_tiles: 사진 없이 색면 타일로 만드는 2:1:1 모자이크. */
.mosaic-body {{ gap: 14px; }}
.mosaic-body .block-title {{ margin: 0; }}
.mosaic-grid {{
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  grid-auto-rows: minmax(88px, 1fr);
  grid-auto-flow: dense;
  gap: 14px;
}}
.mosaic-tile {{
  min-width: 0;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--accent) 14%, transparent);
  background: color-mix(in srgb, var(--accent) 8%, var(--c60));
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}
.mosaic-tile:nth-child(odd) {{ background: var(--c30); }}
.mosaic-tile-large {{ grid-row: span 2; }}
.mosaic-tile-medium {{ grid-column: span 2; }}
.mosaic-tile-small {{ grid-column: span 1; }}
.mosaic-tile .body-text,
.mosaic-tile .bullet-list li {{ font-size: 15px; line-height: 1.45; }}
.mosaic-tile .callout {{ margin: 0; padding: 0; border: 0; background: transparent; font-size: 17px; }}
.mosaic-tile .metric-grid {{ gap: 12px; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); }}
.mosaic-tile .metric-card {{
  border: 0;
  background: transparent;
  padding: 0;
  min-height: 0;
}}
.mosaic-tile .metric-label {{ font-size: 12px; }}
/* 48px는 minmax(88px) 타일에서 하단 잘림(overflow:hidden이라 ovf 검출 사각) — 실측 34px */
.mosaic-tile .metric-value {{ font-size: 34px; }}
.theme-editorial-serif .mosaic-tile {{
  border-color: color-mix(in srgb, var(--ink) 18%, transparent);
  box-shadow: inset 0 1px 0 color-mix(in srgb, #FFFFFF 72%, transparent);
}}
/* split_status: 55/45 상태보고 문법 — 좌측 정성, 우측 정량 칩. */
.split-status-body {{
  display: grid;
  grid-template-columns: minmax(0, 55fr) minmax(260px, 45fr);
  gap: 42px;
  align-items: start;
}}
.split-status-body > .block-title {{ grid-column: 1 / -1; margin: 0; }}
.status-copy {{
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}}
.status-chip-stack {{
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}}
.status-chip {{
  border: 1px solid var(--line);
  border-radius: calc(var(--radius) + 4px);
  background: color-mix(in srgb, var(--card) 76%, transparent);
  padding: 14px 16px;
}}
.status-chip .metric-grid {{ display: flex; flex-direction: column; gap: 12px; }}
.status-chip .metric-card {{
  min-height: 0;
  border: 0;
  background: transparent;
  border-radius: 0;
  padding: 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) max-content;
  gap: 18px;
  align-items: baseline;
}}
.status-chip .metric-label {{ font-size: 13px; line-height: 1.35; }}
.status-chip .metric-value {{ font-size: 30px; line-height: 1; }}
.status-chip .metric-delta {{ grid-column: 1 / -1; margin: 2px 0 0; }}
.theme-data-mono .status-chip .metric-label {{
  font-family: var(--mono-font);
  font-size: 11px;
  letter-spacing: .12em;
  text-transform: uppercase;
}}
/* scenario_cards: headline이 카드를 열고 후속 body/metric류가 카드 안에 착지한다. */
.scenario-body {{ justify-content: center; }}
.scenario-grid {{
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 16px;
  align-items: stretch;
}}
/* 4+1 종합: 앞 카드는 4열 고정, 마지막(종합)은 하단 전폭 — 눕혀서 결론에 무게를 준다. */
.scenario-grid-fixed {{ grid-template-columns: repeat(4, 1fr); grid-auto-rows: minmax(0, auto); }}
.scenario-card-wide {{ grid-column: 1 / -1; }}
.scenario-card {{
  min-width: 0;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: calc(var(--radius) + 8px);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}}
.scenario-card .block-title {{ margin: 0; color: var(--ink); font-size: 20px; }}
.scenario-card-body {{
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}}
.scenario-card .body-text,
.scenario-card .bullet-list li {{ font-size: 15px; line-height: 1.45; }}
.scenario-card .callout {{ margin: 0; padding: 0; border: 0; background: transparent; font-size: 16px; }}
.scenario-card .metric-grid {{ display: flex; flex-direction: column; gap: 12px; }}
.scenario-card .metric-card {{
  min-height: 0;
  border: 0;
  background: transparent;
  border-radius: 0;
  padding: 0;
}}
.scenario-card .metric-value {{ font-size: 46px; }}
.theme-dark-premium .scenario-card,
.theme-pop-dark .scenario-card {{
  border-color: rgba(255,255,255,.1);
  box-shadow: 0 18px 44px rgba(0,0,0,.24);
}}

/* ══ 파일럿 5: pop_dark — 팝 다크(후추님 7/4 스샷 스타일·다색 팝 + 도형 오브제) ══ */
/* 본문은 눌린 회색(다크 공통 문법) + 헤비 제목. */
.theme-pop-dark .body-text,
.theme-pop-dark .bullet-list li,
.theme-pop-dark .closing-copy {{ color: var(--muted); }}
.theme-pop-dark .slide-head h1 {{ font-weight: 850; letter-spacing: -.01em; }}
/* 메트릭 = 컬러 필 블록(스샷의 라운드 블롭 카드) — 카드가 곧 팝 오브제. t램프 순환. */
.theme-pop-dark .metric-card {{
  border: none;
  background: var(--t2);
  min-height: 128px;
  padding: 20px 22px;
}}
.theme-pop-dark .metric-grid .metric-card:nth-child(3n+1) {{ background: var(--t1); }}
.theme-pop-dark .metric-grid .metric-card:nth-child(3n) {{ background: var(--t3); }}
.theme-pop-dark .metric-card .metric-label,
.theme-pop-dark .metric-card .metric-value,
.theme-pop-dark .metric-card .metric-source {{ color: #FFFFFF; }}
.theme-pop-dark .metric-card .metric-delta.up,
.theme-pop-dark .metric-card .metric-delta.down {{ color: rgba(255,255,255,.85); }}
/* 콜아웃 = 필 캡슐. 액센트 칩 위 글자는 어두운 잉크(무독). */
.theme-pop-dark .callout {{ background: var(--card); border-left: 6px solid var(--t3); border-radius: 18px; }}
.theme-pop-dark .eyebrow.eyebrow-chip {{ color: #15120C; }}
/* 표지·간지 = 오렌지 풀블리드 북엔드(스샷 커버 문법) — 다크 본문과 강한 리듬 교차. */
.theme-pop-dark.cover-slide,
.theme-pop-dark.layout-divider.slide {{ background: #E8551A; color: #17120E; }}
.theme-pop-dark.cover-slide h1,
.theme-pop-dark .divider-title {{ color: #17120E; }}
.theme-pop-dark.cover-slide .cover-eyebrow,
.theme-pop-dark .divider-part {{ color: rgba(23,18,14,.72); }}
.theme-pop-dark.cover-slide .cover-subtitle {{ color: rgba(23,18,14,.78); }}
.theme-pop-dark.cover-slide .cover-credit,
.theme-pop-dark.cover-slide .presenter-email {{ color: rgba(23,18,14,.6); }}
.theme-pop-dark.cover-slide .presenter-company,
.theme-pop-dark.cover-slide .presenter-name {{ color: #17120E; }}
.theme-pop-dark .divider-quiet-num {{ color: rgba(23,18,14,.28); font-weight: 850; }}
.theme-pop-dark .divider-subtitle {{ color: rgba(23,18,14,.75); }}
.theme-pop-dark .divider-progress span {{ background: rgba(23,18,14,.25); }}
.theme-pop-dark .divider-progress .is-active {{ background: #17120E; }}
.theme-pop-dark .divider-items li {{ color: rgba(23,18,14,.8); }}
.theme-pop-dark .divider-items li::before {{ background: #17120E; }}
/* outro는 다크 유지(북엔드는 표지·간지만) — 연락처 밝게. */
.theme-pop-dark .slide-foot {{ color: rgba(245,242,236,.45); }}
/* 다크 차트 보정: 라이트 전용 회색 트랙 명도 하한(dark_premium과 동일 클래스). */
.theme-pop-dark .visual-card rect[fill="#E2E8F0"],
.theme-pop-dark .visual-card rect[fill="#E7EBEF"] {{ fill: rgba(255,255,255,.18); }}
.theme-pop-dark .visual-note {{ fill: var(--muted); }}
.theme-pop-dark .visual-card {{ border-top-color: rgba(245,242,236,.16); }}
/* 오렌지 북엔드 위 ==키워드== 강조색(오렌지)이 배경과 동화되던 무독(자동검출 lowc 실검출) — 잉크로. */
.theme-pop-dark.cover-slide .kw,
.theme-pop-dark.layout-divider .kw {{ color: #17120E; text-decoration: underline; text-underline-offset: 6px; }}
.theme-pop-dark .stack-outer > .visual-card {{ width: min(100%, 680px); }}

/* ══ PG-pricing_cards(2026-07-04 승격): 2~4열 플랜/옵션 카드. emphasis_style 파라미터로
   강조 방식 분기 — 단일 고정 금지("같은 템플릿" 천장 재발 방지가 요구사항). ══ */
.pricing-body {{ justify-content: center; }}
.pricing-grid {{
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  align-items: stretch;
}}
.pricing-card {{
  min-width: 0;
  overflow: hidden;
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: calc(var(--radius) + 8px);
  padding: 22px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}}
.pricing-card .block-title {{ margin: 0; color: var(--ink); font-size: 20px; }}
.pricing-card-body {{ min-height: 0; display: flex; flex-direction: column; gap: 14px; }}
.pricing-card .body-text,
.pricing-card .bullet-list li {{ font-size: 15px; line-height: 1.45; }}
.pricing-card .metric-grid {{ display: flex; flex-direction: column; gap: 12px; }}
.pricing-card .metric-value {{ font-size: 40px; }}
/* emphasis_style: invert(기본) — 강조 카드만 액센트 배경 + 흰 글자. */
.pricing-card-emphasis.pricing-emphasis-invert {{
  background: var(--accent);
  border-color: var(--accent);
  color: #FFFFFF;
}}
.pricing-card-emphasis.pricing-emphasis-invert .block-title,
.pricing-card-emphasis.pricing-emphasis-invert .metric-value,
.pricing-card-emphasis.pricing-emphasis-invert .metric-label,
.pricing-card-emphasis.pricing-emphasis-invert .body-text,
.pricing-card-emphasis.pricing-emphasis-invert .bullet-list li {{ color: #FFFFFF; }}
/* emphasis_style: offset — 강조 카드만 위로 살짝 띄워 그림자로 튀어나오게. */
.pricing-card-emphasis.pricing-emphasis-offset {{
  transform: translateY(-10px);
  box-shadow: 0 20px 44px color-mix(in srgb, var(--ink) 22%, transparent);
  border-color: var(--accent);
}}
/* emphasis_style: scale — 강조 카드만 살짝 확대. */
.pricing-card-emphasis.pricing-emphasis-scale {{
  transform: scale(1.05);
  border-color: var(--accent);
  z-index: 1;
}}
/* emphasis_style: border — 배경은 유지하고 두꺼운 액센트 테두리만. */
.pricing-card-emphasis.pricing-emphasis-border {{
  border: 3px solid var(--accent);
}}

/* ══ PG-running_head(2026-07-04 승격): 본문 페이지 상단 3점 크롬(kicker/브랜드/페이지분수) +
   하단 PREV/NEXT. 기존 헤더 예산(56px 상단 패딩) 안에서 해결 — 새 높이 추가 금지. ══ */
.running-head {{
  position: absolute;
  top: 24px;
  left: 72px;
  right: 72px;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-family: var(--mono-font);
  font-size: 11px;
  letter-spacing: .12em;
  text-transform: uppercase;
  color: var(--muted);
}}
.running-head-kicker {{ flex: 1 1 0; text-align: left; color: var(--accent); font-weight: 700; }}
.running-head-brand {{ flex: 1 1 0; text-align: center; color: var(--ink); font-weight: 700; }}
.running-head-frac {{ flex: 1 1 0; text-align: right; white-space: nowrap; }}
.chrome-running-head .slide-head {{ margin-top: 20px; }}
.running-foot {{
  position: absolute;
  bottom: 14px;
  left: 72px;
  right: 72px;
  z-index: 2;
  display: flex;
  justify-content: space-between;
  font-family: var(--mono-font);
  font-size: 10px;
  letter-spacing: .14em;
  color: var(--muted);
  pointer-events: none;
}}

/* ══ DC-side_wordmark(2026-07-04 승격): 좌/우 여백에 세로 회전 대형 워드마크(ghost 톤).
   전용 여백 컬럼 확보 — 본문과 겹치지 않는다. ══ */
.decor-side-wordmark {{ padding-right: 128px; }}
.decor-side-wordmark.decor-side-wordmark-right {{ padding-right: 72px; padding-left: 128px; }}
.side-wordmark {{
  position: absolute;
  top: 50%;
  right: 28px;
  transform: translateY(-50%) rotate(180deg);
  writing-mode: vertical-rl;
  font-size: 64px;
  font-weight: 900;
  letter-spacing: .04em;
  /* var(--ghost)는 rgba() 고정값(Python에서 계산) — color-mix()는 Chrome이 color(srgb ... / a)로
     직렬화해 capture_deck.sh의 rgb() 전제 저대비 체커가 알파를 못 읽고 오탐한다(7/4 pop_dark 실측). */
  color: var(--ghost);
  pointer-events: none;
  z-index: 0;
  white-space: nowrap;
}}
.decor-side-wordmark-right .side-wordmark {{ right: auto; left: 28px; transform: translateY(-50%) rotate(0deg); }}

/* ══ CH-swot_quad(2026-07-04 승격): 2×2 정성 사분면. 강조 사분면(role:highlight)만
   액센트 명도 램프, 나머지는 잉크 저명도 트랙. ══ */
.visual-swot-quad .swot-label {{ fill: var(--ink); }}
.visual-swot-quad .swot-cell-highlight .swot-label {{ fill: var(--accent); }}
.visual-swot-quad .swot-item {{ fill: var(--muted); }}

/* ══ index compositions(2026-07-04): 스킨이 아니라 목차 골격 자체를 시스템별로 분기 ══ */
.theme-editorial-serif .index-list {{
  width: min(100%, 940px);
  gap: 0;
}}
.theme-editorial-serif .index-row {{
  grid-template-columns: 132px minmax(0, 1fr);
  grid-template-rows: auto auto;
  column-gap: 30px;
  row-gap: 4px;
  align-items: start;
  min-height: 62px;
  padding: 4px 0 7px;
  border-top: 0;
}}
.theme-editorial-serif .index-row + .index-row {{
  border-top: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
}}
.theme-editorial-serif .index-row:last-child {{ border-bottom: 0; }}
.theme-editorial-serif .index-row::before {{
  grid-column: 1;
  grid-row: 1 / span 2;
  align-self: start;
  justify-self: end;
  color: color-mix(in srgb, var(--ink) 30%, transparent);
  font-family: var(--font-head);
  font-size: 90px;
  font-weight: 400;
  line-height: .72;
  text-align: right;
  opacity: 1;
}}
.theme-editorial-serif .index-part {{
  grid-column: 2;
  grid-row: 1;
  align-self: end;
  font-family: var(--font-head);
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: 1.02;
}}
.theme-editorial-serif .index-copy {{
  grid-column: 2;
  grid-row: 2;
  max-width: 620px;
  color: color-mix(in srgb, var(--ink) 58%, transparent);
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 500;
  line-height: 1.34;
}}
.theme-editorial-serif .index-content {{
  grid-column: 2;
  grid-row: 1 / span 2;
  align-self: center;
  font-family: var(--font-head);
  font-size: 32px;
  font-weight: 600;
  letter-spacing: 0;
  line-height: 1.05;
}}

.theme-data-mono .index-list {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  width: min(100%, 1000px);
}}
.theme-data-mono .index-row {{
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto auto 1fr;
  gap: 8px;
  align-content: start;
  min-height: 126px;
  padding: 15px 17px 16px;
  border: 1px solid color-mix(in srgb, var(--ink) 68%, transparent);
  background: color-mix(in srgb, var(--c60) 90%, var(--ink));
  border-radius: 0;
  font-family: var(--mono-font);
}}
.theme-data-mono .index-row:last-child {{
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 68%, transparent);
}}
.theme-data-mono .index-row::before {{
  content: "IDX " counter(index, decimal-leading-zero);
  grid-row: 1;
  justify-self: start;
  color: var(--ink);
  font-family: var(--mono-font);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: .14em;
  line-height: 1;
  opacity: .78;
}}
.theme-data-mono .index-part,
.theme-data-mono .index-content {{
  grid-row: 2;
  color: var(--ink);
  font-family: var(--mono-font);
  font-size: 19px;
  font-weight: 800;
  letter-spacing: .06em;
  line-height: 1.18;
  text-transform: uppercase;
}}
.theme-data-mono .index-content {{
  grid-row: 2 / span 2;
}}
.theme-data-mono .index-copy {{
  grid-row: 3;
  color: color-mix(in srgb, var(--ink) 72%, transparent);
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 650;
  letter-spacing: .04em;
  line-height: 1.34;
  text-transform: uppercase;
}}

.theme-dark-premium .index-body {{
  align-items: center;
  justify-content: center;
}}
.theme-dark-premium .index-list {{
  justify-items: center;
  width: min(100%, 790px);
  gap: 7px;
  text-align: center;
}}
.theme-dark-premium .index-row {{
  grid-template-columns: minmax(0, 1fr);
  justify-items: center;
  gap: 3px;
  min-height: 0;
  padding: 3px 30px 5px;
  border-top: 0;
  text-align: center;
}}
.theme-dark-premium .index-row:last-child {{
  border-bottom: 0;
}}
.theme-dark-premium .index-row::before {{
  grid-row: 1;
  color: var(--accent);
  font-family: var(--mono-font);
  font-size: 13px;
  font-weight: 800;
  letter-spacing: .18em;
  line-height: 1;
  opacity: .82;
  text-shadow: 0 0 20px color-mix(in srgb, var(--accent) 28%, transparent);
}}
.theme-dark-premium .index-part,
.theme-dark-premium .index-content {{
  grid-row: 2;
  max-width: 720px;
  color: var(--ink);
  font-size: 25px;
  font-weight: 850;
  line-height: 1.12;
}}
/* 폴백 경로(list 블록)가 index-content로 들어오면 항목이 여럿이라 큰 폰트로 넘침 → 리스트 항목만 절제. */
.theme-dark-premium .index-content .bullet-list li {{ font-size: 19px; line-height: 1.4; }}
.theme-dark-premium .index-copy {{
  grid-row: 3;
  max-width: 620px;
  color: color-mix(in srgb, var(--ink) 58%, transparent);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.34;
}}

.theme-minimal-typo .index-body {{
  align-items: flex-start;
  justify-content: center;
}}
.theme-minimal-typo .index-list {{
  width: min(100%, 880px);
  gap: 14px;
}}
.theme-minimal-typo .index-row {{
  grid-template-columns: minmax(0, 1fr);
  min-height: 0;
  padding: 10px 0 12px;
  border-top: 0;
}}
.theme-minimal-typo .index-row:last-child {{
  border-bottom: 0;
}}
.theme-minimal-typo .index-row::before {{
  content: none;
}}
.theme-minimal-typo .index-part,
.theme-minimal-typo .index-content {{
  color: var(--ink);
  font-size: 43px;
  font-weight: 420;
  letter-spacing: 0;
  line-height: 1.08;
}}
.theme-minimal-typo .index-copy {{
  display: none;
}}

.theme-pop-dark .index-list {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  width: min(100%, 1040px);
}}
.theme-pop-dark .index-row {{
  grid-template-columns: minmax(0, 1fr);
  grid-template-rows: auto 1fr auto;
  align-content: space-between;
  min-height: 138px;
  padding: 17px 20px 18px;
  border-top: 0;
  border-radius: 0;
  background: var(--t1);
}}
.theme-pop-dark .index-row:nth-child(4n+1) {{ background: var(--t1); }}
.theme-pop-dark .index-row:nth-child(4n+2) {{ background: var(--t2); }}
.theme-pop-dark .index-row:nth-child(4n+3) {{ background: var(--t3); }}
.theme-pop-dark .index-row:nth-child(4n) {{ background: var(--t4); }}
.theme-pop-dark .index-row:last-child {{
  border-bottom: 0;
}}
.theme-pop-dark .index-row::before {{
  grid-row: 1;
  color: var(--t5);
  font-family: var(--mono-font);
  font-size: 38px;
  font-weight: 950;
  line-height: .92;
  opacity: 1;
}}
.theme-pop-dark .index-part,
.theme-pop-dark .index-content {{
  grid-row: 2;
  align-self: end;
  color: var(--t5);
  font-size: 27px;
  font-weight: 950;
  line-height: 1.04;
}}
.theme-pop-dark .index-copy {{
  grid-row: 3;
  color: color-mix(in srgb, var(--t5) 84%, transparent);
  font-size: 15px;
  font-weight: 750;
  line-height: 1.28;
}}

/* ══ arch-versus: A/B 두 진영 시각 신호 ══ */
.arch-versus {{
  --versus-a: var(--accent);
  --versus-b: color-mix(in srgb, var(--accent) 20%, slategray);
  --versus-spine: color-mix(in srgb, var(--accent) 62%, var(--ink));
}}
.arch-versus .visual-mirror-bars svg > line {{
  stroke: var(--versus-spine);
  stroke-width: 2.2;
  opacity: .62;
}}
.arch-versus .visual-mirror-bars svg > g:nth-of-type(odd) rect {{
  fill: var(--versus-a);
}}
.arch-versus .visual-mirror-bars svg > g:nth-of-type(even) rect {{
  fill: var(--versus-b);
}}
.arch-versus .visual-mirror-bars svg > g:nth-of-type(odd) .visual-value {{
  fill: var(--versus-a);
}}
.arch-versus .visual-mirror-bars svg > g:nth-of-type(even) .visual-value-accent {{
  fill: var(--versus-b);
}}
.arch-versus .scenario-card:nth-child(1) {{
  border-top: 4px solid var(--versus-a);
  background: color-mix(in srgb, var(--versus-a) 7%, var(--card));
}}
.arch-versus .scenario-card:nth-child(2) {{
  border-top: 4px solid var(--versus-b);
  background: color-mix(in srgb, var(--versus-b) 7%, var(--card));
}}
.arch-versus .scenario-card:nth-child(1) .block-title {{
  color: var(--versus-a);
}}
.arch-versus .scenario-card:nth-child(2) .block-title {{
  color: var(--versus-b);
}}
/* 두 진영 틴트는 pane 내용 높이가 아니라 전체 높이 균등으로 깔아야 깔끔한 사각형이 된다
   (후추님 7/4 p03/p05 "영역이 이상" — 내용높이 pane에 틴트라 뜬 직사각형이던 것). */
.arch-versus .split-body:not(.split-single) {{
  align-items: stretch;
  border-radius: calc(var(--radius) + 2px);
  overflow: hidden;
}}
.arch-versus .split-body:not(.split-single) .split-pane {{ justify-content: center; }}
.arch-versus .split-body:not(.split-single) .split-primary {{
  border-right: 2px solid var(--versus-spine);
  background: color-mix(in srgb, var(--versus-a) 7%, transparent);
  padding: 22px 30px 22px 24px;
}}
.arch-versus .split-body:not(.split-single) .split-secondary {{
  background: color-mix(in srgb, var(--versus-b) 7%, transparent);
  padding: 22px 24px 22px 30px;
}}

/* ══ 최종 컨텍스트 평탄화 — 반드시 스타일시트 맨 끝 ══
   스텝퍼·히어로·매트릭스 셀·대시 타일 안의 카드류는 테마 불문 박스를 벗긴다(카드 속 카드 방지).
   테마 블록이 소스 순서로 이 리셋을 덮어써 이중박스가 재발하던 클래스(7/3 mono 스텝퍼·7/4 dark
   매트릭스) 근절 — 새 테마를 추가해도 이 블록이 항상 마지막에 이긴다. 새 규칙은 이 블록 위에 둘 것. */
.stepper-item .callout,
.stepper-item .metric-card,
.hero-stage .metric-card,
.matrix-cell .metric-card,
.dash-tile .metric-card,
.dash-tile .callout,
.mosaic-tile .metric-card,
.mosaic-tile .callout,
.status-chip .metric-card,
.scenario-card .metric-card,
.scenario-card .callout {{
  border: 0;
  background: transparent;
  padding: 0;
  min-height: 0;
  border-radius: 0;
  margin: 0;
}}
.stepper-item .metric-card::before,
.matrix-cell .metric-card::before,
.dash-tile .metric-card::before,
.mosaic-tile .metric-card::before,
.status-chip .metric-card::before,
.scenario-card .metric-card::before,
.stepper-item .callout::before,
.dash-tile .callout::before,
.mosaic-tile .callout::before,
.scenario-card .callout::before {{ display: none; }}
.theme-minimal-typo .visual-note {{ font-size: 14px; }}
""".strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render TickDeck deck_spec.json with verified registries.")
    parser.add_argument("deck_spec", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--title", default="TickDeck")
    parser.add_argument("--theme", default=None, choices=sorted(PALETTES))
    args = parser.parse_args()

    deck_spec = json.loads(args.deck_spec.read_text(encoding="utf-8"))
    # archetype이 deck_spec에 아예 없으면(designer 누락) 형제 page_plan에서 주입 — arch-* 시각효과 누수 마감(7/5).
    if not _deck_archetype_class(deck_spec):
        pp = args.deck_spec.parent / "05_page_plan.json"
        if pp.exists():
            try:
                arch = json.loads(pp.read_text(encoding="utf-8")).get("archetype")
                if arch:
                    deck_spec["archetype"] = arch
            except Exception:
                pass
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    rendered = render_deck(deck_spec, registry, title=args.title, theme=args.theme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"rendered {len(deck_spec.get('pages', []))} pages -> {args.output}")

    # 시각 QA 산출물을 렌더 과정에 박는다 — HTML을 쓰면 PDF도 자동 생성(규율 아닌 코드 강제).
    # 이 PDF가 4층 시각 QA의 필수 입력. capture 실패(Chrome 없음 등)는 경고로 표면화한다.
    cap = Path(__file__).parent / "capture_deck.sh"
    if cap.exists():
        r = subprocess.run(["bash", str(cap), str(args.output)], capture_output=True, text=True)
        print((r.stdout or r.stderr).strip())


if __name__ == "__main__":
    main()
