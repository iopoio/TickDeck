엔진에 바로 삽입할 수 있도록 임계값, 조건문, 마크업을 코드 기반으로 명문화한 규칙 명세입니다.

---

### 1. 콘텐츠 높이 추정 휴리스틱 (사이드카드/풋노트 트리거)
브라우저 렌더 없이 텍스트 글자 수와 요소 개수로 Body 영역(600px)의 70% 미달(420px 미만) 여부를 판정하는 공식입니다.

```python
def is_content_sparse(char_count: int, element_count: int) -> bool:
    # 상수 정의 (디자인 시스템 기준값)
    BODY_TOTAL_HEIGHT = 600
    SPARSE_THRESHOLD = BODY_TOTAL_HEIGHT * 0.7  # 420px
    
    AVG_CHAR_PER_LINE = 42  # 데스크탑 기준 (폰트 18px, 컨텐츠 폭 900px 가정)
    LINE_HEIGHT_PX = 28     # 18px * 1.5 line-height + 여백
    ELEMENT_MARGIN_PX = 24  # 리스트, 이미지 등 블록 요소 간 마진
    
    # 추정 높이 계산
    estimated_text_lines = math.ceil(char_count / AVG_CHAR_PER_LINE)
    estimated_text_height = estimated_text_lines * LINE_HEIGHT_PX
    estimated_element_height = element_count * ELEMENT_MARGIN_PX
    
    estimated_total_height = estimated_text_height + estimated_element_height
    
    # 420px 미달 시 True 반환 (사이드카드/풋노트 활성화)
    return estimated_total_height < SPARSE_THRESHOLD
```

---

### 2. 레이아웃 매칭 규칙 (30개 갤러리)
코드의 `dict` 또는 `switch/catch`로 바로 옮길 수 있는 매칭 조건입니다.

```json
{
  "single_kpi": "데이터 포인트가 1개이고, 핵심 수치 1개+부가 설명 1~2줄만 있을 때",
  "horizontal_bar_chart": "카테고리가 4~10개이고, 라벨 텍스트가 길어 가로 배치가 필요할 때",
  "vertical_bar_chart": "카테고리가 3~8개이고, 시계열(월/분기) 또는 라벨이 짧을 때",
  "two_item_compare": "비교 대상이 정확히 2개(A vs B)이고, 우열을 시각적으로 대비해야 할 때",
  "before_after": "상태 변화(전/후)를 보여주는 이미지나 명확한 2단계 데이터가 있을 때",
  "timeline": "이벤트가 3~6개이고, 시간의 흐름(순서)이 중요한 내러티브일 때",
  "process_steps": "순차적 프로세스나 워크플로우가 3~5단계로 구성되어 있을 때",
  "funnel_convergence": "데이터가 상위 단계에서 하위로 축소/수렴하는 퍼널 구조일 때",
  "quadrant": "2개의 축(X, Y) 기준으로 대상을 4분면으로 분류해야 할 때",
  "heatmap_matrix": "카테고리 x 카테고리(행렬) 교차 데이터이고, 밀도/강도를 색상으로 표현해야 할 때",
  "two_column_cards": "독립된 정보 블록이 2개이고, 각각 제목+본문+이미지 구조일 때",
  "three_cards": "독립된 정보 블록이 3개이고, 병렬적 우위(동급)일 때",
  "comparison_table": "비교 항목(열)이 3개 이상, 속성(행)이 3개 이상인 정형 데이터일 때",
  "quote_statement": "핵심 인용구 또는 강력한 선언적 문장 1~2줄이 메인 콘텐츠일 때",
  "logo_grid": "이미지/로고/아이콘만으로 구성된 동급의 요소가 6~12개일 때",
  "mirror_bar": "양측을 비교하는 데이터(예: 성비, 찬반)이고 중앙 기준 좌우로 뻗어야 할 때",
  "dumbbell_plot": "2개 시점 또는 2개 그룹 간의 격차(Gap) 변화가 핵심일 때",
  "donut_chart": "전체 대비 비율(%) 데이터가 3~6개이고, 중앙에 총합 수치를 노출해야 할 때",
  "bullet_chart": "목표값(Goal)과 실적값 Actual)을 동일 축에서 비교해야 할 때",
  "stacked_bar": "각 카테고리의 총합과 내부 세부 항목 비율을 동시에 봐야 할 때",
  "pyramid": "계층 구조(조직도, 마스로우 등)이거나 하단이 넓고 상단이 좁은 데이터일 때",
  "stat_with_sparkline": "현재 핵심 수치 1개와 그 수치의 과거 추세선(시계열)을 함께 봐야 할 때",
  "agenda": "목차나 발표 순서가 3~5개로 구성된 개요 슬라이드일 때",
  "team_grid": "인물 사진과 이름/직책 정보가 3~6명 분량일 때",
  "treemap": "계층형 데이터이며, 크기(Size)와 비율을 면적으로 직관적으로 봐야 할 때",
  "section_divider_large": "새로운 챕터 시작 시 전환 효과가 필요하고 텍스트가 짧을 때 (타이포 중심)",
  "section_divider_kpi": "새로운 챕터 시작과 동시에 상기시킬 핵심 KPI 1개가 있을 때",
  "section_divider_quote": "챕터 전환 시 철학/방향성을 암시하는 문구가 있을 때",
  "cover": "슬라이드의 첫 페이지이고 메인 타이틀, 서브타이틀, 발표자 정보가 있을 때",
  "closing": "슬라이드의 마지막이며 요약, Q&A, 연락처 정보를 포함할 때"
}
```

---

### 3. 순수 CSS/SVG 차트 재현 마크업 패턴

#### 1) 막대 (Bar)
```html
<div style="display:flex; align-items:flex-end; gap:12px; height:200px;">
  <div style="width:40px; height:80%; background:var(--accent);"></div>
  <div style="width:40px; height:50%; background:var(--neutral);"></div>
</div>
```

#### 2) 도넛 (Donut)
```html
<svg width="120" height="120" viewBox="0 0 36 36">
  <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--neutral-light)" stroke-width="4"/>
  <!-- 75% 채우기: stroke-dasharray="전체비율 남은비율", stroke-dashoffset="25" -->
  <circle cx="18" cy="18" r="15.9" fill="none" stroke="var(--accent)" stroke-width="4" 
          stroke-dasharray="75 25" stroke-dashoffset="25" transform="rotate(-90 18 18)"/>
</svg>
```

#### 3) 덤벨 (Dumbbell)
```html
<svg width="200" height="40">
  <line x1="20" y1="20" x2="150" y2="20" stroke="var(--neutral)" stroke-width="2"/>
  <circle cx="20" cy="20" r="6" fill="var(--neutral-dark)"/>
  <circle cx="150" cy="20" r="6" fill="var(--accent)"/>
</svg>
```

#### 4) Sparkline
```html
<svg width="100" height="30" viewBox="0 0 100 30">
  <polyline points="0,20 20,15 40,18 60,5 80,10 100,2" 
            fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round"/>
</svg>
```

#### 5) Bullet Chart
```html
<div style="width:200px; height:24px; background:var(--neutral-light); border-radius:12px; position:relative;">
  <!-- 목표선 -->
  <div style="position:absolute; left:70%; width:2px; height:100%; background:var(--danger);"></div>
  <!-- 실적 바 -->
  <div style="position:absolute; left:0; width:60%; height:40%; top:30%; background:var(--accent); border-radius:4px;"></div>
</div>
```

#### 6) Treemap
```html
<div style="display:grid; grid-template-columns:2fr 1fr; grid-template-rows:2fr 1fr; gap:4px; width:300px; height:200px;">
  <div style="background:var(--accent); grid-column:1; grid-row:1 / span 2;"></div>
  <div style="background:var(--accent-light);"></div>
  <div style="background:var(--neutral);"></div>
</div>
```

---

### 4. 보조 통계/사이드 인사이트 텍스트 추출 규칙

원본 텍스트에서 파생 데이터를 생성하는 NLP/추출 규칙입니다.

```python
def extract_aux_stats(raw_text: str, layout_type: str):
    extracted = []
    
    # 1. 정규표현식 기반 수치 추출 (숫자 + 단위/증감률)
    # 예: "매출 50억", "전년대비 12% 증가", "목표 달성률 85%"
    pattern = r'([가-힣a-zA-Z\s]{2,10})\s*(\d{1,3}(?:,\d{3})*|\d+\.\d+)\s*(%|억|만|조|원|명|개|건)?'
    matches = re.findall(pattern, raw_text)
    
    for match in matches[:4]: # 최대 4개만
        extracted.append({
            "label": match[0].strip(),
            "value": match[1] + (match[2] if match[2] else "")
        })
        
    return extracted

def extract_side_insight(raw_text: str):
    # 사이드 인사이트는 '결론/시사점' 문장 우선 추출
    keywords = ["따라서", "결과적으로", "주목할 점은", "핵심은", "특히", "즉"]
    sentences = raw_text.split('.')
    
    for sentence in sentences:
        for keyword in keywords:
            if keyword in sentence:
                return sentence.strip() + "."
                
    # 키워드가 없으면 가장 마지막 문장(결론) 반환
    return sentences[-2].strip() + "." if len(sentences) > 1 else raw_text
```

---

### 5. 제목 액센트 및 한국어 줄바꿈 규칙

#### 액센트(`--accent`) 부여 규칙
```python
def apply_title_accent(title: str) -> str:
    # 어절 단위 분리
    words = title.split()
    
    # 조사/어미 제외 배열
    particles = ['은', '는', '이', '가', '을', '를', '의', '에', '와', '과']
    
    # 후보 찾기: 숫자/단위가 포함된 어절 > 마지막 2음절 이상 명사
    target_word = None
    for word in reversed(words):
        # 숫자 포함 시 최우선
        if re.search(r'\d', word):
            target_word = word
            break
        # 조사로 끝나지 않는 2음절 이상 어절
        clean_word = re.sub(r'[.,!?:]', '', word)
        if len(clean_word) >= 2 and not any(clean_word.endswith(p) for p in particles):
            target_word = word
            break
            
    if target_word:
        return title.replace(target_word, f'<span class="accent">{target_word}</span>')
    return title
```

#### 한국어 줄바꿈 CSS (깨짐 방지)
```css
.title {
  word-break: keep-all; /* 어절 중간 단어 끊김 방지 */
  overflow-wrap: break-word; /* 긴 영문/URL 방지용 안전장치 */
  line-height: 1.3;
  letter-spacing: -0.02em; /* 한국어 가독성 위한 자간 축소 */
}
```

---

### 6. 주제 → 팔레트 매칭 및 다크/라이트 기준

#### 팔레트 매칭 규칙 (Python Dict)
```python
PALETTE_MAPPING = {
    "finance": { # 재무, 경영, 금융
        "bg": "#FFFFFF", "surface": "#F4F6F8", "text": "#1A1A1A",
        "accent": "#003566", "accent_secondary": "#FFD60A", "danger": "#D62828",
        "mode": "light"
    },
    "tech": { # 기술, IT, SaaS, 엔지니어링
        "bg": "#0D1117", "surface": "#161B22", "text": "#E6EDF3",
        "accent": "#58A6FF", "accent_secondary": "#3FB950", "danger": "#F85149",
        "mode": "dark"
    },
    "eco": { # 친환경, ESG, 자연, 헬스케어
        "bg": "#F8F9F4", "surface": "#E9ECE0", "text": "#1B1B1B",
        "accent": "#2D6A4F", "accent_secondary": "#D4A373", "danger": "#BC4749",
        "mode": "light"
    },
    "creative": { # 마케팅, 디자인, 미디어, 아트
        "bg": "#121212", "surface": "#1E1E1E", "text": "#FFFFFF",
        "accent": "#FF3366", "accent_secondary": "#FFD23F", "danger": "#FF6B6B",
        "mode": "dark"
    }
}

def select_palette(topic: str, data_density: str) -> dict:
    palette = PALETTE_MAPPING.get(topic, PALETTE_MAPPING["finance"])
    
    # 다크/라이트 오버라이드 조건
    # 데이터 밀도가 높고(표/차트 다수) 시인성 확보가 필요하면 무조건 다크 모드 강제
    if data_density == "high":
        if topic in ["finance", "eco"]: 
            pass # 재무/에코는 데이터가 많아도 라이트가 가독성 좋음
        else:
            palette["mode"] = "dark" # 테크/크리에이티브는 데이터가 많으면 다크 고정
            
    return palette
```

#### 60-30-10 적용 원칙 (엔진 CSS 변수 매핑)
*   **60% (Background / Base):** `bg`, `surface` 색상 사용. 대면적 여백.
*   **30% (Text / Secondary Elements):** `text` 컬러, `surface`보다 1톤 어두운 중간 요소(선, 보조 텍스트, 보조 차트).
*   **10% (Accent / Call to Action):** `accent`와 `accent_secondary` 색상. 핵심 KPI 수치, 제목의 특정 단어, 차트의 가장 중요한 데이터 시리즈(Primary series)에만 제한적으로 적용.