#!/usr/bin/env python3
"""2026 마케팅 트렌드 — 흡수 루프로 재생성(end-to-end 시험).

marketing_full.py(흡수 전)의 실제 내용·출처를 CED로 감싸 파이프라인에 통과:
  - 단일 히어로 수치 → route()가 출처 강도로 강등(T2 단일·미검증 → QUALITATIVE/DIRECTIONAL).
  - 원본의 무출처 '62%' → DROP(파이프라인이 무근거 적발).
  - 비교 차트·내러티브·퍼널 = raw 블록 그대로(단일 수치 아님).
  - 렌즈 = counterfactual(B5) 챕터별 반사실 + tombstone(B10).
실행: python3 marketing_v2.py [theme]  →  out_marketing_v2_<theme>.html
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).with_name("pipeline")))
from dig_schema import DigRecord, validate          # noqa: E402
from ced import CED                                  # noqa: E402
from story_mapper import chapter, assemble, DROPPED  # noqa: E402
from engine import build_deck, selfcheck            # noqa: E402

Y = 2026
def src(pub, rep, tier="T2", year=Y, region="", sample=""):
    # visited_primary=False — 이번 세션서 1차 원문 직접 열람 안 함(정직). 그래서 강등됨.
    host = (pub.lower().split() or ["unknown"])[0]
    return validate(DigRecord("", None, f"https://{host}.com/r", tier, year,
                              publisher=pub, report=rep, region=region, sample=sample), current_year=Y)

# ── 히어로 단일수치 CED 풀 (실제 출처·정직 신뢰도) ──────────────────
AUTH97 = CED("진짜다움이 신뢰의 핵심이라는 동의 97%", "97%",
             src("Ogilvy", "Social Trends 2026"), "단일 조사·표본 미공개·자사 리포트", 0.7)
SYNTH65 = CED("진짜와 합성 콘텐츠 구분 어려움 65%", "65%",
              src("WPP Media", "UK Trends 2026", region="영국"), "영국 한정·단일 출처", 0.7)
BURN42 = CED("덜 최적화된 진정성 갈망 42%", "42%",
             src("WGSN", "Future Consumer 2026"), "소비자 서베이·N 미표기", 0.68)
HUMAN62 = CED("인간 창의팀은 대체 불가 동의 62%", "62%",
              src("", "", tier="T3", year=None), "", 0.5)  # 원본 무출처 → DROP 대상

def main(theme="breeze"):
    DROPPED.clear()
    ch1 = chapter("01", "Ch1 · 변화", "AI가 마케팅의 기본값",
                  "도입은 끝난 논쟁 — 격차는 '얼마나 잘 쓰느냐'로 이동",
                  [{"layout": "bar", "eyebrow": "변화 · 투자 우선순위", "title": "AI는 마케터의 1순위 투자처",
                    "sub": "증액 우선 투자영역 1위 = gen AI", "insight": "1순위지만 이미 기본값 — 차별화는 딴 자리로.",
                    "rows": [{"k": "gen AI", "v": 50}, {"k": "MROI", "v": 42}, {"k": "인사이트", "v": 38},
                             {"k": "디지털", "v": 36}, {"k": "R&D", "v": 28}],
                    "foot": "McKinsey — State of Marketing Europe 2026 [T2·비교·전거]"},
                   {"layout": "cards", "eyebrow": "변화 · AI 역할 이동", "title": "'도구'에서 '실행자'로",
                    "cards": [{"kick": "~2024", "title": "Tool", "body": "파일럿·보조 도구로 시험."},
                              {"kick": "2025", "title": "Integration", "body": "전사 기본 도구로 안착."},
                              {"kick": "2026~", "title": "Agentic", "body": "목표만 받아 집행·측정까지 자율."}]}])

    ch2 = chapter("02", "Ch2 · 역설", "AI가 흔할수록 사람이 비싸짐",
                  "콘텐츠가 무한히 싸지는 시대 — 가장 비싼 자산은 인간 신뢰",
                  [AUTH97, SYNTH65, BURN42, HUMAN62],
                  counterfactual="합성 탐지·워터마크가 표준화돼 '진짜' 구분 비용이 0이 되면 진정성 프리미엄 소멸")

    ch3 = chapter("03", "Ch3 · 지각 변동", "한 변화의 다섯 얼굴",
                  "발견·고객·진정성·팬덤·재투자 — 따로 노는 트렌드가 아니다",
                  [{"layout": "bar", "eyebrow": "① 발견", "unit": "h", "title": "발견 입구가 소셜·숏폼으로",
                    "sub": "SEO에서 GEO(AI 답변 최적화)로", "insight": "입구를 다시 설계해야 한다.",
                    "rows": [{"k": "소셜", "v": 7.1}, {"k": "숏폼", "v": 6.6}, {"k": "스트리밍", "v": 5.0},
                             {"k": "TV", "v": 4.9}, {"k": "기사", "v": 3.0}, {"k": "인쇄", "v": 1.6}],
                    "foot": "GWI — Connecting the Dots 2026 [T2·주간 소비시간·글로벌 평균]"},
                   {"layout": "beforeafter", "eyebrow": "② 고객", "title": "새 고객 = 기계 + 사람, 이중 청중",
                    "before": {"label": "기계 청중", "items": [{"t": "노출", "b": "구조화 데이터·제품 피드(ACO)"},
                                                            {"t": "우선", "b": "읽히는 형식·사실"}]},
                    "after": {"label": "사람 청중", "items": [{"t": "연결", "b": "감정·브랜드 스토리"},
                                                          {"t": "우선", "b": "진정성·신뢰"}]},
                    "foot": "WPP Media — UK Trends 2026 [T2]"},
                   {"layout": "table", "eyebrow": "④ 팬덤", "title": "'팬'은 모든 지표에서 앞선다",
                    "sub": "도달이 아니라 공명이 가치를 만든다", "cols": ["지표", "팬 아님", "팬"],
                    "rows": [["SVOD 가입", "77%", "92%"], ["게이머", "52%", "75%"],
                             ["유료 음악", "40%", "67%"], ["일 미디어(대비)", "기준", "+51분"]],
                    "foot": "Deloitte — 2026 Digital Media Trends [T2]"}],
                  counterfactual="AI 답변이 출처 클릭을 흡수해 GEO가 트래픽으로 안 이어지면 발견 재설계가 헛수고")

    ch4 = chapter("04", "Ch4 · 해자", "인간 신뢰가 복제 불가능한 해자", "AI가 가장 따라 사기 어려운 자산",
                  [{"layout": "agenda", "eyebrow": "다섯이 한 곳으로", "title": "다섯 갈래는 한 곳을 가리킨다",
                    "items": [{"no": "1", "t": "발견", "d": "검색→피드·AI 답변(GEO)"},
                              {"no": "2", "t": "고객", "d": "기계+사람 이중 청중 동시 설계"},
                              {"no": "3", "t": "진정성", "d": "효율은 기본값, 검증 신뢰가 차별값"},
                              {"no": "4", "t": "팬덤", "d": "도달 아닌 공명"},
                              {"no": "5", "t": "재투자", "d": "효율로 번 것을 신뢰에 재투자"}]},
                   {"layout": "beforeafter", "eyebrow": "⑤ 재투자", "title": "효율의 함정 — 절감 아닌 재투자",
                    "before": {"label": "함정 · 절감", "items": [{"t": "결과", "b": "더 싼 commodity 콘텐츠뿐"},
                                                             {"t": "끝", "b": "평준화로 수렴"}]},
                    "after": {"label": "성장 · 재투자", "items": [{"t": "전환", "b": "신뢰·관점·관계에 재투자"},
                                                            {"t": "차별", "b": "자동화 못 만드는 차별화를 산다"}]},
                    "foot": "McKinsey — State of Marketing Europe 2026 [T2]"}])

    ch5 = chapter("05", "Ch5 · 실행", "마케터가 내일부터 바꿀 것", "큰 전략 아니라 이번 분기 실행 단위로",
                  [{"layout": "cards", "eyebrow": "세 레버", "title": "다섯 갈래를 세 레버로",
                    "cards": [{"kick": "01 발견·팬덤", "title": "재설계", "body": "검색 키워드 → GEO·커뮤니티·earned."},
                              {"kick": "02 이중 청중", "title": "분리 설계", "body": "에이전트엔 구조화, 사람엔 감정."},
                              {"kick": "03 진정성·재투자", "title": "루프", "body": "번 시간·예산을 인간 craft에 재투자."}]},
                   {"layout": "funnel", "eyebrow": "운영화", "title": "실험에서 멈추면 효율만 남는다",
                    "steps": ["1. 실험 도입", "2. 전사 통합", "3. 에이전틱 실행", "4. 측정→재투자"]},
                   # B10 Tombstone — 실패한 유사 트렌드
                   {"layout": "statement", "eyebrow": "Tombstone · 묘비명",
                    "title": "'메타버스 마케팅'(2022)도 전 기관이 외쳤다 — 채택 마찰을 못 넘고 소멸"}])

    meta = {"title": "AI는 기본값, 차별화는 증명된 인간다움", "eyebrow": "2026 Marketing Trend · 재생성",
            "thesis": "AI가 마케팅을 평준화하면서, 검증된 인간 신뢰를 유일한 해자로 재편한다",
            "sub": "누구나 AI를 쓰는 시대 — 끝까지 남는 차별화는 '검증된 인간다움'",
            "meta": "TickDeck · 흡수 루프 재생성",
            "closing": {"layout": "closing", "eyebrow": "결론", "title": "AI는 기본값 — 인간 신뢰에 재투자",
                        "bullets": ["단기 — 발견을 GEO·커뮤니티로 재설계",
                                    "중기 — 에이전트엔 구조화, 사람엔 감정으로 분리",
                                    "장기 — 효율을 진정성·커뮤니티에 재투자",
                                    "수치는 단일 기관 '방향 신호' — 파이프라인이 히어로서 강등(아래 로그)"]}}
    sources = [c.source for c in (AUTH97, SYNTH65, BURN42)]  # DROP된 HUMAN62는 refs서도 제외
    slides = assemble(meta, [ch1, ch2, ch3, ch4, ch5], sources, lenses=("counterfactual", "tombstone"))

    html = build_deck(slides, theme=theme, title="2026 마케팅 트렌드 — 흡수 루프 재생성")
    out = pathlib.Path(__file__).with_name(f"out_marketing_v2_{theme}.html")
    out.write_text(html, encoding="utf-8")
    selfcheck(slides, html)
    print(f"OK [{theme}] — {len(slides)}슬라이드 · 레이아웃 {len(set(s['layout'] for s in slides))}종 → {out.name}")
    print(f"DROP({len(DROPPED)}): " + "; ".join(f"{d[0]}(conf{d[1]}·{d[2]})" for d in DROPPED))
    return slides

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "breeze")
