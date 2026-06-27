#!/usr/bin/env python3
"""2026 마케팅 트렌드 — 종합 검증 덱 (제대로 판).

처음 21p(흡수 전·Ogilvy/WPP/WGSN 재인용)를 폐기하고, 검증 파이프라인 +
메조급 차트로 재구성. 두 1차 문서를 출처 강도대로 합침:
  - Deloitte Digital Marketing Trends 2026 (1차 설문·N=1,854) → 깨끗한 MAIN/statgrid
  - MezzoMedia 2026 Trend Report (통계청·공제회 재인용) → 차트에 '방향·약출처' 캐비엇
관통 명제: AI가 마케팅 실행을 자동화할수록, 차별화는 검증된 적합성·신뢰·발견으로 이동한다.
실행: python3 marketing_2026.py [theme]
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).with_name("pipeline")))
import marketing_dmt2026 as D                       # noqa: E402  Deloitte CED 재사용
import marketing_mezzo as M                          # noqa: E402  MezzoMedia CED 재사용
from story_mapper import chapter, assemble, chart_block, DROPPED  # noqa: E402
from engine import build_deck, selfcheck             # noqa: E402

DELO = "Deloitte Digital Marketing Trends 2026 [T2·1차]"


def main(theme="breeze"):
    DROPPED.clear()

    ch1 = chapter("01", "Ch1 · 변화", "AI가 마케팅의 기본값", "도입은 끝난 논쟁 — AI는 광고 실행을 자동화하고, 과대단순화됐다",
                  [M.AISIZE,   # Statista 2028 예측 재인용 → 방향 신호(수치 숨김)
                   {"layout": "cards", "eyebrow": "변화 · 3주체 자동화", "title": "광고주·매체사·에이전시 모두 AI로",
                    "cards": [{"kick": "광고주", "title": "개인화", "body": "자사 앱 맞춤 추천·CRM·생성형 SNS 콘텐츠."},
                              {"kick": "매체사", "title": "자동 집행", "body": "구글·메타·네이버·카카오가 집행 자동화 제공."},
                              {"kick": "에이전시", "title": "솔루션", "body": "기획·제작·플래닝·운영 자동화 툴(예: adly)."}]}])

    ch2 = chapter("02", "Ch2 · 소비자", "도달이 아니라 적합성", "검색 전에 콘텐츠·추천·커뮤니티로 발견하고, 지출은 신중해진다",
                  [{"layout": "statgrid", "eyebrow": "소비자 · 설문 수치", "title": "발견은 적합성으로, 지출은 신중하게",
                    "sub": "Deloitte 소비자 설문 — 행동 변화의 네 신호",
                    "stats": [{"label": "소셜·추천·커뮤니티가 발견에 영향", "value": "60%", "dir": "up"},
                              {"label": "재량 카테고리 지출 축소", "value": "40%", "dir": "down"},
                              {"label": "CX 강한 브랜드의 만족·전환 개선", "value": "20%", "dir": "up"},
                              {"label": "개인화로 인식되는 상호작용", "value": "43%", "note": "노력-인식 갭"}],
                    "foot": "Deloitte analysis of survey data, 2025 [T2·1차]"},
                   chart_block("line",
                       {"eyebrow": "소비자 · 커머스 성숙", "title": "2024년 온라인쇼핑 242조, 역대 최대",
                        "sub": "국내 온라인쇼핑 연간 거래액 (조 원) · 통계청 온라인쇼핑동향(표준 기준·본부 1차 확인)"},
                       {"labels": ["2020", "2021", "2022", "2023", "2024"], "unit": "조",
                        "series": [{"name": "온라인쇼핑 거래액", "values": [159, 193, 210, 227, 242], "accent": True}],
                        "insight": "성장률 +5.8%로 둔화 — 시장 성숙기, 경쟁은 발견형 점유로 이동한다."},
                       M.ECOM242),
                   {"layout": "beforeafter", "eyebrow": "소비자 · 패러다임", "title": "목적형에서 발견형으로",
                    "before": {"label": "목적형(Reach)", "items": [{"t": "경로", "b": "필요를 알고 검색창에 입력"},
                                                                {"t": "한계", "b": "이미 존재하는 수요만 회수"}]},
                    "after": {"label": "발견형(Relevance)", "items": [{"t": "경로", "b": "콘텐츠·추천·또래로 먼저 노출"},
                                                                  {"t": "기회", "b": "콘텐츠가 수요를 새로 만든다"}]},
                    "foot": DELO}])

    ch3 = chapter("03", "Ch3 · AI의 진실", "효율은 실현, 신뢰·가치는 미실현", "Deloitte가 정리한 마케팅 AI의 다섯 진실 — N=1,854",
                  [D.AGENTIC10,   # 빅넘버 히어로(1차)
                   {"layout": "cards", "eyebrow": "AI · 다섯 진실", "title": "효율은 실현, 신뢰·가치는 미실현",
                    "cards": [{"kick": "01 비용", "title": "제작비 붕괴", "body": "카피 +200%·수작업 디자인 -60%·이미지 €45→€4-6."},
                              {"kick": "02 신뢰", "title": "초개인화 양날", "body": "전환 2.9% vs 0.5%·CTR 3.4% vs 1.8%, 그러나 신뢰는 흔들림."},
                              {"kick": "03 실행", "title": "대부분 미실현", "body": "agentic ROI 10%뿐 — 조직·통제층 부재. ROI 회수 2~4년."}]},
                   {"layout": "statgrid", "eyebrow": "AI · GenAI 업리프트", "title": "검증된 유스케이스 효과",
                    "sub": "Deloitte Analysis 2025 — GenAI 적용 시 측정된 향상",
                    "stats": [{"label": "매출 성장(우선 고객군)", "value": "+48%", "dir": "up"},
                              {"label": "콘텐츠 제작 속도", "value": "100X", "dir": "up"},
                              {"label": "아티클 개발 속도", "value": "300X", "dir": "up"},
                              {"label": "개인화 CTR", "value": "+50%", "dir": "up"},
                              {"label": "오디언스·여정 시간 절감", "value": "+36%", "dir": "up"}],
                    "foot": "Deloitte Analysis 2025 [T2·1차]"},
                   D.TRUST42])   # 신뢰 갭(1차)

    ch4 = chapter("04", "Ch4 · 채널", "발견 입구와 옥외의 부상", "검색에서 피드·AI 답변(GEO)으로, 옥외는 디지털로 성과 매체화",
                  [chart_block("donut",
                       {"eyebrow": "채널 · DOOH 비중", "title": "디지털 옥외가 옥외광고의 3분의 1"},
                       {"value": 36, "center": "DOOH 비중",
                        "aux": [{"label": "2024 전체 옥외광고", "value": "4.6조"}, {"label": "DOOH 매출", "value": "1.7조"},
                                {"label": "전년比 DOOH 성장", "value": "+16%"}]},
                       M.DOOH),
                   {"layout": "cards", "eyebrow": "채널 · 입구 이동", "title": "발견의 입구가 다시 설계된다",
                    "cards": [{"kick": "검색→GEO", "title": "AI 답변", "body": "SEO에서 GEO로 — AI 답변에 읽히게 구조화."},
                              {"kick": "피드·커뮤니티", "title": "발견형", "body": "소셜·숏폼·커뮤니티가 첫 접점."},
                              {"kick": "DOOH", "title": "성과 옥외", "body": "착시·QR 상호작용으로 노출→성과 매체화."}]}])

    ch5 = chapter("05", "Ch5 · CMO & 실행", "통제 없이 성장을 요구받는 CMO", "그래서 MarTech·신뢰에 먼저 투자한다",
                  [{"layout": "statgrid", "eyebrow": "CMO · 새 현실", "title": "성장은 요구받고, 통제는 없다",
                    "sub": "Deloitte CMO Survey 2025 — 마케팅 리더의 네 현실",
                    "stats": [{"label": "수익성 우선 CMO", "value": "33%", "delta": "C레벨 67%", "dir": "down", "note": "전사 대비 절반"},
                              {"label": "최대 과제 = 가치 증명", "value": "64%", "dir": "up"},
                              {"label": "AI 쓰는 마케팅 활동", "value": "1/6", "delta": "3년 내 2배+", "dir": "up"},
                              {"label": "인재 확보가 최대 난제", "value": "62%", "note": "외부 적임자"}],
                    "foot": "Deloitte CMO Survey 2025 [T2·1차]"},
                   D.MARTECH18,
                   {"layout": "cards", "eyebrow": "실행 · 세 레버", "title": "지금 분기에 손댈 세 가지",
                    "cards": [{"kick": "01 적합성", "title": "발견 재설계", "body": "검색 키워드 → 소셜·추천·커뮤니티·GEO."},
                              {"kick": "02 신뢰", "title": "윤리 가드레일", "body": "초개인화에 투명성·동의·브랜드 안전(신뢰 42% 갭)."},
                              {"kick": "03 시스템", "title": "MarTech 우선", "body": "워킹미디어보다 MarTech에 — 매출 18%·성장 7%."}]}])

    meta = {"title": "AI는 기본값 — 차별화는 검증된 적합성·신뢰·발견으로",
            "eyebrow": "2026 마케팅 트렌드 · 종합 검증판",
            "thesis": "AI가 마케팅 실행을 자동화할수록, 차별화는 검증된 적합성·신뢰·발견으로 이동한다",
            "sub": "Deloitte 1차 설문 + MezzoMedia 채널 데이터를 검증 파이프라인으로 합성 — 출처 강도대로 빅넘버/방향 신호 분리",
            "meta": "TickDeck · 검증 + 메조급 출력",
            "closing": {"layout": "closing", "eyebrow": "결론", "title": "흔한 AI 위에서, 검증된 차별값에 투자",
                        "bullets": ["발견은 도달→적합성 — 소셜·추천·커뮤니티·GEO로 입구 재설계",
                                    "AI 효율은 실현됐으나 ROI 10%·신뢰 42% — 차별값은 신뢰·실행",
                                    "채널은 모바일 발견형·DOOH로 무게 이동(통계청·공제회 방향 신호)",
                                    "CMO 64%가 '가치 증명'이 과제 — MarTech 투자가 매출 18%로 회수",
                                    "Deloitte 수치 = 1차 검증(빅넘버) · 재인용 = 방향 신호로 분리 표기"]}}
    sources = [D.AGENTIC10.source, M.COMMERCE76.source]   # Deloitte 1차 + Mezzo 경유 통계
    slides = assemble(meta, [ch1, ch2, ch3, ch4, ch5], sources, lenses=())

    html = build_deck(slides, theme=theme, title="2026 마케팅 트렌드 — 종합 검증판")
    out = pathlib.Path(__file__).with_name(f"out_marketing_2026_{theme}.html")
    out.write_text(html, encoding="utf-8")
    selfcheck(slides, html)
    print(f"OK [{theme}] — {len(slides)}슬라이드 · 레이아웃 {len(set(s['layout'] for s in slides))}종 → {out.name}")
    print(f"  DROP: {[d[0] for d in DROPPED]}")
    return slides


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "breeze")
