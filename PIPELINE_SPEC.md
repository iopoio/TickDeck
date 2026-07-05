# TickDeck v4 파이프라인 정본 스펙 (모델 불문 실행 규격)

> 목적(후추님 2026-07-05): **클로드가 아니어도, 이 문서 + 리포의 스크립트만으로 유사 품질의 덱이 나오게 한다.**
> 원칙: ①규칙은 여기 명문화하고 ②지켰는지는 사람/모델 재량이 아니라 **코드 게이트**가 판정한다 (스킵 = 게이트 FAIL).
> 상세 규칙의 SoT는 각 에이전트 정의(.claude/agents/*.md)와 장르 스킬(.claude/skills/genre-*/SKILL.md) — 이 문서는 그 목차이자 실행 규격이다.

## 0. 실행 모델

- 작업 공간: `_workspace/<run_id>/` (run_id = `YYYYMMDD_슬러그`)
- 각 단계는 **파일을 읽고 파일을 쓴다**. 단계 간 전달은 파일뿐 — 대화 맥락에 의존하지 않는다.
- 어떤 LLM이 각 단계를 수행하든, 산출 파일이 아래 계약을 만족하고 게이트를 통과하면 유효하다.
- 1콜 진입점: `.claude/skills/deck-harness/scripts/run_deck.sh "<요청>" [URL...]`

## 1. 단계 규격 (입력 → 산출 → 의무 규칙 → 검증)

| # | 단계 | 입력 | 산출 | 의무 규칙 (요약·상세는 SoT) | 검증 |
|---|---|---|---|---|---|
| 1 | intake | 사용자 요청 원문 | `00_intake.json` | 장르 3종 판별(트렌드/주제/시장조사→genre 스킬 로드)·청중 기본값 general·`provided_sources` 기록·`target_market/language` 기본 한국/ko | 게이트가 genre 등록값 검사 |
| 2 | collect | 00 + 장르 스킬 Evidence Profile | `01_evidence_pool.json` | 사용자 자료 ⓪⁻최우선 → 로컬 코퍼스 → 웹. 니치/브랜드면 **1차 관찰 의무**(스토어·SNS·가격·리뷰). 시장조사면 **DART 사업보고서 = Tier-A**. URL 날조 금지(모르면 빈칸)·블로그 제외·스키마 전 필드 | C8(장르별 최소 관찰 수) |
| 3 | verify | 01 | `02_verified.json` (source_registry + metric_registry) | 좀비·세탁·순환인용·중복 검사. 승격 못 하는 수치는 downgraded로 명시·사유 기록. 표시 정밀도 정규화(조원 소수 1자리 등) | C4·레지스트리 참조 무결성 |
| 4 | analyze | 02 + 장르 Analysis Recipe | `03_insights.json` | 인사이트당 독립 2출처. 주장-근거 강도 보정. 시장조사면 **taxonomy-first + 플레이어 테이블 재료**. 적대적 셀프리뷰(기각 기록) | C3(장르별 필수 필드) |
| 5 | editorial | 03 | `04_dag.json` | 관통 명제 1문장·모든 노드가 명제에 연결·**"데이터 부재" 명제 최대 1노드**·MECE 3~5 클러스터·결론은 끝에서 | C1(DAG 연결성) |
| 6 | page-plan | 04 | `05_page_plan.json` | 페이지별 short_title·allowed_source_ids·allowed_metric_ids·archetype. **장르 필수 산출물 페이지에 `genre_artifact` 필드 마킹**(예: `"taxonomy"`·`"player_table"`). `stage_log_patch`에 수행 단계 기록 | C5(단계 순서)·C8(필수 산출물 페이지) |
| 7 | design | 05 + 02 | `06_deck_spec.json` | 수치·기관명·URL 직접 타이핑 금지(id 참조만)·allowed 밖 참조 금지·변주 장부·원문자(①②③) 금지·렌더 전 `qa_lint.py` No defects | qa_lint + C6 |
| 8 | render | 06 + 02 | `deck.html` + `deck.pdf`(자동) | 코드만 수행: `render_deck.py` → capture가 FIT 게이트(넘침·겹침·저대비·과소밀도) 자동 보고 | FIT_* 신호 |
| 9 | gate | run 전체 | 통과/위반 목록 | `run_contracts.py <run_dir>` — C1~C8 일괄. **위반 0이 될 때까지 done 금지** | 코드 게이트 |
| 10 | qa | 전 산출물 + deck.pdf | `07_qa_report.json` | C7 제목 척추·밀도/단조/닫는장/기호 4판정·**요청 커버리지**(사용자 명시 항목별 실체 페이지 매핑, 캐비앗-only=미충족)·3층 외부리뷰 기록·visual_verdict(PDF 직독 없이 pass 금지) | report 필드 필수 검사 |

- 사람/상위 검수자(클차장 역할): 2층 총괄 게이트(디자인 전 "제대로 된 보고서인가")와 최종 PDF 실측 — 이 역할도 문서화된 판정 기준(qa-reviewer.md)을 따른다.
- 루프: Loop A(증거 부족→재수집·verifier/analyst 발동), Loop B(공간·밀도→page-plan 반송·designer 발동). 조건·양식은 deck-harness/SKILL.md.

## 2. 스킵 방지 배선 (규칙→코드 승격 원칙)

**"프롬프트에 쓴 규칙은 어긴 채 지나갈 수 있다. 게이트에 쓴 규칙만 강제된다."** 반복 위반이 발견되면 그 규칙은 다음 중 하나로 승격한다:
1. `contract_checks.py` (C1~C8) — 산출물 구조로 판정 가능한 것
2. `qa_lint.py` — 렌더 전 결정론 린트
3. `capture_deck.sh` FIT — 렌더 실측
4. qa-reviewer 필수 판정 필드 — 판단이 필요하되 기록 없이 pass 못 하게

승격 이력: 원문자 금지(C6)·stage 순서(C5)·요청 커버리지(qa 필수 필드·7/5)·**장르 필수 산출물(C8·7/5 신설)**.

## 3. 장르 라우팅

| 요청 신호 | 장르 스킬 | 필수 산출물 (C8) |
|---|---|---|
| "무엇이 변하나"·트렌드·전망 | genre-trend-report | 상태전이 인사이트 |
| 주제 발표·설득 | genre-topic-deck | — |
| 시장조사·경쟁분석·"X 시장에서 브랜드 Y" | genre-market-research | **분류 트리 1장 + 플레이어 비교표 1장**(5~8 플레이어 × 주력제품·가격대·포지셔닝·채널) + 관찰 출처 ≥5 |

## 4. 파일 스키마 (필수 필드 — 전체 예시는 최근 run 참조)

- `00_intake.json`: `genre`(등록값)·`audience`·`audience_literacy`·`provided_sources[]`·`target_market`·`language`·`evidence_profile`·`unknowns[]`
- `01_evidence_pool.json`: `items[]`(source_id·url|local_path·title·publisher·year·tier·source_type(`observation` 포함)·claims[]·metrics[]·limitations)·`gaps[]`
- `02_verified.json`: `source_registry{}`·`metric_registry{}`(value·unit·label·source_ids·basis)·`downgraded_items[]`·`discrepancies[]`
- `05_page_plan.json`: `pages[]`(page_id·role·short_title·allowed_source_ids·allowed_metric_ids·`genre_artifact`?)·`archetype`·`stage_log_patch[]`
- `06_deck_spec.json`: `pages[]`(layout·content 블록 — 타입은 contract_checks SUPPORTED_CONTENT_BLOCK_TYPES)·`theme`
- `07_qa_report.json`: `contract_results`·`c7_title_spine`·`visual_verdict`(4판정 페이지별)·`request_coverage`(항목별 충족/근거 페이지)·`external_review_layer3`

## 5. 갱신 규율

이 문서는 배선의 목차다 — 규칙 상세를 여기 복붙하지 않는다(이중 SoT 금지). 새 규칙이 생기면: ①해당 에이전트/스킬 SoT에 추가 ②코드 승격 여부 판단(§2) ③이 문서의 표에 한 줄 반영.
