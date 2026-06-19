#!/usr/bin/env python3
"""Axis 2 visual component renderer.

The renderer deliberately has no text-only fallback. A slide must choose one of
the registered visual components, and each component returns a real SVG surface.
"""

from __future__ import annotations

import argparse
import contextvars
import json
import math
import re
from html import escape
from pathlib import Path
from typing import Any, Callable


WIDTH = 1280
HEIGHT = 720
KOREAN_FONT_STACK = "'Malgun Gothic', NanumGothic, Pretendard, sans-serif"
CAIROSVG_FONT_FAMILY = "AppleGothic"


BASE_THEME = {
    "ink": "#111827",
    "deep": "#071525",
    "muted": "#64748b",
    "line": "#e5e7eb",
    "panel": "#ffffff",
    "surface": "#f8fafc",
    "surface_alt": "#f1f5f9",
    "primary": "#2563eb",
    "primary_dark": "#1e3a8a",
    "primary_soft": "#dbeafe",
    "secondary": "#475569",
    "secondary_dark": "#1e293b",
    "secondary_soft": "#e2e8f0",
    "accent": "#d97706",
    "accent_dark": "#92400e",
    "accent_soft": "#fef3c7",
    "series_1": "#dbeafe",
    "series_2": "#bfdbfe",
    "series_3": "#60a5fa",
    "series_4": "#2563eb",
    "emphasis": "#d97706",
    "emphasis_soft": "#fef3c7",
    "on_soft": "#111827",
    "map": "#d8dee8",
}


CATEGORY_THEMES: dict[str, dict[str, str]] = {
    "data": {
        "primary": "#2563eb",
        "primary_dark": "#1e3a8a",
        "primary_soft": "#dbeafe",
        "secondary": "#334155",
        "secondary_dark": "#0f172a",
        "secondary_soft": "#e2e8f0",
        "accent": "#d97706",
        "accent_dark": "#92400e",
        "accent_soft": "#fef3c7",
    },
    "process": {
        "primary": "#2563eb",
        "primary_dark": "#1e40af",
        "primary_soft": "#dbeafe",
        "secondary": "#475569",
        "secondary_dark": "#1e293b",
        "secondary_soft": "#e2e8f0",
        "accent": "#d97706",
        "accent_dark": "#92400e",
        "accent_soft": "#fef3c7",
    },
    "comparison": {
        "primary": "#1e40af",
        "primary_dark": "#1e3a8a",
        "primary_soft": "#dbeafe",
        "secondary": "#0f766e",
        "secondary_dark": "#134e4a",
        "secondary_soft": "#ccfbf1",
        "accent": "#d97706",
        "accent_dark": "#92400e",
        "accent_soft": "#fef3c7",
    },
}


COMPONENT_CATEGORIES = {
    "big_percent": "data",
    "donut_gauge": "data",
    "bar_chart": "data",
    "card_grid": "comparison",
    "funnel": "process",
    "timeline": "process",
    "matrix_2x2": "comparison",
    "comparison_vs": "comparison",
    "dashboard": "data",
    "map_data": "data",
    "process": "process",
}


COLOR_ALIASES = {
    "purple": "primary",
    "purple_dark": "primary_dark",
    "violet": "primary",
    "green": "secondary",
    "green_soft": "secondary_soft",
    "cyan": "accent",
    "cyan_soft": "accent_soft",
    "amber": "accent",
    "orange": "accent",
    "rose": "accent",
    "teal": "secondary",
    "blue": "primary",
    "sky": "accent",
    "yellow": "accent",
    "indigo": "primary_dark",
}


def _resolve_palette(theme: dict[str, Any] | None = None, category: str = "data") -> dict[str, str]:
    palette = dict(BASE_THEME)
    palette.update(CATEGORY_THEMES.get(category, {}))
    alias_overrides: dict[str, str] = {}

    if isinstance(theme, dict):
        categories = theme.get("categories")
        if isinstance(categories, dict):
            category_theme = categories.get(category)
            if isinstance(category_theme, dict):
                palette.update({key: str(value) for key, value in category_theme.items()})

        direct_category = theme.get(category)
        if isinstance(direct_category, dict):
            palette.update({key: str(value) for key, value in direct_category.items()})

        for key, value in theme.items():
            if key in {"categories", *CATEGORY_THEMES.keys()} or not isinstance(value, str):
                continue
            if key in COLOR_ALIASES:
                alias_overrides[key] = value
            else:
                palette[key] = value

    for alias, source in COLOR_ALIASES.items():
        palette[alias] = palette.get(source, BASE_THEME.get(source, "#111827"))
    palette.update(alias_overrides)
    return palette


_ACTIVE_PALETTE = contextvars.ContextVar("axis2_active_palette", default=_resolve_palette())


class _PaletteProxy:
    def __getitem__(self, key: str) -> str:
        return _ACTIVE_PALETTE.get()[key]


PALETTE = _PaletteProxy()


DEMO_DATA: dict[str, dict[str, Any]] = {
    "big_percent": {
        "title": "시장 준비",
        "value": 73,
        "unit": "%",
        "caption": "핵심 수치 검산 완료",
        "source_map": {"value": "demo:axis2:big_percent"},
    },
    "donut_gauge": {
        "title": "신뢰 전환",
        "value": 82,
        "unit": "%",
        "caption": "근거 단계까지 도달한 비율",
        "source_map": {"value": "demo:axis2:donut_gauge"},
    },
    "bar_chart": {
        "title": "세그먼트 상승",
        "items": [
            {"label": "인지", "value": 42},
            {"label": "관심", "value": 58},
            {"label": "시범", "value": 71},
            {"label": "유지", "value": 86},
        ],
        "unit": "%",
        "source_map": {"items": "demo:axis2:bar_chart"},
    },
    "card_grid": {
        "title": "성장 동인",
        "cards": [
            {"label": "신호", "value": 64, "caption": "의도 데이터"},
            {"label": "근거", "value": 78, "caption": "사례 근거"},
            {"label": "실행", "value": 55, "caption": "영업 리듬"},
        ],
        "unit": "%",
        "source_map": {"cards": "demo:axis2:card_grid"},
    },
    "funnel": {
        "title": "리드 퍼널",
        "stages": [
            {"label": "도달", "value": 92, "caption": "대상 열람"},
            {"label": "참여", "value": 71, "caption": "근거 클릭"},
            {"label": "검증", "value": 48, "caption": "영업 준비"},
            {"label": "계약", "value": 24, "caption": "계약 성사"},
        ],
        "unit": "%",
        "source_map": {"stages": "demo:axis2:funnel"},
    },
    "timeline": {
        "title": "출시 일정",
        "events": [
            {"label": "발견", "date": "Q1", "caption": "신호 탐색"},
            {"label": "시제품", "date": "Q2", "caption": "시각 근거"},
            {"label": "파일럿", "date": "Q3", "caption": "실계정 검증"},
            {"label": "확장", "date": "Q4", "caption": "반복 운영"},
        ],
        "source_map": {"events": "demo:axis2:timeline"},
    },
    "matrix_2x2": {
        "title": "포지션 매트릭스",
        "x_axis": "실행 부담",
        "y_axis": "시장 영향",
        "points": [
            {"label": "검색", "x": 28, "y": 68},
            {"label": "행사", "x": 70, "y": 42},
            {"label": "제휴", "x": 58, "y": 82},
        ],
        "source_map": {"points": "demo:axis2:matrix_2x2"},
    },
    "comparison_vs": {
        "title": "기존 방식 vs 새 방식",
        "left": {"label": "수동", "value": 42, "caption": "느린 인계"},
        "right": {"label": "자동화", "value": 84, "caption": "근거 확장"},
        "unit": "%",
        "source_map": {"left": "demo:axis2:comparison_vs:left", "right": "demo:axis2:comparison_vs:right"},
    },
    "dashboard": {
        "title": "매출 대시보드",
        "kpis": [
            {"label": "파이프라인", "value": 6.2, "unit": "M"},
            {"label": "승률", "value": 28, "unit": "%"},
            {"label": "주기", "value": 31, "unit": "d"},
        ],
        "series": [32, 45, 38, 62, 58, 74, 69],
        "bars": [24, 38, 52, 44, 68],
        "source_map": {"kpis": "demo:axis2:dashboard"},
    },
    "map_data": {
        "title": "지역 수요",
        "regions": [
            {"label": "서부", "value": 52, "x": 330, "y": 310},
            {"label": "중부", "value": 41, "x": 610, "y": 370},
            {"label": "동부", "value": 64, "x": 860, "y": 275},
        ],
        "unit": "%",
        "source_map": {"regions": "demo:axis2:map_data"},
    },
    "process": {
        "title": "근거 프로세스",
        "steps": [
            {"label": "구상", "value": 50, "caption": "주장 찾기"},
            {"label": "개발", "value": 75, "caption": "근거 만들기"},
            {"label": "확장", "value": 60, "caption": "스토리 묶기"},
            {"label": "위임", "value": 65, "caption": "운영 넘김"},
        ],
        "unit": "%",
        "source_map": {"steps": "demo:axis2:process"},
    },
}


class RenderedComponent:
    def __init__(self, component: str, html: str, svg: str, metadata: dict[str, Any]) -> None:
        self.component = component
        self.html = html
        self.svg = svg
        self.metadata = metadata


class DemoArtifact:
    def __init__(
        self,
        html_path: Path,
        css_path: Path,
        manifest_path: Path,
        svg_paths: dict[str, Path],
        png_paths: dict[str, Path],
    ) -> None:
        self.html_path = html_path
        self.css_path = css_path
        self.manifest_path = manifest_path
        self.svg_paths = svg_paths
        self.png_paths = png_paths


def _clamp(value: Any, low: float = 0.0, high: float = 100.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = low
    return max(low, min(high, number))


def _text(value: Any) -> str:
    return escape(str(value), quote=True)


def _percent_label(value: float, unit: str) -> str:
    if value.is_integer():
        main = str(int(value))
    else:
        main = f"{value:.1f}"
    return f"{main}{_text(unit)}"


def _value_label(value: Any, unit: str = "") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{_text(value)}{_text(unit)}"
    if number.is_integer():
        main = str(int(number))
    else:
        main = f"{number:.1f}"
    return f"{main}{_text(unit)}"


NUMBER_TOKEN_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _number_for_gauge(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        match = NUMBER_TOKEN_RE.search(str(value or ""))
        return float(match.group(0)) if match else 0.0


def _big_value_label(value: Any, unit: str) -> str:
    unit = str(unit or "")
    raw = str(value if value is not None else "").strip()
    if not raw:
        raw = "0"
    else:
        try:
            number = float(raw)
        except ValueError:
            pass
        else:
            raw = str(int(number)) if number.is_integer() else f"{number:.2f}".rstrip("0").rstrip(".")
    if unit and not raw.endswith(unit):
        raw = f"{raw}{unit}"
    return raw


def _text_width_units(text: str) -> float:
    units = 0.0
    for char in text:
        if char.isdigit():
            units += 0.58
        elif char in ".,:":
            units += 0.28
        elif char == "%":
            units += 0.72
        elif char.isspace():
            units += 0.32
        elif char.isascii():
            units += 0.56
        else:
            units += 0.95
    return max(units, 0.1)


def _fit_text_size(text: str, *, max_width: float, base_size: int, min_size: int) -> int:
    fit_size = max(1, math.floor(max_width / _text_width_units(text)))
    if fit_size < min_size:
        return fit_size
    return min(base_size, fit_size)


def _fit_text_attrs(text: str, font_size: int, max_width: float) -> str:
    if _text_width_units(text) * font_size <= max_width:
        return ""
    return f' textLength="{max_width:.0f}" lengthAdjust="spacingAndGlyphs"'


def _wrap_words(value: Any, max_chars: int, max_lines: int) -> list[str]:
    words = str(value or "").split()
    if not words:
        return []
    lines: list[str] = []
    current = ""
    for word in words:
        if len(word) > max_chars:
            chunks = [word[index : index + max_chars] for index in range(0, len(word), max_chars)]
        else:
            chunks = [word]
        for chunk in chunks:
            candidate = chunk if not current else f"{current} {chunk}"
            if len(candidate) <= max_chars:
                current = candidate
                continue
            lines.append(current)
            current = chunk
            if len(lines) == max_lines:
                break
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1].rstrip(".")[: max_chars - 3].rstrip() + "..."
    return lines


def _text_lines(
    lines: list[str],
    *,
    x: float,
    y: float,
    line_height: float,
    fill: str,
    font_size: int,
    font_weight: str = "400",
    role: str | None = None,
    anchor: str | None = None,
) -> str:
    nodes = []
    role_attr = f' data-role="{role}"' if role else ""
    anchor_attr = f' text-anchor="{anchor}"' if anchor else ""
    for index, line in enumerate(lines):
        nodes.append(
            f'  <text{role_attr} x="{x:g}" y="{y + index * line_height:g}"{anchor_attr} fill="{fill}" font-family="{KOREAN_FONT_STACK}" font-size="{font_size}" font-weight="{font_weight}">{_text(line)}</text>'
        )
    return "\n".join(nodes)


def _line_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    first_x, first_y = points[0]
    commands = [f"M {first_x:.2f} {first_y:.2f}"]
    commands.extend(f"L {x:.2f} {y:.2f}" for x, y in points[1:])
    return " ".join(commands)


def _arrow_points(x: float, y: float, width: float, height: float, notch: float = 34.0) -> str:
    return (
        f"{x:.2f},{y:.2f} {x + width - notch:.2f},{y:.2f} {x + width:.2f},{y + height / 2:.2f} "
        f"{x + width - notch:.2f},{y + height:.2f} {x:.2f},{y + height:.2f} {x + notch:.2f},{y + height / 2:.2f}"
    )


def _polar_to_cartesian(cx: float, cy: float, radius: float, angle_degrees: float) -> tuple[float, float]:
    angle_radians = math.radians(angle_degrees - 90)
    return cx + radius * math.cos(angle_radians), cy + radius * math.sin(angle_radians)


def _arc_path(cx: float, cy: float, radius: float, percent: float) -> str:
    end_angle = 359.99 * percent / 100
    start_x, start_y = _polar_to_cartesian(cx, cy, radius, 0)
    end_x, end_y = _polar_to_cartesian(cx, cy, radius, end_angle)
    large_arc = 1 if end_angle > 180 else 0
    return f"M {start_x:.2f} {start_y:.2f} A {radius} {radius} 0 {large_arc} 1 {end_x:.2f} {end_y:.2f}"


def _metadata(component: str, data: dict[str, Any], refs: list[str]) -> dict[str, Any]:
    return {
        "component": component,
        "design_refs": refs,
        "source_map": data.get("source_map", {}),
    }


def _series_fill(index: int, total: int, *, emphasize_last: bool = True) -> str:
    if emphasize_last and total > 1 and index == total - 1:
        return PALETTE["emphasis"]
    shades = [PALETTE["series_1"], PALETTE["series_2"], PALETTE["series_3"], PALETTE["series_4"]]
    return shades[min(index, len(shades) - 1)]


def svg_for_png(svg: str) -> str:
    return svg.replace(f'font-family="{KOREAN_FONT_STACK}"', f'font-family="{CAIROSVG_FONT_FAMILY}"')


def _svg_shell(body: str, defs: str = "", class_name: str = "", aria_label: Any = "TickDeck visual component") -> str:
    label = _text(aria_label or "TickDeck visual component")
    return f"""<svg class="tdc-svg {class_name}" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" width="{WIDTH}" height="{HEIGHT}" role="img" aria-label="{label}">
  <defs>
    <filter id="tdc-shadow" x="-20%" y="-20%" width="140%" height="150%">
      <feDropShadow dx="0" dy="16" stdDeviation="18" flood-color="#0f172a" flood-opacity="0.13"/>
    </filter>
    <linearGradient id="tdc-purple" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['primary']}"/>
      <stop offset="100%" stop-color="{PALETTE['primary_dark']}"/>
    </linearGradient>
    <linearGradient id="tdc-green" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['secondary_soft']}"/>
      <stop offset="100%" stop-color="{PALETTE['secondary']}"/>
    </linearGradient>
    <linearGradient id="tdc-cyan" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['accent_soft']}"/>
      <stop offset="100%" stop-color="{PALETTE['accent']}"/>
    </linearGradient>
    <linearGradient id="tdc-orange" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['accent_soft']}"/>
      <stop offset="100%" stop-color="{PALETTE['accent']}"/>
    </linearGradient>
    <linearGradient id="tdc-teal" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['secondary_soft']}"/>
      <stop offset="100%" stop-color="{PALETTE['secondary']}"/>
    </linearGradient>
    <linearGradient id="tdc-rose" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['accent_soft']}"/>
      <stop offset="100%" stop-color="{PALETTE['accent']}"/>
    </linearGradient>
    <linearGradient id="tdc-blue" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{PALETTE['primary_soft']}"/>
      <stop offset="100%" stop-color="{PALETTE['primary']}"/>
    </linearGradient>
    {defs}
  </defs>
{body}
</svg>"""


def _component_html(name: str, svg: str) -> str:
    return f'<section class="tdc-component tdc-{name}" data-component="{name}">\n{svg}\n</section>'


def render_big_percent(data: dict[str, Any]) -> RenderedComponent:
    raw_value = data.get("value")
    value = _clamp(_number_for_gauge(raw_value))
    unit = str(data.get("unit", "%"))
    label_text = _big_value_label(raw_value, unit)
    label = _text(label_text)
    fill_width = 680 * value / 100
    title = _text(data.get("title", "Big percent"))
    big_font_size = _fit_text_size(label_text, max_width=270, base_size=150, min_size=42)
    big_fit_attrs = _fit_text_attrs(label_text, big_font_size, 270)
    side_font_size = _fit_text_size(label_text, max_width=360, base_size=42, min_size=22)
    side_fit_attrs = _fit_text_attrs(label_text, side_font_size, 360)
    caption_lines = _wrap_words(data.get("caption", ""), 24, 3)
    caption_svg = _text_lines(
        caption_lines,
        x=132,
        y=486,
        line_height=30,
        fill=PALETTE["primary_soft"],
        font_size=24,
        role="caption-line",
    )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" rx="0" fill="{PALETTE['surface']}"/>
  <rect x="88" y="78" width="1104" height="564" rx="34" fill="{PALETTE['panel']}" filter="url(#tdc-shadow)"/>
  <rect x="88" y="78" width="392" height="564" rx="34" fill="url(#tdc-purple)"/>
  <text x="132" y="160" fill="{PALETTE['primary_soft']}" font-family="{KOREAN_FONT_STACK}" font-size="28" font-weight="700">BIG PERCENT</text>
  <text x="132" y="358" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="{big_font_size}" font-weight="800"{big_fit_attrs}>{label}</text>
  <text x="132" y="430" fill="{PALETTE['primary_soft']}" font-family="{KOREAN_FONT_STACK}" font-size="32" font-weight="700">{title}</text>
{caption_svg}
  <line x1="548" y1="176" x2="1128" y2="176" stroke="{PALETTE['line']}" stroke-width="2"/>
  <line x1="548" y1="290" x2="1128" y2="290" stroke="{PALETTE['line']}" stroke-width="2"/>
  <line x1="548" y1="404" x2="1128" y2="404" stroke="{PALETTE['line']}" stroke-width="2"/>
  <rect x="548" y="488" width="680" height="34" rx="17" fill="{PALETTE['secondary_soft']}"/>
  <rect data-role="progress-fill" x="548" y="488" width="{fill_width:.2f}" height="34" rx="17" fill="url(#tdc-green)"/>
  <text x="548" y="126" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="46" font-weight="760">Evidence-weighted signal</text>
  <text x="548" y="228" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="26">Target threshold</text>
  <text x="1128" y="228" text-anchor="end" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="42" font-weight="800">70%</text>
  <text x="548" y="342" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="26">Current measure</text>
  <text x="1128" y="342" text-anchor="end" fill="{PALETTE['purple_dark']}" font-family="{KOREAN_FONT_STACK}" font-size="{side_font_size}" font-weight="800"{side_fit_attrs}>{label}</text>
  <text x="548" y="582" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="22">Big-number signal with financial gauge structure</text>
"""
    svg = _svg_shell(body, class_name="tdc-big-percent-svg", aria_label=data.get("title", "Big percent"))
    return RenderedComponent(
        "big_percent",
        _component_html("big_percent", svg),
        svg,
        _metadata("big_percent", data, ["Big number emphasis", "Financial gauge structure"]),
    )


def render_donut_gauge(data: dict[str, Any]) -> RenderedComponent:
    value = _clamp(data.get("value"))
    unit = str(data.get("unit", "%"))
    label = _percent_label(value, unit)
    title = _text(data.get("title", "Donut gauge"))
    caption = _text(data.get("caption", ""))
    arc_path = _arc_path(438, 360, 172, value)
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
  <rect x="80" y="82" width="1120" height="556" rx="38" fill="#f8fafc" filter="url(#tdc-shadow)"/>
  <circle cx="438" cy="360" r="198" fill="#ffffff"/>
  <circle cx="438" cy="360" r="172" fill="none" stroke="{PALETTE['primary_soft']}" stroke-width="46"/>
  <path data-role="donut-arc" d="{arc_path}" fill="none" stroke="url(#tdc-purple)" stroke-width="46" stroke-linecap="round"/>
  <circle cx="438" cy="360" r="104" fill="#f8fafc"/>
  <text x="438" y="348" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="92" font-weight="820">{label}</text>
  <text x="438" y="404" text-anchor="middle" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="25" font-weight="700">conversion gauge</text>
  <rect x="728" y="154" width="330" height="72" rx="22" fill="url(#tdc-green)"/>
  <text x="760" y="201" fill="{PALETTE['on_soft']}" font-family="{KOREAN_FONT_STACK}" font-size="30" font-weight="800">{title}</text>
  <text x="728" y="300" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="58" font-weight="780">Signal strength</text>
  <text x="728" y="356" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="26">{caption}</text>
  <line x1="728" y1="430" x2="1060" y2="430" stroke="{PALETTE['line']}" stroke-width="3"/>
  <circle cx="776" cy="500" r="17" fill="{PALETTE['secondary']}"/>
  <text data-role="donut-legend-line" x="812" y="509" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="700">Clean sales palette</text>
  <circle cx="776" cy="552" r="17" fill="{PALETTE['purple']}"/>
  <text data-role="donut-legend-line" x="812" y="561" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="700">Three-part gauge pattern</text>
"""
    svg = _svg_shell(body, class_name="tdc-donut-gauge-svg", aria_label=data.get("title", "Donut gauge"))
    return RenderedComponent(
        "donut_gauge",
        _component_html("donut_gauge", svg),
        svg,
        _metadata("donut_gauge", data, ["Circular progress gauge", "Clean sales palette"]),
    )


def render_bar_chart(data: dict[str, Any]) -> RenderedComponent:
    items = list(data.get("items") or [])
    if not items:
        raise ValueError("No fallback renderer for bar_chart: items are required")
    unit = str(data.get("unit", ""))
    values = [_clamp(item.get("value")) for item in items]
    max_value = max(values + [1])
    title = _text(data.get("title", "Bar chart"))
    bar_width = 116
    gap = 54
    x0 = 260
    y_base = 560
    chart_height = 286
    bars = []
    for index, item in enumerate(items):
        value = _clamp(item.get("value"))
        height = chart_height * value / max_value
        x = x0 + index * (bar_width + gap)
        y = y_base - height
        color = _series_fill(index, len(items[:4]))
        label = _text(item.get("label", f"Item {index + 1}"))
        bars.append(
            f"""  <rect data-role="bar" x="{x}" y="{y:.2f}" width="{bar_width}" height="{height:.2f}" rx="24" fill="{color}"/>
  <text x="{x + bar_width / 2}" y="{y - 22:.2f}" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="31" font-weight="800">{_percent_label(value, unit)}</text>
  <text x="{x + bar_width / 2}" y="594" text-anchor="middle" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="23" font-weight="700">{label}</text>"""
        )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#f3f4f6"/>
  <rect x="76" y="74" width="1128" height="572" rx="28" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <text x="126" y="142" fill="{PALETTE['purple_dark']}" font-family="{KOREAN_FONT_STACK}" font-size="52" font-weight="760">{title}</text>
  <text x="126" y="190" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="24">Rising percent bars with disciplined chart spacing</text>
  <line x1="220" y1="560" x2="1052" y2="560" stroke="{PALETTE['line']}" stroke-width="4"/>
  <line x1="220" y1="464" x2="1052" y2="464" stroke="{PALETTE['line']}" stroke-width="2"/>
  <line x1="220" y1="370" x2="1052" y2="370" stroke="{PALETTE['line']}" stroke-width="2"/>
  <line x1="220" y1="274" x2="1052" y2="274" stroke="{PALETTE['line']}" stroke-width="2"/>
{chr(10).join(bars)}
  <rect x="980" y="114" width="134" height="48" rx="24" fill="{PALETTE['secondary_soft']}"/>
  <text x="1047" y="147" text-anchor="middle" fill="{PALETTE['secondary_dark']}" font-family="{KOREAN_FONT_STACK}" font-size="22" font-weight="800">SVG DATA</text>
"""
    svg = _svg_shell(body, class_name="tdc-bar-chart-svg", aria_label=data.get("title", "Bar chart"))
    return RenderedComponent(
        "bar_chart",
        _component_html("bar_chart", svg),
        svg,
        _metadata("bar_chart", data, ["Rising percent bars", "Financial chart discipline"]),
    )


def render_card_grid(data: dict[str, Any]) -> RenderedComponent:
    cards = list(data.get("cards") or [])
    if not cards:
        raise ValueError("No fallback renderer for card_grid: cards are required")
    unit = str(data.get("unit", ""))
    title = _text(data.get("title", "Card grid"))
    card_width = 320
    card_height = 318
    x0 = 130
    y0 = 256
    gap = 36
    card_svgs = []
    for index, card in enumerate(cards[:3]):
        x = x0 + index * (card_width + gap)
        raw_value = card.get("value")
        has_value = raw_value is not None and str(raw_value).strip() != ""
        value = _clamp(raw_value) if has_value else None
        label = _text(card.get("label", f"Card {index + 1}"))
        caption = _text(card.get("caption", ""))
        fill = _series_fill(index, len(cards[:3]))
        metric_html = ""
        if has_value and value is not None:
            spark_y = y0 + 256 - 54 * value / 100
            metric_html = f"""
  <text data-role="card-value" x="{x + 282}" y="{y0 + 200}" text-anchor="end" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="32" font-weight="820">{_percent_label(value, unit)}</text>
  <rect data-role="spark-panel" x="{x + 30}" y="{y0 + 204}" width="260" height="78" rx="20" fill="#f8fafc"/>
  <path data-role="card-spark" d="M {x + 42} {y0 + 256} L {x + 268} {spark_y:.2f}" data-value="{value:.1f}" fill="none" stroke="{PALETTE['primary']}" stroke-width="10" stroke-linecap="round"/>
  <circle data-role="card-spark-marker" data-value="{value:.1f}" cx="{x + 268}" cy="{spark_y:.2f}" r="11" fill="{fill}" stroke="#ffffff" stroke-width="4"/>
  <rect data-role="card-progress-track" x="{x + 38}" y="{y0 + 270}" width="244" height="18" rx="9" fill="{PALETTE['secondary_soft']}"/>
  <rect x="{x + 38}" y="{y0 + 270}" width="{244 * value / 100:.2f}" height="18" rx="9" fill="{fill}"/>
"""
        card_svgs.append(
            f"""  <rect data-role="card-frame" x="{x}" y="{y0}" width="{card_width}" height="{card_height}" rx="28" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <rect x="{x + 28}" y="{y0 + 28}" width="58" height="58" rx="18" fill="{fill}"/>
  <text x="{x + 57}" y="{y0 + 67}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="23" font-weight="840">0{index + 1}</text>
  <text x="{x + 28}" y="{y0 + 132}" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="35" font-weight="800">{label}</text>
  <text x="{x + 28}" y="{y0 + 174}" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="23">{caption}</text>
{metric_html}
"""
        )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{PALETTE['surface']}"/>
  <text x="130" y="132" fill="{PALETTE['secondary']}" font-family="{KOREAN_FONT_STACK}" font-size="30" font-weight="800">SUMMARY</text>
  <text x="130" y="194" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="62" font-weight="780">{title}</text>
  <text x="760" y="176" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="24">Source-linked cards.</text>
{chr(10).join(card_svgs)}
"""
    svg = _svg_shell(body, class_name="tdc-card-grid-svg", aria_label=data.get("title", "Card grid"))
    return RenderedComponent(
        "card_grid",
        _component_html("card_grid", svg),
        svg,
        _metadata("card_grid", data, ["Metric card grid", "Big-number metrics"]),
    )


def render_funnel(data: dict[str, Any]) -> RenderedComponent:
    stages = list(data.get("stages") or [])
    if not stages:
        raise ValueError("No fallback renderer for funnel: stages are required")
    unit = str(data.get("unit", ""))
    title = _text(data.get("title", "Funnel"))
    colors = ["url(#tdc-purple)", "url(#tdc-teal)", "url(#tdc-orange)", PALETTE["secondary_dark"]]
    widths = [470, 390, 310, 230, 150]
    cx = 890
    top_y = 160
    layer_h = 70
    segments = []
    labels = []
    for index, stage in enumerate(stages[:4]):
        top_width = widths[index]
        bottom_width = widths[index + 1]
        y = top_y + index * (layer_h + 8)
        top_left = cx - top_width / 2
        top_right = cx + top_width / 2
        bottom_left = cx - bottom_width / 2
        bottom_right = cx + bottom_width / 2
        value = _clamp(stage.get("value"))
        label = _text(stage.get("label", f"Stage {index + 1}"))
        caption = _text(stage.get("caption", ""))
        fill = colors[index % len(colors)]
        segments.append(
            f"""  <path data-role="funnel-segment" d="M {top_left:.2f} {y:.2f} C {cx - top_width * 0.28:.2f} {y - 28:.2f}, {cx + top_width * 0.28:.2f} {y - 28:.2f}, {top_right:.2f} {y:.2f} L {bottom_right:.2f} {y + layer_h:.2f} C {cx + bottom_width * 0.22:.2f} {y + layer_h + 22:.2f}, {cx - bottom_width * 0.22:.2f} {y + layer_h + 22:.2f}, {bottom_left:.2f} {y + layer_h:.2f} Z" fill="{fill}" opacity="0.96"/>
  <ellipse cx="{cx:.2f}" cy="{y:.2f}" rx="{top_width / 2:.2f}" ry="26" fill="#ffffff" opacity="0.22"/>
  <text x="{cx:.2f}" y="{y + 47:.2f}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="820">{label}</text>"""
        )
        label_x = 138
        label_y = 304 + index * 70
        value_x = 406
        labels.append(
            f"""  <line x1="{value_x + 26:.2f}" y1="{label_y - 10:.2f}" x2="{top_left - 22:.2f}" y2="{y + 36:.2f}" stroke="{PALETTE['line']}" stroke-width="3"/>
  <circle cx="{label_x:.2f}" cy="{label_y - 10:.2f}" r="20" fill="{fill}"/>
  <text x="{label_x:.2f}" y="{label_y - 3:.2f}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="17" font-weight="840">0{index + 1}</text>
  <text x="{label_x + 42:.2f}" y="{label_y - 18:.2f}" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="27" font-weight="820">{_percent_label(value, unit)}</text>
  <text x="{label_x + 42:.2f}" y="{label_y + 12:.2f}" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="19" font-weight="700">{caption}</text>"""
        )
    neck_y = top_y + 4 * (layer_h + 8) + 4
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{PALETTE['accent_soft']}"/>
  <rect x="70" y="66" width="1140" height="588" rx="34" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <g data-role="funnel-text-column">
  <text x="118" y="126" fill="{PALETTE['purple']}" font-family="{KOREAN_FONT_STACK}" font-size="18" font-weight="840">FUNNEL INFOGRAPHIC</text>
  <text x="118" y="184" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="54" font-weight="780">{title}</text>
  <text x="118" y="228" fill="{PALETTE['accent']}" font-family="{KOREAN_FONT_STACK}" font-size="30" font-weight="820">Layered funnel conversion logic</text>
{chr(10).join(labels)}
  </g>
  <g data-role="funnel-chart-column">
  <ellipse cx="{cx}" cy="{top_y - 2}" rx="308" ry="42" fill="{PALETTE['primary_soft']}"/>
{chr(10).join(segments)}
  <path data-role="funnel-neck" d="M {cx - 84} {neck_y} L {cx + 84} {neck_y} L {cx + 38} {neck_y + 96} L {cx - 38} {neck_y + 96} Z" fill="{PALETTE['secondary_dark']}"/>
  <ellipse cx="{cx}" cy="{neck_y}" rx="84" ry="20" fill="{PALETTE['accent']}" opacity="0.55"/>
  </g>
  <circle cx="110" cy="608" r="22" fill="{PALETTE['purple']}"/>
  <circle cx="158" cy="608" r="14" fill="{PALETTE['accent']}"/>
"""
    svg = _svg_shell(body, class_name="tdc-funnel-svg", aria_label=data.get("title", "Funnel"))
    return RenderedComponent(
        "funnel",
        _component_html("funnel", svg),
        svg,
        _metadata("funnel", data, ["Layered funnel geometry", "Pyramid conversion logic"]),
    )


def render_timeline(data: dict[str, Any]) -> RenderedComponent:
    events = list(data.get("events") or [])
    if not events:
        raise ValueError("No fallback renderer for timeline: events are required")
    title = _text(data.get("title", "Timeline"))
    x_positions = [228, 496, 764, 1032]
    axis_y = 360
    nodes = []
    cards = []
    for index, event in enumerate(events[:4]):
        x = x_positions[index]
        label = _text(event.get("label", f"Event {index + 1}"))
        date = _text(event.get("date", ""))
        caption = _text(event.get("caption", ""))
        fill = _series_fill(index, len(events[:4]))
        card_y = 170 if index % 2 == 0 else 446
        connector_end = card_y + 92 if index % 2 == 0 else card_y - 28
        nodes.append(
            f"""  <line data-role="timeline-connector" x1="{x}" y1="{axis_y}" x2="{x}" y2="{connector_end}" stroke="{PALETTE['primary']}" stroke-width="4" stroke-linecap="round"/>
  <circle data-role="timeline-node" cx="{x}" cy="{axis_y}" r="38" fill="{fill}"/>
  <circle cx="{x}" cy="{axis_y}" r="22" fill="#ffffff" opacity="0.28"/>
  <text x="{x}" y="{axis_y + 9}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="23" font-weight="840">0{index + 1}</text>"""
        )
        cards.append(
            f"""  <rect x="{x - 104}" y="{card_y}" width="208" height="112" rx="22" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <rect data-role="timeline-date-pill" x="{x - 82}" y="{card_y + 18}" width="58" height="28" rx="14" fill="{PALETTE['primary_soft']}"/>
  <text x="{x - 53}" y="{card_y + 38}" text-anchor="middle" fill="{PALETTE['primary_dark']}" font-family="{KOREAN_FONT_STACK}" font-size="16" font-weight="820">{date}</text>
  <text x="{x - 82}" y="{card_y + 72}" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="820">{label}</text>
  <text x="{x - 82}" y="{card_y + 100}" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="18">{caption}</text>"""
        )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#f8fafc"/>
  <text x="112" y="118" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="58" font-weight="780">{title}</text>
  <text x="112" y="158" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="24">Alternating milestone cards with roadmap clarity</text>
  <path data-role="timeline-axis" d="M 150 {axis_y} C 350 {axis_y - 74}, 504 {axis_y + 74}, 672 {axis_y} S 984 {axis_y - 74}, 1138 {axis_y}" fill="none" stroke="{PALETTE['primary_soft']}" stroke-width="24" stroke-linecap="round"/>
  <path d="M 150 {axis_y} C 350 {axis_y - 74}, 504 {axis_y + 74}, 672 {axis_y} S 984 {axis_y - 74}, 1138 {axis_y}" fill="none" stroke="{PALETTE['purple']}" stroke-width="6" stroke-linecap="round"/>
{chr(10).join(cards)}
{chr(10).join(nodes)}
"""
    svg = _svg_shell(body, class_name="tdc-timeline-svg", aria_label=data.get("title", "Timeline"))
    return RenderedComponent(
        "timeline",
        _component_html("timeline", svg),
        svg,
        _metadata("timeline", data, ["Alternating timeline cards", "Roadmap clarity"]),
    )


def render_matrix_2x2(data: dict[str, Any]) -> RenderedComponent:
    points = list(data.get("points") or [])
    if not points:
        raise ValueError("No fallback renderer for matrix_2x2: points are required")
    title = _text(data.get("title", "Matrix 2x2"))
    x_axis = _text(data.get("x_axis", "X axis"))
    y_axis = _text(data.get("y_axis", "Y axis"))
    chart_x = 448
    chart_y = 154
    chart_w = 600
    chart_h = 420
    subtitle_svg = _text_lines(
        ["Cost-impact positioning pattern"],
        x=126,
        y=194,
        line_height=28,
        fill=PALETTE["muted"],
        font_size=23,
        role="matrix-subtitle-line",
    )
    quadrants = [
        (chart_x, chart_y, PALETTE["primary_soft"], "Strategic", chart_x + 24, chart_y + 42, "start"),
        (chart_x + chart_w / 2, chart_y, PALETTE["secondary_soft"], "Scale", chart_x + chart_w - 24, chart_y + 42, "end"),
        (chart_x, chart_y + chart_h / 2, PALETTE["accent_soft"], "Watch", chart_x + 24, chart_y + chart_h - 42, "start"),
        (
            chart_x + chart_w / 2,
            chart_y + chart_h / 2,
            PALETTE["surface_alt"],
            "Automate",
            chart_x + chart_w - 24,
            chart_y + chart_h - 42,
            "end",
        ),
    ]
    quadrant_svgs = [
        f"""  <rect data-role="matrix-quadrant" x="{x:.2f}" y="{y:.2f}" width="{chart_w / 2:.2f}" height="{chart_h / 2:.2f}" fill="{fill}"/>
  <text data-role="matrix-quadrant-label" x="{label_x:.2f}" y="{label_y:.2f}" text-anchor="{anchor}" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="20" font-weight="800">{label}</text>"""
        for x, y, fill, label, label_x, label_y, anchor in quadrants
    ]
    point_svgs = []
    point_colors = ["url(#tdc-purple)", "url(#tdc-orange)", "url(#tdc-teal)", "url(#tdc-blue)"]
    for index, point in enumerate(points[:6]):
        px = chart_x + chart_w * _clamp(point.get("x")) / 100
        py = chart_y + chart_h * (1 - _clamp(point.get("y")) / 100)
        label = _text(point.get("label", f"P{index + 1}"))
        fill = point_colors[index % len(point_colors)]
        point_svgs.append(
            f"""  <circle data-role="matrix-point" cx="{px:.2f}" cy="{py:.2f}" r="19" fill="{fill}" stroke="#ffffff" stroke-width="6"/>
  <text x="{px + 28:.2f}" y="{py + 7:.2f}" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="22" font-weight="800">{label}</text>"""
        )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#f1f5f9"/>
  <rect x="78" y="76" width="1124" height="568" rx="32" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <text x="126" y="150" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="54" font-weight="780">{title}</text>
{subtitle_svg}
  <circle cx="176" cy="302" r="32" fill="url(#tdc-purple)"/>
  <text x="224" y="312" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="800">High impact</text>
  <circle cx="176" cy="382" r="32" fill="url(#tdc-teal)"/>
  <text x="224" y="392" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="800">Low effort</text>
  <rect x="{chart_x}" y="{chart_y}" width="{chart_w}" height="{chart_h}" rx="24" fill="#ffffff" stroke="{PALETTE['line']}" stroke-width="3"/>
{chr(10).join(quadrant_svgs)}
  <line data-role="matrix-axis-x" x1="{chart_x}" y1="{chart_y + chart_h / 2}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h / 2}" stroke="#94a3b8" stroke-width="4"/>
  <line data-role="matrix-axis-y" x1="{chart_x + chart_w / 2}" y1="{chart_y}" x2="{chart_x + chart_w / 2}" y2="{chart_y + chart_h}" stroke="#94a3b8" stroke-width="4"/>
  <text x="{chart_x + chart_w / 2}" y="{chart_y + chart_h + 46}" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="23" font-weight="820">{x_axis}</text>
  <text transform="translate({chart_x - 46} {chart_y + chart_h / 2}) rotate(-90)" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="23" font-weight="820">{y_axis}</text>
{chr(10).join(point_svgs)}
"""
    svg = _svg_shell(body, class_name="tdc-matrix-2x2-svg", aria_label=data.get("title", "Matrix 2x2"))
    return RenderedComponent(
        "matrix_2x2",
        _component_html("matrix_2x2", svg),
        svg,
        _metadata("matrix_2x2", data, ["Cost-impact positioning"]),
    )


def render_comparison_vs(data: dict[str, Any]) -> RenderedComponent:
    left = dict(data.get("left") or {})
    right = dict(data.get("right") or {})
    if not left or not right:
        raise ValueError("No fallback renderer for comparison_vs: left and right are required")
    unit = str(data.get("unit", ""))
    title = _text(data.get("title", "Comparison"))
    left_value = _clamp(left.get("value"))
    right_value = _clamp(right.get("value"))
    panel_data = [
        (150, left, left_value, "url(#tdc-purple)", PALETTE["primary_soft"]),
        (760, right, right_value, "url(#tdc-teal)", PALETTE["secondary_soft"]),
    ]
    panels = []
    for x, item, value, fill, soft in panel_data:
        label = _text(item.get("label", "Option"))
        caption = _text(item.get("caption", ""))
        panels.append(
            f"""  <rect data-role="vs-panel" x="{x}" y="214" width="370" height="330" rx="34" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <rect x="{x + 28}" y="242" width="314" height="98" rx="28" fill="{soft}"/>
  <circle cx="{x + 82}" cy="291" r="32" fill="{fill}"/>
  <text x="{x + 82}" y="301" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="23" font-weight="840">{_percent_label(value, unit)}</text>
  <text x="{x + 42}" y="402" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="43" font-weight="800">{label}</text>
  <text x="{x + 42}" y="452" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="24">{caption}</text>
  <rect x="{x + 42}" y="486" width="270" height="20" rx="10" fill="{PALETTE['secondary_soft']}"/>
  <rect x="{x + 42}" y="486" width="{270 * value / 100:.2f}" height="20" rx="10" fill="{fill}"/>"""
        )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{PALETTE['surface_alt']}"/>
  <text x="640" y="118" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="56" font-weight="780">{title}</text>
  <text x="640" y="160" text-anchor="middle" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="23">Centered VS comparison with balanced contrast</text>
{chr(10).join(panels)}
  <path data-role="vs-connector" d="M 520 302 C 574 262, 616 262, 660 324" fill="none" stroke="{PALETTE['purple']}" stroke-width="9" stroke-linecap="round"/>
  <path data-role="vs-connector" d="M 760 458 C 704 500, 654 500, 620 396" fill="none" stroke="{PALETTE['teal']}" stroke-width="9" stroke-linecap="round"/>
  <circle data-role="vs-medallion" cx="640" cy="360" r="78" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <circle cx="640" cy="360" r="56" fill="url(#tdc-orange)"/>
  <text x="640" y="379" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="46" font-weight="880">VS</text>
"""
    svg = _svg_shell(body, class_name="tdc-comparison-vs-svg", aria_label=data.get("title", "Comparison"))
    return RenderedComponent(
        "comparison_vs",
        _component_html("comparison_vs", svg),
        svg,
        _metadata("comparison_vs", data, ["Centered VS comparison", "Two-color contrast"]),
    )


def render_dashboard(data: dict[str, Any]) -> RenderedComponent:
    kpis = list(data.get("kpis") or [])
    series = [_clamp(value) for value in list(data.get("series") or [])]
    bars = [_clamp(value) for value in list(data.get("bars") or [])]
    if not kpis or not series or not bars:
        raise ValueError("No fallback renderer for dashboard: kpis, series, and bars are required")
    title = _text(data.get("title", "Dashboard"))
    card_svgs = []
    card_specs = [
        (104, 142, 260, 140, 42, 188, 246),
        (408, 154, 176, 116, 32, 194, 242),
        (610, 154, 176, 116, 32, 194, 242),
    ]
    marker_fills = [PALETTE["emphasis"], PALETTE["series_3"], PALETTE["series_4"]]
    for index, kpi in enumerate(kpis[:3]):
        x, y, width, height, value_size, label_y, value_y = card_specs[index]
        value_text = _value_label(kpi.get("value"), str(kpi.get("unit", "")))
        label = _text(kpi.get("label", f"KPI {index + 1}"))
        fill = marker_fills[index]
        card_svgs.append(
            f"""  <rect data-role="dashboard-card" x="{x}" y="{y}" width="{width}" height="{height}" rx="24" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <circle data-role="dashboard-kpi-marker" cx="{x + width - 36}" cy="{y + 38}" r="18" fill="{fill}"/>
  <text x="{x + 26}" y="{value_y}" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="{value_size}" font-weight="840">{value_text}</text>
  <text data-role="dashboard-kpi-label" x="{x + 26}" y="{label_y}" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="18" font-weight="800">{label}</text>"""
        )
    line_min = min(series)
    line_max = max(series)
    line_span = max(line_max - line_min, 1)
    line_points = [
        (142 + index * 84, 542 - 170 * (value - line_min) / line_span)
        for index, value in enumerate(series[:7])
    ]
    bar_max = max(bars + [1])
    bar_svgs = []
    for index, value in enumerate(bars[:5]):
        height = 174 * value / bar_max
        x = 740 + index * 72
        y = 548 - height
        fill = _series_fill(index, len(bars[:5]))
        bar_svgs.append(f'  <rect data-role="dashboard-bar" x="{x}" y="{y:.2f}" width="42" height="{height:.2f}" rx="14" fill="{fill}"/>')
    donut_value = _clamp(kpis[1].get("value") if len(kpis) > 1 else 68)
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#f8fafc"/>
  <rect x="72" y="72" width="1136" height="576" rx="30" fill="#ffffff" filter="url(#tdc-shadow)"/>
  <text x="104" y="116" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="42" font-weight="780">{title}</text>
  <text x="828" y="116" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="22">Multi-chart management board</text>
{chr(10).join(card_svgs)}
  <rect x="104" y="312" width="552" height="264" rx="26" fill="#f8fafc"/>
  <line x1="140" y1="542" x2="620" y2="542" stroke="{PALETTE['line']}" stroke-width="3"/>
  <line x1="140" y1="456" x2="620" y2="456" stroke="{PALETTE['line']}" stroke-width="2"/>
  <line x1="140" y1="370" x2="620" y2="370" stroke="{PALETTE['line']}" stroke-width="2"/>
  <path data-role="dashboard-line" d="{_line_path(line_points)}" fill="none" stroke="{PALETTE['teal']}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="{line_points[-1][0]:.2f}" cy="{line_points[-1][1]:.2f}" r="13" fill="{PALETTE['teal']}" stroke="#ffffff" stroke-width="5"/>
  <rect x="704" y="312" width="426" height="264" rx="26" fill="#f8fafc"/>
{chr(10).join(bar_svgs)}
  <circle cx="1026" cy="210" r="72" fill="none" stroke="{PALETTE['primary_soft']}" stroke-width="24"/>
  <path data-role="dashboard-donut" d="{_arc_path(1026, 210, 72, donut_value)}" fill="none" stroke="url(#tdc-purple)" stroke-width="24" stroke-linecap="round"/>
  <text x="1026" y="220" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="32" font-weight="840">{_percent_label(donut_value, "%")}</text>
  <text x="1026" y="260" text-anchor="middle" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="17" font-weight="800">conversion</text>
"""
    svg = _svg_shell(body, class_name="tdc-dashboard-svg", aria_label=data.get("title", "Dashboard"))
    return RenderedComponent(
        "dashboard",
        _component_html("dashboard", svg),
        svg,
        _metadata("dashboard", data, ["Multi-chart dashboard"]),
    )


def render_map_data(data: dict[str, Any]) -> RenderedComponent:
    regions = list(data.get("regions") or [])
    if not regions:
        raise ValueError("No fallback renderer for map_data: regions are required")
    unit = str(data.get("unit", ""))
    title = _text(data.get("title", "Map data"))
    map_x = 396
    map_y = 174
    map_w = 744
    map_h = 416
    map_regions = [
        "M 424 278 C 492 226, 588 218, 654 260 C 620 302, 548 326, 458 326 Z",
        "M 630 280 C 704 228, 820 226, 906 274 C 854 328, 736 346, 648 322 Z",
        "M 490 364 C 566 326, 672 350, 730 414 C 650 464, 546 452, 474 410 Z",
        "M 746 388 C 842 342, 966 358, 1034 430 C 954 500, 828 490, 752 440 Z",
    ]
    region_svgs = [
        f'  <path data-role="map-region" d="{path}" fill="{PALETTE["map"]}" stroke="#f8fafc" stroke-width="8"/>'
        for path in map_regions
    ]
    bubbles = []
    legend_items = []
    for index, region in enumerate(regions[:3]):
        value = _clamp(region.get("value"))
        radius = 22 + value * 0.28
        raw_x = float(region.get("x", 440 + index * 180))
        raw_y = float(region.get("y", 320))
        x = max(map_x + radius + 24, min(map_x + map_w - radius - 24, raw_x))
        y = max(map_y + radius + 24, min(map_y + map_h - radius - 24, raw_y))
        label = _text(region.get("label", f"Region {index + 1}"))
        fill = ["url(#tdc-orange)", "url(#tdc-purple)", "url(#tdc-teal)"][index % 3]
        bubbles.append(
            f"""  <circle data-role="map-bubble" cx="{x:.2f}" cy="{y:.2f}" r="{radius:.2f}" fill="{fill}" opacity="0.94"/>
  <text x="{x:.2f}" y="{y + 8:.2f}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="21" font-weight="840">{_percent_label(value, unit)}</text>"""
        )
        legend_items.append(
            f"""    <circle cx="138" cy="{302 + index * 76}" r="20" fill="{fill}"/>
    <text x="138" y="{310 + index * 76}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="17" font-weight="840">0{index + 1}</text>
    <text x="178" y="{296 + index * 76}" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="820">{label}</text>
    <text x="178" y="{322 + index * 76}" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="18">Demand score</text>"""
        )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="{PALETTE['deep']}"/>
  <text x="92" y="112" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="52" font-weight="780">{title}</text>
  <text x="92" y="154" fill="{PALETTE['secondary_soft']}" font-family="{KOREAN_FONT_STACK}" font-size="23">Map cards with regional data tone</text>
  <rect x="86" y="226" width="278" height="314" rx="24" fill="#f8fafc"/>
  <g data-role="map-legend">
{chr(10).join(legend_items)}
  </g>
  <rect x="{map_x}" y="{map_y}" width="{map_w}" height="{map_h}" rx="28" fill="#f1f5f9"/>
{chr(10).join(region_svgs)}
{chr(10).join(bubbles)}
  <rect x="868" y="514" width="224" height="44" rx="22" fill="#ffffff" opacity="0.92"/>
  <text x="980" y="543" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="18" font-weight="820">SVG map geometry</text>
"""
    svg = _svg_shell(body, class_name="tdc-map-data-svg", aria_label=data.get("title", "Map data"))
    return RenderedComponent(
        "map_data",
        _component_html("map_data", svg),
        svg,
        _metadata("map_data", data, ["Map card layout", "Regional data tone"]),
    )


def render_process(data: dict[str, Any]) -> RenderedComponent:
    steps = list(data.get("steps") or [])
    if not steps:
        raise ValueError("No fallback renderer for process: steps are required")
    unit = str(data.get("unit", ""))
    title = _text(data.get("title", "Process"))
    step_svgs = []
    connectors = []
    start_x = 116
    step_w = 286
    step_h = 116
    gap = -18
    for index, step in enumerate(steps[:4]):
        x = start_x + index * (step_w + gap)
        y = 230
        fill = _series_fill(index, len(steps[:4]))
        label = _text(step.get("label", f"Step {index + 1}"))
        caption = _text(step.get("caption", ""))
        value = _clamp(step.get("value"))
        step_svgs.append(
            f"""  <polygon data-role="process-step" points="{_arrow_points(x, y, step_w, step_h, 42)}" fill="{fill}"/>
  <text x="{x + step_w / 2:.2f}" y="{y + 52}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="24" font-weight="860">{label}</text>
  <text x="{x + step_w / 2:.2f}" y="{y + 84}" text-anchor="middle" fill="#ffffff" font-family="{KOREAN_FONT_STACK}" font-size="18" font-weight="700">{caption}</text>
  <text x="{x + 56}" y="424" text-anchor="middle" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="38" font-weight="840">{_percent_label(value, unit)}</text>
  <text x="{x + 56}" y="456" text-anchor="middle" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="18" font-weight="800">step 0{index + 1}</text>"""
        )
        if index < 3:
            connectors.append(
                f'  <line data-role="process-connector" x1="{x + step_w - 18:.2f}" y1="{y + step_h / 2:.2f}" x2="{x + step_w + gap + 18:.2f}" y2="{y + step_h / 2:.2f}" stroke="#ffffff" stroke-width="5" stroke-linecap="round" opacity="0.7"/>'
            )
    body = f"""
  <rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
  <text x="116" y="132" fill="{PALETTE['ink']}" font-family="{KOREAN_FONT_STACK}" font-size="58" font-weight="780">{title}</text>
  <text x="116" y="176" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="23">Vivid arrows with sequential structure</text>
  <rect x="90" y="206" width="1100" height="298" rx="32" fill="#f8fafc"/>
{chr(10).join(step_svgs)}
{chr(10).join(connectors)}
  <circle cx="174" cy="586" r="22" fill="{_series_fill(0, 4)}"/>
  <circle cx="230" cy="586" r="22" fill="{_series_fill(1, 4)}"/>
  <circle cx="286" cy="586" r="22" fill="{_series_fill(2, 4)}"/>
  <circle cx="342" cy="586" r="22" fill="{_series_fill(3, 4)}"/>
  <text x="398" y="594" fill="{PALETTE['muted']}" font-family="{KOREAN_FONT_STACK}" font-size="22" font-weight="800">Real polygon arrows with four measured steps.</text>
"""
    svg = _svg_shell(body, class_name="tdc-process-svg", aria_label=data.get("title", "Process"))
    return RenderedComponent(
        "process",
        _component_html("process", svg),
        svg,
        _metadata("process", data, ["Arrow sequence", "Step structure"]),
    )


COMPONENTS: dict[str, Callable[[dict[str, Any]], RenderedComponent]] = {
    "big_percent": render_big_percent,
    "donut_gauge": render_donut_gauge,
    "bar_chart": render_bar_chart,
    "card_grid": render_card_grid,
    "funnel": render_funnel,
    "timeline": render_timeline,
    "matrix_2x2": render_matrix_2x2,
    "comparison_vs": render_comparison_vs,
    "dashboard": render_dashboard,
    "map_data": render_map_data,
    "process": render_process,
}


def render_component(component: str | None, data: dict[str, Any], theme: dict[str, Any] | None = None) -> RenderedComponent:
    if component not in COMPONENTS:
        raise ValueError(f"No fallback renderer for component: {component!r}")
    category = COMPONENT_CATEGORIES.get(component, "data")
    token = _ACTIVE_PALETTE.set(_resolve_palette(theme, category))
    try:
        return COMPONENTS[component](data)
    finally:
        _ACTIVE_PALETTE.reset(token)


def component_css() -> str:
    return f"""html {{
  box-sizing: border-box;
  background: #eef2f7;
  color: #111827;
  font-family: {KOREAN_FONT_STACK};
}}

*, *::before, *::after {{
  box-sizing: inherit;
}}

body {{
  margin: 0;
}}

.tdc-demo {{
  width: min(1440px, calc(100vw - 48px));
  margin: 0 auto;
  padding: 48px 0 72px;
}}

.tdc-demo-header {{
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 24px;
  align-items: end;
  margin-bottom: 28px;
}}

.tdc-demo-title {{
  margin: 0;
  font-size: 38px;
  line-height: 1.06;
  letter-spacing: 0;
}}

.tdc-demo-kicker {{
  margin: 0 0 10px;
  color: #2563eb;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}}

.tdc-demo-note {{
  max-width: 560px;
  margin: 0;
  color: #64748b;
  font-size: 17px;
  line-height: 1.55;
}}

.tdc-demo-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 28px;
}}

.tdc-component {{
  min-width: 0;
  aspect-ratio: 16 / 9;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 24px 60px rgba(15, 23, 42, 0.12);
}}

.tdc-svg {{
  display: block;
  width: 100%;
  height: 100%;
}}

.tdc-card-grid {{
  background: #f8fafc;
}}

.tdc-funnel {{
  background: #fef3c7;
}}

.tdc-dashboard {{
  background: #f8fafc;
}}

.tdc-map_data {{
  background: #071525;
}}

@media (max-width: 920px) {{
  .tdc-demo {{
    width: min(100vw - 24px, 720px);
    padding-top: 28px;
  }}

  .tdc-demo-header,
  .tdc-demo-grid {{
    grid-template-columns: 1fr;
  }}

  .tdc-demo-title {{
    font-size: 30px;
  }}
}}
"""


def _demo_html(rendered: list[RenderedComponent]) -> str:
    components = "\n".join(item.html for item in rendered)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TickDeck Axis 2 Components Demo</title>
  <link rel="stylesheet" href="components.css">
</head>
<body>
  <main class="tdc-demo">
    <header class="tdc-demo-header">
      <div>
        <p class="tdc-demo-kicker">TickDeck v3 Phase 1</p>
        <h1 class="tdc-demo-title">TickDeck Axis 2 Components Demo</h1>
      </div>
      <p class="tdc-demo-note">Eleven reusable visual components rendered from demo data with real SVG chart geometry and no text-only rendering path.</p>
    </header>
    <section class="tdc-demo-grid" aria-label="Axis 2 visual components">
{components}
    </section>
  </main>
</body>
</html>
"""


def _write_png(svg: str, out_path: Path) -> None:
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError("cairosvg is required to render component PNG files") from exc
    cairosvg.svg2png(bytestring=svg_for_png(svg).encode("utf-8"), write_to=str(out_path), output_width=WIDTH, output_height=HEIGHT)


def write_demo(output_dir: Path, theme: dict[str, Any] | None = None) -> DemoArtifact:
    output_dir.mkdir(parents=True, exist_ok=True)
    rendered = [render_component(name, DEMO_DATA[name], theme=theme) for name in COMPONENTS]
    css_path = output_dir / "components.css"
    html_path = output_dir / "demo.html"
    manifest_path = output_dir / "manifest.json"
    svg_paths: dict[str, Path] = {}
    png_paths: dict[str, Path] = {}

    css_path.write_text(component_css(), encoding="utf-8")
    html_path.write_text(_demo_html(rendered), encoding="utf-8")

    manifest = {
        "title": "TickDeck Axis 2 Components Demo",
        "components": [item.component for item in rendered],
        "metadata": {item.component: item.metadata for item in rendered},
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    for item in rendered:
        svg_path = output_dir / f"{item.component}.svg"
        png_path = output_dir / f"{item.component}.png"
        svg_path.write_text(item.svg, encoding="utf-8")
        _write_png(item.svg, png_path)
        svg_paths[item.component] = svg_path
        png_paths[item.component] = png_path

    return DemoArtifact(html_path, css_path, manifest_path, svg_paths, png_paths)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render TickDeck Axis 2 component demos.")
    parser.add_argument("--demo", type=Path, default=Path(__file__).resolve().parent / "demo", help="Output directory for demo HTML, SVG, and PNG files.")
    args = parser.parse_args(argv)
    artifact = write_demo(args.demo)
    print(f"demo_html={artifact.html_path}")
    for name, path in artifact.png_paths.items():
        print(f"{name}_png={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
