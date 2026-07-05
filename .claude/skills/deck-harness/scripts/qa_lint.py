from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


HARNESS_CONTRACTS_DIR = Path(__file__).resolve().parents[2] / "harness-contracts" / "scripts"
if str(HARNESS_CONTRACTS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_CONTRACTS_DIR))

from contract_checks import _registry_map, _string_set  # noqa: E402


RAW_DIGIT_PATTERN = re.compile(r"\d")
NUMBER_PATTERN = re.compile(r"(?<![A-Za-z0-9_])[+-]?\d+(?:[.,]\d+)*(?:\.\d+)?")

TEXT_BLOCK_TYPES = {"headline", "body", "note", "eyebrow", "text"}
RAW_EXCLUDED_BLOCK_TYPES = {"citation", "metric", "metrics", "metric_grid", "stat_grid"}
VISIBLE_TEXT_KEYS = {
    "text",
    "headline",
    "body",
    "note",
    "eyebrow",
    "title",
    "label",
    "summary",
    "callout",
}
STRUCTURAL_TEXT_KEYS = {
    "id",
    "page_id",
    "part_id",
    "layout",
    "type",
    "chart",
    "role",
    "metric_id",
    "src_id",
    "source_id",
    "short_title",
}
NON_BODY_LAYOUTS = {"cover", "index", "divider", "outro", "source_appendix"}
BODY_OR_METRIC_BLOCK_TYPES = {"body", "metric", "metrics", "metric_grid", "stat_grid"}

SEVERITY = {
    "RAW_NUMBER_IN_LABEL": "high",
    "MIXED_SOURCE_CHART": "medium",
    "ARCHETYPE_MISSING": "medium",
    "LAYOUT_MONOTONY": "low",
    "EMPTY_SCENARIO_CARD": "high",
    "UNBACKED_NUMBER_CLAIM": "medium",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint deck_spec defects before rendering.")
    parser.add_argument("deck_spec", nargs="?", help="Path to 06_deck_spec.json")
    parser.add_argument("registry", nargs="?", help="Path to 02_verified.json")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--corpus", help="Scan _workspace-style corpus directory")
    args = parser.parse_args(argv)

    if args.corpus:
        try:
            print_corpus_report(Path(args.corpus))
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0

    if not args.deck_spec or not args.registry:
        parser.error("deck_spec and registry are required unless --corpus is used")

    deck_path = Path(args.deck_spec)
    registry_path = Path(args.registry)
    try:
        defects = lint_paths(deck_path, registry_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        payload = {
            "deck_spec": str(deck_path),
            "defects": defects,
            "counts": dict(sorted(Counter(item["code"] for item in defects).items())),
        }
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    else:
        print_human_defects(defects)
    return 0


def lint_paths(deck_path: Path, registry_path: Path) -> list[dict[str, Any]]:
    deck_spec = load_json(deck_path, "deck_spec")
    registry = load_json(registry_path, "registry")
    return lint_deck(deck_spec, registry, deck_path)


def load_json(path: Path, label: str) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"failed to parse {label}: {path}: {exc}") from exc


def lint_deck(deck_spec: dict[str, Any], registry: dict[str, Any], deck_path: Path | None = None) -> list[dict[str, Any]]:
    if not isinstance(deck_spec, dict):
        raise ValueError("failed to parse deck_spec: root must be an object")
    if not isinstance(registry, dict):
        raise ValueError("failed to parse registry: root must be an object")

    metric_registry = _registry_map(registry, ("metrics", "metric_registry"))
    defects: list[dict[str, Any]] = []
    raw_paths: set[tuple[str, str]] = set()

    pages = deck_spec.get("pages", [])
    if not isinstance(pages, list):
        pages = []

    if not _deck_has_archetype(deck_spec):
        detail = "deck_spec missing top-level/meta archetype"
        page_plan_archetype = _sibling_page_plan_archetype(deck_path)
        if page_plan_archetype:
            detail = f"{detail}; sibling page_plan archetype={page_plan_archetype}"
        defects.append(_defect("ARCHETYPE_MISSING", "deck", "deck_spec.archetype", detail))

    defects.extend(_layout_monotony_defects(pages))

    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            continue
        page_id = _page_id(page, page_index)
        page_path = f"pages[{page_index}]"
        allowed_metric_ids = _string_set(page.get("allowed_metric_ids"))
        content = page.get("content", page.get("blocks", []))

        for defect in _raw_number_defects(content, page_id, f"{page_path}.content"):
            raw_paths.add((defect["page_id"], defect["where"]))
            defects.append(defect)

        defects.extend(_mixed_source_chart_defects(content, page_id, f"{page_path}.content", metric_registry))

        if str(page.get("layout", "")).strip() == "scenario_cards":
            defects.extend(_empty_scenario_card_defects(content, page_id, f"{page_path}.content"))

        defects.extend(
            _unbacked_number_defects(
                content,
                page_id,
                f"{page_path}.content",
                allowed_metric_ids,
                metric_registry,
                raw_paths,
            )
        )

    return defects


def _defect(code: str, page_id: str, where: str, detail: str) -> dict[str, str]:
    return {
        "code": code,
        "severity": SEVERITY[code],
        "page_id": page_id,
        "where": where,
        "detail": detail,
    }


def _page_id(page: dict[str, Any], page_index: int) -> str:
    value = page.get("page_id")
    if isinstance(value, str) and value.strip():
        return value
    return f"pages[{page_index}]"


def _deck_has_archetype(deck_spec: dict[str, Any]) -> bool:
    if str(deck_spec.get("archetype", "")).strip():
        return True
    meta = deck_spec.get("meta")
    return isinstance(meta, dict) and str(meta.get("archetype", "")).strip() != ""


def _sibling_page_plan_archetype(deck_path: Path | None) -> str:
    if deck_path is None:
        return ""
    page_plan_path = deck_path.parent / "05_page_plan.json"
    if not page_plan_path.exists():
        return ""
    try:
        page_plan = load_json(page_plan_path, "page_plan")
    except ValueError:
        return ""
    if not isinstance(page_plan, dict):
        return ""
    meta = page_plan.get("meta")
    candidates = [
        page_plan.get("archetype"),
        meta.get("archetype") if isinstance(meta, dict) else None,
    ]
    for candidate in candidates:
        if str(candidate or "").strip():
            return str(candidate).strip()
    return ""


def _layout_monotony_defects(pages: list[Any]) -> list[dict[str, str]]:
    layouts: list[str] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        layout = str(page.get("layout", "")).strip()
        if layout and layout not in NON_BODY_LAYOUTS:
            layouts.append(layout)
    if not layouts:
        return []

    counts = Counter(layouts)
    total = len(layouts)
    defects = []
    for layout, count in sorted(counts.items()):
        ratio = count / total
        if ratio > 0.60:
            defects.append(
                _defect(
                    "LAYOUT_MONOTONY",
                    "deck",
                    "pages[].layout",
                    f"layout {layout} repeats {count}/{total} body pages ({ratio:.1%})",
                )
            )
    return defects


def _raw_number_defects(value: Any, page_id: str, path: str) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for block, block_path in _iter_blocks(value, path):
        block_type = str(block.get("type", "")).strip()
        if block_type in RAW_EXCLUDED_BLOCK_TYPES:
            continue
        if block_type == "viz":
            defects.extend(_raw_number_viz_defects(block, page_id, block_path))
            continue
        if block_type in TEXT_BLOCK_TYPES:
            text = block.get("text")
            if isinstance(text, str) and RAW_DIGIT_PATTERN.search(text):
                defects.append(
                    _defect(
                        "RAW_NUMBER_IN_LABEL",
                        page_id,
                        f"{block_path}.text",
                        f"{block_type} contains raw number: {_clip(text)}",
                    )
                )
        if block_type == "bullets":
            defects.extend(_raw_number_bullet_defects(block, page_id, block_path))
    return defects


def _raw_number_viz_defects(block: dict[str, Any], page_id: str, block_path: str) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for field in ("title", "note"):
        text = block.get(field)
        if isinstance(text, str) and RAW_DIGIT_PATTERN.search(text):
            defects.append(
                _defect(
                    "RAW_NUMBER_IN_LABEL",
                    page_id,
                    f"{block_path}.{field}",
                    f"viz {field} contains raw number: {_clip(text)}",
                )
            )

    series = block.get("series")
    if isinstance(series, list):
        for index, item in enumerate(series):
            if not isinstance(item, dict):
                continue
            label = item.get("label")
            if isinstance(label, str) and RAW_DIGIT_PATTERN.search(label):
                defects.append(
                    _defect(
                        "RAW_NUMBER_IN_LABEL",
                        page_id,
                        f"{block_path}.series[{index}].label",
                        f"viz series label contains raw number: {_clip(label)}",
                    )
                )
    return defects


def _raw_number_bullet_defects(block: dict[str, Any], page_id: str, block_path: str) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    items = block.get("items")
    if not isinstance(items, list):
        return defects
    for index, item in enumerate(items):
        item_path = f"{block_path}.items[{index}]"
        text = _item_text(item)
        if text and RAW_DIGIT_PATTERN.search(text):
            suffix = ".text" if isinstance(item, dict) else ""
            defects.append(
                _defect(
                    "RAW_NUMBER_IN_LABEL",
                    page_id,
                    f"{item_path}{suffix}",
                    f"bullets item contains raw number: {_clip(text)}",
                )
            )
    return defects


def _mixed_source_chart_defects(
    value: Any,
    page_id: str,
    path: str,
    metric_registry: dict[str, Any],
) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for block, block_path in _iter_blocks(value, path):
        if block.get("type") != "viz":
            continue
        metric_ids: list[str] = []
        series = block.get("series")
        if isinstance(series, list):
            for item in series:
                if isinstance(item, dict) and str(item.get("metric_id", "")).strip():
                    metric_ids.append(str(item["metric_id"]))
        source_ids: set[str] = set()
        for metric_id in metric_ids:
            metric = metric_registry.get(metric_id)
            if isinstance(metric, dict):
                source_ids |= _string_set(metric.get("source_ids"))
        if len(source_ids) >= 2:
            defects.append(
                _defect(
                    "MIXED_SOURCE_CHART",
                    page_id,
                    f"{block_path}.series",
                    f"viz series metrics span {len(source_ids)} sources: {', '.join(sorted(source_ids))}",
                )
            )
    return defects


def _empty_scenario_card_defects(value: Any, page_id: str, path: str) -> list[dict[str, str]]:
    content = value if isinstance(value, list) else []
    defects: list[dict[str, str]] = []
    pending_headline_index: int | None = None
    pending_has_body_or_metric = False

    for index, block in enumerate(content):
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type", "")).strip()
        if block_type == "headline":
            if pending_headline_index is not None and not pending_has_body_or_metric:
                defects.append(
                    _defect(
                        "EMPTY_SCENARIO_CARD",
                        page_id,
                        f"{path}[{pending_headline_index}]",
                        f"headline is followed by another headline before body/metric content at {path}[{index}]",
                    )
                )
            pending_headline_index = index
            pending_has_body_or_metric = False
        elif pending_headline_index is not None and block_type in BODY_OR_METRIC_BLOCK_TYPES:
            pending_has_body_or_metric = True
    return defects


def _unbacked_number_defects(
    value: Any,
    page_id: str,
    path: str,
    allowed_metric_ids: set[str],
    metric_registry: dict[str, Any],
    raw_paths: set[tuple[str, str]],
) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    backed_numbers = _allowed_metric_numbers(allowed_metric_ids, metric_registry)
    for text, text_path in _iter_visible_texts(value, path):
        if (page_id, text_path) in raw_paths:
            continue
        numbers = [_normalize_number(item) for item in NUMBER_PATTERN.findall(text)]
        numbers = [item for item in numbers if item]
        if not numbers:
            continue
        if not allowed_metric_ids:
            detail = f"text has {', '.join(numbers)} but page allowed_metric_ids is empty: {_clip(text)}"
        else:
            unbacked = [item for item in numbers if item not in backed_numbers]
            if not unbacked:
                continue
            detail = (
                f"text has unbacked number(s) {', '.join(unbacked)}; "
                f"allowed metric values: {', '.join(sorted(backed_numbers)) or 'none'}"
            )
        defects.append(_defect("UNBACKED_NUMBER_CLAIM", page_id, text_path, detail))
    return defects


def _allowed_metric_numbers(allowed_metric_ids: set[str], metric_registry: dict[str, Any]) -> set[str]:
    values: set[str] = set()
    for metric_id in allowed_metric_ids:
        metric = metric_registry.get(metric_id)
        if not isinstance(metric, dict):
            continue
        for key in ("value", "label", "scope"):
            text = metric.get(key)
            if isinstance(text, str):
                values |= {_normalize_number(item) for item in NUMBER_PATTERN.findall(text)}
    values.discard("")
    return values


def _iter_blocks(value: Any, path: str):
    if isinstance(value, dict):
        if "type" in value:
            yield value, path
        for key, nested in value.items():
            yield from _iter_blocks(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_blocks(nested, f"{path}[{index}]")


def _iter_visible_texts(value: Any, path: str, parent_block_type: str = ""):
    if isinstance(value, dict):
        block_type = str(value.get("type", parent_block_type)).strip() or parent_block_type
        if block_type in RAW_EXCLUDED_BLOCK_TYPES:
            return
        for key, nested in value.items():
            next_path = f"{path}.{key}"
            if key in STRUCTURAL_TEXT_KEYS:
                continue
            if isinstance(nested, str) and key in VISIBLE_TEXT_KEYS:
                yield nested, next_path
            elif key == "items" and isinstance(nested, list):
                for index, item in enumerate(nested):
                    item_path = f"{next_path}[{index}]"
                    text = _item_text(item)
                    if text:
                        suffix = ".text" if isinstance(item, dict) else ""
                        yield text, f"{item_path}{suffix}"
                    if isinstance(item, dict):
                        for item_key, item_nested in item.items():
                            if item_key == "text":
                                continue
                            yield from _iter_visible_texts(item_nested, f"{item_path}.{item_key}", block_type)
                    elif isinstance(item, list):
                        yield from _iter_visible_texts(item, item_path, block_type)
            else:
                yield from _iter_visible_texts(nested, next_path, block_type)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_visible_texts(nested, f"{path}[{index}]", parent_block_type)


def _item_text(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict) and isinstance(item.get("text"), str):
        return item["text"]
    return ""


def _normalize_number(value: str) -> str:
    return value.replace(",", "").strip()


def _clip(text: str, limit: int = 80) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 1]}..."


def print_human_defects(defects: list[dict[str, Any]]) -> None:
    if not defects:
        print("No defects.")
        return
    for defect in defects:
        print(
            f"{defect['code']} {defect['severity']} "
            f"{defect['page_id']} {defect['where']} - {defect['detail']}"
        )


def print_corpus_report(corpus_dir: Path) -> None:
    spec_paths = sorted(corpus_dir.glob("*/06_deck_spec.json"))
    total_specs = len(spec_paths)
    scanned_specs = 0
    skipped: list[str] = []
    defectful_specs = 0
    totals: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)

    for spec_path in spec_paths:
        run_id = spec_path.parent.name
        registry_path = spec_path.parent / "02_verified.json"
        if not registry_path.exists():
            skipped.append(run_id)
            continue
        defects = lint_paths(spec_path, registry_path)
        scanned_specs += 1
        if defects:
            defectful_specs += 1
        for defect in defects:
            code = defect["code"]
            totals[code] += 1
            if len(examples[code]) < 3:
                examples[code].append(f"{run_id}:{defect['page_id']}")

    ratio = (defectful_specs / scanned_specs) if scanned_specs else 0.0
    print("QA lint corpus defect map")
    print(f"corpus: {corpus_dir}")
    print(f"total_specs: {total_specs}")
    print(f"scanned_specs: {scanned_specs}")
    print(f"skipped_missing_registry: {len(skipped)}")
    if skipped:
        print(f"skipped_runs: {', '.join(skipped)}")
    print(f"defectful_specs: {defectful_specs}/{scanned_specs} scanned ({ratio:.1%})")
    print("defects_by_code:")
    for code in sorted(SEVERITY):
        top = ", ".join(examples[code]) if examples.get(code) else "none"
        print(f"  {code}: {totals[code]} (top_examples: {top})")


if __name__ == "__main__":
    raise SystemExit(main())
