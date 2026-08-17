# DELIVERY_OK 배선 결과

- 작업일: 2026-08-17 KST
- 기준 설계: `docs/LAYOUT_ALGORITHM.md` §G.5
- 구현: `.claude/skills/deck-harness/scripts/delivery_gate.py`
- 단위 검사: `.claude/skills/deck-harness/scripts/test_delivery_gate.py`

## 구현 결과

`delivery_gate.py <run_dir>`가 일곱 판정 결과를 기본 `08_delivery_report.json`에 저장한다. 일곱 결과가 모두 PASS일 때만 exit 0이며, 하나라도 FAIL이거나 결과 수가 일곱이 아니면 exit 1이다. 명령 실행 자체가 없거나 실패한 경우도 각 항목을 FAIL로 닫는다.

1. receipt 유효: 기존 `render_deck.py --html-only`를 subprocess로 호출한다. 추가로 런 폴더의 `*.unattested.*` 파일명과 HTML의 `UNATTESTED` 표식을 찾아 차단한다.
2. 최종 계약: 기존 `run_contracts.py --skip-spec-gates`를 subprocess로 호출한다. 덱 게이트·의도 보존은 5번에서 별도로 재실행한다.
3. FIT overflow: 기존 `capture_deck.sh`를 임시 PDF 출력 경로로 subprocess 호출하고 stdout의 `FIT_OK:`/`FIT_OVERFLOW:` 신호를 사용한다. 이 스크립트 뒤쪽의 잉크 실패가 FIT 실패로 중복 기록되지 않게 exit code만으로 판정하지 않는다. 문서에 적힌 `fit_report.json`은 현재 코드에 구현되어 있지 않아 존재를 가정하지 않았다.
4. 잉크 분포: 기존 `qa_ink.py`를 subprocess로 호출한다. 기존 명령은 도구 오류를 `INK_CHECK_SKIP`과 exit 0으로 낮추므로, 납품 판정에서는 stdout이 `INK_OK:`가 아니면 FAIL로 닫았다.
5. 덱 게이트·의도 보존: 기존 `run_contracts.py`를 일반 모드로 subprocess 호출해 C14·C15를 포함한 결과를 사용한다.
6. PDF 텍스트 레이어: 새 내부 함수 `count_embedded_fonts()`가 `pdffonts` stdout의 `emb` 열을 파싱한다. 명령 실패 또는 임베드 폰트 0개면 FAIL이다.
7. 전 장 시각 검토: 새 내부 함수 `validate_visual_review()`가 `07_qa_report.json`의 `visual_review.reviewer`, `reviewed_at`, `montage_path`, `scope: "all_pages"`와 몽타주 파일 존재를 검사한다.

## 납품 복사 경로

복사 경로 없음.

화면·venv·worktree·`Think/`를 제외한 실제 코드에서 납품 폴더로 `cp`, `shutil.copy`, `copy2`, `copytree`를 수행하는 프로덕션 경로를 찾지 못했다. 발견된 `shutil.copy*` 네 호출은 harness-contracts 테스트 fixture뿐이다. 확정 지시대로 새 복사 경로를 만들지 않았고 앞단 배선도 추가하지 않았다.

## 단위 검사와 회귀

- RED: 구현 전 신규 검사 5개가 `delivery_gate.py` 부재로 error 5건을 냈다.
- GREEN: 신규 unittest 8개 PASS, fail 0, skip 0. 기존 다섯 subprocess 항목을 subtest로 각각 실패시켰고, 6번 임베드 폰트 0개, 7번 전 장 검토 기록 누락을 각각 실패시켜 일곱 실패 분기 7/7을 확인했다. JSON 일곱 결과, 하나 실패 시 exit 1, 전부 통과 시 exit 0, 잉크 실패와 FIT 결과 분리, 런 밖 몽타주 거부도 확인했다.
- deck-harness: 53 PASS, fail 0, skip 0.
- harness-contracts: 167 PASS, fail 0, skip 0.
- Python 구문 검사: 2파일 PASS, fail 0, skip 0.
- `git diff --check`: PASS, 오류 0.

## 판단 근거와 미검증

- [판단] `fit_report.json`은 승인 문서에는 있으나 실제 생성 코드가 없다. 새 FIT 판정을 복제하지 않고 기존 `capture_deck.sh`의 `FIT_OK:`/`FIT_OVERFLOW:` 출력 신호를 사용했다.
- [판단] 2번과 5번의 책임을 JSON에서 분리하기 위해 2번은 `--skip-spec-gates`, 5번은 일반 모드로 호출했다. 전체 DELIVERY 판정은 일반 모드 결과까지 모두 PASS여야 하므로 C14·C15 실패가 누락되지 않는다.
- [미검증] 실제 런을 넣은 `delivery_gate.py` 전체 실행은 하지 않았다. Chrome·`pdftoppm`·`pdffonts` 등 화면 계열 바이너리 실행 금지 제약 때문이다. 본부에서 §G.5 명령으로 확인해야 한다.
- [미검증] 기존 `render_deck.py`는 canonical spec·registry와 receipt의 해시를 재검증하지만, 이미 존재하는 `deck.html`·`deck.pdf`가 그 receipt에서 나온 동일 산출물인지 대조하는 기존 검사는 현재 없다. 이번 지시의 "기존 검사 재구현 금지"를 지켜 새 결속 검사는 만들지 않았다. stale HTML/PDF 차단을 완성하려면 기존 캡처 계층에 receipt meta 대조 검사가 먼저 필요하다.
- [제약 위반 기록] 첫 GREEN 시도에서 테스트 mock이 기본 인자 바인딩을 우회해 `pdffonts`가 1회 실행됐다. 원인은 `runner=subprocess.run` 기본값이 함수 정의 시점에 고정된 것이며, `runner=None` 후 호출 시점 바인딩으로 수정했다. 수정 후 신규·회귀 검사는 화면 계열 바이너리를 호출하지 않는 코드 경로로 다시 통과했다.
- [잠재 리스크] receipt 재검증은 기존 renderer CLI의 현재 검증 범위에 의존한다. 기존 검증 범위가 바뀌면 DELIVERY 결과도 함께 바뀐다.

커밋·푸시는 하지 않았다. `Think/` 경로도 쓰지 않았다.
