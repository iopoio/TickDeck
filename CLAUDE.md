등급: 미디엄

⚠️ 세션 시작 시 `~/.claude/CLAUDE.md` 반드시 읽고 따를 것.

# TickDeck — URL → PPTX 자동 생성 서비스

컨셉: "딸깍" — URL 하나 넣으면 PPTX 바로 다운로드

## 역할 분리
| 작업 | 담당 |
|------|------|
| 시스템 설계, 아키텍처 결정 | 클과장 |
| 버그 수정 (1파일, 단순) | 클과장 |
| 코드 수정 (2파일 이상) | 제대리 |
| 새 기능 구현 | 제대리 |
| 리뷰/QA 판단 | 클과장 |

→ 작업 시작 전 판단: 2파일 이상 or 디버깅 사이클 2회 이상 예상 → 제대리에게 넘김

## 기술 스택
- Backend: FastAPI + SQLAlchemy(asyncpg) + PostgreSQL
- Frontend: React + Vite + TypeScript + Tailwind CSS
- Worker: Celery + Redis (Windows: `--pool=solo --concurrency=1` 필수)
- AI: Gemini `gemini-3.1-flash-lite-preview` (2.5 Flash 초과 사용 금지)
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

## 현재 단계 (Phase 5 진행중)
- [x] Phase 1: DB 모델 + 인증
- [x] Phase 2: 크롤러 + Gemini 연동
- [x] Phase 3: PPTX 빌더
- [x] Phase 4: 프론트엔드 (HomePage/LoadingPage/EditorPage/DonePage) + E2E
- [ ] Phase 5: AI 파이프라인 업그레이드 (WebToSlide 이식)
  - [x] schemas.py — SlideType, BrandInfo.narrative_type 추가
  - [x] quality.py — 신규 (RULE A/J/B 품질 검증)
  - [ ] gemini_client.py — 3단계 에이전트 (Researcher→Strategist→Copywriter) ← 제대리 작업중
  - [ ] crawler.py — Playwright 감지 개선 + 텍스트 정제 ← 제대리 작업중
  - [ ] worker/tasks/generate.py — quality.py 연결 ← 제대리 작업중
  - [ ] Google OAuth 실제 구현 (현재 DEV_TOKEN 하드코딩)
  - [ ] 토큰 시스템 실제 연동

## 알려진 제약
- Windows Celery prefork → PermissionError WinError 5 → solo pool만 사용
- Gemini surrogate 문자 → `_clean_surrogates()` 처리 (gemini_client.py, slides.py)
- 다운로드 엔드포인트 auth-free (UUID가 접근 제어 역할)
- Samsung SEM 등 JS-heavy 사이트 → httpx 크롤러로는 내용 부족
