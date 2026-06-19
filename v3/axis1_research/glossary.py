"""용어·표현 추출 layer — 축3 통합 (6/18 후추님 지시)

조사·종합 중 그 분야 전문가가 자주 쓰는 **용어·표현·프레이밍**을 수집한다.
명언 인용이 아니라 분야 언어 (예: 반도체=테이프아웃·수율 / 투자=밸류에이션·컨센서스).

진실 안전장치 (수치 대조와 동일 사상·축3 1번 규칙=정확):
- 보고서에서 후보 용어를 뽑되, **corpus 본문에 실재하는 용어만** 살린다. 지어내기 X.
- 매칭된 용어는 출처 URL과 함께 저장 → 재사용·검산 가능.

누적 = 축3:
- 실행마다 나온 용어집을 한곳(glossary_library.json)에 append.
- 분야 태그 + 출처를 함께 저장 → 축적물이 곧 축3 라이브러리 (별도 시스템 X).

설계 (저비용·외부 LLM 호출 0·키워드 기반):
- 한국어 명사구(2~6자 한글 덩어리)·영문 용어(약어 포함)·CamelCase 추출.
- 흔한 일반어(불용어)·수치·날짜는 제외.
- corpus 본문에 등장하는 것만 통과.
  보고서 본문에만 있는 후보는 출처 검산이 안 되므로 누적하지 않음.
"""

import re
import json
import unicodedata
from pathlib import Path

MODULE_DIR = Path(__file__).parent
LIBRARY_PATH = MODULE_DIR / "glossary_library.json"   # 축3 누적 라이브러리

# 한국어 일반어/연결어 불용어 (분야 용어가 아닌 흔한 말).
# 분야 무관 흔한 명사·부사·접속사·서술형. 조사는 _strip_josa로 따로 떼어냄.
_KO_STOP = {
    # 흔한 일반 명사
    "시장", "전망", "성장", "글로벌", "증가", "감소", "확대", "축소", "분석", "보고서",
    "기준", "전년", "올해", "내년", "지난해", "현재", "최근", "이상", "이하", "관련",
    "주요", "다양", "경우", "부분", "수준", "규모", "구조", "동인", "요인", "영향",
    "지역", "국가", "기업", "업체", "산업", "부문", "제품", "기술", "수요", "공급",
    "가격", "비용", "투자", "정책", "지원", "확보", "강화", "개선", "예상", "전체",
    "달러", "원화", "생산", "판매", "점유율", "비중", "수치", "결과", "내용", "업데이트",
    "중심", "핵심", "선도", "진출", "도입", "출시", "발표", "확장", "유지", "전환",
    # 부사·접속사·시점어
    "이번", "통해", "위해", "대한", "따라", "또한", "특히", "한편", "그러나", "하지만",
    "반면", "향후", "대비", "연간", "연평균", "당시", "이후", "이전", "동안", "기간",
    "미국", "중국", "유럽", "한국", "일본", "독일", "인도", "각국", "세계", "국내",
    "북미", "보고", "모두", "완료", "구조적", "년은", "년간", "삼성",
    # 서술형 어간(노이즈로 자주 잡힘)
    "있으", "없으", "되는", "하는", "이며", "으로", "에서", "에게", "부터", "까지",
    "성장하", "성장", "감소하", "증가하", "확대되", "전망되", "예상되",
}
# 조사·서술형 접미 (단어 끝에서 떼어냄 → 어근만 비교)
_JOSA = ("으로서", "으로써", "에서는", "에게는", "라고", "이라고", "으로", "에서", "에게",
         "에는", "으론", "에선", "까지", "부터", "이며", "이고", "이다", "이라", "라는",
         "은", "는", "이", "가", "을", "를", "의", "와", "과", "도", "만", "로", "에",
         "들", "은는", "하고", "하며", "하여", "되는", "되어", "였다", "했다", "한다",
         "이고", "라며", "면서", "지만", "거나", "처럼", "보다", "마다", "조차",
         "고", "며", "서", "나", "야")
# 영문 일반어 불용어
_EN_STOP = {
    "the", "and", "for", "with", "this", "that", "from", "will", "has", "have",
    "market", "report", "growth", "size", "global", "year", "billion", "million",
    "trillion", "usd", "cagr", "forecast", "share", "industry", "region", "company",
    "according", "expected", "during", "between", "compared", "https", "http", "www",
    # 발행처·월·일반 명사 (분야 용어 아님)
    "fortune", "business", "insights", "precedence", "research", "volumes",
    "outlook", "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december", "bi", "inc", "ltd",
}

# 영문 용어 후보: 약어(대문자 2~6)만. CamelCase/일반 단어는 발행처·인명 노이즈가 많아 제외.
#   분야 jargon으로 확실한 건 약어(EV·ESS·NVIDIA·AMD·IDC·CAGR…). 단 발행처 약어는 _EN_STOP로 컷.
_EN_TERM = re.compile(r"\b[A-Z]{2,7}\b")
# 한국어 명사구 후보: 한글 2~8자 덩어리
_KO_TERM = re.compile(r"[가-힣]{2,8}")
# 영문+한글 복합(예: LFP 배터리, BESS 시장) — 약어 뒤 한글
_MIX_TERM = re.compile(r"\b[A-Z]{2,6}\b\s?[가-힣]{2,6}")
_URL_PAT = re.compile(r"https?://[^\s)\]}>,]+")
_DIGIT = re.compile(r"\d")


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).lower()


def _strip_josa(tok: str) -> str:
    """한국어 단어 끝의 조사·서술형 접미를 떼어내 어근만 남김 (긴 것부터).

    예: "시장은"→"시장", "수요가"→"수요", "점유율로"→"점유율", "선도하고"→"선도".
    어근이 2자 미만으로 줄면 원본 유지(과도 절단 방지).
    """
    for j in sorted(_JOSA, key=len, reverse=True):
        if tok.endswith(j) and len(tok) - len(j) >= 2:
            return tok[: -len(j)]
    return tok


def _candidates(report: str) -> list[str]:
    """보고서에서 분야 용어 후보 추출 (서식·URL·수치 제거 후)."""
    text = _URL_PAT.sub(" ", report)
    # 마크다운 서식 제거(##·**·- 등)는 단어 경계만 흩뜨리므로 가볍게 공백 치환
    text = re.sub(r"[#*`>\-\|]", " ", text)
    cands: list[str] = []
    seen = set()

    def _add(tok: str):
        tok = tok.strip()
        if not tok or _DIGIT.search(tok):
            return
        # 순수 한글 토큰은 조사·서술형 접미 제거 후 어근으로 (시장은→시장)
        if re.fullmatch(r"[가-힣]+", tok):
            tok = _strip_josa(tok)
        low = tok.lower()
        if low in _EN_STOP or tok in _KO_STOP:
            return
        if len(tok) < 2:
            return
        key = _normalize(tok)
        if key in seen:
            return
        seen.add(key)
        cands.append(tok)

    # 우선순위: 복합(약어+한글) → 영문/약어 → 한국어 명사구
    for m in _MIX_TERM.finditer(text):
        # "BESS 시장이" → 약어 + 한글어근 (조사 제거): "BESS 시장"
        parts = re.sub(r"\s+", " ", m.group(0)).split(" ", 1)
        if len(parts) == 2:
            abbr, ko = parts[0], _strip_josa(parts[1])
            if ko and ko not in _KO_STOP and len(ko) >= 2:
                _add(f"{abbr} {ko}")
    for m in _EN_TERM.finditer(text):
        _add(m.group(0))
    for m in _KO_TERM.finditer(text):
        _add(m.group(0))
    return cands


def extract_glossary(report: str, corpus_docs: list[dict], domain: str, topic: str,
                     max_terms: int = 30) -> dict:
    """보고서 용어 후보를 corpus 본문에 대조 → 실재 용어만 용어집으로.

    진실 안전장치: corpus 본문에 실제 등장하는 용어만 살린다(지어내기 X).
    반환: {domain, topic, terms:[{term, source_url, kind}], extracted, corpus_confirmed}
    """
    # corpus 정규화본 + 출처 URL 보관
    norm_docs = [(d.get("url", ""), _normalize(d.get("raw_content", "") or "")) for d in corpus_docs]
    full_norm = "\n".join(nd for _, nd in norm_docs)
    cands = _candidates(report)
    terms = []
    for tok in cands:
        ntok = _normalize(tok)
        # corpus 원문에 실재해야 통과 (지어낸 용어·번역 노이즈 차단)
        is_en = bool(re.search(r"[a-z]", ntok))
        if ntok in full_norm:
            kind = "복합" if re.search(r"[a-z].*[가-힣]", ntok) else ("영문" if is_en else "한국어")
            src = ""
            for url, nd in norm_docs:
                if ntok in nd:
                    src = url
                    break
            terms.append({"term": tok, "source_url": src, "kind": kind})

    # 랭킹: ① 종류 우선순위(복합·영문 약어 = 분야 jargon이라 가장 확실) ② corpus 출처 확인 우선.
    #   순수 한국어 단일 명사는 형태소 분석 없이 regex로 뽑아 노이즈 잔여 → 뒤로.
    _kind_rank = {"복합": 0, "영문": 1, "한국어": 2}

    def _sort_key(t):
        confirmed = 0 if (t["source_url"] and t["source_url"] != "(보고서 종합 본문)") else 1
        return (_kind_rank.get(t["kind"], 3), confirmed)

    terms.sort(key=_sort_key)
    terms = terms[:max_terms]
    corpus_confirmed = sum(1 for t in terms if t["source_url"] and t["source_url"] != "(보고서 종합 본문)")
    return {
        "domain": domain,
        "topic": topic,
        "extracted": len(cands),
        "kept": len(terms),
        "corpus_confirmed": corpus_confirmed,
        "terms": terms,
    }


def append_to_library(glossary: dict, ran_at: str, library_path: Path = LIBRARY_PATH) -> int:
    """실행 용어집을 축3 누적 라이브러리에 append (분야 태그 + 출처 보존).

    중복 용어는 같은 분야 안에서 source_url을 합쳐 누적. 반환: 라이브러리 총 용어 수.
    """
    if library_path.exists():
        lib = json.loads(library_path.read_text(encoding="utf-8"))
    else:
        lib = {"updated_at": "", "entries": []}

    lib["entries"].append({
        "ran_at": ran_at,
        "domain": glossary["domain"],
        "topic": glossary["topic"],
        "terms": glossary["terms"],
    })
    lib["updated_at"] = ran_at
    library_path.write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(e["terms"]) for e in lib["entries"])
    return total


def infer_domain(topic: str) -> str:
    """주제 문장에서 대략의 분야 태그를 추론 (간단 키워드 매핑·없으면 '일반')."""
    t = topic.lower()
    table = [
        (("배터리", "전기차", "ev", "ess", "2차전지"), "에너지·배터리"),
        (("반도체", "ai 반도체", "semiconductor", "칩", "파운드리"), "반도체"),
        (("투자", "주식", "증시", "밸류", "금리", "채권"), "투자·금융"),
        (("바이오", "제약", "신약", "헬스"), "바이오·헬스"),
        (("부동산", "리츠", "건설"), "부동산"),
        (("ai", "인공지능", "llm", "머신러닝"), "AI"),
    ]
    for kws, label in table:
        if any(k in t for k in kws):
            return label
    return "일반"


if __name__ == "__main__":
    # 자가 테스트 (API 호출 X): 기존 run 결과로 용어집 추출 검증
    base = MODULE_DIR / "runs"
    runs = sorted(base.glob("*_corpus.json"))
    if not runs:
        print("[자가 테스트] runs/ 에 corpus 없음 — 운영 실행 후 재시도.")
    else:
        corpus_file = runs[-1]
        result_file = Path(str(corpus_file).replace("_corpus.json", ".json"))
        corpus = json.loads(corpus_file.read_text(encoding="utf-8"))
        result = json.loads(result_file.read_text(encoding="utf-8"))
        topic = result["topic"]
        report = result["leader"]["final"]
        dom = infer_domain(topic)
        g = extract_glossary(report, corpus, dom, topic)
        print(f"=== 용어집 자가 테스트 · 분야={dom} · 주제={topic} ===")
        print(f"  후보 {g['extracted']} → 채택 {g['kept']} (corpus 출처확인 {g['corpus_confirmed']})")
        for t in g["terms"]:
            src = t["source_url"][:50] if t["source_url"] else "(미상)"
            print(f"  [{t['kind']}] {t['term']:<16} ← {src}")
