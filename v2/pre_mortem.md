# TickDeck v2 — Pre-Mortem (출시 전 위험 분석)

> 작성: 2026-05-15 03:30 KST (Ralph P3-T4)
> 기준: `PRD_v2.md` v2.1·v2.2 + `PLAN_5-14.md` + `feature_spec.md` + `test_scenarios.md`
> 영역: PLAN_5-13 7단계 중 5단계 (pre-mortem) — `pm-execution:pre-mortem` skill 5단계 양식 적용
> 가설: TickDeck v2 6주 검증 (5/13~6/23) GO 조건 (waitlist→결제 30%+·재방문 70%+·10x NPS·Distribution 채널 검증) 미충족 시 위험 = Tiger / Paper Tiger / Elephant 분류

---

## 0. 사상·범위

본 pre-mortem = "6주 검증 (5/13~6/23) 끝 시점에 TickDeck v2 = 실패했다" 가상 시점에서 거꾸로 원인 추적·위험 영역 도출.

분류 양식 (pm-execution:pre-mortem 사상 정합):

| 분류 | 의미 | 대응 |
|---|---|---|
| 🐅 Tiger | launch-blocking·실패 = 죽음 영역 | 즉시 회피·1주 안 mitigation 의무 |
| 📜 Paper Tiger | 보기는 무서운데 실제 영향 ↓ | track·monitoring·6주 안 점검 |
| 🐘 Elephant | 지금 외 큰 영역·1단계 끝 후 | fast-follow·2~3단계 영역 |

목표 = Tiger 영역 사전 식별·1단계 (5/13~6/23) 안 회피 또는 mitigation 시동·매몰비용 폐기 결단 영역 명확화.

---

## 1. Setup the Pre-Mortem (시점·시나리오 설정)

### 가상 시점
2026-06-23 (6주 검증 끝). TickDeck v2 = 실패 판정. 자산 노선 (본인 도구) 전환.

### 실패 시나리오 4종

| 시나리오 | 풀이 |
|---|---|
| A. 시장 무관심 | waitlist 30명 모집 실패·결제 전환 X·재방문 X |
| B. 빌드 불완성 | Streamlit MVP 6주 안 X·sample 5종 X·5 Named Agents UI X |
| C. 가치 layer 무너짐 | Gamma·Tome 사용자 비교 NPS ↓·"왜 이거 써?" 답 X |
| D. 외부 사고 | 잡솔트 결과·EatScan 결과·외부 공모전 마감 = TickDeck 빌드 stall |

각 시나리오 = root cause 영역 위험 분포 다름. 본 pre-mortem = A·B·C 영역 strict (D = 외부 마감 양보 룰 정합·5/13 PRD line 400~405 영역 자국).

---

## 2. Imagine the Failure — 실패 시나리오 brainstorm

### 시나리오 A (시장 무관심) — root cause 후보

1. Gamma·Tome·Claude Design 시장 영역 정면 충돌·한국 톤 + 컨설팅 리서치 layer 차별 layer 약함 인식
2. 한국 BD agency·BYOD 실무자 영역 실제 거부 (BYOD 제한·보안 layer 두려움·검증 X 도구 신뢰 X)
3. Distribution 채널 약함 (펩핀치·잡솔트·X = waitlist 30명 모집 X)
4. Time-to-value 3~10분 wedge 사용자 인내 X (Gamma 60초 익숙·"왜 이렇게 느려?")
5. 1회 5,000~10,000원 pricing = "deck 1장 → 5천원 = 비싸다" 인식 (구독 sub 익숙)
6. cold-start interview 5분 사용자 인내 X (Gamma·Tome = 인터뷰 X·즉시 결과)
7. 5 Named Agents 선택 화면 = "어느 거 써?" 사용자 부담·단일 도구 X 부정 영향

### 시나리오 B (빌드 불완성) — root cause 후보

8. 6주 영역 부족 (architecture base + MVP + 5 Named Agents UI + 결제 검증 + 검증 영역 동시)
9. 후추님 137개 + ARK + KPMG/BCG 리서치 톤 학습 영역 본진+제대리 교차 분석 부담
10. practice_areas plugin 사상 base 1단계 추가 비용 (MVP 부담 ↑)
11. Streamlit MVP 영역 한계 (UI 디자인·5 Named Agents 선택 화면·review gate 영역 어색)
12. 결제 어댑터 토스페이먼츠 단일 의존 (외부 의존 영역·5/30~5/31 사보원 마감 X 영역)
13. source attribution 라이선스 cleared 확인 부담 (137개 + ARK + KPMG/BCG 각 자료 라이선스 점검)

### 시나리오 C (가치 layer 무너짐) — root cause 후보

14. 후추님 137개 = B2B 제안서 톤만·*리서치 톤 X* (PRD v2.1 line 311 영역 자국)
15. ARK + KPMG/BCG 리서치 톤 1단계 안 학습 영역 부족 (자료 32MB·6주 안 patterns 추출 X)
16. 한국 비즈니스 톤·존댓말 검증 영역 부족 (sample 5종 dogfood 영역 N=5 = 통계 X)
17. 산업별 톤 dictionary 매칭 X (automotive ≠ entertainment 영역 검증 부족)
18. 10x breakthrough 검증 X (Gamma·Tome 사용자 비교 N=10+ 영역 6주 안 X 가능)
19. premature globalization (1단계부터 architecture base = 한국 wedge 검증 영역 분산)
20. paywall·내부 자료 라이선스 risk (KPMG·BCG·Deloitte 영역 일부 paywall 가능)

---

## 3. Identify Causes — root cause 분석 (5 whys 사상)

### root cause 1 — wedge 검증 부족 (시나리오 C 핵심)
**Why 1**: 137개 = B2B 제안서 톤만·리서치 톤 X
→ **Why 2**: 후추님 5/13 정정 영역 강조·1단계부터 ARK·KPMG/BCG 동시 학습 의무
→ **Why 3**: 6주 안 32MB ARK + KPMG/BCG patterns 추출 영역 본진+제대리 교차 분석 부담
→ **Why 4**: 매주 1~2일 영역 분석 시간 영역 제대리 작업 큐 정합·우선순위 명확화 X
→ **Why 5**: PRD·feature_spec 영역 명시·근데 ClickUp Task·writing-plans 영역 분해 X

→ **Tiger**: Week 1·Week 2 ClickUp Task 영역 strict·본진+제대리 교차 분석 시간 영역 우선순위 1번 자국

### root cause 2 — Distribution 약함 (Thiel 5번·시나리오 A 핵심)
**Why 1**: 펩핀치·잡솔트·X = waitlist 30명 모집 검증 X
→ **Why 2**: 한국 marketing 채널 (디스콰이엇·스타트업 슬랙·linkedin Korea) 영역 본진 사용 부담
→ **Why 3**: 후추님 1인 영역·외주 X·marketing layer 부족
→ **Why 4**: Week 3 (5/27~6/2) = waitlist 마케팅·디스콰이엇·스타트업 슬랙 영역·실 채널 검증 X
→ **Why 5**: 채널 검증 시기 = Week 3 = 빌드 4주차·MVP X·prelaunch waitlist만

→ **Tiger**: Week 1~2 영역부터 waitlist 페이지 + 본진·잡솔트·X 채널 영역 시동 의무

### root cause 3 — Time-to-value 3~10분 wedge 무너짐 (시나리오 A 핵심)
**Why 1**: Gamma·Tome 60초 익숙·"왜 이렇게 느려?"
→ **Why 2**: 컨설팅 리서치 layer = 사용자 *기대*하는 시간 layer (PLAN_5-14 line 76 영역)
→ **Why 3**: UI 영역 "3~10분 = 정상·진짜 deck 만드는 시간" 메시지 strict 필수
→ **Why 4**: feature_spec 영역 = 화면 4 (파이프라인 시각화·예상 시간 3~10분 strict) 명시
→ **Why 5**: 실 사용자 사용 시 5분 후 "포기" 가능성·진행 영역 UX (progress bar·단계별 영역 시각화) 영역 부담

→ **Paper Tiger**: UI 영역 strict 메시지 + 진행 영역 UX·track 영역

### root cause 4 — BYOD·보안 layer (시나리오 A·실 한국 대기업 영역)
**Why 1**: 한국 대기업 (SK 제외) BYOD 多·근데 검증 X
→ **Why 2**: PRD v2.1 line 298 = "보안 풀이 정정·BYOD 사용 多·시장 진입 가능" 후추님 직관 영역
→ **Why 3**: 실 BYOD 가능 영역 검증 = waitlist 인터뷰 시 (Week 3~4) 영역
→ **Why 4**: 인터뷰 N=10+ 영역 6주 안 X 가능·답 = 1단계 운영 후 (1년) 명확화
→ **Why 5**: 1단계 = BD agency·1인 외주 영역 strict 좁힘·대기업 BYOD 영역 = 1년 후 확장

→ **Paper Tiger**: 1단계 = BD agency·1인 외주 strict·대기업 BYOD = Elephant 영역

### root cause 5 — pricing 1회 5,000~10,000원 시장 거부 (시나리오 A)
**Why 1**: 구독 sub 익숙·1회 deck 1장 = 비싸다 인식
→ **Why 2**: 1 deck 원가 1,700원 + 수수료 150원·이익률 63~81% 영역 (PRD v2.1 line 373)
→ **Why 3**: 구독 9,900원 / 5 deck = 이익률 11% (X) 영역·구독 X 결정 (PRD line 374)
→ **Why 4**: 후추님 5/13 영역 강조·1회 pricing 정밀도 최고 노선
→ **Why 5**: 시장 = pricing test (waitlist 인터뷰 시 가격 점검 의무·Week 3~4 영역)

→ **Paper Tiger**: 가격 인식 영역 = waitlist 인터뷰 점검·track 영역

---

## 4. Categorize Risks — 위험 분류표 (20개·Tiger·Paper Tiger·Elephant)

### 🐅 Tiger (launch-blocking·즉시 회피·1주 안 mitigation 의무)

| # | 위험 | root cause | mitigation | 시기 |
|---|---|---|---|---|
| T1 | wedge 검증 부족·137개 = 리서치 톤 X | root cause 1 | Week 1~2 ClickUp Task·본진+제대리 교차 분석 시간 strict·ARK + KPMG/BCG patterns 추출 우선순위 1번 자국 | Week 1 (5/13~5/19) 의무 |
| T2 | Distribution 약함·waitlist 30명 모집 X | root cause 2 | Week 1~2 waitlist 페이지 + 본진·잡솔트·X 채널 시동·디스콰이엇·스타트업 슬랙 가입 자국 | Week 1~2 의무 |
| T3 | 6주 GO 조건 미충족 매몰비용 폐기 결단 X | "1주 안 X 시 폐기" 룰 약함 | 매주 GO 조건 4종 (waitlist→결제 30%+·재방문 70%+·10x NPS·채널 검증) 점검·미충족 시 즉시 archived 결정·매몰비용 폐기 결단 의무 | 매주 의무 |
| T4 | 10x breakthrough 검증 X·Gamma·Tome NPS 비교 X | root cause 3·15 | Week 4~5 sample 5종 동작 후 즉시 Gamma·Tome 사용자 N=5+ 영역 NPS 비교 점검·Week 6 N=10+ 영역 검증 의무 | Week 4~6 의무 |
| T5 | Streamlit MVP 영역 한계·5 Named Agents UI X | root cause 11·8 | Week 4 (6/3~6/9) = MVP UI 영역 strict 점검·feature_spec 화면 5종 영역 (랜딩·업로드·interview·파이프라인·완료) 영역 dogfood·문제 시 Week 5 추가 영역 | Week 4 의무·Week 5 buffer |

→ **5개 Tiger 영역 = 1단계 (5/13~6/23) 6주 안 죽음 영역 strict 회피 의무.**

### 📜 Paper Tiger (보기는 무서운데 실제 영향 ↓·track·monitoring)

| # | 위험 | root cause | track 영역 | 점검 시기 |
|---|---|---|---|---|
| P1 | Time-to-value 3~10분 wedge 무너짐 | root cause 3 | UI 영역 strict 메시지 ("3~10분 = 진짜 deck·Gamma 60초 ≠ 진짜") + 진행 영역 UX (progress bar·단계별 영역) | Week 4 MVP 안 검증 |
| P2 | BYOD·보안 layer 영역 한국 대기업 거부 | root cause 4 | 1단계 = BD agency·1인 외주 strict·대기업 BYOD = waitlist 인터뷰 시 점검·1년 운영 후 확장 | Week 3~4 인터뷰·1년 후 확장 |
| P3 | pricing 1회 5,000~10,000원 시장 거부 | root cause 5 | waitlist 인터뷰 시 가격 점검 의무·"구독 X·1회 5천 OK?" 영역·답 시장 데이터·track | Week 3~4 인터뷰 |
| P4 | cold-start interview 5분 사용자 인내 X | root cause 6 | feature_spec acceptance criteria = interview 5분 안 완료 영역·1인 dogfood + waitlist 인터뷰 점검·skip OK (default 자동 매칭) buffer | Week 4 MVP 안 검증 |
| P5 | 5 Named Agents 선택 화면 = 사용자 부담 | root cause 7 | 랜딩 페이지 = "5 agents 골라 사용" 영역 strict·default agent 추천 영역 (profile 인풋 정합 자동 매칭) buffer | Week 4 MVP 안 검증 |
| P6 | source attribution 라이선스 cleared 확인 부담 | root cause 13 | 137개 = 후추님 본인 저작권·ARK·정부·OECD·World Bank·YC 공개 = 라이선스 cleared 영역·KPMG·BCG·Deloitte = 공개 자료만 strict + 출처 표기 (PRD line 342~346) | Week 2 patterns 추출 시 점검 |
| P7 | premature globalization·1단계부터 architecture base 분산 | root cause 19 | 1단계 = ko 단일·plug-in 빈 파일 base만·풀 활성화 X (PRD line 309) + Week 1 architecture base 영역 작업 1~2일 strict | Week 1 의무 |

→ **7개 Paper Tiger = track·monitoring 영역·점검 시점 strict.**

### 🐘 Elephant (fast-follow·1단계 끝 후·2~3단계 영역)

| # | 위험 | 영역 | 시기 |
|---|---|---|---|
| E1 | practice_areas plugin 사상 base 1단계 추가 비용 | 1단계 = code 구조 base만·실 plugin 빌드 = 2단계 (1년 후·동아시아 확장 시점) | 1년 후·2단계 |
| E2 | 한국 대기업 (BYOD 多·SK 제외) 실 시장 진입 검증 | 1년 운영 후 BD agency 영역 검증 후 확장 | 1년 후·2단계 |
| E3 | 영어권 wedge 확장 (3단계 글로벌·1.5~2년 후) | architecture base 영역 i18n·결제·distribution 어댑터 plug-in 활성화 | 1.5~2년 후·3단계 |
| E4 | scheduled agents (Industry Trend Watcher·Template Update Suggester·Client Re-engagement) | 2~3단계 영역·1단계 MVP 부담 X (PRD v2.2 line 484~495) | 2~3단계 |
| E5 | MCP connectors (Google Drive·Notion·Figma·ClickUp·Linear·Slack·Bloomberg·CB Insights·Statista) | 2~3단계 영역·1단계 = Streamlit local·MCP X | 2~3단계 |
| E6 | Same system + 3 deploy choice (Cowork plugin·Code plugin·Managed Agents API) | 3~4단계 영역·1단계 = Streamlit local·tickdeck.peppinch.com | 3~4단계 |
| E7 | Fine-tuning·RAG layer | 1단계 = Template extraction + Few-shot strict·Fine-tuning·RAG = 2단계 이후 검토 (PRD line 332~340) | 2단계 이후 |
| E8 | secondary segment (포폴·이력서·학회·과제·회의 메모) marketing | 1단계 = secondary 옵션·marketing X·1년 운영 후 검토 (PRD line 290·292) | 1년 후·2단계 |

→ **8개 Elephant = 1단계 (6주 검증) 영역 X·fast-follow·2~3단계 영역·1단계 부담 X.**

---

## 5. Mitigation — 회피·강화 영역 (Tiger·Paper Tiger 영역)

### Tiger mitigation (5종·즉시 의무)

#### T1 mitigation: wedge 검증 강화
- **Week 1 (5/13~5/19) ClickUp Task**: "본진+제대리 교차 분석 시간 strict 1~2일 / 주" 영역 등록
- **Week 2 (5/20~5/26) Task**: ARK + KPMG/BCG patterns 추출·templates.json 한국 5종 + 리서치 톤 5종 누적·메타데이터 schema strict
- **검증 영역**: Week 2 끝 시점 = templates.json 5종+ 영역 = B2B 제안서 톤 4종 + 리서치 톤 1종 minimum 의무·미충족 시 archived 결정

#### T2 mitigation: Distribution 채널 시동
- **Week 1 Task**: waitlist 페이지 (peppinch.com/tickdeck 또는 tickdeck.peppinch.com 영역) 시동
- **Week 1 Task**: 본진·잡솔트·X 채널 영역 첫 발화 (waitlist 모집·"한국 B2B 제안서 자동 생성 wedge" 영역)
- **Week 2 Task**: 디스콰이엇·스타트업 슬랙 가입 의무·매주 1회 발화 영역
- **검증 영역**: Week 3 끝 시점 = waitlist 10명 minimum·Week 4 = 20명·Week 5 = 30명 의무·미충족 시 archived 결정

#### T3 mitigation: 매주 GO 조건 점검·매몰비용 폐기 결단
- **매주 금요일 Task**: GO 조건 4종 점검 의무 (waitlist 진척·결제 전환 진척·재방문 의향·NPS 비교·채널 검증)
- **Week 3 끝 시점**: waitlist 10명 미충족 시 = archived 결정·6주 검증 중단·자산 노선 (본인 도구) 전환 진행
- **Week 5 끝 시점**: waitlist 20명·결제 전환 X 영역 시 = 매몰비용 폐기 결단 의무
- **자가 정정 룰**: 매몰비용 영역 자가 정정 어려움 영역 본진 자가 점검 의무 (AGENTS.md 27238 영역 정합·1주 안 X 시 archived)

#### T4 mitigation: 10x breakthrough 검증
- **Week 4 (6/3~6/9) Task**: sample 5종 동작 후 즉시 Gamma·Tome 동일 자료 영역 비교 deck 생성·NPS 인터뷰 영역 시동
- **Week 5 (6/10~6/16) Task**: 본진·잡솔트·X 영역 사용자 N=5+ 영역 NPS 비교 인터뷰 의무
- **Week 6 (6/17~6/23) Task**: N=10+ 영역 확장·NPS ↑ 확인
- **검증 영역**: Week 6 끝 시점 = NPS ↑ X·"왜 이거 써?" 답 X 영역 시 = archived 결정

#### T5 mitigation: Streamlit MVP 영역 buffer
- **Week 4 (6/3~6/9) Task**: MVP UI 영역 strict 점검·feature_spec 화면 5종 (랜딩·업로드·interview·파이프라인·완료) 영역 dogfood
- **Week 5 buffer**: 문제 시 추가 영역 buffer·UI 영역 디자인 부담 시 = Claude Design 영역 후추님 직접 영역·본진 자율 X (PLAN_5-14 line 132 영역 자국)
- **검증 영역**: Week 4 끝 시점 = 5 Named Agents 선택 화면·cold-start interview·source attribution footer·disclaimer·review gate 영역 다 동작 의무

### Paper Tiger mitigation (7종·track·UX strict)

| # | mitigation | acceptance criteria |
|---|---|---|
| P1 | UI 영역 strict 메시지 + 진행 영역 UX | feature_spec 화면 4 영역 "3~10분 = 진짜 deck" 메시지 표기·progress bar 단계별 영역 시각화·실 시간 카운트 |
| P2 | 1단계 = BD agency·1인 외주 strict·대기업 BYOD = 1년 후 | waitlist 인터뷰 시 BYOD 가능 영역 확인·1단계 ICP 정합 영역만 strict 영역 |
| P3 | 가격 인식 영역 = waitlist 인터뷰 점검 | "구독 X·1회 5천 OK?" 질문 영역·답 시장 데이터·답 X 영역 시 pricing 영역 정정 후 6주 안 1회 |
| P4 | interview 5분 안 완료·skip OK (default 자동 매칭) buffer | feature_spec acceptance criteria 자국 영역 strict |
| P5 | default agent 추천 영역 (profile 인풋 정합 자동 매칭) buffer | feature_spec 5 Named Agents 영역 매칭 영역 strict·UI default 추천 영역 |
| P6 | 137개 = 후추님 본인 + 공개 자료 + 출처 strict + paywall X 영역 | PRD line 342~346 영역 정합·Week 2 patterns 추출 시 라이선스 영역 strict 점검 |
| P7 | architecture base 영역 작업 = Week 1 안 1~2일 strict | feature_spec 영역 i18n·결제 어댑터·메타데이터 schema·practice_areas plugin 사상 base 1단계 X 영역·base만 |

→ **Tiger 5종 + Paper Tiger 7종 = 1단계 6주 검증 영역 mitigation 풀세트.**

### Elephant 영역 = 1단계 X·fast-follow

- 8 Elephant 영역 = 1단계 영역 부담 X·2~3단계 영역 fast-follow·매주 회고 시 = Elephant 영역 X 진행 영역 자가 점검 의무 (premature scaling 회피)

---

## 6. 가설 확인/기각 (P3-T4)

**가설**: "TickDeck v2 6주 검증 영역 GO 조건 영역 미충족 시 위험 = Tiger / Paper Tiger / Elephant 영역 분류."

→ **✅ 확인.**

근거:
- 20개 위험 영역 도출 → 5 Tiger + 7 Paper Tiger + 8 Elephant 분류
- 각 영역 root cause 영역 5 whys 분석·시점·mitigation 명시
- Tiger 영역 = 1단계 6주 검증 영역 strict 회피 의무·매주 점검 의무
- Paper Tiger 영역 = track·monitoring·UX strict·waitlist 인터뷰 영역 점검
- Elephant 영역 = 1단계 X·2~3단계 fast-follow·premature scaling 회피

본 pre-mortem = 1단계 6주 검증 영역 GO/STOP 의사결정 영역 input 자국.

---

## 7. 다음 step

1. ✅ pre_mortem.md 신설 (본 문서)
2. **6단계 (writing-plans)** 영역 input = Tiger 5종 + Paper Tiger 7종 mitigation 영역 = 매주 ClickUp Task 분해 의무
3. **매주 GO 조건 점검** = 매주 금요일 Task 등록 (T3 mitigation 영역)
4. **매몰비용 폐기 결단** = Week 3·Week 5·Week 6 시점 archived 결정 의무
5. **본진 자가 점검** = 매 사이클 시작 시 (AGENTS.md 매 사이클 본진 자가 점검 의무 6종 정합)
6. **회고 영역**: 매주 목요일 회고 시 = Tiger 영역 진척·Paper Tiger 영역 점검·Elephant 영역 X 확인 의무

---

## 8. 가시성 (한 줄)

5 Tiger (즉시) + 7 Paper Tiger (track) + 8 Elephant (1단계 X) = 1단계 6주 검증 영역 strict 회피·매주 GO 조건 점검·매몰비용 폐기 결단 의무 input 자국.
