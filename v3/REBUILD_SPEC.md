# TickDeck v3 재작업 명세서 (REBUILD_SPEC)

작성: 본부 클차장 · 2026-06-18 · 검사 4중(코드리뷰 워크플로우 31 findings·인벤토리 워크플로우·codex 코드리뷰·클차장 직접 정독) 반영

## 배경
- 마케팅 덱(matched_marketing_trends_2026) 결과 = 내용·렌더 둘 다 깨짐.
- 근본 원인 둘:
  1. **매칭**: matching_engine이 leader.final 실제 내용 대신 검산 메타(numeric_audit)·임의값(64+8i)·플레이스홀더(핵심N·axis1 block)를 시각화. leader.final이 clean_md로 통짜 텍스트로 뭉개져 항목 구조가 죽음(코드리뷰 #4). parse_driver_items 등 실파서가 정의만 있고 호출 0(#23).
  2. **렌더**: 양식이 SVG→PNG '이미지'라 deck_harness 검증을 못 받음. 11개 전부 긴 한글 오버플로우/겹침(#9·#10~18). 제목 중복(#19·21)·CARD GRID 라벨 노출(#20).
- 해결: **deck_harness 32 네이티브 레이아웃 재사용 + 매칭 엔진 재작성.**

## 1. 목표
- 양식 = deck_harness 32 레이아웃(build.py:1518-1551 LAYOUT_RENDERERS) 재사용. renderer.py SVG→PNG 방식 폐기.
- 매칭 엔진 = leader.final 실제 내용 파싱 → 적합 레이아웃 선택(+variation) → slides.json 직렬화 → deck_harness build로 HTML/PDF/PNG/validation.
- 결과 = 실제 내용이 슬라이드에·검증 통과·출처 유지·같은 주제 2회 다른 덱.

## 2. 하지 말 것 (금지)
- SVG→PNG 양식 이미지를 image 슬롯에 넣기 (image_to_uri는 검증 텍스트가 없어 auto-fit/overflow/safe-area 검사가 통째로 무력화됨·인벤토리 discard).
- 임의값/더미: `_line_cards` 64+8i·render_stat_cards 42/70/56 폴백 등. 본문 실수치 없으면 값 비우기(게이지 강제 금지).
- 플레이스홀더: "핵심 N"·"axis1 block"·"CARD GRID"·"Structured metric cards" 등 코드 합성 문자열.
- 검산 메타(numeric_audit·coverage·Checked/Matched/Review/Sources)를 슬라이드 콘텐츠로 노출 (QA 리포트용이지 슬라이드 내용 아님).
- 하드코딩 제목·제목 중복(슬라이드 헤더 + 컴포넌트 내부 둘 다 그리기).
- **색/브랜드 변경 금지** — comparison 청록 3색(#28) 등 색 정책 변경은 후추님 게이트. 현행 유지.

## 3. 읽을 파일
- deck_harness: `/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py`(32 레이아웃·render_*·fit_attrs·render_text·render_outputs)·`validation.py`(AUTO_FIT_JS·VALIDATE_JS·summarize_validation)·`README.md`·`slides_pepstock.json` 등 예제 deck·`styles/tokens.css`.
- TickDeck: `pipeline/matching_engine.py`·`axis1_research/runs/20260618_1858_2026_마케팅_트렌드.json`·`axis2_layouts/components/manifest.json`.

## 4. 콘텐츠 매핑 규칙 (핵심 — 이게 빠져서 망했던 부분)
leader.final 마크다운 → 슬라이드. 구조 보존(clean_md 통짜 뭉개기 금지):
- `## 섹션 헤더` = 슬라이드 제목 (실제 제목 그대로·하드코딩/합성 금지).
- 시장 규모·수치 섹션 → 큰 수치 강조 레이아웃 또는 data_visualization_3col_chart (본문 실제 수치만).
- 5대 성장 동인 등 **항목 리스트** → 3-card / workflow_table_3col / product_use_case_4step. 항목 수만큼만 생성, 부족해도 더미로 채우지 말 것. parse_driver_items 결과 직접 소비.
- 기관 전망 **표** → tam_scenario_table / requirements_excel_table / data_visualization (행=기관·열=예측). markdown_table_rows 활용. 표 셀 텍스트 길이는 매칭이 사전 통제(셀엔 data-fit 없음·인벤토리 한계).
- 시사점·결론 → narrative_centered_text_block / closing.
- 출처 → references_notes (기관 라벨·URL). 카드별 실제 출처 매핑(전역 top6 재탕 금지·#22).
- 수치 = 본문 실제 값만. 없으면 비움.
- 환각 의심값(numeric_audit found=false, 예: '1조 달러') = 슬라이드에서 제외 유지(진실주의).

## 5. 수정 범위
- `pipeline/matching_engine.py`: extract_content_blocks·build_component_data 전면 재작성 → leader.final 파싱 결과를 deck_harness 레이아웃별 slides.json으로 직렬화. deck_harness build 호출(이미 render_deck_harness 있음).
- `axis2_layouts/components/renderer.py` SVG 양식: 폐기. deck_harness에 없는 도형(도넛/매트릭스 등)이 꼭 필요하면 inline SVG로 .safe 안 data-check div에 넣되, **라벨/수치 텍스트는 SVG 밖 HTML(data-fit)로 빼서** 검증 받게(인벤토리 한계).
- `manifest.json`: content kind → deck_harness 레이아웃 매핑 규칙으로 재정의.
- deck_harness: 기존 32 레이아웃 우선. 부족하면 신규 render_*+LAYOUT_RENDERERS 등록+tokens.css `.layout-<name> .safe` 그리드 추가(인벤토리 design_notes (a) 경로).

## 6. variation (같은 주제 2회 = 다른 덱)
- 같은 content kind에 복수 레이아웃 후보를 두고 _next_rotation으로 로테이션.

## 7. 완료 기준 (evidence — codex가 충족 증거 제출)
1. 마케팅 run으로 덱 생성 → validation.json issues=0 (overflow·safe-area·font-below-min 0).
2. 슬라이드에 실제 내용: 5대 동인(에이전틱 AI·AEO·프라이버시·숏폼·오프라인 회귀)·Gartner/Forrester/Deloitte·실수치(23%·54%·70% 등) 들어감.
3. 플레이스홀더 grep 0건: "핵심 [0-9]"·"axis1 block"·"CARD GRID"·"Structured metric".
4. 검산 메타(Checked/Matched/Review/coverage) 슬라이드 노출 0건.
5. 출처 references 유지. 환각 의심값 제외 유지.
6. 같은 run 2회 실행 → 서로 다른 레이아웃 덱.
7. 실패 중인 테스트 2개(test_matching_engine.py:150-211·test_card_grid_without_values) 통과 + 실데이터→카드라벨 검증·플레이스홀더 차단·긴 한글 오버플로우 테스트 추가.
8. verify_boundary pass(신야 중국 모델 경계).

## 8. 검증/보고 형식
- codex 완료 후: 변경 파일 목록·완료기준 8항목 각 충족 여부(validation.json 수치·플레이스홀더 grep 결과·실내용 슬라이드별 인용·테스트 수)를 evidence로 보고.
- 이후 본부 클차장이 전체 슬라이드 PNG 직접 시각 검사 + ui-reviewer/codex 교차 리뷰. 둘 다 통과해야 후추님 보고.
