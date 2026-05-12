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
