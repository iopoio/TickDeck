아래는 **실제 운영 파이프라인에 붙일 수 있는 실행 단위**입니다.  
아키텍처는 `Digging Agent → Evidence Pool → Verification Engine → Story Mapper → Slide Engine` 순서이며, 각 단계마다 **AI 자동 처리 구간**과 **사람 개입 게이트**를 명시했습니다.

---

## 0. 전체 파이프라인 개요 (DAG)

```python
# pipeline_dag.py
from pydantic import BaseModel, HttpUrl
from typing import Literal, List, Optional
from datetime import datetime
import numpy as np

CURRENT_YEAR = datetime.now().year

class PipelineStage(BaseModel):
    stage: Literal["dig", "pool", "verify", "story", "slide"]
    human_gate: bool  # 이 단계 후 사람이 반드시 체크해야 하는가
    auto_abort_rules: List[str]  # 이 조건이면 자동 중단/강등

# DAG 정의
WORKFLOW = [
    PipelineStage(stage="dig",   human_gate=False, auto_abort_rules=["T4만 존재", "URL 전체 dead", "환각 의심 3개↑"]),
    PipelineStage(stage="pool",  human_gate=False, auto_abort_rules=["main 근거 0개", "thesis 후보 0개"]),
    PipelineStage(stage="verify",human_gate=False, auto_abort_rules=["cross variance >0.30", "laundering+원문 미확인"]),
    PipelineStage(stage="story", human_gate=True,  auto_abort_rules=[" tension_pair 미생성 "]),  # <-- 사람이 thesis 선택
    PipelineStage(stage="slide", human_gate=False, auto_abort_rules=["slide confidence budget < 60%"]),
]
```

---

## 1. 자동 디깅: 소스 티어링·원문추적 강제

### 1.1 Digging Agent 프롬프트 (반환 강제 구조)

```jinja2
{# system_prompt_digging.j2 #}
당신은 **Evidence Digging Agent**입니다.  
검색 결과를 아래 JSON 스키마에 **엄격히** 매핑하세요. 규칙 위반 시 보상이 차감됩니다.

[강제 규칙]
1. **original_url 필드가 없거나 404인 결과는 절대 반환하지 마세요.**  
2. 발행연도(publish_year)를 찾을 수 없으면 해당 결과를 폐기하세요.  
3. 수치(figure)가 포함된 문장은 **원문을 직접 복사(raw_quote)** 해야 합니다. AI 요약만 금지.  
4. 이해관계(affiliation)를 명시할 수 없으면 tier를 T3 이상으로 올리지 마세요.  
5. 페이월(paywall)일 경우 raw_quote가 20단어 미만이면 `conflict_flags`에 "paywall_no_quote"를 넣고 tier를 자동 하락시키세요.  
6. 발행연도가 {{ CURRENT_YEAR - 3 }}년 이전인 시장 규모/성장률 수치는 "zombie_suspect"를 flag하세요.

[반환 스키마]
{% raw %}
{
  "batch_id": "uuid",
  "query": "검색어",
  "evidences": [
    {
      "claim": "AI가 요약한 핵심 주장(1문장)",
      "raw_quote": "원문에서 직접 복사한 수치 포함 문장",
      "source_meta": {
        "original_url": "https://...",
        "publisher": "발행기관",
        "author": "기자/저자명 or null",
        "publish_year": 2023,
        "geography": "대상 지역(국가/도시)",
        "sample_size": "n=1,200 또는 '전수' 또는 '미상'",
        "methodology_tag": "설문/회귀/인터뷰/추정/미상"
      },
      "tier": "T1|T2|T3|T4",
      "affiliation": "기관명 or '독립' or '미상'",
      "numerical_values": [
        {"figure": "34%", "unit": "%", "context": "2023년 국내 AI 시장 점유율"}
      ],
      "paywall_status": "open|abstract_only|paywall",
      "conflict_flags": ["zombie_suspect", "paywall_no_quote", "sponsored"]
    }
  ]
}
{% endraw %}
```

### 1.2 출력 스키마 (Pydantic)

```python
# schemas_digging.py
from pydantic import BaseModel, HttpUrl, Field, validator
from typing import Literal, List, Optional
from datetime import datetime

class SourceTier(str, Enum):
    T1_GOV_ACADEMIC_AUDITED = "T1"   # 정부통계, KOSIS, 학술지(PubMed/SSCI), 상장사 10-K
    T2_ESTABLISHED_MEDIA = "T2"      # Reuters, Bloomberg, WSJ, 중앙/동아(기자명 명시)
    T3_INDUSTRY_PR = "T3"            # 컨설팅(무료보고서), 협회, 보도자료, think-tank
    T4_UNVERIFIED = "T4"             # 블로그, 커뮤니티, 익명, press release only

class NumericalValue(BaseModel):
    figure: str  # "34%", "12.3조", "1.2x"
    unit: str
    context: str

class SourceMeta(BaseModel):
    original_url: HttpUrl
    publisher: str = Field(..., min_length=2)
    author: Optional[str] = None
    publish_year: int = Field(..., le=CURRENT_YEAR, ge=1990)
    geography: Optional[str] = None
    sample_size: Optional[str] = None
    methodology_tag: Optional[str] = None

    @validator('original_url')
    def must_be_reachable(cls, v):
        # 파이프라인 내에서 HEAD 요청으로 사전 체크
        return v

class RawEvidence(BaseModel):
    claim: str = Field(..., min_length=10)
    raw_quote: str = Field(..., min_length=20)  # 환각 방지용 원문 앵커
    source_meta: SourceMeta
    tier: SourceTier
    affiliation: Optional[str] = "미상"
    numerical_values: List[NumericalValue] = []
    paywall_status: Literal["open", "abstract_only", "paywall"]
    conflict_flags: List[str] = []

    # 자동 거름망 필드
    auto_drop_reason: Optional[str] = None  # 내부 전용
```

### 1.3 페이월·환각·좀비 자동 거름망 코드

```python
# filter_digging.py
import requests
from datetime import datetime

class DiggingFilter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "EvidenceBot/1.0"})

    def check_url_alive(self, url: str) -> bool:
        try:
            r = self.session.head(str(url), allow_redirects=True, timeout=5)
            return r.status_code == 200
        except Exception:
            return False

    def auto_filter(self, ev: RawEvidence) -> Optional[RawEvidence]:
        # 1. URL dead → 즉시 삭제
        if not self.check_url_alive(str(ev.source_meta.original_url)):
            ev.auto_drop_reason = "URL_DEAD"
            return None

        # 2. 원문 인용 너무 짧음 → 환각 의심 → 삭제
        if len(ev.raw_quote) < 20:
            ev.auto_drop_reason = "HALLUCINATION_SUSPECT_SHORT_QUOTE"
            return None

        # 3. 페이월 + 인용 없음 → T3 강등 or 삭제
        if ev.paywall_status == "paywall" and len(ev.raw_quote) < 40:
            ev.conflict_flags.append("paywall_no_quote")
            if ev.tier in [SourceTier.T1, SourceTier.T2]:
                ev.tier = SourceTier.T3  # 강등

        # 4. 좀비수치(시장 규모/성장률 중 3년 이상) 플래그
        if ev.source_meta.publish_year <= CURRENT_YEAR - 3:
            if any(k in ev.claim for k in ["시장", "규모", "성장률", "CAGR", "점유율"]):
                ev.conflict_flags.append("zombie_suspect")

        # 5. T4는 풀에 누적하지 않음 (단, 반대증거 수집용 별도 버킷 예외 가능)
        if ev.tier == SourceTier.T4:
            ev.auto_drop_reason = "T4_BLOCKED"
            return None

        return ev
```

---

## 2. CED/CEMS: 슬라이드 엔진이 먹는 데이터 구조

### 2.1 JSON 스키마 (Pydantic)

```python
# schemas_slide.py
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List
from schemas_digging import SourceTier, HttpUrl

class CEMSMeta(BaseModel):
    """Context-ErrorMargin-Limitation-Source"""
    context: str = Field(..., description="수치의 맥락: 'B2B 기업 대상'")
    error_margin: Optional[str] = None       # "±3.2%", "95% CI[12.1, 14.5]"
    limitation: str = Field(..., description="방법론적 한계/편향")
    source_tier: SourceTier
    source_url: HttpUrl
    publish_year: int
    cross_verified: bool = False
    zombie_flag: bool = False
    laundering_risk: Literal["low", "high"] = "low"

class DataPoint(BaseModel):
    value: Optional[float | str] = None
    unit: str
    geo: Optional[str] = None
    sample: Optional[str] = None
    year: int
    cems: CEMSMeta
    # 파이프라인 내부 상태
    status: Literal["main", "demoted_qualitative", "demoted_directional", "deleted"] = "main"
    slide_eligible: bool = True
    human_review_flag: bool = False

class CEDBlock(BaseModel):
    """Claim-Evidence-Data: 슬라이드 1개 단위"""
    block_id: str
    claim: str  # 슬라이드에 들어갈 서술 문장
    data_points: List[DataPoint]
    narrative_role: Literal["setup", "tension", "action", "resolution"] = "setup"
```

### 2.2 수치 비면 자동 강등/삭제 로직

```python
# slide_qualify.py
def auto_demote_or_delete(dp: DataPoint) -> DataPoint:
    # 1. 값 자체가 없음 → 삭제
    if dp.value is None or dp.value == "":
        dp.status = "deleted"
        dp.slide_eligible = False
        return dp

    # 2. Temporal Decay + Tier 조합
    age = CURRENT_YEAR - dp.cems.publish_year
    if age >= 5:
        dp.status = "deleted"
    elif age >= 3 and dp.cems.zombie_flag:
        dp.status = "demoted_directional"
        dp.slide_eligible = False  # 본문 수치 불가, 각주/appendix만
    elif age >= 3 and not dp.cems.cross_verified:
        dp.status = "demoted_directional"
    elif dp.cems.source_tier == SourceTier.T3 and not dp.cems.cross_verified:
        dp.status = "demoted_qualitative"  # "일부 조사에서~" 와 같은 정성 표현으로 격하
    elif dp.cems.laundering_risk == "high" and not dp.cems.cross_verified:
        dp.status = "deleted"
    elif dp.cems.source_tier == SourceTier.T4:
        dp.status = "deleted"

    # 최종 슬라이드 배치 가능 여부
    dp.slide_eligible = dp.status in ["main", "demoted_qualitative"]
    
    # 방향신호는 사람 확인 게이트
    if dp.status == "demoted_directional":
        dp.human_review_flag = True

    return dp

# CEDBlock 전체에 적용
def qualify_block(block: CEDBlock) -> CEDBlock:
    block.data_points = [auto_demote_or_delete(dp) for dp in block.data_points]
    # 메인 근거가 하나도 없으면 블록 자체를 HOLD
    mains = [dp for dp in block.data_points if dp.status == "main"]
    if len(mains) == 0:
        block.narrative_role = "HOLD_FOR_REVIEW"
    return block
```

---

## 3. 검증 자동화: AI가 스스로 교차확인·좀비사냥·역검색

### 3.1 Self-Check 모듈

```python
# verification_engine.py
from statistics import stdev, mean
from typing import List

class VerificationEngine:
    def __init__(self, search_tool):  # Serper/Google/Brave API wrapper
        self.search = search_tool

    # ── A. 교차확인 (자동) ──
    def cross_verify(self, target_claim: str, evidences: List[RawEvidence]) -> dict:
        figures = []
        for ev in evidences:
            for nv in ev.numerical_values:
                # 숫자 파싱 (간단 버전)
                try:
                    f = float(nv.figure.replace("%","").replace("조",""))
                    figures.append(f)
                except:
                    continue
        
        if len(figures) < 2:
            return {"cross_verified": False, "variance_cv": None, "reason": "단일출처"}
        
        cv = stdev(figures) / mean(figures) if mean(figures) != 0 else 0
        return {
            "cross_verified": cv < 0.15,  # 15% 이내 변동계수
            "variance_cv": round(cv, 3),
            "figures": figures
        }

    # ── B. 좀비수치 사냥 (자동) ──
    def zombie_hunt(self, ev: RawEvidence) -> bool:
        if "zombie_suspect" not in ev.conflict_flags:
            return False
        # 최근 1년간 해당 수치가 "인용" 형태로 얼마나 반복되는지 검색
        query = f'"{ev.raw_quote[:30]}" market size cited reported 2024'
        results = self.search(query, num=5)
        # 원문을 재확인하지 않고 반복 인용된 경우 좀비 확정
        re_citations = [r for r in results if ev.source_meta.publish_year <= CURRENT_YEAR - 3]
        is_zombie = len(re_citations) >= 2
        return is_zombie

    # ── C. 출처세탁 탐지 (자동 플래그 + 사람 판단) ──
    def laundering_check(self, ev: RawEvidence) -> RawEvidence:
        publisher = ev.source_meta.publisher.lower()
        # 원문 URL의 도메인과 publisher 불일치 체크
        domain = str(ev.source_meta.original_url).split("/")[2].replace("www.","")
        # 간단히: 보도기사가 "통계청" 수치를 인용했지만 원문은 뉴스 도메인 → laundering 의심
        if "kosis" in publisher and "kostat" not in domain:
            ev.conflict_flags.append("laundering_suspect")
            # 원문이 KOSIS 직링크가 아니면 high
            # (파이프라인 내에서 KOSIS API로 재확인 시도)
        return ev

    # ── D. 반대증거 역검색 (자동 수집 + 사람 최종 판단) ──
    def counter_evidence_search(self, claim: str) -> dict:
        negatives = ["반박", "오히려 감소", "criticism", "contradict", "declining", "not true", "오류"]
        counters = []
        for neg in negatives:
            results = self.search(f"{claim} {neg}", num=3)
            counters.extend(results)
        
        return {
            "counter_exists": len(counters) > 0,
            "counter_samples": [r["title"] for r in counters[:3]],
            "human_review_required": len(counters) > 0  # 반대증거 있으면 사람이 반드시 봐야 함
        }
```

### 3.2 자동 vs 사람 구분표

| 검증 항목 | 자동 처리 | 사람 개입 (게이트) |
|---|---|---|
| **URL alive / paywall 탐지** | HEAD 요청, raw_quote 길이 체크 | 없음 |
| **수치 교차확인 편차** | CV 계산, 15% 임계값 통과/탈락 | 경계값(10~20%) 모호 케이스 |
| **좀비수치 탐지** | 발행연도 + 반복인용 패턴 매칭 | 원문이 날짜미상 보고서일 때 확인 |
| **출처세탁 탐지** | publisher-domain 불일치 플래그 | **원문 vs 인용처 직접 비교** (세탁 확정은 사람) |
| **반대증거 존재** | 부정어 키워드 다중 검색 | **반대증거의 서사적 중요도** 판단 (삭제할지, tension에 쓸지) |
| **방법론 오류** | methodology_tag 누락 시 플래그 | 회귀분석 설계미흡, 표본 편bias 심층 판단 |
| **이해관계 심층 분석** | affiliation 키워드 매칭 | 복수 기관 간 상충 이해관계 가중치 조정 |

---

## 4. 풀 → 스토리 → 챕터 자동 매핑

### 4.1 알고리즘 개요

```python
# story_mapper.py
from sentence_transformers import SentenceTransformer
from sklearn.cluster import HDBSCAN
from keybert import KeyBERT
import numpy as np
from scipy.spatial.distance import cosine

class StoryMapper:
    def __init__(self, pool: List[RawEvidence]):
        self.pool = pool
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.kw_model = KeyBERT(self.embedder)

    def vectorize_pool(self):
        texts = [f"{ev.claim} {ev.source_meta.geography or ''}" for ev in self.pool]
        self.embeddings = self.embedder.encode(texts, show_progress_bar=True)

    def cluster_evidence(self, min_cluster_size=3):
        self.vectorize_pool()
        clusterer = HDBSCAN(min_cluster_size=min_cluster_size, metric='cosine')
        labels = clusterer.fit_predict(self.embeddings)
        self.clusters = {}
        for idx, label in enumerate(labels):
            if label == -1:  # 노이즈는 단일 클러스터로
                label = f"noise_{idx}"
            self.clusters.setdefault(label, []).append(self.pool[idx])
        return self.clusters

    def extract_tension_axes(self) -> List[dict]:
        # 클러스터별 키워드 & 임베딩 중심 추출
        axes = []
        for cid, evs in self.clusters.items():
            emb = self.embedder.encode([e.claim for e in evs])
            centroid = np.mean(emb, axis=0)
            keywords = self.kw_model.extract_keywords(
                " ".join([e.claim for e in evs]), 
                keyphrase_ngram_range=(1,2), stop_words='english', top_n=5
            )
            # 감정 극성 (간단: 긍정/부정 키워드 카운트)
            pos = sum(1 for e in evs if any(p in e.claim for p in ["성장","증가","확대","기회"]))
            neg = sum(1 for e in evs if any(n in e.claim for n in ["위기","감소","규제","리스크","불확실"]))
            axes.append({
                "cluster_id": cid,
                "centroid": centroid,
                "keywords": [k[0] for k in keywords],
                "pos_count": pos,
                "neg_count": neg,
                "tension_score": neg / (pos + neg + 1e-6)
            })
        
        # 코사인 거리가 가장 먼 두 축을 Tension Pair로 선정
        max_dist = -1
        tension_pair = (None, None)
        for i, a in enumerate(axes):
            for j, b in enumerate(axes):
                if i >= j: continue
                d = cosine(a["centroid"], b["centroid"])
                if d > max_dist:
                    max_dist = d
                    tension_pair = (a, b)
        return tension_pair

    def map_chapters(self, tension_pair: tuple) -> List[dict]:
        a, b = tension_pair
        # 나머지 클러스터 분류
        others = [ax for ax in self.get_all_axes() if ax["cluster_id"] not in [a["cluster_id"], b["cluster_id"]]]
        
        chapters = [
            {"name": "Setup",    "role": "background", "cluster_ids": [], "rule": "시간순 가장 이른 광범위 데이터"},
            {"name": "Tension",  "role": "conflict",   "cluster_ids": [a["cluster_id"], b["cluster_id"]], "rule": "pos vs neg 대립"},
            {"name": "Action",   "role": "solution",   "cluster_ids": [], "rule": "action_score 높은 클러스터"},
            {"name": "Resolution","role": "outlook",   "cluster_ids": [], "rule": "미래 시제/예측 키워드"},
        ]
        
        # Action 채우기: "해야 한다", "전략", "투자", "regulation" 등 행동 어휘 비율
        for ax in others:
            claims = " ".join([e.claim for e in self.clusters[ax["cluster_id"]]])
            action_score = sum(1 for w in ["전략","대응","도입","해야","필요","제안","정책"] if w in claims)
            if action_score >= 2:
                chapters[2]["cluster_ids"].append(ax["cluster_id"])
            elif any(w in claims for w in ["전망","예측","2025","2026","미래","CAGR"]):
                chapters[3]["cluster_ids"].append(ax["cluster_id"])
            else:
                chapters[0]["cluster_ids"].append(ax["cluster_id"])
        
        return chapters
```

### 4.2 챕터 프레임 (Tension → Action) 자동 배치 규칙

| 챕터 | 할당 규칙 (자동) | 예외 시 사람 조정 |
|---|---|---|
| **Setup** | 시간순 가장 이른(2년↑) + 지리적/산업적 배경 데이터 | 클러스터가 2개뿐이면 Setup 생략 |
| **Tension** | `tension_score` 상위 2개 클러스터가 대립(pair) | 대립이 아닌 단일 축이면 사람이 **Thesis 후보 3개** 중 선택 |
| **Action** | "전략/대응/정책/투자" 어휘 밀도 상위 | 없으면 Tension에서 파생 |
| **Resolution** | 미래 시제(year > current) or "전망/예측" 키워드 | |

**사람 개입 포인트**:  
`StoryMapper`는 **3개의 thesis 후보**를 생성하고, 각 후보의 근거 분포를 요약 테이블로 보여줍니다. 사람은 여기서 **1개를 선택**하거나 클러스터를 수동 편입시킵니다.

---

## 5. 약한 데이터 자동 분류: 임계값 매트릭스

### 5.1 4분류 결정 트리 (코드)

```python
# evidence_classifier.py
from typing import Tuple

def classify_evidence(
    tier: SourceTier,
    cross_cv: Optional[float],      # 교차확인 변동계수 (None이면 단일출처)
    publish_year: int,
    sample: Optional[str],
    geo: Optional[str],
    zombie_flag: bool,
    laundering_risk: str,
    quote_length: int
) -> Tuple[str, bool]:
    """
    Returns: (status, slide_eligible)
    """
    age = CURRENT_YEAR - publish_year

    # ===== 삭제 (Delete) =====
    if tier == SourceTier.T4:
        return "deleted", False
    if laundering_risk == "high" and cross_cv is None:
        return "deleted", False
    if cross_cv is not None and cross_cv > 0.30:
        return "deleted", False
    if age >= 5:
        return "deleted", False
    if quote_length < 20:
        return "deleted", False  # 환각 의심

    # ===== 메인근거 (Main) =====
    if (tier in [SourceTier.T1, SourceTier.T2] 
        and cross_cv is not None 
        and cross_cv < 0.10 
        and age <= 2
        and sample is not None 
        and geo is not None
        and not zombie_flag
        and laundering_risk == "low"):
        return "main", True

    # ===== 정성격하 (Demoted Qualitative) =====
    if (cross_cv is not None and 0.10 <= cross_cv <= 0.25 
        and age <= 3 
        and sample is not None):
        return "demoted_qualitative", True  # 슬라이드 본문 가능 but "일부에 따르면" 문구 강제

    # ===== 방향신호 (Demoted Directional) =====
    if age <= 3 and tier == SourceTier.T3 and (cross_cv is None or cross_cv > 0.15):
        return "demoted_directional", False  # 각주/appendix만, 사람 확인 필요
    
    if zombie_flag and age < 5:
        return "demoted_directional", False

    # ===== 최후 보루 =====
    if age < 5 and tier != SourceTier.T4:
        return "demoted_directional", False

    return "deleted", False
```

### 5.2 요약 매트릭스표

| 구분 | **메인근거** | **정성격하** | **방향신호** | **삭제** |
|---|---|---|---|---|
| **소스 티어** | T1/T2, 2개↑ 교차 | T2 단일 or T1+T3 | T3 단일 or T2 단일+old | T4 / 출처미상 |
| **교차 편차(CV)** | < 10% | 10~25% | 교차 실패 or 단일 | > 30% |
| **시한성** | ≤ 2년 | ≤ 3년 | ≤ 3년 (but old) | > 5년 |
| **표본·지역** | 둘 다 명시 | 1개 미상 허용 | 둘 다 미상 가능 | 완전 미상 |
| **좀비수치** | 없음 | 의심 체크 | 플래그 있음 | 플래그+원문 미확인 |
| **출처세탁** | 원문 확인됨 | 저위험 | 원문 미확인 | laundering_risk=high |
| **슬라이드 배치** | 본문 수치 | 본문 + 각주(문구 격하) | Appendix / 각주 | 사용 불가 |
| **사람 게이트** | 불필요 | 불필요 | **필수 확인** | 없음 (자동 폐기) |

---

## 부록: 우리가 추가로 쓰는 기법

### A. Provenance Graph (좀비·세탁 가시화)

```python
# provenance_graph.py
import networkx as nx

G = nx.DiGraph()
for ev in pool:
    node = ev.source_meta.original_url
    G.add_node(node, year=ev.source_meta.publish_year, tier=ev.tier)
    # "인용" 링크가 탐지되면
    if "cited_by" in ev.meta:
        G.add_edge(ev.meta["cited_by"], node, relation="cites")

# 좀비 탐지: in-degree 높으나 publish_year old
zombies = [n for n in G.nodes() if G.in_degree(n) >= 3 and G.nodes[n]["year"] <= CURRENT_YEAR - 3]
```

### B. Confidence Budget (슬라이드 품질 게이트)

```python
# slide_budget.py
def check_slide_budget(block: CEDBlock) -> bool:
    total = len(block.data_points)
    mains = len([dp for dp in block.data_points if dp.status == "main"])
    ratio = mains / total if total > 0 else 0
    
    if ratio < 0.6:
        block.narrative_role = "HOLD_FOR_REVIEW"
        return False  # 자동 생성 중단, 사람 대기열로
    return True
```

### C. Temporal Decay Score (시간 가중치)

```python
def temporal_confidence(base: float, year: int, half_life: float = 1.5) -> float:
    """반감기 1.5년"""
    return base * np.exp(-0.693 * (CURRENT_YEAR - year) / half_life)

# 사용 예: T2 단일 출처라도 3년 전이면 메인 근거로 승격 불가
```

---

### 전체 파이프라인 실행 예시

```python
# main.py
if __name__ == "__main__":
    # 1. Digging
    raw = digging_agent.search("국내 생성형 AI 시장 규모 2024")
    filtered = [DiggingFilter().auto_filter(e) for e in raw if e is not None]
    
    # 2. Pool 적재
    pool = EvidencePool.insert(filtered)
    
    # 3. Verification
    for ev in pool:
        ev.cems.cross_verified = verifier.cross_verify(ev.claim, pool)
        ev.cems.zombie_flag = verifier.zombie_hunt(ev)
        ev.cems.laundering_risk = verifier.laundering_check(ev)
    
    # 4. Classification
    for dp in pool.to_datapoints():
        dp.status, dp.slide_eligible = classify_evidence(...)
        auto_demote_or_delete(dp)
    
    # 5. Story Mapping (사람 게이트 포함)
    mapper = StoryMapper(pool)
    clusters = mapper.cluster_evidence()
    tension_pair = mapper.extract_tension_axes()
    chapters = mapper.map_chapters(tension_pair)
    
    # <-- HUMAN GATE: thesis 3후보 중 선택, 챕터 순서 조정 -->
    
    # 6. Slide Engine
    for ch in chapters:
        blocks = SlideEngine.from_chapter(ch)
        for blk in blocks:
            if not check_slide_budget(blk):
                send_to_human_queue(blk)
            else:
                html = SlideEngine.render_html(blk)  # CED/CEMS 각주 자동 삽입
                save(blk.block_id, html)
```

이 구조를 그대로 `.py` 모듈화하면, 사람은 **thesis 선택**과 **방향신호 데이터 확인** 두 지점만 체크하면 됩니다. 나머지는 코드가 티어링·검증·강등·슬라이드화를 자동으로 처리합니다.