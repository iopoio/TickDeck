# TickDeck v3 — 3축 설득 자료 시스템

2026-06-18 TickDeck 피봇 통합본. 기존 `backend/`, `frontend/`, `worker/`, `v2/`는 보존하고, 새 3축 실험은 이 `v3/` 아래에만 둔다.

## 구성

| 경로 | 역할 |
|---|---|
| `axis1_research/` | 리서치 결과 소비, 수치 대조, 2층 선별, 용어·표현 라이브러리 |
| `axis2_layouts/` | Envato 미리보기 양식 수집본과 수집 스크립트 |
| `pipeline/` | 축1 결과와 축2 양식을 deck harness로 넘기기 전의 연결 뼈대 |

## 보안 경계

중국 모델 호출 코드는 TickDeck로 옮기지 않는다.

- 수집 엔진 정본: `/Users/hwa/Projects/Automation/sinya/experiments/deepresearch/`
- TickDeck/v3가 받는 것: 실행 결과 JSON, corpus JSON, 안전한 후처리 helper
- TickDeck/v3가 갖지 않는 것: `runner.py`, OpenRouter/Tavily API 키 로딩, Qwen/Kimi/MiniMax 호출 코드

즉, 신야는 격리된 수집 엔진이고 TickDeck/v3는 결과 자료를 소비하는 쪽이다.

## 현재 통합 상태

- 축1: 안전 helper 3개(`numeric_audit.py`, `two_tier_select.py`, `glossary.py`), 용어 라이브러리, 실행 결과 2세트(결과+corpus) 복사.
- 축2: `sandbox/deck_layouts/envato/` 기준 item 폴더 37개, 파일 154개 복사.
- pipeline: JSON 결과 요약과 경계 검증 스크립트만 둔 미구현 뼈대.

## 다음

1. `axis1_research/runs/*.json`을 deck_harness 입력 스키마로 얇게 변환.
2. `axis2_layouts/envato/*/layouts.md`를 레이아웃 태그 사전으로 정리.
3. 축1 내용 유형과 축2 레이아웃 태그를 매칭하는 rule table 작성.
