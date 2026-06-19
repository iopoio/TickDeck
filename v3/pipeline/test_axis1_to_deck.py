#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import axis1_to_deck


def sample_page_specs() -> dict:
    return {
        "topic": "2026 마케팅 트렌드",
        "governing_thought_short": "AI가 마케팅 운영체제를 바꾼다",
        "pages": [
            {
                "page_no": 1,
                "role": "cover",
                "section_id": None,
                "section_nav": "",
                "headline": "AI가 마케팅 운영체제를 바꾸는 해",
                "takeaways": ["검색·제작·측정이 AI 중심으로 재배열된다", "브랜드 신뢰가 성과의 병목이 된다"],
                "content_kind": "narrative",
                "payload": {"paragraphs": ["표지 메시지"]},
                "sources": [],
                "footnotes": [],
            },
            {
                "page_no": 2,
                "role": "agenda",
                "section_id": None,
                "section_nav": "",
                "headline": "세 가지 전환축",
                "takeaways": ["AI 검색", "신뢰 인프라", "운영 자동화"],
                "content_kind": "narrative",
                "payload": {
                    "sections": [
                        {"num": "01", "key": "검색 재편", "tag": "AI Search", "line": "답변 엔진 노출 경쟁"},
                        {"num": "02", "key": "신뢰 회복", "tag": "Trust", "line": "진정성과 개인정보 보호"},
                        {"num": "03", "key": "운영 자동화", "tag": "Agent Ops", "line": "에이전틱 AI 확산"},
                    ]
                },
                "sources": [],
                "footnotes": [],
            },
            {
                "page_no": 3,
                "role": "section_divider",
                "section_id": "S1",
                "section_nav": "1-1 검색 재편 (1/2)",
                "headline": "AI 검색이 발견 경로를 재정의",
                "takeaways": ["검색 결과가 링크 목록에서 답변 단위로 이동한다"],
                "content_kind": "narrative",
                "payload": {"paragraphs": ["섹션 간지"]},
                "sources": [],
                "footnotes": [],
            },
            {
                "page_no": 4,
                "role": "content",
                "section_id": "S1",
                "section_nav": "1-1 검색 재편 (2/2)",
                "headline": "마케팅 기술 지출의 AI 쏠림",
                "takeaways": ["MarTech 지출은 AI 자동화 수요와 함께 확대된다", "수치 슬라이드는 출처를 하단 토큰으로 분리한다"],
                "content_kind": "market_numbers",
                "payload": {
                    "stats": [
                        {"label": "MarTech 시장", "value": "6,609억 달러", "note": "2026년 추정", "source": "Mordor Intelligence"},
                        {"label": "AI 검색 관심", "value": "70%", "note": "마케터 응답", "source": "Gartner"},
                        {"label": "신뢰 예산", "value": "100억 달러", "note": "CX 보완 투자", "source": "Forrester"},
                    ]
                },
                "sources": [{"name": "Mordor Intelligence", "url": "https://example.com/mordor"}],
                "footnotes": [{"term": "AEO", "en": "Answer Engine Optimization", "def": "AI 답변 엔진 최적화"}],
            },
            {
                "page_no": 5,
                "role": "content",
                "section_id": "S1",
                "section_nav": "1-1 검색 재편 (3/3)",
                "headline": "예산 전환의 두 번째 수치 묶음",
                "takeaways": ["같은 content_kind가 반복되면 후보 레이아웃을 회전한다", "표지 메시지와 BLUF를 분리한다"],
                "content_kind": "market_numbers",
                "payload": {
                    "stats": [
                        {"label": "AI 검색", "value": "54%", "note": "우선순위 상승", "source": "Gartner"},
                        {"label": "콘텐츠 자동화", "value": "23%", "note": "CAGR 기준", "source": "Deloitte"},
                    ]
                },
                "sources": [{"name": "Gartner", "url": "https://example.com/gartner"}],
                "footnotes": [],
            },
            {
                "page_no": 6,
                "role": "content",
                "section_id": "S1",
                "section_nav": "1-1 검색 재편 (4/4)",
                "headline": "AI는 기본값이 됐다 **(이제 신뢰에 투자하라)**",
                "takeaways": ["좌측은 결론을 담고", "우측은 핵심 근거를 담는다"],
                "content_kind": "split",
                "payload": {
                    "right_kind": "stats",
                    "lead": "AI 도입 논쟁은 끝났고, 투자 판단은 신뢰와 운영체계로 이동한다.",
                    "stats": [
                        {"label": "매일 AI 사용", "value": "60%", "note": "마케터 응답", "source": "IDNZ"},
                        {"label": "시간 절약", "value": "95%", "note": "AI 활용 효과", "source": "IDNZ"},
                    ],
                },
                "sources": [{"name": "IDNZ", "url": "https://example.com/idnz"}],
                "footnotes": [],
            },
            {
                "page_no": 7,
                "role": "content",
                "section_id": "S2",
                "section_nav": "2-1 기관 전망 (1/1)",
                "headline": "기관별 2026 마케팅 전망",
                "takeaways": ["표는 원본 표 구조를 다시 그린다", "출처는 행이 아니라 source/caption에만 둔다"],
                "content_kind": "institution_forecasts",
                "payload": {
                    "headers": ["기관", "핵심 예측", "근거"],
                    "rows": [
                        ["Gartner", "모바일 앱·오프라인 경험 재평가", "CMO 예산 재배분"],
                        ["Forrester", "AI 챗봇 신뢰 비용 증가", "CX 보완 투자"],
                    ],
                    "source": "Gartner, Forrester",
                },
                "sources": [{"name": "Forrester", "url": "https://example.com/forrester"}],
                "footnotes": [],
            },
            {
                "page_no": 8,
                "role": "content",
                "section_id": "S3",
                "section_nav": "3-1 실행 구조 (1/4)",
                "headline": "AEO로 이어지는 발견 경로",
                "takeaways": ["시간 흐름은 타임라인으로 배치한다", "연도·단계는 본문에서 추린다"],
                "content_kind": "timeline_evolution",
                "payload": {"stages": [{"period": "2024", "label": "SEO", "detail": "검색엔진 노출"}, {"period": "2026", "label": "AEO", "detail": "답변 엔진 노출"}]},
                "sources": [{"name": "Deloitte Digital", "url": "https://example.com/deloitte"}],
                "footnotes": [],
            },
            {
                "page_no": 9,
                "role": "content",
                "section_id": "S3",
                "section_nav": "3-1 실행 구조 (2/4)",
                "headline": "현재와 미래의 마케팅 운영 차이",
                "takeaways": ["관계 변화는 before/after로 보인다"],
                "content_kind": "concept_relation",
                "payload": {
                    "before": {"title": "현재", "items": ["채널별 운영", "사후 리포트"]},
                    "after": {"title": "미래", "items": ["에이전트 운영", "실시간 조정"]},
                    "metric": {"label": "전환", "value": "채널→운영체계", "note": "보고서 종합"},
                },
                "sources": [],
                "footnotes": [],
            },
            {
                "page_no": 10,
                "role": "content",
                "section_id": "S3",
                "section_nav": "3-1 실행 구조 (3/4)",
                "headline": "에이전틱 AI 도입 퍼널",
                "takeaways": ["단계형 변화는 funnel로 요약한다"],
                "content_kind": "funnel_steps",
                "payload": {"steps": [{"label": "탐색", "body": "검색·콘텐츠 실험"}, {"label": "확장", "body": "워크플로 자동화"}, {"label": "통제", "body": "브랜드·법무 가드"}]},
                "sources": [],
                "footnotes": [],
            },
            {
                "page_no": 11,
                "role": "content",
                "section_id": "S3",
                "section_nav": "3-1 실행 구조 (4/4)",
                "headline": "성장 동인을 세 카드로 압축",
                "takeaways": ["나열형 근거는 카드 그리드로 묶는다"],
                "content_kind": "growth_drivers",
                "payload": {"cards": [{"title": "AI 검색", "body": "브랜드 발견의 진입점 변화"}, {"title": "숏폼", "body": "짧은 주기의 실험 확산"}, {"title": "프라이버시", "body": "동의 기반 데이터 운영"}]},
                "sources": [],
                "footnotes": [],
            },
            {
                "page_no": 12,
                "role": "conclusion",
                "section_id": None,
                "section_nav": "결론",
                "headline": "AI가 마케팅 운영체제를 바꾼다",
                "takeaways": ["검색·콘텐츠·측정이 하나의 운영 루프로 묶인다", "브랜드 신뢰는 선택지가 아니라 인프라다"],
                "content_kind": "implications",
                "payload": {"paragraphs": ["결론은 표지의 지배 메시지를 반복한다."]},
                "sources": [],
                "footnotes": [],
            },
        ],
        "references": [
            {"name": "Mordor Intelligence", "url": "https://example.com/mordor", "tag": "수치 근거"},
            {"name": "Forrester", "url": "https://example.com/forrester", "tag": "본문 출처"},
        ],
    }


def write_page_specs(payload: dict) -> Path:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False)
    with handle:
        json.dump(payload, handle, ensure_ascii=False)
    return Path(handle.name)


def test_build_deck_binds_page_specs_to_native_layouts_and_rotates_candidates():
    page_specs = write_page_specs(sample_page_specs())
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    layouts = [slide["layout"] for slide in deck["slides"]]

    assert layouts[:3] == ["cover_hero", "editorial_impact_axes", "section_divider_hero_text"]
    assert layouts[3] == "data_visualization_3col_chart"
    assert layouts[4] == "data_visualization_2col_chart_text"
    assert "split_master" in layouts
    assert "requirements_excel_table" in layouts
    assert "evolution_timeline" in layouts
    assert "before_after_diagram_with_metric" in layouts
    assert "funnel" in layouts
    assert "3-card" in layouts
    assert "conclusion_synthesis" in layouts
    assert layouts[-2] == "references_notes"
    assert layouts[-1] == "back_cover"


def test_authority_tokens_are_carried_without_polluting_table_rows():
    page_specs = write_page_specs(sample_page_specs())
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    number_slide = deck["slides"][3]
    table_slide = next(slide for slide in deck["slides"] if slide["layout"] == "requirements_excel_table")
    refs_slide = next(slide for slide in deck["slides"] if slide["layout"] == "references_notes")

    assert number_slide["eyebrow"] == "1-1 검색 재편 (2/2)"
    assert number_slide["source"] == "자료: Mordor Intelligence, Gartner, Forrester"
    assert number_slide["footnotes"][0]["term"] == "AEO"
    assert "AEO(Answer Engine Optimization)" in number_slide["footnote_text"]

    assert table_slide["source"] == "자료: Forrester, Gartner"
    assert table_slide["caption"] == "자료: Forrester, Gartner"
    assert all("출처" not in json.dumps(row, ensure_ascii=False) for row in table_slide["rows"])
    assert refs_slide["notes"] == [
        {"source": "Mordor Intelligence", "title": "https://example.com/mordor", "tag": "수치 근거"},
        {"source": "Forrester", "title": "https://example.com/forrester", "tag": "본문 출처"},
    ]


def test_authority_tokens_preserve_evidence_ids_alongside_short_source_label():
    payload = sample_page_specs()
    payload["pages"][3]["sources"] = [
        {"name": "Adobe", "url": "https://example.com/adobe"},
        {"name": "Mordor", "url": "https://example.com/mordor"},
        {"name": "TBRC", "url": "https://example.com/tbrc"},
        {"name": "Coherent", "url": "https://example.com/coherent"},
    ]
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    slide = deck["slides"][3]

    assert slide["source"] == "자료: Adobe, Mordor, TBRC 외 4건"
    assert slide["evidence_ids"] == [
        "https://example.com/adobe",
        "https://example.com/mordor",
        "https://example.com/tbrc",
        "https://example.com/coherent",
        "Mordor Intelligence",
        "Gartner",
        "Forrester",
    ]
    assert slide["source_map"]["sources"][3]["name"] == "Coherent"


def test_authority_tokens_merge_page_payload_and_stat_sources():
    page = sample_page_specs()["pages"][3]
    page["sources"] = [{"name": "Adobe", "url": "https://example.com/adobe"}]
    page["payload"]["source"] = "Grand View Research"
    page["payload"]["stats"][0]["source"] = "IMARC Group"

    fields = axis1_to_deck.authority_fields(page)

    assert fields["source"] == "자료: Adobe, Grand View Research, IMARC Group 외 2건"
    assert fields["evidence_ids"] == [
        "https://example.com/adobe",
        "Grand View Research",
        "IMARC Group",
        "Gartner",
        "Forrester",
    ]


def test_subtitle_from_takeaways_never_uses_ellipsis_and_dedupes_paragraphs():
    page = {
        "headline": "중복 제거",
        "section_nav": "01",
        "takeaways": ["짧은 결론"],
        "payload": {"paragraphs": ["짧은 결론", "본문만 남는 문장"]},
        "sources": [],
        "footnotes": [],
    }
    long_page = {
        "takeaways": ["가" * 120, "나" * 120],
    }

    slide = axis1_to_deck.bind_narrative(page, "narrative_centered_text_block")

    assert slide["subtitle"] == "짧은 결론"
    assert slide["paragraphs"] == ["본문만 남는 문장"]
    assert axis1_to_deck.subtitle_from_takeaways(long_page) == ""
    assert "…" not in slide["subtitle"]

    page["takeaways"] = ["같은 문장", "다른 문장"]
    page["payload"]["paragraphs"] = ["같은 문장", "다른 문장"]
    slide = axis1_to_deck.narrative_fallback(page)

    assert slide["subtitle"] == "같은 문장 · 다른 문장"
    assert slide["paragraphs"] == []


def test_subtitle_fields_never_receive_truncated_ellipsis_text():
    payload = sample_page_specs()
    long = "아주 긴 지배 메시지 " * 20
    payload["governing_thought_short"] = long
    payload["pages"][0]["takeaways"] = [long]
    payload["pages"][1]["takeaways"] = [long]
    payload["pages"][2]["takeaways"] = [long]
    payload["pages"][-1]["payload"]["paragraphs"] = [long]
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    subtitles = [slide.get("subtitle", "") for slide in deck["slides"]]

    assert all("…" not in subtitle for subtitle in subtitles)
    assert deck["slides"][0]["subtitle"] == ""
    assert deck["slides"][1]["subtitle"] == ""
    assert deck["slides"][2]["subtitle"] == ""


def test_market_number_bars_use_parsed_values_not_index_order():
    page = {
        "headline": "시장 수치",
        "section_nav": "01",
        "takeaways": [],
        "content_kind": "market_numbers",
        "payload": {
            "stats": [
                {"label": "큰 값", "value": "470억 → 1,070억$", "note": "범위", "source": "A"},
                {"label": "작은 값", "value": "2032년 158억$", "note": "전망", "source": "B"},
                {"label": "비율", "value": "35.8%", "note": "점유율", "source": "C"},
            ]
        },
        "sources": [],
        "footnotes": [],
    }

    slide = axis1_to_deck.bind_market_numbers(page, "data_visualization_3col_chart")
    bars = [item["barPct"] for item in slide["stats"]]

    assert bars[0] == 100
    assert 14 <= bars[1] <= 15
    assert bars[2] == 35.8

    assert axis1_to_deck.parsed_metric_value("2026년 35.8%") == ("percent", 35.8)
    assert axis1_to_deck.parsed_metric_value("1조 원") == ("money", 10000.0)
    assert axis1_to_deck.parsed_metric_value("9,000억 원") == ("money", 9000.0)
    assert axis1_to_deck.parsed_metric_value("1조 2,708억 원") == ("money", 12708.0)
    assert axis1_to_deck.parsed_metric_value("$500M") == ("money", 5.0)
    assert axis1_to_deck.parsed_metric_value("$1.2B") == ("money", 12.0)
    assert axis1_to_deck.parsed_metric_value("1.2 trillion dollars") == ("money", 12000.0)
    assert axis1_to_deck.parsed_metric_value("2026 $500M") == ("money", 5.0)
    assert axis1_to_deck.parsed_metric_value("$500M in 2026") == ("money", 5.0)
    assert axis1_to_deck.parsed_metric_value("2032 $15.8B") == ("money", 158.0)
    assert axis1_to_deck.scaled_bar_pcts(["$500M", "$1.2B"]) == [41.7, 100.0]


def test_two_column_market_numbers_preserve_values_in_bars():
    page = sample_page_specs()["pages"][4]

    slide = axis1_to_deck.bind_market_numbers(page, "data_visualization_2col_chart_text")

    assert slide["bars"] == [
        {"label": "AI 검색", "value": "54%", "pct": 54.0},
        {"label": "콘텐츠 자동화", "value": "23%", "pct": 23.0},
    ]


def test_split_kind_binds_left_conclusion_and_right_stats():
    page = sample_page_specs()["pages"][5]

    slide = axis1_to_deck.bind_split(page)

    assert slide["layout"] == "split_master"
    assert slide["title"] == "AI는 기본값이 됐다 **(이제 신뢰에 투자하라)**"
    assert slide["lead"] == "AI 도입 논쟁은 끝났고, 투자 판단은 신뢰와 운영체계로 이동한다."
    assert slide["takeaways"] == ["좌측은 결론을 담고", "우측은 핵심 근거를 담는다"]
    assert slide["right_kind"] == "stats"
    assert slide["stats"] == [
        {"label": "매일 AI 사용", "value": "60%", "note": "마케터 응답"},
        {"label": "시간 절약", "value": "95%", "note": "AI 활용 효과"},
    ]
    assert slide["source"] == "자료: IDNZ"


def test_split_table_infers_columns_rows_without_explicit_right_kind():
    page = sample_page_specs()["pages"][5]
    page["payload"] = {
        "lead": "표도 우측 슬롯에 들어간다.",
        "columns": ["축", "과제"],
        "rows": [["AI", "운영화"], ["Trust", "진정성"]],
    }

    slide = axis1_to_deck.bind_split(page)

    assert slide["right_kind"] == "table"
    assert slide["columns"] == ["축", "과제"]
    assert slide["rows"] == [
        {"축": "AI", "과제": "운영화"},
        {"축": "Trust", "과제": "진정성"},
    ]


def test_chart_content_kinds_bind_payloads_to_chart_layouts():
    payload = sample_page_specs()
    payload["theme"] = "TD_pantone_ink_dark"
    payload["pages"] = [
        {
            "page_no": 1,
            "role": "content",
            "section_id": "S1",
            "section_nav": "01 지표",
            "headline": "AI 도입은 이미 일상 사용 단계",
            "takeaways": ["막대 길이는 실제 비율 값에서 나온다"],
            "content_kind": "chart_bar",
            "payload": {
                "categories": ["매일 AI 사용", "시간 절약", "개인화 기대"],
                "series": [{"name": "응답 비율", "values": [60, 95, 67]}],
                "orient": "h",
                "stacked": False,
            },
            "sources": [{"name": "IDNZ", "url": "https://example.com/idnz"}],
            "footnotes": [],
        },
        {
            "page_no": 2,
            "role": "content",
            "section_id": "S1",
            "section_nav": "01 지표",
            "headline": "북미는 최대 MarTech 시장",
            "takeaways": ["도넛 비율은 value/max로 계산한다"],
            "content_kind": "chart_donut",
            "payload": {"value": 35.8, "label": "북미 점유율", "max": 100},
            "sources": [{"name": "IMARC", "url": "https://example.com/imarc"}],
            "footnotes": [],
        },
        {
            "page_no": 3,
            "role": "content",
            "section_id": "S1",
            "section_nav": "01 지표",
            "headline": "AI 마케팅 수익은 3년 만에 2배 이상",
            "takeaways": ["KPI도 payload 값만 사용한다"],
            "content_kind": "chart_kpi",
            "payload": {"value": "470억 → 1,070억$", "label": "AI 마케팅 수익 2025→2028", "mini": [47, 70, 107]},
            "sources": [{"name": "Adobe", "url": "https://example.com/adobe"}],
            "footnotes": [],
        },
    ]
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    assert deck["theme"] == "TD_pantone_ink_dark"
    layouts = [slide["layout"] for slide in deck["slides"]]
    assert layouts[:3] == ["chart_bar", "chart_donut", "chart_kpi"]

    bar = deck["slides"][0]
    assert bar["chart"]["type"] == "bar"
    assert bar["chart"]["categories"] == ["매일 AI 사용", "시간 절약", "개인화 기대"]
    assert bar["chart"]["series"][0]["values"] == [60.0, 95.0, 67.0]
    assert bar["chart"]["orient"] == "h"
    assert bar["chart"]["stacked"] is False

    donut = deck["slides"][1]
    assert donut["chart"]["type"] == "donut"
    assert donut["chart"]["value"] == 35.8
    assert donut["chart"]["percent"] == 35.8

    kpi = deck["slides"][2]
    assert kpi["kpi"]["value"] == "470억 → 1,070억$"
    assert kpi["chart"]["type"] == "line"
    assert kpi["chart"]["series"][0]["values"] == [47.0, 70.0, 107.0]


def test_chart_series_preserve_category_positions_and_percent_strings():
    page = {
        "headline": "값 위치 보존",
        "section_nav": "01",
        "takeaways": [],
        "content_kind": "chart_bar",
        "payload": {
            "categories": ["A", "B", "C"],
            "series": [{"name": "값", "values": [10, None, "30%"]}],
            "orient": "h",
        },
        "sources": [],
        "footnotes": [],
    }

    slide = axis1_to_deck.bind_chart(page, "chart_bar")

    assert slide["chart"]["categories"] == ["A", "B", "C"]
    assert slide["chart"]["series"][0]["values"] == [10.0, None, 30.0]


def test_share_charts_accept_percent_only_payloads():
    page = {
        "headline": "점유율",
        "section_nav": "01",
        "takeaways": [],
        "content_kind": "chart_donut",
        "payload": {"percent": 35.8, "label": "북미 점유율"},
        "sources": [],
        "footnotes": [],
    }

    slide = axis1_to_deck.bind_chart(page, "chart_donut")

    assert slide["chart"]["value"] == 35.8
    assert slide["chart"]["max"] == 100.0
    assert slide["chart"]["percent"] == 35.8


def test_chart_kpi_preserves_nested_chart_payload_when_present():
    page = {
        "headline": "KPI + mini",
        "section_nav": "01",
        "takeaways": [],
        "content_kind": "chart_kpi",
        "payload": {
            "value": "470억 → 1,070억$",
            "label": "AI 마케팅 수익",
            "chart": {
                "type": "line",
                "categories": ["2025", "2026", "2028"],
                "series": [{"name": "수익", "values": [47, 70, 107]}],
            },
        },
        "sources": [],
        "footnotes": [],
    }

    slide = axis1_to_deck.bind_chart(page, "chart_kpi")

    assert slide["chart"]["categories"] == ["2025", "2026", "2028"]
    assert slide["chart"]["series"][0]["values"] == [47.0, 70.0, 107.0]


def test_split_right_kind_chart_binds_nested_chart_payload():
    page = sample_page_specs()["pages"][5]
    page["payload"] = {
        "right_kind": "chart",
        "lead": "도입은 끝난 논쟁이고, 격차는 활용 성숙도에서 난다.",
        "chart": {
            "type": "bar",
            "categories": ["매일 AI 사용", "시간 절약"],
            "series": [{"name": "응답 비율", "values": [60, 95]}],
            "orient": "h",
        },
    }

    slide = axis1_to_deck.bind_split(page)

    assert slide["right_kind"] == "chart"
    assert slide["chart"]["type"] == "bar"
    assert slide["chart"]["series"][0]["values"] == [60.0, 95.0]
    assert slide["chart"]["categories"] == ["매일 AI 사용", "시간 절약"]


def test_timeline_evolution_routes_to_horizontal_evolution_layout():
    page_specs = write_page_specs(sample_page_specs())
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    timeline_slide = next(slide for slide in deck["slides"] if slide["layout"] == "evolution_timeline")

    assert len(timeline_slide["stages"]) == 2
    assert timeline_slide["stages"][0] == {
        "period": "2024",
        "label": "SEO",
        "detail": "검색엔진 노출",
    }
    assert timeline_slide["stages"][1]["period"] == "2026"
    assert "events" not in timeline_slide
    assert "sections" not in timeline_slide


def test_concept_relation_metric_is_optional():
    payload = sample_page_specs()
    concept_page = next(page for page in payload["pages"] if page["content_kind"] == "concept_relation")
    concept_page["payload"].pop("metric")
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    relation_slide = next(slide for slide in deck["slides"] if slide["layout"] == "before_after_diagram_with_metric")

    assert "metric" not in relation_slide


def test_missing_payload_uses_narrative_fallback_instead_of_fabricating_values():
    payload = sample_page_specs()
    payload["pages"][3]["content_kind"] = "market_numbers"
    payload["pages"][3]["payload"] = {}
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    slide = deck["slides"][3]

    assert slide["layout"] == "narrative_centered_text_block"
    assert "6,609억 달러" not in json.dumps(slide, ensure_ascii=False)
    assert slide["paragraphs"] == payload["pages"][3]["takeaways"]


def test_growth_driver_card_titles_strip_leading_enumerators():
    page = next(page for page in sample_page_specs()["pages"] if page["content_kind"] == "growth_drivers")
    page["payload"]["cards"] = [
        {"title": "①컴포저블 스택", "body": "도구를 갈아끼울 수 있어야 한다"},
        {"title": "2.퍼티 데이터", "body": "동의 기반 데이터를 쌓는다"},
        {"title": "3)AI 운영화", "body": "프로세스에 붙인다"},
    ]

    slide = axis1_to_deck.bind_growth_drivers(page, "3-card")

    assert [card["kicker"] for card in slide["cards"]] == ["01", "02", "03"]
    assert [card["title"] for card in slide["cards"]] == [
        "컴포저블 스택",
        "퍼티 데이터",
        "AI 운영화",
    ]


def test_conclusion_synthesis_splits_action_nodes_and_moves_caution_to_note():
    payload = sample_page_specs()
    conclusion = payload["pages"][-1]
    conclusion["content_kind"] = "narrative"
    conclusion["takeaways"] = [
        "지금 할 일: ① AI를 운영체계로 통합 ② 퍼티 데이터를 자산화 ③ 브랜드 관점에 투자",
        "단, 시장 규모 추정은 방향 신호로만 읽는다",
    ]
    conclusion["payload"]["paragraphs"] = [
        "AI는 기본값이 됐고 신뢰가 차별화 지점이다.",
        "[해석 주의] 시장 규모는 기관별 정의가 다르다.",
    ]
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    slide = next(slide for slide in deck["slides"] if slide["layout"] == "conclusion_synthesis")
    serialized = json.dumps(slide, ensure_ascii=False)

    assert slide["title"] == payload["governing_thought_short"]
    assert slide["actions"] == [
        {"num": "01", "text": "AI를 운영체계로 통합"},
        {"num": "02", "text": "퍼티 데이터를 자산화"},
        {"num": "03", "text": "브랜드 관점에 투자"},
    ]
    assert slide["note"] == "단, 시장 규모 추정은 방향 신호로만 읽는다 · [해석 주의] 시장 규모는 기관별 정의가 다르다."
    assert conclusion["takeaways"][0] not in serialized
    assert "subtitle" not in slide or slide["subtitle"] == ""


def test_conclusion_synthesis_does_not_duplicate_caution_only_takeaway():
    payload = sample_page_specs()
    conclusion = payload["pages"][-1]
    caution = "[해석 주의] 시장 규모는 기관별 정의가 다르다."
    conclusion["content_kind"] = "narrative"
    conclusion["takeaways"] = [caution]
    conclusion["payload"]["paragraphs"] = []
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    slide = next(slide for slide in deck["slides"] if slide["layout"] == "conclusion_synthesis")
    serialized = json.dumps(slide, ensure_ascii=False)

    assert slide["actions"] == []
    assert slide["note"] == caution
    assert serialized.count(caution) == 1


def test_section_divider_carries_chapter_number_and_deck_appends_back_cover():
    payload = sample_page_specs()
    page_specs = write_page_specs(payload)
    try:
        deck = axis1_to_deck.build_deck(page_specs)
    finally:
        page_specs.unlink(missing_ok=True)

    divider = deck["slides"][2]
    back_cover = deck["slides"][-1]

    assert divider["chapter_num"] == "01"
    assert back_cover["layout"] == "back_cover"
    assert back_cover["cover"] is True
    assert back_cover["brand_mark"] == "TickDeck"
    assert back_cover["disclaimer"] == "본 자료는 공개 출처를 종합한 참고용입니다"
    assert back_cover["basis_date"]
    assert payload["topic"] in back_cover["document_label"]
