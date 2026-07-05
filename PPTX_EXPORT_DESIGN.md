# 레버 3 설계 — 편집 가능 PPTX 출력 (2026-07-05 Fable 5)

> 제품화 레버 3: "페이지 이미지"가 아니라 **텍스트를 고칠 수 있는 PPTX**. 구현 전 설계 문서 — 착수는 후추님 결재 후.

## 결정: 렌더러 이원화 ❌ → 레이아웃 복제 하이브리드 ⭕

| 안 | 방식 | 판정 |
|---|---|---|
| A. 전면 이미지 | 슬라이드=PNG 1장 | 편집 불가 — 레버 3 목적 미달. 탈락 |
| B. 네이티브 재구현 | deck_spec→python-pptx 별도 렌더러 | 레이아웃 엔진 2개 = 영구 drift·유지비 2배. v3에서 겪은 천장. 탈락 |
| **C. 레이아웃 복제** | 브라우저가 계산한 박스를 PPTX 좌표로 복제 | **레이아웃 SoT 1개 유지**(HTML/CSS). 채택 |

## C안 구조 (2파일)

1. **capture_deck.sh 확장** — 이미 headless Chrome을 돌린다. 페이지별로:
   - 텍스트 요소들의 `getBoundingClientRect()` + computed style(글꼴 크기·굵기·색·정렬) + textContent를 `layout_boxes.json`으로 덤프
   - 텍스트를 `visibility:hidden` 처리한 **배경판 스크린샷**(그라디언트·모티프·차트·카드 윤곽 포함) 페이지별 PNG
2. **pptx_export.py (신규)** — python-pptx로:
   - 슬라이드 배경 = 배경판 PNG (풀블리드)
   - `layout_boxes.json`의 각 텍스트 박스를 같은 좌표(px→EMU 환산)에 네이티브 텍스트박스로 오버레이
   - 서체 매핑: Pretendard → **맑은 고딕**(1순위)·나눔고딕(2순위) — 타 기기 호환([[deck-font-safety]] 규칙)

## 왜 이게 지속가능한가
- 레이아웃 계산은 계속 브라우저 한 곳: v4 디자인 진화(새 layout·테마)가 **자동으로 PPTX에 따라옴** — export층 수정 불필요
- 차트·모티프는 배경판에 박제(어차피 사용자가 고치는 건 텍스트·수치)
- C6 부산물: 수치가 전부 registry 주입이라, 텍스트박스에 metric_id를 alt-text로 심으면 **PPTX에서도 근거 추적** 유지(레버2 신뢰 표면의 연장)

## 알려진 절충 (수용)
- 텍스트박스 줄바꿈이 브라우저와 1~2px 다를 수 있음 — 박스 폭을 rect보다 +2% 여유
- 편집 시 배경판의 카드 윤곽과 텍스트가 어긋날 수 있음 — "가벼운 문구 수정용"으로 포지셔닝 (전면 재편집은 B형 로드맵 밖)
- ==강조== 색전환은 run 단위 분해 필요 — v1은 통짜 텍스트(강조색 손실), v2에서 rich run 분리

## 수용 기준 (착수 시)
1. `pptx_export.py <run_dir>` → deck.pptx 생성, PowerPoint/Keynote에서 열림
2. 텍스트 전부 선택·수정 가능, 좌표 오차 육안 무감(±3px)
3. 맑은 고딕 폴백 확인 (Pretendard 없는 기기 시나리오)
4. 기존 게이트 무영향 (render/contracts 경로 변경 없음 — export는 후단 부가물)

## 규모 추정
capture 확장 ~40줄(JS) + pptx_export ~150줄 = Codex 1~2회 위임 + 실측 검수 1회. 기간 하루 내.
