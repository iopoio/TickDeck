from __future__ import annotations

import json
from pathlib import Path

import axis1_to_deck


MANIFEST = Path(__file__).resolve().parents[1] / "axis2_layouts" / "components" / "manifest.json"


def test_manifest_matches_author_stage_routing_table():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    mappings = {entry["route"]: entry["layout_candidates"] for entry in manifest["layout_mappings"]}

    assert mappings["role:cover"] == ["cover_hero"]
    assert mappings["role:agenda"] == ["editorial_impact_axes"]
    assert mappings["role:section_divider"] == ["section_divider_hero_text"]
    assert mappings["kind:market_numbers"] == ["data_visualization_3col_chart", "data_visualization_2col_chart_text"]
    assert mappings["kind:split"] == ["split_master"]
    assert mappings["kind:institution_forecasts"] == ["requirements_excel_table", "tam_scenario_table"]
    assert mappings["kind:comparison"] == ["requirements_excel_table", "tam_scenario_table"]
    assert mappings["kind:timeline_evolution"] == ["evolution_timeline"]
    assert mappings["kind:concept_relation"] == ["before_after_diagram_with_metric"]
    assert mappings["kind:funnel_steps"] == ["funnel"]
    assert mappings["kind:growth_drivers"] == ["3-card"]
    assert mappings["kind:implications"] == ["narrative_centered_text_block", "closing"]
    assert mappings["kind:narrative"] == ["narrative_centered_text_block"]
    assert mappings["role:conclusion"] == ["conclusion_synthesis"]
    assert mappings["role:references"] == ["references_notes"]


def test_manifest_uses_only_deck_harness_supported_layouts():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    layouts = {
        layout
        for entry in manifest["layout_mappings"]
        for layout in entry["layout_candidates"]
    }

    assert layouts <= axis1_to_deck.ALLOWED_LAYOUTS
    assert "shot" not in layouts
    assert all("image" not in slot.lower() for entry in manifest["layout_mappings"] for slot in entry.get("data_slots", []))
