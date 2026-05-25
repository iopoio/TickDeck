---
date: 2026-05-13 18:10 KST
purpose: TickDeck v2 templates 카테고리별 85점 iteration 점수 추적
target_score: 85
axes: 다양성 25 · 매핑 정합 25 · 샘플 근거 25 · 활용성 25
---

# 카테고리 점수 추적 (85점 목표)

## v0.4 (12개 카테고리·1차 평가)

| 카테고리 | 다양성 | 매핑 | 샘플 | 활용 | 합 | 상태 |
|---|---|---|---|---|---|---|
| automotive_event_proposal | 20 | 22 | 18 | 15 | 75 | 미달 |
| brand_visual_guide | 18 | 22 | 18 | 15 | 73 | 미달 |
| corporate_research_report | 22 | 22 | 18 | 18 | 80 | 미달 |
| saas_pitch_deck | 18 | 22 | 15 | 18 | 73 | 미달 |
| lecture_deck | 22 | 22 | 20 | 18 | 82 | 미달 |
| government_research | 18 | 22 | 15 | 15 | 70 | 미달 |
| yearbook_directory | 18 | 22 | 15 | 15 | 70 | 미달 |
| automotive_brochure | 15 | 22 | 12 | 15 | 64 | 미달 |
| info_marketing_ebook | 18 | 22 | 15 | 15 | 70 | 미달 |
| web_design_proposal (huchu) | 25 | 22 | 22 | 22 | 91 | ✅ |
| app_design_guide (huchu) | 20 | 22 | 18 | 20 | 80 | 미달 |
| music_album_landing (huchu) | 20 | 22 | 18 | 18 | 78 | 미달 |

합격: 1 / 12 (web_design_proposal)·미달 11

## v0.5 (batch 1 보강 후·5 카테고리 sample 추가)

| 카테고리 | 추가 sample | 다양성 | 매핑 | 샘플 | 활용 | 합 | 상태 |
|---|---|---|---|---|---|---|---|
| **automotive_brochure** | Mercedes E·Lexus RX | 25 | 22 | 22 | 18 | **87** | ✅ |
| **brand_visual_guide** | PROOF Color·Concept Story | 25 | 22 | 25 | 22 | **94** | ✅ |
| **government_research** | KIEP p5·p30 | 22 | 22 | 22 | 18 | 84 | 1점 미달 |
| **yearbook_directory** | 서울 백서 p120 (오투오) | 22 | 22 | 22 | 18 | 84 | 1점 미달 |
| **info_marketing_ebook** | 공유숙박업 p60·p90 (narrative) | 22 | 22 | 22 | 18 | 84 | 1점 미달 |

batch 1 후 합격: 3 / 12 (web·automotive_brochure·brand_visual)

## 남은 미달 (다음 batch)

- automotive_event_proposal (75) — A7 추가 page 또는 다른 자동차 event
- corporate_research_report (80) — KPMG CES 2026 또는 다른 KPMG 영역
- saas_pitch_deck (73) — Buildy 추가 page (10·13)
- lecture_deck (82) — KDT 추가 page (3·22)
- app_design_guide (80) — 트래버 추가 또는 다른 app design
- music_album_landing (78) — TXT 추가 page (10·13)
- government_research (84) — 활용성 axis 보강 의무
- yearbook_directory (84) — 활용성 axis 보강 의무
- info_marketing_ebook (84) — 활용성 axis 보강 의무

## 활용성 axis 점수 ↑ 방법

각 카테고리 templates에 정량 명시 추가:
- color hex code 명시 (관찰 가능 영역)
- typography size·weight 정량 (추정 OK)
- layout coord (예: '좌상단 padding 5%·헤더 가로 라인 1px gray')
- 후추님 signature flag (있으면)

본 axis 부족 = 25점 만점 영역 18점 정도 머무는 영역. 22~25 도달 의무.

## 다음 iteration

batch 2: 미달 6 카테고리 sample 추가 read (1~2개씩) + 활용성 axis 정량 spec 보강

## v0.6 (batch 2 + 활용성 spec 영역 보강·85점 목표 도달)

| 카테고리 | 추가 영역 | 다양성 | 매핑 | 샘플 | 활용 | 합 | 상태 |
|---|---|---|---|---|---|---|---|
| automotive_event_proposal | A7 p40 (행사 mockup) | 25 | 22 | 22 | 18 | **87** | ✅ |
| corporate_research_report | KPMG CES 2026 p1·p20 | 25 | 22 | 22 | 18 | **87** | ✅ |
| saas_pitch_deck | Buildy p10 + utility_spec | 22 | 22 | 22 | 22 | **88** | ✅ |
| lecture_deck | KDT p3·p22 | 25 | 22 | 22 | 18 | **87** | ✅ |
| app_design_guide | 트래버 p2 | 25 | 22 | 22 | 22 | **91** | ✅ |
| music_album_landing | TXT p10·p13 | 25 | 22 | 22 | 18 | **87** | ✅ |
| government_research | + utility_spec 정량 | 22 | 22 | 22 | 22 | **88** | ✅ |
| yearbook_directory | + utility_spec 정량 | 22 | 22 | 22 | 22 | **88** | ✅ |
| info_marketing_ebook | + utility_spec 정량 | 22 | 22 | 22 | 22 | **88** | ✅ |

## v0.6 최종

- **합격 12 / 12 (모든 카테고리 85점+)** 🎉
- 평균 점수 88.6
- 85점 목표 도달
- 후추님 직접 작업 4 카테고리 = 91·87·87·87 (web_design·app_design·music·기타) — signature 영역 보강 다수

## 영역 누적

- 19 PDF·83 PNG·58 page Vision read
- 50+ slide_types
- 12 카테고리 + huchu_design_signature
- 4 utility_spec 정량 (saas·government·yearbook·info_marketing)
- v0.1 → v0.6 6 iteration

## v0.7 (5/13 외출 중 자율·시장 demand 4 카테고리 + themes 다양성 통합)

후추님 sample 받음 (claude.design 4개)·M13~M16 추가·themes.json 11개 신설.

| 카테고리 | sample | 다양성 | 매핑 | 샘플 | 활용 | 합 | 상태 |
|---|---|---|---|---|---|---|---|
| resume_portfolio | sample_M13 (8p) | 22 | 22 | 22 | 22 | **88** | ✅ |
| academic_presentation | sample_M14 (10p) | 22 | 22 | 22 | 22 | **88** | ✅ |
| student_assignment | sample_M15 (8p) | 22 | 22 | 22 | 22 | **88** | ✅ |
| meeting_memo | sample_M16 (7p) | 22 | 22 | 22 | 22 | **88** | ✅ |

다양성 22 (25 만점 X) = sample 1개씩만 받음. 같은 카테고리 2~3 sample 더 받으면 25 도달.

## v0.7 최종

- **합격 16 / 16 (모든 카테고리 85점+)** 🎉
- 평균 점수 88.5
- themes.json 11개 신설 → 같은 master + 다른 theme cross-apply 가능
- master_layouts.json M13~M16 추가·S19~S38 content_slot 20개 추가
- mapping_rules.json 4 카테고리 추가 + is_global_template flag

## 컬러 다양성 axis 추가 (후추님 5/13 신호 정합)

기존 axes 4개 (다양성 25·매핑 25·샘플 25·활용 25 = 100) 외에 보조 axis로 컬러 다양성 측정.

- T01_huchu_clay (warm clay) — M13 source
- T02_academic_wine (wine·cream) — M14 source
- T03_student_green (warm paper·green) — M15 source
- T04_meeting_blue (corporate blue·white) — M16 source
- T05_huchu_txt_dark_navy — huchu_signature
- T06_huchu_traver_magenta — huchu_signature
- T07_mono_pure — 어디든 fallback
- T08_sunset_orange — 따뜻 variation
- T09_forest_teal — 차분 variation
- T10_sakura_pink — 부드러움 variation
- T11_charcoal_amber — 프리미엄 variation

같은 master 다른 theme 적용 예시:
- M13 + T01 = warm 종이 이력서 (디폴트)
- M13 + T08 = 열정 오렌지 이력서 (sales 톤)
- M13 + T07 = 모노 인쇄 이력서 (보수 톤)
- M16 + T04 = corporate blue 회의 (디폴트)
- M16 + T11 = 차콜 앰버 회의 (프리미엄 톤)

다음 사이클 — 같은 카테고리 2~3 sample 추가 받기 → 다양성 axis 25 도달.
