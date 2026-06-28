---
name: deck-harness
description: Run the TickDeck v4 deck harness for any presentation request, trend report, topic deck, update, 다시 만들기, 보완, 재수집, or deck refresh. Orchestrates agents, workspace artifacts, loops, contracts, and QA.
---

# TickDeck Deck Harness

Use this skill when the user asks for a presentation deck, trend report, topic deck, deck update, 다시, 업데이트, 보완, or any request that should become a reusable TickDeck v4 presentation artifact.

## Source Of Truth
- Design SoT: `PRD_v4.md`
- Contract skill: `.claude/skills/harness-contracts/SKILL.md`
- Trend genre: `.claude/skills/genre-trend-report/SKILL.md`
- Topic genre: `.claude/skills/genre-topic-deck/SKILL.md`
- Design canon: `tickdeck_harness/knowledge/design/`

## Pipeline

All runs use `_workspace/<run_id>/` as the file handoff area.

1. `intake-director` creates `_workspace/<run_id>/00_intake.json`.
2. `collector` creates `_workspace/<run_id>/01_evidence_pool.json`.
3. `verifier` creates `_workspace/<run_id>/02_verified_evidence.json`.
4. `analyst` creates `_workspace/<run_id>/03_insights.json`.
5. `editorial-director` creates `_workspace/<run_id>/04_proposition_dag.json`.
6. `page-planner` creates `_workspace/<run_id>/05_page_plan.json`.
7. `designer` creates `_workspace/<run_id>/06_render_manifest.json` and render artifacts.
8. `qa-reviewer` creates `_workspace/<run_id>/07_qa_report.json`.

## Agent Team
- `intake-director`: genre, audience, evidence profile, analysis recipe.
- `collector`: Tier-A first raw evidence, opposing views, forced source schema.
- `verifier`: DWS, duplicate, zombie, laundering, circular citation checks.
- `analyst`: structured Insight[] and adversarial self review.
- `editorial-director`: thesis and proposition DAG.
- `page-planner`: page-level meaning design.
- `designer`: fit check and final render after page-plan only.
- `qa-reviewer`: C1~C5 contract scan and cold review.

## Genre Routing
- Trend report: load `genre-trend-report`; trend means state transition, not static statistics.
- Topic deck: load `genre-topic-deck`; organize the topic around claims, counterpoints, audience needs, and decision flow.
- Unknown genre: do not invent a new recipe silently. Put it in `00_intake.json.unknowns` and proceed only with the generic harness if the user accepts broad handling.

## Loop A: Recollection

Verifier or analyst can return to collector when:
- Tier-A evidence is missing.
- Evidence was heavily downgraded or rejected.
- Insight requires at least two independent source ids and the pool cannot supply them.
- A counter-signal or opposing view is missing.

Loop A handoff format:

```json
{
  "loop": "A",
  "from_stage": "verifier|analyst",
  "to_stage": "collector",
  "reason": "",
  "required_source_types": [],
  "required_questions": []
}
```

## Loop B: Page And Design Fit

Designer can return to page-planner only for space, density, or overflow constraints.

Allowed:
- split a crowded page
- shorten a page message
- change page order for fit
- request a simpler visual density

Not allowed:
- change the thesis because a layout looks nicer
- choose content by template
- start rendering before page-plan

Loop B handoff format:

```json
{
  "loop": "B",
  "from_stage": "designer",
  "to_stage": "page-planner",
  "loop_reason": "space|density|overflow|공간|과밀|잘림",
  "page_ids": [],
  "fit_evidence": []
}
```

## Error Handling
- If a stage misses the next input contract, retry once or escalate to the heavier model specified in PRD §5.
- If still missing, record the gap in the next artifact and continue only when the absence is explicit.
- Same error twice means stop and report.
- Never expose validation metadata in slide content.
- Never make `.claude/commands/` for this harness.

## Contract Gate

Before final handoff, run:

```bash
python .claude/skills/harness-contracts/scripts/test_contracts.py
```

For an actual deck artifact, call `validate_all_contracts(deck_json)` from `.claude/skills/harness-contracts/scripts/contract_checks.py`.

## Test Scenarios
- Trend report with no supplied files: must collect Tier-A evidence before analysis.
- Trend report with one strong report only: must trigger C4 or Loop A rather than repackage.
- Static-stat trend page: must fail C3 unless state transition fields exist.
- Designer before page-plan: must fail C5.
- Rendered page title containing validation metadata terms: must fail C2.
