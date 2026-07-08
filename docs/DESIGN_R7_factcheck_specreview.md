# R7 설계 — 전 수치 팩트체크 + 외부리뷰 spec 단계 이동 (2026-07-08)

> 배경: 취향 장부 [코드 대기] 잔여 2건 (7/8 경쟁모델 분석發·후추님 "코드 대기 진행" 지시). "감사 가능한 신뢰" 해자의 마지막 조각.

## A. 전 수치 팩트체크 (fact-checker)

### 문제
verifier는 **수집 시점**에 검증한다. 그 뒤 insights→dag→page_plan→deck_spec 4번의 변환을 거치며 수치가 문맥과 어긋날 수 있다 (반올림·기간 표기 이동·주체 뒤바뀜). 최종 덱의 수치를 **끝에서 한 번 더 원문과 대조**하는 눈이 없다.

### 설계
1. **기계 추출 (script·소넷)**: `factcheck_dump.py` — 06_deck_spec.json + metric/source registry에서 대조표 생성: `[{metric_id, page_no, value, unit, period, claim_문맥, source_url|local_path}]` → `08_factcheck_table.json`.
2. **판정 (agent·클차장 md)**: `fact-checker.md` 신설 — 대조표의 **전 수치**를 원문 재열람(URL fetch 또는 local Read)으로 확인. 항목별 판정 3종: `confirmed` / `mismatch`(값·단위·기간·주체 불일치) / `unreachable`(원문 접근 불가). → `08_factcheck.json`.
3. **게이트**: mismatch ≥1 = 통과 금지 (verifier 반송). unreachable = 해당 페이지에 [미검증] 각주 의무 또는 수치 제거 — 조용히 통과 금지.
4. **비용 통제**: 납품·쇼케이스 런 한정 의무 (§7.6 폴리시 패스와 같은 관례). 데모·내부 런 면제. URL 재열람 실패 시 insane-search 폴백 1회, 그래도 실패면 unreachable.

## B. 외부리뷰(gemini) spec 단계 이동 — 검토 결론: 이동 ㄱ

### 근거
- 현행 = 렌더 후 HTML 텍스트 리뷰. 리뷰가 잡는 것(논리 gap·주장 약점·근거 부족)은 **06_deck_spec에 이미 전부 존재** — 렌더 후 발견하면 재계획→재렌더 루프 낭비 (GLM 교차에서도 동일 지적·"코덱스 프리리뷰처럼").
- 시각 층 검수는 qa-reviewer 실측 판정(밀도·블라인드 비교·팩토리 티)이 이미 담당 — 외부리뷰가 렌더본을 볼 이유가 소멸.

### 설계
- `external_review.py`에 `--stage spec` 모드 추가: 06_deck_spec.json에서 페이지별 제목·클레임·수치 텍스트를 추출해 리뷰 프롬프트 구성. 기존 렌더 후 모드는 플래그로 보존 (기본 = spec).
- SKILL 절차 위치: 06 완성 직후·렌더 전. 리뷰 지적 → page-planner/deck_spec 수정 → 렌더는 한 번만.

## C. 분담
- 클차장: 본 설계 + `fact-checker.md` 신설 + SKILL.md 절차 갱신 (외부리뷰 위치·팩트체크 stage 추가)
- 소넷: `factcheck_dump.py` + `external_review.py --stage spec` + 테스트 (추출 정합·spec 모드 프롬프트 구성·기존 모드 회귀)
- 검수: 클차장 diff + 실전 런 1회 (R5 실증 런 산출물 재사용 가능)

## D. 상태
- [x] 설계 (7/8)
- [ ] fact-checker.md·SKILL 갱신 (클차장)
- [ ] 스크립트·테스트 (소넷)
- [ ] 검수·커밋·실증
