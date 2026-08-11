from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from predictor import (  # noqa: E402
    KEY_DIMENSIONS,
    CalibrationFormatError,
    UncalibratedCombinationError,
    resolve_entry,
)


KEY = {
    "renderer_struct_hash": "renderer-sha256",
    "css_hash": "css-sha256",
    "theme": "editorial",
    "page_chrome": "title_band",
    "layout": "statement",
    "width_class": "820px",
    "font_build": "pretendard-v1.3.9-sha256",
    "browser_major": "151",
}


def calibration_document() -> dict:
    return {
        "schema_version": 1,
        "key_dimensions": list(KEY_DIMENSIONS),
        "entries": [
            {
                "key": dict(KEY),
                "values": {"capacity_px": 529.0, "viz_heights_px": {}},
                "provenance": {"status": "measured"},
            }
        ],
    }


class PredictorTests(unittest.TestCase):
    def test_resolve_entry_requires_exact_eight_dimension_match(self):
        entry = resolve_entry(calibration_document(), KEY)
        self.assertEqual(entry["values"]["capacity_px"], 529.0)

    def test_resolve_entry_never_falls_back_to_the_only_entry(self):
        requested = dict(KEY, browser_major="152")
        with self.assertRaises(UncalibratedCombinationError):
            resolve_entry(calibration_document(), requested)

    def test_resolve_entry_rejects_missing_or_extra_key_dimensions(self):
        missing = dict(KEY)
        missing.pop("font_build")
        extra = dict(KEY, silent_default="forbidden")
        for requested in (missing, extra):
            with self.subTest(requested=requested):
                with self.assertRaises(CalibrationFormatError):
                    resolve_entry(calibration_document(), requested)

    def test_resolve_entry_rejects_unmeasured_or_duplicate_entries(self):
        unmeasured = calibration_document()
        unmeasured["entries"][0]["provenance"]["status"] = "estimated"
        with self.assertRaises(UncalibratedCombinationError):
            resolve_entry(unmeasured, KEY)

        duplicate = calibration_document()
        duplicate["entries"].append(copy.deepcopy(duplicate["entries"][0]))
        with self.assertRaises(CalibrationFormatError):
            resolve_entry(duplicate, KEY)

    def test_resolve_entry_rejects_unknown_schema_version(self):
        unknown = calibration_document()
        unknown["schema_version"] = 2
        with self.assertRaises(CalibrationFormatError):
            resolve_entry(unknown, KEY)


if __name__ == "__main__":
    unittest.main(verbosity=2)
