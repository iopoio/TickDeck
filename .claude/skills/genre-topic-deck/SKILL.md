---
name: genre-topic-deck
description: TickDeck v4 genre profile for general topic presentation decks. Structures a topic into audience-fit claims, evidence, counterpoints, and page-ready argument flow.
---

# Genre: Topic Deck

Use this profile when the user asks for a general presentation about a topic, explainer, proposal, briefing, lecture, or decision deck that is not primarily a trend report.

## Evidence Profile

Collector should target:
- authoritative definitions and primary documents
- current facts and metrics where relevant
- stakeholder perspectives
- counterarguments and known risks
- examples that clarify the topic without becoming the entire answer

Tier-A still wins, but the source mix can include standards, official docs, academic papers, product docs, government material, and credible operator case studies depending on the topic.

## Analysis Recipe

Answer these before page planning:
- What does the audience need to decide, understand, or do?
- What are the 3~5 core claims?
- What evidence supports each claim?
- What counterpoint could weaken each claim?
- What sequence reduces confusion fastest?

## Topic Insight Schema

Use the same base Insight schema, without trend-only state fields unless the topic includes a change claim.

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

## Proposition Frame

Recommended structure:

1. Context: why this topic matters now.
2. Definition: what it is and is not.
3. Core claims: the argument backbone.
4. Evidence: proof per claim.
5. Counterpoints: risks, limits, alternatives.
6. Implications: what changes for the audience.
7. Action: next steps or decision options.

## Anti-Patterns
- Dictionary-style overview with no thesis.
- Equal-weight list when one point matters more.
- Example collection without analysis.
- Design-first page sequence.
- Unsupported claim hidden behind polished language.

## Output

Return:
- audience-specific thesis
- core claims and counterpoints
- Insight[] with source ids
- suggested page roles for page-planner
