#!/usr/bin/env python3
"""Sweep renderer probes and regenerate fail-closed layout calibration data."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


SCRIPT_DIR = Path(__file__).resolve().parent
HARNESS_DIR = SCRIPT_DIR.parent
CALIBRATION_DIR = HARNESS_DIR / "calibration"
DEFAULT_PROBE_DIR = CALIBRATION_DIR / "probe_specs"
DEFAULT_RAW_DIR = CALIBRATION_DIR / "raw"
DEFAULT_OUTPUT = CALIBRATION_DIR / "layout_calibration.json"
RENDERER_PATH = SCRIPT_DIR / "render_deck.py"
FONT_DIR = HARNESS_DIR / "assets" / "fonts"

if str(CALIBRATION_DIR) not in sys.path:
    sys.path.insert(0, str(CALIBRATION_DIR))

from predictor import (  # noqa: E402
    FONT_FACES,
    FONT_VERSION,
    KEY_DIMENSIONS,
    CalibrationRuntimeKeyError,
    css_hash,
    font_build_hash,
    renderer_struct_hash,
    validate_key,
)
from layout_budget import LayoutBudgetInputError, viz_signature  # noqa: E402
from pptx_export import find_chrome, insert_before_body, run_chrome  # noqa: E402
import render_deck  # noqa: E402


class CalibrationRunError(RuntimeError):
    pass


MEASUREMENT_SCRIPT = r"""
<script id="__layout_calibration_runner__">
(function(){
  document.documentElement.dataset.calibrationStage = 'runner-start';
  function px(value) {
    var number = Number.parseFloat(value);
    return Number.isFinite(number) ? Math.round(number * 1000) / 1000 : null;
  }
  function rect(el) {
    if (!el) return null;
    var r = el.getBoundingClientRect();
    return {x_px:px(r.x), y_px:px(r.y), width_px:px(r.width), height_px:px(r.height)};
  }
  Promise.resolve(window.__tickdeckCalibrationFontsReady).then(function(fontReady){
    document.documentElement.dataset.calibrationStage = 'font-loads-resolved';
    return document.fonts.ready.then(function(){ return fontReady; });
  }).then(function(fontReady){
    document.documentElement.dataset.calibrationStage = 'document-fonts-ready';
    // chrome-headless-shell --single-process has no display link in the managed
    // macOS sandbox, so animation frames never fire. A zero-delay task runs
    // under virtual time; the geometry reads below synchronously flush layout.
    return new Promise(function(resolve){ setTimeout(function(){ resolve(fontReady); }, 0); });
  }).then(function(fontReady){
    document.documentElement.dataset.calibrationStage = 'layout-task-ready';
    var pages = [];
    document.querySelectorAll('section.slide[data-page-id]').forEach(function(slide){
      var body = slide.querySelector(':scope > main.body');
      var bodyStyle = body ? getComputedStyle(body) : null;
      var visuals = [];
      slide.querySelectorAll('.visual-card').forEach(function(card){
        var cardStyle = getComputedStyle(card);
        var svg = card.querySelector('svg');
        visuals.push({
          card: rect(card),
          width_px: rect(card).width_px,
          svg: rect(svg),
          svg_height_px: svg ? rect(svg).height_px : null,
          margin_top_px: px(cardStyle.marginTop),
          margin_bottom_px: px(cardStyle.marginBottom),
          padding_top_px: px(cardStyle.paddingTop)
        });
      });
      pages.push({
        page_id: slide.dataset.pageId,
        slide: rect(slide),
        body: body ? {
          rect: rect(body),
          client_height_px: body.clientHeight,
          client_width_px: body.clientWidth,
          scroll_height_px: body.scrollHeight,
          scroll_width_px: body.scrollWidth,
          row_gap_px: px(bodyStyle.rowGap),
          padding_top_px: px(bodyStyle.paddingTop),
          padding_bottom_px: px(bodyStyle.paddingBottom)
        } : null,
        slide_head: rect(slide.querySelector(':scope > .slide-head')),
        title_band: rect(slide.querySelector(':scope > .title-band')),
        source_row: rect(slide.querySelector(':scope > .source-row')),
        footnote_row: rect(slide.querySelector(':scope > .footnote-row')),
        slide_foot: rect(slide.querySelector(':scope > .slide-foot')),
        visuals: visuals
      });
    });
    var payload = {
      font_ready: Boolean(fontReady),
      user_agent: navigator.userAgent,
      device_pixel_ratio: window.devicePixelRatio,
      viewport: {width_px: window.innerWidth, height_px: window.innerHeight},
      pages: pages
    };
    var out = document.createElement('script');
    out.type = 'application/json';
    out.id = '__layout_calibration__';
    out.textContent = JSON.stringify(payload);
    document.body.appendChild(out);
  }).catch(function(error){
    document.documentElement.dataset.calibrationStage = 'error';
    var out = document.createElement('script');
    out.type = 'application/json';
    out.id = '__layout_calibration__';
    out.textContent = JSON.stringify({error:String(error), font_ready:false, pages:[]});
    document.body.appendChild(out);
  });
})();
</script>
"""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate TickDeck layout calibration from HTML probes.")
    parser.add_argument("--probe-dir", type=Path, default=DEFAULT_PROBE_DIR)
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chrome", default=None, help="Explicit Chrome/Chromium executable.")
    return parser.parse_args(argv)


def parse_browser_major(version: str) -> str:
    match = re.search(
        r"(?:Google Chrome(?: for Testing)?|Chrome|Chromium|Microsoft Edge)\s+(\d+)\.",
        version,
    )
    if not match:
        raise CalibrationRunError(f"cannot parse browser major from: {version}")
    return match.group(1)


def chrome_runtime_flags(chrome: str) -> list[str]:
    if Path(chrome).name == "chrome-headless-shell":
        # Codex already supplies an outer macOS sandbox. Chromium's nested child
        # sandbox cannot register its Mach rendezvous service there, so the local
        # headless shell must stay in one process for file:// probe measurement.
        return ["--no-sandbox", "--single-process"]
    return []


def find_calibration_chrome(explicit: str | None = None) -> str:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        raise CalibrationRunError(f"explicit browser is not executable: {path}")

    cache_root = Path.home() / "Library" / "Caches" / "ms-playwright"
    headless_shells = sorted(
        cache_root.glob("chromium_headless_shell-*/chrome-headless-shell-mac-arm64/chrome-headless-shell"),
        reverse=True,
    )
    for path in headless_shells:
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
    try:
        return find_chrome()
    except SystemExit as exc:
        raise CalibrationRunError(str(exc)) from exc


def extract_measurement_payload(dom: str) -> dict[str, Any]:
    match = re.search(
        r"<script(?=[^>]*\bid=[\"']__layout_calibration__[\"'])[^>]*>(.*?)</script>",
        dom,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        raise CalibrationRunError("Chrome DOM has no __layout_calibration__ payload")
    try:
        payload = json.loads(html.unescape(match.group(1).strip()))
    except json.JSONDecodeError as exc:
        raise CalibrationRunError(f"invalid calibration JSON in Chrome DOM: {exc}") from exc
    if not isinstance(payload, dict):
        raise CalibrationRunError("calibration payload must be an object")
    if payload.get("error"):
        raise CalibrationRunError(f"browser measurement failed: {payload['error']}")
    return payload


def _ensure_pretendard_probe_theme(theme: str) -> None:
    if theme not in render_deck.PALETTES:
        raise CalibrationRunError(f"unknown renderer theme: {theme}")
    palette = render_deck._resolve_palette({"theme": theme}, theme)
    for slot in ("font_body", "font_head"):
        stack = str(palette.get(slot) or "").strip()
        if stack and not re.match(r'^\s*["\']?Pretendard["\']?(?:\s*,|$)', stack):
            raise CalibrationRunError(
                f"theme {theme} uses unsupported {slot} typography; "
                "refusing Pretendard-only calibration"
            )


def _font_injection(font_dir: Path = FONT_DIR) -> str:
    faces = []
    checks = []
    for face, weight in FONT_FACES:
        font_uri = (font_dir / f"Pretendard-{face}.woff2").resolve().as_uri()
        faces.append(
            "@font-face{font-family:'TickDeck Calibration Pretendard';font-style:normal;"
            f"font-weight:{weight};font-display:block;src:url('{font_uri}') format('woff2');}}"
        )
        checks.append(f"document.fonts.load('{weight} 16px \\\"TickDeck Calibration Pretendard\\\"',sentinel)")
    return (
        '<style id="tickdeck-calibration-font">'
        + "".join(faces)
        + ":root{--font-body:'TickDeck Calibration Pretendard',sans-serif;"
        "--font-head:'TickDeck Calibration Pretendard',sans-serif;"
        "--font-chart:'TickDeck Calibration Pretendard',sans-serif;}"
        "body{font-family:'TickDeck Calibration Pretendard',sans-serif!important;}"
        "</style><script>(function(){var sentinel='기초화장용 리에종 차지하는 몫이 줄었다 목차 관찰 가격을';"
        "window.__tickdeckCalibrationFontsReady=Promise.all(["
        + ",".join(checks)
        + "]).then(function(){return document.fonts.ready;}).then(function(){return [100,200,300,400,500,600,700,800,900].every(function(w){return document.fonts.check(w+' 16px \\\"TickDeck Calibration Pretendard\\\"',sentinel);});});})();</script>"
    )


def inject_measurement_html(rendered_html: str) -> str:
    if "</head>" not in rendered_html.lower():
        raise CalibrationRunError("rendered probe HTML has no </head>")
    head_end = rendered_html.lower().index("</head>")
    with_fonts = rendered_html[:head_end] + _font_injection() + rendered_html[head_end:]
    return insert_before_body(with_fonts, MEASUREMENT_SCRIPT)


def _page_map(measurement: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    pages = measurement.get("pages")
    if not isinstance(pages, list):
        raise CalibrationRunError("measurement pages must be a list")
    mapped: dict[str, Mapping[str, Any]] = {}
    for page in pages:
        if not isinstance(page, Mapping):
            raise CalibrationRunError("measurement page must be an object")
        page_id = str(page.get("page_id", "")).strip()
        if not page_id or page_id in mapped:
            raise CalibrationRunError(f"invalid or duplicate measured page_id: {page_id}")
        mapped[page_id] = page
    return mapped


def _positive_number(value: Any, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise CalibrationRunError(f"{label} must be numeric") from exc
    if number <= 0:
        raise CalibrationRunError(f"{label} must be positive")
    return number


def build_calibration_entry(
    probe_spec: Mapping[str, Any],
    measurement: Mapping[str, Any],
    *,
    renderer_struct_hash: str,
    css_hash: str,
    font_build: str,
    browser_major: str,
    raw_path: str,
    measured_at: str,
) -> dict[str, Any]:
    if measurement.get("font_ready") is not True:
        raise CalibrationRunError("vendored Pretendard fonts were not ready; refusing calibration")
    pages = probe_spec.get("pages")
    if not isinstance(pages, list) or not pages:
        raise CalibrationRunError("probe spec requires pages")
    layouts = {
        str(page.get("layout") or "statement").strip()
        for page in pages
        if isinstance(page, Mapping)
    }
    if len(layouts) != 1:
        raise CalibrationRunError("one probe spec must contain exactly one layout dimension")
    layout = next(iter(layouts))
    theme = str(probe_spec.get("theme") or "editorial").strip()
    _ensure_pretendard_probe_theme(theme)
    meta = probe_spec.get("meta") if isinstance(probe_spec.get("meta"), Mapping) else {}
    page_chrome = str(meta.get("page_chrome") or "none").strip()
    probe_meta = meta.get("calibration_probe") if isinstance(meta.get("calibration_probe"), Mapping) else {}
    capacity_page_id = str(probe_meta.get("capacity_page_id", "")).strip()
    if not capacity_page_id:
        raise CalibrationRunError("probe meta.calibration_probe.capacity_page_id is required")

    measured_pages = _page_map(measurement)
    capacity_page = measured_pages.get(capacity_page_id)
    if not capacity_page:
        raise CalibrationRunError(f"capacity page was not measured: {capacity_page_id}")
    body = capacity_page.get("body") if isinstance(capacity_page.get("body"), Mapping) else {}
    capacity_px = _positive_number(body.get("client_height_px"), "capacity body client_height_px")

    widths: set[int] = set()
    viz_heights: dict[str, float] = {}
    for page in pages:
        if not isinstance(page, Mapping):
            raise CalibrationRunError("probe page must be an object")
        page_id = str(page.get("page_id", "")).strip()
        measured_page = measured_pages.get(page_id)
        if not measured_page:
            raise CalibrationRunError(f"probe page was not measured: {page_id}")
        blocks = [
            block
            for block in page.get("content", [])
            if isinstance(block, Mapping) and block.get("type") == "viz"
        ]
        visuals = measured_page.get("visuals")
        if not isinstance(visuals, list) or len(visuals) != len(blocks):
            raise CalibrationRunError(f"{page_id}: measured visual count does not match probe viz blocks")
        for block, visual in zip(blocks, visuals):
            if not isinstance(visual, Mapping):
                raise CalibrationRunError(f"{page_id}: visual measurement must be an object")
            width = _positive_number(visual.get("width_px"), f"{page_id} visual width_px")
            card = visual.get("card") if isinstance(visual.get("card"), Mapping) else {}
            card_height = _positive_number(
                card.get("height_px"),
                f"{page_id} visual card height_px",
            )
            widths.add(round(width))
            try:
                signature = viz_signature(block)
            except LayoutBudgetInputError as exc:
                raise CalibrationRunError(str(exc)) from exc
            if signature in viz_heights and abs(viz_heights[signature] - card_height) > 0.01:
                raise CalibrationRunError(f"conflicting measurements for viz signature: {signature}")
            viz_heights[signature] = card_height
    if len(widths) != 1:
        raise CalibrationRunError(f"probe must measure exactly one viz width class, got {sorted(widths)}")

    key = validate_key(
        {
            "renderer_struct_hash": renderer_struct_hash,
            "css_hash": css_hash,
            "theme": theme,
            "page_chrome": page_chrome,
            "layout": layout,
            "width_class": f"{next(iter(widths))}px",
            "font_build": font_build,
            "browser_major": browser_major,
        }
    )
    return {
        "key": key,
        "values": {
            "capacity_px": capacity_px,
            "viz_heights_px": dict(sorted(viz_heights.items())),
            "measurement_basis": {
                "capacity_page_id": capacity_page_id,
                "viz_width_px": next(iter(widths)),
                "viz_height": "visual-card border-box; CSS margins excluded",
            },
        },
        "provenance": {
            "status": "measured",
            "measured_at": measured_at,
            "raw_path": raw_path,
        },
    }


def _json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CalibrationRunError(f"cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CalibrationRunError(f"JSON root must be an object: {path}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _atomic_write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, prefix=f".{path.name}.")
    temp_path = Path(handle.name)
    try:
        with handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def _relative(path: Path, root: Path = CALIBRATION_DIR) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def _run_probe(
    spec_path: Path,
    registry_path: Path,
    run_dir: Path,
    chrome: str,
    browser_version: str,
    renderer_hash: str,
    font_build: str,
    measured_at: str,
) -> dict[str, Any]:
    probe_name = spec_path.name.removesuffix(".spec.json")
    rendered_path = run_dir / f"{probe_name}.html"
    measured_html_path = run_dir / f"{probe_name}.measurement.html"
    dom_path = run_dir / f"{probe_name}.dom.html"
    raw_path = run_dir / f"{probe_name}.measurement.json"
    spec = _json(spec_path)
    theme = str(spec.get("theme") or "editorial").strip()
    _ensure_pretendard_probe_theme(theme)

    render_command = [
        sys.executable,
        str(RENDERER_PATH),
        str(spec_path),
        str(registry_path),
        "-o",
        str(rendered_path),
        "--html-only",
    ]
    rendered = subprocess.run(render_command, capture_output=True, text=True)
    if rendered.returncode:
        raise CalibrationRunError(
            f"renderer probe failed ({rendered.returncode}): {(rendered.stderr or rendered.stdout).strip()}"
        )
    measured_html_path.write_text(
        inject_measurement_html(rendered_path.read_text(encoding="utf-8")),
        encoding="utf-8",
    )
    chrome_args = [
        "--headless=new",
        *chrome_runtime_flags(chrome),
        "--disable-gpu",
        "--allow-file-access-from-files",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=8000",
        "--dump-dom",
        measured_html_path.resolve().as_uri(),
    ]
    try:
        chrome_result = run_chrome(chrome, chrome_args, "LAYOUT_CALIBRATION")
    except SystemExit as exc:
        raise CalibrationRunError(str(exc)) from exc
    dom_path.write_text(chrome_result.stdout, encoding="utf-8")
    measurement = extract_measurement_payload(chrome_result.stdout)
    entry = build_calibration_entry(
        spec,
        measurement,
        renderer_struct_hash=renderer_hash,
        css_hash=css_hash(theme),
        font_build=font_build,
        browser_major=parse_browser_major(browser_version),
        raw_path=_relative(raw_path),
        measured_at=measured_at,
    )
    entry["provenance"].update(
        {
            "probe_spec": _relative(spec_path),
            "probe_registry": _relative(registry_path),
            "rendered_html": _relative(rendered_path),
            "measurement_html": _relative(measured_html_path),
            "chrome_dom": _relative(dom_path),
        }
    )
    raw_record = {
        "status": "measured",
        "measured_at": measured_at,
        "probe_spec": _relative(spec_path),
        "probe_registry": _relative(registry_path),
        "renderer_command": render_command,
        "renderer_stdout": rendered.stdout,
        "renderer_stderr": rendered.stderr,
        "chrome_command": [chrome, *chrome_args],
        "chrome_version": browser_version,
        "key": entry["key"],
        "measurement": measurement,
    }
    _write_json(raw_path, raw_record)
    return entry


def run_calibration(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    probe_paths = sorted(args.probe_dir.glob("*.spec.json"))
    if not probe_paths:
        raise CalibrationRunError(f"no probe specs found: {args.probe_dir}")
    chrome = find_calibration_chrome(args.chrome)
    version_result = subprocess.run([chrome, "--version"], capture_output=True, text=True)
    if version_result.returncode:
        raise CalibrationRunError(f"browser version command failed: {version_result.stderr.strip()}")
    browser_version = version_result.stdout.strip()
    parse_browser_major(browser_version)

    now = datetime.now(ZoneInfo("Asia/Seoul"))
    measured_at = now.isoformat(timespec="seconds")
    run_id = now.strftime("%Y%m%dT%H%M%S%z")
    run_dir = args.raw_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    renderer_hash = renderer_struct_hash()
    font_build = font_build_hash()

    entries: list[dict[str, Any]] = []
    for spec_path in probe_paths:
        registry_path = spec_path.with_name(spec_path.name.removesuffix(".spec.json") + ".registry.json")
        if not registry_path.is_file():
            raise CalibrationRunError(f"probe registry missing: {registry_path}")
        entries.append(
            _run_probe(
                spec_path,
                registry_path,
                run_dir,
                chrome,
                browser_version,
                renderer_hash,
                font_build,
                measured_at,
            )
        )

    key_tuples = [tuple(entry["key"][dimension] for dimension in KEY_DIMENSIONS) for entry in entries]
    if len(key_tuples) != len(set(key_tuples)):
        raise CalibrationRunError("probe sweep produced duplicate eight-dimension keys")
    document = {
        "schema_version": 1,
        "key_dimensions": list(KEY_DIMENSIONS),
        "generated_at": measured_at,
        "hash_methods": {
            "renderer_struct_hash": "sha256(ast.dump(render_deck.py excluding _css))",
            "css_hash": "sha256(render_deck._css(resolved_theme))",
            "font_build": "sha256(vendored Pretendard v1.3.9 files plus PDF weight map)",
            "width_class": "rounded measured .visual-card width in px; canonical naming otherwise unresolved",
        },
        "entries": entries,
        "runs": [
            {
                "run_id": run_id,
                "status": "measured",
                "measured_at": measured_at,
                "probe_count": len(entries),
                "raw_dir": _relative(run_dir),
                "chrome_version": browser_version,
            }
        ],
    }
    _atomic_write_json(args.output, document)
    return document, run_dir


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        document, run_dir = run_calibration(args)
    except (CalibrationRunError, CalibrationRuntimeKeyError, OSError) as exc:
        print(f"CALIBRATION_ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"CALIBRATION_OK entries={len(document['entries'])} "
        f"raw={run_dir} output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
