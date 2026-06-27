# 프레젠테이션 디자인 시스템 규칙 명세서 (Deck Engine Rulebook)

이 문서는 코드 기반 덱 엔진이 동일한 품질의 HTML 슬라이드를 자동 생성할 수 있도록, 디자인 판단을 수치와 조건 기반의 규칙으로 명문화한 것입니다.

---

## 1. 슬라이드 디자인 핵심 원칙

엔진은 다음 4가지 제약을 하드 코딩된 조건으로 적용해야 합니다.

*   **원칙 A: 1슬라이드 1메시지 (1S1M)**
    *   조건: 슬라이드당 `H1` 또는 `H2`는 1개만 허용.
    *   조건: 본문 텍스트(Paragraph)는 최대 3줄(또는 120자)을 넘지 못함. 초과 시 다음 슬라이드로 분할.
*   **원칙 B: 수직 균형 (Vertical Balance)**
    *   구조: `display:flex; flex-direction:column` 강제.
    *   비율: `Topbar` 60px (고정) + `Body` flex:1 + `Footbar` 60px (고정).
    *   Body 내부 여백: 상단 24px, 하단 40px, 좌우 56px. 내용이 수직 중앙에 위치하도록 `justify-content` 조정.
*   **원칙 C: 정보 위계 (Information Hierarchy)**
    *   순서: `Eyebrow(맥락)` → `Title(핵심)` → `Sub(설명)` → `Visual/Chart(증명)` → `Footbar(출처)`.
    *   텍스트는 절대 중앙 정렬(`text-align: center`)하지 않음. (단, Cover, Divider는 예외).
*   **원칙 D: 여백 처리 (Whitespace)**
    *   좌우 안전 여백: 56px (기본), 80px (표지 및 디바이더).
    *   요소 간 최소 간격: `gap: 24px` 이하로 설정 불가.

---

## 2. 내용 → 레이아웃 매칭 규칙

데이터 형태를 분석하여 아래 매핑 테이블의 레이아웃을 자동 선택합니다.

| 데이터 형태 (Input Type) | 매칭 레이아웃 (Output Layout) | 레이아웃 상세 규칙 |
| :--- | :--- | :--- |
| **단일 수치 (Single Metric)** | `Hero Metric` | 상단: Title/Sub. 하단: 120px 이상의 대형 수치 + 32px 우측 여백 + 보조 텍스트. |
| **2자 비교 (Comparison)** | `Dual Split` | `grid-template-columns: 1fr 1fr; gap: 32px`. 컬럼 사이 `width: 1px; background: var(--line-strong)` 세로선 삽입. |
| **시계열 (Time Series)** | `Hero Timeline` | 상단 60%: 인사이트 텍스트 카드 2~3개 가로 배치. 하단 40%: 꺾은선/막대 차트. 좌측 Y축 라벨 생략, 우측 끝 수치만 강조. |
| **다범주 (Multi-Category)** | `Agenda Grid` | `grid-template-columns: repeat(N, 1fr); gap: 18px`. N 최대 5. 카드 배경 `linear-gradient(180deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))`. 우측 하단에 `rgba(52,211,153,0.18)` 원형 글로우(90x90px) 삽입. |
| **수렴·퍼널 (Funnel)** | `Stepped Cards` | 단계별 박스 너비를 상위 대비 85%로 축소. 좌우 정렬은 중앙 기준. 배경 투명도를 단계별로 5%씩 증가시켜 깊이감 부여. |
| **표 (Table)** | `Zebra Data Grid` | 테두리 없음. 홀수행 배경 `#112037`, 짝수행 `#0b1626`. 헤더 폰트 12px, `letter-spacing: 0.12em`, `color: var(--dim)`. 텍스트는 우측 정렬(수치) 또는 좌측 정렬(문자). |

---

## 3. '빈 하단·여백 과다' 방지 기법

슬라이드 렌더링 후, 콘텐츠 높이가 Body 영역(600px)의 70% 미만일 경우 아래 로직을 순차적으로 실행합니다.

1.  **사이드 인사이트 카드 (Side Insight Card)**
    *   조건: 메인 비주얼(차트/이미지)의 너비가 Body의 70% 미만일 때.
    *   실행: 우측에 `width: 300px`인 인사이트 카드 생성. 배경 `rgba(255,255,255,0.03)`, `border-radius: 12px`. 내부에 12px 아이콘, 16px 소제목, 13px 본문 2줄 배치.
2.  **풋노트 바 (Footnote Bar)**
    *   조건: Body 하단 여백이 100px 이상일 때.
    *   실행: `Footbar` 영역을 활성화. 좌측에 출처 텍스트(`font-size: 11px; color: var(--dim)`), 우측에 3개의 키워드 태그(`border: 1px solid var(--line); padding: 4px 10px; border-radius: 99px`) 삽입.
3.  **분배 그리드 (Distribution Grid)**
    *   조건: Cover 또는 Divider 슬라이드에서 배경이 비었을 때.
    *   실행: `position: absolute; inset: 0`인 격자 무늬 배경 삽입. `background-size: 80px 80px`, `linear-gradient(var(--line) 1px, transparent 1px)`. 가장자리 페이드아웃을 위해 `mask-image: linear-gradient(180deg, transparent, black 30%, black 70%, transparent)` 적용.

---

## 4. 색·타이포·간격 시스템 (Design Tokens)

엔진의 CSS 변수로 직접 주입할 수 있는 값입니다.

### 4.1 컬러 시스템 (Color Tokens)
```css
:root {
  /* Base & Background */
  --navy-900: #070f1c; /* Body 배경 */
  --navy-800: #0b1626;
  --navy-700: #112037;
  --line: rgba(255,255,255,0.08); /* 기본 테두리 */
  --line-strong: rgba(255,255,255,0.16); /* 강조 테두리 */
  
  /* Text */
  --text: #e8eef6; /* 본문 */
  --muted: #8b9bb4; /* 부제/설명 */
  --dim: #5a6a82; /* 메타 정보/출처 */
  
  /* Accent (사용 제한: 1슬라이드당 3회 이하) */
  --accent: #34d399; /* 핵심 수치, 메인 포인트 */
  --accent-2: #5eead4; /* 타이틀 내 1단어 강조 */
  --gold: #e0b873; /* 2차 강조 (보조 데이터) */
  --violet: #8b8cf0; /* 3차 강조 */
}
```
*   **배경 규칙:** 무조건 그라디언트 사용. `linear-gradient(135deg, #0a1426 0%, #0b1626 60%, #0a1a1f 100%)`. 추가로 좌상단 또는 우하단에 `radial-gradient`로 10% 투명도의 `--accent` 잔광을 필수 삽입.

### 4.2 타이포그래피 (Typography)
*   **폰트 패밀리:** `"Pretendard", "Apple SD Gothic Neo", sans-serif"` 강제.
*   **위계:**
    *   `Cover H1`: 108px / weight: 900 / line-height: 0.98 / letter-spacing: -0.03em
    *   `Body H1`: 46px / weight: 800 / line-height: 1.15 / letter-spacing: -0.01em
    *   `Body H2`: 34px / weight: 800 / line-height: 1.2
    *   `Sub`: 16px / weight: 400 / color: `--muted` / line-height: 1.6 / max-width: 900px
    *   `Eyebrow`: 12px / weight: 700 / color: `--accent` / letter-spacing: 0.32em / uppercase (앞에 24px 가로선 삽입)
    *   `Foot`: 11px / color: `--dim` / letter-spacing: 0.12em

### 4.3 간격 시스템 (Spacing)
*   `XS`: 8px
*   `S`: 14px (Eyebrow-H1 간, Sub 상단 간)
*   `M`: 24px (Body 상단 패딩)
*   `L`: 40px (Body 하단 패딩, 섹션 간)
*   `XL`: 56px (좌우 기본 패딩)
*   `XXL`: 80px (Cover/Divider 좌우 패딩)

---

## 5. '아마추어처럼 안 보이게' 체크리스트 (Anti-Pattern Filter)

슬라이드 생성 후 아음 조건에 걸리면 렌더링을 거부하거나 자동 수정해야 합니다.

1.  **원문자/특수기호 사용 금지**
    *   조건: ①, ❶, ●, ■ 등의 문자 사용 시.
    *   수정: `<span>` 태그로 분리하여 `color: var(--accent)` 및 `font-weight: 900` 적용 후 일반 숫자로 치환.
2.  **균등 나열 및 중앙 정렬 남발 금지**
    *   조건: 본문 슬라이드에서 `text-align: center` 또는 `justify-content: center` 사용 시 (단, 메인 비주얼 제외).
    *   수정: 좌측 정렬(`flex-start`)로 강제 변경.
3.  **검은 배경 + 완전 흰 글씨 금지**
    *   조건: `background: #000000` 또는 `color: #ffffff` 사용 시.
    *   수정: 배경은 `--navy-900` 계열, 글씨는 `--text`(#e8eef6) 계열로 변경. 눈부심 방지 및 고급스러움 확보.
4.  **데두리 없는 카드 금지**
    *   조건: 배경색이 있는 박스에 `border` 속성이 없을 시.
    *   수정: `border: 1px solid var(--line)` 자동 부여.
5.  **단조로운 글먹으로 기호 금지**
    *   조건: `list-style-type: disc` 사용 시.
    *   수정: `list-style: none` 처리 후 각 `<li>` 앞에 8px 크기의 `--accent` 색상 정사각형 또는 점을 `::before`로 삽입.

---

## 6. 같은 레이아웃 반복 방지 규칙 (Layout Variation Engine)

사용자가 N장의 슬라이드를 요청할 때, 단조로움을 방지하기 위한 알고리즘 규칙입니다.

*   **연속 사용 제한:** 동일한 레이아웃은 최대 2연속까지만 허용. 3번째부터 강제로 다른 레이아웃 또는 디바이더를 삽입.
*   **디바이더(Divider) 삽입 주기:**
    *   조건: 챕터(목차의 1단계)가 바뀔 때마다, 또는 5~7장의 본문 슬라이드가 연속될 때.
    *   디바이더 디자인 변주 3가지 (랜덤 선택):
        1.  `Big Number`: 280px 크기의 챕터 번호, `color: transparent`, `-webkit-text-stroke: 1.5px var(--line-strong)` (아웃라인 텍스트).
        2.  `Quote`: 중앙 정렬의 64px 타이틀과 680px 너비의 인용구. 우측에 1px 세로선과 상단 60px 길이의 `--accent` 라인.
        3.  `Image Overlay`: (이미지 에셋 있을 시) 배경 이미지 + `rgba(7,15,28,0.85)` 오버레이 + 좌측 정렬 텍스트.
*   **차트 위치 교차:** 차트가 포함된 슬라이드가 연속될 경우, 홀수 번째는 우측 차트/좌측 텍스트(`flex-direction: row`), 짝수 번째는 하단 차트/상단 텍스트(`flex-direction: column`)로 강제 교차 배치.
*   **액센트 컬러 로테이션:** 5장 단위로 메인 액센트를 `--accent`(그린)에서 `--gold`(골드) 또는 `--violet`(바이올렛)로 1회 변경하여 시각적 리듬감 부여. (단, 토큰 `--accent` 값 자체를 변경하지 않고, 특정 슬라이드 내에서 `--gold`를 주 포인트로 사용).