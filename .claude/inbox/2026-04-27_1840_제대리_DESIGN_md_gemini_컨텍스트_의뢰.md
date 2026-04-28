# 제대리 핸드오프 — TickDeck DESIGN.md 시스템 프롬프트 통합

> 발신: 클차장 / 수신: 제대리 / 일자: 2026-04-27 18:40 KST
> 라벨: AI 디자인 톤 일관성 (디자인 톤 튐 차단)

## 1) 배경

후추님 결재 (4/27 ① Y): TickDeck DESIGN.md 도입.
- 위치: `c:/Projects/Automation/TickDeck/DESIGN.md` (v0.1, 클차장 작성)
- 목적: AI(Gemini) 슬라이드 생성 시 매번 디자인 톤 튐 차단
- 메모리 정합: `feedback_design_md_workflow` (DESIGN.md 우선 워크플로우)

## 2) 현재 상태

DESIGN.md 작성됨. 단 `gemini-prompts/` 시스템 프롬프트엔 아직 미반영. 슬라이드 생성 시 DESIGN.md 토큰·룰이 AI에 전달 X 상태.

## 3) 의뢰 항목 (3건)

### 항목 1: 시스템 프롬프트에 DESIGN.md 컨텍스트 박기
- 대상: `TickDeck/gemini-prompts/` 시스템 프롬프트 파일들
- 작업: 슬라이드 생성 호출 시 DESIGN.md 토큰·룰을 컨텍스트로 포함
- 형식: DESIGN.md 파일 전체 첨부 또는 핵심 토큰만 압축 인라인
- DESIGN.md 6번 섹션 "AI 호출 룰 (Gemini 슬라이드 생성)" 참조

### 항목 2: 결과물 lint 검증 스크립트
- 슬라이드 생성 결과 (PPTX 또는 HTML)에서 DESIGN.md 토큰 위반 검출
- 검증 항목:
  - 토큰 외 색 사용
  - 폰트 위계 무시 (h1·h2·h3 순서)
  - 페이지 가장자리 여백 60pt 미만
  - AI 디자인 함정 (보라·핑크 그라디언트, 패스텔 무지개) 자동 검출
- 위반 시 재생성 자동 트리거 또는 경고

### 항목 3: 단위 테스트
- DESIGN.md 토큰 변경 시 시스템 프롬프트 자동 갱신 확인
- 1개 시술 코드(라식 또는 백내장 추천) 시뮬 슬라이드 1장 생성 + lint 통과 확인

## 4) 검증 게이트

| 단계 | Pass 조건 | Fail 시 |
|---|---|---|
| 시스템 프롬프트 갱신 | DESIGN.md 컨텍스트 포함 + 기존 프롬프트와 정합 | 보고 후 클차장 리뷰 |
| lint 스크립트 | 의도적 위반 슬라이드에서 검출 OK | 디버그 후 재제출 |
| 단위 테스트 | 슬라이드 1장 생성 + lint 통과 | "막힘" 보고 |

## 5) 거짓 보고 방지 (재확인)

- 작업 후 실 슬라이드 생성 1회 + 결과 첨부 후에만 "완료"
- "코드 수정만" = "완료 X" — 메모리 `feedback_jedaerii_handoff_relay` + 4/27 페널티 1차 사례 정합
- 의존성 체크리스트: gemini-prompts/·backend/·frontend/ 영향 받는 파일 사전 매핑

## 6) 무한루프 방지

- 같은 에러 2회 → 멈추고 보고
- 같은 파일 3회+ 수정 → 접근 재검토
- 시간 압박 X (TickDeck 데드라인 X) — 신중히 마무리

## 7) 디자인 게이트 룰

- DESIGN.md 자체 변경은 후추님 명시 결재 필수
- 본 의뢰 = 시스템 프롬프트·lint·테스트만 (DESIGN.md 토큰 변경 X)
- 토큰 변경 필요 시 별도 결재 의뢰

## 8) ETA

제대리 자체 결정. TickDeck 데드라인 X라 시간 압박 작음.

## 9) 회신 위치

`TickDeck/.claude/inbox/YYYY-MM-DD_HHMM_제대리_DESIGN_md_통합_회신.md`

## 10) 자기 도구 부트스트랩 X

본 의뢰 = 일반 코드 작업. jedaerii_worker 변경 X.

## 11) 참조

- TickDeck DESIGN.md: `TickDeck/DESIGN.md` (v0.1)
- 메모리: `feedback_design_md_workflow` (2026-04-27 신설)
- 분석 산출: `Think/.claude/inbox/2026-04-27_긱뉴스_분석_DESIGN_md.md`
