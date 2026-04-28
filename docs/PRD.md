# Product Requirements Document: TickDeck (틱덱)

**작성자**: 클차장 (후추님 본진)
**작성일**: 2026-04-26
**상태**: Draft v1.0 (Claude Design 출시로 본질 영역 흡수, 차별화 재정립 또는 개인 도구 옵션)
**소유자**: 후추님 (시즌드 사업자, 1인 인디해커)
**진행 상태**: Phase 4 완료, Phase 5 진행 중

---

## 0. 사업 vs Phase 구분 (특이 케이스)

> **TickDeck은 본 사업 → 시장 흡수로 재정의 영역**.

| 레벨 | 내용 |
|---|---|
| **원래 비전 (장기)** | URL → PPTX 자동 생성. "딸깍" 컨셉. 토큰 기반 SaaS |
| **2026-04-18 시장 변화** | Anthropic Claude Design 출시. 자연어 + 파일 + **웹 캡처(URL)** → PPTX·Canva·PDF·HTML. **TickDeck 본질 영역 거의 흡수** |
| **현재 결정 영역** | 4가지 옵션 (아카이브 / 차별화 재정립 / Claude Design wrapper / 개인 도구) |
| **클차장 추천** | **개인 도구로 놔두기** (1~2개 집중·FIRE 노선 정합) |

> 후추님 회고 2회: "텍덱이 이런식이 되었으면 ㅎㅎ" → "이거야 말로 바로 틱덱 아니냐고"

---

## 1. Executive Summary

TickDeck은 URL 한 줄로 PPTX를 자동 생성하는 "딸깍" 도구다. Phase 4까지 프론트엔드 4페이지 + E2E 파이프라인 완료, Phase 5에서 3에이전트(Researcher→Strategist→Copywriter) + quality.py 신규 구축. 단 2026-04-18 Claude Design 출시로 본질 영역(자연어→슬라이드, URL 웹 캡처)이 거의 흡수됨. 본 PRD는 차별화 재정립 또는 개인 도구 결정의 근거 자료.

---

## 2. Background & Context

### 시장 변화 (2026-04-18)
- Anthropic Claude Design 출시 (claude.ai/design, Opus 4.7 엔진)
- 자연어 + 파일 + 이미지 + **웹 캡처(URL)** → PPTX·Canva·PDF·HTML
- Claude Code 핸드오프 → 프로덕션 코드까지 완결
- Claude Pro 이상 구독자 무료 (사실상)
- Figma 주가 출시 당일 하락 (시장 충격)

### TickDeck 차별화 가능 영역 (Claude Design이 못 하는)
1. **분석·트래킹**: Featpaper 스타일 (Claude Design 없음)
2. **한국 특화**: 한국식 슬라이드 템플릿·한국어 폰트·한국 SaaS 가격 (예: 신학기·연말정산·공모전 템플릿)
3. **무료 + 광고 모델**: Claude Design은 Pro 이상 유료
4. **RSS·메타데이터 자동 큐레이션**: 단순 URL 캡처 X, 정기 발행 자동화

### 진행 상태
- Phase 4 완료: 프론트엔드 4페이지 + E2E
- Phase 5 진행 중: 3에이전트 + quality.py
- 제대리 작업 중: gemini_client.py, crawler.py 개선
- DEV_TOKEN 하드코딩 (OAuth 미구현)

---

## 3. Objectives & Success Metrics

### Goals (옵션별)

#### 옵션 1. 아카이브
- 결정만. Phase 5+ 진행 X. 코드 보존, 운영 X

#### 옵션 2. 차별화 재정립 (Phase 5 변경)
1. 분석·트래킹 통합 (Featpaper 스타일)
2. 한국 특화 템플릿 (10+)
3. 무료 + 광고 BM
4. **위험**: 6~12개월 후 Claude Design이 한국어·분석 추가하면 또 흡수

#### 옵션 3. Claude Design wrapper
1. Claude Design API 백엔드
2. 한국어 UI + 한국 템플릿 얹기
3. **위험**: Anthropic 정책 변경 시 의존

#### 옵션 4. 개인 도구로 놔두기 (클차장 추천)
1. 후추님 본인 슬라이드 자동 생성용
2. 시장 진출 X (1~2개 집중 노선)
3. Phase 5 잔여 = 본인 사용 만족도 위주

### Non-Goals
1. 풀스택 SaaS화 (옵션 4 시)
2. Claude Design 직접 경쟁 (옵션 2도 좁은 영역만)
3. 글로벌 (한국 특화 차별화)

### Success Metrics (옵션 4 기준)
| Metric | 현재 | 목표 |
|---|---|---|
| 후추님 본인 사용 빈도 | 0 | 월 1+ |
| 슬라이드 생성 만족도 (자체) | [미확인] | 80%+ |
| Phase 5 잔여 작업 | 진행 중 | 본인 만족 시 종료 |

---

## 4. Target Users & Segments

### 옵션 4 (개인 도구) 기준
- 후추님 본인만

### 옵션 2 (차별화) 기준
- 한국 SaaS·콘텐츠 운영자 (분석·트래킹 가치 인지층)
- 공모전·기획서 작성 빈도 높은 사용자

---

## 5. User Stories & Requirements

### P0 (옵션 4 기준 — 본인 도구)

| # | User Story | Acceptance Criteria |
|---|---|---|
| P0-1 | 후추님으로서 URL 한 줄로 PPTX 받는다 | Phase 4 완성도 유지 |
| P0-2 | 후추님으로서 3에이전트 결과 안정 | Phase 5 quality.py 통과 |
| P0-3 | 후추님으로서 한국식 템플릿 1~2개 활용 | 본인 만족 |

### P1 (옵션 2 기준 — 차별화 재정립)

| # | User Story | Acceptance Criteria |
|---|---|---|
| P1-1 | 한국 사용자로서 신학기·연말정산·공모전 템플릿 본다 | 템플릿 10+ |
| P1-2 | 운영자로서 슬라이드 트래킹 본다 | Featpaper식 |
| P1-3 | 사용자로서 무료 + 광고로 사용 | AdSense |

### P2 (사업화 시)
1. RSS·정기 발행 자동화
2. 회원·구독
3. API

---

## 6. Solution Overview

### 현 기술 스택 (Phase 5 진행 중)
- Backend: FastAPI + Celery
- Frontend: Next.js
- AI: Gemini 3.1 Flash Lite Preview (메모리 명시)
- 데이터: Pickle 또는 SQLite [코드 직접 확인]
- 환경: Windows Celery `--pool=solo --concurrency=1` 필수

### Claude Design 정합성 영역
- TickDeck = URL → PPTX 직접 (특수 케이스 자동화)
- Claude Design = 자연어 + 다양한 입력 (범용)
- = 일부 사용자 케이스에서 TickDeck 더 빠를 수 있음 (URL 한 줄)

---

## 7. Open Questions

| Question | Owner | Deadline |
|---|---|---|
| 옵션 4가지 중 결정 | 후추님 | 5/15 |
| Phase 5 잔여 작업 (제대리 결과) | 클차장 (제대리 회신 검토) | 즉시 |
| Gemini 모델 ID 정합성 | 클차장 (코드 확인) | 즉시 |
| 옵션 2·3 진행 시 시장 진입 시점 (Claude Design 한국어 추가 모니터링) | 후추님 | 6개월 추적 |

---

## 8. Timeline & Phasing

### 옵션 4 (추천) 기준

#### Phase 5 (지금 ~ 본인 만족 시)
- 제대리 결과 통합 (3에이전트 + quality.py 안정화)
- 후추님 본인 사용 시범
- 만족 시 종료

#### Phase 6+ X
- 시장 진출 X
- 다른 프로젝트 (잡솔트·EatScan·펩핀치) 우선

### 옵션 2 (차별화) 기준 — 후추님 결정 시

#### Phase 5 (~ 5/15)
- 본인 결정
- 한국 특화 템플릿 시드 5개

#### Phase 6 (~ 7월)
- 분석·트래킹 통합
- 무료 + 광고 BM 시드

#### Phase 7 (~ 연말)
- Claude Design 한국어·분석 추가 모니터링
- 흡수 시 옵션 4 전환

### 후추님 1인 노선 정합성
- 1~2개 집중 + FIRE 2033 + 슬렁슬렁 = **옵션 4 강력 정합**
- 옵션 2·3 진행 시 자원 분산 (잡솔트·EatScan·펩핀치 영역 침범)

---

## 변경 이력
| 일자 | 변경 |
|---|---|
| 2026-04-26 | v1.0 Draft — Claude Design 시장 변화 정면 반영 + 4옵션 구조 + 옵션 4 추천 |
