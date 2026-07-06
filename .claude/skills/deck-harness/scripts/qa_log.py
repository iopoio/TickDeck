#!/usr/bin/env python3
"""Append one TickDeck run quality measurement to _workspace/_quality_log.jsonl."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CONTRACTS_SCRIPT = SCRIPT_DIR.parents[1] / "harness-contracts" / "scripts" / "run_contracts.py"
CAPTURE_SCRIPT = SCRIPT_DIR / "capture_deck.sh"
FIT_PRIORITY = (
    "FIT_ANNOTATION_OVERLAP",
    "FIT_TEXT_OVERLAP",
    "FIT_BAND_OVERFLOW",
    "FIT_OVERFLOW",
    "FIT_HOVERFLOW",
    "FIT_LOWCONTRAST",
    "FIT_SPARSE",
    "FIT_OK",
)


def _load_json(path: Path, errors: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        errors.append(f"missing {path.name}")
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - logging must not block the loop.
        errors.append(f"parse {path.name}: {exc}")
        return None
    if not isinstance(loaded, dict):
        errors.append(f"parse {path.name}: expected object")
        return None
    return loaded


def _top_or_meta(payload: dict[str, Any] | None, key: str) -> str | None:
    if not payload:
        return None
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    value = payload.get(key) or meta.get(key)
    value = str(value or "").strip()
    return value or None


def _page_count(deck_spec: dict[str, Any] | None, errors: list[str]) -> int | None:
    if not deck_spec:
        return None
    pages = deck_spec.get("pages")
    if not isinstance(pages, list):
        errors.append("parse 06_deck_spec.json: pages is not a list")
        return None
    return len(pages)


def _run_contracts(run_dir: Path, errors: list[str]) -> tuple[bool, int | None, list[str]]:
    try:
        result = subprocess.run(
            [sys.executable, str(CONTRACTS_SCRIPT), str(run_dir)],
            capture_output=True,
            text=True,
        )
    except Exception as exc:  # noqa: BLE001 - quality logging must still append.
        errors.append(f"run_contracts failed: {exc}")
        return False, None, []

    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    codes = _unique(re.findall(r"^FAIL\s+(C[1-6])\b", output, flags=re.MULTILINE))
    count_match = re.search(r"→\s*(\d+)건 위반", output)
    if count_match:
        violation_count: int | None = int(count_match.group(1))
    elif result.returncode == 0:
        violation_count = 0
    elif codes:
        violation_count = len(re.findall(r"^FAIL\s+C[1-6]\b", output, flags=re.MULTILINE))
    else:
        violation_count = None
        errors.append(f"run_contracts exit {result.returncode}: {_first_line(output)}")

    if result.returncode not in (0, 1):
        errors.append(f"run_contracts exit {result.returncode}: {_first_line(output)}")
    return result.returncode == 0, violation_count, codes


def _capture_quality(run_dir: Path, errors: list[str]) -> tuple[str | None, float | None]:
    html_path = _latest_html(run_dir)
    if html_path is None:
        errors.append("missing rendered html for FIT/ink")
        return None, None
    if not CAPTURE_SCRIPT.exists():
        errors.append("missing capture_deck.sh for FIT/ink")
        return None, None

    with tempfile.TemporaryDirectory() as td:
        tmp_html = Path(td) / html_path.name
        tmp_pdf = Path(td) / f"{html_path.stem}.pdf"
        shutil.copyfile(html_path, tmp_html)
        result = subprocess.run(
            ["bash", str(CAPTURE_SCRIPT), str(tmp_html), str(tmp_pdf)],
            capture_output=True,
            text=True,
        )
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    if result.returncode != 0:
        errors.append(f"capture_deck exit {result.returncode}: {_first_line(output)}")

    fit_status = _parse_fit_status(output)
    if fit_status is None:
        skip = re.search(r"^FIT_CHECK_SKIP:\s*(.+)$", output, flags=re.MULTILINE)
        errors.append(f"fit parse: {skip.group(1) if skip else 'status not found'}")

    ink_min = _parse_ink_min(output)
    if ink_min is None:
        skip = re.search(r"^INK_CHECK_SKIP:\s*(.+)$", output, flags=re.MULTILINE)
        errors.append(f"ink parse: {skip.group(1) if skip else 'min not found'}")

    return fit_status, ink_min


def _latest_html(run_dir: Path) -> Path | None:
    candidates = [path for path in run_dir.glob("*.html") if "__fit__" not in path.name]
    return max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None


def _parse_fit_status(output: str) -> str | None:
    for status in FIT_PRIORITY:
        if re.search(rf"^{status}:", output, flags=re.MULTILINE):
            return status
    return None


def _parse_ink_min(output: str) -> float | None:
    ok = re.search(r"^INK_OK:\s+min\s+p\d+\s+([0-9.]+)%", output, flags=re.MULTILINE)
    if ok:
        return float(ok.group(1))
    empty = [float(value) for value in re.findall(r"^INK_EMPTY:\s+p\d+\s+\(([0-9.]+)%\)", output, flags=re.MULTILINE)]
    return min(empty) if empty else None


def _quality_log_path(run_dir: Path) -> Path:
    if run_dir.parent.name == "_workspace":
        return run_dir.parent / "_quality_log.jsonl"
    return Path.cwd() / "_workspace" / "_quality_log.jsonl"


def _first_line(text: str) -> str:
    line = text.strip().splitlines()[0] if text.strip() else "no output"
    return line[:300]


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            unique_values.append(value)
    return unique_values


def main() -> int:
    parser = argparse.ArgumentParser(description="Append one run quality measurement.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--phase", required=True, choices=("raw", "fixed"))
    parser.add_argument("--note", default="")
    args = parser.parse_args()

    run_dir = args.run_dir.resolve()
    errors: list[str] = []
    if not run_dir.is_dir():
        errors.append(f"NO_RUN_DIR: {run_dir}")

    page_plan = _load_json(run_dir / "05_page_plan.json", errors)
    deck_spec = _load_json(run_dir / "06_deck_spec.json", errors)
    contracts_ok, violation_count, violation_codes = _run_contracts(run_dir, errors)
    fit_status, ink_min = _capture_quality(run_dir, errors)

    record: dict[str, Any] = {
        "run_id": run_dir.name,
        "ts": time.time(),
        "phase": args.phase,
        "archetype": _top_or_meta(page_plan, "archetype"),
        "theme": _top_or_meta(deck_spec, "theme"),
        "page_count": _page_count(deck_spec, errors),
        "contracts_ok": contracts_ok,
        "violation_count": violation_count,
        "violation_codes": violation_codes,
        "fit_status": fit_status,
        "ink_min": ink_min,
        "note": args.note,
    }
    if errors:
        record["error"] = "; ".join(_unique(errors))

    line = json.dumps(record, ensure_ascii=False, sort_keys=True)
    log_path = _quality_log_path(run_dir)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
