#!/usr/bin/env python3
"""2026 마케팅 트렌드 보고서 — 원본 기반 내용정리·스토리·페이지구성 (꽉꽉).
스토리: AI는 기본값 → AI 흔할수록 사람이 비싸짐(역설) → 5개 지각변동 →
        다섯이 한 곳(인간 신뢰=해자)으로 수렴 → 내일부터 실행.
실행: python3 marketing_full.py  →  out_marketing.html / .pdf
"""
import pathlib
from engine import build_deck, selfcheck

SLIDES = [
    {"layout": "cover", "eyebrow": "2026 Marketing Trend",
     "title": "AI는 기본값, 차별화는 증명된 인간다움",
     "sub": "누구나 AI를 쓰는 시대 — 끝까지 남는 차별화는 '검증된 인간다움'이다."},

    {"layout": "statement", "eyebrow": "한 줄 요지",
     "title": "AI가 흔할수록, 사람이 비싸진다"},

    {"layout": "agenda", "eyebrow": "목차 · Agenda",
     "title": "AI가 기본이 된 시대, 차별화는 어디서 오는가",
     "items": [{"no": "01", "t": "변화", "d": "AI가 마케팅의 기본값 — 도입은 끝난 논쟁"},
               {"no": "02", "t": "역설", "d": "AI가 흔할수록 사람이 비싸짐"},
               {"no": "03", "t": "지각 변동", "d": "발견 · 고객 · 진정성 · 팬덤 · 재투자"},
               {"no": "04", "t": "해자", "d": "다섯은 한 곳 — 인간 신뢰가 유일한 해자"},
               {"no": "05", "t": "실행", "d": "마케터가 내일부터 바꿀 것"}]},

    {"layout": "divider", "num": "01", "eyebrow": "Chapter 01 · 변화 (The Shift)",
     "title": "AI가 마케팅의 기본값", "sub": "도입 여부는 끝난 논쟁 — 격차는 '얼마나 잘 쓰느냐'로 이동했다"},

    {"layout": "bar", "eyebrow": "변화 · 투자 우선순위",
     "title": "AI는 마케터의 1순위 투자처",
     "sub": "올해 '증액 우선 투자영역' 1위가 gen AI — 남은 건 '얼마나 잘 쓰느냐'",
     "rows": [{"k": "gen AI", "v": 50}, {"k": "MROI", "v": 42}, {"k": "인사이트", "v": 38},
              {"k": "디지털", "v": 36}, {"k": "R&D", "v": 28}],
     "insight": "gen AI가 1순위지만 이미 '기본값'이다. 차별화는 다른 자리로 이동한다.",
     "foot": "출처: McKinsey — State of Marketing Europe 2026"},

    {"layout": "cards", "eyebrow": "변화 · AI의 역할 이동",
     "title": "'도구'에서 '실행자'로",
     "cards": [{"kick": "~2024 실험", "title": "Tool", "body": "파일럿·부분 도입 — 생성형 AI를 보조 도구로 시험."},
               {"kick": "2025 통합", "title": "Integration", "body": "콘텐츠·캠페인 전반의 기본 도구로 전사 안착."},
               {"kick": "2026~ 에이전틱", "title": "Agentic", "body": "목표만 받아 타기팅·집행·측정까지 자율 수행."}]},

    {"layout": "divider", "num": "02", "eyebrow": "Chapter 02 · 역설 (The Paradox)",
     "title": "AI가 흔할수록 사람이 비싸짐", "sub": "콘텐츠가 무한히 싸지는 시대 — 가장 비싼 자산은 인간의 신뢰"},

    {"layout": "kpi", "eyebrow": "역설 · 진정성 프리미엄",
     "title": "AI가 흔할수록, 진정성이 비싸진다",
     "sub": "콘텐츠가 무한히 싸지는 시대 — 검증 가능한 '진짜'가 프리미엄이 된다",
     "value": "97%", "delta": "'진짜다움'이 신뢰의 핵심이라는 동의",
     "aux": [{"label": "진짜와 합성 콘텐츠, 구분 어려움 (영국)", "value": "65%"},
             {"label": "소비자 번아웃 — '덜 최적화된 진정성' 갈망", "value": "42%"},
             {"label": "신뢰 확보 방향", "value": "스토리텔링 → 증명"}],
     "foot": "출처: WPP Media · Ogilvy Social Lab · WGSN 2026"},

    {"layout": "divider", "num": "03", "eyebrow": "Chapter 03 · 지각 변동 (Seismic Shifts)",
     "title": "한 변화의 다섯 얼굴", "sub": "발견 · 고객 · 진정성 · 팬덤 · 재투자 — 따로 노는 트렌드가 아니다"},

    {"layout": "bar", "eyebrow": "지각 변동 · ① 발견", "unit": "h",
     "title": "발견의 입구가 소셜·숏폼으로",
     "sub": "첫 접점이 피드로 이동 — SEO에서 GEO(AI 답변 최적화)로",
     "rows": [{"k": "소셜미디어", "v": 7.1}, {"k": "숏폼 영상", "v": 6.6}, {"k": "스트리밍", "v": 5.0},
              {"k": "방송 TV", "v": 4.9}, {"k": "온라인 기사", "v": 3.0}, {"k": "인쇄", "v": 1.6}],
     "insight": "발견이 검색에서 피드·AI 답변으로 옮겨갔다. SEO → GEO로 입구를 다시 설계해야 한다.",
     "foot": "출처: GWI — Connecting the Dots 2026 (주간 소비 시간, 글로벌 평균)"},

    {"layout": "beforeafter", "eyebrow": "지각 변동 · ② 고객",
     "title": "새 고객은 기계 + 사람, 이중 청중",
     "before": {"label": "기계 청중 · 구조화", "items": [
         {"t": "노출", "b": "구조화 데이터·제품 피드(ACO)로 에이전트에 읽힘"},
         {"t": "우선", "b": "읽히는 형식·사실적 정보가 먼저"}]},
     "after": {"label": "사람 청중 · 감정", "items": [
         {"t": "연결", "b": "감정·브랜드 스토리로 사람을 움직임"},
         {"t": "우선", "b": "진정성·신뢰가 먼저"}]},
     "foot": "출처: WPP Media — UK Trends 2026"},

    {"layout": "cards", "eyebrow": "지각 변동 · ③ 진정성",
     "title": "기본값은 효율, 차별값은 인간",
     "cards": [{"kick": "AI가 푸는 것", "title": "기본값", "body": "효율(제작·운영 속도/규모)·개인화(대규모 자동화). 모두가 가져 차별화가 안 됨."},
               {"kick": "사람이 버는 것", "title": "차별값 62%", "body": "'인간 창의팀은 대체 불가' 동의 62% — 진정성·창의·공감이 자동화를 능가."},
               {"kick": "소비자 방향", "title": "번아웃 42%", "body": "사실·투명성 요구 / 42%가 '덜 최적화된 진정성'을 갈망."}]},

    {"layout": "table", "eyebrow": "지각 변동 · ④ 팬덤",
     "title": "'팬'은 모든 지표에서 앞선다",
     "sub": "팬덤은 감성이 아니라 수치 — 도달이 아니라 공명이 가치를 만든다",
     "cols": ["지표", "팬 아님", "팬"],
     "rows": [["SVOD(유료 스트리밍) 가입", "77%", "92%"], ["게이머 비율", "52%", "75%"],
              ["유료 음악 스트리밍 가입", "40%", "67%"], ["일 미디어 소비 (대비)", "기준", "+51분 (16%)"]],
     "foot": "출처: Deloitte — 2026 Digital Media Trends"},

    {"layout": "beforeafter", "eyebrow": "지각 변동 · ⑤ 재투자",
     "title": "효율의 함정 — 절감이 아니라 재투자",
     "before": {"label": "함정 · 절감", "items": [
         {"t": "결과", "b": "효율을 비용 절감에만 쓰면 더 싼 commodity 콘텐츠뿐"},
         {"t": "끝", "b": "남보다 싸고 많은 '평준화' 콘텐츠로 수렴"}]},
     "after": {"label": "성장 · 재투자", "items": [
         {"t": "전환", "b": "효율로 번 자원을 신뢰·관점·관계에 재투자"},
         {"t": "차별", "b": "자동화가 못 만드는 차별화를 산다"}]},
     "foot": "출처: McKinsey — State of Marketing Europe 2026"},

    {"layout": "divider", "num": "04", "eyebrow": "Chapter 04 · 해자 (The Moat)",
     "title": "인간 신뢰가 유일한 해자", "sub": "AI가 못 사는 단 하나의 자산"},

    {"layout": "agenda", "eyebrow": "해자 · 다섯이 한 곳으로",
     "title": "다섯 갈래는 한 곳을 가리킨다",
     "sub": "따로 노는 트렌드가 아니라 한 변화의 다섯 얼굴 — 결국 인간 신뢰가 유일한 해자",
     "items": [{"no": "1", "t": "발견 · 새 유통", "d": "검색에서 피드·AI 답변(GEO)으로 입구가 이동"},
               {"no": "2", "t": "고객 · 최종 결정자", "d": "기계+사람 이중 청중을 분리해 동시 설계"},
               {"no": "3", "t": "진정성 · 차별화 통화", "d": "효율은 기본값, 검증된 신뢰가 차별값"},
               {"no": "4", "t": "팬덤 · retention 엔진", "d": "도달이 아니라 공명 — 팬이 가치를 만듦"},
               {"no": "5", "t": "재투자 · 성장 승수", "d": "효율로 번 것을 인간 신뢰에 재투자"}]},

    {"layout": "cards", "eyebrow": "해자 · 왜 신뢰인가",
     "title": "차별화는 '살 수 없는 것'에서만 남는다",
     "cards": [{"kick": "효율은 평준화", "title": "기본값", "body": "AI가 콘텐츠·캠페인·실행을 평준화 — 효율·개인화는 모두의 것."},
               {"kick": "신뢰 = 대체불가", "title": "경쟁우위", "body": "'AI가 살 수 없는 것' — 신뢰·진정성·커뮤니티로 우위 이동."},
               {"kick": "재투자 루프", "title": "성장 승수", "body": "효율로 번 시간·예산을 인간 신뢰에 재투자하는 자가 2026을 가져감."}]},

    {"layout": "divider", "num": "05", "eyebrow": "Chapter 05 · 실행 (What To Do)",
     "title": "마케터가 내일부터 바꿀 것", "sub": "큰 전략이 아니라 이번 분기에 손댈 실행 단위로"},

    {"layout": "cards", "eyebrow": "실행 · 세 레버",
     "title": "다섯 갈래를 세 레버로",
     "cards": [{"kick": "01 발견·팬덤", "title": "재설계", "body": "검색 키워드 → AI 답변(GEO)·커뮤니티·earned 노출. 팬의 '그룹챗 공유'를 콘텐츠 기준으로."},
               {"kick": "02 이중 청중", "title": "분리 설계", "body": "에이전트엔 구조화 데이터·피드(ACO), 사람엔 감정·브랜드 스토리. 둘을 동시에."},
               {"kick": "03 진정성·재투자", "title": "루프", "body": "AI로 번 시간·예산을 더 싼 콘텐츠가 아니라 진정성·커뮤니티·인간 craft에 재투자."}]},

    {"layout": "funnel", "eyebrow": "실행 · 운영화",
     "title": "실험에서 멈추면 효율만 남는다",
     "sub": "측정·재투자까지 올라가야 차별화가 회수된다 — 네 단계의 상승",
     "steps": ["1. 실험적 도입 — AI 유스케이스 인벤토리", "2. 전사 통합 — 제품 피드·스키마 audit",
               "3. 에이전틱 실행 — 에이전트 플레이북", "4. 측정 → 재투자 — proof asset 라이브러리"]},

    {"layout": "closing", "eyebrow": "결론",
     "title": "AI는 기본값 — 이제 인간 신뢰에 재투자",
     "bullets": ["단기 — 발견을 GEO·커뮤니티로 재설계",
                 "중기 — 에이전트엔 구조화, 사람엔 감정으로 분리",
                 "장기 — 효율을 진정성·커뮤니티에 재투자 체계화",
                 "수치는 기관별로 갈리는 '방향 신호' — 방향은 전 출처 일관"]},

    {"layout": "refs", "eyebrow": "참고자료 · Sources",
     "title": "근거 출처",
     "refs": [{"s": "GWI — Connecting the Dots 2026", "t": "미디어·발견 p9"},
              {"s": "KPMG — Global Tech Report 2026", "t": "AI 성숙도"},
              {"s": "Deloitte Digital — Marketing Trends 2026", "t": "배경"},
              {"s": "AMA — 2026 Future Trends in Marketing", "t": "흐름·실행"},
              {"s": "WPP Media — UK Trends 2026", "t": "이중 청중 p10"},
              {"s": "Ogilvy Social Lab — Social Trends 2026", "t": "진정성 p7"},
              {"s": "McKinsey — State of Marketing Europe 2026", "t": "효율·재투자"},
              {"s": "Deloitte — 2026 Digital Media Trends", "t": "팬덤 LTV p12"},
              {"s": "PwC — Marketing in the AI Era", "t": "배경"},
              {"s": "WGSN — Future Consumer 2026", "t": "진정성 p11"},
              {"s": "HubSpot — 2026 State of Marketing Report", "t": "배경 리서치"},
              {"s": "Kantar — Marketing Trends 2026", "t": "배경 리서치"},
              {"s": "Gartner · Forrester · eMarketer", "t": "추가 참조"},
              {"s": "Nielsen · Statista · BCG · Accenture · IDC", "t": "배경 리서치"}]},
]

if __name__ == "__main__":
    import sys
    theme = sys.argv[1] if len(sys.argv) > 1 else "brass"
    html = build_deck(SLIDES, theme=theme, title="2026 마케팅 트렌드 — 완성본")
    out = pathlib.Path(__file__).with_name(f"out_marketing_{theme}.html")
    out.write_text(html, encoding="utf-8")
    selfcheck(SLIDES, html)
    print(f"OK [{theme}] — {len(SLIDES)}슬라이드 · 레이아웃 {len(set(s['layout'] for s in SLIDES))}종 · 원문자0 · 3연속없음 → {out.name}")
