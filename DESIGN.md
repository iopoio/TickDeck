---
project: TickDeck (URL → PPTX 자동 생성)
version: v0.1 (2026-04-27 신설, AI 디자인 톤 튐 차단)
brand_decision_gate: 후추님 명시 승인 필수 (메모리 feedback_design_md_workflow 정합)
references:
  - GeekNews DESIGN.md 한국어 정리: https://news.hada.io/topic?id=28861
  - 분석: Think/.claude/inbox/2026-04-27_긱뉴스_분석_DESIGN_md.md
status: draft (TickDeck 슬라이드 출력 톤 일관성 확보용)
---

# TickDeck DESIGN.md

> AI(Gemini·Claude)가 슬라이드 생성 시 **반드시 따라야 할 헌법**.
> "디자인 잘해줘" 추상 명령 X → 본 토큰·룰 안에서만 동작.
> 양방향 동기화 X — 코드 변경 시 사람이 의도적으로 본 파일 갱신 (PR 단위 검증).

---

## 1. Colors (토큰)

```yaml
colors:
  # 본진 디자인-가이드.md 정합
  primary: "#1F2937"          # 진한 회색 (메인)
  secondary: "#3B82F6"         # 블루 (포인트)
  background: "#FFFFFF"        # 순백
  surface: "#F8F9FA"           # 오프화이트 (카드·섹션)
  text_primary: "#1A1A1A"      # 메인 텍스트
  text_secondary: "#374151"    # 서브 텍스트
  text_muted: "#6B7280"        # 보조
  success: "#22C55E"
  warning: "#F59E0B"
  danger: "#EF4444"

  # 사용자 커스텀 (URL 페이지 브랜드 추출 시)
  user_primary: "[추출값]"
  user_accent: "[추출값]"
```

### Why
- 본진 디자인-가이드.md 정합 (`feedback_design_first` 메모리)
- AI 디자인 함정 (보라·핑크 그라디언트, 패스텔 무지개) 회피
- TickDeck = 사용자 URL 콘텐츠 변환 도구라 사용자 브랜드 우선, 본진 톤은 보조

### 금지 색
- 보라·핑크 그라디언트 (Stable Diffusion 톤)
- 모든 카드 그라디언트 보더 + glow
- 패스텔 무지개 (등급·태그마다 다른 색)

---

## 2. Typography (토큰)

```yaml
typography:
  display: "Noto Serif KR, serif"     # 표지·섹션 헤더
  body: "Pretendard, sans-serif"       # 본문
  mono: "JetBrains Mono, monospace"    # 코드·데이터
  sizes:
    h1: 36pt
    h2: 28pt
    h3: 22pt
    body: 14pt
    caption: 11pt
  weights:
    bold: 700
    medium: 500
    regular: 400
  line_height: 1.5
```

### Why
- Pretendard + Noto Serif KR = 본진 디자인-가이드.md 정합 + 한국어 디스플레이 강함
- "Generic Sans" (Inter / Poppins 단독) 금지 — AI 디자인 함정

---

## 3. Spacing (토큰)

```yaml
spacing:
  page_padding: 60pt
  section_gap: 40pt
  card_padding: 24pt
  list_gap: 16pt
  inline_gap: 8pt
```

---

## 4. Components

```yaml
components:
  slide_title:
    font: display
    size: h1
    color: primary
    align: left
    weight: bold
  slide_body:
    font: body
    size: body
    color: text_primary
    line_height: 1.5
  card:
    background: surface
    border_radius: 12pt
    padding: card_padding
    shadow: subtle
  badge:
    background: secondary
    color: white
    border_radius: 99pt
    padding_x: 12pt
    padding_y: 4pt
    font_size: caption
    weight: medium
```

---

## 5. Layout 룰

- **슬라이드 비율**: 16:9 기본 (4:3 옵션)
- **여백**: 페이지 가장자리 60pt 이상
- **섹션 간격**: 40pt
- **이미지**: 절반 이상 차지 X (텍스트 가독성 우선)
- **이모지**: 한국어 자연스러운 한도 (남용 금지)

---

## 6. AI 호출 룰 (Gemini 슬라이드 생성)

### 시스템 프롬프트 포함 의무
```
You MUST follow the design tokens defined in TickDeck/DESIGN.md.
- Colors: only use colors defined in `colors` section
- Typography: only use fonts defined in `typography.display`, `body`, `mono`
- Spacing: respect `spacing` token values
- If user URL has brand colors, override `user_primary` and `user_accent` only
- Forbidden: gradient backgrounds, rainbow palettes, generic-sans-only typography
```

### 결과물 검증 (lint)
- 토큰 외 색 사용 → 재생성 트리거
- 폰트 위계 무시 (h1·h2·h3 순서 X) → 경고
- 페이지 가장자리 여백 60pt 미만 → 경고

---

## 7. 사용 컨텍스트

### 적용
- TickDeck Phase4 PPTX 생성 (메인)
- `frontend/` 슬라이드 미리보기
- `gemini-prompts/` 시스템 프롬프트에 토큰 박기

### 미적용
- 사용자 입력 URL의 브랜드 톤 (사용자 우선) — 단 본진 룰의 "금지 색"은 항상 적용

---

## 8. 변경 이력

| 버전 | 날짜 | 결재 | 변경 |
|---|---|---|---|
| v0.1 | 2026-04-27 | 후추님 ① Y | 신설 (GeekNews DESIGN.md 도입) |

---

## ⚠️ 디자인 게이트 룰

본 DESIGN.md의 색·로고·브랜드 톤 변경은 **후추님 명시 승인 필수** (메모리 `feedback_design_md_workflow` 정합). Agent 합의 ≠ 후추님 승인 (EatScan 4/20 사건 정합).

다음 적용 단계 (제대리 의뢰 가능):
1. `gemini-prompts/` 시스템 프롬프트에 본 DESIGN.md 컨텍스트 박기
2. PPTX 생성 결과 lint 검증 스크립트 작성
3. 토큰 위반 시 재생성 자동 트리거
