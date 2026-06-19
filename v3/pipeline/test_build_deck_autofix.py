#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import build_deck


def test_collect_hard_issue_reports_keeps_slide_context():
    validation = {
        "slides": [
            {"index": 1, "title": "OK", "layout": "cover_hero", "issues": []},
            {
                "index": 2,
                "title": "본문",
                "layout": "data_visualization_2col_chart_text",
                "issues": [
                    {"type": "overflow-height", "element": "slide-2-body", "amount": 12},
                    {"type": "DensityWarning", "element": "slide-2-body"},
                ],
            },
        ]
    }

    reports = build_deck.collect_hard_issue_reports(validation)

    assert reports == [
        {
            "index": 2,
            "title": "본문",
            "layout": "data_visualization_2col_chart_text",
            "issues": [{"type": "overflow-height", "element": "slide-2-body", "amount": 12}],
        }
    ]


def test_apply_autofixes_shortens_target_text_fields():
    deck = {
        "slides": [
            {
                "layout": "data_visualization_2col_chart_text",
                "title": "긴 본문",
                "body": "첫 문장입니다. 둘째 문장은 더 길고 자세합니다. 셋째 문장도 이어집니다.",
            },
            {
                "layout": "narrative_centered_text_block",
                "title": "서술",
                "paragraphs": [
                    "긴 문단 첫 문장입니다. 긴 문단 둘째 문장입니다. 긴 문단 셋째 문장입니다.",
                ],
            },
        ]
    }
    reports = [
        {
            "index": 1,
            "issues": [{"type": "overflow-height", "element": "slide-1-body", "amount": 12}],
        },
        {
            "index": 2,
            "issues": [{"type": "safe-area", "element": "slide-2-paragraph-1", "rect": {"top": -20, "bottom": 780}}],
        },
    ]

    changed = build_deck.apply_autofixes(deck, reports, iteration=1)

    assert changed
    assert len(deck["slides"][0]["body"]) < len("첫 문장입니다. 둘째 문장은 더 길고 자세합니다. 셋째 문장도 이어집니다.")
    assert deck["slides"][0]["body"].endswith("…")
    assert len(deck["slides"][1]["paragraphs"][0]) < len("긴 문단 첫 문장입니다. 긴 문단 둘째 문장입니다. 긴 문단 셋째 문장입니다.")


def test_apply_autofixes_blanks_subtitle_instead_of_adding_ellipsis():
    deck = {
        "slides": [
            {
                "layout": "requirements_excel_table",
                "title": "표",
                "subtitle": "긴 부제입니다. 렌더가 넘치면 말줄임표로 자르지 말고 비웁니다.",
                "columns": ["항목", "값"],
                "rows": [{"항목": "도입", "값": "60%"}],
            }
        ]
    }

    changed = build_deck.apply_autofixes(
        deck,
        [{"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-subtitle", "amount": 12}]}],
        iteration=1,
    )

    assert changed
    assert deck["slides"][0]["subtitle"] == ""
    assert "…" not in deck["slides"][0]["subtitle"]


def test_apply_autofixes_does_not_split_compact_small_table_slide():
    rows = [{"항목": f"항목 {idx}", "값": f"값 {idx}"} for idx in range(1, 4)]
    deck = {
        "slides": [
            {
                "layout": "requirements_excel_table",
                "title": "도입 현황 표",
                "columns": ["항목", "값"],
                "rows": rows,
            }
        ]
    }

    changed = build_deck.apply_autofixes(
        deck,
        [{"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-table", "amount": 24}]}],
        iteration=1,
    )

    assert not changed
    assert len(deck["slides"]) == 1
    assert deck["slides"][0]["rows"] == rows


def test_apply_autofixes_splits_overflowing_large_table_slide():
    rows = [{"항목": f"항목 {idx}", "값": f"값 {idx}"} for idx in range(1, 10)]
    source_row = {"항목": "출처(표 주석)", "값": "출처: 본문", "_row_type": "source_note"}
    deck = {
        "slides": [
            {
                "layout": "requirements_excel_table",
                "title": "종합 전망 표",
                "columns": ["항목", "값"],
                "rows": [*rows, source_row],
            }
        ]
    }

    changed = build_deck.apply_autofixes(
        deck,
        [{"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-table", "amount": 24}]}],
        iteration=1,
    )

    assert changed
    assert len(deck["slides"]) == 2
    assert deck["slides"][0]["title"] == "종합 전망 표 (1/2)"
    assert deck["slides"][1]["title"] == "종합 전망 표 (2/2)"
    assert len([row for row in deck["slides"][0]["rows"] if row.get("_row_type") != "source_note"]) == 5
    assert deck["slides"][1]["rows"][-1]["_row_type"] == "source_note"


def test_autofix_does_not_downgrade_stat_cards_and_drop_values():
    deck = {
        "slides": [
            {
                "layout": "data_visualization_3col_chart",
                "title": "시장 수치",
                "stats": [
                    {"label": "AI 마케팅", "value": "470억 → 1,070억$", "note": "Adobe"},
                    {"label": "MarTech", "value": "2032년 158억$", "note": "기관 전망"},
                ],
            }
        ]
    }

    build_deck.apply_autofixes(
        deck,
        [{"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-stat-1-value", "amount": 12}]}],
        iteration=2,
    )

    assert deck["slides"][0]["layout"] == "data_visualization_3col_chart"
    values = [item["value"] for item in deck["slides"][0]["stats"]]
    assert "470억 → 1,070억$" in values
    assert "2032년 158억$" in values


def test_autofix_does_not_downgrade_numeric_bars_and_drop_values():
    deck = {
        "slides": [
            {
                "layout": "data_visualization_2col_chart_text",
                "title": "시장 수치",
                "bars": [
                    {"label": "AI 검색", "value": "54%", "pct": 54.0},
                    {"label": "콘텐츠 자동화", "value": "23%", "pct": 23.0},
                ],
                "body": "2열 수치 차트는 값이 렌더의 핵심이다.",
            }
        ]
    }

    build_deck.apply_autofixes(
        deck,
        [{"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-body", "amount": 12}]}],
        iteration=2,
    )

    assert deck["slides"][0]["layout"] == "data_visualization_2col_chart_text"
    assert [item["value"] for item in deck["slides"][0]["bars"]] == ["54%", "23%"]


def test_autofix_does_not_downgrade_split_master_and_drop_right_slot():
    deck = {
        "slides": [
            {
                "layout": "split_master",
                "title": "소비자의 결정은 더 빨라진다",
                "lead": "기술은 의사결정 사이클을 압축하고, 소비자는 더 빠르게 비교하고 더 빨리 이탈한다.",
                "takeaways": ["좌측은 결론", "우측은 근거"],
                "right_kind": "bullets",
                "right_items": [
                    "가치 기준이 유동화된다",
                    "결정 방식이 짧아진다",
                ],
            }
        ]
    }

    changed = build_deck.apply_autofixes(
        deck,
        [{"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-lead", "amount": 12}]}],
        iteration=2,
    )

    assert changed
    assert deck["slides"][0]["layout"] == "split_master"
    assert deck["slides"][0]["right_kind"] == "bullets"
    assert deck["slides"][0]["right_items"] == [
        "가치 기준이 유동화된다",
        "결정 방식이 짧아진다",
    ]
    assert deck["slides"][0]["lead"].endswith("…")


def test_apply_autofixes_shortens_new_layout_stage_action_and_note_fields():
    deck = {
        "slides": [
            {
                "layout": "evolution_timeline",
                "title": "진화",
                "stages": [
                    {
                        "period": "2026~",
                        "label": "에이전틱 AI",
                        "detail": "매우 긴 단계 설명입니다. 캠페인을 스스로 기획하고 집행하고 조정하는 흐름을 길게 설명합니다.",
                    }
                ],
            },
            {
                "layout": "conclusion_synthesis",
                "title": "결론",
                "actions": [
                    {"num": "01", "text": "매우 긴 행동 문장입니다. AI를 운영체계로 통합하고 데이터와 브랜드까지 한꺼번에 관리합니다."}
                ],
                "note": "매우 긴 주석입니다. 시장 규모는 기관별 정의가 다르고 단일 합의치가 아니므로 방향 신호로만 읽습니다.",
            },
        ]
    }

    changed = build_deck.apply_autofixes(
        deck,
        [
            {"index": 1, "issues": [{"type": "overflow-height", "element": "slide-1-stage-1", "amount": 18}]},
            {"index": 2, "issues": [{"type": "overflow-height", "element": "slide-2-action-1", "amount": 18}]},
            {"index": 2, "issues": [{"type": "overflow-height", "element": "slide-2-note", "amount": 18}]},
        ],
        iteration=1,
    )

    assert changed
    assert deck["slides"][0]["stages"][0]["detail"].endswith("…")
    assert deck["slides"][1]["actions"][0]["text"].endswith("…")
    assert deck["slides"][1]["note"].endswith("…")


def test_render_autofix_loop_rerenders_until_validation_is_clean(tmp_path, monkeypatch):
    slides_json = tmp_path / "slides.json"
    out_dir = tmp_path / "out"
    deck = {
        "title": "테스트",
        "slides": [
            {
                "layout": "data_visualization_2col_chart_text",
                "title": "긴 본문",
                "body": "첫 문장입니다. 둘째 문장은 더 길고 자세합니다. 셋째 문장도 이어집니다.",
            }
        ],
    }
    calls = {"count": 0}

    def fake_run(cmd, text):
        calls["count"] += 1
        out_dir.mkdir(parents=True, exist_ok=True)
        issues = []
        returncode = 0
        if calls["count"] == 1:
            issues = [{"type": "overflow-height", "element": "slide-1-body", "amount": 12}]
            returncode = 2
        (out_dir / "validation.json").write_text(
            json.dumps(
                {
                    "summary": {"total_issues": len(issues)},
                    "slides": [{"index": 1, "title": "긴 본문", "layout": deck["slides"][0]["layout"], "issues": issues}],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, returncode)

    monkeypatch.setattr(build_deck.subprocess, "run", fake_run)

    result = build_deck.render_with_autofix_loop(deck, slides_json, out_dir, render=True)

    saved = json.loads(slides_json.read_text(encoding="utf-8"))
    assert calls["count"] == 2
    assert result["autofix_iterations"] == 1
    assert result["final_hard_issues"] == 0
    assert len(saved["slides"][0]["body"]) < len("첫 문장입니다. 둘째 문장은 더 길고 자세합니다. 셋째 문장도 이어집니다.")


def test_render_autofix_loop_reports_render_failure_without_reusing_stale_validation(tmp_path, monkeypatch):
    slides_json = tmp_path / "slides.json"
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    (out_dir / "validation.json").write_text(
        json.dumps({"slides": [], "summary": {"total_issues": 0}}, ensure_ascii=False),
        encoding="utf-8",
    )
    deck = {"title": "테스트", "slides": [{"layout": "cover_hero", "title": "표지"}]}

    def fake_run(cmd, text):
        return subprocess.CompletedProcess(cmd, 2)

    monkeypatch.setattr(build_deck.subprocess, "run", fake_run)

    result = build_deck.render_with_autofix_loop(deck, slides_json, out_dir, render=True)

    assert result["render_returncode"] == 2
    assert result["final_hard_issues"] == 1
    assert result["final_hard_issue_details"][0]["issues"][0]["type"] == "render-failure"


def test_build_and_render_accepts_explicit_page_specs_without_author_call(tmp_path, monkeypatch):
    result_json = tmp_path / "result.json"
    result_json.write_text(
        json.dumps({"topic": "테스트", "leader": {"final": "## 본문\n내용"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    page_specs = tmp_path / "page_specs.json"
    page_specs.write_text(
        json.dumps(
            {
                "topic": "테스트",
                "governing_thought_short": "테스트 지배 메시지",
                "pages": [
                    {
                        "page_no": 1,
                        "role": "cover",
                        "section_id": None,
                        "section_nav": "",
                        "headline": "테스트 지배 메시지",
                        "takeaways": ["첫 결론", "둘째 결론"],
                        "content_kind": "narrative",
                        "payload": {"paragraphs": ["표지"]},
                        "sources": [],
                        "footnotes": [],
                    }
                ],
                "references": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fail_author(*args, **kwargs):
        raise AssertionError("author should not run when page_specs_path is provided")

    monkeypatch.setattr(build_deck, "ensure_page_specs", fail_author)

    result = build_deck.build_and_render(
        result_json,
        out_dir=tmp_path / "out",
        render=False,
        page_specs_path=page_specs,
    )

    assert result["page_specs_json"] == str(page_specs.resolve())
    assert result["slides"] == 2
    slides = json.loads((tmp_path / "out" / "slides.json").read_text(encoding="utf-8"))["slides"]
    assert slides[0]["title"] == "테스트 지배 메시지"
    assert slides[1]["layout"] == "back_cover"


def test_build_and_render_without_page_specs_uses_author_scaffold_path(tmp_path, monkeypatch):
    result_json = tmp_path / "result.json"
    result_json.write_text(
        json.dumps({"topic": "테스트", "leader": {"final": "## 본문\n내용"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    page_specs = tmp_path / "page_specs.json"
    page_specs.write_text(
        json.dumps(
            {
                "topic": "테스트",
                "governing_thought_short": "테스트 지배 메시지",
                "pages": [
                    {
                        "page_no": 1,
                        "role": "cover",
                        "section_id": None,
                        "section_nav": "",
                        "headline": "테스트 지배 메시지",
                        "takeaways": ["첫 결론", "둘째 결론"],
                        "content_kind": "narrative",
                        "payload": {"paragraphs": ["표지"]},
                        "sources": [],
                        "footnotes": [],
                    }
                ],
                "references": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    calls = {"count": 0}

    def fake_ensure(path, **kwargs):
        calls["count"] += 1
        assert path == result_json.resolve()
        return page_specs

    monkeypatch.setattr(build_deck, "ensure_page_specs", fake_ensure)

    result = build_deck.build_and_render(
        result_json,
        out_dir=tmp_path / "out",
        render=False,
    )

    assert calls["count"] == 1
    assert result["page_specs_json"] == str(page_specs.resolve())
    assert result["slides"] == 2
