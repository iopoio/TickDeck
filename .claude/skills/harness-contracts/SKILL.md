---
name: harness-contracts
description: TickDeck v4 contract definitions and executable tests for Insight schema, proposition DAG, citation tracker, validation metadata scan, trend state transition, and stage order.
---

# Harness Contracts

Use this skill before accepting any TickDeck v4 harness output as complete.

## Files

- `scripts/contract_checks.py`: executable contract validators.
- `scripts/test_contracts.py`: unittest coverage for C1~C5.

Run:

```bash
python .claude/skills/harness-contracts/scripts/test_contracts.py
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
