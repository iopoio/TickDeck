#!/usr/bin/env python3
"""한국어 조사·맞춤법 규칙 검사 — deck_spec 표면 텍스트의 기계적 오류를 잡는다.

완성 게이트용. 형태소 분석 없이 받침 규칙만으로 조사 오류(으로/로·은/는·이/가·을/를·과/와)를
검출한다. sed 치환 부작용("한 명로")·재작성 조사 깨짐 같은 기계 오류가 사람 눈 없이 걸린다.
100% 정확은 아니라(조사 vs 단어 일부 구분 불가) 의심 목록을 WARN으로 낸다 — 차단 아닌 리뷰 신호.

  python3 spellcheck_kr.py <deck_spec.json>   # exit 0 = 의심 0, exit 2 = 의심 있음
"""
import json, re, sys
from pathlib import Path

# ponytail: 받침 규칙만. 형태소 분석은 과설계 — 조사 오류 유형은 이걸로 잡힌다.
def jongseong(ch):
    """종성 인덱스. 0=받침없음, 8=ㄹ, None=한글 아님."""
    if "가" <= ch <= "힣":
        return (ord(ch) - 0xAC00) % 28
    return None


def strings_in(obj, path=""):
    """JSON에서 (경로, 문자열) 전수 추출."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from strings_in(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from strings_in(v, f"{path}[{i}]")


# 조사쌍: (받침_없을때, 받침_있을때). 검사 = 앞글자 받침과 안 맞는 조사 사용.
# 경계(뒤가 공백·문장부호·끝)로 조사일 가능성만 좁힘 — 그래도 오탐 있어 WARN.
JOSA = [
    ("가", "이"),   # 이/가
    ("는", "은"),   # 은/는
    ("를", "을"),   # 을/를
    ("와", "과"),   # 과/와
]
BOUNDARY = r"(?=[\s,.\"')\]]|$)"


def check(text):
    hits = []
    # 으로/로: 받침 있고 ㄹ 아니면 "으로", 받침 없거나 ㄹ이면 "로"
    for m in re.finditer(r"([가-힣])로" + BOUNDARY, text):
        j = jongseong(m.group(1))
        if j is not None and j != 0 and j != 8:  # 받침 있고 ㄹ 아닌데 "로"
            hits.append(f"'{m.group(1)}로' → '{m.group(1)}으로'?")
    # 이/가·은/는·을/를·과/와
    for no_b, with_b in JOSA:
        for m in re.finditer(rf"([가-힣])({no_b}|{with_b})" + BOUNDARY, text):
            prev, used = m.group(1), m.group(2)
            j = jongseong(prev)
            if j is None:
                continue
            need = with_b if j != 0 else no_b
            if used != need:
                hits.append(f"'{prev}{used}' → '{prev}{need}'?")
    return hits


def main():
    if len(sys.argv) < 2:
        print("usage: spellcheck_kr.py <deck_spec.json>"); sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    # id·경로·registry 참조는 조사 없음 → 사람이 읽는 표면 필드만 검사
    SURFACE = ("short_title", "subtitle", "title", "note", "label", "headline",
               "eyebrow", "text", "caption", "def", "term", "governing", "value", "name")
    found = []
    for path, s in strings_in(data):
        field = path.rsplit(".", 1)[-1].split("[")[0]
        if field not in SURFACE:
            continue
        if not re.search(r"[가-힣]", s):
            continue
        for h in check(s):
            found.append((path, h, s[:50]))
    if not found:
        print("맞춤법 규칙 검사: 의심 0건 ✅"); sys.exit(0)
    print(f"⚠️ 조사·맞춤법 의심 {len(found)}건 (WARN — 사람 확인):")
    seen = set()
    for path, hit, ctx in found:
        key = (hit, ctx)
        if key in seen:
            continue
        seen.add(key)
        print(f"  · {hit}   [{path}] \"{ctx}\"")
    sys.exit(2)


if __name__ == "__main__":
    main()
