#!/usr/bin/env python3
"""Translate one TickDeck run into ppt-master planning artifacts."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "input"

PALETTE = {
    "background": "#0D1220",
    "secondary_background": "#161D31",
    "primary": "#6E8BFF",
    "accent": "#B49BF2",
    "secondary_accent": "#4A5578",
    "body_text": "#EEF1FB",
}

RHYTHM = {
    "cover": "anchor",
    "divider": "breathing",
    "hero_bleed": "anchor",
    "closing": "anchor",
    "outro": "breathing",
    "index": "breathing",
    "source_appendix": "dense",
    "split": "dense",
    "split_status": "dense",
    "stack": "dense",
}

AUDIENCE_MOVE = {
    "cover": "주제를 모르는 상태 → 올해 예산 판단의 중심 질문을 인식한 상태",
    "index": "핵심 질문만 아는 상태 → 보고서의 논리 순서를 예측하는 상태",
    "divider": "앞 장의 결론을 이해한 상태 → 다음 논점의 질문으로 전환한 상태",
    "split": "현상을 아는 상태 → 대조되는 증거와 실무 함의를 연결한 상태",
    "split_status": "정보가 흩어진 상태 → 전체 시장의 현재 상태와 우선순위를 요약한 상태",
    "stack": "개별 신호를 아는 상태 → 근거 묶음과 실행 기준을 함께 이해한 상태",
    "hero_bleed": "유행어를 아는 상태 → 기대와 실제 성과의 격차를 한 문장으로 기억한 상태",
    "closing": "개별 변화들을 아는 상태 → 변화들을 관통하는 결론을 설명할 수 있는 상태",
    "source_appendix": "주장을 받아들인 상태 → 사용된 출처 범위와 검증 경로를 확인한 상태",
    "outro": "보고 내용을 이해한 상태 → 보고가 종료되었음을 인식한 상태",
}


def load(name: str) -> dict:
    return json.loads((INPUT / name).read_text(encoding="utf-8"))


def registry_items(registry: dict | list, prefix: str):
    if isinstance(registry, dict):
        return list(registry.items())
    return [(item.get("id", f"{prefix}_{i:03d}"), item) for i, item in enumerate(registry, 1)]


def fact_rows(verified: dict, topic: str) -> tuple[list[dict], dict[str, str]]:
    rows: list[dict] = []
    id_map: dict[str, str] = {}
    sources = dict(registry_items(verified["source_registry"], "src"))

    def add(original_id: str, claim: str, source: dict, classification: str):
        fact_id = f"F{len(rows) + 1:03d}"
        id_map[original_id] = fact_id
        rows.append(
            {
                "fact_id": fact_id,
                "claim": claim,
                "source_title": source.get("title", ""),
                "source_url": source.get("url", ""),
                "classification": classification,
                "retrieved_at": verified.get("verified_at", "")[:10],
                "tickdeck_id": original_id,
            }
        )

    for source_id, source in registry_items(verified["source_registry"], "src"):
        classification = "external" if source.get("url") else "local-corpus"
        add(source_id, f"검증 출처 레지스트리: {source.get('publisher', '')} — {source.get('title', '')}", source, classification)

    for metric_id, metric in registry_items(verified["metric_registry"], "metric"):
        source_ids = metric.get("source_ids", [])
        primary = sources.get(source_ids[0], {}) if source_ids else {}
        value = f"{metric.get('value', '')}{metric.get('unit', '')}"
        scope = metric.get("scope", "")
        claim = f"{metric.get('label', metric_id)}: {value}"
        if scope:
            claim += f" ({scope})"
        classification = "external" if primary.get("url") else "local-corpus"
        add(metric_id, claim, primary, classification)
        rows[-1]["source_ids"] = source_ids
        rows[-1]["verification_note"] = metric.get("verification_note", "")
        rows[-1]["status"] = metric.get("status", "")

    return rows, id_map


def metric_text(metric: dict) -> str:
    return f"{metric.get('value', '')}{metric.get('unit', '')}"


def resolve_metrics(value, metrics: dict):
    if isinstance(value, str):
        return re.sub(
            r"\{\{(metric_\d+)\}\}",
            lambda m: metric_text(metrics[m.group(1)]) if m.group(1) in metrics else m.group(0),
            value,
        )
    if isinstance(value, list):
        return [resolve_metrics(v, metrics) for v in value]
    if isinstance(value, dict):
        out = {k: resolve_metrics(v, metrics) for k, v in value.items()}
        mid = out.get("metric_id")
        if mid in metrics:
            out["registry_value"] = metric_text(metrics[mid])
            out["registry_scope"] = metrics[mid].get("scope", "")
        return out
    return value


def content_markdown(page: dict, metrics: dict, sources: dict) -> str:
    if page["layout"] == "source_appendix":
        source_lines = [
            f"{sid}: {s.get('publisher', '')} — {s.get('title', '')}" + (f" — {s['url']}" if s.get("url") else " — URL 없음(로컬 코퍼스)")
            for sid, s in sources.items()
        ]
        prefix = resolve_metrics(page.get("content", []), metrics)
        return json.dumps(prefix, ensure_ascii=False) + "\n  - 전체 출처:\n    - " + "\n    - ".join(source_lines)
    resolved = resolve_metrics(page.get("content", []), metrics)
    return json.dumps(resolved, ensure_ascii=False, separators=(", ", ": "))


def exact_math(page: dict, metrics: dict) -> str | None:
    parts = []
    for metric_id in page.get("allowed_metric_ids", []):
        metric = metrics[metric_id]
        parts.append(f"{metric.get('label', metric_id)} = {metric_text(metric)} [{metric.get('scope', '')}]")
    return "; ".join(parts) or None


def write_design_spec(out_dir: Path, intake: dict, deck: dict, verified: dict, id_map: dict[str, str]):
    metrics = dict(registry_items(verified["metric_registry"], "metric"))
    sources = dict(registry_items(verified["source_registry"], "src"))
    lines = [
        "<!-- ppt-master-schema: design-spec/v1 -->",
        "# 2026 Marketing Trends Bridge - Design Spec",
        "",
        "## I. Project Information",
        "",
        "| Item | Value |",
        "| --- | --- |",
        "| Project Name | 2026 Marketing Trends Bridge |",
        "| Canvas Format | PPT 16:9 (1280 × 720) |",
        f"| Page Count | {len(deck['pages'])} |",
        "| Primary Language | ko-KR |",
        f"| Target Audience | {intake['audience']} |",
        "| Communication Intent | 검증된 근거로 2026 마케팅 변화와 한국 실무 착지를 설명한다 |",
        "| Desired Audience Outcome | 예산·검색·AI 제작·측정에 대해 점검할 기준을 말할 수 있다 |",
        "| Core Message / Ask / Action | 예산은 성과를 숫자로 보여준 쪽으로 움직인다 |",
        "| Delivery Context | 비즈니스·마케팅 실무자용 리서치 보고서 |",
        "| Artifact Afterlife | PowerPoint에서 요소별 편집 가능한 16장 보고서 |",
        "| Reading Mode | balanced |",
        "| Content Strategy | TickDeck의 검증된 페이지 순서·문구·허용 레지스트리를 보존한다 |",
        "| Design Style | navy_glow style workspace의 다크 프리미엄·절제된 글로우 |",
        "| AI Image Acquisition Path | not applicable |",
        "| Generation Mode | continuous |",
        "| Spec Refinement | disabled |",
        "| Speaker Notes | disabled — explicit task scope |",
        "| Custom Animations | disabled — explicit task scope |",
        "| Narration Audio | disabled — explicit task scope |",
        "| Created Date | 2026-08-15 |",
        "",
        "## II. Canvas Specification",
        "",
        "| Property | Value |",
        "| --- | --- |",
        "| Format | PPT 16:9 |",
        "| Dimensions | 1280 × 720 |",
        "| viewBox | `0 0 1280 720` |",
        "| Margins | 좌우 64px, 상하 48px 안전 여백 |",
        "| Content Area | 1152 × 624 |",
        "",
        "## III. Visual Theme",
        "",
        "### Theme Style",
        "",
        "- **Mode**: custom",
        "- **Visual style**: custom",
        "- **Theme**: navy_glow 다크 베이스와 인접 2색 글로우",
        "- **Tone**: 차분한 신뢰, 절제된 프리미엄",
        "",
        "### Color Scheme",
        "",
        "| Role | HEX | Purpose |",
        "| --- | --- | --- |",
        "| Background | #0D1220 | 주 지면 |",
        "| Secondary background | #161D31 | 카드·보조 지면 |",
        "| Primary | #6E8BFF | 핵심 수치·강조 |",
        "| Accent | #B49BF2 | 인접 보조 액센트 |",
        "| Secondary accent | #4A5578 | 비교군 |",
        "| Body text | #EEF1FB | 제목·본문 잉크 |",
        "",
        "## IV. Typography System",
        "",
        "### Font Plan",
        "",
        "| Role | Character (Reference) | Primary | English if non-English | Fallback tail |",
        "| --- | --- | --- | --- | --- |",
        "| Title | 굵고 큰 산세리프 | Pretendard | Aptos | Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif |",
        "| Body | 읽기 쉬운 산세리프 | Pretendard | Aptos | Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif |",
        "",
        "- **Typography upgrade (Reference)**: 대상 환경에 Pretendard가 없으면 Aptos 또는 Noto Sans KR로 대체",
        "",
        "### Font Size Hierarchy",
        "",
        "| Role | Size | Usage |",
        "| --- | --- | --- |",
        "| Title | 42px | 페이지 제목 |",
        "| Subtitle | 26px | 보조 주장 |",
        "| Body | 18px | 본문 |",
        "| Annotation | 12px | 출처·각주 |",
        "",
        "## V. Layout Principles",
        "",
        "- 1280×720 안에서 직전·직후 페이지 실루엣을 달리한다.",
        "- 다크 지면, 흰색 5% 유리 카드, 흰색 8% 보더를 기본으로 한다.",
        "- 글로우는 페이지당 최대 2곳, 데이터는 페리윙클→라벤더→저채도 네이비 순으로 쓴다.",
        "- 수치 페이지에는 검증 칩과 실제 사용 출처 기관을 보인다.",
        "",
        "## VI. Icon Usage Specification",
        "",
        "| Library | Inventory | Usage |",
        "| --- | --- | --- |",
        "| none | none | 네이티브 SVG 도형과 데이터 마크만 사용 |",
        "",
        "## VIII. Image Resource List",
        "",
        "| Filename | Dimensions | Ratio | Purpose | Type | Layout pattern | Crop Policy | Acquire Via | Status | Reference | text_policy | page_role |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "",
        "## IX. Content Outline",
        "",
    ]

    for idx, page in enumerate(deck["pages"], 1):
        source_facts = [id_map[x] for x in page.get("allowed_source_ids", [])]
        metric_facts = [id_map[x] for x in page.get("allowed_metric_ids", [])]
        facts = source_facts + metric_facts
        lines.extend(
            [
                f"### Part {idx}: {page['page_id']}",
                "",
                f"#### Slide {idx:02d} - {page['short_title']}",
                "",
                f"- **Audience move**: {AUDIENCE_MOVE[page['layout']]}",
                f"- **Layout**: TickDeck `{page['layout']}` 의미를 보존하되 flat SVG에서 navy_glow 관계 규칙으로 재구성",
                f"- **Title**: {page['short_title']}",
                f"- **Core message**: {page['short_title']}",
                f"- **Content**: {content_markdown(page, metrics, sources)}",
            ]
        )
        math = exact_math(page, metrics)
        if math:
            lines.append(f"- **Mathematical content**: {math}")
        if facts:
            lines.append(f"- **Fact IDs**: {', '.join(facts)}")
        lines.append("- **Native shape suggestion**: 네이티브 기본 도형과 연결선으로 카드·지표·관계를 구성")
        if idx == 1:
            lines.append("- **Cover impact**: ‘예산은 성과를 보여준 쪽으로 간다’를 결론형 훅으로 고정하고 우상단 글로우와 3색 룰 바로 구성")
        if page["layout"] == "closing":
            lines.append("- **Closing impact**: 개별 변화가 성과 측정 능력으로 수렴한다는 결론을 세 개 대비와 한 문장으로 고정")
        lines.append("")

    lines.extend(["## X. Speaker Notes Requirements", "", "- **Generation**: disabled", ""])
    (out_dir / "design_spec.md").write_text("\n".join(lines), encoding="utf-8")


def write_lock(out_dir: Path, intake: dict, deck: dict):
    lines = [
        "<!-- ppt-master-schema: spec-lock/v1 -->",
        "# Execution Lock",
        "",
        "## canvas",
        "- viewBox: 0 0 1280 720",
        "- format: PPT 16:9",
        "",
        "## communication",
        "- primary_language: ko-KR",
        f"- audience: {intake['audience']}",
        "- objective: 검증된 근거로 2026 마케팅 변화를 설명하여 청중이 예산·검색·AI 제작·측정의 점검 기준을 말할 수 있게 한다.",
        "- core_message: 예산은 성과를 숫자로 보여준 쪽으로 움직인다",
        "- consumption_mode: balanced",
        "",
        "## mode",
        "- mode: custom",
        "- mode_behavior: 결론을 먼저 제시하고 검증된 대조 수치와 한국 실무 기준으로 설명한 뒤 실행 항목으로 닫는다.",
        "",
        "## visual_style",
        "- visual_style: custom",
        "- visual_style_behavior: 다크 네이비 지면에 인접한 페리윙클·라벤더 액센트, 저투명 유리 카드, 페이지당 최대 두 곳의 절제된 글로우를 사용한다.",
        "",
        "## colors",
        *[f"- {k}: {v}" for k, v in PALETTE.items()],
        "",
        "## typography",
        "- font_family: Pretendard, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif",
        "- title_family: Pretendard, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif",
        "- body_family: Pretendard, Apple SD Gothic Neo, Noto Sans KR, Malgun Gothic, sans-serif",
        "- body: 18",
        "- title: 42",
        "- subtitle: 26",
        "- annotation: 12",
        "",
        "## icons",
        "- library: none",
        "- inventory: none",
        "",
        "## page_rhythm",
    ]
    for i, page in enumerate(deck["pages"], 1):
        lines.append(f"- P{i:02d}: {RHYTHM[page['layout']]}")
    lines.extend(
        [
            "",
            "## pptx_structure",
            "- mode: flat",
            "",
            "## forbidden",
            "- `mask`, `<style>`, `class`, external CSS, `<foreignObject>`, `textPath`, `@font-face`, `<animate*>`, `<set>`, `<script>` / event attributes, `<iframe>`",
            "- HTML named entities in text; write typography as raw Unicode and escape XML reserved characters",
            "",
        ]
    )
    (out_dir / "spec_lock.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "adapter" / "generated")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "sources").mkdir(exist_ok=True)

    intake = load("00_intake.json")
    verified = load("02_verified.json")
    deck = load("06_deck_spec.json")
    facts, id_map = fact_rows(verified, intake["topic"])
    payload = {"schema": "ppt-master.fact-provenance.v1", "topic": intake["topic"], "facts": facts}
    (args.out / "sources" / "marketing_trends_2026.facts.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_design_spec(args.out, intake, deck, verified, id_map)
    write_lock(args.out, intake, deck)
    print(json.dumps({"pages": len(deck["pages"]), "facts": len(facts), "output": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
