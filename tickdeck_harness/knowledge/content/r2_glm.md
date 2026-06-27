# 트렌드 리포트 자동화 파이프라인: 실행 규칙·스키마·코드

---

## 0. 전체 파이프라인 개요

```
[AI 웹검색 디깅]
     │  ← Section 1: 소스 티어링·원문추적 강제
     ▼
[자료 풀(Pool)]  ← JSON 레코드 누적
     │  ← Section 5: 약한 데이터 자동 분류
     ▼
[자동 검증 엔진]  ← Section 3: 교차확인·좀비·세탁·역검색
     │
     ▼
[검증된 풀] ──→ [스토리 도출] ← Section 4: 풀→thesis→챕터 매핑
                   │  (사람+AI)
                   ▼
              [챕터 슬라이드 JSON] ← Section 2: CED/CEMS 스키마
                   │
                   ▼
              [HTML 슬라이드 엔진]
```

---

## 1. 자동 디깅에서 소스 티어링·원문추적 강제

### 1.1 디깅 에이전트 시스템 프롬프트

```text
你是调查记者级别的趋势研究员。你进行网页搜索后，对每一个主张/数值必须执行“溯源到一级来源（primary source）”的动作。如果无法访问一级来源，请明确标记为“一级来源未验证”，绝对不要推测或编造。

每次搜索后返回以下 JSON。如果字段无法填写，请输入 null 并在 flags 中记录原因。绝对不要用你的训练数据“知识”填补空白——所有信息必须来自你本次实际访问过的 URL。

[티어 정의]
T1_1차: 정부통계·학술논문·SEC공시·기업 공식 보도자료/IR자료 (원문 직접)
T2_2차: T1을 인용하는 언론/분석리포트 (원문을 추적 가능한 경우)
T3_3차: 블로그·위키·집계사이트·마케팅 콘텐츠
T4_불명: 출처 추적 불가

[필수 행동 규칙]
1. 수치를 발견하면 반드시 “이 수치의 최초 출처가 무엇인가?”를 한 번 더 검색한다.
2. 1차 출처 URL에 실제로 방문했을 때만 tier=T1로 기록한다. 방문 못 했으면 tier=T2 이하.
3. 페이월이면 is_paywalled=true, 그리고 페이월 너머 내용을 확인했는지 여부를 기록한다.
4. 같은 수치가 여러 출처에 나타나면, 이들이 모두 같은 원본을 인용하는지(좀비/세탁) 확인한다.
5. sample_size, geography, publication_date가 보이지 않으면 반드시 flag한다. 추측 금지.
6. 이해관계: 해당 연구/수치의 자금출처나 이해관계가 명시되어 있으면 기록한다.
```

> 💡 **한국어 번역 금지**: 프롬프트는 원문 그대로 제시합니다. 번역 시 원문의 뉘앙스가 훼손될 수 있습니다.

### 1.2 디깅 에이전트 출력 스키마 (JSON)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DigResult",
  "type": "object",
  "required": ["claim_id", "claim_text", "source", "flags"],
  "properties": {
    "claim_id": {"type": "string", "description": "UUID"},
    "claim_text": {"type": "string", "description": "발견한 주장/수치의 원문"},
    "numeric_value": {"type": ["number", "null"]},
    "unit": {"type": ["string", "null"]},
    "comparison_context": {"type": ["string", "null"], "description": "예: '전년 대비 15% 증가'"},
    "valence": {
      "type": "string",
      "enum": ["problem", "trend", "solution", "contradiction", "neutral"]
    },
    "source": {
      "type": "object",
      "required": ["url", "tier"],
      "properties": {
        "url": {"type": "string", "description": "에이전트가 실제 방문한 URL"},
        "url_verified_alive": {"type": "boolean"},
        "title": {"type": ["string", "null"]},
        "publisher": {"type": ["string", "null"]},
        "publisher_type": {
          "type": ["string", "null"],
          "enum": ["government", "academic", "media_outlet", "analyst_firm", "corporate", "blog", "aggregator", "unknown"]
        },
        "publication_date": {"type": ["string", "null"], "format": "date"},
        "access_date": {"type": "string", "format": "date"},
        "tier": {"type": "string", "enum": ["T1", "T2", "T3", "T4"]},
        "is_paywalled": {"type": "boolean"},
        "paywall_content_accessed": {"type": "boolean", "description": "페이월 너머 내용을 실제로 확인했는가"},
        "original_source_url": {"type": ["string", "null"], "description": "2차 출처가 인용하는 1차 출처 URL"},
        "original_source_visited": {"type": "boolean", "description": "1차 출처에 실제 방문했는가"},
        "funding_source": {"type": ["string", "null"], "description": "연구 자금출처"},
        "conflict_of_interest": {
          "type": "string",
          "enum": ["none", "noted", "undisclosed", "unknown"]
        }
      }
    },
    "methodology": {
      "type": "object",
      "properties": {
        "study_design": {"type": ["string", "null"], "enum": ["rct", "cohort", "survey", "administrative_data", "meta_analysis", "editorial", "unknown", null]},
        "sample_size": {"type": ["integer", "null"]},
        "sample_description": {"type": ["string", "null"]},
        "geography": {"type": ["string", "null"]},
        "timeframe": {"type": ["string", "null"], "description": "데이터 수집 기간"},
        "margin_of_error": {"type": ["number", "null"]}
      }
    },
    "extraction_confidence": {
      "type": "number",
      "minimum": 0, "maximum": 1,
      "description": "에이전트가 이 수치를 원문에서 정확히 추출했음에 대한 자신감"
    },
    "flags": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": [
          "PAYWALL_UNVERIFIED",
          "NO_PRIMARY_TRACE",
          "ZOMBIE_SUSPECT",
          "ROUND_NUMBER_SUSPECT",
          "DATE_MISSING",
          "SAMPLE_MISSING",
          "GEO_MISSING",
          "METHODOLOGY_MISSING",
          "COI_RISK",
          "STALE_DATA",
          "SINGLE_SOURCE",
          "AGENT_GENERATED_SOURCE",
          "URL_NOT_RESOLVED",
          "RECALLED_NOT_SEARCHED"
        ]
      }
    },
    "raw_excerpt": {"type": "string", "description": "원문에서 발췌한 문장 (검증용)"}
  }
}
```

### 1.3 자동 필터링·플래그 규칙 (코드)

```python
def auto_flag_dig_result(record: dict) -> dict:
    """디깅 결과 1건에 대해 자동 플래그 보정"""
    flags = set(record.get("flags", []))
    src = record["source"]
    meth = record.get("methodology", {})

    # 1. URL 검증
    if not src.get("url_verified_alive"):
        flags.add("URL_NOT_RESOLVED")

    # 2. 1차 출처 추적 여부
    if src["tier"] in ("T2", "T3") and not src.get("original_source_visited"):
        flags.add("NO_PRIMARY_TRACE")

    # 3. 페이월 미확인
    if src.get("is_paywalled") and not src.get("paywall_content_accessed"):
        flags.add("PAYWALL_UNVERIFIED")

    # 4. 필수 메타데이터 누락
    if not src.get("publication_date"):
        flags.add("DATE_MISSING")
    if meth.get("sample_size") is None and record.get("numeric_value") is not None:
        flags.add("SAMPLE_MISSING")
    if not meth.get("geography"):
        flags.add("GEO_MISSING")

    # 5. 노후 데이터 (3년 초과)
    if src.get("publication_date"):
        age_days = (date.today() - parse(src["publication_date"]).date()).days
        if age_days > 1095:  # 3년
            flags.add("STALE_DATA")

    # 6. 라운드 넘버 휴리스틱 (좀비 의심)
    v = record.get("numeric_value")
    if v is not None:
        if v in (10, 20, 50, 80, 90, 100) or (v == int(v) and v % 10 == 0):
            if src["tier"] in ("T3", "T4"):
                flags.add("ROUND_NUMBER_SUSPECT")

    # 7. RECALLED_NOT_SEARCHED 감지
    # 에이전트가 검색 없이 기억으로 반환했는지 휴리스틱 체크
    if src.get("url") and not src.get("url_verified_alive"):
        flags.add("RECALLED_NOT_SEARCHED")

    record["flags"] = sorted(flags)
    return record


def hard_reject(record: dict) -> bool:
    """이 조건이면 풀 적급 거부"""
    flags = set(record.get("flags", []))
    if "URL_NOT_RESOLVED" in flags:
        return True
    if "RECALLED_NOT_SEARCHED" in flags:
        return True
    if record["source"]["tier"] == "T4" and record.get("numeric_value") is not None:
        return True  # T4 출처의 수치는 적급 불가
    return False
```

---

## 2. CED/CEMS → 슬라이드 엔진이 먹는 데이터 구조

### 2.1 슬라이드 JSON 스키마

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SlideObject",
  "type": "object",
  "required": ["slide_id", "chapter_id", "slide_type", "ced"],
  "properties": {
    "slide_id": {"type": "string"},
    "chapter_id": {"type": "string"},
    "slide_type": {
      "type": "string",
      "enum": ["tension", "action", "data", "narrative", "summary"]
    },
    "headline": {"type": "string"},
    "subtext": {"type": ["string", "null"]},

    "ced": {
      "type": "object",
      "description": "Claim-Evidence-Data 구조",
      "required": ["claim"],
      "properties": {
        "claim": {
          "type": "object",
          "required": ["text"],
          "properties": {
            "text": {"type": "string"},
            "claim_type": {
              "type": "string",
              "enum": ["descriptive", "causal", "predictive", "normative"]
            },
            "claim_strength": {
              "type": "string",
              "enum": ["assertion", "hedged", "directional", "speculative"]
            }
          }
        },
        "evidence": {
          "type": "object",
          "properties": {
            "summary": {"type": "string"},
            "evidence_type": {
              "type": "string",
              "enum": ["quantitative", "qualitative", "expert_opinion", "anecdotal", "none"]
            },
            "evidence_grade": {
              "type": "string",
              "enum": ["main", "qualitative_support", "directional_signal", "weak"]
            }
          }
        },
        "data": {
          "type": "object",
          "properties": {
            "value": {"type": ["number", "null"]},
            "unit": {"type": ["string", "null"]},
            "comparison": {"type": ["string", "null"]},
            "baseline": {"type": ["number", "null"]},
            "chart_type": {"type": ["string", "null"], "enum": ["bar", "line", "pie", "none", null]},
            "data_label": {"type": ["string", "null"]}
          }
        },
        "methodology": {
          "type": "object",
          "properties": {
            "design": {"type": ["string", "null"]},
            "sample_size": {"type": ["integer", "null"]},
            "sample_description": {"type": ["string", "null"]},
            "geography": {"type": ["string", "null"]},
            "timeframe": {"type": ["string", "null"]},
            "margin_of_error": {"type": ["number", "null"]}
          }
        },
        "source": {
          "type": "object",
          "properties": {
            "primary_url": {"type": ["string", "null"]},
            "secondary_url": {"type": ["string", "null"]},
            "publisher": {"type": ["string", "null"]},
            "publication_date": {"type": ["string", "null"], "format": "date"},
            "tier": {"type": ["string", "null"], "enum": ["T1", "T2", "T3", "T4", null]},
            "citation_chain": {
              "type": "array",
              "items": {"type": "string"},
              "description": "A→B→C 인용 연쇄. 세탁 감지용"
            }
          }
        },
        "limitation": {
          "type": "object",
          "required": ["text", "severity"],
          "properties": {
            "text": {"type": "string", "description": "예: '미국 소비자만 대상, 한국 적용 불확실'"},
            "severity": {
              "type": "string",
              "enum": ["none", "minor", "major", "fatal"]
            }
          }
        }
      }
    },

    "render_rules": {
      "type": "object",
      "properties": {
        "show_footnote": {"type": "boolean", "default": true},
        "show_limitation_badge": {"type": "boolean", "default": true},
        "footnote_text": {"type": "string"}
      }
    }
  }
}
```

### 2.2 슬라이드 자동 강등·삭제 로직

```python
def evaluate_slide(slide: dict) -> dict:
    """
    슬라이드 1장의 CED를 평가하여 KEEP / DOWNGRADE / DELETE 결정.
    반환: {action, reason, modified_slide?}
    """
    ced = slide["ced"]
    data = ced.get("data", {})
    source = ced.get("source", {})
    meth = ced.get("methodology", {})
    lim = ced.get("limitation", {})
    evidence = ced.get("evidence", {})
    claim = ced["claim"]

    value = data.get("value")
    tier = source.get("tier")
    lim_severity = lim.get("severity", "none")

    # ── DELETE 조건 ──────────────────────────
    # D1: 수치도 없고 출처도 T1/T2가 아님
    if value is None and tier not in ("T1", "T2"):
        return {"action": "DELETE", "reason": "no_data_no_credible_source"}

    # D2: limitation이 fatal
    if lim_severity == "fatal":
        return {"action": "DELETE", "reason": "fatal_limitation"}

    # D3: T4 출처의 수치
    if value is not None and tier == "T4":
        return {"action": "DELETE", "reason": "t4_numeric"}

    # D4: 출처 URL이 아예 없음
    if not source.get("primary_url") and not source.get("secondary_url"):
        return {"action": "DELETE", "reason": "no_source_url"}

    # ── DOWNGRADE_TO_DIRECTIONAL ─────────────
    # DG1: T3 출처의 수치 → "방향신호"로 약화
    if value is not None and tier == "T3":
        return _downgrade_to_directional(slide, "t3_source")

    # DG2: limitation이 major
    if lim_severity == "major":
        return _downgrade_to_directional(slide, "major_limitation")

    # DG3: sample_size 누락 + 수치 존재 + descriptive 주장
    if (value is not None 
        and meth.get("sample_size") is None 
        and claim.get("claim_type") == "descriptive"):
        return _downgrade_to_directional(slide, "no_sample_size")

    # ── DOWNGRADE_TO_QUALITATIVE ─────────────
    # QL1: limitation이 minor + 수치 존재
    if lim_severity == "minor" and value is not None:
        return _downgrade_to_qualitative(slide, "minor_limitation")

    # QL2: T2 출처, 1차 방문 안 함
    if tier == "T2" and not source.get("primary_url"):
        return _downgrade_to_qualitative(slide, "secondary_only_no_primary_visit")

    # ── KEEP ─────────────────────────────────
    return {"action": "KEEP", "reason": "passes_all_checks"}


def _downgrade_to_directional(slide: dict, reason: str) -> dict:
    """수치를 제거하고 '방향성'만 남김"""
    s = copy.deepcopy(slide)
    s["ced"]["data"]["value"] = None
    s["ced"]["data"]["chart_type"] = None
    s["ced"]["evidence"]["evidence_grade"] = "directional_signal"
    s["ced"]["claim"]["claim_strength"] = "directional"
    s["render_rules"]["footnote_text"] = (
        f"정확한 수치는 출처 신뢰도 한계로 표기하지 않음 ({reason})"
    )
    return {"action": "DOWNGRADE_TO_DIRECTIONAL", "reason": reason, "modified_slide": s}


def _downgrade_to_qualitative(slide: dict, reason: str) -> dict:
    """수치는 유지하되 '정성적 근거'로 표기"""
    s = copy.deepcopy(slide)
    s["ced"]["evidence"]["evidence_grade"] = "qualitative_support"
    s["ced"]["claim"]["claim_strength"] = "hedged"
    s["render_rules"]["show_limitation_badge"] = True
    return {"action": "DOWNGRADE_TO_QUALITATIVE", "reason": reason, "modified_slide": s}
```

### 2.3 슬라이드 엔진 렌더 규칙 (HTML 생성 시)

```python
def render_footnote(slide: dict) -> str:
    """각 슬라이드 하단에 자동 부착되는 출처·한계 표시"""
    ced = slide["ced"]
    src = ced.get("source", {})
    lim = ced.get("limitation", {})
    parts = []

    # 출처 라인
    if src.get("publisher"):
        line = f"출처: {src['publisher']}"
        if src.get("publication_date"):
            line += f" ({src['publication_date'][:4]})"
        line += f" [Tier {src.get('tier','?')}]"
        if src.get("primary_url"):
            line += f" — {src['primary_url']}"
        parts.append(line)

    # 한계 라인
    if lim.get("text") and lim.get("severity") != "none":
        icon = {"minor": "⚠", "major": "⚠⚠", "fatal": "🚫"}.get(lim["severity"], "")
        parts.append(f"{icon} 한계: {lim['text']}")

    return " | ".join(parts) if parts else ""
```

---

## 3. 검증 자동화 (사람 없이)

### 3.1 자동 검증 엔진 (파이썬 의사코드)

```python
class AutoVerificationEngine:
    """
    풀에 누적된 각 레코드에 대해 자동 검증 실행.
    모든 검사는 AI 웹검색 API를 사용하여 수행.
    """

    def verify(self, record: dict) -> dict:
        results = {}

        # ① 교차확인: 같은 수치/주장이 독립 출처에 존재하는가?
        results["cross_check"] = self._cross_verification(record)

        # ② 좀비 수치 감지
        results["zombie_check"] = self._zombie_detection(record, results["cross_check"])

        # ③ 출처 세탁 감지
        results["laundering_check"] = self._laundering_detection(results["cross_check"])

        # ④ 반대증거 역검색
        results["counter_evidence"] = self._counter_evidence_search(record)

        # ⑤ 인용 연쇄 분석 (citation chain)
        results["citation_chain"] = self._citation_chain_analysis(record)

        # ⑥ 시간 일관성: 수치의 "원본 발행일" vs "유통일" 차이
        results["temporal_check"] = self._temporal_consistency(record)

        # 종합 판정
        results["verdict"] = self._aggregate_verdict(results)
        return results

    # ────────────────────────────────────────────

    def _cross_verification(self, record: dict) -> dict:
        """
        수치값 + 단위 + 핵심 컨텍스트로 웹검색.
        반환된 각 출처를 독립성 기준으로 필터링.
        """
        value = record.get("numeric_value")
        if value is None:
            return {"status": "SKIP", "reason": "no_numeric_value"}

        query = f'"{value}" "{record.get("unit","")}" {record["claim_text"][:50]}'
        search_results = web_search(query, top_k=20)

        # 독립성 판정: publisher가 다르고 AND original_source가 다름
        independent = []
        seen_origins = set()
        for r in search_results:
            origin = r.get("original_source_url") or r.get("url")
            publisher = r.get("publisher", "")
            # 같은 퍼블리셔 + 같은 원본 = 종속
            key = (publisher, origin)
            if key not in seen_origins:
                seen_origins.add(key)
                independent.append(r)

        n_indep = len(independent)
        n_t1 = sum(1 for r in independent if r.get("tier") == "T1")

        if n_indep >= 3 and n_t1 >= 1:
            status = "STRONG"
        elif n_indep >= 2:
            status = "MODERATE"
        elif n_indep >= 1:
            status = "WEAK"
        else:
            status = "NONE"

        return {
            "status": status,
            "n_independent_sources": n_indep,
            "n_t1_sources": n_t1,
            "sources": independent
        }

    # ────────────────────────────────────────────

    def _zombie_detection(self, record: dict, cross: dict) -> dict:
        """
        좀비 수치 = 여러 출처에 퍼져 있으나 1차 출처가 없음.
        """
        if cross["status"] == "SKIP":
            return {"status": "SKIP"}

        n_indep = cross["n_independent_sources"]
        n_t1 = cross["n_t1_sources"]

        # 3개 이상 독립 출처인데 T1이 0개 → 좀비 의심
        if n_indep >= 3 and n_t1 == 0:
            # 추가 확인: 이 수치의 "최초 등장"을 검색
            earliest = self._find_earliest_appearance(record)
            if earliest and earliest.get("tier") != "T1":
                return {
                    "status": "ZOMBIE_CONFIRMED",
                    "n_carriers": n_indep,
                    "earliest_known": earliest,
                    "primary_origin": None
                }
            return {"status": "ZOMBIE_SUSPECT", "n_carriers": n_indep}

        return {"status": "OK", "n_indep": n_indep, "n_t1": n_t1}

    # ────────────────────────────────────────────

    def _laundering_detection(self, cross: dict) -> dict:
        """
        출처 세탁 = "독립"처럼 보이는 출처들이 모두 같은 원본을 인용.
        citation_chain을 비교하여 동일 원본 클러스터 감지.
        """
        if cross["status"] == "SKIP":
            return {"status": "SKIP"}

        sources = cross.get("sources", [])
        if len(sources) < 2:
            return {"status": "INSUFFICIENT_DATA"}

        # original_source_url 기준 클러스터링
        origin_groups = defaultdict(list)
        for s in sources:
            origin = s.get("original_source_url") or s.get("url")
            origin_groups[origin].append(s)

        n_distinct_origins = len(origin_groups)

        if n_distinct_origins == 1 and len(sources) >= 3:
            return {
                "status": "LAUNDERING_SUSPECT",
                "n_apparent_sources": len(sources),
                "n_real_origins": 1,
                "shared_origin": list(origin_groups.keys())[0]
            }

        return {"status": "OK", "n_distinct_origins": n_distinct_origins}

    # ────────────────────────────────────────────

    def _counter_evidence_search(self, record: dict) -> dict:
        """
        의도적 역검색: 이 주장의 반대/모순 증거를 찾는다.
        """
        claim = record["claim_text"]
        value = record.get("numeric_value")

        # 역검색 쿼리 생성
        queries = [
            f'{claim[:60]} 반대 모순 오류',
            f'{claim[:60]} debunked disputed criticized',
            f'"{value}" {record.get("unit","")} 다른 수치 contradicts',
        ]

        counter_results = []
        for q in queries:
            results = web_search(q, top_k=5)
            for r in results:
                # 실제로 반대 주장인지 LLM으로 판정
                is_contradicting = llm_judge_contradiction(
                    original=claim,
                    candidate=r["snippet"],
                    threshold=0.6  # contradiction_score ≥ 0.6
                )
                if is_contradicting:
                    counter_results.append(r)

        if len(counter_results) == 0:
            status = "UNCONTESTED"
        elif len(counter_results) == 1:
            status = "MILDLY_CONTESTED"
        else:
            status = "CONTESTED"

        return {
            "status": status,
            "n_counter_results": len(counter_results),
            "strongest_counter": counter_results[0] if counter_results else None
        }

    # ────────────────────────────────────────────

    def _citation_chain_analysis(self, record: dict) -> dict:
        """
        A→B→C 인용 연쇄를 그래프로 구성.
        깊이 ≥ 3이고 끝이 T1이 아니면 '약한 연쇄'.
        """
        chain = record.get("source", {}).get("citation_chain", [])
        if not chain:
            return {"status": "NO_CHAIN_DATA"}

        depth = len(chain)
        terminal_tier = record["source"].get("tier")

        if depth >= 3 and terminal_tier != "T1":
            return {"status": "WEAK_CHAIN", "depth": depth, "terminal": terminal_tier}
        return {"status": "OK", "depth": depth, "terminal": terminal_tier}

    # ────────────────────────────────────────────

    def _temporal_consistency(self, record: dict) -> dict:
        """
        수치의 원본 발행연도 vs 현재 보고서 작성 시점.
        3년 초과 = STALE.
        """
        pub = record["source"].get("publication_date")
        if not pub:
            return {"status": "UNKNOWN"}

        age_days = (date.today() - parse(pub).date()).days
        if age_days > 1825:  # 5년
            return {"status": "STALE", "age_years": age_days / 365.25}
        elif age_days > 1095:  # 3년
            return {"status": "AGING", "age_years": age_days / 365.25}
        return {"status": "FRESH", "age_years": age_days / 365.25}

    # ────────────────────────────────────────────

    def _aggregate_verdict(self, results: dict) -> str:
        """모든 검사 결과를 종합하여 최종 판정"""
        cross = results["cross_check"]["status"]
        zombie = results["zombie_check"]["status"]
        laundering = results["laundering_check"]["status"]
        counter = results["counter_evidence"]["status"]
        chain = results["citation_chain"]["status"]
        temporal = results["temporal_check"]["status"]

        # REJECT
        if cross == "NONE":
            return "REJECT"
        if zombie == "ZOMBIE_CONFIRMED":
            return "REJECT"
        if laundering == "LAUNDERING_SUSPECT":
            return "REJECT"

        # DOWNGRADE
        if zombie == "ZOMBIE_SUSPECT":
            return "DOWNGRADE"
        if temporal == "STALE":
            return "DOWNGRADE"
        if chain == "WEAK_CHAIN":
            return "DOWNGRADE"
        if cross == "WEAK":
            return "DOWNGRADE"

        # FLAG_FOR_HUMAN
        if counter == "CONTESTED":
            return "FLAG_FOR_HUMAN"
        if counter == "MILDLY_CONTESTED" and cross == "MODERATE":
            return "FLAG_FOR_HUMAN"

        # ACCEPT
        if cross in ("STRONG", "MODERATE") and counter in ("UNCONTESTED", "MILDLY_CONTESTED"):
            return "ACCEPT"

        return "FLAG_FOR_HUMAN"  # 기본값
```

### 3.2 자동 vs 사람 분담표

| 검증 항목 | 자동 가능? | 근거 |
|---|---|---|
| 교차확인 (수치가 여러 출처에 존재?) | ✅ 자동 | 웹검색 + publisher 비교 |
| 좀비 수치 감지 | ✅ 자동 | 1차 출처 존재 여부 + 전파 패턴 |
| 출처 세탁 감지 | ✅ 자동 | citation_chain 클러스터링 |
| 인용 연쇄 깊이 | ✅ 자동 | 그래프 분석 |
| 티어 분류 | ✅ 자동 (1차) | publisher_type + URL 패턴 |
| 페이월 확인 | ✅ 자동 | HTTP 응답코드 + 콘텐츠 접근 |
| 노후 데이터 | ✅ 자동 | 날짜 계산 |
| 반대증거 존재 여부 | ✅ 자동 | 역검색 쿼리 |
| **반대증거가 실제로 모순인지 판정** | ⚠️ 반자동 | LLM 판정 후 사람 확인 권장 |
| **contest된 주장을 보고서에 넣을지 최종 결정** | ❌ 사람 | 컨텍스트·보고서 목적에 따라 다름 |
| **이해관계 심층 평가** | ❌ 사람 | 자금출처 → 결론까지의 인과관계 판단 |
| **서사 적합성 (이 수치가 스토리에 기여하는가?)** | ❌ 사람 | 서사적 판단 |

---

## 4. 풀 → 스토리 → 챕터 자동 매핑

### 4.1 알고리즘 전체

```python
def pool_to_story(pool: list[dict], n_chapters: int = 5) -> list[dict]:
    """
    누적된 자료 풀에서 thesis를 도출하고 챕터에 배치.
    """

    # ── Step 1: 검증 통과 레코드만 필터 ──
    verified = [r for r in pool if r.get("verdict") in ("ACCEPT", "DOWNGRADE")]
    if len(verified) < n_chapters * 3:
        raise InsufficientDataError(f"검증 통과 레코드 부족: {len(verified)} < {n_chapters*3}")

    # ── Step 2: 의미론적 클러스터링 ──
    clusters = semantic_cluster(verified, threshold=0.72, min_size=3)

    # ── Step 3: 클러스터 강도 평가 ──
    scored = []
    for cluster in clusters:
        score = score_cluster(cluster)
        scored.append((cluster, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    # ── Step 4: 상위 N개 클러스터 → 챕터 ──
    chapters = []
    for i, (cluster, score) in enumerate(scored[:n_chapters]):
        chapter = build_chapter(cluster, score, chapter_id=f"ch{i+1}")
        chapters.append(chapter)

    return chapters
```

### 4.2 클러스터 강도 평가

```python
def score_cluster(cluster: list[dict]) -> float:
    """
    클러스터가 "보고서의 한 챕터"가 될 자격이 있는지 평가.
    0~100점.
    """
    n = len(cluster)

    # 출처 다양성 (최대 25점)
    unique_publishers = len({r["source"]["publisher"] for r in cluster if r["source"].get("publisher")})
    publisher_score = min(unique_publishers * 5, 25)

    # 티어 가중 (최대 25점)
    tier_weights = {"T1": 10, "T2": 6, "T3": 2, "T4": 0}
    tier_score = min(sum(tier_weights.get(r["source"].get("tier"), 0) for r in cluster), 25)

    # 수치 밀도 (최대 20점): 수치를 가진 레코드 비율
    n_numeric = sum(1 for r in cluster if r.get("numeric_value") is not None)
    numeric_score = (n_numeric / n) * 20

    # 검증 상태 (최대 15점)
    n_accept = sum(1 for r in cluster if r.get("verdict") == "ACCEPT")
    n_downgrade = sum(1 for r in cluster if r.get("verdict") == "DOWNGRADE")
    verify_score = (n_accept * 3 + n_downgrade * 1.5)
    verify_score = min(verify_score, 15)

    # 시역성 (최대 15점): 최근 데이터 비중
    recent = sum(1 for r in cluster if _is_recent(r, years=2))
    recency_score = (recent / n) * 15

    total = publisher_score + tier_score + numeric_score + verify_score + recency_score
    return round(total, 1)


def _is_recent(record: dict, years: int = 2) -> bool:
    pub = record["source"].get("publication_date")
    if not pub:
        return False
    age_days = (date.today() - parse(pub).date()).days
    return age_days <= years * 365
```

### 4.3 챕터 빌드 (tension → action 프레임)

```python
def build_chapter(cluster: list[dict], score: float, chapter_id: str) -> dict:
    """
    클러스터를 tension→action 챕터 프레임에 배치.
    """

    # ── Thesis 도출 (LLM) ──
    thesis = llm_generate_thesis(
        cluster_records=cluster,
        prompt_template=THESIS_PROMPT  # 아래 정의
    )

    # ── valence별 분류 ──
    tensions = [r for r in cluster if r.get("valence") in ("problem", "contradiction")]
    actions = [r for r in cluster if r.get("valence") in ("solution",)]
    trends = [r for r in cluster if r.get("valence") in ("trend", "neutral")]

    # ── 슬라이드 구성 ──
    slides = []

    # Slide 1: Tension (문제/모순)
    if tensions:
        slides.append(_make_slide(
            chapter_id, "tension",
            headline=_extract_headline(tensions[0]),
            records=tensions[:3]  # 상위 3개
        ))

    # Slide 2-3: Data (트렌드 수치)
    for r in trends[:2]:
        if r.get("numeric_value") is not None:
            slides.append(_make_slide(chapter_id, "data", records=[r]))

    # Slide 4: Action (대응/해법)
    if actions:
        slides.append(_make_slide(
            chapter_id, "action",
            headline=_extract_headline(actions[0]),
            records=actions[:3]
        ))

    # 빈 슬라이드 보정: tension이나 action이 비면 trends에서 재구성
    if not tensions and not actions:
        slides.append(_make_slide(chapter_id, "narrative", records=trends[:3]))

    return {
        "chapter_id": chapter_id,
        "thesis": thesis,
        "cluster_score": score,
        "slides": slides
    }
```

### 4.4 Thesis 도출 프롬프트

```text
THESIS_PROMPT = """
아래 클러스터의 자료들을 분석하여 이 챕터의 핵심 thesis(논제)를 한 문장으로 작성하시오.

형식: "[주체]가 [무엇을 하는/겪는] 중이며, 이는 [긴장/모순]을 만들지만 [대응/방향]으로 나아가고 있다."

규칙:
1. 수치가 없으면 "증가하는", "가속하는" 등 방향 표현만 쓰고 구체적 숫자는 쓰지 마시오.
2. 검증 상태가 DOWNGRADE인 자료는 "일부 자료에 따르면" 수식어를 붙이시오.
3. 반대증거가 있는 주장은 thesis에 모순을 명시하시오.
4. 추측 금지. 자료에 없는 내용은 쓰지 마시오.

자료:
{cluster_summaries}

출력: thesis 문장 1개 + 근거 자료 ID 목록
"""
```

---

## 5. 약한 데이터 자동 분류

### 5.1 분류 기준 매트릭스

```python
def classify_evidence(record: dict, verification: dict) -> str:
    """
    반환: "main_evidence" | "qualitative_support" | "directional_signal" | "DELETE"

    판정 매트릭스:
    ┌──────────────┬─────────┬──────────┬──────────┬──────────┐
    │              │ T1 출처 │ T2 출처  │ T3 출처  │ T4/없음  │
    ├──────────────┼─────────┼──────────┼──────────┼──────────┤
    │ ACCEPT+강력교차│ MAIN    │ MAIN     │ QUALITAT │ DELETE   │
    │ ACCEPT+교차   │ MAIN    │ QUALITAT │ DIRECT.  │ DELETE   │
    │ DOWNGRADE    │ QUALITAT│ DIRECT.  │ DIRECT.  │ DELETE   │
    │ REJECT       │ DELETE  │ DELETE   │ DELETE   │ DELETE   │
    └──────────────┴─────────┴──────────┴──────────┴──────────┘
    """
    tier = record["source"].get("tier", "T4")
    verdict = verification["verdict"]
    cross = verification["cross_check"]["status"]

    # REJECT → 무조건 DELETE
    if verdict == "REJECT":
        return "DELETE"

    # DOWNGRADE
    if verdict == "DOWNGRADE":
        if tier == "T1":
            return "qualitative_support"
        elif tier == "T2":
            return "directional_signal"
        else:
            return "directional_signal" if cross != "NONE" else "DELETE"

    # ACCEPT
    if verdict == "ACCEPT":
        if tier == "T4":
            return "DELETE"
        if cross == "STRONG":
            return "main_evidence" if tier in ("T1", "T2") else "qualitative_support"
        elif cross == "MODERATE":
            return "main_evidence" if tier == "T1" else "qualitative_support"
        elif cross == "WEAK":
            return "qualitative_support" if tier in ("T1","T2") else "directional_signal"
        else:  # NONE
            return "directional_signal" if tier == "T1" else "DELETE"

    # FLAG_FOR_HUMAN → 임시로 qualitative_support
    if verdict == "FLAG_FOR_HUMAN":
        return "qualitative_support"

    return "DELETE"
```

### 5.2 임계값 정의 (명시적)

```python
# ═══════════════════════════════════════════
# 전역 임계값 설정
# ═══════════════════════════════════════════

THRESHOLDS = {
    # 교차확인
    "cross_strong_min_independent": 3,      # 3개 이상 독립 출처
    "cross_strong_min_t1": 1,               # 그 중 1개 이상 T1
    "cross_moderate_min_independent": 2,    # 2개 이상

    # 좀비 감지
    "zombie_min_carriers": 3,               # 3개 이상 매개체
    "zombie_max_t1": 0,                     # T1이 0개

    # 출처 세탁
    "laundering_min_apparent_sources": 3,   # 겉보기 3개 이상
    "laundering_max_real_origins": 1,       # 실제 원본 1개

    # 반대증거
    "counter_contested_min": 2,             # 2개 이상 반대증거
    "contradiction_llm_threshold": 0.6,     # LLM 모순 판정 임계값

    # 시간 노후
    "stale_years": 5,                       # 5년 초과 = STALE
    "aging_years": 3,                       # 3년 초과 = AGING

    # 의미론적 클러스터링
    "semantic_cluster_threshold": 0.72,     # 코사인 유사도
    "cluster_min_size": 3,                  # 최소 레코드 수

    # 클러스터 강도
    "min_chapter_score": 45.0,              # 이 점수 미만은 챕터 불가

    # 수치 신뢰도
    "extraction_confidence_min": 0.7,       # 에이전트 추출 자신감
    "round_number_set": {10, 20, 25, 50, 75, 80, 90, 100},  # 좀비 의심 라운드 넘버
}
```

### 5.3 분류 결과별 렌더링 규칙

```python
RENDER_BY_GRADE = {
    "main_evidence": {
        "show_number": True,
        "show_chart": True,
        "claim_strength": "assertion",
        "footnote": "full",            # 출처+한계 전체 표시
        "badge": None
    },
    "qualitative_support": {
        "show_number": True,           # 숫자는 보여주되
        "show_chart": False,           # 차트는 안 그림 (정성적)
        "claim_strength": "hedged",    # "~한다고 한다" 수준
        "footnote": "full",
        "badge": "⚠ 참고자료"
    },
    "directional_signal": {
        "show_number": False,          # 숫자 숨김
        "show_chart": False,
        "claim_strength": "directional",  # "증가 추세" 수준
        "footnote": "source_only",     # 출처만
        "badge": "◆ 방향신호"
    },
    "DELETE": {
        "show_number": False,
        "show_chart": False,
        "claim_strength": None,
        "footnote": None,
        "badge": None,
        "action": "REMOVE_SLIDE"
    }
}
```

---

## 6. 추가 기법 (나만의)

### 6.1 Provenance Graph (출처 계보 그래프)

```python
class ProvenanceGraph:
    """
    모든 레코드의 인용 관계를 방향 그래프로 구성.
    노드 = 출처 URL, 엣지 = "A가 B를 인용함".
    이 그래프로 세탁·좀비·순환인용을 한 번에 감지.
    """

    def __init__(self):
        self.graph = defaultdict(list)  # {url: [cited_urls]}
        self.nodes = {}                  # {url: {tier, publisher, date}}

    def add_record(self, record: dict):
        url = record["source"]["url"]
        origin = record["source"].get("original_source_url")
        self.nodes[url] = {
            "tier": record["source"]["tier"],
            "publisher": record["source"].get("publisher"),
            "date": record["source"].get("publication_date")
        }
        if origin and origin != url:
            self.graph[url].append(origin)
            if origin not in self.nodes:
                self.nodes[origin] = {"tier": None, "publisher": None, "date": None}

    def detect_circular_citation(self) -> list:
        """A→B→C→A 순환 인용 감지 (세탁의 극단적 형태)"""
        return list(nx.simple_cycles(self.graph))

    def find_orphan_roots(self) -> list:
        """
        인용 연쇄를 따라갔더니 끝이 T1이 아닌/없는 노드.
        = 좀비 수치의 근원.
        """
        orphans = []
        for url in self.nodes:
            if self._trace_to_root(url, visited=set()) is None:
                orphans.append(url)
        return orphans

    def _trace_to_root(self, url: str, visited: set, depth: int = 0) -> str | None:
        if depth > 10:  # 무한 루프 방지
            return None
        if url in visited:
            return None
        visited.add(url)

        node = self.nodes.get(url, {})
        if node.get("tier") == "T1":
            return url  # 1차 출처 도달

        children = self.graph.get(url, [])
        if not children:
            return None  # 끝이 T1이 아님 = orphan

        for child in children:
            result = self._trace_to_root(child, visited, depth + 1)
            if result:
                return result
        return None

    def compute_provenance_depth(self, url: str) -> int:
        """해당 출처에서 1차 출처까지의 거리. 짧을수록 좋음."""
        return nx.shortest_path_length(self.graph, url, target=self._find_t1(url))
```

### 6.2 Negative Search Mandate (역검색 의무화)

```python
MANDATORY_NEGATIVE_QUERIES = [
    "{claim} 오류 오류정정",
    "{claim} debunked false misleading",
    "{claim} retracted withdrawn",
    '"{value}" {unit} 다르다 contradicts different',
    "{publisher} {claim} 논란 controversy",
]

def mandatory_negative_search(record: dict) -> dict:
    """
    모든 MAIN_EVIDENCE 급 수치에 대해 역검색을 의무 실행.
    역검색 없이는 main_evidence 등급 불가.
    """
    if record.get("evidence_grade") != "main_evidence":
        return {"required": False}

    results = []
    for template in MANDATORY_NEGATIVE_QUERIES:
        query = template.format(
            claim=record["claim_text"][:50],
            value=record.get("numeric_value"),
            unit=record.get("unit", ""),
            publisher=record["source"].get("publisher", "")
        )
        hits = web_search(query, top_k=3)
        results.extend(hits)

    # 역검색에서 반대증거가 1개라도 나오면 main_evidence 불가
    if len(results) > 0:
        record["evidence_grade"] = "qualitative_support"
        record["limitation"]["text"] = (
            (record["limitation"].get("text","") + 
             " | 역검색에서 반대/논란 증거 발견").strip(" |")
        )
        record["limitation"]["severity"] = "minor"

    return {"required": True, "n_hits": len(results), "results": results}
```

### 6.3 Temporal Decay (시간 감쇠)

```python
def apply_temporal_decay(record: dict) -> dict:
    """
    데이터 나이에 따라 자동으로 신뢰도를 감쇠.
    매년 tier가 한 단계씩 하향.
    """
    pub = record["source"].get("publication_date")
    if not pub:
        return record

    age_years = (date.today() - parse(pub).date()).days / 365.25

    tier_order = ["T1", "T2", "T3", "T4"]
    current_idx = tier_order.index(record["source"]["tier"])

    # 2년마다 1단계 하향
    decay_steps = int(age_years // 2)
    new_idx = min(current_idx + decay_steps, 3)

    if new_idx != current_idx:
        record["source"]["tier"] = tier_order[new_idx]
        record["flags"] = record.get("flags", []) + ["TEMPORAL_DECAY"]
        # tier 하향으로 인한 재분류 트리거
        record["_needs_reclassify"] = True

    return record
```

### 6.4 Round Number Heuristic (라운드 넘버 휴리스틱)

```python
def round_number_zombie_check(record: dict, pool: list[dict]) -> dict:
    """
    "80%의 소비자가~" 같은 라운드 넘버가 풀에 여러 개 있고
    모두 T1 출처가 없으면 좀비로 판정.
    """
    value = record.get("numeric_value")
    if value is None:
        return {"status": "SKIP"}

    # 라운드 넘버인가?
    is_round = (
        value in THRESHOLDS["round_number_set"] or
        (value == int(value) and value % 10 == 0 and value <= 100)
    )
    if not is_round:
        return {"status": "NOT_ROUND"}

    # 풀에서 같은 값 + 비슷한 컨텍스트를 가진 다른 레코드 검색
    siblings = [
        r for r in pool
        if r.get("numeric_value") == value
        and r["claim_id"] != record["claim_id"]
        and _context_similarity(r, record) > 0.5
    ]

    n_siblings = len(siblings)
    n_t1_siblings = sum(1 for r in siblings if r["source"].get("tier") == "T1")

    if n_siblings >= 2 and n_t1_siblings == 0:
        return {
            "status": "ROUND_NUMBER_ZOMBIE",
            "value": value,
            "n_carriers": n_siblings + 1,
            "action": "FORCE_DOWNGRADE_TO_DIRECTIONAL"
        }

    return {"status": "OK", "n_siblings": n_siblings}
```

### 6.5 풀 정체 감지 (Pool Stagnation)

```python
def detect_pool_stagnation(pool: list[dict]) -> dict:
    """
    새로운 디깅이 와도 풀에 "새로운 1차 출처"가 안 늘어나면
    = 에이전트가 같은 2차 출처들을 계속 가져오고 있다는 신호.
    """
    recent_10 = pool[-10:]
    unique_origins = {
        r["source"].get("original_source_url") or r["source"]["url"]
        for r in recent_10
    }
    n_t1_recent = sum(1 for r in recent_10 if r["source"].get("tier") == "T1")

    if len(unique_origins) <= 3 and n_t1_recent == 0:
        return {
            "status": "STAGNANT",
            "action": "REFRESH_SEARCH_STRATEGY",
            "suggestion": "검색 쿼리를 바꾸거나, 1차 출처 직접 탐색 모드로 전환"
        }
    return {"status": "HEALTHY", "n_unique_origins": len(unique_origins)}
```

---

## 7. 엔드투엔드 파이프라인 (통합)

```python
def run_pipeline(search_topics: list[str], n_chapters: int = 5) -> dict:
    """전체 파이프라인 실행"""

    pool = []

    # ── Phase 1: 디깅 ──
    for topic in search_topics:
        raw_results = ai_agent_dig(topic)  # Section 1 프롬프트+스키마
        for record in raw_results:
            record = auto_flag_dig_result(record)       # Section 1.3
            if hard_reject(record):
                continue
            record = apply_temporal_decay(record)        # Section 6.3
            pool.append(record)

    # ── Phase 2: 정체 감지 ──
    stagnation = detect_pool_stagnation(pool)            # Section 6.5
    if stagnation["status"] == "STAGNANT":
        # 검색 전략 갱신 후 재디깅
        pool = refresh_and_redig(search_topics, pool)

    # ── Phase 3: 자동 검증 ──
    verifier = AutoVerificationEngine()
    provenance = ProvenanceGraph()                       # Section 6.1

    for record in pool:
        provenance.add_record(record)
        verification = verifier.verify(record)            # Section 3
        record["verdict"] = verification["verdict"]
        record["verification_detail"] = verification

        # 좀비 라운드넘버 추가 검사
        zombie_round = round_number_zombie_check(record, pool)  # Section 6.4
        if zombie_round["status"] == "ROUND_NUMBER_ZOMBIE":
            record["verdict"] = "DOWNGRADE"

    # ── Phase 4: 증거 등급 분류 ──
    for record in pool:
        record["evidence_grade"] = classify_evidence(record, record["verification_detail"])  # Section 5

        # main_evidence에 역검색 의무화
        if record["evidence_grade"] == "main_evidence":
            mandatory_negative_search(record)             # Section 6.2

    # ── Phase 5: 스토리 → 챕터 ──
    chapters = pool_to_story(pool, n_chapters=n_chapters)  # Section 4

    # ── Phase 6: 슬라이드 평가·강등 ──
    final_slides = []
    for ch in chapters:
        for slide in ch["slides"]:
            eval_result = evaluate_slide(slide)           # Section 2.2
            if eval_result["action"] == "DELETE":
                continue
            elif eval_result["action"].startswith("DOWNGRADE"):
                slide = eval_result["modified_slide"]
            final_slides.append(slide)

    # ── Phase 7: HTML 렌더 ──
    html = slide_engine.render(final_slides, render_rules=RENDER_BY_GRADE)

    return {
        "html": html,
        "chapters": chapters,
        "pool_stats": {
            "total_records": len(pool),
            "accepted": sum(1 for r in pool if r["verdict"] == "ACCEPT"),
            "downgraded": sum(1 for r in pool if r["verdict"] == "DOWNGRADE"),
            "rejected": sum(1 for r in pool if r["verdict"] == "REJECT"),
            "flagged_for_human": sum(1 for r in pool if r["verdict"] == "FLAG_FOR_HUMAN"),
            "evidence_grades": {
                g: sum(1 for r in pool if r.get("evidence_grade") == g)
                for g in ["main_evidence", "qualitative_support", "directional_signal"]
            }
        },
        "provenance_orphans": provenance.find_orphan_roots(),
        "stagnation_check": stagnation
    }
```

---

## 요약: 핵심 설계 원칙

| 원칙 | 구현 |
|---|---|
| **1차 출처 안 가면 통과 못 함** | `original_source_visited=false` → tier T2 이하 강제 + `NO_PRIMARY_TRACE` 플래그 |
| **수치 없는 슬라이드는 강등** | `data.value == null && tier ∉ {T1,T2}` → DELETE |
| **좀비 수치 자동 감지** | 3개+ 매개체, T1=0 → `ZOMBIE_CONFIRMED` → REJECT |
| **세탁 감지** | 겉보기 3개 출처가 같은 원본 → `LAUNDERING_SUSPECT` → REJECT |
| **역검색 의무화** | `main_evidence` 등급은 반드시 역검색 통과해야 |
| **시간 감쇠** | 2년마다 tier 1단계 하향 |
| **사람은 판단만** | `FLAG_FOR_HUMAN`만 사람이 보고, 나머지는 전부 자동 |

이 전체를 YAML/JSON 설정 파일로 임계값을 조정 가능하게 만들면, 보고서 주제별로 "엄격 모드"/"탐색 모드"를 전환할 수 있습니다.