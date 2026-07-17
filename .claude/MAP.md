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

## 관련 전역 메모리 (상세는 이관 중)
[[project_tickdeck_harness_v4]]·[[feedback_deck_design_peppinch_taste]]·[[project_deck_platform_tickdeck]]·[[project_tickdeck_showcase_plan]]·[[feedback_ai_deck_tooling]]·[[klcha_recurring_patterns]](#8 증식·코딩위임·뿌리고치기).

> 전체 메모리 federation(170개 도메인 폴더 분할)은 별도 신중 작업(정기-루틴 #10) — 즉흥 이관 X. 본 MAP은 덱 도메인 첫 이관.
