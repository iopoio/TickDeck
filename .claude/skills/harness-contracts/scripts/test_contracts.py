import importlib.util
import json
import os
import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

import contract_checks as contract_checks_module
from contract_checks import (
    ContractViolation,
    validate_c1_proposition_dag,
    validate_c2_no_validation_metadata,
    validate_c3_trend_state_transition,
    validate_c4_citation_tracker,
    validate_c5_stage_order,
    validate_c6_content_authority,
    check_c8_genre_artifacts,
    check_c9_final_review,
    validate_all_contracts,
)

RENDER_DECK_PATH = pathlib.Path(__file__).resolve().parents[2] / "deck-harness" / "scripts" / "render_deck.py"
RENDER_DECK_SPEC = importlib.util.spec_from_file_location("render_deck", RENDER_DECK_PATH)
render_deck_module = importlib.util.module_from_spec(RENDER_DECK_SPEC)
RENDER_DECK_SPEC.loader.exec_module(render_deck_module)

EXTERNAL_REVIEW_PATH = pathlib.Path(__file__).resolve().parents[2] / "deck-harness" / "scripts" / "external_review.py"
EXTERNAL_REVIEW_SPEC = importlib.util.spec_from_file_location("external_review", EXTERNAL_REVIEW_PATH)
external_review_module = importlib.util.module_from_spec(EXTERNAL_REVIEW_SPEC)
EXTERNAL_REVIEW_SPEC.loader.exec_module(external_review_module)

PPTX_EXPORT_PATH = pathlib.Path(__file__).resolve().parents[2] / "deck-harness" / "scripts" / "pptx_export.py"
PPTX_EXPORT_SPEC = importlib.util.spec_from_file_location("pptx_export", PPTX_EXPORT_PATH)
pptx_export_module = importlib.util.module_from_spec(PPTX_EXPORT_SPEC)
PPTX_EXPORT_SPEC.loader.exec_module(pptx_export_module)

QA_LINT_PATH = pathlib.Path(__file__).resolve().parents[2] / "deck-harness" / "scripts" / "qa_lint.py"
QA_LINT_SPEC = importlib.util.spec_from_file_location("qa_lint", QA_LINT_PATH)
qa_lint_module = importlib.util.module_from_spec(QA_LINT_SPEC)
QA_LINT_SPEC.loader.exec_module(qa_lint_module)

RUN_CONTRACTS_PATH = pathlib.Path(__file__).resolve().parent / "run_contracts.py"
RUN_CONTRACTS_SPEC = importlib.util.spec_from_file_location("run_contracts", RUN_CONTRACTS_PATH)
run_contracts_module = importlib.util.module_from_spec(RUN_CONTRACTS_SPEC)
RUN_CONTRACTS_SPEC.loader.exec_module(run_contracts_module)

RUN_DECK_SH = pathlib.Path(__file__).resolve().parents[2] / "deck-harness" / "scripts" / "run_deck.sh"


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
        appendix_badge_html = """
        <section class="slide layout-source_appendix">
          <div class="verified-badge">모든 수치 출처 연결 검증 · 출처 2곳</div>
        </section>
        """
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, appendix_badge_html), [])

    def test_c6_accepts_metric_registry_sources_without_page_source_allowlist(self):
        spec = {
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    allowed_source_ids=[],
                    allowed_metric_ids=["metric_click_drop"],
                    content=[
                        {"type": "metric", "metric_id": "metric_click_drop"},
                        {"type": "citation", "src_id": "src_a"},
                    ],
                )
            ]
        }
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_still_rejects_disallowed_metric_unknown_source_and_untagged_number(self):
        cases = {
            "disallowed_metric": (
                {
                    "pages": [
                        dict(
                            VALID_DECK_SPEC["pages"][0],
                            allowed_metric_ids=[],
                            content=[{"type": "metric", "metric_id": "metric_click_drop"}],
                        )
                    ]
                },
                "",
                "metric_id not in page allowed_metric_ids: metric_click_drop",
            ),
            "unknown_source": (
                {
                    "pages": [
                        dict(
                            VALID_DECK_SPEC["pages"][0],
                            content=[{"type": "citation", "src_id": "src_missing"}],
                        )
                    ]
                },
                "",
                "unknown source id referenced: src_missing",
            ),
            "untagged_number": (
                VALID_DECK_SPEC,
                "<section><p>CTR fell 999% after AI summaries.</p></section>",
                "untagged number in rendered output",
            ),
        }
        for name, (spec, rendered_html, expected) in cases.items():
            with self.subTest(name=name):
                violations = validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, rendered_html)
                self.assertTrue(any(expected in str(v) for v in violations))

    def test_c6_accepts_viz_blocks_with_metric_id_series(self):
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC_WITH_VIZ, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_accepts_text_table_without_numeric_cells(self):
        spec = {
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    layout="statement",
                    allowed_source_ids=[],
                    allowed_metric_ids=[],
                    content=[
                        {"type": "headline", "text": "Player Comparison"},
                        {
                            "type": "text_table",
                            "title": "브랜드 포지션",
                            "columns": ["브랜드", "주력 제품", "가격대", "포지션", "채널"],
                            "rows": [
                                ["CLO", "넥앤프로 에어코즈 메디소닉", "중가", "헬스 뷰티 멀티부위", "자사몰 SNS 없음"],
                                ["TheraFace", "얼굴 케어 기기", "프리미엄", "뷰티 테크", "자사몰 리테일"],
                            ],
                            "highlight_row": 0,
                        },
                    ],
                )
            ]
        }
        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Text Table Fixture")
        self.assertIn("<table", html)
        self.assertIn("text-table", html)
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html), [])

    def test_c6_rejects_text_table_numeric_cells_as_untagged_numbers(self):
        spec = {
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    layout="statement",
                    allowed_source_ids=[],
                    allowed_metric_ids=[],
                    content=[
                        {"type": "headline", "text": "Player Comparison"},
                        {
                            "type": "text_table",
                            "columns": ["브랜드", "주력 제품", "가격대", "포지션"],
                            "rows": [["CLO", "넥앤프로", "중가", "인지도 999%"]],
                        },
                    ],
                )
            ]
        }
        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Text Table Numeric Fixture")
        violations = validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html)
        self.assertTrue(any("untagged number in rendered output" in str(v) for v in violations))

    def test_c6_backed_number_in_body_passes(self):
        registry = {
            "sources": VALID_CONTENT_REGISTRY["sources"],
            "metrics": {
                **VALID_CONTENT_REGISTRY["metrics"],
                "metric_launch_sales": {
                    "value": "300",
                    "unit": "만개",
                    "source_ids": ["src_a"],
                }
            },
        }
        rendered = "<section><p>검증된 성과는 300만 개였다.</p></section>"

        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC, registry, rendered), [])

    def test_c6_unbacked_number_in_body_fails(self):
        rendered = "<section><p>근거 없는 매출 999억이 본문에 들어갔다.</p></section>"

        violations = validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, rendered)

        self.assertTrue(any("untagged number in rendered output" in str(v) for v in violations))

    def test_c6_year_in_body_passes(self):
        rendered = "<section><p>2018~19년 흐름과 2024년 기준 변화가 이어졌다.</p></section>"

        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, rendered), [])

    def test_c6_manual_source_label_still_fails(self):
        rendered = "<section><p>출처: 어쩌구</p></section>"

        violations = validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, rendered)

        self.assertTrue(any("manual source label" in str(v) for v in violations))

    def test_c6_enclosed_numeral_still_fails(self):
        rendered = "<section><p>① 첫 번째 근거를 본문에 썼다.</p></section>"

        violations = validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, rendered)

        self.assertTrue(any("enclosed numeral" in str(v) for v in violations))

    def test_c6_accepts_closing_layout_in_supported_layout_enum(self):
        self.assertIn("closing", contract_checks_module.SUPPORTED_LAYOUTS)
        self.assertEqual(validate_c6_content_authority(VALID_CLOSING_DECK_SPEC, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_accepts_new_signature_layouts_in_supported_layout_enum(self):
        for layout in ("mosaic_tiles", "split_status", "scenario_cards"):
            with self.subTest(layout=layout):
                self.assertIn(layout, contract_checks_module.SUPPORTED_LAYOUTS)
                spec = {"pages": [dict(VALID_DECK_SPEC["pages"][0], layout=layout)]}
                self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_accepts_pricing_cards_layout_in_supported_layout_enum(self):
        self.assertIn("pricing_cards", contract_checks_module.SUPPORTED_LAYOUTS)
        spec = {"pages": [dict(VALID_DECK_SPEC["pages"][0], layout="pricing_cards")]}
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_accepts_swot_quad_viz_without_metric_ids(self):
        self.assertIn("swot_quad", contract_checks_module.SUPPORTED_VIZ_CHART_TYPES)
        spec = {
            "pages": [
                dict(
                    VALID_DECK_SPEC_WITH_VIZ["pages"][0],
                    allowed_metric_ids=[],
                    content=[
                        {
                            "type": "viz",
                            "chart": "swot_quad",
                            "title": "Qualitative SWOT",
                            "series": [
                                {"label": "Strengths", "items": ["Owned proof assets"], "role": "highlight"},
                                {"label": "Weaknesses", "items": ["Low aided awareness"]},
                                {"label": "Opportunities", "items": ["Partner distribution"]},
                                {"label": "Threats", "items": ["Platform policy shifts"]},
                            ],
                        }
                    ],
                )
            ]
        }
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, ""), [])

    def test_c6_rejects_swot_quad_items_with_raw_numbers(self):
        invalid = {
            "pages": [
                dict(
                    VALID_DECK_SPEC_WITH_VIZ["pages"][0],
                    allowed_metric_ids=[],
                    content=[
                        {
                            "type": "viz",
                            "chart": "swot_quad",
                            "series": [
                                {"label": "Strengths", "items": ["Awareness rose 47%"]},
                                {"label": "Weaknesses", "items": ["Manual process"]},
                                {"label": "Opportunities", "items": ["Retail partner"]},
                                {"label": "Threats", "items": ["Policy change"]},
                            ],
                        }
                    ],
                )
            ]
        }
        violations = validate_c6_content_authority(invalid, VALID_CONTENT_REGISTRY, "")
        self.assertTrue(any("swot_quad item contains raw number" in str(v) for v in violations))

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
          <p>CTR fell 999% after AI summaries.</p>
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

    def test_c8_accepts_market_research_required_artifacts(self):
        intake = {"genre": "market-research"}
        evidence_pool = {"items": [{"source_type": "observation"} for _ in range(5)]}
        page_plan = {"pages": [{"genre_artifact": "taxonomy"}, {"genre_artifact": "player_table"}]}
        self.assertEqual(check_c8_genre_artifacts(intake, evidence_pool, page_plan), [])

    def test_c8_market_research_aliases_include_spaced_korean_and_brand_research(self):
        evidence_pool = {"items": [{"source_type": "observation"} for _ in range(5)]}
        page_plan = {"pages": [{"genre_artifact": "taxonomy"}]}
        for genre in ("시장 조사", "brand-research", "경쟁 분석"):
            with self.subTest(genre=genre):
                violations = check_c8_genre_artifacts({"genre": genre}, evidence_pool, page_plan)
                self.assertEqual(len(violations), 1)
                self.assertEqual(violations[0].contract_id, "C8")
                self.assertIn("player_table", violations[0].message)

    def test_c8_rejects_market_research_without_player_table(self):
        intake = {"genre": "market_research"}
        evidence_pool = {"items": [{"source_type": "observation"} for _ in range(5)]}
        page_plan = {"pages": [{"genre_artifact": "taxonomy"}]}
        violations = check_c8_genre_artifacts(intake, evidence_pool, page_plan)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C8")
        self.assertIn("player_table", violations[0].message)

    def test_c8_rejects_market_research_with_too_few_observations(self):
        intake = {"genre": "시장조사"}
        evidence_pool = {"items": [{"source_type": "observation"} for _ in range(3)]}
        page_plan = {"pages": [{"genre_artifact": "taxonomy"}, {"genre_artifact": "player_table"}]}
        violations = check_c8_genre_artifacts(intake, evidence_pool, page_plan)
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C8")
        self.assertIn("requires at least 5 observation evidence items (found 3)", violations[0].message)

    def test_c8_skips_non_market_research_genres(self):
        intake = {"genre": "trend-report"}
        evidence_pool = {"items": []}
        page_plan = {"pages": []}
        self.assertEqual(check_c8_genre_artifacts(intake, evidence_pool, page_plan), [])

    def test_c8_skips_missing_genre(self):
        evidence_pool = {"items": []}
        page_plan = {"pages": []}
        self.assertEqual(check_c8_genre_artifacts({}, evidence_pool, page_plan), [])

    def _write_c10_run(self, run_dir: pathlib.Path, genre: str, source_registry):
        (run_dir / "00_intake.json").write_text(json.dumps({"genre": genre}), encoding="utf-8")
        (run_dir / "02_verified.json").write_text(
            json.dumps({"source_registry": source_registry}),
            encoding="utf-8",
        )

    def _check_c10(self, run_dir: pathlib.Path):
        self.assertTrue(
            hasattr(contract_checks_module, "check_c10_collection_evidence"),
            "check_c10_collection_evidence must exist",
        )
        return contract_checks_module.check_c10_collection_evidence(run_dir)

    def test_c10_market_research_rejects_legacy_registry_without_doc_type(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            self._write_c10_run(
                run_dir,
                "market-research",
                {"src_1": {"tier": "Tier-A", "local_path": "pdf/source.pdf"}},
            )

            violations = self._check_c10(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C10")
        self.assertIn("doc_type", violations[0].message)
        self.assertEqual(violations[0].path, "02_verified.json.source_registry")

    def test_c10_market_research_rejects_fewer_than_five_canonical_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            for index in range(4):
                source_file = run_dir / "pdf" / f"source_{index}.pdf"
                source_file.parent.mkdir(exist_ok=True)
                source_file.write_text("pdf", encoding="utf-8")
            self._write_c10_run(
                run_dir,
                "market-research",
                {
                    f"src_{index}": {
                        "tier": "Tier-A",
                        "doc_type": "pdf",
                        "local_path": f"pdf/source_{index}.pdf",
                        "cited_pages": [1],
                    }
                    for index in range(4)
                },
            )

            violations = self._check_c10(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C10")
        self.assertIn("at least 5 canonical document sources (found 4)", violations[0].message)

    def test_c10_market_research_accepts_five_pdf_sources_with_files_and_pages(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            for index in range(5):
                source_file = run_dir / "pdf" / f"source_{index}.pdf"
                source_file.parent.mkdir(exist_ok=True)
                source_file.write_text("pdf", encoding="utf-8")
            self._write_c10_run(
                run_dir,
                "market-research",
                {
                    f"src_{index}": {
                        "tier": "Tier-A",
                        "doc_type": "pdf",
                        "local_path": f"pdf/source_{index}.pdf",
                        "cited_pages": [1, "12-15"],
                    }
                    for index in range(5)
                },
            )

            violations = self._check_c10(run_dir)

        self.assertEqual(violations, [])

    def test_c10_market_research_rejects_missing_local_path_file_per_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            for index in range(4):
                source_file = run_dir / "pdf" / f"source_{index}.pdf"
                source_file.parent.mkdir(exist_ok=True)
                source_file.write_text("pdf", encoding="utf-8")
            self._write_c10_run(
                run_dir,
                "market-research",
                {
                    f"src_{index}": {
                        "tier": "Tier-A",
                        "doc_type": "pdf",
                        "local_path": f"pdf/source_{index}.pdf",
                        "cited_pages": [1],
                    }
                    for index in range(5)
                },
            )

            violations = self._check_c10(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C10")
        self.assertIn("local_path file missing", violations[0].message)
        self.assertEqual(violations[0].path, "02_verified.json.source_registry.src_4.local_path")

    def test_c10_market_research_requires_pdf_pages_but_accepts_extract_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            for index in range(5):
                source_file = run_dir / "pdf" / f"source_{index}.pdf"
                source_file.parent.mkdir(exist_ok=True)
                source_file.write_text("source", encoding="utf-8")
            self._write_c10_run(
                run_dir,
                "market-research",
                {
                    "src_pdf": {
                        "tier": "Tier-A",
                        "doc_type": "pdf",
                        "local_path": "pdf/source_0.pdf",
                    },
                    **{
                        f"src_db_{index}": {
                            "tier": "Tier-A",
                            "doc_type": "official_db_extract",
                            "local_path": f"pdf/source_{index}.pdf",
                            "extract_note": "official database extract",
                        }
                        for index in range(1, 5)
                    },
                },
            )

            violations = self._check_c10(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C10")
        self.assertIn("cited_pages", violations[0].message)
        self.assertEqual(violations[0].path, "02_verified.json.source_registry.src_pdf.cited_pages")

    def test_c10_skips_non_market_research_genre(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            self._write_c10_run(run_dir, "trend-report", {})

            violations = self._check_c10(run_dir)

        self.assertEqual(violations, [])

    def test_c9_rejects_missing_external_review_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            (run_dir / "deck.html").write_text("<section>Deck</section>", encoding="utf-8")

            violations = check_c9_final_review(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C9")
        self.assertIn("final external review missing", violations[0].message)

    def test_c9_accepts_matching_hash_with_codex_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            html_path = run_dir / "deck.html"
            html_path.write_text("<section>Deck</section>", encoding="utf-8")
            deck_hash = contract_checks_module.sha256_file(html_path)
            (run_dir / "review_codex.txt").write_text("지적 1. " + ("충분한 리뷰 본문입니다. " * 20), encoding="utf-8")
            (run_dir / "08_external_review.json").write_text(
                json.dumps(
                    {
                        "deck_html_sha256": deck_hash,
                        "codex": {"ok": True, "file": "review_codex.txt"},
                        "gemini": {"ok": False, "file": "review_gemini.txt"},
                    }
                ),
                encoding="utf-8",
            )

            violations = check_c9_final_review(run_dir)

        self.assertEqual(violations, [])

    def test_c9_rejects_deck_html_changed_after_external_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            html_path = run_dir / "deck.html"
            html_path.write_text("<section>Current</section>", encoding="utf-8")
            reviewed_hash = "0" * 64
            (run_dir / "08_external_review.json").write_text(
                json.dumps(
                    {
                        "deck_html_sha256": reviewed_hash,
                        "codex": {"ok": True, "file": "review_codex.txt"},
                        "gemini": {"ok": False, "file": "review_gemini.txt"},
                    }
                ),
                encoding="utf-8",
            )

            violations = check_c9_final_review(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertIn("deck.html changed after external review", violations[0].message)
        self.assertIn(reviewed_hash[:12], violations[0].message)

    def test_c9_rejects_when_both_external_reviewers_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            html_path = run_dir / "deck.html"
            html_path.write_text("<section>Deck</section>", encoding="utf-8")
            deck_hash = contract_checks_module.sha256_file(html_path)
            (run_dir / "08_external_review.json").write_text(
                json.dumps(
                    {
                        "deck_html_sha256": deck_hash,
                        "codex": {"ok": False, "file": "review_codex.txt"},
                        "gemini": {"ok": False, "file": "review_gemini.txt"},
                    }
                ),
                encoding="utf-8",
            )

            violations = check_c9_final_review(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C9")
        self.assertIn("both external reviewers failed", violations[0].message)

    def test_c9_rejects_ok_reviewers_when_output_files_are_sentinel_or_too_short(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            html_path = run_dir / "deck.html"
            html_path.write_text("<section>Deck</section>", encoding="utf-8")
            deck_hash = contract_checks_module.sha256_file(html_path)
            (run_dir / "review_codex.txt").write_text("REVIEWER_TIMEOUT (600s)\n", encoding="utf-8")
            (run_dir / "review_gemini.txt").write_text("too short\n", encoding="utf-8")
            (run_dir / "08_external_review.json").write_text(
                json.dumps(
                    {
                        "deck_html_sha256": deck_hash,
                        "codex": {"ok": True, "file": "review_codex.txt"},
                        "gemini": {"ok": True, "file": "review_gemini.txt"},
                    }
                ),
                encoding="utf-8",
            )

            violations = check_c9_final_review(run_dir)

        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].contract_id, "C9")
        self.assertIn("both external reviewers failed", violations[0].message)

    def test_c9_accepts_when_one_ok_reviewer_has_substantive_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            html_path = run_dir / "deck.html"
            html_path.write_text("<section>Deck</section>", encoding="utf-8")
            deck_hash = contract_checks_module.sha256_file(html_path)
            (run_dir / "review_codex.txt").write_text("REVIEWER_FAILED_TO_START\nboom\n", encoding="utf-8")
            (run_dir / "review_gemini.txt").write_text("지적 1. " + ("충분한 리뷰 본문입니다. " * 20), encoding="utf-8")
            (run_dir / "08_external_review.json").write_text(
                json.dumps(
                    {
                        "deck_html_sha256": deck_hash,
                        "codex": {"ok": True, "file": "review_codex.txt"},
                        "gemini": {"ok": True, "file": "review_gemini.txt"},
                    }
                ),
                encoding="utf-8",
            )

            violations = check_c9_final_review(run_dir)

        self.assertEqual(violations, [])

    def test_render_deck_injects_metric_values_and_generated_citations(self):
        html = render_deck_module.render_deck(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, title="C6 Fixture")
        self.assertIn('data-metric-id="metric_click_drop"', html)
        self.assertIn("47%", html)
        self.assertIn('data-src-id="src_a"', html)
        self.assertIn("Pew Research Center", html)
        self.assertNotIn("출처:", html)
        self.assertEqual(validate_c6_content_authority(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, html), [])

        appendix_spec = {
            "pages": [
                dict(VALID_DECK_SPEC["pages"][0]),
                {
                    "page_id": "appendix",
                    "short_title": "출처",
                    "layout": "source_appendix",
                    "allowed_source_ids": ["src_a", "src_b"],
                    "allowed_metric_ids": [],
                    "content": [{"type": "headline", "text": "출처"}],
                },
            ]
        }
        appendix_registry = {
            "sources": {
                "src_a": {
                    "publisher": "Pew Research Center",
                    "title": "Pew & Partners 2026",
                    "url": "https://example.com/pew?q=ai&src=deck",
                },
                "src_b": {"publisher": "IAB", "title": "IAB Report", "url": ""},
            },
            "metrics": VALID_CONTENT_REGISTRY["metrics"],
        }
        appendix_html = render_deck_module.render_deck(appendix_spec, appendix_registry, title="Appendix Fixture")
        self.assertIn(
            '<a class="appendix-link" href="https://example.com/pew?q=ai&amp;src=deck">Pew &amp; Partners 2026 ↗</a>',
            appendix_html,
        )
        self.assertIn('<span class="appendix-title" data-src-id="src_b">IAB Report</span>', appendix_html)
        self.assertIn("모든 수치 출처 연결 검증 · 출처 2곳", appendix_html)
        self.assertEqual(validate_c6_content_authority(appendix_spec, appendix_registry, appendix_html), [])

    def test_render_deck_source_appendix_links_only_http_schemes(self):
        appendix_spec = {
            "pages": [
                {
                    "page_id": "appendix",
                    "short_title": "출처",
                    "layout": "source_appendix",
                    "allowed_source_ids": ["src_a", "src_b"],
                    "allowed_metric_ids": [],
                    "content": [{"type": "headline", "text": "출처"}],
                }
            ]
        }
        appendix_registry = {
            "sources": {
                "src_a": {"publisher": "Pew", "title": "Safe", "url": "http://example.com/report"},
                "src_b": {"publisher": "Bad", "title": "Unsafe", "url": "javascript:alert(1)"},
            },
            "metrics": VALID_CONTENT_REGISTRY["metrics"],
        }

        appendix_html = render_deck_module.render_deck(appendix_spec, appendix_registry, title="Appendix Fixture")

        self.assertIn('<a class="appendix-link" href="http://example.com/report">Safe ↗</a>', appendix_html)
        self.assertIn('<span class="appendix-title" data-src-id="src_b">Unsafe</span>', appendix_html)
        self.assertNotIn('href="javascript:alert(1)"', appendix_html)

    def test_render_deck_text_table_cells_use_rich_text_markup(self):
        spec = {
            "pages": [
                {
                    "page_id": "table_fixture",
                    "short_title": "Table",
                    "layout": "statement",
                    "allowed_source_ids": [],
                    "allowed_metric_ids": [],
                    "content": [
                        {
                            "type": "text_table",
                            "columns": ["구분", "해석"],
                            "rows": [["A", "==중요== 신호"]],
                        }
                    ],
                }
            ]
        }

        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Text Table Rich Fixture")

        self.assertIn('<td><b class="kw">중요</b> 신호</td>', html)
        self.assertNotIn("==중요==", html)

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

    def test_render_deck_outputs_new_signature_layouts(self):
        specs = {
            "mosaic_tiles": [
                {"type": "headline", "text": "Mosaic Lead"},
                {"type": "body", "text": "First tile copy"},
                {"type": "metric", "metric_id": "metric_click_drop"},
                {"type": "bullets", "items": ["One", "Two"]},
                {"type": "body", "text": "Last tile copy"},
            ],
            "split_status": [
                {"type": "headline", "text": "Status Lead"},
                {"type": "body", "text": "Narrative first"},
                {"type": "bullets", "items": ["Qualitative signal"]},
                {"type": "metric", "metric_id": "metric_click_drop"},
                {"type": "metric", "metric_id": "metric_measurement"},
            ],
            "scenario_cards": [
                {"type": "headline", "text": "Base Case"},
                {"type": "body", "text": "Scenario body"},
                {"type": "metric", "metric_id": "metric_click_drop"},
                {"type": "headline", "text": "Upside Case"},
                {"type": "body", "text": "Scenario body"},
                {"type": "metric", "metric_id": "metric_measurement"},
            ],
        }
        expected_markers = {
            "mosaic_tiles": ("mosaic-body", "mosaic-grid", "mosaic-tile-large"),
            "split_status": ("split-status-body", "status-copy", "status-chip"),
            "scenario_cards": ("scenario-body", "scenario-grid", "scenario-card"),
        }
        for layout, content in specs.items():
            with self.subTest(layout=layout):
                spec = {
                    "pages": [
                        {
                            "page_id": f"{layout}_fixture",
                            "short_title": layout,
                            "layout": layout,
                            "allowed_source_ids": ["src_a", "src_b"],
                            "allowed_metric_ids": ["metric_click_drop", "metric_measurement"],
                            "content": content,
                        }
                    ]
                }
                html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Signature Fixture")
                for marker in expected_markers[layout]:
                    self.assertIn(marker, html)
                self.assertIn('data-metric-id="metric_click_drop"', html)
                self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_outputs_pricing_cards_with_configurable_emphasis(self):
        spec = {
            "pages": [
                {
                    "page_id": "pricing_fixture",
                    "short_title": "Choose The Operating Model",
                    "layout": "pricing_cards",
                    "emphasis_style": "border",
                    "allowed_source_ids": ["src_a", "src_b"],
                    "allowed_metric_ids": ["metric_click_drop", "metric_measurement"],
                    "content": [
                        {"type": "headline", "text": "Starter"},
                        {"type": "bullets", "items": ["Manual reporting", "Email support"]},
                        {"type": "metric", "metric_id": "metric_click_drop"},
                        {"type": "headline", "text": "Operator", "emphasis": True},
                        {"type": "bullets", "items": ["Live dashboard", "Priority review"]},
                        {"type": "metric", "metric_id": "metric_measurement"},
                    ],
                }
            ]
        }
        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Pricing Fixture")
        self.assertIn("pricing-body", html)
        self.assertIn("pricing-grid", html)
        self.assertIn("pricing-card-emphasis", html)
        self.assertIn("pricing-emphasis-border", html)
        self.assertIn('data-metric-id="metric_click_drop"', html)
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_outputs_swot_quad_without_metric_ids(self):
        spec = {
            "pages": [
                {
                    "page_id": "swot_fixture",
                    "short_title": "Strategic Read",
                    "layout": "statement",
                    "allowed_source_ids": [],
                    "allowed_metric_ids": [],
                    "content": [
                        {
                            "type": "viz",
                            "chart": "swot_quad",
                            "title": "Market Position",
                            "series": [
                                {"label": "Strengths", "items": ["Proof library"], "role": "highlight"},
                                {"label": "Weaknesses", "items": ["Small sales surface"]},
                                {"label": "Opportunities", "items": ["Agency bundles"]},
                                {"label": "Threats", "items": ["Platform lock-in"]},
                            ],
                        }
                    ],
                }
            ]
        }
        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="SWOT Fixture")
        self.assertIn("visual-swot-quad", html)
        self.assertIn("swot-cell-highlight", html)
        self.assertIn("Proof library", html)
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_outputs_running_head_chrome_for_body_pages(self):
        spec = {
            "meta": {"page_chrome": "running_head", "short_title": "Proof OS"},
            "pages": [
                dict(VALID_COVER_DECK_SPEC["pages"][0]),
                dict(VALID_DECK_SPEC["pages"][0], page_id="body_a"),
                dict(VALID_DECK_SPEC["pages"][1], page_id="body_b", content=[{"type": "eyebrow", "text": "Signal"}, *VALID_DECK_SPEC["pages"][1]["content"]]),
                dict(VALID_CLOSING_DECK_SPEC["pages"][0]),
            ],
        }
        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Running Head Fixture")
        body_a = html.split('data-page-id="body_a"', 1)[1].split("</section>", 1)[0]
        body_b = html.split('data-page-id="body_b"', 1)[1].split("</section>", 1)[0]
        cover = html.split('data-page-id="cover"', 1)[1].split("</section>", 1)[0]
        self.assertIn("running-head", body_a)
        # kicker는 명시적 eyebrow만 — 내부 role/layout 명 폴백은 크롬 노출 금지 (7/4 클차장 수정)
        self.assertNotIn('running-head-kicker">HERO_METRIC', body_a)
        self.assertIn('running-head-kicker"></span>', body_a)
        self.assertIn('running-head-kicker">Signal<', body_b)
        self.assertIn("Proof OS", body_a)
        self.assertIn("01 / 02", body_a)
        self.assertIn("PREV", body_b)
        self.assertNotIn("NEXT", body_b)
        self.assertNotIn("page-number", body_a)
        self.assertNotIn("running-head", cover)

    def test_render_deck_outputs_side_wordmark_from_context(self):
        spec = {
            "meta": {"short_title": "Proof OS"},
            "pages": [
                dict(
                    VALID_DECK_SPEC["pages"][0],
                    page_id="wordmark_fixture",
                    decor="side_wordmark",
                    section_label="Evidence",
                )
            ],
        }
        html = render_deck_module.render_deck(spec, VALID_CONTENT_REGISTRY, title="Side Wordmark Fixture")
        self.assertIn("decor-side-wordmark", html)
        self.assertIn("side-wordmark", html)
        self.assertIn("Evidence", html)
        self.assertEqual(validate_c6_content_authority(spec, VALID_CONTENT_REGISTRY, html), [])

    def test_render_deck_omits_eyebrow_when_no_explicit_block(self):
        # 명시 eyebrow 없으면 role/layout 내부명 폴백 노출 금지(C2 계열) — div 자체를 렌더하지 않는다(7/4).
        html = render_deck_module.render_deck(VALID_DECK_SPEC, VALID_CONTENT_REGISTRY, title="No Eyebrow Fixture")
        self.assertNotIn('<div class="eyebrow', html)
        self.assertNotIn("HERO_METRIC", html)
        self.assertNotIn("STAT_GRID", html)

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
        self.assertIn("text_table", contract_checks_module.SUPPORTED_CONTENT_BLOCK_TYPES)

    def test_every_supported_viz_chart_has_a_renderer(self):
        # 계약 enum에 있는데 렌더러 분기가 없으면 "조용한 no-op"이 된다 — 1:1을 코드로 강제.
        self.assertEqual(
            set(render_deck_module._CHART_RENDERERS),
            set(contract_checks_module.SUPPORTED_VIZ_CHART_TYPES),
        )

    def test_external_review_lenses_metadata_matches_prompt_lenses(self):
        prompt = external_review_module.build_review_prompt([{"page_id": "p01", "text": "본문"}])
        self.assertEqual(len(external_review_module.LENSES), 5)
        for lens in external_review_module.LENSES:
            self.assertIn(lens, prompt)
        self.assertTrue(any("독자 패널" in lens for lens in external_review_module.LENSES))

    def test_external_review_resolves_gemini_env_overrides_and_checks_existence(self):
        with tempfile.TemporaryDirectory() as tmp:
            wrapper = pathlib.Path(tmp) / "gemini_call_wrapper.py"
            python = pathlib.Path(tmp) / "python"
            wrapper.write_text("# wrapper\n", encoding="utf-8")
            python.write_text("# python\n", encoding="utf-8")
            with mock.patch.dict(os.environ, {"GEMINI_WRAPPER": str(wrapper), "GEMINI_PY": str(python)}):
                resolved_python, resolved_wrapper = external_review_module.resolve_gemini_paths()
            self.assertEqual(resolved_python, python)
            self.assertEqual(resolved_wrapper, wrapper)

        with mock.patch.dict(os.environ, {"GEMINI_WRAPPER": "/missing/wrapper.py", "GEMINI_PY": "/missing/python"}):
            with self.assertRaises(FileNotFoundError) as ctx:
                external_review_module.resolve_gemini_paths()
        self.assertIn("GEMINI", str(ctx.exception))

    def test_external_review_gemini_command_reads_prompt_file_without_prompt_in_argv(self):
        with tempfile.TemporaryDirectory() as tmp:
            prompt_path = pathlib.Path(tmp) / "prompt.txt"
            prompt_text = "매우 긴 프롬프트 본문"
            prompt_path.write_text(prompt_text, encoding="utf-8")

            command = external_review_module.build_gemini_command(
                pathlib.Path("/bin/python3"),
                pathlib.Path("/tmp/gemini_call_wrapper.py"),
                prompt_path,
            )

        self.assertIn(str(prompt_path), command)
        self.assertIn("-c", command)
        self.assertNotIn(prompt_text, "\0".join(command))
        self.assertNotIn("--prompt", command)

    def test_external_review_codex_command_keeps_argv_but_enforces_size_limit(self):
        command = external_review_module.build_codex_command("짧은 프롬프트")
        self.assertEqual(command[:3], ["codex", "exec", "--skip-git-repo-check"])
        self.assertIn("짧은 프롬프트", command)
        with self.assertRaises(ValueError):
            external_review_module.build_codex_command("x" * (external_review_module.CODEX_PROMPT_ARGV_LIMIT + 1))

    def test_pptx_export_run_checked_reports_timeout_with_configured_seconds(self):
        with mock.patch.object(
            pptx_export_module.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["pip"], 300),
        ) as run:
            with self.assertRaises(RuntimeError) as ctx:
                pptx_export_module.run_checked(["pip"], "pip install", timeout=300)

        self.assertEqual(run.call_args.kwargs["timeout"], 300)
        self.assertIn("pip install timed out after 300s", str(ctx.exception))

    def test_pptx_export_run_chrome_reports_timeout_with_configured_seconds(self):
        with mock.patch.object(
            pptx_export_module.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired(["chrome"], 180),
        ) as run:
            with self.assertRaises(SystemExit) as ctx:
                pptx_export_module.run_chrome("chrome", ["--dump-dom"], "LAYOUT_DUMP")

        self.assertEqual(run.call_args.kwargs["timeout"], 180)
        self.assertIn("LAYOUT_DUMP_TIMEOUT: Chrome timed out after 180s", str(ctx.exception))

    def test_qa_lint_treats_text_table_rows_as_body_text(self):
        spec = {
            "archetype": "selfcheck",
            "pages": [
                {
                    "page_id": "table_rows",
                    "short_title": "표",
                    "layout": "statement",
                    "allowed_metric_ids": [],
                    "content": [
                        {
                            "type": "text_table",
                            "columns": ["구분", "해석"],
                            "rows": [["단, 관찰되지 않는다", "성장 47%"]],
                        }
                    ],
                }
            ],
        }

        codes = {defect["code"] for defect in qa_lint_module.lint_deck(spec, {})}

        self.assertIn("READER_FIRST_CAVEAT", codes)
        self.assertIn("READER_FIRST_EPISTEMIC", codes)
        self.assertIn("RAW_NUMBER_IN_LABEL", codes)

    def test_run_contracts_defaults_to_deck_html_not_latest_html(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = pathlib.Path(tmp)
            deck_html = run_dir / "deck.html"
            later_html = run_dir / "z_later.html"
            deck_html.write_text("<section>deck</section>", encoding="utf-8")
            later_html.write_text("<section>later</section>", encoding="utf-8")
            os.utime(deck_html, (1, 1))
            os.utime(later_html, (2, 2))

            selected = run_contracts_module.select_html_path(run_dir, None)

        self.assertEqual(selected, deck_html)

    def test_run_deck_parses_run_id_from_claude_result_before_workspace_fallback(self):
        command = (
            f'TICKDECK_RUN_DECK_TEST=1 source "{RUN_DECK_SH}"; '
            "printf '%s\\n' '중간 로그' '20260705_clo_market' | parse_result_run_id"
        )
        completed = subprocess.run(["bash", "-c", command], capture_output=True, text=True, check=False)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), "20260705_clo_market")

    def test_validate_all_contracts_can_raise(self):
        broken = dict(VALID_DECK, rendered_pages=[{"title": "신뢰도 강등", "body": "본문"}])
        with self.assertRaises(ContractViolation):
            validate_all_contracts(broken, raise_on_error=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
