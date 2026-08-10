#!/usr/bin/env python3
"""PDF page ink coverage check for TickDeck visual QA."""

from __future__ import annotations

import argparse
import json
import re
import statistics
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


LUMINANCE_DIFF_THRESHOLD = 0.12

# 간지·표지 등은 잉크가 적어도 정상이라 본문 판정에서 뺀다(게이트 명세 그대로).
NON_BODY_LAYOUTS = frozenset({"divider", "cover", "closing", "outro", "index", "source_appendix"})

# 2026-08-10 실측 (40dpi, 아래 luminance 알고리즘, 같은 폴더 06_deck_spec.json layout 기준 본문 페이지만):
#   정상 덱(20260809_liaison_de_loren_market, 차트 있음) — 본문 20장, 중앙값 17.54%, 2.5% 미만 0장(0%)
#   사고 덱(20260810_liaison_proposals, 41장 중 40장 저밀도로 납품됐던 그 덱) — 본문 32장, 중앙값 3.28%,
#     2.5% 미만 7장(21.9%). 중앙값 하한(4%)만으로도 이 사고를 잡는다.
#   참고 덱(20260810_brand_strategy) — 본문 18장, 중앙값 4.80%, 2.5% 미만 0장 → 통과(경계 근접)
# 정상 덱은 큰 여유로 통과하고 사고 덱은 중앙값 기준에서 걸림을 확인했다. 두 임계는 OR로 결합
# (분포 기준 + 중앙값 기준 중 하나만 걸려도 FAIL) — 명세(review_fable.md) 원안 값을 그대로 확정.
INK_BODY_MIN_RATIO = 0.025  # 본문 페이지 "저밀도" 판정선 (2.5%)
INK_SPARSE_PAGE_SHARE_MAX = 0.30  # 저밀도 본문 페이지 비율 상한 (30% 초과 시 FAIL)
INK_MEDIAN_MIN_RATIO = 0.04  # 본문 페이지 잉크 중앙값 하한 (4% 미만 FAIL)


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


def _page_layouts(pdf: Path) -> list[str] | None:
    """같은 폴더 06_deck_spec.json의 page별 layout. 없거나 못 읽으면 None(전 페이지 본문 취급)."""
    spec_path = pdf.parent / "06_deck_spec.json"
    if not spec_path.exists():
        return None
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    pages = spec.get("pages")
    if not isinstance(pages, list):
        return None
    return [str(page.get("layout", "statement")) if isinstance(page, dict) else "statement" for page in pages]


def check_pdf(pdf: Path) -> tuple[list[str], bool]:
    """Returns (output lines, is_fail). is_fail=True만 파이프라인 실패(exit 2) 대상."""
    if not pdf.exists():
        return [f"INK_CHECK_SKIP: PDF 없음: {pdf}"], False
    with tempfile.TemporaryDirectory() as td:
        prefix = str(Path(td) / "page")
        result = subprocess.run(
            ["pdftoppm", "-r", "40", "-png", str(pdf), prefix],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            reason = result.stderr.strip() or result.stdout.strip() or "pdftoppm 실패"
            return [f"INK_CHECK_SKIP: {reason}"], False
        pages = sorted(Path(td).glob("page-*.png"), key=page_sort_key)
        if not pages:
            return [f"INK_CHECK_SKIP: PDF 페이지 이미지 없음: {pdf}"], False
        ratios = [(idx, ink_ratio(path)) for idx, path in enumerate(pages, start=1)]

    layouts = _page_layouts(pdf)
    body_ratios: list[tuple[int, float]] = []
    for idx, ratio in ratios:
        layout = layouts[idx - 1] if layouts is not None and idx - 1 < len(layouts) else None
        is_body = layouts is None or layout not in NON_BODY_LAYOUTS
        if is_body:
            body_ratios.append((idx, ratio))

    if not body_ratios:
        return [f"INK_CHECK_SKIP: 본문 페이지 없음(전부 {'/'.join(sorted(NON_BODY_LAYOUTS))})"], False

    sparse_pages = [(idx, ratio) for idx, ratio in body_ratios if ratio < INK_BODY_MIN_RATIO]
    sparse_share = len(sparse_pages) / len(body_ratios)
    median_ink = statistics.median(ratio for _, ratio in body_ratios)

    fail_reasons = []
    if sparse_share > INK_SPARSE_PAGE_SHARE_MAX:
        fail_reasons.append(
            f"본문 {len(body_ratios)}장 중 {len(sparse_pages)}장({sparse_share * 100:.1f}%)이 잉크 "
            f"{INK_BODY_MIN_RATIO * 100:.1f}% 미만 (상한 {INK_SPARSE_PAGE_SHARE_MAX * 100:.0f}%)"
        )
    if median_ink < INK_MEDIAN_MIN_RATIO:
        fail_reasons.append(
            f"본문 잉크 중앙값 {median_ink * 100:.2f}% (하한 {INK_MEDIAN_MIN_RATIO * 100:.1f}%)"
        )

    if fail_reasons:
        lines = [f"INK_SPARSE_FAIL: {' · '.join(fail_reasons)}"]
        if sparse_pages:
            page_list = ", ".join(f"p{idx}({ratio * 100:.2f}%)" for idx, ratio in sparse_pages)
            lines.append(f"INK_SPARSE_PAGES: {page_list}")
        return lines, True

    min_idx, min_ratio = min(body_ratios, key=lambda item: item[1])
    return (
        [
            f"INK_OK: median {median_ink * 100:.2f}% · min p{min_idx} {min_ratio * 100:.2f}% "
            f"· {len(body_ratios)} body pages"
        ],
        False,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Detect low ink-density decks by body-page distribution.")
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()
    try:
        lines, is_fail = check_pdf(args.pdf)
        for line in lines:
            print(line)
    except Exception as exc:  # noqa: BLE001 - unexpected errors must not silently pass as FAIL either.
        print(f"INK_CHECK_SKIP: {exc}")
        return 0
    return 2 if is_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
