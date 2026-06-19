#!/usr/bin/env python3
"""Axis1 leader.final to native deck_harness slides for TickDeck v3.

The engine consumes local Axis1 run JSON only. It does not call models, search,
or remote APIs. It emits deck_harness native layouts directly; SVG component
PNG image slots are not part of this path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


V3_ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = PIPELINE_DIR / "generated"
COMPONENT_ROOT = V3_ROOT / "axis2_layouts" / "components"
DEFAULT_MANIFEST_PATH = COMPONENT_ROOT / "manifest.json"
DEFAULT_STATE_PATH = GENERATED_DIR / "matching_rotation_state.json"
DEFAULT_DECK_HARNESS_BUILD = Path("/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py")

KOREAN_FONT_STACK = "'Malgun Gothic', NanumGothic, Pretendard, sans-serif"
SUPPORTED_NATIVE_LAYOUTS = {
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
    "thankyou",
    "section_divider_hero_text",
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
CONTENT_KIND_ORDER = [
    "market_numbers",
    "institution_forecasts",
    "growth_drivers",
    "implications",
]
FORBIDDEN_SLIDE_STRINGS = [
    "axis1 block",
    "CARD GRID",
    "Structured metric",
    "numeric_audit",
    "coverage",
]

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)]+)\)")
URL_RE = re.compile(r"https?://[^\s)|]+")
NUMBER_VALUE_PATTERNS = [
    re.compile(r"\d+(?:\.\d+)?\s*%"),
    re.compile(r"\d+\s*/\s*\d+"),
    re.compile(r"\d+\s*분의\s*\d+"),
    re.compile(r"\d[\d,]*(?:\.\d+)?\s*조\s*(?:\d[\d,]*(?:\.\d+)?\s*억\s*)?달러"),
    re.compile(r"\d[\d,]*(?:\.\d+)?\s*억\s*달러"),
    re.compile(r"\d[\d,]*(?:\.\d+)?\s*만\s*대"),
    re.compile(r"\d[\d,]*(?:\.\d+)?\s*달러"),
]
SOURCE_LABEL_HINTS = {
    "AdCellerant": ["AdCellerant", "WSJ", "Neil Patel", "AEO", "숏폼", "프라이버시"],
    "Gartner": ["Gartner", "CMO", "오프라인", "모바일 앱"],
    "Forrester": ["Forrester", "신뢰", "100억", "챗봇"],
    "Deloitte Digital": ["Deloitte", "진정성", "경제 압박", "재정의"],
}


def load_manifest(path: Path = DEFAULT_MANIFEST_PATH) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    mappings = manifest.get("layout_mappings")
    if not isinstance(mappings, list):
        raise ValueError("layout manifest must contain a layout_mappings list")

    required_fields = {"content_kind", "layout_candidates", "data_slots", "source_fields"}
    seen = set()
    for entry in mappings:
        missing = sorted(required_fields - set(entry))
        if missing:
            raise ValueError(f"layout manifest entry missing fields: {missing}")
        kind = entry["content_kind"]
        candidates = entry["layout_candidates"]
        if not kind or not isinstance(candidates, list) or not candidates:
            raise ValueError(f"layout manifest entry has empty candidates: {kind}")
        unknown = sorted(set(candidates) - SUPPORTED_NATIVE_LAYOUTS)
        if unknown:
            raise ValueError(f"unknown deck_harness layouts for {kind}: {unknown}")
        if "shot" in candidates:
            raise ValueError("shot/image-slot layouts are forbidden in TickDeck v3 matching")
        if any("image" in str(slot).lower() for slot in entry.get("data_slots", [])):
            raise ValueError(f"image data slot is forbidden in layout mapping: {kind}")
        seen.add(kind)

    expected = {"market_numbers", "institution_forecasts", "growth_drivers", "implications", "references"}
    missing = sorted(expected - seen)
    if missing:
        raise ValueError(f"layout manifest missing content kinds: {missing}")
    return manifest


def load_axis1(path: Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = ["topic", "leader", "numeric_audit", "glossary", "fetch_stats"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"missing required Axis1 keys: {', '.join(missing)}")
    return data


def clean_md(text: Any, limit: int | None = None) -> str:
    value = MARKDOWN_LINK_RE.sub(r"\1", str(text or ""))
    value = re.sub(r"https?://\S+", "", value)
    value = re.sub(r"[\U00010000-\U0010ffff]", "", value)
    value = re.sub(r"(^|\n)\s*#{1,6}\s*", r"\1", value)
    value = re.sub(r"[*_>`]", "", value)
    value = re.sub(r"\s+", " ", value).strip(" -\n\t")
    if limit and len(value) > limit:
        return value[: max(0, limit - 1)].rstrip() + "…"
    return value


def strip_markdown_links(text: str) -> str:
    return MARKDOWN_LINK_RE.sub(r"\1", str(text or ""))


def strip_source_tail(text: str) -> str:
    value = str(text or "")
    value = re.split(r"\n\s*---\s*\n", value, maxsplit=1)[0]
    value = re.split(r"\n\s*\*{0,2}출처\*{0,2}\s*[:：]", value, maxsplit=1)[0]
    return value.strip()


def split_section_blocks(report: str) -> list[dict[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", report or "", flags=re.M))
    blocks: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(report)
        title = clean_md(match.group(1))
        body = strip_source_tail(str(report[start:end]).strip())
        if title and body:
            blocks.append({"title": title, "body": body})
    return blocks


def split_sections(report: str) -> dict[str, str]:
    return {section["title"]: section["body"] for section in split_section_blocks(report)}


def pick_section(sections: list[dict[str, str]], keywords: list[str], *, exclude: set[str] | None = None) -> dict[str, str] | None:
    exclude = exclude or set()
    for section in sections:
        if section["title"] in exclude:
            continue
        if any(keyword in section["title"] for keyword in keywords):
            return section
    return None


def source_refs_from_report(report: str) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen = set()
    source_started = False
    for line in str(report or "").splitlines():
        if "출처" in line:
            source_started = True
        if not source_started:
            continue
        for label, url in MARKDOWN_LINK_RE.findall(line):
            if url in seen:
                continue
            seen.add(url)
            refs.append({"label": clean_md(label, 48), "url": url})
        plain_urls = URL_RE.findall(line)
        if plain_urls:
            label_text = clean_md(line.split(plain_urls[0], 1)[0].strip(":-| "), 48)
            for url in plain_urls:
                if url in seen:
                    continue
                seen.add(url)
                refs.append({"label": label_text or urlparse(url).netloc.replace("www.", ""), "url": url})
    return refs


def source_refs_from_axis1(data: dict[str, Any]) -> list[dict[str, str]]:
    refs = source_refs_from_report(data.get("leader", {}).get("final") or "")
    if refs:
        return refs

    seen = set()
    fallback: list[dict[str, str]] = []
    for flag in data.get("numeric_audit", {}).get("flags", []):
        url = flag.get("evidence_url")
        if not url or not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        fallback.append({"label": urlparse(url).netloc.replace("www.", ""), "url": url})
    for term in data.get("glossary", {}).get("terms", []):
        url = term.get("source_url")
        if not url or not url.startswith("http") or url in seen:
            continue
        seen.add(url)
        fallback.append({"label": str(term.get("term") or urlparse(url).netloc.replace("www.", "")), "url": url})
    return fallback


def source_urls_from_axis1(data: dict[str, Any]) -> list[str]:
    return [ref["url"] for ref in source_refs_from_axis1(data)]


def source_map_for_text(data: dict[str, Any], text: str) -> list[dict[str, str]]:
    refs = source_refs_from_axis1(data)
    if not refs:
        return []

    haystack = clean_md(text).lower()
    matched: list[dict[str, str]] = []
    for ref in refs:
        label = ref["label"]
        hints = SOURCE_LABEL_HINTS.get(label, [label])
        if any(hint.lower() in haystack for hint in hints):
            matched.append(ref)
    return matched or refs[:1]


def markdown_table_rows(section: str) -> list[dict[str, str]]:
    rows = []
    table_lines = [line.strip() for line in str(section or "").splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return rows
    header = [clean_md(cell) for cell in table_lines[0].strip("|").split("|")]
    for line in table_lines[1:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if not cells or all(set(cell.strip()) <= {"-", ":"} for cell in cells):
            continue
        rows.append({header[index]: clean_md(strip_markdown_links(cell), 180) for index, cell in enumerate(cells[: len(header)])})
    return rows


def split_inline_numbered_items(text: str) -> list[str]:
    value = str(text or "").strip()
    if not value:
        return []
    pieces = re.split(r"(?=(?:[①②③④⑤⑥⑦⑧⑨]|\d+[.)])\s*)", value)
    return [piece.strip() for piece in pieces if clean_md(piece)]


def markdown_list_items(section: str) -> list[str]:
    items: list[str] = []
    for raw in str(section or "").splitlines():
        line = raw.strip()
        if not line or line.startswith("|") or set(line) <= {"-", ":", "|", " "}:
            continue
        match = re.match(r"^(?:[-*+]|\d+[.)]|[①②③④⑤⑥⑦⑧⑨])\s*(.+)$", line)
        if match:
            items.append(match.group(1).strip())
            continue
        inline_items = split_inline_numbered_items(line)
        if len(inline_items) > 1:
            items.extend(inline_items)
    return items


def sentence_chunks(text: str, count: int | None = None, limit: int = 120) -> list[str]:
    cleaned = re.sub(r"\n+", " ", str(text or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []
    pieces = [
        clean_md(piece, limit)
        for piece in re.split(r"(?<=[.!?다])\s+|(?<=\))\s+", cleaned)
        if clean_md(piece)
    ]
    if count is None:
        return pieces
    return pieces[:count]


def extract_number_label(text: str) -> str | None:
    for pattern in NUMBER_VALUE_PATTERNS:
        match = pattern.search(str(text or ""))
        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip()
    return None


def parse_percent(value: Any) -> float | None:
    text = str(value or "")
    if "%" not in text:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", text.replace(",", ""))
    if not match:
        return None
    return max(0.0, min(100.0, float(match.group(1))))


def metric_number(value: Any) -> float | None:
    pct = parse_percent(value)
    if pct is not None:
        return pct
    match = re.search(r"\d+(?:\.\d+)?", str(value or "").replace(",", ""))
    return float(match.group(0)) if match else None


def title_and_caption(raw: str, *, keep_parenthetical: bool = True) -> tuple[str, str]:
    value = strip_markdown_links(raw)
    value = re.sub(r"^\s*(?:[-*+]|\d+[.)]|[①②③④⑤⑥⑦⑧⑨])\s*", "", value).strip()
    bold = re.match(r"^\*\*([^*]+)\*\*\s*(?:[:：—-]\s*)?(.*)$", value)
    if bold:
        label = bold.group(1).strip()
        caption = bold.group(2).strip()
    else:
        parts = re.split(r"\s*(?:[:：]|—)\s*", value, maxsplit=1)
        label = parts[0].strip()
        caption = parts[1].strip() if len(parts) > 1 else value
    label = clean_md(label, 54)
    if not keep_parenthetical:
        label = clean_md(re.sub(r"\s*\([^)]*\)", "", label), 54)
    return label, clean_md(caption or value, 160)


def is_suspected_numeric_flag(flag: dict[str, Any]) -> bool:
    status_text = f"{flag.get('flag', '')} {flag.get('status', '')}".lower()
    if flag.get("found") is False:
        return True
    return any(token in status_text for token in ["환각", "미발견", "사람 확인", "suspect"])


def suspected_numeric_values(data: dict[str, Any]) -> list[str]:
    return [
        str(flag.get("number"))
        for flag in data.get("numeric_audit", {}).get("flags", [])
        if flag.get("number") and is_suspected_numeric_flag(flag)
    ]


def scrub_suspected_numeric_values(text: str, suspected_values: list[str]) -> str:
    cleaned = str(text or "")
    for value in sorted(suspected_values, key=len, reverse=True):
        cleaned = cleaned.replace(value, "")
    cleaned = re.sub(r"\*\*\s*\*\*", "", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned


def parse_metric_items(*sections: str) -> list[dict[str, Any]]:
    metrics: list[dict[str, Any]] = []
    seen = set()
    for section in sections:
        candidates = markdown_list_items(section)
        if not candidates:
            candidates = sentence_chunks(section, None, 180)
        for item in candidates:
            value = extract_number_label(item)
            if not value or value in seen:
                continue
            seen.add(value)
            label, caption = title_and_caption(item)
            metrics.append({
                "label": label,
                "value_label": value,
                "value": metric_number(value),
                "caption": caption,
            })
    return metrics


def parse_forecasts(section: str, data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    rows = markdown_table_rows(section)
    forecasts = []
    for row in rows:
        institution = row.get("기관") or next(iter(row.values()), "")
        prediction = row.get("핵심 예측") or " ".join(value for key, value in row.items() if key != "기관")
        value_label = extract_number_label(prediction)
        forecasts.append({
            "label": clean_md(institution, 42),
            "caption": clean_md(prediction, 180),
            "value_label": value_label,
            "value": metric_number(value_label),
        })
    if forecasts:
        return forecasts

    for item in markdown_list_items(section):
        label, caption = title_and_caption(item)
        value_label = extract_number_label(item)
        forecasts.append({
            "label": label,
            "caption": caption,
            "value_label": value_label,
            "value": metric_number(value_label),
        })
    if forecasts:
        return forecasts

    refs = source_refs_from_axis1(data or {}) if data else []
    sentences = sentence_chunks(section, 3, 180)
    for index, sentence in enumerate(sentences):
        label = refs[index]["label"] if index < len(refs) else f"전망 {index + 1}"
        value_label = extract_number_label(sentence)
        forecasts.append({
            "label": clean_md(label, 42),
            "caption": clean_md(sentence, 180),
            "value_label": value_label,
            "value": metric_number(value_label),
        })
    return forecasts


def parse_driver_items(section: str) -> list[dict[str, Any]]:
    drivers = []
    for item in markdown_list_items(section):
        label, caption = title_and_caption(item, keep_parenthetical=False)
        value_label = extract_number_label(item)
        drivers.append({
            "label": label,
            "caption": caption,
            "value_label": value_label,
            "value": metric_number(value_label),
        })
    return drivers


def section_summary(section: str, limit: int = 150) -> str:
    chunks = sentence_chunks(section, 1, limit)
    return chunks[0] if chunks else clean_md(section, limit)


def short_label(text: str, fallback: str = "") -> str:
    cleaned = clean_md(text, 42)
    for token in ["—", ":", "·"]:
        if token in cleaned:
            cleaned = cleaned.split(token, 1)[0].strip()
    return cleaned[:28] or fallback


def _build_metric_block(section: dict[str, str], all_clean_report: str, data: dict[str, Any]) -> dict[str, Any]:
    metrics = parse_metric_items(all_clean_report)
    percent_metrics = [metric for metric in metrics if parse_percent(metric.get("value_label")) is not None]
    ordered = percent_metrics + [metric for metric in metrics if metric not in percent_metrics]
    refs = source_map_for_text(data, section["body"])
    return {
        "id": "market_numbers",
        "title": section["title"],
        "text": clean_md(section["body"], 620),
        "metrics": ordered,
        "source_urls": [ref["url"] for ref in refs],
    }


def _build_forecast_block(section: dict[str, str], data: dict[str, Any]) -> dict[str, Any]:
    forecasts = parse_forecasts(section["body"], data)
    refs_by_label = {ref["label"]: ref["url"] for ref in source_refs_from_axis1(data)}
    for forecast in forecasts:
        ref = refs_by_label.get(forecast["label"])
        if not ref:
            mapped = source_map_for_text(data, f"{forecast['label']} {forecast['caption']}")
            ref = mapped[0]["url"] if mapped else ""
        forecast["source_url"] = ref
    return {
        "id": "institution_forecasts",
        "title": section["title"],
        "text": clean_md(section["body"], 620),
        "rows": forecasts,
        "source_urls": [row["source_url"] for row in forecasts if row.get("source_url")],
    }


def _build_drivers_block(section: dict[str, str], data: dict[str, Any]) -> dict[str, Any]:
    drivers = parse_driver_items(section["body"])
    for driver in drivers:
        mapped = source_map_for_text(data, f"{driver['label']} {driver['caption']}")
        driver["source_url"] = mapped[0]["url"] if mapped else ""
    return {
        "id": "growth_drivers",
        "title": section["title"],
        "text": clean_md(section["body"], 620),
        "items": drivers,
        "source_urls": [item["source_url"] for item in drivers if item.get("source_url")],
    }


def _build_implications_block(section: dict[str, str]) -> dict[str, Any]:
    paragraphs = sentence_chunks(section["body"], 3, 170)
    return {
        "id": "implications",
        "title": section["title"],
        "text": clean_md(section["body"], 620),
        "paragraphs": paragraphs,
        "source_urls": [],
    }


def extract_content_blocks(data: dict[str, Any]) -> list[dict[str, Any]]:
    report = data.get("leader", {}).get("final") or ""
    suspected_values = suspected_numeric_values(data)
    clean_report = scrub_suspected_numeric_values(report, suspected_values)
    sections = split_section_blocks(clean_report)
    used_titles: set[str] = set()
    blocks: list[dict[str, Any]] = []

    market = pick_section(sections, ["시장", "규모", "수치", "성장"])
    if market:
        used_titles.add(market["title"])
        block = _build_metric_block(market, clean_report, data)
        if block["metrics"]:
            blocks.append(block)

    forecast = None
    for section in sections:
        if section["title"] in used_titles:
            continue
        if markdown_table_rows(section["body"]) or any(token in section["title"] for token in ["기관", "전망", "판매"]):
            forecast = section
            break
    if forecast:
        used_titles.add(forecast["title"])
        block = _build_forecast_block(forecast, data)
        if block["rows"]:
            blocks.append(block)

    drivers = pick_section(sections, ["동인", "성장 동인"], exclude=used_titles)
    if drivers:
        used_titles.add(drivers["title"])
        block = _build_drivers_block(drivers, data)
        if block["items"]:
            blocks.append(block)

    implications = pick_section(sections, ["시사점", "결론", "리스크", "위험", "주의"], exclude=used_titles)
    if implications:
        used_titles.add(implications["title"])
        block = _build_implications_block(implications)
        if block["paragraphs"] or block["text"]:
            blocks.append(block)

    return sorted(blocks, key=lambda block: CONTENT_KIND_ORDER.index(block["id"]) if block["id"] in CONTENT_KIND_ORDER else 99)


def classify_content_block(block: dict[str, Any]) -> str:
    block_id = str(block.get("id") or "")
    if block_id in {"market_numbers", "institution_forecasts", "growth_drivers", "implications", "references"}:
        return block_id
    title = str(block.get("title") or "")
    if block.get("metrics") or any(token in title for token in ["시장", "규모", "수치"]):
        return "market_numbers"
    if block.get("rows") or any(token in title for token in ["기관", "전망"]):
        return "institution_forecasts"
    if block.get("items") or "동인" in title:
        return "growth_drivers"
    return "implications"


def match_layout_for_kind(kind: str, manifest: dict[str, Any], rotation: int = 0) -> str:
    candidates = []
    for entry in manifest.get("layout_mappings", []):
        if entry.get("content_kind") == kind:
            candidates = list(entry.get("layout_candidates") or [])
            break
    if not candidates:
        raise ValueError(f"No deck_harness layout registered for content kind: {kind}")
    return candidates[rotation % len(candidates)]


def _load_state(path: Path) -> dict[str, int]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _write_state(path: Path, state: dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_rotation(state: dict[str, int], topic: str, kind: str) -> int:
    key = hashlib.sha1(f"{topic}|{kind}".encode("utf-8")).hexdigest()
    value = int(state.get(key, -1)) + 1
    state[key] = value
    return value


def _source_note(data: dict[str, Any], urls: list[str]) -> str:
    refs = source_refs_from_axis1(data)
    labels = [ref["label"] for ref in refs if ref["url"] in set(urls)]
    if not labels:
        labels = [ref["label"] for ref in refs[:3]]
    return "출처: " + " · ".join(labels[:4]) if labels else ""


def _card_body(item: dict[str, Any]) -> str:
    caption = clean_md(item.get("caption"), 90)
    value = item.get("value_label")
    if value and value not in caption:
        prefix = f"{value} · "
        return clean_md(prefix + caption, 90)
    return caption


def _metric_stats(block: dict[str, Any]) -> list[dict[str, Any]]:
    stats = []
    for metric in block.get("metrics", []):
        pct = parse_percent(metric.get("value_label"))
        if pct is None:
            continue
        stat = {
            "label": clean_md(metric.get("label"), 26),
            "value": metric["value_label"],
            "barPct": pct,
            "barCaption": clean_md(metric.get("caption"), 42),
            "note": clean_md(metric.get("caption"), 70),
        }
        stats.append(stat)
        if len(stats) == 3:
            break
    if not stats:
        raise ValueError(f"no verified percentage metrics for block: {block.get('id')}")
    return stats


def _metric_bars(block: dict[str, Any]) -> list[dict[str, Any]]:
    bars = []
    for metric in block.get("metrics", []):
        pct = parse_percent(metric.get("value_label"))
        if pct is None:
            continue
        bars.append({
            "label": clean_md(metric.get("label"), 14),
            "value": metric["value_label"],
            "pct": pct,
        })
        if len(bars) == 5:
            break
    if not bars:
        raise ValueError(f"no verified percentage bars for block: {block.get('id')}")
    return bars


def _forecast_rows(block: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for item in block.get("rows", [])[:4]:
        rows.append({
            "기관": clean_md(item.get("label"), 28),
            "핵심 예측": clean_md(item.get("caption"), 105),
            "실수치": clean_md(item.get("value_label") or "", 22),
        })
    return rows


def build_native_slide(block: dict[str, Any], layout: str, axis1: dict[str, Any]) -> dict[str, Any]:
    if layout not in SUPPORTED_NATIVE_LAYOUTS:
        raise ValueError(f"unknown deck_harness layout: {layout}")

    kind = classify_content_block(block)
    title = clean_md(block.get("title"), 64)
    source_urls = [url for url in block.get("source_urls", []) if url]

    if layout == "data_visualization_3col_chart":
        return {
            "layout": layout,
            "section": "MARKET NUMBERS",
            "title": title,
            "subtitle": "본문에 확인된 실제 수치만 표시",
            "stats": _metric_stats(block),
            "source": _source_note(axis1, source_urls),
        }

    if layout == "data_visualization_2col_chart_text":
        return {
            "layout": layout,
            "section": "MARKET NUMBERS",
            "title": title,
            "subtitle": "숫자와 맥락을 분리해 읽는 요약",
            "bars": _metric_bars(block),
            "body": clean_md(block.get("text"), 230),
            "source": _source_note(axis1, source_urls),
        }

    if layout == "requirements_excel_table":
        rows = _forecast_rows(block)
        if not rows:
            raise ValueError("institution forecast table requires rows from leader.final")
        return {
            "layout": layout,
            "section": "FORECASTS",
            "title": title,
            "subtitle": "기관별 핵심 예측과 본문 수치를 보존",
            "columns": ["기관", "핵심 예측", "실수치"],
            "col_widths": ["18%", "64%", "18%"],
            "rows": rows,
        }

    if layout == "tam_scenario_table":
        rows = []
        for item in block.get("rows", [])[:4]:
            value = clean_md(item.get("value_label") or "정성", 18)
            rows.append({
                "driver": clean_md(item.get("label"), 30),
                "tam": clean_md(item.get("caption"), 48),
                "cells": [value],
                "impacts": [clean_md(item.get("caption"), 36)],
            })
        if not rows:
            raise ValueError("institution forecast scenario table requires rows from leader.final")
        return {
            "layout": layout,
            "section": "FORECASTS",
            "title": title,
            "subtitle": "기관별 전망을 한 열 시나리오로 압축",
            "scenarios": ["핵심 예측"],
            "driver_header": "기관",
            "rows": rows,
            "source": _source_note(axis1, source_urls),
        }

    if layout == "3-card":
        cards = [
            {
                "kicker": f"{index:02d}",
                "title": clean_md(item.get("label"), 32),
                "body": _card_body(item),
            }
            for index, item in enumerate(block.get("items", []), start=1)
        ]
        if not cards:
            raise ValueError("3-card layout requires leader.final list items")
        return {
            "layout": layout,
            "section": "GROWTH DRIVERS",
            "title": title,
            "subtitle": f"{len(cards)}개 항목을 더미 없이 그대로 매핑",
            "cards": cards,
        }

    if layout == "product_use_case_4step":
        steps = [
            {
                "title": clean_md(item.get("label"), 28),
                "body": _card_body(item),
            }
            for item in block.get("items", [])
        ]
        if not steps:
            raise ValueError("product_use_case_4step layout requires leader.final list items")
        return {
            "layout": layout,
            "section": "GROWTH DRIVERS",
            "title": title,
            "subtitle": f"{len(steps)}개 성장 동인을 순서대로 표시",
            "steps": steps,
        }

    if layout == "narrative_centered_text_block":
        paragraphs = [clean_md(text, 170) for text in (block.get("paragraphs") or sentence_chunks(block.get("text", ""), 3, 170))]
        if not paragraphs:
            raise ValueError("narrative layout requires implication paragraphs")
        return {
            "layout": layout,
            "section": "IMPLICATIONS",
            "eyebrow": "IMPLICATIONS",
            "title": title,
            "subtitle": "leader.final 시사점 원문 기반",
            "paragraphs": paragraphs,
        }

    if layout == "closing":
        paragraphs = [clean_md(text, 120) for text in (block.get("paragraphs") or sentence_chunks(block.get("text", ""), 2, 120))]
        subtitle = clean_md(paragraphs[0] if paragraphs else block.get("text", ""), 82)
        bullets = [clean_md(text, 56) for text in paragraphs[1:2]]
        return {
            "layout": layout,
            "section": "IMPLICATIONS",
            "eyebrow": "IMPLICATIONS",
            "title": title,
            "subtitle": subtitle,
            "bullets": bullets,
        }

    if layout == "references_notes":
        notes = reference_notes(axis1)
        if not notes:
            raise ValueError("references_notes requires leader.final sources")
        return {
            "layout": layout,
            "section": "SOURCES",
            "title": "출처",
            "subtitle": "leader.final 하단 출처를 그대로 유지",
            "notes": notes,
        }

    raise ValueError(f"layout adapter not implemented: {layout} for {kind}")


def reference_notes(data: dict[str, Any]) -> list[dict[str, str]]:
    notes = []
    for ref in source_refs_from_axis1(data):
        notes.append({
            "source": ref["label"],
            "title": ref["url"],
            "tag": "leader.final",
        })
    return notes[:8]


def safe_stem(path: Path) -> str:
    safe = re.sub(r"[^\w가-힣]+", "_", Path(path).stem).strip("_")
    return safe[:80] or "axis1"


def build_deck_payload(data: dict[str, Any], matched_slides: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    topic = data["topic"]
    topic_label = clean_md(topic.replace(" 전망", ""))
    return {
        "title": f"{topic} matched deck",
        "theme": "T04_meeting_blue",
        "brand": {
            "name": "TickDeck v3",
            "footer": "TickDeck v3 · Axis1 Matching Engine",
            "accent": "#1e40af",
            "accent_dark": "#16306e",
            "accent_soft": "#dbe7ff",
            "background": "#f7f9fc",
            "ink": "#13233b",
            "muted": "#56677e",
            "panel": "#ffffff",
            "line": "#d3deef",
            "body_font": KOREAN_FONT_STACK,
            "display_font": KOREAN_FONT_STACK,
            "label_font": KOREAN_FONT_STACK,
        },
        "slides": [
            {
                "layout": "cover_hero",
                "cover_variant": "left",
                "brand_mark": "TickDeck v3",
                "title": topic_label,
                "subtitle": "leader.final 기반 네이티브 deck_harness 덱",
                "cover_meta": data.get("ran_at", ""),
            },
            *matched_slides,
        ],
    }


def _assert_no_forbidden_slide_strings(deck: dict[str, Any]) -> None:
    text = json.dumps(deck, ensure_ascii=False)
    hits = [token for token in FORBIDDEN_SLIDE_STRINGS if token in text]
    hits.extend(re.findall(r"핵심\s+[0-9]", text))
    if hits:
        raise ValueError(f"forbidden placeholder/meta strings in deck payload: {sorted(set(hits))}")


def build_matched_deck(
    result_json: Path,
    *,
    output_dir: Path | None = None,
    state_path: Path | None = DEFAULT_STATE_PATH,
    manifest_path: Path = DEFAULT_MANIFEST_PATH,
    render_harness: bool = False,
    harness_out: Path | None = None,
    deck_harness_build: Path = DEFAULT_DECK_HARNESS_BUILD,
) -> dict[str, Any]:
    result_path = Path(result_json).expanduser().resolve()
    data = load_axis1(result_path)
    manifest = load_manifest(manifest_path)
    if output_dir is None:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        output_dir = GENERATED_DIR / f"matched_{safe_stem(result_path)}_{stamp}"
    output_dir = Path(output_dir).expanduser().resolve()

    state = _load_state(Path(state_path)) if state_path else {}
    next_state = dict(state)
    matched_slides = []
    matches = []
    topic = data["topic"]

    for block in extract_content_blocks(data):
        kind = classify_content_block(block)
        rotation = _next_rotation(next_state, topic, kind) if state_path else 0
        layout = match_layout_for_kind(kind, manifest, rotation=rotation)
        slide = build_native_slide(block, layout, data)
        matched_slides.append(slide)
        matches.append({
            "block_id": block["id"],
            "content_kind": kind,
            "layout": layout,
            "rotation": rotation,
            "source_urls": block.get("source_urls", []),
        })

    refs_kind = "references"
    refs_rotation = _next_rotation(next_state, topic, refs_kind) if state_path else 0
    refs_layout = match_layout_for_kind(refs_kind, manifest, rotation=refs_rotation)
    refs_slide = build_native_slide({"id": refs_kind, "title": "출처"}, refs_layout, data)
    matched_slides.append(refs_slide)
    matches.append({
        "block_id": "references",
        "content_kind": refs_kind,
        "layout": refs_layout,
        "rotation": refs_rotation,
        "source_urls": source_urls_from_axis1(data),
    })

    deck = build_deck_payload(data, matched_slides, output_dir)
    _assert_no_forbidden_slide_strings(deck)
    output_dir.mkdir(parents=True, exist_ok=True)
    deck_path = output_dir / "slides.json"
    deck_path.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf-8")
    if state_path:
        _write_state(Path(state_path), next_state)

    harness_payload = None
    if render_harness:
        harness_payload = render_deck_harness(deck_path, harness_out or (output_dir / "deck_harness"), deck_harness_build)

    return {
        "deck": deck,
        "deck_path": str(deck_path),
        "component_artifacts": [],
        "matches": matches,
        "harness": harness_payload,
    }


def render_deck_harness(deck_path: Path, out_dir: Path, build_script: Path = DEFAULT_DECK_HARNESS_BUILD) -> dict[str, Any]:
    build_script = Path(build_script).expanduser().resolve()
    if not build_script.exists():
        raise FileNotFoundError(f"deck_harness build.py not found: {build_script}")
    harness_root = build_script.parents[1]
    python_bin = harness_root / ".venv" / "bin" / "python"
    if not python_bin.exists():
        python_bin = Path(sys.executable)

    out_dir = Path(out_dir).resolve()
    cmd = [str(python_bin), str(build_script), str(Path(deck_path).resolve()), "--out", str(out_dir)]
    completed = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "deck_harness render failed\n"
            f"cmd: {' '.join(cmd)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )
    validation_path = out_dir / "validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else None
    return {
        "out_dir": str(out_dir),
        "validation_path": str(validation_path),
        "validation": validation,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Axis1 JSON -> native deck_harness slides JSON")
    parser.add_argument("result_json", help="TickDeck/v3 axis1 result JSON")
    parser.add_argument("--out-dir", help="Output directory for slides.json")
    parser.add_argument("--state", default=str(DEFAULT_STATE_PATH), help="Rotation state JSON path")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST_PATH), help="Native layout manifest path")
    parser.add_argument("--harness-out", help="deck_harness output directory")
    parser.add_argument("--deck-harness-build", default=str(DEFAULT_DECK_HARNESS_BUILD), help="deck_harness src/build.py path")
    parser.add_argument("--no-render-harness", action="store_true", help="Only write matched deck JSON")
    args = parser.parse_args(argv)

    result = build_matched_deck(
        Path(args.result_json),
        output_dir=Path(args.out_dir) if args.out_dir else None,
        state_path=Path(args.state) if args.state else None,
        manifest_path=Path(args.manifest),
        render_harness=not args.no_render_harness,
        harness_out=Path(args.harness_out) if args.harness_out else None,
        deck_harness_build=Path(args.deck_harness_build),
    )
    print(json.dumps({
        "deck_path": result["deck_path"],
        "slides": len(result["deck"]["slides"]),
        "layouts": [match["layout"] for match in result["matches"]],
        "harness_out": result["harness"]["out_dir"] if result["harness"] else None,
        "validation_issues": result["harness"]["validation"]["summary"]["total_issues"] if result["harness"] else None,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
