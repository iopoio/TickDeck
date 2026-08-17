# TickDeck 조판 알고리즘 설계 (LAYOUT_ALGORITHM v2)

> 2026-08-10 v2. v1은 4자 적대 리뷰(본부 코드 대조·코덱스 솔 울트라·제미나이·페이블)에서 "방향 유효·그대로 구현 금지" 판정을 받았다. v2는 치명 10건(C-01~C-10)·중요 9건(I-01~I-09)·참고 3건(R-01~R-03)과 제미나이 시각 리듬·페이블 실측·본부 자체 구멍 7건을 전부 반영한 개정이다.
> - v1 원문 백업 = `docs/LAYOUT_ALGORITHM.v1.md` · 리뷰 원문 = `_workspace/20260810_algo_review/`
> - **본문의 모든 산술 예시는 `_workspace/20260810_algo_review/v2_arithmetic_check.py` 실행 출력과 1:1 일치한다.** 불일치가 발견되면 문서 결함이다.
> - 이 문서는 여전히 구현 전 설계 문서다. 단 오늘 별도 구현 중인 소형 게이트 6개(§4.4)는 v2의 선행 부분집합이며, v2 구현은 그 위에 얹는다(재구현 금지).
> - 지적별 반영/기각 판정 전체 = 부록 B.

---

## 0. v2가 v1에서 고친 것 (요약)

| 부분 | v1 | v2 |
|---|---|---|
| 산술 | B.1 예시가 자기 공식과 모순(C-02) | 전 예시 파이썬 재검산·정오표 부록 A |
| 보정 상수 | CSS 해시 1개 키·미보정 무음 통과 | 8차원 키 + **키 미일치 = fail-closed**(렌더 실측 강제) |
| 측정 주장 | "10/10 검출·오검출은 안전 방향" | 측정이 editorial·820px 조건을 data_mono·656px 실덱에 오적용된 사실을 명시·검출률 주장 강등·재측정 계획 |
| 입력 | spec + calibration | spec + **registry** + calibration (치환 후 문자열 기준) |
| 게이트 경계 | draft 파일명 | **receipt 초크포인트** (모든 진입점 재검증) |
| 분할 | 종료 조건 없음·SPARSE는 경고 | terminal verdict 2종 + 롤백 + 고아 방지 |
| 덱 단위 | 없음 (28→41 팽창이 알고리즘상 정상) | 페이지 팽창율·SPARSE 비율·밀도 중앙값·시각 리듬 = 전부 반려 조건 |
| 의도 보존 | 없음 (chart→text 강등이 통과) | 페이지 수준 1:1 대응 + 강등 승인 필드 |
| 납품 판정 | FIT_OK = 사실상 납품 | **DELIVERY_OK 분리** + 이미지 PDF 납품 금지 |
| 재현성 | 검증 산출물 리포 밖 | 프로브·원시 측정·predictor 리포 보존 의무 |

---

## 1. 왜 필요한가 (8/9~10 실측 증거)

| # | 실패 | 실측 수치 |
|---|---|---|
| 1 | 페이지 넘침을 렌더 후에야 발견 | 3번 덱 원안 28장 중 15장 세로 넘침 → 사람이 나눠 41장. 사람이 나눈 11묶음을 재결합 렌더하니 10장이 실측 넘침 |
| 2 | 렌더러에 없는 블록을 디자이너가 발명 | 3개 런 합계 63건 손 변환. 렌더러는 `_render_block`에서 raise |
| 3 | 제목과 리드가 같은 문장 | 3개 런에서 23곳 |
| 4 | 간지 파트 번호 오기 | 1부 간지에 "PART 3" (`_divider_part_meta` 폴백 원인 특정) |
| 5 | 런마다 디자인을 새로 고름 + 미지 레이아웃 무음 폴백 | 3번 덱 최종본에 계약 위반 레이아웃 7장이 조용히 납품됨 |
| 6 | 단위 중복·화면 요소 인쇄 노출 | "5건건" / PREV·NEXT 인쇄 |

리뷰로 추가 확정된 사실(v1 이후):
- 최종 41장을 qa_ink로 전수 재측정하면 **40장이 잉크 6% 미만·중앙값 3.3%·최저 1.23%**인데 현행 게이트(임계 1%·항상 exit 0)는 INK_OK를 출력한다 (C-07·페이블 실측).
- plan 28장 → 최종 41장 = **+46.4% 팽창**, 최종 spec의 viz = **0개** (plan은 차트 3개 명시·C-08).
- 최종 41장에 run_contracts 재실행 시 **위반 94건** 상태로 납품됐다 (C-09).
- v1 공식을 1번 덱 실물에 적용하면 통과 페이지 p17을 +169px, p24를 +83.5px 과대예측해 REJECT한다 (C-01). 넘침을 막으려던 판정이 오검출로 페이지 팽창을 스스로 유발하는 구조였다.

---

## 2. 알고리즘 전체 그림

원칙 (v1에서 축소·명확화):

1. **높이·배치 판정은 순수 함수다.** 같은 (spec, registry, calibration, 렌더러 버전)이면 같은 판정. 랜덤·LLM 판단 없음.
2. **파이프라인 전체가 결정론이라고는 주장하지 않는다** (I-07 반영). Loop B 산출물(분할 제목 재발행·압축 문장)은 LLM 산출이다. 채택되는 순간 spec에 들어가 receipt 해시에 고정되는 "승인된 입력"으로 다룬다. 결정론 선언의 범위는 판정 함수까지다.
3. **경계는 파일명이 아니라 receipt다** (C-04 반영·v1 "파일명을 얻지 못하므로 우회 불가" 서술 폐기). render·capture·export 모든 진입점이 receipt를 재검증한다(§G).

```
page-plan (05_page_plan.json · visual_intent 필드 포함)
  |
  v
designer가 06_deck_spec.draft.json 작성 (registry 치환 전 토큰 포함)
  |
  v
[게이트 1] 어휘 게이트 (§E)        : 미지 블록·레이아웃 = 반려
[게이트 2] 자동 채움 (§F)          : 간지 번호·파트 수 등 계산값 덮어쓰기
[게이트 3] 조판 예산 판정 (§A·§B)  : 페이지별 H vs C. 입력 = spec+registry+calibration.
     |                              미보정 키 = fail-closed(렌더 실측 경로로 강등)
     +- H > C-50  → [게이트 4] 분할/압축 캐스케이드 (§C.1) → 재판정 최대 2회
     +- H < C-240 → SPARSE 표시 → 덱 게이트 입력 (§C.5. 경고로 끝나지 않는다)
[게이트 5] 역할 중복 C13 (§D) · 의도 보존 (§E.6)
[게이트 6] 덱 단위 게이트 (§C.5)   : 팽창율·SPARSE 비율·밀도·시각 리듬 = 반려 조건
[게이트 7] 기존 계약 일괄 (run_contracts --spec draft 경로)
  |   (여기까지 렌더 없음. 단 HTML 의존 검사 C6/C9는 N/A로 명시 skip 후 렌더 뒤 재실행 §G.3)
  v
spec_gate: draft → 06_deck_spec.json 원자적 승격 + gate receipt 발급 (§G.1)
  |
  v
render_deck.py (receipt 검증) → capture_deck.sh (receipt 대조·FIT 실측·exit 전파)
  |
  v
[사후 대조] FIT vs 예측 불일치 로그 → 재보정 트리거 (§G.4 7단계)
  |
  v
[납품 판정] DELIVERY_OK (§G.4 9단계) : FIT_OVERFLOW_OK와 별개. 실패 = 납품 폴더 복사 차단
```

---

## 3. 규칙 상세 (A~H)

### A. 용량 모델: 렌더 없이 페이지 높이를 예측한다

#### A.0 입력 정의 (신설 · C-03·I-02 반영)

높이 계산의 입력은 **(spec, registry, calibration)** 세 개다.

- 모든 문자열 길이는 `{{metric_id}}` 토큰과 단위를 registry로 **치환한 뒤의 최종 문자열** 기준으로 잰다. 토큰 원문 길이로 재면 표 셀 wrap·본문 줄 수가 전부 틀린다.
- source-row 높이는 고정 차감이 아니라 **실제 표시 문자열**(최대 4개 publisher·title 연결·wrap 허용) 기준 줄 수 모델로 계산한다. citation이 카드별 출처로 처리되어 source-row 자체가 생략되는 렌더 분기(`render_deck.py:700-703`)도 모델에 반영한다.
- footnote도 항목별 실제 길이 기반. v1의 "1개든 2개든 -22" 고정 상수는 폐기한다.
- `image` 블록은 높이 공식이 없다. **image가 있는 페이지 = fail-closed**(판정 불가·렌더 실측 경로). 비율·object-fit 모델이 보정되기 전까지 무음 통과 금지.

#### A.1 페이지 용량 C (앵커 값 · 측정 조건 명시)

측정 조건: **editorial 테마·title_band 크롬·1280x720·Pretendard·2026-08-10 시점 CSS**. 이 조건 밖에서는 이 표를 쓰지 않는다(§A.5 fail-closed).

| 조건 | 용량 C (px) |
|---|---|
| title_band 크롬 (기본) | **529** |
| 크롬 없음·제목 1줄 | 531 |
| 크롬 없음·eyebrow 있음 | -14 |
| 크롬 없음·제목 2줄 | -52 |

정정 (C-01): v1은 "body 상20/하8 패딩이 C에 포함"이라고 썼으나 **title_band는 padding-top:0으로 덮는다**(`render_deck.py:4835-4836`). C 값 자체는 실측이므로 유지하되, 패딩 서술은 삭제한다. C는 상수가 아니라 **차원 키의 함수**이며 calibration 파일에서 읽는다.

source-row·footnote 고정 차감(-13/-22)은 폐기 → A.0의 문자열 기반 모델로 이동.

판정 경계 2개 (유지):
- **넘침: H > C - 50** 반려. 50px 안전마진.
- **과소: H < C - 240** = SPARSE. v2에서 SPARSE는 경고가 아니라 **덱 게이트(§C.5)의 반려 조건 입력**이다.

#### A.2 글자 수 → 줄 수

```
cpl(width, font) = floor(width / (font * 0.78))
lines(chars, width, font) = max(1, ceil(chars / cpl))
```

- 정정 (I-03): v1의 "본문 980px·18px에서 75~80자" 서술은 자기 공식(cpl=69)과 불일치했다. 서술을 삭제하고 **공식이 SoT**다.
- 한계 명시: `word-break: keep-all` 아래에서는 글자 수가 같아도 단어 길이·라틴/숫자 비중에 따라 줄바꿈이 달라진다. 문단당 +-1줄 오차는 구조적이며 안전마진 50px가 흡수 대상이다. 라틴 비중 큰 덱은 계수 재측정 필요.
- bullets 정정 (I-03): v1 상수는 font18·width940으로 측정했으나 실제 CSS는 **font20·max-width980·line-height1.45**다. bullets 행은 **재보정 전까지 fail-closed**.

#### A.3 블록 높이 표 (앵커 지위 · editorial·프로브 폭 820px 조건)

v1 표를 유지하되 지위를 강등한다: 이 표는 "editorial 조건의 앵커 값"이며, 실덱 적용은 calibration 키가 일치할 때만 가능하다.

| 블록 | 높이 공식 (px) | 위/아래 마진 | 실측 앵커 |
|---|---|---|---|
| headline | 33.5 x lines(chars, 960, 24) | -8 / 4 | 1줄 34·2줄 67 |
| body | 28 x lines(chars, 980, 18) | 18 / 18 | 1~6줄 = 28~168 |
| callout / note | 36 + 30 x lines(chars, 972, 20) | 14 / 0 | 1~4줄 = 66~156 |
| callout(emphasis) | 44 + 45 x lines(chars, 968, 30) | 14 / 0 | 2줄 = 134 |
| bullets | **fail-closed (재보정 대기·I-03)** | - | v1 상수는 CSS와 불일치 |
| metric (단독) | 172 | 0 / 0 | 170 실측 |
| metric_grid | **교정 공식: 4개씩 행 구성. 4열 행 202·1~3열 행 170·행간 20** | 0 / 0 | 2~3개 170·4개 202·5~6개 392 (검산 [1]) |
| text_table (5행 이하) | 37(제목 있으면) + 40 + Σ행[38.5 + 20 x (셀최대줄수-1)] | 0 / 0 | 3행 190·5행 267. **공식은 +2.5px 균일 보수** (검산 [2]) |
| text_table compact (6~8행) | 30(제목) + 35 + 33 x 행수 (+셀 랩 20/줄) | 0 / 0 | 6행 263·8행 329 |
| text_table dense (9행 이상) | 28(제목) + 32 + 28.3 x 행수 (+셀 랩 20/줄) | 0 / 0 | 9행 315·12행 400 |
| viz | A.3b + split 칸 x0.72 | 8 / 6 | |
| image | **fail-closed (모델 없음·A.0)** | - | |
| 블록 사이 간격 | 24 (flex gap) + 인접 마진 | | |

- metric_grid 공식 교정 근거 (C-02): v1 공식 `행수 x 205 + 20`은 6개=430으로 자기 실측 예시 392와 모순이었다. 교정 공식은 앵커 3점(170/202/392)을 전부 재현한다.
- 셀 줄 수: `lines(치환 후 cell_chars, 열폭-16, 13.5)` (compact/dense는 13). 열폭 = (1080 - 24) / 열수.

#### A.3b viz 종류별 높이 (프로브 폭 820px 조건 · 폭 클래스가 보정 키 차원)

v1 수치표 유지 (donut 301·dumbbell 204·multi_line 320 등). 단:

- **이 표는 프로브 폭 820px에서 잰 값이다.** 실덱의 viz 실폭은 layout·테마에 따라 820/656/640px 등으로 달라지고(`render_deck.py:6059-6069, 6281`), SVG는 height:auto라 폭 차이가 그대로 높이 차이가 된다. 어제 사고의 p17 +169px 과대예측이 정확히 이것이다(C-01). **폭 클래스(width_class)는 calibration 키의 독립 차원이다.**
- v1의 "전폭 1136px 실측" 서술은 실제 렌더 폭과 달라 삭제.
- 미측정 종류·행형 차트의 계열 수 스케일링: v1의 "기본값 400 보수" **폐기** (C-03: 400은 상한 증명이 아니다). 미측정 조합 = fail-closed(렌더 실측 경로).

#### A.4 검증 결과 (정직 재기술)

**v1의 측정과 검증은 전부 editorial 테마·820px 프로브 폭 조건에서 수행됐고, 그 상수를 data_mono·656px(stack)·title_band 실덱에 오적용한 상태로 대조가 이뤄졌다.** 따라서 v1의 수치는 모델 일반 성능이 아니라 "그 조건 오적용 상태"의 결과다.

- 유지되는 관찰: 넘침 원형 11장 중 10장 검출·놓침 0. 단 과대예측 방향의 오적용 아래에서는 검출률이 유리하게 나온다. **일반 성능 주장으로 쓸 수 없다.**
- 폐기되는 해석: "오검출 16%는 안전 방향" (v1 §A.4·§6). 실물 반례 = p17 +169px·p24 +83.5px 거짓 overflow → 분할 지시 → 페이지 팽창. **오검출은 28→41 팽창의 입력이며 비용이다.**
- p25 반례 (C-06 실측): 높이가 예산 안이어도 좌/우 질문 묶음처럼 의미상 split이 필요한 페이지가 있다. 높이 판정은 split을 "금지"하지 않는다. B.3은 넘침 페이지의 split 전환 조건이고, 디자이너가 의미 근거로 선택한 split은 예산 판정만 받는다(v1 서술 보완).
- **재측정 계획 (구현 단계 1차 작업)**: theme x page_chrome x layout 폭 클래스 x 폰트 빌드 x 브라우저 메이저 차원별 프로브 재측정. 검출률·오검출률 주장은 재측정 후 원시 산출물과 함께(§H)만 재수립한다. 그 전까지 10/10은 "editorial 조건 한정 예비 결과"다.

#### A.5 보정 상수: 키 확장 + fail-closed (C-01·I-04)

- 상수는 `deck-harness/calibration/layout_calibration.json`에 산다. 손으로 고치지 않는다.
- **calibration 키 = {renderer_struct_hash, css_hash, theme, page_chrome, layout, width_class, font_build, browser_major}**
  - renderer_struct_hash = 레이아웃 관련 파이썬 함수(`_render_stack`·`_render_split`·SVG viewBox 계산·source-row 생성 등)의 소스 해시. CSS를 안 바꾸고 구조만 바꿔도 무효화된다(I-04).
- **키 미일치 = fail-closed.** 무음 skip 금지. 동작: 해당 페이지는 "판정 불가" verdict → **렌더 실측 판정 경로로 강등**(프로브 렌더 → FIT 결과가 판정을 대신). 파이프라인 정지가 아니라 느린 경로 강등이므로, CSS 1px 수정이 전체를 마비시키지 않는다(제미나이 지적 수용). grid 계열(dashboard·matrix 등 v1 미보정 +99~+649px)·bullets·image·미측정 viz가 전부 이 경로다.
- **이중 유지보수 지적(제미나이)에 대한 답 = 하이브리드.** 보정된 조합은 상수(빠른 경로: 렌더 없이 draft 반려 루프에 즉시 피드백), 미보정 조합은 실측(느린 경로). 전면 사전 렌더 전환은 기각한다. 근거: 게이트가 렌더 없이 도는 것이 designer 반려 루프의 핵심 가치이고, capture는 Chrome Abort trap 실사례(코덱스 재현)처럼 단일 의존이 위험하다.
- 재보정 트리거: 키 해시 변경 시 즉시 + fit_vs_pred 불일치 누적 3건. 누적 범위의 SoT = calibration JSON 안의 run 로그 필드(I-04의 "어느 run 범위인지 SoT 없음" 해소).

### B. 배치 규칙

#### B.1 페이지 예산 (전면 재계산 · 검산 스크립트 [3][4]와 일치)

판정은 언제나 **Σ(블록 높이+마진) + 24 x (블록 수-1) ≤ C-50** 하나다. 아래 대표 예시는 C=529·cutoff 479 기준이며 전부 파이썬 검산을 통과했다:

- 리드 1 + 본문 4줄 + 표 5행(1줄 셀·표 제목 없음) = **458 → 통과 (여유 21)**. 표 제목을 붙이면 495 → 넘침 +16. 여기에 note는 어떤 길이도 불가.
- 리드 1 + viz(donut) + 본문 1줄 = **456.5 → 통과 (여유 22.5)**. 본문 2줄이면 484.5 → 넘침 +5.5. **donut 페이지의 상한은 본문 1줄·note 없음** (v1의 "본문 2줄 상한" 정정).
- text_table 6행(compact) + viz(dumbbell) = **505 = cutoff의 105.4% → 동거 불가** (v1 "예산의 94%"는 분모를 529로 쓴 오기).
- 리드 1 + callout(emphasis) 2줄 + 본문 7줄 = **457.5 → 통과**. 본문 8줄이면 485.5 → 넘침. 상한은 본문 7줄 (v1의 "3줄" 서술은 공식과 불일치한 과소 기재).
- metric_grid 5개 + 최소 viz(causal_chain 164) = **594 → 리드 없이도 넘침 = 동거 불가** (v1 주장 유지·수치만 재계산).

v1 예시 정오표 (C-02 재계산 재현·검산 [4]):
- v1 "리드+본문4줄+표5행+note2줄 = 493 통과" → 공식값 **629·넘침 +150** (note 110과 gap 1개 누락·표 값 오기)
- v1 "donut 예시 = 593" → 공식값 **618.5** (본문·note 마진 누락)

#### B.2 블록 동거 금지 (문법 규칙)

v1의 5개 규칙 유지 + 추가:

6. **본문 페이지는 headline 정확히 1개** (I-01: v1은 최대 1개만 검사·최소를 안 봤다. 실제 41장 덱은 headline 5개뿐이었다). 예외: `split_from` 필드가 있는 분할 뒷장만 0개 허용(§C.4).
7. **한 페이지의 `viz|text_table` + `metric|metric_grid` + `note` 동거는 반려**: 차트·표와 숫자 카드를 나누거나, note를 다음 장으로 옮긴다. 전 실덱 45개·본문 555장 중 39장(7.0%)이 해당했다.
8. **`viz|text_table` + `metric|metric_grid` 동거는 경고**: 전 실덱 45개·본문 555장 중 83장(15.0%)이 해당해 즉시 반려하면 기존 덱을 과도하게 막는다. 실제 과밀·겹침 결과를 누적한 뒤 승격 여부를 판단한다.

#### B.3 좌우 분할(split) 조건

v1 판정식 유지 + 후보 문법 확장 + 렌더러 미러 경고:

- 후보 확장: 좌우 후보 = 비주얼 1개(viz·metric_grid·text_table 4행 이하) + **나머지 블록 묶음(텍스트 또는 metric)**. v1은 텍스트 묶음만 허용해 viz+metric 조합의 해소 경로(§C.1 반례)를 막고 있었다.
- **렌더러 미러 경고 (C-10)**: 현행 `_render_split`은 의미 묶음이 아니라 블록 개수 중간점에서 자르고, `_render_stack`의 top 선택도 블록 type과 무관하다. **§4의 렌더러 수정(문법 일치)이 선행되지 않으면 이 절의 예측은 렌더와 어긋난다.** 예측기가 렌더러를 미러한다는 전제는 코드 수정으로만 성립한다.

#### B.4 차트 제목 3층 + 단위 1회 선언

`viz` 제목은 선택 필드 `exhibit`(눈썹) → 기존 `title`(결론 문장) → `subtitle`(측정 대상 + 단위)의 3층을 쓴다. 세 필드가 모두 있을 때만 3층으로 렌더하고, 없으면 기존 제목 렌더를 그대로 유지한다.

- 단위는 `subtitle`에서 한 번만 선언하고 개별 수치에는 단위 기호를 반복하지 않는다.
- `subtitle`이 없는 viz는 경고다. 전 실덱 45개에서 171개가 해당해 반려로 올리지 않는다.

### C. 분할·압축·밀도·리듬

#### C.0 분할 전 오토핏 검토 (제미나이 PPT 비교에 대한 결정)

**폰트 축소 오토핏(shrink-to-fit)은 기각한다.** 근거:
1. 위계 고정 계약과 충돌: 같은 위계 블록은 덱 전체에서 같은 크기여야 한다. 페이지별 미세 축소는 페이지 간 타이포 일관성을 깨 "들쑥날쑥"의 새 형태를 만든다. 이번 사고의 평가 축이 바로 그 일관성이다.
2. 축소 폭이 연속값이 되는 순간 높이 예측·보정 상수 체계 전체가 무너진다.

대신 **이산 압축 티어가 오토핏의 역할을 담당한다**: text_table compact/dense 강제·중복 표 제목 제거·note 축약 지시. 전부 이산 단계라 보정 가능하고 위계를 건드리지 않는다.

**고아 방지(orphans/widows)는 채택한다**: 분할 결과 가분 블록의 첫/마지막 1단위(본문 1줄·bullets 1항목·표 1행)만 떨어져 남는 cut 금지. cut을 1단위 이동해 회피하고, 회피 불가면 해 없음으로 처리한다.

#### C.1 분할 전 판단 순서 (terminal verdict 신설 · C-06)

```
overflow_resolve(page):                      # H > C-50 인 페이지
  0. max(원자 unit 높이) > C-50
       → TERMINAL: ATOM_OVERSIZE. 분할 시도 금지. designer/planner 반송
         (긴 callout 하나·거대 viz 하나가 예산 초과면 어떤 분할도 무의미)
  1. 무손실 기계 압축: compact 티어 강제 / 중복 표 제목 제거 (§D 연동)
  2. split 전환 평가 (B.3 확장 문법)
  3. 선형 분할 가능성 사전 검사: H - 24 < 2 x (C-240)
       → TERMINAL: NO_VALID_PARTITION (구조적으로 어느 cut이든 한쪽이 SPARSE)
         압축/재구성 지시와 함께 designer/planner 반송
  4. C.2 분할 실행 (고아 방지 포함). 유효 cut이 없으면(모든 cut에서
     한쪽 SPARSE 또는 재넘침) → TERMINAL: NO_VALID_PARTITION
  5. 재판정 최대 2회. 실패 → TERMINAL: ESCALATE_HUMAN

  TERMINAL 공통 롤백: 분할 부분 산출물 전부 폐기·원 페이지 원복.
  draft에 잔재를 남기지 않는다(전부 적용 또는 전무). C-06의 "2회 뒤
  부분 페이지를 폐기하는지 정의 없음" 해소.
```

**반례 처리 명시 (C-06의 viz400+metric172 · 검산 [5])**:
- H = 414 + 172 + 24 = 610 → D = 131 > 60 → 분할 경로.
- 유일 cut(viz | metric)의 뒷장 = 172 < 289 → 선형 분할 해 없음.
- 단계 2 split 전환: 좌 viz 400x0.72 = 288 ≤ 479, |288-172| = 116 ≤ 160 → **split YES. 반송 없이 해소.**
- split도 불가한 변형(viz560: |403.2-172| = 231.2 > 160) → **NO_VALID_PARTITION 반송.**
- 구조 불가 창 (검산 [6]): H가 (539, 602) 구간이면 분할 의무인데 어떤 cut도 한쪽이 SPARSE다. 단계 3의 사전 검사가 이 구간 전체를 TERMINAL 처리한다.

#### C.2 분할 알고리즘

v1 유지(원자/가분 구분·greedy + 뒷장 밸런싱) + 두 가지 추가:
- 고아 방지 규칙 적용 (C.0).
- 분할 산출물에 lineage 필드 기록 (C.4).

#### C.3 나뉜 페이지의 제목

v1 유지: 자연 키 있으면 기계 생성, 없으면 page-planner Loop B 반환. "(이어서)"류 접미사 금지. Loop B 산출물은 채택 시 spec에 반영되어 receipt 해시로 고정된다(§2 원칙 2·I-07).

#### C.4 split lineage와 ID 체계 (신설 · I-01)

- **page_id는 승격 시 전량 연번 재발급**(p01..pNN). `p02b`·`p15bb` 같은 suffix ID 금지 - `hybrid_brief.py`의 `int(pid[1:])`(18행)이 즉시 ValueError를 내는 실물 결함이다. 연번 재발급으로 근본 해소 + hybrid_brief 파싱도 방어적으로 수정(§4).
- 계보는 ID가 아니라 필드로: `plan_id`(plan 원본 페이지 id)·`split_from`(분할 원본 page_id)·`split_seq`(1..n)·`split_total`.
- 분배 규칙: citation은 뒷받침하는 블록을 따라간다(spec의 citation에 `refs` 필드 신설·블록 대응 명시). footnote·allowed_source_ids·allowed_metric_ids는 각 자식이 실제 사용하는 것만 상속(기존 C6 allowlist 검사가 그대로 검증).
- 분할 뒷장 headline 0 허용 조건 = `split_from` 존재 (B.2-6 연동).
- plan과의 1:1 추적: `plan_id`로 유지. Loop B가 제목을 다시 써도 계보 필드는 불변.

#### C.5 덱 단위 예산·시각 리듬 게이트 (신설 · C-07·제미나이)

페이지별 판정만 있으면 "빈 페이지 추가"가 넘침의 가장 쉬운 해가 된다(28→41이 알고리즘상 정상 결과였던 이유). 그래서 덱 단위 목적함수를 반려 조건으로 둔다. **전부 반려이지 경고가 아니다.** 본문 페이지 = cover·divider·closing·outro·index·source_appendix 제외.

| 게이트 | 조건 (위반 = 반려) | 수치 근거 |
|---|---|---|
| 페이지 팽창율 | 최종 페이지 수 > ceil(plan x 1.2) | 사고 덱 +46.4%. 오늘 선행 구현 C15와 동일 |
| SPARSE 비율 | H < C-240 인 본문 페이지 비율 > 20% | 사고 덱은 34/41 |
| 밀도 중앙값 (spec 시점) | 본문 H 중앙값 < C-240 | |
| 잉크 중앙값 (PDF 시점) | 본문 잉크 중앙값 < 4% 또는 잉크 2.5% 미만 페이지 > 30% | 사고 덱 중앙값 3.3%·최저 1.23%. 선행 구현 qa_ink 분포 게이트와 동일 |
| 연속 텍스트-온리 | 시각 블록(viz·metric·metric_grid·text_table) 없는 본문 페이지 **4장 연속** | 정상 1번 덱 실측 최대 연속 3장 |
| 시각 포함 비율 | 시각 블록 포함 본문 페이지 < 50% | 정상 1번 덱 실측 80% (16/20) |
| 정보량 편차 | 본문 페이지 글자 수(치환 후) 변동계수 > 0.65 → 초기 WARN, 실덱 3종 검증 후 반려 승격 | 정상 1번 덱 실측 0.45 (평균 397자·표준편차 177) |

- 수치의 지위: **정상이었던 1번 덱(26장·data_mono·2026-08-10 spec 분석)에서 도출한 초기값**이다. 기존 산출물 분석이지 새 프로브 측정이 아니다. 구현 시 정상 덱 표본을 넓혀 확정한다.
- 의도적 텍스트 덱(법률 요약 등)은 intake의 명시 플래그로 시각 비율 게이트만 면제(오탐 방지·페이블 제안 수용).

### D. 역할 분리 (같은 말이 두 번 나오지 않게)

v1의 슬롯 정의(D.1)·C13 검출(D.2) 유지. 확장 계획 (I-08):

- 1차 구현 = v1 범위(제목·리드·callout·표 제목). 임계 0.6은 실패 표본 23곳 + **negative set(정상 덱 2종 전 페이지)** 양쪽으로 재조정 - v1은 실패 표본만으로 정해 과탐 통제가 없었다.
- 2차 확장 = bullets 항목·table cell·note·강조 마크(`==`) 제거 후 문자열·metric 토큰 치환 후 문자열.
- **의미 유사(paraphrase) 검출은 기각**: 임베딩 판정은 결정론 원칙(§2-1) 위반이고 오탐 통제가 안 된다. 한계로 명시하고 사람 검토 몫으로 남긴다(§6).

### E. 블록 어휘 강제 + 의도 보존

v1의 E.1~E.4 유지(스키마 제공·저장 게이트·힌트만 제공·렌더러 폴백 제거). 개정·신설:

- **E.1 개정 (I-06)**: `deck_spec.schema.json`은 손으로 쓰지 않는다. `contract_checks.py`의 `SUPPORTED_CONTENT_BLOCK_TYPES`(20종 frozenset)·`SUPPORTED_LAYOUTS`가 SoT이고, 생성 스크립트가 schema를 뽑는다. 생성물 해시는 receipt에 포함되어 renderer/contract/schema 3중 drift를 막는다. 계약 번호 표기도 코드에 맞춘다: 현행은 C7 없음·C12 존재 (v1의 "C1~C11" 서술 정정).
- **E.4 구현 주의 (C-10·선행 게이트 6)**: `_render_layout_body`의 마지막 generic 분기는 unknown만이 아니라 지원 레이아웃(statement·timeline·stat_grid·metric_grid·cards)도 렌더한다. 단순 raise 교체는 정상 덱을 죽인다. **함수 진입부에서 `SUPPORTED_LAYOUTS` 미포함만 raise하고 generic 분기는 유지**한다. 오늘 선행 게이트 6이 정확히 이 형태로 구현 중이다.
- **E.6 의도 보존 게이트 (신설 · C-08)**: 스키마를 다 지키면서 chart를 body/text_table로 강등하는 의미 손실은 어휘 게이트가 못 잡는다(어제 viz 0개 사고의 실제 경로).
  - 덱 수준 (선행 구현 = C14): plan의 차트 의도 페이지 수 vs spec viz 총수. 하한 안전망.
  - **페이지 수준 (v2)**: page_plan 스키마에 `visual_intent` 필드 신설({intent: chart|table|none, desc}) → spec의 대응 페이지(`plan_id` 매칭·분할 자식은 묶어서)에 해당 시각 블록 존재 검사. 1:1 대응.
  - **의도적 강등 경로**: spec 페이지에 `visual_downgrade: {reason, approved_by, date}` 필드가 있을 때만 허용. 승인자는 후추님 또는 본부이되 **spec을 쓰는 에이전트 자신은 불가** (결정 1 "오케스트레이터 손 변환" 재발 방지). 필드 없이 강등 = 반려.

### F. 자동 계산 대상

v1 표 유지(간지 서수·part_count·목차·단위 중복·no-print 회귀). 수정 규모 정정 (I-05): divider 수정은 "함수 3곳 각 10줄"이 아니다. `_divider_part_meta`·`_divider_part_count`에는 덱 수준 컨텍스트(간지 등장 서수·전체 간지 수)가 아예 없어, 호출부 `_render_divider`·`_section_items`와 deck-level 계산·cover 전달 경로까지 함께 바꿔야 한다. §4 표에 반영.

### G. 게이트 구조: receipt 초크포인트 (C-04·C-05·C-09)

v1의 "통과 전에는 06_deck_spec.json 파일명을 얻지 못하므로 우회가 구조적으로 불가능" 서술은 **틀렸다**. 같은 에이전트가 쓰기 권한을 갖고, renderer CLI·Python API·capture·hybrid·pptx 전 진입점이 임의 파일을 받는다(C-04 실증: C6가 거부한 spec을 direct 호출로 렌더 성공). 경계를 재설계한다.

#### G.1 gate receipt

- spec_gate 통과 시 정본 승격과 함께 `06_deck_spec.receipt.json` 발급:
  `{spec_sha256, registry_sha256, calibration_sha256, renderer_struct_hash, css_hash, schema_hash, gate_results, issued_at}`
- 승격은 원자적: 임시 파일 → `os.replace`. 검사한 draft의 SHA와 승격되는 파일의 SHA 동일성 재확인. 실패 시 기존 정본 유지 + rejected 사본 격리. stale 정본을 남기지 않는다(C-05의 원자성 요구).

#### G.2 진입점 전수 목록과 수정 지점 (C-04)

| 진입점 | 현행 | v2 수정 |
|---|---|---|
| `render_deck.py` CLI main | 임의 경로 수용 | receipt 로드 → 4개 SHA 재계산 대조. 불일치/부재 = 산출 없이 exit. 예외는 `--unattested`뿐 |
| `render_deck()` Python API | 게이트 없음 | receipt 인자 의무. 없으면 unattested 모드(HTML meta에 UNATTESTED 표시 삽입) |
| `capture_deck.sh` | 임의 HTML 수용 | 렌더가 HTML meta에 receipt 해시 임베드 → capture가 대조. unattested HTML = PDF 파일명 `.unattested.pdf` 강제 |
| `hybrid_brief.py`·`hybrid_assemble.py` | 없음 | 정본+receipt 검증 후 진행 |
| `pptx_export.py` | 없음 | 동일 |
| `run_deck.sh` | PDF 부재 시 `ls \|\| echo`로 계속 | receipt·PDF 존재를 하드 실패로 |

- 정당한 무게이트 렌더(calibration 프로브·디버깅)는 `--unattested` 단일 경로로 수렴: 산출물이 스스로 미검증임을 표시하고, 납품 판정(G.4 9단계)이 걸러낸다. **몰래 우회는 불가능하고, 표시된 우회만 가능하다.**
- 한계 정직: 같은 프로세스가 파일 쓰기 권한을 가지므로 receipt 재계산 코드를 복제하는 결의된 위조까지 코드로 못 막는다. receipt의 목표는 실수·관성 우회 차단과 **우회 흔적 강제**다. 결의 위조 차단은 프로세스 규율(_defect_ledger 연동) 몫.

#### G.3 run_contracts 배선 (C-05)

- `run_contracts.py`에 `--spec <path>`(및 `--plan`) override 신설. 현행은 `06_deck_spec.json` 고정 로드(98행)라 draft를 검사할 수 없다.
- spec_gate는 draft 경로로 호출한다.
- HTML 의존 검사(C6 rendered 검사·C9)는 렌더 전 단계에서 **N/A로 명시 출력 후 skip**하고, 렌더 후 같은 runner를 재실행해 채운다. v1의 "여기까지 전부 렌더 없이 C1~C11" 서술은 이 시점 분리로 정정한다.

#### G.4 검증 순서 (v1 표 개정)

| 단계 | 시점 | 검사 | 실패 동작 |
|---|---|---|---|
| 1 | draft 저장 시 | 스키마·어휘 (§E) | rejected 강등 |
| 2 | 〃 | 자동 계산 값 (§F) | WARN + 덮어쓰기 |
| 3 | 〃 | 페이지별 조판 예산 (§A·§B) - 미보정 키는 fail-closed·렌더 실측 경로 | 분할/압축 캐스케이드 (§C.1) |
| 4 | 〃 | 역할 중복 C13 (§D) | rejected 강등 |
| 5 | 〃 | 의도 보존 (§E.6: C14 + 페이지 수준) | rejected 강등 |
| 6 | 〃 | 덱 게이트 (§C.5: C15 팽창율·SPARSE 비율·밀도·리듬) | rejected 강등 |
| 7 | 〃 | 기존 계약 (run_contracts --spec draft. HTML 의존분 N/A 명시) | rejected 강등 |
| 8 | 렌더+캡처 후 | FIT 실측 - **FIT_OVERFLOW는 exit 전파**(선행 게이트 4). `FIT_OK` 표기는 `FIT_OVERFLOW_OK`로 개명(R-03: 이름이 품질 통과로 오독되는 것 차단). fit_report.json 기록. 예측 대조 → 불일치 누적 3건 = 재보정 | 넘침 = 실패 exit·PDF는 디버깅용 표시 |
| 9 | 납품 직전 | **DELIVERY_OK 판정 (§G.5)** | 납품 폴더 복사 차단 |

#### G.5 납품 판정 DELIVERY_OK (C-09 · FIT과 분리)

FIT_OVERFLOW_OK는 "세로 넘침 없음" 한 가지 사실이다. 납품 판정은 별도 명령이 다음 전부를 요구한다:

1. receipt 유효 (spec·registry·calibration·렌더러 해시 4중 일치·unattested 산출물 부재)
2. 최종 spec에 run_contracts 재실행 위반 0건 (어제는 94건인 채 납품)
3. FIT overflow 0
4. 잉크 분포 게이트 통과 (§C.5)
5. 덱 게이트·의도 보존 통과
6. **PDF 텍스트 레이어: pdffonts 기준 임베드 폰트 1개 이상** (이미지 전용 PDF 기계 차단. 실측 근거: 사고 image PDF는 추출 텍스트 26B)
7. 전 장 시각 검토 기록: `pdftoppm -r 20` 저해상 몽타주 생성 + 검토자·시각을 `07_qa_report`에 기록 (표본 검토 금지)

**이미지 PDF 정책 (결정 4 후속·확정)**: 정식 납품물 = native PDF 단일. **이미지(래스터) PDF는 납품 금지.** 내부 검토용 폴백으로만 존재 가능하며 4조건 전부 충족해야 한다: ①파일명 `*.raster.pdf` 강제 ②manifest(승인자·사유·만료일) 동봉 - 승인자는 후추님 ③납품 폴더 반입 금지(위 6번이 기계 차단) ④만료일 경과 시 삭제. 검색 불가 산출물은 덱이 아니라 그림 묶음이다.

구현 위치는 `.claude/skills/deck-harness/scripts/delivery_gate.py`다. 런 폴더의 기존 산출물을 대상으로 아래처럼 실행하며, 일곱 결과를 기본값 `08_delivery_report.json`에 기록한다. 일곱 항목 중 하나라도 실패하면 exit 1이다. `capture_deck.sh`·`qa_ink.py`·`pdffonts`가 실제 PDF를 다시 검사하므로 이 명령은 화면 계열 도구를 실행할 수 있는 본부 환경에서 사용한다.

```bash
python3 .claude/skills/deck-harness/scripts/delivery_gate.py _workspace/<run_id>
# 출력 경로를 바꿀 때
python3 .claude/skills/deck-harness/scripts/delivery_gate.py _workspace/<run_id> --output /path/to/delivery_report.json
```

`07_qa_report.json`의 전 장 검토 기록은 `visual_review` 객체 안에 `reviewer`, `reviewed_at`, `montage_path`, `scope: "all_pages"`를 두고, `montage_path`가 가리키는 파일을 런 폴더에 보존한다. 몽타주 생성은 이 판정 명령의 책임이 아니다.

### H. 검증 산출물 보존·재현 (신설 · R-01·R-02)

- **보존 위치 = `deck-harness/calibration/`** (커밋 대상): `probe_specs/`(프로브 spec 전체)·`raw/`(원시 측정값: page id·측정 px·조건 키)·`layout_calibration.json`·`predictor.py`(판정 원형). v1의 검증 산출물(74장 프로브·13지점 스윕·predictor)은 리포 밖이라 10/10 주장이 재현 불가였다.
- **문서 규칙**: 검출률·오검출률 등 성능 주장은 원시 측정값·대상 page id·조건 키가 리포에 있을 때만 문서에 쓸 수 있다.
- **재현 커맨드 (R-02 반영)**: 현행 render main은 capture까지 강제하고 capture 실패 시 non-zero exit라, 프로브 HTML 생성이 capture 장애에 묶인다. **`--html-only` 플래그를 신설**하고 calibrate_layout.py는 이 경로만 쓴다.

```bash
python render_deck.py probe_spec.json probe_registry.json -o probe.html --html-only --unattested
# 이후 headless Chrome 측정 주입은 calibrate_layout.py가 수행
```

---

## 4. 기존 시스템 수정 목록 (재작성 · C-10·I-05·I-09 반영)

### 4.1 파일·함수 단위

| 파일 | 수정 | 비고 |
|---|---|---|
| `deck-harness/calibration/` **신설** | probe_specs·raw·layout_calibration.json·predictor.py 보존 (§H) | 커밋 대상 |
| `deck-harness/scripts/layout_budget.py` **신설** | §A~§C 순수 함수. **입력 = spec+registry+calibration** | |
| `deck-harness/scripts/spec_gate.py` **신설** | 게이트 1~7 오케스트레이션 + receipt 발급 + 원자적 승격 (§G.1) | |
| `deck-harness/scripts/calibrate_layout.py` **신설** | 차원 키별 프로브 스윕 → calibration 재생성 + raw 보존 | --html-only 경로 사용 |
| schema 생성 스크립트 **신설** | contract_checks frozenset(SoT) → deck_spec.schema.json + 해시 (§E.1·I-06) | 손 복제 금지 |
| `render_deck.py` | ① divider: `_divider_part_meta`·`_divider_part_count` + 호출부 `_render_divider`·`_section_items` + **deck 수준 컨텍스트 전달·cover 경로** (I-05 규모 정정) ② `_render_layout_body`: 진입부 SUPPORTED_LAYOUTS 검사 raise·generic 분기 유지 (C-10·선행 게이트 6) ③ `_render_text_table`: 4~5행 compact **강제 flag 신설** (현행은 6행부터 자동뿐이라 §C.1-1이 구현 불가였다) ④ `_render_split`·`_render_stack`: §B.3 문법과 일치시키는 수정 ⑤ receipt 검증 + `--html-only` + `--unattested` | |
| `contract_checks.py` | C13 (§D)·metric 토큰 직후 단위 검출 (§F)·E.6 페이지 수준 의도 보존·§C.5 덱 게이트. C14·C15는 선행 구현을 그대로 흡수 | validate_all_contracts 배선·테스트 포함 |
| `run_contracts.py` | `--spec`/`--plan` override (C-05)·C12 표기를 코드 실물에 맞춤 (I-06) | |
| `capture_deck.sh` | fit_report.json·FIT_OVERFLOW exit 전파(선행 게이트 4)·FIT_OK → FIT_OVERFLOW_OK 개명(R-03)·receipt meta 대조·**PDF 확정(mv)을 FIT 측정보다 앞으로**(측정 실패가 완성 PDF를 파괴하지 않게 - 페이블 중-2) | |
| `qa_ink.py` | 분포 게이트 + exit 전파 (선행 게이트 1 그대로) | |
| `hybrid_brief.py` | `int(pid[1:])` → 정규식/필드 기반 (I-01 방어) | 연번 재발급이 근본 해소 |
| `run_deck.sh` | receipt·PDF 존재 하드 실패 | |
| 폰트 | woff2 리포 vendoring (선행 게이트 5). Bold→ExtraBold 대체는 **재검 조건 기록 의무**: Chrome 메이저 업데이트 시 Bold 실물 재시험 (페이블 중-1) | |
| 문서 | harness-contracts SKILL.md(C6 목록·C13~C15)·designer.md·page-planner 스키마(visual_intent)·deck-harness SKILL.md 워크플로 | |

### 4.2 테스트 목록 (I-09 · 8건 + baseline)

0. **baseline green 선행**: 현행 suite의 python-pptx 미설치 error 4건 해소(설치 또는 명시 skip). baseline이 green이어야 새 회귀를 귀속할 수 있다.
1. renderer direct bypass·stale receipt 거부 테스트
2. theme x chrome x layout x font calibration golden 테스트
3. atom oversize·해 없는 partition·3장 이상 recursive split property 테스트
4. split 후 ID·lineage·citation/footnote/allowlist 보존 테스트
5. plan visual_intent ↔ final spec 대응 테스트
6. plan 대비 페이지 증가·덱 SPARSE 비율 테스트
7. native/raster PDF manifest·selectable text 테스트
8. legacy generic layout·구 spec migration 테스트 (suffix ID 워크스페이스 로드 포함)

### 4.3 마이그레이션·롤아웃

- 마이그레이션: 기존 워크스페이스(receipt 없음)는 읽기 전용 호환. 재렌더하려면 spec_gate부터 통과. suffix ID 구 덱은 lineage 필드 없이 로드만 허용(신규부터 강제).
- 롤아웃 순서: ①baseline green → ②선행 소형 게이트 6개(오늘 진행 중) → ③calibrate_layout + layout_budget (차원별 재측정 포함) → ④spec_gate + receipt → ⑤renderer 문법 일치 수정 → ⑥DELIVERY_OK 배선.

### 4.4 선행 부분집합: 오늘 구현 중인 소형 게이트 6개의 v2 내 위치

이 6개는 v2를 기다리지 않고 오늘 들어가는 최소 장치이며, v2 구현은 이를 재구현하지 않고 위에 얹는다.

| 선행 게이트 | v2 구조 내 위치 |
|---|---|
| 1. qa_ink 분포 게이트 + exit 전파 | §C.5 잉크 중앙값 행 + §G.5 조건 4 |
| 2. C14 차트 의도 보존 (덱 수준) | §E.6의 덱 수준 하한. 페이지 수준은 v2 확장 |
| 3. C15 페이지 수 상한 (plan x 1.2) | §C.5 페이지 팽창율 행 |
| 4. capture FIT_OVERFLOW exit 전파 | §G.4 8단계 |
| 5. 폰트 리포 내장 | §G.5 native PDF 신뢰성의 전제 (조건 6이 성립하려면 폰트 임베드가 안정적이어야) |
| 6. 미지 레이아웃 폴백 raise (generic 유지) | §E.4 |

---

## 5. 이 알고리즘이 실패를 막는 방식

| # | 실패 | 방어 |
|---|---|---|
| 1 | 넘침 사후 발견·무규칙 분할 | §A 예측 + §C.1 terminal 캐스케이드. 검출률 주장은 차원별 재측정 후 재수립 (§A.4) |
| 2 | 발명 블록 63건 | §E 저장 게이트 + receipt (§G) - draft 파일명이 아니라 해시가 경계 |
| 3 | 제목=리드 23곳 | §D C13 |
| 4 | 간지 번호 오기 | §F + I-05 규모의 렌더러 수정 |
| 5 | 런마다 디자인 새로 고름·무음 폴백 | §E.4 (선행 게이트 6) + 보정 키 고정 (§A.5). 색·테마 일관성은 여전히 이 문서 밖 (style_sets 후속) |
| 6 | "5건건"·PREV/NEXT 인쇄 | §F |
| 7 | **페이지 팽창 28→41** | §C.5 팽창율 (선행 C15) + §C.1 terminal (오검출발 분할 억제는 §A.5 fail-closed가 담당) |
| 8 | **차트 소실 viz 0** | §E.6 (선행 C14 + 페이지 수준) + 강등 승인 필드 |
| 9 | **저밀도 34장** | §C.5 SPARSE 비율·밀도·리듬 (선행 게이트 1) |
| 10 | **이미지 PDF 우회 납품** | §G.5 조건 6 + raster 정책 |
| 11 | **FIT_OK 오독 납품** | §G.4 개명 + §G.5 DELIVERY_OK 분리 |

---

## 6. 한계와 사람이 판단해야 할 것

**모델의 한계 (숨기지 않는다):**
- 모든 상수는 editorial·820px 조건의 앵커다. 차원별 재측정 전까지 다른 조합은 전부 fail-closed(느린 실측 경로)로 돈다. v1의 "오검출 16%" 수치 자체가 조건 오적용 상태의 측정이라 성능 지표로 무효다 (§A.4).
- receipt는 실수·관성 우회를 막고 우회에 흔적을 남기는 장치이지, 결의된 위조까지 막지 못한다 (§G.2).
- 줄 수 예측은 keep-all·가변 폭 폰트 특성상 문단당 +-1줄 오차가 구조적이다. 숫자·라틴 비중이 큰 문장은 오차가 커진다 (제미나이 참고 지적 수용·안전마진 50px + FIT 안전망이 흡수 대상).
- C13은 문자열 기반이라 의미가 같은 재서술(paraphrase)을 놓친다. 사람 검토 몫 (§D).
- 텍스트-온리 판단 오류는 코드로 완전 차단이 안 된다. 게이트는 도구를 거치는 경로만 강제한다.

**사람(또는 상위 에이전트)이 계속 판단하는 것:** v1의 5개 항목 유지(압축 대상 문장 선택·자연 키 없는 분할 제목·SPARSE 의도 여부·분할점 의미 적합성·어휘 확장 결정) + 추가 2개:
6. visual_downgrade 승인 (§E.6) - spec 작성자 본인은 승인 불가.
7. raster PDF 폴백 승인·만료 관리 (§G.5) - 승인자는 후추님.

---

## 부록 A. 산술 검산 결과

`python3 _workspace/20260810_algo_review/v2_arithmetic_check.py` 2026-08-10 실행·전 항목 통과:

```
[1] metric_grid v2 공식: 2개170 · 3개170 · 4개202 · 5개392 · 6개392 (실측 앵커 전부 재현)
[2] text_table 공식 보수 편차: 3행 +2.5 · 5행 +2.5 (균일·보수 방향 유지)
[3] B.1 대표 예시:
    리드+본문4줄+표5행(무제목)          458   통과 (여유 21)
    + 표 제목                          495   넘침 +16
    리드+donut+본문1줄                 456.5 통과 (여유 22.5)
    본문 2줄로 늘리면                   484.5 넘침 +5.5
    표6행(compact)+dumbbell            505   넘침 +26 (cutoff의 105.4%)
    리드+callout(emph)2줄+본문7줄       457.5 통과 (여유 21.5)
    본문 8줄로 늘리면                   485.5 넘침 +6.5
    metric_grid(5)+최소viz(164)        594   넘침 +115 (동거 불가)
[4] v1 정오표: 예시1 493→629 (통과→넘침 반전) · 예시2 593→618.5
[5] C-06 반례: viz400+metric = 610 → 선형 해 없음 → split 전환 288/172 = YES 해소
    변형 viz560 → |403.2-172|>160 → NO_VALID_PARTITION 반송
[6] 선형 분할 구조 불가 창 = H in (539, 602) → C.1 3단계가 TERMINAL 처리
```

## 부록 B. 리뷰 지적 대조표 (반영/기각)

### 코덱스 치명 C-01~C-10

| # | 지적 | 판정 | v2 위치·근거 |
|---|---|---|---|
| C-01 | 테마·layout 폭이 상수 키에 없어 판정 재현 불가·거짓 overflow | **반영** | §A.3b·§A.4·§A.5 8차원 키 + fail-closed |
| C-02 | 대표 산식이 자기 공식과 모순 | **반영** | §B.1 전면 재계산·부록 A 정오표·검산 스크립트 상시화 |
| C-03 | 모델 밖 페이지(grid 22%·image·미측정 viz)의 실패 동작 없음·registry 입력 누락 | **반영** | §A.0 입력 3요소·§A.3 fail-closed·"기본값 400" 폐기 |
| C-04 | draft 파일명은 경계가 아님·전 진입점 우회 가능 | **반영** | §G.1~G.2 receipt 초크포인트·진입점 전수 표·unattested 단일 우회 경로. 결의 위조 한계는 §6에 정직 명시 |
| C-05 | run_contracts가 draft를 검사 못 함·원자적 교체 없음 | **반영** | §G.3 --spec override·§G.1 원자 승격·N/A 시점 분리 |
| C-06 | 분할이 해 없는 입력에서 SPARSE·재넘침 생성·종료 조건 없음 | **반영** | §C.1 terminal 2종 + 롤백·반례 처리 검산 [5][6] |
| C-07 | 덱 page budget·밀도 게이트 없음·qa_ink 무력·FIT_SPARSE gap 검사 자체가 동작 불능 | **반영** | §C.5 반려 조건 7종 (선행 게이트 1·3 포함). FIT_SPARSE 240 차용 서술은 v2에서 삭제(근거 검사가 부실) - SPARSE 판정은 spec 시점 H 기준 + PDF 잉크 기준 이중 |
| C-08 | 시각 의도 보존 게이트 없음 | **반영** | §E.6 페이지 수준 1:1 + visual_downgrade 승인 필드 (선행 C14는 하한) |
| C-09 | FIT·PDF·이미지 PDF는 delivery gate가 아님 | **반영** | §G.5 DELIVERY_OK 7조건·raster 납품 금지 정책 확정 |
| C-10 | §4 수정안 문자 적용 시 정상 레이아웃 파괴·compact 강제 경로 부재·split/stack 미러 불일치 | **반영** | §E.4 사전 분기·§4.1 render_deck ③④·§B.3 미러 경고 |

### 코덱스 중요 I-01~I-09 · 참고 R-01~R-03

| # | 지적 | 판정 | v2 위치·근거 |
|---|---|---|---|
| I-01 | split 계약·lineage 없음·suffix ID가 int 파싱 파괴 | **반영** | §C.4 연번 재발급+계보 필드·B.2-6 headline 최소 규칙·hybrid_brief 수정 |
| I-02 | source·footnote 고정 상수가 렌더러와 다름 | **반영** | §A.0·§A.1 고정 차감 폐기·문자열 기반 모델 |
| I-03 | 줄 수 상수가 실제 CSS와 불일치·근거 산출물 부재 | **반영** | §A.2 정정·bullets fail-closed·§H 보존 규칙 |
| I-04 | invalidation이 CSS 해시 하나뿐 | **반영** | §A.5 renderer_struct_hash 포함 8차원·누적 SoT 명시 |
| I-05 | divider 수정 규모 과소 추정 | **반영** | §F 정정·§4.1 |
| I-06 | 계약 번호·schema SoT 이탈 | **반영** | §E.1 생성 스크립트·해시 receipt 포함·표기 정정 |
| I-07 | 결정론 선언과 Loop B 모순 | **반영** | §2 원칙 1~2: 결정론 범위를 판정 함수로 축소·Loop B 산출물은 승인 입력으로 해시 고정 |
| I-08 | C13이 중복의 일부만 잡음 | **부분 반영** | §D 2차 확장(문자열 범위)·negative set. **paraphrase 의미 검출은 기각**: 결정론 위반·오탐 통제 불가. 한계 명시로 대체 |
| I-09 | 테스트·rollout·migration 목록 없음 | **반영** | §4.2~4.3 (8건 + baseline green 선행) |
| R-01 | 검증 산출물 리포 부재·주장 재현 불가 | **반영** | §H 보존 의무 + 성능 주장 조건부 규칙 |
| R-02 | 재현 커맨드가 capture 강제 동작 미반영 | **반영** | §H --html-only 신설 |
| R-03 | FIT_OK 명칭이 품질 통과로 오독 | **반영** | §G.4 FIT_OVERFLOW_OK 개명 + §G.5 분리 |

### 제미나이

| 지적 | 판정 | v2 위치·근거 |
|---|---|---|
| SPARSE가 경고에 그침 (치1-1) | **반영** | §C.5 반려 조건화 |
| 시각 리듬·정보량 편차 규칙 0개 (치1-2) | **반영** | §C.5 리듬 게이트 3종·수치는 정상 1번 덱 실측 도출 |
| 픽셀 상수 이중 유지보수·CSS 해시 마비 (중2-1) | **부분 반영** | §A.5 하이브리드: 미보정 = 헤드리스 실측 경로(제안의 부분 채택)·fail-closed는 마비가 아니라 느린 경로 강등. **전면 사전 렌더 전환은 기각**: 렌더 없는 즉시 반려 루프가 핵심 가치 + capture 단일 의존 위험(Chrome Abort trap 실사례) |
| 문맥 무시 분할·서사 단절 (중2-2) | **부분 반영** | §C.0 고아 방지·§C.1 반송 우선(분할은 최후). 문장 의미 단위 분할은 조판기 권한 밖(콘텐츠 권한 침해라 기각) - 반송받은 플래너가 의미 재구성 |
| LaTeX 전역 최적화(Knuth-Plass DP) 부재 (중2-3) | **기각 (v3 후보)** | 근거: 조판기는 콘텐츠 재작성 권한이 없어 cut 자유도가 블록 경계로 이산·소수다. DP의 이득이 성립하는 연속 badness 공간이 없다. 전역 품질은 §C.5 덱 게이트(반려)가 담당하고 재구성은 콘텐츠 권한자(플래너) 몫. 페이지 나눔 badness 최소화는 v3에서 재검토 여지만 남김 |
| CSS orphans/widows 부재 (중2-3) | **반영** | §C.0 고아 방지 규칙 |
| PPT AutoFit(폰트 축소) 부재 (중2-3) | **기각** | §C.0: 위계 고정 계약 충돌 + 연속값 축소는 보정 체계 파괴. 이산 압축 티어가 역할 대체 |
| 가변 폭 폰트 줄바꿈 오차 (참3-1) | **반영** | §A.2·§6 한계 명시 (안전마진+FIT 흡수) |
| 폰트 CDN 의존·Bold 대체 등 렌더러 diff 지적 | **반영 (경로 분리)** | 선행 게이트 5 + §4.1 재검 조건 기록. diff 세부는 이 문서가 아니라 renderer 수정 결재의 몫 |

### 페이블 (렌더러 diff 실측 - 설계 문서에 걸리는 것만)

| 지적 | 판정 | v2 위치·근거 |
|---|---|---|
| 치-1 폰트 공급망 CDN+임시 폴더 | **반영** | 선행 게이트 5 (리포 vendoring)·§4.4 |
| 치-2 라벨 솔버 계층 미공유·무음 포기 | **범위 밖·위치만 지정** | SVG 라벨 겹침은 렌더 후 FIT 몫(§G.4 8단계)이 맞고, 솔버 자체 수정은 renderer 결재 항목. 단 "소진 시 무음" 금지 원칙은 §E.4·§A.5 fail-closed와 같은 정신으로 renderer 수정 시 적용 |
| 치-3 회귀 테스트 미커밋·미배선 | **반영** | §4.2 baseline green 선행 + 테스트 8건을 수정 목록의 1급 항목으로 |
| 중-1 Bold→ExtraBold 무기록 대체 | **반영** | §4.1 재검 조건 기록 의무 |
| 중-2 측정 실패가 완성 PDF 파괴 | **반영** | §4.1 capture: PDF 확정을 FIT보다 앞으로 (측정과 생산 분리) |
| 중-3 dedup 무음 번복 / 중-4 별칭 무음 수용 / 중-6 빈 밴드 무음 통과 / 중-7 정규식 파싱 | **범위 밖·이관** | renderer diff 결재 항목. 공통 원칙(무음 동작 금지·힌트는 제안·변환 금지)은 §E·§F가 이미 선언 |
| 결정 1~5 판정 | **반영** | 결정 1→§E.6, 결정 2→§C.1·§C.5, 결정 3→§G.5, 결정 4→§G.5 raster 정책, 결정 5→단일 오너·병렬 게이트는 designer.md 워크플로 몫으로 §4.1 문서 행에 포함 |

### 본부 자체 구멍 7건

| # | 지적 | 판정 | v2 위치 |
|---|---|---|---|
| 1 | SPARSE 경고 그침 | 반영 | §C.5 |
| 2 | 의도 보존 검사 없음 | 반영 | §E.6 |
| 3 | 덱 페이지 수 통제 없음 | 반영 | §C.5 팽창율 |
| 4 | grid 계열 미보정 무음 통과 | 반영 | §A.5 fail-closed·판정 불가 명시 분류 |
| 5 | 이미지 PDF 코드베이스 밖 | 반영 | §G.5 정책 확정(납품 금지·조건부 내부 폴백) |
| 6 | 디자인 일관성 범위 밖 | 유지 (정직) | §5-5: style_sets 후속으로 명시. 이 문서는 조판까지 |
| 7 | 프로세스 규율 (코드 밖) | 반영 (경계 명시) | §G.2 한계·§6. 코드로 못 막는 것은 _defect_ledger·pm_briefing cooldown 몫 |
