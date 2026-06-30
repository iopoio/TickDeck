import importlib.util
import pathlib
import unittest

import contract_checks as contract_checks_module
from contract_checks import (
    ContractViolation,
    validate_c1_proposition_dag,
    validate_c2_no_validation_metadata,
    validate_c3_trend_state_transition,
    validate_c4_citation_tracker,
    validate_c5_stage_order,
    validate_c6_content_authority,
    validate_all_contracts,
)

RENDER_DECK_PATH = pathlib.Path(__file__).resolve().parents[2] / "deck-harness" / "scripts" / "render_deck.py"
RENDER_DECK_SPEC = importlib.util.spec_from_file_location("render_deck", RENDER_DECK_PATH)
render_deck_module = importlib.util.module_from_spec(RENDER_DECK_SPEC)
RENDER_DECK_SPEC.loader.exec_module(render_deck_module)


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
    {"stage": "verifier", "artifact": "workspace/02_verified.json"},
    {"stage": "analyst", "artifact": "workspace/03_insights.json"},
    {"stage": "editorial-director", "artifact": "workspace/04_proposition_dag.json"},
    {"stage": "page-planner", "artifact": "workspace/05_page_plan.json"},
    {"stage": "designer", "artifact": "workspace/06_deck_spec.json"},
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

VALID_CONTENT_REGISTRY = {
    "sources": {
        "src_a": {"publisher": "Pew Research Center", "url": "https://example.com/pew"},
        "src_b": {"publisher": "IAB", "url": "https://example.com/iab"},
    },
    "metrics": {
        "metric_click_drop": {
            "value": "47",
            "unit": "%",
            "source_ids": ["src_a"],
            "scope": "Google searches with AI summaries",
        },
        "metric_measurement": {
            "value": "72",
            "unit": "%",
            "source_ids": ["src_b"],
            "scope": "cross-platform measurement adoption",
        },
    },
}

VALID_DECK_SPEC = {
    "pages": [
        {
            "page_id": "p01",
            "short_title": "Search Stops Sending Clicks",
            "layout": "hero_metric",
            "allowed_source_ids": ["src_a"],
            "allowed_metric_ids": ["metric_click_drop"],
            "content": [
                {"type": "headline", "text": "Search Stops Sending Clicks"},
                {"type": "metric", "metric_id": "metric_click_drop"},
                {"type": "citation", "src_id": "src_a"},
            ],
        },
        {
            "page_id": "p02",
            "short_title": "Measurement Moves To Owned Data",
            "layout": "stat_grid",
            "allowed_source_ids": ["src_b"],
            "allowed_metric_ids": ["metric_measurement"],
            "content": [
                {"type": "headline", "text": "Measurement Moves To Owned Data"},
                {"type": "metric", "metric_id": "metric_measurement"},
                {"type": "citation", "src_id": "src_b"},
            ],
        },
    ]
}

VALID_DECK_SPEC_WITH_EYEBROW = {
    "pages": [
        dict(
            VALID_DECK_SPEC["pages"][0],
            content=[
                {"type": "eyebrow", "text": "Chapter 1"},
                *VALID_DECK_SPEC["pages"][0]["content"],
            ],
        )
    ]
}

VALID_DECK_SPEC_WITH_VIZ = {
    "pages": [
        {
            "page_id": "p03",
            "short_title": "Search Stops Sending Clicks",
            "layout": "statement",
            "allowed_source_ids": ["src_a", "src_b"],
            "allowed_metric_ids": ["metric_click_drop", "metric_measurement"],
            "content": [
                {"type": "headline", "text": "Search Stops Sending Clicks"},
                {
                    "type": "viz",
                    "chart": "before_after",
                    "title": "Summary Collapse",
                    "series": [
                        {"label": "Baseline", "metric_id": "metric_measurement", "role": "baseline"},
                        {"label": "With Summary", "metric_id": "metric_click_drop", "role": "highlight"},
                    ],
                    "note": "Registry values only",
                },
            ],
        }
    ]
}

VALID_COVER_DECK_SPEC = {
    "pages": [
        {
            "page_id": "cover",
            "short_title": "표지",
            "layout": "cover",
            "allowed_source_ids": [],
            "allowed_metric_ids": [],
            "content": [
                {"type": "eyebrow", "text": "표지"},
                {"type": "headline", "text": "Market Shifts"},
                {"type": "summary", "text": "What changes when proof beats reach"},
            ],
        }
    ]
}

VALID_CLOSING_DECK_SPEC = {
    "theme": "tech",
    "pages": [
        {
            "page_id": "p15",
            "short_title": "전이를 가려내는 일이 분기점이다",
            "layout": "closing",
            "allowed_source_ids": ["src_a"],
            "allowed_metric_ids": [],
            "content": [
                {"type": "eyebrow", "text": "맺음 · 핵심 시사점"},
                {"type": "headline", "text": "전이를 가려내는 일이 분기점이다"},
                {
                    "type": "bullets",
                    "items": [
                        {"text": "도구 · 인프라 — 비가역적 투자에 올라탄다", "source_ids": ["src_a"]},
                        {"text": "자율화 — 통제된 파일럿으로 가둔다"},
                        {"text": "신흥 기술 — 관찰 대상으로 둔다"},
                    ],
                },
                {"type": "callout", "text": "승부는 어느 전이가 끝났느냐를 먼저 가려내는 데서 갈린다."},
                {"type": "citation", "src_id": "src_a"},
            ],
        }
    ],
}

VALID_RENDERED_HTML = """
<section class="slide">
  <h1>Search Stops Sending Clicks</h1>
  <span data-metric-id="metric_click_drop">47%</span>
  <cite data-src-id="src_a">Pew Research Center</cite>
  <span data-page-number>01 / 02</span>
</section>
"""


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
            {"stage": "designer", "artifact": "workspace/06_deck_spec.json"},
            {"stage": "page-planner", "artifact": "workspace/05_page_plan.json"},
        ]
        violations = validate_c5_stage_order(invalid)
        self.assertEqual(len(violations), 1)
        self.assertIn("designer", violations[0].message)

    def test_c6_accepts_deck_spec_references_inside_page_allowlists(self):
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, VALID_RENDERED_HTML), [])

    def test_c6_accepts_viz_blocks_with_metric_id_series(self):
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC_WITH_VIZ, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_accepts_closing_layout_in_supported_layout_enum(self):
        self.assertIn("closing", contract_checks_module.SUPPORTED_LAYOUTS)
        self.assertEqual(validate_c6_content_authority(VALID_CLOSING_DECK_SPEC, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_rejects_unsupported_layouts(self):
        invalid = {
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    layout="unknown_layout",
                )
            ]
        }
        violations = validate_c6_content_authority(invalid, VALID_CONTENT_REGISTRY, "")
        self.assertEqual(len(violations), 1)
        self.assertIn("unsupported layout: unknown_layout", violations[0].message)

    def test_c6_rejects_viz_raw_numbers_in_designer_fields(self):
        invalid = {
            "pages": [
                dict(
                    VALID_DECK_SPEC_WITH_VIZ["pages"][0],
                    content=[
                        {
                            "type": "viz",
                            "chart": "before_after",
                            "title": "CTR fell 47%",
                            "series": [
                                {"label": "Before 72%", "metric_id": "metric_measurement", "role": "baseline"},
                                {"label": "After", "metric_id": "metric_click_drop", "role": "highlight"},
                            ],
                            "note": "Gap is 25pp",
                        }
                    ],
                )
            ]
        }
        violations = validate_c6_content_authority(invalid, VALID_CONTENT_REGISTRY, "")
        self.assertTrue(any("raw number" in str(v) for v in violations))

    def test_c6_rejects_viz_metric_ids_outside_page_allowlist(self):
        invalid = {
            "pages": [
                dict(
                    VALID_DECK_SPEC_WITH_VIZ["pages"][0],
                    allowed_metric_ids=["metric_click_drop"],
                )
            ]
        }
        violations = validate_c6_content_authority(invalid, VALID_CONTENT_REGISTRY, "")
        self.assertTrue(any("metric_id not in page allowed_metric_ids: metric_measurement" in str(v) for v in violations))

    def test_c6_rejects_unsupported_content_block_types_before_render(self):
        invalid = {
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    content=[
                        {"type": "headline", "text": "Search Stops Sending Clicks"},
                        {"type": "sparkline", "metric_id": "metric_click_drop"},
                    ],
                )
            ]
        }
        violations = validate_c6_content_authority(invalid, VALID_CONTENT_REGISTRY, "")
        self.assertEqual(len(violations), 1)
        self.assertIn("unsupported content block type: sparkline", violations[0].message)

    def test_c6_rejects_unknown_or_disallowed_references(self):
        invalid = {
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    allowed_source_ids=["src_a"],
                    allowed_metric_ids=[],
                    content=[
                        {"type": "metric", "metric_id": "metric_click_drop"},
                        {"type": "citation", "src_id": "src_missing"},
                    ],
                )
            ]
        }
        violations = validate_c6_content_authority(invalid, VALID_CONTENT_REGISTRY, "")
        self.assertEqual(len(violations), 3)
        self.assertTrue(any("allowed_metric_ids" in str(v) for v in violations))
        self.assertTrue(any("unknown source id" in str(v) for v in violations))

    def test_c6_rejects_untagged_numbers_and_manual_source_labels_in_render(self):
        rendered = """
        <section class="slide">
          <h1>Manual Render</h1>
          <p>CTR fell 47% after AI summaries.</p>
          <p>출처: Pew Research Center</p>
        </section>
        """
        violations = validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, rendered)
        self.assertEqual(len(violations), 2)
        self.assertTrue(any("untagged number" in str(v) for v in violations))
        self.assertTrue(any("manual source label" in str(v) for v in violations))

    def test_validate_all_contracts_passes_valid_deck(self):
        self.assertEqual(validate_all_contracts(VALID_DECK), [])

    def test_validate_all_contracts_runs_c6_when_deck_spec_is_present(self):
        deck = dict(
            VALID_DECK,
            deck_spec=VALID_DECK_SPEC,
            content_registry=VALID_CONTENT_REGISTRY,
            rendered_html=VALID_RENDERED_HTML,
        )
        self.assertEqual(validate_all_contracts(deck), [])

    def test_render_deck_injects_metric_values_and_generated_citations(self):
        html = render_deck_module.render_deck(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, title="C6 Fixture")
        self.assertIn('data-metric-id="metric_click_drop"', html)
        self.assertIn("47%", html)
        self.assertIn('data-src-id="src_a"', html)
        self.assertIn("Pew Research Center", html)
        self.assertNotIn("출처:", html)
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_outputs_svg_for_each_supported_viz_chart(self):
        for chart in ("before_after", "dumbbell", "flow", "big_number", "gap_map", "shift"):
            with self.subTest(chart=chart):
                spec = {
                    "pages": [
                        dict(
                            VALID_DECK_SPEC_WITH_VIZ["pages"][0],
                            content=[
                                dict(
                                    VALID_DECK_SPEC_WITH_VIZ["pages"][0]["content"][1],
                                    chart=chart,
                                )
                            ],
                        )
                    ]
                }
                html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Viz Fixture")
                self.assertIn("<svg", html)
                self.assertIn('data-metric-id="metric_click_drop"', html)
                self.assertIn("47%", html)
                self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_cover_hides_cover_role_and_uses_light_background(self):
        html = render_deck_module.render_deck(VALID_COVER_DECK_SPEC, VALID_CONTENT_REGISTRY, title="Cover Fixture")
        rendered_body = html.split("</style>", 1)[1]
        self.assertIn("Market Shifts", html)
        self.assertNotIn("표지", rendered_body)
        self.assertNotIn('<footer class="slide-foot">', html)
        self.assertNotIn("background: #111", html)
        self.assertIn("axis-strip", html)

    def test_render_deck_keeps_footer_in_flow_so_page_number_stays_visible(self):
        # 푸터를 정상 흐름(flex 아이템)에 두고 본문은 overflow:hidden로 잘리게 해서
        # 과밀 슬라이드에서도 본문이 푸터/페이지번호 위로 겹치지 못하게 한다(겹침 버그의 근본 차단).
        html = render_deck_module.render_deck(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, title="Footer Fixture")
        self.assertIn(".slide-foot {", html)
        self.assertIn("flex: 0 0 auto;", html)
        self.assertIn("overflow: hidden;", html)
        self.assertIn('class="page-number" data-page-number>01 / 02</span>', html)

    def test_render_deck_outputs_closing_layout(self):
        html = render_deck_module.render_deck(VALID_CLOSING_DECK_SPEC, VALID_CONTENT_REGISTRY, title="Closing Fixture")
        self.assertIn("layout-closing", html)
        self.assertIn("closing-body", html)
        self.assertIn("closing-point", html)
        self.assertIn("closing-label", html)
        self.assertIn("도구 · 인프라", html)
        self.assertIn("closing-callout", html)
        self.assertIn("어느 전이가 끝났느냐", html)
        self.assertIn('class="page-number" data-page-number>01 / 01</span>', html)
        self.assertEqual(validate_c6_content_authority(VALID_CLOSING_DECK_SPEC, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_supports_eyebrow_blocks_as_section_labels(self):
        html = render_deck_module.render_deck(VALID_DECK_SPEC_WITH_EYEBROW, VALID_CONTENT_REGISTRY, title="Eyebrow Fixture")
        self.assertIn('<div class="eyebrow">Chapter 1</div>', html)
        self.assertNotIn("unsupported content block type: eyebrow", html)
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC_WITH_EYEBROW, VALID_CONTENT_REGISTRY, html), [])

    def test_renderer_and_contracts_share_supported_content_block_types(self):
        self.assertTrue(hasattr(contract_checks_module, "SUPPORTED_CONTENT_BLOCK_TYPES"))
        self.assertIs(
            render_deck_module.SUPPORTED_CONTENT_BLOCK_TYPES,
            contract_checks_module.SUPPORTED_CONTENT_BLOCK_TYPES,
        )
        self.assertIn("eyebrow", contract_checks_module.SUPPORTED_CONTENT_BLOCK_TYPES)
        self.assertIn("viz", contract_checks_module.SUPPORTED_CONTENT_BLOCK_TYPES)

    def test_validate_all_contracts_can_raise(self):
        broken = dict(VALID_DECK, rendered_pages=[{"title": "신뢰도 강등", "body": "본문"}])
        with self.assertRaises(ContractViolation):
            validate_all_contracts(broken, raise_on_error=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
