#!/usr/bin/env python3
"""run 디렉토리에서 계약 payload를 자동 조립해 C1~C6를 일괄 검증한다.

수동 조립 누락 사고(20260630 run "C5 stage_log dict 누락")의 배선 풀이:
사람이 deck_json을 손으로 만들지 않고, run 디렉토리 산출물에서 그대로 조립한다.

usage: run_contracts.py <run_dir> [deck.html]
- html 인자를 생략하면 run_dir에서 가장 최근 수정된 .html을 쓴다.
- rendered_pages(C2)는 deck_spec.pages를 프록시로 스캔한다(렌더 문자열의 원천).
- exit code: 위반 있으면 1.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contract_checks import validate_all_contracts


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


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: run_contracts.py <run_dir> [deck.html]")
        return 2
    run_dir = Path(sys.argv[1])
    if not run_dir.is_dir():
        print(f"NO_RUN_DIR: {run_dir}")
        return 2

    intake = _load(run_dir, "00_intake.json") or {}
    insights = (_load(run_dir, "03_insights.json") or {}).get("insights", [])
    dag = _load(run_dir, "04_proposition_dag.json", "04_dag.json") or {}
    page_plan = _load(run_dir, "05_page_plan.json") or {}
    verified = _load(run_dir, "02_verified.json") or {}
    deck_spec = _load(run_dir, "06_deck_spec.json") or {}

    if len(sys.argv) > 2:
        html_path = Path(sys.argv[2])
    else:
        candidates = [p for p in run_dir.glob("*.html") if "__fit__" not in p.name]
        html_path = max(candidates, key=lambda p: p.stat().st_mtime) if candidates else None
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

    missing = [
        name
        for name, value in (
            ("00_intake", intake),
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

    violations = validate_all_contracts(deck)
    print(f"run: {run_dir.name} · html: {html_path.name if html_path else '-'}")
    if violations:
        for violation in violations:
            print(f"FAIL {violation}")
        print(f"→ {len(violations)}건 위반")
        return 1
    print("→ C1~C6 위반 0건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
