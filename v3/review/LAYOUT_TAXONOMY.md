# 레이아웃 택소노미 — 엔진 전수 카탈로그 (정본)

> 2026-06-24 · 후추님 지적("양식을 헤드 거동으로 섹션화·전수 정리")에 따라 **deck_harness 43종 전수 감사**로 재작성.
> 이전 flat 흡수(manifest 20종)를 대체하는 **작가 팔레트 정본**. 이제 여기서 골라 짠다(그때그때 발견 X).
> 패밀리 = 엔진 `validation.py HEADER_EXEMPT`가 코드로 가진 구분. 📷 = 이미지 필요(B단계). ★ = 트렌드/컨설팅 덱 주력.

## 원리
- **Family A(고정 헤드)** = 눈썹+헤드 상단 고정, 본문만 변주. A끼리 헤더 100% 동일 = 일관성.
- **Family B(가변 헤드)** = 헤드가 구성요소(중앙·좌거대·다크). 표지·간지·핵심주장·결론 = 구두점.
- 덱 = **A 다수 + B 드문 구두점.** 각 장은 의도적으로 A or B.

---

## Family A — 고정 헤드 (헤더 고정, 본문 변주)

### A1. 차트 (수치) — payload 슬롯
- ★ `chart_kpi` `{kpi:{value,label}, mini:[]}` — 단일 우세 수치(히어로 숫자)
- ★ `chart_bar` `{categories, series, orient}` — 항목 순위
- ★ `chart_line` `{categories, series}` — 추세·격차
- ★ `chart_donut` `{value, percent, items}` — 비중·구성비
- ★ `chart_gauge` `{value, percent, max}` — 단일 비율(반원)
- ★ `chart_combo` `{categories, bars, line}` — 규모+추세(이중축)

### A2. 비교·관계
- ★ `before_after_diagram_with_metric` `{before, after, metric}` — 2상태 + 수치 콜아웃
- ★ `convergence_diagram` `{drivers[], outcome}` — 다→1 수렴
- ★ `requirements_excel_table` `{columns, rows}` — 다축 비교 표
- `tam_scenario_table` `{scenarios, rows, total}` — 시나리오 표(시장규모형)
- `data_visualization_3col_chart` `{stats, cards}` — 빅넘버 3
- `data_visualization_2col_chart_text` `{bars, body, bullets}` — 차트 + 설명 2단

### A3. 진행·단계
- ★ `evolution_timeline` `{stages[]}` — 시간 진화
- `contest_history_timeline_bullet` `{events, milestones}` — 연혁 타임라인
- `ir_company_overview_timeline_milestone` `{milestones, tabs}` — 마일스톤(탭)
- ★ `funnel` `{stages[]}` — 단계 상승
- `product_use_case_4step` `{steps[]}` — 4단계 유스케이스
- `workflow_table_3col` `{columns, secondary}` — 워크플로우 표

### A4. 카드·항목·혼합
- ★ `3-card` `{cards[]}` — 병렬 3
- `ir_business_area_2col_card` `{areas, cards, tabs}` — 영역 카드(탭)
- `case_card_examples_pair` `{cases[]}` — 사례 2짝
- ★ `split_master` `{lead, right_kind, stats/bullets/table/chart}` — 좌 리드 / 우 위젯
- ★📷 `content-image` `{body, bullets, image}` — 헤더 + 이미지 본문
- `references_notes` `{notes}` — 출처 집약

### A-제외 (UI/제품 데모 전용 · 트렌드덱 비관련)
`logo_grid` · `mobile_mockup_with_annotation_arrows` · `multi_wireframe_dense_admin` · `wireframe_left_explanation_right` · `shot`📷 · `portfolio_cover_photo_brand_red`📷 · `contest_cover_title_date_centered`

---

## Family B — 가변 헤드 (스테이트먼트/히어로) = HEADER_EXEMPT

- ★ `cover_hero` `{title, subtitle, eyebrow, brand_mark}` — 표지(중앙 히어로)
- 📷 `cover_split_brand_product` `{title, image, features}` — 표지(이미지형)
- ★ `editorial_impact_axes` `{axes[]}` — 목차(축 미리노출)
- ★ `section_divider_hero_text` `{chapter_num, kicker, title}` — 간지
- ★📷 `corporate_research_navy_split_focus` `{focus[], cards, image}` — **다크** 핵심 주장(역설·전환점)
- ★ `narrative_centered_text_block` `{paragraphs, bullets}` — **중앙 한 문장** 선언
- ★📷 `title-hero` `{title, bullets, image}` — 히어로 오프닝
- ★ `conclusion_synthesis` `{actions, body, source}` — 결론 종합
- 📷 `closing` `{title, bullets, image}` — 클로징
- `thankyou` `{message, contacts}` — 감사
- ★ `back_cover` `{disclaimer, document_label}` — 백커버
- `single_page_complete_landing_mockup` — (랜딩 데모용, 비관련)

---

## 작가 규율 (이 팔레트에서 고른다)
1. 데이터/설명 = **Family A** (헤더 고정, A1~A4에서 내용 모양에 맞는 본문 선택 · 같은 양식 ≤1~2회).
2. 표지·목차·간지·핵심주장1~2·결론 = **Family B** (드물게·임팩트).
3. A끼리 헤더 100% 동일 점검 = 일관성. B는 리듬 깨기.
4. 📷 양식 = B단계(Pexels) 이후 활성. 그 전엔 이미지-불필요 양식만.
5. 바인더 직접지정 = `axis1_to_deck.py EXPLICIT_LAYOUTS` (B + 비-차트 A 패스스루).

## 현 마케팅 덱 매핑
- **B 구두점:** p1 표지 · p2 목차 · p3·6·8·15 간지 · **p7 역설(navy 다크)** · p18 결론
- **A 본문:** p4 kpi · p5 timeline · p9 bar · p10 split · p11 3-card · p12 표 · p13 before_after · p14 convergence · p16 3-card · p17 funnel
- **다음:** 간지 4장 → B 다크 통일 / 결론 직전 narrative_centered 1장 / B단계 이미지.
