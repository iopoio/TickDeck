#!/usr/bin/env python3
"""run 디렉토리에서 계약 payload를 자동 조립해 C1~C10를 일괄 검증한다.

수동 조립 누락 사고(20260630 run "C5 stage_log dict 누락")의 배선 풀이:
사람이 deck_json을 손으로 만들지 않고, run 디렉토리 산출물에서 그대로 조립한다.

usage: run_contracts.py <run_dir> [deck.html]
- html 인자를 생략하면 run_dir/deck.html만 쓴다.
- rendered_pages(C2)는 deck_spec.pages를 프록시로 스캔한다(렌더 문자열의 원천).
- deck.html이 있으면 08_external_review.json(C9)을 검증한다.
- exit code: 위반 있으면 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_checks import (
    check_c9_final_review,
    check_c10_collection_evidence,
    check_c11_source_coverage,
    check_c14_viz_intent_preserved,
    check_c15_page_count_ceiling,
    validate_all_contracts,
)


def _load(run_dir: Path, *names: str):
    for name in names:
        path = run_dir / name
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    return None


def _assemble_stage_log(page_plan: dict, run_dir: Path, deck_spec: dict) -> list[dict]:
    # page_plan의 patch(문자열/딕트 혼용 흡수) + 이후 산출물 존재로 확정되는 단계를 덧붙인다.
    stage_log: list[dict] = []
    for entry in page_plan.get("stage_log_patch", []) or []:
        if isinstance(entry, dict):
            stage_log.append(entry)
        elif isinstance(entry, str) and entry.strip():
            stage_log.append({"stage": entry.strip()})
    seen = {entry.get("stage") for entry in stage_log}
    if deck_spec and "designer" not in seen:
        stage_log.append({"stage": "designer"})
    if (run_dir / "07_qa_report.json").exists() and "qa-reviewer" not in seen:
        stage_log.append({"stage": "qa-reviewer"})
    return stage_log


def _archetype_value(payload: dict) -> str:
    meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
    return str(payload.get("archetype") or meta.get("archetype") or "").strip()


def _warn_archetype_leak(page_plan: dict, deck_spec: dict) -> None:
    page_plan_archetype = _archetype_value(page_plan)
    if not page_plan_archetype:
        return
    meta = deck_spec.get("meta") if isinstance(deck_spec.get("meta"), dict) else {}
    deck_spec_archetypes = {
        str(value).strip()
        for value in (deck_spec.get("archetype"), meta.get("archetype"))
        if str(value or "").strip()
    }
    if page_plan_archetype not in deck_spec_archetypes:
        print(
            f"WARN archetype 누수: page_plan={page_plan_archetype} 인데 deck_spec에 미기재/불일치 — designer가 deck_spec 최상위 archetype로 실어야 함"
        )


def select_html_path(run_dir: Path, explicit_html: str | None) -> Path | None:
    if explicit_html:
        return Path(explicit_html)
    deck_html = run_dir / "deck.html"
    return deck_html if deck_html.exists() else None


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: run_contracts.py <run_dir> [deck.html]")
        return 2
    run_dir = Path(sys.argv[1])
    if not run_dir.is_dir():
        print(f"NO_RUN_DIR: {run_dir}")
        return 2

    has_c8_inputs = all(
        (run_dir / name).exists()
        for name in ("00_intake.json", "01_evidence_pool.json", "05_page_plan.json")
    )
    has_c10_inputs = all(
        (run_dir / name).exists()
        for name in ("00_intake.json", "02_verified.json")
    )
    intake = _load(run_dir, "00_intake.json") or {}
    evidence_pool = _load(run_dir, "01_evidence_pool.json") or {}
    insights = (_load(run_dir, "03_insights.json") or {}).get("insights", [])
    dag = _load(run_dir, "04_proposition_dag.json", "04_dag.json") or {}
    page_plan = _load(run_dir, "05_page_plan.json") or {}
    verified = _load(run_dir, "02_verified.json") or {}
    deck_spec = _load(run_dir, "06_deck_spec.json") or {}

    html_path = select_html_path(run_dir, sys.argv[2] if len(sys.argv) > 2 else None)
    rendered_html = html_path.read_text(encoding="utf-8") if html_path and html_path.exists() else ""

    deck = {
        "genre": intake.get("genre", ""),
        "insights": insights,
        "proposition_dag": dag,
        "stage_log": _assemble_stage_log(page_plan, run_dir, deck_spec),
        "rendered_pages": deck_spec.get("pages", []),
        "deck_spec": deck_spec,
        "content_registry": verified,
        "rendered_html": rendered_html,
    }
    if has_c8_inputs:
        deck.update(
            {
                "intake": intake,
                "evidence_pool": evidence_pool,
                "page_plan": page_plan,
            }
        )

    missing = [
        name
        for name, value in (
            ("00_intake", intake),
            ("01_evidence_pool", evidence_pool),
            ("02_verified", verified),
            ("03_insights", insights),
            ("04_dag", dag),
            ("05_page_plan", page_plan),
            ("06_deck_spec", deck_spec),
        )
        if not value
    ]
    if missing:
        print(f"WARN 누락 산출물(해당 계약은 빈 입력으로 평가됨): {', '.join(missing)}")
    if not rendered_html:
        print("WARN 렌더 HTML 없음 — C6 rendered_html 검사 생략")
    _warn_archetype_leak(page_plan, deck_spec)

    # 레지스트리 위생 lint(7/2 사고: unit 오염 36/60·영어 라벨) — 경고(비차단), verifier 반송 근거.
    import re as _re

    lint = []
    for mid, metric in (verified.get("metric_registry") or {}).items():
        value, unit = str(metric.get("value", "")), str(metric.get("unit", ""))
        label = str(metric.get("label") or metric.get("scope") or "")
        if not _re.fullmatch(r"-?[\d.,~\-]+", value):
            lint.append(f"{mid}: value가 순수 숫자가 아님 → {value!r}")
        if "(" in unit or _re.search(r"[A-Za-z]{3,}", unit):
            lint.append(f"{mid}: unit 오염 → {unit!r} (한정어는 scope로)")
        if _re.search(r"[A-Za-z]{4,}", label) and not _re.search(r"[가-힣]", label):
            lint.append(f"{mid}: 라벨이 영어 원문 → {label[:40]!r} (한국어 label 필수)")
    if lint:
        print(f"WARN 레지스트리 위생 {len(lint)}건 (verifier 반송 근거):")
        for line in lint[:10]:
            print(f"  - {line}")
        if len(lint) > 10:
            print(f"  … 외 {len(lint) - 10}건")

    # 디자인 위생 lint(7/3 후추님: 출처 혼합 차트·양식 돌려쓰기) — 경고(비차단), designer 반송 근거.
    design_lint = []
    metric_reg = verified.get("metric_registry") or {}
    body_layouts = []  # 간지 등 비본문은 None — 연속-run을 끊는다(간지가 리듬을 리셋).
    for page in deck_spec.get("pages", []):
        layout = str(page.get("layout", "statement"))
        if layout not in {"cover", "index", "divider", "closing", "outro", "source_appendix"}:
            body_layouts.append(layout)
        else:
            body_layouts.append(None)
        for block in page.get("content", []) or []:
            if not (isinstance(block, dict) and block.get("type") == "viz"):
                continue
            src_sets = [
                set(metric_reg.get(s.get("metric_id"), {}).get("source_ids", []))
                for s in block.get("series", [])
                if isinstance(s, dict)
            ]
            src_sets = [s for s in src_sets if s]
            if len(src_sets) >= 2 and not set.intersection(*src_sets):
                design_lint.append(
                    f"{page.get('page_id')}: 한 차트에 출처 혼합(공통 src 없음) — 단일 출처 시리즈로 재구성"
                )
    body_only = [l for l in body_layouts if l]
    if len(body_only) >= 4:
        from collections import Counter

        top_layout, top_n = Counter(body_only).most_common(1)[0]
        if top_n / len(body_only) > 0.6:
            design_lint.append(
                f"본문 {len(body_only)}장 중 '{top_layout}' {top_n}장(>60%) — 양식 돌려쓰기. 내용에 맞는 컴포지션 다양화"
            )
        for i in range(len(body_layouts) - 2):
            if body_layouts[i] and body_layouts[i] == body_layouts[i + 1] == body_layouts[i + 2]:
                design_lint.append(f"동일 layout '{body_layouts[i]}' 3장 연속 — 리듬 단조")
                break
    if design_lint:
        print(f"WARN 디자인 위생 {len(design_lint)}건 (designer 반송 근거):")
        for line in design_lint:
            print(f"  - {line}")

    violations = validate_all_contracts(deck)
    c9_applied = (run_dir / "deck.html").exists()
    if c9_applied:
        violations.extend(check_c9_final_review(run_dir))
    c10_applied = has_c10_inputs
    if c10_applied:
        violations.extend(check_c10_collection_evidence(run_dir))
    violations.extend(check_c11_source_coverage(run_dir))
    # C14/C15 — 05_page_plan.json 있을 때만 활성(내부에서 자체 guard). 어제 사고(viz 소실·28→41장)
    # 재발 검출.
    violations.extend(check_c14_viz_intent_preserved(page_plan, deck_spec))
    violations.extend(check_c15_page_count_ceiling(page_plan, deck_spec))
    contract_range = "C1~C11" if c10_applied else ("C1~C9+C11" if c9_applied else "C1~C8")
    print(f"run: {run_dir.name} · html: {html_path.name if html_path else '-'}")
    if violations:
        for violation in violations:
            print(f"FAIL {violation}")
        print(f"→ {len(violations)}건 위반")
        return 1
    print(f"→ {contract_range} 위반 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
