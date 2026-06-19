"""2층 선별 — 문서 스크리닝 → 섹션 RAG (시동 신규 ③)

PoC v2는 본문 앞 4,000자를 통째로 모델에 투입했다. SemiWiki 본문은 65만자라 앞 4천자만
보면 핵심 수치 섹션을 놓칠 수 있고, 무관 문서까지 동일 토큰을 먹는다.

2층 설계 (deck 비용설계 차용):
- 1층 (문서 스크리닝): 각 문서 앞 800자(목차·요약)로 쿼리 관련성 점수 → 무관 문서 컷.
- 2층 (섹션 RAG): 통과 문서에서 쿼리 키워드 주변 ±window 문단만 발췌 → 핵심만 모델 투입.

외부 임베딩 모델 비용 없이 키워드 기반 BM25-lite 스코어링 (1인 운영·저비용 원칙).
수치가 든 문단을 우선 살리도록 숫자 보너스 가중.
"""

import re

SCREEN_HEAD_CHARS = 800       # 1층 스크리닝: 문서 앞부분만
SECTION_WINDOW = 600          # 2층: 키워드 매칭 문단 ±글자
MAX_SECTIONS_PER_DOC = 4      # 문서당 발췌 섹션 상한
SCREEN_MIN_SCORE = 1          # 1층 통과 최소 점수 (무관 문서 컷)
NUM_BONUS = 1.5               # 숫자(시장규모·%) 든 섹션 가중


def _tokenize(text: str) -> list[str]:
    """영문·숫자 단어 토큰화 (소문자)."""
    return re.findall(r"[a-zA-Z]{3,}|\d[\d,\.]*%?", text.lower())


def _keywords(query: str) -> list[str]:
    """쿼리에서 의미 키워드 추출 (불용어 제거)."""
    stop = {"the", "and", "for", "with", "size", "report", "market"}  # market 흔해서 약하게
    toks = [t for t in _tokenize(query) if t not in stop and not t.isdigit()]
    return list(dict.fromkeys(toks))  # 중복 제거·순서 유지


def screen_documents(docs: list[dict], query: str) -> list[dict]:
    """1층: 문서 앞부분으로 쿼리 관련성 점수 → 정렬. 무관 문서 컷.

    docs = [{"title","url","raw_content",...}]
    반환: score 내림차순 정렬 + screen_score 부여 (SCREEN_MIN_SCORE 미만 제외).
    """
    kws = _keywords(query)
    scored = []
    for d in docs:
        head = (d.get("raw_content", "") or "")[:SCREEN_HEAD_CHARS].lower()
        title = (d.get("title", "") or "").lower()
        score = 0.0
        for kw in kws:
            score += head.count(kw) + title.count(kw) * 2  # 제목 매칭 가중
        # 숫자(%·금액) 든 문서 약한 보너스 (전망 보고서는 수치 핵심)
        if re.search(r"\d[\d,\.]*\s?%|\$\s?\d|\d[\d,\.]*\s?(?:billion|trillion|억|조)", head):
            score += 1
        d2 = dict(d)
        d2["screen_score"] = round(score, 2)
        scored.append(d2)
    scored.sort(key=lambda x: x["screen_score"], reverse=True)
    return [d for d in scored if d["screen_score"] >= SCREEN_MIN_SCORE]


def extract_sections(doc: dict, query: str) -> str:
    """2층: 문서에서 쿼리 키워드 주변 ±window 섹션만 발췌. 숫자 든 섹션 우선."""
    raw = doc.get("raw_content", "") or ""
    if not raw:
        return ""
    kws = _keywords(query)
    low = raw.lower()
    # 키워드 등장 위치 수집
    hits = []
    for kw in kws:
        start = 0
        while True:
            idx = low.find(kw, start)
            if idx < 0:
                break
            hits.append(idx)
            start = idx + len(kw)
    if not hits:
        # 키워드 없으면 앞부분만
        return raw[:SECTION_WINDOW * 2]
    hits.sort()
    # 인접 hit 병합 → 섹션 후보
    sections = []
    cur_start = max(0, hits[0] - SECTION_WINDOW)
    cur_end = min(len(raw), hits[0] + SECTION_WINDOW)
    for h in hits[1:]:
        s = max(0, h - SECTION_WINDOW)
        e = min(len(raw), h + SECTION_WINDOW)
        if s <= cur_end:  # 겹치면 병합
            cur_end = max(cur_end, e)
        else:
            sections.append((cur_start, cur_end))
            cur_start, cur_end = s, e
    sections.append((cur_start, cur_end))
    # 섹션 점수 = 키워드 밀도 + 숫자 보너스
    scored_sec = []
    for s, e in sections:
        chunk = raw[s:e]
        cl = chunk.lower()
        sc = sum(cl.count(kw) for kw in kws)
        if re.search(r"\d[\d,\.]*\s?%|\$\s?\d|\d[\d,\.]*\s?(?:billion|trillion|억|조)", chunk):
            sc *= NUM_BONUS
        scored_sec.append((sc, chunk))
    scored_sec.sort(key=lambda x: x[0], reverse=True)
    top = [c for _, c in scored_sec[:MAX_SECTIONS_PER_DOC]]
    return "\n…\n".join(top)


def build_context(docs: list[dict], query: str, per_doc_chars: int = 2500) -> tuple[str, list[dict]]:
    """2층 선별 전체 파이프라인 → 모델 투입용 컨텍스트 문자열 + 선별 메타.

    반환: (context_text, screen_meta)
    """
    screened = screen_documents(docs, query)
    blocks = []
    meta = []
    for i, d in enumerate(screened):
        section = extract_sections(d, query)[:per_doc_chars]
        meta.append({
            "rank": i + 1,
            "title": d.get("title", "")[:80],
            "url": d.get("url", ""),
            "screen_score": d["screen_score"],
            "raw_len": d.get("raw_len", len(d.get("raw_content", "") or "")),
            "section_len": len(section),
        })
        blocks.append(f"[{i+1}] {d.get('title','')}\nURL: {d.get('url','')}\n관련 섹션:\n{section}")
    return ("\n\n---\n\n".join(blocks) if blocks else "관련 문서 없음"), meta


if __name__ == "__main__":
    # 자가 테스트: PoC corpus로 2층 선별 효과 측정
    import json
    from pathlib import Path
    base = Path(__file__).parent.parent
    corpus = json.loads((base / "deepresearch_poc_v2_corpus.json").read_text(encoding="utf-8"))
    for leader in ["qwen", "kimi"]:
        docs = corpus[leader]
        q = "AI semiconductor market size forecast 2026 CAGR growth"
        ctx, meta = build_context(docs, q)
        raw_total = sum(d["raw_len"] for d in docs)
        print(f"\n=== {leader} 2층 선별 ===")
        print(f"  원본 {len(docs)}문서 {raw_total:,}자 → 스크리닝 통과 {len(meta)}문서 → 컨텍스트 {len(ctx):,}자")
        print(f"  압축률 {len(ctx)/raw_total*100:.1f}% (원본 대비)")
        for m in meta[:5]:
            print(f"  #{m['rank']} score={m['screen_score']} raw={m['raw_len']:,}→sec={m['section_len']} {m['title'][:50]}")
