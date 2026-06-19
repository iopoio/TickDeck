#!/usr/bin/env python3
"""Verify that TickDeck/v3 does not contain Sinya runtime collection code."""

from __future__ import annotations

import sys
from pathlib import Path


V3_ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_RUNTIME_MARKERS = [
    "OPENROUTER_API_KEY",
    "TAVILY_API_KEY",
    "https://openrouter.ai",
    "from openai import OpenAI",
    "client.chat.completions.create",
]


def scan(root: Path = V3_ROOT) -> list[tuple[Path, str]]:
    hits: list[tuple[Path, str]] = []
    for path in root.rglob("*.py"):
        if path.name == "verify_boundary.py":
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            if marker in text:
                hits.append((path.relative_to(root), marker))
    return hits


def main() -> int:
    hits = scan()
    if hits:
        print("Boundary check failed: forbidden runtime markers found.")
        for path, marker in hits:
            print(f"- {path}: {marker}")
        return 1
    print("Boundary check passed: no Sinya runtime collection code in v3 Python files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
