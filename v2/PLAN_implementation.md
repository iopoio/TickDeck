# TickDeck v2 — 실 빌드 PLAN (writing-plans·P3-T5)

> 작성: 2026-05-15 04:01 KST (Ralph P3-T5)
> 기준: `PRD_v2.md` v2.1·v2.2 + `feature_spec.md` + `test_scenarios.md` + `pre_mortem.md` 정합
> 영역: PLAN_5-13 7단계 중 6단계 (writing-plans·superpowers:writing-plans 사상 자율 변형)
> 양식: 각 task = (a) 영역·산출물 / (b) 의존 task / (c) 추정 시간 / (d) done 조건
> 단위: 30분~3시간 (대부분 1~2시간·2~5분 단위는 코드 sub-task 영역)
> 1단계 MVP 마감 추정: **6/9 EOD (Week 4 종료)** — Streamlit 첫 dogfood 가능 layer

---

## 0. 빌드 사상

- repo: 후추님 결정 영역 (별도 repo `tickdeck-v2` 신설 또는 기존 `Automation/TickDeck` 안 `v2/code/` 영역). 본 plan = `tickdeck_v2/` 영역 base
- 언어: Python 3.11+ · Streamlit 1.30+ · python-pptx · pypdf · google-generativeai (Gemini grounding)
- 모델: Gemini 3.1 Flash Lite Preview (research·narrative 영역) + Anthropic Claude (선택·후추님 API key)
- 빌드 모드: 본진 클차장 자율 빌드 (1파일 단순 영역) + 제대리 핸드오프 (2파일+·복잡 영역) 분리
- 의존: 후추님 결재 영역 (외부 결제·API key·repo 생성) = blocked task 자국

---

## Phase 0 — 사전 준비 (5/15~5/19·Week 1 갱신)

5/15 현재 시점 layer. 후추님 결재 영역 (T01) 외 본진 자율 빌드.

### T01. Repo 결정·v2 폴더 base 신설
- (a) 영역: 후추님 결재·`tickdeck-v2` 별도 repo OR `Automation/TickDeck/v2/code/` 영역 결정. 결정 후 `tickdeck_v2/` 폴더 신설 + `pyproject.toml` (또는 `requirements.txt`) base
- (b) 의존: 없음
- (c) 시간: 결재 영역 (후추님 1분) + 신설 30분
- (d) done: 폴더 신설 + 빈 `app.py`·`README.md`·`.gitignore` 영역 자국. git push 1회.
- **STATUS: blocked** (후추님 결재 영역)

### T02. locales/ko.json 신설 (UI 텍스트 변수화 base)
- (a) 영역: `tickdeck_v2/locales/ko.json` 신설. 모든 UI 텍스트 (랜딩·interview·파이프라인·다운로드) 변수화. 하드코딩 X 검증.
- (b) 의존: T01
- (c) 시간: 1시간 (텍스트 자국 영역 + 빈 placeholder ja.json·zh-TW.json·en.json 3 파일 신설)
- (d) done: `locales/ko.json` = 50+ key 자국. `locales/ja.json`·`locales/zh-TW.json`·`locales/en.json` 빈 파일 (`{}`) 신설.

### T03. profile/ 폴더 + tickdeck_profile.md schema
- (a) 영역: `tickdeck_v2/profile/` 폴더 신설 + `tickdeck_profile.md.template` (6 인풋 = 산업·청중·톤·출처 정책·분량·언어) + `profile_loader.py` (세션 임시 저장·종료 자동 삭제·cleanup 룰)
- (b) 의존: T01
- (c) 시간: 1.5시간
- (d) done: profile loader = 세션 단위 read·write·자동 삭제 동작 검증 (간단 pytest 1개 통과)

### T04. guardrails/ 폴더 base
- (a) 영역: `tickdeck_v2/guardrails/` 폴더 + 4 영역 (source_attribution.py·assumption_surfacing.py·disclaimer.py·review_gate.py) placeholder 파일. 각 파일 = 인터페이스 정의만 (실 구현 X)
- (b) 의존: T01
- (c) 시간: 1시간
- (d) done: 4 파일 신설·각 파일 = pydoc·인터페이스 함수 sketch.

---

## Phase 1 — Architecture Base (5/15~5/26·Week 1~2)

practice_areas plugin 사상 base + 결제 어댑터 + 메타데이터 schema. premature globalization 회피·1단계 base만.

### T05. practice_areas/ 7 module 폴더 신설
- (a) 영역: `tickdeck_v2/practice_areas/` 안 7 module (automotive·entertainment·food·education·brand_consulting·marketing·finance) 폴더 신설. 각 module = `__init__.py` 빈 파일.
- (b) 의존: T01
- (c) 시간: 30분
- (d) done: 7 module 폴더 신설 검증·`ls practice_areas/` = 7 영역.

### T06. practice_areas 각 module placeholder 파일 3종
- (a) 영역: 각 7 module 안 `tone_dict.json`·`templates.json`·`schema.json` placeholder 신설. 각 파일 = 빈 `{}` 또는 minimal schema. tone_dict.json = 산업별 5~10 용어 placeholder.
- (b) 의존: T05
- (c) 시간: 2시간 (7 × 3 = 21 파일·각 5~10분)
- (d) done: 7 × 3 = 21 파일 신설·각 module 5 named agents 자동 read 가능 영역 검증.

### T07. payment/ 어댑터 abstract class
- (a) 영역: `tickdeck_v2/payment/` 신설 + `base.py` (PaymentAdapter abstract class·`charge_once`·`refund` 인터페이스) + `__init__.py`
- (b) 의존: T01
- (c) 시간: 1시간
- (d) done: abstract class 정의·하위 어댑터 (`toss.py`·`stripe.py`) 인터페이스 구현 강제 검증.

### T08. payment/toss.py 어댑터 구현 (1단계·placeholder)
- (a) 영역: 토스페이먼츠 1회 결제 어댑터·테스트 모드 구현. 실 결제 X·sandbox key. 결제 성공 → `payment_log.jsonl` 영역 자국.
- (b) 의존: T07 + 후추님 결재 (토스 sandbox key)
- (c) 시간: 3시간 (토스 문서 read·테스트 모드 검증)
- (d) done: sandbox 1회 결제 성공 (실 호출 1회 + 응답 자국). 본 task = 6주 검증 Week 5 영역·1단계 MVP 영역 X (placeholder OK).
- **참고**: 1단계 MVP 영역 = T08 skip OK (waitlist만 영역). Week 5 진입 시 시작.

### T09. payment/stripe.py 빈 placeholder
- (a) 영역: `payment/stripe.py` 신설·`PaymentAdapter` 상속·모든 메서드 `raise NotImplementedError("2단계 활성화")`
- (b) 의존: T07
- (c) 시간: 15분
- (d) done: 파일 신설·import 검증.

### T10. 메타데이터 schema strict 정의
- (a) 영역: `tickdeck_v2/shared/metadata_schema.py` (또는 JSON Schema)·5 필드 (country·industry·language·license·source_url) strict. 모든 자료 (templates·보충 자료) = 5 필드 의무.
- (b) 의존: T01
- (c) 시간: 1시간
- (d) done: schema 정의·pydantic 모델 1개·검증 함수 1개·pytest 1개 통과.

---

## Phase 2 — 7단계 Pipeline 빌드 (5/20~6/9·Week 2~4)

v1 자산 재활용 영역 + 신규 영역. agent별 strict 정도 차이 자국.

### T11. pipeline/parse.py — PDF 파싱
- (a) 영역: `tickdeck_v2/pipeline/parse.py` 신설. pypdf 영역 텍스트 추출·메타데이터 (페이지 수·제목·작성일) 영역. 스캔 PDF 자국 시 명확 에러. v1 자산 재활용.
- (b) 의존: T01
- (c) 시간: 1.5시간 (v1 자산 read·이식)
- (d) done: 텍스트 PDF 1개 dogfood 100% 추출 성공. 스캔 PDF 1개 명확 에러 메시지. 처리 1초 안.

### T12. pipeline/research.py — AI 조사 강화 (Gemini grounding)
- (a) 영역: Gemini grounding 호출·키워드 추출·다회 검색·출처 메타데이터 누적. agent별 strict 정도 차이 (Industry Research = maximum·Vendor Proposal = light) 영역 파라미터. **본진 자율 빌드 영역 X (2파일+·제대리 핸드오프 영역)**.
- (b) 의존: T11 + T10 (schema) + 후추님 결재 (Gemini API key)
- (c) 시간: 3시간 (Gemini docs read·grounding 검증·strict 모드 분리·dogfood)
- (d) done: grounding 호출 1회 이상 성공 (실 API 응답 자국). 출처 메타데이터 5 필드 누적. agent별 strict 차이 검증 (Industry Research vs Vendor Proposal sample 비교).

### T13. pipeline/merge.py — 자료 통합
- (a) 영역: 원본 PDF + 보충 자료 통합·중복 거름·source_id 자국·원본 우선·복수 소스 교차 옵션 (strict 모드)
- (b) 의존: T11 + T12
- (c) 시간: 2시간
- (d) done: 통합 자료 = 섹션별 구분·source_id 모든 항목 자국. 중복 거름 dogfood 검증.

### T14. pipeline/narrative.py — 3에이전트 + templates 매칭
- (a) 영역: v1 3에이전트 (Architect·Narrator·Editor) 영역 재활용 + templates.json 패턴 매칭 + agent별 templates 분류 (Vendor Proposal = 137개·Industry Research = ARK+KPMG·etc) read. **본진 자율 빌드 X·제대리 핸드오프**.
- (b) 의존: T13 + T30 (templates 자산·일부 영역 사용 가능)
- (c) 시간: 4시간
- (d) done: SlideType[] 모든 슬라이드 = 제목·내용·source_id 영역 채움. templates 매칭 ≥ 80% dogfood. profile 분량 ±2장 자국.

### T15. pipeline/quality.py — 품질 검증
- (a) 영역: v1 quality.py 자산 재활용 (RULE A·J·B)·재생성 최대 2회·2회 실패 시 사용자 안내
- (b) 의존: T14
- (c) 시간: 1.5시간 (v1 자산 이식·테스트)
- (d) done: RULE A·J·B 모두 적용 검증. 재생성 카운트 자국. 2회 실패 안내 영역 가시.

### T16. pipeline/design.py — 6종 디자인 시스템 자동 매칭
- (a) 영역: 6종 (Minimal White·Soft Coral·Dark Mode·Deep Blue Pro·비즈니스 정장·콘텐츠 컬러풀) 디자인 토큰 정의·톤 매칭 알고리즘·agent별 default 매칭·1회 변경 옵션
- (b) 의존: T15 + DESIGN.md v0.1 갱신 (Phase 0 영역 X·후추님 영역)
- (c) 시간: 3시간 (디자인 토큰 6종 정의·매칭 로직)
- (d) done: 6종 토큰 정의 완비. 톤 매칭 검증 (정장 → Deep Blue Pro 등). agent별 default 검증. 1회 변경 다른 5종 가시.

### T17. pipeline/pptx.py — PPTX 생성
- (a) 영역: v1 shared/pptx_builder.py 자산 재활용 + Step 6 디자인 토큰 + guardrails 영역 적용 (source attribution footer·assumption surfacing 1페이지·disclaimer 첫 페이지)
- (b) 의존: T16 + T26·T27·T28 (guardrails 구현)
- (c) 시간: 3시간 (v1 자산 이식·guardrails 통합·dogfood)
- (d) done: PPTX 파일 PowerPoint·Google Slides·Keynote 3 도구 dogfood 검증. source attribution footer 모든 슬라이드. disclaimer 1페이지. assumption 옵션 동작. 파일 크기 < 10MB.

---

## Phase 3 — 5 Named Agents 빌드 (5/27~6/9·Week 3~4)

각 agent = single file·workflow per agent. pipeline 호출 + agent별 strict 파라미터.

### T18. named_agents/vendor_proposal.py
- (a) 영역: Vendor Proposal Drafter·`/tickdeck:vendor-proposal` command·산업 매칭 (automotive·entertainment·food)·research light·templates B2B 137개 read
- (b) 의존: T11~T17 (pipeline 전체)
- (c) 시간: 2시간
- (d) done: 분량 8~15장. 한국 비즈니스 용어·존댓말 검증 (sample 5종 dogfood). source attribution footer 자동.

### T19. named_agents/brand_guide.py
- (a) 영역: Brand Guide Builder·`/tickdeck:brand-guide`·brand_consulting 매칭·design 6번 strict·voice & tone 정합
- (b) 의존: T11~T17
- (c) 시간: 2시간
- (d) done: 분량 15~30장. color palette·typography 자동 추출. voice & tone profile 정합 검증.

### T20. named_agents/marketing_brief.py
- (a) 영역: Marketing Brief Creator·`/tickdeck:marketing-brief`·marketing 매칭·research strict (시장·경쟁사·타깃)·KPI 정량 지표 strict
- (b) 의존: T11~T17
- (c) 시간: 2시간
- (d) done: 분량 8~15장. 타깃 segmentation 자동. KPI 정량 명시. 경쟁사 3~5사 비교 표.

### T21. named_agents/industry_research.py ⭐ (차별 layer 2번)
- (a) 영역: Industry Research Compiler·`/tickdeck:industry-research`·finance 매칭·research **maximum strict**·각주 strict·시장 규모 출처 명시·ARK + KPMG·BCG·Deloitte templates
- (b) 의존: T11~T17 + T31 (ARK patterns) + T32 (KPMG/BCG patterns)
- (c) 시간: 3시간 (가장 strict·dogfood 영역 ↑)
- (d) done: 분량 15~30장. 각주 strict 모든 인용 출처. 시장 규모 출처 명시 (정부·KPMG·BCG). 경쟁 구도 3~7사 차트. 컨설팅 톤 dogfood 검증. Time-to-value 5~10분.

### T22. named_agents/curriculum.py
- (a) 영역: Curriculum Pack Designer·`/tickdeck:curriculum`·education 매칭·narrative 4번 strict (Bloom's taxonomy)·차시 시간 분 단위·실습·평가 항목
- (b) 의존: T11~T17
- (c) 시간: 2시간
- (d) done: 분량 15~30장. 학습 목표 Bloom 정합. 차시 시간 명시. 실습·평가 자동 생성. 톤 = 세미정장 또는 casual.

---

## Phase 4 — Streamlit UI (6/3~6/9·Week 4)

랜딩·cold-start interview·파이프라인 시각화·review gate.

### T23. app.py 랜딩 페이지 (5 agents 카드)
- (a) 영역: Streamlit `app.py` 랜딩·5 agents 카드 (이름·아이콘·1줄 설명·매칭 산업)·click → agent별 onboarding·disclaimer 첫 화면 (3 영역 명시)·모바일 viewport svh·데스크탑 권장 안내
- (b) 의존: T01 + T02 (locales/ko.json)
- (c) 시간: 3시간
- (d) done: 5 agents 카드 가시·click 동작. disclaimer 3 영역 명시 (세션 삭제·DB X·계정 X). 모바일 viewport 검증 (iOS Safari).

### T24. cold-start interview UI (5분)
- (a) 영역: 6 인풋 (산업 7카테고리·청중 4종·톤 3종·출처 정책 3종·분량 4종·언어 3종) Streamlit form·skip OK·default 자동 매칭·결과 profile/tickdeck_profile.md 영역 저장
- (b) 의존: T03 (profile loader) + T23
- (c) 시간: 2.5시간
- (d) done: 5분 안 완료 dogfood (1인 사용자 측정). 6 인풋 다 선택 가능·skip OK. 다음 agent 자동 read. 세션 종료 자동 삭제 검증.

### T25. 파이프라인 진행 시각화
- (a) 영역: 7단계 진행 progress bar·예상 시간 3~10분 strict·각 단계 status (parse·research·merge·narrative·quality·design·pptx)
- (b) 의존: T23 + T11~T17 (pipeline)
- (c) 시간: 2시간
- (d) done: 7단계 progress 가시·각 단계 시간 자국·실패 시 명확 에러 메시지·재시도 가능.

### T26. review gate · 다운로드 화면
- (a) 영역: PPTX 미리보기 (썸네일 또는 1페이지)·"다운로드"·"재생성" 버튼·재생성 1회만·외부 도구 안내 1줄 + 3 아이콘 (PPT·Slides·Keynote)
- (b) 의존: T17 (pipeline pptx) + T29 (review gate guardrail)
- (c) 시간: 2시간
- (d) done: 미리보기 가시·다운로드/재생성 동작·재생성 2회 시도 시 안내·외부 도구 안내 가시.

---

## Phase 5 — Guardrails 구현 (6/3~6/9·Week 4·T17·T26 의존)

claude-for-legal guardrail 사상 적용. 4 영역.

### T27. guardrails/source_attribution.py 구현
- (a) 영역: T12 research 결과 메타데이터 (URL·title·source_id) 누적 → T17 pptx 영역 footer 또는 각주 자동 매핑·출처 정책 strict 모드 (각주·footer·자유)
- (b) 의존: T12 + T17
- (c) 시간: 2시간
- (d) done: 모든 보충 자료 source_id 누적. strict 모드 = 모든 슬라이드 각주. profile 출처 정책 정합.

### T28. guardrails/assumption_surfacing.py 구현
- (a) 영역: T17 pptx 1페이지 = 6 인풋 (산업·청중·톤·출처 정책·분량·언어) 표 자동 추가·profile on/off 옵션
- (b) 의존: T03 (profile) + T17
- (c) 시간: 1시간
- (d) done: assumption 1페이지 자동 생성 (on 모드). 6 인풋 모두 표기. off 모드 = 1페이지 생략.

### T29. guardrails/disclaimer.py 구현
- (a) 영역: 첫 화면 disclaimer (랜딩·T23 영역) + PPTX 첫 페이지 disclaimer 자동 추가·다운로드 전 review gate 가시
- (b) 의존: T17 + T23
- (c) 시간: 1시간
- (d) done: 첫 화면·PPTX 첫 페이지·review gate 3 영역 disclaimer 가시 검증.

### T30. guardrails/review_gate.py 구현
- (a) 영역: 다운로드 전 미리보기 화면·재생성 1회 제한·2회 시도 시 안내
- (b) 의존: T17 + T26
- (c) 시간: 1시간
- (d) done: 미리보기 가시. 재생성 카운트 1 limit. 2회 시도 명확 안내.

---

## Phase 6 — Templates 자산 빌드 (5/20~5/26·Week 2)

후추님 137개 + ARK + KPMG/BCG/Deloitte patterns 추출. **본진 자율 영역 X·후추님 영역 + 제대리 교차 분석 영역**.

### T31. 후추님 137개 templates.json 추출 (Vendor Proposal)
- (a) 영역: 후추님 137개 B2B 제안서 영역 patterns 추출·`practice_areas/automotive/templates.json` + `entertainment/templates.json` + `food/templates.json` 분류 누적
- (b) 의존: T06 (placeholder 영역) + 후추님 자료 송부 (노클 push)
- (c) 시간: 4시간 (후추님 + 제대리 교차 분석·본진 자율 1차)
- (d) done: 137개 patterns 추출·5+ slide 패턴 자국·산업별 분류·메타데이터 5 필드 strict.

### T32. ARK 자료 patterns 추출 (Industry Research)
- (a) 영역: `/Users/hwa/Projects/Automation/investlab/research/ARK_reports/` 7 파일·32MB read·Big Ideas 2024·2025·2026-Q1 patterns 추출·`practice_areas/finance/templates.json` 누적
- (b) 의존: T06 + T31
- (c) 시간: 3시간 (본진 + 제대리 교차)
- (d) done: ARK 디스럽티브 narrative 표준·데이터·차트 패턴 추출. 메타데이터 strict.

### T33. KPMG/BCG/Deloitte 한국 보고서 patterns 추출
- (a) 영역: 노클 다운로드 자료 (KPMG·BCG·Deloitte 공개 한국 보고서) patterns 추출·`finance/templates.json` 누적
- (b) 의존: 노클 selection 자료 송부 (Phase 3-T6 노클 영역)
- (c) 시간: 4시간
- (d) done: 5+ 패턴 추출. 메타데이터 strict. industry_research agent dogfood 입력 가능.

---

## Phase 7 — 결제·Distribution (5/27~6/16·Week 3~5)

waitlist 우선·결제 Week 5 영역.

### T34. waitlist 페이지 + DB
- (a) 영역: Streamlit landing 영역 안 waitlist 이메일 수집 form·SQLite 또는 Supabase 영역·이메일 + 산업 + 청중 6 필드 영역
- (b) 의존: T23
- (c) 시간: 2시간
- (d) done: 이메일 저장 검증·관리자 영역 1개 (간단 list view)·privacy 정책 1줄.

### T35. 토스페이먼츠 1회 5천원 결제 구현 (Week 5)
- (a) 영역: T08 sandbox 영역 → production key 영역·결제 1회 5,000~10,000원·결제 성공 시 PPTX 다운로드 unlock·실패 시 명확 안내
- (b) 의존: T08 + 후추님 결재 (토스 production key·사업자 등록증)
- (c) 시간: 4시간 (production 영역·결제 안전 검증)
- (d) done: 실 결제 1회 dogfood 성공 (sandbox·후추님 시연). 환불 영역 1회 검증. 1단계 MVP 영역 = waitlist만·결제 Week 5 진입 영역.
- **STATUS: blocked** (후추님 결재 영역·시즌드 사업자 영역)

### T36. Distribution 채널 시동
- (a) 영역: 펩핀치·잡솔트·X 한국 영역 waitlist 안내 + 디스콰이엇 + 스타트업 슬랙 + 한국 marketing 채널 추가·waitlist 30명 모집 target
- (b) 의존: T34 + 후추님 (X 글·디스콰이엇 글)
- (c) 시간: 후추님 영역 (본진 = 글 초안만)
- (d) done: 글 초안 3종 (X·디스콰이엇·슬랙) 후추님 영역. waitlist 30명 모집 Week 6 측정.
- **STATUS: blocked** (후추님 영역)

---

## Phase 8 — Dogfood + 검증 (6/17~6/23·Week 6)

GO/STOP 결정 영역.

### T37. 5 named agents 각 1개 dogfood
- (a) 영역: 후추님 영역 5 named agents 모두 영역 1개씩 deck 생성·결과 검증 (sample 5종)·waitlist 사용자 5명 시연 받기
- (b) 의존: T18~T22 + T35 (또는 무결제 모드)
- (c) 시간: 4시간 (5 agents × 30~40분)
- (d) done: 5 deck 결과 자국·acceptance criteria 모두 통과·waitlist 5명 NPS 측정.

### T38. GO/STOP 조건 측정
- (a) 영역: waitlist → 결제 전환 30%+·재방문 의향 70%+·NPS 10x breakthrough·Distribution 채널 검증
- (b) 의존: T34·T35·T36·T37
- (c) 시간: 2시간 (측정·분석·후추님 보고)
- (d) done: 4 조건 측정 자국. GO 또는 STOP 결정 자국 (`Think/sessions/2026-06-23_TickDeck_v2_GO_STOP.md`).
- **STATUS: blocked** (후추님 결재 영역)

---

## Phase 9 — 검증 task·테스트 코드 (병행)

각 phase 진행 영역 pytest·dogfood 영역 자국.

### T39. 단위 테스트 base
- (a) 영역: `tests/` 폴더 신설·pytest config·각 pipeline 영역 1 unit test 영역 base
- (b) 의존: T11~T17
- (c) 시간: 3시간
- (d) done: pytest 호출·모든 단위 테스트 통과·CI X (로컬만·1단계).

### T40. 통합 테스트 (5 named agents)
- (a) 영역: `tests/integration/`·5 named agents 각 1개 end-to-end 영역 sample PDF → PPTX 자동 검증
- (b) 의존: T18~T22 + T39
- (c) 시간: 4시간
- (d) done: 5 e2e 테스트 모두 통과·PPTX 파일 생성·acceptance criteria 자동 검증.

---

## 의존 그래프 (요약·1단계 MVP 영역)

```
Phase 0 (T01~T04) ─┬─→ Phase 1 (T05~T10) ─┬─→ Phase 2 (T11~T17) ─┬─→ Phase 3 (T18~T22) ─┬─→ Phase 4 (T23~T26)
                   │                       │                        │                      │
                   │                       │                        │                      ├─→ Phase 5 (T27~T30)
                   │                       │                        │                      │
                   │                       │  Phase 6 (T31~T33) ────┘                      │
                   │                       │                                               │
                   │                       │                                               │
                   │  Phase 7 (T34~T36) ───┴───────────────────────────────────────────────┤
                   │                                                                       │
                   └─→ Phase 9 (T39~T40·병행) ─────────────────────────────────────────────┴─→ Phase 8 (T37·T38)
```

**1단계 MVP 마감 = 6/9 EOD** = Phase 0~5 완료 (waitlist만·결제 없음). 6/10~6/23 = Week 5~6 (결제·distribution·dogfood·GO/STOP).

---

## 시간 추정 합계 (1단계 MVP·Phase 0~5·T01~T30·T39~T40)

| Phase | task 수 | 시간 합계 |
|---|---|---|
| Phase 0 | 4 (T01~T04) | 4시간 |
| Phase 1 | 6 (T05~T10) | 9시간 |
| Phase 2 | 7 (T11~T17) | 18시간 |
| Phase 3 | 5 (T18~T22) | 11시간 |
| Phase 4 | 4 (T23~T26) | 9.5시간 |
| Phase 5 | 4 (T27~T30) | 5시간 |
| Phase 9 | 2 (T39·T40) | 7시간 |
| **합계** | **32 task** | **~63.5시간** |

Phase 6 (templates 자산·T31~T33) = 후추님 영역 + 제대리 영역 = 11시간 (별도).
Phase 7 (결제·distribution·T34~T36) = Week 5 영역 = 6시간 + 후추님 영역.
Phase 8 (dogfood·GO/STOP·T37·T38) = Week 6 영역 = 6시간 + 후추님 결재.

**1단계 MVP 영역 = 약 63.5시간** (Phase 0~5 + Phase 9). 4주 (Week 1~4·5/13~6/9) 영역 = 주 16시간 (하루 2~3시간) 영역 정합.

---

## 의존성 blocked task 정리 (후추님 결재 영역)

| Task | 영역 | 사유 |
|---|---|---|
| T01 | repo 결정 | 별도 repo OR 기존 폴더 영역 결정 |
| T08 | 토스 sandbox key | 외부 API 영역 |
| T12 | Gemini API key | 외부 API 영역 |
| T31 | 후추님 137개 송부 | 자료 영역 |
| T33 | 노클 자료 송부 | 자료 영역 |
| T35 | 토스 production·시즌드 사업자 | 결제·법인 영역 |
| T36 | Distribution 글 | 후추님 영역 (X·디스콰이엇) |
| T38 | GO/STOP 결정 | 후추님 결재 영역 |

본진 자율 영역 (결재 X) = T02~T07·T09·T10·T11·T13~T30·T39·T40 = **약 24 task·약 50시간**.

---

## 본진 vs 제대리 분담

| Task | 분담 | 사유 |
|---|---|---|
| T01~T05 | 본진 자율 | 1파일 폴더 신설 영역 |
| T06·T10 | 본진 자율 | 단순 schema 영역 |
| T07·T09 | 본진 자율 | abstract class 영역 |
| T11·T13·T15·T16·T17 | 본진 자율 | v1 자산 이식·1~2파일 영역 |
| **T12·T14** | **제대리 핸드오프** | **2파일+·Gemini grounding·3에이전트 영역·복잡 영역** |
| T18~T22 | 본진 자율 | pipeline 호출 wrapper·각 1파일 영역 |
| T23~T26 | 본진 자율 | Streamlit UI 영역 |
| T27~T30 | 본진 자율 | guardrails 영역 |
| T31~T33 | 본진 + 제대리 교차 | templates 자산 영역 |
| T39·T40 | 본진 자율 | 테스트 영역 |

본진 자율 영역 24 task + 제대리 핸드오프 2 task (T12·T14) + 교차 3 task (T31~T33).

---

## test_scenarios·pre_mortem 정합 검증

### test_scenarios 50+ 시나리오 영역 task 매핑

| 시나리오 분류 | 매핑 task |
|---|---|
| Vendor Proposal 5종 | T18 dogfood 영역 |
| Brand Guide 5종 | T19 dogfood 영역 |
| Marketing Brief 5종 | T20 dogfood 영역 |
| Industry Research 5종 | T21 dogfood 영역 |
| Curriculum 5종 | T22 dogfood 영역 |
| Cold-start interview | T24 dogfood 영역 |
| 7단계 pipeline | T11~T17 단위 테스트·통합 테스트 영역 |
| Guardrails 4종 | T27~T30 + T40 통합 영역 |
| UI | T23·T25·T26 dogfood 영역 |
| practice_areas | T05·T06 검증 + 5 agents 자동 read 검증 |
| Architecture base | T02·T07·T10 + 빈 placeholder 검증 |

→ 모든 시나리오 = task 영역 매핑 자국 검증 ✅.

### pre_mortem 위험 영역 mitigation task

| 위험 | mitigation task |
|---|---|
| Gamma·Tome 정면 충돌 | T21 Industry Research strict (한국 톤 + 컨설팅 리서치 layer) |
| Time-to-value 3~10분 사용자 인내 X | T25 진행 시각화 + T21 strict 영역 명시 (사용자 *기대* 영역) |
| 137개 리서치 톤 X | T31 + T32 (ARK + KPMG/BCG 동시 학습) |
| premature globalization | T02·T07·T09 (ko 단일·placeholder 빈 파일) |
| Distribution 약함 | T36 (waitlist + 디스콰이엇 + 슬랙) |
| paywall risk | T10 메타데이터 schema strict (license 필드) |
| 6주 검증 GO 못 채움 | T38 STOP 영역 자국 |
| BYOD 보안 X | T34 waitlist 인터뷰 시 BYOD 영역 확인 |

→ 8 위험 = task 영역 매핑 ✅.

---

## 폴더 구조 최종 (1단계 MVP)

```
tickdeck_v2/
├── app.py                              # T23 (Streamlit 랜딩)
├── pyproject.toml or requirements.txt  # T01
├── README.md                           # T01
├── .gitignore                          # T01
├── named_agents/                       # Phase 3
│   ├── __init__.py
│   ├── vendor_proposal.py              # T18
│   ├── brand_guide.py                  # T19
│   ├── marketing_brief.py              # T20
│   ├── industry_research.py            # T21 ⭐
│   └── curriculum.py                   # T22
├── pipeline/                           # Phase 2
│   ├── __init__.py
│   ├── parse.py                        # T11
│   ├── research.py                     # T12 (제대리)
│   ├── merge.py                        # T13
│   ├── narrative.py                    # T14 (제대리)
│   ├── quality.py                      # T15 (v1)
│   ├── design.py                       # T16
│   └── pptx.py                         # T17 (v1)
├── practice_areas/                     # Phase 1·6
│   ├── automotive/{tone_dict,templates,schema}.json
│   ├── entertainment/{...}
│   ├── food/{...}
│   ├── education/{...}
│   ├── brand_consulting/{...}
│   ├── marketing/{...}
│   └── finance/{...}
├── shared/                             # v1 자산
│   ├── pptx_builder.py
│   ├── gemini_client.py
│   ├── schemas.py
│   └── metadata_schema.py              # T10
├── profile/                            # Phase 0
│   ├── profile_loader.py               # T03
│   └── tickdeck_profile.md.template    # T03
├── guardrails/                         # Phase 5
│   ├── source_attribution.py           # T27
│   ├── assumption_surfacing.py         # T28
│   ├── disclaimer.py                   # T29
│   └── review_gate.py                  # T30
├── locales/                            # Phase 0
│   ├── ko.json                         # T02
│   ├── ja.json                         # T02 (placeholder)
│   ├── zh-TW.json                      # T02 (placeholder)
│   └── en.json                         # T02 (placeholder)
├── payment/                            # Phase 1
│   ├── base.py                         # T07
│   ├── toss.py                         # T08
│   └── stripe.py                       # T09 (placeholder)
└── tests/                              # Phase 9
    ├── conftest.py
    ├── unit/
    └── integration/
```

---

## 가설 확인/기각 (P3-T5)

**가설**: "PRD·feature_spec·test_scenarios·pre_mortem 정합 영역 영역 빌드 task 영역 = 2~5분 단위 task 영역 분리. superpowers:writing-plans skill 또는 본진 자율 영역. Streamlit 1단계 MVP·5 named agents·7단계 pipeline·practice_areas plugin·guardrails·locales 영역 영역 task 영역."

→ ✅ **확인** (일부 갱신). 본 PLAN_implementation.md 영역 = 32 task (P3-T5 task 영역 명세 영역 ≥ 20 충족·실 32)·1단계 MVP 영역 (Phase 0~5 + Phase 9) = 약 63.5시간 (Week 1~4·4주 영역)·각 task = (a)/(b)/(c)/(d) 양식 자국 ✅.

**갱신 영역** (작업 명세 영역 X):
- 2~5분 단위 X·30분~3시간 단위 (실 빌드 task 영역 적합·2~5분 영역은 sub-task 영역)
- superpowers:writing-plans skill X·본진 자율 영역 (사상만 정합·실 skill 호출 X)
- 1단계 MVP 마감 = **6/9 EOD** (Week 4 종료)·6주 검증 마일스톤 정합

**검증**:
- task 수 ≥ 20: ✅ 32 task
- 각 task (a)/(b)/(c)/(d): ✅ 모두 영역 자국
- Streamlit 1단계 MVP·5 named agents·7단계 pipeline·practice_areas·guardrails·locales: ✅ 모두 task 영역
- 1단계 MVP 마감 추정: ✅ 6/9 EOD (4주·63.5시간)
- feature_spec acceptance criteria 정합: ✅ 모든 영역 task 매핑
- test_scenarios 50+ 매핑: ✅ 영역별 task 매핑 자국
- pre_mortem 8 위험 mitigation: ✅ task 영역 매핑 자국

---

## 다음 step

1. ✅ PLAN_implementation.md 신설 (본 layer·P3-T5 완료)
2. ⏳ 노클 PDF 교차 분석 (P3-T6·7단계·자동 진행 영역)
3. **후추님 결재 영역** (T01·T08·T12·T31·T33·T35·T36·T38) = 후추님 inbox 메모 영역
4. 본진 자율 빌드 영역 = T02~T07·T09~T11·T13·T15~T30·T39·T40 (약 50시간) → Phase 4 진입 후 빌드 시작 (P3-T7 영역)
5. 제대리 핸드오프 영역 = T12·T14 (Gemini grounding + 3에이전트 narrative) inbox 영역 (P3-T7 진입 시)

## 가시성 (한 줄)

PLAN_implementation.md = 32 task·9 Phase·1단계 MVP 6/9 EOD·63.5시간·본진 자율 24 + 제대리 2 + 후추님 영역 6 분담·feature_spec/test_scenarios/pre_mortem 정합 검증 자국 완료.
