등급: 미디엄

⚠️ 세션 시작 시 `~/.claude/CLAUDE.md` 반드시 읽고 따를 것.

# TickDeck — URL → PPTX 자동 생성 서비스

컨셉: "딸깍" — URL 하나 넣으면 PPTX 바로 다운로드

## 제품화 (2026-06-30 추가)
- **이거 자체가 유료 제품(B형=라이브 생성기)으로 갈 로드맵 = `PRODUCT_ROADMAP.md`** (Phase 0 베타 쇼케이스 ~ Phase 6 유료 오픈·간트형). 트렐로 "TickDeck 제품화" 리스트로 추적.
- A형(베타 쇼케이스: 펩핀치 진열대 임베드)·B형(유료) 결정 = `[[project_tickdeck_showcase_plan]]`. v4 덱 하네스(`.claude/skills/deck-harness/`)가 품질 엔진.

## 역할 분리
| 작업 | 담당 |
|------|------|
| 시스템 설계, 아키텍처 결정 | 클과장 |
| 버그 수정 (1파일, 단순) | 클과장 |
| 코드 수정 (2파일 이상) | 제대리 |
| 새 기능 구현 | 제대리 |
| 리뷰/QA 판단 | 클과장 |

→ 작업 시작 전 판단: 2파일 이상 or 디버깅 사이클 2회 이상 예상 → 제대리에게 넘김

## 모델 역할 분담 (2026-07-04 후추님 지시)
| 역할 | 모델 | 방법 |
|------|------|------|
| 아키텍처·설계·판단·트리아지·**최종 검수** | Fable 5 (클차장 본체) | 스펙 작성 → 위임 → diff·실측 검수만. **직접 구현 금지**(예외: 5줄 이하 수술) |
| 코드 작성·구현 | **Codex** | `codex exec --skip-git-repo-check "<스펙>"` — 스펙에 파일·수용 기준·테스트 명령 명시 |
| 반복 수정·테스트·서브 파이프라인 | Sonnet 서브에이전트 | Agent 툴 (v4 하네스 에이전트들 포함) |
| 토큰 무거운 선처리 (코드베이스 분석·긴 로그·PDF 대량 읽기·대량 요약) | Sonnet/제대리 | 압축 결과만 본체 컨텍스트로 |

- 검증 게이트는 모델 무관 항상: `test_contracts.py` 28건 + `run_contracts.py` + FIT_OK + PDF 실측.
- 위임 스펙 필수 요소: 대상 파일 경로 / 수용 기준(테스트 명령과 기대 출력) / 건드리지 말 것 목록.
- Codex 결과는 클차장이 diff 검수 후 커밋 (Codex 자체 커밋 금지).

### 단계별 모델 고정 (2026-07-04 후추님 "단계마다 모델 지정" — 세션 모델이 풀려도 이 표가 SoT)
클차장은 **각 작업 시작 시 어느 모델로 하는지 한 줄 선언**하고 진행한다(모델 리셋 방지).

| 제작 단계 | 모델 | 사유 |
|------|------|------|
| 설계·아키타입·문법 정의·page_plan 편집 판단·트리아지·최종 diff/PDF 검수 | **Fable 5** | 사고·판단. "제작 시 Fable로 최대한 생각"(후추님) |
| 엔진 코드 구현(render_deck·contract·page-planner 개조 등) | **Codex** | `codex exec … < /dev/null`. 스펙은 Fable 5가 |
| 반복 렌더·FIT/계약 재검·데모 대량 생성·긴 로그/PDF 대량 읽기·deck_spec 조립 | **Sonnet** | 경제적 grunt. Fable 토큰 보존 |
| 5줄 이하 진짜 사소(오타·1값) | Fable 5 직접 | 위임 왕복이 더 비쌈 |

- **토큰 조언 의무**: Sonnet이 경제적인 grunt가 보이면 클차장이 먼저 "이건 Sonnet이 쌉니다" 제안(후추님 요청). Fable 5 절약 = 오래 감.
- 다양화 깊은 층 SoT = `v3/axis2_layouts/DECK_ARCHETYPES.md` (아키타입 4종·page-planner 개조 범위).

## 기술 스택
- Backend: FastAPI + SQLAlchemy(asyncpg) + PostgreSQL
- Frontend: React + Vite + TypeScript + Tailwind CSS
- Worker: Celery + Redis (Windows: `--pool=solo --concurrency=1` 필수)
- AI: Gemini `gemini-3.1-flash-lite` (GA, 2026-05-13 preview→GA 전환·메일 공지. 2.5 Flash 초과 사용 금지)
- PPTX: python-pptx (shared/pptx_builder.py)

## 실행 명령
```bash
# 백엔드 (TickDeck/ 루트에서)
backend/.venv/Scripts/uvicorn backend.main:app --reload --port 8000

# 프론트엔드
cd frontend && npm run dev

# Celery 워커 (backend/ 에서, Windows 필수 옵션)
cd backend && .venv/Scripts/celery -A worker.celery_app worker --pool=solo --concurrency=1 --loglevel=info
```

## 주요 경로
- `.env` → `TickDeck/.env` (루트)
- PPTX 저장 → `backend/tmp/pptx/` (절대경로로 저장됨)
- DB 마이그레이션 → `cd backend && .venv/Scripts/alembic upgrade head`

## 현재 단계 (SaaS 층 Phase 1~5 완료 — 2026-07-03 실사 확인)
- [x] Phase 1: DB 모델 + 인증
- [x] Phase 2: 크롤러 + Gemini 연동
- [x] Phase 3: PPTX 빌더
- [x] Phase 4: 프론트엔드 (HomePage/LoadingPage/EditorPage/DonePage) + E2E
- [x] Phase 5: AI 파이프라인 업그레이드 (WebToSlide 이식) — 전 항목 구현 확인(7/3 실사)
  - [x] gemini_client.py — 3단계 에이전트 (Researcher→Strategist→Copywriter)
  - [x] crawler.py — Playwright 감지 (JS 렌더링 감지 → 자동 재시도)
  - [x] worker/tasks/generate.py — quality.py 연결 (validate_and_fix)
  - [x] Google OAuth 실제 구현 (DEV_TOKEN 제거·프로덕션급)
  - [x] 토큰 시스템 연동 (생성 시 1 차감·실패 시 자동 환불)
- 미구현: 결제 API (PRODUCT_ROADMAP Phase 5), v4 하네스와의 연결 (Phase 1 엔진 1콜화)

🧊 **SaaS 층 동결 선언 (2026-07-08·PLAN_SEED)**: seed 덱 4주 수요 검증(PLAN_SEED_2026-07-08.md)이 끝날 때까지 backend/frontend/shared(Gemini 파이프라인)는 수정 금지. 이 기간 품질·엔진 작업도 seed 덱에 필요한 것만(렌더·문체 다듬기 커밋 금지). 게이트 판정 후 거취 재결정.

⚠️ **두 엔진 괴리 주의**: 이 SaaS 파이프라인(Gemini 3단계→python-pptx·PPTX 출력)과 v4 덱 하네스(Claude 에이전트 9단계→HTML/PDF·계약 게이트)는 **별개 엔진**이다. 검증·품질 체계는 v4에만 있다. 제품 품질 작업 = v4 하네스가 SoT. SaaS 층은 PRODUCT_ROADMAP Phase 1(엔진 1콜화)에서 v4를 감싸는 방향. backend/frontend는 2026-04-17, shared는 2026-05-13 이후 동결 상태 — Phase 3(서비스 래핑) 착수 전 재점검 필요.

## 알려진 제약
- Windows Celery prefork → PermissionError WinError 5 → solo pool만 사용
- Gemini surrogate 문자 → `_clean_surrogates()` 처리 (gemini_client.py, slides.py)
- 다운로드 엔드포인트 auth-free (UUID가 접근 제어 역할)
- Samsung SEM 등 JS-heavy 사이트 → httpx 크롤러로는 내용 부족

## TickDeck 하네스 v4 포인터

트리거:
- 발표자료, 덱, 트렌드 리포트, 주제 발표자료, 다시, 업데이트, 보완 요청은 `.claude/skills/deck-harness/SKILL.md`를 먼저 사용한다.
- 트렌드 리포트 장르는 `.claude/skills/genre-trend-report/SKILL.md`를 함께 사용한다.
- 일반 주제 발표 장르는 `.claude/skills/genre-topic-deck/SKILL.md`를 함께 사용한다.
- 시장조사·경쟁분석·"X 시장에서 브랜드 Y" 장르는 `.claude/skills/genre-market-research/SKILL.md`를 함께 사용한다 (분류 트리·플레이어 비교표 필수).
- 완료 전 5대 계약은 `.claude/skills/harness-contracts/scripts/test_contracts.py`로 실행 확인한다.

주의:
- `.claude/commands/`는 만들지 않는다.
- 디자인은 page-plan 이후에만 수행한다.
- 검증 메타데이터를 사용자용 슬라이드 콘텐츠에 노출하지 않는다.

변경 이력:
- 2026-06-28: PRD v4.1 기준 에이전트+스킬 하네스 포인터 추가.
- 2026-07-03: Phase 5 stale 표기 정정(전 항목 구현 완료 실사 확인)·두 엔진 괴리 주의 추가.
