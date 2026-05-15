# TickDeck v2 — 1단계 MVP

본 폴더 = TickDeck v2 1단계 MVP 코드 base. PRD_v2.md·PLAN_implementation.md 정합.

## 목표 (1단계 MVP)

- 마감: 6/9 EOD
- 영역: URL/PDF → PPTX 변환 (Streamlit 기반 minimal viable)
- 산출물: 작동하는 prototype + 5 named agent 영역 협업 검증

## 5 named agents 영역

| Agent | 역할 |
|---|---|
| 본진 클차장 | PM·아키텍처·검증 |
| 제대리 (Gemini CLI) | 복잡 코딩·교차 검증 |
| 양념이 (Gemini Flash) | 인테이크·검증 |
| 노클 (Windows 분신) | PDF·요강 영역 |
| Ralph 루프 | 자율 빌드·base 영역 |

## 진입점

- `app.py` — Streamlit 진입 (현재 placeholder)
- `requirements.txt` — 의존성
- `.gitignore` — Python 표준

## 자세히

- PRD: `../../PRD_v2.md`
- PLAN: `../../PLAN_implementation.md`
- templates: `../../templates.json`
- master_layouts: `../../master_layouts.json`
- mapping_rules: `../../mapping_rules.json`

## 갱신 영역

- 2026-05-15: P4-T1 — base 영역 신설 (Ralph 자율). repo 결정 영역 (기존 TickDeck repo vs 별도 tickdeck-v2 repo) = 후추님 결재 영역 대기
