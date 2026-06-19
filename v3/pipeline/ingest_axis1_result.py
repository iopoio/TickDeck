#!/usr/bin/env python3
"""Read a copied Sinya deepresearch result and print a compact summary.

This is an interface skeleton only. It does not call OpenRouter, Tavily, or any
external model. Collection stays in the Sinya sandbox; TickDeck/v3 consumes
result JSON files only.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


V3_ROOT = Path(__file__).resolve().parents[1]
AXIS1_RUNS = V3_ROOT / "axis1_research" / "runs"


def latest_result_path(runs_dir: Path = AXIS1_RUNS) -> Path:
    candidates = sorted(
        p for p in runs_dir.glob("*.json") if not p.name.endswith("_corpus.json")
    )
    if not candidates:
        raise FileNotFoundError(f"No axis1 result JSON found in {runs_dir}")
    return candidates[-1]


def load_result(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ["topic", "leader", "numeric_audit", "glossary", "fetch_stats"]
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError(f"Missing required keys in {path}: {', '.join(missing)}")
    return data


def summarize(data: dict[str, Any], source: Path) -> dict[str, Any]:
    leader = data.get("leader") or {}
    audit = data.get("numeric_audit") or {}
    glossary = data.get("glossary") or {}
    fetch_stats = data.get("fetch_stats") or {}
    return {
        "source": str(source),
        "topic": data.get("topic"),
        "ran_at": data.get("ran_at"),
        "leader_final_chars": len(leader.get("final") or ""),
        "docs": fetch_stats.get("docs"),
        "numeric_audit": {
            "checked": audit.get("checked"),
            "matched": audit.get("matched"),
            "suspected": audit.get("suspected"),
            "coverage": audit.get("coverage"),
        },
        "glossary": {
            "domain": glossary.get("domain"),
            "kept": glossary.get("kept"),
            "corpus_confirmed": glossary.get("corpus_confirmed"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "result",
        nargs="?",
        help="Path to an axis1 result JSON. Defaults to latest copied run.",
    )
    args = parser.parse_args()

    path = Path(args.result).expanduser() if args.result else latest_result_path()
    data = load_result(path)
    print(json.dumps(summarize(data, path), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
