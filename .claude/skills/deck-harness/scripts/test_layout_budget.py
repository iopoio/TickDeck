from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parent
CALIBRATION_DIR = SCRIPT_DIR.parent / "calibration"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(CALIBRATION_DIR))

from layout_budget import (  # noqa: E402
    BudgetVerdict,
    LayoutBudgetInputError,
    block_height,
    classify_height,
    evaluate_layout,
    line_count,
    linear_partition_impossible,
    metric_grid_height,
    page_height,
    sibling_vertical_overlaps,
    split_fits,
    split_page_height,
    split_viz_height,
    substitute_metric_tokens,
    text_table_height,
    viz_signature,
)
from calibrate_layout import css_hash, font_build_hash, renderer_struct_hash  # noqa: E402
from predictor import CalibrationRuntimeKeyError, resolve_entry  # noqa: E402


KEY = {
    "renderer_struct_hash": renderer_struct_hash(),
    "css_hash": css_hash("editorial"),
    "theme": "editorial",
    "page_chrome": "title_band",
    "layout": "statement",
    "width_class": "820px",
    "font_build": font_build_hash(),
    "browser_major": "151",
}


REGISTRY = {
    "sources": {
        "src_probe": {"publisher": "Probe Publisher", "url": "https://example.com"},
        "src_a": {"publisher": "Publisher A", "url": "https://example.com/a"},
        "src_b": {"publisher": "Publisher B", "url": "https://example.com/b"},
    },
    "metrics": {
        "m": {"value": "123456789012345678901234567890", "unit": "%", "source_ids": []},
        "m_a": {"value": "1", "unit": "%", "source_ids": ["src_a"]},
        "m_b": {"value": "2", "unit": "%", "source_ids": ["src_b"]},
        "m_derived": {"value": "3", "unit": "%", "derived_from": ["m_a"]},
        "m_nested": {"value": "4", "unit": "%", "derived_from": ["m_derived"]},
    },
}


def viz(chart: str, series_count: int = 2) -> dict:
    return {
        "type": "viz",
        "chart": chart,
        "series": [{"label": f"series-{index}"} for index in range(series_count)],
    }


VIZ_BLOCKS = {
    "donut": viz("donut"),
    "dumbbell": viz("dumbbell"),
    "causal_chain": viz("causal_chain"),
}


CALIBRATION_ENTRY = {
    "key": dict(KEY),
    "values": {
        "capacity_px": 529.0,
        "viz_heights_px": {
            viz_signature(VIZ_BLOCKS["donut"]): 301.0,
            viz_signature(VIZ_BLOCKS["dumbbell"]): 204.0,
            viz_signature(VIZ_BLOCKS["causal_chain"]): 164.0,
        },
    },
    "provenance": {"status": "measured"},
}


def chars_for_lines(lines: int, width: float, font: float) -> str:
    chars_per_line = int(width // (font * 0.78))
    return "가" * ((lines - 1) * chars_per_line + 1)


def headline(lines: int) -> dict:
    return {"type": "headline", "text": chars_for_lines(lines, 960, 24)}


def body(lines: int) -> dict:
    return {"type": "body", "text": chars_for_lines(lines, 980, 18)}


def note(lines: int) -> dict:
    return {"type": "note", "text": chars_for_lines(lines, 972, 20)}


def emphasis(lines: int) -> dict:
    return {"type": "callout", "emphasis": True, "text": chars_for_lines(lines, 968, 30)}


def table(rows: int, *, titled: bool) -> dict:
    return {
        "type": "text_table",
        "title": "표 제목" if titled else "",
        "columns": ["A", "B"],
        "rows": [["가", "나"] for _ in range(rows)],
    }


class LayoutBudgetArithmeticTests(unittest.TestCase):
    def test_split_page_height_adds_note_as_a_full_width_row(self):
        self.assertEqual(
            split_page_height(34.0, 216.0, 360.0, 80.0),
            520.0,
        )

    def test_sibling_vertical_overlaps_reports_only_intersections(self):
        self.assertEqual(
            sibling_vertical_overlaps(
                [("split-body", 100.0, 460.0), ("split-note-row", 440.0, 520.0), ("footer", 540.0, 560.0)]
            ),
            (("split-body", "split-note-row", 20.0),),
        )

    def test_appendix_a_numeric_checks_match_all_21_values(self):
        h = lambda block: block_height(block, REGISTRY, CALIBRATION_ENTRY)
        cases = {
            "metric_grid(2)": metric_grid_height(2),
            "metric_grid(3)": metric_grid_height(3),
            "metric_grid(4)": metric_grid_height(4),
            "metric_grid(5)": metric_grid_height(5),
            "metric_grid(6)": metric_grid_height(6),
            "table5(3)-190": text_table_height(table(3, titled=True), REGISTRY) - 190,
            "table5(5)-267": text_table_height(table(5, titled=True), REGISTRY) - 267,
            "B1-1": page_height([h(headline(1)), h(body(4)), h(table(5, titled=False))]),
            "B1-1b": page_height([h(headline(1)), h(body(4)), h(table(5, titled=True))]),
            "B1-2": page_height([h(headline(1)), h(VIZ_BLOCKS["donut"]), h(body(1))]),
            "B1-2b": page_height([h(headline(1)), h(VIZ_BLOCKS["donut"]), h(body(2))]),
            "B1-3": page_height([h(table(6, titled=True)), h(VIZ_BLOCKS["dumbbell"])]),
            "B1-4": page_height([h(headline(1)), h(emphasis(2)), h(body(7))]),
            "B1-4b": page_height([h(headline(1)), h(emphasis(2)), h(body(8))]),
            "B1-5": page_height([metric_grid_height(5), h(VIZ_BLOCKS["causal_chain"])]),
            "v1-example-1": page_height([h(headline(1)), h(body(4)), h(table(5, titled=True)), h(note(2))]),
            "v1-example-2": page_height([h(headline(1)), h(VIZ_BLOCKS["donut"]), h(body(2)), h(note(2))]),
            "C1-viz400+metric": page_height([400 + 14, 172]),
            "C1-split-viz400": split_viz_height(400),
            "partition-lower": 529 - 50 + 60,
            "partition-upper": 2 * (529 - 240) + 24,
        }
        expected = {
            "metric_grid(2)": 170,
            "metric_grid(3)": 170,
            "metric_grid(4)": 202,
            "metric_grid(5)": 392,
            "metric_grid(6)": 392,
            "table5(3)-190": 2.5,
            "table5(5)-267": 2.5,
            "B1-1": 458,
            "B1-1b": 495,
            "B1-2": 456.5,
            "B1-2b": 484.5,
            "B1-3": 505,
            "B1-4": 457.5,
            "B1-4b": 485.5,
            "B1-5": 594,
            "v1-example-1": 629,
            "v1-example-2": 618.5,
            "C1-viz400+metric": 610,
            "C1-split-viz400": 288,
            "partition-lower": 539,
            "partition-upper": 602,
        }
        self.assertEqual(len(cases), 21)
        mismatches = {name: (got, expected[name]) for name, got in cases.items() if abs(got - expected[name]) > 0.01}
        self.assertEqual(mismatches, {})
        self.assertTrue(split_fits(288, 172, 479))
        self.assertFalse(split_fits(split_viz_height(560), 172, 479))

    def test_boundary_operators_are_strict(self):
        self.assertEqual(classify_height(479, 529), BudgetVerdict.FIT)
        self.assertEqual(classify_height(479.01, 529), BudgetVerdict.OVERFLOW)
        self.assertEqual(classify_height(289, 529), BudgetVerdict.FIT)
        self.assertEqual(classify_height(288.99, 529), BudgetVerdict.SPARSE)
        self.assertTrue(linear_partition_impossible(601.99, 529))
        self.assertFalse(linear_partition_impossible(602, 529))

    def test_registry_tokens_are_replaced_before_line_count(self):
        resolved = substitute_metric_tokens("값 {{m}} 확인", REGISTRY)
        self.assertEqual(resolved, "값 123,456,789,012,345,678,901,234,567,890% 확인")
        self.assertEqual(
            block_height({"type": "body", "text": "값 {{m}} 확인"}, REGISTRY, CALIBRATION_ENTRY),
            28 * line_count(len(resolved), 980, 18) + 36,
        )
        with self.assertRaises(LayoutBudgetInputError):
            substitute_metric_tokens("{{unknown_metric}}", REGISTRY)

    def test_viz_signature_separates_chart_specific_height_controls(self):
        pictograph_10 = {
            "type": "viz",
            "chart": "pictograph",
            "series": [{"label": "표본", "total": 10, "filled": 4}],
        }
        pictograph_50 = {
            **pictograph_10,
            "series": [{"label": "표본", "total": 50, "filled": 20}],
        }
        self.assertNotEqual(viz_signature(pictograph_10), viz_signature(pictograph_50))

    def test_three_level_viz_title_has_distinct_unmeasured_signature(self):
        legacy = VIZ_BLOCKS["donut"]
        titled = {
            **legacy,
            "exhibit": "Exhibit 3",
            "title": "도입은 늘었지만 수익 전환은 드물다.",
            "subtitle": "AI 도입 단계별 응답 비율, %",
        }
        self.assertNotIn("title_layers=3", viz_signature(legacy))
        self.assertIn("title_layers=3", viz_signature(titled))
        self.assertNotEqual(viz_signature(legacy), viz_signature(titled))

        spec = {
            "theme": KEY["theme"],
            "meta": {
                "page_chrome": KEY["page_chrome"],
                "calibration_runtime": {
                    "width_class": KEY["width_class"],
                    "browser_major": KEY["browser_major"],
                },
            },
            "pages": [{"page_id": "p01", "layout": "statement", "content": [headline(1), titled]}],
        }
        result = evaluate_layout(spec, REGISTRY, CALIBRATION_ENTRY)[0]
        self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
        self.assertIn("unmeasured viz combination", result.reasons[0])


class LayoutBudgetFailClosedTests(unittest.TestCase):
    def _spec(self, content: list[dict], **overrides) -> dict:
        page = {
            "page_id": "p01",
            "short_title": "한 줄 제목",
            "layout": "statement",
            "content": content,
        }
        page.update(overrides)
        return {
            "theme": KEY["theme"],
            "meta": {
                "page_chrome": KEY["page_chrome"],
                "calibration_runtime": {
                    "width_class": KEY["width_class"],
                    "browser_major": KEY["browser_major"],
                },
            },
            "pages": [page],
        }

    def test_model_outside_blocks_and_unmeasured_viz_require_render_measurement(self):
        cases = {
            "image": [{"type": "image", "asset": "probe.png"}],
            "bullets": [{"type": "bullets", "items": ["하나"]}],
            "unmeasured_viz": [viz("donut", series_count=3)],
            "footnote": [{"type": "footnote", "text": "일반 높이 공식 미규명"}],
            "source_row": [{"type": "citation", "src_id": "src_probe"}],
        }
        for name, content in cases.items():
            with self.subTest(name=name):
                result = evaluate_layout(self._spec(content), REGISTRY, CALIBRATION_ENTRY)[0]
                self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
                self.assertIsNone(result.height_px)

    def test_calibration_key_mismatch_never_uses_anchor_fallback(self):
        result = evaluate_layout(
            self._spec([body(1)], layout="stack"),
            REGISTRY,
            CALIBRATION_ENTRY,
        )[0]
        self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)

    def test_each_stale_calibration_key_dimension_requires_render_measurement(self):
        spec = self._spec([body(1)])
        for dimension in KEY:
            stale_entry = copy.deepcopy(CALIBRATION_ENTRY)
            stale_entry["key"][dimension] = f"stale-{dimension}"
            with self.subTest(dimension=dimension):
                result = evaluate_layout(spec, REGISTRY, stale_entry)[0]
                self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
                self.assertIsNone(result.capacity_px)
                self.assertEqual(result.reasons, (f"calibration key mismatch: {dimension}",))

    def test_missing_caller_runtime_key_dimensions_never_use_defaults(self):
        for dimension in ("theme", "page_chrome", "layout", "width_class", "browser_major"):
            spec = copy.deepcopy(self._spec([body(1)]))
            if dimension == "theme":
                spec.pop("theme")
            elif dimension == "layout":
                spec["pages"][0].pop("layout")
            elif dimension in {"width_class", "browser_major"}:
                spec["meta"]["calibration_runtime"].pop(dimension)
            else:
                spec["meta"].pop(dimension)
            with self.subTest(dimension=dimension):
                result = evaluate_layout(spec, REGISTRY, CALIBRATION_ENTRY)[0]
                self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
                self.assertIsNone(result.capacity_px)
                self.assertEqual(
                    result.reasons,
                    (f"runtime calibration key dimension is missing: {dimension}",),
                )

    def test_unavailable_local_runtime_key_dimensions_require_render_measurement(self):
        for dimension, helper_name in (
            ("renderer_struct_hash", "renderer_struct_hash"),
            ("css_hash", "css_hash"),
            ("font_build", "font_build_hash"),
        ):
            error = CalibrationRuntimeKeyError(f"probe-{dimension}")
            with self.subTest(dimension=dimension), patch(
                f"layout_budget.{helper_name}", side_effect=error
            ):
                result = evaluate_layout(
                    self._spec([body(1)]), REGISTRY, CALIBRATION_ENTRY
                )[0]
                self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
                self.assertIsNone(result.capacity_px)
                self.assertEqual(
                    result.reasons,
                    (f"runtime calibration key cannot be confirmed: probe-{dimension}",),
                )

    def test_renderer_per_card_sources_suppress_source_row_measurement_downgrade(self):
        content = [{"type": "metric_grid", "metric_ids": ["m_a", "m_b"]}]
        result = evaluate_layout(self._spec(content), REGISTRY, CALIBRATION_ENTRY)[0]
        self.assertEqual(result.verdict, BudgetVerdict.SPARSE)
        self.assertEqual(result.height_px, 170.0)

    def test_renderer_nested_derived_metric_source_requires_source_row_measurement(self):
        content = [{"type": "metric", "metric_id": "m_nested"}]
        result = evaluate_layout(self._spec(content), REGISTRY, CALIBRATION_ENTRY)[0]
        self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
        self.assertEqual(
            result.reasons,
            ("source-row general height formula is uncalibrated",),
        )

    def test_chrome_none_eyebrow_deducts_fourteen_pixels(self):
        chrome_none_entry = copy.deepcopy(CALIBRATION_ENTRY)
        chrome_none_entry["key"]["page_chrome"] = "none"
        chrome_none_entry["values"]["capacity_px"] = 531.0
        spec = self._spec([{"type": "eyebrow", "text": "구분"}, body(1)])
        spec["meta"]["page_chrome"] = "none"

        result = evaluate_layout(spec, REGISTRY, chrome_none_entry)[0]
        self.assertEqual(result.capacity_px, 517.0)

    def test_chrome_none_eyebrow_chip_fails_closed_until_calibrated(self):
        chrome_none_entry = copy.deepcopy(CALIBRATION_ENTRY)
        chrome_none_entry["key"]["page_chrome"] = "none"
        chrome_none_entry["values"]["capacity_px"] = 531.0
        spec = self._spec([{"type": "eyebrow", "text": "구분"}, body(1)])
        spec["meta"]["page_chrome"] = "none"
        spec["pages"][0]["eyebrow_chip"] = True

        result = evaluate_layout(spec, REGISTRY, chrome_none_entry)[0]
        self.assertEqual(result.verdict, BudgetVerdict.RENDER_MEASURE_REQUIRED)
        self.assertEqual(
            result.reasons,
            ("chrome-none eyebrow_chip height is uncalibrated",),
        )

    def test_chrome_none_two_line_title_and_eyebrow_keep_strict_boundary_fit(self):
        chrome_none_entry = copy.deepcopy(CALIBRATION_ENTRY)
        chrome_none_entry["key"]["page_chrome"] = "none"
        chrome_none_entry["values"]["capacity_px"] = 531.0
        spec = self._spec(
            [{"type": "eyebrow", "text": "구분"}, emphasis(1), body(9)]
        )
        spec["meta"]["page_chrome"] = "none"
        spec["pages"][0]["short_title"] = "가" * 29

        result = evaluate_layout(spec, REGISTRY, chrome_none_entry)[0]
        self.assertEqual(result.capacity_px, 465.0)
        self.assertEqual(result.overflow_cutoff_px, 415.0)
        self.assertEqual(result.height_px, 415.0)
        self.assertEqual(result.verdict, BudgetVerdict.FIT)

    def test_exact_split_calibration_height_is_not_scaled_twice(self):
        split_entry = {
            **CALIBRATION_ENTRY,
            "key": {**KEY, "layout": "split", "width_class": "640px"},
        }
        measured_height = CALIBRATION_ENTRY["values"]["viz_heights_px"][
            viz_signature(VIZ_BLOCKS["donut"])
        ]
        self.assertEqual(
            block_height(VIZ_BLOCKS["donut"], REGISTRY, split_entry),
            measured_height + 14,
        )

    def test_split_budget_places_note_below_the_taller_pane(self):
        split_entry = copy.deepcopy(CALIBRATION_ENTRY)
        split_entry["key"]["layout"] = "split"
        spec = self._spec(
            [headline(1), VIZ_BLOCKS["donut"], body(1), {"type": "metric", "metric_id": "m"}, {"type": "metric", "metric_id": "m"}, note(1)],
            layout="split",
        )

        result = evaluate_layout(spec, REGISTRY, split_entry)[0]

        self.assertEqual(result.height_px, 527.5)
        self.assertEqual(result.verdict, BudgetVerdict.OVERFLOW)

    def test_generated_calibration_resolves_into_budget_without_height_drift(self):
        calibration_root = SCRIPT_DIR.parent / "calibration"
        document = json.loads(
            (calibration_root / "layout_calibration.json").read_text(encoding="utf-8")
        )
        measured_entry = resolve_entry(document, document["entries"][0]["key"])
        probe_spec = json.loads(
            (
                calibration_root
                / "probe_specs"
                / "editorial_title_band_statement.spec.json"
            ).read_text(encoding="utf-8")
        )
        probe_registry = json.loads(
            (
                calibration_root
                / "probe_specs"
                / "editorial_title_band_statement.registry.json"
            ).read_text(encoding="utf-8")
        )
        measured_viz = probe_spec["pages"][1]["content"][0]
        boundary_spec = {
            "theme": "editorial",
            "meta": {
                "page_chrome": "title_band",
                "calibration_runtime": {
                    "width_class": measured_entry["key"]["width_class"],
                    "browser_major": measured_entry["key"]["browser_major"],
                },
            },
            "pages": [
                {
                    "page_id": "p_boundary",
                    "short_title": "경계",
                    "layout": "statement",
                    "content": [headline(1), measured_viz, body(2)],
                }
            ],
        }
        result = evaluate_layout(boundary_spec, probe_registry, measured_entry)[0]
        self.assertAlmostEqual(result.height_px, 484.219, places=3)
        self.assertEqual(result.verdict, BudgetVerdict.OVERFLOW)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful():
        print("ARITHMETIC_MATCHED=21 ARITHMETIC_MISMATCHED=0")
    raise SystemExit(0 if result.wasSuccessful() else 1)
