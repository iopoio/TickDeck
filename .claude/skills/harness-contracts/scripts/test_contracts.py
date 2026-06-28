import unittest

from contract_checks import (
    ContractViolation,
    validate_c1_proposition_dag,
    validate_c2_no_validation_metadata,
    validate_c3_trend_state_transition,
    validate_c4_citation_tracker,
    validate_c5_stage_order,
    validate_all_contracts,
)


VALID_DAG = {
    "nodes": [
        {"id": "thesis", "type": "thesis", "text": "AI execution shifts advantage toward proof assets"},
        {"id": "p1", "type": "claim", "text": "Discovery is moving from search to answer engines"},
        {"id": "p2", "type": "claim", "text": "Trust becomes a scarce asset"},
    ],
    "edges": [
        {"from": "thesis", "to": "p1"},
        {"from": "thesis", "to": "p2"},
    ],
}

VALID_INSIGHTS = [
    {
        "id": "i1",
        "claim": "Discovery moves from search pages to answer engines",
        "evidence_ids": ["src_a", "src_b"],
        "derivation_type": "synthesis",
        "counter_signal": "SEO spend remains resilient in some categories",
        "narrative_reason": "distribution control is shifting",
        "source_overlap_score": 0.24,
        "from_state": "keyword-led search",
        "to_state": "answer-led discovery",
        "mechanism": "agentic summaries collapse the funnel",
    },
    {
        "id": "i2",
        "claim": "Trust assets become more valuable as synthetic content rises",
        "evidence_ids": ["src_c", "src_d"],
        "derivation_type": "cross_source_inference",
        "counter_signal": "some low-consideration categories remain price-led",
        "narrative_reason": "synthetic abundance raises proof requirements",
        "source_overlap_score": 0.31,
        "from_state": "brand story accepted at face value",
        "to_state": "proof-backed credibility demanded",
        "mechanism": "audiences discount undifferentiated AI content",
    },
]

VALID_STAGE_LOG = [
    {"stage": "intake-director", "artifact": "workspace/00_intake.json"},
    {"stage": "collector", "artifact": "workspace/01_evidence_pool.json"},
    {"stage": "verifier", "artifact": "workspace/02_verified_evidence.json"},
    {"stage": "analyst", "artifact": "workspace/03_insights.json"},
    {"stage": "editorial-director", "artifact": "workspace/04_proposition_dag.json"},
    {"stage": "page-planner", "artifact": "workspace/05_page_plan.json"},
    {"stage": "designer", "artifact": "workspace/06_render.html"},
    {"stage": "qa-reviewer", "artifact": "workspace/07_qa.json"},
]

VALID_DECK = {
    "genre": "trend-report",
    "proposition_dag": VALID_DAG,
    "insights": VALID_INSIGHTS,
    "rendered_pages": [
        {"title": "Discovery Moves From Search To Answers", "body": "Answer engines compress comparison into one structured response."},
        {"title": "Trust Becomes The Scarce Asset", "body": "Proof-backed assets matter when synthetic content is cheap."},
    ],
    "stage_log": VALID_STAGE_LOG,
}


class HarnessContractTests(unittest.TestCase):
    def test_c1_accepts_connected_dag(self):
        self.assertEqual(validate_c1_proposition_dag(VALID_DAG), [])

    def test_c1_rejects_orphan_claim_nodes(self):
        broken = {
            "nodes": VALID_DAG["nodes"] + [{"id": "orphan", "type": "claim", "text": "route=all benchmark bucket"}],
            "edges": VALID_DAG["edges"],
        }
        violations = validate_c1_proposition_dag(broken)
        self.assertTrue(any("orphan" in str(v) for v in violations))

    def test_c2_rejects_validation_metadata_in_content(self):
        pages = [{"title": "단일출처 강등", "body": "정성근거로만 유지한 슬라이드"}]
        violations = validate_c2_no_validation_metadata(pages)
        self.assertEqual(len(violations), 1)
        self.assertIn("validation metadata", violations[0].message)

    def test_c3_requires_state_transition_for_trend_insights(self):
        invalid = [dict(VALID_INSIGHTS[0], mechanism="")]
        violations = validate_c3_trend_state_transition("trend-report", invalid)
        self.assertEqual(len(violations), 1)
        self.assertIn("from_state/to_state/mechanism", violations[0].message)

    def test_c4_requires_multi_source_low_overlap_insights(self):
        invalid = [dict(VALID_INSIGHTS[0], evidence_ids=["src_a"], source_overlap_score=0.12)]
        violations = validate_c4_citation_tracker(invalid)
        self.assertEqual(len(violations), 1)
        self.assertIn("evidence_ids", violations[0].message)

    def test_c4_rejects_high_source_overlap(self):
        invalid = [dict(VALID_INSIGHTS[0], evidence_ids=["src_a", "src_b"], source_overlap_score=0.91)]
        violations = validate_c4_citation_tracker(invalid)
        self.assertEqual(len(violations), 1)
        self.assertIn("source_overlap_score", violations[0].message)

    def test_c5_accepts_pipeline_order(self):
        self.assertEqual(validate_c5_stage_order(VALID_STAGE_LOG), [])

    def test_c5_rejects_designer_before_page_plan(self):
        invalid = [
            {"stage": "intake-director", "artifact": "workspace/00_intake.json"},
            {"stage": "designer", "artifact": "workspace/06_render.html"},
            {"stage": "page-planner", "artifact": "workspace/05_page_plan.json"},
        ]
        violations = validate_c5_stage_order(invalid)
        self.assertEqual(len(violations), 1)
        self.assertIn("designer", violations[0].message)

    def test_validate_all_contracts_passes_valid_deck(self):
        self.assertEqual(validate_all_contracts(VALID_DECK), [])

    def test_validate_all_contracts_can_raise(self):
        broken = dict(VALID_DECK, rendered_pages=[{"title": "신뢰도 강등", "body": "본문"}])
        with self.assertRaises(ContractViolation):
            validate_all_contracts(broken, raise_on_error=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
