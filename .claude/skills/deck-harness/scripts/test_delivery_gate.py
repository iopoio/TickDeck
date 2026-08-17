from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
DELIVERY_GATE = SCRIPT_DIR / "delivery_gate.py"


def _load_delivery_gate():
    spec = importlib.util.spec_from_file_location("delivery_gate", DELIVERY_GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DeliveryGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)
        for name, content in (
            ("06_deck_spec.json", "{}"),
            ("06_deck_spec.receipt.json", '{"verdict":"PASS"}'),
            ("02_verified.json", "{}"),
            ("deck.html", "<html></html>"),
            ("deck.pdf", "%PDF"),
        ):
            (self.run_dir / name).write_text(content, encoding="utf-8")
        (self.run_dir / "07_qa_report.json").write_text(json.dumps({
            "visual_review": {
                "reviewer": "본부 클차장",
                "reviewed_at": "2026-08-17T14:30:00+09:00",
                "montage_path": "07_visual_montage.png",
                "scope": "all_pages",
            }
        }), encoding="utf-8")
        (self.run_dir / "07_visual_montage.png").write_bytes(b"png")

    def tearDown(self):
        self.temp.cleanup()

    def _runner(self, failed_check: str | None = None, fonts: str | None = None):
        font_output = fonts or "ABCDEE+Pretendard CID TrueType Identity-H yes yes yes 1 0"

        def run(command, **kwargs):
            check = kwargs.pop("delivery_check", None)
            if check == failed_check:
                return subprocess.CompletedProcess(command, 1, stdout="", stderr=f"{check} failed")
            if check == "pdf_text_layer":
                return subprocess.CompletedProcess(command, 0, stdout=font_output, stderr="")
            output = {
                "fit_overflow": "FIT_OK: 세로 오버플로 없음.",
                "ink_distribution": "INK_OK: median 10.00%",
            }.get(check, "PASS")
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")

        return run

    def test_each_existing_check_failure_is_recorded(self):
        gate = _load_delivery_gate()
        for check in ("receipt", "run_contracts", "fit_overflow", "ink_distribution", "deck_intent"):
            with self.subTest(check=check):
                report = gate.evaluate(self.run_dir, runner=self._runner(failed_check=check))
                result = next(item for item in report["results"] if item["id"] == check)
                self.assertEqual(result["verdict"], "FAIL")
                self.assertEqual(report["verdict"], "FAIL")

    def test_unattested_artifact_fails_receipt_check(self):
        gate = _load_delivery_gate()
        (self.run_dir / "debug.unattested.pdf").write_bytes(b"%PDF")

        report = gate.evaluate(self.run_dir, runner=self._runner())

        result = next(item for item in report["results"] if item["id"] == "receipt")
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("unattested", result["detail"])

    def test_zero_embedded_fonts_fails_pdf_text_layer(self):
        gate = _load_delivery_gate()
        header_only = "name type encoding emb sub uni object ID\n--------------------------------"

        report = gate.evaluate(self.run_dir, runner=self._runner(fonts=header_only))

        result = next(item for item in report["results"] if item["id"] == "pdf_text_layer")
        self.assertEqual(result["verdict"], "FAIL")

    def test_missing_full_visual_review_fails(self):
        gate = _load_delivery_gate()
        (self.run_dir / "07_qa_report.json").write_text(
            '{"visual_review":{"reviewer":"본부 클차장"}}', encoding="utf-8"
        )

        report = gate.evaluate(self.run_dir, runner=self._runner())

        result = next(item for item in report["results"] if item["id"] == "visual_review")
        self.assertEqual(result["verdict"], "FAIL")

    def test_all_seven_results_are_written_and_failure_exits_one(self):
        gate = _load_delivery_gate()
        output = self.run_dir / "delivery_report.json"
        with mock.patch.object(gate.subprocess, "run", side_effect=self._runner(failed_check="ink_distribution")):
            exit_code = gate.main([str(self.run_dir), "--output", str(output)])

        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 1)
        self.assertEqual(len(report["results"]), 7)
        self.assertEqual(report["verdict"], "FAIL")

    def test_all_seven_pass_and_exit_zero(self):
        gate = _load_delivery_gate()
        output = self.run_dir / "delivery_report.json"
        with mock.patch.object(gate.subprocess, "run", side_effect=self._runner()):
            exit_code = gate.main([str(self.run_dir), "--output", str(output)])

        report = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(report["results"]), 7)
        self.assertTrue(all(item["verdict"] == "PASS" for item in report["results"]))

    def test_ink_failure_does_not_relabel_fit_as_overflow(self):
        gate = _load_delivery_gate()

        report = gate.evaluate(self.run_dir, runner=self._runner(failed_check="ink_distribution"))

        fit = next(item for item in report["results"] if item["id"] == "fit_overflow")
        ink = next(item for item in report["results"] if item["id"] == "ink_distribution")
        self.assertEqual(fit["verdict"], "PASS")
        self.assertEqual(ink["verdict"], "FAIL")

    def test_visual_review_rejects_montage_outside_run_dir(self):
        gate = _load_delivery_gate()
        outside = Path(self.temp.name).parent / "outside-montage.png"
        outside.write_bytes(b"png")
        self.addCleanup(outside.unlink, missing_ok=True)
        (self.run_dir / "07_qa_report.json").write_text(json.dumps({
            "visual_review": {
                "reviewer": "본부 클차장",
                "reviewed_at": "2026-08-17T14:30:00+09:00",
                "montage_path": str(outside),
                "scope": "all_pages",
            }
        }), encoding="utf-8")

        report = gate.evaluate(self.run_dir, runner=self._runner())

        result = next(item for item in report["results"] if item["id"] == "visual_review")
        self.assertEqual(result["verdict"], "FAIL")


if __name__ == "__main__":
    unittest.main()
