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
2. `collector` creates `_workspace/<run_id>/01_evidence_pool.json`. 수집 우선순위 = ⓪로컬 코퍼스(사용자 제공·`mypdf/2026` 등, provenance=`local_path`) → ①신야 dig → ②차단 URL은 insane-search/Jina → ③WebSearch (collector.md SoT).
3. `verifier` creates `_workspace/<run_id>/02_verified.json` with `source_registry` and `metric_registry`.
4. `analyst` creates `_workspace/<run_id>/03_insights.json`.
5. `editorial-director` creates `_workspace/<run_id>/04_dag.json` (실 run 관행 · 구명 `04_proposition_dag.json`도 run_contracts가 읽음).
6. `page-planner` creates `_workspace/<run_id>/05_page_plan.json` with `short_title`, `allowed_source_ids`, and `allowed_metric_ids` per page.
7. `designer` creates `_workspace/<run_id>/06_deck_spec.json` only. It may choose layout and shorten text, but must reference sources/metrics only by `src_id`/`metric_id`. 시스템·시그니처·차트는 `PATTERN_LIBRARY.md`에서 고르고, `_workspace/_variation_ledger.json`을 읽어 **최근 2 run과 다른 시스템으로 변주**한 뒤 자기 run을 장부에 append 한다(designer.md 규칙·후추님 7/4 "혼자 몇 번 써도 매번 다른 물건"). designer는 `05_page_plan.json.archetype`을 읽어 그 아키타입의 권장/금지 시그니처 안에서 고른다(`DECK_ARCHETYPES.md`).
7.4. **렌더 전 코덱스 프리리뷰 (7/6 신설 — 코덱스 정액 자원 활용·Claude 루프 절약):** designer가 06_deck_spec을 완성하면 렌더 전에 코덱스 1콜로 텍스트만 냉정 리뷰시킨다 — 어색한 문구·논리 비약·금지 패턴(원문자·모델명 디지트·조어)을 렌더 비용 없이 선제 검거. 명령: `codex exec --skip-git-repo-check "<deck_spec 텍스트 필드 나열 + 지적 지시>"`. 치명 지적만 designer가 반영(트리아지 클차장). 최종 외부리뷰(3층·C9)의 대체가 아니라 앞단 절약 장치다.

7.5. **렌더 전 결정론적 린트 (qa_lint · 렌더 비용 아끼는 조기 게이트):** designer 산출물을 *렌더 전에* 검사해 결함을 잡는다 — render→위반→고침→render 반복을 1패스로 줄인다(토큰↓).

```bash
python3 .claude/skills/deck-harness/scripts/qa_lint.py \
  _workspace/<run_id>/06_deck_spec.json _workspace/<run_id>/02_verified.json
```

- `RAW_NUMBER_IN_LABEL`(데이터 값을 텍스트/라벨에)·`EMPTY_SCENARIO_CARD`·`ARCHETYPE_MISSING`은 렌더 전 고친다(고신뢰).
- `MIXED_SOURCE_CHART`·`LAYOUT_MONOTONY`는 **경고(WARN)** — 미·영 비교처럼 정당한 다출처도 있으니 designer가 체리피킹인지 판단(차단 아님·클차장 7/5 스팟체크: 오탐 ~절반).

7.55. **맞춤법·조사 규칙 검사 (7/26 신설 — 후추님 "완성됐다 생각하면 단어·문장·맞춤법 검사" 지시·"한 명로" 사고 후속):** 렌더 전 + done 선언 전에 실행 의무:

```bash
python3 .claude/skills/deck-harness/scripts/spellcheck_kr.py _workspace/<run_id>/06_deck_spec.json
```

조사 오류(으로/로·은/는·이/가·을/를·과/와)를 받침 규칙으로 검출 — sed 치환 부작용·기계 편집 깨짐이 사람 눈 없이 걸린다. WARN은 사람 확인(오탐 있음 — "추이"류 단어·"없는"류 어미를 조사로 오인, 받침 규칙의 한계). 문장 자연스러움·AI 말투 검사는 이게 아니라 7.6 폴리시 + 3층 외부리뷰 몫 — 이 검사가 대체하지 않는다.

7.6. **고티어 문장 폴리시 패스 (7/8 신설 — 납품·쇼케이스 런 한정·경쟁분석 수렴 항목):** 렌더 직전, deck_spec의 **헤드라인·리드(subtitle)·캐비앗(note) 텍스트만** 오퍼스급 이상 1콜로 다듬는다. 논리·수치·ID 참조는 불변(문장 표현만). 프롬프트에 ①`references/writing-standard.md` 적용 규칙 + ②`docs/STYLE_KR_CONSULTING.md`의 실물 예시를 few-shot으로 함께 투입한다(규칙+정본 예시 병행 — GLM 교차 검증 7/8). 데모·내부 런은 생략(비용 절약).

7.7. **핵심 페이지 best-of-N (7/8 신설 — 납품·쇼케이스 런 한정):** 표지·감정 반전(pivot)·클로저 등 덱의 인상을 결정하는 **2~3장만** designer에게 변형 2~3개를 생성시켜 클차장이 선택한다(헤드라인 문안·레이아웃 조합 변주). 계약은 바닥을 올리고 샘플링은 천장을 올린다 — 전 페이지 적용 금지(비용), 핵심 장만.

8. Code renderer creates HTML from deck_spec and registry:

```bash
python .claude/skills/deck-harness/scripts/render_deck.py \
  _workspace/<run_id>/06_deck_spec.json \
  _workspace/<run_id>/02_verified.json \
  -o _workspace/<run_id>/deck.html
```

9. Run C6 content-authority gate before QA.
10. `qa-reviewer` creates `_workspace/<run_id>/07_qa_report.json`.

## 런 원가 기록 (7/9 신설 — test-time compute 뷰 흡수·EP102)

성능 경쟁의 단위가 "점수"에서 "같은 품질을 얼마나 적은 토큰으로"로 이동했다 (Noam Brown 프레임). 우리 버전: **매 런 종료 시 `_workspace/<run_id>/cost_note.md`에 주요 배치별 토큰 사용량·모델을 3~5줄로 기록**한다 (서브에이전트 완료 통보의 usage 수치 전기). 목적 ① 품질 래칫과 나란히 원가 래칫 — 같은 게이트 통과를 더 싸게 ② B형 SaaS 가격 책정의 원가 기초 데이터 (게이트 판정 시 필수). 정밀 계측 시스템을 만들지 말 것 — 손 전기 3~5줄이면 충분, 쌓이면 그때 자동화 판단.

## 검토 단계 (4층)

1. 1층 자동 체크(만드는 내내): `contract_checks` + `naturalness_check` + 커버리지. 거의 공짜라 초안·수정본마다 돌린다.
2. 2층 총괄 게이트(내용/스토리 완성 후·디자인 전): 클차장이 "제대로된·잘 읽히는 보고서인가"를 통째 판정한다.
3. 3층 외부 리뷰(최종 직전 1회·**skip 금지 — 미수행이면 done 불가, 07_qa_report에 `external_review_layer3` 기록 의무**): 코덱스 + 제미나이 교차 후 클차장이 트리아지한다. 둘 다 그대로 받지 않는다(기각 사유도 기록).
   - **"최종"의 정의 = 사용자에게 전달하는 그 판** (run당 1회가 아니다 — 7/6 후추님 지적). 대폭 개정(논지 변경·페이지 절반 이상 재작성·장르 재지정)이 있으면 **개정 최종본으로 재실행**한다. 이전 판 리뷰 기록은 개정본에 대한 리뷰가 아니다. 소폭 수정(문구·1~2페이지)만 기존 기록+개정 명기로 갈음 가능.
   - 입력 (7/8 R7 — spec 단계로 이동): **06_deck_spec.json에서 페이지별 제목·클레임·수치 텍스트 추출** (`external_review.py --stage spec`, 기본값) + 냉정 리뷰 프롬프트(논리 비약·어색한 한국어·제목/부제 관계·흐름 단절, 페이지 명시, 최대 10건). 리뷰 지적 반영 → 렌더는 한 번만. 렌더 후 HTML 입력 모드는 플래그로 보존(레거시).
   - 코덱스: `codex exec --skip-git-repo-check "$(cat review_input.txt)"`
   - 제미나이: `Think/.venv/bin/python Think/.claude/scripts/gemini_call_wrapper.py --prompt "..." --no-cache` (시스템 python엔 google-genai 없음 — Think/.venv가 wrapper 전용 venv, 7/3 복구)
3b. 3b층 전 수치 팩트체크(7/8 R7 신설 — **납품·쇼케이스 런 의무**·데모 면제): 06 확정 후 `factcheck_dump.py`로 수치 대조표(08_factcheck_table.json) 생성 → `fact-checker` 에이전트가 전 수치를 원문 재열람으로 대조(08_factcheck.json). mismatch ≥1 = verifier 반송·통과 금지. unreachable = [미검증] 각주 또는 수치 제거 전까지 통과 금지. verifier는 수집 시점 검증, 이건 최종본 기준 재대조 — 변환 4단(insights→dag→plan→spec)에서 생긴 어긋남을 잡는다.
4. 4층 시각 QA(디자인 후): **렌더가 자동 생성한 `<output>.pdf`를 필수 입력으로 받는다** — `render_deck.py`가 끝나며 `capture_deck.sh`를 호출해 HTML 쓸 때 PDF가 자동 생성된다(규율 아닌 코드 강제). 클차장/`qa-reviewer`가 이 PDF를 *직접 Read로 읽고* 잘림·겹침·밀도·차트 렌더·그레이아웃 강조·깨짐을 판정해 `07_qa_report.json`에 `visual_verdict`(본 슬라이드·발견·pass/fail)를 기록한다. **밀도·단조·닫는 장·제목 기호 잔재 4개 판정(qa-reviewer.md 필수 항목·7/2)도 visual_verdict에 포함해야 한다** — "틀린 것"만 잡고 "부족한 것"을 통과시키던 구멍의 판정 게이트. **이 시각 판정 기록 없이는 done 불가**(보고서/덱 전달 금지). "안 보고 됐다" 차단의 코드/배선 버전.

원칙:
- 싼 자동 체크는 내내 돌린다.
- 비싼 외부 리뷰는 거의 완성본에 1회만 돌린다.
- 큰 구멍은 2층 총괄 게이트에서 디자인 전에 일찍 잡는다.

## Agent Team
- `intake-director`: genre, audience, evidence profile, analysis recipe.
- `collector`: Tier-A first raw evidence, opposing views, forced source schema.
- `verifier`: DWS, duplicate, zombie, laundering, circular citation checks.
- `analyst`: structured Insight[] and adversarial self review.
- `editorial-director`: thesis and proposition DAG.
- `page-planner`: page-level meaning design and page source/metric allowlists.
- `designer`: layout/fit/deck_spec only. No fact, metric, citation, HTML authority.
- `qa-reviewer`: C1~C6 contract scan and cold review.
- `fact-checker`: 최종 deck_spec 전 수치의 원문 재대조 (납품·쇼케이스 의무·R7).

## Genre Routing
- Trend report: load `genre-trend-report`; trend means state transition, not static statistics.
- Topic deck: load `genre-topic-deck`; organize the topic around claims, counterpoints, audience needs, and decision flow.
- **Market research (시장조사·경쟁 분석·"X 시장에서 브랜드 Y의 위치")**: load `genre-market-research`; taxonomy-first, DART 사업보고서 mining, 플레이어 비교표 필수 (7/5 CLO run 교훈 — 이 장르를 트렌드 문법으로 흘리면 "뭉뚱그린 보고서"가 된다).
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
- type a numeric value, publisher name, URL, or source label directly
- add facts not present in story/page-plan

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

## Loop L: 표현 학습 (상시·append-only — 게이트 아님)

컨설팅사·투자사 PDF를 메인 수집원으로 삼는 이유의 절반은 *문체 학습*이다. 매 run에서 collector/analyst가 Tier-A 원문 소화 중 관찰한 새 표현(말투·어휘·수치 어법·구성 관례)을 `references/writing-standard.md` 톤 가이드에 출처와 함께 누적한다(규칙은 그 파일 머리·collector.md). 덱 텍스트를 쓰는 단계(editorial→page-planner→designer)는 그 누적본을 읽는다 — **수집이 문체를 키우고 문체가 다음 덱에 반영되는 닫힌 루프.**

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

For an actual deck artifact, run (payload를 손으로 조립하지 않는다 — 조립 누락 사고 방지·7/2):

```bash
python .claude/skills/harness-contracts/scripts/run_contracts.py _workspace/<run_id>
```

Actual deck contract payload for C6:

```json
{
  "deck_spec": {},
  "content_registry": {
    "source_registry": {},
    "metric_registry": {}
  },
  "rendered_html": "<!doctype html>..."
}
```

C6 fails when:
- deck_spec references unknown `src_id` or `metric_id`
- referenced IDs are outside that page's `allowed_source_ids` / `allowed_metric_ids`
- rendered HTML contains untagged numbers
- rendered HTML contains manual `출처:` labels instead of generated citations
- `viz` blocks use unsupported chart types, omit `series[].metric_id`, or put raw numbers in `title`, `series[].label`, or `note`

## Viz Blocks

Use `viz` when a page needs a compact visual comparison, flow, or concept diagram that text/metric cards cannot express.

```json
{
  "type": "viz",
  "chart": "(SoT: contract_checks.py SUPPORTED_VIZ_CHART_TYPES)",
  "title": "짧은 제목. 숫자 금지",
  "series": [
    {"label": "비교군 라벨. 숫자 금지", "metric_id": "metric_001", "role": "baseline|highlight|left|right|benchmark"}
  ],
  "note": "선택 설명. 숫자 금지"
}
```

Rules:
- Numeric values, units, and source strings are injected only from `02_verified.json` registries.
- `series[].metric_id` must be listed in the same page's `allowed_metric_ids`.
- Metric source ids must be listed in the same page's `allowed_source_ids`.
- Chart enum SoT = `contract_checks.py SUPPORTED_VIZ_CHART_TYPES` (renderer 1:1 coverage is test-enforced). 현재: `before_after`(2행이면 델타 자동), `dumbbell`, `flow`, `big_number`, `gap_map`(role `benchmark`=유령막대·`"sort":"desc"` 옵션), `shift`, `funnel`, `donut`, `mirror_bars`(role left/right 필수), `rising_columns`(배율 브래킷 자동). 선택 기준은 designer.md 차트 선택 가이드 + `references/visualization.md`.
- Comparison groups render gray; the highlighted claim uses the active trend/accent color. No external images or chart libraries.
- 텍스트 블록의 `==키워드==`는 강조어 색전환으로 렌더된다(슬라이드당 1~2개). 델타 주석·배율 브래킷은 렌더러가 계산한다 — designer가 변화량을 손으로 쓰지 않는다.

## Test Scenarios
- Trend report with no supplied files: must collect Tier-A evidence before analysis.
- Trend report with one strong report only: must trigger C4 or Loop A rather than repackage.
- Static-stat trend page: must fail C3 unless state transition fields exist.
- Designer before page-plan: must fail C5.
- Rendered page title containing validation metadata terms: must fail C2.
- Designer-written metric values or manual source labels in rendered HTML: must fail C6.
- Viz block with raw title/label/note numbers or out-of-allowlist metric ids: must fail C6.
