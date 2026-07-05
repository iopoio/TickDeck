#!/usr/bin/env bash
# TickDeck 엔진 1콜 진입점 (PRODUCT_ROADMAP Phase 1 · 7/5).
# 사용: run_deck.sh "<요청문>" [자료URL ...]
#   예: run_deck.sh "이 리포트로 우리 팀 공유용 발표자료 만들어줘" https://blog.example.com/report
# 하는 일: claude 헤드리스 1콜(v4 하네스 스킬이 전 단계 오케스트레이션) → 계약 게이트 재확인
#          → 산출물 경로 echo → 원가(total_cost_usd)·시간 _workspace/_cost_log.jsonl 기록.
set -euo pipefail
cd "$(cd "$(dirname "$0")/../../../.." && pwd)"   # repo root

REQ="${1:?usage: run_deck.sh \"<요청문>\" [URL ...]}"; shift || true
SRCS=""
for u in "$@"; do SRCS+="
- $u"; done

PROMPT="$REQ"
[ -n "$SRCS" ] && PROMPT+="

사용자 제공 자료(provided_sources·⓪ 최우선):$SRCS"
PROMPT+="

완료 기준: _workspace/<run_id>/deck.html+deck.pdf 생성, run_contracts.py 위반 0건, FIT_OK, 07_qa_report.json(visual_verdict·external_review_layer3 포함) 기록까지. 끝나면 run_id만 한 줄로 출력."

START=$(date +%s)
# ponytail: 무인 로컬 실행이라 skip-permissions. 서비스화(Phase 3)에서 SDK 권한 모델로 교체.
OUT_JSON=$(claude -p "$PROMPT" --output-format json --dangerously-skip-permissions) || {
  echo "RUN_FAILED"; printf '%s\n' "$OUT_JSON" | tail -c 2000; exit 1; }
ELAPSED=$(( $(date +%s) - START ))

RESULT=$(printf '%s' "$OUT_JSON" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('result','')[:200])")
COST=$(printf '%s' "$OUT_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin).get('total_cost_usd',''))")
RUN_ID=$(ls -td _workspace/2*/ 2>/dev/null | head -1 | xargs basename)

echo "── 게이트 재확인 (run=$RUN_ID) ──"
python3 .claude/skills/harness-contracts/scripts/run_contracts.py "_workspace/$RUN_ID" | tail -2

python3 - "$RUN_ID" "$COST" "$ELAPSED" <<'EOF'
import json, sys, pathlib
run_id, cost, elapsed = sys.argv[1], sys.argv[2], int(sys.argv[3])
row = {"run_id": run_id, "cost_usd": float(cost) if cost else None, "wall_seconds": elapsed}
p = pathlib.Path("_workspace/_cost_log.jsonl")
with p.open("a", encoding="utf-8") as f:
    f.write(json.dumps(row, ensure_ascii=False) + "\n")
print(f"COST_LOGGED: ${cost} · {elapsed//60}분{elapsed%60}초 → {p}")
EOF

echo "RESULT: $RESULT"
echo "ARTIFACTS:"
ls "_workspace/$RUN_ID"/deck.html "_workspace/$RUN_ID"/deck.pdf 2>/dev/null || echo "  (deck 산출물 없음 — 로그 확인 필요)"
echo "→ PPTX 필요 시: python3 .claude/skills/deck-harness/scripts/pptx_export.py _workspace/$RUN_ID/deck.html"
