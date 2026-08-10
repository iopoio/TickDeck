#!/usr/bin/env python3
"""Lightweight renderer regression checks.

Run directly with Python. No unittest/pytest dependency.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


ROOT = pathlib.Path(__file__).resolve().parents[3]
RENDER_DECK_PATH = ROOT / ".claude" / "skills" / "deck-harness" / "scripts" / "render_deck.py"
SPINE_CHECK_PATH = ROOT / ".claude" / "skills" / "deck-harness" / "scripts" / "spine_check.py"


def load_module(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


render_deck = load_module("render_deck_regression_target", RENDER_DECK_PATH)


REGISTRY = {
    "sources": {
        "src_a": {
            "publisher": "Source A",
            "title": "Quoted report 2026",
            "url": "https://example.com/a",
        },
        "src_b": {
            "publisher": "Source B",
            "title": "Unquoted report 2026",
            "url": "https://example.com/b",
        },
    },
    "metrics": {
        "pct_a": {"value": "38", "unit": "%", "source_ids": ["src_a"], "scope": "baseline share"},
        "pct_b": {"value": "79", "unit": "%", "source_ids": ["src_a"], "scope": "current share"},
        "count_a": {"value": "10", "unit": "건", "source_ids": ["src_a"], "scope": "baseline count"},
        "count_b": {"value": "20", "unit": "건", "source_ids": ["src_a"], "scope": "current count"},
        "growth_a": {"value": "120", "unit": "%", "source_ids": ["src_a"], "scope": "growth low"},
        "growth_b": {"value": "280", "unit": "%", "source_ids": ["src_a"], "scope": "growth high"},
    },
}


def page(content, **overrides):
    base = {
        "page_id": "p01",
        "short_title": "테스트 슬라이드",
        "layout": "statement",
        "allowed_source_ids": ["src_a"],
        "allowed_metric_ids": ["pct_a", "pct_b", "count_a", "count_b", "growth_a", "growth_b"],
        "content": content,
    }
    base.update(overrides)
    return base


def render_single(content, **overrides) -> str:
    return render_deck.render_deck({"pages": [page(content, **overrides)]}, REGISTRY, title="Regression")


def _dumbbell_geometry(first: float, second: float):
    series = [
        {"label": "리에종 드 로렌", "metric_id": "price_a", "value": f"{first:,.0f}원", "number": first},
        {"label": "설화수", "metric_id": "price_b", "value": f"{second:,.0f}원", "number": second},
    ]
    root = ET.fromstring(render_deck._svg_dumbbell(series, "", "", "#0E6B4F", "p17", {}))
    groups = {group.attrib["data-metric-id"]: group for group in root.findall("g")}

    def geometry(metric_id: str):
        group = groups[metric_id]
        circle = group.find("circle")
        texts = group.findall("text")
        value = next(text for text in texts if "visual-value" in text.attrib.get("class", ""))
        label = next(text for text in texts if text.attrib.get("class") == "visual-note")
        return {
            "circle_x": float(circle.attrib["cx"]),
            "circle_y": float(circle.attrib["cy"]),
            "value_y": float(value.attrib["y"]),
            "label_y": float(label.attrib["y"]),
        }

    return geometry("price_a"), geometry("price_b")


def test_dumbbell_separates_colliding_value_category_and_point_lanes():
    close_a, close_b = _dumbbell_geometry(139_000, 140_000)
    assert (close_a["circle_x"], close_b["circle_x"]) == (755.0, 760.0), "data x positions must stay truthful"
    assert close_a["circle_y"] != close_b["circle_y"], "near-coincident dots must both remain visible"
    assert close_a["value_y"] != close_b["value_y"], "close value labels must use separate lanes"
    assert close_a["label_y"] != close_b["label_y"], "close category labels must use separate lanes"

    equal_a, equal_b = _dumbbell_geometry(140_000, 140_000)
    assert equal_a["circle_x"] == equal_b["circle_x"], "equal values must keep the same x coordinate"
    assert equal_a["circle_y"] != equal_b["circle_y"], "equal-value dots must both remain visible"
    assert equal_a["value_y"] != equal_b["value_y"]
    assert equal_a["label_y"] != equal_b["label_y"]


def test_dumbbell_keeps_existing_geometry_when_labels_do_not_overlap():
    far_a, far_b = _dumbbell_geometry(70_000, 140_000)
    assert (far_a["circle_x"], far_b["circle_x"]) == (410.0, 760.0)
    assert (far_a["circle_y"], far_b["circle_y"]) == (110.0, 110.0)
    assert (far_a["value_y"], far_b["value_y"]) == (76.0, 76.0)
    assert (far_a["label_y"], far_b["label_y"]) == (158.0, 158.0)


def _rising_label_geometry(values: list[str], labels: list[str]):
    series = [
        {"label": label, "metric_id": f"column_{index}", "value": value, "number": 100}
        for index, (label, value) in enumerate(zip(labels, values))
    ]
    root = ET.fromstring(render_deck._svg_rising_columns(series, "", "", "#0E6B4F", "p01", {}))
    value_nodes = [
        node
        for node in root.iter("text")
        if node.attrib.get("class", "").startswith("visual-value")
    ]
    category_nodes = [node for node in root.iter("text") if node.attrib.get("class") == "visual-label"]
    return {
        "value_x": [float(node.attrib["x"]) for node in value_nodes],
        "value_y": [float(node.attrib["y"]) for node in value_nodes],
        "category_x": [float(node.attrib["x"]) for node in category_nodes],
        "category_y": [float(node.attrib["y"]) for node in category_nodes],
    }


def test_rising_columns_separates_only_colliding_value_and_category_labels():
    short = _rising_label_geometry(["100원"] * 5, ["A", "B", "C", "D", "E"])
    assert len(set(short["value_y"])) == 1
    assert len(set(short["category_y"])) == 1

    long = _rising_label_geometry(
        ["123,456,789,012,345원"] * 5,
        [f"아주 긴 브랜드 이름 {index}" for index in range(5)],
    )
    assert long["value_x"] == short["value_x"], "label lanes must not move column data coordinates"
    assert long["category_x"] == short["category_x"]
    assert len(set(long["value_y"])) > 1, "overlapping column values need separate lanes"
    assert len(set(long["category_y"])) > 1, "overlapping column categories need separate lanes"


def _quarterly_label_geometry(values: list[str], labels: list[str]):
    series = [
        {"label": label, "metric_id": f"quarter_{index}", "value": value, "number": 100}
        for index, (label, value) in enumerate(zip(labels, values))
    ]
    root = ET.fromstring(render_deck._svg_quarterly_bars(series, "", "", "#0E6B4F", "p01", {}))
    value_nodes = [node for node in root.iter("text") if node.attrib.get("class") == "quarter-value-onbar"]
    category_nodes = [node for node in root.iter("text") if node.attrib.get("class") == "visual-label"]
    return {
        "value_x": [float(node.attrib["x"]) for node in value_nodes],
        "value_y": [float(node.attrib["y"]) for node in value_nodes],
        "category_x": [float(node.attrib["x"]) for node in category_nodes],
        "category_y": [float(node.attrib["y"]) for node in category_nodes],
    }


def test_quarterly_bars_separates_only_colliding_value_and_category_labels():
    short = _quarterly_label_geometry(["100원"] * 8, list("ABCDEFGH"))
    assert len(set(short["value_y"])) == 1
    assert len(set(short["category_y"])) == 1

    long = _quarterly_label_geometry(
        ["123,456,789원"] * 8,
        [f"긴 분기 카테고리 {index}" for index in range(8)],
    )
    assert long["value_x"] == short["value_x"], "label lanes must not move quarter coordinates"
    assert long["category_x"] == short["category_x"]
    assert len(set(long["value_y"])) > 1, "overlapping quarterly values need separate lanes"
    assert len(set(long["category_y"])) > 1, "overlapping quarterly categories need separate lanes"


def test_multi_line_keeps_equal_values_and_separates_actual_text_collisions():
    series = []
    for role, count in (("highlight", 3), ("baseline", 4)):
        for index in range(count):
            series.append(
                {
                    "label": f"{role} 긴 카테고리 {index}",
                    "metric_id": f"{role}_{index}",
                    "value": "123,456,789원",
                    "number": 100,
                    "role": role,
                }
            )
    root = ET.fromstring(render_deck._svg_multi_line(series, "", "", "#0E6B4F", "p01", {}))
    value_nodes = [node for node in root.iter("text") if node.attrib.get("class") == "visual-value"]
    category_nodes = [node for node in root.iter("text") if node.attrib.get("class") == "visual-label"]

    assert len(value_nodes) == len(series), "equal values belong to distinct points and must not be deleted"
    interior = sorted(
        (float(node.attrib["x"]), float(node.attrib["y"]))
        for node in value_nodes
        if 500 <= float(node.attrib["x"]) <= 670
    )
    assert len(interior) == 2
    assert interior[0][1] != interior[1][1], "wide labels across old 88px buckets still collide"
    shared_categories = [
        float(node.attrib["y"])
        for node in category_nodes
        if float(node.attrib["x"]) in {80.0, 940.0}
    ]
    assert len(set(shared_categories)) > 1, "categories at shared coordinates need separate lanes"


def test_percent_bars_use_100_point_scale_and_counts_keep_max_scale():
    pct_html = render_single(
        [
            {
                "type": "viz",
                "chart": "gap_map",
                "title": "Percent scale",
                "series": [
                    {"label": "Before", "metric_id": "pct_a"},
                    {"label": "After", "metric_id": "pct_b", "role": "highlight"},
                ],
            }
        ]
    )
    assert 'width="288.8"' in pct_html, "38% must render as 38% of the 760px track"
    assert 'width="600.4"' in pct_html, "79% must render as 79% of the 760px track"

    count_html = render_single(
        [
            {
                "type": "viz",
                "chart": "gap_map",
                "title": "Count scale",
                "series": [
                    {"label": "Before", "metric_id": "count_a"},
                    {"label": "After", "metric_id": "count_b", "role": "highlight"},
                ],
            }
        ]
    )
    assert 'width="380.0"' in count_html, "10 of max 20 count items must render at half track"
    assert 'width="760.0"' in count_html, "max count item must fill the track"

    growth_html = render_single(
        [
            {
                "type": "viz",
                "chart": "gap_map",
                "title": "Growth scale",
                "series": [
                    {"label": "Before", "metric_id": "growth_a"},
                    {"label": "After", "metric_id": "growth_b", "role": "highlight"},
                ],
            }
        ]
    )
    assert 'width="325.7"' in growth_html, "120% growth must not overflow a 0-100 share track"
    assert 'width="760.0"' in growth_html, "largest growth percent uses max-relative scale"


def test_footnote_block_renders_above_footer():
    html = render_single(
        [
            {"type": "body", "text": "본문"},
            {"type": "footnote", "term": "에이전트 AI", "def": "스스로 일을 처리하는 AI"},
        ]
    )
    body = html.split("</style>", 1)[1]
    assert '<div class="footnote-row">' in html
    assert '<span class="footnote-item"><b>에이전트 AI</b> 스스로 일을 처리하는 AI</span>' in html
    assert body.index("footnote-row") < body.index("slide-foot")


def test_global_keep_all_is_in_body_css():
    html = render_single([{"type": "body", "text": "한국어 단어 쪼개짐 방지"}])
    assert "body {\n" in html
    assert "word-break: keep-all;" in html


def test_source_appendix_defaults_to_cited_sources_only():
    spec = {
        "pages": [
            page([{"type": "metric", "metric_id": "pct_a"}]),
            {
                "page_id": "appendix",
                "short_title": "출처",
                "layout": "source_appendix",
                "content": [{"type": "headline", "text": "출처"}],
            },
        ]
    }
    html = render_deck.render_deck(spec, REGISTRY, title="Appendix Regression")
    assert 'data-page-id="appendix"' in html
    assert "Source A" in html
    assert "Quoted report 2026" in html
    assert "Source B" not in html
    assert "Unquoted report 2026" not in html


def test_divider_supports_custom_fourth_part_label():
    spec = {
        "pages": [
            {
                "page_id": "d4",
                "short_title": "측정 — 운영 지표",
                "layout": "divider",
                "part_index": 4,
                "part_count": 4,
                "part_label": "측정",
                "content": [
                    {"type": "headline", "text": "측정 — 운영 지표"},
                    {"type": "summary", "text": "지표로 운영을 닫는다"},
                ],
            }
        ]
    }
    html = render_deck.render_deck(spec, REGISTRY, title="Divider Regression")
    assert "PART 4 · 측정" in html
    assert '<h2 class="divider-title">운영 지표</h2>' in html
    assert html.count('class="is-active"') == 1


def test_spine_check_outputs_skim_view():
    spec = {
        "pages": [
            {"page_id": "cover", "short_title": "표지", "layout": "cover", "content": []},
            {"page_id": "d1", "short_title": "증거", "layout": "divider", "content": []},
            {"page_id": "p01", "short_title": "로봇 — 성능에서 조율로", "layout": "statement", "content": []},
            {"page_id": "appendix", "short_title": "출처", "layout": "source_appendix", "content": []},
            {"page_id": "outro", "short_title": "감사합니다", "layout": "outro", "content": []},
        ]
    }
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(spec, handle, ensure_ascii=False)
        temp_path = handle.name
    try:
        result = subprocess.run(
            [sys.executable, str(SPINE_CHECK_PATH), temp_path],
            check=True,
            capture_output=True,
            text=True,
        )
    finally:
        pathlib.Path(temp_path).unlink(missing_ok=True)

    assert "제목 척추" in result.stdout
    assert " 2 ▸ 증거" in result.stdout
    assert " 3 · 로봇 — 성능에서 조율로" in result.stdout
    assert "본문 가리고 위 제목만 이어 읽어 논증이 서는지 판정" in result.stdout


def main() -> None:
    tests = [
        test_dumbbell_separates_colliding_value_category_and_point_lanes,
        test_dumbbell_keeps_existing_geometry_when_labels_do_not_overlap,
        test_rising_columns_separates_only_colliding_value_and_category_labels,
        test_quarterly_bars_separates_only_colliding_value_and_category_labels,
        test_multi_line_keeps_equal_values_and_separates_actual_text_collisions,
        test_percent_bars_use_100_point_scale_and_counts_keep_max_scale,
        test_footnote_block_renders_above_footer,
        test_global_keep_all_is_in_body_css,
        test_source_appendix_defaults_to_cited_sources_only,
        test_divider_supports_custom_fourth_part_label,
        test_spine_check_outputs_skim_view,
    ]
    for test in tests:
        test()
    print(f"PASS render_deck_regressions: {len(tests)} checks")


if __name__ == "__main__":
    main()
