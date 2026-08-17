from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from contract_checks import SUPPORTED_CONTENT_BLOCK_TYPES, SUPPORTED_LAYOUTS


DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "deck_spec.schema.json"


def schema_bytes() -> bytes:
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "additionalProperties": True,
        "properties": {
            "pages": {
                "items": {
                    "additionalProperties": True,
                    "properties": {
                        "content": {
                            "items": {
                                "additionalProperties": True,
                                "properties": {
                                    "exhibit": {"type": "string"},
                                    "subtitle": {"type": "string"},
                                    "title": {"type": "string"},
                                    "type": {
                                        "enum": sorted(SUPPORTED_CONTENT_BLOCK_TYPES),
                                        "type": "string",
                                    }
                                },
                                "required": ["type"],
                                "type": "object",
                            },
                            "type": "array",
                        },
                        "layout": {"enum": sorted(SUPPORTED_LAYOUTS), "type": "string"},
                    },
                    "required": ["layout", "content"],
                    "type": "object",
                },
                "type": "array",
            }
        },
        "required": ["pages"],
        "title": "TickDeck deck spec",
        "type": "object",
    }
    return (json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def schema_hash() -> str:
    """Return the canonical generated schema digest for gate receipts."""

    return hashlib.sha256(schema_bytes()).hexdigest()


def summary(data: bytes) -> str:
    return (
        f"block_types={len(SUPPORTED_CONTENT_BLOCK_TYPES)} "
        f"layouts={len(SUPPORTED_LAYOUTS)} "
        f"sha256={hashlib.sha256(data).hexdigest()}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deck_spec.schema.json from contract SoT constants.")
    parser.add_argument("--check", action="store_true", help="fail if the output differs from the generated schema")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)

    generated = schema_bytes()
    if args.check:
        try:
            current = args.output.read_bytes()
        except FileNotFoundError:
            print(f"schema missing: {args.output}", file=sys.stderr)
            return 1
        if current != generated:
            print(f"schema out of date: {args.output}", file=sys.stderr)
            return 1
        print(f"schema matches SoT: {summary(generated)}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(generated)
    print(f"wrote {args.output}: {summary(generated)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
