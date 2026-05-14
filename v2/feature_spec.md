# TickDeck v2 — 기능 명세서 (feature_spec)

> 작성: 2026-05-15 02:20 KST (Ralph P3-T2)
> 기준: `PRD_v2.md` v2.1·v2.2 영역 + `PLAN_5-14.md` 갱신 layer 정합
> 영역: PLAN_5-13 7단계 중 3단계 (feature-spec) — 1단계 architecture base 정합·실 빌드 입력 자산
> 양식: 각 feature = (a) 사용자 가치·user goal / (b) 기능 명세·동작 / (c) 검증 가능 기준·acceptance criteria

---

## 0. 사상·범위

- Primary ICP: 한국 BD·marketing·컨설팅 agency·1인 외주·BYOD 실무자
- Time-to-value: 3~10분 (컨설팅 리서치 layer 자국)
- 사상: 단일 도구 X·5 Named Agents 선택 화면
- 1단계 architecture base = i18n·결제 어댑터·메타데이터 schema·practice_areas plugin 사상 base (활성화 X)
- 본 문서 영역 X (별도 영역): 와이어프레임 (2단계·후추님 직접)·실 task 분해 (6단계·writing-plans)

---

## 1. Cold-start interview (1단계 ⭐)

claude-for-legal `claude-init` 사상 적용·각 사용자 5분 onboarding interview → `tickdeck_profile.md` 세션 임시 저장.

### (a) 사용자 가치
- 매 deck 생성 시 동일 인풋 재입력 X·1회 5분 후 자동 매칭
- 산업·청중·톤·출처 정책 자기 playbook 학습 시키는 영역
- 결과 deck 정합도 ↑·랜덤 결과 X

### (b) 기능 명세

| 인풋 | 영역 | 선택지 |
|---|---|---|
| 산업 | 7카테고리 + 기타 | automotive·entertainment·food·education·brand_consulting·marketing·finance·기타 |
| 청중 | 4종 | 임원·실무자·외부 클라이언트·투자자 |
| 톤 | 3종 | 정장·세미정장·casual |
| 출처 정책 | 3종 | 각주 strict·footer·인용 자유 |
| 분량 | 4종 | 8장·15장·30장·자유 |
| 언어 | 3종 | 한국어·영어·혼용 |

저장 영역: `profile/tickdeck_profile.md` (세션 임시·종료 시 자동 삭제·DB X·계정 X)
재방문 시: 세션 신규·profile 재생성 (계정 X 정합)

### (c) acceptance criteria
- [ ] interview 5분 안 완료 (1인 사용자 dogfood 측정)
- [ ] 6 인풋 영역 다 선택 가능·skip OK (default = 자동 매칭)
- [ ] profile 결과 = 다음 named agent 자동 read·해당 정보 재입력 X
- [ ] 세션 종료 시 profile 파일 자동 삭제 검증 (cleanup 룰)
- [ ] 첫 화면 disclaimer 명시 ("계정 X·세션 종료 시 자동 삭제")

---

## 2. 5 Named Agents (1단계 ⭐)

claude-for-legal 70+ named agents 사상 적용·각 agent = single command + job-style 이름·workflow per agent.

### 2.1 Vendor Proposal Drafter

#### (a) 사용자 가치
- B2B 외주 제안서·brochure·press kit 자동 생성
- 한국 BD agency·1인 외주 실무자 대상
- 자동차·엔터·식품 산업 매칭 (Primary 3종)

#### (b) 기능 명세
- command: `/tickdeck:vendor-proposal`
- 입력: PDF (참고 자료) + profile (산업·청중·톤)
- 파이프라인: 7단계 전체 호출 (parse → research → merge → narrative → quality → design → pptx)
- 출력: PPTX 1개 (B2B 제안서 톤·한국 비즈니스 용어·존댓말)
- 산업 매칭: practice_areas/automotive·entertainment·food module read

#### (c) acceptance criteria
- [ ] 결과 deck 분량 = 8~15장 (profile 분량 정합)
- [ ] 한국 비즈니스 용어·존댓말 검증 (sample 5종 dogfood)
- [ ] 산업별 톤 dictionary 매칭 검증 (automotive ≠ entertainment)
- [ ] B2B 제안서 templates.json 패턴 5종+ 적용
- [ ] source attribution footer 자동 출력 검증

### 2.2 Brand Guide Builder

#### (a) 사용자 가치
- brand 가이드·디자인 시스템·시각 자료 deck 자동 생성
- brand 컨설팅 1인 외주·agency 대상 (Primary 1종)

#### (b) 기능 명세
- command: `/tickdeck:brand-guide`
- 입력: PDF (brand 자료·로고·color·typography) + profile
- 파이프라인: 7단계 호출·디자인 단계 (6번) strict (디자인 시스템 추출·재구성 사상)
- 출력: PPTX 1개 (brand 가이드·로고 영역·color palette·typography 영역·voice & tone)
- practice_areas/brand_consulting module read

#### (c) acceptance criteria
- [ ] 분량 = 15~30장 (brand 가이드 표준 분량)
- [ ] color palette·typography 영역 자동 추출·시각화 검증
- [ ] voice & tone 영역 = 사용자 profile 톤 정합
- [ ] 디자인 시스템 6종 (PRD line 41~45) 중 자동 매칭 검증
- [ ] 출처 표기 (사용자 PDF 원본 인용)

### 2.3 Marketing Brief Creator

#### (a) 사용자 가치
- marketing 전략·campaign brief deck 자동 생성
- marketing agency 실무자·1인 marketing 외주 대상

#### (b) 기능 명세
- command: `/tickdeck:marketing-brief`
- 입력: PDF (시장 자료·경쟁사·타깃·campaign 인풋) + profile
- 파이프라인: 7단계 호출·research 단계 (2번) strict (시장·경쟁사·트렌드 검색 layer)
- 출력: PPTX 1개 (campaign brief·타깃 분석·메시지·KPI·일정·예산 영역)
- practice_areas/marketing module read

#### (c) acceptance criteria
- [ ] 분량 = 8~15장 (brief 표준)
- [ ] 타깃 segmentation 영역 자동 추출 검증
- [ ] KPI 영역 = 정량 지표 명시 (전환·CAC·LTV 등)
- [ ] 경쟁사 분석 영역 = 3~5사 비교 표 자동 생성
- [ ] 출처 표기 (시장 자료 인용)

### 2.4 Industry Research Compiler

#### (a) 사용자 가치
- 산업 분석 보고서·시장 동향·경쟁사 분석 deck 자동 생성
- 금융·리서치·증권사 애널리스트·컨설팅 agency 대상
- 차별 layer 2번 (컨설팅 리서치 layer) ⭐ 가장 강한 영역

#### (b) 기능 명세
- command: `/tickdeck:industry-research`
- 입력: PDF (산업 자료·리서치 인풋) + profile
- 파이프라인: 7단계 호출·research 단계 (2번) maximum strict (1차/2차 자료·인용·각주 풀활성화)
- 출력: PPTX 1개 (산업 동향·시장 규모·경쟁 구도·트렌드·전망 영역·각주 strict)
- 학습 자산: ARK Big Ideas + 삼정KPMG·KPMG·Deloitte·BCG/McKinsey Korea + 한국 증권사 200~300개 templates 패턴
- practice_areas/finance module read

#### (c) acceptance criteria
- [ ] 분량 = 15~30장 (리서치 보고서 표준)
- [ ] 각주 strict = 모든 인용 출처 표기 (footer 또는 footnote)
- [ ] 시장 규모 수치 영역 = 출처 명시 (정부·KPMG·BCG·증권사 등)
- [ ] 경쟁 구도 = 3~7사 비교·시장 점유율 차트
- [ ] 컨설팅 리서치 톤 검증 (ARK·KPMG·BCG templates 정합 dogfood)
- [ ] Time-to-value 5~10분 (research 단계 layer 자국)

### 2.5 Curriculum Pack Designer

#### (a) 사용자 가치
- 교육 커리큘럼·강의 자료 deck 자동 생성
- 교육 강사·교육 컨설팅·기업 교육 담당자 대상

#### (b) 기능 명세
- command: `/tickdeck:curriculum`
- 입력: PDF (교육 자료·커리큘럼 인풋) + profile
- 파이프라인: 7단계 호출·내러티브 단계 (4번) strict (학습 목표·진행·실습·평가 구조)
- 출력: PPTX 1개 (학습 목표·차시별 진행·실습 영역·평가 항목)
- practice_areas/education module read

#### (c) acceptance criteria
- [ ] 분량 = 15~30장 (커리큘럼 표준·차시 단위)
- [ ] 학습 목표 영역 = Bloom's taxonomy 사상 정합 (인지·이해·적용·분석)
- [ ] 차시별 진행 영역 = 시간 분 단위 명시
- [ ] 실습·평가 항목 자동 영역 생성
- [ ] 톤 = 정장 X·세미정장 또는 casual (교육 영역 default)

---

## 3. 랜딩·UI 5 Agents 선택 화면 (1단계 ⭐)

PRD v2.2 line 458 명시: "5 agents 중 골라서 사용 화면·단일 도구 X". PLAN_5-14 와이어프레임 갱신 후보 영역 (와이어프레임 영역 = 후추님 직접).

### (a) 사용자 가치
- 사용자 자기 영역 명확 선택·단일 도구 옵션 폭발 X
- agent별 시각 = job-style 이름·사용자 즉시 이해

### (b) 기능 명세
- 화면 1 (랜딩): 5 agents 카드 영역 (이름·아이콘·1줄 설명·매칭 산업)
- 각 카드 click → agent별 onboarding (cold-start interview)
- 첫 화면 disclaimer 명시 ("세션 종료 시 자동 삭제·DB X·계정 X·BYOD OK")
- 모바일·데스크탑 동일 (Streamlit responsive)
- 데스크탑 권장 안내 (PDF 업로드·PPTX 다운로드 영역)

### (c) acceptance criteria
- [ ] 5 agents 카드 영역 모두 가시·click 가능
- [ ] 각 agent 이름·1줄 설명·매칭 산업 표기 검증
- [ ] disclaimer 명시 (3 영역 = 세션 삭제·DB X·계정 X)
- [ ] 모바일 viewport 동작 검증 (svh 적용·iOS Safari 정합)
- [ ] 데스크탑 권장 안내 1줄 명시

---

## 4. 7단계 Pipeline (1단계 ⭐)

PRD line 57~67 + v1 자산 정합. 5 named agents 모두 호출하는 공통 파이프라인.

### 4.1 Step 1 — PDF 파싱

#### (a) 사용자 가치
- PDF 텍스트 추출·자동 클린·1초 안 처리

#### (b) 기능 명세
- 도구: pypdf
- 입력: PDF 파일 (텍스트 PDF만·스캔 PDF X)
- 출력: 텍스트 + 메타데이터 (페이지 수·제목·작성일)
- 에러: 스캔 PDF 자국·안내 ("OCR 미래 영역")
- v1 자산 재활용

#### (c) acceptance criteria
- [ ] 텍스트 PDF 100% 추출 성공 (dogfood 10개)
- [ ] 스캔 PDF 자국 시 명확 에러 메시지
- [ ] 처리 시간 = 1초 이내 (PDF 1~30 페이지)

### 4.2 Step 2 — AI 조사 강화 (Research Layer)

#### (a) 사용자 가치
- 사용자 PDF 부족 영역 자동 보충·컨설팅 리서치 톤 layer
- 차별 layer 2번 = 가장 강한 영역 (Industry Research Compiler 영역에서 strict)

#### (b) 기능 명세
- 도구: Gemini grounding (Gemini 3.1 Flash Lite Preview)
- 입력: Step 1 텍스트 + profile (산업·청중·출처 정책)
- 동작: 키워드 추출 → 다회 검색 → 결과 수집 → 출처 메타데이터 누적
- 출력: 보충 자료 (1차/2차 자료·시장 통계·경쟁사 정보·트렌드·인용·URL·출처)
- agent별 strict 영역:
  - Industry Research Compiler = maximum strict
  - Marketing Brief Creator = strict (시장·경쟁사·타깃)
  - Vendor Proposal Drafter = light (산업 트렌드만)
  - Brand Guide Builder = light (brand 인용만)
  - Curriculum Pack Designer = light (학습 자료 보충)

#### (c) acceptance criteria
- [ ] grounding 호출 1회 이상 성공 (Gemini API 응답 검증)
- [ ] 출처 메타데이터 누적 (URL·title·snippet·search_term)
- [ ] 출처 정책 strict 모드 = 모든 보충 자료 출처 명시 검증
- [ ] agent별 strict 정도 차이 검증 (Industry Research vs Vendor Proposal)
- [ ] Time-to-value 3~10분 자국 (research strict 시 5~10분)

### 4.3 Step 3 — 자료 통합 (Merge)

#### (a) 사용자 가치
- 원본 PDF + AI 조사 보충 자료 통합·중복 제거·우선순위 정렬

#### (b) 기능 명세
- 입력: Step 1 + Step 2 결과
- 동작: 중복 거름·원본 우선·보충 자료 출처 자국 (각주 영역)
- 출력: 통합 자료 (섹션별 구분·source_id 자국)
- 사실 검증 옵션 (strict 모드): 복수 소스 교차

#### (c) acceptance criteria
- [ ] 중복 자료 거름 검증 (dogfood 측정)
- [ ] 원본 자료 우선 검증 (보충 자료 = 원본 보완 영역만)
- [ ] source_id 자국 = Step 7 PPTX 각주 영역 자동 read

### 4.4 Step 4 — 내러티브 구조화 (3에이전트 + templates 매칭)

#### (a) 사용자 가치
- 통합 자료 → 인 흐름 deck 구조 자동 매칭·후추님 137개 + 글로벌 templates 정합

#### (b) 기능 명세
- 도구: v1 3에이전트 (Architect·Narrator·Editor) + templates.json
- 입력: Step 3 통합 자료 + profile (청중·톤·분량) + agent별 산업 매칭
- 동작: templates.json 패턴 매칭 → 내러티브 구조 결정 → 슬라이드별 내용 분배
- 출력: SlideType[] (제목·구조·내용·source_id)
- v1 자산 재활용 (gemini_client·schemas.py)
- agent별 templates 분류 read:
  - Vendor Proposal Drafter = 137개 B2B 제안서 패턴
  - Brand Guide Builder = brand 가이드 패턴
  - Marketing Brief Creator = marketing 패턴
  - Industry Research Compiler = ARK + KPMG/BCG 패턴
  - Curriculum Pack Designer = 교육 커리큘럼 패턴

#### (c) acceptance criteria
- [ ] templates.json 패턴 매칭 ≥ 80% (dogfood 측정)
- [ ] SlideType[] 모든 슬라이드 = 제목·내용·source_id 영역 채움
- [ ] 분량 = profile 정합 (±2장 자국)
- [ ] 청중·톤 정합 검증 (sample dogfood)

### 4.5 Step 5 — 품질 검증 (quality.py)

#### (a) 사용자 가치
- 결과 deck 품질 자동 검증·룰 위반 시 자동 재생성

#### (b) 기능 명세
- 도구: v1 quality.py (RULE A·J·B)
- 입력: Step 4 SlideType[]
- 동작: 룰 위반 영역 자국 → 재생성 (최대 2회)
- 출력: 검증 통과 SlideType[]
- v1 자산 재활용

#### (c) acceptance criteria
- [ ] RULE A·J·B 모두 적용 검증
- [ ] 위반 시 재생성 최대 2회 자국
- [ ] 2회 실패 시 사용자 안내·재시도 가능

### 4.6 Step 6 — 디자인 시스템 자동 매칭 (6종)

#### (a) 사용자 가치
- 6종 디자인 시스템 중 사용자 profile + agent 정합 자동 매칭
- 옵션 폭발 X·1-딸깍 가치 유지

#### (b) 기능 명세
- 6종: Minimal White·Soft Coral·Dark Mode·Deep Blue Pro·비즈니스 정장·콘텐츠 컬러풀 (PRD line 41~45)
- 입력: Step 5 + profile (톤·산업)
- 동작: 톤 매칭 알고리즘 → 디자인 시스템 1종 자동 결정
- 출력: 디자인 토큰 (색·폰트·간격·DESIGN.md v0.1 정합)
- 1회 변경 영역 = 사용자 옵션·다른 5종 중 1종 재매칭 후 v2 deck 다운로드

#### (c) acceptance criteria
- [ ] 6종 디자인 토큰 정의 완비 (DESIGN.md 갱신)
- [ ] 톤 매칭 알고리즘 검증 (정장 → Deep Blue Pro·세미정장 → Minimal White 등)
- [ ] agent별 default 매칭 검증 (Industry Research → Deep Blue Pro·Vendor Proposal → 비즈니스 정장 등)
- [ ] 1회 변경 시 다른 5종 영역 가시·v2 deck 생성 검증

### 4.7 Step 7 — PPTX 생성 (python-pptx)

#### (a) 사용자 가치
- 사용자 즉시 다운로드 가능 PPTX 파일 1개·외부 도구 (PowerPoint·Google Slides) 편집 가능

#### (b) 기능 명세
- 도구: python-pptx + DESIGN.md 토큰
- 입력: Step 5 SlideType[] + Step 6 디자인 토큰
- 출력: PPTX 파일 1개
- guardrails:
  - source attribution footer 자동 출력 (Step 3 source_id 영역)
  - assumption surfacing 1페이지 = "산업·청중·톤" 인풋 표 (옵션)
  - disclaimer = "draft for review·사용자 검토·수정 의무" 첫 페이지
- v1 자산 재활용 (shared/pptx_builder.py)

#### (c) acceptance criteria
- [ ] PPTX 파일 PowerPoint·Google Slides·Keynote 열기 검증 (3 도구 dogfood)
- [ ] source attribution footer 모든 슬라이드 자동 출력
- [ ] disclaimer 1페이지 자동 출력
- [ ] assumption 영역 옵션 동작 검증
- [ ] 파일 크기 < 10MB (1~30장 영역)

---

## 5. Practice Areas Plugin 사상 (1단계 base·2~3단계 활성화)

PRD v2.2 line 460~468 정합. 1단계 = 코드 구조만·실 plugin 빌드 X.

### (a) 사용자 가치
- 산업별 톤·용어·schema 분리·향후 plugin 확장 가능 base
- 사용자 = 1단계에서 영역 X (인프라 영역)

### (b) 기능 명세
- 폴더 구조 base (PLAN_5-14 line 96~119 정합):
```
practice_areas/
├── automotive/       (자동차)
├── entertainment/    (엔터)
├── food/             (식품)
├── education/        (교육)
├── brand_consulting/ (brand 컨설팅)
├── marketing/        (marketing)
└── finance/          (금융·리서치)
```
- 각 module 내 (1단계 빈 파일·placeholder):
  - `tone_dict.json` (산업별 용어·존댓말 영역)
  - `templates.json` (산업별 패턴·후추님 137개 분류 영역)
  - `schema.json` (산업별 메타데이터 schema)
- 2단계 (1년 후·동아시아 확장) = 실 Claude Code plugin 빌드
- 3단계 = 산업별 7~12 plugin 확장

### (c) acceptance criteria
- [ ] 7 module 폴더 신설 (1단계 빈 파일 OK)
- [ ] 각 module = `tone_dict.json`·`templates.json`·`schema.json` 3 파일 base
- [ ] 5 named agents 각각 자기 module 자동 read 검증 (Vendor Proposal → automotive·entertainment·food module)
- [ ] practice_areas 영역 변경 시 named agents 영향 X 검증 (격리·plugin 사상)

---

## 6. Guardrails (1단계 ⭐)

PRD v2.2 line 471~480 + claude-for-legal guardrail 사상 정합.

### 6.1 Source Attribution

#### (a) 사용자 가치
- 모든 인용 자료 출처 자동 표기·사용자 신뢰도 ↑·컨설팅 리서치 톤

#### (b) 기능 명세
- Step 2 (AI 조사) 결과 = 메타데이터 (URL·title·source_id) 누적
- Step 7 (PPTX 생성) = source_id → footer 또는 각주 자동 매핑
- 출처 정책 strict 모드 (profile 정합):
  - strict = 각주 또는 footnote (Industry Research Compiler 영역 default)
  - footer = footer 영역만 (Marketing Brief 영역 default)
  - 자유 = footer 없음·인용 영역만 (자유 모드)

#### (c) acceptance criteria
- [ ] 모든 보충 자료 source_id 영역 누적 검증
- [ ] strict 모드 = 모든 슬라이드 각주 출력 검증
- [ ] 사용자 profile 출처 정책 정합 검증

### 6.2 Assumption Surfacing

#### (a) 사용자 가치
- 사용자 인풋 (산업·청중·톤) 결과 deck에 명시·블랙박스 X

#### (b) 기능 명세
- Step 7 PPTX 생성 시 1페이지 = "본 deck 영역 인풋: 산업·청중·톤·분량·출처 정책" 표 자동 추가
- 옵션 (profile에서 on/off)
- 사용자 결과 review·자기 인풋 영역 재확인 가능

#### (c) acceptance criteria
- [ ] assumption 1페이지 자동 생성 (profile on 모드)
- [ ] 6 인풋 영역 (산업·청중·톤·출처 정책·분량·언어) 모두 표기
- [ ] profile off 모드 = 1페이지 생략 검증

### 6.3 Disclaimer

#### (a) 사용자 가치
- "draft for review·사용자 검토·수정 의무" 영역 명시·법적·전문가 책임 보호 영역

#### (b) 기능 명세
- 첫 화면 disclaimer (1단계 명시): "결과 deck = 초안·사용자 검토·수정 의무·계정 X·세션 종료 시 자동 삭제·BYOD 가능"
- PPTX 첫 페이지 disclaimer 자동 추가: "draft for review · not final · 본 deck = AI 보조·사용자 검토 의무"

#### (c) acceptance criteria
- [ ] 첫 화면 disclaimer 가시 검증
- [ ] PPTX 첫 페이지 disclaimer 자동 출력 검증
- [ ] 사용자 review gate 다운로드 전 영역 가시 검증

### 6.4 Review Gate

#### (a) 사용자 가치
- 다운로드 전 사용자 1차 review 영역·실수·의도 X 결과 즉시 polic

#### (b) 기능 명세
- Step 7 PPTX 생성 후 = 미리보기 화면 (썸네일 영역) → "다운로드"·"재생성" 버튼
- 재생성 = 1회만 (PRD 결정 8 정합·스타일 변경 영역)
- 다운로드 시 파일 1~2개 (원본·v2 영역)

#### (c) acceptance criteria
- [ ] 미리보기 화면 가시 검증 (썸네일 또는 1페이지 미리보기)
- [ ] "다운로드"·"재생성" 버튼 동작 검증
- [ ] 재생성 1회만 자국·2회 시도 시 안내

---

## 7. Architecture Base (1단계 base·풀 활성화 X)

PRD v2.1 line 313~321 정합·premature globalization 회피·1단계 base만.

### 7.1 i18n base
- 1단계: ko 단일·하드코딩 X·모든 텍스트 변수화·`locales/ko.json` 1 파일
- 빈 파일 신설: `locales/ja.json`·`locales/zh-TW.json`·`locales/en.json` (placeholder)
- 2단계 활성화 = ja 파일 채움 시 자동 동작

### 7.2 톤 dictionary
- 1단계: 한국 산업별 5~10종 (practice_areas/<industry>/tone_dict.json)
- 2~4단계 활성화 = 일본·중화권·동남아·영어권 plug-in

### 7.3 자료 메타데이터 schema
- 1단계 strict: country·industry·language·license·source_url 필드 strict
- 모든 자료 (templates·보충 자료) = 5 필드 의무 자국

### 7.4 결제 어댑터
- 1단계: 토스페이먼츠 단일 (PRD pricing 정합·1회 5,000~10,000원)
- 빈 어댑터: `payment/stripe.py` (placeholder)
- 2단계 활성화 = Stripe·동남아 결제

### 7.5 Distribution 어댑터
- 1단계: 펩핀치·잡솔트·X 한국 (waitlist + 디스콰이엇 + 스타트업 슬랙)
- 2~3단계 활성화 = ProductHunt·Reddit·Asia 채널

### (c) acceptance criteria (architecture base 영역)
- [ ] `locales/ko.json` 모든 UI 텍스트 영역 (하드코딩 X 검증)
- [ ] 메타데이터 schema 5 필드 모든 자료 영역 의무 검증
- [ ] 결제 어댑터 abstract class 영역 정의·toss 1 구현 영역
- [ ] 빈 placeholder 파일 (ja·zh-TW·en·stripe) 신설 검증

---

## 8. Secondary 옵션 (1년 운영 후 검토·marketing X)

PRD v2.1 line 285~292 정합. Primary B2B strict 영역 외 secondary 옵션.

### (a) 사용자 가치
- 도구 자유 허용 영역·marketing X·waitlist 영역에서 자연 발견 사용자만
- 5종: 포폴·이력서·학회·과제·회의 메모

### (b) 기능 명세
- 1단계 = 명시 영역 X·실 구현 X·기존 v1 sample 4종 보존만
- 사용자 자유 입력 영역 (5 named agents 외 영역) = "기타·자유" agent 옵션 (1년 후 검토)
- marketing 영역 = 0·landing 페이지 자국 X

### (c) acceptance criteria
- [ ] 1단계 secondary 영역 명시 X 검증 (UI·landing 영역)
- [ ] sample 4종 (이력서·학회·과제·회의 메모) 영역 = v1 자산 보존만 (재빌드 X)
- [ ] 1년 운영 후 (2027 4~5월) 검토 자국

---

## 9. 외부 도구 안내 (편집 영역)

PRD 결정 2번 정합·TickDeck 내부 편집 X.

### (a) 사용자 가치
- 사용자 PPTX 다운로드 후 외부 도구 (PowerPoint·Google Slides·Keynote) 자유 편집
- TickDeck 영역 = 생성만·편집 X·복잡도 ↓

### (b) 기능 명세
- 다운로드 화면 = "외부 도구에서 편집 안내" 1줄 + 3 도구 아이콘 (PPT·Slides·Keynote)
- 안내 = "결과물 만족 X 시 1회 재생성·또는 외부 도구 직접 수정"

### (c) acceptance criteria
- [ ] 다운로드 화면 = 외부 도구 안내 1줄 가시
- [ ] 3 도구 (PPT·Slides·Keynote) PPTX 호환 검증 (Step 7 acceptance 영역 정합)

---

## 10. 가설 확인/기각 (P3-T2)

**가설**: "PRD v2.1·v2.2 정합 영역 feature 영역 명세 영역 = 5 named agents (Vendor Proposal·Brand Guide·Marketing Brief·Industry Research·Curriculum) + cold-start interview + 7단계 pipeline (parse·research·merge·narrative·quality·design·pptx) + practice_areas plugin 사상 영역. feature-spec:index skill 또는 본진 자율 영역."

→ ✅ **확인**. 본 feature_spec.md 영역 = PRD v2.1·v2.2 영역 모든 feature 영역 명세 영역 자국:
- 5 named agents = 영역 2 (각 a/b/c 영역 작성·산업 매칭·command sketch·acceptance criteria)
- Cold-start interview = 영역 1 (6 인풋·세션 임시·a/b/c 작성)
- 7단계 pipeline = 영역 4 (각 step별 a/b/c·v1 자산 정합·agent별 strict 정도 차이)
- Practice areas plugin = 영역 5 (7 module 폴더 구조·tone_dict·templates·schema 3 파일·1단계 base·2~3단계 plugin 빌드)
- Guardrails = 영역 6 (source attribution·assumption surfacing·disclaimer·review gate 4 영역)
- Architecture base = 영역 7 (i18n·결제 어댑터·메타데이터 schema·distribution·1단계 base 정합)

본진 자율 영역 = OK (feature-spec:index skill X·본 영역 = 더 자세한 영역 영역 + agent별 acceptance criteria 구체 영역).

---

## 11. 다음 step

1. ✅ feature_spec.md 신설 (본 layer·P3-T2 완료)
2. ⏳ test_scenarios.md (P3-T3·4단계·pm-execution:test-scenarios skill)
3. ⏳ pre_mortem.md (P3-T4·5단계·pm-execution:pre-mortem skill)
4. ⏳ PLAN_implementation.md (P3-T5·6단계·superpowers:writing-plans·2~5분 task 분해)
5. ⏳ 노클 PDF 교차 분석 (P3-T6·7단계·자동 진행 영역)
6. 와이어프레임 (2단계) = 후추님 직접 영역·prompt 갱신 후보 (PLAN_5-14 line 122~132)

## 12. 가시성 (한 줄)

feature_spec.md = 5 named agents + 7단계 pipeline + cold-start interview + practice_areas plugin 사상 + guardrails + architecture base 영역 명세 자국 완료·1단계 빌드 입력 자산.
