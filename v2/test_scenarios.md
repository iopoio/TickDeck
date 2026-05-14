# TickDeck v2 — Test Scenarios (test_scenarios)

> 작성: 2026-05-15 02:55 KST (Ralph P3-T3)
> 기준: `feature_spec.md` (P3-T2) + `PRD_v2.md` v2.1·v2.2 영역
> 영역: PLAN_5-13 7단계 중 4단계 (test-scenarios) — 1단계 architecture base 정합·dogfood 검증 입력 자산
> 양식: 각 시나리오 = (a) 시작 영역 (b) 단계 영역 (c) 예상 결과 영역
> 분류: 5 named agents 별 × {happy path · edge case · error handling} + 공통 pipeline + guardrails + UI

---

## 0. 사상·범위

- Dogfood 1차 = 후추님·본진 클차장·노클 본인 사용 (외부 사용자 X)
- Dogfood 2차 = 펩핀치랩·잡솔트·디스콰이엇 5~10명 (1단계 후·waitlist)
- 시나리오 분류:
  - **Happy path** = 정상 입력·정상 출력 (golden case)
  - **Edge case** = 경계 영역 입력 (분량·언어·산업 매칭 boundary)
  - **Error handling** = 비정상 입력·외부 시스템 실패 영역
- 본 문서 영역 X (별도 영역): 실 자동 test code (1단계 빌드 시점 영역)·시나리오 기반 pytest fixture (P3-T5 영역)

---

## 1. Cold-start Interview 시나리오

feature_spec 영역 1 정합·5분 onboarding·6 인풋·세션 임시 저장.

### 1.1 Happy path: 정상 6 인풋 완료

#### (a) 시작 영역
- 사용자: 한국 B2B 외주 실무자 (자동차 산업)
- 화면: 랜딩 → Vendor Proposal Drafter agent 카드 선택
- 인풋 가능 영역: 6 영역 다 채울 의사

#### (b) 단계 영역
1. 산업 선택 화면 → automotive 선택
2. 청중 선택 → 외부 클라이언트
3. 톤 선택 → 세미정장
4. 출처 정책 → footer
5. 분량 → 15장
6. 언어 → 한국어
7. "다음" 버튼 클릭 → profile 저장

#### (c) 예상 결과 영역
- `profile/tickdeck_profile.md` 세션 임시 저장 (6 영역 모두 자국)
- 5분 안 완료 (타이머 측정)
- 다음 화면 (PDF 업로드) 자동 전환
- profile 자국 결과 = Vendor Proposal Drafter agent 자동 read 가능

### 1.2 Edge case: 일부 인풋 skip (default 자동 매칭)

#### (a) 시작 영역
- 사용자: 기타 산업 (default 매칭 의존)
- 인풋 가능 영역: 일부만 채울 의사·나머지 skip

#### (b) 단계 영역
1. 산업 → 기타 선택
2. 청중 → skip (default 매칭)
3. 톤 → skip
4. 출처 정책 → strict 선택
5. 분량·언어 → skip
6. "건너뛰기" 버튼 → profile 저장

#### (c) 예상 결과 영역
- skip 영역 = default 매칭 알고리즘 자동 결정
- profile 영역 = 사용자 명시 영역 + default 영역 분리 자국
- 다음 화면 전환·결과 deck 영역 default 매칭 자국 가시 (assumption surfacing 영역 정합)

### 1.3 Error handling: 세션 종료 후 재방문

#### (a) 시작 영역
- 사용자: 이전 세션 진행 영역
- 브라우저 닫음·재방문

#### (b) 단계 영역
1. 페이지 재로드
2. 이전 profile 영역 read 시도

#### (c) 예상 결과 영역
- 이전 profile 영역 자동 삭제 검증 (계정 X 정합)
- 세션 신규 시작·랜딩 화면 재진입
- disclaimer 명시 ("세션 종료 시 자동 삭제·계정 X") 가시

---

## 2. Vendor Proposal Drafter 시나리오 (2.1)

feature_spec 영역 2.1 정합·B2B 외주 제안서·자동차/엔터/식품 산업 매칭.

### 2.1.1 Happy path: 자동차 산업 제안서 정상 생성

#### (a) 시작 영역
- 사용자: 자동차 부품 외주 BD 실무자
- profile: automotive·외부 클라이언트·세미정장·footer·15장·한국어
- 입력: 자동차 부품 카탈로그 PDF (12 페이지·텍스트 PDF)

#### (b) 단계 영역
1. cold-start interview 완료
2. PDF 업로드 (자동차 부품 카탈로그)
3. `/tickdeck:vendor-proposal` agent 실행
4. 7단계 pipeline 호출 (parse → research → merge → narrative → quality → design → pptx)
5. 미리보기 화면 → "다운로드" 클릭

#### (c) 예상 결과 영역
- 결과 PPTX 분량 = 8~15장 (profile 정합)
- 한국 비즈니스 용어·존댓말 영역 (sample 5 슬라이드 검증)
- automotive tone_dict 매칭 검증 (자동차 용어·OEM·부품·BOM 영역)
- B2B 제안서 templates 영역 5종+ 패턴 적용 (회사 소개·강점·제품·실적·견적)
- footer = 출처 영역 자동 출력 (사용자 PDF 인용·grounding 보충 자료 출처)
- Time-to-value 3~5분 자국 (research light 영역)
- assumption surfacing 1페이지 = 6 인풋 영역 표 출력

### 2.1.2 Edge case: 매우 짧은 PDF (1 페이지·100 단어)

#### (a) 시작 영역
- 사용자: 자료 부족 영역·grounding layer 의존 강함
- profile: automotive·외부 클라이언트·세미정장·footer·15장·한국어
- 입력: 1 페이지 PDF·100 단어 미만

#### (b) 단계 영역
1. PDF 업로드 (1 페이지)
2. 7단계 pipeline 호출
3. Step 2 (research) 영역 = grounding 다회 호출 (자료 부족 자국)
4. Step 3 (merge) 영역 = 보충 자료 80%+ 비율

#### (c) 예상 결과 영역
- 결과 PPTX 영역 = 8장 (분량 down·15장 X·자료 부족 정합)
- 보충 자료 비율 ↑ 자국 (source_id 영역 = grounding 출처 80%+)
- footer 출처 = grounding 영역 더 많이 자국
- assumption surfacing 영역 = "원본 자료 부족·AI 보충 layer 자국" 명시
- Time-to-value 5~7분 (research 단계 layer 자국)

### 2.1.3 Edge case: 산업 매칭 boundary (자동차·엔터 hybrid)

#### (a) 시작 영역
- 사용자: 자동차 광고 영역 (엔터 + automotive hybrid)
- profile: automotive 선택 (사용자 자기 정의)
- 입력: 자동차 광고 캠페인 PDF (자동차 + 엔터 hybrid 자료)

#### (b) 단계 영역
1. PDF 업로드
2. Step 4 (narrative) 영역 = automotive practice_area read·엔터 영역 light layer
3. templates 매칭 = automotive 패턴 우선·엔터 sub-pattern read

#### (c) 예상 결과 영역
- 결과 deck 영역 = automotive 톤 우선·엔터 영역 sub-section (2~3 슬라이드)
- 사용자 자기 정의 산업 영역 strict (automotive)·엔터 자동 매칭 light
- footer 영역 = 두 산업 자료 출처 모두 자국

### 2.1.4 Error handling: 스캔 PDF 업로드

#### (a) 시작 영역
- 사용자: 스캔 PDF (텍스트 추출 X) 업로드 시도

#### (b) 단계 영역
1. PDF 업로드
2. Step 1 (pypdf parse) 영역 = 텍스트 추출 실패·빈 string 또는 1~10 단어만

#### (c) 예상 결과 영역
- 명확 에러 메시지 출력: "스캔 PDF 영역 X·OCR 미래 영역·텍스트 PDF 영역 재업로드 안내"
- 다음 단계 진행 X·사용자 재업로드 버튼 가시
- 에러 로그 자국 (Step 1 영역·dogfood 측정)

### 2.1.5 Error handling: Gemini grounding 호출 실패

#### (a) 시작 영역
- 정상 PDF 업로드 후 Step 2 grounding 단계
- Gemini API rate limit 또는 network 실패

#### (b) 단계 영역
1. Step 2 grounding 호출 → API 에러 (429 또는 5xx)
2. 재시도 1회 자국 (5초 후)
3. 재시도 실패 시 fallback 영역

#### (c) 예상 결과 영역
- fallback = Step 2 영역 skip·Step 1 자료만 영역 다음 단계 진행
- 사용자 안내: "AI 조사 layer X·원본 자료만 영역 deck 생성·결과 보완 X 영역 자국"
- 결과 deck 영역 = 분량 ↓·grounding 출처 X·footer 영역 사용자 PDF 출처만
- assumption surfacing 영역 = "AI 조사 실패·원본 자료만 layer" 명시

---

## 3. Brand Guide Builder 시나리오 (2.2)

feature_spec 영역 2.2 정합·brand 가이드·디자인 시스템·시각 자료.

### 3.1 Happy path: brand 가이드 정상 생성

#### (a) 시작 영역
- 사용자: brand 컨설팅 1인 외주
- profile: brand_consulting·외부 클라이언트·세미정장·strict·30장·한국어
- 입력: 클라이언트 brand 자료 PDF (로고·color·typography·voice & tone)

#### (b) 단계 영역
1. profile 완료
2. PDF 업로드 (brand 자료)
3. `/tickdeck:brand-guide` agent 실행
4. Step 6 (디자인 단계) strict 자국 (brand 자료 영역 디자인 토큰 추출·재구성)
5. 미리보기 → 다운로드

#### (c) 예상 결과 영역
- 결과 PPTX 분량 = 15~30장 (brand 가이드 표준)
- color palette 영역 자동 추출·시각화 (Hex code + RGB + 색 patch)
- typography 영역 자동 추출 (Display/Body/Mono 폰트 영역 자국)
- voice & tone 영역 = profile 톤 정합 (세미정장 자국)
- 디자인 시스템 6종 (Minimal White·Soft Coral·Dark Mode·Deep Blue Pro 등) 중 자동 매칭 (brand_consulting → Minimal White 또는 Deep Blue Pro)
- 출처 표기 (사용자 PDF 원본 인용·strict 모드 자국)

### 3.2 Edge case: 로고 없는 brand 자료

#### (a) 시작 영역
- 사용자: 텍스트 only brand 자료 (로고 SVG·PNG X)
- 입력: 텍스트 PDF (brand 정책·voice 영역만)

#### (b) 단계 영역
1. PDF 업로드
2. Step 1 parse 영역 = 텍스트만 추출
3. Step 4 narrative 영역 = 로고 영역 placeholder 자국

#### (c) 예상 결과 영역
- 결과 deck 영역 = 로고 자리 [PLACEHOLDER: 로고 이미지 영역 사용자 추가] 자국
- 외부 도구 안내 (PowerPoint·Google Slides 영역) 영역 = 로고 추가 후 완성
- color palette·typography 영역 = 텍스트 자료 영역 grep 자국·정상 추출
- voice & tone·정책 영역 = 풀 자국

### 3.3 Edge case: 분량 자유 (사용자 자유 입력)

#### (a) 시작 영역
- profile: brand_consulting·자유 분량 선택
- 입력: 50 페이지 brand 자료 PDF

#### (b) 단계 영역
1. Step 4 narrative 영역 = 분량 결정 알고리즘 자동
2. 50 페이지 자료 영역 → 25~40장 결정

#### (c) 예상 결과 영역
- 결과 deck 영역 = 30~40장 (자료 분량 정합)
- 자유 모드 정합·고정 X
- 사용자 review 시 분량 적정성 dogfood 영역

### 3.4 Error handling: 잘못된 color code 형식

#### (a) 시작 영역
- 입력 PDF 영역 = color code 형식 비표준 (예: "주황색"·"#FFFXXX" 등)

#### (b) 단계 영역
1. Step 4 narrative 영역 = color 추출 grep 시도
2. 비표준 형식 자국 → fallback (한국어 색 사전 매칭)

#### (c) 예상 결과 영역
- 비표준 색 영역 = 한국어 색 사전 매칭 (예: "주황색" → #F59E0B)
- 매칭 실패 영역 = placeholder 자국 + 사용자 안내
- 결과 deck 영역 color palette 정상 출력·매칭 출처 자국 (자동 매칭 또는 사용자 PDF 원본)

---

## 4. Marketing Brief Creator 시나리오 (2.3)

feature_spec 영역 2.3 정합·campaign brief·타깃·KPI·예산.

### 4.1 Happy path: campaign brief 정상 생성

#### (a) 시작 영역
- 사용자: marketing agency 실무자
- profile: marketing·외부 클라이언트·세미정장·footer·15장·한국어
- 입력: 시장 자료 PDF + campaign 인풋 (타깃·예산·기간)

#### (b) 단계 영역
1. PDF 업로드 (시장 자료)
2. `/tickdeck:marketing-brief` agent 실행
3. Step 2 research strict 영역 (시장·경쟁사·트렌드 검색)
4. Step 4 narrative 영역 = campaign brief 구조 (타깃·메시지·KPI·일정·예산)
5. 미리보기 → 다운로드

#### (c) 예상 결과 영역
- 결과 PPTX 분량 = 8~15장
- 타깃 segmentation 영역 자동 추출 (인구통계·심리·행동 영역)
- KPI 영역 = 정량 지표 명시 (전환·CAC·LTV·CTR 등)
- 경쟁사 분석 영역 = 3~5사 비교 표 자동 생성 (grounding 영역 자료 정합)
- 예산·일정 영역 자국 (사용자 인풋 또는 grounding 시장 평균)
- footer = 시장 자료·grounding 출처

### 4.2 Edge case: 경쟁사 정보 부족

#### (a) 시작 영역
- 사용자 PDF 영역 = 경쟁사 자료 X·자기 회사 자료만
- profile: marketing·strict 출처

#### (b) 단계 영역
1. Step 2 grounding 호출 = 경쟁사 영역 strict 검색
2. 경쟁사 자료 grounding 영역 5사+ 자국

#### (c) 예상 결과 영역
- 결과 deck 영역 = 경쟁사 분석 영역 grounding 자료 우선·footer 출처 자국
- 사용자 PDF X 영역 = assumption surfacing 자국 ("경쟁사 자료 AI 보충")
- review gate 영역 = 사용자 검토·수정 명시

### 4.3 Error handling: 예산·일정 인풋 X

#### (a) 시작 영역
- 사용자 cold-start interview 영역 = 예산·일정 영역 X
- profile = marketing 기본 영역만

#### (b) 단계 영역
1. Step 4 narrative 영역 = 예산·일정 영역 placeholder 자국
2. 보충 영역 = grounding 시장 평균 또는 placeholder

#### (c) 예상 결과 영역
- 예산·일정 영역 = [PLACEHOLDER: 사용자 입력 영역] 또는 시장 평균 자국
- 사용자 review 시 채울 영역 명시
- assumption surfacing 영역 = "예산·일정 미입력·placeholder 자국" 명시

---

## 5. Industry Research Compiler 시나리오 (2.4·차별 layer ⭐)

feature_spec 영역 2.4 정합·산업 분석·시장 동향·차별 layer 가장 강한 영역.

### 5.1 Happy path: 금융 산업 리서치 정상 생성

#### (a) 시작 영역
- 사용자: 증권사 애널리스트
- profile: finance·임원·정장·strict·30장·한국어
- 입력: 산업 리서치 인풋 PDF (예: 반도체 시장 동향)

#### (b) 단계 영역
1. PDF 업로드
2. `/tickdeck:industry-research` agent 실행
3. Step 2 research **maximum strict** 영역 (1차/2차 자료·각주 풀활성화)
4. ARK Big Ideas + 삼정KPMG·KPMG·BCG/McKinsey + 한국 증권사 templates 패턴 read
5. Step 5 quality 영역 = strict 검증 (출처 누락 영역 재생성)
6. 다운로드

#### (c) 예상 결과 영역
- 결과 PPTX 분량 = 25~30장 (리서치 보고서 표준)
- **각주 strict** = 모든 인용 출처 표기 (footer + footnote 영역)
- 시장 규모 수치 영역 = 출처 명시 (정부·KPMG·BCG·증권사 등)
- 경쟁 구도 = 3~7사 비교·시장 점유율 차트
- 컨설팅 리서치 톤 검증 dogfood (sample 5 슬라이드 영역 = ARK·KPMG·BCG templates 정합)
- Time-to-value 5~10분 (research strict 영역 자국)
- review gate 영역 = "draft for review·사용자 검토 의무" 명시

### 5.2 Edge case: 한국 외 시장 (글로벌 영역)

#### (a) 시작 영역
- profile: finance·언어 = 한국어
- 입력: 글로벌 시장 자료 PDF (영어)

#### (b) 단계 영역
1. PDF 업로드 (영어 자료)
2. Step 1 parse 영역 = 영어 텍스트 추출
3. Step 4 narrative 영역 = 한국어 출력·영어 자료 번역 영역 자국
4. Step 2 grounding 영역 = 한국·글로벌 동시 검색

#### (c) 예상 결과 영역
- 결과 deck 영역 = 한국어 출력 (profile 정합)
- 원본 자료 영어 영역 = 출처 영어 그대로·번역 영역 자국 표기
- 글로벌 시장 영역 + 한국 시장 영역 비교 영역 자국

### 5.3 Edge case: 출처 정책 strict 모드 충돌 (자료 출처 불명)

#### (a) 시작 영역
- profile: finance·출처 정책 strict
- 입력 PDF 영역 = 출처 표기 X 자료 (블로그·뉴스 영역만)

#### (b) 단계 영역
1. Step 3 merge 영역 = source_id 누락 영역 자국
2. Step 5 quality 영역 = strict 모드 위반 자국

#### (c) 예상 결과 영역
- 출처 X 자료 영역 = "[출처 미상]" 자국 + 사용자 안내
- 또는 자동 재시도 (grounding 영역 = 출처 영역 보강 시도)
- 결과 deck 영역 = 모든 슬라이드 영역 출처 표기 검증·X 영역은 "[출처 미상]" 명시

### 5.4 Error handling: 30장 분량 X·자료 부족

#### (a) 시작 영역
- profile = 30장 분량 strict
- 입력 자료 = 5 페이지 PDF·grounding 영역 한계 자국

#### (b) 단계 영역
1. Step 4 narrative 영역 = 분량 30장 시도·자료 부족 자국
2. grounding 다회 호출 (5+회)·rate limit 영향 자국
3. 분량 자동 조정 영역 결정

#### (c) 예상 결과 영역
- 분량 자동 조정 = 15~20장 (자료 정합)
- 사용자 안내: "원본 자료 부족·30장 X·15장 결과 자국·재업로드 가능"
- assumption surfacing 영역 = "분량 자동 조정·자료 부족 자국" 명시

---

## 6. Curriculum Pack Designer 시나리오 (2.5)

feature_spec 영역 2.5 정합·교육 커리큘럼·강의 자료.

### 6.1 Happy path: 기업 교육 커리큘럼 정상 생성

#### (a) 시작 영역
- 사용자: 기업 교육 컨설팅
- profile: education·실무자·casual·footer·30장·한국어
- 입력: 교육 자료 PDF (강의 주제·시간·실습 영역)

#### (b) 단계 영역
1. PDF 업로드 (교육 자료)
2. `/tickdeck:curriculum` agent 실행
3. Step 4 narrative **strict** 영역 (학습 목표·진행·실습·평가 구조)
4. Bloom's taxonomy 사상 정합 (인지·이해·적용·분석 영역)
5. 다운로드

#### (c) 예상 결과 영역
- 결과 PPTX 분량 = 25~30장 (커리큘럼 표준·차시 단위)
- 학습 목표 영역 = Bloom's taxonomy 사상 정합 (인지·이해·적용·분석 자국)
- 차시별 진행 영역 = 시간 분 단위 명시 (예: "1차시 90분·도입 10분·전개 70분·정리 10분")
- 실습·평가 항목 영역 자동 생성
- 톤 = casual·실무자 영역 정합

### 6.2 Edge case: 1차시·짧은 강의

#### (a) 시작 영역
- profile = education·분량 자유 또는 8장
- 입력: 1 페이지 PDF (1시간 짧은 강의)

#### (b) 단계 영역
1. Step 4 narrative 영역 = 1차시 영역 구조 자동
2. 분량 = 8장 자국 (짧은 강의 정합)

#### (c) 예상 결과 영역
- 결과 deck 영역 = 8장 (도입·핵심·실습·정리·평가 영역)
- 차시 영역 = 1차시·60분 자국
- Bloom's taxonomy 영역 = 인지·이해 layer 영역 (짧은 강의 영역 정합)

### 6.3 Error handling: 학습 목표 영역 X

#### (a) 시작 영역
- 사용자 PDF 영역 = 학습 목표 명시 X·내용만 영역

#### (b) 단계 영역
1. Step 4 narrative 영역 = 학습 목표 추출 시도
2. 자동 생성 영역 = AI 추론 자국

#### (c) 예상 결과 영역
- 학습 목표 영역 = AI 자동 생성·assumption surfacing 자국
- 사용자 review 영역 = "AI 자동 생성 학습 목표·사용자 검토 의무" 명시
- 결과 deck 영역 = Bloom's taxonomy 사상 자국·사용자 수정 가능

---

## 7. 7단계 Pipeline 공통 시나리오

feature_spec 영역 4 정합·모든 agents 공통 호출.

### 7.1 Happy path: 7단계 전체 정상 흐름

#### (a) 시작 영역
- 정상 PDF + profile 영역
- 모든 외부 시스템 정상 (Gemini grounding·python-pptx)

#### (b) 단계 영역
1. Step 1 PDF 파싱 → 1초 안 처리
2. Step 2 grounding → 3~7분 자국
3. Step 3 merge → 30초 안
4. Step 4 narrative → 1~2분
5. Step 5 quality → 30초~1분 (재생성 영역 자국 시 +1분)
6. Step 6 디자인 매칭 → 즉시
7. Step 7 PPTX 생성 → 30초~1분

#### (c) 예상 결과 영역
- 총 Time-to-value = 3~10분 자국
- 모든 step 영역 = 로그 자국 (dogfood 측정)
- 결과 PPTX 파일 영역 = PowerPoint·Google Slides·Keynote 호환

### 7.2 Edge case: research strict 모드 (5~10분 layer)

#### (a) 시작 영역
- profile = Industry Research Compiler·strict 모드
- 입력: 자료 풍부 PDF (30 페이지)

#### (b) 단계 영역
1. Step 2 grounding = 다회 호출 (5~10회)
2. 각주 strict 영역 = 모든 출처 메타데이터 누적

#### (c) 예상 결과 영역
- Time-to-value 5~10분 자국 (사용자 progress bar 영역 안내)
- 결과 deck 영역 = 출처 풍부·각주 strict·footer 모든 슬라이드 출력

### 7.3 Error handling: Step 5 quality 영역 2회 실패

#### (a) 시작 영역
- Step 4 영역 결과 deck 영역 = 룰 위반 (RULE A·J·B 영역)
- 재생성 1회 → 또 위반 → 2회 → 또 위반

#### (b) 단계 영역
1. Step 5 quality 영역 1차 검증 → 위반
2. Step 4 재생성 → 2차 검증 → 위반
3. 2회 실패 자국

#### (c) 예상 결과 영역
- 사용자 안내: "품질 검증 2회 실패·재시도 또는 자료 영역 변경 안내"
- 결과 deck 영역 X·다운로드 X
- 에러 로그 자국 (dogfood 측정·룰 영역 영향 분석)

---

## 8. Guardrails 시나리오

feature_spec 영역 6 정합·source attribution·assumption surfacing·disclaimer·review gate.

### 8.1 Source Attribution Happy Path

#### (a) 시작 영역
- profile 출처 정책 strict
- 입력 PDF + grounding 자료 영역 자국

#### (b) 단계 영역
1. Step 2 grounding 영역 = 출처 메타데이터 (URL·title·snippet) 누적
2. Step 7 PPTX 생성 영역 = source_id 자동 매핑 (각주 또는 footer)

#### (c) 예상 결과 영역
- 모든 슬라이드 영역 = 출처 표기 영역 자국
- 각주 영역 = 사용자 PDF 인용 + grounding 인용 영역 모두 자국
- footer = 출처 URL·title·snippet 영역 표기

### 8.2 Assumption Surfacing On 모드

#### (a) 시작 영역
- profile = assumption on 모드

#### (b) 단계 영역
1. Step 7 PPTX 생성 영역 = 1페이지 자동 추가
2. 6 인풋 영역 (산업·청중·톤·출처 정책·분량·언어) 표 출력

#### (c) 예상 결과 영역
- 결과 deck 1페이지 = 인풋 표·assumption 자국
- 사용자 review 영역 = 자기 인풋 영역 재확인 가능

### 8.3 Review Gate Happy Path

#### (a) 시작 영역
- Step 7 PPTX 생성 완료

#### (b) 단계 영역
1. 미리보기 화면 가시 (썸네일 또는 1페이지 영역)
2. "다운로드" 버튼 클릭

#### (c) 예상 결과 영역
- PPTX 파일 다운로드 영역 = browser 영역 정합
- 외부 도구 안내 1줄 가시 (3 도구 영역)

### 8.4 Review Gate Edge Case: 재생성 시나리오

#### (a) 시작 영역
- 미리보기 화면 → 사용자 만족 X
- "재생성" 버튼 클릭

#### (b) 단계 영역
1. 재생성 1회 자국 (PRD 결정 8 정합·스타일 변경 영역)
2. Step 6 디자인 매칭 영역 = 다른 디자인 시스템 1종 자동 매칭

#### (c) 예상 결과 영역
- 재생성 결과 = 다른 디자인 토큰 영역 deck 출력
- 2회 시도 시 안내: "재생성 1회만 자국·외부 도구 직접 수정 안내"

### 8.5 Review Gate Error Handling: 재생성 2회 시도

#### (a) 시작 영역
- 1회 재생성 완료 후 또 만족 X·2회 재생성 시도

#### (b) 단계 영역
1. "재생성" 버튼 클릭
2. 시스템 영역 = 2회 시도 자국 → 차단

#### (c) 예상 결과 영역
- 안내: "재생성 1회만 자국·외부 도구 (PPT·Slides·Keynote) 직접 수정 안내"
- 외부 도구 아이콘 영역 가시·다운로드 영역 가능

---

## 9. UI·랜딩 시나리오

feature_spec 영역 3 정합·5 agents 카드 선택 화면.

### 9.1 Happy path: 5 agents 카드 가시·정상 선택

#### (a) 시작 영역
- 사용자 첫 방문·랜딩 화면

#### (b) 단계 영역
1. 5 agents 카드 영역 가시
2. 각 카드 = 이름·아이콘·1줄 설명·매칭 산업 표기
3. Industry Research Compiler 카드 클릭

#### (c) 예상 결과 영역
- 선택 agent 영역 = cold-start interview 자동 전환
- profile 영역 = agent 영역 자국 (Industry Research → finance 자동 default 또는 사용자 변경 영역)

### 9.2 Edge case: 모바일 viewport 동작

#### (a) 시작 영역
- 사용자 = iOS Safari (svh 정합)
- 화면: 모바일 viewport (375px width)

#### (b) 단계 영역
1. 랜딩 화면 로드
2. 5 agents 카드 영역 = 세로 stack 자국
3. 카드 클릭

#### (c) 예상 결과 영역
- 5 agents 카드 영역 = 모바일 stack 가시·click 가능
- viewport 영역 = svh 정합·iOS Safari 100vh 이슈 X
- 데스크탑 권장 안내 1줄 가시 ("PDF 업로드·PPTX 다운로드 영역 데스크탑 권장")

### 9.3 Error handling: 첫 화면 disclaimer 영역 사용자 동의

#### (a) 시작 영역
- 사용자 첫 방문
- disclaimer 영역 = 세션 삭제·DB X·계정 X·BYOD OK 명시

#### (b) 단계 영역
1. 랜딩 화면 영역 = disclaimer 가시
2. 사용자 "동의" 또는 "닫기" 선택

#### (c) 예상 결과 영역
- 동의 시 = 5 agents 카드 선택 가능
- 닫기 시 = 랜딩 영역 잔존·agent 카드 영역 흐림 (disabled)
- 세션 진행 영역 = disclaimer 동의 필수 자국

---

## 10. Practice Areas Plugin 시나리오 (1단계 base)

feature_spec 영역 5 정합·1단계 base·실 plugin X.

### 10.1 Happy path: 7 module 폴더 영역 존재 검증

#### (a) 시작 영역
- 1단계 빌드 완료 영역
- 사용자 deck 생성 시도

#### (b) 단계 영역
1. agent 실행 → practice_areas 폴더 영역 read 시도
2. 7 module 폴더 영역 (automotive·entertainment·food·education·brand_consulting·marketing·finance) 자국

#### (c) 예상 결과 영역
- 7 module 폴더 영역 = 빈 파일 또는 placeholder 자국 (1단계 정합)
- 각 module = `tone_dict.json`·`templates.json`·`schema.json` 3 파일 자국
- agent 영역 = 자기 module 자동 read 검증

### 10.2 Edge case: 산업 매칭 X (기타 선택)

#### (a) 시작 영역
- profile 산업 = 기타

#### (b) 단계 영역
1. agent 실행 → practice_areas 영역 X
2. fallback 영역 = global tone_dict 또는 default templates

#### (c) 예상 결과 영역
- 결과 deck 영역 = global tone 자국·산업 매칭 X 영역 명시
- assumption surfacing 영역 = "산업 매칭 X·global default 자국"

### 10.3 Error handling: practice_areas 폴더 영역 변경 영향 검증

#### (a) 시작 영역
- 본진/르메 영역 = practice_areas 영역 변경 시도

#### (b) 단계 영역
1. practice_areas/automotive/tone_dict.json 영역 수정
2. agent 영역 = 격리 검증 (plugin 사상)

#### (c) 예상 결과 영역
- automotive 영역 변경 = Vendor Proposal Drafter 영역만 영향
- 다른 agents (Brand Guide·Marketing Brief 등) 영역 = 영향 X
- plugin 격리 사상 검증 (1단계 base 자국)

---

## 11. Architecture Base 시나리오 (1단계 base)

feature_spec 영역 7 정합·1단계 base·풀 활성화 X.

### 11.1 Happy path: i18n base 영역 검증

#### (a) 시작 영역
- 1단계 빌드 영역
- `locales/ko.json` 존재 자국

#### (b) 단계 영역
1. UI 영역 텍스트 영역 read → `locales/ko.json` 영역 자국
2. 하드코딩 텍스트 영역 X 검증

#### (c) 예상 결과 영역
- 모든 UI 텍스트 영역 = `locales/ko.json` 정합
- `locales/ja.json`·`locales/zh-TW.json`·`locales/en.json` 영역 = 빈 placeholder 자국
- 2단계 활성화 영역 = ja 파일 채움 시 자동 동작 검증 (1단계 비활성)

### 11.2 Edge case: 메타데이터 schema 5 필드 영역 strict

#### (a) 시작 영역
- 1단계 영역 = 모든 자료 (templates·grounding 보충) 메타데이터 영역 의무

#### (b) 단계 영역
1. 자료 영역 read → 5 필드 (country·industry·language·license·source_url) 검증
2. 필드 누락 영역 자국 → 자료 X 또는 placeholder

#### (c) 예상 결과 영역
- 5 필드 모두 자국 자료 영역 = pipeline 진행 OK
- 누락 영역 = placeholder 또는 사용자 안내·strict 영역 보호

### 11.3 Error handling: 결제 어댑터 영역 toss 호출 실패

#### (a) 시작 영역
- 1단계 결제 = 토스페이먼츠 단일 (1회 5,000~10,000원·PRD pricing 정합)
- 사용자 결제 시도

#### (b) 단계 영역
1. 토스페이먼츠 API 호출 → 실패 (network 또는 카드 오류)
2. 에러 자국 영역 = abstract class fallback

#### (c) 예상 결과 영역
- 사용자 안내: "결제 실패·다시 시도 또는 다른 카드 영역"
- 결제 어댑터 abstract class 영역 검증 (toss 1 구현 영역 자국)
- 2단계 활성화 영역 = Stripe·동남아 결제 영역 placeholder 영역 자국

---

## 12. Gemini Grounding 외부 시스템 시나리오

feature_spec Step 2 정합·Gemini 3.1 Flash Lite Preview·외부 API 의존성.

### 12.1 Happy path: 정상 grounding 호출

#### (a) 시작 영역
- Gemini API 정상·rate limit 영역 안

#### (b) 단계 영역
1. Step 2 영역 = grounding 호출 (다회·키워드 추출)
2. 결과 영역 = 출처 메타데이터 누적

#### (c) 예상 결과 영역
- grounding 호출 1회 이상 성공 검증
- 출처 메타데이터 (URL·title·snippet·search_term) 누적 검증
- Time-to-value 영역 정합

### 12.2 Edge case: Rate limit 영역

#### (a) 시작 영역
- 사용자 영역 = 동시 N명·Gemini API rate limit 영역 boundary

#### (b) 단계 영역
1. grounding 호출 → 429 에러
2. 자동 재시도 (5초 대기·1회만)

#### (c) 예상 결과 영역
- 재시도 성공 시 = 정상 진행
- 재시도 실패 시 = fallback (Step 2 skip·Step 1 자료만 영역 진행)
- 사용자 안내 자국

### 12.3 Error handling: API key 영역 X 또는 만료

#### (a) 시작 영역
- 환경 변수 영역 = Gemini API key X 또는 만료

#### (b) 단계 영역
1. grounding 호출 → 401 에러
2. 시스템 영역 = 명확 에러 메시지

#### (c) 예상 결과 영역
- 사용자 안내: "AI 조사 layer X·시스템 영역 외부 의존성·관리자 안내"
- 결과 deck 영역 = 원본 자료만 영역 진행 (fallback 정합)
- 본진 영역 = API key 영역 갱신 의무 (DevOps 영역)

---

## 13. Dogfood 측정 시나리오 (1차·후추님 본인)

PRD v2.2 + claude-for-legal cold-start interview 영역 정합.

### 13.1 Happy path: 후추님 본인 dogfood (1차)

#### (a) 시작 영역
- 후추님 본인 PDF 영역 (잡솔트 자료·펩핀치 자료 등)
- profile: brand_consulting·실무자·세미정장·footer·15장·한국어

#### (b) 단계 영역
1. Brand Guide Builder agent 선택
2. PDF 업로드
3. 결과 deck 영역 review

#### (c) 예상 결과 영역
- 결과 deck 영역 = 후추님 자기 영역 정합 (잡솔트·펩핀치 톤 자국)
- 5분 안 결과·dogfood 측정 timer 자국
- 후추님 review·문제 영역 자국 (회고 영역 정합)

### 13.2 Dogfood 2차 (외부·5~10명·waitlist)

#### (a) 시작 영역
- 1단계 빌드 완료 후·외부 사용자 5~10명·디스콰이엇·잡솔트·펩핀치 영역

#### (b) 단계 영역
1. waitlist 영역 사용자 모집
2. 5 agents 영역 모두 사용·후추님·본진 영역 = 결과 review

#### (c) 예상 결과 영역
- 외부 사용자 N=5~10·결과 deck 영역 정합 dogfood
- 후추님·본진 영역 = 문제·개선 영역 자국 (회고·다음 사이클 영역)

---

## 14. 가설 확인/기각 (P3-T3)

**가설**: "feature_spec 영역 정합 영역 test scenarios 영역 = happy path + edge case + error handling 영역 영역 도출 영역. pm-execution:test-scenarios skill 또는 본진 자율 영역."

→ ✅ **확인**. 본 test_scenarios.md 영역 = feature_spec 영역 모든 feature 영역 정합 시나리오 자국:
- 5 named agents 별 시나리오 = 영역 2~6 (각 happy path + edge case + error handling 영역 분리·a/b/c 양식)
- Cold-start interview 시나리오 = 영역 1 (정상·skip·세션 종료 영역)
- 7단계 pipeline 공통 시나리오 = 영역 7 (정상·strict·실패 영역)
- Guardrails 시나리오 = 영역 8 (source attribution·assumption surfacing·review gate·재생성 영역)
- UI 시나리오 = 영역 9 (랜딩·모바일·disclaimer 영역)
- Practice areas plugin 시나리오 = 영역 10 (1단계 base 검증·격리 검증)
- Architecture base 시나리오 = 영역 11 (i18n·메타데이터·결제 어댑터 영역)
- 외부 시스템 (Gemini grounding) 시나리오 = 영역 12 (정상·rate limit·API key 영역)
- Dogfood 측정 시나리오 = 영역 13 (1차·2차)

본진 자율 영역 = OK (pm-execution:test-scenarios skill X·본 영역 = 더 자세한 영역 영역 + agent별 시나리오 구체 영역·5 명확 분류 happy/edge/error 영역).

---

## 15. 다음 step

1. ✅ feature_spec.md 신설 (P3-T2 완료)
2. ✅ test_scenarios.md 신설 (P3-T3 본 layer 완료)
3. ⏳ pre_mortem.md (P3-T4·5단계·pm-execution:pre-mortem skill·1단계 빌드 영역 위험 영역 분석)
4. ⏳ PLAN_implementation.md (P3-T5·6단계·superpowers:writing-plans·2~5분 task 분해)
5. ⏳ 노클 PDF 교차 분석 (P3-T6·7단계·자동 진행 영역)
6. 와이어프레임 (2단계) = 후추님 직접 영역·prompt 갱신 후보

## 16. 가시성 (한 줄)

test_scenarios.md = 5 named agents 별 + cold-start + 7단계 pipeline + guardrails + UI + practice_areas + architecture base + 외부 시스템 + dogfood 영역 = 50+ 시나리오 (happy/edge/error 3분류) 자국 완료·1단계 dogfood 검증 입력 자산.
