#!/usr/bin/env python3
"""PDF page ink coverage check for TickDeck visual QA."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:
    venv_py = Path(__file__).parent / ".venv" / "bin" / "python"
    if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
        raise SystemExit(subprocess.run([str(venv_py), *sys.argv]).returncode)
    print("INK_CHECK_SKIP: pillow 없음 — scripts/.venv 생성 필요: uv venv && uv pip install pillow")
    raise SystemExit(0)


# 미니멀 클로징("감사합니다" 1행)이 실측 1.8%라 3%는 오탐 — 깨짐/공백 페이지는 0~0.5% 수준
INK_THRESHOLD = 0.01
LUMINANCE_DIFF_THRESHOLD = 0.12


def page_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"-(\d+)\.png$", path.name)
    return (int(match.group(1)) if match else 0, path.name)


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255


def ink_ratio(image_path: Path) -> float:
    with Image.open(image_path) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        colors = rgb.getcolors(maxcolors=width * height)
        if not colors:
            raise RuntimeError(f"배경색 산출 실패: {image_path.name}")
        _, background = max(colors, key=lambda item: item[0])
        bg_lum = luminance(background)
        data = rgb.tobytes()
    ink_pixels = 0
    for i in range(0, len(data), 3):
        pixel = (data[i], data[i + 1], data[i + 2])
        if abs(luminance(pixel) - bg_lum) >= LUMINANCE_DIFF_THRESHOLD:
            ink_pixels += 1
    return ink_pixels / (width * height)


def check_pdf(pdf: Path) -> list[str]:
    if not pdf.exists():
        return [f"INK_CHECK_SKIP: PDF 없음: {pdf}"]
    with tempfile.TemporaryDirectory() as td:
        prefix = str(Path(td) / "page")
        result = subprocess.run(
            ["pdftoppm", "-r", "40", "-png", str(pdf), prefix],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            reason = result.stderr.strip() or result.stdout.strip() or "pdftoppm 실패"
            return [f"INK_CHECK_SKIP: {reason}"]
        pages = sorted(Path(td).glob("page-*.png"), key=page_sort_key)
        if not pages:
            return [f"INK_CHECK_SKIP: PDF 페이지 이미지 없음: {pdf}"]

        ratios = [(idx, ink_ratio(path)) for idx, path in enumerate(pages, start=1)]
    empty = [
        f"INK_EMPTY: p{idx} ({ratio * 100:.2f}%)"
        for idx, ratio in ratios
        if ratio < INK_THRESHOLD
    ]
    if empty:
        return empty
    min_idx, min_ratio = min(ratios, key=lambda item: item[1])
    return [f"INK_OK: min p{min_idx} {min_ratio * 100:.2f}%"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect nearly blank PDF pages by ink coverage.")
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    try:
        for line in check_pdf(args.pdf):
            print(line)
    except Exception as exc:  # noqa: BLE001 - QA check must never block capture.
        print(f"INK_CHECK_SKIP: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
