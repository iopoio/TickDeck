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
