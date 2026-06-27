# 틱덱 하네스 (tickdeck_harness)

> 틱덱 전용 **덱 생성 시스템** — 흡수한 디자인 규칙 + 콘텐츠 방법론 + 작업 루프를 한곳에. 하네스 자체가 루프다(흩어진 문서 X).
> ⚠️ `Think/tools/deck_harness`(범용 렌더 엔진·여러 프로젝트 공용)와 **분리·독립**. 그건 안 건드린다. 이건 틱덱 산출물 전용.
> 흡수 출처: GLM·Qwen·Kimi 3-way 2라운드(2026-06-27~28). 철학 = **백본 수렴 / 렌즈 발산**.

## 루프 (주제 → 덱)

```
1. 인풋        주제 / RFP / 보고서 원본
2. 디깅        knowledge/content 규칙대로 — 소스 티어링·강제 출처 스키마로 자료 수집
   ↓ (자료 풀에 누적: claim·metric·source·limitation)
3. 검증·강등   CED/CEMS — 수치 비면 삭제, 약한 데이터 DWS로 (메인/정성/방향신호/삭제)
4. 스토리      thesis "A는 B를 C한다" + 챕터 프레임(Tension→Diagnosis→…→Action)
              + 분석 렌즈 2~4개 선택(knowledge/content LENSES, 골라 겹쳐)
5. 렌더        engine.py build_deck(slides, theme) → HTML → PDF/PNG
6. 리뷰        Codex/Gemini 비전 평가 → 수정(1순위=출처/근거)
```

## 구성

| 경로 | 내용 | 상태 |
|---|---|---|
| `engine.py` | 내용→HTML 덱 엔진. 흡수한 *디자인* 규칙 코드화(토큰·팔레트·레이아웃 12종·다양성·자가검증) | ✅ 루프 안 |
| `marketing_full.py` | 예시 — 2026 마케팅 트렌드 21p(breeze). `python3 marketing_full.py [theme]` | ✅ |
| `demo_content.py` | 레이아웃 데모 | ✅ |
| `knowledge/design/` | 디자인 흡수 캐논(01~05 + 갤러리 HTML) | ✅ 참조 |
| `knowledge/content/` | 콘텐츠 방법론 캐논(원본 90K + `00_SYNTHESIS`) | ✅ 참조 |
| `pipeline/dig_schema.py` | 디깅 강제 스키마 — 좀비/순환/페이월 flag·1차 미방문 T1 강등 | ✅ 루프 안 |
| `pipeline/ced.py` | CED + DWS 라우팅(MAIN/정성/방향/삭제) + 렌더 게이트 | ✅ 루프 안 |
| `pipeline/story_mapper.py` | route 결과 → engine 슬라이드 + 챕터 프레임(C2) + 렌즈 체크리스트 + 정성묶음 | ✅ 루프 안 |
| `pipeline/dig.py` | 디깅 입구 — 요청 빌더(DIG_PROMPT 주입) + 반환 JSON→DigRecord 파서·validate | ✅ 루프 안 |
| `marketing_v2.py` | 흡수 루프 재생성 = end-to-end 시험. `python3 marketing_v2.py [theme]` → 단일수치 강등·무출처 DROP | ✅ |

## 다음 세션 (보고서 통째 재생성 = 흡수 end-to-end 시험)
현 21p 덱은 흡수 *전* 산출물. 단발 패치 그만 쌓고 이 루프로 재생성:
1. ✅ `pipeline/dig_schema.py` — 디깅이 tier·원문URL·표본·flag를 구조화 반환(훈련지식 빈칸 채우기 금지). = 리뷰 1순위 약점(출처) fix.
2. ✅ `pipeline/ced.py` — 슬라이드 수치에 source+limitation+confidence, 자동 강등/삭제.
3. ✅ `pipeline/story_mapper.py` + `marketing_v2.py` — 위 둘로 보고서 재생성. route(MAIN/QUALITATIVE/DIRECTIONAL/DROP)→engine 슬라이드 + 챕터 프레임(C2) + 렌즈(counterfactual·tombstone) + A6 인용·정성묶음.
4. ✅ `pipeline/dig.py` — 디깅 입구 열림(스키마는 만들었는데 호출부가 비었던 갭 fix). **실제 디깅 1건 검증**(본부 WebSearch+WebFetch, deloitte.com 1차 직접 열람) → Deloitte 팬덤 92%가 MAIN(히어로) 승격, 미검증 단일수치(97/65/42)는 정성 강등, 무출처 62%는 DROP. 23p·12레이아웃·렌더 QA 통과. **남은 것: 전 수치 라이브 재dig(현 대부분 미방문 T2라 정성)**. `visited_primary`는 디깅 모델 자기보고라 본부 1차 spot-check가 사람 몫(Part D.3 HITL).

상세 설계 = `knowledge/content/00_SYNTHESIS_콘텐츠방법론.md` Part D · 핸드오프 = `Think/.claude/inbox/2026-06-28_0015_…`.
