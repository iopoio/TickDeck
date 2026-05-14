# TickDeck v2 — PRD (계획 문서)

> 작성: 2026-05-12 (브레인스토밍 후 정리)
> 상태: 계획 단계·실 빌드 진입 전 후추님 review·OK 후 writing-plans 단계
> 출발점: TickDeck v1 시장 출시 포기 (4/27) → 5/12 재개·*가볍게 + 잘 나오게* 방향

## 한 줄 가치

PDF 한 장 업로드하면 AI 조사로 내용 강화하고 후추님 톤 디자인 시스템 자동 매칭해서 PPTX 1-딸깍.

## 사용자

일반인 (자료 만들기에 익숙 X·옵션 폭발 X 원함). 후추님 본인은 power user라 옵션 多 필요·v0 영역 X.

## 차별점

- Gamma·Tome·Claude Design = 일반 톤·*프롬프트 + 편집 多*
- TickDeck v2 = **후추님 PDF 자산 분석 → 템플릿화** + AI 조사 강화 + 본진 디자인 시스템 (다른 도구에 없는 자산)
- 본진 + 제대리 교차 분석으로 템플릿 신뢰도 ↑

## 결정 9개 (브레인스토밍 결과)

| # | 영역 | 결정 |
|---|---|---|
| 1 | 사용자 | 일반인 1-딸깍 |
| 2 | 편집 | PPTX 다운로드 후 외부 도구 (PowerPoint·Google Slides)에서 수정·TickDeck 내부 편집 X |
| 3 | 디자인 | AI 자동 매칭·6종 라인업 (core 4 + 비즈니스 1 + 콘텐츠 1) |
| 4 | AI 조사 | 오프라인 PDF 분석 → 템플릿 → 런타임은 가벼움 영역 |
| 5 | 자료 분석 | 후추님 PDF 송부 → 본진+제대리 교차 → 카테고리 분류 → 비는 영역 외부 보충 |
| 6 | 입력 형태 | PDF만·다른 포맷 (PPT·HWP·Word)은 PDF 변환 안내 |
| 7 | 추가 입력 | 청중 한 줄 + 목적 한 줄 (분류·매칭 정확도 ↑) |
| 8 | 스타일 변경 | 1회 허용·내용 그대로·레이아웃·디자인만 변화·*파일 2개 다운로드 (원본 + 변경본)* |
| 9 | 프라이버시 | 세션 종료 시 자동 삭제·DB·계정 X·서버 저장 X·첫 화면 안내 명시 |

## 디자인 라인업 (6종)

| 영역 | 톤 |
|---|---|
| Minimal White (core) | 깔끔·여백 多·기본 |
| Soft Coral (core) | 따뜻한 톤·라이프스타일 |
| Dark Mode (core) | 다크·테크 영역 |
| Deep Blue Pro (core) | 비즈니스·정장 |
| 비즈니스 정장 (신규) | IR·사업계획·B2B 제안·모노톤·세리프 |
| 콘텐츠 컬러풀 (신규) | 마케팅·엔터·SNS·비비드 |

brand 5종 (잡솔트·EatScan·IdalTrip·시즌드·펩핀치) 다 빼기 — 비슷·기억 약함.

## 전체 아키텍처

```
사용자 (브라우저)
   ↓
[Streamlit UI] tickdeck.peppinch.com (Mac mini + Cloudflare Tunnel)
   ↓
세션 임시 저장 (메모리·N분 idle 또는 닫힘 시 자동 cleanup)
   ↓
[런타임 파이프라인]
  1. PDF 파싱 (pypdf)
  2. AI 조사 강화 (Gemini grounding·키워드 다회 검색)
  3. 자료 통합 (원본 + 보충)
  4. 내러티브 구조화 (3에이전트 + 템플릿 매칭) ← 핵심
  5. 품질 검증 (quality.py 룰)
  6. 디자인 시스템 자동 선택 (6종 중 매칭)
  7. PPTX 생성 (python-pptx + DESIGN.md 토큰)
   ↓
다운로드 (PPTX 1개·"스타일 변경" 누르면 v2도 다운로드)
```

### 별도·오프라인 영역

- **템플릿 분석**: 본진 (Claude) + 제대리 (Gemini CLI) 교차로 후추님 PDF read·내러티브 패턴 추출 → `templates.json` 자산. 런타임 영역과 분리.
- **위치**: `Think/inbox-pdf/research/` (노클이 git으로 일괄 송부)

## 기술 스택

| 영역 | 선택 |
|---|---|
| UI | Streamlit |
| AI | Gemini 3.1 Flash Lite Preview·grounding |
| PPTX | python-pptx + DESIGN.md 토큰 (TickDeck v1 자산) |
| 인프라 | Mac mini + Cloudflare Tunnel (잡솔트 동일) |
| 저장 | 메모리만·DB X |
| 호스팅 | tickdeck.peppinch.com (페핀치 서브도메인) |

## 빌드 순서 (재빌딩 X 방향)

| 단계 | 내용 |
|---|---|
| **1단계 (오프라인 분석)** | 노클 PDF 일괄 송부 → 본진+제대리 교차 분석 → `templates.json` 완성 → 카테고리 분포 점검 → 비는 영역 외부 자료 보충 결정 |
| **2단계 (런타임 파이프라인 빌드)** | TickDeck v1 자산 (3에이전트·quality.py·DESIGN.md·gemini_client·pptx_builder) 재활용 + Streamlit UI 신규 |
| **3단계 (디자인 6종 정합)** | 6종 디자인 시스템 토큰 정의·자동 매칭 알고리즘 |
| **4단계 (페핀치 진열대 노출)** | tickdeck.peppinch.com 셋업·*무저장 MVP* 안내 명시 |

## 살릴 자산 (TickDeck v1)

| 영역 | 결정 |
|---|---|
| `shared/pptx_builder.py` | 그대로 |
| `backend/crawler.py` | URL 입력 영역 빠지므로 X·PDF 영역만 |
| `backend/gemini_client.py` (3에이전트 영역) | 그대로 |
| `schemas.py` (SlideType·BrandInfo·narrative_type) | 그대로 |
| `quality.py` (RULE A/J/B) | 그대로 |
| `DESIGN.md` v0.1 | 그대로·6종 디자인 토큰으로 확장 |
| FastAPI·Celery·Redis·Postgres·OAuth·토큰 시스템·React 4페이지 | 다 빼기 |

## 모듈 영역 ("잘 안 되면 하나씩 강화")

각 단계 독립 모듈·강화 옵션은 별도 진행 가능.

| # | 단계 | v0 작업 | 강화 옵션 |
|---|---|---|---|
| 1 | PDF 파싱 | pypdf·텍스트 추출·기본 클린 | OCR·이미지 캡션·표 인식 |
| 2 | AI 조사 강화 | Gemini grounding 1회·키워드 다회 검색 | 도메인별 검색·신뢰도 점수·복수 소스 교차 |
| 3 | 자료 통합 | 단순 병합·중복 거름 | 사실 검증·출처 표기·우선순위 룰 |
| 4 | 내러티브 구조화 | 3에이전트 + 템플릿 매칭 | 청중별 톤·길이 옵션·내러티브 타입 세분화 |
| 5 | 품질 검증 | quality.py 그대로 | 룰 추가·자동 재생성 횟수 조정 |
| 6 | 디자인 선택 | 6종 자동 매칭 | 새 디자인 추가·사용자 톤 추출 |
| 7 | PPTX 생성 | python-pptx + DESIGN.md 토큰 | 차트·이미지 자동 삽입·애니메이션 |

## 노력·시기 (5/12 갱신·내일부터 실 빌드)

| 단계 | 시간 | 시기 |
|---|---|---|
| 0. PRD 완성·후추님 review | 오늘 (5/12) | 완료 |
| 1. 오프라인 템플릿 분석 (자동·본진+제대리) + 노클 PDF 송부 | 1~2일 | 5/13~5/14 |
| 2. 런타임 파이프라인 빌드 (v1 자산 재활용) | 1~2주 | 5/14~5/27 |
| 3. 디자인 6종 토큰 + 매칭 | 1주 | 5/27~6/3 |
| 4. Streamlit UI + 페핀치 진열대 노출 | 1주 | 6/3~6/10 |
| **합** | **3~4주 (저녁 짬짬이)** | **5/13~6/10** |

페이스 점검 영역:
- 5/14 = 고용노동 마감 (잡솔트·이미 제출)·결과 대기
- 5/15 = 모두의 창업 마감 (EatScan·이미 제출)·결과 대기
- 5/18 = 혁신창업리그 dropped 최종 결정 (후추님 99% dropped 의향)
- **6/1 = 사보원 (국민행복서비스) 제출 영역** — 5/30경 작성·HWP 변환 시간 확보 필요
- 7~9월 = 잡솔트 Phase 2 (이력서·자소서 AI)·TickDeck v2 완성 후 진입

→ 6/1 사보원 제출 영역 만 시기 충돌 영역·TickDeck 빌드 *3·4단계*에서 1~2일 사보원 작업으로 영역 양도 가능.

**공모전 우선 룰 (5/12 후추님 명시)**: 진행 중 공모전 영역 들어오면 TickDeck 진행 일시 정지·공모전 우선. 5/14·5/15 결과 발표·5/18 dropped 결정·6/1 사보원 제출 같은 외부 마감 = critical. 본진이 자동 알림·TickDeck 단계 양보.

## 매출·시장 영역

- 어필리에이트 등록 어려움 (한국 사업자 영역)·시장 작음
- 매출 X·*취미 + 기술 자산 + 페핀치 진열대* 자국
- 후추님 본인 + 일반인 진짜 쓰는 도구 자체가 가치

## 데이터 흐름 (단계별 상세)

각 단계 = 입력 / 처리 / 출력 / 오류 처리.

### 1. PDF 파싱
- **입력**: 사용자 PDF (파일 1개·MB 영역)
- **처리**: pypdf로 텍스트 추출·페이지별·헤더·문단 인식·텍스트 클린
- **출력**: `{pages: [{page_num, text, headers, paragraphs}], meta: {...}}`
- **오류**: 스캔 PDF (텍스트 X) 감지 → 사용자에게 안내·OCR은 v1 영역

### 2. AI 조사 강화
- **입력**: 파싱 JSON + 사용자 청중 한 줄 + 목적 한 줄
- **처리**: Gemini grounding으로 핵심 키워드 추출 → 키워드별 구글 검색 (다회)·외부 자료 fetch·신뢰도 점수
- **출력**: `{supplements: [{keyword, source, snippet, confidence}]}`
- **오류**: 검색 결과 X·grounding 실패 → 원본만으로 진행·로그 남김

### 3. 자료 통합
- **입력**: 원본 JSON + 보충 JSON
- **처리**: 중복 제거·우선순위 룰 (원본 > 보충)·신뢰도 점수 결합
- **출력**: `{key_points: [...], supporting: [...], confidence_avg: 0.x}`
- **오류**: 충돌 시 원본 우선

### 4. 내러티브 구조화 (핵심)
- **입력**: 통합 자료 + 청중 + 목적 + `templates.json` (오프라인 분석 결과)
- **처리**: 3에이전트 (Researcher → Strategist → Copywriter)·내러티브 타입 매칭·해당 타입 템플릿 prompt 적용
- **출력**: `{slides: [{type, title, body, narrative_type, layout_hint}]}`
- **오류**: 3에이전트 어느 단계 실패 시 fallback prompt 적용·간단 템플릿으로

### 5. 품질 검증
- **입력**: 슬라이드 JSON
- **처리**: quality.py·RULE A (헤드라인 길이)·J (숫자↔body 비율)·B (body 최소 2개)
- **출력**: 통과 시 그대로·실패 시 내러티브 단계 자동 재호출 (1회만)
- **오류**: 재호출도 실패 시 경고와 함께 그대로 진행

### 6. 디자인 시스템 자동 선택
- **입력**: 슬라이드 JSON + 청중 + 목적 + narrative_type
- **처리**: 6종 디자인 매칭 알고리즘 (예: Tech narrative + 임원 청중 → Deep Blue Pro·콘텐츠 → Soft Coral·기본 → Minimal White)
- **출력**: 디자인 토큰 JSON
- **오류**: 매칭 X 시 Minimal White (default)

### 7. PPTX 생성
- **입력**: 슬라이드 JSON + 디자인 토큰
- **처리**: python-pptx로 슬라이드별 생성·DESIGN.md 토큰 적용·차트·이미지 영역
- **출력**: PPTX 파일 (세션 메모리·다운로드 직후 삭제)
- **오류**: python-pptx 실패 시 사용자에게 에러 안내·재시도 버튼

### 8. 스타일 변경 (옵션·사용자가 누르면)
- **입력**: 캐싱된 슬라이드 JSON + 다른 디자인 토큰 (6종 중 다른 1개)
- **처리**: 6·7단계만 재호출·내러티브·내용 그대로
- **출력**: PPTX v2 (사용자 화면에 2개 파일 다운로드 버튼)
- **오류**: 실패 시 1회 자동 재시도

## 컴포넌트 (Streamlit 단일 앱)

```
tickdeck_v2/
├── app.py                  # Streamlit 메인·UI·세션 영역
├── pipeline/
│   ├── parse.py            # 1단계 (pypdf)
│   ├── research.py         # 2단계 (Gemini grounding)
│   ├── merge.py            # 3단계
│   ├── narrative.py        # 4단계 (3에이전트·templates 매칭)
│   ├── quality.py          # 5단계 (v1 자산 그대로)
│   ├── design.py           # 6단계 (6종 매칭)
│   └── pptx.py             # 7단계 (python-pptx·v1 자산 활용)
├── templates/
│   └── templates.json      # 오프라인 분석 결과
├── design_systems/
│   └── *.json              # 6종 디자인 토큰
├── shared/                 # v1 자산 (pptx_builder 등)
└── tests/
    └── *.py                # 단위 테스트·E2E
```

## 에러 핸들링 영역

| 영역 | 처리 |
|---|---|
| PDF 텍스트 추출 실패 (스캔 PDF) | 사용자에게 *"텍스트 PDF만 지원·OCR은 미래 영역"* 안내 |
| Gemini grounding API 실패 | 원본 자료만으로 진행·로그·사용자에게 *"조사 강화 일부 실패·결과 영향 작음"* |
| 3에이전트 실패 | fallback prompt·간단 템플릿·결과 약간 평이 |
| quality 검증 통과 X | 자동 재호출 1회·여전히 실패 시 경고 표시·그대로 진행 |
| PPTX 생성 실패 | 사용자에게 *"잠시 후 다시 시도"*·1회 자동 재시도 |
| 세션 timeout | 사용자에게 다시 업로드 안내 |

## 테스팅 영역

| 단계 | 방식 |
|---|---|
| 단위 테스트 | 각 pipeline 모듈 단독·고정 입력 → 고정 출력 |
| E2E 테스트 | 샘플 PDF 5종 (다양 카테고리) → 결과 PPTX 시각 점검 |
| 회귀 테스트 | quality 룰 통과율·각 라인업 디자인 정합·고정 PDF로 |
| 사용자 테스트 | 후추님 본인 + 1~2명 일반인 자료로 v0 사용·피드백 |

## 다음 영역 (5/13 내일부터)

### 오늘 (5/12) 마무리

- ✅ PRD 작성 완료 (본 문서)
- ✅ 후추님 OK
- 본진 자율: ClickUp Task 등록·메모리 갱신·노클 PDF 송부 안내 메모

### 내일 (5/13) 7단계 진행

| # | 단계 | skill | 시간 |
|---|---|---|---|
| 1 | 유저 플로우 | `user-flow:index` | 30분 |
| 2 | UI 시안 (간단 wireframe) | HTML 또는 figma·후추님 인풋 영역 | 1시간 |
| 3 | 기능 명세 | `feature-spec:index` | 30분 |
| 4 | 테스트 시나리오 | `pm-execution:test-scenarios` | 30분 |
| 5 | pre-mortem (위험 분석) | `pm-execution:pre-mortem` | 30분 |
| 6 | writing-plans (실 구현 계획) | superpowers skill | 1시간 |
| 7 | 노클 PDF 송부 받고 본진+제대리 교차 분석 시작 | 자동 | 1~2일 |

**5/13 = 약 4시간 작업 (위 1~6) + 7번은 자동 진행.**

---

# v2.1 — 5/13 wedge 재정의 (SaaS 노선 시동)

> 작성: 2026-05-13 (TickDeck v2 wedge 재토론·Thiel framework 적용)
> 상태: 5/12 PRD v2 풀이 보존 + 5/13 갱신 layer 추가
> 자세한 풀이: `Think/sessions/2026-05-13_TickDeck_v2_wedge_재정의.md`

## 갱신 사상

5/12 PRD = "일반인 1-딸깍" wedge → Gamma·Tome·Claude Design 점령 시장 정면 충돌·죽음
5/13 = wedge 좁힘 + Thiel framework 적용·SaaS 진짜 살리는 노선

## 갱신 한 줄 가치

한국 B2B 제안서·brand 컨설팅·marketing brief deck — Gamma·Tome 영어권 점령자가 absolutely 못 따라오는 *한국 비즈니스 톤 + 컨설팅 리서치 단계 + 산업별 다양·후추님 137개 검증 자료* layer.

## ICP 1줄 (Primary)

"한국 BD·marketing·컨설팅 agency·1인 외주 작업자 + 대기업·중견기업 실무자 (BYOD·본인 카드 결제) 가 클라이언트사 또는 사내·외 제출하는 한국 비즈니스 톤·컨설팅 리서치 layer 가진 제안서·brand 컨설팅 deck"

## Primary·Secondary 분리 (Trojan Horse·Land & Expand)

| 구분 | 풀이 | 정책 |
|---|---|---|
| Primary | B2B 제안서·brand 컨설팅·marketing brief | marketing·brand·landing 페이지 strict 좁힘 |
| Secondary | 포폴·이력서·학회·과제·회의 메모·기타 | 도구 자유 허용·marketing X·1년 운영 후 검토 |

5/12 sample 4종 (이력서·학회·과제·회의 메모) = secondary 옵션으로 살림·marketing X.

## 차별 layer 3개 (5/13 후추님 직관)

1. 말투·용어·단어 = 한국 비즈니스 톤·존댓말·산업별 전문 용어 (Gamma·Tome 영어 직역 어색)
2. 컨설팅 회사 리서치 단계 layer = 1차/2차 자료·시장·경쟁사·트렌드·인용·출처 (3~10분 소요·1-딸깍 X·*Time-to-value 60초 X → 3~10분으로 갱신*)
3. 보안 풀이 정정 = 한국 대기업 (SK 제외) 실무자 BYOD 사용 多·시장 진입 가능

## Asia-first 3단계 노선 (1 국내 → 2 아시아 → 3 글로벌)

| 단계 | 시기 | 자료 source |
|---|---|---|
| 1 국내 | 5/13~6/23 6주 검증·1년 운영 | 후추님 137개 + ARK Big Ideas + 삼정KPMG·KPMG·Deloitte·BCG/McKinsey Korea + 한국 증권사 (200~300개) |
| 2 아시아 | 1년 후 (2027 4~5월) | 노무라·미즈호·일본 BCG/McKinsey·대만 KPMG·동남아 IR (200~500개 추가) |
| 3 글로벌 | 1.5~2년 후 | McKinsey/BCG/Bain Insights·Deloitte/KPMG/PwC Global·World Bank/IMF/OECD·YC public decks·ARK 글로벌·Statista·CB Insights (500~1,000개 추가) |
| 4 영어권 직진 | 2.5~3년 후 (풀타임 layer 결정 후) | 영어권 자료 대량 누적 |

⚠️ 1단계부터 *글로벌 호환 architecture 사상 base*·실제 다국어·다통화 풀 활성화 X (premature globalization risk 회피).

⚠️ 후추님 137개 정정 = B2B 제안서 톤 ✅·*리서치 톤 X*. 1단계부터 리서치 톤 학습 자료 (ARK·KPMG·BCG 등) 동시 학습 필수 (차별 layer 2 빌드용).

## 글로벌 호환 architecture 사상 5개 (1단계부터 base·풀 활성화 X)

| # | 부분 | 1단계 | 2~4단계 활성화 |
|---|---|---|---|
| 1 | i18n base | ko 단일·하드코딩 X·변수화 | ja·zh-TW·en 등 plug-in |
| 2 | 톤 dictionary | 한국 산업별 5~10종 | 일본·중화권·동남아·영어권 plug-in |
| 3 | 자료 메타데이터 schema | country·industry·language·license·source_url 필드 strict | 단계별 누적 |
| 4 | 결제 어댑터 | 토스페이먼츠 단일 | Stripe·동남아 결제 plug-in |
| 5 | distribution 어댑터 | 펩핀치·잡솔트·X 한국 | 단계별 X 확장·ProductHunt·Reddit |

## ARK Invest 자료 (1단계 리서치 톤 학습용)

위치 = `/Users/hwa/Projects/Automation/investlab/research/ARK_reports/` (7 파일·32MB)
- Big Ideas 2024·2025·2026-Q1 PDF + 마크다운 요약 3개 + 예측 적중률 분석
- 활용 = 디스럽티브 이노베이션 narrative 표준·데이터·차트·출처·영어권 컨설팅 톤
- 1단계 시점 = 본진+제대리 교차 분석·patterns 추출·templates/research_tone/ 누적
- 3단계 글로벌 진입 시 = 영어권 리서치 톤 표준 자료 그대로 활용

## 학습 방식 = Template extraction + Few-shot (Fine-tuning X)

| 옵션 | 풀이 | 채택 |
|---|---|---|
| A. Fine-tuning | 모델 weights 학습·비용 ↑·라이선스 risk ↑ | ❌ 1인 인디해커 X |
| B. RAG | 자료 DB·런타임 검색 | 🟡 가능 (다음 단계) |
| C. Few-shot prompting | 예시 5~10개 prompt 주입 | ✅ |
| D. Template extraction | 패턴 추출·templates.json | ✅ 가장 권장 |

= D + C 조합·비용 ↓·라이선스 risk ↓.

라이선스 룰:
- ✅ 공개 자료 + 출처 표기·패턴 추출
- ✅ 정부·OECD·World Bank 자유 사용
- ✅ 후추님 137개 본인 저작권
- ❌ paywall 자료·내부 자료·전체 복사·재배포

## Thiel 7 monopoly questions 점검 (5🟢·2🟡)

| # | 질문 | 점검 | 평가 |
|---|---|---|---|
| 1 | 10x breakthrough | 한국 톤 + 컨설팅 리서치 layer vs Gamma 영어 톤 | 🟡 1단계 검증 |
| 2 | Timing right | 한국 B2B 컨설팅 톤 빈 자리·now right time | 🟢 |
| 3 | 큰 share·작은 market | 한국 BD/agency 수만·100억 80% | 🟢 |
| 4 | 팀 | 본진 + 르메 + 양념이 + 신야 격리 자율 agent | 🟢 |
| 5 | Distribution | 펩핀치·잡솔트·X = 약함 | 🟡 강화 필수 |
| 6 | Durability | B2B 제안서 시장 영구·moat 시간 지날수록 강함 | 🟢 |
| 7 | Secret | 한국 컨설팅 톤 + 137개 = 다른 누구도 모름 | 🟢 |

→ monopoly 가능성 검증·1단계 검증으로 🟡 두 개 답 명확화.

## 4 monopoly 특성 점검

- Proprietary technology ⭐ 강함 (한국 톤 + 137개 + Template extraction)
- Network effects ⭕ 가능 (사용자 결과 deck 누적·templates 강화)
- Economies of scale ⭕ 가능 (자료 누적·고정 비용 ↓)
- Branding ⭐ 강함 (펩핀치·잡솔트·후추님 brand)

## pricing 갱신

| 모델 | 가격 | 1 deck 원가 | 이익률 |
|---|---|---|---|
| 1회 단발 (권장) | 5,000~10,000원 | ~1,700원 + 수수료 150원 | 63~81% |
| 월 구독 9,900 (5 deck) | 9,900원 | 8,800원 | 11% (X) |
| 월 구독 19,900 (10 deck) | 19,900원 | 17,600원 | 12% (X) |

→ *1회 단발 5,000~10,000원* 권장·구독 X (정밀도 최고 노선 + 컨설팅 리서치 layer 비용 ↑).

비용 절감 layer 적용 시 (grounding 캐싱·단계별 모델 분리·prompt cache 등) = 단가 70% ↓·이익률 90%.

## 6주 검증 마일스톤 (5/13~6/23)

| 주 | 한국 wedge 검증 (메인) | 글로벌 호환 architecture (백그라운드) |
|---|---|---|
| 1 (5/13~5/19) | wedge 1줄 갱신·PRD v2.1·랜딩 페이지 | 코드 base architecture (i18n·결제 어댑터·메타데이터 schema) |
| 2 (5/20~5/26) | templates.json 한국 5종 추출 + ARK 본진+제대리 교차 분석 | 메타데이터 schema strict·country·industry·language·license |
| 3 (5/27~6/2) | waitlist 마케팅 X·디스콰이엇·스타트업 슬랙 | 노클 글로벌 자료 백그라운드 다운로드 (YC·McKinsey 공개) |
| 4 (6/3~6/9) | Streamlit MVP·sample 5종 동작·Time-to-value 3~10분 strict | i18n 파일 분리·locales/ko.json·locales/ja.json 빈 파일 |
| 5 (6/10~6/16) | 결제 검증 토스페이먼츠·1회 5천원 | 결제 어댑터 사상 base·Stripe 빈 파일 |
| 6 (6/17~6/23) | LTV·재방문·NPS·GO/STOP | 백그라운드 글로벌 자료 누적 점검 |

GO 조건:
- waitlist → 결제 전환 30%+
- 재방문 의향 70%+
- 10x breakthrough 검증 (Gamma·Tome 사용자 비교 NPS ↑)
- Distribution 채널 검증 (waitlist 30명 모집 채널 확인)

조건 못 채우면 STOP·자산 노선 (본인 도구) 전환.

## 외부 마감 양보 룰 (5/12 PRD 정합)

- 5/14 잡솔트 고용노동 결과 대기 (외부 마감 X·빌드 동시 진행 OK)
- 5/15 EatScan 모두의창업 결과 대기 (동일)
- 5/30~5/31 사보원 6/1 마감 = 1~2일 양보·정상 흐름 복귀
- 외부 공모전·발표 critical 마감 = TickDeck 빌드 일시 정지·외부 우선

## 다음 step (자율 진행)

1. ✅ PRD v2.1 갱신 (본 layer)
2. 메모리 [project_tickdeck.md] 갱신 = wedge 재정의·Thiel framework
3. 노클 selection v2 작업 가이드 push (`inbox/from_honjin/`):
   - Primary 분류 (자동차·엔터·식품·교육·brand 컨설팅·marketing brief)
   - Secondary 분류 (포폴·이력서·학회·과제·회의 메모·기타)
   - 글로벌 리서치 자료 일괄 다운로드 (YC·McKinsey·BCG·Bain·Deloitte 공개 + ARK 추가 자료)
   - 메타데이터 schema strict (country·industry·language·license·source_url)
4. ClickUp 6주 검증 마일스톤 Task 등록 (Peppinch's works)
5. 회고·메모리 누적 ([klcha_recurring_patterns.md] 패턴 24·3·17 재발 카운트)

---

# v2.2 — 5/13 claude-for-legal 참고 적용 layer

> 출처: `anthropics/claude-for-legal` repo (5/13 후추님 공유·1,230 stars·Apache 2.0·9 practice area plugins·70+ named agents)
> 사상: plugin·skill·MCP 인프라 표준 + cold-start interview + named workflow agents
> 적용: 1단계 architecture base + 2~3단계 확장

## 1. Cold-start interview + Practice Profile (1단계 적용 ⭐)

claude-for-legal = 각 사용자 자기 playbook learn 시키는 *cold-start interview*·결과 = `CLAUDE.md` practice profile·skill이 read해서 매칭.

TickDeck v2 적용 (1단계):
- 사용자 첫 사용 시 = 5분 interview
  - 산업 (7카테고리 + 기타)
  - 청중 (임원·실무자·외부 클라이언트·투자자 등)
  - 톤 (정장·세미정장·casual)
  - 출처 정책 (각주·footer·인용 정도)
  - 분량 (8장·15장·30장·자유)
  - 한국어/영어/혼용
- 결과 = `tickdeck_profile.md` (사용자 세션 임시 저장·세션 종료 자동 삭제·계정 X)
- 다음 deck 생성 시 = profile 자동 read·매칭

## 2. Named workflow agents 사상 (1단계 ⭐)

claude-for-legal = 70+ named agents (Vendor Agreement Reviewer·DSAR Responder 등)·job-style 이름·single command. *단일 도구 X*·*특정 workflow per agent*.

TickDeck v2 적용 (1단계):

| Named Agent | 사용자 시각 | 산업 매칭 |
|---|---|---|
| Vendor Proposal Drafter | B2B 외주 제안서·brochure·press kit | 자동차·엔터·식품 |
| Brand Guide Builder | brand 가이드·디자인 시스템·시각 자료 | brand 컨설팅 |
| Marketing Brief Creator | marketing 전략·campaign brief | marketing |
| Industry Research Compiler | 산업 분석 보고서·시장 동향·경쟁사 | 금융·리서치 |
| Curriculum Pack Designer | 교육 커리큘럼·강의 자료 | 교육 |

각 agent = `/tickdeck:vendor-proposal`·`/tickdeck:brand-guide`·`/tickdeck:marketing-brief`·`/tickdeck:industry-research`·`/tickdeck:curriculum` 같은 single command sketch.

랜딩 페이지·UI = *"5 agents 중 골라서 사용"* 화면·단일 도구 X.

## 3. Practice-area plugin 사상 (architecture base 1단계·실 plugin 2~3단계)

claude-for-legal = 9 practice area plugins (commercial·corporate·employment 등). 각 plugin = 자기 skills·MCP·cold-start.

TickDeck v2 적용:
- 1단계 = single Streamlit MVP·근데 *코드 구조는 plugin 사상 base* (각 industry → 별도 module·skill·tone dictionary 분리)
- 2단계 (1년 후·동아시아 확장 시점) = 실 Claude Code plugin 빌드·`tickdeck-proposal`·`tickdeck-brand-consulting` 등 분리
- 3단계 = 산업별 7~12 plugin 확장

## 4. Source attribution + Assumption surfacing + Disclaimer (1단계 ⭐)

claude-for-legal guardrail:
- 모든 인용 출처 표기
- assumption 명시 (jurisdiction 등)
- explicit gate (filed/sent 전)
- disclaimer ("draft for review·not final")

TickDeck v2 적용 (1단계):
- 모든 자료 인용 = 자동 footer 또는 각주
- 시작 화면 disclaimer = "결과 deck = 초안·사용자가 검토·수정 의무"
- assumption 명시 = "산업: 자동차·청중: 임원·정장 톤" 등 인풋 표 deck 1페이지에 (옵션)
- gate = 다운로드 전 사용자 review 화면·1차 검토 후 다운로드

## 5. Scheduled agents (cron·자율 워커) (2~3단계)

claude-for-legal scheduled agents:
- Renewal Watcher (계약 만료 monitoring)
- Docket Watcher (소송 docket 감시)
- Reg Feed Watcher (규제 변경 감시)
- Launch Watcher (제품 출시 감시)

TickDeck v2 적용 (2~3단계):
- Industry Trend Watcher (산업 동향 monitoring·산업별 update alert)
- Template Update Suggester (templates.json 갱신·신규 자료 추가 시 자동 patterns 재추출)
- Client Re-engagement (사용자 재방문 alert·새 산업·새 deck 권장)
- (1단계 X·MVP 부담 X)

## 6. MCP connectors (2~3단계 deploy)

claude-for-legal MCP:
- 일반: Slack·Google Drive·Box
- 법률 전용: Ironclad·DocuSign·iManage·Everlaw·CourtListener

TickDeck v2 적용 (2~3단계):
- 1단계 = Streamlit local·MCP X
- 2단계 = Google Drive (사용자 자료 fetch)·Notion (사용자 작업 환경)·Figma (디자인 시스템)
- 3단계 = ClickUp·Linear (PM 도구)·Slack (사용자 work 영역)
- 3~4단계 글로벌 진입 시 = Bloomberg·CB Insights·Statista API plugin

## 7. Same system + 3 deploy choice (3단계 architecture)

claude-for-legal = same skills → Cowork·Code·Managed Agents API 3가지 deploy.

TickDeck v2 적용 (3단계):
- 1단계 = Streamlit local·tickdeck.peppinch.com
- 2단계 = Claude Cowork plugin·Anthropic Cowork 안 사용 가능
- 3단계 = Claude Code plugin·`anthropics/tickdeck-{industry}` 사상 자국 공개 (마지막 영역)
- 4단계 = Managed Agents API·B2B enterprise sales (영어권·풀타임 layer 결정 후)

## 갱신 사상 — 1단계 architecture base

1단계 빌드 시점부터 *plugin·skill·MCP 인프라 사상 base*·실 plugin·MCP 활성화 X. 2~4단계에서 자연 확장 가능한 구조.

```
tickdeck_v2/
├── app.py                    # Streamlit (1단계·MVP UI)
├── named_agents/             # Named agent 5종 (1단계·single workflow per file)
│   ├── vendor_proposal.py
│   ├── brand_guide.py
│   ├── marketing_brief.py
│   ├── industry_research.py
│   └── curriculum.py
├── pipeline/                 # 7단계 (parse·research·merge·narrative·quality·design·pptx)
├── practice_areas/           # plugin 사상 base (각 산업별 module·tone·schema)
│   ├── automotive/
│   ├── entertainment/
│   ├── food/
│   ├── education/
│   ├── brand_consulting/
│   ├── marketing/
│   └── finance/
├── shared/                   # v1 자산 (pptx_builder·3에이전트·quality.py)
├── profile/                  # cold-start interview + tickdeck_profile.md (세션 임시)
├── guardrails/               # source attribution·assumption surfacing·disclaimer
└── locales/                  # i18n (ko.json·ja.json 등)
```

## 6주 검증 마일스톤 영향 (Week 1·Week 4 갱신)

| Week | 기존 | 갱신 (claude-for-legal 참고) |
|---|---|---|
| 1 (5/13~5/19) | architecture base | + Cold-start interview 사상·named agents 5종 sketch·practice_areas 폴더 구조 잡기 |
| 4 (6/3~6/9) | Streamlit MVP·sample 5종 | + named agents UI (단일 도구 X·5 agents 골라 사용) + source attribution + disclaimer 화면 |

다른 Week (2·3·5·6) = 변경 X·그대로.

## 다음 step

1. ✅ PRD v2.2 layer 추가 (본 layer)
2. 메모리 [project_tickdeck.md] = claude-for-legal 사상 누적
3. ClickUp Week 1·Week 4 Task description 갱신
4. 노클 가이드 = 갱신 X (selection 분류·자료 수집 영역에 영향 X)
