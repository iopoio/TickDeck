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
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

CONTRACTS_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "harness-contracts" / "scripts"
if str(CONTRACTS_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CONTRACTS_SCRIPT_DIR))

from contract_checks import SUPPORTED_CONTENT_BLOCK_TYPES, SUPPORTED_VIZ_CHART_TYPES


PALETTES = {
    "pantone": {
        "c60": "#FFFFFF",
        "c30": "#F7F8FA",
        "accent": "#5A6F92",
        "accent2": "#A8664F",
        "ink": "#1F2733",
        "muted": "#6B7384",
        "line": "rgba(31,39,51,.12)",
        "t1": "#8A6F3D",
        "t2": "#A8664F",
        "t3": "#5A6F92",
        "t4": "#6D856D",
        "t5": "#7A5F73",
    },
    "breeze": {
        "c60": "#EDF3F2",
        "c30": "#DFEBE9",
        "accent": "#1C8A80",
        "accent2": "#E08A4F",
        "ink": "#14282A",
        "muted": "#6C8385",
        "line": "rgba(20,40,42,.14)",
        "t1": "#8A6F3D",
        "t2": "#A8664F",
        "t3": "#1C8A80",
        "t4": "#6D856D",
        "t5": "#7A5F73",
    },
    "cobalt": {
        "c60": "#EFF1F6",
        "c30": "#E4E8F1",
        "accent": "#2D52C9",
        "accent2": "#E0833B",
        "ink": "#171E2B",
        "muted": "#6B7384",
        "line": "rgba(23,30,43,.14)",
        "t1": "#8A6F3D",
        "t2": "#A8664F",
        "t3": "#2D52C9",
        "t4": "#6D856D",
        "t5": "#7A5F73",
    },
}


def render_deck(
    deck_spec: dict[str, Any],
    content_registry: dict[str, Any],
    title: str = "TickDeck",
    theme: str = "pantone",
) -> str:
    registry = normalize_registry(content_registry)
    pages = deck_spec.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("deck_spec.pages must be a non-empty list")

    palette = PALETTES.get(theme, PALETTES["breeze"])
    rendered_pages = [
        _render_page(page, index + 1, len(pages), registry, palette)
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
            "<body>",
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


def _render_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    registry: dict[str, dict[str, Any]],
    palette: dict[str, str],
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
        return _render_cover_page(page, page_number, page_count, content, palette)

    body_parts: list[str] = []
    cited_source_ids: list[str] = []
    eyebrow_text = _page_eyebrow_text(page, content, layout)
    for block in content:
        if _block_type(block) == "eyebrow":
            continue
        block_html, block_sources = _render_block(block, page_id, registry, palette)
        if block_html:
            body_parts.append(block_html)
        cited_source_ids.extend(block_sources)

    for metric_id in _iter_metric_ids(content):
        metric = _require_metric(metric_id, page_id, registry)
        cited_source_ids.extend(_as_list(metric.get("source_ids")))

    sources_html = _render_sources(cited_source_ids, registry)
    body_class = "body body-grid" if layout in {"stat_grid", "metric_grid", "cards"} else "body"
    return f"""
<section class="slide layout-{_class_name(layout)}" data-page-id="{_escape(page_id)}">
  <header class="slide-head">
    <div class="eyebrow">{_escape(eyebrow_text)}</div>
    <h1>{_escape(short_title)}</h1>
  </header>
  <main class="{body_class}">
    {''.join(body_parts)}
  </main>
  <footer class="slide-foot">
    <div class="source-list">{sources_html}</div>
    <span class="page-number" data-page-number>{page_number:02d} / {page_count:02d}</span>
  </footer>
</section>""".strip()


def _render_cover_page(
    page: dict[str, Any],
    page_number: int,
    page_count: int,
    content: list[Any],
    palette: dict[str, str],
) -> str:
    page_id = str(page.get("page_id", f"p{page_number:02d}"))
    title = _first_block_text(content, {"headline", "title"}) or _non_cover_text(str(page.get("short_title", "")))
    subtitle = _first_block_text(content, {"summary", "body", "text", "note"})
    eyebrow = _non_cover_text(_first_block_text(content, {"eyebrow"}))
    bands = "".join(
        f'<span style="--band:{_escape(palette[f"t{i}"])}"><b>T{i}</b></span>' for i in range(1, 6)
    )
    eyebrow_html = f'<p class="cover-eyebrow">{_escape(eyebrow)}</p>' if eyebrow else ""
    subtitle_html = f'<p class="cover-subtitle">{_escape(subtitle)}</p>' if subtitle else ""
    return f"""
<section class="slide layout-cover cover-slide" data-page-id="{_escape(page_id)}">
  <main class="cover-body">
    <div class="cover-lockup">
      {eyebrow_html}
      <h1>{_escape(title)}</h1>
      {subtitle_html}
    </div>
    <div class="axis-strip">{bands}</div>
  </main>
  <footer class="slide-foot cover-foot">
    <span></span>
    <span class="page-number" data-page-number>{page_number:02d} / {page_count:02d}</span>
  </footer>
</section>""".strip()


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
        return f'<h2 class="block-title">{_escape(str(block.get("text", "")))}</h2>', []
    if block_type in {"body", "text", "summary"}:
        return f'<p class="body-text">{_escape(str(block.get("text", "")))}</p>', []
    if block_type in {"callout", "note"}:
        return f'<aside class="callout">{_escape(str(block.get("text", "")))}</aside>', []
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
        cards = [_render_metric(metric_id, page_id, registry, "") for metric_id in metric_ids]
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


def _render_metric(
    metric_id: str,
    page_id: str,
    registry: dict[str, dict[str, Any]],
    label_override: str,
) -> str:
    metric = _require_metric(metric_id, page_id, registry)
    value = _format_metric_value(metric)
    label = label_override or str(metric.get("label") or metric.get("scope") or metric_id)
    return f"""
<article class="metric-card" data-metric-id="{_escape(metric_id)}">
  <div class="metric-label">{_escape(label)}</div>
  <div class="metric-value" data-metric-id="{_escape(metric_id)}">{_escape(value)}</div>
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
    svg = {
        "before_after": _svg_before_after,
        "dumbbell": _svg_dumbbell,
        "flow": _svg_flow,
        "big_number": _svg_big_number,
        "gap_map": _svg_gap_map,
        "shift": _svg_shift,
    }[chart](series, title, note, accent, page_id)
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
        metric_id = str(item.get("metric_id", "")).strip()
        metric = _require_metric(metric_id, page_id, registry)
        label = str(item.get("label") or metric_id).strip()
        rendered.append(
            {
                "metric_id": metric_id,
                "label": label,
                "role": str(item.get("role", "")).strip(),
                "value": _format_metric_value(metric),
                "number": _metric_number(metric),
            }
        )
    return rendered


def _svg_before_after(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
) -> str:
    rows = series[:4]
    height = 88 + len(rows) * 42 + (28 if note else 0)
    max_value = _max_metric_number(rows)
    body = []
    for index, item in enumerate(rows):
        y = 62 + index * 42
        width = _scale_metric_width(item, max_value, 560)
        color = accent if _is_highlight(item, index, rows) else "#E5E7EB"
        value_x = min(840, 260 + width + 22)
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <text x="0" y="{y + 4}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <rect x="260" y="{y - 16}" width="{width:.1f}" height="22" rx="11" fill="{color}"/>
              <text x="{value_x:.1f}" y="{y + 5}" class="{'visual-value-accent' if color == accent else 'visual-value'}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("before-after", title, note, height, "".join(body), page_id)


def _svg_dumbbell(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
) -> str:
    points = (series[:2] if len(series) >= 2 else [series[0], series[0]])
    max_value = _max_metric_number(points)
    x1 = _scale_metric_position(points[0], max_value, 180, 720)
    x2 = _scale_metric_position(points[1], max_value, 180, 720)
    left, right = sorted((x1, x2))
    body = f"""
      <line x1="180" y1="96" x2="900" y2="96" stroke="#E5E7EB" stroke-width="12" stroke-linecap="round"/>
      <line x1="{left:.1f}" y1="96" x2="{right:.1f}" y2="96" stroke="{accent}" stroke-width="5" stroke-linecap="round"/>
      {_svg_point(points[0], x1, 96, "#E5E7EB", "visual-value")}
      {_svg_point(points[1], x2, 96, accent, "visual-value-accent")}
    """
    return _svg_shell("dumbbell", title, note, 188, body, page_id)


def _svg_flow(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
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
) -> str:
    item = _highlight_or_first(series)
    arrow = "↓" if (item["number"] or 0) < 0 else "↑"
    body = f"""
      <text x="0" y="132" fill="{accent}" font-size="84" font-weight="900" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
      <text x="300" y="122" fill="{accent}" font-size="42" font-weight="900">{arrow}</text>
      <text x="364" y="92" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
    """
    return _svg_shell("big-number", title, note, 190, body, page_id)


def _svg_gap_map(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
) -> str:
    rows = series[:5]
    height = 80 + len(rows) * 30 + (28 if note else 0)
    max_value = _max_metric_number(rows)
    body = []
    for index, item in enumerate(rows):
        y = 58 + index * 30
        width = _scale_metric_width(item, max_value, 430)
        color = accent if _is_highlight(item, index, rows) else "#E5E7EB"
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <text x="0" y="{y + 12}" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <rect x="220" y="{y}" width="430" height="14" rx="7" fill="#E5E7EB"/>
              <rect x="220" y="{y}" width="{width:.1f}" height="14" rx="7" fill="{color}"/>
              <text x="682" y="{y + 13}" class="{'visual-value-accent' if color == accent else 'visual-value'}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("gap-map", title, note, height, "".join(body), page_id)


def _svg_shift(
    series: list[dict[str, Any]],
    title: str,
    note: str,
    accent: str,
    page_id: str,
) -> str:
    nodes = series[:5]
    arrow_id = f"arrow-{_class_name(page_id)}-shift"
    step = 900 / max(1, len(nodes))
    body = [
        f"""
        <defs>
          <marker id="{arrow_id}" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
            <path d="M0,0 L10,5 L0,10 Z" fill="#1F2733" opacity=".42"/>
          </marker>
        </defs>"""
    ]
    for index, item in enumerate(nodes):
        x = 42 + step * index
        y = 92 + (18 if index % 2 else 0)
        body.append(
            f"""
            <g data-metric-id="{_escape(item["metric_id"])}">
              <circle cx="{x:.1f}" cy="{y}" r="18" fill="#E5E7EB"/>
              <line x1="{x + 28:.1f}" y1="{y}" x2="{x + 108:.1f}" y2="{y}" stroke="#1F2733" stroke-width="2" opacity=".34" marker-end="url(#{arrow_id})"/>
              <circle cx="{x + 136:.1f}" cy="{y}" r="27" fill="{accent}"/>
              <text x="{x + 136:.1f}" y="{y + 54}" text-anchor="middle" class="visual-label" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
              <text x="{x + 136:.1f}" y="{y + 82}" text-anchor="middle" class="visual-value-accent" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
            </g>"""
        )
    return _svg_shell("shift", title, note, 218, "".join(body), page_id)


def _svg_shell(kind: str, title: str, note: str, height: int, body: str, page_id: str) -> str:
    note_y = height - 10
    note_html = f'<text x="0" y="{note_y}" class="visual-note">{_escape(note)}</text>' if note else ""
    title_html = f'<text x="0" y="20" class="visual-title">{_escape(title)}</text>' if title else ""
    return f"""
<svg viewBox="0 0 1000 {height}" role="img" aria-label="{_escape(kind)} chart for {_escape(page_id)}">
  {title_html}
  {body}
  {note_html}
</svg>""".strip()


def _svg_point(item: dict[str, Any], x: float, y: int, fill: str, value_class: str) -> str:
    return f"""
      <g data-metric-id="{_escape(item["metric_id"])}">
        <circle cx="{x:.1f}" cy="{y}" r="22" fill="{fill}" stroke="#CBD5E1" stroke-width="2"/>
        <text x="{x:.1f}" y="{y - 36}" text-anchor="middle" class="{value_class}" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["value"])}</text>
        <text x="{x:.1f}" y="{y + 46}" text-anchor="middle" class="visual-note" data-metric-id="{_escape(item["metric_id"])}">{_escape(item["label"])}</text>
      </g>"""


def _max_metric_number(series: list[dict[str, Any]]) -> float:
    numbers = [abs(item["number"]) for item in series if isinstance(item.get("number"), (int, float))]
    return max(numbers) if numbers else 1.0


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


def _format_metric_value(metric: dict[str, Any]) -> str:
    value = str(metric.get("value", "")).strip()
    unit = str(metric.get("unit", "")).strip()
    if not value:
        raise ValueError("metric value is required")
    if not unit or value.endswith(unit):
        return value
    if unit in {"%", "pp", "p", "x", "X", "조", "억", "만", "명", "개", "건", "원", "달러"}:
        return f"{value}{unit}"
    return f"{value} {unit}"


def _iter_metric_ids(value: Any):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "metric_id" and str(nested).strip():
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
    return html.escape(value, quote=True)


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
  --t1: {palette["t1"]};
  --t2: {palette["t2"]};
  --t3: {palette["t3"]};
  --t4: {palette["t4"]};
  --t5: {palette["t5"]};
  --card: rgba(255, 255, 255, .7);
}}
@page {{ size: 1280px 720px; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: var(--c30);
  color: var(--ink);
  font-family: "Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif;
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
  background: var(--c60);
}}
.slide-head {{ flex: 0 0 auto; }}
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
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 24px;
  padding: 20px 0 34px;
}}
.body-grid {{ justify-content: center; }}
.block-title {{ font-size: 30px; line-height: 1.24; margin: 0; max-width: 920px; }}
.body-text, .callout {{ font-size: 19px; line-height: 1.58; max-width: 900px; word-break: keep-all; }}
.callout {{
  border-left: 4px solid var(--accent);
  background: var(--card);
  padding: 22px 24px;
}}
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
  flex: 0 0 auto;
  border-top: 1px solid var(--line);
  padding-top: 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  color: var(--muted);
  font-size: 12px;
  letter-spacing: .08em;
}}
.source-list {{
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  min-width: 0;
}}
.source-link {{ color: var(--muted); text-decoration: none; }}
.source-link::before {{ content: "["; color: var(--accent); }}
.source-link::after {{ content: "]"; color: var(--accent); }}
.page-number {{ white-space: nowrap; }}
.cover-slide {{ padding: 64px 72px 36px; }}
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
.visual-card {{
  margin-top: auto;
  width: min(100%, 1000px);
  border-top: 1px solid var(--line);
  padding-top: 14px;
}}
.visual-card svg {{ display: block; width: 100%; height: auto; overflow: visible; }}
.visual-card text {{
  font-family: "Pretendard", "Apple SD Gothic Neo", -apple-system, BlinkMacSystemFont, sans-serif;
  letter-spacing: 0;
}}
.visual-title {{ fill: var(--ink); font-size: 18px; font-weight: 900; }}
.visual-note {{ fill: var(--muted); font-size: 13px; font-weight: 700; }}
.visual-label {{ fill: var(--ink); font-size: 15px; font-weight: 800; }}
.visual-value {{ fill: var(--ink); font-size: 22px; font-weight: 900; }}
.visual-value-accent {{ fill: var(--accent); font-size: 28px; font-weight: 900; }}
""".strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render TickDeck deck_spec.json with verified registries.")
    parser.add_argument("deck_spec", type=Path)
    parser.add_argument("registry", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--title", default="TickDeck")
    parser.add_argument("--theme", default="pantone", choices=sorted(PALETTES))
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
