# Axis 1 — Research, Audit, Glossary

축1은 리서치·디깅·종합 결과를 TickDeck 안에서 소비하기 위한 영역이다.

## 들어온 것

| 파일/폴더 | 출처 | 비고 |
|---|---|---|
| `numeric_audit.py` | `sinya/experiments/deepresearch/` | 모델 출력 수치를 corpus 본문과 대조 |
| `two_tier_select.py` | `sinya/experiments/deepresearch/` | 문서 스크리닝 + 섹션 RAG helper |
| `glossary.py` | `sinya/experiments/deepresearch/` | 용어·표현 후보 추출 helper |
| `glossary_library.json` | `sinya/experiments/deepresearch/` | 2026-06-18 실행에서 누적된 용어 라이브러리 |
| `runs/` | `sinya/experiments/deepresearch/runs/` | 실행 결과 JSON 2개 + corpus JSON 2개 |

## 들어오지 않은 것

`runner.py`는 복사하지 않았다. 해당 파일은 `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, OpenRouter client, Qwen/Kimi/MiniMax 호출을 포함한다. 중국 모델 호출은 신야 격리 sandbox에만 둔다.

## 사용 방식

1. 신야에서 공개 주제만 입력해 deepresearch를 실행한다.
2. 결과 JSON과 corpus JSON만 이 폴더의 `runs/`로 가져온다.
3. TickDeck는 이 결과를 수치 대조, 용어 검산, deck 생성 입력으로만 사용한다.

API 호출이 필요한 재수집은 여기서 하지 않는다.
