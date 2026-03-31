# TickDeck 아키텍처 리뷰 — 50년차 개발자 관점

> 파일 구조 · 로직 효율성 · 보안 — 3가지 축 심층 분석
> 총 코드: 15,768줄 (핵심 파일 기준)

---

## 현재 파일 구조

```
WebToSlide/
├── app.py                    1,046줄  ← Flask 서버 (라우팅+인증+API+관리자 전부)
├── celery_app.py               157줄  ← Celery 태스크
├── i18n.py                     477줄  ← KO/EN 번역
├── templates/
│   ├── index.html            6,801줄  ← 앱 페이지 (HTML+CSS+JS+PptxGenJS 전부)
│   ├── landing.html            500줄
│   ├── landing_en.html         499줄  ← 랜딩은 아직 중복
│   └── admin.html              288줄
├── web_to_slide/
│   ├── pipeline.py             913줄  ← 파이프라인 오케스트레이터
│   ├── agents.py               795줄  ← Gemini API 호출 (4 에이전트)
│   ├── prompts.py              895줄  ← 프롬프트 텍스트
│   ├── brand_extractor.py    1,237줄  ← 브랜드 색상/로고 추출
│   ├── scraper.py              868줄  ← 웹 크롤링
│   ├── color_resolver.py       298줄  ← 색상 판정
│   ├── image_pipeline.py       284줄  ← 이미지 처리
│   ├── database.py             237줄  ← SQLite
│   ├── quality.py              193줄  ← 품질 체크
│   ├── config.py                94줄  ← 설정
│   └── utils.py                167줄  ← 유틸리티
└── web_to_slide_v4_backup.py  (310KB 레거시 — 삭제 대상)
```

---

## 1. 파일 구조 — 진단

### 🔴 Critical: `index.html` = 6,801줄 (386KB)

**이건 사실상 풀스택 앱이 HTML 파일 하나에 들어있는 거예요.**

포함된 것:
- HTML 마크업 (~300줄)
- CSS 스타일 (~600줄)
- 프론트엔드 JS 로직 (~1,200줄) — 인증, SSE, 모달, 폼, 이력
- **PptxGenJS 슬라이드 렌더링 엔진 (~4,500줄)** — 30+ 레이아웃, 컬러 시스템, 아이콘

4,500줄짜리 PPT 엔진이 HTML 안에 인라인으로 있으면:
- 브라우저가 매 요청마다 386KB HTML을 파싱
- 수정할 때 실수 확률 급증 (한 파일에서 CSS, JS, HTML 동시 편집)
- 캐싱 불가 (HTML이니까 no-store)

**제안: `static/js/pptmon.js`로 PPT 엔진 분리**
```
index.html  →  HTML + CSS + 프론트 로직 (~2,300줄)
static/js/pptmon.js  →  PPT 렌더링 엔진 (~4,500줄, 캐싱 가능)
```
- JS 파일은 브라우저가 캐싱 → 재방문 시 로딩 0ms
- 수정 범위 명확 → PPT만 고치면 pptmon.js만 터치
- Jinja2 변수가 필요한 부분은 `window.__SLIDE_CONFIG__` 같은 전역 객체로 주입

### 🟡 High: `app.py` = 1,046줄 (모든 역할 혼합)

현재 app.py에 들어있는 것:
- Flask 앱 설정 + 미들웨어
- Google OAuth (login, callback, signup, logout)
- 토큰 API (free-charge)
- 설문 API (check, submit)
- 슬라이드 재생성 API
- 생성 이력 API
- PDF 다운로드
- SSE 스트리밍 (Redis + In-Memory 2가지)
- 파이프라인 실행 + 에러 핸들링 + 재시도
- 관리자 라우트 7개
- 피드백 API

**1,000줄이 넘으면 "어디에 뭐가 있는지" 찾기 어려워져요.**

**제안: Blueprint로 분리**
```
app.py          → Flask 앱 초기화 + 미들웨어 (~100줄)
routes/auth.py  → OAuth + signup/login/logout (~150줄)
routes/api.py   → generate, stream, regen, history (~300줄)
routes/admin.py → 관리자 전체 (~200줄)
routes/pages.py → 페이지 렌더링 (~50줄)
```

### 🟡 High: `brand_extractor.py` = 1,237줄

CSS 파싱 + 파비콘 + 로고 탐지 + Playwright가 전부 한 파일.
기능별로 분리하면:
```
brand/css_parser.py      → CSS 변수/빈도 분석 (~400줄)
brand/favicon.py         → 파비콘/로고 탐지 (~300줄)
brand/playwright_cache.py → Playwright 캐시 관리 (~200줄)
brand/extractor.py       → 통합 오케스트레이터 (~300줄)
```

### 🟡 Medium: 랜딩 KO/EN 중복 (500줄 × 2)

index.html은 i18n으로 통합했는데 **landing은 아직 2개 파일이에요.** 
동일한 i18n 패턴으로 통합 가능.

### 🟢 Low: `web_to_slide_v4_backup.py` (310KB)

**이건 지금 당장 삭제해야 해요.** git에 히스토리 있으니까 로컬 백업 의미 없음.
310KB짜리 레거시 파일이 repo에 있으면:
- 실수로 import될 수 있음
- git clone 시 불필요한 용량
- 검색 시 혼란

---

## 2. 로직 효율성 — 진단

### 🔴 인메모리 모드 + Celery 모드 동시 유지

```python
if USE_CELERY:
    # Redis 모드
else:
    # In-Memory 모드 (JOBS dict)
```

이게 app.py 전체에 걸쳐 분기되면서 코드가 2배로 불어나 있어요.
`_stream_memory()` vs `_stream_redis()`, `_run()` vs `run_pipeline_task` 등.

**프로덕션에서 In-Memory는 안 쓰잖아요.** 로컬 개발용이라면 Redis를 로컬에서도 돌리거나, 
아니면 In-Memory 모드를 별도 파일로 분리해서 메인 코드를 깔끔하게 유지하는 게 좋아요.

### 🟡 에러 재시도가 파이프라인 전체를 다시 실행

```python
except Exception as e:
    clear_slide_cache(_slug, on_progress)
    result = run_pipeline(url, company, ...)  # 전체 재시도
```

크롤링은 성공했는데 Gemini에서 실패했을 때도 크롤링부터 다시 해요.
파이프라인을 단계별로 캐싱하면 (크롤링 결과 → Gemini 결과) 실패 지점부터 재시도 가능.

### 🟡 PptxGenJS 렌더링이 클라이언트에서 실행

현재: 서버 → JSON 데이터 → 클라이언트 JS에서 PPTX 조립 → 다운로드
장점: 서버 부하 없음
단점: 4,500줄 JS가 매번 로드, 브라우저 메모리 사용, 모바일에서 느림

**당장 바꿀 필요는 없지만**, 향후 서버사이드 PPTX 생성(python-pptx)으로 이전하면:
- 클라이언트 JS 4,500줄 제거
- 모바일 성능 개선
- PDF 변환도 서버에서 일관되게 처리

### 🟢 pipeline.py의 오케스트레이션은 잘 되어 있음

`run_pipeline()`이 단계별로 progress_fn을 호출하면서 진행하는 구조는 좋아요.
각 단계(scrape → extract → strategize → generate → match)가 명확하게 분리되어 있음.

---

## 3. 보안 — 진단

### ✅ 이미 수정된 것 (오늘 작업)
- OAuth CSRF (state 파라미터)
- SSRF 차단 (localhost/private/169.254/224/240)
- Rate Limiting (Redis 스토리지)
- Admin XSS (esc 함수)
- SECRET_KEY 경고
- 세션 쿠키 보안 플래그

### 🔴 아직 남은 보안 이슈

**B1. GitHub에 .env 민감정보 히스토리**
```
GEMINI_API_KEY=AIzaSy...
PEXELS_API_KEY=WpVwO...
GOOGLE_CLIENT_ID=98937...
```
.env가 .gitignore에 있지만, **과거 커밋에 포함되었을 수 있어요.**
→ `git log --all -- .env` 로 확인 필요
→ 포함되었다면 API 키 로테이션 필수

**B2. SQLite 동시 접근**
Gunicorn 워커 2개 + Celery 워커 1개 = 3개 프로세스가 동시에 SQLite 접근.
WAL 모드로 읽기는 괜찮지만 쓰기 충돌 가능.
현재는 유저가 적어서 괜찮지만, 100명 넘으면 PostgreSQL 이전 필요.

**B3. 에러 로그에 Traceback 전달**
SSE로 프론트에 전달되는 로그에 `TB| File "/opt/tickdeck/app/..."` 같은 서버 경로가 노출될 수 있어요.
`on_progress(f"  TB| {_tl}")` 부분. 프로덕션에서는 TB 라인을 프론트에 안 보내는 게 맞아요.

**B4. Admin 이메일 하드코딩**
```python
ADMIN_EMAILS = set(
    e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', 'chaejenn@gmail.com').split(',')
)
```
기본값에 실제 이메일이 있어요. 환경변수 없으면 기본값이 관리자가 됨.
→ 기본값을 빈 문자열로 변경

**B5. free_charge API 무제한**
```python
@app.route("/api/token/free-charge", methods=["POST"])
@login_required
def free_charge():
    add_tokens(user_id, 2, 'free_charge')
```
Rate limit이 걸려있긴 하지만, 이 엔드포인트는 **아무나 호출하면 토큰 2개 무한 충전**이에요.
설문 완료 체크나 1일 1회 제한 같은 로직이 필요해요.

---

## 우선순위 정리

### 즉시 (이번 주)
| # | 항목 | 임팩트 | 작업량 |
|---|------|--------|--------|
| 1 | `web_to_slide_v4_backup.py` 삭제 | 정리 | 1분 |
| 2 | B4 Admin 기본값 빈 문자열 | 보안 | 1분 |
| 3 | B5 free_charge 제한 | 보안 | 10분 |
| 4 | B3 TB 로그 프론트 미전달 | 보안 | 10분 |
| 5 | B1 .env git 히스토리 확인 | 보안 | 5분 |

### 중기 (1~2주)
| # | 항목 | 임팩트 | 작업량 |
|---|------|--------|--------|
| 6 | index.html → pptmon.js 분리 | 성능+유지보수 | 2~3시간 |
| 7 | landing KO/EN i18n 통합 | 유지보수 | 1시간 |
| 8 | app.py Blueprint 분리 | 유지보수 | 2시간 |

### 장기 (1~3개월)
| # | 항목 | 임팩트 | 작업량 |
|---|------|--------|--------|
| 9 | brand_extractor 모듈화 | 유지보수 | 3시간 |
| 10 | In-Memory 모드 분리/제거 | 코드 정리 | 1시간 |
| 11 | 파이프라인 단계별 캐싱 | 효율성 | 4시간 |
| 12 | SQLite → PostgreSQL | 확장성 | 하루 |
| 13 | 서버사이드 PPTX 생성 | 성능 | 1주 |

---

## 한 줄 총평

> **15,000줄 프로젝트로서는 구조가 나쁘지 않아요.**
> 하지만 `index.html`이 6,800줄인 건 **기술 부채의 핵**이에요.
> PPT 엔진을 분리하는 것만으로도 유지보수성이 2배 좋아집니다.
> 보안은 90% 해결됐지만, free_charge 무제한 + TB 로그 노출은 빨리 잡아야 해요.

---

*Reviewed by Claude Opus 4.6 (클과장) — 50년차 개발자 관점*
