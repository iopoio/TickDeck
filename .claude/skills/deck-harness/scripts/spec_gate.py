#!/usr/bin/env python3
"""Validate a draft deck spec through LAYOUT_ALGORITHM §G.4 gates 1–7."""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


SCRIPT_DIR = Path(__file__).resolve().parent
HARNESS_DIR = SCRIPT_DIR.parent
CALIBRATION_DIR = HARNESS_DIR / "calibration"
CONTRACT_DIR = HARNESS_DIR.parent / "harness-contracts" / "scripts"
for import_dir in (SCRIPT_DIR, CALIBRATION_DIR, CONTRACT_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import layout_budget
import run_contracts
from contract_checks import (
    SUPPORTED_CONTENT_BLOCK_TYPES,
    SUPPORTED_LAYOUTS,
    check_c13_role_duplication,
    check_c14_viz_intent_preserved,
    check_deck_spec_gates,
    check_page_visual_intent_preserved,
)
from generate_deck_spec_schema import schema_bytes, schema_hash
from predictor import (
    KEY_DIMENSIONS,
    CalibrationFormatError,
    CalibrationRuntimeKeyError,
    UncalibratedCombinationError,
    css_hash,
    font_build_hash,
    renderer_struct_hash,
    resolve_entry,
    sha256_bytes,
    sha256_file,
    validate_key,
)


DEFAULT_CALIBRATION = CALIBRATION_DIR / "layout_calibration.json"
KST = ZoneInfo("Asia/Seoul")


class Verdict(str, Enum):
    PASS = "PASS"
    SKIPPED = "SKIPPED"
    REJECTED = "REJECTED"
    BLOCKED_ON_MEASUREMENT = "BLOCKED_ON_MEASUREMENT"
    BLOCKED_ON_UPSTREAM = "BLOCKED_ON_UPSTREAM"


class DraftChangedError(RuntimeError):
    pass


@dataclass
class GateResult:
    gate: int
    name: str
    verdict: str
    details: list[str]
    warnings: list[str]


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, raw_temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temp = Path(raw_temp)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def assert_draft_unchanged(draft: Path, expected_sha256: str) -> None:
    current = sha256_file(draft)
    if current != expected_sha256:
        raise DraftChangedError(
            f"TOCTOU draft SHA mismatch: checked={expected_sha256} current={current}"
        )


def promote_pair(run_dir: Path, spec_data: bytes, receipt_data: bytes) -> None:
    """Replace canonical spec and receipt together, restoring the old pair on error."""

    canonical = run_dir / "06_deck_spec.json"
    receipt = run_dir / "06_deck_spec.receipt.json"
    run_dir.mkdir(parents=True, exist_ok=True)
    staged: list[Path] = []
    backups: dict[Path, Path] = {}
    try:
        for target, data in ((canonical, spec_data), (receipt, receipt_data)):
            fd, raw_temp = tempfile.mkstemp(prefix=f".{target.name}.new.", dir=run_dir)
            temp = Path(raw_temp)
            staged.append(temp)
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        for target in (canonical, receipt):
            if target.exists():
                backup = run_dir / f".{target.name}.rollback"
                os.replace(target, backup)
                backups[target] = backup
        os.replace(staged[0], canonical)
        os.replace(staged[1], receipt)
    except BaseException:
        for target in (canonical, receipt):
            if target.exists() and target not in backups:
                target.unlink()
            elif target.exists() and target in backups:
                target.unlink()
        for target, backup in backups.items():
            if backup.exists():
                os.replace(backup, target)
        raise
    finally:
        for path in staged:
            if path.exists():
                path.unlink()
        for backup in backups.values():
            if backup.exists():
                backup.unlink()


def _divider_label(page: dict[str, Any]) -> str:
    label = str(page.get("part_label", "")).strip()
    if label:
        return label
    for block in page.get("content", []):
        if isinstance(block, dict) and block.get("type") in {"headline", "title"}:
            text = str(block.get("text", "")).strip()
            if text:
                return text
    return str(page.get("short_title", "")).strip()


def apply_automatic_values(spec: dict[str, Any]) -> list[str]:
    pages = spec.get("pages") if isinstance(spec, dict) else None
    if not isinstance(pages, list):
        return []
    warnings: list[str] = []
    dividers = [page for page in pages if isinstance(page, dict) and page.get("layout") == "divider"]
    part_count = len(dividers)
    divider_index = 0
    index_items = [label for page in dividers if (label := _divider_label(page))]
    for page_number, page in enumerate(pages, 1):
        if not isinstance(page, dict):
            continue
        expected_id = f"p{page_number:02d}"
        if page.get("page_id") != expected_id:
            warnings.append(f"page_id {page.get('page_id')!r} → {expected_id}")
            page["page_id"] = expected_id
        if page.get("layout") == "divider":
            divider_index += 1
            for field, expected in (("part_index", divider_index), ("part_count", part_count)):
                if page.get(field) != expected:
                    warnings.append(f"{expected_id}.{field} {page.get(field)!r} → {expected}")
                    page[field] = expected
        if page.get("layout") == "index":
            content = page.get("content") if isinstance(page.get("content"), list) else []
            kept = [block for block in content if not (isinstance(block, dict) and block.get("type") in {"bullets", "list"})]
            if len(kept) != len(content):
                warnings.append(f"{expected_id}.content 손작성 목차 → 계산값")
            if index_items:
                kept.append({"type": "list", "items": index_items})
            page["content"] = kept
    return warnings


def _schema_violations(spec: Any) -> list[str]:
    generated = json.loads(schema_bytes())
    if not isinstance(spec, dict):
        return ["draft root must be an object"]
    pages = spec.get("pages")
    if not isinstance(pages, list):
        return ["pages must be an array"]
    violations: list[str] = []
    layout_enum = set(generated["properties"]["pages"]["items"]["properties"]["layout"]["enum"])
    block_enum = set(generated["properties"]["pages"]["items"]["properties"]["content"]["items"]["properties"]["type"]["enum"])
    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            violations.append(f"pages[{page_index}] must be an object")
            continue
        if page.get("layout") not in layout_enum or page.get("layout") not in SUPPORTED_LAYOUTS:
            violations.append(f"pages[{page_index}].layout unsupported: {page.get('layout')!r}")
        content = page.get("content")
        if not isinstance(content, list):
            violations.append(f"pages[{page_index}].content must be an array")
            continue
        for block_index, block in enumerate(content):
            if not isinstance(block, dict):
                violations.append(f"pages[{page_index}].content[{block_index}] must be an object")
            elif block.get("type") not in block_enum or block.get("type") not in SUPPORTED_CONTENT_BLOCK_TYPES:
                violations.append(
                    f"pages[{page_index}].content[{block_index}].type unsupported: {block.get('type')!r}"
                )
    return violations


def classify_layout_results(results: list[Any] | tuple[Any, ...]) -> tuple[Verdict, list[str]]:
    blocked: list[str] = []
    rejected: list[str] = []
    for result in results:
        page_id = str(getattr(result, "page_id", "?"))
        verdict = str(getattr(result, "verdict", ""))
        reasons = "; ".join(str(reason) for reason in getattr(result, "reasons", ()))
        if verdict.endswith("RENDER_MEASURE_REQUIRED"):
            blocked.append(f"{page_id}: {reasons or 'renderer measurement required'}")
        elif verdict.endswith("INVALID_INPUT"):
            rejected.append(f"{page_id}: {reasons or 'invalid layout input'}")
        elif verdict.endswith("OVERFLOW"):
            rejected.append(f"{page_id}: OVERFLOW — §C.1 cascade required")
    if rejected:
        return Verdict.REJECTED, rejected
    if blocked:
        return Verdict.BLOCKED_ON_MEASUREMENT, blocked
    return Verdict.PASS, []


def classify_visual_intent(page_plan: dict[str, Any], spec: dict[str, Any]) -> tuple[Verdict, list[str]]:
    plan_pages = page_plan.get("pages") if isinstance(page_plan, dict) else None
    spec_pages = spec.get("pages") if isinstance(spec, dict) else None
    unsupported: list[str] = []
    if not isinstance(plan_pages, list) or not plan_pages:
        unsupported.append("page_plan.pages missing")
    else:
        for index, page in enumerate(plan_pages):
            intent = page.get("visual_intent") if isinstance(page, dict) else None
            if not isinstance(intent, dict):
                unsupported.append(f"page_plan.pages[{index}].visual_intent missing")
    if isinstance(spec_pages, list):
        for index, page in enumerate(spec_pages):
            if isinstance(page, dict) and not str(page.get("plan_id", "")).strip():
                unsupported.append(f"deck_spec.pages[{index}].plan_id missing")
    if unsupported:
        return Verdict.BLOCKED_ON_UPSTREAM, unsupported
    violations = check_c14_viz_intent_preserved(page_plan, spec)
    violations.extend(check_page_visual_intent_preserved(page_plan, spec))
    if violations:
        return Verdict.REJECTED, [str(item) for item in violations]
    return Verdict.PASS, []


def _layout_results(
    spec: dict[str, Any], registry: dict[str, Any], calibration_doc: dict[str, Any]
) -> tuple[Any, ...]:
    meta = spec.get("meta") if isinstance(spec.get("meta"), dict) else {}
    runtime = meta.get("calibration_runtime") if isinstance(meta.get("calibration_runtime"), dict) else {}
    pages = spec.get("pages", [])

    def error_result(page: dict[str, Any], verdict: str, reason: str) -> layout_budget.PageBudget:
        return layout_budget.PageBudget(
            page_id=str(page.get("page_id", "?")),
            verdict=verdict,
            height_px=None,
            capacity_px=None,
            overflow_cutoff_px=None,
            sparse_cutoff_px=None,
            reasons=(reason,),
        )

    try:
        common = {
            "renderer_struct_hash": renderer_struct_hash(),
            "css_hash": css_hash(str(spec.get("theme", ""))),
            "theme": str(spec.get("theme", "")),
            "page_chrome": str(meta.get("page_chrome", "")),
            "width_class": str(runtime.get("width_class", "")),
            "font_build": font_build_hash(),
            "browser_major": str(runtime.get("browser_major", "")),
        }
    except CalibrationRuntimeKeyError as exc:
        return tuple(error_result(page, "RENDER_MEASURE_REQUIRED", str(exc)) for page in pages)

    results: list[Any] = []
    for page in pages:
        one_page_spec = copy.deepcopy(spec)
        one_page_spec["pages"] = [copy.deepcopy(page)]
        try:
            requested_key = validate_key({**common, "layout": str(page.get("layout", ""))})
        except CalibrationFormatError as exc:
            results.append(error_result(page, "RENDER_MEASURE_REQUIRED", str(exc)))
            continue
        try:
            entry = resolve_entry(calibration_doc, requested_key)
            results.extend(layout_budget.evaluate_layout(one_page_spec, registry, entry))
        except (UncalibratedCombinationError, CalibrationRuntimeKeyError) as exc:
            results.append(error_result(page, "RENDER_MEASURE_REQUIRED", str(exc)))
        except (CalibrationFormatError, layout_budget.LayoutBudgetInputError) as exc:
            results.append(error_result(page, "INVALID_INPUT", str(exc)))
    return tuple(results)


def _result(gate: int, name: str, verdict: Verdict, details: list[str], warnings: list[str] | None = None) -> GateResult:
    return GateResult(gate, name, verdict.value, details, warnings or [])


def _overall(results: list[GateResult]) -> Verdict:
    verdicts = {result.verdict for result in results}
    if Verdict.REJECTED.value in verdicts:
        return Verdict.REJECTED
    if Verdict.BLOCKED_ON_UPSTREAM.value in verdicts:
        return Verdict.BLOCKED_ON_UPSTREAM
    if Verdict.BLOCKED_ON_MEASUREMENT.value in verdicts:
        return Verdict.BLOCKED_ON_MEASUREMENT
    return Verdict.PASS


def _receipt_payload(
    spec_data: bytes,
    registry_path: Path,
    calibration_path: Path,
    spec: dict[str, Any],
    gate_results: list[GateResult],
) -> dict[str, Any]:
    def runtime_hash(value: Callable[[], str]) -> str | None:
        try:
            return value()
        except CalibrationRuntimeKeyError:
            return None

    return {
        "spec_sha256": sha256_bytes(spec_data),
        "registry_sha256": sha256_file(registry_path),
        "calibration_sha256": sha256_file(calibration_path),
        "renderer_struct_hash": runtime_hash(renderer_struct_hash),
        "css_hash": runtime_hash(lambda: css_hash(str(spec.get("theme", "")))),
        "schema_hash": schema_hash(),
        "gate_results": [asdict(result) for result in gate_results],
        "issued_at": datetime.now(KST).isoformat(timespec="seconds"),
    }


def isolate_rejected(run_dir: Path, draft_data: bytes, receipt_payload: dict[str, Any]) -> tuple[Path, Path]:
    stamp = datetime.now(KST).strftime("%Y%m%dT%H%M%S%z")
    short_hash = sha256_bytes(draft_data)[:12]
    rejected = run_dir / f"06_deck_spec.rejected.{stamp}.{short_hash}.json"
    rejected_receipt = rejected.with_suffix(".receipt.json")
    _atomic_write(rejected, draft_data)
    _atomic_write(rejected_receipt, _json_bytes(receipt_payload))
    return rejected, rejected_receipt


def run_gate(
    run_dir: Path,
    draft_path: Path,
    plan_path: Path,
    registry_path: Path,
    calibration_path: Path,
    *,
    before_promote: Callable[[], None] | None = None,
) -> tuple[Verdict, list[GateResult], str]:
    raw = draft_path.read_bytes()
    spec = json.loads(raw)
    page_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))
    intake_path = run_dir / "00_intake.json"
    intake = json.loads(intake_path.read_text(encoding="utf-8")) if intake_path.exists() else {}
    results: list[GateResult] = []

    schema_errors = _schema_violations(spec)
    results.append(_result(1, "schema_vocabulary", Verdict.REJECTED if schema_errors else Verdict.PASS, schema_errors))
    if schema_errors:
        checked_data = raw
    else:
        warnings = apply_automatic_values(spec)
        checked_data = _json_bytes(spec)
        _atomic_write(draft_path, checked_data)
        results.append(_result(2, "automatic_values", Verdict.PASS, [], warnings))

        layout_results = _layout_results(spec, registry, calibration)
        layout_verdict, layout_details = classify_layout_results(layout_results)
        results.append(_result(3, "layout_budget", layout_verdict, layout_details))
        if layout_verdict is Verdict.BLOCKED_ON_MEASUREMENT:
            payload = _receipt_payload(checked_data, registry_path, calibration_path, spec, results)
            payload["verdict"] = layout_verdict.value
            rejected, rejected_receipt = isolate_rejected(run_dir, checked_data, payload)
            return layout_verdict, results, f"isolated={rejected.name} receipt={rejected_receipt.name}"

        # 사고 6건/정상 6건으로 변별력 0 (Round 3 실측). negative set 확대 또는 판정 방식 변경 시 재활성화.
        results.append(_result(4, "c13_role_duplication", Verdict.SKIPPED, []))

        intent_verdict, intent_details = classify_visual_intent(page_plan, spec)
        results.append(_result(5, "visual_intent", intent_verdict, intent_details))

        deck_gate = check_deck_spec_gates(
            page_plan, spec, intake, registry, calibration, layout_results=layout_results
        )
        measurement_only = [
            str(item) for item in deck_gate.violations
            if "layout_budget" in str(item) or "높이·용량" in str(item)
        ]
        deck_violations = [str(item) for item in deck_gate.violations if str(item) not in measurement_only]
        deck_verdict = Verdict.REJECTED if deck_violations else (
            Verdict.BLOCKED_ON_MEASUREMENT if measurement_only else Verdict.PASS
        )
        results.append(_result(
            6, "deck_spec_gates", deck_verdict, deck_violations or measurement_only,
            [str(item) for item in deck_gate.warnings],
        ))

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            contract_exit = run_contracts.main([
                str(run_dir), "--spec", str(draft_path), "--plan", str(plan_path),
                "--skip-spec-gates",
            ])
        contract_text = output.getvalue().strip()
        results.append(_result(
            7, "run_contracts", Verdict.PASS if contract_exit == 0 else Verdict.REJECTED,
            [] if contract_exit == 0 else [contract_text],
        ))

    overall = _overall(results)
    payload = _receipt_payload(checked_data, registry_path, calibration_path, spec, results)
    payload["verdict"] = overall.value
    if overall is Verdict.PASS:
        checked_sha = sha256_bytes(checked_data)
        if before_promote:
            before_promote()
        try:
            assert_draft_unchanged(draft_path, checked_sha)
        except DraftChangedError:
            changed_data = draft_path.read_bytes()
            payload["verdict"] = Verdict.REJECTED.value
            results.append(_result(7, "toctou", Verdict.REJECTED, ["draft changed after validation"]))
            payload["spec_sha256"] = sha256_bytes(changed_data)
            payload["gate_results"] = [asdict(result) for result in results]
            isolate_rejected(run_dir, changed_data, payload)
            raise
        promote_pair(run_dir, checked_data, _json_bytes(payload))
        return overall, results, "promoted"
    rejected, rejected_receipt = isolate_rejected(run_dir, checked_data, payload)
    return overall, results, f"isolated={rejected.name} receipt={rejected_receipt.name}"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gate and atomically promote a TickDeck deck spec draft.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--draft", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--calibration", type=Path, default=DEFAULT_CALIBRATION)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    run_dir = args.run_dir
    draft = args.draft or run_dir / "06_deck_spec.draft.json"
    plan = args.plan or run_dir / "05_page_plan.json"
    registry = args.registry or run_dir / "02_verified.json"
    try:
        verdict, results, action = run_gate(run_dir, draft, plan, registry, args.calibration)
    except (OSError, ValueError, json.JSONDecodeError, DraftChangedError) as exc:
        print(f"ERROR {type(exc).__name__}: {exc}")
        return 2
    for result in results:
        print(f"GATE {result.gate} {result.name}: {result.verdict}")
        for warning in result.warnings:
            print(f"  WARN {warning}")
        for detail in result.details:
            print(f"  - {detail}")
    print(f"VERDICT {verdict.value} · {action}")
    return {
        Verdict.PASS: 0,
        Verdict.REJECTED: 1,
        Verdict.BLOCKED_ON_MEASUREMENT: 3,
        Verdict.BLOCKED_ON_UPSTREAM: 4,
    }[verdict]


if __name__ == "__main__":
    raise SystemExit(main())
