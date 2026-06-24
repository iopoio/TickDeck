#!/usr/bin/env python3
"""Bind TickDeck author page_specs JSON to deck_harness slides JSON."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


PIPELINE_DIR = Path(__file__).resolve().parent
V3_DIR = PIPELINE_DIR.parent
GENERATED_DIR = PIPELINE_DIR / "generated"
MANIFEST_PATH = V3_DIR / "axis2_layouts" / "components" / "manifest.json"

REFERENCE_NOTES_PER_SLIDE = 16

ALLOWED_LAYOUTS = {
    "ir_business_area_2col_card",
    "contest_cover_title_date_centered",
    "contest_history_timeline_bullet",
    "workflow_table_3col",
    "mobile_mockup_with_annotation_arrows",
    "multi_wireframe_dense_admin",
    "portfolio_cover_photo_brand_red",
    "title-hero",
    "editorial_impact_axes",
    "references_notes",
    "logo_grid",
    "funnel",
    "convergence_diagram",
    "thankyou",
    "section_divider_hero_text",
    "evolution_timeline",
    "conclusion_synthesis",
    "back_cover",
    "split_master",
    "chart_bar",
    "chart_donut",
    "chart_gauge",
    "chart_line",
    "chart_combo",
    "chart_kpi",
    "product_use_case_4step",
    "case_card_examples_pair",
    "data_visualization_2col_chart_text",
    "content-image",
    "3-card",
    "closing",
    "cover_split_brand_product",
    "cover_hero",
    "before_after_diagram_with_metric",
    "data_visualization_3col_chart",
    "requirements_excel_table",
    "tam_scenario_table",
    "wireframe_left_explanation_right",
    "narrative_centered_text_block",
    "corporate_research_navy_split_focus",
    "ir_company_overview_timeline_milestone",
    "single_page_complete_landing_mockup",
}

ROLES = {
    "cover",
    "agenda",
    "section_divider",
    "content",
    "section_synthesis",
    "conclusion",
    "references",
}
CONTENT_KINDS = {
    "market_numbers",
    "institution_forecasts",
    "comparison",
    "timeline_evolution",
    "concept_relation",
    "funnel_steps",
    "growth_drivers",
    "convergence",
    "implications",
    "split",
    "chart_bar",
    "chart_donut",
    "chart_gauge",
    "chart_line",
    "chart_combo",
    "chart_kpi",
    "narrative",
}

CHART_LAYOUTS = {
    "chart_bar",
    "chart_donut",
    "chart_gauge",
    "chart_line",
    "chart_combo",
    "chart_kpi",
}


def clean_text(value: Any, limit: int | None = None, *, preserve_markup: bool = False) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not preserve_markup:
        text = text.replace("**", "").replace("__", "")
    if limit and len(text) > limit:
        return text[: max(1, limit - 1)].rstrip() + "…"
    return text


def clean_subtitle(value: Any, limit: int) -> str:
    text = clean_text(value)
    return text if text and len(text) <= limit else ""


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON must be an object: {path}")
    return data


def load_axis1(path: Path) -> dict[str, Any]:
    """Load an Axis1 result only for build_deck output-directory decisions."""
    data = load_json(path)
    if not isinstance(data.get("topic"), str) or not data["topic"].strip():
        raise ValueError("missing required key: topic")
    final = (data.get("leader") or {}).get("final")
    if not isinstance(final, str) or not final.strip():
        raise ValueError("missing required key: leader.final")
    return data


def validate_page_specs(data: dict[str, Any]) -> None:
    if not isinstance(data.get("topic"), str) or not data["topic"].strip():
        raise ValueError("page_specs missing topic")
    if not isinstance(data.get("governing_thought_short"), str) or not data["governing_thought_short"].strip():
        raise ValueError("page_specs missing governing_thought_short")
    pages = data.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("page_specs pages must be a non-empty list")
    for idx, page in enumerate(pages, start=1):
        if not isinstance(page, dict):
            raise ValueError(f"pages[{idx}] must be an object")
        role = page.get("role")
        kind = page.get("content_kind")
        if role not in ROLES:
            raise ValueError(f"pages[{idx}] unsupported role: {role}")
        if kind not in CONTENT_KINDS:
            raise ValueError(f"pages[{idx}] unsupported content_kind: {kind}")
        if not isinstance(page.get("headline"), str) or not page["headline"].strip():
            raise ValueError(f"pages[{idx}] missing headline")
        if not isinstance(page.get("takeaways"), list):
            raise ValueError(f"pages[{idx}] takeaways must be a list")
        if not isinstance(page.get("payload"), dict):
            raise ValueError(f"pages[{idx}] payload must be an object")
        if not isinstance(page.get("sources"), list):
            raise ValueError(f"pages[{idx}] sources must be a list")
        if not isinstance(page.get("footnotes"), list):
            raise ValueError(f"pages[{idx}] footnotes must be a list")
    if not isinstance(data.get("references"), list):
        raise ValueError("page_specs references must be a list")


def load_page_specs(path: Path) -> dict[str, Any]:
    data = load_json(path)
    validate_page_specs(data)
    return data


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    manifest = load_json(path)
    mappings = manifest.get("layout_mappings")
    if not isinstance(mappings, list):
        raise ValueError("manifest layout_mappings must be a list")
    for entry in mappings:
        if not isinstance(entry, dict):
            raise ValueError("manifest entries must be objects")
        route = entry.get("route")
        candidates = entry.get("layout_candidates")
        if not isinstance(route, str) or not route:
            raise ValueError("manifest entry missing route")
        if not isinstance(candidates, list) or not candidates:
            raise ValueError(f"manifest route has no candidates: {route}")
        unknown = sorted(set(candidates) - ALLOWED_LAYOUTS)
        if unknown:
            raise ValueError(f"unknown deck_harness layouts for {route}: {unknown}")
    return manifest


def manifest_routes(manifest: dict[str, Any]) -> dict[str, list[str]]:
    return {entry["route"]: entry["layout_candidates"] for entry in manifest["layout_mappings"]}


def route_for_page(page: dict[str, Any]) -> str:
    role = page.get("role")
    if role in {"cover", "agenda", "section_divider", "references"}:
        return f"role:{role}"
    if role == "conclusion":
        return "role:conclusion"
    if role == "section_synthesis":
        return "role:section_synthesis"
    return f"kind:{page.get('content_kind')}"


# 작가가 page_specs에서 직접 지정할 수 있는 대담 레이아웃(패스스루). content_kind 라우팅으로
# 도달 못 하던 다크/에디토리얼/히어로 양식. payload 키를 슬라이드에 그대로 spread해 렌더한다.
EXPLICIT_LAYOUTS = {
    "corporate_research_navy_split_focus",
    "narrative_centered_text_block",
    "title-hero",
    "content-image",
    "case_card_examples_pair",
    "ir_company_overview_timeline_milestone",
    "single_page_complete_landing_mockup",
}
_STRUCTURAL_ROLES = {"cover", "agenda", "section_divider", "references", "conclusion"}


def explicit_layout_for(page: dict[str, Any]) -> str:
    layout = clean_text(page.get("layout"))
    if layout in EXPLICIT_LAYOUTS and page.get("role") not in _STRUCTURAL_ROLES:
        return layout
    return ""


def choose_layout(page: dict[str, Any], routes: dict[str, list[str]], counters: dict[str, int]) -> str:
    explicit = explicit_layout_for(page)
    if explicit:
        return explicit
    route = route_for_page(page)
    candidates = routes.get(route)
    if not candidates and route.startswith("role:"):
        candidates = routes.get(f"kind:{page.get('content_kind')}")
    if not candidates:
        raise ValueError(f"No deck_harness layout candidates for {route}")
    idx = counters.get(route, 0)
    counters[route] = idx + 1
    return candidates[idx % len(candidates)]


def source_records(page: dict[str, Any]) -> list[dict[str, str]]:
    payload = page.get("payload") or {}
    records: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    seen_names: set[str] = set()

    def add_record(raw: Any) -> None:
        if isinstance(raw, str) and "," in raw and "http" not in raw:
            for part in raw.split(","):
                add_record(part)
            return
        if isinstance(raw, dict):
            name = clean_text(raw.get("name") or raw.get("source") or raw.get("title"))
            url = clean_text(raw.get("url"))
            tag = clean_text(raw.get("tag"))
        else:
            name = clean_text(raw)
            url = ""
            tag = ""
        name = re.sub(r"^자료:\s*", "", name).strip()
        name_key = name.casefold()
        url_key = url.casefold()
        if not (url or name):
            return
        if (url_key and url_key in seen_urls) or (name_key and name_key in seen_names):
            return
        if url_key:
            seen_urls.add(url_key)
        if name_key:
            seen_names.add(name_key)
        record = {"name": name or url}
        if url:
            record["url"] = url
        if tag:
            record["tag"] = tag
        records.append(record)

    for source in page.get("sources") or []:
        add_record(source)

    payload_source = clean_text(payload.get("source")) if isinstance(payload, dict) else ""
    if payload_source:
        add_record(payload_source)
    if isinstance(payload, dict):
        for stat in payload.get("stats") or []:
            if isinstance(stat, dict):
                add_record(stat.get("source"))
    return records


def source_names(page: dict[str, Any]) -> list[str]:
    return [record["name"] for record in source_records(page)]


def source_text(page: dict[str, Any]) -> str:
    names = source_names(page)
    if not names:
        return ""
    shown = names[:3]
    suffix = f" 외 {len(names) - len(shown)}건" if len(names) > len(shown) else ""
    return "자료: " + ", ".join(shown) + suffix


def footnote_text(page: dict[str, Any]) -> str:
    pieces = []
    for note in page.get("footnotes") or []:
        if not isinstance(note, dict):
            continue
        term = clean_text(note.get("term"))
        en = clean_text(note.get("en"))
        definition = clean_text(note.get("def"))
        if not term:
            continue
        label = f"{term}({en})" if en else term
        pieces.append(f"{label}: {definition}" if definition else label)
    return " · ".join(pieces)


def takeaways(page: dict[str, Any], limit: int | None = None) -> list[str]:
    items = [clean_text(item, limit) for item in page.get("takeaways") or []]
    return [item for item in items if item]


def subtitle_from_takeaways(page: dict[str, Any], limit: int = 150) -> str:
    text = clean_text(" · ".join(takeaways(page)))
    return text if text and len(text) <= limit else ""


def dedupe_paragraphs_against_subtitle(paragraphs: list[str], subtitle: str) -> list[str]:
    if not subtitle:
        return paragraphs
    subtitle_norm = clean_text(subtitle)
    subtitle_parts = {clean_text(part) for part in re.split(r"\s*[·|]\s*", subtitle_norm) if clean_text(part)}
    return [
        paragraph
        for paragraph in paragraphs
        if clean_text(paragraph) != subtitle_norm and clean_text(paragraph) not in subtitle_parts
    ]


def chapter_num_from_nav(value: Any) -> str:
    text = clean_text(value)
    match = re.search(r"(?<!\d)(\d{1,2})(?=\s|[-_.]|$)", text)
    if not match:
        return ""
    return f"{int(match.group(1)):02d}"


def strip_leading_enumerator(value: Any) -> str:
    text = clean_text(value)
    return re.sub(r"^(?:[①②③④⑤⑥⑦⑧⑨⑩]|[0-9]{1,2}[.)])\s*", "", text).strip()


def is_caution_text(value: str) -> bool:
    text = clean_text(value)
    return text.startswith("[") or text.startswith("단,") or "해석 주의" in text


def split_action_takeaway(value: str) -> list[str]:
    text = clean_text(value)
    if not re.search(r"[①②③④⑤⑥⑦⑧⑨⑩]", text):
        return [strip_leading_enumerator(text)] if text else []
    parts = [strip_leading_enumerator(part) for part in re.split(r"[①②③④⑤⑥⑦⑧⑨⑩]\s*", text) if clean_text(part)]
    if parts and parts[0].endswith(":"):
        parts = parts[1:]
    return [part for part in parts if part]


def conclusion_actions_and_note(page: dict[str, Any]) -> tuple[list[dict[str, str]], str, str]:
    action_texts: list[str] = []
    note_texts: list[str] = []
    for item in takeaways(page, 140):
        if is_caution_text(item):
            note_texts.append(item)
            continue
        action_texts.extend(split_action_takeaway(item))

    body_parts: list[str] = []
    for paragraph in (page.get("payload") or {}).get("paragraphs") or []:
        text = clean_text(paragraph, 260)
        if not text:
            continue
        if is_caution_text(text):
            note_texts.append(text)
        else:
            body_parts.append(text)

    actions = [
        {"num": f"{idx:02d}", "text": clean_text(text, 90)}
        for idx, text in enumerate(action_texts[:5], start=1)
        if clean_text(text)
    ]
    note = " · ".join(dict.fromkeys(note_texts))
    body = clean_text(" ".join(body_parts), 260)
    return actions, note, body


def authority_fields(page: dict[str, Any]) -> dict[str, Any]:
    src = source_text(page)
    foot = footnote_text(page)
    records = source_records(page)
    fields = {
        "eyebrow": clean_text(page.get("section_nav")),
        "source": src,
        "caption": src,
        "footnotes": page.get("footnotes") or [],
        "footnote_text": foot,
    }
    if records:
        fields["source_map"] = {"sources": records}
        fields["evidence_ids"] = [record.get("url") or record["name"] for record in records]
    return {key: value for key, value in fields.items() if value not in ("", [], None)}


NUMBER_RE = r"-?\d+(?:,\d{3})*(?:\.\d+)?"
KOREAN_MONEY_UNITS = {"조": 10000.0, "억": 1.0, "만": 0.0001}
ENGLISH_MONEY_UNITS = {
    "m": 0.01,
    "million": 0.01,
    "millions": 0.01,
    "b": 10.0,
    "billion": 10.0,
    "billions": 10.0,
    "t": 10000.0,
    "trillion": 10000.0,
    "trillions": 10000.0,
}


def is_year_number(text: str, start: int, end: int) -> bool:
    if text[end : end + 2].startswith("년"):
        return True
    raw = text[start:end].replace(",", "")
    if not re.fullmatch(r"\d{4}", raw):
        return False
    year = int(raw)
    if not 1900 <= year <= 2099:
        return False
    before = text[:start].rstrip()
    after = text[end:].lstrip()
    has_direct_money_unit = bool(
        before.endswith("$")
        or re.match(r"(?i)(m|b|t)\b|(millions?|billions?|trillions?)\b", after)
        or after.startswith(("조", "억", "만"))
    )
    return not has_direct_money_unit


def parse_money_segment(segment: str) -> float | None:
    korean_values: list[tuple[str, float]] = []
    for match in re.finditer(rf"({NUMBER_RE})\s*(조|억|만)", segment):
        number = float(match.group(1).replace(",", ""))
        unit = match.group(2)
        korean_values.append((unit, number * KOREAN_MONEY_UNITS[unit]))
    if korean_values:
        units = {unit for unit, _ in korean_values}
        values = [number for _, number in korean_values]
        return sum(values) if {"조", "억"} <= units else max(values)

    money_marker = bool(re.search(r"[$]|원|달러|\b(?:usd|krw|dollars?|won)\b", segment, re.IGNORECASE))
    values: list[float] = []
    for match in re.finditer(NUMBER_RE, segment):
        if is_year_number(segment, match.start(), match.end()):
            continue
        number = float(match.group(0).replace(",", ""))
        after = segment[match.end() :].lstrip()
        unit_match = re.match(
            r"(?i)(m|b|t)\b|(millions?|billions?|trillions?)\b",
            after,
        )
        if unit_match and money_marker:
            unit = (unit_match.group(1) or unit_match.group(2)).lower()
            values.append(number * ENGLISH_MONEY_UNITS[unit])
        elif money_marker:
            values.append(number)
    return max(values) if values else None


def parsed_metric_value(value: Any) -> tuple[str, float] | None:
    text = str(value or "")
    if "%" in text:
        percentages = []
        for match in re.finditer(NUMBER_RE, text):
            if is_year_number(text, match.start(), match.end()):
                continue
            after = text[match.end() :].lstrip()
            if after.startswith("%"):
                percentages.append(float(match.group(0).replace(",", "")))
        if not percentages:
            return None
        return ("percent", max(percentages))

    money_values = [
        value
        for value in (parse_money_segment(part) for part in re.split(r"\s*(?:→|->|~|〜|–|—|\bto\b)\s*", text))
        if value is not None
    ]
    if money_values:
        return ("money", max(money_values))

    numbers: list[float] = []
    for match in re.finditer(NUMBER_RE, text):
        if is_year_number(text, match.start(), match.end()):
            continue
        number = float(match.group(0).replace(",", ""))
        numbers.append(number)
    if not numbers:
        return None
    return ("number", max(numbers))


def scaled_bar_pcts(values: list[Any]) -> list[float | None]:
    parsed = [parsed_metric_value(value) for value in values]
    max_by_axis: dict[str, float] = {}
    for item in parsed:
        if item is None:
            continue
        axis, number = item
        if axis != "percent":
            max_by_axis[axis] = max(max_by_axis.get(axis, 0.0), number)

    out: list[float | None] = []
    for item in parsed:
        if item is None:
            out.append(None)
            continue
        axis, number = item
        if axis == "percent":
            out.append(round(max(4.0, min(100.0, number)), 1))
            continue
        max_value = max_by_axis.get(axis) or number
        out.append(round(max(4.0, min(100.0, (number / max_value) * 100.0)), 1))
    return out


def coerce_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        compact = value.replace(",", "").strip().rstrip("%")
        try:
            return float(compact)
        except ValueError:
            return None
    return None


def number_values(values: Any) -> list[float | None]:
    if not isinstance(values, list):
        return []
    out = []
    for value in values:
        num = coerce_number(value)
        out.append(round(num, 4) if num is not None else None)
    return out


def chart_categories(values: Any, limit: int = 16) -> list[str]:
    if not isinstance(values, list):
        return []
    return [clean_text(value, 34) for value in values[:limit] if clean_text(value)]


def normalize_series(values: Any, *, default_name: str = "값") -> list[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    series = []
    for idx, item in enumerate(values, start=1):
        if not isinstance(item, dict):
            continue
        nums = number_values(item.get("values"))
        if not any(num is not None for num in nums):
            continue
        series.append(
            {
                "name": clean_text(item.get("name") or f"{default_name} {idx}", 30),
                "values": nums,
            }
        )
    return series


def normalize_bar_chart(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "bar",
        "categories": chart_categories(payload.get("categories")),
        "series": normalize_series(payload.get("series"), default_name="Series"),
        "orient": "h" if clean_text(payload.get("orient")).lower() == "h" else "v",
        "stacked": bool(payload.get("stacked")),
    }


def normalize_line_chart(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "line",
        "categories": chart_categories(payload.get("categories")),
        "series": normalize_series(payload.get("series"), default_name="Line"),
    }


def normalize_combo_chart(payload: dict[str, Any]) -> dict[str, Any]:
    categories = chart_categories(payload.get("categories"))
    bars = number_values(payload.get("bars"))
    line = number_values(payload.get("line"))
    series = []
    if bars:
        series.append({"name": clean_text(payload.get("bar_name") or "막대", 24), "type": "bar", "values": bars})
    if line:
        series.append({"name": clean_text(payload.get("line_name") or "추세", 24), "type": "line", "values": line})
    return {
        "type": "combo",
        "categories": categories,
        "series": series,
        "y2": clean_text(payload.get("y2"), 24),
    }


def normalize_share_chart(payload: dict[str, Any], chart_type: str) -> dict[str, Any]:
    value = coerce_number(payload.get("value"))
    percent_value = coerce_number(payload.get("percent"))
    max_value = coerce_number(payload.get("max")) or 100.0
    if value is None and percent_value is not None:
        value = (max_value * percent_value / 100.0) if payload.get("max") is not None else percent_value
    safe_value = max(0.0, value or 0.0)
    safe_max = max(safe_value, max_value, 1.0)
    percent = round(percent_value if percent_value is not None else (safe_value / safe_max) * 100.0, 1)
    return {
        "type": chart_type,
        "value": round(safe_value, 4),
        "max": round(safe_max, 4),
        "percent": percent,
        "label": clean_text(payload.get("label"), 40),
    }


def normalize_nested_chart(payload: dict[str, Any], default_type: str = "bar") -> dict[str, Any]:
    chart_type = clean_text(payload.get("type") or payload.get("chart_type") or default_type).lower()
    if chart_type == "bar":
        return normalize_bar_chart(payload)
    if chart_type == "line":
        return normalize_line_chart(payload)
    if chart_type == "combo":
        return normalize_combo_chart(payload)
    if chart_type in {"donut", "gauge"}:
        return normalize_share_chart(payload, chart_type)
    return normalize_bar_chart(payload)


def bind_chart(page: dict[str, Any], layout: str) -> dict[str, Any]:
    payload = page.get("payload") or {}
    slide = common_slide(page, layout)
    if layout == "chart_bar":
        slide["chart"] = normalize_bar_chart(payload)
    elif layout == "chart_donut":
        slide["chart"] = normalize_share_chart(payload, "donut")
    elif layout == "chart_gauge":
        slide["chart"] = normalize_share_chart(payload, "gauge")
    elif layout == "chart_line":
        slide["chart"] = normalize_line_chart(payload)
    elif layout == "chart_combo":
        slide["chart"] = normalize_combo_chart(payload)
    elif layout == "chart_kpi":
        slide["kpi"] = {
            "value": clean_text(payload.get("value"), 48),
            "label": clean_text(payload.get("label"), 64),
        }
        if isinstance(payload.get("chart"), dict):
            slide["chart"] = normalize_nested_chart(payload["chart"], "line")
        else:
            mini = number_values(payload.get("mini"))
            if any(num is not None for num in mini):
                slide["chart"] = {
                    "type": "line",
                    "categories": [str(idx) for idx in range(1, len(mini) + 1)],
                    "series": [{"name": "mini", "values": mini}],
                    "mini": True,
                }
    return slide


def common_slide(page: dict[str, Any], layout: str) -> dict[str, Any]:
    slide = {
        "layout": layout,
        "title": clean_text(page.get("headline"), 96, preserve_markup=True),
        "subtitle": subtitle_from_takeaways(page),
    }
    slide.update(authority_fields(page))
    return slide


def bind_explicit_layout(page: dict[str, Any]) -> dict[str, Any]:
    """작가가 직접 지정한 대담 레이아웃 — payload 키를 슬라이드에 spread해 해당 렌더러 슬롯을 채운다."""
    layout = clean_text(page.get("layout"))
    slide = common_slide(page, layout)
    payload = page.get("payload") or {}
    for key, value in payload.items():
        slide[key] = value
    if not any(payload.get(k) for k in ("paragraphs", "bullets", "cards", "focus", "cases", "milestones", "sections", "image")):
        slide["bullets"] = takeaways(page, 110)
    return slide


def has_market_payload(page: dict[str, Any]) -> bool:
    return bool((page.get("payload") or {}).get("stats"))


def has_table_payload(page: dict[str, Any]) -> bool:
    payload = page.get("payload") or {}
    return bool(payload.get("headers") and payload.get("rows"))


def has_list_payload(page: dict[str, Any], key: str) -> bool:
    return bool((page.get("payload") or {}).get(key))


def narrative_fallback(page: dict[str, Any]) -> dict[str, Any]:
    paragraphs = [clean_text(item, 260) for item in (page.get("payload") or {}).get("paragraphs") or [] if clean_text(item)]
    paragraphs_from_takeaways = False
    if not paragraphs:
        paragraphs = takeaways(page, 220)
        paragraphs_from_takeaways = True
    slide = common_slide(page, "narrative_centered_text_block")
    if paragraphs_from_takeaways:
        slide["subtitle"] = ""
    else:
        paragraphs = dedupe_paragraphs_against_subtitle(paragraphs, slide.get("subtitle", ""))
    slide["paragraphs"] = paragraphs
    return slide


def bind_cover(page: dict[str, Any], page_specs: dict[str, Any]) -> dict[str, Any]:
    return {
        "layout": "cover_hero",
        "cover": True,
        "brand_mark": "TickDeck",
        "title": clean_text(page.get("headline") or page_specs.get("governing_thought_short"), 92, preserve_markup=True),
        "subtitle": subtitle_from_takeaways(page, 180) or clean_subtitle(page_specs.get("governing_thought_short"), 120),
        "cover_meta": "",
    }


def bind_agenda(page: dict[str, Any], page_specs: dict[str, Any]) -> dict[str, Any]:
    payload = page.get("payload") or {}
    raw_sections = payload.get("sections") or []
    axes = []
    if raw_sections:
        for idx, section in enumerate(raw_sections[:6], start=1):
            if not isinstance(section, dict):
                continue
            axes.append(
                {
                    "num": clean_text(section.get("num") or f"{idx:02d}"),
                    "key": clean_text(section.get("key") or section.get("title"), 32),
                    "tag": clean_text(section.get("tag") or section.get("slogan"), 24),
                    "line": clean_text(section.get("line") or section.get("body"), 82),
                    "statStyle": "none",
                }
            )
    if not axes:
        axes = [
            {"num": f"{idx:02d}", "key": clean_text(item, 32), "tag": "", "line": "", "statStyle": "none"}
            for idx, item in enumerate(takeaways(page)[:6], start=1)
        ]
    return {
        "layout": "editorial_impact_axes",
        "kicker": "INDEX",
        "headline": "목차",
        "headline_mark": "목차",
        "subtitle": "",
        "axes": axes,
    }


def bind_section_divider(page: dict[str, Any]) -> dict[str, Any]:
    slide = {
        "layout": "section_divider_hero_text",
        "kicker": clean_text(page.get("section_nav") or page.get("section_id")),
        "chapter_num": chapter_num_from_nav(page.get("section_nav") or page.get("section_id")),
        "title": clean_text(page.get("headline"), 96, preserve_markup=True),
        "subtitle": subtitle_from_takeaways(page, 160),
    }
    # 간지 = Family B 다크 statement (챕터 경계 리듬). page.dark 또는 page.style로 켠다.
    if page.get("dark"):
        slide["style"] = {
            "bg": "#14211F", "ink": "#F3F1E9", "muted": "#A7B7B4",
            "panel": "#1B2C29", "line": "#2C3F3B",
            "accent-soft": "#1E332F",  # 거대 챕터 숫자 = 어두운 워터마크(제목 겹침 해소)
            "accent-dark": "#6FD3CF",  # 킥커 = 밝은 틸(다크 위 가독)
        }
    if isinstance(page.get("style"), dict):
        slide.setdefault("style", {}).update(page["style"])
    return slide


def bind_market_numbers(page: dict[str, Any], layout: str) -> dict[str, Any]:
    if not has_market_payload(page):
        return narrative_fallback(page)
    payload = page.get("payload") or {}
    stats = []
    raw_stats = [stat for stat in payload.get("stats") or [] if isinstance(stat, dict)]
    bar_pcts = scaled_bar_pcts([stat.get("value") for stat in raw_stats])
    for idx, stat in enumerate(raw_stats, start=1):
        item = {
            "label": clean_text(stat.get("label") or f"Metric {idx}", 28),
            "value": clean_text(stat.get("value"), 36),
            "note": clean_text(stat.get("note"), 110),
            "barCaption": clean_text(stat.get("source")),
        }
        if bar_pcts[idx - 1] is not None:
            item["barPct"] = bar_pcts[idx - 1]
        stats.append(item)
    if not stats:
        return narrative_fallback(page)
    slide = common_slide(page, layout)
    if layout == "data_visualization_2col_chart_text":
        slide["bars"] = [
            {"label": item["label"], "value": item["value"], "pct": item.get("barPct", 0)}
            for item in stats
        ]
        slide["body"] = clean_text(" ".join(item["note"] for item in stats if item.get("note")), 320)
        slide["bullets"] = takeaways(page, 88)
    else:
        slide["stats"] = stats
    return slide


def infer_split_right_kind(payload: dict[str, Any]) -> str:
    raw = clean_text(payload.get("right_kind")).lower()
    if raw in {"stats", "bullets", "table", "chart"}:
        return raw
    if isinstance(payload.get("chart"), dict):
        return "chart"
    if payload.get("stats"):
        return "stats"
    if (payload.get("headers") or payload.get("columns")) and payload.get("rows"):
        return "table"
    return "bullets"


def bind_split(page: dict[str, Any]) -> dict[str, Any]:
    payload = page.get("payload") or {}
    slide = common_slide(page, "split_master")
    paragraphs = [clean_text(item, 220) for item in payload.get("paragraphs") or [] if clean_text(item)]
    lead = clean_text(payload.get("lead") or (paragraphs[0] if paragraphs else ""), 220)
    if lead:
        slide["lead"] = lead
    slide["takeaways"] = takeaways(page, 120)

    right_kind = infer_split_right_kind(payload)
    slide["right_kind"] = right_kind
    if right_kind == "stats":
        stats = []
        for idx, stat in enumerate(payload.get("stats") or [], start=1):
            if not isinstance(stat, dict):
                continue
            stats.append(
                {
                    "label": clean_text(stat.get("label") or f"Metric {idx}", 34),
                    "value": clean_text(stat.get("value"), 36),
                    "note": clean_text(stat.get("note"), 90),
                }
            )
        slide["stats"] = stats
    elif right_kind == "table":
        headers = [clean_text(header, 34) for header in payload.get("headers") or payload.get("columns") or []]
        rows = payload.get("rows") or []
        slide["columns"] = headers
        slide["rows"] = row_dicts(headers, rows) if headers else rows
    elif right_kind == "chart":
        chart_payload = payload.get("chart") if isinstance(payload.get("chart"), dict) else payload
        slide["chart"] = normalize_nested_chart(chart_payload, "bar")
    else:
        raw_items = payload.get("right_items") or payload.get("bullets") or payload.get("items") or []
        slide["right_items"] = [
            clean_text(item.get("text") or item.get("body") or item.get("title") or item.get("label"), 110)
            if isinstance(item, dict)
            else clean_text(item, 110)
            for item in raw_items
            if clean_text(item.get("text") or item.get("body") or item.get("title") or item.get("label") if isinstance(item, dict) else item)
        ]
        if not slide["right_items"]:
            slide["right_items"] = slide["takeaways"]
    return slide


def row_dicts(headers: list[Any], rows: list[Any]) -> list[dict[str, str]]:
    cleaned_headers = [clean_text(header, 32) for header in headers]
    out = []
    for row in rows:
        values = row if isinstance(row, list) else [row.get(header, "") for header in cleaned_headers] if isinstance(row, dict) else []
        out.append(
            {
                header: clean_text(values[idx] if idx < len(values) else "", 120)
                for idx, header in enumerate(cleaned_headers)
            }
        )
    return out


def bind_table(page: dict[str, Any], layout: str) -> dict[str, Any]:
    if not has_table_payload(page):
        return narrative_fallback(page)
    payload = page.get("payload") or {}
    headers = [clean_text(header, 34) for header in payload.get("headers") or []]
    rows = payload.get("rows") or []
    slide = common_slide(page, layout)
    slide["source"] = slide.get("source") or (f"자료: {clean_text(payload.get('source'))}" if payload.get("source") else "")
    slide["caption"] = slide.get("caption") or slide.get("source", "")
    if layout == "tam_scenario_table":
        scenarios = headers[1:] or ["값"]
        slide["driver_header"] = headers[0] if headers else "구분"
        slide["scenarios"] = scenarios
        slide["rows"] = [
            {
                "driver": clean_text(row[0] if isinstance(row, list) and row else "", 56),
                "cells": [clean_text(cell, 80) for cell in (row[1:] if isinstance(row, list) else [])],
                "impacts": [],
            }
            for row in rows
        ]
    else:
        slide["columns"] = headers
        slide["rows"] = row_dicts(headers, rows)
        if headers:
            width = f"{100 / len(headers):.2f}%"
            slide["col_widths"] = [width for _ in headers]
    return slide


def bind_timeline(page: dict[str, Any], layout: str) -> dict[str, Any]:
    if not has_list_payload(page, "stages"):
        return narrative_fallback(page)
    stages = (page.get("payload") or {}).get("stages") or []
    slide = common_slide(page, layout)
    if layout == "evolution_timeline":
        slide["stages"] = [
            {
                "period": clean_text(stage.get("period") or stage.get("year") or f"{idx:02d}", 18),
                "label": clean_text(stage.get("label") or stage.get("title"), 54),
                "detail": clean_text(stage.get("detail") or stage.get("body") or stage.get("note"), 110),
            }
            for idx, stage in enumerate(stages[:5], start=1)
            if isinstance(stage, dict)
        ]
    elif layout == "ir_company_overview_timeline_milestone":
        slide["milestones"] = [
            {
                "year": clean_text(stage.get("period") or stage.get("year") or f"{idx:02d}", 18),
                "title": clean_text(stage.get("label") or stage.get("title"), 48),
                "note": clean_text(stage.get("detail") or stage.get("body"), 100),
            }
            for idx, stage in enumerate(stages, start=1)
            if isinstance(stage, dict)
        ]
    else:
        slide["events"] = [
            {
                "date": clean_text(stage.get("period") or stage.get("year") or f"{idx:02d}", 18),
                "label": clean_text(stage.get("label") or stage.get("title"), 56),
                "note": clean_text(stage.get("detail") or stage.get("body"), 80),
            }
            for idx, stage in enumerate(stages, start=1)
            if isinstance(stage, dict)
        ]
    return slide


def _normalize_panel(data: Any, default_title: str) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"label": default_title[:1], "title": default_title, "items": []}
    items = data.get("items") or data.get("bullets") or []
    return {
        "label": clean_text(data.get("label") or default_title[:1]),
        "title": clean_text(data.get("title") or default_title, 42),
        "items": items,
    }


def bind_concept_relation(page: dict[str, Any], layout: str) -> dict[str, Any]:
    payload = page.get("payload") or {}
    if not payload.get("before") or not payload.get("after"):
        return narrative_fallback(page)
    slide = common_slide(page, layout)
    slide["before"] = _normalize_panel(payload.get("before"), "현재")
    slide["after"] = _normalize_panel(payload.get("after"), "미래")
    relation = clean_text(payload.get("relation"))
    if relation:
        slide["relation"] = relation
    metric = payload.get("metric") if isinstance(payload.get("metric"), dict) else {}
    if metric and any(clean_text(metric.get(key)) for key in ("label", "value", "note")):
        slide["metric"] = {
            "label": clean_text(metric.get("label") or "핵심 전환", 28),
            "value": clean_text(metric.get("value") or "Before → After", 36),
            "note": clean_text(metric.get("note") or subtitle_from_takeaways(page), 80),
        }
    return slide


def bind_funnel(page: dict[str, Any], layout: str) -> dict[str, Any]:
    if not has_list_payload(page, "steps"):
        return narrative_fallback(page)
    steps = (page.get("payload") or {}).get("steps") or []
    slide = common_slide(page, layout)
    slide["stages"] = [
        {
            "stage": clean_text(step.get("label") or f"Step {idx}", 32),
            "tag": f"{idx:02d}",
            "desc": clean_text(step.get("body") or step.get("detail"), 110),
        }
        for idx, step in enumerate(steps, start=1)
        if isinstance(step, dict)
    ]
    return slide


def bind_growth_drivers(page: dict[str, Any], layout: str) -> dict[str, Any]:
    if not has_list_payload(page, "cards"):
        return narrative_fallback(page)
    cards = (page.get("payload") or {}).get("cards") or []
    slide = common_slide(page, layout)
    slide["cards"] = [
        {
            "kicker": f"{idx:02d}",
            "title": clean_text(strip_leading_enumerator(card.get("title")), 34),
            "body": clean_text(card.get("body"), 170),
        }
        for idx, card in enumerate(cards[:4], start=1)
        if isinstance(card, dict)
    ]
    return slide if slide["cards"] else narrative_fallback(page)


def bind_convergence(page: dict[str, Any]) -> dict[str, Any]:
    payload = page.get("payload") or {}
    drivers = payload.get("drivers") or []
    outcome = payload.get("outcome") or {}
    if not drivers or not isinstance(outcome, dict) or not outcome.get("title"):
        return narrative_fallback(page)
    slide = common_slide(page, "convergence_diagram")
    slide["drivers"] = [
        {
            "title": clean_text(strip_leading_enumerator(d.get("title")), 30),
            "body": clean_text(d.get("body"), 72),
        }
        for d in drivers[:5]
        if isinstance(d, dict) and clean_text(d.get("title"))
    ]
    slide["outcome"] = {
        "label": clean_text(outcome.get("label") or "결과", 16),
        "title": clean_text(outcome.get("title"), 44),
        "body": clean_text(outcome.get("body"), 120),
    }
    return slide if slide["drivers"] else narrative_fallback(page)


def bind_conclusion(page: dict[str, Any], page_specs: dict[str, Any]) -> dict[str, Any]:
    actions, note, body = conclusion_actions_and_note(page)
    slide = common_slide(page, "conclusion_synthesis")
    slide["title"] = clean_text(page_specs.get("governing_thought_short") or page.get("headline"), 96)
    slide["subtitle"] = ""
    if body:
        slide["body"] = clean_text(body, 150)  # 닫는 펀치라인(마무리 임팩트)
    slide["actions"] = actions
    if note:
        slide["note"] = clean_text(note, 220)
    return slide


def bind_narrative(page: dict[str, Any], layout: str) -> dict[str, Any]:
    slide = common_slide(page, layout)
    paragraphs = [clean_text(item, 220) for item in (page.get("payload") or {}).get("paragraphs") or [] if clean_text(item)]
    if layout == "closing":
        slide["bullets"] = takeaways(page, 90)
        if paragraphs and not slide.get("subtitle"):
            slide["subtitle"] = clean_subtitle(paragraphs[0], 160)
    else:
        paragraphs_from_takeaways = not paragraphs
        if paragraphs_from_takeaways:
            paragraphs = takeaways(page, 220)
            slide["subtitle"] = ""
        slide["paragraphs"] = dedupe_paragraphs_against_subtitle(
            paragraphs,
            slide.get("subtitle", ""),
        )
    return slide


def reference_notes(references: list[Any]) -> list[dict[str, str]]:
    notes = []
    seen: set[str] = set()
    for ref in references:
        if not isinstance(ref, dict):
            continue
        url = clean_text(ref.get("url"))
        if not url or url in seen:
            continue
        seen.add(url)
        notes.append(
            {
                "source": clean_text(ref.get("name") or ref.get("source") or "출처", 64),
                "title": url,
                "tag": clean_text(ref.get("tag"), 24),
            }
        )
    return notes


def bind_references(page_specs: dict[str, Any], page: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    refs = reference_notes((page or {}).get("payload", {}).get("references") or page_specs.get("references") or [])
    chunks = [refs[idx : idx + REFERENCE_NOTES_PER_SLIDE] for idx in range(0, len(refs), REFERENCE_NOTES_PER_SLIDE)]
    if not chunks and page is not None:
        chunks = [[]]
    slides = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        title = "참고자료" if total <= 1 else f"참고자료 ({idx}/{total})"
        slides.append(
            {
                "layout": "references_notes",
                "title": title,
                "subtitle": "본문 출처·수치 근거·용어 근거",
                "notes": chunk,
            }
        )
    return slides


def bind_back_cover(page_specs: dict[str, Any]) -> dict[str, Any]:
    title = clean_text(page_specs.get("topic"), 90)
    basis_date = clean_text(
        page_specs.get("basis_date")
        or page_specs.get("as_of")
        or datetime.now().astimezone().date().isoformat()
    )
    return {
        "layout": "back_cover",
        "cover": True,
        "brand_mark": "감사합니다",
        "disclaimer": "본 자료는 공개 출처를 종합한 참고용입니다",
        "basis_date": basis_date,
        "document_label": title,
    }


def bind_page(page: dict[str, Any], layout: str, page_specs: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
    role = page.get("role")
    kind = page.get("content_kind")
    if role == "cover":
        return bind_cover(page, page_specs)
    if role == "agenda":
        return bind_agenda(page, page_specs)
    if role == "section_divider":
        return bind_section_divider(page)
    if role == "references":
        return bind_references(page_specs, page)
    if role == "conclusion":
        return bind_conclusion(page, page_specs)
    if explicit_layout_for(page):
        return bind_explicit_layout(page)
    if kind == "split":
        return bind_split(page)
    if kind in CHART_LAYOUTS:
        return bind_chart(page, layout)
    if kind == "market_numbers":
        return bind_market_numbers(page, layout)
    if kind in {"institution_forecasts", "comparison"}:
        return bind_table(page, layout)
    if kind == "timeline_evolution":
        return bind_timeline(page, layout)
    if kind == "concept_relation":
        return bind_concept_relation(page, layout)
    if kind == "funnel_steps":
        return bind_funnel(page, layout)
    if kind == "growth_drivers":
        return bind_growth_drivers(page, layout)
    if kind == "convergence":
        return bind_convergence(page)
    return bind_narrative(page, layout)


def build_deck(page_specs_path: Path, theme: str | None = None) -> dict[str, Any]:
    page_specs = load_page_specs(Path(page_specs_path))
    manifest = load_manifest()
    routes = manifest_routes(manifest)
    counters: dict[str, int] = {}
    slides: list[dict[str, Any]] = []
    explicit_references = False

    for page in sorted(page_specs["pages"], key=lambda item: item.get("page_no") or 0):
        layout = choose_layout(page, routes, counters)
        bound = bind_page(page, layout, page_specs)
        if page.get("role") == "references":
            explicit_references = True
        if isinstance(bound, list):
            slides.extend(bound)
        else:
            slides.append(bound)

    if not explicit_references and page_specs.get("references"):
        slides.extend(bind_references(page_specs))

    slides.append(bind_back_cover(page_specs))

    # 섹션 내비탭용 챕터 목록 — 목차(editorial_impact_axes)의 axes에서 추출
    chapters: list[dict[str, str]] = []
    for slide in slides:
        if slide.get("layout") == "editorial_impact_axes":
            chapters = [
                {"num": clean_text(axis.get("num")), "key": clean_text(axis.get("key"), 16)}
                for axis in slide.get("axes", [])
                if clean_text(axis.get("key"))
            ]
            break

    title = clean_text(page_specs.get("topic"), 90)
    theme_id = clean_text(theme or page_specs.get("theme") or "TD_pantone_ink_light")
    return {
        "title": title,
        "theme": theme_id,
        "chapters": chapters,
        "brand": {
            "name": "TickDeck",
            "footer": title,
        },
        "slides": slides,
    }


def write_deck(deck: dict[str, Any], out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def default_out_path(page_specs_path: Path) -> Path:
    stem = Path(page_specs_path).stem
    safe = re.sub(r"[^\w가-힣]+", "_", stem).strip("_")[:80]
    return GENERATED_DIR / f"slides_{safe}.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="page_specs JSON -> deck_harness slides JSON")
    parser.add_argument("page_specs_json", help="TickDeck author page_specs JSON")
    parser.add_argument("--out", help="Output slides JSON path")
    parser.add_argument("--theme", help="deck_harness theme preset id")
    args = parser.parse_args(argv)

    page_specs_path = Path(args.page_specs_json).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve() if args.out else default_out_path(page_specs_path)
    deck = build_deck(page_specs_path, theme=args.theme)
    write_deck(deck, out_path)
    print(
        json.dumps(
            {
                "out": str(out_path),
                "slides": len(deck["slides"]),
                "title": deck["title"],
                "layouts": [slide["layout"] for slide in deck["slides"]],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
