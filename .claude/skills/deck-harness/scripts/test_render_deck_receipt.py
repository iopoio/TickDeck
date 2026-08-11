from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CALIBRATION_DIR = SCRIPT_DIR.parent / "calibration"
for path in (SCRIPT_DIR, CALIBRATION_DIR):
    sys.path.insert(0, str(path))

from predictor import css_hash, renderer_struct_hash, sha256_file  # noqa: E402


RENDERER = SCRIPT_DIR / "render_deck.py"


class RenderDeckReceiptCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.run_dir = Path(self.temp.name)
        self.spec = self.run_dir / "06_deck_spec.json"
        self.registry = self.run_dir / "02_verified.json"
        self.output = self.run_dir / "deck.html"
        self.spec.write_text(json.dumps({
            "theme": "editorial",
            "pages": [{
                "page_id": "p01",
                "short_title": "Probe",
                "layout": "statement",
                "content": [{"type": "headline", "text": "receipt probe"}],
            }],
        }), encoding="utf-8")
        self.registry.write_text(
            '{"sources":{"S1":{"title":"probe"}},'
            '"metrics":{"M1":{"display":"1"}}}',
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def _write_receipt(self, **overrides: str) -> Path:
        receipt = {
            "spec_sha256": sha256_file(self.spec),
            "registry_sha256": sha256_file(self.registry),
            "renderer_struct_hash": renderer_struct_hash(),
            "css_hash": css_hash("editorial"),
            "verdict": "PASS",
        }
        receipt.update(overrides)
        path = self.run_dir / "06_deck_spec.receipt.json"
        path.write_text(json.dumps(receipt), encoding="utf-8")
        return path

    def _run(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RENDERER), str(self.spec), str(self.registry),
             "-o", str(self.output), "--html-only", *extra],
            capture_output=True,
            text=True,
        )

    def test_valid_receipt_renders(self):
        self._write_receipt()

        result = self._run()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.output.exists())

    def test_missing_receipt_refuses_without_output(self):
        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertIn("receipt", result.stderr.lower())

    def test_changed_spec_refuses_without_output(self):
        self._write_receipt()
        self.spec.write_bytes(self.spec.read_bytes() + b" ")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertIn("spec_sha256", result.stderr)

    def test_changed_receipt_hash_refuses_without_output(self):
        self._write_receipt(registry_sha256="0" * 64)

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertIn("registry_sha256", result.stderr)

    def test_theme_override_with_different_css_refuses_without_output(self):
        self._write_receipt()

        result = self._run("--theme", "cobalt")

        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.output.exists())
        self.assertIn("css_hash", result.stderr)

    def test_unattested_renders_with_html_marker(self):
        result = self._run("--unattested")

        self.assertEqual(result.returncode, 0, result.stderr)
        html = self.output.read_text(encoding="utf-8")
        self.assertIn('<meta name="tickdeck-attestation" content="UNATTESTED">', html)


if __name__ == "__main__":
    unittest.main()
