# 작업: 틱덱 내용 엔진 → ppt-master 출력 엔진 교량 실증 1회

너는 코과장(Codex)이다. 본부 클차장이 보내는 자기완결 작업서다. 이 문서 밖의 대화 맥락은 없다고 가정하라.

## 0. 배경 (3줄)

- 틱덱 = 리서치 덱 생성 하네스. 강점은 내용(증거 검증 레지스트리·계약 코드 강제·팩트체크), 약점은 출력(PPTX가 배경 그림 + 텍스트박스라 PowerPoint에서 도형 편집 불가).
- `hugohe3/ppt-master`(46.9k★·MIT) = 반대. SVG로 페이지를 그려 DrawingML 네이티브 PPTX로 변환(요소별 편집 가능). 대신 팩트체크 게이트가 없고 내용 규칙이 얕다.
- **이번 작업 = 둘을 합칠 수 있는지 실측 1회.** 채택 결정이 아니다. 결론을 쓰지 말고 사실과 수치만 남겨라.

## 1. 진짜 산출물이 무엇인지 (제일 중요)

**이 실증의 산출물은 PPTX가 아니라 `MAPPING.md`다.** 우리 스펙을 저쪽 형식으로 번역할 때 ⓐ 자동으로 대응되는 필드 ⓑ 추론으로 억지로 채워야 하는 필드 ⓒ 아예 못 옮기는 것, 이 3분류가 "합칠 때 실제로 얼마나 드는가"의 유일한 실측 데이터다.

그래서 **순서가 강제된다: Phase 1(어댑터 + MAPPING.md)을 끝내고 파일을 디스크에 저장한 뒤에만 Phase 2(SVG 작성)로 넘어간다.** Phase 2에서 시간이 다 떨어져도 Phase 1 산출물이 있으면 이 작업은 성공이다. 반대로 PPTX만 있고 MAPPING.md가 부실하면 실패다.

## 2. 작업 루트와 환경

- 작업 루트 = 지금 이 폴더. **이 폴더 밖에는 아무것도 쓰지 마라.** 특히 `Think/inbox/` 에 보고서를 쓰려 하지 마라(샌드박스 밖이라 물리적으로 실패한다). 보고서는 이 폴더 안에 쓴다.
- **파이썬은 반드시 `./.venv/bin/python`** 을 써라. ppt-master 의존성(python-pptx·PyMuPDF·uharfbuzz·skia-pathops·flask 등)이 여기 설치돼 있다. 시스템 python3 로는 안 돈다.
- 폴더 구조:
  - `upstream/` — ppt-master 클론(commit `228fe8b7558f6c2abeb557952b10c8caff574b26`). **읽기만. 절대 수정 금지.**
  - `input/` — 틱덱 런 아티팩트 복사본(읽기 전용 취급)
  - `adapter/` — 네가 쓸 어댑터 코드
  - `project/` — ppt-master 작업 폴더(아직 없음. `project_manager.py init` 이 만든다)
  - `out/` — 최종 산출물
  - `MAPPING.md`·`REPORT.md` — 네가 쓸 보고

## 3. 입력 (input/)

| 파일 | 내용 |
|---|---|
| `06_deck_spec.json` | 틱덱 최종 덱 스펙. `pages[]` 16개. 각 페이지 = `page_id`·`short_title`·`layout`·`allowed_source_ids`·`allowed_metric_ids`·`content[]` |
| `02_verified.json` | 검증된 출처·수치 레지스트리. `source_registry` 32건(`publisher`·`url`·`title`·`tier`·`local_path`·`circular_group`), `metric_registry` 118건(`label`·`value`·`unit`·`source_ids`·`scope`·`verification_note`·`status`) |
| `00_intake.json` | 기획 입력. `topic`·`audience`·`genre`(trend-report)·`depth`·`constraints`·`evidence_profile` |
| `05_page_plan.json` | 페이지 계획(참고) |
| `deck_spec.schema.json` | 우리 스펙 JSON Schema. `layout` enum 26종·`content[].type` enum 20여종 정본 |
| `deck.pdf` | **대조군.** 우리 엔진이 같은 내용으로 낸 완성물(16페이지) |
| `style_navy_glow_premium/` | 우리 스타일 자산 1종. `STYLE_GUIDE.md`(색 관계 규칙 서술) + 예시 HTML 2장 |

이 덱의 주제 = 2026 마케팅 트렌드 리포트, 청중 = 한국 비즈니스·마케팅 실무자, 테마 = navy_glow.

## 4. 읽어야 할 upstream 문서 (순서 강제됨)

ppt-master 는 읽기 순서를 스스로 강제한다. 그대로 따르라.

1. `upstream/skills/ppt-master/SKILL.md`
2. `./.venv/bin/python upstream/skills/ppt-master/scripts/attribution_guard.py` 실행 — **비0 종료면 거기서 멈추고 REPORT.md에 기록 후 반환**
3. `upstream/skills/ppt-master/workflows/routing.md`
4. `upstream/skills/ppt-master/workflows/generate-pptx.md` (기본 경로)
5. `upstream/skills/ppt-master/references/strategist.md` **§6.2** — `design_spec.md` §I~§X 와 `spec_lock.md` 필수 필드 정본
6. `upstream/skills/ppt-master/templates/design_spec_reference.md`·`templates/spec_lock_reference.md` — 실제 스키마
7. `upstream/skills/ppt-master/templates/README.md` — 템플릿 4종. **이번엔 `style` 종만 쓴다**(`templates/design_spec.md` 한 장·SVG 로스터 없음)
8. `upstream/skills/ppt-master/workflows/stages/topic-research.md` Step 3 — `facts.json` 형식

## 5. Phase 1 — 어댑터 + MAPPING.md (여기부터. 끝나면 반드시 저장)

### 5-1. 스타일 세트 1종 이관

`input/style_navy_glow_premium/STYLE_GUIDE.md`(우리 자산)를 ppt-master `style` 종 템플릿으로 옮겨라.
- 출력 = `upstream` 이 아니라 **작업 루트 안**에 만들어라. upstream 수정 금지 원칙 유지를 위해, `register_template.py` 가 upstream 안을 건드려야만 동작한다면 **등재는 건너뛰고** 그 사실을 REPORT.md에 기록한 뒤 템플릿 없이(free design + design_spec 색 앵커) 진행하라. 어느 쪽을 택했는지 명시할 것.
- `exemplar_*.html` 2장은 참고만. style 종은 SVG 로스터를 갖지 않는 게 저쪽 규칙이다.

### 5-2. 어댑터 `adapter/bridge.py`

입력 `06_deck_spec.json` + `02_verified.json` + `00_intake.json` → 출력 `design_spec.md`(§I~§X) + `sources/<slug>.facts.json` + `spec_lock.md`.

알려진 대응(나머지는 네가 §6.2 읽고 직접 대조해 채워라):

| 틱덱 | ppt-master |
|---|---|
| `00_intake.json` audience·topic·genre | §I 소통 계약(`audience`·`communication_intent`·`core_message`·`consumption_mode`) |
| `06_deck_spec.json` pages[] 16개·순서 | §IX 페이지 로스터 **정확히 16개·순서 보존** (저쪽은 로스터 1항목 = 슬라이드 1장이 계약) |
| pages[].short_title | §IX Title |
| pages[].layout (이 런이 쓰는 10종: cover·index·divider·split·split_status·stack·hero_bleed·closing·outro·source_appendix) | §IX Layout |
| pages[].content[] | §IX preferred wording / 본문 |
| pages[].allowed_source_ids·allowed_metric_ids | §IX `sourced Fact IDs` ← **두 체계가 만나는 핵심 지점** |
| `source_registry` 32건 | `facts.json` 의 `source_title`·`source_url`·`classification` |
| `metric_registry` 118건 | `facts.json` 의 `claim` + §IX exact mathematical content |
| navy_glow 팔레트 | §I·§III 색 앵커 |
| **대응 필드 없음** | §IX **Audience move** (페이지마다 필수) |
| **대응 필드 없음** | `spec_lock.md` **page_rhythm** (페이지마다 `anchor`/`dense`/`breathing` 필수) |

**철칙: 숫자·출처는 반드시 `02_verified.json` 레지스트리에서 주입한다. 손으로 치거나 지어내지 마라.** 이게 틱덱 계약 C6의 정신이고, 이번 실증이 지키는지 보는 대상이다. `url` 이 빈 출처가 다수 있는데(로컬 코퍼스 기반), 어떻게 처리했는지 기록할 것.

### 5-3. `MAPPING.md` 작성 후 **디스크에 저장** (Phase 2 진입 전 필수)

필드별 3분류:
- **ⓐ 자동** — 우리 필드가 그대로 대응됨
- **ⓑ 추론으로 채움** — 대응 필드가 없어 규칙을 만들어 채움. **어떤 규칙으로 채웠는지 반드시 적을 것** (`page_rhythm`·`Audience move` 등)
- **ⓒ 못 채움/버림** — 옮길 수 없어 손실된 것

각 항목에 `[CONFIRMED:<파일:줄 또는 실행로그>]` / `[ASSUMED]` 태그를 붙여라.

## 6. Phase 2 — 저쪽 파이프라인 통과

1. `project_manager.py init` 으로 `project/` 생성 → 어댑터 산출물 배치
2. **Confirm UI(로컬 Flask 서버)는 띄우지 마라.** `generate-pptx.md` 에 있는 채팅 fallback / 명시 위임 경로를 쓴다. 확인값은 어댑터가 만든 `design_spec.md` 가 이미 갖고 있다.
3. Executor 로 16페이지 SVG 작성 → `svg_output/`
4. `./.venv/bin/python upstream/skills/ppt-master/scripts/svg_quality_checker.py --stage final ...` 로 검사
   - 저쪽 규칙 2개 준수: ① 출력을 `head`·`grep`으로 자르지 말고 전체를 볼 것 ② **하나 고치고 재검사 반복 금지** — 전체 이슈를 모아 1회 수정 후 1회 재검증
5. `svg_to_pptx.py` 로 내보내기 → `.pptx`

**AI 이미지 생성·나레이션·애니메이션은 하지 마라**(범위 밖·비용). 이미지가 필요한 자리는 네이티브 SVG 로 대체하라.

## 7. Phase 3 — 비교물

1. 나온 `.pptx` → `soffice --headless --convert-to pdf --outdir out/` (없으면 REPORT.md에 기록하고 건너뜀)
2. `pdftoppm -r 20 -png` 으로 저쪽 PDF와 `input/deck.pdf` 각각 콘택트시트 PNG 생성 → `out/`
3. 둘을 나란히 볼 수 있게 파일명 명확히 (`out/theirs_contact.png`·`out/ours_contact.png`)

## 8. 완료 기준

1. `MAPPING.md` — ⓐⓑⓒ 3분류 완비 (**최우선. 이것만 있어도 성공**)
2. `adapter/bridge.py` 1개 파일
3. `out/` 에 `.pptx` 1개. 슬라이드 수 = **16** (불일치면 실제 숫자를 보고)
4. `svg_quality_checker --stage final` 리포트 파일 + errors 0 (0이 아니면 남은 이슈 전량을 REPORT.md에 붙일 것)
5. `out/` 에 콘택트시트 PNG 2장
6. `REPORT.md` — 아래 형식

## 9. REPORT.md 형식

```
# 교량 실증 결과 (2026-08-15)
upstream commit: 228fe8b...
소요 시간: Phase별
## 완료 여부 (완료 기준 1~5 각각 O/X + 근거 경로)
## 막힌 지점 (있는 그대로. 우회했으면 어떻게)
## 수동 개입한 곳 전부 (어댑터가 못 해서 내가 손으로 채운 것)
## 검사기가 잡은 결함 유형 (몇 건·어떤 종류)
## upstream 코드를 고쳐야 했나 (Y/N. Y면 어디를 왜)
## 체감 비용 (페이지당 시간·재시도 횟수)
```

**결론·권고는 쓰지 마라.** "그래서 A로 가자" 류 판단은 후추님 몫이다. 사실과 수치만.

## 10. 가드레일

- **REPORT.md 는 진행하면서 계속 갱신하라.** 마지막에 몰아 쓰지 마라 — 시간이 끊기면 아무것도 안 남는다.
- **같은 접근 2회 실패 = 3번째 수정 금지.** 멈추고 "여기서 막혔다"를 REPORT.md에 기록한 뒤 다음 단계로 넘어가거나 반환하라.
- 완료 선언("됐다·통과")은 **실제 산출물을 확인한 뒤에만**, 근거 파일 경로를 같은 줄에 붙여서.
- 실패해도 REPORT.md는 쓴다. 어디서 왜 막혔는지가 그 자체로 이번 작업의 데이터다.
- 범위 팽창 금지: 스타일 세트 1개·런 1개. 레이아웃 26종 전체 이관 시도하지 마라.
