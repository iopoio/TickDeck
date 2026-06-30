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

Audience localization (when the audience is tied to a region/market):
- If `00_intake.json.audience` names a region (e.g., 한국 비즈니스·기획 실무자), the evidence pool must include that region's local landing as a required dimension, not only global sources.
- Collect, per major trend: local market size or adoption, named local companies/products/agencies, local regulation or policy, and how the global signal actually lands there (수혜/지체/규제 변수).
- A global-only pool (e.g., only Gartner·McKinsey·NVIDIA·IEA) fails a regional audience. The local angle is a coverage requirement, and at least one trend page must carry a "현지 좌표" beat. (Source priority is unchanged — local consulting/securities research PDF and government statistics are Tier-A.)
- 현지/한국 같은 *별첨성 localization 페이지*(글로벌 분석에 덧대는 현지 종합)는 제목 앞에 `* `를 붙여 본류와 살짝 구분할 수 있다(선택·후추님 6/30). 본류 증거 4전선처럼 *핵심 흐름의 일부*인 페이지엔 붙이지 않는다 — 어디까지가 별첨인지는 그 덱의 구조 판단.

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

## Headline Spine (PRD 원칙 6 · 계약 C7)

제목 시퀀스가 1급 구조다. 본문 없이 제목만 훑어도 위 프레임이 흐르게 짠다(page-planner가 설계, qa가 C7로 검사).
- **증거 섹션은 병렬 명명.** 여러 트렌드(전선)를 동급으로 보일 땐 같은 틀로: `[도메인] — [from→to 이동]`(예: "로봇 — 성능에서 조율로" / "전력 — 부담에서 자급으로"). 트렌드=상태전이(C3)가 제목에서부터 보이고, 훑을 때 "N개 전선"이 한눈에 잡힌다. 은유 조각·포맷명("~매트릭스") 금지(C7).
- **닫음은 결론 → 제언 두 박자.** 5.Convergence = *결론 슬라이드*(신호들이 함께 가리키는 종합), 6.Action = *제언 슬라이드*(그래서 무엇을 하라 — 단정적 권고/마인드셋, 빈 워크시트 X). 둘을 한 장에 뭉치지 말고 결론 → 제언으로 이어 닫는다(딜로이트 Tech Trends "결론 → 제언" 흐름 흡수).

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
