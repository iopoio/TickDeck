시니어 리서치 애널리스트이자 데이터 파이프라인 엔지니어의 관점에서, **"인간의 개입을 최소화하면서(Human-out-of-the-loop) 연구의 엄밀성을 유지하는 AI 자동화 파이프라인(TRAP: Trend Research Automated Pipeline)"** 아키텍처를 설계해 드립니다.

단순한 프롬프트 엔지니어링을 넘어, **LangChain/LangGraph, Pydantic, 벡터 DB, 그래프 DB**를 활용한 실제 프로덕션 레벨의 코드 로직과 스키마로 번역했습니다.

---

### 1. 자동 디깅 에이전트: 소스 티어링 및 원문 추적 (Ingestion Layer)
AI 에이전트가 웹 서핑(OSINT)을 할 때, 단순 텍스트가 아닌 **강제 구조화 스키마(Pydantic)** 를 반환하게 하여 환각과 좀비 수치를 파이프라인 진입 단계에서 차단합니다.

**🛠️ 에이전트 시스템 프롬프트 및 Pydantic 스키마**
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class SourceMeta(BaseModel):
    url: str = Field(description="원문 URL (PDF/DOI 우선)")
    publisher: str = Field(description="발행 기관")
    tier: Literal["T1_Gov_Acad", "T2_Global_Consulting", "T3_Media_Industry", "T4_Blog_Unknown"]
    publish_year: int = Field(description="발행 연도 (없으면 0)")
    sample_size: Optional[int] = Field(default=None, description="표본 수 (N)")
    region: List[str] = Field(description="조사 대상 지역")
    conflict_of_interest: bool = Field(description="이해관계 충돌 여부 (예:自社 조사)")
    
class DataPointRaw(BaseModel):
    claim: str = Field(description="수치 기반 핵심 주장")
    metric_value: float
    metric_unit: str
    source_meta: SourceMeta
    paywall_flag: bool = Field(description="본문 없이 제목/요약만 있는 페이월 의심")
    zombie_flag: bool = Field(description="3년 이상 된 데이터를 최신인 것처럼 인용했는가")
    circular_citation: bool = Field(description="다른 언론/블로그의 재인용(Source Laundering) 의심")
```

**🚨 자동 FLAG 로직 (파이프라인 게이트웨이)**
*   **Zombie Flag:** `current_year - publish_year > 3` 이고 IT/트렌드 도메인일 경우 자동 `True`.
*   **Source Laundering (출처 세탁) 탐지:** URL 도메인이 언론사(.com/news)인데 원본 데이터 링크(PDF, .gov, .org)가 본문에 없을 경우 `circular_citation = True`로 마킹.
*   **페이월 우회 검증:** Selenium/Playwright로 DOM 파싱 시 `<article>` 태그 내 텍스트 길이가 500자 미만이고 `subscription` 관련 클래스가 감지되면 `paywall_flag = True`.

---

### 2. CED/CEMS 슬라이드 엔진용 JSON 스키마 (Storage & Rendering Layer)
슬라이드 HTML 자동 생성 엔진(예: Reveal.js, Marp)이 소비할 데이터 구조입니다. 수치가 비거나 신뢰도가 낮으면 **엔진이 자동으로 시각화 컴포넌트를 강등**시킵니다.

**📦 슬라이드 블록 JSON 스키마**
```json
{
  "slide_id": "s_04_market_tension",
  "layout_type": "dynamic", 
  "blocks": [
    {
      "component": "HeroMetric", 
      "fallback_component": "QualitativeQuote",
      "data": {
        "value": 73.4,
        "unit": "%",
        "context": "Z세대의 AI 도구 유료 전환율",
        "source": {"publisher": "McKinsey", "year": 2023, "tier": "T2"},
        "limitation": "북미 지역 표본(N=1,200)에 국한됨",
        "confidence_score": 0.92
      }
    }
  ]
}
```

**⚙️ 코드 로직: 자동 강등 (降级) 및 삭제 엔진**
```python
def render_component(block):
    data = block['data']
    
    # 1. 데이터가 없거나 환각 위험이 높음
    if not data.get('value') or data['confidence_score'] < 0.6:
        return None # 슬라이드에서 블록 자체를 삭제 (Delete)
        
    # 2. 신뢰도는 높으나 표본/지역 한계가 명확함 (정성격하로 강등)
    if data['confidence_score'] < 0.8 or data['source']['tier'] not in ["T1", "T2"]:
        block['component'] = block['fallback_component'] # HeroMetric -> QualitativeQuote
        return generate_text_quote(block)
        
    # 3. 메인 근거로 렌더링
    return generate_big_number_chart(block)
```

---

### 3. 검증 자동화: Multi-Agent Self-Check (QA Layer)
사람이 일일이 교차 확인하는 것을 **LangGraph의 다중 에이전트 토론(Debate) 구조**로 대체합니다.

| 검증 항목 | 자동화 방법 (AI 파이프라인) | 사람 개입 필요 (HITL) |
| :--- | :--- | :--- |
| **수치 환각/오타** | **Math-Verifier Agent:** LLM이 추출한 수치와 원문 PDF/HTML 테이블 수치를 코드(Python AST)로 대조. | 원문 PDF가 스캔본(이미지)이라 OCR 오류가 발생한 경우 |
| **좀비 수치** | **Time-Travel Search:** "해당 주제 + {현재연도} + report"로 역검색하여 최신 데이터가 존재하면 구버전 FLAG. | 산업의 구조적 변화로 과거 데이터가 오히려 유의미한 경우 |
| **출처 세탁** | **Graph DB (Neo4j) 순환 인용 탐지:** A가 B를, B가 C를 인용하는 체인에서 C(근원)가 존재하지 않으면 경고. | - |
| **반대 증거** | **Devil's Advocate Agent:** "이 주장에 반박하는 {도메인}의 데이터나 논리를 찾아라" 역검색 강제. | 상반된 데이터 중 어떤 것을 '메인 스트림'으로 볼지 판단 |

**🔄 역검색(Counter-Evidence) 프롬프트 템플릿**
> "You are a skeptical peer-reviewer. Given the claim: '{claim}', use web search to find at least ONE credible source (T1/T2) published within the last 2 years that CONTRADICTS or shows a different trend. Return JSON with `contradiction_found` (bool) and `counter_evidence`."

---

### 4. 약한 데이터 자동 분류 임계값 (Scoring & Routing)
풀(Pool)에 쌓인 수치를 슬라이드의 위계(Hierarchy)에 맞게 자동 배분하는 **가중치 점수화 알고리즘**입니다.

**🧮 Data Weight Score (DWS) 공식**
`DWS = (Tier_Score * 0.4) + (Recency_Score * 0.3) + (Sample_Score * 0.2) + (Methodology_Score * 0.1)`

*   **Tier (0~10점):** T1(10), T2(8), T3(5), T4(0)
*   **Recency (0~10점):** 1년 이내(10), 2년(7), 3년(4), 4년+(0)
*   **Sample (0~10점):** N>1000(10), N>300(7), N<100(4), 정성/미상(2)
*   **Methodology (0~10점):** 무작위 추출/패널(10), 자사 DB(6), 온라인 설문(4)

**🗂️ 자동 라우팅 임계값 (Thresholds)**
```python
def route_data(dws_score, data_type):
    if dws_score >= 8.0 and data_type == 'quantitative':
        return "MAIN_EVIDENCE" # 슬라이드 메인 타이틀 및 Big Number
        
    elif 5.0 <= dws_score < 8.0:
        return "QUALITATIVE_SUPPORT" # 본문 불릿 포인트 또는 참고 박스
        
    elif dws_score < 5.0 and is_directionally_consistent(data):
        return "DIRECTIONAL_SIGNAL" # 구체적인 수치 숨김, "증가세/하락세" 화살표 아이콘만 노출
        
    else:
        return "TRASH" # 파이프라인에서 영구 삭제 (슬레이트에 반영 안 함)
```

---

### 5. Pool → Story → Chapter 자동 매핑 (Synthesis Layer)
자료 풀에서 인사이트를 뽑아 `Tension → Action` 프레임에 자동 배치하는 **클러스터링 및 서사 생성 알고리즘**입니다.

**알고리즘 워크플로우:**
1.  **임베딩 및 클러스터링 (DBSCAN):** Pool의 모든 `claim`과 `data`를 벡터화하여 의미론적 클러스터로 묶습니다.
2.  **Tension(긴장감) 자동 탐지:** 
    *   *규칙:* 서로 다른 클러스터의 벡터 거리가 가깝지만(같은 주제), **수치의 방향성(증감)이 상충**되거나 **기대치 vs 현실의 괴리**가 발견되는 노드를 `Tension_Point`로 마킹.
    *   *예시:* 클러스터 A(시장 규모 급성장) vs 클러스터 B(실제 기업 도입률/ROI 정체) $\rightarrow$ **"The Adoption Paradox"**
3.  **서사 매핑 (LLM Director Agent):**

**🎬 스토리보드 자동 생성 프롬프트 (Mapping to Framework)**
```text
[Input]
- Tension Points: {list_of_contradictions}
- Data Clusters: {list_of_themes}

[Task]
You are a Master Strategist. Map the inputs into a 4-chapter slide narrative.
Chapter 1: The Hook (Tension/Paradox derived from data contradictions)
Chapter 2: The Root Cause (Why the tension exists, backed by Tier 1/2 Data)
Chapter 3: The Shift (Directional signals showing where the market is moving)
Chapter 4: The Action (Strategic imperatives for the target audience)

[Output Format]
JSON array of chapters, each containing `title`, `core_message`, `required_data_ids` (from the pool).
```

---

### 💡 [Bonus] 시니어 엔지니어의 히든 기법: Data Decay & Provenance Graph

트렌드 리포트 파이프라인에서 가장 간과하기 쉬운 것이 **"데이터의 반감기(Data Half-life)"** 입니다. 
AI 도메인의 2022년 데이터와 인구통계학의 2022년 데이터는 완전히 다른 무게를 가집니다.

**🚀 Provenance Graph & TTL (Time-To-Live) 설정**
*   **도메인별 Decay Rate 적용:** 
    *   AI/테크: `decay_rate = 0.5` (6개월마다 신뢰도 점수 절반 차감)
    *   소비트렌드: `decay_rate = 0.2`
    *   거시경제/인구: `decay_rate = 0.05`
*   **파이프라인 적용:** 디깅 에이전트가 데이터를 가져올 때 `Domain`을 태깅하고, 슬라이드 엔진이 데이터를 Pulling할 때 `(현재일 - 발행일) * decay_rate`를 계산하여 `confidence_score`에서 자동 감점합니다.
*   **효과:** 사람이 "이거 2년 전 데이터인데 최신인 척 들어가 있네?" 하고 지적할 일을 코드 레벨에서 원천 차단합니다.

---

### 🎯 요약: 인간과 AI의 역할 분리 (HITL Boundary)

이 파이프라인이 도입되면 여러분의 팀은 다음과 같이 일하게 됩니다.

*   **AI가 100% 자동화하는 것:** 웹 크롤링, 출처 티어링, 페이월/좀비/세탁 필터링, 수치 교차 검증, 데이터 위계 분류, 슬라이드 HTML/JSON 렌더링.
*   **인간(애널리스트)만 하는 것:** 
    1. AI가 찾아온 `Tension Point` 중 **어떤 것이 클라이언트/독자에게 진짜 전략적 울림(Strategic Resonance)을 줄지 '타겟팅'**
    2. `Limitation(한계점)`을 슬라이드 하단에 얼마나 우아하게 배치하여 **신뢰도를 방어할지 '프레이밍'**
    3. 최종 스토리의 **Tone & Manner(어조) 튜닝**

이 아키텍처를LangGraph로 구현하시면, 매주 수백 페이지의 리포트를 생산하면서도 "출처 세탁"이나 "좀비 수치"로 인한 크레디블리티 리스크를 제로화할 수 있습니다. 코드 구현 시 특정 모듈(LangGraph 노드 등)의 상세 로직이 필요하시면 말씀해 주십시오.