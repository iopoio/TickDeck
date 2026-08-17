#!/usr/bin/env python3
"""Pure TickDeck v2 page-budget functions for LAYOUT_ALGORITHM §A–§C.

Phase 1 accepts a measured calibration entry and independently verifies all eight
runtime dimensions before using it.  Spec-gate orchestration is a later phase.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


CALIBRATION_DIR = Path(__file__).resolve().parents[1] / "calibration"
if str(CALIBRATION_DIR) not in sys.path:
    sys.path.insert(0, str(CALIBRATION_DIR))

from predictor import (  # noqa: E402
    KEY_DIMENSIONS,
    CalibrationFormatError,
    CalibrationRuntimeKeyError,
    css_hash,
    font_build_hash,
    renderer_struct_hash,
    validate_key,
)
from render_deck import (  # noqa: E402
    _block_type,
    _first_block_text,
    _format_metric_value,
    _iter_metric_ids,
    _iter_source_ids,
    _metric_source_ids,
    _page_has_per_card_sources,
    _page_title_text,
    _source_row_ids_after_caption,
    _viz_caption_source_ids,
    normalize_registry,
)


GAP_PX = 24.0
SPLIT_OUTER_GAP_PX = 14.0
SPLIT_NOTE_MARGIN_PX = 18.0
SPLIT_PANE_GAP_PX = 22.0
SPLIT_METRIC_HEIGHT_PX = 132.0
OVERFLOW_MARGIN_PX = 50.0
SPARSE_MARGIN_PX = 240.0
NO_CHROME_EYEBROW_DEDUCTION_PX = 14.0
NO_CHROME_TWO_LINE_TITLE_DEDUCTION_PX = 52.0
METRIC_TOKEN_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


class LayoutBudgetInputError(ValueError):
    """The spec, registry, or measured calibration entry is malformed."""


class _RenderMeasurementRequired(RuntimeError):
    pass


class BudgetVerdict(str, Enum):
    FIT = "FIT"
    SPARSE = "SPARSE"
    OVERFLOW = "OVERFLOW"
    RENDER_MEASURE_REQUIRED = "RENDER_MEASURE_REQUIRED"


@dataclass(frozen=True)
class PageBudget:
    page_id: str
    verdict: BudgetVerdict
    height_px: float | None
    capacity_px: float | None
    overflow_cutoff_px: float | None
    sparse_cutoff_px: float | None
    reasons: tuple[str, ...] = ()


def cpl(width: float, font: float) -> int:
    if width <= 0 or font <= 0:
        raise LayoutBudgetInputError("width and font must be positive")
    value = math.floor(width / (font * 0.78))
    if value < 1:
        raise LayoutBudgetInputError("width/font produces zero characters per line")
    return value


def line_count(chars: int, width: float, font: float) -> int:
    if not isinstance(chars, int) or chars < 0:
        raise LayoutBudgetInputError("chars must be a non-negative integer")
    return max(1, math.ceil(chars / cpl(width, font)))


def _normalized_registry(registry: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    try:
        return normalize_registry(dict(registry))
    except (TypeError, ValueError) as exc:
        raise LayoutBudgetInputError(str(exc)) from exc


def substitute_metric_tokens(text: str, registry: Mapping[str, Any]) -> str:
    normalized = _normalized_registry(registry)

    def replace(match: re.Match[str]) -> str:
        metric_id = match.group(1)
        metric = normalized["metrics"].get(metric_id)
        if not isinstance(metric, dict):
            raise LayoutBudgetInputError(f"unknown metric token: {metric_id}")
        try:
            return _format_metric_value(metric)
        except ValueError as exc:
            raise LayoutBudgetInputError(f"invalid registry metric {metric_id}: {exc}") from exc

    return METRIC_TOKEN_PATTERN.sub(replace, str(text))


def metric_grid_height(metric_count: int) -> float:
    if not isinstance(metric_count, int) or metric_count < 1:
        raise LayoutBudgetInputError("metric_grid requires at least one metric")
    rows: list[float] = []
    remaining = metric_count
    while remaining:
        take = min(4, remaining)
        rows.append(202.0 if take == 4 else 170.0)
        remaining -= take
    return sum(rows) + 20.0 * (len(rows) - 1)


def _table_rows(block: Mapping[str, Any]) -> tuple[list[Any], list[Any]]:
    columns = block.get("columns")
    rows = block.get("rows")
    if not isinstance(columns, list) or not 2 <= len(columns) <= 6:
        raise LayoutBudgetInputError("text_table columns must contain 2 to 6 items")
    if not isinstance(rows, list):
        raise LayoutBudgetInputError("text_table rows must be a list")
    for index, row in enumerate(rows):
        if not isinstance(row, list) or len(row) != len(columns):
            raise LayoutBudgetInputError(f"text_table row {index} must match column count")
    return columns, rows


def text_table_height(block: Mapping[str, Any], registry: Mapping[str, Any]) -> float:
    columns, rows = _table_rows(block)
    row_count = len(rows)
    font = 13.5 if row_count <= 5 else 13.0
    column_width = (1080.0 - 24.0) / len(columns)
    text_width = column_width - 16.0
    extra_lines: list[int] = []
    for row in rows:
        cell_lines = [
            line_count(len(substitute_metric_tokens(str(cell), registry)), text_width, font)
            for cell in row
        ]
        extra_lines.append(max(cell_lines, default=1) - 1)

    titled = bool(str(block.get("title", "")).strip())
    if row_count <= 5:
        return (37.0 if titled else 0.0) + 40.0 + sum(
            38.5 + 20.0 * extra for extra in extra_lines
        )
    if row_count <= 8:
        return (30.0 if titled else 0.0) + 35.0 + 33.0 * row_count + 20.0 * sum(extra_lines)
    return (28.0 if titled else 0.0) + 32.0 + 28.3 * row_count + 20.0 * sum(extra_lines)


def viz_signature(block: Mapping[str, Any]) -> str:
    series = block.get("series")
    if not isinstance(series, list) or not series:
        raise LayoutBudgetInputError("viz requires a non-empty series list")
    chart = str(block.get("chart", "")).strip()
    if not chart:
        raise LayoutBudgetInputError("viz chart is required")
    try:
        canonical_block = json.dumps(
            dict(block),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise LayoutBudgetInputError(f"viz block is not canonical JSON: {exc}") from exc
    block_hash = hashlib.sha256(canonical_block.encode("utf-8")).hexdigest()
    signature_parts = [
            chart,
            f"series={len(series)}",
            f"size={str(block.get('size', '')).strip() or 'default'}",
            f"title={int(bool(str(block.get('title', '')).strip()))}",
            f"note={int(bool(str(block.get('note', '')).strip()))}",
            f"title_style={str(block.get('title_style', '')).strip() or 'default'}",
            f"source_caption={str(block.get('source_caption', '')).strip() or 'off'}",
    ]
    if all(str(block.get(field, "")).strip() for field in ("exhibit", "title", "subtitle")):
        signature_parts.append("title_layers=3")
    signature_parts.append(f"block_sha256={block_hash}")
    return "|".join(signature_parts)


def split_viz_height(raw_viz_height: float) -> float:
    return float(raw_viz_height) * 0.72


def _calibration_values(calibration: Mapping[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    if not isinstance(calibration, Mapping):
        raise LayoutBudgetInputError("calibration must be one resolved measured entry")
    try:
        key = validate_key(calibration.get("key", {}))
    except CalibrationFormatError as exc:
        raise _RenderMeasurementRequired(f"calibration key cannot be confirmed: {exc}") from exc
    provenance = calibration.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("status") != "measured":
        raise _RenderMeasurementRequired("calibration entry is not measured")
    values = calibration.get("values")
    if not isinstance(values, dict):
        raise LayoutBudgetInputError("calibration entry values must be an object")
    return key, values


def block_height(
    block: Mapping[str, Any],
    registry: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> float:
    if not isinstance(block, Mapping):
        raise LayoutBudgetInputError("content block must be an object")
    block_type = str(block.get("type", "text")).strip()
    _key, values = _calibration_values(calibration)

    if block_type in {"headline", "title"}:
        text = substitute_metric_tokens(str(block.get("text", "")), registry)
        return 33.5 * line_count(len(text), 960.0, 24.0) - 8.0 + 4.0
    if block_type in {"body", "text", "summary"}:
        text = substitute_metric_tokens(str(block.get("text", "")), registry)
        return 28.0 * line_count(len(text), 980.0, 18.0) + 18.0 + 18.0
    if block_type in {"callout", "note"}:
        text = substitute_metric_tokens(str(block.get("text", "")), registry)
        if block.get("emphasis"):
            return 44.0 + 45.0 * line_count(len(text), 968.0, 30.0) + 14.0
        return 36.0 + 30.0 * line_count(len(text), 972.0, 20.0) + 14.0
    if block_type == "metric":
        metric_id = str(block.get("metric_id", "")).strip()
        if metric_id not in _normalized_registry(registry)["metrics"]:
            raise LayoutBudgetInputError(f"unknown metric_id: {metric_id}")
        return 172.0
    if block_type in {"metrics", "metric_grid", "stat_grid"}:
        metric_ids = block.get("metric_ids")
        if not isinstance(metric_ids, list) or not metric_ids:
            raise LayoutBudgetInputError("metric_grid requires metric_ids")
        known = _normalized_registry(registry)["metrics"]
        missing = [str(metric_id) for metric_id in metric_ids if str(metric_id) not in known]
        if missing:
            raise LayoutBudgetInputError(f"unknown metric_ids: {missing}")
        return metric_grid_height(len(metric_ids))
    if block_type == "text_table":
        return text_table_height(block, registry)
    if block_type == "viz":
        heights = values.get("viz_heights_px")
        signature = viz_signature(block)
        if not isinstance(heights, dict) or signature not in heights:
            raise _RenderMeasurementRequired(f"unmeasured viz combination: {signature}")
        raw_height = float(heights[signature])
        return raw_height + 8.0 + 6.0
    if block_type in {"image", "bullets", "list", "footnote"}:
        raise _RenderMeasurementRequired(f"unmodeled block requires renderer measurement: {block_type}")
    raise _RenderMeasurementRequired(f"unmodeled block requires renderer measurement: {block_type}")


def page_height(block_heights: Sequence[float]) -> float:
    heights = [float(height) for height in block_heights]
    if any(height < 0 for height in heights):
        raise LayoutBudgetInputError("block heights must not be negative")
    return sum(heights) + GAP_PX * max(0, len(heights) - 1)


def split_page_height(
    lead_height: float,
    left_height: float,
    right_height: float,
    note_height: float = 0.0,
) -> float:
    rows = [float(lead_height), max(float(left_height), float(right_height))]
    if note_height:
        rows.append(float(note_height) + SPLIT_NOTE_MARGIN_PX)
    return sum(rows) + SPLIT_OUTER_GAP_PX * max(0, len(rows) - 1)


def sibling_vertical_overlaps(
    ranges: Sequence[tuple[str, float, float]],
) -> tuple[tuple[str, str, float], ...]:
    overlaps: list[tuple[str, str, float]] = []
    for index, (name, top, bottom) in enumerate(ranges):
        for other_name, other_top, other_bottom in ranges[index + 1 :]:
            depth = min(float(bottom), float(other_bottom)) - max(float(top), float(other_top))
            if depth > 0:
                overlaps.append((str(name), str(other_name), depth))
    return tuple(overlaps)


def _split_layout_height(
    blocks: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> float:
    remaining = list(blocks)
    lead = remaining.pop(0) if remaining and _block_type(remaining[0]) in {"headline", "title"} else None
    note = next((block for block in remaining if _block_type(block) == "note"), None)
    if note is not None:
        remaining.remove(note)

    visual_index = next(
        (
            index
            for index, block in enumerate(remaining)
            if _block_type(block) in {"viz", "metric_grid", "metrics", "stat_grid"}
            or (_block_type(block) == "text_table" and len(block.get("rows", [])) <= 4)
        ),
        None,
    )
    if visual_index is None:
        midpoint = max(1, len(remaining) // 2)
        left, right = remaining[:midpoint], remaining[midpoint:]
    else:
        left = [remaining[visual_index]]
        right = [block for index, block in enumerate(remaining) if index != visual_index]

    def pane_height(pane: Sequence[Mapping[str, Any]]) -> float:
        heights = [
            SPLIT_METRIC_HEIGHT_PX
            if _block_type(block) == "metric"
            else block_height(block, registry, calibration)
            for block in pane
        ]
        return sum(heights) + SPLIT_PANE_GAP_PX * max(0, len(heights) - 1)

    return split_page_height(
        block_height(lead, registry, calibration) if lead is not None else 0.0,
        pane_height(left),
        pane_height(right),
        block_height(note, registry, calibration) if note is not None else 0.0,
    )


def classify_height(height: float, capacity: float) -> BudgetVerdict:
    if height > capacity - OVERFLOW_MARGIN_PX:
        return BudgetVerdict.OVERFLOW
    if height < capacity - SPARSE_MARGIN_PX:
        return BudgetVerdict.SPARSE
    return BudgetVerdict.FIT


def split_fits(left_height: float, right_height: float, cutoff: float) -> bool:
    return max(left_height, right_height) <= cutoff and abs(left_height - right_height) <= 160.0


def linear_partition_impossible(height: float, capacity: float) -> bool:
    return height - GAP_PX < 2.0 * (capacity - SPARSE_MARGIN_PX)


def _page_requires_source_row_measurement(
    page: Mapping[str, Any], registry: Mapping[str, Any]
) -> bool:
    normalized = _normalized_registry(registry)
    raw_content = page.get("content")
    if not isinstance(raw_content, list):
        raise LayoutBudgetInputError("page content must be a list")
    content = [dict(block) if isinstance(block, Mapping) else block for block in raw_content]
    page_dict = dict(page)
    page_dict["content"] = content
    page_id = str(page.get("page_id", "?")).strip() or "?"
    try:
        if _page_has_per_card_sources(content, page_id, normalized):
            return False
        cited_source_ids = list(_iter_source_ids(content))
        for metric_id in _iter_metric_ids(page_dict):
            cited_source_ids.extend(_metric_source_ids(metric_id, page_id, normalized))
        caption_source_ids: list[str] = []
        for block in content:
            if _block_type(block) == "viz":
                caption_source_ids.extend(_viz_caption_source_ids(block, page_id, normalized))
        return bool(_source_row_ids_after_caption(cited_source_ids, caption_source_ids))
    except ValueError as exc:
        raise LayoutBudgetInputError(str(exc)) from exc


def _runtime_dimension(value: Any, name: str) -> str:
    normalized = str(value).strip() if value is not None else ""
    if not normalized:
        raise _RenderMeasurementRequired(
            f"runtime calibration key dimension is missing: {name}"
        )
    return normalized


def _page_capacity(
    page: Mapping[str, Any],
    content: list[Any],
    registry: Mapping[str, Any],
    *,
    base_capacity: float,
    page_chrome: str,
    layout: str,
) -> float:
    if page_chrome != "none":
        return base_capacity

    page_dict = dict(page)
    renderer_content = [dict(block) if isinstance(block, Mapping) else block for block in content]
    title = _page_title_text(page_dict, renderer_content, layout)
    if not title:
        raise _RenderMeasurementRequired("chrome-none title line count cannot be confirmed")
    resolved_title = substitute_metric_tokens(title, registry)
    title_lines = line_count(len(resolved_title), 980.0, 44.0)
    if title_lines > 2:
        raise _RenderMeasurementRequired("chrome-none title over two lines is uncalibrated")

    capacity = base_capacity
    eyebrow_text = _first_block_text(renderer_content, {"eyebrow"})
    if eyebrow_text and page.get("eyebrow_chip"):
        raise _RenderMeasurementRequired("chrome-none eyebrow_chip height is uncalibrated")
    if eyebrow_text:
        capacity -= NO_CHROME_EYEBROW_DEDUCTION_PX
    if title_lines == 2:
        capacity -= NO_CHROME_TWO_LINE_TITLE_DEDUCTION_PX
    if capacity <= 0:
        raise LayoutBudgetInputError("adjusted capacity_px must be positive")
    return capacity


def _measurement_result(page_id: str, reason: str, capacity: float | None = None) -> PageBudget:
    return PageBudget(
        page_id=page_id,
        verdict=BudgetVerdict.RENDER_MEASURE_REQUIRED,
        height_px=None,
        capacity_px=capacity,
        overflow_cutoff_px=None if capacity is None else capacity - OVERFLOW_MARGIN_PX,
        sparse_cutoff_px=None if capacity is None else capacity - SPARSE_MARGIN_PX,
        reasons=(reason,),
    )


def evaluate_layout(
    spec: Mapping[str, Any],
    registry: Mapping[str, Any],
    calibration: Mapping[str, Any],
) -> tuple[PageBudget, ...]:
    """Evaluate pages only after the measured entry matches the runtime 8D key."""

    if not isinstance(spec, Mapping):
        raise LayoutBudgetInputError("spec must be an object")
    pages = spec.get("pages")
    if not isinstance(pages, list) or not pages:
        raise LayoutBudgetInputError("spec.pages must be a non-empty list")
    for index, page in enumerate(pages):
        if not isinstance(page, Mapping):
            raise LayoutBudgetInputError(f"spec.pages[{index}] must be an object")
    _normalized_registry(registry)

    try:
        key, values = _calibration_values(calibration)
    except _RenderMeasurementRequired as exc:
        return tuple(
            _measurement_result(str(page.get("page_id", "?")), str(exc))
            for page in pages
        )

    try:
        base_capacity = float(values["capacity_px"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LayoutBudgetInputError("measured calibration requires numeric capacity_px") from exc
    if base_capacity <= 0:
        raise LayoutBudgetInputError("capacity_px must be positive")

    meta = spec.get("meta") if isinstance(spec.get("meta"), Mapping) else {}
    runtime_meta = (
        meta.get("calibration_runtime")
        if isinstance(meta.get("calibration_runtime"), Mapping)
        else {}
    )
    try:
        theme = _runtime_dimension(spec.get("theme"), "theme")
        page_chrome = _runtime_dimension(meta.get("page_chrome"), "page_chrome")
        width_class = _runtime_dimension(runtime_meta.get("width_class"), "width_class")
        browser_major = _runtime_dimension(runtime_meta.get("browser_major"), "browser_major")
        common_runtime_key = {
            "renderer_struct_hash": renderer_struct_hash(),
            "css_hash": css_hash(theme),
            "theme": theme,
            "page_chrome": page_chrome,
            "width_class": width_class,
            "font_build": font_build_hash(),
            "browser_major": browser_major,
        }
    except _RenderMeasurementRequired as exc:
        return tuple(
            _measurement_result(str(page.get("page_id", "?")), str(exc))
            for page in pages
        )
    except CalibrationRuntimeKeyError as exc:
        reason = f"runtime calibration key cannot be confirmed: {exc}"
        return tuple(
            _measurement_result(str(page.get("page_id", "?")), reason)
            for page in pages
        )

    results: list[PageBudget] = []
    for index, page in enumerate(pages):
        page_id = str(page.get("page_id", f"p{index + 1:02d}"))
        try:
            layout = _runtime_dimension(page.get("layout"), "layout")
            runtime_key = validate_key({**common_runtime_key, "layout": layout})
        except (_RenderMeasurementRequired, CalibrationFormatError) as exc:
            results.append(_measurement_result(page_id, str(exc)))
            continue
        mismatched = [
            dimension
            for dimension in KEY_DIMENSIONS
            if key[dimension] != runtime_key[dimension]
        ]
        if mismatched:
            results.append(
                _measurement_result(
                    page_id,
                    f"calibration key mismatch: {', '.join(mismatched)}",
                )
            )
            continue
        page_capacity: float | None = None
        try:
            content = page.get("content")
            if not isinstance(content, list):
                raise LayoutBudgetInputError(f"{page_id}: content must be a list")
            page_capacity = _page_capacity(
                page,
                content,
                registry,
                base_capacity=base_capacity,
                page_chrome=page_chrome,
                layout=layout,
            )
            if _page_requires_source_row_measurement(page, registry):
                raise _RenderMeasurementRequired("source-row general height formula is uncalibrated")
            if any(isinstance(block, Mapping) and block.get("type") == "footnote" for block in content):
                raise _RenderMeasurementRequired("footnote general height formula is uncalibrated")
            flow_blocks = [
                block
                for block in content
                if isinstance(block, Mapping)
                and str(block.get("type", "")).strip() not in {"eyebrow", "citation", "source", "footnote"}
            ]
            height = (
                _split_layout_height(flow_blocks, registry, calibration)
                if layout == "split"
                else page_height([block_height(block, registry, calibration) for block in flow_blocks])
            )
            verdict = classify_height(height, page_capacity)
            results.append(
                PageBudget(
                    page_id=page_id,
                    verdict=verdict,
                    height_px=height,
                    capacity_px=page_capacity,
                    overflow_cutoff_px=page_capacity - OVERFLOW_MARGIN_PX,
                    sparse_cutoff_px=page_capacity - SPARSE_MARGIN_PX,
                )
            )
        except _RenderMeasurementRequired as exc:
            results.append(_measurement_result(page_id, str(exc), page_capacity))
    return tuple(results)


__all__ = [
    "BudgetVerdict",
    "LayoutBudgetInputError",
    "PageBudget",
    "block_height",
    "classify_height",
    "cpl",
    "evaluate_layout",
    "line_count",
    "linear_partition_impossible",
    "metric_grid_height",
    "page_height",
    "sibling_vertical_overlaps",
    "split_fits",
    "split_page_height",
    "split_viz_height",
    "substitute_metric_tokens",
    "text_table_height",
    "viz_signature",
]
