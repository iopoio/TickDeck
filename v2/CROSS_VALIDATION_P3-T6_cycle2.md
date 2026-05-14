# P3-T6 Cycle 2 — Gemini 제대리 Cross-Validation Report

- 일시: 2026-05-15 05:18 KST
- 본진: Claude Opus (Ralph P3-T6 cycle 2)
- 제대리: Gemini CLI 0.41.2 (gemini -p --skip-trust)
- 대상: TickDeck/v2/ templates.json v0.7 · master_layouts.json v0.3 · mapping_rules.json v0.3

## 의뢰 요지

본진이 한국 자료 137 PDF 영역 영역 18 master frame + 59 slide_type + 18 url_domain 추출. 본진 view 영역 saturation 가까움. 제대리 view 영역 gap·약점 짚기.

## 제대리 진단

> **"Standardization은 우수하나, High-Density & Vertical Specialization 영역에서 Gap 발견"**

### 1. Master Frame 추가 후보 (4건)

| ID | 이름 | Why | 후보 PDF |
|---|---|---|---|
| M19 | Insight-Heavy Trend Report (Data-First) | DMC·샘앤파커스 영역 영역 시장 보고서 영역 텍스트+차트 혼합 고밀도 영역 영역 | [dmc] 2018 1인가구·2025 trend |
| M20 | Component-Based Design System (Documentation) | Wireframe 영역 영역 UI Kit·명세서 영역 영역 구조적 frame | 3-4 디자인 시스템 설계·4-1 디자인시스템 |
| M21 | B2C Service/App User Flow (Step-by-Step) | SaaS(B2B) 영역 영역 사용자 여정 Mobile-First 레이아웃 | [SCORDI] 스코디 서비스소개서 |
| M22 | Policy & Compliance (Text-Centric) | 정부 과제·법인 가이드라인 영역 영역 조항(Article) 중심 엄격 그리드 | (제2026-208호) 모두의 창업 프로젝트 |

### 2. Slide Type 약점 (4건)

| 후보 ID | 이름 | Why |
|---|---|---|
| timeline_milestone_parallel_workstream | Timeline & Roadmap (Advanced) | 선형 영역 영역 Parallel Workstream·Milestone Highlight 영역 영역 약함 |
| comparison_matrix_pricing_5col | Comparison & Pricing (Complex) | 2분할 영역 영역 3~5 plan + Feature Check-list Matrix 영역 영역 의사결정 영역 |
| map_data_overlay_global_local | Global/Local Map & Logistics | 지리적 확장·Data-over-Map 시각화 |
| executive_summary_top_down_1page | Executive Summary (The 'So What') | 전체 장표 핵심 인사이트 영역 1Page Top-Down Summary 구조 |

### 3. Industry Vertical Gap (4건)

| Vertical | 현재 coverage | Gap | Priority |
|---|---|---|---|
| Medical & Bio-Tech | M18 마크로젠 IR 1건만 | 임상 데이터·논문 인용·복잡 메커니즘 시각화 | high (잡솔트·EatScan 영역 정합) |
| FinTech & Traditional Finance | 0건 | 공시자료 표·Compliance 폰트·컬러 | medium |
| Real Estate & PropTech | 0건 (inbox-pdf 영역 영역 부동산 PDF 다수 영역 read X) | 매물·입지·조감도 Photo-Grid Priority | medium |
| F&B & Franchise | 0건 | 메뉴판·가맹·QSC 지표 | low-medium |

### 4. Actionable Recommendations (4단계)

1. **Refine Mapping Rules**: url_domain_classifier 영역 영역 Industry vs Format 이원화 영역 영역 매핑 정밀도 향상
2. **Add M19~M22**: 4 master frame 영역 master_layouts.json 영역 추가 정의 (실 PDF read 후)
3. **Table/Chart Detail**: slide_types 안 Waterfall·Sankey·Spider Web 등 난이도 높은 데이터 시각화 영역 추가
4. **Information Density 변수**: mapping_rules v0.4 영역 영역 Information Density 변수 추가 — TickDeck 차별점

## 본진 검토

- ✅ **수용 가능**: M19~M22 master 후보·4 advanced slide_type·4 industry vertical gap·이원화·Information Density 변수 모두 actionable·근거 합리
- ⏸️ **유보 (실 read 의무)**: M19~M22 신설은 실 PDF read 후 (5/15 cycle 영역 read 영역 X·다음 cycle). 본진 룰: "추측 X·실 호출 검증". cross-validation 결과 영역 영역 영역 stub 등록만
- 📌 **자국**: templates.json v0.7.1·mapping_rules v0.3.1 영역 영역 cross-validation section 신설·v0_4_plan section 신설

## 다음 Cycle 액션 (M19~M22 실현)

1. 디자인 시스템 강의 3-4·4-1 영역 read → M20 신설
2. dmc 1인가구·2025 trend 영역 read → M19 신설
3. SCORDI 서비스소개서 영역 read → M21 신설
4. 정부 공고 (모두의 창업 프로젝트 등) 영역 read → M22 신설
5. mapping_rules v0.4 영역 영역 → Industry vs Format 이원화·Information Density 변수·vertical_industry_tag 도입

## 가설 확인/기각

- **가설** (P3-T6): 노클 5/13 송부 PDF + TickDeck v2 sample 영역 영역 137개 자료 영역. 본진 + 제대리 교차 분석 영역 영역 patterns 추출 영역 가능
- **결과**: ✅ **확인** — Gemini 제대리 cross-validation 영역 영역 본진 단독 view 영역 영역 영역 영역 발견 X gap 4 master + 4 slide_type + 4 industry vertical 영역 식별. 본진 단독 view 영역 saturation 도달 영역 영역 영역 cross view 영역 영역 영역 영역 영역 영역 영역 영역 영역 영역
- **교훈**: 단독 검토 = "saturation" 자가 진단 위험. 다른 모델·다른 view 영역 영역 영역 gap 영역 영역 영역 (29236 HITL 신호 + 29153 Judge 분리 정합)

## 자국

- templates.json: v0.7 → v0.7.1-cross-validated (gemini_cross_validation_v0_7 + v0_4_plan section 신설)
- mapping_rules.json: v0.3 → v0.3.1-cross-validated (v0_4_plan section 신설)
- master_layouts.json: 변경 X (실 PDF read 후 다음 cycle 영역 M19~M22 신설)
- CROSS_VALIDATION_P3-T6_cycle2.md 신설 (정본 영역)
