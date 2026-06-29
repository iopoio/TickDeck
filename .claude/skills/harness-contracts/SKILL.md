---
name: harness-contracts
description: TickDeck v4 contract definitions and executable tests for Insight schema, proposition DAG, citation tracker, validation metadata scan, trend state transition, stage order, and render content authority.
---

# Harness Contracts

Use this skill before accepting any TickDeck v4 harness output as complete.

## Files

- `scripts/contract_checks.py`: executable contract validators.
- `scripts/test_contracts.py`: unittest coverage for C1~C6.
- `scripts/naturalness_check.py`: markdown naturalness scanner for AI translationese and borrowed cliches.
- `scripts/test_naturalness.py`: unittest coverage for the naturalness scanner.

Run:

```bash
python .claude/skills/harness-contracts/scripts/test_contracts.py
python .claude/skills/harness-contracts/scripts/test_naturalness.py
python .claude/skills/harness-contracts/scripts/naturalness_check.py <report.md>
```

## Insight Schema

Base fields:

```json
{
  "claim": "",
  "evidence_ids": [],
  "derivation_type": "",
  "counter_signal": "",
  "narrative_reason": "",
  "source_overlap_score": 0.0
}
```

Trend fields:

```json
{
  "from_state": "",
  "to_state": "",
  "mechanism": ""
}
```

## Proposition DAG Schema

```json
{
  "nodes": [
    {"id": "thesis", "type": "thesis", "text": "", "insight_ids": []}
  ],
  "edges": [
    {"from": "thesis", "to": "node_001", "reason": ""}
  ]
}
```

## Contract C1: No Dict-Matching Curation

Validator: `validate_c1_proposition_dag`.

Pass condition:
- DAG has a thesis/root node.
- Every non-root page proposition is reachable from the thesis/root.
- No route bucket text such as `route=` or "전부 모음".

Fail examples:
- orphan node
- route bucket section
- edge references unknown node id

## Contract C2: No Validation Metadata In Content

Validator: `validate_c2_no_validation_metadata`.

Rendered title/body strings must not expose terms such as:
- 단일출처
- 정성근거
- 강등
- 신뢰도
- single source
- downgrade
- confidence score

QA reports may contain these terms. User-facing deck content must not.

## Contract C3: Trend Means Direction

Validator: `validate_c3_trend_state_transition`.

For trend genres, each trend Insight must include:
- `from_state`
- `to_state`
- `mechanism`

Static statistics are evidence, not a trend headline.

## Contract C4: Original Analysis, Not Repackaging

Validator: `validate_c4_citation_tracker`.

Pass condition:
- each Insight has at least two distinct `evidence_ids`
- `source_overlap_score` is numeric
- `source_overlap_score` is not above the operational max

Current script default:
- `DEFAULT_MAX_SOURCE_OVERLAP_SCORE = 0.85`

The exact threshold is not set in PRD v4.1, so this default is an operational guardrail and should be changed if 후추님 sets a hard value.

## Contract C5: No Design-First Flow

Validator: `validate_c5_stage_order`.

Pass condition:
- first occurrences follow the PRD order from intake to QA.
- designer runs after page-planner.
- Loop B back to page-planner is allowed only for space, density, overflow, 공간, 과밀, or 잘림.

## Contract C6: Render Content Authority

Validator: `validate_c6_content_authority`.

Supported block type SoT: `scripts/contract_checks.py`의 `SUPPORTED_CONTENT_BLOCK_TYPES`.

Current supported block types:
- `eyebrow`
- `headline`, `title`
- `body`, `text`, `summary`
- `callout`, `note`
- `citation`, `source`
- `metric`
- `metrics`, `metric_grid`, `stat_grid`
- `bullets`, `list`

Pass condition:
- every `deck_spec.pages[].content` block type is in `SUPPORTED_CONTENT_BLOCK_TYPES`
- every `src_id` referenced by `deck_spec.pages[].content` exists in `content_registry.sources` or `content_registry.source_registry`
- every `metric_id` referenced by `deck_spec.pages[].content` exists in `content_registry.metrics` or `content_registry.metric_registry`
- referenced IDs are inside that page's `allowed_source_ids` / `allowed_metric_ids`
- metric source_ids are also inside that page's `allowed_source_ids`
- rendered HTML has no untagged numbers
- rendered HTML has no manual `출처:` labels

Expected render tags:

```html
<span data-metric-id="metric_001">47%</span>
<a data-src-id="src_001" href="https://example.com">Publisher</a>
<span data-page-number>01 / 10</span>
```

The designer must not type publisher names, URLs, or numeric values into `deck_spec`. Code rendering injects them from the registry.

## Use In A Deck Run

```python
from contract_checks import validate_all_contracts

violations = validate_all_contracts(deck_json)
if violations:
    for violation in violations:
        print(violation)
```

## Reporting

Final reports must include:
- test command
- passed count
- failed count
- skipped count
- unknowns or thresholds not fixed by PRD
