# R4 설계 — 시계열 수집 계약 + 리포트 판짜기 + 블라인드 QA (2026-07-07)

> 배경: 후추님 7/7 "여전히 PDF 자료가 거의 안 들어간 게 보인다 — 왜 못 넘어서나". 진단 = R1~R3는 표기 층(크롬·캡션·색)만 흡수, 리포트다움의 본체 3층이 옛날 그대로: ①판짜기(차트가 페이지 주인공) ②시계열 데이터(차트 세울 재료) ③에이전트 선택 지식. 결재 = "②→① 한 묶음 ㄱ 하고 ③도 ㄱ".

## 1. ② 시계열 수집 계약 (선행 — 재료 없으면 판짜기는 그릴 게 없다)

### 1a. 스키마 (최소 변경 — 기존 렌더러 무개조)
- metric_registry optional 2필드: `series_id`(같은 시계열 소속 표시)·`series_key`(x축 키 — "2021"·"1Q26").
- 점 1개 = 기존 metric 1개 그대로 (검증·출처·C6 전부 기존 계약 재사용). 렌더러의 "N metrics = N points" 방식과 그대로 호환.
- **chartable series** 정의: 같은 `series_id`에 서로 다른 `series_key`를 가진 metric ≥ 4.
- deck_spec meta `"tone": "report"` (optional) 신설 — 아래 게이트·판짜기 룰의 트리거.

### 1b. 게이트 (contract_checks — 코과장)
- series_key 중복·단위 혼재(같은 series_id 안에서 unit 불일치) = C6 위반.
- tone=report인데 chartable series < 3 = `REPORT_TONE_DATA_THIN` 위반 (수집 단계로 되돌리는 신호).

### 1c. 수집·검증 지시 (collector·verifier md — 클차장)
- collector: 수치 주장을 만나면 헤드라인 숫자 하나가 아니라 **그 출처의 표/차트에 있는 시계열 전체**를 수집 (연도별·분기별 원값). "차트를 세울 데이터셋"이 1급 수집물.
- verifier: 시계열은 series 단위로 검증(단위·기간·출처 일관) 후 series_id/series_key 부여.

## 2. ① 리포트 판짜기 룰 (page-planner·designer md — 클차장)

- tone=report이면:
  - **본문 페이지 과반(≥60%) = 차트 주인공 페이지** — viz 1개 + 보조 블록 ≤2(헤드라인·노트), split·사이드 인용 금지. BOND "제목 + 풀차트 한 장" 문법.
  - page_chrome=title_band 기본, source_caption 기본 on, CL-semantic_color 의무.
  - 시계열 있는 주장을 차트 주인공 페이지에 우선 배치. 시계열 없는 주장이 주인공 페이지를 차지하면 안 됨.
- 게이트 (contract_checks — 코과장): tone=report에서 본문 페이지 중 "viz 1개+블록≤2" 페이지 비율 < 50% = `REPORT_TONE_COMPOSITION` 위반.

## 3. ③ 블라인드 비교 QA (qa-reviewer md — 클차장)

- capture 후 본문 3장 샘플 → `v3/axis2_layouts/inbox/pdf_*`에서 같은 장르 실전 페이지 2~3장을 실제로 Read → 나란히 판정: "실전 문서 사이에 섞여도 안 튀나".
- 판정 3축 (각 pass/fail + 근거): 판짜기(차트 지면 비중)·출처 표기 층·색 의미.
- qa_report에 `blind_comparison` 섹션 의무. fail 축 있으면 재계획 신호 (통과 도장 금지).

## 4. 구현 분담
- 클차장 (직접): 본 설계 + collector·verifier·page-planner·designer·qa-reviewer md 갱신 — 완료 시 §5 체크.
- 코과장 (R4 배치): 1b·2 게이트 + 테스트 + 데모(tone=report 미니 spec으로 THIN/COMPOSITION 위반 재현·통과 케이스).
- 실증 (클차장): R4 완료 후 **파이프라인 처음부터 재실행** (spec 손편집 없이) — 에이전트가 스스로 새 문법으로 판을 짜는지가 진짜 시험. 이게 후추님 질문("왜 못 넘어서나")의 검증선.

## 5. 상태
- [x] 설계 (7/7)
- [x] 에이전트 md 5종 갱신 (7/7 클차장)
- [ ] 게이트 코드 (코과장 R4)
- [ ] 풀 파이프라인 재실행 실증
