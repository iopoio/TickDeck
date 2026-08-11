from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from calibrate_layout import (  # noqa: E402
    CalibrationRunError,
    MEASUREMENT_SCRIPT,
    build_calibration_entry,
    chrome_runtime_flags,
    css_hash,
    extract_measurement_payload,
    parse_browser_major,
)


PROBE_SPEC = {
    "theme": "editorial",
    "meta": {
        "page_chrome": "title_band",
        "calibration_probe": {"capacity_page_id": "p_capacity"},
    },
    "pages": [
        {"page_id": "p_capacity", "layout": "statement", "content": []},
        {
            "page_id": "p_viz",
            "layout": "statement",
            "content": [
                {
                    "type": "viz",
                    "chart": "donut",
                    "series": [{"label": "A"}, {"label": "B"}],
                }
            ],
        },
    ],
}


MEASUREMENT = {
    "font_ready": True,
    "pages": [
        {
            "page_id": "p_capacity",
            "body": {"client_height_px": 529.0, "client_width_px": 1136.0},
            "visuals": [],
        },
        {
            "page_id": "p_viz",
            "body": {"client_height_px": 529.0, "client_width_px": 1136.0},
            "visuals": [
                {
                    "width_px": 820.0,
                    "card": {"height_px": 301.0},
                    "svg_height_px": 284.0,
                }
            ],
        },
    ],
}


class CalibrateLayoutTests(unittest.TestCase):
    def test_parse_browser_major_requires_real_version_shape(self):
        self.assertEqual(parse_browser_major("Google Chrome 151.0.7922.108"), "151")
        self.assertEqual(parse_browser_major("Google Chrome for Testing 148.0.7778.96"), "148")
        with self.assertRaises(CalibrationRunError):
            parse_browser_major("unknown browser")

    def test_headless_shell_uses_single_process_inside_managed_sandbox(self):
        self.assertEqual(
            chrome_runtime_flags("/tmp/chrome-headless-shell"),
            ["--no-sandbox", "--single-process"],
        )
        self.assertEqual(chrome_runtime_flags("/Applications/Google Chrome"), [])

    def test_measurement_runner_does_not_wait_on_animation_frames(self):
        self.assertNotIn("requestAnimationFrame", MEASUREMENT_SCRIPT)
        self.assertIn("setTimeout", MEASUREMENT_SCRIPT)

    def test_css_hash_uses_renderer_palette_resolution(self):
        digest = css_hash("editorial")
        self.assertEqual(len(digest), 64)
        self.assertTrue(all(character in "0123456789abcdef" for character in digest))

    def test_extract_measurement_payload_reads_json_script(self):
        dom = '<html><body><script id="__layout_calibration__" type="application/json">{"font_ready":true,"pages":[]}</script></body></html>'
        self.assertEqual(extract_measurement_payload(dom), {"font_ready": True, "pages": []})

    def test_build_calibration_entry_uses_all_eight_measured_dimensions(self):
        entry = build_calibration_entry(
            PROBE_SPEC,
            MEASUREMENT,
            renderer_struct_hash="renderer-sha256",
            css_hash="css-sha256",
            font_build="pretendard-v1.3.9-sha256",
            browser_major="151",
            raw_path="raw/run/probe.measurement.json",
            measured_at="2026-08-11T10:00:00+09:00",
        )
        self.assertEqual(
            set(entry["key"]),
            {
                "renderer_struct_hash",
                "css_hash",
                "theme",
                "page_chrome",
                "layout",
                "width_class",
                "font_build",
                "browser_major",
            },
        )
        self.assertEqual(entry["key"]["width_class"], "820px")
        self.assertEqual(entry["values"]["capacity_px"], 529.0)
        self.assertEqual(list(entry["values"]["viz_heights_px"].values()), [301.0])
        self.assertEqual(entry["provenance"]["status"], "measured")

    def test_build_calibration_entry_rejects_font_or_width_measurement_gaps(self):
        no_font = dict(MEASUREMENT, font_ready=False)
        no_width = {
            "font_ready": True,
            "pages": [dict(MEASUREMENT["pages"][0]), dict(MEASUREMENT["pages"][1], visuals=[])],
        }
        for measurement in (no_font, no_width):
            with self.subTest(measurement=measurement):
                with self.assertRaises(CalibrationRunError):
                    build_calibration_entry(
                        PROBE_SPEC,
                        measurement,
                        renderer_struct_hash="renderer-sha256",
                        css_hash="css-sha256",
                        font_build="pretendard-v1.3.9-sha256",
                        browser_major="151",
                        raw_path="raw/run/probe.measurement.json",
                        measured_at="2026-08-11T10:00:00+09:00",
                    )

    def test_probe_rejects_theme_whose_typography_is_not_pretendard(self):
        serif_probe = {**PROBE_SPEC, "theme": "editorial_serif"}
        with self.assertRaisesRegex(CalibrationRunError, "typography"):
            build_calibration_entry(
                serif_probe,
                MEASUREMENT,
                renderer_struct_hash="renderer-sha256",
                css_hash="css-sha256",
                font_build="pretendard-v1.3.9-sha256",
                browser_major="151",
                raw_path="raw/run/probe.measurement.json",
                measured_at="2026-08-11T10:00:00+09:00",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
