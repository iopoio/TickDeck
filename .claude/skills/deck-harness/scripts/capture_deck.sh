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

# --- 4층 시각 QA 보강: 세로 오버플로(본문이 푸터로 넘쳐 잘림)·과소밀도 프로그램 검출 ---
# 렌더러가 overflow:hidden로 '조용히' 잘라낸 본문은 PDF만 봐선 안 보인다 → 코드로 신호를 남긴다.
# ponytail: Chrome dump-dom 측정. 측정 실패 시 SKIP만 출력(차단 아님) — 더 정밀하면 puppeteer로 교체.
FIT="${ABS%.html}.__fit__.html"
cp "$ABS" "$FIT"
cat >> "$FIT" <<'EOF'
<script>
(function(){
  var ovf=[], sparse=[], hovf=[], lowc=[];
  document.querySelectorAll('.slide').forEach(function(s){
    var b=s.querySelector('.body'); if(!b) return;
    var gap=b.clientHeight-b.scrollHeight, id=s.dataset.pageId||'?';
    if(gap < -2) ovf.push(id);
    else if(gap > 240 && !/layout-(divider|closing|cover|index|matrix)/.test(s.className)) sparse.push(id);
    // hero_bleed는 블리드가 문법(수치가 우측 여백 너머로) — 의도된 가로 초과라 hovf 제외
    if(b.scrollWidth - b.clientWidth > 4 && !/layout-hero-bleed/.test(s.className)) hovf.push(id);
  });
  // 저대비 무독 텍스트 — closing 칩 navy-on-navy처럼 글자색≈배경색이라 실측으로만 잡히던 클래스(7/3).
  // 텍스트 leaf의 색 vs 가장 가까운 불투명 배경색의 명도차. 그라디언트(background-image) 조상은 판정 불가라 skip.
  function lum(c){var m=c.match(/\d+(\.\d+)?/g);if(!m)return null;return (0.2126*m[0]+0.7152*m[1]+0.0722*m[2])/255;}
  // 반투명 배경(알파<0.9)은 실효색을 모름 — 다크 테마의 rgba 카드가 "흰 배경"으로 오판되던 사각(7/4). 판정 불가 취급.
  function alphaOf(c){var m=c.match(/rgba\([^)]*,\s*([\d.]+)\s*\)/);return m?parseFloat(m[1]):1;}
  document.querySelectorAll('.slide *').forEach(function(el){
    if(!el.childNodes.length||el.offsetParent===null) return;
    var hasText=[].some.call(el.childNodes,function(n){return n.nodeType===3&&n.textContent.trim();});
    if(!hasText) return;
    var cs=getComputedStyle(el); if(parseFloat(cs.opacity)<0.05) return;
    var fg=lum(cs.color); if(fg===null) return;
    var p=el, bg=null;
    while(p && p.nodeType===1){
      var pcs=getComputedStyle(p);
      if(pcs.backgroundImage!=='none') return;             // 그라디언트 위 = 판정 불가
      var b2=pcs.backgroundColor;
      if(b2 && !/rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*0\s*\)/.test(b2) && b2!=='transparent'){
        if(alphaOf(b2)<0.9) return;                        // 반투명 = 실효색 판정 불가
        bg=lum(b2);break;
      }
      p=p.parentElement;
    }
    if(bg===null) return;
    if(Math.abs(fg-bg)<0.08){                              // 근소 명도차 = 사실상 무독만 잡는다(스타일 취향 X)
      var sl=el.closest('.slide');
      var pid=(sl&&sl.dataset.pageId)||'?';
      if(lowc.indexOf(pid)<0) lowc.push(pid);
    }
  });
  document.title='FITREPORT|ovf:'+ovf.join(',')+'|sparse:'+sparse.join(',')+'|hovf:'+hovf.join(',')+'|lowc:'+lowc.join(',');
})();
</script>
EOF
RAW="$("$CHROME" --headless=new --disable-gpu --dump-dom "file://$FIT" 2>/dev/null | grep -o 'FITREPORT|[^<]*' | head -1 || true)"
rm -f "$FIT"
if [ -n "$RAW" ]; then
  _t="${RAW#*ovf:}"; OVF="${_t%%|*}"
  _t="${RAW#*sparse:}"; SPARSE="${_t%%|*}"
  _t="${RAW#*hovf:}"; HOVF="${_t%%|*}"
  LOWC="${RAW##*lowc:}"
  if [ -n "$OVF" ]; then
    echo "FIT_OVERFLOW: $OVF — 본문이 세로 공간을 초과해 잘림. Loop B(designer→page-planner)로 분리/압축 필요."
  else
    echo "FIT_OK: 세로 오버플로 없음."
  fi
  if [ -n "$SPARSE" ]; then
    echo "FIT_SPARSE: $SPARSE — 본문 과소밀도(빈 공간 과다). 최소 밀도 가이드 검토(병합·시각 추가)."
  fi
  if [ -n "$HOVF" ]; then
    echo "FIT_HOVERFLOW: $HOVF — 본문 가로 초과(칩·nowrap·SVG 폭). 잘린 글자 확인 필요."
  fi
  if [ -n "$LOWC" ]; then
    echo "FIT_LOWCONTRAST: $LOWC — 글자색≈배경색 무독 의심(closing 칩 navy-on-navy 클래스). 실측 확인 필요."
  fi
else
  echo "FIT_CHECK_SKIP: DOM 측정 실패(Chrome dump-dom 미동작) — 시각 QA 수동 확인 필요."
fi

echo "→ 다음: 클차장이 이 PDF를 Read로 직접 읽고 시각 QA (차트 렌더·그레이아웃·깨짐·여백). 보고 안 하고 '됐다' 금지."
