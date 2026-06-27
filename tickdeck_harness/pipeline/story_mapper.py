#!/usr/bin/env python3
"""story_mapper — route 결과 → engine 슬라이드 + 챕터 프레임 + 렌즈 체크리스트.

CED route(MAIN/QUALITATIVE/DIRECTIONAL/DROP)를 engine 레이아웃으로 매핑:
  MAIN→kpi(빅넘버) · QUALITATIVE→cards(수치는 맥락) · DIRECTIONAL→statement(수치숨김·증감) · DROP→제외.
챕터 골격은 수렴(C2 Tension→…→Action), 분석 렌즈는 발산(B 라이브러리서 2~4개 골라 beat 주입).
출처(캐논): 00_SYNTHESIS Part B·C2·D.4.

assemble(meta, chapters, sources) → engine.build_deck가 먹는 slides 리스트.
"""
from __future__ import annotations
from ced import CED, route, MAIN, QUALITATIVE, DROP  # DIRECTIONAL = slide_for의 else 분기

FRAME = ("Tension", "Diagnosis", "Mechanism", "Scenarios", "Convergence", "Action")  # C2 골격

# 분석 렌즈 라이브러리 — 체크리스트(리포트 시작 시 2~4개 선택). 값 = 사람용 설명.
LENSES = {
    "friction": "마찰 추적 — 규제·노조·소송 변곡점(Qwen B1)",
    "talent_capital": "Talent×Capital 괴리 — 숨은 알파/거품(Qwen B2)",
    "negative_space": "네거티브 스페이스 — 사라지는 것 역추적(GLM B3)",
    "inversion": "증거 역검색 — 반론 병렬배치(Kimi B4)",
    "counterfactual": "반사실 슬롯 — 챕터 끝 실패 시나리오(B5)",
    "lang_lag": "언어간 시차 — Regional Variance(Kimi B6)",
    "tombstone": "Tombstone — 실패한 유사 트렌드(Qwen B10)",
    "trigger": "Trigger Point — 지표 도달 시 행동(GLM B9)",
}

DROPPED = []   # 라우터가 뺀 CED 로그(투명성 — selfcheck에서 읽음)


def _cite(src):
    """A6 인용 — 가진 필드만(없는 건 추측 안 함)."""
    bits = [b for b in (src.publisher, f"《{src.report}》" if src.report else "", src.year and str(src.year)) if b]
    cond = " · ".join(b for b in (src.region, src.sample) if b)
    tag = src.tier + (" ·⚠" + "/".join(src.flags) if src.flags else "")
    s = ", ".join(str(b) for b in bits)
    return f"{s} [{tag}]" + (f" · {cond}" if cond else "")


def _up(ced):
    m = (ced.metric or "") + ced.claim
    return any(w in m for w in ("증가", "상승", "↑", "+", "성장", "확대"))


def slide_for(ced, eyebrow):
    """CED 하나 → engine 슬라이드 dict(또는 DROP이면 None)."""
    r = route(ced)
    if r == DROP:
        DROPPED.append((ced.claim, ced.confidence, ced.source.tier, ced.source.flags))
        return None
    cite = _cite(ced.source)
    if r == MAIN:                                    # 빅넘버 — T1/T2·고신뢰만 여기 옴
        return {"layout": "kpi", "eyebrow": eyebrow, "title": ced.claim, "value": ced.metric, "delta": "",
                "aux": [{"label": "한계", "value": ced.limitation or "—"}, {"label": "출처", "value": cite}],
                "foot": cite}
    if r == QUALITATIVE:                             # 수치는 맥락(히어로 X) · _qmerge로 묶임
        return {"layout": "cards", "eyebrow": eyebrow, "title": "단일 출처 · 정성 근거(히어로서 강등)", "_qmerge": True,
                "cards": [{"kick": cite, "title": ced.metric or "정성 근거",
                           "body": f"{ced.claim} · 한계: {ced.limitation or '미표기(UNAUDITED)'}"}]}
    arrow = "▲ 증가" if _up(ced) else "→ 이동"        # DIRECTIONAL — 수치 숨기고 방향만
    return {"layout": "statement", "eyebrow": eyebrow + " · 방향 신호",
            "title": f"{ced.claim} {arrow}"}


def _merge_qual(slides):
    """연속 _qmerge(정성 강등) 카드를 한 cards 슬라이드로(최대 3장) — 단일카드 난립·3연속 방지."""
    out, buf = [], []
    def flush():
        for i in range(0, len(buf), 3):
            grp = buf[i:i + 3]
            out.append({"layout": "cards", "eyebrow": grp[0]["eyebrow"], "title": grp[0]["title"],
                        "cards": [c for s in grp for c in s["cards"]]})
        buf.clear()
    for s in slides:
        if s.get("_qmerge"):
            buf.append(s)
        else:
            flush()
            out.append(s)
    flush()
    return out


def chart_block(kind, head, data, source_ced):
    """line/donut 차트를 CED와 동일한 출처 게이트로 통과시켜 슬라이드 dict 반환(또는 DROP=None).
    kind = 'line'|'donut' · head = {eyebrow,title,sub} · data = 차트 데이터 · source_ced = 헤드라인 수치 감싼 CED.
    약한 출처(MAIN 아님)면 foot에 '방향·약출처' 캐비엇, DROP이면 차트 자체를 빼버린다."""
    r = route(source_ced)
    if r == DROP:
        DROPPED.append((head.get("title", kind), source_ced.confidence, source_ced.source.tier, source_ced.source.flags))
        return None
    cite = _cite(source_ced.source)
    foot = ("방향·약출처 · " + cite) if r != MAIN else cite
    return {"layout": kind, "foot": foot, **head, **data}


def chapter(num, eyebrow, title, sub, blocks, counterfactual=None):
    """divider + 블록(raw dict 그대로 / CED는 route, 정성은 묶음) + (렌즈)반사실 beat."""
    out = [{"layout": "divider", "num": num, "eyebrow": eyebrow, "title": title, "sub": sub}]
    routed = []
    for b in blocks:
        s = slide_for(b, eyebrow) if isinstance(b, CED) else b
        if s:
            routed.append(s)
    out += _merge_qual(routed)
    if counterfactual:                               # B5 반사실 슬롯(렌즈 적용 시)
        out.append({"layout": "statement", "eyebrow": eyebrow + " · 반사실",
                    "title": f"이 트렌드가 2026 실패/지연한다면: {counterfactual}"})
    return out


def assemble(meta, chapters, sources, lenses=()):
    """cover + agenda + 챕터들 + closing + refs(sources)."""
    for k in lenses:
        assert k in LENSES, f"알 수 없는 렌즈: {k}"
    slides = [{"layout": "cover", "eyebrow": meta.get("eyebrow", ""), "title": meta["title"],
               "sub": meta.get("sub", ""), "meta": meta.get("meta", "TickDeck")}]
    if chapters:
        slides.append({"layout": "agenda", "eyebrow": "목차 · Agenda", "title": meta.get("thesis", meta["title"]),
                       "items": [{"no": c[0]["num"], "t": c[0]["title"], "d": c[0]["sub"]} for c in chapters]})
    for c in chapters:
        slides += c
    if meta.get("closing"):
        slides.append(meta["closing"])
    if sources:
        slides.append({"layout": "refs", "eyebrow": "참고자료 · Sources", "title": "근거 출처",
                       "refs": [{"s": f"{s.publisher} — {s.report}" if s.report else (s.publisher or s.url),
                                 "t": _cite(s)} for s in sources]})
    return slides


if __name__ == "__main__":
    from dig_schema import DigRecord, validate
    DROPPED.clear()
    strong = validate(DigRecord("AI 유료전환 73%", "73%", "https://data.bls.gov/r.pdf", "T1", 2026,
                                publisher="BLS", report="X", sample="N=1,200", visited_primary=True))
    weak = validate(DigRecord("진정성 갈망 42%", "42%", "https://wgsn.com/r", "T2", 2026, publisher="WGSN", report="Future Consumer"))
    junk = validate(DigRecord("출처불명 30%", "30%", "https://news.x.com/p", "T1", 2019))  # 좀비+강등→DROP대상
    ch = chapter("01", "Ch1 · 긴장", "AI 역설", "흔할수록 비싸짐",
                 [CED("AI 유료전환", "73%", strong, "북미 N=1,200", 0.9),
                  CED("진정성 갈망", "42%", weak, "영국", 0.7),
                  CED("출처불명", "30%", junk, "", 0.4),
                  {"layout": "cards", "eyebrow": "Ch1", "title": "내러티브",
                   "cards": [{"kick": "k", "title": "t", "body": "b"}]}],
                 counterfactual="합성 탐지 기술이 신뢰 격차를 메우면 프리미엄 소멸")
    deck = assemble({"title": "테스트", "thesis": "A는 B를 C한다", "eyebrow": "demo"}, [ch], [strong, weak])
    layouts = [s["layout"] for s in deck]
    assert layouts.count("kpi") == 1, "MAIN→kpi 1개여야"          # strong만 MAIN
    assert layouts.count("cards") == 2, "QUAL카드 + 내러티브카드"   # weak QUAL + raw
    assert any("방향" not in "" and s["layout"] == "statement" for s in deck)  # 반사실 statement
    assert len(DROPPED) == 1 and DROPPED[0][0] == "출처불명", DROPPED  # junk DROP
    assert deck[0]["layout"] == "cover" and deck[-1]["layout"] == "refs"
    print(f"story_mapper OK — {len(deck)}슬라이드 · MAIN1/QUAL1/DROP1 · refs+cover · DROPPED={len(DROPPED)}")
