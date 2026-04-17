# TickDeck Critical 3건 수정 지시서 — 제대리용 (진행 보드판)

작성: 클과장 / 2026-04-17

⚠️ 작업 전 필독: `CLAUDE.md` + `~/.claude/rules/역할-제대리.md`

---

## 배경

TickDeck 코드 리뷰(2026-04-17)에서 Critical 3건 지적됨. 운영 제품 프로덕션 배포 전 필수 수정.

예상 총 작업시간: 8~12시간 (분할 가능)
공모전 마감 없음 (운영 제품). 단, 다중 사용자 서비스 오픈 전 OAuth 필수.

---

## 🔎 현재 상태 (클과장 실측 — 2026-04-17)

| 파일 | 상태 | 요약 |
|---|---|---|
| `backend/routers/auth.py` | ✅ 백엔드 OAuth 엔드포인트 완성 | `/api/auth/google`, `/callback`, `/me` 모두 구현됨. User 생성 + JWT 발급 + 가입 보너스 2토큰 |
| `frontend/src/App.tsx:14` | ❌ DEV_TOKEN 하드코딩 | 3곳에서 사용 (generateSlide, getStatus, confirmGeneration) |
| `backend/routers/tokens.py` | ❌ `{"balance": 0}` 하드코딩 | 9줄짜리 스텁. DB 조회 없음 |
| `worker/tasks/generate.py` | ❌ psycopg2 동기 호출 + 토큰 환불 없음 | 실패 시 `failed` 상태만 저장. 토큰 차감됐으면 사용자 손해 |
| `backend/models/token.py` | ✅ TokenBalance, TokenTransaction 모델 있음 | `signup_bonus`/`generation_lock`/`generation_confirm`/`generation_refund`/`survey_reward` 타입 정의 |

---

## 🎯 Task 분할

### ☐ Task A — Frontend OAuth 완성

**목표**: DEV_TOKEN 제거, 실제 Google OAuth 로그인 → JWT localStorage 저장 → API 호출 시 사용

#### A-1. LoginPage 컴포넌트 신규
- [ ] `frontend/src/pages/LoginPage.tsx` 생성
- [ ] 중앙에 Google 로그인 버튼 (Tailwind)
- [ ] 버튼 클릭 시 `window.location.href = '${API_BASE}/api/auth/google'`
- [ ] 로고 + 서비스 소개 간단 문구
- [ ] API_BASE는 기존 `src/services/api.ts`에서 재사용

#### A-2. Callback 처리
- [ ] `frontend/src/pages/CallbackPage.tsx` 생성 (또는 App.tsx에 useEffect 추가)
- [ ] URL 경로 `/auth/callback` 라우팅
- [ ] URL query에서 `access_token`, `refresh_token` 추출
- [ ] `localStorage.setItem('tickdeck_token', accessToken)`
- [ ] 저장 후 `/` 리다이렉트
- [ ] 백엔드 `/api/auth/callback`은 현재 JSON 응답. 프론트 리다이렉트로 토큰 전달하려면 백엔드 수정 필요 → **아래 A-5 참고**

#### A-3. JWT 유틸
- [ ] `frontend/src/lib/auth.ts` 생성
  ```typescript
  export function getToken(): string | null {
    return localStorage.getItem('tickdeck_token');
  }
  export function setToken(token: string) {
    localStorage.setItem('tickdeck_token', token);
  }
  export function clearToken() {
    localStorage.removeItem('tickdeck_token');
  }
  export function isLoggedIn(): boolean {
    return !!getToken();
  }
  ```

#### A-4. App.tsx DEV_TOKEN 제거
- [ ] `DEV_TOKEN` 상수 삭제
- [ ] `generateSlide(url, language, DEV_TOKEN)` → `generateSlide(url, language, getToken())` (3곳)
- [ ] 앱 진입 시 `isLoggedIn()` 체크 → false면 `<LoginPage />` 렌더
- [ ] 로그아웃 버튼 추가 (기존 UI 적절한 위치 또는 헤더)

#### A-5. 백엔드 callback 수정
- [ ] `backend/routers/auth.py:37` `google_callback`이 JSON 리턴 → **프론트 URL로 리다이렉트로 변경**
- [ ] `RedirectResponse(f"{settings.frontend_url}/auth/callback?access_token={...}&refresh_token={...}")`
- [ ] `settings.frontend_url` 추가 (core/config.py)
- [ ] 로컬 개발: `http://localhost:5173`, 프로덕션: 환경변수

#### A-6. 검증
- [ ] `cd frontend && npm run build` 통과
- [ ] `cd backend && uvicorn main:app --reload` 실행 가능 (에러 없음)
- [ ] 로그인 플로우 수동 테스트 (브라우저):
  - [ ] 로그인 안 된 상태 → LoginPage 표시
  - [ ] Google 버튼 클릭 → Google 로그인 화면 이동 (로컬 Google OAuth client 설정 필요, 기존 `.env` 확인)
  - [ ] 로그인 → /auth/callback → localStorage 토큰 저장 → 홈 리다이렉트
  - [ ] 이후 slide 생성 시 DEV_TOKEN 아닌 실제 토큰 사용 확인

#### A-7. 커밋
- [ ] `feat: Google OAuth 프론트엔드 완성 + DEV_TOKEN 제거 (Task A)`
- [ ] **push 금지**

---

### ☐ Task B — tokens.py 실제 구현

**목표**: `{"balance": 0}` 하드코딩 → 실제 DB 조회

#### B-1. get_balance 구현
- [ ] `backend/routers/tokens.py` 수정
- [ ] `from backend.routers.auth import get_current_user`
- [ ] `@router.get("/balance")` 시그니처 변경:
  ```python
  async def get_balance(
      authorization: str = Header(""),
      db: AsyncSession = Depends(get_db),
  ):
      if not authorization.startswith("Bearer "):
          raise HTTPException(status_code=401, detail="Authorization required")
      token = authorization.split(" ")[1]
      user = await get_current_user(token, db)
      result = await db.execute(select(TokenBalance).where(TokenBalance.user_id == user.id))
      balance_obj = result.scalar_one_or_none()
      return {"balance": balance_obj.balance if balance_obj else 0}
  ```

#### B-2. 거래 내역 엔드포인트 추가 (선택)
- [ ] `@router.get("/transactions")` → 최근 20건 TokenTransaction 반환
- [ ] 프론트에서 토큰 사용 이력 보여줄 때 사용

#### B-3. 프론트 연동
- [ ] `frontend/src/services/api.ts`에 `getBalance()` 추가
- [ ] App.tsx 또는 Header 컴포넌트에 잔액 표시 (예: "토큰 2개")
- [ ] 로그인 후 주기적으로 갱신 (slide 생성 전/후)

#### B-4. 검증
- [ ] 로그인 후 `curl -H "Authorization: Bearer <token>" http://localhost:8000/api/tokens/balance` → 실제 잔액 반환
- [ ] 신규 가입 유저는 2 반환 (auth.py:67 가입 보너스)
- [ ] 빌드 + 프론트 표시 확인

#### B-5. 커밋
- [ ] `feat: 토큰 잔액 API 실제 DB 조회 구현 (Task B)`

---

### ☐ Task C — Celery 안정성 + 토큰 환불

**목표**: 워커 실패 시 토큰 자동 환불 + retry 3회

psycopg2 동기 호출은 **유지** (SQLAlchemy async로 바꾸면 큰 리팩토링. 현재 동작 중이니 안전성만 보완).

#### C-1. 토큰 차감 로직 확인
- [ ] `backend/routers/slides.py` 또는 generation 생성 라우터에서 토큰 차감 구현 여부 확인
- [ ] 없으면 **추가**: generation 생성 시 `transaction_type='generation_lock'`로 -1 차감
- [ ] 차감 트랜잭션 id를 generation 테이블에 FK 저장 (환불용)

#### C-2. 토큰 환불 헬퍼
- [ ] `worker/tasks/generate.py`에 `_refund_token(generation_id)` 함수 추가
  ```python
  def _refund_token(generation_id: str):
      """실패 시 해당 generation의 lock 트랜잭션을 환불"""
      dsn = _get_dsn()
      conn = psycopg2.connect(dsn)
      try:
          with conn.cursor() as cur:
              # generation에서 user_id + lock_tx_id 조회
              cur.execute("SELECT user_id, lock_tx_id FROM generations WHERE id = %s", (generation_id,))
              row = cur.fetchone()
              if not row:
                  return
              user_id, lock_tx_id = row
              if lock_tx_id is None:
                  return  # 이미 환불됨 or 차감 없었음
              # TokenTransaction 생성 (refund)
              cur.execute("""
                  INSERT INTO token_transactions (user_id, transaction_type, amount, note, created_at)
                  VALUES (%s, 'generation_refund', 1, %s, NOW())
              """, (user_id, f"실패 환불: {generation_id}"))
              # TokenBalance 증가
              cur.execute("UPDATE token_balances SET balance = balance + 1, updated_at = NOW() WHERE user_id = %s", (user_id,))
              # generation lock_tx_id 클리어 (중복 환불 방지)
              cur.execute("UPDATE generations SET lock_tx_id = NULL WHERE id = %s", (generation_id,))
          conn.commit()
      finally:
          conn.close()
  ```

#### C-3. generate_slides에서 실패 시 환불
- [ ] `except Exception as e:` 블록에서 `_refund_token(generation_id)` 호출
- [ ] 환불 실패도 로그 남김 (토큰 손실 방지)

#### C-4. Celery retry
- [ ] `@app.task(bind=True, name="tasks.generate_slides", autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 5})`
- [ ] **단, 크롤링 실패 같은 영구 에러는 retry 의미 없음** → 커스텀 exception 분기:
  - `TransientError` (네트워크/timeout): retry
  - `PermanentError` (크롤링 거부, Gemini quota): retry X, 즉시 failed

#### C-5. 마이그레이션 (generation.lock_tx_id 필드 추가)
- [ ] `backend/models/generation.py` Generation 모델에 `lock_tx_id` 컬럼 추가
- [ ] Alembic 마이그레이션 or `Base.metadata.create_all()` 재실행
- [ ] 기존 generation 레코드는 NULL 허용

#### C-6. 검증
- [ ] 크롤링 실패 케이스 수동 테스트: 잘못된 URL로 generate_slide → 토큰 차감 확인 → 실패 후 토큰 복구 확인
- [ ] Celery 로그에서 retry 동작 확인 (timeout URL로 테스트)
- [ ] DB의 token_transactions 테이블에 `generation_refund` 레코드 존재 확인

#### C-7. 커밋
- [ ] `feat: Celery retry + 실패 시 토큰 자동 환불 (Task C)`

---

## ⛔ 중단 조건 (즉시 멈추고 보고)

- 전체 루프 4회 초과
- 같은 파일 4회 이상 수정
- 같은 에러 2회 연속
- 데이터베이스 스키마 변경이 기존 데이터 손실 가능 → 클과장 판단 필요
- OAuth Google client 설정이 `.env`에 없음 → 후추님 확인 필요

## ✋ 수정 권한

- **허용**: `backend/`, `frontend/`, `worker/`, `shared/` 내 파일
- **금지**:
  - `.env`, `.env.example` 수정 (값 추가는 후추님만)
  - `docker-compose.yml` 변경 (운영 구성)
  - `alembic/versions/` 기존 마이그레이션 수정 (append만 OK)
- `git commit` OK, **`git push` 절대 금지**

---

## 📝 Task별 보고 형식

`.claude/inbox/2026-04-XX_HHmm_TaskX_완료.md`에 작성.

```markdown
## Task X 완료 보고

### 변경 파일
- 파일명: 변경 요약

### 신규 파일
- 파일명: 역할

### 검증 결과
- 빌드: 통과/실패
- 수동 테스트: 각 단계 pass/fail + 증거 (curl 응답 원문 or 스크린샷)

### 커밋
- 해시 + 메시지

### 클과장 리뷰 요청
- 특히 봐달라는 부분
- 설계 판단이 필요한 부분

### 블로커 (있다면)
- 후추님/클과장 확인 필요한 것
```

---

## 🏁 완료 조건

다음 전부 충족 시 완료 보고:
1. Task A/B/C 체크리스트 전부 ☑
2. `cd frontend && npm run build` 통과
3. `cd backend && python -m pytest tests/` (테스트 있으면) or `python -c "from backend.main import app"` 임포트 에러 없음
4. 로컬에서 로그인 → 슬라이드 생성 → 완료 플로우 1회 수동 확인
5. 토큰 잔액 표시 + 실패 시 환불 확인

`.claude/inbox/2026-04-XX_Critical_완료.md`에 최종 보고:

```markdown
## TickDeck Critical 3건 완료

- Task A (OAuth): 커밋 해시
- Task B (토큰 잔액): 커밋 해시  
- Task C (Celery + 환불): 커밋 해시

최종 커밋: xxxxx
배포 준비 상태: OK / 블로커 있음
클과장 리뷰 요청 사항: (있으면)
```

---

## 🚫 규칙 재확인

- `git push` 절대 금지
- 거짓 보고 금지 (J2 카운터 6회 누적 중. 실제 확인한 것만 체크)
- DB 스키마 변경은 마이그레이션 파일 생성으로, 직접 SQL 실행 금지
- OAuth 실기기 테스트 시 `.env`의 `GOOGLE_CLIENT_ID/SECRET` 실존 확인
- 같은 에러 2회 → 멈추고 보고
- Gemini 호출은 최소화 (4월 `gemini-2.5-flash` 한도 소진, preview 계열 capacity 불안정)

---

## 🔗 참조

- 회고(실수 카운터): `.claude/retro/회고.md`
- 역할 규칙: `~/.claude/rules/역할-제대리.md`
- 코드 리뷰 원본(참고): Think/sessions/ 에 있었으나 정리됨. 본 지시서의 "현재 상태" 섹션 참조
- 이달여행 Phase5 사례: IdalTrip Task 7에서 제대리 QA 루프 성공적 (1사이클 완료)
