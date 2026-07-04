from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
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
        "viz",
        "bullets",
        "list",
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
        "gauge",
        # 2026-07-04 다이어그램 어휘(후추님 — 관계·순환·프로세스·표 인포그래픽 공백 지적):
        "hub_cycle",       # 중심+궤도 노드 순환 허브 (series[0]=중심·값 선택)
        "arrow_flow",      # 두꺼운 셰브런 프로세스 (단계가 화살표 도형·값 선택)
        "timeline_bars",   # 간트형 계단 타임라인 (값 선택)
        "data_table",      # 액센트 헤더 + 줄무늬 데이터 표 (값=registry)
        # 2026-07-04 승격 라운드(PATTERN_LIBRARY ⬜→✅·report_ops 정체성):
        "multi_line",        # 다계열 라인 — role baseline/highlight로 선 분리
        "progress_bar",      # 트랙+채움 진척 막대 (number=0~100 해석)
        "target_vs_actual",  # 계획(점선 고스트) vs 실제(채움) 짝 — series 연속 2개=1행
        "radial_progress",   # 단일 링 진척 게이지·% 중앙 (최대 3링)
        "swot_quad",         # 2×2 정성 사분면 — metric_id 없이 series[].items 텍스트만 허용
    }
)
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
    }
)
RAW_NUMBER_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])[+-]?\d+(?:[.,]\d+)*(?:\.\d+)?"
    r"(?:\s?(?:%|\$|조|억|만|명|개|건|pp|p|B|M|K|원|달러|USD|YoY))?(?![A-Za-z0-9_])"
)
ENCLOSED_NUMERAL_PATTERN = re.compile(
    "[\u2460-\u249b\u24ea-\u24ff\u2776-\u2793\u3251-\u325f\u32b1-\u32bf]"
)


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

    for page_index, page in enumerate(pages):
        if not isinstance(page, dict):
            violations.append(ContractViolation("C6", "page must be an object", f"deck_spec.pages[{page_index}]"))
            continue

        page_path = f"deck_spec.pages[{page_index}]"
        allowed_source_ids = _string_set(page.get("allowed_source_ids"))
        allowed_metric_ids = _string_set(page.get("allowed_metric_ids"))
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

        for block_type, type_path in _iter_content_block_types(content, f"{page_path}.content"):
            if block_type not in SUPPORTED_CONTENT_BLOCK_TYPES:
                violations.append(
                    ContractViolation("C6", f"unsupported content block type: {block_type}", type_path)
                )

        for viz_block, viz_path in _iter_viz_blocks(content, f"{page_path}.content"):
            violations.extend(_validate_viz_block(viz_block, viz_path))

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

            metric_source_ids = _string_set(metric.get("source_ids") if isinstance(metric, dict) else [])
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
        layout = page.get("layout")
        if layout is None:
            violations.append(ContractViolation("C6", "page must include layout", f"{page_path}.layout"))
        elif str(layout).strip() not in SUPPORTED_LAYOUTS:
            violations.append(ContractViolation("C6", f"unsupported layout: {layout}", f"{page_path}.layout"))

    if rendered_html:
        violations.extend(_validate_rendered_content_authority(rendered_html))

    return violations


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


def _string_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {str(item) for item in value if str(item).strip()}
    if isinstance(value, tuple):
        return {str(item) for item in value if str(item).strip()}
    return set()


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


def _validate_viz_block(block: dict[str, Any], path: str) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    chart = str(block.get("chart", "")).strip()
    if chart not in SUPPORTED_VIZ_CHART_TYPES:
        violations.append(ContractViolation("C6", f"unsupported viz chart type: {chart}", f"{path}.chart"))

    for field in ("title", "note"):
        text = block.get(field)
        if isinstance(text, str) and RAW_NUMBER_PATTERN.search(text):
            violations.append(ContractViolation("C6", f"viz {field} contains raw number", f"{path}.{field}"))

    for field in ("value", "unit", "values", "data"):
        if field in block:
            violations.append(ContractViolation("C6", f"viz block must not include direct {field}", f"{path}.{field}"))

    series = block.get("series")
    if not isinstance(series, list) or not series:
        violations.append(ContractViolation("C6", "viz block must include non-empty series", f"{path}.series"))
        return violations

    for index, item in enumerate(series):
        item_path = f"{path}.series[{index}]"
        if not isinstance(item, dict):
            violations.append(ContractViolation("C6", "viz series item must be an object", item_path))
            continue
        if chart != "swot_quad" and not str(item.get("metric_id", "")).strip():
            violations.append(ContractViolation("C6", "viz series item must include metric_id", f"{item_path}.metric_id"))
        label = item.get("label")
        if isinstance(label, str) and RAW_NUMBER_PATTERN.search(label):
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
        for field in ("value", "unit", "values", "data"):
            if field in item:
                violations.append(ContractViolation("C6", f"viz series must not include direct {field}", f"{item_path}.{field}"))

    return violations


def _validate_rendered_content_authority(rendered_html: str) -> list[ContractViolation]:
    parser = _RenderedAuthorityParser()
    parser.feed(rendered_html)
    return parser.violations


class _RenderedAuthorityParser(HTMLParser):
    _NUMBER_PATTERN = RAW_NUMBER_PATTERN
    _ENCLOSED_NUMERAL_PATTERN = ENCLOSED_NUMERAL_PATTERN

    def __init__(self) -> None:
        super().__init__()
        self.stack: list[dict[str, str]] = []
        self.violations: list[ContractViolation] = []
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
        if "출처:" in data and not self._manual_source_seen:
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
        if self._NUMBER_PATTERN.search(data) and not self._inside_authorized_numeric_context() and not self._untagged_number_seen:
            self._untagged_number_seen = True
            self.violations.append(
                ContractViolation("C6", "untagged number in rendered output; use metric_id injection", "rendered_html")
            )

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
            if classes & {"page-number", "citation-index", "source-index", "eyebrow", "cover-eyebrow", "copyright", "running-head-frac"}:
                return True
            # 간지 프리뷰(divider-items) = short_title 복제 — 원본(h1)이 면제이므로 복제도 면제(7/3).
            # 각주(footnote-row) = 조사 정의 병기·조건부 캐비앳이 본질이라 숫자 필요(writing-standard 9b·D-12).
            # 단 각주로 본문 통계를 밀반입하는 건 qa-reviewer 판정 대상(designer.md 명시).
            if classes & {"divider-items", "footnote-row"}:
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
