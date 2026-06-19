import json
import os
import sys
import unittest
from pathlib import Path


AXIS1_ROOT = Path(os.environ.get(
    "AXIS1_ROOT",
    "/Users/hwa/Projects/Automation/TickDeck/v3/axis1_research",
))
sys.path.insert(0, str(AXIS1_ROOT))

import glossary
import numeric_audit


class Axis1ResearchTests(unittest.TestCase):
    def test_extract_numbers_excludes_url_list_and_bare_decimal_noise(self):
        report = (
            "1. 핵심 수치\n"
            "출처: https://example.com/market-101700/report\n"
            "CAGR 12.5%, 성장률 52.8%, 매출 $84.17B.\n"
            "근거 없는 bare decimal 3.3은 검증 수치가 아니다."
        )

        numbers = numeric_audit.extract_numbers(report)

        self.assertNotIn("1.", numbers)
        self.assertNotIn("101700", numbers)
        self.assertNotIn("12.5", numbers)
        self.assertNotIn("52.8", numbers)
        self.assertNotIn("3.3", numbers)
        self.assertIn("CAGR 12.5%", numbers)
        self.assertIn("52.8%", numbers)
        self.assertIn("$84.17B", numbers)

    def test_glossary_keeps_only_terms_with_corpus_source(self):
        result = json.loads(
            (AXIS1_ROOT / "runs/20260618_1749_2026년_글로벌_AI_반도체_시장_전망.json")
            .read_text(encoding="utf-8")
        )
        corpus = json.loads(
            (AXIS1_ROOT / "runs/20260618_1749_2026년_글로벌_AI_반도체_시장_전망_corpus.json")
            .read_text(encoding="utf-8")
        )

        terms = glossary.extract_glossary(
            result["leader"]["final"],
            corpus,
            glossary.infer_domain(result["topic"]),
            result["topic"],
        )["terms"]
        term_names = {item["term"] for item in terms}

        self.assertIn("AI", term_names)
        self.assertIn("NVIDIA", term_names)
        self.assertIn("AMD", term_names)
        self.assertNotIn("종합", term_names)
        self.assertNotIn("따르면", term_names)
        self.assertTrue(all(item["source_url"].startswith("http") for item in terms))


if __name__ == "__main__":
    unittest.main()
