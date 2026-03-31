# TickDeck 제품 로드맵

> 범례: ✅ 완료 · 🟡 중요 · 🟢 추후

---

## ✅ 완료된 작업

### 서비스 인프라
- ✅ **DigitalOcean 배포** — Singapore 4GB, Nginx + HTTPS + Gunicorn (gevent)
- ✅ **Google OAuth** — 소셜 로그인 + 세션 관리
- ✅ **토큰 시스템** — 가입 2개 + 차감/환불 + 설문 충전
- ✅ **생성 이력** — DB 기록 + 직전 PDF 보관 + 인라인 PDF 다운로드
- ✅ **PDF 변환** — LibreOffice 서버사이드 (PPTX→PDF 동일 결과)
- ✅ **랜딩 페이지** — Poseidon 컬러 테마 + 서비스 소개
- ✅ **모바일 반응형** — landing + app 페이지
- ✅ **Celery + Redis** — 백그라운드 작업 큐 (멀티 유저 동시 처리)
- ✅ **관리자 페이지** — 사용자/토큰/생성이력/설문 관리 + CSV 다운로드
- ✅ **설문 시스템** — 9문항 + 토큰 보상 + 계정당 1회
- ✅ **카카오페이 후원** — 커피 한 잔 후원하기 (수수료 0%)
- ✅ **보안 강화** — convert-pdf 인증 + 개인정보 안내 문구
- ✅ **Beta 표시** — 랜딩 + 앱 헤더

### 슬라이드 엔진
- ✅ **컬러 감지 3중 검증** — CSS + 파비콘 교차검증 + 스크린샷 fallback
- ✅ **파비콘 교차검증 개선** — CSS 선명색 있으면 파비콘 override 안 함
- ✅ **사이트 배경색 반영** — 밝은 파스텔/크림 배경 → 슬라이드 배경 적용
- ✅ **모노크롬 사이트 대응** — 파비콘 선명색으로 override
- ✅ **20+ 레이아웃** — cover/split/cards/portfolio/cta + pm_ 함수 20종
- ✅ **3-Font System** — Pretendard + NotoSerifKR + BlackHanSans PPTX 내장
- ✅ **4가지 내러티브** — A(마케팅) / B(대기업) / C(크리에이티브) / D(럭셔리)
- ✅ **노이즈 필터** — 범용 nav/위젯 텍스트 제거 + nameKo 검증
- ✅ **빈 슬라이드 제거** — body 2개 미만 자동 삭제
- ✅ **C-type body 보충** — 프롬프트 강화 + Gemini 2차 보충 패스
- ✅ **이미지 없는 split/portfolio 전환** — cards/two_col_text 자동 분산
- ✅ **이미지 비율 보존** — bg_aspect PIL 계산 + contain/cover 정확 배치
- ✅ **이미지 힌트 금지어 필터** — handshake/puzzle 등 자동 교체
- ✅ **Gemini 비용 최적화** — factbook 4000자 제한 (토큰 30~40% 절감)

### 디자인
- ✅ **TickDeck 브랜딩** — Poseidon 팔레트 + 라이트 테마
- ✅ **TickDeck 로고/파비콘** — 다이아몬드 레이어 + 체크마크 SVG (v2)
- ✅ **Poseidon 컬러 완전 이관** — 블루/보라 잔재 제거 + 웜톤 그레이 통일
- ✅ **Phase 8 스타일 현대화** — 라디우스 통일 (0.14~0.16")
- ✅ **분홍 분리선 수정** — accentColor2 → accentLight 통일
- ✅ **커버 디자인 다양화** — 이미지 없는 A/B/D 커버에 보조 데코 + 워터마크
- ✅ **앱 배경 그라데이션** — nav 연결 웜톤 gradient

### 사용자 기능
- ✅ **생성 이력 UX** — 상태 배지 + 인라인 PDF 다운로드
- ✅ **슬라이드별 재생성** — AI 재생성 버튼 (토큰 소모 없음)
- ✅ **컬러 오버라이드** — 클릭 → 컬러 피커 → 미리보기 즉시 반영
- ✅ **슬라이드 순서 이동** — ▲/▼ 버튼으로 순서 변경
- ✅ **슬라이드 텍스트 편집** — 헤드라인/서브/본문 직접 수정

### 품질 개선 (최근)
- ✅ **저작권 연도 동적화** — new Date().getFullYear()
- ✅ **아이브로우 필 폭 제한** — 3.5" 캡 (오버플로우 방지)
- ✅ **Portfolio body 확대** — 1개 → 3개 표시
- ✅ **로고 aspect 검증** — 세로형/극단형 오감지 스킵
- ✅ **빈 body fallback** — sub로 자동 대체

### 최근 추가 (2026-03-27)
- ✅ **영문 페이지** — /en 랜딩 + /en/app + 언어 스위처
- ✅ **슬라이드 언어 선택** — 한국어/영어 pill + Gemini 프롬프트 분기
- ✅ **Ko-fi 해외 후원** — 위젯 버튼 (#5A9E86)
- ✅ **카카오페이 QR 모달** — PC 스캔 + 모바일 클릭
- ✅ **SSE 자동 재연결** — 끊기면 3초마다 재시도 (최대 30회)
- ✅ **PDF 자동 저장** — fetchAndRenderResult 완료 후 백그라운드 저장
- ✅ **SEO** — og:image, Twitter Card, robots.txt, sitemap.xml, hreflang
- ✅ **앱 nav** — glassmorphism + 로고 + user bar
- ✅ **버전 표시** — v11.0 / 모든 페이지 푸터
- ✅ **Playwright 동적 wait** — 하드코딩 timeout 제거 (~15-20초 절감)
- ✅ **body 보충 최적화** — 3개 이상일 때만 Gemini 호출

---

## ✅ 최적화 완료 (2026-03-27)

- ✅ **Playwright 동적 wait** — 하드코딩 timeout 11곳 제거 (~15-20초 절감)
- ✅ **HTTP Session 풀링** — requests.get() → _session.get() (~10-20초 절감)
- ✅ **body 보충 조건 강화** — 3개 이상일 때만 Gemini 호출 (~500-1K 토큰)
- ✅ **언어별 캐시 분리** — slide_{name}_en_text.json
- ✅ **import 정리** — session/redirect top-level

---

## ✅ 추가 완료 (2026-03-27 후반)

- ✅ **랜딩 디자인 리뉴얼** — 2컬럼 히어로 + 밝은 Steps + 둥근 CTA + 새 푸터
- ✅ **텍스트 로고** — Tick(네이비) + Deck(그린), weight 800 (모든 페이지)
- ✅ **앱 디자인 폴리시** — 카드/인풋/버튼 라운딩 14~20px + 소프트 보더
- ✅ **영어 슬라이드 생성** — Gemini CRITICAL LANGUAGE OVERRIDE
- ✅ **EN 디자인 통일** — KO와 동일 디자인 + 전체 텍스트 영문화
- ✅ **앱 SEO** — canonical, hreflang, OG 태그 (KO + EN)
- ✅ **SSH 직접 배포** — ssh root@서버 "명령어" 방식 확보
- ✅ **커버 세로줄 제거** — 이미지 없는 커버 depth 라인 삭제
- ✅ **7p 텍스트 여백 균등화** — checklist pills 번호 박스 위아래 맞춤
- ✅ **9p 회사명 위치 조정** — 구분선과 가까워지도록

---

## ✅ 추가 완료 (2026-03-28)

- ✅ **SSE job_id 복원** — DB 저장 + 페이지 로드 시 자동 재연결
- ✅ **processing 자동 실패** — 10분 초과 시 토큰 환불
- ✅ **5p 카드 하단 허전함** — heading+desc 세로 중앙 정렬
- ✅ **Playwright 캐시** — 중복 호출 제거 (30~40초 절감)
- ✅ **코드 정리** — cache 유틸 공유 + timeout 상수 통일
- ✅ **primaryColor 함수 추출** — 260줄 → color_resolver.py 분리
- ✅ **사이트맵 도메인 루트 수정** — 깊은 URL 입력 시 sitemap 못 찾던 버그
- ✅ **EN 앱 한글 잔존 텍스트 수정** — 진행 UI/모달/설문 전부 영문화
- ✅ **피드백 시스템** — 모달 + API + 관리자 뷰 (KO/EN)
- ✅ **GitHub MCP 설정** — 연결 확인 완료
- ✅ **레이아웃 연속 중복 방지** — creative_approach → two_col_text 매핑 추가
- ✅ **이미지 중복 배정 방지** — 시맨틱 매칭 used_indices 추적

---

## ✅ 추가 완료 (2026-03-31) — 보안·품질·디자인 대규모 업데이트

### 보안 (7건)
- ✅ **OAuth CSRF** — state 토큰 생성 + 콜백 검증
- ✅ **SECRET_KEY** — 경고 + 세션 쿠키 HttpOnly/Secure/SameSite
- ✅ **SSRF 방지** — localhost/private/169.254/224/240 + metadata.google 차단
- ✅ **Rate Limiting** — Flask-Limiter + Redis (signup 5/h, login 10/h, generate 10/h)
- ✅ **Admin XSS** — esc() 함수 + 리다이렉트
- ✅ **에러 메시지 일반화** — 시스템 정보 미노출
- ✅ **brand_extractor 크래시** — 변수 7개 사전 초기화

### AI 품질 (4건)
- ✅ **시맨틱 검증** — RULE J 숫자 일치 + body 최소 2개 + 헤드라인 28자
- ✅ **데이터 부족 축소** — 충실도 < 30% → 5~6개 슬라이드
- ✅ **타입 강제 경고** — 자동감지 ≠ 강제 시 로그
- ✅ **CTA RULE F** — 시간 약속 자동 감지 + 수정

### 인프라 (4건)
- ✅ **DB 인덱스** — 7개 (email, user_id, status, job_id 등)
- ✅ **토큰 원자성** — WHERE tokens >= 1 (레이스 컨디션 방지)
- ✅ **Celery 타임아웃** — SoftTimeLimitExceeded → 환불 + 에러 전달
- ✅ **SSE 지수 백오프** — 3s→6s→12s→최대 30s

### 코드 통합 (1건)
- ✅ **KO/EN i18n 통합** — i18n.py (110 HTML + 92 JS 키) + index_en.html 삭제 (-6,330줄)

### Phase 3 품질 강화 (5건)
- ✅ **PM 상수 객체** — W/H 중복 5곳 제거 + 공통 레이아웃 상수
- ✅ **ARIA 접근성** — nav label, 편집 모달 role="dialog", ESC 닫기
- ✅ **영문 톤 가이드** — MOOD_TONE_EN 3종 (trendy/professional/minimal)
- ✅ **품질 메트릭** — _quality 객체 (슬라이드 수, 빈 body, 충실도)
- ✅ **로그아웃 동기화** — location.reload() 추가

### 디자인 폴리시 (14건)
- ✅ **동심원 radius** — 외부 24, 패딩 16, 내부 8 (랜딩 KO+EN)
- ✅ **transition 구체화** — all → 구체적 속성 (랜딩+앱 전체)
- ✅ **active 피드백** — CTA 버튼 scale(0.96)
- ✅ **text-wrap** — balance(헤딩) + pretty(본문) 전 페이지
- ✅ **히트 영역** — 언어 전환/이력/로그아웃 패딩 확장
- ✅ **이미지 outline** — 1px rgba(0,0,0,0.08)
- ✅ **로딩 피드백** — "⏳ 생성 중..." + 완료/에러 복원
- ✅ **PPT 타이포** — sub 14px bold, body 12.5px (위계 분리)
- ✅ **PPT 보더** — 0.75→0.5px (세밀화)
- ✅ **PPT 오버레이** — transparency 40→32 (가독성 강화)
- ✅ **PPT 텍스트 대비** — textOnAccentLight 자동 계산

### QA 대응 (8건)
- ✅ **EN 편집 모달 한글** — 12개 키 영문화
- ✅ **EN 에러 모달 한글** — error_user_msg 영문화
- ✅ **EN 커피 모달 한글** — 랜딩 3곳 영문화
- ✅ **Rate Limit Redis** — memory:// → Redis 스토리지
- ✅ **SSRF 169.254** — 링크-로컬+멀티캐스트+예약 차단
- ✅ **EN 에러 메시지** — 7개 에러 힌트 body 영문화
- ✅ **로그아웃 네비 동기화** — location.reload()
- ✅ **Admin 리다이렉트** — JSON 401 → /app

### Playwright QA 자동화
- ✅ **Playwright MCP 설치** — @playwright/mcp@latest 등록
- ✅ **E2E 테스트 스크립트** — 4파일 30개 테스트 (i18n, 보안, 디자인, 반응형)
- ✅ **랜딩 모바일 오버플로우** — hero-grid 1fr + CTA 패딩 수정 (QA에서 발견)
- ✅ **테스트 계정 정리** — Rate Limit 더미 11개 삭제

### 팀 규칙
- ✅ **CLAUDE.md** — 팀 구조(후추팀장/클과장/제대리) + 워크플로우 + 핸드오프 규칙

### 문서 (4건)
- ✅ **REVIEW_2026-03-30.md** — 프로덕트 종합 리뷰 (최종 8.3/10)
- ✅ **DESIGN_REVIEW_2026-03-30.md** — 디자인 리뷰 (최종 8.4/10)
- ✅ **TEST_CHECKLIST.md** — QA 체크리스트 50항목
- ✅ **QA_SCENARIO_2026-03-31.md** — QA 시나리오 8개

---

## 🟡 중요 — 다음 작업 (슬라이드 품질)

1. ✅ **contact 슬라이드 허전** — A/B/D/F 마지막: 로고 추가, 중간 CTA: 회사명 추가 (KO+EN)
2. ✅ **EN 앱 진행 중 한글 로그** — 설문/이력/편집/생성/에러 등 20개소 한글 → 영문화 완료
3. ✅ **이미지 부족 시 타이포 전환 강화** — showcase_work_1/2 이미지 없으면 cards/two_col_text로 전환 (KO+EN)

## 🟡 중요 — 다음 작업 (인프라)

5. **primaryColor 점수 기반 리팩토링** — 현재 함수 추출 완료, 로직 자체는 추후
6. ✅ **C-type 아티스트 이미지 최소 해상도** — max 600→300, min 300→200
7. ✅ **Playwright brand_extractor 중복** — _pw_cache HTML 재활용으로 로고 탐색 시 중복 기동 제거

---

## 🟡 다음 세션 — 예정 작업

### 제대리(Gemini) 작업 → 클과장 리뷰
1. **M3 getSlideLayout 리팩토링** — 180줄 단일 함수 → 모듈화 (대규모, 제대리 적합)
2. **M13 업종별 프롬프트 변형** — 헬스케어/핀테크/건설 3개 특화 프롬프트

### 클과장(Claude) 직접 처리
3. **primaryColor 점수 기반 리팩토링** — 로직 설계 + 구현
4. **Playwright 테스트 확장** — 로그인 플로우, 슬라이드 생성 플로우 추가

## 🟢 추후 — 스케일업 + 수익화

- **이용약관 / 개인정보처리방침** — 법률 문서 (홀드)
- **M9 태블릿 반응형** — 768~899px 갭
- **M10 에러 힌트 확장** — SSL, OOM, CORS
- **M11 URL 클라이언트 검증** — 정규식 사전 검증
- **M14 Pain 분석 개선** — 업종별 Pain 특화
- **폰트 IndexedDB 캐싱** — 반복 접속 로딩 절약
- **Admin 페이지네이션** — 유저 100+ 대비
- **JSON-LD 구조화 데이터** — SEO Schema.org
- **토큰 충전 결제** — 토스페이먼츠 연동
- **카카오 로그인** — 한국 사용자 확대
- **슬라이드 수 조절** — 5/8/12장 선택
- **히스토리 공유 링크** — URL로 결과 공유
- **대기열 안내** — 큐 대기 시 "앞에 N명, 예상 N×5분" 표시

---

## 📋 레퍼런스 PDF 분석 — ✅ 전체 완료 (27개 / 9배치)

> 실제 회사소개서/제안서 PDF 27개 분석 완료. 배치 1~9 확인완료.
> ⚠️ 웰마케팅(corrupt), 피터팬AD(파일없음), 트래픽설계자(텍스트문서) 3건 스킵.

### 반영 가능 인사이트

#### 레이아웃 패턴 (빈도순)
1. **Key Numbers 2x2 그리드** — 라벨+대형숫자+설명 (BAT, 팀스완) → `key_metrics` 강화
2. **2컬럼 케이스 카드** — 좌측 다크패널+우측 화이트 상세 (OPINNO 뷰티/패션) → `portfolio` 변형
3. **프라이싱 3컬럼 카드** — 패키지+가격+체크리스트 (팀스완) → `pricing_cards` 신규 검토
4. **프로세스 수평 플로우** — HELP→TO→GROWTH / 구매여정 S커브 (OPINNO, 케이앤웍스) → `checklist` 변형
5. **조직도 트리 카드** — 상위→하위 카드 구조 (BAT, TheAgency) → `org_chart` 신규 검토
6. **간트차트 테이블** — 주차별 컬러블록 (MMIC, Bungee) → 테이블 셀 배경 하이라이트

#### 커버 패턴
7. **다크 풀스크린 커버** — 가장 빈번 (BAT, OPINNO, 팀스완, Bungee, 그립클라우드)
8. **2분할 커버** — 흑백+컬러 듀오톤 (케이앤웍스)
9. **사진 블리드 커버** — 풀이미지+로고 오버레이 (앰비션플랜)
10. **웨이브/그라데이션 커버** — 패턴 배경 (PICLICK, MMIC)

#### 디자인 요소
11. **섹션 넘버링 "01."** — 대형 번호 아이브로우 (BAT, 팀스완, PICLICK)
12. **컬러코딩 매트릭스** — 항목별 색상 구분 (TheAgency SEM)
13. **인용문 슬라이드** — 큰 따옴표 + 대형 텍스트 (앰비션플랜)
14. **키워드 태그 "A | B | C"** — 파이프 구분 서브타이틀 (Bungee B2B)
15. **아우트로 = 커버 변형** — CTA를 커버 디자인으로 마무리 (그립클라우드)

---

## 💰 토큰 구조

| 항목 | 토큰 |
|------|------|
| 가입 시 | 무료 2개 |
| 슬라이드 생성 | 1개 소모 |
| 설문 참여 | +2개 (계정당 1회) |
| 무료 충전 (베타) | +2개 |
| 생성 실패 시 | 자동 환불 |

> 추후: 토큰 패키지 판매 (5/10/30개)
