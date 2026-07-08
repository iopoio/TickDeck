#!/usr/bin/env python3
"""Dump the deck-exposed metric crosswalk table for fact-checker (R7).

Reads a run directory's 06_deck_spec.json (rendered page tree) plus
02_verified.json (metric_registry / source_registry) and writes
08_factcheck_table.json: one row per (metric_id, page) actually shown in the
deck, with its value/unit/period and a pointer back to the source that
verified it. Metrics with no source pointer are flagged, not hidden
(fact-checker.md gate depends on that).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

TABLE_FILE = "08_factcheck_table.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_metric_refs(node: Any, out: list[str]) -> None:
    """Recursively collect every metric_id / metric_ids reference under a page content tree."""
    if isinstance(node, dict):
        metric_id = node.get("metric_id")
        if isinstance(metric_id, str):
            out.append(metric_id)
        metric_ids = node.get("metric_ids")
        if isinstance(metric_ids, list):
            out.extend(m for m in metric_ids if isinstance(m, str))
        for value in node.values():
            collect_metric_refs(value, out)
    elif isinstance(node, list):
        for item in node:
            collect_metric_refs(item, out)


def page_no_of(page: dict[str, Any], fallback_index: int) -> int:
    match = re.search(r"\d+", str(page.get("page_id", "")))
    return int(match.group()) if match else fallback_index


def claim_context_of(page: dict[str, Any]) -> str:
    parts = [page.get("short_title", "")]
    for block in page.get("content", []):
        if block.get("type") == "headline" and block.get("text"):
            parts.append(block["text"])
            break
    return " — ".join(p for p in parts if p)


def build_table(deck_spec: dict[str, Any], verified: dict[str, Any]) -> list[dict[str, Any]]:
    metric_registry = verified.get("metric_registry", {})
    source_registry = verified.get("source_registry", {})
    rows: list[dict[str, Any]] = []

    for index, page in enumerate(deck_spec.get("pages", []), start=1):
        refs: list[str] = []
        collect_metric_refs(page.get("content", []), refs)
        if not refs:
            continue

        page_no = page_no_of(page, index)
        claim_context = claim_context_of(page)
        seen_on_page: set[str] = set()

        for metric_id in refs:
            if metric_id in seen_on_page:
                continue  # same metric referenced twice on one page (chart + callout) -> one row
            seen_on_page.add(metric_id)

            metric = metric_registry.get(metric_id)
            row: dict[str, Any] = {
                "metric_id": metric_id,
                "page_no": page_no,
                "value": metric.get("value") if metric else None,
                "unit": metric.get("unit") if metric else None,
                "period": metric.get("period") if metric else None,
                "claim_context": claim_context,
            }
            if metric is None:
                row["registry_missing"] = True
                row["source_missing"] = True
                rows.append(row)
                continue

            source_ids = metric.get("source_ids") or []
            source_id = source_ids[0] if source_ids else None
            if not source_id:
                row["source_missing"] = True
                rows.append(row)
                continue

            source = source_registry.get(source_id, {})
            row["source_id"] = source_id
            if source.get("url"):
                row["source_url"] = source["url"]
            elif source.get("local_path"):
                row["local_path"] = source["local_path"]
            else:
                row["source_missing"] = True
            rows.append(row)

    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dump the fact-check crosswalk table for a TickDeck run.")
    parser.add_argument("--run", required=True, help="Run directory containing 06_deck_spec.json + 02_verified.json")
    args = parser.parse_args(argv)

    run_dir = Path(args.run)
    deck_spec_path = run_dir / "06_deck_spec.json"
    verified_path = run_dir / "02_verified.json"
    if not deck_spec_path.exists():
        print(f"NO_DECK_SPEC: {deck_spec_path}", file=sys.stderr)
        return 2
    if not verified_path.exists():
        print(f"NO_VERIFIED: {verified_path}", file=sys.stderr)
        return 2

    deck_spec = load_json(deck_spec_path)
    verified = load_json(verified_path)
    rows = build_table(deck_spec, verified)

    output_path = run_dir / TABLE_FILE
    output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    source_missing = sum(1 for row in rows if row.get("source_missing"))
    print(f"rows: {len(rows)}")
    print(f"source_missing: {source_missing}")
    print(f"json: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
