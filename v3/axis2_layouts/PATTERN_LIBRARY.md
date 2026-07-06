# 패턴 라이브러리 (SoT)

> 2026-07-04 신설 (후추님: "그대로 따라하지 말고 습득해서 패턴화하고, 제작할 때 골라서 적용").
> 레퍼런스는 여기로 **패턴 단위**로 누적되고, designer는 제작 시 여기서 **골라서** 조합한다.
> 운영 flow = `REF_COLLECTION_RULES.md` §패턴화 flow. 선택 규칙 = `.claude/agents/designer.md`.
> 상태: ✅ 엔진 구현됨 / ⬜ 백로그(관찰만 등재). 관찰수 = 수집 레퍼런스에서 실측된 아이템 수(누적).

## A. 디자인 시스템 (덱 전체의 옷)

| ID | 시스템 | 성격 | 상태 |
|---|---|---|---|
| SYS-base | 기본 8테마(editorial·tech·peppinch·marketing·health·forest·violet+별칭) | 산세리프+카드 라이트 | ✅ |
| SYS-serif | editorial_serif | 세리프 매거진·카드리스·제본선 | ✅ |
| SYS-mono | data_mono | 모노 데이터·방안지·스펙시트 | ✅ |
| SYS-dark | dark_premium | 전면 다크·골드 1액센트·depth 카드 | ✅ |
| SYS-minimal | minimal_typo | 웜 미니멀·극단 위계비·1액센트 | ✅ |
| SYS-pop | pop_dark | 블랙+오렌지 북엔드+다색 팝 | ✅ |

## B. 페이지 골격 (페이지의 몸 — 시그니처는 권장 시스템 명기)

| ID | 골격 | 설명 | 권장 | 상태 |
|---|---|---|---|---|
| PG-statement/split/stack/matrix/stepper/index/cards/timeline/node/hero_metric/closing | 공용 11종 | 전 시스템 공용 | 전체 | ✅ |
| PG-poster | 제목 없는 한 문장 포스터 | 지면 전체가 한 문장 | minimal | ✅ |
| PG-hero_bleed | 화면 절반 블리드 수치 | 숫자가 페이지 | dark·pop | ✅ |
| PG-magazine_spread | 다단 조판+전폭 풀쿼트 | 잡지 스프레드 | serif | ✅ |
| PG-dashboard | 풀페이지 위젯 타일 | 계기판 | mono | ✅ |
| PG-mosaic_tiles | 크기가변 사진/블록 모자이크(관찰 14+ — magazine 6 + 2R Arabella·Maison·Minimo·Ombar 번호닷·Artista 등 8). 사진 없이 색면 타일로 구현 | 화보 타일 + 선택적 번호닷 | serif·minimal | ✅(7/4 배치2) |
| PG-running_head | 상단 3점 러닝헤드 프레임(관찰 17+). 좌 kicker(명시적 eyebrow만·내부명 노출 금지)·중 브랜드·우 페이지분수(렌더러 계산) + 하단 PREV/NEXT. 스펙: deck_spec meta `"page_chrome": "running_head"` (본문 페이지만·표지/간지/클로징 제외·기존 페이지번호 억제) | 일하는 덱 프레임 | serif·minimal | ✅(7/4 배치3) |
| PG-pricing_cards | 가격/플랜 3열 카드(관찰 13+ — 전 6패밀리 관통). headline이 카드를 열고 후속 블록 착지. 스펙: `"layout": "pricing_cards"` + 페이지 옵션 `"emphasis_style": "invert"\|"offset"\|"scale"\|"border"` (기본 invert — **run마다 다르게 골라 "같은 템플릿" 천장 방지**) | 옵션·시나리오 비교 | 전체 | ✅(7/4 배치3) |
| PG-nav_chrome | 상단 탭바/햄버거 웹크롬 반복(관찰 8 — report_ops 2 + 2R corporate·minimal·dark 6) | SaaS/상태보고 톤 | mono·pop | ⬜ |
| PG-split_status | 좌 정성서술 + 우 정량지표칩 상태페이지(관찰 2 — report_ops) | 상태·리스크 보고 | 전체 | ✅(7/4 배치2) |
| PG-scenario_cards | headline이 카드를 열고 후속 블록이 카드에 착지 — 시나리오/케이스 N열 카드(트렌드 장르 Scenarios 착지용) | 시나리오·결론 비교 | dark·pop | ✅(7/4 배치2 — 카드당 블록 3개+ 밀도 규칙. **도입용 단독 headline 금지** — 카드 개시 문법이라 빈 카드가 됨, 7/4 run4 실측) |
| PG-profile_row | 아바타+이름 인물 카드 열(관찰 15+ — report_ops 3 + 2R 9 + 7/6 실전 3: 삼성 003·KPMG 오토 013·M&A 013) | 팀·전문가 소개 | 전체 | ⬜(사진 자산 정책 미정이었으나 **KPMG 실물이 사진 없는 텍스트 연락처 그리드** — 아바타 없이 구현 가능 실증, 보류 사유 완화) |
| PG-color_block_bento | 전면 색면 직사각형 베노(여백 없이 컬러블록 맞물림+번호/사진 삽입, 관찰 3 — 2R Artista·Ombar·dark-normal) | 강렬 편집·표지 | pop·creative | ⬜ |
| PG-title_band | 상단 전폭 솔리드 색밴드(높이 10~14%)에 좌정렬 흰 제목 1~2줄, 본문 백지. 간지 = 같은 밴드를 **비우고** 중앙 스테이트먼트만. 착지 2형: ①페이지 제목형(BOND trends_ai ~330장 + 2015 덱 본문 전수 = **10년 크롬**) ②차트 제목형(밴드가 차트 제목 — Activate 5개년 본문 전수·BOND 메모 카드 헤더) ⚠ 승격 전 미결: 밴드의 auto-fit 제외 여부·제목 2줄 시 높이 규칙 (7/6 리뷰) | 실전 리포트 크롬 | corporate·mono·전체 | ⬜(3발행처) |
| PG-toc_progress | 섹션 시작마다 진행 표시. 변주 3형: ①목차 전체 재출력+현재 행 반전(KPMG ces 4·Activate 2021/2024 3) ②상단 번호 칩 현재만 채움(KPMG 오토 11) ③섹션 필+도트 ●○○○○(KPMG M&A 7) | 긴 일하는 덱 내비 | corporate·전체 | ⬜(3발행처 25관찰) |
| PG-item_profile | 반복 아이템 카탈로그: 카테고리 필(+메타 칩) → 헤드라인 → 2~4줄 dek → 좌 라벨바+이미지 패널 / 우 틴트 카드(액센트 볼드 미니헤드 + 불릿 2단 • → –) (관찰 — KPMG ces2026 ~30장 **단독**. ⚠ 7/6 배치 15건 재확증 0 — KPMG 다른 발행물 2건에도 없음 → 1건 출처 강등. 구현 비용도 최고(이미지 자산 정책 선결)) | 카탈로그·사례집 | corporate·전체 | ⬜(1건 출처·승격 보류) |
| PG-prose_page | 문단 에세이 페이지 — 불릿 없이 문단 스택. 변형 3: ①중앙정렬 에세이(BOND trends_ai 5장) ②좌정렬 메모 prose+볼드 리드인(BOND 메모 3건 — 문서 전체가 prose) ③IR 유의사항/Disclaimer(카카오·네이버·삼성 모두 2페이지째) + Activate 테이크어웨이 스택 변형(볼드 런인 리드+헤어라인 룰, act25 001~003) | 서문·맺음·면책 | mono·corporate | ⬜(7건 재확증) |
| PG-metric_commentary | IR 원자 블록: 지표명 헤딩 + `+X% YoY, ±Y% QoQ` 델타쌍 헤드라인 + (YoY)/(QoQ) 라벨 불릿 + 분기 차트. 페이지당 1~2행 스택 (관찰 12+ — 카카오 016~019 2행형·네이버 003~008 1행형) | 실적·상태 보고 | corporate·전체 | ⬜ |

## C. 차트·다이어그램 (수치 비교 12종 + 관계·프로세스 4종)

| ID | 차트 | 용도 | 상태 |
|---|---|---|---|
| CH-비교 12종 | before_after·dumbbell·flow·big_number·gap_map·shift·funnel·donut·mirror_bars·rising_columns·pictogram·gauge | 수치 비교·비율·추이 | ✅ |
| ⚠ shift 주의 | 두 점-쌍(회색→강조 도트)이 연결선 약해 다크에서 화살표가 안 보이고 "같은 것 두 번"으로 읽힘(후추님 7/4 반복 지적). 증감 2값이면 **rising_columns/before_after 우선** | designer 회피 | — |
| CH-hub_cycle | 중심+궤도 순환 허브 | 관계·생태계 | ✅ |
| CH-arrow_flow | 셰브런 화살표 프로세스 | 인과·단계 | ✅ |
| CH-timeline_bars | 간트형 계단 타임라인 | 순서·구간 | ✅ |
| CH-data_table | 액센트 헤더 데이터 표 | 지표 나열 | ✅ |
| CH-multi_line | 다계열 라인(관찰 8/8 dashboard + 4/5 report_ops) — role baseline/highlight로 선 분리 | 시계열 비교 | ✅(7/4 승격) |
| CH-progress_bar | 목표 대비 진척 막대: 트랙+채움 %(관찰 3 — report_ops·number=0~100 해석) | OKR/상태 진척 | ✅(7/4 승격) |
| CH-target_vs_actual | 계획 vs 실제 대비쌍(관찰 3 — series 연속 2개=1행·계획=점선 고스트) | 목표-달성 비교 | ✅(7/4 승격) |
| CH-rating_dots | N/10 도트 채움 레이팅(관찰 5 — report_ops 3 + 2R 별점 testimonial 2) | 정성 점수 | ⬜ |
| CH-radial_progress | 단일 링 진척 게이지·% 중앙(관찰 7+ — 2R 게이지 라이브러리·도넛% 다수 재확증) | 단일 KPI 진척 | ✅(7/4 승격) |
| CH-kpi_delta_card | 숫자+델타+미니추세 KPI 블록(관찰 11+ — dashboard 8 + report_ops 3 + 2R 델타스택·타깃블록) | 계기판 단위 | ⬜(델타·숫자블록은 ✅ — 미니추세 스파크라인만 백로그) |
| CH-puzzle/gear/polygon | 퍼즐·기어·다각형 인포그래픽(pop 스샷 관찰) | 구성요소·맞물림 은유 | ⬜ |
| CH-swot_quad | 2×2 SWOT/정성 사분면 — 중앙 십자축·highlight 사분면 틴트(관찰 4). 스펙: viz `"chart": "swot_quad"`, series 4개 = 사분면(`label`+`items` 문자열 배열·숫자 금지), metric_id 예외 유일 차트 | 전략·경쟁분석 | ✅(7/4 배치3) |
| CH-annotated_trend | 성장 서사 라인차트 주석 레이어 4종: 성장률 타원 콜아웃("+X%/Year")·보조 추세 화살표·끝점 굵은 수치·**이벤트 구간 세로 음영 밴드+상단 라벨**(usa_inc WWII·COVID / a16z "ICO boom" 에포크 밴드 흡수). 기존 multi_line 확장 (관찰 20+ — BOND 4/4 아이템·2015까지 10년 연속 + Activate/a16z 10) ⚠ 구현 선결: C6 계약상 title/note raw number 금지 — 파생값(성장률) metric 체계 설계 먼저 (7/6 코과장 리뷰) | 추세에 서사 싣기 | ⬜ |
| CH-chart_card_grid | 차트 카드 그리드(2×2·3×2·세로 스택) — 카드별 미니 헤더밴드 (관찰 10+장 — BOND 3/4 아이템: our_new_world 007·015~017 / ai_education 004·007~009 / usa_inc 002·004·022) ⚠ 코너 번호닷+"Details on Page N"은 trends_ai 1건 고유 장식으로 분리 — 그리드만 등재 | 익제큐티브 서머리 | ⬜ |
| CH-quarterly_bars | 분기 시계열 막대: 데이터 라벨 온바(축눈금 생략)·마지막/비교 분기만 액센트 나머지 뮤트·옵션 축절단 `≈`. 기존 rising_columns 확장 (관찰 20+ — 카카오 014~019·025 / 네이버 003~009 / 삼성 005~010 = **IR 3사 관통**) | 실적 시계열 | ✅(7/6 R1) |
| CH-fin_table | data_table 확장: 분기 열+YoY/QoQ 파생 열·**현재 분기 열 액센트 아웃라인 박스**(3사 관통 최강)·그룹행 볼드/하위행 들여쓰기·비율행 이탤릭·음수 빨강 또는 괄호·"흑자전환" 텍스트 셀 (관찰 9 — 카카오 020·021 / 네이버 002·007·015 / 삼성 011~014) | 재무·지표 표 | ✅(7/6 R1) |
| CH-quote_card | 카드 그리드 안에 차트 대신 센터 이탤릭 인용문+"이름 – 직함, 날짜" 어트리뷰션. 기존 카드 부품 재사용 (관찰 2아이템 6회 — our_new_world 015~019 / 2015 045 풀페이지 간지형) | 정성 근거 착지 | ⬜ |
| CH-photo_bar | 사진/포스터/커버가 막대·타일 그 자체가 되는 차트(값 라벨 칩 부착). 엔진은 색면+이니셜 플레이스홀더 구현 (관찰 5 — act25 060·096·144 / act24 100 / act22 050) | 실전 데이터 톤 | ⬜(사진 자산 정책 선결) |
| CH-logo_connector_map | 좌 주체 열 ↔ 우 대상 열 곡선 점선 연결 관계 지도 + 로고 랜드스케이프(카테고리 구획) (관찰 3 — act24 150 / act25 168·180. 로고 자산 의존 — 텍스트 칩 대체 구현) | 관계·생태계 | ⬜ |
| CH-waterfall_bridge | 시작·끝 솔리드 막대 + 중간 부유 델타 블록(▲/▼ 라벨) 워터폴 브리지 (관찰 1건 — 네이버 016 YoY·QoQ 2연. 등재 기준 미달이나 IR 손익 서사 핵심이라 백로그 기록) | 손익 증감 분해 | ⬜(1건 출처) |
| CH-choropleth | 지도 코로플레스(관찰 7+ — 2R 지도 라이브러리 2건 통째·Vatino·Pezane 등. 보류 사유였던 관찰1은 해소) | 지역 분포 | ⬜(국가 SVG 자산 정책 필요 — 자산 부담으로 승격 보류 유지) |

## D. 장식·오브제 레버 (시스템 토큰에 색 위임 — 스타일 복제 금지)

| ID | 레버 | 상태 |
|---|---|---|
| DC-ghost_word · cover_sheen · spine_label · eyebrow_chip · divider quiet/standard · cover center/corner · divider_variant accent · hero_title | 기존 변주축 묶음. ghost_word 하위 변형: **에코 반복**(동일 제목 3회 겹침 — 솔리드1+아웃라인2, 관찰 4 — 2R Arabella·Pezane 등. 별도 ID 없이 여기 흡수) | ✅ |
| DC-offset_block | 빅넘버 뒤 오프셋 컬러블록(관찰 4/8 minimal B형) | ✅(minimal) |
| DC-depth_card | 바탕+1단 밝은 카드 부양(관찰 6/8 dark) | ✅(dark) |
| DC-pill_metric | 다색 필 메트릭 블록(pop 스샷) | ✅(pop) |
| DC-outline_number | 대형 아웃라인 숫자 오브제(관찰 6+ — 2R 코너 거대 페이지숫자 용례 추가 확증) | ✅(mono 간지) |
| DC-side_wordmark | 지면 좌/우 세로 회전 대형 워드마크(관찰 6). 스펙: 페이지 `"decor": "side_wordmark"` (+`section_label` 있으면 그 텍스트, 없으면 덱 short title — designer 자유 텍스트 금지·고스트 톤 자동) | ✅(7/4 배치3) |
| DC-photo_frame | 기하 마스크/라운드 사진 프레임(관찰 다수) | ⬜(사진 자산 정책 미정) |

## E. 컬러·타이포 규칙 (패밀리 공통 문법에서 승격된 원칙)

| ID | 규칙 | 근거 | 상태 |
|---|---|---|---|
| CL-single_accent | 단일 지배 액센트 (다크 7/8·미니멀 8/8·코퍼레이트 9/9) | _grammar | ✅(4 시스템) |
| CL-multi_pop | 다색 팝 t램프 순환 — pop 계열만 예외 허용 | pop 스샷 | ✅(pop 한정) |
| CL-muted_body_on_dark | 다크 본문은 순백 금지·60~75% 회색 (6/8) | _grammar/dark | ✅ |
| TY-extreme_ratio | 헤드:본문 극단 크기비 (미니멀 8/8) | _grammar/minimal | ✅(minimal) |
| TY-kicker | 초소형 자간 키커 라벨 (5/8+ · report_ops 다수) | _grammar | ✅ |
| CL-gradient_accent | 그라디언트 액센트를 지배색으로 (관찰 4 — report_ops 2 + 2R Inside 무지개 웨이브·corporate 마젠타→퍼플 풀블리드) | inbox 실측 | ⬜(creative/dark 한정 승격 후보) |
| TY-source_infra | 출처 다층 체계: ① 차트 제목 안 "– 기간, per 출처" ② 하단 Note:/Source: 마이크로 캡션 ③ 번호 각주 1)2)3)·※사진 출처 분리(IR) ④ **데이터 성격 배지**(Activate "FORECAST" 배지·자체조사 스탬프·파트너 로고 박스 — 예측/실측/외부를 시각 구분). 실전 신뢰 문법의 핵 — 템플릿 46건 관찰 0 ⚠ 구현 선결: deck_spec `source`가 페이지 레벨 배열(viz/series 1:1 아님) → 스키마 확장 필요 + 현 source-row CSS가 한 줄 clip(nowrap+hidden, render_deck.py ~3038) — overflow 정책 먼저 (7/6 리뷰 실측) | **17/17 전 실전 아이템** — BOND 2015부터 10년 무결점·Activate 4층·KPMG 하우스·IR 3사 | ⬜(실전 톤 의무 후보) |
| CL-semantic_color | 색 = 의미 고정: 액센트 1색 = 주인공, 빨강 = 악화·음수 전용(또는 괄호), 초록 = 상승·개선. 장식 다색 금지. 추가 룰 2: **브랜드/체인색 = 시리즈색 예외**(a16z 비트코인 주황·Activate 인스타 보라 — 덱 전체 불변) · 잉크는 비교 대상에만(마지막 분기·비교쌍만 액센트, 나머지 뮤트). 구현: series role `negative`/`positive`/`brand` — 코과장 평가 최저비용 | BOND 3/4(2015엔 약함 = 최근 10년 문법)·Activate/a16z 12+·IR 3사·KPMG — 5발행처 관통 | ✅(7/6 R1 — series role negative/positive/brand) |
| TY-headline_highlight | 헤드라인 핵심 구절에만 솔리드 형광 마커 색면(섹션 액센트색 연동·목차 색칩과 색 코딩). `<mark>` 스타일 1개 — 구현 최저비용·효과 최대급 | a16z 9관찰 (004~052) — 1발행물 출처라 재확증 대기 | ⬜(1건 출처) |
| TY-bold_lead_bullet | 불릿 = "**볼드 결론구** – 뒷받침 문장" 리드인 구조 (writer 룰 후보) | BOND 메모 2건 10장+ (ai_education 003~014 등) | ⬜(writer 룰 검토) |
| CL-accent_rotation | 섹션/세그먼트별 액센트 1색 로테이션 — 페이지 안은 여전히 단일 액센트(CL-single_accent와 양립) | 4발행물 — KPMG 오토 4색·네이버 세그먼트 5색·Activate 2022/2024 섹션별 키커색 | ⬜ |

## 승격 큐 (⬜→✅ 순서 — 2026-07-04 2라운드 46건 병합 시 재산정)

관찰수 × 시스템 관통성 × 구현 저비용 종합. 구현 = 코덱스 위임(배치 단위).

~~1~5순위 전부 승격 완료 (7/4 배치2·배치3)~~ — pricing_cards·running_head·mosaic_tiles·split_status·scenario_cards·swot_quad·side_wordmark ✅
- 다음 후보(관찰 재확인 후): PG-nav_chrome(관찰 8)·PG-color_block_bento(관찰 3)·CL-gradient_accent(관찰 4)·CH-rating_dots(관찰 5·자산 무관 도트라 사진 정책과 분리 가능)
- 보류 유지: CH-choropleth(SVG 자산 정책 선결)·PG-profile_row/DC-photo_frame(사진·아바타 자산 정책 선결)·CH-kpi_delta_card 스파크라인
- **실전 PDF 승격안 (7/6 확정 — 17건 실측 + 제대리·코과장 교차 리뷰 반영·후추님 결재 대기):**
  - **0순위 (선결·버그)**: overflow 게이트 신뢰성 — clo_v51 p08 출처 칩 잘림이 게이트 미검출로 통과한 사고. 뿌리 특정됨(source-row CSS `nowrap+hidden` clip). 긴 텍스트 얹는 모든 패턴의 선결 조건. 코과장 위임 1건. → ✅ 완료(7/6 R1 — flex-wrap 2줄+`+N` 축약·FIT_SOURCE_CLIP 게이트 신설·clo_v51 p08 실측 해소·commit cf15859)
  - **R1 (저비용·고관통)**: ✅ 완료(7/6 — commit e3a39a8·test 84/84·데모 4/4) CL-semantic_color + CH-quarterly_bars + CH-fin_table
  - **R2 (스키마 설계 선행)**: TY-source_infra(17/17 관통 — 단 source를 viz/series 단위로 스키마 확장 먼저) + PG-title_band(auto-fit 정책 결정 먼저·착지 2형 스펙)
  - **R3 (계약 설계 후)**: CH-annotated_trend(C6 파생 metric 체계 선행 — 안 하면 "검증 게이트에서 깨지는 장식", 코과장) + PG-toc_progress(3발행처 25관찰) + PG-metric_commentary
  - **강등·보류**: PG-item_profile(재확증 0 — 1건 출처 강등 + 구현 비용 최고) · CH-photo_bar/logo_connector_map(자산 정책 선결)
  - 옛 "1순위 title_band·item_profile" 표기는 리뷰로 교정됨 — 구현 비용 실측(deck_spec source 구조·C6 계약) 반영.
- 미등재 기록 (1건 출처 — 다음 수집 배치 재확증 대상): DC-pixel_block(a16z)·CH-redline_edit(usa_inc 업데이트판 문법)·PG-results_outlook(삼성 좌Results/우Outlook)·CH-ranked_leaderboard(KPMG 오토)·PG-boxed_section_label(BOND 메모 간지)·PG-perspective_sidebar(Activate 의견 박스 — KPMG 틴트 카드와 병합 시 3+)·PG-contacts_closing(KPMG 하우스)·히트 열 테이블(a16z 008)

주의(추출 에이전트 반대신호 — 숨기지 않음): corporate/data 다수가 "부품 카탈로그"라 choropleth/funnel/gauge 관찰수는 부품 존재이지 페이지 문법 아님(과대 계상 주의). pricing/running_head 외 신규 후보 관찰수는 00 컨택트시트 의존도 높음 → 승격 확정 전 본문 슬라이드 추가 실측 권장.

## 실전 리포트 문법 (2026-07-06 — pdf_report 17건 실측. "일하는 덱" vs "팔려는 덱")

designer 선택 시 참고 — 실전 톤 요청이면 아래가 우선한다:

1. **골격 수렴이 곧 신뢰** — BOND 340장=골격 4종·Activate 본문 200장=사실상 1종·KPMG 오토 14장 중 11장=단일 템플릿·IR 3사=원자 블록 반복. 템플릿 마켓의 "페이지마다 다른 레이아웃 전시"와 정반대. ⚠ 적용 조건부(7/6 리뷰): **30p+ 장편 또는 명시적 리포트 톤 요청 시만** — 15~20p 단편 덱에 강제하지 않는다 (layout 다양성 규칙과의 조율은 장르별 정책).
2. **출처·주석 인프라 상시 가동** (TY-source_infra) — 템플릿 46건 관찰 0 vs 실전 17/17. 실전 톤이면 기본값.
3. **색은 의미를 진다** (CL-semantic_color) — 5발행처 관통. 단 2015 BOND엔 약함 = 최근 10년에 강화된 문법.
4. **밀도를 위계로 견딘다** — 여백 과시 대신 정보 밀도 + 극단 크기비·볼드·색 위계 + 주석 레이어.
5. (writer 규칙 후보) "X = Y" 등식형 제목 + 말줄임 "…" 페이지 연쇄 — BOND 2015~2025 10년 관통 재실측(슬라이드 제목→카드 밴드 제목으로 자리만 이동). 근거 충분 — designer/writer 룰 승격 검토.
6. **서사 시퀀스 축 (신설 검토·7/6 Gemini 지적 + IR 실측)** — 페이지 부품보다 상위 문법. 실측 1건: SEQ-ir_arc = 표지→면책→실적 요약→부문별 반복→비용/손익 표→Appendix 재무제표→감사(IR 3사 순서 이탈 0). 후보(실측 대기): SEQ-impact_explanation(임팩트 숫자 던지고 다음 장에서 설명 — Gemini 추정·미실측이라 등재 보류).

## 갱신 규칙

- 새 레퍼런스에서 관찰된 패턴: 기존 ID면 관찰수 갱신, 새로우면 ⬜로 등재 (추출 에이전트가 제안 → 클차장 병합)
- ⬜ → ✅ 승격은 관찰수·판매 임팩트 순 라운드 처리, 구현은 항상 시스템 무관 부품 + 색·서체는 토큰 위임
- 관찰 1~2건짜리 "개별 버릇"은 등재하지 않는다 (패밀리 시트의 개별 버릇 원칙과 동일)
