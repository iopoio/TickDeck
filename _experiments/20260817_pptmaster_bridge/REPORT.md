# 교량 실증 결과 (2026-08-15)
upstream commit: 228fe8b7558f6c2abeb557952b10c8caff574b26
소요 시간: 총 17분(19:11~19:28 KST); Phase 1 약 5분, Phase 2 약 8분, Phase 3 약 4분

## 완료 여부 (완료 기준 1~5 각각 O/X + 근거 경로)

1. O — `MAPPING.md`: ⓐ 자동, ⓑ 추론, ⓒ 손실 3분류와 `[CONFIRMED]`/`[ASSUMED]` 근거 포함
2. O — `adapter/bridge.py`: 문법 검사 1/1 통과; `adapter/generated/`에 16페이지, 150 facts 생성
3. O — `out/tickdeck_pptmaster_bridge.pptx`: python-pptx와 OOXML 양쪽에서 슬라이드 16장 확인; shape 59개; exporter skipped 0
4. O — `out/svg_quality_final_report.json`: final 검사 errors 0, warnings 16, 검사 대상 16파일
5. O — `out/ours_contact.png`, `out/theirs_contact.png`: 각각 4×4, 16페이지. theirs는 LibreOffice PDF가 아니라 `svg_final/` 직접 렌더 fallback

## 막힌 지점 (있는 그대로. 우회했으면 어떻게)

- attribution guard: `./.venv/bin/python upstream/skills/ppt-master/scripts/attribution_guard.py`, 2026-08-15 19:11:04 KST, 종료 코드 0, 표준 출력 없음.
- style workspace는 `style_navy_glow_premium/templates/design_spec.md` 한 파일로 만들었다. upstream가 읽기 전용이어서 등록은 생략했다.
- style template 검사 1회: 오류 1건(`template_style_contract_error`). 가상환경에 `PyYAML`이 없어 YAML frontmatter를 읽지 못했다. 의존성 설치나 upstream 수정 없이 free design + planning artifact 색 앵커로 진행했다.
- `project_manager.py init project --dir .`이 `project_ppt169_20260815/`를 생성해, 초기화 직후 `project/`로 이름을 바꿨다.
- project validate 1차: 오류 1건(`Icon Usage` 제목 불일치), 경고 2건. §VI 제목을 `Icon Usage Specification`으로 고쳐 2차 검사에서 오류 0, 경고 2건이었다. 경고는 SVG 미작성 상태와 사용자가 고정한 `project/` 이름의 날짜 접미사 없음이다.
- live preview: `127.0.0.1:6060..6109`에 빈 포트가 없어 종료 코드 1. preview 없이 SVG를 작성했다.
- P05/P10/P15 직후 예정된 lock 재열람을 지키지 못했고, P02~P16 작성 뒤 한 번 재열람했다. 중간 checker 호출은 0회였다.
- LibreOffice PDF 변환 2회 모두 `Abort trap: 6`, 종료 코드 134. 1차 기본 프로필, 2차 작업 루트의 전용 `lo_profile/`을 사용했다. 세 번째 시도는 하지 않았다.
- ImageMagick SVG 렌더 2회 모두 빈 폰트 해석 오류로 실패했다. Quick Look 1회도 sandbox 초기화 오류로 실패했다.
- `out/theirs_contact.png`는 PIL로 `svg_final/`의 rect/circle/line/text를 직접 렌더한 fallback이다. 따라서 `soffice → PDF → pdftoppm` 결과가 아니다. `out/ours_contact.png`는 지시대로 `input/deck.pdf`를 `pdftoppm -r 20 -png`로 변환해 묶었다.

## 수동 개입한 곳 전부 (어댑터가 못 해서 내가 손으로 채운 것)

- `Audience move`: layout별 10개 상태 전이 사전으로 16건 생성.
- `page_rhythm`: cover·hero·closing=`anchor`, divider·index·outro=`breathing`, 나머지=`dense` 규칙으로 16건 생성.
- URL 공란 17건: 빈 문자열을 유지하고 `classification: local-corpus`로 표시.
- source 자체 fact의 claim: `검증 출처 레지스트리: publisher — title` 형식으로 생성.
- §II 안전 여백·콘텐츠 영역, §IV 글자 크기, 페이지별 Native shape suggestion, cover/closing impact를 규칙으로 채움.
- `style_navy_glow_premium/templates/design_spec.md`를 STYLE_GUIDE에서 수동 이관. SVG roster와 자산 폴더는 만들지 않음.
- P01~P16 SVG를 메인 에이전트가 직접 작성. 외부 이미지·나레이션·애니메이션은 사용하지 않음.
- final 1차의 footer bounds 경고 14건을 한 번의 일괄 수정으로 고침.
- LibreOffice 실패 뒤 ours contact는 PDF 페이지 PNG를 조합, theirs contact는 SVG 직접 렌더 fallback으로 조합.

## 검사기가 잡은 결함 유형 (몇 건·어떤 종류)

- style template 검사: error 1 — `template_style_contract_error` (`PyYAML` 미설치).
- project validate 1차: error 1 — Design Spec §VI 제목 불일치; warning 2 — SVG 비어 있음, project 이름 날짜 접미사 없음.
- first-page 1차: error 1종 — visible root `<g>` 3개의 `data-pptx-bounds` 누락; warning 2종 — PPT-safe font, ungrouped root elements.
- first-page 재검증: errors 0, warnings 1 — PPT-safe font.
- final 1차: errors 0, warnings 30 — font 16, footer bounds 14.
- final 재검증: errors 0, warnings 16 — 페이지별 Pretendard/Noto Sans KR unsafe exported font advisory. footer bounds 14건은 제거됨.
- PPTX postflight: `passed-with-warnings`; `quality_introduced_warnings=16`, `unsafe_exported_font_faces=3`; 슬라이드 16, skipped 0.
- 대조군 콘택트시트 시각 QA: 빈 페이지 0, 잘림 0, 배열 오류 0; P15 출처 글자가 조밀함.
- generated fallback 콘택트시트 1차 QA: 알파 합성 오류로 카드·표 저대비 다수. renderer를 알파 합성으로 수정해 재생성; 육안상 4×4 16장, 빈 페이지·겹침·캔버스 잘림 0.

## upstream 코드를 고쳐야 했나 (Y/N. Y면 어디를 왜)

- N. `git -C upstream status --short` 출력 0줄. upstream 코드·문서·index 수정 0건.

## 체감 비용 (페이지당 시간·재시도 횟수)

- Phase 2 전체 약 8분 / 16장 = 페이지당 약 0.5분. 문서 읽기·SVG 작성·검사·export 포함 수치.
- 어댑터 실행: 1회 성공. free-design 표시 교정 뒤 Phase 1 재검증 1회.
- style 검사: 실패 1회, 재시도 0회.
- project validate: 1회 수정 + 1회 재검증.
- P01 gate: 1회 수정 + 1회 재검증.
- final gate: 1회 일괄 수정 + 1회 재검증.
- PPTX export: 재시도 0회.
- LibreOffice: 실패 2회, 중단.
- ImageMagick SVG raster: 실패 2회, 중단. Quick Look 실패 1회. PIL fallback 1회 수정 + 1회 재렌더.

## 산출물 계측

- 입력: pages 16, source_registry 32, metric_registry 118, URL 공란 source 17.
- facts 출력: 150 = source 32 + metric 118; Fact ID `F001`~`F150` 중복 0.
- SVG: `svg_output/` 16, `svg_final/` 16.
- PPTX: 47,223 bytes, 슬라이드 XML 16, python-pptx shape 59, text run 191, text 2,654자, placeholder hit 0.
- contact: ours 238,872 bytes; theirs 147,025 bytes.
- 기존 사용자 변경 `../../.gitignore` 1건은 건드리지 않음.
