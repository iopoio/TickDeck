#!/usr/bin/env python3
"""스토리 어시스트 — CED 풀 → 챕터 구성 제안(앞 절반 마지막 조각).

검증된 CED 풀을 에디토리얼 디렉터(LLM)가 읽고 덱 골격을 제안한다:
  관통 명제(A는 B를 C한다) + 3~5 챕터(서술 제목·C2 프레임·CED 배치·레이아웃 힌트).
⚠️ 이건 '제안'이다 — 어떤 Tension이 전략적으로 울리나·최종 배치·어조는 사람이 잡는다
   (Part D.3 HITL). story_mapper.chapter()로 사람이 최종 조립.
출처(캐논): 00_SYNTHESIS_콘텐츠방법론 C1·C2·Part D.4.
"""
from __future__ import annotations
import json, re
from ced import route
from story_mapper import chapter, assemble

STORY_PROMPT = """너는 트렌드 리포트 에디토리얼 디렉터다. 아래 [CED 풀](검증된 수치·근거 단위)로 덱 구성을 제안한다.

1. 관통 명제(thesis) = "[거시변인]이 [기술/행동]과 결합해 [구조]를 [형태]로 재편한다" 형식. 추상 제목 금지.
2. CED를 주제로 묶어 3~5개 챕터로. 각 챕터:
   - title: 서술적·결론 문장(예: "도달이 아니라 적합성")
   - frame: C2 골격 중 하나 — Tension | Diagnosis | Mechanism | Scenarios | Convergence | Action
   - ced_indices: 이 챕터에 들어갈 CED 번호들(아래 [n])
   - layout_hint: statgrid(수치 4~6개 묶음) | kpi(히어로 1개) | line(시계열) | donut(비중) | cards(내러티브)
   - so_what: 누구에게 왜 중요한가 1줄
3. 강한 수치(MAIN)는 히어로/빅넘버, 약한 것(정성/방향)은 보조. 약출처·DROP은 빼도 된다.
4. 데이터:내러티브 비율·전환 논리·최종 어조는 사람 몫 — 너는 골격만.

반환(JSON 하나만): {"thesis":"...","title":"...","chapters":[{"num":"01","title":"...","frame":"...","ced_indices":[0,1],"layout_hint":"...","so_what":"..."}]}

[CED 풀]
"""


def pool_summary(ceds):
    """CED 풀을 디렉터용 번호 목록으로."""
    return "\n".join(
        f"[{i}] {route(c):11} {c.source.tier} conf={c.confidence:.2f} | {c.metric} · {c.claim} "
        f"(출처: {c.source.publisher or '미상'})"
        for i, c in enumerate(ceds))


def build_request(ceds):
    return STORY_PROMPT + pool_summary(ceds)


def parse_outline(text):
    """디렉터 반환 → (outline dict, 오류). chapters·thesis 검증."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, "NO_JSON"
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError as e:
        return None, f"BAD_JSON: {e}"
    if not isinstance(d.get("chapters"), list) or not d["chapters"]:
        return None, "NO_CHAPTERS"
    return d, ""


def _short(claim, n=20):
    """긴 주장 → statgrid 라벨용 짧은 구(숫자·주어 군더더기 제거). ponytail: 거친 휴리스틱, 라벨 최종 다듬기는 사람."""
    s = re.sub(r"[\d][\d.,]*\s*(%|vs|/|명|개|배)?", "", claim).strip(" ·,")
    s = re.sub(r"^(소비자|조직|기업|마케팅 예산|브랜드 상호작용|CMO)(의|는|가|이|만)?\s*", "", s).strip()
    s = re.sub(r"^(가|이|은|는|만|의|를|을)\s+", "", s).strip()   # 숫자 제거 후 남은 고아 조사
    return s[:n] + ("…" if len(s) > n else "")


def compose_deck(outline, ceds, meta_extra=None):
    """outline + CED 풀 → engine 슬라이드(자동 조립). statgrid 힌트는 묶음 격자, 그 외는 slide_for 라우팅.
    ⚠️ 라벨·내러티브 다듬기는 사람 — 이건 골격 자동화까지."""
    chapters, used = [], []
    for ch in outline["chapters"]:
        cc = [ceds[i] for i in ch.get("ced_indices", []) if 0 <= i < len(ceds)]
        if not cc:
            continue
        used += [c.source for c in cc]
        eyebrow = f"Ch{ch['num']} · {ch.get('frame', '')}"
        sub = (ch.get("so_what", "") or "")[:74]
        if ch.get("layout_hint") == "statgrid" and len(cc) >= 2:
            src = cc[0].source
            cite = f"{src.publisher} [{src.tier}]" if src.publisher else src.tier
            blocks = [{"layout": "statgrid", "eyebrow": eyebrow, "title": ch["title"], "sub": sub,
                       "stats": [{"label": _short(c.claim), "value": c.metric} for c in cc], "foot": cite}]
        else:
            blocks = cc                                   # CED → slide_for(kpi/cards/…) via chapter()
        chapters.append(chapter(ch["num"], eyebrow, ch["title"], sub, blocks))
    seen, srcs = set(), []
    for s in used:                                        # refs용 출처 dedup
        if s.url not in seen:
            seen.add(s.url); srcs.append(s)
    meta = {"title": outline.get("title", "2026 트렌드"), "thesis": outline.get("thesis", ""),
            "eyebrow": "자동 생성 · 검증 파이프라인", "sub": outline.get("thesis", "")[:84],
            "meta": "TickDeck · 풀 사이클 자동"}
    if meta_extra:
        meta.update(meta_extra)
    return assemble(meta, chapters, srcs[:3])


if __name__ == "__main__":
    sample = '''제안입니다:
```json
{"thesis":"AI가 마케팅 실행과 결합해 차별화를 검증된 신뢰로 재편한다","title":"AI는 기본값",
 "chapters":[
   {"num":"01","title":"도달이 아니라 적합성","frame":"Tension","ced_indices":[0,1,2,3],"layout_hint":"statgrid","so_what":"마케터: 발견 입구 재설계"},
   {"num":"02","title":"AI는 흔하지만 가치는 미실현","frame":"Diagnosis","ced_indices":[4,6],"layout_hint":"kpi","so_what":"경영진: ROI 현실"},
   {"num":"03","title":"통제 없이 성장 요구받는 CMO","frame":"Action","ced_indices":[8,9,10],"layout_hint":"statgrid","so_what":"CMO: MarTech 우선"}]}
```'''
    o, err = parse_outline(sample)
    assert o and not err, err
    assert o["thesis"].count("재편") == 1 and len(o["chapters"]) == 3
    assert o["chapters"][0]["layout_hint"] == "statgrid" and o["chapters"][0]["ced_indices"] == [0, 1, 2, 3]
    assert parse_outline("제안 못 함")[0] is None        # JSON 없음 안전

    # compose_deck — outline + CED 풀 → 슬라이드 자동 조립
    from dig_schema import DigRecord, validate
    from ced import CED
    def c(metric, claim):
        return CED(claim, metric, validate(DigRecord("", None, "local:x", "T2", 2026, publisher="Deloitte", sample="N=1", visited_primary=True)), "", 0.85)
    pool = [c("60%", "소비자의 60%가 소셜로 발견"), c("40%", "소비자 40%가 지출 축소"),
            c("10%", "agentic ROI 10%"), c("85%", "투자 85% 증가"), c("64%", "CMO 64% 과제")]
    mini = {"thesis": "A가 B와 결합해 C를 D로 재편한다", "title": "테스트",
            "chapters": [{"num": "01", "title": "소비자", "frame": "Tension", "ced_indices": [0, 1], "layout_hint": "statgrid"},
                         {"num": "02", "title": "AI 현실", "frame": "Diagnosis", "ced_indices": [2, 3, 4], "layout_hint": "statgrid"}]}
    slides = compose_deck(mini, pool)
    layouts = [s["layout"] for s in slides]
    assert slides[0]["layout"] == "cover" and layouts.count("statgrid") == 2, layouts
    assert _short("소비자의 60%가 소셜·추천으로 발견").startswith("소셜"), _short("소비자의 60%가 소셜·추천으로 발견")
    print(f"story_assist OK — 파싱 {len(o['chapters'])}챕터 + compose {len(slides)}슬라이드(statgrid 2)·빈입력 안전")
