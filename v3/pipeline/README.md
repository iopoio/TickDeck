# TickDeck v3 Pipeline

축1 결과 JSON을 deck_harness 입력 JSON으로 변환하는 얇은 파이프라인이다.
deck 생성 엔진은 새로 만들지 않고 `Think/tools/deck_harness/`를 호출한다.

## 현재 파일

| 파일 | 역할 |
|---|---|
| `ingest_axis1_result.py` | `axis1_research/runs/*.json`을 읽어 요약한다. API 호출 없음 |
| `axis1_to_deck.py` | Axis1 result JSON을 deck_harness `slides_*.json`으로 변환한다. API 호출 없음 |
| `verify_boundary.py` | v3 Python 파일에 OpenRouter/Tavily runtime 호출 코드가 들어왔는지 검사한다 |
| `generated/` | 변환된 deck_harness 입력 JSON |
| `test_axis1_to_deck.py` | 어댑터 계약 테스트 |

## 데이터 흐름

```text
sinya/experiments/deepresearch/runner.py
  -> result JSON + corpus JSON
  -> TickDeck/v3/axis1_research/runs/
  -> TickDeck/v3/pipeline/axis1_to_deck.py
  -> TickDeck/v3/pipeline/generated/slides_*.json
  -> Think/tools/deck_harness/src/build.py
  -> Think/tools/deck_harness/out_tickdeck_*/
```

## 1단계 실행

```bash
cd /Users/hwa/Projects/Automation/Think
python3 -B /Users/hwa/Projects/Automation/TickDeck/v3/pipeline/axis1_to_deck.py \
  /Users/hwa/Projects/Automation/TickDeck/v3/axis1_research/runs/20260618_1749_2026년_글로벌_AI_반도체_시장_전망.json \
  --out /Users/hwa/Projects/Automation/TickDeck/v3/pipeline/generated/slides_ai_semiconductor_e2e.json

tools/deck_harness/.venv/bin/python tools/deck_harness/src/build.py \
  /Users/hwa/Projects/Automation/TickDeck/v3/pipeline/generated/slides_ai_semiconductor_e2e.json \
  --out out_tickdeck_ai_semiconductor_e2e
```

## 금지

- 이 폴더에서 OpenRouter, Qwen, Kimi, MiniMax, Tavily를 직접 호출하지 않는다.
- API key를 읽지 않는다.
- 신야 sandbox 내부 파일을 write하지 않는다.
