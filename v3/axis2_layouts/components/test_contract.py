import importlib.util
import json
import math
import re
import tempfile
import unittest
from html import unescape
from pathlib import Path


COMPONENT_ROOT = Path(__file__).resolve().parent
EXPECTED_COMPONENTS = {
    "big_percent",
    "donut_gauge",
    "bar_chart",
    "card_grid",
    "funnel",
    "timeline",
    "matrix_2x2",
    "comparison_vs",
    "dashboard",
    "map_data",
    "process",
}

DEBUG_TOKEN_RE = re.compile(
    r"PNMPSYM|PRPT925|KRY4PCK|Y9L99BJ|XXDRKDW|FZPUS97|creative_ZUCHJ3X|"
    r"9QWELHB|KTFH6XF|3RR4Y5L|Z5584UT|6NMN2TA|TMF9QZK|DA2MZMD"
)


DEMO_DATA = {
    "big_percent": {
        "title": "Market readiness",
        "value": 73,
        "unit": "%",
        "caption": "Qualified buyers prefer visual proof.",
        "source_map": {"value": "demo:axis2:big_percent"},
    },
    "donut_gauge": {
        "title": "Trust conversion",
        "value": 82,
        "unit": "%",
        "caption": "Share of prospects reaching proof stage.",
        "source_map": {"value": "demo:axis2:donut_gauge"},
    },
    "bar_chart": {
        "title": "Segment lift",
        "items": [
            {"label": "Awareness", "value": 42},
            {"label": "Intent", "value": 58},
            {"label": "Trial", "value": 71},
            {"label": "Renewal", "value": 86},
        ],
        "unit": "%",
        "source_map": {"items": "demo:axis2:bar_chart"},
    },
    "card_grid": {
        "title": "Growth levers",
        "cards": [
            {"label": "Signal", "value": 64, "caption": "Intent data"},
            {"label": "Proof", "value": 78, "caption": "Case evidence"},
            {"label": "Motion", "value": 55, "caption": "Sales rhythm"},
        ],
        "unit": "%",
        "source_map": {"cards": "demo:axis2:card_grid"},
    },
    "funnel": {
        "title": "Lead funnel",
        "stages": [
            {"label": "Reach", "value": 92, "caption": "Audience opened"},
            {"label": "Engage", "value": 71, "caption": "Clicked proof"},
            {"label": "Qualify", "value": 48, "caption": "Sales ready"},
            {"label": "Close", "value": 24, "caption": "Won deals"},
        ],
        "unit": "%",
        "source_map": {"stages": "demo:axis2:funnel"},
    },
    "timeline": {
        "title": "Launch timeline",
        "events": [
            {"label": "Discover", "date": "Q1", "caption": "Signal scan"},
            {"label": "Prototype", "date": "Q2", "caption": "Visual proof"},
            {"label": "Pilot", "date": "Q3", "caption": "Live account"},
            {"label": "Scale", "date": "Q4", "caption": "Repeatable motion"},
        ],
        "source_map": {"events": "demo:axis2:timeline"},
    },
    "matrix_2x2": {
        "title": "Positioning matrix",
        "x_axis": "Execution effort",
        "y_axis": "Market impact",
        "points": [
            {"label": "SEO", "x": 28, "y": 68},
            {"label": "Events", "x": 70, "y": 42},
            {"label": "Partner", "x": 58, "y": 82},
        ],
        "source_map": {"points": "demo:axis2:matrix_2x2"},
    },
    "comparison_vs": {
        "title": "Old motion vs new motion",
        "left": {"label": "Manual", "value": 42, "caption": "Slow handoff"},
        "right": {"label": "Automated", "value": 84, "caption": "Proof at scale"},
        "unit": "%",
        "source_map": {"left": "demo:axis2:comparison_vs:left", "right": "demo:axis2:comparison_vs:right"},
    },
    "dashboard": {
        "title": "Revenue dashboard",
        "kpis": [
            {"label": "Pipeline", "value": 6.2, "unit": "M"},
            {"label": "Win rate", "value": 28, "unit": "%"},
            {"label": "Cycle", "value": 31, "unit": "d"},
        ],
        "series": [32, 45, 38, 62, 58, 74, 69],
        "bars": [24, 38, 52, 44, 68],
        "source_map": {"kpis": "demo:axis2:dashboard"},
    },
    "map_data": {
        "title": "Regional demand",
        "regions": [
            {"label": "West", "value": 52, "x": 330, "y": 310},
            {"label": "Central", "value": 41, "x": 610, "y": 370},
            {"label": "East", "value": 64, "x": 860, "y": 275},
        ],
        "unit": "%",
        "source_map": {"regions": "demo:axis2:map_data"},
    },
    "process": {
        "title": "Proof process",
        "steps": [
            {"label": "Ideation", "value": 50, "caption": "Find claim"},
            {"label": "Develop", "value": 75, "caption": "Build evidence"},
            {"label": "Expand", "value": 60, "caption": "Package story"},
            {"label": "Delegate", "value": 65, "caption": "Run motion"},
        ],
        "unit": "%",
        "source_map": {"steps": "demo:axis2:process"},
    },
}


def load_renderer():
    path = COMPONENT_ROOT / "renderer.py"
    if not path.exists():
        raise AssertionError(f"renderer.py missing: {path}")
    spec = importlib.util.spec_from_file_location("axis2_components_renderer", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ComponentContractTests(unittest.TestCase):
    @staticmethod
    def _estimated_label_width(text: str, font_size: float) -> float:
        widths = {
            "digit": 0.58,
            "dot": 0.28,
            "percent": 0.72,
            "space": 0.32,
            "ascii": 0.56,
            "wide": 0.95,
        }
        units = 0.0
        for char in unescape(text):
            if char.isdigit():
                units += widths["digit"]
            elif char in ".,:":
                units += widths["dot"]
            elif char == "%":
                units += widths["percent"]
            elif char.isspace():
                units += widths["space"]
            elif char.isascii():
                units += widths["ascii"]
            else:
                units += widths["wide"]
        return units * font_size

    @staticmethod
    def _svg_attrs(attrs: str) -> dict[str, str]:
        return dict(re.findall(r'([a-zA-Z-]+)="([^"]*)"', attrs))

    def test_phase0_rejects_missing_or_unknown_component_without_fallback(self):
        renderer = load_renderer()

        self.assertEqual(set(renderer.COMPONENTS), EXPECTED_COMPONENTS)
        with self.assertRaisesRegex(ValueError, "fallback"):
            renderer.render_component(None, {"title": "plain text only"})
        with self.assertRaisesRegex(ValueError, "fallback"):
            renderer.render_component("plain_text", {"title": "plain text only"})

    def test_each_component_renders_real_svg_geometry_not_text_fallback(self):
        renderer = load_renderer()
        geometry_expectations = {
            "big_percent": ("data-role=\"progress-fill\"", 1),
            "donut_gauge": ("<path data-role=\"donut-arc\"", 1),
            "bar_chart": ("data-role=\"bar\"", 4),
            "card_grid": ("data-role=\"card-spark\"", 3),
            "funnel": ("data-role=\"funnel-segment\"", 4),
            "timeline": ("data-role=\"timeline-node\"", 4),
            "matrix_2x2": ("data-role=\"matrix-quadrant\"", 4),
            "comparison_vs": ("data-role=\"vs-panel\"", 2),
            "dashboard": ("data-role=\"dashboard-card\"", 3),
            "map_data": ("data-role=\"map-bubble\"", 3),
            "process": ("data-role=\"process-step\"", 4),
        }

        for name, data in DEMO_DATA.items():
            with self.subTest(component=name):
                rendered = renderer.render_component(name, data)
                token, count = geometry_expectations[name]
                self.assertIn("<svg", rendered.svg)
                self.assertGreaterEqual(rendered.svg.count(token), count)
                self.assertNotIn("fallback", rendered.html.lower())
                self.assertEqual(rendered.metadata["component"], name)
                self.assertTrue(rendered.metadata["source_map"])

    def test_metadata_records_public_design_references_without_debug_tokens(self):
        renderer = load_renderer()

        expected_refs = {
            "big_percent": {"Big number emphasis", "Financial gauge structure"},
            "donut_gauge": {"Circular progress gauge", "Clean sales palette"},
            "bar_chart": {"Rising percent bars", "Financial chart discipline"},
            "card_grid": {"Metric card grid", "Big-number metrics"},
            "funnel": {"Layered funnel geometry", "Pyramid conversion logic"},
            "timeline": {"Alternating timeline cards", "Roadmap clarity"},
            "matrix_2x2": {"Cost-impact positioning"},
            "comparison_vs": {"Centered VS comparison", "Two-color contrast"},
            "dashboard": {"Multi-chart dashboard"},
            "map_data": {"Map card layout", "Regional data tone"},
            "process": {"Arrow sequence", "Step structure"},
        }
        for name, refs in expected_refs.items():
            with self.subTest(component=name):
                rendered = renderer.render_component(name, DEMO_DATA[name])
                self.assertTrue(refs.issubset(set(rendered.metadata["design_refs"])))
                self.assertNotIn("envato_refs", rendered.metadata)
                self.assertIsNone(DEBUG_TOKEN_RE.search(rendered.svg))
                self.assertIsNone(DEBUG_TOKEN_RE.search(rendered.html))
                self.assertIsNone(DEBUG_TOKEN_RE.search(json.dumps(rendered.metadata, ensure_ascii=False)))

    def test_render_component_accepts_theme_palette_override(self):
        renderer = load_renderer()

        rendered = renderer.render_component(
            "bar_chart",
            DEMO_DATA["bar_chart"],
            theme={
                "primary": "#123456",
                "secondary": "#abcdef",
                "accent": "#fedcba",
                "ink": "#101820",
            },
        )

        self.assertIn("#123456", rendered.svg)
        self.assertIn("#abcdef", rendered.svg)
        self.assertIn("#fedcba", rendered.svg)
        self.assertIn("#101820", rendered.svg)

    def test_demo_html_and_png_artifacts_are_written(self):
        renderer = load_renderer()
        with tempfile.TemporaryDirectory() as tmp:
            artifact = renderer.write_demo(Path(tmp))

            self.assertTrue(artifact.html_path.exists())
            html = artifact.html_path.read_text(encoding="utf-8")
            self.assertIn("TickDeck Axis 2 Components Demo", html)
            self.assertIsNone(DEBUG_TOKEN_RE.search(html))
            for name in EXPECTED_COMPONENTS:
                self.assertIn(f"data-component=\"{name}\"", html)
                svg = artifact.svg_paths[name]
                self.assertTrue(svg.exists())
                svg_text = svg.read_text(encoding="utf-8")
                self.assertIn("<svg", svg_text)
                self.assertIsNone(DEBUG_TOKEN_RE.search(svg_text))
                png = artifact.png_paths[name]
                self.assertTrue(png.exists())
                self.assertGreater(png.stat().st_size, 8000)
                self.assertEqual(png.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

            manifest = json.loads(artifact.manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["components"]), EXPECTED_COMPONENTS)
            manifest_text = artifact.manifest_path.read_text(encoding="utf-8")
            self.assertIsNone(DEBUG_TOKEN_RE.search(manifest_text))

    def test_css_is_scoped_to_axis2_components(self):
        renderer = load_renderer()

        css = renderer.component_css()
        self.assertIn(".tdc-component", css)
        self.assertIn(".tdc-card-grid", css)
        self.assertIn(".tdc-dashboard", css)
        self.assertNotIn("fallback", css.lower())

    def test_svg_and_demo_css_use_installed_korean_font_stack(self):
        renderer = load_renderer()
        expected_stack = "'Malgun Gothic', NanumGothic, Pretendard, sans-serif"

        rendered = renderer.render_component(
            "big_percent",
            {
                **DEMO_DATA["big_percent"],
                "title": "핵심 수치 검산",
                "caption": "시장 준비 동인 주의",
            },
        )

        self.assertIn(f'font-family="{expected_stack}"', rendered.svg)
        self.assertIn(f"font-family: {expected_stack};", renderer.component_css())
        self.assertNotIn("Apple SD Gothic Neo", rendered.svg)
        self.assertNotIn("Noto Sans CJK KR", rendered.svg)

    def test_png_conversion_uses_installed_korean_font_without_changing_ppt_stack(self):
        renderer = load_renderer()

        rendered = renderer.render_component(
            "big_percent",
            {
                **DEMO_DATA["big_percent"],
                "title": "핵심 수치 검산",
                "caption": "시장 준비 동인 주의",
            },
        )
        png_svg = renderer.svg_for_png(rendered.svg)

        self.assertIn(f'font-family="{renderer.CAIROSVG_FONT_FAMILY}"', png_svg)
        self.assertNotIn(f'font-family="{renderer.KOREAN_FONT_STACK}"', png_svg)
        self.assertIn(renderer.CAIROSVG_FONT_FAMILY, {"AppleGothic", "Apple SD Gothic Neo", "Arial Unicode MS"})

    def test_svg_root_uses_component_title_as_aria_label(self):
        renderer = load_renderer()

        for name, data in DEMO_DATA.items():
            with self.subTest(component=name):
                rendered = renderer.render_component(name, data)
                title = data["title"]
                self.assertRegex(rendered.svg, rf'<svg\b[^>]* aria-label="{re.escape(title)}"')

    def test_default_palette_avoids_old_purple_default_colors(self):
        renderer = load_renderer()
        old_default_colors = {"#6d5bd0", "#312e81", "#ede9fe", "#8b5cf6", "#4c1d95", "#f5f3ff"}

        resolved = renderer._resolve_palette()

        self.assertTrue(old_default_colors.isdisjoint(set(resolved.values())))

    def test_funnel_contract_uses_segment_geometry(self):
        renderer = load_renderer()

        rendered = renderer.render_component("funnel", DEMO_DATA["funnel"])
        self.assertGreaterEqual(rendered.svg.count('data-role="funnel-segment"'), 4)
        self.assertIn('data-role="funnel-neck"', rendered.svg)
        self.assertIn("<path", rendered.svg)

    def test_timeline_contract_uses_axis_and_nodes(self):
        renderer = load_renderer()

        rendered = renderer.render_component("timeline", DEMO_DATA["timeline"])
        self.assertIn('data-role="timeline-axis"', rendered.svg)
        self.assertGreaterEqual(rendered.svg.count('data-role="timeline-node"'), 4)
        self.assertGreaterEqual(rendered.svg.count('data-role="timeline-connector"'), 4)

    def test_matrix_2x2_contract_uses_quadrants_and_points(self):
        renderer = load_renderer()

        rendered = renderer.render_component("matrix_2x2", DEMO_DATA["matrix_2x2"])
        self.assertEqual(rendered.svg.count('data-role="matrix-quadrant"'), 4)
        self.assertGreaterEqual(rendered.svg.count('data-role="matrix-point"'), 3)
        self.assertIn('data-role="matrix-axis-x"', rendered.svg)
        self.assertIn('data-role="matrix-axis-y"', rendered.svg)

    def test_comparison_vs_contract_uses_two_panels_and_center_vs(self):
        renderer = load_renderer()

        rendered = renderer.render_component("comparison_vs", DEMO_DATA["comparison_vs"])
        self.assertEqual(rendered.svg.count('data-role="vs-panel"'), 2)
        self.assertIn('data-role="vs-medallion"', rendered.svg)
        self.assertGreaterEqual(rendered.svg.count('data-role="vs-connector"'), 2)

    def test_dashboard_contract_uses_multiple_chart_geometries(self):
        renderer = load_renderer()

        rendered = renderer.render_component("dashboard", DEMO_DATA["dashboard"])
        self.assertGreaterEqual(rendered.svg.count('data-role="dashboard-card"'), 3)
        self.assertIn('data-role="dashboard-line"', rendered.svg)
        self.assertGreaterEqual(rendered.svg.count('data-role="dashboard-bar"'), 5)
        self.assertIn('data-role="dashboard-donut"', rendered.svg)

    def test_data_series_colors_use_brand_scale_with_single_emphasis(self):
        renderer = load_renderer()
        expected_series = ["#dbeafe", "#bfdbfe", "#60a5fa", "#d97706"]

        bar_chart = renderer.render_component("bar_chart", DEMO_DATA["bar_chart"]).svg
        bar_fills = re.findall(r'data-role="bar"[^>]* fill="([^"]+)"', bar_chart)
        self.assertEqual(bar_fills, expected_series)

        process = renderer.render_component("process", DEMO_DATA["process"]).svg
        process_fills = re.findall(r'data-role="process-step"[^>]* fill="([^"]+)"', process)
        self.assertEqual(process_fills, expected_series)

        dashboard = renderer.render_component("dashboard", DEMO_DATA["dashboard"]).svg
        dashboard_bar_fills = re.findall(r'data-role="dashboard-bar"[^>]* fill="([^"]+)"', dashboard)
        self.assertEqual(dashboard_bar_fills, ["#dbeafe", "#bfdbfe", "#60a5fa", "#2563eb", "#d97706"])

    def test_dashboard_gives_primary_kpi_visual_hierarchy(self):
        renderer = load_renderer()

        rendered = renderer.render_component("dashboard", DEMO_DATA["dashboard"])
        cards = [
            (float(width), float(height))
            for width, height in re.findall(r'data-role="dashboard-card"[^>]* width="([0-9.]+)" height="([0-9.]+)"', rendered.svg)
        ]

        self.assertEqual(len(cards), 3)
        self.assertGreater(cards[0][0], cards[1][0])
        self.assertGreater(cards[0][1], cards[1][1])
        self.assertEqual(cards[1], cards[2])

    def test_timeline_removes_decorative_left_color_strips(self):
        renderer = load_renderer()

        rendered = renderer.render_component("timeline", DEMO_DATA["timeline"])

        self.assertNotRegex(rendered.svg, r'<rect x="[^"]+" y="[^"]+" width="10" height="112"')
        self.assertEqual(rendered.svg.count('data-role="timeline-date-pill"'), 4)

    def test_card_grid_sparkline_is_bound_to_card_value(self):
        renderer = load_renderer()

        rendered = renderer.render_component("card_grid", DEMO_DATA["card_grid"])

        self.assertEqual(rendered.svg.count('data-role="card-spark"'), 3)
        self.assertEqual(rendered.svg.count('data-role="card-spark-marker"'), 3)
        for card in DEMO_DATA["card_grid"]["cards"]:
            self.assertIn(f'data-value="{float(card["value"]):.1f}"', rendered.svg)

    def test_card_grid_without_values_does_not_invent_metric_values(self):
        renderer = load_renderer()
        data = {
            "title": "5대 성장 동인",
            "cards": [
                {"label": "에이전틱 AI", "caption": "캠페인 실행 자동화"},
                {"label": "AI 퍼스트 검색", "caption": "AEO 노출 경쟁"},
                {"label": "프라이버시 우선", "caption": "제1자 데이터 자산화"},
            ],
            "unit": "",
            "source_map": {"cards": ["axis1:leader.final"]},
        }

        rendered = renderer.render_component("card_grid", data)

        self.assertIn("에이전틱 AI", rendered.svg)
        self.assertIn("AI 퍼스트 검색", rendered.svg)
        self.assertNotIn('data-role="card-value"', rendered.svg)
        self.assertNotIn('data-role="card-spark"', rendered.svg)
        self.assertNotIn('data-role="card-progress-track"', rendered.svg)

    def test_map_data_contract_uses_map_regions_and_data_bubbles(self):
        renderer = load_renderer()

        rendered = renderer.render_component("map_data", DEMO_DATA["map_data"])
        self.assertGreaterEqual(rendered.svg.count('data-role="map-region"'), 4)
        self.assertEqual(rendered.svg.count('data-role="map-bubble"'), 3)
        self.assertIn('data-role="map-legend"', rendered.svg)

    def test_process_contract_uses_arrow_sequence_geometry(self):
        renderer = load_renderer()

        rendered = renderer.render_component("process", DEMO_DATA["process"])
        self.assertEqual(rendered.svg.count('data-role="process-step"'), 4)
        self.assertGreaterEqual(rendered.svg.count('data-role="process-connector"'), 3)
        self.assertIn("<polygon", rendered.svg)

    def test_bar_chart_value_labels_stay_below_header_area(self):
        renderer = load_renderer()

        rendered = renderer.render_component("bar_chart", DEMO_DATA["bar_chart"])
        label_y_values = [
            float(value)
            for value in re.findall(r'y="([0-9.]+)"[^>]*>(?:42|58|71|86)%</text>', rendered.svg)
        ]
        self.assertEqual(len(label_y_values), 4)
        self.assertGreaterEqual(min(label_y_values), 220)

    def test_card_grid_reference_note_fits_inside_viewbox(self):
        renderer = load_renderer()

        rendered = renderer.render_component("card_grid", DEMO_DATA["card_grid"])
        match = re.search(r'<text x="([0-9.]+)" y="176"[^>]*>(Source-linked cards[^<]+)</text>', rendered.svg)
        self.assertIsNotNone(match)
        x = float(match.group(1))
        text = match.group(2)
        self.assertLessEqual(x + len(text) * 13, 1220)

    def test_big_percent_caption_wraps_inside_left_panel(self):
        renderer = load_renderer()
        data = dict(DEMO_DATA["big_percent"])
        data["caption"] = "Qualified buyers prefer visual proof when the deck shows evidence without making the card overflow."

        rendered = renderer.render_component("big_percent", data)
        caption_lines = re.findall(
            r'<text data-role="caption-line" x="([0-9.]+)" y="([0-9.]+)"[^>]*>([^<]+)</text>',
            rendered.svg,
        )
        self.assertGreaterEqual(len(caption_lines), 2)
        self.assertNotIn(data["caption"], rendered.svg)
        for x_value, _y_value, text in caption_lines:
            self.assertLessEqual(float(x_value) + len(text) * 12, 450)

    def test_big_percent_value_labels_auto_fit_inside_cards(self):
        renderer = load_renderer()
        cases = [
            (73, "%", "73%"),
            (10.6, "%", "10.6%"),
            (123, "%", "123%"),
            ("1.29조 달러", "", "1.29조 달러"),
            ("123456789.12% CAGR", "", "123456789.12% CAGR"),
        ]

        for value, unit, expected in cases:
            with self.subTest(expected=expected):
                data = dict(DEMO_DATA["big_percent"])
                data["value"] = value
                data["unit"] = unit
                rendered = renderer.render_component("big_percent", data)

                main_match = re.search(r'<text (?P<attrs>[^>]*\sy="358"[^>]*)>(?P<label>[^<]+)</text>', rendered.svg)
                self.assertIsNotNone(main_match)
                self.assertEqual(unescape(main_match.group("label")), expected)
                main_attrs = self._svg_attrs(main_match.group("attrs"))
                main_width = self._estimated_label_width(expected, float(main_attrs["font-size"]))
                self.assertLessEqual(float(main_attrs["x"]) + main_width, 456)

                side_matches = list(re.finditer(r'<text (?P<attrs>[^>]*\sy="342"[^>]*)>(?P<label>[^<]+)</text>', rendered.svg))
                self.assertGreaterEqual(len(side_matches), 2)
                side_match = side_matches[-1]
                self.assertEqual(unescape(side_match.group("label")), expected)
                side_attrs = self._svg_attrs(side_match.group("attrs"))
                side_width = self._estimated_label_width(expected, float(side_attrs["font-size"]))
                if side_attrs.get("text-anchor") == "end":
                    self.assertGreaterEqual(float(side_attrs["x"]) - side_width, 548)
                    self.assertLessEqual(float(side_attrs["x"]), 1180)
                else:
                    self.assertLessEqual(float(side_attrs["x"]) + side_width, 1180)

    def test_card_grid_sparkline_stays_below_label_text(self):
        renderer = load_renderer()

        rendered = renderer.render_component("card_grid", DEMO_DATA["card_grid"])
        spark_paths = re.findall(r'data-role="card-spark" d="([^"]+)"', rendered.svg)
        self.assertEqual(len(spark_paths), 3)
        for path_data in spark_paths:
            y_values = [float(y) for _x, y in re.findall(r'([0-9.]+) ([0-9.]+)', path_data)]
            self.assertGreaterEqual(min(y_values), 456)

    def test_card_grid_value_labels_do_not_overlap_progress_bars(self):
        renderer = load_renderer()

        rendered = renderer.render_component("card_grid", DEMO_DATA["card_grid"])
        value_y_values = [
            float(value)
            for value in re.findall(r'data-role="card-value"[^>]* y="([0-9.]+)"', rendered.svg)
        ]
        progress_y_values = [
            float(value)
            for value in re.findall(r'data-role="card-progress-track"[^>]* y="([0-9.]+)"', rendered.svg)
        ]
        self.assertEqual(len(value_y_values), 3)
        self.assertEqual(len(progress_y_values), 3)
        for value_y, progress_y in zip(value_y_values, progress_y_values):
            self.assertLessEqual(value_y + 10, progress_y)

    def test_funnel_chart_column_stays_clear_of_title_column(self):
        renderer = load_renderer()

        rendered = renderer.render_component("funnel", DEMO_DATA["funnel"])
        self.assertIn('data-role="funnel-text-column"', rendered.svg)
        self.assertIn('data-role="funnel-chart-column"', rendered.svg)
        segment_paths = re.findall(r'data-role="funnel-segment" d="([^"]+)"', rendered.svg)
        x_values = [
            float(x)
            for path_data in segment_paths
            for x, _y in re.findall(r'([0-9.]+) ([0-9.]+)', path_data)
        ]
        self.assertGreaterEqual(min(x_values), 560)

    def test_map_bubbles_stay_inside_chart_column_away_from_legend(self):
        renderer = load_renderer()

        rendered = renderer.render_component("map_data", DEMO_DATA["map_data"])
        bubble_x_values = [
            float(value)
            for value in re.findall(r'data-role="map-bubble" cx="([0-9.]+)"', rendered.svg)
        ]
        self.assertEqual(len(bubble_x_values), 3)
        self.assertGreaterEqual(min(bubble_x_values), 456)

    def test_matrix_subtitle_and_quadrant_labels_have_reserved_space(self):
        renderer = load_renderer()

        rendered = renderer.render_component("matrix_2x2", DEMO_DATA["matrix_2x2"])
        self.assertIn('data-role="matrix-subtitle-line"', rendered.svg)
        quadrant_labels = [
            (float(x), float(y))
            for x, y in re.findall(r'data-role="matrix-quadrant-label"[^>]* x="([0-9.]+)" y="([0-9.]+)"', rendered.svg)
        ]
        points = [
            (float(x), float(y))
            for x, y in re.findall(r'data-role="matrix-point" cx="([0-9.]+)" cy="([0-9.]+)"', rendered.svg)
        ]
        self.assertEqual(len(quadrant_labels), 4)
        for label_x, label_y in quadrant_labels:
            for point_x, point_y in points:
                self.assertGreater(math.dist((label_x, label_y), (point_x, point_y)), 64)

    def test_dashboard_kpi_markers_do_not_cover_labels(self):
        renderer = load_renderer()

        rendered = renderer.render_component("dashboard", DEMO_DATA["dashboard"])
        markers = [
            float(value)
            for value in re.findall(r'data-role="dashboard-kpi-marker" cx="([0-9.]+)"', rendered.svg)
        ]
        labels = [
            float(value)
            for value in re.findall(r'data-role="dashboard-kpi-label" x="([0-9.]+)"', rendered.svg)
        ]
        self.assertEqual(len(markers), 3)
        self.assertEqual(len(labels), 3)
        for marker_x, label_x in zip(markers, labels):
            self.assertGreaterEqual(marker_x - label_x, 104)

    def test_donut_gauge_legend_text_stays_inside_viewbox(self):
        renderer = load_renderer()

        rendered = renderer.render_component("donut_gauge", DEMO_DATA["donut_gauge"])
        legend_lines = re.findall(
            r'data-role="donut-legend-line" x="([0-9.]+)"[^>]*>([^<]+)</text>',
            rendered.svg,
        )
        self.assertGreaterEqual(len(legend_lines), 2)
        for x_value, text in legend_lines:
            self.assertLessEqual(float(x_value) + len(text) * 12, 1180)


if __name__ == "__main__":
    unittest.main()
