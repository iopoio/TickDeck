#!/usr/bin/env python3
"""Focused checks for conservative native rectangle promotion."""

import json
import re
import subprocess

from pptx_export import LAYOUT_DUMP_SCRIPT, rect_promotion_rejection_reason


def candidate(**overrides):
    value = {
        "background_color": "rgb(25, 30, 43)",
        "background_alpha": 1.0,
        "background_image": "none",
        "transform": "none",
        "area_ratio": 0.01,
        "clipped_child": False,
        "filter": "none",
        "backdrop_filter": "none",
        "box_shadow": "none",
    }
    value.update(overrides)
    return value


def color_alpha(value):
    px_function = re.search(r"  function px\(value, fallback\) \{.*?\n  \}", LAYOUT_DUMP_SCRIPT, re.DOTALL)
    function = re.search(r"  function colorAlpha\(value\) \{.*?\n  \}", LAYOUT_DUMP_SCRIPT, re.DOTALL)
    assert px_function and function
    script = f"{px_function.group(0)}\n{function.group(0)}\nconsole.log(colorAlpha({json.dumps(value)}));"
    return float(subprocess.check_output(["node", "-e", script], text=True).strip())


assert rect_promotion_rejection_reason(candidate()) is None
assert rect_promotion_rejection_reason(candidate(background_image="linear-gradient(red, blue)")) == "background_image"
assert rect_promotion_rejection_reason(candidate(background_alpha=0.5)) == "background_alpha"
assert rect_promotion_rejection_reason(candidate(area_ratio=0.0014)) == "area_too_small"
assert rect_promotion_rejection_reason(candidate(
    background_alpha=color_alpha("color(srgb 0.93 0.945 0.984 / 0.03)"),
)) == "background_alpha"
assert rect_promotion_rejection_reason(candidate(
    background_alpha=color_alpha("color(srgb 0.43 0.545 1 / 10%)"),
)) == "background_alpha"

print("PASS: 6 rect promotion cases")

# 8/16 추가 — 구워진 글자를 품은 사각형은 승격 금지 (p11 표 줄무늬 행이 통째로 덮인 실측)
assert rect_promotion_rejection_reason(candidate(baked_text_child=True)) == "baked_text_child"
assert rect_promotion_rejection_reason(candidate(baked_text_child=False)) is None
print("PASS: baked_text_child cases")
