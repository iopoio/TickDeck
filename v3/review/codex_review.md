## 버그/정확성

- [P1] 중앙 표지가 빌드를 막습니다. `HEADER_EXEMPT`에 `contest_cover_title_date_centered`가 없고 `is-cover`도 무시합니다. 해당 제목은 실제 중앙 정렬이므로 30% 기준을 넘습니다. [validation.py:151](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/validation.py:151), [build.py:1737](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py:1737), [tokens.css:2701](/Users/hwa/Projects/Automation/Think/tools/deck_harness/styles/tokens.css:2701)
- [P1] `[data-name$="-title"]`은 슬라이드 제목이 아니라 카드·영역 제목도 잡습니다. 메인 제목이 비면 첫 카드 제목을 검사합니다. `[data-role="slide-title"]` 같은 명시적 표식이 필요합니다. [validation.py:160](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/validation.py:160), [build.py:473](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py:473)
- document 범위 셀렉터 자체는 현재 슬라이드별 HTML을 따로 검증하므로 교차 슬라이드 문제는 없습니다. [build.py:2448](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py:2448)
- layout 정규식은 현재 카탈로그가 소문자·숫자·`_`·`-`뿐이고 미등록 layout을 거부하므로 현재는 정확합니다. 다만 `classList` 기반 추출이 향후 변경에 더 안전합니다. [validation.py:157](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/validation.py:157), [build.py:2190](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py:2190)
- 반복·source-band 보고의 슬라이드 번호가 0부터 시작해 실제 번호보다 하나 작습니다. [design_lint.py:51](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:51), [design_lint.py:81](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:81)

## false-positive

- 가장 큼: `source-band`는 출처 여부가 아니라 `metric`에 값이 있으면 무조건 경고합니다. 이름부터 `with_metric`인 정상 사용도 걸립니다. [design_lint.py:78](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:78)
- `hardcoded-color`는 render 함수 안의 6자리 hex를 문맥 없이 block 처리합니다. 합법적인 흰색·SVG·예시 문자열도 걸리고, 반대로 CSS·3/8자리 hex·rgb는 놓칩니다. [design_lint.py:61](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:61)
- layout 반복은 덱 길이·의도와 무관하게 3회부터 경고합니다. 긴 보고서나 의도적 반복에서 오탐이 큽니다.
- balance는 고정 비율 기반이라 advisory 유지가 맞습니다. blocking 승격은 권하지 않습니다.

## 설계 평가

레지스트리는 적발 이력과 비전 체크리스트 SoT로는 좋지만, 실행 SoT는 아닙니다.

`LIVE_CHECKS`는 문자열 존재만 확인합니다. 실제 handler가 없어도 문자열만 추가하면 드리프트가 사라지고, `balance`처럼 여러 게이트가 한 이름을 공유하면 일부 검사가 삭제돼도 탐지하지 못합니다. [design_lint.py:24](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:24), [design_lint.py:122](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:122)

또한:

- warn은 exit code에 반영되지 않아 `gated = 사람 빠짐` 정의와 맞지 않습니다. [design_lint.py:151](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:151)
- 레지스트리 누락은 정상 처리되고, lint 예외도 빌드가 통과합니다. [design_lint.py:117](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/design_lint.py:117), [build.py:2562](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py:2562)

권장 구조는 게이트 ID별 실행 함수 매핑 + gated 항목마다 양성 fixture 테스트입니다. 레지스트리 누락·파싱·handler 오류는 fail-closed가 맞습니다.

## weight 정리 권고

가치는 있으나 정확성 수정 뒤의 중간 우선순위입니다.

현재는 13종이 아니라 `tokens.css`에 숫자 weight 18종, 102개 선언이 있습니다. 이미 상단에 5개 의미 토큰이 있지만 다수 컴포넌트가 우회합니다. [tokens.css:13](/Users/hwa/Projects/Automation/Think/tools/deck_harness/styles/tokens.css:13)

안전한 순서:

1. 후보 5단계는 `560 / 650 / 740 / 820 / 880`. 근접값 치환 후 역할별 재판정.
2. 전체 layout 샘플을 전후 PNG 비교하고 overflow·auto-fit·PDF·PPTX를 함께 검증.
3. PPTX는 `600 이상 = bold`이므로 치환 전후 이 경계를 절대 넘기지 않기. [pptx_export.py:203](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/pptx_export.py:203)
4. baseline 승인 후에만 raw `font-weight` 금지 게이트 추가. 토큰 정의·`@font-face`는 예외 처리.

Hahmlet은 100~900 variable font라 weight 변경이 실제 굵기와 줄바꿈을 바꿉니다. 일괄 치환은 시각 regression 위험이 큽니다. [build.py:2327](/Users/hwa/Projects/Automation/Think/tools/deck_harness/src/build.py:2327)

## 최우선 3개

1. header 제목에 명시적 role 추가, `is-cover` 자동 면제, 중앙 표지 회귀 테스트 추가.
2. `LIVE_CHECKS` 문자열 대조를 ID별 handler + 양성 fixture 계약 테스트로 교체하고 fail-closed 적용.
3. `source-band`를 “metric 존재”가 아닌 출처성 밴드로 좁히고 슬라이드 번호를 1부터 표시.

[미확인] Playwright 실측은 sandbox의 임시 디렉터리 생성 `EPERM` 때문에 실행하지 못했습니다.