#!/usr/bin/env python3
"""Exact-match reader for TickDeck layout calibration records.

There is deliberately no default entry.  A caller must provide all eight runtime
dimensions and an exact measured record must exist for that combination.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CALIBRATION_DIR = Path(__file__).resolve().parent
HARNESS_DIR = CALIBRATION_DIR.parent
SCRIPT_DIR = HARNESS_DIR / "scripts"
RENDERER_PATH = SCRIPT_DIR / "render_deck.py"
FONT_DIR = HARNESS_DIR / "assets" / "fonts"
FONT_VERSION = "Pretendard v1.3.9"
FONT_FACES = (
    ("Thin", 100),
    ("ExtraLight", 200),
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("SemiBold", 600),
    ("ExtraBold", 700),
    ("ExtraBold", 800),
    ("Black", 900),
)

KEY_DIMENSIONS = (
    "renderer_struct_hash",
    "css_hash",
    "theme",
    "page_chrome",
    "layout",
    "width_class",
    "font_build",
    "browser_major",
)


class CalibrationError(RuntimeError):
    """Base error for unusable calibration data."""


class CalibrationFormatError(CalibrationError):
    """The calibration document or key is malformed."""


class UncalibratedCombinationError(CalibrationError):
    """No measured record exactly matches the requested eight dimensions."""


class CalibrationRuntimeKeyError(CalibrationError):
    """A local runtime key dimension could not be recomputed."""


def _renderer_module():
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))
    try:
        import render_deck
    except ImportError as exc:
        raise CalibrationRuntimeKeyError(f"cannot import renderer: {exc}") from exc
    return render_deck


def renderer_struct_hash(path: Path = RENDERER_PATH) -> str:
    """Hash renderer Python structure while keeping CSS as its own dimension."""

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise CalibrationRuntimeKeyError(f"cannot hash renderer structure: {exc}") from exc
    tree.body = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name != "_css"
    ]
    normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def css_hash(theme: str) -> str:
    renderer = _renderer_module()
    if theme not in renderer.PALETTES:
        raise CalibrationRuntimeKeyError(f"unknown renderer theme: {theme}")
    palette = renderer._resolve_palette({"theme": theme}, theme)
    stylesheet = renderer._css(palette)
    return hashlib.sha256(stylesheet.encode("utf-8")).hexdigest()


def font_build_hash(font_dir: Path = FONT_DIR) -> str:
    digest = hashlib.sha256()
    digest.update((FONT_VERSION + "\n").encode("utf-8"))
    for face, weight in FONT_FACES:
        path = font_dir / f"Pretendard-{face}.woff2"
        try:
            font_bytes = path.read_bytes()
        except OSError as exc:
            raise CalibrationRuntimeKeyError(f"cannot hash calibration font {path}: {exc}") from exc
        digest.update(f"{weight}:{path.name}:".encode("utf-8"))
        digest.update(font_bytes)
    return f"pretendard-v1.3.9-{digest.hexdigest()}"


def validate_key(key: Mapping[str, Any]) -> dict[str, str]:
    if not isinstance(key, Mapping):
        raise CalibrationFormatError("calibration key must be an object")
    actual = set(key)
    expected = set(KEY_DIMENSIONS)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise CalibrationFormatError(
            f"calibration key dimensions mismatch: missing={missing}, extra={extra}"
        )
    normalized: dict[str, str] = {}
    for dimension in KEY_DIMENSIONS:
        value = str(key[dimension]).strip()
        if not value:
            raise CalibrationFormatError(f"calibration key dimension is empty: {dimension}")
        normalized[dimension] = value
    return normalized


def resolve_entry(calibration: Mapping[str, Any], requested_key: Mapping[str, Any]) -> dict[str, Any]:
    """Return one exact measured record or fail closed.

    Invalid unrelated records also fail the document.  Silently ignoring a broken
    record would make lookup behavior depend on entry ordering.
    """

    if not isinstance(calibration, Mapping):
        raise CalibrationFormatError("calibration document must be an object")
    if type(calibration.get("schema_version")) is not int or calibration["schema_version"] != 1:
        raise CalibrationFormatError("unsupported calibration schema_version; expected 1")
    if tuple(calibration.get("key_dimensions", ())) != KEY_DIMENSIONS:
        raise CalibrationFormatError("calibration key_dimensions must list the canonical eight dimensions")
    entries = calibration.get("entries")
    if not isinstance(entries, list):
        raise CalibrationFormatError("calibration entries must be a list")

    requested = validate_key(requested_key)
    matches: list[dict[str, Any]] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise CalibrationFormatError(f"calibration entry {index} must be an object")
        entry_key = validate_key(entry.get("key", {}))
        if entry_key == requested:
            matches.append(entry)

    if len(matches) > 1:
        raise CalibrationFormatError("duplicate calibration entries for one exact key")
    if not matches:
        raise UncalibratedCombinationError(
            "no exact measured calibration; route this page to renderer measurement"
        )

    entry = matches[0]
    provenance = entry.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("status") != "measured":
        raise UncalibratedCombinationError(
            "matching calibration is not measured; route this page to renderer measurement"
        )
    if not isinstance(entry.get("values"), dict):
        raise CalibrationFormatError("matching calibration entry has no values object")
    return copy.deepcopy(entry)


__all__ = [
    "FONT_FACES",
    "FONT_VERSION",
    "KEY_DIMENSIONS",
    "CalibrationError",
    "CalibrationFormatError",
    "CalibrationRuntimeKeyError",
    "UncalibratedCombinationError",
    "css_hash",
    "font_build_hash",
    "renderer_struct_hash",
    "resolve_entry",
    "sha256_bytes",
    "sha256_file",
    "validate_key",
]
