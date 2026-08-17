#!/usr/bin/env python3
"""Decide TickDeck DELIVERY_OK by orchestrating LAYOUT_ALGORITHM §G.5 checks."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo


SCRIPT_DIR = Path(__file__).resolve().parent
CONTRACTS = SCRIPT_DIR.parent.parent / "harness-contracts" / "scripts" / "run_contracts.py"
KST = ZoneInfo("Asia/Seoul")
Runner = Callable[..., subprocess.CompletedProcess[str]]


def _run(runner: Runner, check_id: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    kwargs = {"capture_output": True, "text": True}
    try:
        try:
            return runner(command, delivery_check=check_id, **kwargs)
        except TypeError:
            return runner(command, **kwargs)
    except OSError as exc:
        return subprocess.CompletedProcess(command, 127, stdout="", stderr=f"{type(exc).__name__}: {exc}")


def _detail(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout or f"exit {result.returncode}").strip()


def _result(check_id: str, name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {
        "id": check_id,
        "name": name,
        "verdict": "PASS" if passed else "FAIL",
        "detail": detail,
    }


def count_embedded_fonts(pdffonts_output: str) -> int:
    count = 0
    for line in pdffonts_output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("name") or set(stripped) <= {"-", " "}:
            continue
        columns = stripped.split()
        if len(columns) >= 8 and columns[-5].lower() == "yes":
            count += 1
    return count


def validate_visual_review(run_dir: Path) -> tuple[bool, str]:
    report_path = run_dir / "07_qa_report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return False, f"07_qa_report.json unavailable: {exc}"
    review = report.get("visual_review")
    if not isinstance(review, dict):
        return False, "visual_review record missing"
    missing = [
        field for field in ("reviewer", "reviewed_at", "montage_path")
        if not str(review.get(field, "")).strip()
    ]
    if review.get("scope") != "all_pages":
        missing.append("scope=all_pages")
    reviewed_at = str(review.get("reviewed_at", ""))
    try:
        datetime.fromisoformat(reviewed_at)
    except ValueError:
        missing.append("reviewed_at ISO-8601")
    run_root = run_dir.resolve()
    montage = (run_dir / str(review.get("montage_path", ""))).resolve()
    if not montage.is_relative_to(run_root):
        missing.append("montage_path inside run_dir")
    if not missing and not montage.is_file():
        missing.append(f"montage file: {montage}")
    if missing:
        return False, "missing " + ", ".join(missing)
    return True, f"reviewer={review['reviewer']} reviewed_at={review['reviewed_at']} montage={montage}"


def _unattested_artifacts(run_dir: Path) -> list[str]:
    found = [str(path.relative_to(run_dir)) for path in run_dir.rglob("*") if path.is_file() and ".unattested." in path.name]
    for html in run_dir.rglob("*.html"):
        try:
            if "UNATTESTED" in html.read_text(encoding="utf-8"):
                relative = str(html.relative_to(run_dir))
                if relative not in found:
                    found.append(relative)
        except (OSError, UnicodeError):
            continue
    return sorted(found)


def evaluate(run_dir: Path, runner: Runner | None = None) -> dict[str, Any]:
    runner = runner or subprocess.run
    spec = run_dir / "06_deck_spec.json"
    registry = run_dir / "02_verified.json"
    html = run_dir / "deck.html"
    pdf = run_dir / "deck.pdf"
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="tickdeck-delivery-") as temp_dir:
        temp = Path(temp_dir)
        checks = (
            ("receipt", "receipt validity", [
                sys.executable, str(SCRIPT_DIR / "render_deck.py"), str(spec), str(registry),
                "-o", str(temp / "receipt-check.html"), "--html-only",
            ]),
            ("run_contracts", "final run_contracts", [
                sys.executable, str(CONTRACTS), str(run_dir), "--skip-spec-gates",
            ]),
            ("fit_overflow", "FIT overflow", [
                str(SCRIPT_DIR / "capture_deck.sh"), str(html), str(temp / "fit-check.pdf"),
            ]),
            ("ink_distribution", "ink distribution", [
                sys.executable, str(SCRIPT_DIR / "qa_ink.py"), str(pdf),
            ]),
            ("deck_intent", "deck gate and intent preservation", [
                sys.executable, str(CONTRACTS), str(run_dir),
            ]),
        )
        for check_id, name, command in checks:
            completed = _run(runner, check_id, command)
            passed = completed.returncode == 0
            detail = _detail(completed)
            if check_id == "fit_overflow":
                passed = "FIT_OK:" in completed.stdout and "FIT_OVERFLOW:" not in completed.stdout
            if check_id == "ink_distribution" and not completed.stdout.strip().startswith("INK_OK:"):
                passed = False
            if check_id == "receipt":
                unattested = _unattested_artifacts(run_dir)
                if unattested:
                    passed = False
                    detail = "unattested artifacts: " + ", ".join(unattested)
            results.append(_result(check_id, name, passed, detail))

        font_check = _run(runner, "pdf_text_layer", ["pdffonts", str(pdf)])
        embedded = count_embedded_fonts(font_check.stdout) if font_check.returncode == 0 else 0
        results.append(_result(
            "pdf_text_layer",
            "PDF text layer",
            font_check.returncode == 0 and embedded >= 1,
            f"embedded_fonts={embedded}" if font_check.returncode == 0 else _detail(font_check),
        ))

    visual_ok, visual_detail = validate_visual_review(run_dir)
    results.append(_result("visual_review", "all-page visual review", visual_ok, visual_detail))
    verdict = "PASS" if all(item["verdict"] == "PASS" for item in results) else "FAIL"
    return {
        "verdict": verdict,
        "issued_at": datetime.now(KST).isoformat(timespec="seconds"),
        "run_dir": str(run_dir.resolve()),
        "results": results,
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate the seven DELIVERY_OK checks for a TickDeck run.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    output = args.output or args.run_dir / "08_delivery_report.json"
    try:
        report = evaluate(args.run_dir)
    except (OSError, ValueError) as exc:
        detail = f"evaluation aborted: {type(exc).__name__}: {exc}"
        report = {
            "verdict": "FAIL",
            "issued_at": datetime.now(KST).isoformat(timespec="seconds"),
            "run_dir": str(args.run_dir.resolve()),
            "results": [
                _result(check_id, name, False, detail)
                for check_id, name in (
                    ("receipt", "receipt validity"),
                    ("run_contracts", "final run_contracts"),
                    ("fit_overflow", "FIT overflow"),
                    ("ink_distribution", "ink distribution"),
                    ("deck_intent", "deck gate and intent preservation"),
                    ("pdf_text_layer", "PDF text layer"),
                    ("visual_review", "all-page visual review"),
                )
            ],
            "error": detail,
        }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in report.get("results", []):
        print(f"{item['id']}: {item['verdict']} — {item['detail']}")
    print(f"DELIVERY_{report['verdict']} · {output}")
    return 0 if report["verdict"] == "PASS" and len(report.get("results", [])) == 7 else 1


if __name__ == "__main__":
    raise SystemExit(main())
