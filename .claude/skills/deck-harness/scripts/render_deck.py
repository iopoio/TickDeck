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
    deck_cited_source_ids = _deck_cited_source_ids(pages, registry)
    # 표지 밴드 수 = 실제 파트 수. 간지 수로 세되, 페이지에 명시된 part_count가 있으면 그게 정답
    # (간지 없는 1부가 있는 덱에서 표지 2밴드 vs 간지 티커 3의 불일치 방지·7/2).
    divider_n = sum(1 for page in pages if isinstance(page, dict) and str(page.get("layout")) == "divider")
    explicit_counts = [int(page.get("part_count")) for page in pages if isinstance(page, dict) and str(page.get("part_count", "")).isdigit()]
    part_count = max([divider_n] + explicit_counts) if (divider_n or explicit_counts) else 0
    rendered_pages = [
        _render_page(page, index + 1, len(pages), registry, palette, deck_cited_source_ids, part_count)
        for index, page in enumerate(pages)
        if isinstance(page, dict)
    ]
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
            f'<body class="deck-theme-{_class_name(palette["theme"])}">',
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


def _render_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    registry: dict[str, dict[str, Any]],
    palette: dict[str, str],
    deck_cited_source_ids: list[str],
    part_count: int = 0,
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
    cited_source_ids: list[str] = []
    footnotes: list[dict[str, Any]] = []
    eyebrow_text = _page_eyebrow_text(page, content, layout)
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
        cited_source_ids.extend(block_sources)

    for metric_id in _iter_metric_ids(content):
        metric = _require_metric(metric_id, page_id, registry)
        cited_source_ids.extend(_as_list(metric.get("source_ids")))

    body_html = _render_layout_body(layout, body_parts, page, content, page_number)
    motif_html = _slide_motif_html(layout, page_number, palette)
    # 카드가 우하단에 자기 출처를 표시한 페이지(다출처 stat_grid)는 하단 source-row가 중복 → 생략(후추님 6/30).
    source_row = "" if _page_has_per_card_sources(content, page_id, registry) else f'<div class="source-row">{_render_sources(cited_source_ids, registry)}</div>'
    footnote_row = _render_footnotes(footnotes)
    # 간지(divider)는 표지·outro처럼 푸터(출처행·카피라이트·페이지번호)를 렌더하지 않는다(후추님 6/30).
    if layout == "divider":
        foot_html = ""
    else:
        foot_html = f"""
  {footnote_row}
  {source_row}
  <footer class="slide-foot">
    <span class="foot-side"></span>
    {_copyright_html()}
    <span class="page-number" data-page-number>{page_number:02d} / {page_count:02d}</span>
  </footer>"""
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-{_class_name(layout)}" data-page-id="{_escape(page_id)}">
  {motif_html}
  <header class="slide-head">
    <div class="eyebrow">{_escape(eyebrow_text)}</div>
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
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-cover cover-slide" data-page-id="{_escape(page_id)}">
  {credit_html}
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
    title = _first_block_text(content, {"headline", "title"}) or "감사합니다"
    eyebrow = _non_cover_text(_first_block_text(content, {"eyebrow"}))
    eyebrow_html = f'<p class="cover-eyebrow">{_escape(eyebrow)}</p>' if eyebrow else ""
    contact_html = _presenter_contact_html()
    # eyebrow를 감사 인사 바로 위에 붙여 한 묶음(상단~중상단), 연락처는 하단(후추님 6/30).
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-cover cover-slide layout-outro outro-slide" data-page-id="{_escape(page_id)}">
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
    eyebrow_text = _page_eyebrow_text(page, content, "source_appendix") or "출처"
    title_text = _page_title_text(page, content, "source_appendix") or "출처"
    src_ids = _as_list(page.get("allowed_source_ids")) or deck_cited_source_ids
    # 출처가 많으면(>10행) 행 간격·폰트를 압축 — 14출처 덱에서 appendix가 넘치던 근본 결함(7/2).
    compact = " appendix-compact" if len(src_ids) > 10 else ""
    rows = []
    for src_id in src_ids:
        source = _require_source(src_id, page_id, registry)
        publisher = str(source.get("publisher") or src_id)
        sttl = str(source.get("title") or "")
        # 넘버링·구분선 없이 "기관 — 리포트명" 한 줄 플랫 리스트(후추님 7/2).
        rows.append(
            f"""
        <article class="appendix-row" data-src-id="{_escape(src_id)}">
          <span class="appendix-pub" data-src-id="{_escape(src_id)}">{_escape(publisher)}</span>
          <span class="appendix-title" data-src-id="{_escape(src_id)}">{_escape(sttl)}</span>
        </article>"""
        )
    motif_html = _slide_motif_html("source_appendix", page_number, palette)
    return f"""
<section class="slide theme-{_class_name(palette["theme"])} layout-source_appendix" data-page-id="{_escape(page_id)}">
  {motif_html}
  <header class="slide-head">
    <div class="eyebrow">{_escape(eyebrow_text)}</div>
    <h1>{_escape(title_text)}</h1>
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
) -> str:
    if layout == "split":
        return _render_split(body_parts)
    if layout == "stepper":
        return _render_stepper(body_parts)
    if layout == "node":
        return _render_node(body_parts)
    if layout == "matrix":
        return _render_matrix(content)
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


def _render_split(body_parts: list[str]) -> str:
    # 거버닝 부제(block-title)는 왼쪽 칸에 가두지 않고 전폭으로 끌어올린다 —
    # 제목 아래 부제가 오는 일반 양식과 통일·좌우 밸런스 회복(후추님 7/2 p05·p07).
    lead = ""
    if body_parts and body_parts[0].lstrip().startswith('<h2 class="block-title"'):
        lead, body_parts = body_parts[0], body_parts[1:]
    # 홀수 블록이면 나머지는 우측(보조 칸)으로 — 좌측은 주 비주얼 하나가 원칙(7/2 p06 좌측 과적 fix).
    midpoint = max(1, len(body_parts) // 2)
    left = "".join(body_parts[:midpoint])
    right = "".join(body_parts[midpoint:])
    return f"""
<main class="body layout-body split-outer">
  {lead}
  <div class="split-body">
    <section class="split-pane split-primary">{left}</section>
    <section class="split-pane split-secondary">{right}</section>
  </div>
</main>""".strip()


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


def _render_matrix(content: list[Any]) -> str:
    # headline/title은 격자 위 소제목으로(후추님 6/30 명시 — "네 전선이…는 소제목"). 셀=body/text 블록만.
    # "라벨 — 설명" 패턴이면 굵은 헤더+본문으로 쪼개 '요약 카드 나열'이 아니라 매트릭스로 읽히게.
    subhead = ""
    cells = []
    for block in content:
        bt = _block_type(block)
        if bt in {"headline", "title"} and not subhead:
            subhead = f'<div class="matrix-subhead"><h2 class="block-title">{_escape(str(block.get("text", "")))}</h2></div>'
            continue
        if bt not in {"body", "text", "callout", "note"}:
            continue
        text = str(block.get("text", "")).strip()
        if not text:
            continue
        label, sep, desc = text.partition(" — ")
        if sep:
            inner = f'<div class="matrix-cell-label">{_escape(label.strip())}</div><div class="matrix-cell-copy">{_escape(desc.strip())}</div>'
        else:
            inner = f'<div class="matrix-cell-copy">{_escape(text)}</div>'
        cells.append(f'<article class="matrix-cell">{inner}</article>')
    return f'<main class="body layout-body matrix-body">{subhead}<section class="matrix-grid">{"".join(cells)}</section></main>'


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
    # 파트 표시는 진척 막대 + 한 줄(PART n · 라벨) 하나로 통일(후추님 #3 — 3중 중복 제거).
    return f"""
<main class="body layout-body divider-body">
  <div class="divider-motif" aria-hidden="true"></div>
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
        for item in items[:3]:
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
        cls = "callout callout-lead" if block.get("emphasis") else "callout"
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
    # 좌측 정렬·좌측 가중(후추님 6/30 재지적): 트랙을 좌측 거터(60)에서 시작하고 span을 줄여
    # 그래프가 슬라이드 좌측 약 60%만 차지(우측 끝까지 안 뻗음) → 덜 퍼지고 왼쪽에 모인다.
    gutter, span = 60, 560
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
    row_h = 82
    height = CHART_TITLE_GAP + row_count * row_h + (30 if note else 0)
    body = [
        f'<line x1="{spine}" y1="{CHART_TITLE_GAP - 8}" x2="{spine}" y2="{CHART_TITLE_GAP + row_count * row_h - 26}" stroke="#1F2733" stroke-width="1.5" opacity=".3"/>'
    ]
    for index in range(row_count):
        top = CHART_TITLE_GAP + index * row_h
        bar_y = top + 28
        if index < len(lefts):
            item = lefts[index]
            width = _scale_metric_width(item, scale_base, half)
            body.append(
                f"""
                <g data-metric-id="{_escape(item["metric_id"])}">
                  <text x="{spine - 14}" y="{top + 10}" text-anchor="end" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
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
                  <text x="{spine + 14}" y="{top + 10}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
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
    base_y = CHART_TITLE_GAP + 206
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
_CHART_RENDERERS = {
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


def _page_eyebrow_text(page: dict[str, Any], content: list[Any], layout: str) -> str:
    for block in content:
        if _block_type(block) == "eyebrow":
            text = str(block.get("text", "")).strip()
            if text:
                return text
    return str(page.get("role", layout)).upper()


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


def _css(palette: dict[str, str]) -> str:
    return f"""
:root {{
  --c60: {palette["c60"]};
  --c30: {palette["c30"]};
  --accent: {palette["accent"]};
  --accent2: {palette["accent2"]};
  --ink: {palette["ink"]};
  --muted: {palette["muted"]};
  --line: {palette["line"]};
  --grid-line: {palette["grid_line"]};
  --slide-bg: {palette["slide_bg"]};
  --slide-bg-size: {palette["slide_bg_size"]};
  --body-bg: {palette["body_bg"]};
  --card: {palette["card"]};
  --radius: {palette["radius"]};
  --mono-font: ui-monospace, "SFMono-Regular", "SF Mono", Consolas, "Liberation Mono", monospace;
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
  font-family: "Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif;
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
.block-eyebrow {{ align-self: flex-start; }}
h1 {{
  margin: 14px 0 0;
  max-width: 980px;
  font-size: 44px;
  line-height: 1.18;
  letter-spacing: 0;
  word-break: keep-all;
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
.cover-slide {{ padding: 64px 72px 36px; }}
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
.stepper-body {{ justify-content: center; }}
.stepper-track {{
  counter-reset: step;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
  gap: 22px;
  align-items: stretch;
}}
/* 스텝퍼 카드 안 callout = 카드 속 카드(이중 박스) 방지 — 박스 벗기고 강조 텍스트만(후추님 7/2 p11 #04). */
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
.stepper-item::after {{
  content: "";
  position: absolute;
  top: 29px;
  left: 64px;
  right: 22px;
  height: 1px;
  background: var(--line);
}}
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
  grid-template-columns: 86px minmax(112px, .35fr) minmax(0, 1fr);
  gap: 24px;
  align-items: center;
  min-height: 96px;
  border-top: 1px solid var(--line);
  padding: 22px 0;
}}
.index-row:last-child {{ border-bottom: 1px solid var(--line); }}
.index-row::before {{
  content: counter(index, decimal-leading-zero);
  color: var(--accent);
  font-family: var(--mono-font);
  font-size: 30px;
  font-weight: 900;
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
.visual-card text {{
  font-family: "Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
}}
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
