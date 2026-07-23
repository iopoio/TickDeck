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
| PG-statement/split/stack/matrix/stepper/index/cards/timeline/node/PG-hero_metric/closing | 공용 11종 | 전 시스템 공용 | 전체 | ✅ |
| PG-poster | 제목 없는 한 문장 포스터 | 지면 전체가 한 문장 | minimal | ✅ |
| PG-hero_bleed | 화면 절반 블리드 수치 | 숫자가 페이지 | dark·pop | ✅ |
| PG-magazine_spread | 다단 조판+전폭 풀쿼트 | 잡지 스프레드 | serif | ✅ |
| PG-dashboard | 풀페이지 위젯 타일 | 계기판 | mono | ✅ |
| PG-mosaic_tiles | 크기가변 사진/블록 모자이크(관찰 14+ — magazine 6 + 2R Arabella·Maison·Minimo·Ombar 번호닷·Artista 등 8). 사진 없이 색면 타일로 구현 | 화보 타일 + 선택적 번호닷 | serif·minimal | ✅(7/4 배치2) |
| PG-running_head | 상단 3점 러닝헤드 프레임(관찰 17+ + dribbble 재확증 10+ — 대부분 덱이 좌 로고/워드마크 + 하단 페이지수·카피라이트 초경량 크롬을 전 페이지 반복, title_band류 색면 바보다 훨씬 우세). 좌 kicker(명시적 eyebrow만·내부명 노출 금지)·중 브랜드·우 페이지분수(렌더러 계산) + 하단 PREV/NEXT. 스펙: deck_spec meta `"page_chrome": "running_head"` (본문 페이지만·표지/간지/클로징 제외·기존 페이지번호 억제) ⚠ 7/23 실측: 기존 title_band 전제로 짜인 페이지(문단 밀도·카드 높이)를 running_head로 그대로 바꾸면 여백 예산이 달라져 overflow 재발(clo_it_planner p06·11·16·19·20 5장) — 전환 시 컨텐츠 재적합 필요, 사후 테마 스왑 아님 | 일하는 덱 프레임 | serif·minimal | ✅(7/4 배치3) |
| PG-pricing_cards | 가격/플랜 3열 카드(관찰 13+ — 전 6패밀리 관통). headline이 카드를 열고 후속 블록 착지. 스펙: `"layout": "pricing_cards"` + 페이지 옵션 `"emphasis_style": "invert"\|"offset"\|"scale"\|"border"` (기본 invert — **run마다 다르게 골라 "같은 템플릿" 천장 방지**) | 옵션·시나리오 비교 | 전체 | ✅(7/4 배치3) |
| PG-nav_chrome | 상단 탭바/햄버거 웹크롬 반복(관찰 8 — report_ops 2 + 2R corporate·minimal·dark 6) | SaaS/상태보고 톤 | mono·pop | ⬜ |
| PG-split_status | 좌 정성서술 + 우 정량지표칩 상태페이지(관찰 2 — report_ops) | 상태·리스크 보고 | 전체 | ✅(7/4 배치2) |
| PG-scenario_cards | headline이 카드를 열고 후속 블록이 카드에 착지 — 시나리오/케이스 N열 카드(트렌드 장르 Scenarios 착지용) | 시나리오·결론 비교 | dark·pop | ✅(7/4 배치2 — 카드당 블록 3개+ 밀도 규칙. **도입용 단독 headline 금지** — 카드 개시 문법이라 빈 카드가 됨, 7/4 run4 실측) |
| PG-profile_row | 아바타+이름 인물 카드 열(관찰 15+ — report_ops 3 + 2R 9 + 7/6 실전 3: 삼성 003·KPMG 오토 013·M&A 013) | 팀·전문가 소개 | 전체 | ⬜(사진 자산 정책 미정이었으나 **KPMG 실물이 사진 없는 텍스트 연락처 그리드** — 아바타 없이 구현 가능 실증, 보류 사유 완화) |
| PG-color_block_bento | 전면 색면 직사각형 베노(여백 없이 컬러블록 맞물림+번호/사진 삽입, 관찰 3 — 2R Artista·Ombar·dark-normal) | 강렬 편집·표지 | pop·creative | ⬜ |
| PG-title_band | 상단 전폭 솔리드 색밴드(높이 10~14%)에 좌정렬 흰 제목 1~2줄, 본문 백지. 간지 = 같은 밴드를 **비우고** 중앙 스테이트먼트만. 착지 2형: ①페이지 제목형(BOND trends_ai ~330장 + 2015 덱 본문 전수 = **10년 크롬**) ②차트 제목형(밴드가 차트 제목 — Activate 5개년 본문 전수·BOND 메모 카드 헤더) ⚠ 승격 전 미결: 밴드의 auto-fit 제외 여부·제목 2줄 시 높이 규칙 (7/6 리뷰) | 실전 리포트 크롬 | corporate·mono·전체 | ✅(7/7 R2 — 착지 2형·간지 비움·FIT_BAND_OVERFLOW) |
| PG-toc_progress | 섹션 시작마다 진행 표시. 변주 3형: ①목차 전체 재출력+현재 행 반전(KPMG ces 4·Activate 2021/2024 3) ②상단 번호 칩 현재만 채움(KPMG 오토 11) ③섹션 필+도트 ●○○○○(KPMG M&A 7) | 긴 일하는 덱 내비 | corporate·전체 | ✅(7/7 R3 — section_nav chips/dots/toc 3형) |
| PG-item_profile | 반복 아이템 카탈로그: 카테고리 필(+메타 칩) → 헤드라인 → 2~4줄 dek → 좌 라벨바+이미지 패널 / 우 틴트 카드(액센트 볼드 미니헤드 + 불릿 2단 • → –) (관찰 — KPMG ces2026 ~30장 **단독**. ⚠ 7/6 배치 15건 재확증 0 — KPMG 다른 발행물 2건에도 없음 → 1건 출처 강등. 구현 비용도 최고(이미지 자산 정책 선결)) | 카탈로그·사례집 | corporate·전체 | ⬜(1건 출처·승격 보류) |
| PG-prose_page | 문단 에세이 페이지 — 불릿 없이 문단 스택. 변형 3: ①중앙정렬 에세이(BOND trends_ai 5장) ②좌정렬 메모 prose+볼드 리드인(BOND 메모 3건 — 문서 전체가 prose) ③IR 유의사항/Disclaimer(카카오·네이버·삼성 모두 2페이지째) + Activate 테이크어웨이 스택 변형(볼드 런인 리드+헤어라인 룰, act25 001~003) | 서문·맺음·면책 | mono·corporate | ⬜(7건 재확증) |
| PG-metric_commentary | IR 원자 블록: 지표명 헤딩 + `+X% YoY, ±Y% QoQ` 델타쌍 헤드라인 + (YoY)/(QoQ) 라벨 불릿 + 분기 차트. 페이지당 1~2행 스택 (관찰 12+ — 카카오 016~019 2행형·네이버 003~008 1행형) | 실적·상태 보고 | corporate·전체 | ✅(7/7 R3) |
| PG-feature_grid_icon | 아이콘 상단 배지 + 볼드 헤드라인 + 1~2줄 설명, 3~4열 균일 카드 그리드(관찰 3 — dribbble_deck_shots_2026-07 01_agritech·07_hirely·16_edtech) | 정성 기능·역량 소개 | 전체 | ⬜(7/23 신규 — 정량 metric-card와 달리 아이콘·정성 설명 전용, 엔진 미구현) |

## C. 차트·다이어그램 (수치 비교 12종 + 관계·프로세스 4종)

| ID | 차트 | 용도 | 상태 |
|---|---|---|---|
| CH-비교 12종 | before_after·dumbbell·flow·big_number·gap_map·shift·funnel·donut·mirror_bars·rising_columns·pictogram·gauge | 수치 비교·비율·추이 | ✅ |
| ⚠ shift 주의 | 두 점-쌍(회색→강조 도트)이 연결선 약해 다크에서 화살표가 안 보이고 "같은 것 두 번"으로 읽힘(후추님 7/4 반복 지적). 증감 2값이면 **rising_columns/before_after 우선** | designer 회피 | — |
| CH-hub_cycle | 중심+궤도 순환 허브 | 관계·생태계 | ✅ |
| CH-arrow_flow | 셰브런 화살표 프로세스 | 인과·단계 | ✅ |
| CH-timeline_bars | 간트형 계단 타임라인 — 분기/마일스톤별 막대 높이 오름차순 + 라벨(관찰 재확증 3 — dribbble_deck_shots_2026-07 09_flume·13_show_your_work·24_noxan 로드맵 계단) | 순서·구간 | ✅ |
| CH-data_table | 액센트 헤더 데이터 표 | 지표 나열 | ✅ |
| CH-multi_line | 다계열 라인(관찰 8/8 dashboard + 4/5 report_ops) — role baseline/highlight로 선 분리 | 시계열 비교 | ✅(7/4 승격) |
| CH-progress_bar | 목표 대비 진척 막대: 트랙+채움 %(관찰 3 — report_ops·number=0~100 해석) | OKR/상태 진척 | ✅(7/4 승격) |
| CH-target_vs_actual | 계획 vs 실제 대비쌍(관찰 3 — series 연속 2개=1행·계획=점선 고스트) | 목표-달성 비교 | ✅(7/4 승격) |
| CH-rating_dots | N/10 도트 채움 레이팅(관찰 5 — report_ops 3 + 2R 별점 testimonial 2) | 정성 점수 | ⬜ |
| CH-radial_progress | 단일 링 진척 게이지·% 중앙(관찰 7+ — 2R 게이지 라이브러리·도넛% 다수 재확증) | 단일 KPI 진척 | ✅(7/4 승격) |
| CH-kpi_delta_card | 숫자+델타+미니추세 KPI 블록(관찰 11+ — dashboard 8 + report_ops 3 + 2R 델타스택·타깃블록) | 계기판 단위 | ⬜(델타·숫자블록은 ✅ — 미니추세 스파크라인만 백로그) |
| CH-puzzle/gear/polygon | 퍼즐·기어·다각형 인포그래픽(pop 스샷 관찰) | 구성요소·맞물림 은유 | ⬜ |
| CH-swot_quad | 2×2 SWOT/정성 사분면 — 중앙 십자축·highlight 사분면 틴트(관찰 4). 스펙: viz `"chart": "swot_quad"`, series 4개 = 사분면(`label`+`items` 문자열 배열·숫자 금지), metric_id 예외 유일 차트 | 전략·경쟁분석 | ✅(7/4 배치3) |
| CH-nested_circle | 중첩/겹침 원 다이어그램 — TAM/SAM/SOM 동심원 또는 그룹 값 벤다이어그램형, 라벨은 리더라인으로 옆에 배치(관찰 3 — dribbble_deck_shots_2026-07 03_board·20_holographik·27_exploration) | 시장규모·그룹핑 비교 | ⬜(7/23 신규) |
| CH-annotated_trend | 성장 서사 라인차트 주석 레이어 4종: 성장률 타원 콜아웃("+X%/Year")·보조 추세 화살표·끝점 굵은 수치·**이벤트 구간 세로 음영 밴드+상단 라벨**(usa_inc WWII·COVID / a16z "ICO boom" 에포크 밴드 흡수). 기존 multi_line 확장 (관찰 20+ — BOND 4/4 아이템·2015까지 10년 연속 + Activate/a16z 10) ⚠ 구현 선결: C6 계약상 title/note raw number 금지 — 파생값(성장률) metric 체계 설계 먼저 (7/6 코과장 리뷰) | 추세에 서사 싣기 | ✅(7/7 R3 — annotations 4종·파생 metric 계약·endpoint 이중라벨 수술) |
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
| DC-cover_glow_orb | 표지·아웃트로 다크 배경 위 대형 글로우 오브(radial 블러 — 솔리드 실루엣 아님). 관찰 6의 솔리드 블롭/다이아몬드는 **7/23 후추님 실측 기각("어설퍼")** — 글로우 변형만 채택 | ✅(7/23 — `page.cover_shape: "glow"` 단일 옵션, blob/diamond 코드 삭제. clo_it_planner_evolution 적용) |

## E. 컬러·타이포 규칙 (패밀리 공통 문법에서 승격된 원칙)

| ID | 규칙 | 근거 | 상태 |
|---|---|---|---|
| CL-single_accent | 단일 지배 액센트 (다크 7/8·미니멀 8/8·코퍼레이트 9/9) | _grammar | ✅(4 시스템) |
| CL-multi_pop | 다색 팝 t램프 순환 — pop 계열만 예외 허용 | pop 스샷 | ✅(pop 한정) |
| CL-muted_body_on_dark | 다크 본문은 순백 금지·60~75% 회색 (6/8) | _grammar/dark | ✅ |
| TY-extreme_ratio | 헤드:본문 극단 크기비 (미니멀 8/8) | _grammar/minimal | ✅(minimal) |
| TY-kicker | 초소형 자간 키커 라벨. 필/뱃지형 변형(eyebrow-chip)도 다수 재확증(관찰 5 — dribbble_deck_shots_2026-07 04_swipee·09_flume·17_clever·19_xpend·25_axo — 컬러 배경 필 안에 카테고리 태그) | _grammar · dribbble 2026-07 | ✅(필형은 기존 eyebrow-chip 레버로 이미 구현·designer 선택 시 적극 활용 권장) |
| CL-gradient_accent | 그라디언트 액센트를 지배색으로 (관찰 4 + dribbble 9 = 13+ — report_ops 2 + 2R Inside 무지개 웨이브·corporate 마젠타→퍼플 풀블리드 + dribbble_deck_shots_2026-07 04_swipee·06_quantum·07_hirely·09_flume·17_clever·19_xpend·25_axo 외. 평면 컬러블록보다 대각/방사 그라디언트가 다수 — "평면=구식, 그라디언트/글로우=고급" 인상의 핵심 레버) | inbox 실측 + dribbble 2026-07 | ✅(7/23 구현 — `.metric-card::before` 방사 글로우 + `.title-band` 대각 그라디언트, render_deck.py. 치수 불변·전 시스템 공용) |
| TY-source_infra | 출처 다층 체계: ① 차트 제목 안 "– 기간, per 출처" ② 하단 Note:/Source: 마이크로 캡션 ③ 번호 각주 1)2)3)·※사진 출처 분리(IR) ④ **데이터 성격 배지**(Activate "FORECAST" 배지·자체조사 스탬프·파트너 로고 박스 — 예측/실측/외부를 시각 구분). 실전 신뢰 문법의 핵 — 템플릿 46건 관찰 0 ⚠ 구현 선결: deck_spec `source`가 페이지 레벨 배열(viz/series 1:1 아님) → 스키마 확장 필요 + 현 source-row CSS가 한 줄 clip(nowrap+hidden, render_deck.py ~3038) — overflow 정책 먼저 (7/6 리뷰 실측) | **17/17 전 실전 아이템** — BOND 2015부터 10년 무결점·Activate 4층·KPMG 하우스·IR 3사 | ✅(7/7 R2 — viz 단위 캡션 자동 생성·short_name/period·칩 공존. 각주/배지 층은 R3+) |
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
  - **R2**: ✅ 완료(7/7 — commit 53d3f52·ef4c97a·54ca3a2·test 93/93·시각QA 본부 실측) TY-source_infra + PG-title_band
  - **R3**: ✅ 완료(7/7 — commit c4d4966·b7850ba·24f6a40·test 102/102·회귀 6/6·시각QA 실측) 파생 metric 계약 + annotated_trend + toc_progress + metric_commentary
  - **강등·보류**: PG-item_profile(재확증 0 — 1건 출처 강등 + 구현 비용 최고) · CH-photo_bar/logo_connector_map(자산 정책 선결)
  - 옛 "1순위 title_band·item_profile" 표기는 리뷰로 교정됨 — 구현 비용 실측(deck_spec source 구조·C6 계약) 반영.
- 미등재 기록 (1건 출처 — 다음 수집 배치 재확증 대상): DC-pixel_block(a16z)·CH-redline_edit(usa_inc 업데이트판 문법)·PG-results_outlook(삼성 좌Results/우Outlook)·CH-ranked_leaderboard(KPMG 오토)·PG-boxed_section_label(BOND 메모 간지)·PG-perspective_sidebar(Activate 의견 박스 — KPMG 틴트 카드와 병합 시 3+)·PG-contacts_closing(KPMG 하우스)·히트 열 테이블(a16z 008)

주의(추출 에이전트 반대신호 — 숨기지 않음): corporate/data 다수가 "부품 카탈로그"라 choropleth/funnel/gauge 관찰수는 부품 존재이지 페이지 문법 아님(과대 계상 주의). pricing/running_head 외 신규 후보 관찰수는 00 컨택트시트 의존도 높음 → 승격 확정 전 본문 슬라이드 추가 실측 권장.

## 2026-07-23 드리블 컬렉션 배치 (30장 — 후추님 "레이아웃도 최대한 많이 확인해서 규칙 저장해")

수집 = `TickDeck/.claude/research/dribbble_deck_shots_2026-07/`(01~30 + manifest.json). 클차장이 30장 전량 직접 열람(팔레트+레이아웃 DNA 동시 추출 — 묶음 판단은 위임하지 않음, 후추님 "많은 게 정답이 아니라 묶음이 어울리는 것" 원칙).

- **승격(⬜→✅, 실구현)**: CL-gradient_accent — `render_deck.py`에 `.metric-card::before` 방사 글로우 + `.title-band` 대각 그라디언트 추가(치수 불변·전 테마 공용). IT기획자 리포트(clo_it_planner_evolution)에 적용해 시각 확인 완료.
- **신규 등재(⬜ 백로그)**: PG-feature_grid_icon·CH-nested_circle·DC-cover_blob_shape (관찰 3~6, 상세는 각 표 참조).
- **기존 항목 재확증·관찰수 갱신**: PG-running_head·CH-timeline_bars·TY-kicker(필형).
- **반대신호(숨기지 않음)**: running_head를 title_band 전제로 짜인 기존 페이지에 그대로 스왑하면 overflow 재발(5장 실측) — 크롬 스타일 전환은 콘텐츠 밀도 재적합을 동반해야 함, 사후 테마 교체로 안 됨.
- 1~2건 관찰 개별 버릇(빈티지 콜라주 13_show_your_work 등)은 원칙대로 미등재.

## 2026-07-23 GMS 아카이브 배치 1 (후추님 본인 저작 — 3사 10년 실무 문법)

수집 = `~/Documents/이전회사_제안서_아카이브_2026-07/GMS_2018-21/` 197건(선별본) 중 대표 7덱 클차장 직접 열람: 롯데푸드 홈페이지 제안서(넥스트컬쳐 2021)·BMW 교육소개(GMS 2018)·JLRK 교육소개(2018)·현대차 제안(2019)·페이센스 what we do(2021)·시스루 양식 v2.0(하우스 템플릿)·MaF 피치덱(2018). **드리블과 결정적 차이 = 전부 실제 수주/납품된 본인 저작** — "팔려는 템플릿"이 아니라 "일한 덱"이라 근거 등급이 실전 코퍼스(BOND·IR)급.

| ID | 패턴 | 관찰 | 상태 |
|---|---|---|---|
| CL-client_brand_accent | **수신자(클라이언트) 브랜드색을 덱 액센트로 차용** — 에이전시 자기 색이 아니라 받는 회사 색으로 팔레트 파생(BMW 시안·JLRK 네이비·현대 블루·롯데푸드 레드·아우디 레드). 로고도 클라이언트 것을 상단 크롬에 | 5 (3사 10년 관통) | ⬜(신규 — TickDeck엔 없는 문법. 납품·제안 장르에서 팔레트 동적 파생 레버로 승격 후보. 후추님 커리어 자체가 이 문법의 실증) |
| PG-photo_cover_dim | 풀블리드 제품 사진 표지 + 다크 딤/반투명 밴드 + 백색 타이틀. 간지도 같은 문법(사진+딤+좌하단 또는 중앙 타이틀) | 표지 4·간지 3 | ⬜(사진 자산 정책 선결 — 기존 DC-photo_frame과 같은 보류 사유) |
| TY-underline_title | 좌정렬 타이틀 + 풀폭/부분 언더라인 룰(시스루 양식·페이센스 러닝헤드·BMW 시안 언더라인·JLRK 헤어라인). title_band(색면)와 다른 "선" 기반 제목 크롬 | 4 | ✅(7/23 구현 — `cover_layout:"ruled"` 표지·outro 골격: 백지+풀폭 언더라인+장식(밴드 티커·모티프) 억제. 후추님 "표지 하단 4줄 그대로면 디자인 바뀐 느낌 안 남" 지적의 근본 대응 — 표지 뼈대 자체를 교체하는 첫 레버) |
| CH-spec_table | 라벨-값 자간정렬 스펙 테이블(회사명·대표이사·설립일… 라벨 양쪽정렬+값 좌정렬) — 회사소개 정형 문법 | 3 | ⬜ |
| PG-index_pagenum | 목차 항목에 페이지번호 우측정렬(+섹션 볼드/서브 들여쓰기 위계) — 현 index 레이아웃엔 페이지번호 없음 | 3 | ⬜(경량 확장) |
| (기록만) Confidential 푸터·코너 색면 블록 크롬(MaF)·사선 패럴렐로그램 밴드(현대차) | 개별 버릇 1~2건 — 원칙대로 미등재, 여기 한 줄 기록만 | 1~2 | — |

묶음 2건은 BUNDLES.json에 등재(B-premium_photo_overlay·B-agency_minimal_white). **손상 고지**: 리커버 폴더 최상위 67건(NXC 시절)은 USB 원본부터 파손(해시 대조 확인) — NXC 웹에이전시 문법은 살아남은 넥스트컬쳐 2건(롯데푸드·페이센스)+시스루 하위 26건으로만 흡수. 배치 2 = 시스루 HYBE/엔터 문법·GMS 잔여.

### GMS 아카이브 배치 2 (7/23 — A7·행복나눔재단·BTS 와이어프레임·Unsung Hero·JLRK Defender 5덱 추가 열람)

- **기존 항목 재확증**: CL-client_brand_accent 관찰 5→**6**(행복나눔재단 덱이 세상파일 CI 퍼플·오렌지 차용) · CH-spec_table 3→**4**(Defender 사다리꼴 라벨 필+값 언더라인 변형) · DC-side_wordmark **실무 실증 추가**(행복나눔재단 좌측 세로 러닝헤드 — 세로 회전 텍스트+세로 헤어라인, 본문 전 페이지 반복) · TY-headline_highlight 1→**3**(A7 "Luxury/Sales" 단어 단위 2색 강조 + 행복나눔재단 키워드 색강조 — a16z 형광마커의 색글자 변형, 1건 출처 문제 해소)
- **신규 관찰(개별 버릇 — 기록만)**: Unsung Hero(2018)의 색면 2분할 스플릿(좌 네이비 텍스트+골드 거대 수치 오버랩 / 우 옐로+컷아웃 사진) — 강렬하지만 1건. A7 키노트 블랙(순블랙 텍스처+중앙 미니멀 타이포+딤 사진 콜라주)은 묶음 B-keynote_black으로 등재.
- **웹기획서 장르 노트 (후추님 "시스루는 대부분 웹기획서라 참고해서" 지시)**: 시스루·NINEFIVE 화면설계서 캐논 문법 = ① 백지 표지(클라이언트명 소·제목 대 좌정렬 + Published by + Confidential) ② 다크 차콜 간지(키커+타이틀 좌정렬 — TickDeck divider와 동형) ③ 화면설계 프레임: 상단 경로 메타바(`BTS / Main Page` + 플랫폼) / 좌 와이어프레임 캔버스 + 원형 번호 배지 / 우 Description 번호 대응 표 / 하단 프로젝트명 바. + 시스루 양식 v2.0의 Document History 표·백지 간지 블랙/그레이 위계. → **TickDeck에 "화면설계서" 장르가 생기면 이게 정본 골격** — 지금은 장르 미존재라 아키타입 백로그로만(AR-webplan ⬜). 개별 시각 패턴 추출은 안 함(기획 문서라 장식이 없는 게 문법).

### GMS 아카이브 배치 3 (7/23 — NO NAME USB 브랜드 순정 템플릿. 아우디 공식 확인)

아우디 공식 PPT 템플릿(Audi templates 16_9_VdT — 브랜드 본사 배포 순정) 열람. **근거 성격이 특별** — 개인 취향이 아니라 프리미엄 브랜드가 사규로 확정한 하우스 스타일:

- **화이트 프리미엄**: 순백 지면 + 제품 부분 클로즈업(그릴·헤드라이트만 크게, 지면 밖으로 페이드) + 좌하단 블랙 볼드 타이틀. 다크가 아닌 백지가 프리미엄이라는 반례 — dark_premium 일변도 교정 재료. (JLRK 교육소개 백지+사진 스트립과 합쳐 관찰 2)
- **CL-micro_accent**: 브랜드 레드를 불릿 셰브런(›)·로고에만 — 제목·수치·표에도 안 씀. CL-single_accent의 극단형(액센트 면적 1% 미만). 관찰 1(공식 규정이라 가중치 있음) → ⬜ 기록
- **컬럼 분절 상단 룰 테이블**: 표 헤더 위 가로줄이 컬럼마다 끊어져 있음(전폭 1줄 아님) + 볼드/레귤러 행 위계로 시간표 조직. CH-fin_table·data_table과 다른 표 크롬. 관찰 1 → 기록만
- 전 페이지 푸터: 좌 페이지번호+문서 메타(Title·Department·Name·Date) / 우 로고+태그라인 — PG-running_head 브랜드판 재확증

Jaguar/Land Rover 공식 템플릿 2종 확보·열람 완료 — **3사 순정 비교 성립**:

- **PG-letterbox_photo_band (신규 ⬜, 관찰 3)**: 상하단 백지 프레임(상단 우측 로고만·하단 좌 메타/우 Confidential) + 가운데 전폭 사진 밴드 — Jaguar·Land Rover 공식 공통 골격. JLRK 교육소개(02) 표지가 이 순정을 그대로 차용했음이 확인 → **CL-client_brand_accent는 색만이 아니라 골격까지 차용하는 문법**이라는 실증(제안서가 수신자 하우스 스타일을 통째로 입는다).
- 3사 순정 공통점: **전부 화이트 지면**(다크 아님)·로고는 우상단 고정·액센트 극절제·Confidential 크롬. 프리미엄 자동차 3사가 수렴한 "백지 프리미엄" — dark_premium 일변도 교정 근거가 관찰 1→3으로 강화.
- 차이: Audi = 부분 클로즈업 페이드 / JLR = 레터박스 풀샷 밴드.

### 배치 4 (7/23 — 제대리(Gemini) 리디자인 1건 역참조. 후추님 "좋은 구조는 흡수하자")

제대리가 clo_it_planner 덱을 보고 만든 리디자인 PDF(기획자 커리어 리포트-2026·13장·후추님 전달)에서 구조만 추출. **출처 1건 + AI 생성물이라 근거등급 최하** — 단 후추님 실물 검토를 거쳐 지시된 흡수라 등재. 콘텐츠 규율은 역면교사: 표 10행→5행 손실·출처 각주 소실·외부 이미지 URL 참조(저작권·비재현) — **구조만 가져오고 C6 규율은 우리 것 유지.**

| ID | 패턴 | 상태 |
|---|---|---|
| DC-side_gradient_panel | 전 페이지 우측 ~20% 폭 미묘한 사선 명암 패널 — 백지 지면에 깊이 주는 상시 크롬. 코너 세리프 자간 워드마크와 세트 | ⬜(구현 저비용 — slide_bg 레이어 추가만) |
| PG-divider_rule_center | 백지 간지: 상단 짧은 액센트 룰(~90px) + 중앙 타이틀 + 뮤트 부제 — quiet 간지의 라이트·중앙판 | ⬜(경량) |
| CH-onbar_label 확장 | 막대 안 흰색 값 라벨 — CH-quarterly_bars "온바 라벨"과 합치(IR 3사 + 제대리 = 독립 재확증). gap_map·before_after로 확장 후보 승격 | ⬜(기존 확장) |
| PG-stat_inline_list | 빅넘버+설명 인라인 스탯 리스트("**36%** 상당수 업무에 사용") — 카드 없이 숫자 위계만으로 | ⬜ |
| CH-donut_legend | 도넛 + 색칩·라벨·값 범례 리스트 조합(도넛 단독보다 판독성) | ⬜(donut 확장) |
| PG-timeline_scenario | 가로 축선+도트 위아래로 시나리오 카드 지그재그 교차 — scenario_cards 3열과 다른 화법 | ⬜ |
| PG-checklist_conclusion | 결론 페이지: ✓ 아이콘 + **볼드 리드**: 설명 행 카드 스택 — p20 "리드: 설명" 형식의 카드판 | ⬜ |
| (재확증) PG-feature_grid_icon | 아이콘+제목+본문 3열 카드 — 관찰 3→**4** (제대리 담론 페이지) | ⬜ 유지 |

### 배치 5 (7/23 — HWA USB 복구본. 카빙 복구 문서 1,538건 중 신규 대표 8종 열람·GMS 기흡수분 중복 제외)

수집 = `~/Documents/HWA_복구_2026-07/문서_정리/` (PhotoRec 카빙이라 파일명 소실·f넘버). 열람 8종: **TAETEA 대익보이차 제안(NEXTCULTURE·37p·최다 수확)**·한국미스미 EC 리뉴얼(NEXT CULTURE 2018·12p)·CSES 2019 연차보고서(인쇄 편집물·20p)·환전지갑 하나멤버스(eWIDEPLUS 2018·84p)·특허기술 제안 템플릿(상용·26p)·대출왕 무료홈페이지(2019·36p)·INFO GRAPHIC 팩(상용 템플릿 160p)·인포뱅크 스마트카(2018·등재 스킵 — 2010년대 관습뿐). **출처 정직 고지**: 이 배치는 본인 저작 확증이 아니라 후추님 소장 아카이브(제작사 혼재) — 후추님 7/23 "내가 만든거 아니라도 잘 만든건 참고해" 지시로 외부 제작물 포함 등재. 동구밭 건은 워드형 연구 보고서라 디자인 제외·내용 흡수 후보로 분류.

| ID | 패턴 | 관찰 | 상태 |
|---|---|---|---|
| PG-fixed_left_rail | **좌측 고정 화이트 레일(~1/3, 섹션 넘버+타이틀 상주) + 우측 2/3 가변 패널**(브랜드컬러 면/풀블리드 사진/딤 사진 교대) — TAETEA 포트폴리오 섹션 10p+ 연속. 레일이 항상성, 우측이 리듬을 만든다 | 1덱 10p+ | ⬜(신규 — 페이지 아키텍처급. 현 엔진에 없는 골격) |
| PG-case_pair_rhythm | 케이스당 2페이지 리듬: A=클라이언트 브랜드색 패널+디바이스 목업+한줄 인용 / B=딤 사진+인용 헤드라인+설명+Scope 리스트 — 포트폴리오 장르 캐논 | 케이스 5쌍 | ⬜(포트폴리오 장르 생기면 정본 후보) |
| TY-quote_bullet_list | 리스트 불릿을 큰따옴표(❝)로 — Scope of work 전 케이스 반복. 불릿의 "말해주는" 뉘앙스 | 1덱 6회+ | ⬜ |
| ST-example_stamp | 기울인 적색 아웃라인 **"예시" 도장**을 목업·더미 데이터에 — 시안임을 지면에서 정직 표기. C6(콘텐츠 정직) 철학과 정합하는 장치 | 1덱 5회+ | ⬜(저비용·TickDeck 시안 렌더에 차용 가치) |
| CH-goal_convergence | 하단 다크 박스 4(현황) → 상향 화살표 → 상단 아웃라인 박스 안 3행 스택+인용 명제 — "현황이 목표를 밀어올리는" 수직 수렴 화법 | 1 | ⬜(기록) |
| CH-platform_blockmap | 최상단 액센트 헤더밴드(플랫폼명) + BI 행 + 모듈 칼럼 6열(칼럼헤더+화이트 칩 스택) → 합병 화살표 → 하단 다크 요약 4 — 서비스 아키텍처 전용 블록맵 | 1 | ⬜(기록) |
| TY-stat_hook_block | 헤드라인 문장 속 핵심 숫자만 반전 색면 블록("방문객 중 **98%**가 떠나갑니다") — 숫자가 문장을 뚫고 나오는 훅 | 1 | ⬜(기록 — 미스미) |
| CH-funnel_dropout | 가로 퍼널 축(단계 아이콘) + 각 단계 위로 이탈률 % 콜아웃 화살표 — 전환/이탈 서사 전용 | 1 | ⬜(기록 — 미스미) |
| CH-qa_chevron_rows | Q(연회색 셰브론)→A(옐로 셰브론) 좌우 페어 행 반복 — 질문 주도 논증 골격 | 1 | ⬜(기록 — 미스미) |
| PG-chapter_card | 다크 지면 중앙에 부유하는 화이트 카드 간지(원형 챕터 넘버 + 하단 액센트 밴드) — 간지의 카드판 | 1 | ⬜(기록 — 상용 템플릿) |
| CH-problem_solution_pair | 문제(다크 헤더 카드) ↔ 해결(액센트 헤더 카드) 좌우 대비 — 같은 행수·같은 넘버링으로 1:1 대응 강제 | 1 | ⬜(기록 — 상용 템플릿) |
| PG-question_band_footer | 매 페이지 하단 풀폭 그라디언트 밴드에 수사 질문/결론 1문장("~안녕하십니까?") — divider_rule_center 결론행의 세일즈판. 반복이 만드는 최면 리듬 | 1덱 전 페이지 | ⬜(기록 — 세일즈 장르 한정) |

- **기존 재확증**: CL-client_brand_accent 관찰 6→**10** (TAETEA 케이스별 브랜드색 스위칭 — LG 마젠타·지멘스 틸·청와대 네이비·롯데 레드. 한 덱 안에서 페이지마다 수신자색이 바뀌는 극단형 실증) · PG-divider_rule_center 재확증(TAETEA Development plan 전 페이지 하단 룰+결론문+적색 키워드 강조) · TY-underline_title 재확증(미스미 좌측 틱바+대문자 섹션 라벨 변형) · CH-spec_table 재확증(TAETEA NEXTCULTURE 소개 라벨-값)
- **연차보고서 장르 노트 (AR-annual_editorial ⬜ 신설)**: CSES 2019 = 인쇄 편집물 캐논 — ① 레터폼 크롭 수평 스플릿 표지(백지/브릭레드 2분할 위에 거대 이니셜 걸침) ② 아웃라인(획 없는) 대문자 타이포 제목 ③ 빅 아웃라인 숫자 KPI 그리드(아이콘 위·얇은 숫자·캡션 아래·3×3·좌측 컬러 탭 카테고리) ④ 곡선 연결 지그재그 연혁 타임라인 ⑤ 사진 위 화이트 시트 오버레이(지면 대부분 덮는 카드) ⑥ 세로 러닝 페이지넘버. 스크린 덱 아닌 인쇄 장르라 AR-webplan처럼 아키타입 백로그로만.
- **INFO GRAPHIC 160p (상용 팩 — 7/23 전수 160/160장 열람 완료. 후추님 "전체를 다봐야해" 지시)**: 1차 8장 표본의 "대부분 중복" 판단을 정정하고 전수 확인. 등재 5건: ① **CH-hierarchy_pyramid** ✅ — 계층 피라미드/깔때기/동심원 스택. 전수 결과 160장 중 30장+가 이 계열(3D·플랫·튜브·동심원·계단) = 팩이 통째로 증언하는 수렴 문법. **차용 정본형 = 플랫만**(p157 플랫 3단+우측 수평 룰 라벨·p41 플랫+회색 행 밴드) — 3D 변주는 전부 avoid ② **CH-quadrant_matrix** ✅ — 축 화살표 2×2 사분면. SWOT 4변주(퍼즐·순환화살표·원 클러스터·헥사곤 사분할, p11~15)가 전부 이 문법의 응용 + **SPC 보고서 실전 사용 = 독립 출처 2** ③ **DC-leader_line_callout** ⬜ — 요소→가는 리더라인→아이콘 배지+라벨. 전 구간 수십 회 관통 + TAETEA·CSES 변형(관찰 3+) ④ **CH-gantt_schedule** ✅(신규 — 전수에서 발견) — 간트 3변주: 그리드 간트(청 헤더 표+색 바, p20)·**달력 간트**(월 캘린더 위 컬러 바 스팬, p21)·마일스톤 축 간트(월 밴드+다이아 마커+상하 콜아웃, p22~23). 제안서 필수 화법(추진일정)인데 현 엔진에 없음 — author-style §6 로테이션 매트릭스와 짝 ⑤ **CH-pictograph_ratio** ✅(신규) — 사람 픽토그램 N개 중 색칠 개수로 비율(9/14=55%, p94). 사물 메타포와 달리 isotype 통계 시각화 정통 계보라 비즈니스 정합. (기록만: 캐스케이드 화살표 스텝 p117 — 화살표 바 계단 배열+아래 설명 칼럼·1건 / 6열 컬러 헤더 표+토탈 행 p26 = CH-fin_table 합계행 재확증) **avoid 확정(전수 근거)**: 3D 스큐어모피즘 전반(기어·튜브·큐브·구 단면·실린더 게이지)·사물/인체 메타포에 데이터 얹기(온도계·플라스크·연필·나무·두상·메가폰·실루엣 색층·클립아트 인물·말풍선 군집) — 팩의 절반 이상이 여기 해당, 2015년대 유행이자 현 하우스 취향(플랫·톤다운)과 정반대. 원본 = `문서_정리/PPTX/f0383680.pptx`
- **환전지갑 84p 확장 열람 (7/23 후추님 "폰트가 별로라서 그렇지 전체적으로는 좋네 — 흡수해줘")**: 폰트는 변환 fallback(임베디드 소실)이라 타이포 판단 제외, 골격·방법론 문법 흡수. ① **AR-ux_benchmark** ⬜ (장르 노트) — 경쟁사 UX 해부 표준 프레임: 좌 "메인 UX 분석"(스크린샷+레이아웃 오버레이) / 우상 "프로세스 Flow N단계"(스크린 릴+번호 스텝 축) / 우하 "입력 폼 및 특징" / ★=마찰 지점 — **경쟁 4사(신한·우리·국민·네이버페이)를 동일 프레임으로 반복**해 비교 가능성을 만드는 게 핵심. AR-webplan(화면설계서)의 짝인 "UX 벤치마크" 장르 캐논 ② **PG-persona_journey** ⬜ — 좌 퍼소나 카드(초상+라벨 필+티얼 원+▼+영문 별명) + 우 가로 여정 축(원 노드+감정 스마일+점프 화살표+★핵심 순간) + 하단 Need(회색)/problem solving(다크) 2행 대응 ③ **CH-phone_flow_map** ⬜ — 스마트폰 픽토그램을 노드로 쓴 화면 흐름도, 색=상태(파랑 메인·블랙 서브·레드 예외 분기) ④ 소소 재확증: 결론 페이지 적색 판정 글자(CL-semantic_color 실무 실증)·다운워드 셰브론 카드·브레드크럼 러닝헤드·듀얼 로고 푸터(좌 클라이언트/우 제안사 — CL-client_brand_accent 크롬판)

### 왜 "3회 이상"만 등재하나 (후추님 질의 — 정직한 답)

기존 라이브러리 규칙("관찰 1~2건은 개별 버릇, 등재 X" — 6/28 이전부터 있던 원칙, 이번에 새로 만든 기준 아님)을 그대로 적용한 것. 근거: 관찰 1~2건으로는 "여러 사람이 수렴한 진짜 문법"과 "그 디자이너 한 명의 우연한 선택"을 구별 못 한다 — 3회+(특히 서로 무관한 출처)면 우연이 아닐 확률이 올라간다는 약한 통계적 프록시.

**단, 이번 드리블 배치엔 이 기준이 평소보다 약하다는 걸 숨기지 않는다**: BOND·Activate·KPMG·IR 3사 같은 기존 코퍼스는 "실제 발행 문서가 몇 년째 반복하는 하우스 스타일"이라 3회는 꽤 강한 신호였다. 반면 드리블은 판매용 템플릿 마켓 — 디자이너 각자가 "이번엔 남들과 다르게" 튀려고 만든 포트폴리오 조각들이라, 3장에서 같은 모티프가 보이는 건 "2026년 지금 드리블에서 유행 중인 것"일 수도 있고 "여러 산업이 수렴한 문법"일 수도 있다 — 이 배치만으론 둘을 못 가른다. 그래서 신규 항목은 전부 ✅(엔진 구현) 아닌 ⬜(백로그)로 두거나, 구현한 것도 "관찰 N" 표기로 근거 강도를 그대로 노출해뒀다 — 실전 리포트 문법(§ 하단 "실전 리포트 문법" 섹션)만큼의 권위는 아직 없다는 뜻.

### 묶음(Bundle) 기록 — 원자 패턴이 아니라 "같이 나온 조합"으로도 남긴다

묶음 정본은 `v3/axis2_layouts/BUNDLES.json`이다. 신뢰 등급은 단일 출처 참고용 `observed_1` → 독립 출처 2개 이상 또는 실전 run과 후추님 승인을 거친 `reconfirmed` → 확정 취향인 `house` 순이다.
원자 상세 정본은 이 문서에 유지하며, ⬜ 원자를 참조한 묶음은 designer 기존 규칙에 따라 사용할 수 없다.

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
