# TickDeck → ppt-master 필드 매핑 실측

실행 범위: `input/00_intake.json` + `input/02_verified.json` + `input/06_deck_spec.json` → `adapter/generated/design_spec.md` + `adapter/generated/spec_lock.md` + `adapter/generated/sources/marketing_trends_2026.facts.json`

분류 기준: ⓐ는 원본 값의 의미를 바꾸지 않고 기계 투영, ⓑ는 목적지 필드가 없어 명시 규칙으로 생성, ⓒ는 이번 어댑터 출력에 보존되지 않은 필드다.

## ⓐ 자동 대응

| TickDeck 필드 | ppt-master 필드 | 변환 | 근거 |
|---|---|---|---|
| `00_intake.audience` | Design Spec §I `Target Audience`; lock `communication.audience` | 문자열 그대로 | [CONFIRMED:adapter/bridge.py:158] [CONFIRMED:adapter/bridge.py:294] |
| `00_intake.topic` | facts `topic` | 문자열 그대로 | [CONFIRMED:adapter/bridge.py:354] |
| `00_intake.genre=trend-report` | §I `Delivery Context`, `Reading Mode` | 장르를 보고서·balanced 소비 형태로 정규화 | [CONFIRMED:input/00_intake.json:1] [CONFIRMED:adapter/generated/design_spec.md:15] |
| `pages[]` 16개와 배열 순서 | §IX Slide 01~16 | 한 입력 페이지를 한 Slide block으로 순서 보존 | [CONFIRMED:adapter/bridge.py:250] [CONFIRMED:adapter/generated/design_spec.md:99] |
| `pages[].page_id` | §IX Part 표지의 추적 키 | `p01`→`Part 1: p01` | [CONFIRMED:adapter/bridge.py:258] |
| `pages[].short_title` | §IX `Title`, Slide heading, `Core message` | 문자열 그대로 | [CONFIRMED:adapter/bridge.py:259] [CONFIRMED:adapter/bridge.py:263] |
| 이 런의 `pages[].layout` 10종 | §IX `Layout` | 원본 layout id를 백틱으로 보존하고 flat SVG 재구성 지시 추가 | [CONFIRMED:adapter/bridge.py:262] [CONFIRMED:실행로그:layouts=10] |
| `pages[].content[]` | §IX `Content` | 모든 content 객체와 추가 키를 JSON으로 보존 | [CONFIRMED:adapter/bridge.py:124] [CONFIRMED:adapter/bridge.py:264] |
| 본문 `{{metric_NNN}}` | §IX `Content`의 표시 수치 | 레지스트리 `value`와 `unit` 연결값으로만 치환 | [CONFIRMED:adapter/bridge.py:106] |
| content 객체의 `metric_id` | §IX `Content.registry_value`, `registry_scope` | 레지스트리에서 값·범위를 주입 | [CONFIRMED:adapter/bridge.py:116] |
| `allowed_source_ids` | §IX `Fact IDs` | 출처 ID→고정 F ID lookup | [CONFIRMED:adapter/bridge.py:252] [CONFIRMED:adapter/bridge.py:272] |
| `allowed_metric_ids` | §IX `Fact IDs` | 수치 ID→고정 F ID lookup | [CONFIRMED:adapter/bridge.py:253] [CONFIRMED:adapter/bridge.py:272] |
| `allowed_metric_ids` | §IX `Mathematical content` | `label = value+unit [scope]`로 전량 투영 | [CONFIRMED:adapter/bridge.py:137] [CONFIRMED:adapter/bridge.py:270] |
| `source_registry` 32건 | facts 32건의 `source_title`, `source_url`, `classification` | 입력 순서대로 F001~F032 | [CONFIRMED:adapter/bridge.py:80] [CONFIRMED:실행로그:facts=150] |
| `metric_registry` 118건 | facts 118건의 `claim` | `label: value+unit (scope)`로 F033~F150 | [CONFIRMED:adapter/bridge.py:85] [CONFIRMED:실행로그:facts=150] |
| metric `source_ids`, `verification_note`, `status` | facts 확장 필드 | 원문 그대로 보존 | [CONFIRMED:adapter/bridge.py:95] |
| navy_glow 6색 앵커 | Design Spec §III; lock `colors` | 스타일 가이드 HEX 직접 투영 | [CONFIRMED:adapter/bridge.py:15] [CONFIRMED:adapter/generated/spec_lock.md:23] |
| navy_glow 폰트 스택 | Design Spec §IV; lock `typography` | Pretendard 우선 스택 보존 | [CONFIRMED:input/style_navy_glow_premium/STYLE_GUIDE.md:17] [CONFIRMED:adapter/generated/spec_lock.md:31] |
| 이미지 생성 제외 | §VIII 빈 테이블; §I `AI Image Acquisition Path: not applicable` | 범위 지시 직접 투영 | [CONFIRMED:adapter/generated/design_spec.md:21] [CONFIRMED:adapter/generated/design_spec.md:94] |

## ⓑ 추론으로 채움

| ppt-master 필드 | 입력에 없는 부분 | 생성 규칙 | 근거 |
|---|---|---|---|
| §I `Communication Intent` | 명시 필드 없음 | topic·genre를 “검증된 근거로 변화와 한국 실무 착지를 설명”으로 압축 | [ASSUMED] [CONFIRMED:adapter/generated/design_spec.md:11] |
| §I `Desired Audience Outcome` | 명시 필드 없음 | 청중이 네 실행 영역의 점검 기준을 말할 수 있는 상태로 정의 | [ASSUMED] [CONFIRMED:adapter/generated/design_spec.md:12] |
| §I `Core Message` | 단일 필드 없음 | P01과 P13의 반복 결론 “예산은 성과를 숫자로 보여준 쪽으로 움직인다”를 선택 | [ASSUMED] [CONFIRMED:adapter/generated/design_spec.md:13] |
| §I `Artifact Afterlife` | 편집 가능성 목표만 작업서에 존재 | “요소별 편집 가능한 16장 PowerPoint”로 작성 | [ASSUMED] [CONFIRMED:adapter/generated/design_spec.md:15] |
| §IX `Audience move` 16건 | TickDeck 대응 필드 없음 | layout별 10개 상태 전이 사전을 만들고 같은 layout에 같은 규칙 적용 | [ASSUMED] [CONFIRMED:adapter/bridge.py:37] [CONFIRMED:adapter/generated/design_spec.md:105] |
| lock `page_rhythm` 16건 | TickDeck 대응 필드 없음 | cover·hero·closing=`anchor`; divider·index·outro=`breathing`; 나머지=`dense` | [ASSUMED] [CONFIRMED:adapter/bridge.py:24] [CONFIRMED:adapter/generated/spec_lock.md:44] |
| §IX `Core message` 페이지별 | 별도 필드 없음 | `short_title`을 페이지 지배 주장으로 재사용 | [ASSUMED] [CONFIRMED:adapter/bridge.py:263] |
| §IX `Native shape suggestion` | 별도 필드 없음 | 모든 페이지에 기본 도형·연결선 우선 원칙 부여 | [ASSUMED] [CONFIRMED:adapter/bridge.py:273] |
| P01 `Cover impact` | 별도 필드 없음 | 표지 핵심 문구와 style guide의 글로우·3색 룰 바를 결합 | [ASSUMED] [CONFIRMED:adapter/bridge.py:275] |
| P13 `Closing impact` | 별도 필드 없음 | 결론 페이지의 세 대비와 한 문장 구성을 binding takeaway로 설정 | [ASSUMED] [CONFIRMED:adapter/bridge.py:277] |
| URL 공란 17건의 `classification` | ppt-master 표준 enum에 로컬 코퍼스 유형 없음 | URL이 있으면 `external`, 없으면 `local-corpus`; 빈 URL은 빈 문자열 유지 | [ASSUMED] [CONFIRMED:adapter/bridge.py:82] [CONFIRMED:실행로그:blank_urls=17] |
| 출처 자체의 `claim` | source registry에는 claim 없음 | “검증 출처 레지스트리: publisher — title”로 출처 추적용 fact row 생성 | [ASSUMED] [CONFIRMED:adapter/bridge.py:83] |
| `retrieved_at` | source별 수집일 없음 | `02_verified.verified_at` 날짜를 공통 사용 | [ASSUMED] [CONFIRMED:adapter/bridge.py:76] |
| §II 안전 여백·콘텐츠 영역 | TickDeck 스펙 없음 | 1280×720에서 좌우 64px·상하 48px, 1152×624로 설정 | [ASSUMED] [CONFIRMED:adapter/generated/design_spec.md:37] |
| §IV 글자 크기 | TickDeck 스펙 없음 | Title 42, Subtitle 26, Body 18, Annotation 12px로 설정 | [ASSUMED] [CONFIRMED:adapter/generated/design_spec.md:72] |
| `pptx_structure.mode` | TickDeck 대응 필드 없음 | style 등재 실패 뒤 free-design 경로의 upstream 규칙에 따라 `flat`; template scope는 생략 | [CONFIRMED:upstream/skills/ppt-master/references/strategist.md:531] [CONFIRMED:adapter/generated/spec_lock.md:62] |

## ⓒ 못 채움 또는 버림

| TickDeck 필드/정보 | 손실 내용 | 이유 | 근거 |
|---|---|---|---|
| `00_intake.rerun_of`, `rerun_purpose` | 재실행 계보·비교 목적 | ppt-master Design Spec/lock/facts에 대응 필드 없음 | [CONFIRMED:input/00_intake.json:1] [CONFIRMED:adapter/bridge.py:145] |
| `00_intake.depth` | 코퍼스 깊이·상태전이 분석 지시 | 목적지 정식 필드 없음; §I에는 결과만 남음 | [CONFIRMED:input/00_intake.json:1] [ASSUMED] |
| `00_intake.constraints[]` | 이전 런 금지·하네스 계약·외부 리뷰 규칙 | ppt-master 출력 계약으로 자동 변환하지 않음 | [CONFIRMED:input/00_intake.json:1] [ASSUMED] |
| `00_intake.evidence_profile` | 출처 목표·한국 현지화 차원·반대 견해 규칙 | facts는 개별 결과만 수용하고 수집 전략은 보존하지 않음 | [CONFIRMED:input/00_intake.json:1] [ASSUMED] |
| `00_intake.analysis_recipe`, `unknowns` | 렌즈 선택 근거·미확인 질문 | 최종 page/content/facts에는 간접 반영됐으나 별도 필드로는 손실 | [CONFIRMED:input/00_intake.json:1] [ASSUMED] |
| source `tier` | Tier-A/B 정보 | 현재 어댑터 classification은 URL 유무만 기록 | [CONFIRMED:adapter/bridge.py:82] |
| source `local_path` | 원본 로컬 파일 경로 | 외부 머신 절대경로라 portable facts에 넣지 않음 | [CONFIRMED:input/02_verified.json:1] [ASSUMED] |
| source `circular_group`, `conditions`, `provenance` | 순환 출처·독립성 판단 메타 | ppt-master facts 기본 필드에 대응 없음 | [CONFIRMED:input/02_verified.json:1] [ASSUMED] |
| verified `discrepancies`, `gaps_acknowledged`, `rejected_items`, `downgraded_items` | 검증 실패·불일치 이력 | 채택된 facts 변환만 구현 | [CONFIRMED:input/02_verified.json:1] [ASSUMED] |
| deck 상위 `run_id`, `theme`, `archetype`, `bundle`, `bundle_core_spec`, `meta`, `fit_check` | 하네스·번들·적합성 메타 | 페이지 내용과 시각 앵커 외에는 목적지 대응 없음 | [CONFIRMED:input/06_deck_spec.json:1] [ASSUMED] |
| page의 `eyebrow_chip`, `divider_style`, `divider_variant`, `part_index`, `part_label`, `part_count`, `cover_shape` | 페이지별 렌더러 힌트 | §IX `content` 밖 페이지 메타는 어댑터가 읽지 않음 | [CONFIRMED:adapter/bridge.py:250] |
| page의 `action_cards`, `watch_callback` | P14 세부 행동 카드 메타 | `content[]`만 본문으로 옮기므로 별도 키는 손실 | [CONFIRMED:input/06_deck_spec.json:1] [CONFIRMED:adapter/bridge.py:133] |
| `allowed_*_ids`의 “허용 목록” 의미 | 사용 허용과 실제 사용의 구분 | ppt-master `Fact IDs`는 실제 사용 ID를 요구하지만 어댑터는 허용 목록 전량을 투영 | [CONFIRMED:upstream/skills/ppt-master/references/strategist.md:531] [ASSUMED] |
| content type enum의 의미 체계 | `metric`, `footnote`, `viz` 등 타입별 native 계획 | JSON 본문은 보존하지만 타입별 ppt-master visualization/image/native 필드로 분해하지 않음 | [CONFIRMED:input/deck_spec.schema.json:1] [CONFIRMED:adapter/bridge.py:133] |
| source appendix의 실제 사용 출처만 필터링 | 실제 인용 집합 | P15에 레지스트리 32건 전체를 나열해 “실제 사용” 여부 구분 손실 | [CONFIRMED:adapter/bridge.py:125] [ASSUMED] |

## 실행 수치

- 입력 페이지: 16 [CONFIRMED:실행로그:pages=16]
- 입력 출처: 32 [CONFIRMED:실행로그:sources=32]
- URL 공란 출처: 17 [CONFIRMED:실행로그:blank_urls=17]
- 입력 수치: 118 [CONFIRMED:실행로그:metrics=118]
- 출력 facts: 150 = 출처 32 + 수치 118 [CONFIRMED:실행로그:facts=150]
- style workspace 파일: 1, SVG roster: 0 [CONFIRMED:style_navy_glow_premium/templates/design_spec.md:1]
- style 검사: 오류 1건(`template_style_contract_error`), 원인 `PyYAML` 미설치 [CONFIRMED:실행로그:style_template_check_exit=1]
- upstream 수정: 0건 [CONFIRMED:git status]
