# TickDeck v3 — 세션 핸드오프 (2026-06-24 EOD)

> 다음 세션의 나에게. 오늘 = 2026 마케팅 덱 재제작 + **엔진 다양화 업그레이드** + **디자인 흡수 백로그**. 여기서 이어간다.
> 메모리(자동 로드): `tickdeck-v3-pivot` · `deck-pipeline-system` · `deck-font-safety` · `deck-single-source-ranking` · `deck-layout-deliberate`. 먼저 이거 본다.

## 한 줄 상태
보강 flow로 **2026 마케팅 덱 v2 완성·렌더됨**(틸·사업화형·단일출처·컨설팅 인용). 엔진에 **레이아웃 직접지정·다크 간지·키워드 accent·섹션 내비탭**을 깔았고(모든 덱 적용), **디자인 흡수 Phase 1 주요항목 완료**. 다음 = **Phase 2(차트 신규)**.

## 산출물 위치
- 작가 원고: `v3/authored/2026_마케팅_트렌드_v2_page_specs.json` (SoT)
- 렌더: `v3/output/2026_마케팅_트렌드_v2_teal/deck.pdf` (+slide_N.png). 빌드 명령:
  ```
  cd v3/pipeline && python3 build_deck.py \
    ~/Projects/Automation/sinya/experiments/deepresearch/runs/20260619_1408_2026_마케팅_트렌드.json \
    --page-specs ../authored/2026_마케팅_트렌드_v2_page_specs.json \
    --out ../output/2026_마케팅_트렌드_v2_teal --theme TD_trend_teal --allow-render-failure
  ```
  (result_json은 topic 로더용일 뿐. --page-specs가 실제 입력.)
- ② blueprint: `v3/authored/2026_마케팅_트렌드_v2_blueprint.json`
- 디자인 정본: `v3/review/LAYOUT_TAXONOMY.md`(43종 2패밀리) · `v3/review/DESIGN_LEARNINGS.md` · `v3/review/DESIGN_ABSORPTION_BACKLOG.md`(★흡수 트래커·진행상태)
- 채굴/디자인 digest: `v3/review/intake/content_*.md` · `design_*.md` · `design2_*.md`

## ⚠️ 오늘 한 엔진 변경 (미커밋 — 되돌리지 말 것 · 커밋 권장)
**`Think/tools/deck_harness/src/build.py`:**
- `==키워드==` 헤드라인 accent 마크업(`render_headline_piece`/`HEADLINE_INLINE_RE`) + `.headline-accent`
- 섹션 내비탭: `render_signature_frame` 탭바(`deck.chapters` 사용·현재 강조) + `SECTION_NAV_SKIP`
- 신규 테마 5종: `TD_trend_coral` · `TD_trend_teal`(현 채택) · `TD_trend_violet` · `TD_trend_fuchsia` · `TD_trend_amber` (WGSN S/S26 키컬러 기반)

**`Think/tools/deck_harness/styles/tokens.css`:** `.headline-accent` · `.signature-nav`/`.nav-tab`/`.is-active`

**`TickDeck/v3/pipeline/axis1_to_deck.py`:**
- `EXPLICIT_LAYOUTS` + `bind_explicit_layout` + `explicit_layout_for` — page_specs에서 **레이아웃 직접지정**(navy-focus·narrative_centered 등 패스스루)
- `bind_section_divider`: `page.dark`/`page.style`로 **다크 간지**(틸 다크 팔레트 + 챕터숫자 워터마크)
- `build_deck`: `deck.chapters` 추출(목차 axes에서) — 내비탭용

## 다음 할 것 (DESIGN_ABSORPTION_BACKLOG.md 순서)
1. **Phase 2 차트 신규**(우선) — 각 새 렌더러 in deck_harness: 히트맵 매트릭스 · 미러 분기막대 · 상승컬럼+멀티플라이어 브래킷 · 덤벨 도트플롯 + bar 델타 주석. (단색+명도램프 철학 유지·자동생성 가능한 것만.)
2. **Phase 3 구조 위젯** — 비교 매트릭스표 · 피라미드 계층도 · 노드-커넥터 분기도 · 틴티드 스탯카드 그리드 · 지그재그 프로세스 · 혼합 통계 대시보드. (top 6~8만 선별.)
3. **Phase 4 색 동적화** — 섹션별 컬러코딩 · 콘텐츠/사진에서 색 생성.
4. **Phase 5 = B 이미지** — v2 Pexels 연동을 v3로(사진=표지·디바이더 한정·데이터/본문 금지) + 지배색 추출.
- 매 항목: 렌더·슬라이드 PNG 검증·후추님 보고. content_kind→layout은 `axis2_layouts/components/manifest.json`(현 20종 라우팅), 직접지정은 `EXPLICIT_LAYOUTS`.

## 현 덱 폴리시 미결(작은 것)
- p7 navy(블루)와 다크 간지(틸 다크)가 **다른 다크** → 한 톤(틸 다크)으로 통일.
- navy-focus 카드 여백(내용 짧을 때 휑함).

## 작가 규율 (오늘 후추님 교정 — 반드시 지킴)
1. **내용 먼저 → 양식 의도 선택**(겹침 최소·흐름 적합). content_kind에 양식 수동 위임 금지. 2패밀리(고정헤드 A / 가변헤드 B)로 구분. = `deck-layout-deliberate`
2. **데이터 = 한 출처 전체 순위/분포**(여러 출처 cherry-pick 금지). = `deck-single-source-ranking`
3. **서체 = 맑은고딕 우선**(portability). 세리프 페어링 스킵. = `deck-font-safety`
4. **적합 > 변주**(변주 욕심에 안 맞는 양식 고르지 말 것 — 오늘 p13 라인차트 실패 교훈).
