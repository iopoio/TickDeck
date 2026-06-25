# 신야 실행 지시서 — "2026 마케팅 트렌드 · 전 과정 GLM-5.2"

> 목적: 기존 **Qwen** 기반 결과물과 비교하기 위해, **리서치+작가 전 과정을 GLM-5.2**로 1회 실행한다.
> 통제 변수: 주제·검색엔진(Tavily)·바인더(`axis1_to_deck.py`)·렌더(`deck_harness`)는 그대로. **모델만 GLM으로 교체.**
> 범위: 이번 비교 테스트 1회용. 기본 경로(작가=클로드)는 바꾸지 않는다.

OpenRouter 슬러그: **`z-ai/glm-5.2`** (Z.ai/Zhipu, ~1M 컨텍스트)

---

## STEP 1 — 딥리서치 (GLM-5.2)

- **주제:** `2026 마케팅 트렌드`  *(기존 Qwen 런과 동일 — 비교 통제)*
- **모델 교체:** `sinya/experiments/deepresearch/runner.py` 의
  - leader: `qwen/qwen3.7-plus` → **`z-ai/glm-5.2`**
  - reviewer: `moonshotai/kimi-k2.6` → **`z-ai/glm-5.2`**
  - (즉 leader/reviewer 둘 다 GLM)
- **유지:** 검색 = **Tavily 그대로** (corpus 통제 → `numeric_audit` 검산 일관성)
- **출력:** result JSON + corpus JSON 을 아래로 복사
  - `TickDeck/v3/axis1_research/runs/2026_마케팅_트렌드_glm.json`
  - `TickDeck/v3/axis1_research/runs/2026_마케팅_트렌드_glm_corpus.json`

## STEP 2 — 작가 (deck_author.py, GLM-5.2)

- `sinya/experiments/deepresearch/deck_author.py` 의 LLM 모델 → **`z-ai/glm-5.2`**
- 입력: STEP 1 의 result JSON
- **작가 지시 (프롬프트에 주입):**
  - **분량: 20~30장.** `sections`의 `page_budget` 합이 표지·목차·섹션 디바이더·결론·참고 포함하여 20~30장이 되도록.
  - **청중: 일반 직장인.**
    - 전문용어는 풀어쓰고 영어·약어는 `footnotes`로 병기
    - "그래서 내 업무엔?" 식 실무 시사점 위주
    - BLUF(결론 먼저) — `takeaways`에 페이지 결론을 2~4개 먼저
  - 그 외 법칙은 `AUTHOR_STAGE_DESIGN.md §2·§3` 그대로:
    지배 메시지 1줄 · 스토리 아크 · 우리 렌즈로 5±2 테마 재분류 · 한 장 한 메시지 · content_kind 라우팅
- **출력:** `deck_blueprint.json` + `page_specs.json` 을 아래로 복사
  - `TickDeck/v3/authored/2026_마케팅_트렌드_glm_page_specs.json`

## STEP 3 — 바인딩 + 렌더 (신야 밖)

STEP 2 의 `page_specs.json` 이 저장소에 들어오면 진행한다.

```bash
# ④ 바인딩 (TickDeck 저장소 안 · API 없음)
python3 -B TickDeck/v3/pipeline/axis1_to_deck.py \
  TickDeck/v3/authored/2026_마케팅_트렌드_glm_page_specs.json \
  --out TickDeck/v3/pipeline/generated/slides_mktg2026_glm.json

# 렌더 (로컬 deck_harness)
tools/deck_harness/.venv/bin/python tools/deck_harness/src/build.py \
  TickDeck/v3/pipeline/generated/slides_mktg2026_glm.json \
  --out out_tickdeck_mktg2026_glm
```

---

## 금지 / 주의

- 중국모델 호출은 **신야 sandbox 안에서만**. `TickDeck/v3/` 안에서 OpenRouter/Tavily 직접 호출 금지(`verify_boundary.py`가 검사).
- 꾸며내기 금지 — payload 수치/문장은 report·corpus에서만.
- `deck_harness` 렌더 코드 수정 금지(레이아웃 그릇 그대로).

## 비교 산출물

| | 리서치 모델 | 작가 모델 | 결과 JSON |
|---|---|---|---|
| 기존(베이스라인) | Qwen | (기존 경로) | `runs/2026_마케팅_트렌드*.json` |
| 이번 테스트 | **GLM-5.2** | **GLM-5.2** | `runs/2026_마케팅_트렌드_glm.json` |

→ 비교 관점: 수치 충실도(`numeric_audit`) · 재분류/스토리 품질 · 슬라이드 가독성(일반 직장인 눈높이).
