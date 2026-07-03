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
| PG-mosaic_tiles | 크기가변 사진/블록 모자이크(관찰 6/8 magazine) | 화보 타일 | serif | ⬜ |
| PG-running_head | 상단 3점 러닝헤드 프레임(관찰 7/8 magazine) | 좌 페이지·중 브랜드·우 날짜 | serif | ⬜ |
| PG-pricing_cards | 가격/플랜 카드 열(pop 스샷 관찰) | 옵션 비교 카드 | pop·dark | ⬜ |
| PG-nav_chrome | 상단 탭바/아이콘 러닝헤드 전 슬라이드 반복(관찰 2 — report_ops) | SaaS/상태보고 톤 | mono·pop | ⬜ |
| PG-split_status | 좌 정성서술 + 우 정량지표칩 상태페이지(관찰 2 — report_ops) | 상태·리스크 보고 | 전체 | ⬜ |
| PG-profile_row | 아바타+이름 인물 카드 열(관찰 3 — report_ops) | 팀·전문가 소개 | 전체 | ⬜(사진 자산 정책 미정) |

## C. 차트·다이어그램 (수치 비교 12종 + 관계·프로세스 4종)

| ID | 차트 | 용도 | 상태 |
|---|---|---|---|
| CH-비교 12종 | before_after·dumbbell·flow·big_number·gap_map·shift·funnel·donut·mirror_bars·rising_columns·pictogram·gauge | 수치 비교·비율·추이 | ✅ |
| CH-hub_cycle | 중심+궤도 순환 허브 | 관계·생태계 | ✅ |
| CH-arrow_flow | 셰브런 화살표 프로세스 | 인과·단계 | ✅ |
| CH-timeline_bars | 간트형 계단 타임라인 | 순서·구간 | ✅ |
| CH-data_table | 액센트 헤더 데이터 표 | 지표 나열 | ✅ |
| CH-multi_line | 다계열 라인(관찰 8/8 dashboard + 4/5 report_ops) — role baseline/highlight로 선 분리 | 시계열 비교 | ✅(7/4 승격) |
| CH-progress_bar | 목표 대비 진척 막대: 트랙+채움 %(관찰 3 — report_ops·number=0~100 해석) | OKR/상태 진척 | ✅(7/4 승격) |
| CH-target_vs_actual | 계획 vs 실제 대비쌍(관찰 3 — series 연속 2개=1행·계획=점선 고스트) | 목표-달성 비교 | ✅(7/4 승격) |
| CH-rating_dots | N/10 도트 채움 레이팅(관찰 3 — report_ops) | 정성 점수 | ⬜ |
| CH-radial_progress | 단일 링 진척 게이지·% 중앙(관찰 3 — 최대 3링·다중이면 t램프) | 단일 KPI 진척 | ✅(7/4 승격) |
| CH-kpi_delta_card | 숫자+델타+미니추세 KPI 블록(관찰 8/8 dashboard + 3/5 report_ops) | 계기판 단위 | ⬜(델타까지는 ✅) |
| CH-puzzle/gear/polygon | 퍼즐·기어·다각형 인포그래픽(pop 스샷 관찰) | 구성요소·맞물림 은유 | ⬜ |
| CH-choropleth | 지도 코로플레스(관찰 corporate 1) | 지역 분포 | ⬜(관찰 1 — 보류) |

## D. 장식·오브제 레버 (시스템 토큰에 색 위임 — 스타일 복제 금지)

| ID | 레버 | 상태 |
|---|---|---|
| DC-ghost_word · cover_sheen · spine_label · eyebrow_chip · divider quiet/standard · cover center/corner · divider_variant accent · hero_title | 기존 변주축 묶음 | ✅ |
| DC-offset_block | 빅넘버 뒤 오프셋 컬러블록(관찰 4/8 minimal B형) | ✅(minimal) |
| DC-depth_card | 바탕+1단 밝은 카드 부양(관찰 6/8 dark) | ✅(dark) |
| DC-pill_metric | 다색 필 메트릭 블록(pop 스샷) | ✅(pop) |
| DC-outline_number | 대형 아웃라인 숫자 오브제(관찰 2/8 dark·mono 간지) | ✅(mono 간지) |
| DC-photo_frame | 기하 마스크/라운드 사진 프레임(관찰 다수) | ⬜(사진 자산 정책 미정) |

## E. 컬러·타이포 규칙 (패밀리 공통 문법에서 승격된 원칙)

| ID | 규칙 | 근거 | 상태 |
|---|---|---|---|
| CL-single_accent | 단일 지배 액센트 (다크 7/8·미니멀 8/8·코퍼레이트 9/9) | _grammar | ✅(4 시스템) |
| CL-multi_pop | 다색 팝 t램프 순환 — pop 계열만 예외 허용 | pop 스샷 | ✅(pop 한정) |
| CL-muted_body_on_dark | 다크 본문은 순백 금지·60~75% 회색 (6/8) | _grammar/dark | ✅ |
| TY-extreme_ratio | 헤드:본문 극단 크기비 (미니멀 8/8) | _grammar/minimal | ✅(minimal) |
| TY-kicker | 초소형 자간 키커 라벨 (5/8+ · report_ops 다수) | _grammar | ✅ |
| CL-gradient_accent | 그라디언트 액센트를 지배색으로 (관찰 2 — report_ops) | inbox 실측 | ⬜ |

## 갱신 규칙

- 새 레퍼런스에서 관찰된 패턴: 기존 ID면 관찰수 갱신, 새로우면 ⬜로 등재 (추출 에이전트가 제안 → 클차장 병합)
- ⬜ → ✅ 승격은 관찰수·판매 임팩트 순 라운드 처리, 구현은 항상 시스템 무관 부품 + 색·서체는 토큰 위임
- 관찰 1~2건짜리 "개별 버릇"은 등재하지 않는다 (패밀리 시트의 개별 버릇 원칙과 동일)
