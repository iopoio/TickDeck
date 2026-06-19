"""수치 자동 대조 layer — 진실주의 핵심 (시동 신규 ②)

모델 출력의 핵심 수치(시장규모·성장률·금액 등)를 corpus(Tavily 본문)에
정규화 grep → corpus에 없는 수치는 [환각 의심] 플래그.

PoC v2 결과 메모에서 수동으로 증명한 검산(IDC 1.29조·52.8% corpus 실재 / Qwen TBRC 수치 실재)을
자동 파이프라인으로 승격한 것. PoC가 수동으로 옳다고 입증한 로직만 코드화한다.

핵심 설계:
- 숫자 + 단위/문맥을 묶어 추출 (예: "618억", "36.1%", "1.29조", "$84.17B", "4,771억").
- corpus는 콤마/공백/통화기호 정규화 후 substring 매칭 (모델은 "841억", 본문은 "84,170 million" 등
  표기가 달라질 수 있으므로 숫자 핵심부 위주로 관대하게 매칭하되, 매칭 실패만 플래그).
- 매칭 실패 != 환각 확정. "본문 미발견 → 사람이 확인할 것"이라는 의심 플래그 (진실주의: 단정 X).
"""

import re
import unicodedata

# 한국어/영어 수치 패턴 (숫자 + 단위/기호). 우선순위 = 구체 패턴부터.
_NUM_PATTERNS = [
    r"\bCAGR\s?\d[\d,\.]*\s?%?",             # CAGR 10.6%
    r"\$\s?\d[\d,\.]*\s?(?:trillion|billion|million|B|T|M)\b",
    r"\d[\d,\.]*\s?(?:trillion|billion|million|B|T|M)\b",
    r"\d[\d,\.]*\s?%",                       # 퍼센트
    r"\d[\d,\.]*\s?(?:조|억|만)\s?(?:달러|원)?",  # 한국어 단위 금액
]

# 노이즈로 제외할 짧은/흔한 수치 (연도·한 자리·각주번호 등)
_TRIVIAL = re.compile(r"^\d{1,4}$")  # 1~4자리 순수 정수 (연도·각주). 단위 붙으면 추출 패턴서 살아남음.
# 출처 발행월·날짜 (YYYY.MM / YYYY.MM.DD / YYYY-MM) = 검증 대상 아님 (인용 메타)
_DATE_LIKE = re.compile(r"^(19|20)\d{2}[\.\-]\d{1,2}([\.\-]\d{1,2})?\.?$")
# 목록 번호 ("1." "2." … 줄머리 또는 단독) = 수치 아님 (6/18 노이즈 정밀화)
_LIST_ORDINAL = re.compile(r"^\d{1,3}\.$")
# URL = 슬러그/식별자 숫자(예: market-101700)가 수치로 오인됨 → 추출 전 제거 (6/18)
_URL_PAT = re.compile(r"https?://[^\s)\]}>,]+")


def _normalize(text: str) -> str:
    """corpus·후보를 비교용으로 정규화: 전각→반각, 콤마/공백/통화기호 제거, 소문자."""
    t = unicodedata.normalize("NFKC", text)
    t = t.lower()
    t = t.replace(",", "").replace(" ", "").replace(" ", "")
    t = t.replace("$", "").replace("usd", "")
    return t


def _digit_core(token: str) -> str:
    """토큰에서 숫자 핵심부만 추출 (소수점 포함). 단위 무시한 raw 숫자 비교용."""
    norm = _normalize(token)
    m = re.search(r"\d[\d\.]*\d|\d", norm)
    return m.group(0) if m else ""


def _korean_unit_variants(token: str) -> list[str]:
    """한국어 억/조 표기를 영문/숫자 환산 변형으로 생성 (표기차 흡수).

    예: "618억" → ["618", "61.8", "6.18", "61,800"] 등 영문 "61.83 billion" 표기 매칭 시도.
    "1.29조" → ["1.29", "1290", "1,290"] (1.29 trillion 등).
    환각 false-positive(정상인데 의심 플래그)를 줄이기 위함. false-negative는 추가하지 않음.
    """
    norm = unicodedata.normalize("NFKC", token)
    m = re.search(r"(\d[\d,\.]*)\s*(조|억|만)", norm)
    if not m:
        return []
    raw = m.group(1).replace(",", "")
    unit = m.group(2)
    try:
        val = float(raw)
    except ValueError:
        return []
    variants = set()
    if unit == "조":  # 조 = 1e12. 영문 trillion 표기는 보통 "1.29" 그대로
        variants.add(_fmt(val))            # 1.29
        variants.add(_fmt(val * 1000))     # 1290 (billion 환산)
    elif unit == "억":  # 억 = 1e8. 영문 billion = 1e9 → val/10
        variants.add(_fmt(val))            # 618
        variants.add(_fmt(val / 10))       # 61.8 (billion 환산: 618억=61.8B)
        variants.add(_fmt(val / 100))      # 6.18
    elif unit == "만":  # 만 = 1e4. 2,160만 = 21.6 million 표기 흔함
        variants.add(_fmt(val))
        variants.add(_fmt(val / 100))   # 21.6 (2160만 → 21.6 million)
        variants.add(_fmt(val / 1000))  # 2.16
    return [v for v in variants if len(v) >= 3]


def _fmt(x: float) -> str:
    """숫자를 정규화 비교용 문자열로 (불필요한 .0 제거)."""
    if x == int(x):
        return str(int(x))
    # 소수 둘째자리까지 (영문 본문 표기 관행)
    s = f"{x:.2f}".rstrip("0").rstrip(".")
    return s


def _overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
    """이미 채택한 더 구체적인 수치 span과 겹치면 중복 후보로 본다."""
    start, end = span
    return any(start < used_end and end > used_start for used_start, used_end in spans)


def extract_numbers(report: str) -> list[str]:
    """보고서에서 의미 있는 수치 후보 추출 (중복 제거·등장 순서 유지).

    6/18 노이즈 정밀화: ① URL을 먼저 제거해 슬러그 숫자(market-101700 등)가 수치로
    오인되는 것 차단 ② 목록 번호("1." "2." …)는 본문 수치가 아니라 서식이므로 제외.
    """
    # ① URL 제거 — 슬러그/식별자 숫자(예: market-101700)가 수치 후보로 새는 것 차단
    report = _URL_PAT.sub(" ", report)
    found: list[str] = []
    accepted_spans: list[tuple[int, int]] = []
    seen = set()
    for pat in _NUM_PATTERNS:
        for m in re.finditer(pat, report):
            if _overlaps(m.span(), accepted_spans):
                continue
            tok = m.group(0).strip()
            if not tok:
                continue
            stripped = tok.replace("$", "").replace(" ", "")
            # ② 목록 번호("1." "2." …)는 서식이지 수치 아님 → 스킵
            if _LIST_ORDINAL.match(stripped):
                continue
            # 단위·기호 없는 순수 1~4자리 정수는 연도/각주 노이즈 → 스킵
            if _TRIVIAL.match(stripped) and "%" not in tok and "조" not in tok and "억" not in tok:
                continue
            # 출처 발행월·날짜(YYYY.MM 등)는 인용 메타 → 검증 대상 아님
            if _DATE_LIKE.match(stripped):
                continue
            key = _normalize(tok)
            if len(key) < 2:  # 너무 짧은 건 노이즈
                continue
            if key in seen:
                continue
            seen.add(key)
            accepted_spans.append(m.span())
            found.append(tok)
    return found


def audit_report(report: str, corpus_docs: list[dict]) -> dict:
    """보고서 수치를 corpus 본문에 대조.

    corpus_docs = [{"title","url","raw_content",...}, ...]
    반환: {checked, matched, suspected, flags:[{number, found, evidence_url}], coverage}
    """
    # corpus 본문 전체를 정규화해 합침 (출처 url 추적 위해 doc별 정규화본도 보관)
    norm_docs = [(d.get("url", ""), _normalize(d.get("raw_content", "") or "")) for d in corpus_docs]
    full_norm = "\n".join(nd for _, nd in norm_docs)

    candidates = extract_numbers(report)
    flags = []
    matched = 0
    for tok in candidates:
        core = _digit_core(tok)
        norm_tok = _normalize(tok)
        kr_variants = _korean_unit_variants(tok)  # 억/조 → 영문 billion 환산 변형
        # 1차: 단위 포함 정규화 토큰. 2차: 숫자 핵심부. 3차: 한국어 단위 환산 변형.
        evidence_url = ""
        hit = False
        if norm_tok and norm_tok in full_norm:
            hit = True
        elif core and len(core) >= 3 and core in full_norm:
            # 핵심 숫자가 3자리+ 일 때만 (1~2자리는 우연 매칭 위험)
            hit = True
        elif any(v in full_norm for v in kr_variants):
            hit = True
        if hit:
            for url, nd in norm_docs:
                if ((norm_tok and norm_tok in nd)
                        or (core and len(core) >= 3 and core in nd)
                        or any(v in nd for v in kr_variants)):
                    evidence_url = url
                    break
            matched += 1
            flags.append({"number": tok, "found": True, "evidence_url": evidence_url})
        else:
            flags.append({"number": tok, "found": False, "evidence_url": "",
                          "flag": "[환각 의심] corpus 본문 미발견 — 사람 확인 요망"})

    checked = len(candidates)
    suspected = checked - matched
    return {
        "checked": checked,
        "matched": matched,
        "suspected": suspected,
        "coverage": round(matched / checked, 3) if checked else None,
        "flags": flags,
    }


if __name__ == "__main__":
    # 자가 테스트: PoC corpus로 Qwen 보고서 수치 대조
    import json
    from pathlib import Path
    base = Path(__file__).parent.parent
    corpus = json.loads((base / "deepresearch_poc_v2_corpus.json").read_text(encoding="utf-8"))
    result = json.loads((base / "deepresearch_poc_v2_result.json").read_text(encoding="utf-8"))
    for leader in ["qwen", "kimi"]:
        rep = result[leader]["leader"]["final"]
        audit = audit_report(rep, corpus[leader])
        print(f"\n=== {leader} 수치 대조 ===")
        print(f"  검사 {audit['checked']} · 본문실재 {audit['matched']} · 의심 {audit['suspected']} · 커버리지 {audit['coverage']}")
        for f in audit["flags"]:
            mark = "OK " if f["found"] else "❓ "
            print(f"  {mark}{f['number']}")
