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
FOUR_DIGIT_YEAR_PATTERN = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
YEAR_RANGE_PREFIX_PATTERN = re.compile(r"(?:19|20)\d{2}\s*[~\-–—]\s*$")
# 데이터 값으로 읽히는 숫자만 결함(연도·섹션 카운터·id 면제) — 검출기 정밀도 보정(7/5 스팟체크: \d는 절반이 오탐).
# 데이터 단위(%·만·억·배 등) 동반 or ==강조== 안의 숫자만. 연/월/주/위 등 모호 단위는 제외.
_DATA_UNIT_NUM = re.compile(r"\d[\d.,]*\s*(%|％|만|억|조|천|배|명|원|점|개|건|달러|위안|엔|퍼센트|‰|[xX×])")
# ==강조== 안의 숫자는 데이터일 확률이 높으나, 날짜(2026년 6월 1일)·서수(3단계)는 정당 → 데이터 단위 있는 경우만.
_EMPH_NUM = re.compile(r"==[^=]*\d[\d.,]*\s*(%|％|만|억|조|천|배|명|원|점|건|달러|위안|엔|퍼센트|[xX×])[^=]*==")


def _has_data_number(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    return bool(_EMPH_NUM.search(text) or _DATA_UNIT_NUM.search(text))

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
READER_FIRST_TEXT_KEYS = {"text", "note", "callout", "headline"}
READER_FIRST_CAVEAT_FIELDS = {"text", "note", "callout"}
READER_FIRST_EPISTEMIC_TERMS = (
    "관찰되지",
    "관찰되",
    "관찰된",
    "실측",
    "병치",
    "검증됨",
    "검증된",
    "스냅샷",
    "레지스트리",
    "표본",
)
READER_FIRST_SELF_REF_TERMS = ("이 덱", "이 보고서", "이 비교군", "이 장만")
READER_FIRST_JARGON_TERMS = ("좌표", "배경층", "저진입", "저신뢰", "양날", "유사군", "매핑", "신뢰 전달 장치", "성과 신호")
READER_FIRST_JARGON_AXIS_PATTERN = re.compile(r"\d+\s*[x×]\s*\d+\s*축|\d+축")

SEVERITY = {
    "RAW_NUMBER_IN_LABEL": "high",
    "MIXED_SOURCE_CHART": "medium",
    "ARCHETYPE_MISSING": "medium",
    "LAYOUT_MONOTONY": "low",
    "EMPTY_SCENARIO_CARD": "high",
    "UNBACKED_NUMBER_CLAIM": "medium",
    "READER_FIRST_EPISTEMIC": "high",
    "READER_FIRST_CAVEAT": "high",
    "READER_FIRST_SELF_REF": "high",
    "READER_FIRST_JARGON": "high",
    # absorb 코덱스 배치8 (7/26): placeholder 잔재·혼합 방향 시리즈 — 둘 다 코덱스 실측 사고 유형.
    "PLACEHOLDER_STRING": "high",
    "MIXED_DIRECTION_SERIES": "low",
}

# placeholder 잔재 (고신뢰 토큰만 — 정상 본문에 나올 수 없는 것들)
_PLACEHOLDER_PATTERN = re.compile(r"\b(?:xxxx+|lorem|ipsum|TBD|TODO|FIXME)\b", re.IGNORECASE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lint deck_spec defects before rendering.")
    parser.add_argument("deck_spec", nargs="?", help="Path to 06_deck_spec.json")
    parser.add_argument("registry", nargs="?", help="Path to 02_verified.json")
    parser.add_argument("--json", action="store_true", help="Print one JSON object")
    parser.add_argument("--corpus", help="Scan _workspace-style corpus directory")
    parser.add_argument("--selfcheck", action="store_true", help="Run built-in qa_lint smoke checks")
    args = parser.parse_args(argv)

    if args.selfcheck:
        return _run_selfcheck()

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
        backed_numbers = _allowed_metric_numbers(allowed_metric_ids, metric_registry)
        content = page.get("content", page.get("blocks", []))

        if not _reader_first_exempt_page(page):
            defects.extend(_reader_first_defects(content, page_id, f"{page_path}.content"))
            defects.extend(_reader_first_jargon_defects(page, content, page_id, page_path))

        for defect in _raw_number_defects(content, page_id, f"{page_path}.content", backed_numbers):
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

        defects.extend(_placeholder_defects(content, page_id, f"{page_path}.content"))
        defects.extend(_mixed_direction_defects(content, page_id, f"{page_path}.content", metric_registry))

    return defects


def _placeholder_defects(value: Any, page_id: str, path: str) -> list[dict[str, str]]:
    # absorb 코덱스 배치8: 최종 산출물에 placeholder 토큰 잔재 = 즉시 결함 (xxxx/lorem/TBD/TODO/FIXME).
    defects: list[dict[str, str]] = []
    def walk(node: Any, node_path: str) -> None:
        if isinstance(node, str):
            hit = _PLACEHOLDER_PATTERN.search(node)
            if hit:
                defects.append(_defect("PLACEHOLDER_STRING", page_id, node_path,
                                       f"placeholder 잔재 '{hit.group(0)}' — 최종본에 남으면 안 됨"))
        elif isinstance(node, dict):
            for k, v in node.items():
                walk(v, f"{node_path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{node_path}[{i}]")
    walk(value, path)
    return defects


def _mixed_direction_defects(
    value: Any, page_id: str, path: str, metric_registry: dict[str, Any]
) -> list[dict[str, str]]:
    # absorb 코덱스 배치8 실측: 양수·음수 지표가 한 차트에 섞이면 0축에서 음수 소실 or 방향 오독.
    # WARN(low) — before_after 델타 등 정당한 경우가 있어 designer 판단 대상 (차단 아님).
    defects: list[dict[str, str]] = []
    for block, block_path in _iter_blocks(value, path):
        if block.get("type") != "viz":
            continue
        series = block.get("series")
        if not isinstance(series, list):
            continue
        signs: set[str] = set()
        for item in series:
            if not isinstance(item, dict):
                continue
            entry = metric_registry.get(str(item.get("metric_id", "")))
            if not isinstance(entry, dict):
                continue
            try:
                num = float(str(entry.get("value", "")).replace(",", ""))
            except (TypeError, ValueError):
                continue
            if num > 0:
                signs.add("+")
            elif num < 0:
                signs.add("-")
        if signs == {"+", "-"}:
            defects.append(_defect(
                "MIXED_DIRECTION_SERIES", page_id, block_path,
                "양수·음수 metric이 한 viz에 혼재 — 음수 소실/방향 오독 위험. 지표 재명명(감소폭 등) 또는 이질 방향은 별도 callout 분리 검토",
            ))
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


def _raw_number_defects(value: Any, page_id: str, path: str, backed_numbers: set[str]) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for block, block_path in _iter_blocks(value, path):
        block_type = str(block.get("type", "")).strip()
        if block_type in RAW_EXCLUDED_BLOCK_TYPES:
            continue
        if block_type == "viz":
            defects.extend(_raw_number_viz_defects(block, page_id, block_path))
            continue
        if block_type == "text_table":
            defects.extend(_raw_number_text_table_defects(block, page_id, block_path, backed_numbers))
            continue
        if block_type in TEXT_BLOCK_TYPES:
            text = block.get("text")
            if _has_unbacked_raw_label_number(text, backed_numbers):
                defects.append(
                    _defect(
                        "RAW_NUMBER_IN_LABEL",
                        page_id,
                        f"{block_path}.text",
                        f"{block_type} contains raw number: {_clip(text)}",
                    )
                )
        if block_type == "bullets":
            defects.extend(_raw_number_bullet_defects(block, page_id, block_path, backed_numbers))
    return defects


def _raw_number_text_table_defects(
    block: dict[str, Any],
    page_id: str,
    block_path: str,
    backed_numbers: set[str],
) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for text, text_path in _iter_text_table_cells(block.get("rows"), f"{block_path}.rows"):
        if _has_unbacked_raw_label_number(text, backed_numbers):
            defects.append(
                _defect(
                    "RAW_NUMBER_IN_LABEL",
                    page_id,
                    text_path,
                    f"text_table cell contains raw number: {_clip(text)}",
                )
            )
    return defects


def _raw_number_viz_defects(block: dict[str, Any], page_id: str, block_path: str) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for field in ("title", "note"):
        text = block.get(field)
        if _has_data_number(text):
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
            if _has_data_number(label):
                defects.append(
                    _defect(
                        "RAW_NUMBER_IN_LABEL",
                        page_id,
                        f"{block_path}.series[{index}].label",
                        f"viz series label contains raw number: {_clip(label)}",
                    )
                )
    return defects


def _raw_number_bullet_defects(
    block: dict[str, Any],
    page_id: str,
    block_path: str,
    backed_numbers: set[str],
) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    items = block.get("items")
    if not isinstance(items, list):
        return defects
    for index, item in enumerate(items):
        item_path = f"{block_path}.items[{index}]"
        text = _item_text(item)
        if _has_unbacked_raw_label_number(text, backed_numbers):
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


def _has_unbacked_raw_label_number(text: Any, backed_numbers: set[str]) -> bool:
    if not _has_data_number(text) or not isinstance(text, str):
        return False
    numbers = [
        number
        for number, match in _iter_normalized_number_matches(text)
        if not _is_context_year_or_date_number(text, number, match)
    ]
    return any(number not in backed_numbers for number in numbers)


def _iter_normalized_number_matches(text: str):
    for match in NUMBER_PATTERN.finditer(text):
        number = _normalize_number(match.group(0))
        if number:
            yield number, match


def _is_context_year_or_date_number(text: str, number: str, match: re.Match[str]) -> bool:
    if FOUR_DIGIT_YEAR_PATTERN.fullmatch(number):
        return True
    suffix = text[match.end() :]
    if (
        re.fullmatch(r"\d{2}", number)
        and YEAR_RANGE_PREFIX_PATTERN.search(text[: match.start()])
        and re.match(r"\s*년", suffix)
    ):
        return True
    return bool(re.match(r"\s*[년월일]", suffix))


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


def _reader_first_exempt_page(page: dict[str, Any]) -> bool:
    if str(page.get("layout", "")).strip() == "source_appendix":
        return True
    short_title = str(page.get("short_title", "")).strip()
    return "방법" in short_title and "한계" in short_title


def _reader_first_defects(value: Any, page_id: str, path: str) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for text, text_path, field_kind in _iter_reader_first_texts(value, path):
        epistemic_term = _first_contained_term(text, READER_FIRST_EPISTEMIC_TERMS)
        if epistemic_term:
            defects.append(
                _defect(
                    "READER_FIRST_EPISTEMIC",
                    page_id,
                    text_path,
                    f"reader-first epistemic term '{epistemic_term}': {_clip(text)}",
                )
            )

        if field_kind in READER_FIRST_CAVEAT_FIELDS and text.lstrip().startswith("단, "):
            defects.append(
                _defect(
                    "READER_FIRST_CAVEAT",
                    page_id,
                    text_path,
                    f"reader-first caveat starts with '단, ': {_clip(text)}",
                )
            )

        self_ref_term = _first_contained_term(text, READER_FIRST_SELF_REF_TERMS)
        if self_ref_term:
            defects.append(
                _defect(
                    "READER_FIRST_SELF_REF",
                    page_id,
                    text_path,
                    f"reader-first self-reference '{self_ref_term}': {_clip(text)}",
                )
            )
    return defects


def _reader_first_jargon_defects(page: dict[str, Any], content: Any, page_id: str, page_path: str) -> list[dict[str, str]]:
    defects: list[dict[str, str]] = []
    for text, text_path in _iter_reader_first_jargon_texts(page, content, page_path):
        jargon_term = _first_contained_term(text, READER_FIRST_JARGON_TERMS)
        if not jargon_term:
            axis_match = READER_FIRST_JARGON_AXIS_PATTERN.search(text)
            jargon_term = axis_match.group(0) if axis_match else ""
        if jargon_term:
            defects.append(
                _defect(
                    "READER_FIRST_JARGON",
                    page_id,
                    text_path,
                    f"reader-first jargon term '{jargon_term}': {_clip(text)}",
                )
            )
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
        # 데이터 값(단위/강조 숫자)이 없는 텍스트는 근거 필요 없음 — 연도·섹션 카운터 오탐 제거(7/5 보정).
        if not _has_data_number(text):
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
            elif key == "rows" and isinstance(nested, list):
                yield from _iter_text_table_cells(nested, next_path)
            else:
                yield from _iter_visible_texts(nested, next_path, block_type)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_visible_texts(nested, f"{path}[{index}]", parent_block_type)


def _iter_reader_first_texts(value: Any, path: str, parent_block_type: str = ""):
    if isinstance(value, dict):
        block_type = str(value.get("type", parent_block_type)).strip() or parent_block_type
        for key, nested in value.items():
            next_path = f"{path}.{key}"
            if key in STRUCTURAL_TEXT_KEYS:
                continue
            if isinstance(nested, str) and key in READER_FIRST_TEXT_KEYS:
                field_kind = block_type if key == "text" and block_type in {"note", "callout", "headline"} else key
                yield nested, next_path, field_kind
            elif key == "items" and isinstance(nested, list):
                yield from _iter_reader_first_items(nested, next_path, block_type)
            elif key == "rows" and isinstance(nested, list):
                yield from _iter_reader_first_rows(nested, next_path, block_type)
            else:
                yield from _iter_reader_first_texts(nested, next_path, block_type)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_reader_first_texts(nested, f"{path}[{index}]", parent_block_type)


def _iter_reader_first_jargon_texts(page: dict[str, Any], content: Any, page_path: str):
    short_title = page.get("short_title")
    if isinstance(short_title, str):
        yield short_title, f"{page_path}.short_title"
    for text, text_path, _field_kind in _iter_reader_first_texts(content, f"{page_path}.content"):
        yield text, text_path
    yield from _iter_reader_first_text_table_columns(content, f"{page_path}.content")


def _iter_reader_first_text_table_columns(value: Any, path: str, parent_block_type: str = ""):
    if isinstance(value, dict):
        block_type = str(value.get("type", parent_block_type)).strip() or parent_block_type
        for key, nested in value.items():
            next_path = f"{path}.{key}"
            if block_type == "text_table" and key == "columns":
                if isinstance(nested, list):
                    for index, column in enumerate(nested):
                        column_path = f"{next_path}[{index}]"
                        if isinstance(column, str):
                            yield column, column_path
                        else:
                            yield from _iter_reader_first_text_table_columns(column, column_path, block_type)
                continue
            yield from _iter_reader_first_text_table_columns(nested, next_path, block_type)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_reader_first_text_table_columns(nested, f"{path}[{index}]", parent_block_type)


def _iter_reader_first_items(items: list[Any], path: str, parent_block_type: str):
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if isinstance(item, str):
            yield item, item_path, "text"
        elif isinstance(item, dict):
            text = _item_text(item)
            if text:
                yield text, f"{item_path}.text", "text"
            for item_key, item_nested in item.items():
                if item_key == "text":
                    continue
                yield from _iter_reader_first_texts(item_nested, f"{item_path}.{item_key}", parent_block_type)
        else:
            yield from _iter_reader_first_texts(item, item_path, parent_block_type)


def _iter_reader_first_rows(rows: list[Any], path: str, parent_block_type: str):
    for row_index, row in enumerate(rows):
        row_path = f"{path}[{row_index}]"
        if isinstance(row, list):
            for cell_index, cell in enumerate(row):
                cell_path = f"{row_path}[{cell_index}]"
                if isinstance(cell, str):
                    yield cell, cell_path, "text"
                else:
                    yield from _iter_reader_first_texts(cell, cell_path, parent_block_type)
        elif isinstance(row, str):
            yield row, row_path, "text"
        else:
            yield from _iter_reader_first_texts(row, row_path, parent_block_type)


def _iter_text_table_cells(rows: Any, path: str):
    if not isinstance(rows, list):
        return
    for row_index, row in enumerate(rows):
        row_path = f"{path}[{row_index}]"
        if isinstance(row, list):
            for cell_index, cell in enumerate(row):
                cell_path = f"{row_path}[{cell_index}]"
                if isinstance(cell, str):
                    yield cell, cell_path
                else:
                    yield from _iter_visible_texts(cell, cell_path, "text_table")
        elif isinstance(row, str):
            yield row, row_path
        else:
            yield from _iter_visible_texts(row, row_path, "text_table")


def _first_contained_term(text: str, terms: tuple[str, ...]) -> str:
    for term in terms:
        if term in text:
            return term
    return ""


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


def _run_selfcheck() -> int:
    registry: dict[str, Any] = {
        "metric_registry": {
            "sales_300": {"value": "300", "unit": "만개"},
            "ratio_156": {"value": "1.56"},
            "week_12": {"value": "12"},
            "week_26": {"value": "26"},
        }
    }
    cases = [
        (
            "reader_first_epistemic_body_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "body_epistemic",
                        "short_title": "본문",
                        "layout": "body",
                        "content": [{"type": "body", "text": "관찰되지 않는다"}],
                    }
                ],
            },
            {"READER_FIRST_EPISTEMIC"},
            set(),
        ),
        (
            "reader_first_epistemic_appendix_skipped",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "appendix_epistemic",
                        "short_title": "출처",
                        "layout": "source_appendix",
                        "content": [{"type": "body", "text": "관찰되지 않는다"}],
                    },
                    {
                        "page_id": "methods_epistemic",
                        "short_title": "방법과 한계",
                        "layout": "body",
                        "content": [{"type": "body", "text": "관찰되지 않는다"}],
                    },
                ],
            },
            set(),
            {"READER_FIRST_EPISTEMIC"},
        ),
        (
            "reader_first_caveat_note_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "body_caveat",
                        "short_title": "본문",
                        "layout": "body",
                        "content": [{"type": "note", "text": "단, 한계는 별도 확인한다"}],
                    }
                ],
            },
            {"READER_FIRST_CAVEAT"},
            set(),
        ),
        (
            "reader_first_self_ref_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "body_self_ref",
                        "short_title": "본문",
                        "layout": "body",
                        "content": [{"type": "callout", "text": "이 덱은 판단만 남긴다"}],
                    }
                ],
            },
            {"READER_FIRST_SELF_REF"},
            set(),
        ),
        (
            "text_table_rows_scanned_as_body_text",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "table_rows",
                        "short_title": "표",
                        "layout": "statement",
                        "content": [
                            {
                                "type": "text_table",
                                "columns": ["구분", "해석"],
                                "rows": [["단, 관찰되지 않는다", "성장 47%"]],
                            }
                        ],
                    }
                ],
            },
            {"READER_FIRST_CAVEAT", "READER_FIRST_EPISTEMIC", "RAW_NUMBER_IN_LABEL"},
            set(),
        ),
        (
            "backed_number_in_table_cell_passes",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "backed_table_cell",
                        "short_title": "표",
                        "layout": "statement",
                        "allowed_metric_ids": ["sales_300"],
                        "content": [
                            {
                                "type": "text_table",
                                "columns": ["구분", "해석"],
                                "rows": [["판매", "출시 1년 만에 300만 개 (2018~19년 얘기)"]],
                            }
                        ],
                    }
                ],
            },
            set(),
            {"RAW_NUMBER_IN_LABEL"},
        ),
        (
            "unbacked_number_in_table_cell_fails",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "unbacked_table_cell",
                        "short_title": "표",
                        "layout": "statement",
                        "allowed_metric_ids": ["sales_300"],
                        "content": [
                            {
                                "type": "text_table",
                                "columns": ["구분", "해석"],
                                "rows": [["판매", "999억을 팔았다"]],
                            }
                        ],
                    }
                ],
            },
            {"RAW_NUMBER_IN_LABEL"},
            set(),
        ),
        (
            "backed_number_in_body_passes",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "backed_body",
                        "short_title": "본문",
                        "layout": "body",
                        "allowed_metric_ids": ["week_12", "ratio_156", "week_26"],
                        "content": [
                            {
                                "type": "body",
                                "text": "12주엔 1.56배로 뚜렷했지만 26주엔 사라졌다",
                            }
                        ],
                    }
                ],
            },
            set(),
            {"RAW_NUMBER_IN_LABEL"},
        ),
        (
            "viz_label_number_still_fails",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "viz_label_raw",
                        "short_title": "차트",
                        "layout": "statement",
                        "allowed_metric_ids": ["sales_300"],
                        "content": [
                            {
                                "type": "viz",
                                "chart": "big_number",
                                "series": [{"metric_id": "sales_300", "label": "300만 개 판매"}],
                            }
                        ],
                    }
                ],
            },
            {"RAW_NUMBER_IN_LABEL"},
            set(),
        ),
        (
            "jargon_headline_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "jargon_headline",
                        "short_title": "본문",
                        "layout": "body",
                        "content": [
                            {
                                "type": "headline",
                                "text": "성장 신호를 낸 유사군은 저마다 ==신뢰 전달 장치==를 가졌다 — CLO에는 아직 없다",
                            }
                        ],
                    }
                ],
            },
            {"READER_FIRST_JARGON"},
            set(),
        ),
        (
            "jargon_short_title_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "jargon_short_title",
                        "short_title": "경영 요약 — 좌표·참고·결정 한 장",
                        "layout": "body",
                        "content": [{"type": "body", "text": "지금 상황과 해야 할 일을 정리한다"}],
                    }
                ],
            },
            {"READER_FIRST_JARGON"},
            set(),
        ),
        (
            "jargon_table_column_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "jargon_table_column",
                        "short_title": "표",
                        "layout": "statement",
                        "content": [
                            {
                                "type": "text_table",
                                "columns": ["브랜드", "신뢰 전달 장치", "성과 신호 성격"],
                                "rows": [["A", "소개 페이지", "성장했다"]],
                            }
                        ],
                    }
                ],
            },
            {"READER_FIRST_JARGON"},
            set(),
        ),
        (
            "jargon_axis_pattern_detected",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "jargon_axis_pattern",
                        "short_title": "본문",
                        "layout": "body",
                        "content": [{"type": "headline", "text": "플레이어 비교표 — 상위 7 × 4축"}],
                    }
                ],
            },
            {"READER_FIRST_JARGON"},
            set(),
        ),
        (
            "jargon_clean_pass",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "jargon_clean",
                        "short_title": "한 장 요약: 지금 상황과 해야 할 일",
                        "layout": "statement",
                        "content": [
                            {
                                "type": "headline",
                                "text": "잘 큰 경쟁사는 다 ==믿게 만드는 창구==가 있었다 — CLO만 아직 없다",
                            },
                            {
                                "type": "text_table",
                                "columns": ["브랜드", "무엇으로 믿게 만드나", "실제로 컸나"],
                                "rows": [["A", "소개 페이지", "그렇다"]],
                            },
                        ],
                    }
                ],
            },
            set(),
            {"READER_FIRST_JARGON"},
        ),
        (
            "jargon_appendix_skipped",
            {
                "archetype": "selfcheck",
                "pages": [
                    {
                        "page_id": "jargon_appendix",
                        "short_title": "출처",
                        "layout": "source_appendix",
                        "content": [{"type": "body", "text": "좌표"}],
                    }
                ],
            },
            set(),
            {"READER_FIRST_JARGON"},
        ),
    ]

    failures: list[str] = []
    for name, deck_spec, required, forbidden in cases:
        codes = {defect["code"] for defect in lint_deck(deck_spec, registry)}
        missing = sorted(required - codes)
        unexpected = sorted(forbidden & codes)
        if missing or unexpected:
            failures.append(f"{name}: missing={missing or 'none'} unexpected={unexpected or 'none'}")

    if failures:
        print("qa_lint selfcheck FAILED", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    print("qa_lint selfcheck OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
