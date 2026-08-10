# TickDeck 조판 알고리즘 설계 (LAYOUT_ALGORITHM v1)

> 2026-08-10. 8/9~10 리에종 3부작 런(26장·26장·41장)에서 "알고리즘이 없다·들쑥날쑥하다"는 실무자 평가를 받은 뒤, 사람이 수습하던 조판 판단을 결정론 알고리즘으로 옮기는 설계 문서.
> 모든 높이 상수는 이 문서 작성 시점에 render_deck.py 실제 렌더를 headless Chrome으로 측정해 뽑았다(측정 절차는 §3-A.5). 추측 상수 없음.
> 구현 전 설계 문서다. 의사코드까지 내려가되 코드 반영은 별도 작업.

---

## 1. 왜 필요한가 (8/9~10 실측 증거)

| # | 실패 | 실측 수치 |
|---|---|---|
| 1 | 페이지 넘침을 렌더 후에야 발견 | 3번 덱 원안 28장 중 15장 세로 넘침 → 사람이 나눠 41장. 검증 재현: 사람이 나눈 페이지 11묶음을 다시 합쳐 렌더하니 10장이 실측 넘침(body 545~1131px vs 용량 517~531px) |
| 2 | 렌더러에 없는 블록을 디자이너가 발명 | 3번 덱 원안에서 미지원 블록 50건 실측(lead 18·table 11·stat_cards 4·cards 4·chart 3·split 3·period_banner 2·part_no 2·index_list 1·funnel 1·stepper 1). 3개 런 합계 63건을 사람이 손 변환. 렌더러는 `_render_block`에서 raise로 죽음 |
| 3 | 제목과 리드가 같은 문장 | 3개 런에서 23곳 (납품 전 사람이 수정) |
| 4 | 간지 파트 번호 오기 | 1부 간지에 "PART Ⅲ". 원인 실측: `_divider_part_meta`가 part_index 없으면 본문 키워드("설정/증거/행동") 매칭, 그것도 없으면 `min(3, page_number)` 폴백. 1번째 간지가 3페이지 이후면 Ⅲ이 찍힌다 |
| 5 | 런마다 디자인을 새로 고름 | meta.design_dna·테마 선택이 매 런 자유 서술. 또한 미지 레이아웃(comparison_table·funnel 등)이 렌더러에서 조용히 기본 세로 스택으로 폴백되어 의도와 다른 화면이 소리 없이 나감 (3번 덱 최종본에 7장) |
| 6 | 단위 중복·화면 요소 인쇄 노출 | "5건건"(본문에 단위 재타이핑) / PREV·NEXT가 PDF에 찍힘(8/9 no-print로 코드 수정 완료, 회귀 감시는 없음) |

밀도 통계(3런): 페이지당 블록 3.7~7.7개, 글자 수 평균 103~151자, 최대 425자. 한 런 8시간 중 대부분이 위 실수 되돌리기였다(_defect_ledger 8/9~10 항목).

---

## 2. 알고리즘 전체 그림

원칙: **렌더는 마지막 안전망이고, 판정은 전부 렌더 전에 끝난다.** 같은 spec이면 같은 판정(순수 함수 + 보정 상수 파일, 랜덤·LLM 판단 없음).

```
page-plan (05_page_plan.json)
  │
  ▼
designer가 06_deck_spec 초안 작성
  │
  ▼
[게이트 1] 어휘 게이트 (§E)         : 미지 블록·미지 레이아웃 = 즉시 반려 (spec 파일 강등)
[게이트 2] 자동 채움 (§F)           : 간지 번호·파트 수·페이지 번호 등 손 값 무시하고 계산
[게이트 3] 조판 예산 판정 (§A·§B)   : 페이지별 예측 높이 H vs 용량 C. 결정론.
     ├─ H > C-50        → [게이트 4] 분할/압축 지시 (§C) → 재판정 (최대 2회, 그래도 실패 = 사람)
     └─ H < C-240       → SPARSE 경고 → 병합 후보 제시
[게이트 5] 역할 중복 검출 (§D)      : 제목=리드, callout=body 문장 재사용
[게이트 6] 기존 계약 C1~C11 일괄 (run_contracts.py)
  │  (여기까지 전부 렌더 없이 spec JSON만으로)
  ▼
render_deck.py → capture_deck.sh FIT 실측
  │
  ▼
[사후 대조] FIT 실측 결과 vs 게이트 3 예측 → 불일치 로그 = 보정 상수 재측정 신호 (§G)
```

게이트 1~5는 신설 `spec_gate.py` 하나가 수행한다. 통과 전에는 `06_deck_spec.json`이라는 파일명을 얻지 못한다(§E.2).

---

## 3. 규칙 상세 (A~G)

### A. 용량 모델: 렌더 없이 페이지 높이를 예측한다

#### A.1 페이지 용량 C (실측)

측정 기준: `.body`의 clientHeight(콘텐츠 + 상20/하8 패딩 포함). editorial 테마·1280x720·Pretendard.

| 조건 | 용량 C (px) |
|---|---|
| title_band 크롬 (기본) | **529** |
| 크롬 없음·제목 1줄 | 531 |
| 크롬 없음·eyebrow 있음 | -14 |
| 크롬 없음·제목 2줄 (h1 44px x 1.18) | -52 |
| 출처행(citation 1개 이상) | **-13** |
| 각주행(footnote, 1개든 2개든 한 행) | **-22** |

판정 경계 2개:
- **넘침 판정: H > C - 50** 이면 반려. 50px는 실측한 모델 최대 과소예측(-50, A.4)을 덮는 안전마진.
- **과소 판정: H < C - 240** 이면 SPARSE(기존 FIT_SPARSE 임계 240 그대로 차용). 목표 밀도 대역 = [C-240, C-50].

#### A.2 글자 수 → 줄 수 (실측)

한국어 혼합 문장의 평균 글자폭은 폰트 크기의 0.750~0.756배로 측정됨(본문 18px에서 한 줄 75~80자 @ 980px). 보수 계수 0.78 사용:

```
cpl(width, font) = floor(width / (font * 0.78))      # 한 줄 글자 수
lines(chars, width, font) = max(1, ceil(chars / cpl))
```

보수 방향 오차: 문단당 최대 +1줄 과대예측(본문 기준 +28px). 과소예측은 안 나온다(스윕 13개 지점 전부 확인).

#### A.3 블록 높이 표 (전부 실측·editorial·전폭 1136px 기준)

| 블록 | 높이 공식 (px) | 위/아래 마진 | 실측 근거 |
|---|---|---|---|
| headline | 33.5 x lines(chars, 960, 24) | -8 / 4 | 1줄 34·2줄 67 |
| body | 28 x lines(chars, 980, 18) | 18 / 18 | 1~6줄 = 28·56·84·112·140·168 |
| callout / note | 36 + 30 x lines(chars, 972, 20) | 14 / 0 | 1~4줄 = 66·96·126·156 |
| callout(emphasis) | 44 + 45 x lines(chars, 968, 30) | 14 / 0 | 2줄 = 134 |
| bullets | Σ항목[45 + 29 x (lines(chars, 940, 18) - 1)] - 16 | 0 / 0 | 1줄 항목 45/개·2줄 74/개·리스트 보정 -16 |
| metric (단독) | 172 | 0 / 0 | 170 실측 + 반올림 |
| metric_grid | 행수 x 행높이 + 20 x (행수-1). 행높이 = 205(4열) / 172(3열 이하). 열수 = min(n, 4) | 0 / 0 | 2~3개 170·4개 202·6개 392 |
| text_table (5행 이하) | 37(제목 있으면) + 40 + Σ행[38.5 + 20 x (셀최대줄수-1)] | 0 / 0 | 3행 190·5행 267 |
| text_table compact (6~8행) | 30(제목) + 35 + 33 x 행수 (+셀 랩 20/줄) | 0 / 0 | 6행 263·8행 329 |
| text_table dense (9행 이상) | 28(제목) + 32 + 28.3 x 행수 (+셀 랩 20/줄) | 0 / 0 | 9행 315·12행 400 |
| viz | 종류별 표 A.3b + split 칸에서는 x0.72 | 8 / 6 | 아래 표 |
| citation / footnote / eyebrow | 본문 0 (용량 차감으로만 반영) | - | A.1 |
| 블록 사이 간격 | **24** (flex gap) + 인접 마진 (겹침 없음, flex라 마진 상쇄 안 됨) | | |
| body 패딩 | 상 20 + 하 8 = 28 (C에 이미 포함) | | |

셀 줄 수: `lines(cell_chars, 열폭-16, 13.5)` (compact/dense는 13). 열폭 = (1080 - 24) / 열수.

#### A.3b viz 종류별 높이 (전폭·제목 포함·기본 계열 수에서 실측)

| chart | 높이 | chart | 높이 | chart | 높이 |
|---|---|---|---|---|---|
| causal_chain | 164 | funnel | 215 | quarterly_bars | 274 |
| flow | 171 | shift | 220 | data_table | 278 |
| big_number | 178 | progress_bar | 225 | gap_map | 288 |
| arrow_flow | 188 | timeline_bars | 233 | donut | 301 |
| before_after | 191 | radial_progress | 233 | pyramid | 306 |
| dumbbell | 204 | mirror_bars | 235 | multi_line | 320 |
|  |  | gauge | 245 | hub_cycle | 338 |
|  |  | rising_columns | 258 | pictogram | 393 |
|  |  |  |  | two_by_two | 397 |

- 미측정 종류(gantt·fin_table·swot_quad·tradeoff·hero 계열 등)와 계열 수가 늘어나는 행형 차트(dumbbell·progress_bar·gap_map 등)는 **기본값 400**(보수)으로 두고, A.5 보정 하네스로 계열 수 스윕까지 채운다.
- split 칸(497~542px)에서는 실측비 0.68(donut 301→205) 반올림 0.72 적용.

#### A.4 검증 결과 (오늘 실덱 3개 + 넘침 원형 재현)

프로토타입 예측기(위 공식 그대로)를 실덱에 돌려 headless Chrome 실측과 대조:

| 검증 | 결과 |
|---|---|
| 스택 계열 통과 페이지 43장 높이 오차 | 중앙값 +8px · p10 -19 · p90 +122 · 범위 [-50, +152] |
| **넘침 원형 11장** (run3에서 사람이 나눈 페이지를 다시 합쳐 렌더) | **10장 검출 · 놓침 0** · 1장은 실측도 용량과 일치(531/531)한 경계 통과 |
| 통과 페이지 57장(스택 계열+split) 오검출 | 9장 (16%) |
| 프로브 조합 4장 (넘침 2·통과 2) | 4/4 일치 |

오검출 원인 셋 다 규명됨: ① 미보정 viz 기본값(before_after·gap_map이 기본값으로 잡히던 시점 측정 포함) ② 블록 20개짜리 페이지의 반올림 누적 ③ split 칸 배분 근사. ①은 A.3b 전수 보정으로 해소, 잔여 오검출의 비용은 "안 나눠도 될 페이지를 조금 가볍게 조판"이므로 안전 방향.

#### A.5 보정 상수는 코드가 아니라 측정 산출물이다

- 상수는 `deck-harness/scripts/layout_calibration.json`(신설)에 산다. 손으로 고치지 않는다.
- 신설 `calibrate_layout.py`가 프로브 덱(블록 1종씩 격리한 74장 + viz 스윕)을 render_deck.py로 렌더 → headless Chrome으로 offsetHeight 측정 → JSON 재생성. (이번 측정에 쓴 스크래치 하네스를 정식 이식.)
- calibration JSON에 **render_deck.py 내장 CSS의 해시**를 같이 기록한다. spec_gate 실행 시 해시 불일치 = "CSS가 바뀌었는데 재보정 안 함" → 게이트 실패. 렌더러를 고치면 보정도 다시 돈다. 이게 상수 썩음 방지 장치다.

### B. 배치 규칙

#### B.1 페이지 예산 (조합 상한의 SoT)

금지 조합을 표로 열거하지 않는다. **판정은 언제나 Σ(블록 높이+마진+갭) ≤ C-50 하나다.** 아래는 그 예산에서 도출되는 대표 상한(디자이너 감각용 참고표, 529px 기준):

- 리드 1 + 본문 4줄 + 표 5행(1줄 셀) + note 2줄 ≈ 30+24+148+24+267 = 493 → 통과 상한선
- 리드 1 + viz(donut) + 본문 2줄 + note ≈ 30+24+315+24+80+24+96 → 넘침. viz 페이지에 본문은 2줄·note 없이가 상한
- text_table 6행+ 와 viz 는 한 페이지 동거 불가 (263+204+갭만으로 예산의 94%)
- callout(emphasis)은 리드+본문 3줄까지만 동반 가능
- metric_grid 5개 이상(2행) + viz 동거 불가

#### B.2 블록 동거 금지 (예산과 무관한 문법 규칙)

1. `headline` 페이지당 1개 (2개째부터 반려. 오늘 raw spec에 다수)
2. `callout(emphasis)` 페이지당 1개
3. `note` 페이지당 1개 (렌더러가 하단 전폭 1행으로 빼는 구조라 2개째는 갈 곳이 없음)
4. `viz` 페이지당 1개 (stack의 가로 행 문법 예외: metric과의 행 묶음은 허용)
5. eyebrow·citation·footnote는 본문 흐름 블록이 아니다: 위치 지정 금지, 존재만 선언

#### B.3 좌우 분할(split)이 필요한 조건 (결정론)

split은 디자이너 취향이 아니라 판정 결과다:

```
split_required(page):
  H_stack = 세로 스택 예측 높이
  if H_stack <= C-50: return NO          # 세로로 들어가면 나누지 않는다
  좌우 후보 = 본문 흐름 블록 중 [viz|metric_grid|text_table(4행 이하)] 1개
             + 텍스트 블록 묶음
  if 후보 구조 불가: return NO → §C 분할로
  H_left  = 비주얼 칸 높이 (497px 폭 기준)
  H_right = 텍스트 칸 높이 (542px 폭 기준)
  if max(H_left, H_right) + 리드 + note행 <= C-50
     and |H_left - H_right| <= 160:      # 절반 여백 재발 방지 (7/26 결함 원장 "세로 균형일 때만")
     return YES
  return NO → §C 분할로
```

stack 레이아웃의 행 묶음 문법(렌더러 `_render_stack` 미러): 첫 비주얼은 전폭, 이후 연속된 metric·viz는 가로 한 행(높이 = max), 문단류는 각자 전폭. 예측기도 같은 문법으로 계산한다(이 미러 반영으로 오검출 16장 → 9장).

### C. 분할 규칙: 넘치면 어떻게 나누는가

#### C.1 분할 전 판단 순서 (결정론 캐스케이드)

```
overflow_resolve(page):                     # H > C-50 인 페이지
  1. 기계 압축 시도 (콘텐츠 무손실 변환만):
     a. text_table 4~5행이면 compact 티어 강제      # -5.5px/행
     b. viz가 있고 split_required가 YES면 split 전환
     c. 표 제목이 short_title과 중복이면 표 제목 제거  # -37px, §D 검출과 연동
  2. 초과분 D = H - (C-50) 계산 후:
     if D <= 60 and 분할하면 뒷장이 SPARSE가 될 때:
        → 분할 금지. "압축 지시"를 반환: 어느 블록에서 몇 자(줄 x cpl)를
          줄여야 하는지 숫자로 산출해 designer(사람/에이전트)에게 돌려준다.
          조판기가 문장을 직접 줄이지 않는다 (콘텐츠 권한 침해 금지, C5 정신).
     else:
        → C.2 분할 실행
  3. 재판정. 2회 실패 = 사람 에스컬레이션 (자동 루프 무한 방지)
```

#### C.2 분할 알고리즘

- **원자 블록** (자르지 않음): viz·metric·metric_grid·callout·image
- **가분 블록** (내부 경계에서 자름): bullets(항목 경계)·text_table(행 경계, 헤더 반복, 양쪽 최소 3행)·연속 body 문단(문단 경계)
- 분할점 선택:

```
split_page(page):
  units = 블록을 가분 블록은 내부 단위로 전개한 순서열
  # 1차: 앞 페이지를 예산까지 greedy로 채움 (읽는 순서 보존, 재배열 금지)
  cut = 예산 내 최대 채움 지점 (단위 경계만)
  # 2차: 뒷 페이지 SPARSE 방지 밸런싱
  if H(뒤) < C-240:
      cut을 앞으로 이동하며 |H(앞) - H(뒤)| 최소화 (둘 다 예산 내 유지)
  # 리드 상속: headline은 앞 페이지에만. 뒤 페이지 리드는 만들지 않고 비움.
  # eyebrow·part 메타는 양쪽 동일 상속. citation은 해당 콘텐츠를 따라간다.
```

#### C.3 나뉜 페이지의 제목 ("(이어서)" 금지)

제목은 조판기 권한이 아니다. 규칙 둘 뿐:

1. **자연 키가 있으면 기계 생성**: 분할 단위에 순번·구분값이 있으면(표 첫 열이 "제안 N"류 순번, bullets가 번호 목록) 제목 = `원제 · 앞범위` / `원제 · 뒷범위` (예: "실행 제안 1~5" / "실행 제안 6~9"). 판별은 첫 열 값의 공통 접두 + 숫자 패턴 정규식으로.
2. **자연 키가 없으면 page-planner로 반환**: 분할 결과(페이지 2장의 블록 구성)를 첨부해 Loop B로 제목 재발행을 요청한다. 기존 계약 C5가 Loop B 사유로 "space·density·overflow·과밀·잘림"을 이미 허용하므로 충돌 없음. 조판기가 임의 접미사("이어서"·"계속"·"2")를 붙이는 것을 금지 규칙으로 명시.

### D. 역할 분리: 같은 말이 두 번 나오지 않게

#### D.1 슬롯 정의 (계약 문서화)

| 슬롯 | 담는 것 | 형태 규칙 |
|---|---|---|
| short_title (밴드 제목) | 주제. "무엇에 대한 페이지인가" | 명사구·72자 이내(기존 TITLE_BAND_MAX_CHARS) |
| headline (리드) | 판단. "이 페이지가 주장하는 한 문장" | 서술형 1문장. 제목의 재서술 금지 |
| body | 근거·전개 | 리드 문장 복붙 금지 |
| callout | 독자가 가져갈 결론 1개 | body 문장 재사용 금지 |
| note | 단서·한계·주의 | "단," 꼴. 결론 재탕 금지 |
| footnote | 용어 풀이 | 본문 주장 금지 |
| eyebrow | 섹션 라벨 | 12자 이내 라벨 |

#### D.2 기계 검출 (신설 계약 C13)

```
normalize(s) = 공백·구두점 제거, 소문자화
dup_check(page):
  T = normalize(short_title); H = normalize(headline.text)
  1. T == H or T in H or H in T           → 위반 (오늘 23곳 유형)
  2. bigram_jaccard(T, H) >= 0.6          → 위반 (부분 재서술)
  3. normalize(callout) 가 body 문장(마침표 분리) normalize 집합과 일치 → 위반
  4. text_table.title 이 T와 1·2 기준 중복  → 위반 (C.1의 압축과 연동: 제거 지시)
```

문자 2-gram 자카드는 조사 차이("시장의 크기"/"시장 크기")를 잡기 위한 선택. 임계 0.6은 시작값이며 실덱 23곳 표본으로 재조정한다(오탐 나면 0.7로).

### E. 블록 어휘 강제: 발명 블록이 렌더러에 도달하지 못하게

오늘의 진실: 어휘 계약(C6)은 **이미 있었다**. 미지원 블록 50건이 렌더러까지 간 이유는 검증 실행이 선택 사항이었고, 심지어 미지 레이아웃은 렌더러가 조용히 기본 스택으로 폴백해 계약 위반이 화면 붕괴 없이 납품됐기 때문이다(3번 덱 최종본의 comparison_table 5장·funnel 2장은 지금도 C6 레이아웃 검사를 통과 못 한다). 그래서 시점과 실패 동작을 바꾼다:

1. **스키마 파일 제공**: `deck_spec.schema.json`(신설, JSON Schema). 블록 type enum = 렌더러 `SUPPORTED_CONTENT_BLOCK_TYPES` 13종(+별칭), layout enum = `SUPPORTED_LAYOUTS`. designer가 작성 중 자가검증.
2. **저장 게이트**: designer 산출물은 `06_deck_spec.draft.json`으로만 저장 가능. `spec_gate.py` 통과 시에만 `06_deck_spec.json`으로 승격되고, 실패하면 `06_deck_spec.rejected.json` + 위반 목록(블록 경로·이유·가까운 지원 블록 힌트). 파이프라인 다음 단계(render·capture)는 `06_deck_spec.json`만 읽으므로 게이트 우회가 구조적으로 불가능하다.
3. **힌트는 제안, 변환은 금지**: lead→headline, table→text_table, stat_cards/cards→metric_grid, chart→viz, index_list→index 레이아웃, part_no/period_banner→divider 페이지 필드, split/stepper/funnel(블록)→같은 이름 레이아웃 또는 viz. 자동 변환하면 콘텐츠 권한이 무너지므로 게이트는 힌트만 출력하고 designer가 고친다.
4. **렌더러 폴백 제거**: `_render_layout_body`의 "미지 레이아웃 = 기본 스택" 폴백을 raise로 교체. 조용한 폴백이 실패 5(들쑥날쑥)의 한 축이었다. 블록 쪽 raise는 지금처럼 유지(최후 방어).
5. 계약 문서 불일치 수정: harness-contracts SKILL.md의 C6 블록 목록에 viz·text_table·image·footnote가 빠져 있다(코드 frozenset이 SoT). 문서를 코드에 맞춘다.

### F. 자동 계산 대상 (사람·디자이너가 손대면 안 되는 값)

| 값 | 계산 규칙 | 현재 결함 |
|---|---|---|
| 간지 part_index | 간지(divider) 페이지의 등장 서수. 1번째 간지 = 1 | 키워드("설정/증거/행동") 매칭 + page_number 폴백 → "1부에 PART Ⅲ" 사고. **폴백 로직 삭제** |
| part_count | 간지 수 (렌더러에 이미 divider_n 계산 있음. spec 값 우선 로직을 제거하고 계산값 단독) | spec 손 값이 우선됨 |
| part_label | page-plan 파트 제목에서 온다 (콘텐츠 권한). 단 간지 서수와의 대응은 게이트가 검사 | |
| 페이지 번호·러닝헤드 분수 | 렌더러 계산 유지 | 정상 |
| 목차(index) 항목·번호 | divider·본문 페이지에서 생성. spec에 손으로 쓴 목차 리스트 금지 | 손 작성 |
| 출처행·근거 수 집계 | registry 기반 유지 (C6) | 정상 |
| 수치 + 단위 | 단위는 registry의 unit만. 본문에서 `{{metric_id}}` 토큰 직후에 단위 문자(%·건·명·원·조 등)가 붙으면 위반 → "5건건" 차단 | 검출 없음 |
| 화면 전용 요소 (PREV/NEXT 등) | `.no-print` 클래스 목록을 계약 상수로 두고, 캡처 시 @media print 숨김 여부를 자동 확인 | 8/9 수정됐지만 회귀 감시 없음 |

게이트 동작: spec에 이 값들이 손으로 들어 있으면 에러가 아니라 **계산값으로 덮어쓰고 WARN 1줄** (디자이너 재작업 왕복을 줄이기 위해. 단 계산값과 다르면 로그에 남아 회고로 간다).

### G. 검증 순서: 무엇을 언제 검사하는가

| 단계 | 시점 | 검사 | 도구 | 실패 동작 |
|---|---|---|---|---|
| 1 | spec 저장 시 | JSON 스키마·블록/레이아웃 어휘 (§E) | spec_gate.py | rejected 강등 |
| 2 | 〃 | 자동 계산 값 채움·덮어쓰기 (§F) | 〃 | WARN + 덮어쓰기 |
| 3 | 〃 | 조판 예산: 페이지별 H vs [C-240, C-50] (§A·§B) | 〃 (layout_budget.py 호출) | 분할/압축 지시 반환 (§C) |
| 4 | 〃 | 역할 중복 C13 (§D) | 〃 | rejected 강등 |
| 5 | 〃 | 기존 계약 C1~C11 | run_contracts.py | 기존과 동일 |
| 6 | 렌더 후 | FIT 실측 8종 (기존) | capture_deck.sh | 기존과 동일 (안전망) |
| 7 | 캡처 후 | **예측 vs 실측 대조 로그**: FIT 결과와 3단계 예측이 다르면(놓침 또는 과대 40px 이상) `fit_vs_pred.log` 기록 | capture_deck.sh 확장 | 누적 3건 = 재보정(calibrate_layout.py) 트리거 |
| 8 | 렌더러 CSS 변경 시 | calibration 해시 불일치 검출 (§A.5) | spec_gate.py | 게이트 실패 → 재보정 후 진행 |

지금 렌더 후에야 알던 것 중 1~4단계로 당겨지는 것: 넘침·과소밀도(3), 어휘 붕괴(1), 제목 중복(4), 간지 오기(2), 단위 중복(2). 렌더 후에만 알 수 있는 것으로 남는 것: 폰트·글리프 문제, SVG 라벨 겹침, 저대비 - 이건 FIT 실측 몫이 맞다.

---

## 4. 기존 시스템 수정 목록 (파일·함수 단위)

| 파일 | 수정 | 규모 |
|---|---|---|
| `deck-harness/scripts/layout_budget.py` **신설** | 용량 모델(§A)·배치 판정(§B)·분할 계산(§C.2)의 순수 함수. 입력 spec+calibration JSON → 페이지별 {H, C, verdict, 분할안/압축지시} | 이번 검증 프로토타입(predictor.py, 약 200줄)이 원형 |
| `deck-harness/scripts/spec_gate.py` **신설** | §G 1~5단계 오케스트레이션 + draft→정본 승격/강등 | 소형 |
| `deck-harness/scripts/calibrate_layout.py` **신설** | 프로브 덱 생성→렌더→Chrome 측정→`layout_calibration.json` 재생성 + CSS 해시 기록 | 이번 측정 하네스(gen_probe.py+measure.sh) 이식 |
| `deck-harness/scripts/render_deck.py` | ① `_divider_part_meta`: 키워드·page_number 폴백 삭제, 간지 서수 계산으로 교체 ② `_divider_part_count`: spec 우선 제거 ③ `_render_layout_body`: 미지 레이아웃 폴백 raise로 | 함수 3곳, 각 10줄 내 |
| `harness-contracts/scripts/contract_checks.py` | C13(역할 중복 §D.2)·metric 토큰 직후 단위 문자 검출(§F) 추가 | 검사 2개 |
| `harness-contracts/SKILL.md` | C6 블록 목록을 코드 frozenset에 맞춤 + C13 문서화 | 문서 |
| `deck-harness/scripts/capture_deck.sh` | FIT 결과를 `fit_report.json`으로 병행 출력 → 예측 대조 로그(§G 7) | 소형 |
| `deck_spec.schema.json` **신설** | §E.1 | 생성물 |
| designer.md·deck-harness SKILL.md | 워크플로 개정: draft 저장→게이트→(분할지시 수령 시) 제목은 page-planner Loop B | 문서 |

계약 충돌 판단:
- **C5 (design-first 금지·Loop B)**: 충돌 없음. 게이트가 넘침을 렌더 전에 알게 하므로 Loop B 횟수가 준다. 제목 재발행(§C.3)은 Loop B의 기존 허용 사유(overflow) 그대로.
- **C6 (콘텐츠 권한)**: 충돌 없음·강화. 단 SKILL.md 문서가 코드와 어긋나 있어 코드를 SoT로 문서 수정(§E.5).
- **SUPPORTED_LAYOUTS vs 렌더러 폴백**: 실질 충돌 발견. 계약은 comparison_table을 거부하는데 렌더러는 조용히 받아서 3번 덱이 계약 위반인 채 납품됨. **계약이 맞다** - 근거: 폴백 결과는 디자이너 의도(비교 표 전용 조판)와 다른 화면이고, 이런 무음 변형이 "알고리즘 없다" 평가의 한 축. 렌더러를 계약에 맞춘다(§E.4).

---

## 5. 이 알고리즘이 오늘 실패 6종을 막는 방식

| # | 실패 | 방어 | 실증 |
|---|---|---|---|
| 1 | 넘침 사후 발견·무규칙 분할 | §A 예측(렌더 전) + §C 분할 캐스케이드 | 사람이 나눈 11묶음 원형 복원 → 10/10 검출·놓침 0 (경계 1장은 실측도 통과) |
| 2 | 발명 블록 12종 63건 | §E 저장 게이트: rejected 강등이라 렌더러 도달 자체가 불가 | run3 raw spec이 게이트에서 50건 전부 잡힘 (C6 검사 존재 확인) |
| 3 | 제목=리드 23곳 | §D C13 완전일치+포함+자카드 0.6 | 검출 규칙이 오늘 23곳 유형(완전 일치) 전부 커버 |
| 4 | 1부 간지에 PART Ⅲ | §F 간지 서수 계산 + 폴백 삭제 + 손 값 덮어쓰기 | 원인 코드(`_divider_part_meta` 폴백) 특정 완료 |
| 5 | 런마다 디자인 새로 고름 | 부분 방어: 미지 레이아웃 무음 폴백 제거(§E.4)·밀도 대역 강제(§A.1)·보정 상수 고정(§A.5)으로 조판 일관성은 잡힌다. **색·타이포·테마 선택의 일관성은 이 문서 밖** - 테마 시스템·design_dna 고정이 별도 필요 | 폴백 7장 실측 |
| 6 | "5건건"·PREV/NEXT 인쇄 | §F 토큰 직후 단위 검출 + no-print 회귀 확인 | 원인 패턴 특정 완료 |

---

## 6. 한계와 사람이 판단해야 할 것

**모델의 한계 (숨기지 않는다):**
- 상수는 editorial 테마·title_band 크롬·Pretendard·현행 CSS에 묶여 있다. 다른 테마(dark_premium 등)·크롬은 같은 프로브로 별도 보정해야 한다. CSS 해시 게이트(§A.5)가 무보정 사용을 막는다.
- 통과 페이지 오검출 16%(9/57): 페이지가 필요보다 가볍게 조판되는 안전 방향 비용. viz 전수 보정 후 재측정해야 하며 0이 되지는 않는다(글줄 ±1 오차는 구조적).
- 그리드 계열 레이아웃(dashboard·matrix·scenario_cards·magazine_spread·split_status·mosaic_tiles·stepper 세부)은 v1 모델 미보정: 현재 예측이 +99~+649px 과대라 쓸 수 없다. v1 적용 대상 = 스택 계열(statement·stack·cards·timeline·metric_grid·hero_metric 등) + split (오늘 3런 본문 페이지의 78%). 그리드 계열은 같은 절차로 2차 보정.
- 행형 차트의 계열 수 스케일링 미측정(기본 계열 수에서만). 보정 스윕 전까지 기본값 400 보수 적용.
- 줄 수 예측은 평균 글자폭 모델이라 문단당 ±1줄. 안전마진 50px가 흡수하지만, 라틴 문자 비중이 큰 덱(영문판)은 계수 재측정 필요.

**사람(또는 상위 에이전트)이 계속 판단하는 것:**
1. 압축 지시("p07 body에서 56자 축소")를 받았을 때 실제로 어느 문장을 줄일지 - 조판기는 숫자만 안다.
2. 자연 키 없는 분할의 제목 - page-planner 권한 (§C.3).
3. SPARSE 페이지의 병합 여부 - 여백이 의도(간지 직후 진술 페이지)인지 결함인지.
4. 분할점의 의미 적합성 최종 확인 - 기계는 블록 경계만 알고 논리 단위는 모른다. 단 확인 비용은 "덱 전체 수습"에서 "분할 제안 검토"로 준다.
5. 새 블록·차트 어휘를 추가할지 - 어휘 확장은 렌더러+계약+보정 3종 세트 갱신이며 결정은 사람 몫.

**측정 재현 커맨드** (이번 측정과 동일 절차):

```bash
# 프로브 렌더 → 측정 → 상수 추출 (calibrate_layout.py로 이식 예정)
python render_deck.py probe_spec.json probe_registry.json -o probe.html
# probe.html에 측정 JS 주입 후:
"Google Chrome" --headless=new --virtual-time-budget=8000 --dump-dom probe.__measure__.html
# .slide별 .body clientHeight/scrollHeight + 블록별 offsetHeight/margin 수집
```
