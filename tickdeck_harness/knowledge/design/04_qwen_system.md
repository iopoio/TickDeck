# 프레젠테이션 디자인 시스템 아키텍처 (v1.0)
본 문서는 코드 기반 슬라이드 생성 엔진(Renderer)이 디자인 판단을 자동화할 수 있도록 임계값, 자료구조, CSS 규칙으로 명문화한 시스템 명세서입니다.

---

## 1. 슬라이드 디자인 핵심 원칙 (수치 조건부)

추상적 감각을 배제하고, 엔진이 판단할 수 있는 **수치적 임계값(Threshold)** 으로 정의합니다.

*   **1슬라이드 1메시지 (인지 부하 제한)**
    *   `MAX_NODES_PER_SLIDE = 3` (메인 카피 + 서브 카피 + 데이터 시각화 1개 또는 텍스트 블록 3개)
    *   `MAX_WORD_COUNT_BODY = 45` (본문 45단어 초과 시 자동 페이지 분할 또는 아코디언 UI로 전환)
*   **세로 균형 및 광학 중심 (Optical Center)**
    *   기하학적 중심(`top: 50%`)은 인간 시각에 아래로 처져 보임.
    *   **광학 중심 공식:** `top: 46.5%`, `transform: translateY(-50%)`
*   **여백(Margin) 및 안전지대(Safe Zone)**
    *   `MIN_MARGIN = 8%` (슬라이드 단축 기준 8% 이하의 여백은 무조건 위반으로 간주하여 컷오프)
    *   `CONTENT_MAX_WIDTH = 84%` (가독성을 위한 최적 라인 길이 유지)
*   **타이포그래피 위계 (Major Third Scale)**
    *   `H1: 48px` (메시지), `H2: 32px` (컨텍스트), `Body: 20px` (디테일), `Caption: 14px` (출처)
    *   `LINE_HEIGHT_BODY = 1.5`, `LINE_HEIGHT_TITLE = 1.1`

---

## 2. 레이아웃 어휘 (Layout Vocabulary Dict)

엔진이 콘텐츠의 `data_type`과 `semantic_weight`를 분석해 선택할 레이아웃 맵입니다.

```python
LAYOUT_DICT = {
    # [기본 및 구조]
    "Manifesto": {"condition": "단일 핵심 메시지, 15단어 이하, 감정적 호소", "css": "display: grid; place-items: center; text-align: center;"},
    "Split_5050": {"condition": "텍스트와 이미지/차트의 비중이 1:1일 때", "css": "grid-template-columns: 1fr 1fr; gap: 4rem;"},
    "Split_Asymmetric": {"condition": "시각적 증거(이미지)가 텍스트보다 중요할 때 (7:3 비율)", "css": "grid-template-columns: 7fr 3fr;"},
    
    # [데이터 및 논리]
    "BentoBox_Modular": {"condition": "서로 다른 4~5개의 독립적 지표/KPI를 동등하게 보여줄 때", "css": "grid-template-areas: 'a a b c' 'a a d d'; gap: 1.5rem;"},
    "Waterfall_Bridge": {"condition": "시작값과 끝값 사이의 증감 요인(플러스/마이너스)을 설명할 때", "css": "flex-direction: row; align-items: flex-end; /* 차트 엔진 연동 필수 */"},
    "Vs_Duel": {"condition": "A와 B의 양자택일, 비교, 대립 구도", "css": "grid-template-columns: 1fr auto 1fr; /* 중앙에 VS.Divider 배치 */"},
    "Zoom_Inset": {"condition": "거시적 차트에서 특정 미세 데이터(Micro-data)를 강조할 때", "css": "position: relative; /* 자식에 absolute 콜아웃 박스 부여 */"},
    
    # [프로세스 및 시간]
    "Timeline_Zigzag": {"condition": "3~5개의 시계열 이벤트 (직선보다 지그재그가 공간 효율적)", "css": "display: flex; flex-direction: column; /* 홀수/짝수 row 정렬 교차 */"},
    "Funnel_Conversion": {"condition": "이탈률이 존재하는 단계별 프로세스", "css": "clip-path: polygon(...); /* 너비를 비율에 따라 동적 축소 */"},
    
    # [독창적/고급 레이아웃]
    "FocalPoint_Mask": {"condition": "배경 이미지가 복잡하지만 텍스트 가독성이 필수일 때", "css": "background: linear-gradient(90deg, rgba(0,0,0,0.8) 40%, transparent 100%);"},
    "Quote_Kinetic": {"condition": "명언, 고객 리뷰, 핵심 인사이트 (타이포그래피 자체를 그래픽화)", "css": "font-size: clamp(3rem, 8vw, 6rem); text-indent: -0.05em; line-height: 0.9;"},
    "Iceberg_Reveal": {"condition": "표면적 문제 vs 근본 원인(숨겨진 데이터)을 대비할 때", "css": "grid-template-rows: 4fr 1fr 6fr; /* 수면 라인(border) 기준 위아래 분리 */"}
}
```

---

## 3. 빈 하단·여백 과다 방지 (Bottom-Gravity & Flex Stretch)

텍스트가 적을 때 슬라이드 하단에 텅 빈 공간이 생기는 '아마추어적 여백'을 코드 단에서 차단합니다.

**규칙 1: 콘텐츠 수직 정렬 전략 (데이터 길이에 따른 분기)**
```css
/* 텍스트가 짧음 (광학 중심 적용) */
.slide-container.short-content {
  display: flex;
  flex-direction: column;
  justify-content: center; /* 기하학적 중심이 아닌 optical center 보정값 적용 */
  padding-top: 4%; 
}

/* 텍스트가 김 (상단 고정, 하단 스트레치) */
.slide-container.long-content {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding-top: 8%;
}
.slide-container.long-content .body-text {
  flex-grow: 1; /* 남은 공간을 텍스트 영역이 흡수하여 하단 여백 방지 */
  display: flex;
  align-items: center; 
}
```

**규칙 2: 동적 폰트 스케일링 (`clamp` 활용)**
하단 여백이 15% 이상 남을 것으로 예측되면, 폰트 사이즈를 자동 확장하여 공간을 채웁니다.
```css
.dynamic-title {
  /* 최소 48px, 뷰포트 기준 6vw, 최대 84px */
  font-size: clamp(48px, 6vw, 84px); 
}
```

---

## 4. 색 팔레트 시스템 (Semantic Color Engine)

단순한 색상 나열이 아닌, **데이터의 의미(Semantic)** 에 따라 색이 할당되는 시스템입니다.

### 4-1. 테마 팔레트 (Hex)
1.  **Deep Tech (신뢰, SaaS, B2B)**
    *   Base: `#0F172A` (Slate 900), Surface: `#1E293B` (Slate 800)
    *   Primary: `#38BDF8` (Sky 400), Accent: `#34D399` (Emerald 400)
2.  **Warm Human (소비자, 라이프스타일, 스토리텔링)**
    *   Base: `#FAF9F6` (Off-White), Surface: `#F3EFE9`
    *   Primary: `#E07A5F` (Terracotta), Accent: `#3D405B` (Navy)
3.  **High-Contrast Data (대규모 컨퍼런스, 핀테크)**
    *   Base: `#000000` (Pure Black), Surface: `#121212`
    *   Primary: `#FF3366` (Neon Coral), Accent: `#00FFCC` (Cyan)

### 4-2. 배합 원리 및 다크/라이트 선택 기준
*   **60-30-10 변형 법칙:** `60%(Surface)` - `30%(Base/Text)` - `10%(Primary)` - **`+ 1%(Semantic Alert)`**
*   **다크모드 자동 선택 임계값:**
    *   `IF` 슬라이드 내 데이터 포인트(차트 막대, 노드) `> 15개` `THEN` **Dark Mode** (시각적 피로도 및 Data-Ink Ratio 최적화)
    *   `IF` 프로젝터 환경 변수 `== 'Low-Lux'` `THEN` **Dark Mode**
*   **색맹 안전성 (Colorblind Safe):** 상태를 나타낼 때 색(Color)만 쓰지 말고, 반드시 패턴(Pattern) 또는 아이콘(Shape)을 중첩(`e.g., ▲ + Red`, `▼ + Green`).

---

## 5. 안티패턴 필터 (Amateur Rejection Rules)

엔진이 렌더링 전 파싱 단계에서 다음 조건을 감지하면 **무조건 에러를 뱉거나 자동 변환**해야 합니다.

| 안티패턴 (감지 조건) | 자동 변환 규칙 (Fix Action) |
| :--- | :--- |
| `UL/LI` (불릿 포인트 3개 이상) | **변환:** `BentoBox` 또는 `Icon_Card_Grid` 레이아웃으로 강제 래핑 |
| `Raw URL` (http://... 텍스트 노출) | **변환:** 텍스트 숨기고 `QR_Code_Generator` 또는 `Hyperlink_Button`으로 대체 |
| `Text-Shadow` (텍스트 그림자) | **폐기:** 가독성 저하. 대신 `Background_Mask` 또는 `Solid_Contrast_Box` 적용 |
| `Center-Aligned Body` (본문 중앙정렬) | **변환:** 본문은 무조건 `Left-Aligned` (제목만 Central). `text-align: left` 강제 |
| `Pie Chart` (원 그래프) | **폐기:** 인간이 각도를 인지하기 어려움. `Donut_Chart` 또는 `Waffle_Chart`(10x10 그리드)로 강제 |
| `3D Effect` (입체감, 그림자 차트) | **폐기:** Data-Ink Ratio 위반. `Flat_Design` + `Gridline`으로 강제 |

---

## 6. 같은 레이아웃 반복 방지 (Rhythm & Pacing Engine)

청중의 지루함을 방지하기 위한 **슬라이드 페이싱(Pacing) 상태 머신**을 구현합니다.

**규칙: 레이아웃 쿨다운 (Cooldown)**
```javascript
// 최근 3개 슬라이드의 레이아웃 해시를 저장
const recentLayouts = [slide[n-3], slide[n-2], slide[n-1]];
if (recentLayouts.includes(currentProposedLayout)) {
    throw new LayoutRepetitionError("동일 레이아웃 3연속 사용 불가. 변형(Variant)을 선택하십시오.");
}
```

**규칙: 텐션과 릴리즈 (Tension-Release Rhythm)**
데이터 밀도(Data Density)를 점수화하여, 고밀도 슬라이드 다음에는 반드시 저밀도 슬라이드를 배치합니다.
*   `High Density` (차트, 표, 벤치마크) ➡️ **다음 슬라이드 강제:** `Manifesto` 또는 `FocalPoint_Mask` (시각적 환기)
*   `Low Density` (타이포, 인용구) ➡️ **다음 슬라이드 강제:** `Split_5050` 또는 `BentoBox` (논리적 근거 제시)

---

## 7. 💡 독창적 기법 (Senior Architect's Value-Add)

다른 모델들이 놓치기 쉬운, **코드 기반 렌더링 엔진에서만 가능한 고급 디자인 기법**입니다.

### A. 시맨틱 Z-인덱스 레이어링 (Semantic Z-Index Layering)
슬라이드를 단일 캔버스가 아닌 4개의 Z축 레이어로 분리하여 일관된 깊이감을 생성합니다.
*   `z-index: 0` **[Noise/Texture]**: 순수 디지털 느낌을 없애기 위한 2% 투명도의 그레인 노이즈 (SVG 필터).
*   `z-index: 10` **[Grid/Axis]**: 배경에 미세하게 깔리는 구조선 (신뢰감 부여, opacity: 0.05).
*   `z-index: 20` **[Content]**: 실제 텍스트 및 차트.
*   `z-index: 30` **[Highlight/Callout]**: 네온 컬러의 포인터, 강조 박스, 마커.

### B. 동적 데이터-잉크 비율CSS (Data-Ink Ratio Enforcer)
에드워드 터프티의 이론을 CSS로 구현. 차트 렌더링 시 불필요한 '차트 정크(Chart Junk)'를 자동 제거합니다.
```css
/* 차트 엔진에 주입할 글로벌 CSS 오버라이드 */
.chart-axis-line { stroke: #CBD5E1; stroke-width: 1px; } /* 축은 얇고 가볍게 */
.chart-grid-line { stroke-dasharray: 4 4; opacity: 0.3; } /* 그리드는 점선으로 인지 간섭 최소화 */
.chart-data-bar { stroke: none; } /* 막대 테두리 선 제거 (데이터 잉크 비율 극대화) */
```

### C. 마이크로-타이포그래피 커닝 (Optical Kerning for Titles)
대문자 또는 특정 폰트 조합에서 발생하는 시각적 불균형을 CSS `letter-spacing` 동적 할당으로 해결.
*   `IF H1 includes "A", "V", "W", "Y"` ➡️ `letter-spacing: -0.02em` (자간 축소)
*   `IF H1 is ALL_CAPS` ➡️ `letter-spacing: 0.05em` (자간 확장 + `font-weight: 600`)