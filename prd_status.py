#!/usr/bin/env python3
"""TickDeck PM 상황판 — 접이식 마인드맵 (markmap). 노드 클릭하면 하위 뎁스 펼침.

한 판에: 버전 진화(v1~v4, 각 버전 고유 뎁스) · v4 구현 부품 50+ · 다음 할일 · 폐기.
상태 이모지 🟢됨 🟡뻗어나감 🔴안됨 🪦폐기/은퇴 ⚪대체. 재실행하면 자동 갱신.
버전별 뎁스는 각 PRD 실측분(config), v4 구현·부품 수는 파일 자동 스캔.

  python3 prd_status.py            # PRD_STATUS.html 생성
  python3 prd_status.py --selftest # self-check
"""
from __future__ import annotations
import json, sys, urllib.request
from datetime import datetime
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent
THINK_ENV = Path("/Users/hwa/Projects/Automation/Think/.env.local")
TRELLO_BOARD = "6a22b068ca1fc1c5f0b68f57"
OUT = ROOT / "PRD_STATUS.html"

# ── 버전 진화 (각 버전 PRD 실측분 · 버전마다 뎁스가 다름) ──
VERSIONS = [
    {"label": "v1 · 원본", "date": "2026-04-26", "content": "AI 덱 생성 도구", "state": "dropped",
     "stamp": "🪦 시장출시 포기 (4/27) — Claude Design 출시로 본질 흡수", "next": "", "path": "docs/PRD.md",
     "depth": [
         "노선 2갈래: 개인도구(옵션4) vs 차별화 재정립(옵션2)",
         "Phase 1~5 · Phase 5(디자인) 진행 중 중단",
         "유저스토리 P0/P1/P2 (본인도구→차별화→사업화)",
         "기술스택: HTML 덱 생성 (Phase 5)",
     ]},
    {"label": "v2", "date": "2026-05-12", "content": "가볍게 + 잘 나오게 (v1 포기 후 재개)", "state": "superseded",
     "stamp": "⏭ v3로 대체 — 방향 전환", "next": "", "path": "v2/PRD_v2.md",
     "depth": [
         "브레인스토밍 결정 9개",
         "디자인 라인업 6종",
         "8단계 흐름: PDF파싱→AI조사→통합→내러티브→품질검증→디자인선택→PPTX→스타일변경",
         "Streamlit 단일 앱 (컴포넌트 구조)",
         "v2.1: SaaS 노선 재정의 (wedge·ICP·Trojan Horse·차별 layer 3)",
     ]},
    {"label": "v3 · +gstack", "date": "2026-06-18", "content": "조사→시각양식 덱 (재사용 반자동)", "state": "superseded",
     "stamp": "⏭ v4로 대체 — 1차 실패(텍스트 fallback·양식 0·1회성)", "next": "", "path": "v3/PRD_v3.md",
     "depth": [
         "낯선 분야 조사→내용별 시각 양식 배치",
         "딥리서치 + 양식 지속 확장 (핵심 함정=양식 적으면 매번 같은 덱)",
         "gstack /office-hours 재설계 분기 (PRD_v3_gstack)",
     ]},
    {"label": "v4.1 · 현재", "date": "2026-06-28~07-07", "content": "장르 적응형 에이전트+스킬 하네스", "state": "active",
     "stamp": "● 활성", "next": "제품화(B형 유료 라이브 생성기) — '다음 할일' 참조", "path": "PRD_v4.md",
     "depth": []},  # v4 뎁스 = 자동 스캔(아래)
]
RETIRED = [
    {"label": "tickdeck_harness", "date": "2026-06-29", "content": "옛 파이썬 덱 생성기 (B)",
     "stamp": "🪦 은퇴 예정 — v4에 검증 부품(engine.py 차트·dig) 기증 중", "path": "tickdeck_harness/README.md"},
]

NODES = {
    "에이전트": [
        ("intake-director", ".claude/agents/intake-director.md", "기획 디렉터·장르/청중 판별"),
        ("collector", ".claude/agents/collector.md", "수집가 팬아웃·Tier-A 우선"),
        ("verifier", ".claude/agents/verifier.md", "검증가·DWS/중복/좀비"),
        ("analyst", ".claude/agents/analyst.md", "분석가[심장]·Insight 구조화"),
        ("editorial-director", ".claude/agents/editorial-director.md", "에디터·명제 DAG"),
        ("page-planner", ".claude/agents/page-planner.md", "페이지 기획·의미 설계"),
        ("designer", ".claude/agents/designer.md", "디자이너·맞춤검사→렌더"),
        ("qa-reviewer", ".claude/agents/qa-reviewer.md", "검수가·5대 계약 스캔"),
    ],
    "장르 프로필": [
        ("genre-trend-report", ".claude/skills/genre-trend-report", "트렌드 보고서·렌즈 10종"),
        ("genre-topic-deck", ".claude/skills/genre-topic-deck", "주제 발표·핵심논점"),
    ],
    "계약 검사 스크립트": [
        ("spine_check", ".claude/skills/deck-harness/scripts/spine_check.py", "C7 제목 척추"),
        ("render_deck", ".claude/skills/deck-harness/scripts/render_deck.py", "C6 렌더 권한(날조 차단)"),
        ("contract_checks", ".claude/skills/harness-contracts/scripts/contract_checks.py", "C1~C5 강제"),
    ],
    "파이프라인": [
        ("PIPELINE_SPEC", "PIPELINE_SPEC.md", "6단계+2 피드백 루프"),
        ("deck-harness", ".claude/skills/deck-harness/SKILL.md", "오케스트레이터 진입점"),
    ],
}
EXTRA_SCAN = {"에이전트": (".claude/agents", "*.md"), "장르 프로필": (".claude/skills", "genre-*")}
CONTRACTS = [
    ("C1", "큐레이션 dict-매칭 금지 (명제 DAG)"),
    ("C2", "검증 메타데이터 콘텐츠 노출 금지"),
    ("C3", "트렌드=방향 (정적 통계 헤드라인 금지)"),
    ("C4", "원본 분석 생산 (재포장 금지·Citation Tracker)"),
    ("C5", "디자인-우선 금지 (순서 강제)"),
    ("C6", "렌더 콘텐츠 권한 (날조 차단)"),
    ("C7", "제목 척추 가독성"),
]
VIZ = ["before_after", "dumbbell", "flow", "big_number", "gap_map", "shift"]
MARK = {"done": "🟢", "extra": "🟡", "gap": "🔴"}


def cnt(d, *pats):
    base = ROOT / d
    return sum(len(list(base.glob(p))) for p in pats) if base.exists() else 0


def scan_nodes():
    sections = []
    for sect, items in NODES.items():
        declared = {Path(p).name for _, p, _ in items}
        rows = [{"name": n, "state": "done" if (ROOT / p).exists() else "gap", "ref": p, "desc": d}
                for n, p, d in items]
        if sect in EXTRA_SCAN:
            dd, pat = EXTRA_SCAN[sect]
            base = ROOT / dd
            if base.exists():
                for f in sorted(base.glob(pat)):
                    if f.name not in declared:
                        rows.append({"name": f.name, "state": "extra", "ref": f"{dd}/{f.name}", "desc": "PRD 미기재·실물에만"})
        sections.append((sect, rows))
    return sections


def recent_run():
    ws = ROOT / "_workspace"
    runs = [p for p in ws.glob("*/") if p.is_dir()] if ws.exists() else []
    if not runs:
        return None
    latest = max(runs, key=lambda p: p.stat().st_mtime)
    days = (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).days
    return latest.name, days, len(runs)


def trello_cards():
    k = t = None
    if THINK_ENV.exists():
        for line in THINK_ENV.read_text().splitlines():
            if line.startswith("TRELLO_KEY="):   k = line.split("=", 1)[1].strip().strip("\"'")
            elif line.startswith("TRELLO_TOKEN="): t = line.split("=", 1)[1].strip().strip("\"'")
    if not (k and t):
        return None
    try:
        auth = f"key={k}&token={t}"
        base = f"https://api.trello.com/1/boards/{TRELLO_BOARD}"
        lists = {l["id"]: l["name"] for l in json.loads(
            urllib.request.urlopen(f"{base}/lists?fields=name&{auth}", timeout=10).read())}
        cards = json.loads(urllib.request.urlopen(f"{base}/cards?fields=name,idList&{auth}", timeout=10).read())
    except Exception as e:
        return {"error": str(e)}
    out = defaultdict(list)
    for c in cards:
        ln, nm = lists.get(c["idList"], "?"), c["name"]
        if "제품화" in ln or any(w in nm.lower() for w in ("틱덱", "tickdeck", "덱", "deck")):
            out[ln].append(nm)
    return dict(out)


def build_markdown(sections, run, trello):
    """markmap용 계층 마크다운 (헤딩=큰 갈래, 리스트 중첩=뎁스)."""
    md = [
        "---", "markmap:", "  initialExpandLevel: 3", "  colorFreezeLevel: 2",
        "  spacingVertical: 5", "  paddingX: 14", "  maxWidth: 340", "---",
        "# 🎯 TickDeck", "## 📜 버전 진화",
    ]
    VE = {"dropped": "🪦", "superseded": "⚪", "active": "🟢"}
    for v in VERSIONS:
        md.append(f"### {VE[v['state']]} {v['label']} · {v['date'][:7]}")
        md.append(f"- 📝 {v['content']}")
        md.append(f"- 📅 {v['date']}")
        md.append(f"- {v['stamp']}")
        if v.get("next"):
            md.append(f"- 🎯 다음: {v['next']}")
        for d in v.get("depth", []):
            md.append(f"- {d}")
        if v["state"] == "active":  # v4 뎁스 = 구현 자동 스캔
            for sect, rows in sections:
                dd = sum(1 for r in rows if r["state"] == "done")
                ee = sum(1 for r in rows if r["state"] == "extra")
                gg = sum(1 for r in rows if r["state"] == "gap")
                tag = f"{dd}🟢" + (f"+{ee}🟡" if ee else "") + (f"+{gg}🔴" if gg else "")
                md.append(f"- ⚙️ {sect} ({tag})")
                for r in rows:
                    md.append(f"  - {MARK[r['state']]} {r['name']} · {r['desc']}")
            md.append("- 📐 계약 C1~C7")
            for c, desc in CONTRACTS:
                md.append(f"  - {c} · {desc}")
            md.append(f"- 📊 viz 차트 {len(VIZ)}종")
            for x in VIZ:
                md.append(f"  - {x}")
            ns = cnt(".claude/skills/deck-harness/scripts", "*.py", "*.sh") + cnt(".claude/skills/harness-contracts/scripts", "*.py")
            nref = cnt(".claude/skills/deck-harness/references", "*.md")
            nknow = cnt("tickdeck_harness/knowledge", "*")
            md.append(f"- 🛠 렌더·QA·export 스크립트 {ns}개")
            md.append(f"- 📚 작법·디자인 캐논 {nref} · 흡수 지식 {nknow}")
            if run:
                nm, days, n = run
                md.append(f"- ▶ 실제 런 {n}개 (최근 {nm} · {days}일 전)")

    md.append("## 🚀 만들 것 · 제품 PRD 딸깍 (PRD_PRODUCT)")
    md.append("### 원칙 (7/25 후추님 결정)")
    md.append("- 질 = v4 그대로, 낮추지 않음 (차별의 근거)")
    md.append("- 속도 = 비동기로 출발, 단계별 단축")
    md.append("- 채택 = 질과 별개 축, Phase 0 신호로 검증 (7/6 교훈)")
    md.append("### 속도 로드맵 S0~S3")
    md.append("- 🔵 S0 · 비동기 래핑 (버튼→알림·기존 Celery)")
    md.append("- 🔵 S1 · 검수루프 제거 → 십몇 분 (여기서 출시 가능)")
    md.append("- 🔵 S2 · 병렬화 → 몇 분")
    md.append("- 🔵 S3 · 모델 라우팅·캐싱 (원가·처리량)")
    md.append("### wedge · 회사 전략기획자의 시장조사 덱")
    md.append("- B2B·임원 보고급, 후추님 = customer zero")
    md.append("- 채택 각도 = 완제품 대체 아니라 0→초안 시간 단축")
    md.append("### Phase 0 진행")
    md.append("- 🟢 샘플 덱 완성 · 시니어 시장 15장 (7/25~26·실무 문체 교정 반영)")
    md.append("- 🟢 원가 실측 · 약 146만 토큰, 에이전트 2시간")
    md.append("- 🔵 마지막 장 실명 정리 + 외부 검수(3층) + 수치 팩트체크")
    md.append("- 🔵 펩핀치 진열대 베타 게시 → 관심 신호 확인")
    md.append("## 🪦 폐기·은퇴")
    for r in RETIRED:
        md.append(f"### 🪦 {r['label']} · {r['date']}")
        md.append(f"- {r['content']}")
        md.append(f"- {r['stamp']}")

    md.append("## 📋 다음 할일 (로드맵·트렐로)")
    md.append("### B형 유료 라이브 생성기 (제품화)")
    if trello is None:
        md.append("- 트렐로 키 없음")
    elif "error" in trello:
        md.append(f"- 트렐로 조회 실패: {trello['error']}")
    else:
        order = ["진행중", "할일", "TickDeck 제품화", "⏰ 예정", "💡 씨앗", "📦 종료"]
        for ln in sorted(trello.keys(), key=lambda x: order.index(x) if x in order else 99):
            md.append(f"- 📋 {ln} ({len(trello[ln])})")
            for c in trello[ln]:
                md.append(f"  - {c}")
    return "\n".join(md)


def render(sections, run, trello):
    md = build_markdown(sections, run, trello)
    now = datetime.now().strftime("%Y-%m-%d %H:%M KST")
    legend = ("🟢 됨 · 🟡 뻗어나감(PRD미기재) · 🔴 안됨/구멍 · ⚪ 대체됨 · 🪦 폐기·은퇴")
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TickDeck — PM 상황판 (접이식 마인드맵)</title>
<style>
:root{{color-scheme:dark}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0f0f12;color:#e6e6ea;font:15px/1.5 -apple-system,"Segoe UI",Roboto,"Apple SD Gothic Neo",sans-serif;display:flex;flex-direction:column;height:100vh}}
header{{padding:18px 24px 12px;border-bottom:1px solid #26262c;flex-shrink:0}}
h1{{font-size:22px;font-weight:700}} h1 b{{color:#FF9B3D}}
.sub{{color:#8a8a93;font-size:13px;margin-top:5px}}
.legend{{color:#b8b8c0;font-size:12px;margin-top:8px}}
.markmap-wrap{{flex:1;width:100%;min-height:0;overflow:hidden}}
.markmap{{width:100%;height:100%}}
.markmap-foreign,.markmap-foreign *{{color:#f2f2f6 !important;font-size:11px !important;line-height:1.35 !important}}
svg.markmap text{{fill:#f2f2f6 !important;font-size:11px !important}}
svg.markmap{{font:300 11px/1.35 -apple-system,"Segoe UI",Roboto,"Apple SD Gothic Neo",sans-serif}}
.markmap-foreign a{{color:#8ec5ff !important}}
footer{{padding:8px 24px;color:#5a5a63;font-size:12px;border-top:1px solid #26262c;flex-shrink:0}}
code{{color:#a0a0aa}}
</style></head><body>
<header>
  <h1><b>TickDeck</b> · PM 상황판 <span style="font-size:13px;color:#8a8a93">접이식 마인드맵</span></h1>
  <div class="sub">노드(원)를 클릭하면 하위 뎁스가 펼쳐져요 · 버전별 시도 + v4 부품 50+ 한 판에</div>
  <div class="legend">{legend}</div>
</header>
<div class="markmap-wrap"><div class="markmap" data-markmap='{{"initialExpandLevel":2,"colorFreezeLevel":2,"spacingVertical":6,"paddingX":14,"maxWidth":320}}'><script type="text/template">
{md}
</script></div></div>
<footer>생성 {now} · <code>python3 prd_status.py</code> 재실행으로 갱신 · 노드 클릭=하위 펼침</footer>
<script src="https://cdn.jsdelivr.net/npm/markmap-autoloader@0.18"></script>
</body></html>"""


def selftest():
    assert (ROOT / ".claude/agents/analyst.md").exists(), "analyst.md 있어야"
    secs = scan_nodes()
    names = {r["name"] for _, rows in secs for r in rows}
    assert "fact-checker.md" in names, "뻗어나감 감지돼야"
    md = build_markdown(secs, recent_run(), None)
    assert "# 🎯 TickDeck" in md and "## 📜 버전 진화" in md, "마크다운 골격"
    assert "8단계 흐름" in md, "v2 뎁스 있어야"
    assert "계약 C1~C7" in md and "C7 · 제목 척추" in md, "v4 계약 뎁스 있어야"
    print("selftest OK ·", len(names), "구현노드 ·", md.count("###"), "버전/갈래 헤딩 ·", len(md.splitlines()), "줄")


def main():
    if "--selftest" in sys.argv:
        selftest(); return
    sections = scan_nodes()
    OUT.write_text(render(sections, recent_run(), trello_cards()), encoding="utf-8")
    t = defaultdict(int)
    for _, rows in sections:
        for r in rows:
            t[r["state"]] += 1
    ns = cnt(".claude/skills/deck-harness/scripts", "*.py", "*.sh") + cnt(".claude/skills/harness-contracts/scripts", "*.py")
    print(f"→ {OUT}")
    print(f"  버전 {len(VERSIONS)}(각 뎁스) · 구현 {t['done']}🟢 {t['extra']}🟡 {t['gap']}🔴 · 계약 {len(CONTRACTS)} · 스크립트 {ns} · 은퇴 {len(RETIRED)}")


if __name__ == "__main__":
    main()
