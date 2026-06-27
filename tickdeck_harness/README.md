# 틱덱 하네스 (tickdeck_harness)

> 틱덱 전용 **덱 생성 시스템** — 흡수한 디자인 규칙 + 콘텐츠 방법론 + 작업 루프를 한곳에. 하네스 자체가 루프다(흩어진 문서 X).
> ⚠️ `Think/tools/deck_harness`(범용 렌더 엔진·여러 프로젝트 공용)와 **분리·독립**. 그건 안 건드린다. 이건 틱덱 산출물 전용.
> 흡수 출처: GLM·Qwen·Kimi 3-way 2라운드(2026-06-27~28). 철학 = **백본 수렴 / 렌즈 발산**.

## 루프 (PDF → 덱) — 앞 절반 자동화 완료 (2026-06-28)

```
1. 인풋        주제 / RFP / 보고서 원본(PDF 등)
2. ingestion   pipeline/dig_source.py — pdftotext, 이미지 PDF는 tesseract OCR 폴백   [자동]
3. 디깅        pipeline/dig_agent.py — 에이전트가 텍스트 읽어 CED JSON(티어링·재인용·신뢰도)  [자동]
4. 추적        pipeline/dig_trace.py — 재인용 4-way(match 승격/scope_diff 라벨/contradiction DROP/notfound)  [반자동]
5. 검증·강등   pipeline/ced.py — CED + DWS 라우팅(MAIN/정성/방향/삭제) + 렌더 게이트     [자동]
6. 스토리      pipeline/story_assist.py — 디렉터가 thesis·챕터·레이아웃 outline 제안 → compose_deck 자동 조립  [반자동·라벨 다듬기 사람]
7. 렌더        engine.py build_deck(slides, theme) → HTML → PDF/PNG                 [자동]
8. 리뷰        Codex/Gemini 비전 평가 → 수정(1순위=출처/근거)                       [사람]
```
> HITL(사람만): 어떤 Tension이 전략적 울림인지·statgrid 라벨/내러티브 다듬기·최종 어조·결재. = Part D.3.

## 구성

| 경로 | 내용 | 상태 |
|---|---|---|
| `engine.py` | 내용→HTML 덱 엔진. 디자인 캐논 코드화 + 차트(line·donut·**statgrid**)·tabular-nums | ✅ 루프 안 |
| `pipeline/dig_source.py` | PDF→텍스트(pdftotext, 이미지 PDF tesseract OCR 폴백) | ✅ 입구 |
| `pipeline/dig_agent.py` | 텍스트→CED JSON 추출(티어링·재인용·신뢰도) + extract_ceds | ✅ |
| `pipeline/dig_schema.py` | DigRecord 스키마 — 좀비/순환/페이월 flag·1차 미방문 강등·local: 보정 | ✅ |
| `pipeline/dig.py` | 디깅 요청 빌더 + JSON→DigRecord 파서(어댑터) | ✅ |
| `pipeline/dig_trace.py` | 재인용 원본 추적 4-way(match/scope_diff/contradiction/notfound) | ✅ |
| `pipeline/ced.py` | CED + DWS 라우팅(MAIN/정성/방향/삭제) + 렌더 게이트 | ✅ |
| `pipeline/story_mapper.py` | route→engine 슬라이드 + 챕터 프레임(C2) + chart_block(출처 게이트) | ✅ |
| `pipeline/story_assist.py` | CED 풀→디렉터 outline 제안 + compose_deck(자동 조립) | ✅ |
| `knowledge/design·content·charts/` | 흡수 캐논(디자인·콘텐츠방법론·차트 — 각 `00_SYNTHESIS`) | ✅ 참조 |
| `marketing_auto.py` | **풀 사이클 자동** — runs/dmt_2026/로 재현. `python3 marketing_auto.py` | ✅ |
| `marketing_2026.py` | hand-tuned 종합 검증판(Deloitte 1차 + 통계청 라인). `python3 marketing_2026.py` | ✅ |
| `marketing_dmt2026.py`·`marketing_mezzo.py`·`marketing_v2.py` | 단계별 시연(Deloitte statgrid·메조 차트·흡수 재생성) | ✅ |

## 현황 (2026-06-28) — 앞 절반 자동화 완성, 사이클 1바퀴 무인 실증
- **PDF→덱 무인**: Deloitte PDF → CED 12건 자동추출 → 디렉터 5챕터 outline → 15슬라이드 자동 조립(marketing_auto). 라벨 다듬기만 사람.
- **출처 규율 실증**: Deloitte 1차=MAIN / 미검증 단일수치=정성 / 무출처=DROP / KPMG OCR 재인용=방향. **259조 사건**: MezzoMedia 259조 추적 → 통계청 공식 242조와 불일치(광의 기준·근거 미확정) → 242 검증본으로 교체.
- **남은 백로그**: ① statgrid 라벨 자동요약 정교화(현 거친 휴리스틱) ② dws가 sample의 연도("2025")를 표본수로 오인하는 느슨함 ③ 차트 백로그(slope·dot·유령막대) ④ dig_trace 웹 추적을 코드 루프에 정식 연결(현재 추적은 에이전트 수동 호출).

상세 설계 = `knowledge/content/00_SYNTHESIS_콘텐츠방법론.md` Part D · 차트 = `knowledge/charts/00_SYNTHESIS_차트캐논.md`.
