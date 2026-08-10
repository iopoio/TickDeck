from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


DEFAULT_MAX_SOURCE_OVERLAP_SCORE = 0.85
VALIDATION_METADATA_TERMS = (
    "단일출처",
    "단일 출처",
    "정성근거",
    "정성 근거",
    "강등",
    "신뢰도",
    "single-source",
    "single source",
    "qualitative evidence",
    "downgrade",
    "confidence score",
)
PIPELINE_ORDER = (
    "intake-director",
    "collector",
    "verifier",
    "analyst",
    "editorial-director",
    "page-planner",
    "designer",
    "qa-reviewer",
)
SUPPORTED_CONTENT_BLOCK_TYPES = frozenset(
    {
        "eyebrow",
        "headline",
        "title",
        "body",
        "text",
        "summary",
        "callout",
        "note",
        "citation",
        "source",
        "footnote",
        "metric",
        "metrics",
        "metric_grid",
        "stat_grid",
        "image",
        "viz",
        "bullets",
        "list",
        "text_table",
    }
)
SUPPORTED_VIZ_CHART_TYPES = frozenset(
    {
        "before_after",
        "dumbbell",
        "flow",
        "big_number",
        "gap_map",
        "shift",
        "funnel",
        # 2026-07-02 2층 어휘 흡수: 차트캐논 A4(도넛) + 백로그 Phase 2(미러·상승컬럼)
        "donut",
        "mirror_bars",
        "rising_columns",
        # 2026-07-03 엔바토 흡수 3라운드: 픽토그램(도트채움)·게이지(반원) — 4곳·3곳 교차검증
        "pictogram",
        "pictograph",
        "gauge",
        # 2026-07-04 다이어그램 어휘(후추님 — 관계·순환·프로세스·표 인포그래픽 공백 지적):
        "hub_cycle",       # 중심+궤도 노드 순환 허브 (series[0]=중심·값 선택)
        "arrow_flow",      # 두꺼운 셰브런 프로세스 (단계가 화살표 도형·값 선택)
        "timeline_bars",   # 간트형 계단 타임라인 (값 선택)
        "gantt",           # 월 그리드 일정 + milestone-only 축
        "data_table",      # 액센트 헤더 + 줄무늬 데이터 표 (값=registry)
        # 2026-07-04 승격 라운드(PATTERN_LIBRARY ⬜→✅·report_ops 정체성):
        "multi_line",        # 다계열 라인 — role baseline/highlight로 선 분리
        "progress_bar",      # 트랙+채움 진척 막대 (number=0~100 해석)
        "target_vs_actual",  # 계획(점선 고스트) vs 실제(채움) 짝 — series 연속 2개=1행
        "radial_progress",   # 단일 링 진척 게이지·% 중앙 (최대 3링)
        "swot_quad",         # 2×2 정성 사분면 — metric_id 없이 series[].items 텍스트만 허용
        "quarterly_bars",    # IR 분기 막대 — 마지막/비교 분기 액센트, 나머지 뮤트
        "fin_table",         # IR 재무 표 — 행 계층·현재 열 아웃라인·음수 의미색
        # 2026-07-08 R5 논증 어휘(DESIGN_R5_argument_diagrams.md — 주장·인과·포지셔닝·양자택일 도식):
        "pyramid",       # 주장 1 + 근거 2~4단 사다리꼴 스택
        "causal_chain",  # A→B→C 인과 사슬 — 링크(화살표)마다 근거 캡션 슬롯
        "two_by_two",    # 축 2개(x_axis/y_axis) 위 아이템 좌표 배치 포지셔닝 맵
        "tradeoff",      # 좌우 저울 — 수치가 아닌 질적 득실 대비
    }
)
SUPPORTED_VIZ_SERIES_ROLES = frozenset(
    {
        "",
        "baseline",
        "highlight",
        "benchmark",
        "left",
        "right",
        "negative",
        "positive",
        "brand",
        # R5 pyramid: claim=꼭대기 주장 1개, evidence=근거 층.
        "claim",
        "evidence",
    }
)
# 정성 도식(수치 슬롯이 선택)은 metric_id 없이 series item이 허용된다 — swot_quad 선례를
# R5 논증 4종에도 그대로 적용(claim/축 좌표/좌우 대비는 본질적으로 텍스트·좌표이지 지표가 아님).
VIZ_CHARTS_WITHOUT_REQUIRED_METRIC = frozenset({"swot_quad", "fin_table", "pyramid", "causal_chain", "two_by_two", "tradeoff", "gantt", "pictograph"})
# 논증 도식 남발 방지 게이트(DESIGN_R5 §3) — 슬롯 최소 개수 미달 시 위반.
ARG_DIAGRAM_MIN_SLOTS = {
    "pyramid": 2,       # evidence 층 ≥2
    "causal_chain": 3,  # 노드 ≥3
    "two_by_two": 3,    # 아이템 ≥3
}
SUPPORTED_PAGE_CHROMES = frozenset({"", "running_head", "title_band"})
SUPPORTED_VIZ_SOURCE_CAPTIONS = frozenset({"", "on", "off"})
SUPPORTED_VIZ_TITLE_STYLES = frozenset({"", "band"})
SUPPORTED_METRIC_DERIVATIONS = frozenset({"cagr", "delta_pct", "delta_abs", "multiple", "share"})
SUPPORTED_SECTION_NAVS = frozenset({"", "chips", "dots", "toc"})
SUPPORTED_VIZ_ANNOTATION_CHARTS = frozenset({"multi_line", "rising_columns", "quarterly_bars"})
SUPPORTED_VIZ_ANNOTATION_KINDS = frozenset({"callout", "endpoint_value", "trend_arrow", "event_band"})
SUPPORTED_VIZ_ANNOTATION_SHAPES = frozenset({"", "ellipse", "box"})
TITLE_BAND_MAX_CHARS = 72
SUPPORTED_LAYOUTS = frozenset(
    {
        "cover",
        "statement",
        "hero_metric",
        "stat_grid",
        "metric_grid",
        "cards",
        "timeline",
        "split",
        "stack",
        "stepper",
        "node",
        "matrix",
        "index",
        "divider",
        "closing",
        "outro",
        "source_appendix",
        # 시그니처 페이지(시스템별 전용 골격·2026-07-04 페이지 아키텍처 파일럿) —
        # "옷(테마)"이 아니라 "몸(페이지 해부학)"을 분기하는 층. 권장 시스템은 designer.md 참조.
        "poster",           # minimal_typo — 제목 없는 한 문장 포스터
        "hero_bleed",       # dark_premium — 화면 절반 블리드 숫자 + 좌측 텍스트
        "magazine_spread",  # editorial_serif — 러닝헤드 + 다단 조판 + 풀쿼트
        "dashboard",        # data_mono — 풀페이지 위젯 타일
        "mosaic_tiles",     # editorial_serif — 텍스트/스탯 색면 모자이크 타일
        "split_status",     # 공용 — 좌측 정성 상태 서술 + 우측 정량 지표 칩
        "scenario_cards",   # dark_premium/pop_dark — 시나리오 카드 열
        "pricing_cards",    # 2~4열 플랜/옵션 카드 — 수치는 metric_id 주입
        "metric_commentary", # R3 — 지표 헤딩 + 파생 델타 헤드라인 + 분기 막대
    }
)
RAW_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[+-]?\d+(?:[.,]\d+)*(?:\.\d+)?"
    r"(?:\s?(?:%|\$|조|억|만|명|개|건|pp|p|B|M|K|원|달러|USD|YoY))?(?![A-Za-z0-9_])"
)
NUMBER_CORE_PATTERN = re.compile(r"[+-]?\d+(?:[.,]\d+)*(?:\.\d+)?")
FOUR_DIGIT_YEAR_PATTERN = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
YEAR_RANGE_PREFIX_PATTERN = re.compile(r"(?:19|20)\d{2}\s*[~\-–—]\s*$")
ENCLOSED_NUMERAL_PATTERN = re.compile(
    "[\u2460-\u249b\u24ea-\u24ff\u2776-\u2793\u3251-\u325f\u32b1-\u32bf]"
)
# {{metric_id}} \uc778\ub77c\uc778 \ud1a0\ud070(7/22 \uc2e0\uc124 \u2014 text_table\u00b7callout/note/body \uc140\uc5d0 \uc11c\uc0ac\ubb38+\uc218\uce58\ub97c \uc11e\uc744 \ub54c
# render_deck.py _rich_with_metrics\uac00 registry \uac12\uc73c\ub85c \uce58\ud658\u00b7data-metric-id\ub85c \uac10\uc2fc\ub2e4). \ub80c\ub354 \uc804
# \ub2e8\uacc4\uc5d0\uc11c\ub3c4 \uac19\uc740 \ud398\uc774\uc9c0 allowlist\u00b7registry \uc874\uc7ac\ub97c \uac15\uc81c\ud574\uc57c designer\uac00 \ud654\uc774\ud2b8\ub9ac\uc2a4\ud2b8 \ubc16 metric\uc744
# \ud504\ub9ac\ud14d\uc2a4\ud2b8\uc5d0 \ubc00\ubc18\uc785\ud558\ub294 \uae38\uc744 \ub9c9\ub294\ub2e4(\uad6c\uc870\ud654 metric \ube14\ub85d\uacfc \ub3d9\uc77c\ud55c C6 \ubcf4\ud638).
METRIC_TOKEN_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")


@dataclass(frozen=True)
class ContractViolation(Exception):
    contract_id: str
    message: str
    path: str = ""

    def __str__(self) -> str:
        prefix = f"{self.contract_id}"
        if self.path:
            prefix = f"{prefix} at {self.path}"
        return f"{prefix}: {self.message}"


def validate_c1_proposition_dag(dag: dict[str, Any]) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    nodes = dag.get("nodes")
    edges = dag.get("edges")

    if not isinstance(nodes, list) or not nodes:
        return [ContractViolation("C1", "proposition DAG must include non-empty nodes", "proposition_dag.nodes")]
    if not isinstance(edges, list):
        return [ContractViolation("C1", "proposition DAG must include edges list", "proposition_dag.edges")]

    node_ids = {node.get("id") for node in nodes if isinstance(node, dict)}
    if None in node_ids:
        violations.append(ContractViolation("C1", "every node must include id", "proposition_dag.nodes"))
        node_ids.discard(None)

    thesis_ids = {
        node.get("id")
        for node in nodes
        if isinstance(node, dict) and node.get("type") in {"thesis", "root"}
    }
    if not thesis_ids:
        violations.append(ContractViolation("C1", "DAG must include a thesis/root node", "proposition_dag.nodes"))

    children: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            violations.append(ContractViolation("C1", "edge must be an object", f"proposition_dag.edges[{index}]"))
            continue
        source = edge.get("from")
        target = edge.get("to")
        if source not in node_ids or target not in node_ids:
            violations.append(
                ContractViolation("C1", "edge references unknown node id", f"proposition_dag.edges[{index}]")
            )
            continue
        children[source].add(target)

    reachable: set[str] = set()
    stack = list(thesis_ids)
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        stack.extend(children.get(current, set()) - reachable)

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        text = str(node.get("text", "")).lower()
        if "route=" in text or "전부 모음" in text:
            violations.append(
                ContractViolation("C1", "dict-matching route bucket is not a narrative proposition", f"node:{node_id}")
            )
        if node_id not in thesis_ids and node_id not in reachable:
            violations.append(
                ContractViolation("C1", f"orphan proposition node is not connected to thesis: {node_id}", f"node:{node_id}")
            )

    return violations


def validate_c2_no_validation_metadata(pages: list[dict[str, Any]]) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    for index, page in enumerate(pages or []):
        page_violation: ContractViolation | None = None
        for text_path, text in _iter_strings(page, f"rendered_pages[{index}]"):
            lowered = text.lower()
            for term in VALIDATION_METADATA_TERMS:
                if term.lower() in lowered:
                    page_violation = ContractViolation(
                        "C2",
                        f"validation metadata term exposed in content: {term}",
                        text_path,
                    )
                    break
            if page_violation:
                break
        if page_violation:
            violations.append(page_violation)
    return violations


def validate_c3_trend_state_transition(genre: str, insights: list[dict[str, Any]]) -> list[ContractViolation]:
    if "trend" not in str(genre).lower():
        return []

    violations: list[ContractViolation] = []
    required = ("from_state", "to_state", "mechanism")
    for index, insight in enumerate(insights or []):
        missing = [field for field in required if not str(insight.get(field, "")).strip()]
        if missing:
            violations.append(
                ContractViolation(
                    "C3",
                    "trend insights require from_state/to_state/mechanism state transition fields",
                    f"insights[{index}]",
                )
            )
    return violations


def validate_c4_citation_tracker(
    insights: list[dict[str, Any]],
    max_source_overlap_score: float = DEFAULT_MAX_SOURCE_OVERLAP_SCORE,
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    for index, insight in enumerate(insights or []):
        evidence_ids = insight.get("evidence_ids")
        if not isinstance(evidence_ids, list) or len({str(item) for item in evidence_ids if str(item).strip()}) < 2:
            violations.append(
                ContractViolation("C4", "insight must fuse evidence_ids from at least 2 sources", f"insights[{index}]")
            )

        score = insight.get("source_overlap_score")
        if not isinstance(score, (int, float)):
            violations.append(
                ContractViolation("C4", "source_overlap_score must be numeric", f"insights[{index}].source_overlap_score")
            )
        elif score > max_source_overlap_score:
            violations.append(
                ContractViolation(
                    "C4",
                    f"source_overlap_score exceeds max {max_source_overlap_score}",
                    f"insights[{index}].source_overlap_score",
                )
            )
    return violations


def validate_c5_stage_order(stage_log: list[dict[str, Any]]) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    first_seen: dict[str, int] = {}

    for index, entry in enumerate(stage_log or []):
        stage = entry.get("stage") if isinstance(entry, dict) else None
        if stage in PIPELINE_ORDER and stage not in first_seen:
            first_seen[stage] = index

    for stage in ("page-planner", "designer"):
        if stage not in first_seen:
            violations.append(ContractViolation("C5", f"stage_log must include {stage}", "stage_log"))

    for earlier, later in zip(PIPELINE_ORDER, PIPELINE_ORDER[1:]):
        if earlier in first_seen and later in first_seen and first_seen[earlier] > first_seen[later]:
            violations.append(
                ContractViolation("C5", f"{later} ran before required prior stage {earlier}", "stage_log")
            )

    for index, entry in enumerate(stage_log or []):
        if not isinstance(entry, dict):
            continue
        if entry.get("stage") == "page-planner" and entry.get("loop_from") == "designer":
            reason = str(entry.get("loop_reason", "")).lower()
            if "space" not in reason and "density" not in reason and "overflow" not in reason and "공간" not in reason and "과밀" not in reason and "잘림" not in reason:
                violations.append(
                    ContractViolation(
                        "C5",
                        "loop B from designer to page-planner is allowed only for space/density/overflow constraints",
                        f"stage_log[{index}]",
                    )
                )

    return violations


def validate_c6_content_authority(
    deck_spec: dict[str, Any],
    content_registry: dict[str, Any],
    rendered_html: str = "",
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    pages = deck_spec.get("pages")
    if not isinstance(pages, list):
        return [ContractViolation("C6", "deck_spec must include pages list", "deck_spec.pages")]

    source_registry = _registry_map(content_registry, ("sources", "source_registry"))
    metric_registry = _registry_map(content_registry, ("metrics", "metric_registry"))
    violations.extend(_validate_registry_fields(source_registry, metric_registry))

    meta = deck_spec.get("meta") if isinstance(deck_spec.get("meta"), dict) else {}
    page_chrome = str(meta.get("page_chrome", "")).strip()
    if page_chrome not in SUPPORTED_PAGE_CHROMES:
        violations.append(ContractViolation("C6", f"unsupported page_chrome: {page_chrome}", "deck_spec.meta.page_chrome"))
    if page_chrome == "title_band" and bool(meta.get("running_head")):
        violations.append(
            ContractViolation(
                "C6",
                "page_chrome title_band cannot combine with running_head",
                "deck_spec.meta",
            )
        )
    section_nav = str(meta.get("section_nav", "")).strip()
    if section_nav not in SUPPORTED_SECTION_NAVS:
        violations.append(ContractViolation("C6", f"unsupported section_nav: {section_nav}", "deck_spec.meta.section_nav"))
    tone = str(meta.get("tone", "")).strip()
    if tone not in ("", "report"):
        violations.append(ContractViolation("C6", f"unsupported tone: {tone}", "deck_spec.meta.tone"))
    violations.extend(_validate_series_fields(metric_registry))
    if tone == "report":
        violations.extend(_validate_report_tone(pages, metric_registry))

    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            violations.append(ContractViolation("C6", "page must be an object", f"deck_spec.pages[{page_index}]"))
            continue

        page_path = f"deck_spec.pages[{page_index}]"
        allowed_source_ids = _string_set(page.get("allowed_source_ids"))
        allowed_metric_ids = _string_set(page.get("allowed_metric_ids"))
        # 자동 도출: 페이지에서 허용한 metric의 출처는 자동 허용(designer 수기 중복 제거·#1 결함 뿌리 소멸).
        # metric을 쓰도록 허가했으면 그 출처 인용은 당연히 허가된 것 — C6 보호 목적 불변.
        for metric_id in allowed_metric_ids:
            allowed_source_ids |= _metric_source_ids(metric_id, metric_registry)
        content = page.get("content", page.get("blocks", []))

        for text_path, text in _iter_strings(page, page_path):
            enclosed = ENCLOSED_NUMERAL_PATTERN.search(text)
            if enclosed:
                violations.append(
                    ContractViolation(
                        "C6",
                        f"enclosed numeral is not allowed: {enclosed.group(0)}",
                        text_path,
                    )
                )
            for token_match in METRIC_TOKEN_PATTERN.finditer(text):
                metric_id = token_match.group(1)
                if metric_id not in metric_registry:
                    violations.append(
                        ContractViolation("C6", f"unknown metric id referenced: {metric_id}", text_path)
                    )
                    continue
                if metric_id not in allowed_metric_ids:
                    violations.append(
                        ContractViolation("C6", f"metric_id not in page allowed_metric_ids: {metric_id}", text_path)
                    )

        for block_type, type_path in _iter_content_block_types(content, f"{page_path}.content"):
            if block_type not in SUPPORTED_CONTENT_BLOCK_TYPES:
                violations.append(
                    ContractViolation("C6", f"unsupported content block type: {block_type}", type_path)
                )

        for viz_block, viz_path in _iter_viz_blocks(content, f"{page_path}.content"):
            violations.extend(_validate_viz_block(viz_block, viz_path, metric_registry))

        for src_id, ref_path in _iter_content_refs(content, "src", f"{page_path}.content"):
            if src_id not in source_registry:
                violations.append(ContractViolation("C6", f"unknown source id referenced: {src_id}", ref_path))
            if src_id not in allowed_source_ids:
                violations.append(ContractViolation("C6", f"src_id not in page allowed_source_ids: {src_id}", ref_path))

        for metric_id, ref_path in _iter_content_refs(content, "metric", f"{page_path}.content"):
            metric = metric_registry.get(metric_id)
            if metric is None:
                violations.append(ContractViolation("C6", f"unknown metric id referenced: {metric_id}", ref_path))
                continue
            if metric_id not in allowed_metric_ids:
                violations.append(
                    ContractViolation("C6", f"metric_id not in page allowed_metric_ids: {metric_id}", ref_path)
                )

            metric_source_ids = _metric_source_ids(metric_id, metric_registry)
            for src_id in metric_source_ids:
                if src_id not in source_registry:
                    violations.append(
                        ContractViolation("C6", f"metric source_id missing from source registry: {src_id}", ref_path)
                    )
                if src_id not in allowed_source_ids:
                    violations.append(
                        ContractViolation(
                            "C6",
                            f"metric source_id not in page allowed_source_ids: {src_id}",
                            ref_path,
                        )
                    )

        if page.get("short_title") is None:
            violations.append(ContractViolation("C6", "page must include short_title", f"{page_path}.short_title"))
        elif page_chrome == "title_band" and str(page.get("layout", "statement")) not in {"cover", "divider", "closing", "outro", "source_appendix"}:
            title = str(page.get("short_title", "")).strip()
            if len(title) > TITLE_BAND_MAX_CHARS:
                violations.append(
                    ContractViolation(
                        "C6",
                        f"title_band title exceeds {TITLE_BAND_MAX_CHARS} characters",
                        f"{page_path}.short_title",
                    )
                )
        layout = page.get("layout")
        if layout is None:
            violations.append(ContractViolation("C6", "page must include layout", f"{page_path}.layout"))
        elif str(layout).strip() not in SUPPORTED_LAYOUTS:
            violations.append(ContractViolation("C6", f"unsupported layout: {layout}", f"{page_path}.layout"))
        elif str(layout).strip() == "metric_commentary":
            violations.extend(
                _validate_metric_commentary_page(page, page_path, metric_registry, allowed_metric_ids)
            )

    if rendered_html:
        violations.extend(
            _validate_rendered_content_authority(rendered_html, _metric_registry_numbers(metric_registry))
        )

    return violations


def check_c8_genre_artifacts(
    intake: dict[str, Any],
    evidence_pool: dict[str, Any],
    page_plan: dict[str, Any],
) -> list[ContractViolation]:
    if not _is_market_research_genre(intake.get("genre", "")):
        return []

    violations: list[ContractViolation] = []
    pages = page_plan.get("pages")
    if not isinstance(pages, list):
        pages = []
    artifacts = {
        str(page.get("genre_artifact", "")).strip()
        for page in pages
        if isinstance(page, dict)
    }
    if "taxonomy" not in artifacts:
        violations.append(
            ContractViolation(
                "C8",
                "market-research requires a taxonomy page (genre_artifact='taxonomy' in page_plan)",
                "page_plan.pages",
            )
        )
    if "player_table" not in artifacts:
        violations.append(
            ContractViolation(
                "C8",
                "market-research requires a player_table page (genre_artifact='player_table' in page_plan)",
                "page_plan.pages",
            )
        )

    items = evidence_pool.get("items")
    if not isinstance(items, list):
        items = []
    observation_count = sum(
        1
        for item in items
        if isinstance(item, dict) and str(item.get("source_type", "")).strip().lower() == "observation"
    )
    if observation_count < 5:
        violations.append(
            ContractViolation(
                "C8",
                f"market-research requires at least 5 observation evidence items (found {observation_count})",
                "evidence_pool.items",
            )
        )

    return violations


# 어제(20260810 liaison_proposals) 사고: page-plan은 chart 3개(p05·p09·p10)를 예고했는데
# 최종 spec은 viz=0으로 전부 body/text_table로 강등됐다 — 시각 의도가 조용히 손실됐다.
VIZ_INTENT_PATTERN = re.compile(r"차트|chart|viz|그래프|막대|추이", re.IGNORECASE)


def check_c14_viz_intent_preserved(
    page_plan: dict[str, Any],
    deck_spec: dict[str, Any],
) -> list[ContractViolation]:
    """C14 — page-plan이 예고한 차트 의도가 완전히 소실되지 않았는지만 본다.

    2026-08-10 재설계: 원래 "viz 개수 < 의도 페이지 수 = FAIL"이었으나, 이는 잘못된 전제다.
    데이터가 적은 페이지(2~3개 값 비교 등)는 표나 큰 숫자 카드가 막대그래프보다 오히려
    더 정확하고 빠르게 읽힌다 — 차트 개수를 의도 개수와 맞추라는 요구는 저품질 차트를
    억지로 끼워 넣게 만든다(후추님 8/10 지적). 이 게이트가 실제로 잡아야 하는 것은
    "판단 없이 시각 요소가 통째로 사라진 것"(8/9 리에종 3번 덱: 41장 중 viz 0개)뿐이다.
    부분적 대체(3개 의도 중 1~2개만 viz, 나머지는 표)는 정상적인 콘텐츠 판단으로 간주하고
    통과시킨다. 페이지별 1:1 대응·부분 대체의 타당성 판정은 사람 검토 몫(v2 §E.6).

    05_page_plan.json이 없으면(빈 입력) 비활성 — 기존 워크스페이스 호환.
    """
    plan_pages = page_plan.get("pages") if isinstance(page_plan, dict) else None
    if not isinstance(plan_pages, list) or not plan_pages:
        return []

    intent_page_ids = [
        str(page.get("page_id", "?"))
        for page in plan_pages
        if isinstance(page, dict)
        and VIZ_INTENT_PATTERN.search(f"{page.get('layout_hint', '')} {page.get('content_notes', '')}")
    ]
    if not intent_page_ids:
        return []

    spec_pages = deck_spec.get("pages") if isinstance(deck_spec, dict) else None
    viz_count = sum(
        1
        for page in (spec_pages if isinstance(spec_pages, list) else [])
        if isinstance(page, dict)
        for block in (page.get("content") or [])
        if isinstance(block, dict) and block.get("type") == "viz"
    )
    if viz_count == 0:
        return [
            ContractViolation(
                "C14",
                f"page-plan은 차트 의도 {len(intent_page_ids)}장을 예고했는데 최종 spec에 viz 블록이 "
                f"하나도 없다 — 판단 없는 전면 소실 의심. 의도 페이지: {', '.join(intent_page_ids)}",
                "06_deck_spec.pages[].content[].type=viz",
            )
        ]
    return []


def check_c15_page_count_ceiling(
    page_plan: dict[str, Any],
    deck_spec: dict[str, Any],
) -> list[ContractViolation]:
    """C15 — plan 대비 최종 page 수 팽창 상한(1.2배). page_plan 없으면 비활성.

    어제 사고: page-plan 28장 → 최종 41장(46% 팽창), Loop B 기계적 반분이 원인이었다.
    """
    plan_pages = page_plan.get("pages") if isinstance(page_plan, dict) else None
    if not isinstance(plan_pages, list) or not plan_pages:
        return []
    plan_count = len(plan_pages)
    spec_pages = deck_spec.get("pages") if isinstance(deck_spec, dict) else None
    spec_count = len(spec_pages) if isinstance(spec_pages, list) else 0
    ceiling = math.ceil(plan_count * 1.2)
    if spec_count > ceiling:
        return [
            ContractViolation(
                "C15",
                f"page-plan {plan_count}장 → 최종 spec {spec_count}장 (상한 {ceiling}장 = "
                f"ceil({plan_count}×1.2) 초과)",
                "06_deck_spec.pages",
            )
        ]
    return []


C11_REQUIRED_AXES = ("kpmg", "pwc", "deloitte", "government_stats", "academic")


def check_c11_source_coverage(run_dir: Path | str) -> list[ContractViolation]:
    """수집 커버리지 게이트 (7/7 후추님 — "안 찾음"과 "없음"의 구조적 구분).

    collector는 01_evidence_pool.json 최상위 `source_coverage` 배열로 소스 축별 탐색 기록을 남겨야 한다.
    행 스키마: {"axis": str, "queries": [실행 검색어...], "found": [src_id...], "verdict": "found|none|blocked"}
    - Big3(kpmg·pwc·deloitte) + 정부통계 + 학술 축은 필수.
    - verdict가 none이면 검색어 2개 이상(일반 웹검색 포함)이 있어야 한다 — 검색 없이 '없음' 판정 금지.
    """
    run_path = Path(run_dir)
    pool_path = run_path / "01_evidence_pool.json"
    if not pool_path.exists():
        return []
    try:
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [ContractViolation("C11", f"evidence pool unreadable: {exc}", "01_evidence_pool.json")]
    coverage = pool.get("source_coverage")
    if not isinstance(coverage, list) or not coverage:
        return [
            ContractViolation(
                "C11",
                "source_coverage 부재 — collector는 소스 축별 탐색 기록(axis·queries·verdict) 의무",
                "01_evidence_pool.source_coverage",
            )
        ]
    violations: list[ContractViolation] = []
    seen_axes: set[str] = set()
    for index, row in enumerate(coverage):
        path = f"01_evidence_pool.source_coverage[{index}]"
        if not isinstance(row, dict):
            violations.append(ContractViolation("C11", "coverage row must be an object", path))
            continue
        axis = str(row.get("axis", "")).strip().lower()
        seen_axes.add(axis)
        queries = [q for q in row.get("queries", []) if str(q).strip()] if isinstance(row.get("queries"), list) else []
        verdict = str(row.get("verdict", "")).strip().lower()
        if verdict not in ("found", "none", "blocked"):
            violations.append(ContractViolation("C11", f"unsupported verdict: {verdict}", f"{path}.verdict"))
        if not queries:
            violations.append(ContractViolation("C11", f"axis {axis}: 탐색 검색어 기록 없음", f"{path}.queries"))
        if verdict == "none" and len(queries) < 2:
            violations.append(
                ContractViolation(
                    "C11",
                    f"axis {axis}: 'none' 판정엔 검색어 2개 이상(일반 웹검색 포함) 필요 — 조기 포기 금지",
                    f"{path}.queries",
                )
            )
        if verdict == "found" and not row.get("found"):
            violations.append(ContractViolation("C11", f"axis {axis}: found 판정인데 src 목록 비어 있음", f"{path}.found"))
    for axis in C11_REQUIRED_AXES:
        if axis not in seen_axes:
            violations.append(
                ContractViolation("C11", f"필수 소스 축 미탐색: {axis} (Big3+정부통계+학술 의무)", "01_evidence_pool.source_coverage")
            )
    return violations


def check_c10_collection_evidence(run_dir: Path | str) -> list[ContractViolation]:
    run_path = Path(run_dir)
    try:
        intake = json.loads((run_path / "00_intake.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [ContractViolation("C10", f"C10 intake unreadable: {exc}", "00_intake.json")]
    if not _is_market_research_genre(intake.get("genre", "")):
        return []

    try:
        verified = json.loads((run_path / "02_verified.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [ContractViolation("C10", f"C10 verified registry unreadable: {exc}", "02_verified.json")]

    source_registry = verified.get("source_registry")
    if not isinstance(source_registry, dict):
        source_registry = {}
    sources = [(str(source_id), source) for source_id, source in source_registry.items() if isinstance(source, dict)]

    if not any("doc_type" in source for _, source in sources):
        return [
            ContractViolation(
                "C10",
                "source_registry에 doc_type 필드 부재 — 수집 단계가 C10 스키마 미준수",
                "02_verified.json.source_registry",
            )
        ]

    qualified = [
        (source_id, source)
        for source_id, source in sources
        if str(source.get("tier", "")).strip() == "Tier-A"
        and str(source.get("doc_type", "")).strip().lower() in {"pdf", "official_db_extract"}
    ]

    violations: list[ContractViolation] = []
    if len(qualified) < 5:
        violations.append(
            ContractViolation(
                "C10",
                f"market-research requires at least 5 canonical document sources (found {len(qualified)})",
                "02_verified.json.source_registry",
            )
        )

    for source_id, source in qualified:
        base_path = f"02_verified.json.source_registry.{source_id}"
        local_path = source.get("local_path")
        if not isinstance(local_path, str) or not local_path.strip():
            violations.append(ContractViolation("C10", "canonical source requires local_path", f"{base_path}.local_path"))
        else:
            relative_path = Path(local_path)
            if relative_path.is_absolute():
                violations.append(
                    ContractViolation("C10", "local_path must be relative to run_dir", f"{base_path}.local_path")
                )
            elif not (run_path / relative_path).is_file():
                violations.append(ContractViolation("C10", "local_path file missing", f"{base_path}.local_path"))

        doc_type = str(source.get("doc_type", "")).strip().lower()
        if doc_type == "pdf":
            cited_pages = source.get("cited_pages")
            if not isinstance(cited_pages, list) or not cited_pages or not all(
                isinstance(page, int) or (isinstance(page, str) and page.strip()) for page in cited_pages
            ):
                violations.append(
                    ContractViolation("C10", "pdf canonical source requires non-empty cited_pages", f"{base_path}.cited_pages")
                )
        elif doc_type == "official_db_extract":
            extract_note = source.get("extract_note")
            if not isinstance(extract_note, str) or not extract_note.strip():
                violations.append(
                    ContractViolation(
                        "C10",
                        "official_db_extract canonical source requires extract_note",
                        f"{base_path}.extract_note",
                    )
                )

    return violations


def validate_c12_seed_integrity(
    intake: dict[str, Any],
    verified: dict[str, Any],
    rendered_html: str = "",
) -> list[ContractViolation]:
    provided_sources = intake.get("provided_sources") if isinstance(intake, dict) else None
    if not isinstance(provided_sources, list) or not provided_sources:
        return []

    source_registry = _registry_map(verified, ("source_registry", "sources"))
    sources = {
        source_id: source
        for source_id, source in source_registry.items()
        if isinstance(source, dict)
    }
    violations: list[ContractViolation] = []

    for index, provided_source in enumerate(provided_sources):
        kind, ref = _provided_source_kind_ref(provided_source)
        path = f"00_intake.json.provided_sources[{index}]"
        if not ref:
            violations.append(ContractViolation("C12", "provided source requires ref/url/file", path))
            continue

        matching_source_ids = _matching_seed_source_ids(kind, ref, sources)
        if not matching_source_ids:
            violations.append(
                ContractViolation(
                    "C12",
                    f"provided source missing from source_registry: {ref}",
                    path,
                )
            )
            continue

        seed_source_ids = [
            source_id
            for source_id in matching_source_ids
            if str(sources[source_id].get("provenance") or "research").strip().lower() == "seed"
        ]
        if not seed_source_ids:
            violations.append(
                ContractViolation(
                    "C12",
                    f"provided source must have provenance='seed': {ref}",
                    f"02_verified.json.source_registry.{matching_source_ids[0]}.provenance",
                )
            )

    html = rendered_html if isinstance(rendered_html, str) else ""
    if "제공하신 자료" not in html or "추가 조사" not in html:
        violations.append(
            ContractViolation(
                "C12",
                "rendered deck HTML missing seed/research appendix section headers",
                "rendered_html",
            )
        )

    return violations


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _reviewer_output_is_valid(run_path: Path, reviewer: Any) -> bool:
    if not isinstance(reviewer, dict) or reviewer.get("ok") is not True:
        return False
    file_name = str(reviewer.get("file", "")).strip()
    if not file_name:
        return False
    review_file = run_path / Path(file_name).name
    try:
        text = review_file.read_text(encoding="utf-8").strip()
    except OSError:
        return False
    if text.startswith(("REVIEWER_TIMEOUT", "REVIEWER_FAILED")):
        return False
    # "없음" = 결함 0의 정상 클린 리뷰 — 길이 하한에 걸리면 안 된다(3자 리뷰 2R 코덱스 지적·7/6).
    # 단 부분일치는 "근거 없음" 같은 부실 출력도 통과시킴(3R 코덱스) — 첫 의미 줄이 정확히 "없음"일 때만.
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    if first_line == "없음":
        return True
    return len(text) >= 200


def check_c9_final_review(run_dir: Path | str) -> list[ContractViolation]:
    run_path = Path(run_dir)
    deck_path = run_path / "deck.html"
    if not deck_path.exists():
        return []

    review_path = run_path / "08_external_review.json"
    if not review_path.exists():
        return [
            ContractViolation(
                "C9",
                "C9 final external review missing (run external_review.py)",
                "08_external_review.json",
            )
        ]

    try:
        review = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [
            ContractViolation(
                "C9",
                f"C9 final external review unreadable: {exc}",
                "08_external_review.json",
            )
        ]

    reviewed_hash = str(review.get("deck_html_sha256", ""))
    current_hash = sha256_file(deck_path)
    if reviewed_hash != current_hash:
        return [
            ContractViolation(
                "C9",
                "C9 deck.html changed after external review — re-run external_review.py "
                f"(reviewed {reviewed_hash[:12] or '-'}, current {current_hash[:12]})",
                "deck.html",
            )
        ]

    codex_ok = _reviewer_output_is_valid(run_path, review.get("codex"))
    gemini_ok = _reviewer_output_is_valid(run_path, review.get("gemini"))
    if not codex_ok and not gemini_ok:
        return [
            ContractViolation(
                "C9",
                "C9 both external reviewers failed or produced invalid output",
                "08_external_review.json",
            )
        ]

    return []


def validate_all_contracts(deck: dict[str, Any], raise_on_error: bool = False) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    violations.extend(validate_c1_proposition_dag(deck.get("proposition_dag", {})))
    violations.extend(validate_c2_no_validation_metadata(deck.get("rendered_pages", [])))
    violations.extend(validate_c3_trend_state_transition(deck.get("genre", ""), deck.get("insights", [])))
    violations.extend(validate_c4_citation_tracker(deck.get("insights", [])))
    violations.extend(validate_c5_stage_order(deck.get("stage_log", [])))
    if "deck_spec" in deck or "content_registry" in deck or "rendered_html" in deck:
        violations.extend(
            validate_c6_content_authority(
                deck.get("deck_spec", {}),
                deck.get("content_registry", {}),
                deck.get("rendered_html", ""),
            )
        )
    if "intake" in deck and "evidence_pool" in deck and "page_plan" in deck:
        violations.extend(
            check_c8_genre_artifacts(
                deck.get("intake", {}),
                deck.get("evidence_pool", {}),
                deck.get("page_plan", {}),
            )
        )
    if "intake" in deck:
        violations.extend(
            validate_c12_seed_integrity(
                deck.get("intake", {}),
                deck.get("content_registry", {}),
                deck.get("rendered_html", ""),
            )
        )

    if raise_on_error and violations:
        raise ContractViolation("CONTRACTS", "; ".join(str(item) for item in violations))
    return violations


def _iter_strings(value: Any, path: str):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield from _iter_strings(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_strings(nested, f"{path}[{index}]")


def _registry_map(registry: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    for key in keys:
        value = registry.get(key) if isinstance(registry, dict) else None
        if isinstance(value, dict):
            return {str(item_key): item_value for item_key, item_value in value.items()}
    return {}


def _is_market_research_genre(genre_value: Any) -> bool:
    genre = str(genre_value).lower()
    genre_compact = re.sub(r"[\s_-]+", "", genre)
    return (
        any(term in genre for term in ("market-research", "market_research", "brand-research", "brand_research"))
        or any(term in genre_compact for term in ("marketresearch", "brandresearch", "시장조사", "경쟁분석"))
    )


def _provided_source_kind_ref(provided_source: Any) -> tuple[str, str]:
    kind = ""
    ref = ""
    if isinstance(provided_source, dict):
        kind = str(provided_source.get("kind") or provided_source.get("type") or "").strip().lower()
        for key in ("ref", "url", "file", "path", "local_path"):
            value = provided_source.get(key)
            if isinstance(value, str) and value.strip():
                ref = value.strip()
                break
    elif isinstance(provided_source, str):
        ref = provided_source.strip()

    if kind in {"local", "local_path", "path"}:
        kind = "file"
    if kind not in {"url", "file"}:
        kind = "url" if ref.startswith(("http://", "https://")) else "file"
    return kind, ref


def _matching_seed_source_ids(kind: str, ref: str, sources: dict[str, dict[str, Any]]) -> list[str]:
    if kind == "url":
        return [
            source_id
            for source_id, source in sources.items()
            if str(source.get("url") or "").strip() == ref
        ]

    filename = Path(ref).name
    if not filename:
        return []
    return [
        source_id
        for source_id, source in sources.items()
        if Path(str(source.get("local_path") or "")).name == filename
    ]


def _string_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item) for item in value if str(item).strip()}
    if isinstance(value, tuple):
        return {str(item) for item in value if str(item).strip()}
    return set()


def _metric_direct_source_ids(metric: dict[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    for field in ("source_ids", "source_id", "src_ids", "src_id"):
        value = metric.get(field)
        if isinstance(value, (list, tuple)):
            source_ids |= {str(item) for item in value if str(item).strip()}
        elif value is not None and str(value).strip():
            source_ids.add(str(value))
    return source_ids


def _metric_source_ids(metric_id: str, metric_registry: dict[str, Any], seen: set[str] | None = None) -> set[str]:
    seen = set(seen or set())
    if metric_id in seen:
        return set()
    seen.add(metric_id)
    metric = metric_registry.get(metric_id)
    if not isinstance(metric, dict):
        return set()

    # Renderer accepts the historical singular/src aliases as well as the canonical list.
    # Keep authority validation on the same registry contract so a cited metric cannot lose
    # its source merely because the producer emitted `source_id` instead of `source_ids`.
    source_ids = _metric_direct_source_ids(metric)
    derived_from = metric.get("derived_from")
    if isinstance(derived_from, list):
        for ref_id in derived_from:
            ref = str(ref_id).strip()
            if ref:
                source_ids |= _metric_source_ids(ref, metric_registry, seen)
    return source_ids


def _iter_content_refs(value: Any, ref_type: str, path: str = "deck_spec.pages[].content"):
    scalar_keys = {"src": {"src_id", "source_id"}, "metric": {"metric_id"}}[ref_type]
    list_keys = {"src": {"src_ids", "source_ids"}, "metric": {"metric_ids"}}[ref_type]

    if isinstance(value, dict):
        for key, nested in value.items():
            next_path = f"{path}.{key}"
            if key in scalar_keys and str(nested).strip():
                yield str(nested), next_path
            elif key in list_keys and isinstance(nested, list):
                for index, item in enumerate(nested):
                    if str(item).strip():
                        yield str(item), f"{next_path}[{index}]"
            else:
                yield from _iter_content_refs(nested, ref_type, next_path)
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_content_refs(nested, ref_type, f"{path}[{index}]")


def _iter_content_block_types(value: Any, path: str):
    if isinstance(value, dict):
        if "type" in value:
            yield str(value.get("type", "text")), f"{path}.type"
        for key, nested in value.items():
            yield from _iter_content_block_types(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_content_block_types(nested, f"{path}[{index}]")


def _iter_viz_blocks(value: Any, path: str):
    if isinstance(value, dict):
        if value.get("type") == "viz":
            yield value, path
        for key, nested in value.items():
            yield from _iter_viz_blocks(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _iter_viz_blocks(nested, f"{path}[{index}]")


def _validate_viz_block(
    block: dict[str, Any],
    path: str,
    metric_registry: dict[str, Any] | None = None,
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    metric_registry = metric_registry or {}
    chart = str(block.get("chart", "")).strip()
    if chart not in SUPPORTED_VIZ_CHART_TYPES:
        violations.append(ContractViolation("C6", f"unsupported viz chart type: {chart}", f"{path}.chart"))

    source_caption = str(block.get("source_caption", "")).strip()
    if source_caption not in SUPPORTED_VIZ_SOURCE_CAPTIONS:
        violations.append(
            ContractViolation("C6", f"unsupported viz source_caption: {source_caption}", f"{path}.source_caption")
        )

    title_style = str(block.get("title_style", "")).strip()
    if title_style not in SUPPORTED_VIZ_TITLE_STYLES:
        violations.append(ContractViolation("C6", f"unsupported viz title_style: {title_style}", f"{path}.title_style"))

    size = str(block.get("size", "")).strip()
    if size not in ("", "hero"):
        violations.append(ContractViolation("C6", f"unsupported viz size: {size}", f"{path}.size"))

    for field in ("title", "note"):
        text = block.get(field)
        if isinstance(text, str) and RAW_NUMBER_PATTERN.search(text):
            violations.append(ContractViolation("C6", f"viz {field} contains raw number", f"{path}.{field}"))

    axis_labels = block.get("axis_labels")
    if axis_labels is not None:
        if chart != "swot_quad" or not isinstance(axis_labels, dict):
            violations.append(ContractViolation("C6", "axis_labels is only supported as an object on swot_quad", f"{path}.axis_labels"))
        else:
            for axis in ("x", "y"):
                labels = axis_labels.get(axis)
                if not isinstance(labels, list) or len(labels) != 2 or not all(isinstance(label, str) and label.strip() for label in labels):
                    violations.append(ContractViolation("C6", f"swot_quad axis_labels.{axis} must include two text labels", f"{path}.axis_labels.{axis}"))
                elif any(RAW_NUMBER_PATTERN.search(label) for label in labels):
                    violations.append(ContractViolation("C6", f"swot_quad axis_labels.{axis} contains raw number", f"{path}.axis_labels.{axis}"))

    for field in ("value", "unit", "values", "data"):
        if field in block:
            violations.append(ContractViolation("C6", f"viz block must not include direct {field}", f"{path}.{field}"))

    annotations = block.get("annotations")
    if annotations is not None:
        violations.extend(_validate_viz_annotations(annotations, chart, block, path, metric_registry))

    series = block.get("series")
    if not isinstance(series, list) or not series:
        violations.append(ContractViolation("C6", "viz block must include non-empty series", f"{path}.series"))
        return violations

    for index, item in enumerate(series):
        item_path = f"{path}.series[{index}]"
        if not isinstance(item, dict):
            violations.append(ContractViolation("C6", "viz series item must be an object", item_path))
            continue
        role = str(item.get("role", "")).strip()
        if role not in SUPPORTED_VIZ_SERIES_ROLES:
            violations.append(ContractViolation("C6", f"unsupported viz series role: {role}", f"{item_path}.role"))
        if chart not in VIZ_CHARTS_WITHOUT_REQUIRED_METRIC and not str(item.get("metric_id", "")).strip():
            violations.append(ContractViolation("C6", "viz series item must include metric_id", f"{item_path}.metric_id"))
        label = item.get("label")
        if chart in {"gantt", "pictograph"} and not str(label or "").strip():
            violations.append(ContractViolation("C6", f"{chart} series item must include label", f"{item_path}.label"))
        # 연도(2018·2024 등)는 데이터 값이 아니라 축 키 — rendered authority 검사와 동일 면제(R4 시계열 계약·연도 키).
        if isinstance(label, str) and RAW_NUMBER_PATTERN.search(FOUR_DIGIT_YEAR_PATTERN.sub("", label)):
            violations.append(ContractViolation("C6", "viz label contains raw number", f"{item_path}.label"))
        if chart == "swot_quad":
            items = item.get("items")
            if not isinstance(items, list):
                violations.append(ContractViolation("C6", "swot_quad series item must include items list", f"{item_path}.items"))
            else:
                for item_index, text in enumerate(items):
                    text_path = f"{item_path}.items[{item_index}]"
                    if not isinstance(text, str):
                        violations.append(ContractViolation("C6", "swot_quad item must be text", text_path))
                    elif RAW_NUMBER_PATTERN.search(text):
                        violations.append(ContractViolation("C6", "swot_quad item contains raw number", text_path))
        if chart == "gantt":
            start = item.get("start")
            end = item.get("end")
            month_pattern = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
            if not isinstance(start, str) or not month_pattern.fullmatch(start):
                violations.append(ContractViolation("C6", "gantt series item start must use YYYY-MM", f"{item_path}.start"))
            if not isinstance(end, str) or not month_pattern.fullmatch(end):
                violations.append(ContractViolation("C6", "gantt series item end must use YYYY-MM", f"{item_path}.end"))
            if isinstance(start, str) and isinstance(end, str) and month_pattern.fullmatch(start) and month_pattern.fullmatch(end) and end < start:
                violations.append(ContractViolation("C6", "gantt series item end must not precede start", f"{item_path}.end"))
            lane = item.get("lane")
            if lane is not None and (not isinstance(lane, int) or isinstance(lane, bool) or not 0 <= lane <= 7):
                violations.append(ContractViolation("C6", "gantt series item lane must be within 0..7", f"{item_path}.lane"))
        if chart == "pictograph":
            total = item.get("total")
            filled = item.get("filled")
            if not isinstance(total, int) or isinstance(total, bool) or total < 1:
                violations.append(ContractViolation("C6", "pictograph total must be a positive integer", f"{item_path}.total"))
            elif total > 20:
                violations.append(ContractViolation("C6", "pictograph total must be at most 20", f"{item_path}.total"))
            if not isinstance(filled, int) or isinstance(filled, bool) or filled < 0:
                violations.append(ContractViolation("C6", "pictograph filled must be a non-negative integer", f"{item_path}.filled"))
            elif isinstance(total, int) and not isinstance(total, bool) and filled > total:
                violations.append(ContractViolation("C6", "pictograph filled must not exceed total", f"{item_path}.filled"))
        if chart == "fin_table":
            cells = item.get("cells")
            if not isinstance(cells, list) or not cells:
                violations.append(ContractViolation("C6", "fin_table series item must include cells list", f"{item_path}.cells"))
            else:
                for cell_index, cell in enumerate(cells):
                    cell_path = f"{item_path}.cells[{cell_index}]"
                    if not isinstance(cell, dict):
                        violations.append(ContractViolation("C6", "fin_table cell must be an object", cell_path))
                        continue
                    has_metric = bool(str(cell.get("metric_id", "")).strip())
                    has_text = bool(str(cell.get("text", "")).strip())
                    if has_metric == has_text:
                        violations.append(
                            ContractViolation("C6", "fin_table cell must include exactly one of metric_id or text", cell_path)
                        )
                    text = cell.get("text")
                    if isinstance(text, str) and RAW_NUMBER_PATTERN.search(text):
                        violations.append(ContractViolation("C6", "fin_table text cell contains raw number", f"{cell_path}.text"))
        if chart == "two_by_two":
            for axis_field in ("x", "y"):
                axis_value = item.get(axis_field)
                if not isinstance(axis_value, (int, float)) or not 0 <= axis_value <= 1:
                    violations.append(
                        ContractViolation("C6", f"two_by_two item {axis_field} must be a number within 0..1", f"{item_path}.{axis_field}")
                    )
        if chart == "tradeoff":
            side = str(item.get("side", "")).strip()
            if side not in {"left", "right"}:
                violations.append(ContractViolation("C6", f"tradeoff item side must be left or right, got: {side}", f"{item_path}.side"))
        for field in ("value", "unit", "values", "data"):
            if field in item:
                violations.append(ContractViolation("C6", f"viz series must not include direct {field}", f"{item_path}.{field}"))

    # R5 남발 방지 게이트(DESIGN_R5 §3): 빈약한 논증 도식이 페이지 주인공이 되는 것 방지.
    if chart == "pyramid" and str(block.get("pyramid_style", "")).strip() != "hierarchy":
        evidence_count = sum(1 for item in series if isinstance(item, dict) and str(item.get("role", "")).strip() == "evidence")
        if evidence_count < ARG_DIAGRAM_MIN_SLOTS["pyramid"]:
            violations.append(
                ContractViolation(
                    "C6",
                    f"ARG_DIAGRAM_THIN: pyramid must include at least {ARG_DIAGRAM_MIN_SLOTS['pyramid']} evidence items (got {evidence_count})",
                    f"{path}.series",
                )
            )
    if chart == "pyramid" and str(block.get("pyramid_style", "")).strip() == "hierarchy" and not 3 <= len(series) <= 5:
        violations.append(ContractViolation("C6", "hierarchy pyramid must include 3 to 5 layers", f"{path}.series"))
    if chart == "causal_chain" and len(series) < ARG_DIAGRAM_MIN_SLOTS["causal_chain"]:
        violations.append(
            ContractViolation(
                "C6",
                f"ARG_DIAGRAM_THIN: causal_chain must include at least {ARG_DIAGRAM_MIN_SLOTS['causal_chain']} nodes (got {len(series)})",
                f"{path}.series",
            )
        )
    if chart == "two_by_two" and len(series) < ARG_DIAGRAM_MIN_SLOTS["two_by_two"]:
        violations.append(
            ContractViolation(
                "C6",
                f"ARG_DIAGRAM_THIN: two_by_two must include at least {ARG_DIAGRAM_MIN_SLOTS['two_by_two']} items (got {len(series)})",
                f"{path}.series",
            )
        )
    if chart == "tradeoff":
        left_count = sum(1 for item in series if isinstance(item, dict) and str(item.get("side", "")).strip() == "left")
        right_count = sum(1 for item in series if isinstance(item, dict) and str(item.get("side", "")).strip() == "right")
        if left_count < 1 or right_count < 1:
            violations.append(
                ContractViolation(
                    "C6",
                    f"ARG_DIAGRAM_THIN: tradeoff must include at least 1 item per side (left={left_count}, right={right_count})",
                    f"{path}.series",
                )
            )
    if chart == "gantt":
        if len(series) > 8:
            violations.append(ContractViolation("C6", "gantt must include at most 8 series items", f"{path}.series"))
        valid_months = [
            int(value[:4]) * 12 + int(value[5:7]) - 1
            for item in series if isinstance(item, dict)
            for value in (item.get("start"), item.get("end"))
            if isinstance(value, str) and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value)
        ]
        if valid_months and max(valid_months) - min(valid_months) + 1 > 36:
            violations.append(ContractViolation("C6", "gantt schedule must span at most 36 months", f"{path}.series"))
    if chart == "pictograph" and len(series) != 1:
        violations.append(ContractViolation("C6", "pictograph must include exactly one series item", f"{path}.series"))

    return violations


def _validate_viz_annotations(
    annotations: Any,
    chart: str,
    block: dict[str, Any],
    path: str,
    metric_registry: dict[str, Any],
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    if chart not in SUPPORTED_VIZ_ANNOTATION_CHARTS:
        violations.append(
            ContractViolation(
                "C6",
                "annotations are supported only for multi_line, rising_columns, quarterly_bars",
                f"{path}.annotations",
            )
        )
    if not isinstance(annotations, list):
        return [*violations, ContractViolation("C6", "viz annotations must be a list", f"{path}.annotations")]

    series = block.get("series") if isinstance(block.get("series"), list) else []
    series_keys = {
        str(item.get("label", "")).strip()
        for item in series
        if isinstance(item, dict) and str(item.get("label", "")).strip()
    }
    for index, annotation in enumerate(annotations):
        annotation_path = f"{path}.annotations[{index}]"
        if not isinstance(annotation, dict):
            violations.append(ContractViolation("C6", "viz annotation must be an object", annotation_path))
            continue

        fixed_anchor_keys = {"x", "y", "left", "top", "right", "bottom", "px", "py"}
        if fixed_anchor_keys & set(annotation):
            violations.append(
                ContractViolation("C6", "annotation must not use fixed pixel anchors", annotation_path)
            )

        kind = str(annotation.get("kind", "")).strip()
        if kind not in SUPPORTED_VIZ_ANNOTATION_KINDS:
            violations.append(ContractViolation("C6", f"unsupported viz annotation kind: {kind}", f"{annotation_path}.kind"))
            continue

        if kind == "callout":
            metric_id = str(annotation.get("metric_id", "")).strip()
            metric = metric_registry.get(metric_id)
            if not metric_id:
                violations.append(ContractViolation("C6", "callout annotation requires metric_id", f"{annotation_path}.metric_id"))
            elif not _is_derived_metric(metric):
                violations.append(
                    ContractViolation(
                        "C6",
                        "callout annotation metric must reference a derived metric",
                        f"{annotation_path}.metric_id",
                    )
                )
            shape = str(annotation.get("shape", "")).strip()
            if shape not in SUPPORTED_VIZ_ANNOTATION_SHAPES:
                violations.append(ContractViolation("C6", f"unsupported callout annotation shape: {shape}", f"{annotation_path}.shape"))
            _validate_annotation_series_index(annotation, "anchor_series", series, annotation_path, violations, required=False)
            continue

        if kind in {"endpoint_value", "trend_arrow"}:
            _validate_annotation_series_index(annotation, "series", series, annotation_path, violations, required=True)
            continue

        if kind == "event_band":
            label = annotation.get("label")
            if not isinstance(label, str) or not label.strip():
                violations.append(ContractViolation("C6", "event_band requires label", f"{annotation_path}.label"))
            elif RAW_NUMBER_PATTERN.search(label):
                violations.append(ContractViolation("C6", "event_band label contains raw number", f"{annotation_path}.label"))
            for field in ("from_key", "to_key"):
                if not isinstance(annotation.get(field), str) or not str(annotation.get(field)).strip():
                    violations.append(ContractViolation("C6", f"event_band requires {field}", f"{annotation_path}.{field}"))
                elif series_keys and str(annotation.get(field)).strip() not in series_keys:
                    violations.append(ContractViolation("C6", f"event_band {field} must reference a series label", f"{annotation_path}.{field}"))

    return violations


def _validate_annotation_series_index(
    annotation: dict[str, Any],
    field: str,
    series: list[Any],
    path: str,
    violations: list[ContractViolation],
    required: bool,
) -> None:
    raw_index = annotation.get(field)
    if raw_index is None:
        if required:
            violations.append(ContractViolation("C6", f"annotation requires {field}", f"{path}.{field}"))
        return
    if not isinstance(raw_index, int) or raw_index < 0 or raw_index >= len(series):
        violations.append(ContractViolation("C6", f"annotation {field} out of range", f"{path}.{field}"))


def _validate_metric_commentary_page(
    page: dict[str, Any],
    page_path: str,
    metric_registry: dict[str, Any],
    allowed_metric_ids: set[str],
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    rows = page.get("rows")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 2:
        return [
            ContractViolation(
                "C6",
                "metric_commentary rows must include 1 to 2 rows",
                f"{page_path}.rows",
            )
        ]

    for row_index, row in enumerate(rows):
        row_path = f"{page_path}.rows[{row_index}]"
        if not isinstance(row, dict):
            violations.append(ContractViolation("C6", "metric_commentary row must be an object", row_path))
            continue
        for field in ("heading_metric_id", "headline_metric_id"):
            _validate_metric_ref(row.get(field), f"{row_path}.{field}", metric_registry, allowed_metric_ids, violations)

        headline_metric = metric_registry.get(str(row.get("headline_metric_id", "")).strip())
        if not isinstance(headline_metric, dict) or str(headline_metric.get("derivation", "")).strip() != "delta_pct":
            violations.append(
                ContractViolation(
                    "C6",
                    "metric_commentary headline_metric_id must reference delta_pct",
                    f"{row_path}.headline_metric_id",
                )
            )

        bullets = row.get("bullets")
        if not isinstance(bullets, list):
            violations.append(ContractViolation("C6", "metric_commentary bullets must be a list", f"{row_path}.bullets"))
        else:
            for bullet_index, bullet in enumerate(bullets):
                bullet_path = f"{row_path}.bullets[{bullet_index}]"
                if not isinstance(bullet, dict):
                    violations.append(ContractViolation("C6", "metric_commentary bullet must be an object", bullet_path))
                    continue
                label = str(bullet.get("label", "")).strip()
                if label not in {"YoY", "QoQ"}:
                    violations.append(
                        ContractViolation("C6", "metric_commentary bullet label must be YoY or QoQ", f"{bullet_path}.label")
                    )
                _validate_metric_ref(bullet.get("metric_id"), f"{bullet_path}.metric_id", metric_registry, allowed_metric_ids, violations)
                bullet_metric = metric_registry.get(str(bullet.get("metric_id", "")).strip())
                if not isinstance(bullet_metric, dict) or str(bullet_metric.get("derivation", "")).strip() != "delta_pct":
                    violations.append(
                        ContractViolation("C6", "metric_commentary bullet metric_id must reference delta_pct", f"{bullet_path}.metric_id")
                    )

        chart = row.get("chart")
        if not isinstance(chart, dict):
            violations.append(ContractViolation("C6", "metric_commentary row must include chart", f"{row_path}.chart"))
            continue
        if str(chart.get("chart", "")).strip() != "quarterly_bars":
            violations.append(
                ContractViolation("C6", "metric_commentary chart must be quarterly_bars", f"{row_path}.chart.chart")
            )
        chart_block = {"type": "viz", **chart}
        violations.extend(_validate_viz_block(chart_block, f"{row_path}.chart", metric_registry))
        for metric_id, ref_path in _iter_content_refs(chart, "metric", f"{row_path}.chart"):
            _validate_metric_ref(metric_id, ref_path, metric_registry, allowed_metric_ids, violations)

    return violations


def _validate_metric_ref(
    raw_metric_id: Any,
    path: str,
    metric_registry: dict[str, Any],
    allowed_metric_ids: set[str],
    violations: list[ContractViolation],
) -> None:
    metric_id = str(raw_metric_id or "").strip()
    if not metric_id:
        violations.append(ContractViolation("C6", "metric_commentary requires metric_id", path))
        return
    if metric_id not in metric_registry:
        violations.append(ContractViolation("C6", f"unknown metric id referenced: {metric_id}", path))
    if metric_id not in allowed_metric_ids:
        violations.append(ContractViolation("C6", f"metric_id not in page allowed_metric_ids: {metric_id}", path))


def _validate_registry_fields(
    source_registry: dict[str, Any],
    metric_registry: dict[str, Any],
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    for src_id, source in source_registry.items():
        if not isinstance(source, dict):
            continue
        if "short_name" in source and not isinstance(source.get("short_name"), str):
            violations.append(
                ContractViolation("C6", "source short_name must be text", f"content_registry.sources.{src_id}.short_name")
            )
    for metric_id, metric in metric_registry.items():
        if not isinstance(metric, dict):
            continue
        if "period" in metric and not isinstance(metric.get("period"), str):
            violations.append(
                ContractViolation("C6", "metric period must be text", f"content_registry.metrics.{metric_id}.period")
            )
        is_derived = (
            str(metric.get("status", "")).strip() == "derived"
            or "derivation" in metric
            or "derived_from" in metric
        )
        if not is_derived:
            continue
        if str(metric.get("status", "")).strip() != "derived":
            violations.append(
                ContractViolation("C6", "derived metric status must be derived", f"content_registry.metrics.{metric_id}.status")
            )
        derivation = str(metric.get("derivation", "")).strip()
        if derivation not in SUPPORTED_METRIC_DERIVATIONS:
            violations.append(
                ContractViolation("C6", f"unsupported metric derivation: {derivation}", f"content_registry.metrics.{metric_id}.derivation")
            )
        derived_from = metric.get("derived_from")
        if not isinstance(derived_from, list) or len(derived_from) < 2:
            violations.append(
                ContractViolation("C6", "derived metric must include at least 2 derived_from refs", f"content_registry.metrics.{metric_id}.derived_from")
            )
        else:
            for ref_index, ref_id in enumerate(derived_from):
                ref = str(ref_id).strip()
                if not ref or ref not in metric_registry:
                    violations.append(
                        ContractViolation(
                            "C6",
                            f"derived_from references unknown metric: {ref}",
                            f"content_registry.metrics.{metric_id}.derived_from[{ref_index}]",
                        )
                    )
        if _metric_direct_source_ids(metric):
            violations.append(
                ContractViolation("C6", "derived metric source_ids must be empty", f"content_registry.metrics.{metric_id}.source_ids")
            )
        violations.extend(_recompute_derived_metric(metric_id, metric, metric_registry))

    for metric_id in metric_registry:
        if _has_metric_cycle(metric_id, metric_registry, [], set()):
            violations.append(
                ContractViolation("C6", "derived metric cycle", f"content_registry.metrics.{metric_id}.derived_from")
            )
            break
    return violations


def _validate_r2_registry_fields(
    source_registry: dict[str, Any],
    metric_registry: dict[str, Any],
) -> list[ContractViolation]:
    return _validate_registry_fields(source_registry, metric_registry)


def _series_groups(metric_registry: dict[str, Any]) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    groups: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for metric_id, metric in metric_registry.items():
        if not isinstance(metric, dict):
            continue
        series_id = str(metric.get("series_id", "")).strip()
        if series_id:
            groups.setdefault(series_id, []).append((metric_id, metric))
    return groups


def _validate_series_fields(metric_registry: dict[str, Any]) -> list[ContractViolation]:
    # 시계열 계약 (7/7 R4): 점 1개 = metric 1개, 같은 series_id로 묶임. 차트 세울 재료의 무결성.
    violations: list[ContractViolation] = []
    for series_id, members in _series_groups(metric_registry).items():
        seen_keys: set[str] = set()
        units: set[str] = set()
        for metric_id, metric in members:
            path = f"content_registry.metrics.{metric_id}"
            if _is_derived_metric(metric):
                violations.append(ContractViolation("C6", "derived metric cannot join a series", f"{path}.series_id"))
            key = str(metric.get("series_key", "")).strip()
            if not key:
                violations.append(ContractViolation("C6", "series member requires series_key", f"{path}.series_key"))
                continue
            if key in seen_keys:
                violations.append(ContractViolation("C6", f"duplicate series_key '{key}' in series {series_id}", f"{path}.series_key"))
            seen_keys.add(key)
            units.add(str(metric.get("unit", "")).strip())
        if len(units) > 1:
            violations.append(
                ContractViolation("C6", f"series {series_id} mixes units: {sorted(units)}", f"content_registry.series.{series_id}")
            )
    return violations


_NON_BODY_LAYOUTS = {"cover", "divider", "closing", "outro", "source_appendix", "toc", "index"}


def _chartable_series_count(metric_registry: dict[str, Any]) -> int:
    count = 0
    for _series_id, members in _series_groups(metric_registry).items():
        keys = {str(m.get("series_key", "")).strip() for _mid, m in members if str(m.get("series_key", "")).strip()}
        if len(keys) >= 4:
            count += 1
    return count


def _validate_report_tone(pages: list[Any], metric_registry: dict[str, Any]) -> list[ContractViolation]:
    # 리포트 판짜기 게이트 (7/7 R4): 시계열 재료 없이·차트 주인공 페이지 없이 "리포트 톤"을 자칭 못 하게.
    violations: list[ContractViolation] = []
    if _chartable_series_count(metric_registry) < 3:
        violations.append(
            ContractViolation(
                "C6",
                "REPORT_TONE_DATA_THIN: report tone requires >=3 chartable series (>=4 points each) — 수집 단계로 되돌릴 것",
                "content_registry.metrics",
            )
        )
    body_pages = 0
    hero_pages = 0
    for page in pages:
        if not isinstance(page, dict):
            continue
        layout = str(page.get("layout", "")).strip()
        if layout in _NON_BODY_LAYOUTS:
            continue
        body_pages += 1
        content = page.get("content") if isinstance(page.get("content"), list) else []
        viz_blocks = [b for b in content if isinstance(b, dict) and b.get("type") == "viz"]
        other_blocks = [b for b in content if isinstance(b, dict) and b.get("type") != "viz"]
        if len(viz_blocks) == 1 and len(other_blocks) <= 2:
            hero_pages += 1
    if body_pages and hero_pages * 2 < body_pages:
        violations.append(
            ContractViolation(
                "C6",
                f"REPORT_TONE_COMPOSITION: chart-hero pages {hero_pages}/{body_pages} < 50% — 판짜기 단계로 되돌릴 것",
                "deck_spec.pages",
            )
        )
    return violations


def _is_derived_metric(metric: Any) -> bool:
    return isinstance(metric, dict) and str(metric.get("status", "")).strip() == "derived"


_DERIVATION_ARITY = {"cagr": 2, "delta_pct": 2, "delta_abs": 2, "multiple": 2, "share": 2}


def _metric_number(metric: Any) -> float | None:
    if not isinstance(metric, dict):
        return None
    raw = str(metric.get("value", "")).strip().replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


def _period_span_years(metric: Any) -> float | None:
    years = re.findall(r"\b(?:19|20)\d{2}\b", str((metric or {}).get("period", "")))
    if len(years) < 2:
        return None
    span = abs(int(years[-1]) - int(years[0]))
    return float(span) if span else None


def _recompute_derived_metric(
    metric_id: str,
    metric: dict[str, Any],
    metric_registry: dict[str, Any],
) -> list[ContractViolation]:
    # 검산 게이트 (7/7 제대리 리뷰 root fix): 파생값이 verifier 문서 프로토콜에만 있으면
    # 틀린 파생값이 계약을 통과한다 — 원천값으로 재계산해 등재값과 대조한다.
    path = f"content_registry.metrics.{metric_id}"
    derivation = str(metric.get("derivation", "")).strip()
    arity = _DERIVATION_ARITY.get(derivation)
    derived_from = metric.get("derived_from")
    if arity is None or not isinstance(derived_from, list) or len(derived_from) < 2:
        return []  # enum·최소 개수 위반은 상위에서 이미 보고됨
    violations: list[ContractViolation] = []
    if len(derived_from) != arity:
        violations.append(
            ContractViolation("C6", f"derivation {derivation} requires exactly {arity} derived_from refs", f"{path}.derived_from")
        )
        return violations
    if not str(metric.get("formula_note", "")).strip():
        violations.append(ContractViolation("C6", "derived metric must include formula_note", f"{path}.formula_note"))
    a = _metric_number(metric_registry.get(str(derived_from[0]).strip()))
    b = _metric_number(metric_registry.get(str(derived_from[1]).strip()))
    registered = _metric_number(metric)
    if a is None or b is None or registered is None:
        violations.append(
            ContractViolation("C6", "derived metric requires numeric single-value sources for recompute", f"{path}.derived_from")
        )
        return violations
    expected: float | None = None
    if derivation == "delta_abs":
        expected = b - a
    elif derivation == "delta_pct" and a:
        expected = (b - a) / a * 100.0
    elif derivation == "multiple" and a:
        expected = b / a
    elif derivation == "share" and b:
        expected = a / b * 100.0
    elif derivation == "cagr":
        years = _period_span_years(metric)
        if years and a > 0 and b > 0:
            expected = ((b / a) ** (1.0 / years) - 1.0) * 100.0
    if expected is None:
        violations.append(
            ContractViolation("C6", f"derivation {derivation} not recomputable (zero source or missing period years)", path)
        )
        return violations
    tolerance = max(abs(expected) * 0.02, 0.51)
    if abs(registered - expected) > tolerance:
        violations.append(
            ContractViolation("C6", f"derived metric value {registered} != recomputed {expected:.2f} ({derivation})", f"{path}.value")
        )
    return violations


def _has_metric_cycle(
    metric_id: str,
    metric_registry: dict[str, Any],
    stack: list[str],
    clean: set[str],
) -> bool:
    if metric_id in clean:
        return False
    if metric_id in stack:
        return True
    metric = metric_registry.get(metric_id)
    if not isinstance(metric, dict):
        clean.add(metric_id)
        return False
    derived_from = metric.get("derived_from")
    if not isinstance(derived_from, list):
        clean.add(metric_id)
        return False
    stack.append(metric_id)
    for ref in derived_from:
        if _has_metric_cycle(str(ref).strip(), metric_registry, stack, clean):
            return True
    stack.pop()
    clean.add(metric_id)
    return False


def _validate_rendered_content_authority(
    rendered_html: str,
    backed_numbers: set[str] | None = None,
) -> list[ContractViolation]:
    parser = _RenderedAuthorityParser(backed_numbers or set())
    parser.feed(rendered_html)
    return parser.violations


class _RenderedAuthorityParser(HTMLParser):
    _NUMBER_PATTERN = RAW_NUMBER_PATTERN
    _ENCLOSED_NUMERAL_PATTERN = ENCLOSED_NUMERAL_PATTERN

    def __init__(self, backed_numbers: set[str]) -> None:
        super().__init__()
        self.stack: list[dict[str, str]] = []
        self.violations: list[ContractViolation] = []
        self._backed_numbers = backed_numbers
        self._manual_source_seen = False
        self._untagged_number_seen = False
        self._enclosed_numeral_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: value or "" for key, value in attrs}
        attr_map["_tag"] = tag
        self.stack.append(attr_map)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].get("_tag") == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not data.strip() or self._inside_ignored_tag():
            return
        if "출처:" in data and not self._manual_source_seen and not self._inside_generated_caption():
            self._manual_source_seen = True
            self.violations.append(
                ContractViolation("C6", "manual source label in rendered output; citations must be generated", "rendered_html")
            )
        enclosed = self._ENCLOSED_NUMERAL_PATTERN.search(data)
        if enclosed and not self._enclosed_numeral_seen:
            self._enclosed_numeral_seen = True
            self.violations.append(
                ContractViolation(
                    "C6",
                    f"enclosed numeral in rendered output: {enclosed.group(0)}",
                    "rendered_html",
                )
            )
        if not self._inside_authorized_numeric_context() and not self._untagged_number_seen:
            unauthorized_number = any(
                not self._authorized_number_match(data, match)
                for match in self._NUMBER_PATTERN.finditer(data)
            )
        else:
            unauthorized_number = False
        if unauthorized_number:
            self._untagged_number_seen = True
            self.violations.append(
                ContractViolation("C6", "untagged number in rendered output; use metric_id injection", "rendered_html")
            )

    def _inside_generated_caption(self) -> bool:
        # visual-source-caption = 렌더러가 registry에서 생성한 출처 캡션 (7/7 — "출처:" 한국어화).
        # manual source label 금지는 writer 손글씨를 막는 것이지 렌더러 생성물이 아니다.
        return any("visual-source-caption" in item.get("class", "") for item in self.stack)

    def _inside_ignored_tag(self) -> bool:
        # <title>은 문서 메타(브라우저 탭)지 슬라이드 콘텐츠가 아니다 — 연도 포함 제목이
        # C6에 걸려 문서 제목에서 연도를 빼는 우회가 반복되던 문제의 근본 풀이(7/2).
        return any(item.get("_tag") in {"script", "style", "title"} for item in self.stack)

    def _inside_authorized_numeric_context(self) -> bool:
        for item in self.stack:
            classes = set(item.get("class", "").split())
            if "data-metric-id" in item or "data-src-id" in item or "data-page-number" in item:
                return True
            # running-head-frac = 러닝헤드 크롬의 페이지분수(NN/총) — 렌더러 생성 페이지번호라 page-number와 동일 면제(배치3 running_head 도입 시 화이트리스트 누락분·7/4).
            # verified-badge = 렌더러가 registry에서 계산한 출처 수 — page-number와 동일 면제(레버2·7/5).
            if classes & {
                "page-number",
                "citation-index",
                "source-index",
                "source-more",
                "eyebrow",
                "cover-eyebrow",
                "copyright",
                "running-head-frac",
                "verified-badge",
                "fin-period",
                "visual-source-caption",
                "viz-structured-number",
                "section-nav",
                "section-nav-item",
                "section-nav-dot",
                "section-nav-toc-item",
            }:
                return True
            # 간지 프리뷰(divider-items) = short_title 복제 — 원본(h1)이 면제이므로 복제도 면제(7/3).
            # 각주(footnote-row) = 조사 정의 병기·조건부 캐비앳이 본질이라 숫자 필요(writing-standard 9b·D-12).
            # 단 각주로 본문 통계를 밀반입하는 건 qa-reviewer 판정 대상(designer.md 명시).
            # title-band(-text) = page_chrome:"title_band" 크롬의 aria-hidden 장식용 제목 복제
            # (동일 title_text를 h1과 함께 배경에 한 번 더 렌더) — divider-items와 동일 근거로 면제(7/22).
            if classes & {"divider-items", "footnote-row", "title-band", "title-band-text"}:
                return True
            # 조용한 간지 뼈대(divider_style:"quiet")의 거대 숫자 = 파트 순번(PART N과 동일 성격의
            # 구조 표시) — standard 뼈대의 "eyebrow divider-part"(PART n)와 같은 면제 근거(7/3).
            if classes & {"divider-quiet-num"}:
                return True
            # 제목·헤드라인·표지 lockup = 서사 텍스트(연도·순번·개수). 본문 통계 수치는
            # 이 면제가 없어 여전히 metric_id 주입을 강제 — C6 본문 규율은 그대로 유지.
            if item.get("_tag") in {"h1", "h2"} or classes & {"block-title", "cover-lockup"}:
                return True
        return False

    def _authorized_number_match(self, data: str, match: re.Match[str]) -> bool:
        number = _normalize_number_token(match.group(0))
        if not number:
            return True
        if number in self._backed_numbers:
            return True
        if FOUR_DIGIT_YEAR_PATTERN.fullmatch(number):
            return True
        if re.fullmatch(r"\d{2}", number):
            return bool(
                YEAR_RANGE_PREFIX_PATTERN.search(data[: match.start()])
                and re.match(r"\s*년", data[match.end() :])
            )
        return False


def _metric_registry_numbers(metric_registry: dict[str, Any]) -> set[str]:
    numbers: set[str] = set()
    for metric in metric_registry.values():
        if not isinstance(metric, dict):
            continue
        value = metric.get("value")
        if isinstance(value, (int, float)):
            value = str(value)
        if not isinstance(value, str):
            continue
        for match in RAW_NUMBER_PATTERN.finditer(value):
            number = _normalize_number_token(match.group(0))
            if number:
                numbers.add(number)
    return numbers


def _normalize_number_token(value: str) -> str:
    match = NUMBER_CORE_PATTERN.search(value)
    if not match:
        return ""
    return match.group(0).replace(",", "").strip()


def normalize_enclosed_numerals(text: str) -> str:
    def replace(match: re.Match[str]) -> str:
        try:
            number = unicodedata.numeric(match.group(0))
        except (TypeError, ValueError):
            return ""
        if float(number).is_integer():
            return f"{int(number)}."
        return ""

    return ENCLOSED_NUMERAL_PATTERN.sub(replace, text)
