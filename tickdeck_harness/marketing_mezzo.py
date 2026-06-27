#!/usr/bin/env python3
"""2026 커머스·미디어 트렌드 — 후추님 1차 문서(MezzoMedia)로 검증 덱 생성.

소스 = MezzoMedia 2026 Trend Report(로컬 PDF, pdftotext 추출). 우리가 실제로 읽음
→ MezzoMedia 기준 visited_primary=True. 단 MezzoMedia는 광고대행사(T2)고 수치는
통계청·Statista·Salesforce를 '재인용'한 것 → 원출처는 limitation에 명시, 1차 미열람
이므로 빅넘버 승격 안 함. 파이프라인이 출처 강도대로 분류:
  - 통계청 재인용(모바일 76%·DOOH) → 정성(원자료 1차 검증하면 MAIN 승격 가능)
  - Statista 2028 예측 재인용 → 방향 신호(수치 숨김)
  - Salesforce(AI 벤더 자체조사·COI) → DROP
실행: python3 marketing_mezzo.py [theme]
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).with_name("pipeline")))
from dig_schema import DigRecord, validate   # noqa: E402
from ced import CED                            # noqa: E402
from story_mapper import chapter, assemble, chart_block, DROPPED  # noqa: E402
from engine import build_deck, selfcheck      # noqa: E402

Y = 2026
def mezzo(year):  # MezzoMedia를 우리가 읽었으니 visited_primary=True, 단 tier=T2(대행사)
    return DigRecord("", None, "local:MezzoMedia_2026_Trend_Report.pdf", "T2", year,
                     publisher="CJ MezzoMedia", report="2026 Trend Report", visited_primary=True)

# ── CED 풀 (원출처·재인용 정직 명시) ──────────────────────────────
COMMERCE76 = CED("국내 온라인쇼핑 중 모바일 비중", "76%", mezzo(2025),
                 "원출처 통계청 2025·2024 국내·MezzoMedia 재인용(원자료 1차 미열람)", 0.78)
COMMERCE76.source.sample = "2024 온라인쇼핑 259조·모바일 198조"   # 데이터 규모(실수치)
DOOH = CED("디지털 옥외광고(DOOH) 매출 비중", "36%", mezzo(2025),
           "원출처 한국지방재정공제회 2025·옥외 4.6조 중 DOOH 1.7조·재인용", 0.75)
DOOH.source.sample = "2024 옥외 4.6조·DOOH 1.7조"
AISIZE = CED("마케팅 AI 시장 규모 2028 전망", "1,075억$", mezzo(2023),
             "(Proj.)·Statista 2023 재인용·2028 예측치라 불확실", 0.6)
SALESFORCE = CED("기업 마케팅 AI '완벽 도입' 비율", "32%", mezzo(2024),
                 "Salesforce 2024 자체조사·AI 벤더 이해관계(COI)·재인용", 0.55)  # → DROP
SALESFORCE.source.coi = "Salesforce(AI 벤더)"

# 추적→검증→승격 실증: MezzoMedia 259조(광의·근거 미확정)를 폐기하고, 통계청 1차를 직접 확인한 표준 242조로.
_KOSTAT = validate(DigRecord("", None, "https://kostat.go.kr/board.es?bid=241&list_no=434934", "T1", 2025,
                             publisher="통계청", report="2024 온라인쇼핑동향(연간)", sample="전국 전수집계",
                             visited_primary=True), current_year=Y)
ECOM242 = CED("2024 온라인쇼핑 거래액(역대 최대)", "242조", _KOSTAT,
              "통계청 온라인쇼핑동향 표준 기준·본부 1차 확인(2026-06-28). MezzoMedia 259조는 광의 기준·근거 미확정이라 제외", 0.9)


def main(theme="cobalt"):
    DROPPED.clear()
    ch1 = chapter("01", "Ch1 · AI 마케팅", "AI가 광고 운영을 자동화한다",
                  "타겟팅·소재·입찰·측정까지 — 사람이 하던 판단을 AI가 실행",
                  [AISIZE, SALESFORCE,   # 약한 출처 → 방향/DROP
                   {"layout": "cards", "eyebrow": "AI 마케팅 · 3주체", "title": "광고주·매체사·에이전시 모두 AI로",
                    "cards": [{"kick": "광고주", "title": "개인화", "body": "자사 앱서 맞춤 추천·CRM·생성형 SNS 콘텐츠."},
                              {"kick": "매체사", "title": "자동 집행", "body": "구글·메타·네이버·카카오가 집행 자동화 시스템 제공."},
                              {"kick": "에이전시", "title": "솔루션", "body": "기획·제작·플래닝·운영 자동화 툴 개발(예: adly)."}]},
                   {"layout": "cards", "eyebrow": "AI 마케팅 · 자동화 범위", "title": "검색·쇼핑·잠재고객 캠페인 전 자동화",
                    "cards": [{"kick": "검색", "title": "AI Max", "body": "구글 — 노출 키워드 구성·소재 최적화 자동."},
                              {"kick": "쇼핑", "title": "ADVoost", "body": "네이버 — 목표 예산만 세팅, 전환가치 최적화."},
                              {"kick": "잠재고객", "title": "Advantage+", "body": "메타 — 타겟·노출위치·예산 자동 최적화."}]}])

    ch2 = chapter("02", "Ch2 · 발견형 커머스", "검색에서 탐색으로",
                  "목적형 쇼핑(검색)에서 발견형 쇼핑(콘텐츠 중 우연한 발견)으로 패러다임 이동",
                  [chart_block("line",
                       {"eyebrow": "발견형 커머스 · 거래액 추이", "title": "2024년 온라인쇼핑 242조, 역대 최대",
                        "sub": "국내 온라인쇼핑 연간 거래액 (조 원) · 통계청 온라인쇼핑동향(표준 기준)"},
                       {"labels": ["2020", "2021", "2022", "2023", "2024"], "unit": "조",
                        "series": [{"name": "온라인쇼핑 거래액", "values": [159, 193, 210, 227, 242], "accent": True}],
                        "insight": "성장률 +5.8%로 둔화 — 시장은 성숙기, 경쟁은 발견형 점유로 이동한다."},
                       ECOM242),
                   {"layout": "beforeafter", "eyebrow": "발견형 커머스 · 패러다임", "title": "목적형에서 발견형으로",
                    "before": {"label": "목적형(Purposeful)", "items": [
                        {"t": "진입", "b": "필요한 걸 알고 검색창에 상품명 입력"},
                        {"t": "한계", "b": "이미 아는 수요만 회수"}]},
                    "after": {"label": "발견형(Discovery)", "items": [
                        {"t": "진입", "b": "콘텐츠 보다가 몰랐던 관심사 우연 발견"},
                        {"t": "기회", "b": "콘텐츠가 수요를 새로 만든다"}]},
                    "foot": "MezzoMedia 2026 Trend Report [T2]"}])

    ch3 = chapter("03", "Ch3 · DOOH", "디지털 옥외가 성과 매체로",
                  "규제 완화 + 디지털 결합으로 옥외광고가 제2의 전성기",
                  [chart_block("donut",
                       {"eyebrow": "DOOH · 옥외광고 비중", "title": "디지털 옥외가 옥외광고의 3분의 1"},
                       {"value": 36, "center": "DOOH 비중",
                        "aux": [{"label": "2024 전체 옥외광고", "value": "4.6조"}, {"label": "DOOH 매출", "value": "1.7조"},
                                {"label": "전년比 DOOH 성장", "value": "+16%"}]},
                       DOOH),
                   {"layout": "cards", "eyebrow": "DOOH · 진화", "title": "주목도 높은 옥외 + 디지털 기술",
                    "cards": [{"kick": "착시", "title": "임팩트", "body": "대형 매체에 튀어나오는 듯한 3D 착시로 시선 장악."},
                              {"kick": "상호작용", "title": "QR 연결", "body": "QR로 소비자와 실시간 상호작용·온라인 연계."},
                              {"kick": "성과형", "title": "측정", "body": "노출에서 멈추지 않고 성과형 매체로 발전."}]}])

    meta = {"title": "AI는 운영을 자동화하고, 시장 무게는 발견·옥외로 이동한다",
            "eyebrow": "2026 커머스·미디어 트렌드 · 검증 재생성",
            "thesis": "AI가 광고 운영을 자동화하는 동안, 검증 가능한 시장 무게는 발견형 모바일 커머스와 디지털 옥외(DOOH)로 옮겨간다",
            "sub": "후추님 1차 문서(MezzoMedia 2026 Trend Report)를 검증 파이프라인으로 재생성",
            "meta": "TickDeck · 내 자료 → 검증 덱",
            "closing": {"layout": "closing", "eyebrow": "결론", "title": "재인용 수치는 정성으로, 구조 변화는 또렷하게",
                        "bullets": ["AI 마케팅 시장 = Statista 예측 재인용 → 방향 신호로만(수치 숨김)",
                                    "모바일 76%·DOOH = 통계청·공제회 재인용 → 정성(원자료 1차 검증 시 빅넘버 승격)",
                                    "Salesforce 도입률 = 벤더 자체조사(COI) → 제외",
                                    "구조 변화(자동화·발견형·옥외)는 출처 무관 일관 → 내러티브로 확정"]}}
    sources = [COMMERCE76.source, DOOH.source, AISIZE.source]   # DROP된 Salesforce 제외
    slides = assemble(meta, [ch1, ch2, ch3], sources, lenses=())

    html = build_deck(slides, theme=theme, title="2026 커머스·미디어 트렌드 — 검증 재생성")
    out = pathlib.Path(__file__).with_name(f"out_mezzo_{theme}.html")
    out.write_text(html, encoding="utf-8")
    selfcheck(slides, html)
    print(f"OK [{theme}] — {len(slides)}슬라이드 · 레이아웃 {len(set(s['layout'] for s in slides))}종 → {out.name}")
    from ced import route
    for n, c in [("모바일76(통계청재인용)", COMMERCE76), ("DOOH(공제회재인용)", DOOH),
                 ("AI시장(Statista예측)", AISIZE), ("Salesforce(벤더COI)", SALESFORCE)]:
        print(f"  {n:24} → {route(c)}")
    print(f"  DROP: {[d[0] for d in DROPPED]}")
    return slides

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "cobalt")
