from __future__ import annotations

from dataclasses import dataclass
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


def validate_all_contracts(deck: dict[str, Any], raise_on_error: bool = False) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    violations.extend(validate_c1_proposition_dag(deck.get("proposition_dag", {})))
    violations.extend(validate_c2_no_validation_metadata(deck.get("rendered_pages", [])))
    violations.extend(validate_c3_trend_state_transition(deck.get("genre", ""), deck.get("insights", [])))
    violations.extend(validate_c4_citation_tracker(deck.get("insights", [])))
    violations.extend(validate_c5_stage_order(deck.get("stage_log", [])))

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
