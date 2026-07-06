# R3 설계 — 파생 metric 계약 + CH-annotated_trend·PG-toc_progress·PG-metric_commentary (2026-07-07)

> 근거: PATTERN_LIBRARY §승격안 R3 · 코과장 7/6 리뷰 "C6 파생 metric 체계 선행 안 하면 검증 게이트에서 깨지는 장식".
> 상태: **✅ 구현 완료 (7/7)** — 결재 포인트 2개는 후추님 위임으로 추천안 확정(verifier 산출·4개 묶음). 커밋 c4d4966·b7850ba·24f6a40. 시각QA에서 endpoint_value·기본 라벨 이중 렌더 1건 발견·수술 완료.

## 0. 실측 전제
- C6 계약 (contract_checks.py `_validate_viz_block`): viz title/note에 raw number 금지·직접 value 금지 — **모든 표시 숫자는 metric_id 경유**
- series 구조 = `{label, metric_id, role}` 1:1. 시계열 = metric 여러 개
- 따라서 "+260%/Year" 같은 주석 숫자는 ①렌더러 즉석 계산(검증 우회 — 기각) ②**registry 파생 metric(채택)** 중 후자

## 1. 파생 metric 계약 (본체)

### 1a. metric_registry 확장
```json
{
  "label": "훈련 데이터 연평균 성장률",
  "value": "260", "unit": "%/년",
  "derivation": "cagr",                      // 신설 enum: cagr | delta_pct | delta_abs | multiple | share
  "derived_from": ["metric_012", "metric_013"],  // 원천 metric 참조 (2개+)
  "period": "2010~2025",                     // R2에서 신설된 필드 재사용
  "source_ids": [],                          // 파생은 원천의 source를 상속 (렌더러가 derived_from 경유 역산)
  "status": "derived"
}
```
- **산출 주체 = verifier** (02 단계): page-planner/analyst가 "이 두 metric의 CAGR 필요"를 `derived_request`로 올리면 verifier가 검산 후 registry append. 렌더러는 절대 계산하지 않는다 (검증 우회 차단)
<!-- verifier protocol: analyst/page-planner emits derived_request {metric_id, derivation, derived_from[], formula_note}. verifier recomputes from source metric values, appends the registry metric with status:"derived", source_ids:[], and derived_from[] intact. renderer/verifier handoff contract is read-only after 02_verified.json; renderer may format value/unit but must never calculate derivation. -->
- contract_checks 신설: `derivation` enum 검증 · `derived_from`이 실재 metric 참조 · derived metric의 source_ids는 비워야 함(상속 강제) · 순환 참조 금지

### 1b. C6 유지
- viz title/note raw number 금지 그대로. 주석 숫자는 전부 metric_id 참조라 계약 무변경 통과

## 2. CH-annotated_trend 스키마

viz 블록에 optional `annotations[]` (multi_line·rising_columns·quarterly_bars에 허용):
```json
"annotations": [
  {"kind": "callout", "metric_id": "metric_derived_01", "anchor_series": 0, "shape": "ellipse"},
  {"kind": "endpoint_value", "series": 0},
  {"kind": "trend_arrow", "series": 0},
  {"kind": "event_band", "label": "COVID", "from_key": "2020", "to_key": "2021"}
]
```
- `callout` = 파생 metric 값+unit을 타원/박스로 (숫자는 registry에서만)
- `endpoint_value` = 해당 series metric 값 굵게 (기존 metric — 신규 숫자 없음)
- `trend_arrow` = 순수 시각 (숫자 0)
- `event_band` = 세로 음영 밴드+상단 라벨. **label에 raw number 금지** (연도는 from_key/to_key 축 좌표로만·표시 라벨은 텍스트만) — C6 패턴 재사용
- 게이트: annotation 겹침·차트 영역 이탈 = R1 FIT_* 신호 패턴 확장 (FIT_ANNOTATION_OVERLAP)
- auto-fit 리사이즈 시 주석 재배치: 주석 앵커를 데이터 좌표(시리즈 index·key) 기준 상대 배치 — 픽셀 고정 금지 (7/6 제대리 리뷰 반영)

## 3. PG-toc_progress 스펙 (계약 이슈 없음 — 경량)
- deck_spec meta `"section_nav": "chips" | "dots" | "toc"` (실측 변주 3형) — 렌더러가 섹션 경계(간지 페이지)에서 자동 생성·designer 자유 텍스트 금지 (section_label 재사용)
- 기본 off. 본문 30p+ 또는 리포트 톤에서 designer 선택

## 4. PG-metric_commentary 스펙
- 신규 layout `"metric_commentary"`: 행 1~2개, 행 = {지표 헤딩(metric label) + 델타쌍 헤드라인(파생 metric delta_pct YoY/QoQ 참조) + (YoY)/(QoQ) 라벨 불릿 + 분기 차트(quarterly_bars 재사용)}
- 델타쌍이 §1 파생 metric의 첫 실전 소비자 — R1 quarterly_bars·semantic_color(negative/positive 자동 적녹)와 합류
- contract: layout enum 추가·행 스키마 검증

## 5. 구현 계획 (결재 후 코과장 배치·4커밋)
1. 파생 metric 계약 (registry 스키마+contract_checks+verifier 프로토콜 문서)
2. annotations 렌더러 (callout·endpoint·arrow·event_band + FIT_ANNOTATION_OVERLAP 게이트)
3. toc_progress (chips/dots/toc 3형)
4. metric_commentary layout
검증: test 회귀 0 · 데모 4종 캡처 · clo_v51 옵션 미지정 diff 0.

## 6. 후추님 결재 포인트 2개
1. **파생 metric 산출 주체 = verifier** (설계안 — 검증 일원화·파이프라인 1단계 추가) vs 렌더러 즉석 계산 (싸지만 검증 우회) — 안은 verifier
2. **R3 범위**: 4개 다 (설계안) vs annotated_trend만 먼저 — 안은 4개 (toc_progress·metric_commentary는 계약 이슈가 없어 묶는 게 배치 효율)
