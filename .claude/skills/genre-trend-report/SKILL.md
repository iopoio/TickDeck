---
name: genre-trend-report
description: TickDeck v4 genre profile for trend reports. Defines evidence profile, analysis recipe, 10 analysis lenses, state-transition Insight requirements, and Tension-Diagnosis-Mechanism-Scenarios-Convergence-Action structure.
---

# Genre: Trend Report

Use this profile when the request asks for a trend report, market outlook, annual outlook, 변화 분석, future report, or a deck whose core question is "what is changing and why?"

## Evidence Profile

Collector starts with evidence, not conclusions.

Priority:
- Tier-A PDF and primary data first: consulting firms, investment firms, securities research, government, statistics agencies, OECD-like primary datasets.
- Include time series, adoption curves, investment, hiring, patent, regulation, litigation, failure, and regional variance signals.
- Include opposing views and negative cases before analysis.
- Do not use a single finished report as the answer.

Required source mix:
- at least two independent source ids per Insight
- at least one directional or time-based signal for each trend claim
- at least one counter-signal for major claims

## Analysis Recipe

Trend means state transition.

Every headline Insight in a trend report must include:
- `from_state`
- `to_state`
- `mechanism`

Use 2~4 lenses from:
- `references/analysis-lenses-10.md`

Do not compress the lens library into one generic checklist. Pick the lenses that fit the subject and explain why they were selected in the analysis artifact.

## Insight Schema

```json
{
  "claim": "",
  "evidence_ids": [],
  "derivation_type": "",
  "counter_signal": "",
  "narrative_reason": "",
  "source_overlap_score": 0.0,
  "from_state": "",
  "to_state": "",
  "mechanism": ""
}
```

## Proposition Frame

Use this story spine unless the request clearly needs another structure:

1. Tension: old belief versus new signal.
2. Diagnosis: quantified evidence and scope.
3. Mechanism: why the change is happening.
4. Scenarios: optimistic, base, adverse paths with triggers.
5. Convergence: what the signals imply together.
6. Action: what the audience should do next.

## Anti-Patterns
- Static market size headline presented as trend.
- Single-source conclusion rewrite.
- Hype-only trend with no friction, counter-signal, or failed analogue.
- Design template deciding which trends survive.
- Validation metadata shown as slide content.

## Output

Return:
- selected lenses and reasons
- evidence gaps for Loop A
- structured Insight[]
- thesis candidates for editorial-director
