# TickDeck v2 — 5/14 작업 plan (PLAN_5-13 wedge 재정의 정합 갱신 layer)

> 작성: 2026-05-15 01:50 KST (Ralph P3-T1)
> 영역: PLAN_5-13.md 영역 = 5/12 PRD v2.0 (line 250~262) 기준. PRD v2.1 (5/13 wedge 재정의·line 266~) + PRD v2.2 (claude-for-legal·line 421~) 갱신 layer 정합 X 영역 누락 → 본 파일 신설.
> 보존: PLAN_5-13.md 그대로 자국·본 파일 = 갱신 layer 추가.
> 기준: PRD_v2.md v2.1·v2.2 영역 (line 266~561)

## 갱신 사상 (PLAN_5-13 → 5/14)

PLAN_5-13 = "일반인 1-딸깍 PDF→PPTX" 7단계 영역 plan
PLAN_5-14 = wedge 좁힘 + Thiel framework + claude-for-legal 사상 정합 = SaaS 진짜 살리는 노선 input 영역

## wedge 재정의 정합 (v2.1·v2.2 영역)

| 영역 | PLAN_5-13 (5/12 PRD v2.0) | PLAN_5-14 (5/13 PRD v2.1·v2.2 정합) |
|---|---|---|
| ICP | 일반인 (대학생·면접관·잠재 고객) | Primary = 한국 BD·marketing·컨설팅 agency·1인 외주·BYOD 실무자 |
| 가치 한 줄 | PDF 한 장 → PPTX 1-딸깍 | 한국 B2B 제안서·brand 컨설팅·marketing brief — Gamma·Tome 못 따라오는 한국 톤 + 컨설팅 리서치 layer |
| Time-to-value | 1~5분 | 3~10분 (컨설팅 리서치 단계 layer) |
| Pricing | 미정 | 1회 단발 5,000~10,000원 (구독 X) |
| 도구 사상 | 단일 도구 1-딸깍 | 5 Named Agents (단일 X·골라 사용) |
| 학습 layer | 후추님 137개 | + ARK Big Ideas + 삼정KPMG·KPMG·Deloitte·BCG/McKinsey Korea + 한국 증권사 200~300개 |
| 노선 | 국내만 | Asia-first 3단계 (국내 → 아시아 → 글로벌·1단계부터 architecture base) |
| Secondary | (단일 wedge) | 포폴·이력서·학회·과제·회의 메모 = secondary 옵션·marketing X |

## 3·4·5·6단계 영역 입력 갱신 (PLAN_5-13 7단계 영역 정합)

PLAN_5-13 7단계 영역 (1 user flow → 2 wireframe → 3 feature-spec → 4 test-scenarios → 5 pre-mortem → 6 writing-plans → 7 노클 PDF) 자체 구조 = 유효. *입력 영역만 갱신*.

### 3단계 (feature-spec:index) 입력 갱신

| 영역 | PLAN_5-13 입력 | PLAN_5-14 입력 갱신 |
|---|---|---|
| 청중·목적 인풋 | 청중 1줄·목적 1줄·skip OK | Cold-start interview 5분 (산업 7카테고리·청중 4종·톤 3종·출처 정책·분량·언어) |
| 도구 사상 | 단일 도구·1-딸깍 | 5 Named Agents 선택 화면 |
| 출력 영역 | PPTX 1개 다운로드 | PPTX + source attribution footer + assumption surfacing + disclaimer 화면 (다운로드 전 review gate) |
| 파이프라인 | 7단계 (parse·research·merge·narrative·quality·design·pptx) | 동일·근데 research 단계 = 컨설팅 리서치 layer (1차/2차 자료·시장·경쟁사·트렌드·인용·출처) strict |
| 산업 매칭 | (없음) | practice_areas 폴더 구조 (automotive·entertainment·food·education·brand_consulting·marketing·finance) base |

### 5 Named Agents 영역 (3단계 feature-spec 필수 자국)

| Agent | command sketch | 산업 매칭 | 사용자 시각 |
|---|---|---|---|
| Vendor Proposal Drafter | `/tickdeck:vendor-proposal` | 자동차·엔터·식품 | B2B 외주 제안서·brochure·press kit |
| Brand Guide Builder | `/tickdeck:brand-guide` | brand 컨설팅 | brand 가이드·디자인 시스템·시각 자료 |
| Marketing Brief Creator | `/tickdeck:marketing-brief` | marketing | marketing 전략·campaign brief |
| Industry Research Compiler | `/tickdeck:industry-research` | 금융·리서치 | 산업 분석 보고서·시장 동향·경쟁사 |
| Curriculum Pack Designer | `/tickdeck:curriculum` | 교육 | 교육 커리큘럼·강의 자료 |

랜딩 페이지·UI 영역 = "5 agents 중 골라 사용" 화면·단일 도구 X. 와이어프레임 5종 (PLAN_5-13 2번 영역) 영역 갱신 후보 (후추님 결정).

### 4단계 (test-scenarios) 입력 갱신

| 시나리오 | PLAN_5-13 영역 | PLAN_5-14 갱신 |
|---|---|---|
| 시나리오 1 | 일반인 PDF 업로드 → PPTX 다운로드 | BD agency 실무자 = Vendor Proposal Drafter 사용 → 자동차 산업 제안서 (5분 interview·3~10분 생성) |
| 시나리오 2 | (없음) | brand 컨설팅 1인 외주 = Brand Guide Builder 사용 → 디자인 시스템 deck |
| 시나리오 3 | (없음) | marketing agency = Marketing Brief Creator 사용 → campaign brief deck |
| 시나리오 4 | (없음) | 증권사 애널리스트 = Industry Research Compiler 사용 → 산업 보고서 deck (출처 표기·각주 strict) |
| 시나리오 5 | (없음) | 교육 강사 = Curriculum Pack Designer 사용 → 강의 자료 deck |
| Secondary | (단일 시나리오) | 포폴·이력서·학회·과제·회의 메모 = secondary 옵션 시나리오 (marketing X·도구 자유 허용 시나리오) |

guardrails 시나리오 추가:
- source attribution = 자동 footer 또는 각주 출력 검증
- assumption surfacing = "산업: 자동차·청중: 임원·정장 톤" 인풋 표 deck 1페이지 출력 검증
- disclaimer = "결과 deck = 초안·사용자 검토·수정 의무" 출력 검증
- review gate = 다운로드 전 review 화면 동작 검증

### 5단계 (pre-mortem) 입력 갱신

PLAN_5-13 = (영역 X) → PLAN_5-14 갱신 영역:

| 위험 | 영역 | 회피 |
|---|---|---|
| Gamma·Tome 정면 충돌 | 영어 톤 + 1-딸깍 = 정면 충돌·죽음 | wedge 좁힘 (한국 톤·컨설팅 리서치 layer·B2B 제안서 strict) |
| Time-to-value 60초 wedge 무너짐 | 3~10분 = 사용자 인내 X 가능 | 컨설팅 리서치 layer = 사용자가 *기대*하는 시간 (Gamma 1분 ≠ 진짜 deck) |
| 137개 = 리서치 톤 X | 137개 = B2B 제안서 톤만 | ARK + KPMG/BCG/Deloitte 동시 학습 필수 |
| premature globalization | 1단계부터 다국어·다통화 풀 활성화 = 풀세트 X | 1단계 = ko 단일·architecture base만·plug-in 빈 파일 |
| Distribution 약함 (Thiel 5번) | 펩핀치·잡솔트·X = 약함 | waitlist + 디스콰이엇 + 스타트업 슬랙 + 한국 marketing 채널 추가 영역 |
| paywall·내부 자료 라이선스 risk | Fine-tuning X·전체 복사 X | Template extraction + Few-shot·공개 자료 + 출처 strict |
| 6주 검증 GO 조건 못 채움 | 매몰비용 폐기 | 자산 노선 (본인 도구) 전환 |
| BYOD 보안 layer 무너짐 | 한국 대기업 (SK 제외) BYOD 多 = 검증 X | 1단계 검증 영역 (waitlist 인터뷰 시 BYOD 가능 영역 확인) |

### 6단계 (writing-plans) 입력 갱신

PLAN_5-13 = superpowers:writing-plans skill·2~5분 task 영역
PLAN_5-14 갱신:

- Week 1 (5/13~5/19) task = wedge 1줄 갱신·PRD v2.1·랜딩 페이지 + architecture base (i18n·결제 어댑터·메타데이터 schema) + Cold-start interview 사상·named agents 5종 sketch·practice_areas 폴더 구조
- Week 2 (5/20~5/26) task = templates.json 한국 5종 추출 + ARK 본진+제대리 교차 분석 + 메타데이터 schema strict (country·industry·language·license)
- Week 3 (5/27~6/2) task = waitlist 마케팅·디스콰이엇·스타트업 슬랙 + 노클 글로벌 자료 백그라운드 다운로드 (YC·McKinsey 공개)
- Week 4 (6/3~6/9) task = Streamlit MVP·sample 5종 (5 named agents 정합) + named agents UI (단일 도구 X) + source attribution + disclaimer 화면 + i18n 파일 분리 (locales/ko.json·locales/ja.json 빈 파일)
- Week 5 (6/10~6/16) task = 결제 검증 토스페이먼츠·1회 5천원 + 결제 어댑터 사상 base (Stripe 빈 파일)
- Week 6 (6/17~6/23) task = LTV·재방문·NPS·GO/STOP + 백그라운드 글로벌 자료 누적 점검

폴더 구조 base (PRD v2.2 line 522~545 정합):

```
tickdeck_v2/
├── app.py                    # Streamlit (1단계·MVP UI)
├── named_agents/             # 5종 (1단계·single workflow per file)
│   ├── vendor_proposal.py
│   ├── brand_guide.py
│   ├── marketing_brief.py
│   ├── industry_research.py
│   └── curriculum.py
├── pipeline/                 # 7단계 (parse·research·merge·narrative·quality·design·pptx)
├── practice_areas/           # plugin 사상 base
│   ├── automotive/
│   ├── entertainment/
│   ├── food/
│   ├── education/
│   ├── brand_consulting/
│   ├── marketing/
│   └── finance/
├── shared/                   # v1 자산
├── profile/                  # cold-start interview + tickdeck_profile.md (세션 임시)
├── guardrails/               # source attribution·assumption surfacing·disclaimer
└── locales/                  # i18n (ko.json·ja.json 등)
```

## 2번 영역 (와이어프레임 prompt) 갱신 후보

PLAN_5-13 2번 영역 prompt = 5개 화면·1-딸깍 노선. 갱신 후보:

- 화면 1 (랜딩) = "5 agents 골라 사용" 화면 영역 (Vendor Proposal·Brand Guide·Marketing Brief·Industry Research·Curriculum)
- 화면 2 (PDF 업로드) = 동일
- 화면 3 (청중·목적) = Cold-start interview 5분 (산업·청중·톤·출처 정책·분량·언어)
- 화면 4 (파이프라인) = 7단계 시각화·예상 시간 3~10분 strict
- 화면 5 (완료·다운로드) = source attribution footer + assumption surfacing + disclaimer + review gate (다운로드 전 review 화면)

⚠️ 와이어프레임 영역 = 후추님 직접 영역 (Claude Design)·본진 자율 X. 후추님 결정 시 위 prompt 영역 갱신.

## 7번 영역 (노클 PDF) 갱신

PLAN_5-13 = 노클 selection·자동 read·제대리 교차 분석 → templates.json
PLAN_5-14 갱신:
- 노클 selection 분류 (PRD v2.1 line 411~415 정합):
  - Primary = 자동차·엔터·식품·교육·brand 컨설팅·marketing brief (B2B 제안서 톤)
  - Secondary = 포폴·이력서·학회·과제·회의 메모·기타
  - 글로벌 리서치 자료 일괄 다운로드 (YC·McKinsey·BCG·Bain·Deloitte 공개 + ARK 추가)
- 메타데이터 schema strict (country·industry·language·license·source_url)

## 가설 확인/기각 (P3-T1)

가설: "PLAN_5-13.md 영역 = 5/12 PRD v2.0 기준 작성. 5/13 wedge 재정의 + PRD v2.2 claude-for-legal layer 정합 X 영역 누락."

→ ✅ 확인. PLAN_5-13.md 영역 7단계 입력 영역 = 5/12 PRD 영역 정합·v2.1 (Primary B2B·5 Named Agents·Asia-first·137개 + ARK·1회 5,000~10,000원·Time-to-value 3~10분) + v2.2 (Cold-start interview·practice_areas·source attribution·disclaimer·guardrails·plugin 사상) 영역 누락. 본 PLAN_5-14.md 신설로 갱신 layer 추가.

## 가시성 (한 줄)

3·4·5·6단계 입력 영역 = v2.1·v2.2 정합 영역 명시. 와이어프레임 영역 (2번) = 후추님 직접 영역·prompt 갱신 후보만 명시. 노클 selection 영역 (7번) = 분류 갱신.

## 다음 step

1. ✅ PLAN_5-14.md 신설 (본 layer)
2. PLAN_5-13.md 2번 영역 prompt = 와이어프레임 영역·후추님 결정 시 갱신 (지금 X·결재 영역)
3. 본진 3~6단계 자율 진행 시 = 본 layer 입력 영역 정합 의무
4. 노클 7번 영역 = `inbox/from_honjin/` push 영역 (5/13 PRD v2.1 line 411 영역 정합·이미 송부 영역 또는 신설)
