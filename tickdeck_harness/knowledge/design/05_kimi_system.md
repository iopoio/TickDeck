 ```markdown
# Presentation Deck Design System — Engine Spec
## ver. 1.0 | Code-Native Layout Engine

---

## 1. 슬라이드 디자인 핵심 원칙 (수치 조건)

### 1-1. 캔버스 & 그리드
| 속성 | 수치 | 엔진 변수 |
|------|------|-----------|
| 기본 해상도 | 1920×1080 (16:9) | `--canvas-w`, `--canvas-h` |
| 안전 영역(Safe Zone) | 상 120px / 하 **96px** / 좌우 120px | `--safe-top`, `--safe-bottom`, `--safe-x` |
| 모듈(수직 리듬) | 32px 기준 | `--rhythm-unit` |
| 행 간격(leading) | Body 1.5 / Headline 1.2 | `--leading-body`, `--leading-head` |

### 1-2. 위계 & 타이포그래피 (Clamp 기반)
```css
:root {
  --t-hero: clamp(40px, 4.4vw, 64px);   /* 1슬라이 1메시지 */
  --t-h1:   clamp(32px, 3.3vw, 48px);   /* 섹션 타이틀 */
  --t-h2:   clamp(24px, 2.2vw, 32px);   /* 서브 헤드 */
  --t-body: clamp(18px, 1.6vw, 24px);    /* 본문 */
  --t-meta: clamp(14px, 1.1vw, 18px);    /* 캡션/소스 */
}
```

### 1-3. “1슬라이드 1메시지” 강제 규칙
- **Visual Center**: Y축 상위 `22% ~ 35%` 구간에 반드시 Main Claim 배치. 물리중심(50%)보다 5% 상향 보정(Optical Alignment).
- **컨텐츠 밀도(Content Density Index)**: `(text_character_count × 0.015) + (image_count × 0.25) + (list_item_count × 0.1)` → `0.35 ~ 0.75` 유지.
  - `< 0.35` 이면: 보조 그래픽, 인용부호 장식, 또는 넓은 이미지로 **fill trigger** 작동.
  - `> 0.75` 이면: 슬라이드 분할 제안(split_heavy_content=true).

### 1-4. 세로 균형 (Vertical Rhythm)
- 모든 요소의 top margin은 `32px` 배수. 예외 허용 시 `16px`(마이크로 조정)만 추가 가능.
- 하단 여백(마지막 요소 ~ `--safe-bottom`)이 `160px` 초과 시 `ALIGN_BOTTOM` 보정: `margin-top: auto` 또는 `align-content: space-between`.

---

## 2. 레이아웃 어휘 (Layout → Condition Dict)

**매핑 원칙**: Content-Layout Affinity Score(0.0~1.0)를 계산해 가장 높은 레이아웃을 선택. 동점 시 시각적 피로도가 낮은 쪽 우선.

```python
LAYOUT_VOCAB = {
    # 단일 메시지
    "MONO_STATEMENT": {
        "condition": "슬라이드 전체를 1개의 핵심 문장(20단어 이하)이 점유해야 할 때",
        "affinity": {"claim_count": 1, "media_count": 0, "text_length_max": 120},
        "variant": "hero_full, centered, optical_up_5pct"
    },
    # 좌우 비대칭 서술
    "ASYMMETRIC_TWO": {
        "condition": "서로 다른 성격의 2개 주제(예: 문제/해결, 인물/인용, 전/후)를 대비할 때",
        "affinity": {"claim_count": 2, "contrast_intent": True},
        "split": "38% / 62% (Golden Ratio近似)"
    },
    # 이미지 고정 + 텍스트 흐름
    "FACTORY_SPLIT": {
        "condition": "좌측에 반드시 보여야 할 시각 자료(차트, 제품, 스크린샷)가 있고 우측에 분석 텍스트가 있을 때",
        "affinity": {"visual_anchor_side": "left", "text_blocks": ">=1"},
        "split": "45% / 55%"
    },
    # 대각선 분할 (독창)
    "DIAGONAL_SLICE": {
        "condition": "충돌, 변화, Before/After, 두 집단의 명백한 대립을 시각화할 때",
        "affinity": {"conflict_theme": True, "dichotomy": True},
        "shape": "clip-path: polygon(0 0, 100% 0, 55% 100%, 0 100%) / complement"
    },
    # 정중앙 철학 (독창)
    "TRUE_CENTER": {
        "condition": "비전, 브랜드 슬로건, 철학 구절로 청중의 몰입이 필요할 때. 배경 minimal.",
        "affinity": {"emotive_weight": "high", "data_count": 0},
        "rule": "padding: 0; text-align: center; max-width: 70%"
    },
    # 깊이 레이어 (독창)
    "DEEP_LAYER": {
        "condition": "시스템 아키텍처, 구성요소가 중심(허브)과 주변(스포크) 관계일 때",
        "affinity": {"hub_spoke": True, "node_count": "3~6"},
        "depth": "z-index 10/20/30, scale 0.9~1.1, blur backdrop"
    },
    # 계단식 배치 (독창)
    "STAGGERED_STAIR": {
        "condition": "3~5단계 프로세스/타임라인을 보여주되, 직선 배열이 지루하거나 공간이 남을 때",
        "affinity": {"sequence_count": "3~5", "horizontal_space": "generous"},
        "offset": "각 카드 Y축 +40px씩 번갈아 이동"
    },
    # 부유하는 섬 (독창)
    "FLOATING_ISLAND": {
        "condition": "중심 1개 개념을 둘러싼 3~4개의 위성 정보(수치, 태그, 단편 팩트)를 부드럽게 배치할 때",
        "affinity": {"satellite_items": "3~6", "center focal": True},
        "rule": "중심 요소 blur(0), 주변 요소 opacity 0.8"
    },
    # 이중 난간(Trellis)
    "TRELLIS_GRID": {
        "condition": "동등한 중요도의 4~6개 소주제를 동시에 나열해야 할 때(기능, 가치, 팀원)",
        "affinity": {"card_count": "4~6", "equal_priority": True},
        "grid": "2×2 또는 3×2, gap 32px"
    },
    # 이미지 블리드 + 인셋 텍스트
    "BLEED_EDGE": {
        "condition": "감성, 분위기, 장소성이 중요하고, 전체 이미지를 써야 하지만 텍스트 가독성도 필요할 때",
        "affinity": {"image_dominant": True, "mood_intent": True},
        "rule": "이미지 100% cover, 텍스트는 gradient scrim 위 인셋 박스"
    },
    # 불규칙 클러스터 (독창)
    "MASONRY_CLUSTER": {
        "condition": "같은 카테고리 아이템(팀원, 고객 로고, 기능 모듈)이 높이/길이가 제각각일 때",
        "affinity": {"heterogeneous_sizes": True, "collection": True},
        "rule": "auto-fit minmax(280px, 1fr), align-items: start"
    },
    # 중첩 스택 (독창)
    "OVERLAP_STACK": {
        "condition": "포트폴리오, 갤러리, 3개 이미지를 하나의 덩어리(depth illusion)로 보여줄 때",
        "affinity": {"image_count": "2~4", "portfolio_mode": True},
        "rule": "translateX(-20/0/20px) translateY(10/0/10px) rotate(-2/0/2deg)"
    },
    # 리포터 인셋
    "INSET_REPORTER": {
        "condition": "상단에 작은 썸네일/아이콘과 함께 방대한 분석 텍스트(리포트 스타일)가 있을 때",
        "affinity": {"text_heavy": True, "media_small": True},
        "rule": "상단 20% 미디어 스트립, 하단 80% 텍스트 컬럼"
    },
    # 래더 화이트보드
    "WIDE_ASSET": {
        "condition": "대시보드, 와이어프레임, 지도 등 가로 긴 이미지를 그대로 보여주고 아래 짧은 설명이 필요할 때",
        "affinity": {"media_aspect": "wide", "landscape_image": True},
        "rule": "이미지 상/하단 full-bleed, 중앙 60px 밴드에 문구"
    },
    # 선언문 리스트
    "MANIFESTO_LIST": {
        "condition": "3~4개 핵심 원칙, 약속, KPI를 숫자와 함께 압도적으로 보여줄 때",
        "affinity": {"bullet_count": "3~4", "principles_or_numbers": True},
        "rule": "숫자는 var(--t-hero), 문구는 var(--t-body), 각 항목 사이 48px"
    },
    # 스코프 레이더 (독창)
    "SCOPE_RADAR": {
        "condition": "중심 개념에서 4방향(또는 8방향)으로 영향도, 파급력, 확장 범위를 설명할 때",
        "affinity": {"center_outward": True, "directional_count": "4~8"},
        "rule": "중앙 circle + stroke line + terminal card"
    },
    # 마이크로 타이포그래피 카드
    "MICRO_CARD": {
        "condition": "여러 짧은 라벨+숫자 조합(통계, 매트릭스)을 밀도 있게 배치할 때",
        "affinity": {"datum_points": ">= 6", "label_value_pairs": True},
        "rule": "gap 16px, padding 24px, border-top: 4px solid var(--accent)"
    }
}
```

---

## 3. 빈 하단·여백 과다 방지 기법 (조건 + CSS)

### 3-1. 여백 예산 시스템 (Negative Space Budget)
총 슬라이드 높이 대비 **여백 비율 ≥ 40%** 이면 `COMPACT_MODE` 발동.

```python
FILL_ALGORITHM = {
    "measure": "last_element_bottom_to_safe_bottom",
    "阈值": {
        "excess_margin": 160,  # px
        "density_ratio": 0.35
    },
    "action_pipeline": [
        "1. gap 축소: 48px → 32px → 24px",
        "2. font-size 1단계 다운: var(--t-body) → 20px",
        "3. padding-bottom 제거: pb-0",
        "4. align-content: space-between 적용",
        "5. 여전히 여백 과다 시: FOOTER_ANCHOR 강제 삽입(소스, 날짜, 슬라이드 넘버 그룹)"
    ]
}
```

### 3-2. CSS (엔진 삽입형)
```css
.slide-frame {
  display: flex;
  flex-direction: column;
  min-height: calc(1080px - var(--safe-top) - var(--safe-bottom));
  align-content: space-between;  /* 빈 공간 하단 밀어내기 금지 */
}

/* 하단 160px 이상 남을 때 자동 발동 클래스 */
.auto-fill-bottom {
  justify-content: flex-start;
  padding-bottom: 0;
}

.auto-fill-bottom::after {
  content: attr(data-footer-inject);
  display: block;
  margin-top: auto;
  font-size: var(--t-meta);
  color: var(--text-muted);
  border-top: 1px solid var(--border-subtle);
  padding-top: 16px;
  width: 100%;
}

/* 컨텐츠 밀도 부족 시 중앙 정렬 해제, 상단 정렬 + 여백 하단 집중 */
.low-density {
  justify-content: flex-start;
  gap: calc(var(--rhythm-unit) * 2);
}
.low-density .spacer-eater {
  flex-grow: 1; /* 빈 공간을 spacer가 흡수 */
}
```

### 3-3. 레이아웃별 하단 채움 전략
| 상황 | 기법 |
|------|------|
| 텍스트 3줄 이하 + 이미지 없음 | 요소를 Visual Center(상위 30%)에 배치, 하단에 `gradient decoration band` 삽입 |
| 데이터 1개만 있음 | `MANIFESTO_LIST`로 확장(숫자+숫자+숫자) 또는 `FLOATING_ISLAND`로 주변 context 추가 |
| 좌우 분할 시 한 쪽이 비어있음 | 빈 쪽에 `watermark keyword` 또는 `light pattern` 투과 배치 |

---

## 4. 색 팔레트 시스템

### 4-1. 주제별 팔레트 (Hex dict)
엔진은 주제 키워드 1개 입력 시 해당 팔레트 자동 적용.

```python
PALETTE_SYSTEM = {
    "CORP_B2B": {
        "mode": "light",
        "60": "#0A2540",   # 딥 네이비: 주 배경/큰 면
        "30": "#00D4AA",   # 민트: 강조, 포인트
        "10": "#F6F9FC",   # 아이스 블루: 서브 배경, 카드
        "text": "#FFFFFF", # (on 60), #0A2540 (on 10)
        "note": "신뢰, 핀테크, 엔터프라이즈"
    },
    "CREATIVE_BRAND": {
        "mode": "dark",
        "60": "#1A1A2E",   # 딥 인디고: 메인 배경
        "30": "#E94560",   # 선명한 코랄: 강조
        "10": "#16213E",   # 네이비 퍼플: 카드/레이어
        "text": "#F9F9F9",
        "note": "패션, 엔터테인먼트, 스타트업 피칭"
    },
    "TECH_INNOVATION": {
        "mode": "dark",
        "60": "#0F172A",   # 슬레이트 900
        "30": "#38BDF8",   # 스카이 400
        "10": "#1E293B",   # 슬레이트 800
        "text": "#F8FAFC",
        "note": "AI, SaaS, 개발자 도구"
    },
    "SOCIAL_IMPACT": {
        "mode": "light",
        "60": "#FFFFFF",   # 흰색 면적 확보 (클린함)
        "30": "#FF6B6B",   # 웜 레드
        "10": "#FFE66D",   # 젠틀 옐로우
        "text": "#2D3436",
        "note": "비영리, 교육, ESG, 커뮤니티"
    }
}
```

### 4-2. 배합 원리
- **60%**: Background / Large shapes / Hero sections. 시선 피로를 낮추는 역할.
- **30%**: Cards / Sidebar / Key objects. 영역 구분.
- **10%**: Accent / CTA / Data highlight. 절대 면적을 크게 쓰지 않음.
- 텍스트 색상 대비비: WCAG AA 최소 4.5:1 준수. 엔진이 `#text`와 배경색의 YIQ luminance 차이를 계산해 자동 교정.

### 4-3. 다크/라이트 선택 기준
```python
def select_mode(content_profile):
    if content_profile.get("chart_count", 0) > 2 or content_profile.get("table_count", 0) > 0:
        return "light"  # 데이터 가독성 최우선
    if content_profile.get("image_dominant") and content_profile.get("image_dark_ratio", 0) > 0.5:
        return "dark"   # 어두운 이미지 위에는 dark mode + scrim
    if content_profile.get("emotive_intent") and content_profile.get("brand_palette", "").startswith("CREATIVE"):
        return "dark"
    return "light"
```

---

## 5. 안티패턴 필터 (Amateur Blocker)

엔진은 렌더링 직전 아래 필터를 통과해야 한다.

```python
ANTI_PATTERNS = {
    "typography": [
        {"id": "AP-01", "rule": "원문자(●) 리스트 마커 사용 금지", "alt": "▸ 또는 01. 또는 →"},
        {"id": "AP-02", "rule": "텍스트에 drop-shadow 금지", "alt": "배경 scrim(opacity 0.4~0.7) 사용"},
        {"id": "AP-03", "rule": "본문 양쪽정렬(justify) 금지", "alt": "text-align: left; word-break: keep-all"},
        {"id": "AP-04", "rule": "3가지 이상 font-weight 혼합 금지", "alt": "max 2 weights: 400 + 700 또는 300 + 600"},
        {"id": "AP-05", "rule": "제목만 있는 빈 슬라이드 금지", "alt": "최소 1개 시각 요소(라인, 도형, 이미지) 추가"},
    ],
    "shape": [
        {"id": "AP-10", "rule": "border-radius 4px 이하 금지(너무 날카로움)", "alt": "0px 또는 8px 또는 16px+ 만 허용"},
        {"id": "AP-11", "rule": "thin divider(1px solid) 세로 2개 이상 중복 금지", "alt": "space로 분리, 대신 24px gap"},
        {"id": "AP-12", "rule": "정사각형 아이콘을 늘려 쓰기(stretch) 금지", "alt": "object-fit: contain; aspect-ratio 강제"},
    ],
    "color": [
        {"id": "AP-20", "rule": "슬라이드 내 텍스트 색상 3색 이상 사용 금지", "alt": "그룹별로 opacity 100%/70%/40%로 depths 처리"},
        {"id": "AP-21", "rule": "배경 이미지 위 텍스트 without scrim/overlay 금지", "alt": "필수: linear-gradient overlay 또는 배경 박스"},
    ],
    "layout": [
        {"id": "AP-30", "rule": "동일 요소 3회 이상 완전 반복 금지", "alt": "3번째부터는 변형(variant) 적용"},
        {"id": "AP-31", "rule": "모든 슬라이드를 중앙 정렬만 사용 금지", "alt": "근육 있는 비대칭 비율 최소 30% 이상 포함"},
        {"id": "AP-32", "rule": "로고를 슬라이드 우측 하단에 단독 배치 금지", "alt": "로고+페이지 넘버+날짜를 그룹화해 좌측 또는 하단 중앙"},
    ]
}
```

---

## 6. 같은 레이아웃 반복 방지 규칙

### 6-1. Layout Memory Stack (엔진 상태 관리)
```python
class LayoutMemory:
    def __init__(self):
        self.stack = []        # 최근 사용 레이아웃 3개 저장
        self.cooldown = {}     # {layout_name: 슬라이드_남은간격}

    def pick(self, candidates):
        # 1. 최근 3개 중복 금지
        candidates = [c for c in candidates if c not in self.stack]
        
        # 2. 쿨다운 레이아웃 필터 (DIAGONAL_SLICE, BLEED_EDGE 등 연속 사용 불가)
        candidates = [c for c in candidates if self.cooldown.get(c, 0) <= 0]
        
        # 3. 의도 기반 강제 전환 (데이터 중첩 방지)
        if self.stack and self.stack[-1].startswith(("DATA_", "FACTORY_", "MICRO_")):
            candidates = [c for c in candidates if not c.startswith(("DATA_", "FACTORY_", "MICRO_"))]
            # 없으면 variant 변형으로 fallback
            if not candidates:
                candidates = [self.generate_variant(self.stack[-1])]
        
        selected = candidates[0]
        self.stack.append(selected)
        if len(self.stack) > 3:
            self.stack.pop(0)
        
        # 쿨다운 갱신
        self.cooldown = {k: v-1 for k, v in self.cooldown.items() if v > 0}
        if selected in ["DIAGONAL_SLICE", "BLEED_EDGE", "OVERLAP_STACK"]:
            self.cooldown[selected] = 4  # 4슬라이드 뒤에 재사용 가능
        
        return selected
```

### 6-2. Variant 강제 생성 (동일 레이아웃 3회 이상 사용 시)
```python
LAYOUT_VARIANTS = {
    "FACTORY_SPLIT": ["reverse_left_right", "vertical_stack", "text_overlay"],
    "TRELLIS_GRID": ["offset_trellis", "asymmetric_trellis_3col", "horizontal_scroll_mock"],
    "MONO_STATEMENT": ["with_mega_number", "with_background_quote", "left_anchor"],
    "STAGGERED_STAIR": ["reverse_stair", "horizontal_cascade", "radial_spread"]
}
```
- **3회째 사용 시**: 반드시 `variant` 적용 또는 axis swap(가로↔세로).
- **5회째 사용 시**: 해당 LAYOUT vocabulary를 candidates에서 2슬라이드간 **강제 배제**.

---

## 엔진 삽입 요약 (Quick Ref)

```python
# 엔진 핵심 로직 개요
def generate_slide(content):
    density = compute_density(content)
    mode = select_mode(content)
    palette = PALETTE_SYSTEM[content.theme]
    
    candidates = score_layouts(LAYOUT_VOCAB, content)
    layout = memory.pick(candidates)
    
    css = build_css(layout, palette, density)
    html = render(layout, content, css)
    
    if anti_pattern_detect(html):
        html = apply_blocker(html)
    
    return {"layout": layout, "html": html, "css": css}
```

**독창적 핵심 요약**:  
1) **Optical Alignment**로 하드웨어 중심이 아닌 시각 중심을 5% 상향, 2) **Negative Space Budget**으로 여백 과다를 수치상 차단, 3) **Diagonal Slice / Deep Layer / Floating Island**로 직사각형 피로도를 해소, 4) **Layout Memory + Cooldown**으로 인간의 다양성 시뮬레이션.