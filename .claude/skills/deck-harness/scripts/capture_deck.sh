#!/usr/bin/env bash
# 덱 HTML → PDF 자동 캡처 (4층 시각 QA용).
# 덱을 렌더한 직후 *자동으로* 실행해서, 클차장이 실물(PDF)을 눈으로 읽고 확인하게 한다.
# Codex/에이전트 "됐습니다" 보고만 믿고 시각 확인을 스킵하지 않기 위한 강제 장치.
# 사용: capture_deck.sh <deck.html> [out.pdf]
set -e
DECK="$1"
[ -z "$DECK" ] && { echo "usage: capture_deck.sh <deck.html> [out.pdf]"; exit 2; }
[ -f "$DECK" ] || { echo "NO_DECK: $DECK"; exit 2; }
OUT="${2:-${DECK%.html}.pdf}"
CHROME=""
for c in \
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  "/Applications/Chromium.app/Contents/MacOS/Chromium" \
  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
  "$(command -v chromium 2>/dev/null)" \
  "$(command -v google-chrome 2>/dev/null)"; do
  [ -n "$c" ] && [ -x "$c" ] && CHROME="$c" && break
done
[ -z "$CHROME" ] && { echo "NO_CHROME — 시각 QA 캡처 불가 (Chrome/Chromium 설치 필요)"; exit 1; }
ABS="$(cd "$(dirname "$DECK")" && pwd)/$(basename "$DECK")"
# --headless=new 라야 CSS @page size(슬라이드 1280x720)를 지킴 — 구 --headless는 Letter 고정이라 가로 슬라이드 아래에 회색 여백이 남는다.
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="$OUT" "file://$ABS" >/dev/null 2>&1
echo "CAPTURED: $OUT"
echo "→ 다음: 클차장이 이 PDF를 Read로 직접 읽고 시각 QA (차트 렌더·그레이아웃·깨짐·여백). 보고 안 하고 '됐다' 금지."
