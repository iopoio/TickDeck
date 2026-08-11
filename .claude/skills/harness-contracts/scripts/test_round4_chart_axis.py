from __future__ import annotations

import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from contract_checks import check_deck_spec_gates  # noqa: E402


class Round4ChartAxisTests(unittest.TestCase):
    def test_rejects_body_pages_with_zero_chart_blocks(self):
        page_plan = {"pages": [{"page_id": "plan-1"}]}
        deck_spec = {
            "pages": [
                {
                    "page_id": "p01",
                    "layout": "statement",
                    "content": [{"type": "metric", "metric_id": "m1"}],
                }
            ]
        }
        layout_results = [
            {"page_id": "p01", "verdict": "FIT", "height_px": 400, "capacity_px": 600}
        ]

        result = check_deck_spec_gates(
            page_plan, deck_spec, {}, {}, {}, layout_results=layout_results
        )

        self.assertTrue(any("차트류" in str(item) for item in result.violations))


if __name__ == "__main__":
    unittest.main()
