# 세션 핸드오프 — UPGRADE_PLAN.md & CLAUDE.md 사실검증 리뷰 (2026-07-03)

> 후추님 보고용 TickDeck 실사 리뷰 검증 자료입니다. 요청하신 6건의 핵심 주장에 대해 실제 코드와 Git 로그를 바탕으로 교차 검증을 진행했습니다.

## 한 줄 요약
**검증 대상 6건의 주장 모두 실제 코드 및 Git 히스토리와 정확히 일치하여 6건 모두 "참"으로 판정되었습니다.**

---

## 6대 핵심 주장 검증 결과

### 1. SaaS Phase 5 전 항목 구현 완료
- **판정**: **참 (True)**
- **상세 근거**:
  - **3단계 에이전트 파이프라인**: [gemini_client.py](file:///Users/hwa/Projects/Automation/TickDeck/shared/shared/gemini_client.py#L60-L214)에서 `Researcher` → `Strategist` → `Copywriter` 순으로 실행하는 구조가 `generate_slide_content` 내에 정확히 구현되어 있습니다.
  - **Playwright 자동 재시도**: [crawler.py](file:///Users/hwa/Projects/Automation/TickDeck/shared/shared/crawler.py#L311-L320)에서 텍스트 길이가 500자 미만이거나 `<noscript>` 태그가 감지되면 Playwright를 이용해 자동으로 재시도합니다.
  - **validate_and_fix 연결**: [generate.py](file:///Users/hwa/Projects/Automation/TickDeck/worker/tasks/generate.py#L16)에서 `validate_and_fix`를 import하여 [line 139](file:///Users/hwa/Projects/Automation/TickDeck/worker/tasks/generate.py#L139)에서 품질 검사 및 자동 수정을 수행합니다.
  - **프로덕션급 OAuth (DEV_TOKEN 없음)**: [auth.py](file:///Users/hwa/Projects/Automation/TickDeck/backend/routers/auth.py#L23-L94)에 실제 Google OAuth의 Redirect 및 Callback API가 구현되어 있으며, `backend/` 내 모든 파일에 `DEV_TOKEN` 하드코딩이 존재하지 않습니다.
  - **토큰 차감 및 실패 환불**: [slides.py](file:///Users/hwa/Projects/Automation/TickDeck/backend/routers/slides.py#L55-L68)에서 요청 시 토큰 1개를 즉시 차감(lock)하며, [generate.py](file:///Users/hwa/Projects/Automation/TickDeck/worker/tasks/generate.py#L56-L89)의 `_refund_token`을 통해 작업 실패(영구 오류 또는 재시도 초과) 시 자동으로 잔액이 복구(환불)됩니다.

### 2. SaaS 파이프라인과 v4 하네스는 별개 엔진
- **판정**: **참 (True)**
- **상세 근거**: 
  - FastAPI/Celery 기반의 구세대 SaaS 파이프라인(Gemini 3단계 → `python-pptx` 빌드)과 v4 덱 하네스(Claude 9단계 → HTML/PDF 및 계약 검증)는 임포트나 함수 호출을 주고받지 않는 완전히 분리된 코드 경로를 가집니다.
  - **관련 파일**: [CLAUDE.md](file:///Users/hwa/Projects/Automation/TickDeck/CLAUDE.md#L61-L62), [UPGRADE_PLAN.md](file:///Users/hwa/Projects/Automation/TickDeck/UPGRADE_PLAN.md#L45-L46)

### 3. capture_deck.sh의 4종 시각 QA 오탐 자동 검출
- **판정**: **참 (True)**
- **상세 근거**:
  - [capture_deck.sh](file:///Users/hwa/Projects/Automation/TickDeck/.claude/skills/deck-harness/scripts/capture_deck.sh#L34-L90) 스크립트 내부의 DOM dump/script 분석 로직에서 다음 4가지를 검출합니다.
    1. **세로 오버플로 (`ovf`)**: `gap < -2` (본문 높이가 컨테이너 높이 초과)
    2. **가로 오버플로 (`hovf`)**: `b.scrollWidth - b.clientWidth > 4` (가로 폭 초과)
    3. **과소밀도 (`sparse`)**: `gap > 240` (레이아웃 제외 빈 공간 과다)
    4. **저대비 무독 (`lowc`)**: `Math.abs(fg-bg) < 0.08` (글자색과 배경색의 근소 명도차 추출)

### 4. harness-contracts C1~C6의 test_contracts.py 실행 및 통과
- **판정**: **참 (True)**
- **상세 근거**:
  - [test_contracts.py](file:///Users/hwa/Projects/Automation/TickDeck/.claude/skills/harness-contracts/scripts/test_contracts.py#L6-L15)에 C1~C6 계약 검증 로직(`validate_c1`~`validate_c6` 및 `validate_all_contracts`)을 검사하는 28개 테스트 케이스가 작성되어 있습니다.
  - `python3 .claude/skills/harness-contracts/scripts/test_contracts.py` 명령어를 통해 실행을 확인한 결과, **28개 테스트 전체가 정상 작동하며 통과(OK)**했습니다.

### 5. backend 및 frontend의 최종 커밋 날짜 동결
- **판정**: **참 (True)**
- **상세 근거**:
  - Git 로그 확인 결과, `backend` 및 `frontend` 하위 폴더에 반영된 마지막 커밋은 모두 `2026-04-17` (`505e105 feat: Critical 3건 수정 (OAuth/토큰/Celery) + frontend 추적 시작`)로 확인되었습니다.
  - 따라서 backend는 2026-05-13 이후, frontend는 2026-04-17 이후 커밋이 추가되지 않은 동결 상태가 맞습니다.

### 6. editorial_serif 테마 CSS 오버라이드의 기존 테마 무영향
- **판정**: **참 (True)**
- **상세 근거**:
  - [render_deck.py](file:///Users/hwa/Projects/Automation/TickDeck/.claude/skills/deck-harness/scripts/render_deck.py#L2843-L2915) CSS 템플릿 후반부에 신설된 `editorial_serif` 레이아웃/스타일 관련 규칙은 모두 `.theme-editorial-serif` 스코프로 한정되어 적용됩니다.
  - 전역 수준에서 추가된 `--font-body`, `--font-head` 변수 역시 다른 테마에는 기본 Pretendard 폰트로 안전하게 폴백되도록 설계되어 기존 테마의 시각 레이아웃에 사이드 이펙트를 미치지 않습니다.
