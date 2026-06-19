#!/usr/bin/env python3
"""Build and render a TickDeck deck from one report result JSON."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import axis1_to_deck


TICKDECK_V3_DIR = Path(__file__).resolve().parents[1]
AUTOMATION_ROOT = TICKDECK_V3_DIR.parents[1]
OUTPUT_ROOT = TICKDECK_V3_DIR / "output"
DECK_AUTHOR_PY = AUTOMATION_ROOT / "sinya" / "experiments" / "deepresearch" / "deck_author.py"
HARNESS_PYTHON = Path("/Users/hwa/Projects/Automation/Think/tools/deck_harness/.venv/bin/python")
HARNESS_BUILD = Path("/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py")
MAX_AUTOFIX_ITERATIONS = 5
MAX_COMPACT_TABLE_ROWS_PER_SLIDE = 8
SOFT_ISSUE_TYPES = {"DensityWarning", "SoftLintWarning"}
TABLE_LAYOUTS = {"requirements_excel_table", "tam_scenario_table", "workflow_table_3col"}
CROWDED_TEXT_LAYOUTS = {
    "3-card",
    "corporate_research_navy_split_focus",
    "data_visualization_2col_chart_text",
    "data_visualization_3col_chart",
    "before_after_diagram_with_metric",
    "contest_history_timeline_bullet",
    "ir_company_overview_timeline_milestone",
}
PAGE_SUFFIX_RE = re.compile(r"\s*\(\d+/\d+\)$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|(?<=다)\s+")


def safe_slug(topic: str) -> str:
    slug = re.sub(r"[^\w가-힣-]+", "_", str(topic or "").strip())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug[:80] or "report"


def default_output_dir(result_json: Path, topic: str | None = None) -> Path:
    if topic is None:
        try:
            data = axis1_to_deck.load_axis1(Path(result_json))
            topic = str(data.get("topic") or Path(result_json).stem)
        except Exception:
            topic = Path(result_json).stem
    return OUTPUT_ROOT / safe_slug(topic)


def load_deck_author_module():
    spec = importlib.util.spec_from_file_location("deck_author", DECK_AUTHOR_PY)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load deck_author module: {DECK_AUTHOR_PY}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def default_page_specs_path(result_json: Path, author_out_dir: Path | None = None) -> Path:
    deck_author = load_deck_author_module()
    return deck_author.default_page_specs_path(Path(result_json).expanduser().resolve(), author_out_dir)


def ensure_page_specs(
    result_json: Path,
    *,
    author_out_dir: Path | None = None,
    model: str | None = None,
) -> Path:
    result_json = Path(result_json).expanduser().resolve()
    out_dir = Path(author_out_dir).expanduser().resolve() if author_out_dir else None
    candidate = default_page_specs_path(result_json, out_dir)
    if candidate.exists():
        return candidate
    deck_author = load_deck_author_module()
    return deck_author.author_deck(result_json, out_dir=out_dir, model=model).page_specs_path


def render_command(slides_json: Path, out_dir: Path) -> list[str]:
    return [
        str(HARNESS_PYTHON),
        str(HARNESS_BUILD),
        str(slides_json),
        "--out",
        str(out_dir),
    ]


def load_validation(out_dir: Path) -> dict[str, Any]:
    path = Path(out_dir) / "validation.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def is_hard_issue(issue: dict[str, Any]) -> bool:
    return bool(issue.get("type")) and issue.get("type") not in SOFT_ISSUE_TYPES


def collect_hard_issue_reports(validation: dict[str, Any]) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for slide_report in validation.get("slides") or []:
        if not isinstance(slide_report, dict):
            continue
        issues = [issue for issue in slide_report.get("issues") or [] if isinstance(issue, dict) and is_hard_issue(issue)]
        if not issues:
            continue
        reports.append(
            {
                "index": slide_report.get("index"),
                "title": slide_report.get("title", ""),
                "layout": slide_report.get("layout", ""),
                "issues": issues,
            }
        )
    return reports


def issue_cut_fraction(issue: dict[str, Any]) -> float:
    cut = 0.15
    try:
        amount = float(issue.get("amount") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    if amount > 0:
        cut += min(0.35, amount / 120.0)

    rect = issue.get("rect") if isinstance(issue.get("rect"), dict) else {}
    if rect:
        top = float(rect.get("top", 0) or 0)
        left = float(rect.get("left", 0) or 0)
        right = float(rect.get("right", 0) or 0)
        bottom = float(rect.get("bottom", 0) or 0)
        violation = max(max(0.0, -top), max(0.0, -left), max(0.0, right - 1280), max(0.0, bottom - 720))
        cut += min(0.35, violation / 260.0)
    return max(0.15, min(0.6, cut))


def split_sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    return [piece.strip() for piece in SENTENCE_SPLIT_RE.split(compact) if piece.strip()] or ([compact] if compact else [])


def clip_text(text: str, max_chars: int) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(compact) <= max_chars:
        return compact
    if max_chars <= 1:
        return "…"

    budget = max(1, max_chars - 1)
    kept: list[str] = []
    for sentence in split_sentences(compact):
        candidate = " ".join([*kept, sentence]) if kept else sentence
        if len(candidate) > budget:
            break
        kept.append(sentence)
    if kept and len(" ".join(kept)) >= max(12, int(budget * 0.45)):
        clipped = " ".join(kept)
    else:
        clipped = compact[:budget]
        boundaries = [clipped.rfind(mark) for mark in (" ", ",", ".", ":", ";", "·", "/", "-", "—")]
        boundary = max(boundaries)
        if boundary >= int(budget * 0.55):
            clipped = clipped[:boundary]
    return clipped.rstrip(" .,!?:;:：-–—/…") + "…"


def shorten_text(text: str, issue: dict[str, Any], *, min_chars: int = 18) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(compact) <= min_chars + 1:
        return compact
    target = max(min_chars, int(len(compact) * (1.0 - issue_cut_fraction(issue))))
    return clip_text(compact, target)


def shorten_mapping_value(target: dict[str, Any], key: str, issue: dict[str, Any], *, min_chars: int = 18) -> bool:
    value = target.get(key)
    if not isinstance(value, str) or not value.strip():
        return False
    shortened = shorten_text(value, issue, min_chars=min_chars)
    if shortened == value:
        return False
    target[key] = shortened
    return True


def table_issue(slide: dict[str, Any], issue: dict[str, Any]) -> bool:
    element = str(issue.get("element") or "")
    if slide.get("layout") not in TABLE_LAYOUTS:
        return False
    return any(marker in element for marker in ("-table", "-tam", "-col-", "-sec-")) or issue.get("type", "").startswith("overflow")


def page_title(base_title: str, idx: int, total: int) -> str:
    base = PAGE_SUFFIX_RE.sub("", str(base_title or "표")).strip() or "표"
    return base if total <= 1 else f"{base} ({idx}/{total})"


def split_rows(rows: list[Any]) -> list[list[Any]]:
    if len(rows) <= 1:
        return [rows]
    chunk_count = max(1, math.ceil(len(rows) / MAX_COMPACT_TABLE_ROWS_PER_SLIDE))
    chunk_size = max(1, math.ceil(len(rows) / chunk_count))
    return [rows[idx : idx + chunk_size] for idx in range(0, len(rows), chunk_size)]


def split_table_slide(deck: dict[str, Any], slide_pos: int) -> bool:
    slide = deck["slides"][slide_pos]
    layout = slide.get("layout")
    rows = slide.get("rows") or []
    if layout not in {"requirements_excel_table", "tam_scenario_table"} or len(rows) <= 2:
        return False

    if layout == "requirements_excel_table":
        source_rows = [row for row in rows if isinstance(row, dict) and row.get("_row_type") == "source_note"]
        body_rows = [row for row in rows if not (isinstance(row, dict) and row.get("_row_type") == "source_note")]
    else:
        source_rows = []
        body_rows = list(rows)
    if len(body_rows) <= MAX_COMPACT_TABLE_ROWS_PER_SLIDE:
        return False

    chunks = split_rows(body_rows)
    if len(chunks) <= 1:
        return False

    new_slides: list[dict[str, Any]] = []
    total = len(chunks)
    for idx, chunk in enumerate(chunks, start=1):
        clone = copy.deepcopy(slide)
        clone["title"] = page_title(str(slide.get("title") or ""), idx, total)
        clone["rows"] = [*chunk, *source_rows] if idx == total else chunk
        new_slides.append(clone)
    deck["slides"][slide_pos : slide_pos + 1] = new_slides
    return True


def shorten_list_item(items: list[Any], idx: int, issue: dict[str, Any]) -> bool:
    if idx < 0 or idx >= len(items):
        return False
    item = items[idx]
    if isinstance(item, str):
        shortened = shorten_text(item, issue)
        if shortened != item:
            items[idx] = shortened
            return True
        return False
    if isinstance(item, dict):
        for key in ("body", "note", "value", "label", "title", "detail", "text"):
            if shorten_mapping_value(item, key, issue):
                return True
    return False


def shorten_text_for_issue(slide: dict[str, Any], issue: dict[str, Any]) -> bool:
    element = str(issue.get("element") or "")
    suffix = re.sub(r"^slide-\d+-", "", element)
    if suffix == "subtitle" and slide.get("subtitle"):
        slide["subtitle"] = ""
        return True
    if suffix in {"title", "subtitle", "body", "headline", "caption", "source", "note", "lead"}:
        return shorten_mapping_value(slide, suffix, issue, min_chars=14 if suffix == "title" else 22)

    match = re.match(r"paragraph-(\d+)$", suffix)
    if match:
        return shorten_list_item(slide.get("paragraphs") or [], int(match.group(1)) - 1, issue)

    match = re.match(r"card-(\d+)-(title|body)$", suffix)
    if match:
        cards = slide.get("cards") or []
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(cards) and isinstance(cards[idx], dict):
            return shorten_mapping_value(cards[idx], match.group(2), issue, min_chars=14 if match.group(2) == "title" else 22)

    match = re.match(r"(?:spec|stat|event|section|milestone|area|stage|action|right)-(\d+)(?:-(title|body|note|label|value|detail|text))?$", suffix)
    if match:
        idx = int(match.group(1)) - 1
        key = match.group(2)
        for list_key in ("focus", "specs", "stats", "events", "sections", "milestones", "areas", "stages", "actions", "right_items"):
            items = slide.get(list_key)
            if not isinstance(items, list) or not (0 <= idx < len(items)):
                continue
            if key and isinstance(items[idx], dict):
                return shorten_mapping_value(items[idx], key, issue)
            return shorten_list_item(items, idx, issue)

    match = re.match(r"col-(\d+)$", suffix)
    if match:
        columns = slide.get("columns") or []
        idx = int(match.group(1)) - 1
        if 0 <= idx < len(columns) and isinstance(columns[idx], dict):
            items = columns[idx].get("items")
            if isinstance(items, list) and items:
                longest_idx = max(range(len(items)), key=lambda item_idx: len(str(items[item_idx])))
                return shorten_list_item(items, longest_idx, issue)
            return shorten_mapping_value(columns[idx], "body", issue)

    match = re.match(r"sec-(\d+)$", suffix)
    if match:
        return shorten_list_item(slide.get("secondary") or [], int(match.group(1)) - 1, issue)
    return False


def text_payload_from_slide(slide: dict[str, Any]) -> list[str]:
    payload: list[str] = []
    for key in ("body", "subtitle"):
        value = slide.get(key)
        if isinstance(value, str) and value.strip():
            payload.append(value)
    for key in ("bullets", "paragraphs", "takeaways", "right_items"):
        payload.extend(str(item) for item in slide.get(key) or [] if str(item).strip())
    for key in ("cards", "focus", "sections", "milestones", "stats", "stages", "actions"):
        for item in slide.get(key) or []:
            if isinstance(item, dict):
                text = (
                    item.get("body")
                    or item.get("note")
                    or item.get("detail")
                    or item.get("text")
                    or item.get("value")
                    or item.get("title")
                )
                if text:
                    payload.append(str(text))
    return payload


def downgrade_text_layout(slide: dict[str, Any]) -> bool:
    if slide.get("layout") not in CROWDED_TEXT_LAYOUTS:
        return False
    if slide.get("stats") or slide.get("bars"):
        return False
    paragraphs = [clip_text(text, 220) for text in text_payload_from_slide(slide)[:3]]
    if not paragraphs:
        return False
    for key in (
        "bars",
        "bullets",
        "cards",
        "focus",
        "stats",
        "before",
        "after",
        "metric",
        "events",
        "sections",
        "milestones",
        "right_items",
        "columns",
        "rows",
    ):
        slide.pop(key, None)
    slide["layout"] = "narrative_centered_text_block"
    slide["paragraphs"] = paragraphs
    return True


def apply_autofixes(deck: dict[str, Any], issue_reports: list[dict[str, Any]], iteration: int) -> bool:
    changed = False
    indexed_reports = sorted(
        (report for report in issue_reports if isinstance(report.get("index"), int)),
        key=lambda report: report["index"],
        reverse=True,
    )
    for report in indexed_reports:
        slide_pos = int(report["index"]) - 1
        if slide_pos < 0 or slide_pos >= len(deck.get("slides") or []):
            continue
        slide = deck["slides"][slide_pos]
        issues = report.get("issues") or []
        if any(table_issue(slide, issue) for issue in issues) and split_table_slide(deck, slide_pos):
            changed = True
            continue
        for issue in issues:
            changed = shorten_text_for_issue(slide, issue) or changed
        if iteration >= 2 and issues:
            changed = downgrade_text_layout(slide) or changed
    return changed


def render_with_autofix_loop(
    deck: dict[str, Any],
    slides_json: Path,
    out_dir: Path,
    *,
    render: bool = True,
    max_iterations: int = MAX_AUTOFIX_ITERATIONS,
) -> dict[str, Any]:
    cmd = render_command(slides_json, out_dir)
    completed: subprocess.CompletedProcess[str] | None = None
    autofix_iterations = 0
    final_reports: list[dict[str, Any]] = []

    for attempt in range(max_iterations + 1):
        axis1_to_deck.write_deck(deck, slides_json)
        if not render:
            return {
                "render_command": cmd,
                "render_returncode": None,
                "autofix_iterations": 0,
                "final_hard_issues": None,
                "final_hard_issue_details": [],
            }

        (Path(out_dir) / "validation.json").unlink(missing_ok=True)
        completed = subprocess.run(cmd, text=True)
        validation = load_validation(out_dir)
        if not validation:
            final_reports = [
                {
                    "index": None,
                    "title": "deck_harness render failed before validation",
                    "layout": "",
                    "issues": [{"type": "render-failure", "returncode": completed.returncode}],
                }
            ]
            break
        final_reports = collect_hard_issue_reports(validation)
        if not final_reports:
            break
        if attempt >= max_iterations:
            print(
                f"autofix: hard issues remain after {autofix_iterations} iterations: {len(final_reports)} slides",
                file=sys.stderr,
            )
            break
        if not apply_autofixes(deck, final_reports, attempt + 1):
            print(
                f"autofix: no applicable JSON fix for {len(final_reports)} hard-issue slides",
                file=sys.stderr,
            )
            break
        autofix_iterations += 1
        print(
            f"autofix: iteration {autofix_iterations} applied to {len(final_reports)} hard-issue slides",
            file=sys.stderr,
        )

    axis1_to_deck.write_deck(deck, slides_json)
    return {
        "render_command": cmd,
        "render_returncode": completed.returncode if completed else None,
        "autofix_iterations": autofix_iterations,
        "final_hard_issues": sum(len(report.get("issues") or []) for report in final_reports),
        "final_hard_issue_details": final_reports,
    }


def build_and_render(
    result_json: Path,
    out_dir: Path | None = None,
    render: bool = True,
    *,
    page_specs_path: Path | None = None,
    author_out_dir: Path | None = None,
    model: str | None = None,
    theme: str | None = None,
) -> dict[str, Any]:
    result_json = Path(result_json).expanduser().resolve()
    data = axis1_to_deck.load_axis1(result_json)
    out_dir = Path(out_dir).expanduser().resolve() if out_dir else default_output_dir(result_json, str(data["topic"]))
    out_dir.mkdir(parents=True, exist_ok=True)

    if page_specs_path is None:
        # (A) parked automatic author scaffold path. This can reach the
        # Chinese-model deck_author placeholder; current (B) runs should pass an
        # explicit hand-written page_specs.json and skip this branch.
        page_specs_path = ensure_page_specs(result_json, author_out_dir=author_out_dir, model=model)
    page_specs_path = Path(page_specs_path).expanduser().resolve()

    deck = axis1_to_deck.build_deck(page_specs_path, theme=theme)
    slides_json = out_dir / "slides.json"
    render_result = render_with_autofix_loop(deck, slides_json, out_dir, render=render)

    return {
        "report_json": str(result_json),
        "page_specs_json": str(page_specs_path),
        "slides_json": str(slides_json),
        "out_dir": str(out_dir),
        "slides": len(deck["slides"]),
        "title": deck["title"],
        **render_result,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report JSON -> slides JSON -> rendered TickDeck output")
    parser.add_argument("result_json", help="Report result JSON with leader.final Markdown")
    parser.add_argument("--out", help="Output directory. Default: TickDeck/v3/output/<topic-slug>/")
    parser.add_argument("--page-specs", help="Explicit page_specs JSON. Skips the automatic author scaffold.")
    parser.add_argument("--theme", help="deck_harness theme preset id")
    parser.add_argument("--skip-render", action="store_true", help="Only write slides.json; do not call deck_harness")
    parser.add_argument(
        "--allow-render-failure",
        action="store_true",
        help="Return 0 after saving slides.json even if deck_harness returns a non-zero code",
    )
    args = parser.parse_args(argv)

    payload = build_and_render(
        Path(args.result_json),
        Path(args.out) if args.out else None,
        render=not args.skip_render,
        page_specs_path=Path(args.page_specs) if args.page_specs else None,
        theme=args.theme,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    if (
        payload["render_returncode"] not in (None, 0)
        and not args.allow_render_failure
    ):
        return int(payload["render_returncode"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
