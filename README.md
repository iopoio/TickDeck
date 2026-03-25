# WebToSlide — AI 슬라이드 생성기

홈페이지 URL 하나면 브랜드 맞춤형 프레젠테이션이 완성됩니다.

---

## 어떻게 만들어지나요?

```
URL 입력 → 홈페이지 크롤링 → Gemini 콘텐츠 분석 → Imagen 배경 생성 → PPTX 완성
```

1. **크롤링** — 홈페이지 텍스트, 브랜드 컬러, 로고 자동 수집
2. **AI 분석** — Gemini가 회사 성격을 파악해 내러티브 타입(A/B/C/D) 결정
3. **슬라이드 구성** — 10~13장 분량의 슬라이드 콘텐츠 생성
4. **배경 이미지** — 슬라이드별 컨셉에 맞는 이미지를 Pexels/Imagen으로 생성
5. **PPTX 빌드** — PptxGenJS로 편집 가능한 파일 완성

---

## 주요 기능

- **딸깍이 UX** — URL 붙여넣기 → 한 번 클릭 → 완성
- **4가지 내러티브 타입** — 브랜드 성격에 맞게 AI가 자동 선택
  - A형: 문제-해결 (마케팅/SaaS)
  - B형: 산업 주도 (대기업/인프라/IR)
  - C형: 포트폴리오 (크리에이티브/에이전시)
  - D형: 가치 제안 (럭셔리/프리미엄)
- **브랜드 컬러 자동 추출** — CSS·OG이미지·로고에서 대표색 감지
- **5가지 레이아웃 시스템** — Cover · Split · Cards · Portfolio · CTA
- **3-Font 내장 PPTX** — Pretendard + NotoSerifKR + BlackHanSans 폰트 포함
- **실시간 진행 상황** — SSE 스트리밍으로 단계별 로그 표시
- **슬라이드 내용 편집** — 완료 후 헤드라인·본문 직접 수정 가능

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| **서버** | Python 3.11 · Flask |
| **AI (콘텐츠)** | Google Gemini 2.5 Flash |
| **AI (이미지)** | Google Imagen 4.0 Fast |
| **이미지 폴백** | Pexels API |
| **슬라이드 생성** | PptxGenJS (브라우저 사이드) |
| **PDF 미리보기** | HTML5 Canvas |
| **프론트엔드** | Vanilla JS · SSE · Pretendard |

---

## 시작하기

### 사전 준비

- Python 3.11+
- [Google AI Studio](https://aistudio.google.com) — Gemini API 키
- [Pexels](https://www.pexels.com/api/) — Pexels API 키 (무료)

### 설치

```bash
# 1. 의존성 설치
pip install -r requirements.txt

# 2. 환경변수 설정
# .env 파일 생성
GEMINI_API_KEY=your_gemini_api_key
PEXELS_API_KEY=your_pexels_api_key

# 3. 서버 시작
python app.py
# → http://localhost:5000
```

### 서버 관리

```bash
# 포트 점유 확인 (Windows)
netstat -ano | findstr :5000

# 포트 점유 프로세스 종료
for /f "tokens=5" %a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /PID %a /F

# 캐시 삭제 (재크롤링 강제)
del slide_*.json
```

---

## 파일 구조

```
WebToSlide/
├── app.py                  Flask 서버 — API + SSE 스트리밍
├── web_to_slide_v4.py      AI 파이프라인 엔진
├── templates/
│   └── index.html          프론트엔드 — UI + PPTX 생성 + PDF 렌더링
├── .env                    API 키 (git 제외)
├── requirements.txt        Python 의존성
└── slide_*_text.json       회사별 텍스트 캐시 (재생성 스킵)
```

---

## API

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 메인 UI |
| `POST` | `/generate` | 파이프라인 시작 → `{job_id}` 반환 |
| `GET` | `/stream/<job_id>` | SSE 실시간 로그 스트림 |
| `GET` | `/result/<job_id>` | 완성된 슬라이드 JSON 반환 |
| `POST` | `/clear-cache` | 캐시 파일 삭제 |

---

## 참고사항

- 슬라이드 1장당 Imagen 호출 1회 (429 방지를 위해 6초 간격)
- Imagen 쿼터 초과 시 Pexels로 자동 폴백
- `slide_*_text.json` 캐시가 있으면 크롤링·Gemini 단계 스킵 (이미지만 재생성)
- 현재 버전: **v10.56** (2026-03-20)
