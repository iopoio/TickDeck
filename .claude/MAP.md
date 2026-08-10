# TickDeck — 덱 작업 폴더 메모리 (먼저 읽기)

> 서비스 폴더 MAP 패턴([[feedback_per_service_folder_map]]). **TickDeck/덱 작업 시 이 파일 먼저 read.** 전역 MEMORY.md는 한 줄 포인터만 두고 상세는 여기로 이관(후추님 7/1 — "틱덱 폴더에 메모리 이관·작업 시 참고"). 코드/설계 정본(SoT)은 아래 파일들, 본 MAP은 *결정·취향·함정* 인덱스.

## 정본(SoT)
- 설계 = `PRD_v4.md`(원칙 1~6·계약 C1~C7·파이프라인·에이전트 8)
- 렌더 = `.claude/skills/deck-harness/scripts/render_deck.py`(PALETTES·차트 SVG·레이아웃)
- 작성 기준 = `.claude/skills/deck-harness/references/writing-standard.md`
- 장르 = `.claude/skills/genre-trend-report/SKILL.md` 등 · 에이전트 = `.claude/agents/`
- 재료 서랍 = `.claude/research/` — kimi_ppt_guide · **investor_intel_피칭덱_재료**(7/17 흡수·장래 피칭 장르용·수신자 조사→핏 게이트→맞춤 훅) 등

## 세 하네스 구분 (혼동 금지)
- **A 공용** `Think/tools/deck_harness/` — 여러 프로젝트 공용 렌더. **안 건드림.**
- **B 파이썬** `tickdeck_harness/` — 은퇴 예정·v4에 부품 기증 중.
- **C = v4** `.claude/skills/deck-harness/` + `.claude/agents/` — **현행 시스템·SoT.**

## ★덱 디자인 확정 취향 (7/1 긴 세션 — 재논의 X)
**펩핀치 비즈니스 컬러(`--theme peppinch`):**
- 포인트 = **오렌지 하나**(레드 X·"두 색 섞임" 싫어함). 배경 대비 튜닝: 다크 위 밝은 `#FF9B3D` / 크림 위 짙은 `#C86F1F`(밝은 오렌지는 크림서 안 읽힘 — 외부 리뷰 #1).
- 구조 = **표지·맺음 다크**(차콜 `#2A2F33`+오렌지) / **간지 회색**(중간 톤·글로우·그리드 X) / **본문 크림**(`#F1ECE0`).

**폰트 = 모던 산세리프(Pretendard).** AI/테크엔 **세리프(명조) X**(문학적·톤 충돌). "세련"은 폰트보다 여백·위계·디테일.

**위계:** 간지 헤드라인(40px) < 본문 제목(44px). 부제목은 한 단계 작게.

**줄바꿈:** 전역 `word-break: keep-all`(음절 쪼개짐 금지). 의도적 줄바꿈은 헤드라인 `\n`.

**배경:** 테크풍 도형(그리드·별자리·원) 금지 — 따뜻한 에디토리얼과 안 맞음.

**내용·구조:** 제목 척추(큰 제목만 훑어 논지 흐름·plain·병렬·은유조각 X)·증거 N장 병렬 `[도메인]—[이동]`·닫음 결론→제언·일반청중(AI=ChatGPT 50%+) 어려운 용어만 하단 각주(남발 X)·출처는 원본 보유면 URL X·appendix는 인용된 것만.

## 자꾸 유실되는 명시 (꼭 지킴)
- 출처 Tier-A = 컨설팅/투자/증권 PDF + 정부통계. 최우선 ≠ 베낄 답(교차 분석).
- **새로 만들기 금지** — 고칠 때 버전업·분화·은퇴 도장. 일회용 드라이버 = 안티패턴.
- **덱 피드백 = 하네스 뿌리 고치기**(렌더 함수·룰·기본값). 한 덱 패치 = 다음 덱 재발(후추님 반복 명시).
- **코딩(반복·대규모)은 코과장 위임** — 클차장 직접 폭주 X. 마무리(하드닝·테스트·커밋)는 코과장.
- 비저자 냉정 리뷰 기본값(자가 채점 X·destroyer/외부).

## 7/22~23 실주행(IT 기획자 리포트) — 렌더러 근본수정 5건 (재발 방지로 기록)

customer-zero 실독 리뷰에서 자동 게이트(C1~C9)가 못 잡는 렌더 버그가 다수 발견됨. 이후 런엔 이미 적용돼 있음 — 재발하면 아래부터 의심:
1. **`_render_stack`이 "첫 블록=hero 단독 + 나머지 전부 한 줄"이던 구조 결함** — body 문단이 차트/숫자 옆으로 밀려 split처럼 읽히던 재발 버그(p08·p15 실측). metric-card/metric-grid/viz(visual-card)만 한 행으로 묶고 body/callout/note는 각자 전폭 줄로 분리하게 근본수정.
2. **`_svg_multi_line`이 음수 포함 시리즈에서 좌표가 viewBox 밖 수천 단위로 이탈** — `number/vmax` 단순나눗셈이 원인, min-max 정규화로 수정. 값 라벨이 x축 카테고리 라벨과 겹치던 문제도 clamp(`(y0+h)-24`)로 완화.
3. **`{{metric_id}}` 인라인 토큰이 C6 검증은 통과하지만 페이지 하단 출처 인용 집계(`_iter_metric_ids`)에서 스캔 안 되던 버그** — 값은 맞게 나오는데 출처가 조용히 빠짐. 문자열 스캔 추가로 수정.
4. **PDF 한글 글자깨짐은 macOS Chrome/Skia가 로컬 CFF Pretendard를 수백 개 Type 3 glyph로 서브셋하며 잘못된 bbox를 만드는 문제** — HTML·ToUnicode 텍스트층은 정상인데 PDF 래스터에서만 다른 글자로 보였고 `pdftoppm`의 `Bad bounding box in Type 3 glyph`로 확인(8/10, 과거 closing h1도 같은 뿌리). 캡처는 공식 정적 TrueType-outline WOFF2를 data URI로 고정하고 `document.fonts.ready/check` 후 인쇄하며, 한글 Type 3 또는 bbox 경고가 남으면 PDF 생성을 실패시킨다.
5. **source_appendix 페이지의 eyebrow 기본값이 h1과 똑같이 "출처"라 단어가 중복 표시되던 것 + 불필요한 "출처 N곳" 카운트 배지 + 2단 자동전환** — eyebrow 미지정 시 비움·배지 제거·1단 고정으로 수정.

## 7/22~23 실주행 — 글쓰기 규율 추가 (writing-standard.md 반영 완료, 여기는 인덱스만)
- "경로"를 시나리오/기회/채용 대체어로 쓰지 않는다("경로라는 말을 보고서에서 잘 안씀" — 후추님 명시)
- 부제가 제목을 어순만 바꿔 복창 금지 — closing 레이아웃 h1 바로 아래 특히 주의
- 섹션·카드 내부 라벨(디바이더 부제·viz 제목·카드 헤드라인)도 은유 조각 금지 — C7 자동검사는 페이지 대제목만 훑어 이런 내부 라벨은 안 잡힘
- **"母집단" 같은 한자 혼용 금지 — "모집단"처럼 순한글로.** 학술/통계 용어 옮길 때 특히 주의(母集団 일본어 표기 습관이 새어나오기 쉬움)
- 표 열을 "분류"·"근거"처럼 내부 분석 카테고리 그대로 노출 금지 — 자연어 한 문장으로 풀 것(writing-standard §4 "법정·논리학 조어 금지"와 동일 원리)
- 지수(index) 수치는 기준점(base=100 등) 설명 없이 단독 노출 금지 — 각주 필수
- 모집단 방향을 뒤집은 재수집(Loop A)에서도 원하는 정확한 자료가 없을 수 있다 — 그럴 땐 가장 근접한 대안(모집단은 맞지만 측정 대상이 다른 자료)을 찾아 캐비앗과 함께 쓴다, 없는 척 넘어가지 않는다

## 7/23 드리블 30장 컬렉션 — CL-gradient_accent 구현 + 패턴 신규 등재

후추님 "디자인이나 컬러가 너무 세련되지 않다" 지적 후속. `dribbble_deck_shots_2026-07/` 30장을 클차장이 직접 열람(팔레트+레이아웃 동시 추출). 정본 등재는 `v3/axis2_layouts/PATTERN_LIBRARY.md` "2026-07-23 드리블 컬렉션 배치" 섹션 — 여기는 인덱스만.

- **구현·적용 완료**: `render_deck.py`의 `.metric-card`(방사 글로우)·`.title-band`(대각 그라디언트)·`page.cover_shape`("blob"\|"diamond" — 표지·아웃트로 다크배경 위 추상 실루엣)·divider PART 라벨에 eyebrow_chip 필배지 개방. 전부 치수 불변·전 테마 공용이라 안전. clo_it_planner_evolution 리포트에 실적용해 시각 확인.
- **후추님 피드백 반영(7/23 2차)**: 첫 라운드(글로우+그라디언트만)는 "양식이 너무 유사해서 별로" 지적 받음 — 원자 패턴을 더 얹어서(블롭/다이아몬드 표지 도형 + 필 키커) 재차 반영. 패턴을 원자 단위로만 흩어 등재하면 "같이 어울렸던 조합"이 사라진다는 지적도 받아 PATTERN_LIBRARY.md에 "묶음(Bundle)" 섹션 신설 — 상세는 정본 문서.
- **재확인**: 이 리포트가 쓰던 `--theme` 미지정 시 root `deck_spec.theme`가 우선 적용됨(CLI `--theme`는 override) — 테마 실험 전에 deck_spec 루트 확인할 것.
- **함정 기록**: `page_chrome: "title_band" → "running_head"` 전환은 기존 승인된 콘텐츠 밀도 그대로면 overflow 재발(5장 실측) — 크롬 스타일은 사후 테마 스왑 대상이 아니라 콘텐츠 재적합을 동반해야 하는 결정.
- **함정 확장 (7/23 후추님 실감으로 확정)**: `--theme` 팔레트 스왑만으로 만든 "디자인 변형안"은 사람 눈에 **"컬러만 조금 바꾼 크게 변한 게 없는 PPT"**로 보인다. 인상은 뼈대(제목 크롬·타이포 위계·페이지 골격)에서 나온다 — 진짜 변형안 = 크롬 교체 + 타이포 위계 재설정 + overflow 페이지 콘텐츠 재적합까지 포함한 재설계 패스. 묶음(BUNDLES) 적용 시 core.spec의 크롬·타이포 부품을 빼고 색만 입히면 묶음을 적용한 게 아니다.

## 7/23 GMS 아카이브 흡수 배치 1 (후추님 본인 저작 — 근거 최상급)

USB 2개 구출 완료: NO NAME 브랜드 PPT 14/40(잔여 26 대기) + GMS 2018_21 선별 197건(`~/Documents/이전회사_제안서_아카이브_2026-07/GMS_2018-21/`). 대표 7덱 열람 → PATTERN_LIBRARY "GMS 아카이브 배치 1" 섹션 + BUNDLES.json 묶음 2건(B-premium_photo_overlay·B-agency_minimal_white — **본인 실납품이라 reconfirmed 등급 즉시 부여**). 핵심 발견 = **CL-client_brand_accent**(수신자 브랜드색 차용·3사 10년 관통) — TickDeck에 없던 납품 장르 문법. ⚠ 리커버 최상위 67건(NXC 시절)은 USB 원본부터 파손 — 복구 불가 확인(해시 대조). 배치 2 잔여 = 시스루 HYBE/엔터 26건·GMS 잔여·NO NAME 26건.

## 관련 전역 메모리 (상세는 이관 중)
[[project_tickdeck_harness_v4]]·[[feedback_deck_design_peppinch_taste]]·[[project_deck_platform_tickdeck]]·[[project_tickdeck_showcase_plan]]·[[feedback_ai_deck_tooling]]·[[klcha_recurring_patterns]](#8 증식·코딩위임·뿌리고치기).

> 전체 메모리 federation(170개 도메인 폴더 분할)은 별도 신중 작업(정기-루틴 #10) — 즉흥 이관 X. 본 MAP은 덱 도메인 첫 이관.
