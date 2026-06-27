#!/usr/bin/env python3
"""2026 디지털 마케팅 트렌드 — Deloitte 1차 문서로 검증 덱 생성.

소스 = Deloitte Digital Marketing Trends 2026(후추님 로컬 PDF, 우리가 직접 읽음).
재인용 아님 — Deloitte 자체 설문(N=1,854 EMEA 임원·CMO Survey 2025·소비자 설문).
→ visited_primary=True + 방법론 공개 → N 공개 수치는 MAIN(빅넘버) 승격.
이게 흔들리던 흡수-전 덱(Ogilvy/WPP/WGSN 재인용)의 정공법 대체.
실행: python3 marketing_dmt2026.py [theme]
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).with_name("pipeline")))
from dig_schema import DigRecord            # noqa: E402
from ced import CED, route                  # noqa: E402
from story_mapper import chapter, assemble, DROPPED  # noqa: E402
from engine import build_deck, selfcheck    # noqa: E402

def dl(year=2026):  # Deloitte 1차·우리가 PDF 직접 읽음 → visited_primary
    return DigRecord("", None, "local:deloitte-digital-marketing-trends-2026.pdf", "T2", year,
                     publisher="Deloitte", report="Digital Marketing Trends 2026", visited_primary=True)

# ── CED 풀 (전부 Deloitte 1차·출처/표본 명시) ──────────────────────
def ced(claim, metric, sample, conf, limit):
    s = dl(); s.sample = sample
    return CED(claim, metric, s, limit, conf)

AGENTIC10 = ced("유의미한 ROI를 내는 agentic AI 조직", "10%",
                "N=1,854 EMEA 임원·Deloitte 2025 설문", 0.88, "EMEA 임원 한정·2025")          # MAIN
INVEST85  = ced("지난 12개월 AI 투자를 늘린 조직", "85%",
                "N=1,854 동일 설문·추가 증액 계획 91%·ROI 2~4년 소요", 0.86, "EMEA·ROI 회수 2~4년")  # MAIN
TRUST42   = ced("기업의 윤리적 AI 사용을 신뢰하는 소비자", "42%",
                "Deloitte 소비자 설문 2025", 0.83, "신뢰 갭 — AI 흔할수록 신뢰가 차별값")          # QUAL
DISCOVER60= ced("브랜드 발견에 소셜·추천·커뮤니티가 영향", "60%",
                "Deloitte 설문·검색은 사후 검증용으로 이동", 0.83, "도달(reach) 아닌 적합성(relevance)")  # QUAL
CMO64     = ced("'마케팅 가치 증명'이 최대 과제라는 CMO", "64%",
                "Deloitte CMO Survey 2025", 0.82, "통제·자원 없이 성장 요구받는 CMO")              # QUAL
MARTECH18 = ced("MarTech>워킹미디어 투자 조직의 추가 매출 상승", "18%",
                "Deloitte·매출 18%↑·전체 매출성장 7%↑", 0.80, "투자 배분 효과·인과 단정 아님")        # QUAL


def main(theme="breeze"):
    DROPPED.clear()
    ch1 = chapter("01", "Ch1 · 소비자", "도달이 아니라 적합성", "검색 전에 콘텐츠·추천·커뮤니티로 브랜드를 발견한다",
                  [DISCOVER60,
                   {"layout": "beforeafter", "eyebrow": "소비자 · 발견의 이동", "title": "검색에서 발견으로",
                    "before": {"label": "기존 · 도달(Reach)", "items": [
                        {"t": "경로", "b": "필요를 알고 검색창에 직접 입력"},
                        {"t": "한계", "b": "이미 존재하는 수요만 회수"}]},
                    "after": {"label": "지금 · 적합성(Relevance)", "items": [
                        {"t": "경로", "b": "소셜·크리에이터·또래 영향으로 먼저 노출"},
                        {"t": "기회", "b": "콘텐츠가 발견을 만들고 검색은 검증으로"}]},
                    "foot": "Deloitte Digital Marketing Trends 2026 [T2·1차 설문]"}])

    ch2 = chapter("02", "Ch2 · AI의 다섯 진실", "AI는 흔하지만 과대단순화됐다", "Deloitte가 정리한 마케팅 AI의 다섯 진실",
                  [AGENTIC10,
                   {"layout": "cards", "eyebrow": "AI · 다섯 진실", "title": "효율은 실현, 신뢰·가치는 미실현",
                    "cards": [{"kick": "01 비용", "title": "제작비 붕괴", "body": "카피 +200%·수작업 디자인 -60%·이미지 단가 €45→€4-6."},
                              {"kick": "02 신뢰", "title": "초개인화 양날", "body": "전환 2.9% vs 0.5%·CTR 3.4% vs 1.8%, 그러나 신뢰는 흔들림."},
                              {"kick": "03 실행", "title": "대부분 미실현", "body": "agentic AI로 유의미 ROI는 10%뿐 — 조직·통제층 부재."}]},
                   INVEST85,
                   TRUST42,
                   {"layout": "cards", "eyebrow": "AI · GenAI 효과", "title": "검증된 유스케이스 업리프트",
                    "cards": [{"kick": "속도", "title": "100X", "body": "콘텐츠 제작 속도 — GenAI 적용 시."},
                              {"kick": "매출", "title": "+48%", "body": "우선 고객군 포착으로 매출 성장."},
                              {"kick": "효율", "title": "+36%", "body": "오디언스·여정 최적화로 시간 절감. (출처: Deloitte Analysis 2025)"}]}])

    ch3 = chapter("03", "Ch3 · CMO & 실행", "통제 없이 성장을 요구받는 CMO", "그래서 MarTech 투자로 시스템을 먼저 세운다",
                  [CMO64, MARTECH18,
                   {"layout": "cards", "eyebrow": "실행 · 우선순위", "title": "지금 분기에 손댈 세 가지",
                    "cards": [{"kick": "01 적합성", "title": "발견 재설계", "body": "검색 키워드 → 소셜·추천·커뮤니티 노출로 입구 이동."},
                              {"kick": "02 신뢰", "title": "윤리 가드레일", "body": "초개인화에 투명성·동의·브랜드 안전을 함께(신뢰 42% 갭)."},
                              {"kick": "03 시스템", "title": "MarTech 우선", "body": "워킹미디어보다 MarTech에 — 매출 리프트 18%·성장 7%."}]}])

    meta = {"title": "AI는 깔렸다 — 우위는 적합성·신뢰·실행으로 간다",
            "eyebrow": "2026 Digital Marketing Trends · 검증 재생성",
            "thesis": "AI가 마케팅에 보편화될수록, 우위는 도달이 아니라 검증된 적합성·신뢰·조직 실행으로 이동한다",
            "sub": "후추님 1차 문서(Deloitte Digital Marketing Trends 2026)를 검증 파이프라인으로 재생성 — 단일 권위 1차 설문",
            "meta": "TickDeck · 내 자료 → 검증 덱",
            "closing": {"layout": "closing", "eyebrow": "결론", "title": "흔한 AI 위에서, 검증된 차별값에 투자",
                        "bullets": ["발견은 도달→적합성 — 소셜·추천·커뮤니티로 입구 재설계",
                                    "AI는 효율은 실현했으나 ROI는 10%·신뢰는 42% — 차별값은 신뢰·실행",
                                    "CMO 64%가 '가치 증명'이 과제 — MarTech 투자가 매출 18%·성장 7%로 회수",
                                    "전 수치 단일 1차 출처(Deloitte 설문·N=1,854 등) — 재인용 아님"]}}
    sources = [AGENTIC10.source]   # 동일 문서라 refs 1개로 충분(중복 제거)
    slides = assemble(meta, [ch1, ch2, ch3], sources, lenses=())

    html = build_deck(slides, theme=theme, title="2026 디지털 마케팅 트렌드 — Deloitte 1차 검증")
    out = pathlib.Path(__file__).with_name(f"out_dmt2026_{theme}.html")
    out.write_text(html, encoding="utf-8")
    selfcheck(slides, html)
    print(f"OK [{theme}] — {len(slides)}슬라이드 · 레이아웃 {len(set(s['layout'] for s in slides))}종 → {out.name}")
    for n, c in [("agentic10(N=1,854)", AGENTIC10), ("invest85(N=1,854)", INVEST85),
                 ("trust42", TRUST42), ("discover60", DISCOVER60), ("cmo64", CMO64), ("martech18", MARTECH18)]:
        print(f"  {n:22} → {route(c)}")
    print(f"  DROP: {[d[0] for d in DROPPED]}")
    return slides

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "breeze")
