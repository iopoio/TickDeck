# TickDeck 아키텍처 리뷰 — 50년차 개발자 관점 (최종)

> 파일 구조 · 로직 효율성 · 보안 — 3가지 축 심층 분석
> 총 코드: ~10,000줄 (레거시 삭제 후)
> 최종 업데이트: 2026-04-01

---

## 현재 파일 구조

```
WebToSlide/
├── app.py                    1,046줄  ← Flask 서버
├── celery_app.py               157줄  ← Celery 태스크
├── i18n.py                     477줄  ← KO/EN 번역
├── CLAUDE.md                         ← 팀 규칙
├── templates/
│   ├── index.html            6,801줄  ← 앱 (HTML+CSS+JS+PPT엔진)
│   ├── landing.html            500줄
│   ├── landing_en.html         499줄  ← 랜딩 KO/EN 아직 중복
│   └── admin.html              288줄
├── web_to_slide/
│   ├── pipeline.py             913줄
│   ├── agents.py               795줄
│   ├── prompts.py              895줄
│   ├── brand_extractor.py    1,237줄
│   ├── scraper.py              868줄
│   ├── color_resolver.py       298줄
│   ├── image_pipeline.py       284줄
│   ├── database.py             237줄
│   ├── quality.py              193줄
│   ├── config.py                94줄
│   └── utils.py                167줄
├── tests/                            ← Playwright E2E (30개 테스트)
└── static/img/                       ← 로고, QR, OG 이미지
```

---

## 1. 파일 구조

### 🔴 index.html = 6,801줄 — 미해결 (중기 예정)

PPT 렌더링 엔진 ~4,500줄이 HTML 안에 인라인.
제안: `static/js/pptmon.js`로 분리 → 캐싱 가능 + 수정 범위 명확.
**상태: 미착수 — 제대리 작업으로 예정**

### ✅ app.py Blueprint 분리 — 완료 (4/07)

1,046줄 → 158줄. routes/ 폴더에 auth/api/admin/pages 4개 Blueprint 분리.
extensions.py 패턴으로 순환 참조 해결. 테스트 27 pass / 3 skip.
**상태: 완료 — 제대리 구현, 클과장 리뷰**

### 🟡 brand_extractor.py = 1,237줄 — 미해결 (장기)

CSS 파싱 + 파비콘 + 로고 + Playwright 혼합.
**상태: 미착수**

### 🟡 랜딩 KO/EN 중복 — 미해결 (중기)

index.html은 i18n 통합 완료. 랜딩은 아직 2파일.
**상태: 미착수**

### ✅ 레거시 파일 삭제 — 완료

- ~~web_to_slide_v4_backup.py (310KB)~~ → 삭제 완료
- ~~diff_full.txt~~ → 삭제 완료
- ~~server.log~~ → 삭제 완료
- ~~stitch_generate.js~~ → 삭제 완료
- ~~stitch_templates.json~~ → 삭제 완료

---

## 2. 로직 효율성

### 🔴 인메모리 + Celery 이중 분기 — 미해결 (장기)

app.py 전체에 `if USE_CELERY` 분기 산재.
**상태: 미착수**

### 🟡 에러 시 파이프라인 전체 재실행 — 미해결 (장기)

단계별 캐싱으로 실패 지점부터 재시도 가능.
**상태: 미착수**

### 🟡 클라이언트 → 서버 PPTX 전환 — 진행 중

- ✅ Phase 1: python-pptx 커버 빌더 완료
- ✅ Phase 1.5: merge-cover API 완료
- ✅ pptmon.js 분리 완료 (index.html -4,261줄)
- □ Phase 2: CTA + Contact
- □ Phase 3: 전체 전환

### ✅ pipeline.py 오케스트레이션 — 양호

단계별 progress_fn 호출 구조 잘 되어 있음.

---

## 3. 보안

### ✅ 완료 (총 12건)

| # | 항목 | 수정일 |
|---|------|--------|
| S1 | OAuth CSRF (state 파라미터) | 3/30 |
| S2 | SECRET_KEY 경고 + 세션 쿠키 보안 | 3/30 |
| S3 | SSRF 차단 (localhost/private/169.254/224/240) | 3/31 |
| S4 | Rate Limiting (Redis 스토리지) | 3/31 |
| S5 | Admin XSS (esc 함수) | 3/30 |
| S6 | 에러 메시지 일반화 | 3/30 |
| B1 | .env git 히스토리 확인 — 깨끗 ✅ | 4/01 |
| B2 | Admin 기본값 빈 문자열 | 4/01 |
| B3 | TB 로그 프론트 미전달 (서버만) | 4/01 |
| B4 | free_charge 1일 2회 제한 (Rate Limit + DB) | 4/01 |
| B5 | brand_extractor 변수 사전 초기화 | 3/31 |
| B6 | 로그아웃 UI 동기화 (reload) | 3/31 |

### 🟡 남은 보안 고려사항 (급하진 않음)

| # | 항목 | 시점 |
|---|------|------|
| B7 | SQLite → PostgreSQL (유저 100명+ 시) | 장기 |
| B8 | 이용약관 / 개인정보처리방침 | 홀드 |

---

## 우선순위 정리

### ✅ 완료

| # | 항목 | 완료일 |
|---|------|--------|
| 1 | 레거시 파일 5개 삭제 (-6,000줄) | 4/01 |
| 2 | 보안 즉시 수정 5건 (B1~B5) | 4/01 |
| 3 | KO/EN 앱 페이지 i18n 통합 | 3/31 |
| 4 | getSlideLayout 리팩토링 (M3) | 3/31 |
| 5 | 업종별 프롬프트 (M13) | 3/31 |
| 6 | Playwright E2E 30개 테스트 | 3/31 |
| 7 | index.html → pptmon.js 분리 | 4/02 |
| 8 | landing KO/EN i18n 통합 | 4/02 |
| 9 | app.py Blueprint 분리 (1046→158줄) | 4/07 |

### 다음 (중기 1~2주)

| # | 항목 | 담당 | 작업량 |
|---|------|------|--------|

### 장기 (1~3개월)

| # | 항목 | 작업량 |
|---|------|--------|
| 10 | brand_extractor 모듈화 | 3시간 |
| 11 | In-Memory 모드 분리/제거 | 1시간 |
| 12 | 파이프라인 단계별 캐싱 | 4시간 |
| 13 | SQLite → PostgreSQL | 하루 |
| 14 | 서버사이드 PPTX 생성 | 1주 |

---

*Last updated: 2026-04-01 — 즉시 수정 5건 완료 반영*
