from __future__ import annotations

import json
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_DIR = Path(__file__).resolve().parent
CONTRACT_DIR = SCRIPT_DIR.parents[1] / "harness-contracts" / "scripts"
CALIBRATION_DIR = SCRIPT_DIR.parent / "calibration"
for path in (SCRIPT_DIR, CONTRACT_DIR, CALIBRATION_DIR):
    sys.path.insert(0, str(path))

import spec_gate  # noqa: E402


class SpecGateUnitTests(unittest.TestCase):
    def test_missing_runtime_key_is_blocked_on_measurement(self):
        spec = {
            "theme": "light",
            "meta": {"page_chrome": "standard"},
            "pages": [{"page_id": "p01", "layout": "statement", "content": []}],
        }
        calibration = {
            "schema_version": 1,
            "key_dimensions": list(spec_gate.KEY_DIMENSIONS),
            "entries": [],
        }

        with (
            patch.object(spec_gate, "renderer_struct_hash", return_value="renderer"),
            patch.object(spec_gate, "css_hash", return_value="css"),
            patch.object(spec_gate, "font_build_hash", return_value="font"),
        ):
            results = spec_gate._layout_results(spec, {}, calibration)

        verdict, details = spec_gate.classify_layout_results(results)
        self.assertEqual(verdict, spec_gate.Verdict.BLOCKED_ON_MEASUREMENT)
        self.assertIn("width_class", details[0])

    def test_malformed_calibration_document_is_rejected(self):
        spec = {
            "theme": "light",
            "meta": {
                "page_chrome": "standard",
                "calibration_runtime": {"width_class": "wide", "browser_major": "120"},
            },
            "pages": [{"page_id": "p01", "layout": "statement", "content": []}],
        }

        with (
            patch.object(spec_gate, "renderer_struct_hash", return_value="renderer"),
            patch.object(spec_gate, "css_hash", return_value="css"),
            patch.object(spec_gate, "font_build_hash", return_value="font"),
        ):
            results = spec_gate._layout_results(spec, {}, {"schema_version": 999})

        verdict, details = spec_gate.classify_layout_results(results)
        self.assertEqual(verdict, spec_gate.Verdict.REJECTED)
        self.assertIn("unsupported calibration schema_version", details[0])

    def test_layout_budget_input_error_is_rejected(self):
        spec = {
            "theme": "light",
            "meta": {
                "page_chrome": "standard",
                "calibration_runtime": {"width_class": "wide", "browser_major": "120"},
            },
            "pages": [{"page_id": "p01", "layout": "statement", "content": []}],
        }
        entry = {"key": {}, "provenance": {"status": "measured"}, "values": {}}

        with (
            patch.object(spec_gate, "renderer_struct_hash", return_value="renderer"),
            patch.object(spec_gate, "css_hash", return_value="css"),
            patch.object(spec_gate, "font_build_hash", return_value="font"),
            patch.object(spec_gate, "resolve_entry", return_value=entry),
            patch.object(
                spec_gate.layout_budget,
                "evaluate_layout",
                side_effect=spec_gate.layout_budget.LayoutBudgetInputError("bad registry"),
            ),
        ):
            results = spec_gate._layout_results(spec, {}, {})

        verdict, details = spec_gate.classify_layout_results(results)
        self.assertEqual(verdict, spec_gate.Verdict.REJECTED)
        self.assertIn("bad registry", details[0])

    def test_unexpected_layout_error_is_not_hidden(self):
        spec = {
            "theme": "light",
            "meta": {
                "page_chrome": "standard",
                "calibration_runtime": {"width_class": "wide", "browser_major": "120"},
            },
            "pages": [{"page_id": "p01", "layout": "statement", "content": []}],
        }

        with (
            patch.object(spec_gate, "renderer_struct_hash", return_value="renderer"),
            patch.object(spec_gate, "css_hash", return_value="css"),
            patch.object(spec_gate, "font_build_hash", return_value="font"),
            patch.object(spec_gate, "resolve_entry", side_effect=RuntimeError("unexpected bug")),
        ):
            with self.assertRaisesRegex(RuntimeError, "unexpected bug"):
                spec_gate._layout_results(spec, {}, {})

    def test_measurement_block_stops_before_later_gates_and_writes_receipt(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            draft = run_dir / "06_deck_spec.draft.json"
            plan = run_dir / "05_page_plan.json"
            registry = run_dir / "02_verified.json"
            calibration = run_dir / "calibration.json"
            draft.write_text(json.dumps({
                "theme": "light",
                "meta": {"page_chrome": "standard"},
                "pages": [{"page_id": "p01", "layout": "statement", "content": []}],
            }), encoding="utf-8")
            plan.write_text('{"pages":[]}', encoding="utf-8")
            registry.write_text('{}', encoding="utf-8")
            calibration.write_text('{}', encoding="utf-8")
            blocked = spec_gate.layout_budget.PageBudget(
                "p01", "RENDER_MEASURE_REQUIRED", None, None, None, None, ("missing width_class",)
            )

            with (
                patch.object(spec_gate, "_layout_results", return_value=(blocked,)),
                patch.object(spec_gate, "check_c13_role_duplication") as c13,
                patch.object(spec_gate, "renderer_struct_hash", return_value="renderer"),
                patch.object(spec_gate, "css_hash", return_value="css"),
                patch.object(spec_gate, "font_build_hash", return_value="font"),
            ):
                verdict, results, action = spec_gate.run_gate(
                    run_dir, draft, plan, registry, calibration
                )

            self.assertEqual(verdict, spec_gate.Verdict.BLOCKED_ON_MEASUREMENT)
            self.assertEqual([result.gate for result in results], [1, 2, 3])
            self.assertIn("receipt=", action)
            c13.assert_not_called()

    def test_automatic_fields_are_replaced_and_warned(self):
        spec = {
            "pages": [
                {"page_id": "old", "layout": "divider", "part_index": 9, "part_count": 9, "content": []},
                {"page_id": "old2", "layout": "index", "content": [{"type": "list", "items": ["손작성"]}]},
                {"page_id": "old3", "layout": "divider", "content": []},
            ]
        }

        warnings = spec_gate.apply_automatic_values(spec)

        self.assertEqual([page["page_id"] for page in spec["pages"]], ["p01", "p02", "p03"])
        self.assertEqual(spec["pages"][0]["part_index"], 1)
        self.assertEqual(spec["pages"][2]["part_index"], 2)
        self.assertEqual(spec["pages"][0]["part_count"], 2)
        self.assertEqual(spec["pages"][2]["part_count"], 2)
        self.assertEqual(spec["pages"][1]["content"], [])
        self.assertGreaterEqual(len(warnings), 4)

    def test_missing_visual_intent_is_blocked_upstream_not_rejected(self):
        plan = {"pages": [{"page_id": "plan-1"}]}
        spec = {"pages": [{"page_id": "p01", "plan_id": "plan-1", "layout": "statement", "content": []}]}

        verdict, details = spec_gate.classify_visual_intent(plan, spec)

        self.assertEqual(verdict, spec_gate.Verdict.BLOCKED_ON_UPSTREAM)
        self.assertIn("visual_intent", details[0])

    def test_unmeasured_layout_is_blocked_on_measurement_not_rejected(self):
        result = type("Budget", (), {"page_id": "p01", "verdict": "RENDER_MEASURE_REQUIRED", "reasons": ("unmeasured",)})()

        verdict, details = spec_gate.classify_layout_results([result])

        self.assertEqual(verdict, spec_gate.Verdict.BLOCKED_ON_MEASUREMENT)
        self.assertIn("unmeasured", details[0])

    def test_promotion_rolls_back_both_files_when_second_replace_fails(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            canonical = run_dir / "06_deck_spec.json"
            receipt = run_dir / "06_deck_spec.receipt.json"
            canonical.write_text('{"old":true}', encoding="utf-8")
            receipt.write_text('{"old_receipt":true}', encoding="utf-8")
            real_replace = spec_gate.os.replace
            calls = 0

            def fail_second(source, target):
                nonlocal calls
                calls += 1
                if calls == 4:
                    raise OSError("injected receipt replace failure")
                return real_replace(source, target)

            with patch.object(spec_gate.os, "replace", side_effect=fail_second):
                with self.assertRaises(OSError):
                    spec_gate.promote_pair(run_dir, b'{"new":true}', b'{"new_receipt":true}')

            self.assertEqual(canonical.read_text(encoding="utf-8"), '{"old":true}')
            self.assertEqual(receipt.read_text(encoding="utf-8"), '{"old_receipt":true}')

    def test_toctou_change_is_rejected_before_promotion(self):
        with tempfile.TemporaryDirectory() as raw:
            draft = Path(raw) / "06_deck_spec.draft.json"
            checked = b'{"pages":[]}'
            draft.write_bytes(checked)
            expected = spec_gate.sha256_bytes(checked)
            draft.write_bytes(b'{"pages":[{"changed":true}]}')

            with self.assertRaises(spec_gate.DraftChangedError):
                spec_gate.assert_draft_unchanged(draft, expected)

    def test_stage7_skips_c14_c15_already_owned_by_spec_gate(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw)
            for name in (
                "00_intake.json", "01_evidence_pool.json", "02_verified.json",
                "03_insights.json", "04_dag.json", "05_page_plan.json",
                "06_deck_spec.draft.json",
            ):
                (run_dir / name).write_text("{}", encoding="utf-8")
            with (
                patch.object(spec_gate.run_contracts, "validate_all_contracts", return_value=[]),
                patch.object(spec_gate.run_contracts, "check_c10_collection_evidence", return_value=[]),
                patch.object(spec_gate.run_contracts, "check_c11_source_coverage", return_value=[]),
                patch.object(spec_gate.run_contracts, "check_c14_viz_intent_preserved") as c14,
                patch.object(spec_gate.run_contracts, "check_c15_page_count_ceiling") as c15,
            ):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    exit_code = spec_gate.run_contracts.main([
                        str(run_dir), "--spec", str(run_dir / "06_deck_spec.draft.json"),
                        "--plan", str(run_dir / "05_page_plan.json"), "--skip-spec-gates",
                    ])

        self.assertEqual(exit_code, 0)
        self.assertNotIn("C14", output.getvalue().split("위반 0건")[-2].split("→")[-1])
        self.assertNotIn("C15", output.getvalue().split("위반 0건")[-2].split("→")[-1])
        c14.assert_not_called()
        c15.assert_not_called()


if __name__ == "__main__":
    unittest.main()
