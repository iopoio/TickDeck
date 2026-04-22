# TickDeck 다음 할 일

> 오늘 어디까지 왔고 다음에 뭘 할지. 세션 시작 시 여기부터 읽을 것.

## 현재 완료 상태 (2026-04-17)

Phase 1~4 완료 + Critical 3건 수정 완료 (제대리 Antigravity 자율):
- ✅ Google OAuth 완성 (백엔드 리다이렉트 + 프론트 콜백 + JWT localStorage)
- ✅ 토큰 잔액 실제 DB 조회
- ✅ Celery 트랜잭션 + 환불 로직 (`lock_tx_id` + autoretry)
- ✅ 신규 리포 `iopoio/TickDeck` 생성 (기존은 `webtoslide`로 rename)
- ✅ Google Client Secret 재발급 + `.env` 갱신
- ✅ 보안 이중 검증 4-pass 통과

## 진행 중

없음. 제대리/클과장 대기 상태.

## 다음 단계 (우선순위 순)

### 1. 로컬 실행 검증 (선택, 후추님 시간 날 때)
- 4 프로세스 기동: backend (uvicorn) / worker (celery) / redis / frontend (vite)
- 전체 E2E: 로그인 → URL 입력 → PPTX 생성 → 다운로드
- 확인 포인트:
  - Google OAuth 로그인 플로우
  - 토큰 잔액 차감/환불
  - 워커 크래시 시 토큰 복원 (intentionally kill worker)

### 2. High 이슈 4건 (제대리 후속 작업 후보)
1. Surrogate 문자 처리 3곳 중복 → 유틸 함수로 통합
2. PPTX 임시 파일 삭제 정책 (현재 누적됨)
3. EditorPage 중간 저장 (현재 브라우저 새로고침하면 날아감)
4. 크롤러 12,000자 + Gemini 8,000자 이중 제한 → 하나로 정리

### 3. 프로덕션 배포 준비
- Vercel/Railway 환경 결정
- 프로덕션 Google OAuth Redirect URI 등록
- 프로덕션 DB (Supabase? Railway Postgres?)
- 도메인 (tickdeck.io 또는 대체)

### 4. 공모전 출품 검토
- TickDeck 자체는 공모전 매칭 아직 없음
- `Think/contests/` 확인하여 맞는 공모전 나오면 출품

## 후추님 확인 필요 시점

- 프로덕션 배포 진입 전 (비용 + 도메인 결정)
- High 이슈 우선순위 결정 (4건 중 어느 것부터)

## 알려진 외부 리스크
- Gemini API 키(`GEMINI_API_KEY`) - 유료 전환 시점 모니터링
- Google OAuth 프로덕션 승인 필요 (`localhost` 외 도메인 등록 시)

## 관련 파일
- `제대리_Critical수정_지시서.md` — 오늘 끝낸 Critical 3건 원본 지시서
- `.claude/retro/회고.md` — 실수 카운터
- `.env` — 로컬 개발 비밀키 (Google Client Secret 재발급됨)
- `docker-compose.yml` — 로컬 4 프로세스 정의
