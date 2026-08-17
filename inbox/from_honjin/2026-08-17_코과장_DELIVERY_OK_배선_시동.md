# 코과장 시동 — DELIVERY_OK 납품 판정 배선

- 발신 = 본부 클차장 · 2026-08-17
- 작업 루트 = `/Users/hwa/Projects/Automation/TickDeck` (git 저장소)
- 결과 보고서 = **`inbox/from_kogwajang/2026-08-17_DELIVERY_OK_배선_결과.md`**
- 기준 커밋 = `84186a1`

## 1. 한 줄

`docs/LAYOUT_ALGORITHM.md` §G.5에 설계만 적혀 있고 **코드가 없는** 납품 판정을 실제로 배선한다.

## 2. 설계는 이미 있다 (§G.5 · 그대로 구현한다)

`FIT_OVERFLOW_OK`는 "세로 넘침 없음" 한 가지 사실일 뿐이고, 납품 판정은 별도 명령이 아래 **일곱 가지 전부**를 요구한다:

1. receipt 유효 (spec·registry·calibration·렌더러 해시 4중 일치 · unattested 산출물 부재)
2. 최종 spec에 `run_contracts` 재실행 위반 0건
3. FIT overflow 0
4. 잉크 분포 게이트 통과 (§C.5)
5. 덱 게이트·의도 보존 통과
6. **PDF 텍스트 레이어**: `pdffonts` 기준 임베드 폰트 1개 이상 (이미지 전용 PDF 기계 차단. 사고 사례의 image PDF는 추출 텍스트가 26바이트였다)
7. 전 장 시각 검토 기록: `pdftoppm -r 20` 저해상 몽타주 + 검토자·시각을 `07_qa_report`에 기록 (표본 검토 금지)

**실패 시 = 납품 폴더 복사 차단.** 이게 이 게이트의 존재 이유다.

이미지(래스터) PDF 정책도 §G.5에 있다 — 납품 금지, 내부 검토용만, `*.raster.pdf` 파일명 강제, manifest 동봉(승인자 = 후추님), 납품 폴더 반입 금지, 만료일 경과 시 삭제.

## 3. 할 일

### (1) 판정 명령 신설

`.claude/skills/deck-harness/scripts/` 아래에 납품 판정 명령을 만든다. 이름·구조는 기존 스크립트(`spec_gate.py`·`run_contracts`)의 관례를 따른다.

- 입력 = 런 폴더 (예: `_workspace/20260727_mktg2026_rerun`)
- 출력 = 판정 결과 JSON (`fit_report.json`·`gate receipt` 형식을 참고해 일관되게)
- exit code로 통과·실패 전파

### (2) 일곱 항목을 하나씩 구현

**6번과 7번이 새 코드다.** 나머지 다섯은 이미 있는 것(receipt 검증·run_contracts·FIT 실측·덱 게이트)을 **불러 쓰는** 것이지 다시 구현하는 게 아니다. 중복 구현하지 마라.

- 6번 = `pdffonts` 결과를 파싱해 임베드 폰트 수를 센다. 0이면 실패
- 7번 = `07_qa_report.json`에 시각 검토 기록(검토자·시각·몽타주 경로)이 있는지 확인. 없으면 실패. **몽타주 생성 자체는 본부가 한다** (pdftoppm은 화면 계열이라 네 샌드박스에서 막힐 수 있다)

### (3) 납품 폴더 복사 차단

판정이 실패하면 납품 폴더로 복사되지 않아야 한다. 지금 복사가 어디서 일어나는지 찾아 그 앞에 게이트를 건다. 복사 경로가 없으면 **만들지 말고 보고서에 "복사 경로 없음"이라고 써라** — 없는 것을 지어내지 않는다.

### (4) 단위 검사

RED→GREEN으로. 일곱 항목 각각이 실패를 실제로 잡는지. 프레임워크 늘리지 말고 기존 테스트 파일 관례를 따른다.

### (5) 문서

`docs/LAYOUT_ALGORITHM.md` §G.5에 **구현 위치와 명령 사용법**을 덧붙인다. 설계 문장은 고치지 마라.

## 4. 하지 말 것

- 화면 계열 바이너리 실행 (Chrome·LibreOffice·ImageMagick·Quick Look·pdftoppm). 필요하면 코드만 쓰고 **본부가 실행한다**
- 이미 있는 검증(receipt·run_contracts·FIT·덱 게이트)을 다시 구현
- 없는 복사 경로를 새로 만들기
- `Think/` 경로에 쓰기 · 커밋·푸시

## 5. 보고서에 넣을 것

1. 일곱 항목을 각각 어디에 어떻게 배선했는지 (기존 코드 재사용 / 새 구현 구분)
2. 납품 폴더 복사 경로를 찾았는지, 못 찾았으면 그 사실
3. 단위 검사 결과 (일곱 항목이 실패를 잡는지)
4. 회귀 결과 — deck-harness·harness-contracts 양쪽
5. 미검증 `[미검증]` 표기 (특히 pdftoppm·pdffonts 실행분)
