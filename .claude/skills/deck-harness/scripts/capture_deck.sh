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
ABS="$(cd "$(dirname "$DECK")" && pwd)/$(basename "$DECK")"
mkdir -p "$(dirname "$OUT")"
OUT="$(cd "$(dirname "$OUT")" && pwd)/$(basename "$OUT")"
[ "$OUT" = "$ABS" ] && { echo "INVALID_OUTPUT: PDF 경로가 입력 HTML과 같음"; exit 2; }
# 실패한 재캡처 뒤 이전 PDF가 새 결과처럼 남지 않게, 정확한 출력 파일만 선제 무효화한다.
rm -f "$OUT"

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

# macOS Chrome/Skia는 로컬 CFF Pretendard OTF를 PDF Type 3 glyph 수백 개로 쪼개며,
# 일부 한글 bbox를 잘못 기록한다. 텍스트 레이어는 정상이라 pdftotext만으로는 잡히지 않는다.
# 동일 메트릭의 공식 정적 TrueType-outline WOFF2를 캡처 HTML에 data URI로 고정해 CFF 경로를 끊는다.
FONT_VERSION="v1.3.9"
FONT_BASE_URL="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@${FONT_VERSION}/packages/pretendard/dist/web/static/woff2"
FONT_CACHE_ROOT="${TMPDIR:-/tmp}/tickdeck-pdf-font-${FONT_VERSION}"
mkdir -p "$FONT_CACHE_ROOT"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# 저장소 내장 폰트(assets/fonts/, 커밋 대상) — 오프라인·CDN 장애 시에도 캡처가 서지 않게 한다.
LOCAL_FONT_DIR="$SCRIPT_DIR/../assets/fonts"

fetch_font() {
  font_name="$1"
  expected_sha="$2"
  font_path="$FONT_CACHE_ROOT/$font_name"
  if [ -f "$font_path" ] && [ "$(shasum -a 256 "$font_path" | awk '{print $1}')" = "$expected_sha" ]; then
    return 0
  fi
  if [ -f "$LOCAL_FONT_DIR/$font_name" ] && [ "$(shasum -a 256 "$LOCAL_FONT_DIR/$font_name" | awk '{print $1}')" = "$expected_sha" ]; then
    cp "$LOCAL_FONT_DIR/$font_name" "$font_path"
    chmod 600 "$font_path"
    return 0
  fi
  command -v curl >/dev/null 2>&1 || {
    echo "PDF_FONT_FETCH_ERROR: curl 없음 — TrueType PDF 폰트를 준비할 수 없음(로컬 assets에도 없음)."
    exit 1
  }
  font_part="$(mktemp "$FONT_CACHE_ROOT/.${font_name}.XXXXXX")"
  if ! curl -fsSL "$FONT_BASE_URL/$font_name" -o "$font_part"; then
    rm -f "$font_part"
    echo "PDF_FONT_FETCH_ERROR: $font_name 다운로드 실패(로컬 assets에도 없음). 캐시가 없으면 PDF 캡처를 중단함."
    exit 1
  fi
  actual_sha="$(shasum -a 256 "$font_part" | awk '{print $1}')"
  if [ "$actual_sha" != "$expected_sha" ]; then
    rm -f "$font_part"
    echo "PDF_FONT_HASH_ERROR: $font_name 무결성 불일치."
    exit 1
  fi
  chmod 600 "$font_part"
  mv "$font_part" "$font_path"
}

fetch_font "Pretendard-Thin.woff2"       "1539755224a64719d5b18406762c476db74fcc299b9e4641ca1e9812fbc7a09b"
fetch_font "Pretendard-ExtraLight.woff2" "df43dc9165dff4542114674bcd8b79b7daae6dec004004586d5d076fec6fe2aa"
fetch_font "Pretendard-Light.woff2"      "b7426635cce2ea2b95c9c802e43fba1c620e0dafaf25f737c069b8b4e09fa841"
fetch_font "Pretendard-Regular.woff2"    "fad853f7f47c6c8b103171e7193fa095708cdcd70850a71d93aa5379e8a61d63"
fetch_font "Pretendard-Medium.woff2"     "d03481330eeba0659ab5b87f25ceb504a35de377dd90a0d0aba2982eb2d05e2c"
fetch_font "Pretendard-SemiBold.woff2"   "c863f76a7de5c1ddc1ed8b2fa794964530774592c4f31407a84e2a2ae93f17f0"
fetch_font "Pretendard-Bold.woff2"       "4609c3356e536fafe38f4add0daeceb3d8595d3057bce13c428c33ddbd43d362"
fetch_font "Pretendard-ExtraBold.woff2"  "dd7c1e156f508eb962acc7a33a7a1896d1e0b71e11156fad96e731689ceb6dc3"
fetch_font "Pretendard-Black.woff2"      "c5fd0c3568fc1368a3edc0d0fbb36df029935954276e3573451b3bae09e27296"

CAPTURE_HTML="${ABS%.html}.__capture__.$$.html"
PDF_TMP="${OUT}.tmp.$$"
CAPTURE_DOM="${ABS%.html}.__capture__.$$.dom"
GLYPH_CHECK_DIR=""
cleanup_capture() {
  rm -f "$CAPTURE_HTML" "$PDF_TMP" "$CAPTURE_DOM"
  if [ -n "$GLYPH_CHECK_DIR" ] && [ -d "$GLYPH_CHECK_DIR" ]; then
    rm -rf "$GLYPH_CHECK_DIR"
  fi
}
trap cleanup_capture EXIT

python3 - "$ABS" "$CAPTURE_HTML" "$FONT_CACHE_ROOT" <<'PY'
import base64
import sys
from pathlib import Path

source_path, capture_path, font_root = map(Path, sys.argv[1:])
weights = (
    ("Thin", 100),
    ("ExtraLight", 200),
    ("Light", 300),
    ("Regular", 400),
    ("Medium", 500),
    ("SemiBold", 600),
    # 700(Bold) 실물 face는 macOS Chrome/Skia 서브셋에서 글리프 매핑이 어긋난다
    # (2026-08 실측: 몫→볶, 목차→복자, 리에종→리에송). 같은 계열의 ExtraBold로 대체한다.
    ("ExtraBold", 700),
    ("ExtraBold", 800),
    ("Black", 900),
)
faces = []
for name, weight in weights:
    encoded = base64.b64encode((font_root / f"Pretendard-{name}.woff2").read_bytes()).decode("ascii")
    faces.append(
        "@font-face{font-family:'TickDeck PDF Pretendard';font-style:normal;"
        f"font-weight:{weight};font-display:block;"
        f"src:url(data:font/woff2;base64,{encoded}) format('woff2');}}"
    )

source = source_path.read_text(encoding="utf-8")
before_style, style_marker, style_tail = source.partition("<style>")
stylesheet, style_end, after_style = style_tail.partition("</style>")
if not style_marker or not style_end:
    raise SystemExit("deck HTML has no renderer <style> block")
stylesheet = stylesheet.replace('"Pretendard"', '"TickDeck PDF Pretendard"')
stylesheet = stylesheet.replace('"Apple SD Gothic Neo"', '"TickDeck PDF Pretendard"')
source = before_style + style_marker + stylesheet + style_end + after_style
font_css = """
<style id="tickdeck-pdf-font">""" + "".join(faces) + """
:root{--mono-font:ui-monospace,"SFMono-Regular","SF Mono",Menlo,"TickDeck PDF Pretendard",monospace;}
</style>
"""
font_gate = """
<script>
(function(){
  var sentinel='기초화장용 리에종 차지하는 몫이 줄었다 목차 관찰 가격을';
  var weights=[100,200,300,400,500,600,700,800,900];
  window.__tickdeckFontsReady=Promise.all(weights.map(function(weight){
    return document.fonts.load(weight+' 16px "TickDeck PDF Pretendard"',sentinel);
  })).then(function(){return document.fonts.ready;}).then(function(){
    var ready=weights.every(function(weight){
      return document.fonts.check(weight+' 16px "TickDeck PDF Pretendard"',sentinel);
    });
    document.documentElement.dataset.tickdeckPdfFont=ready?'ready':'error';
    return ready;
  });
})();
</script>
"""
if "</head>" not in source:
    raise SystemExit("deck HTML has no </head> marker")
source = source.replace("</head>", font_css + font_gate + "</head>", 1)
capture_path.write_text(source, encoding="utf-8")
PY

# --headless=new 라야 CSS @page size(슬라이드 1280x720)를 지킨다. data URI 폰트라 네트워크
# dumpDOM→printToPDF를 같은 headless 세션에서 실행해, 인쇄 직전 fonts Promise 상태를 남긴다.
if ! "$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --run-all-compositor-stages-before-draw \
  --virtual-time-budget=5000 \
  --dump-dom \
  --print-to-pdf="$PDF_TMP" \
  "file://$CAPTURE_HTML" >"$CAPTURE_DOM" 2>/dev/null; then
  echo "PDF_CAPTURE_ERROR: Chrome PDF 캡처 실패."
  exit 1
fi
if ! grep -Fq 'data-tickdeck-pdf-font="ready"' "$CAPTURE_DOM"; then
  echo "PDF_FONT_READY_ERROR: document.fonts.ready/check 미완료 — PDF 캡처 중단."
  exit 1
fi

command -v pdffonts >/dev/null 2>&1 || {
  echo "PDF_FONT_CHECK_ERROR: pdffonts 없음 — Type 3 한글 회귀를 검증할 수 없어 캡처 중단."
  exit 1
}
FONT_REPORT="$(pdffonts "$PDF_TMP" 2>&1)"
if ! printf '%s\n' "$FONT_REPORT" | grep -Eq 'Pretendard.*CID TrueType'; then
  echo "PDF_FONT_EMBED_ERROR: TrueType Pretendard가 PDF에 임베드되지 않음."
  exit 1
fi
# 한글을 담는 폰트가 Type 3로 임베드되면 글리프가 다른 글자로 바뀐다(2026-08 실측).
# 라틴 전용 고정폭(Menlo·Courier 등)은 한글 글리프와 무관하므로 검사에서 제외한다.
UNSAFE_TYPE3="$(printf '%s\n' "$FONT_REPORT" | grep 'Type 3' | grep -Ei 'pretendard|gothic|malgun|noto|nanum|batang|myeongjo' || true)"
if [ -n "$UNSAFE_TYPE3" ]; then
  echo "PDF_FONT_TYPE3: 한글 폰트가 Type 3로 임베드됨 — 글리프 손상 위험, 캡처 중단."
  printf '%s\n' "$UNSAFE_TYPE3"
  exit 1
fi

command -v pdftoppm >/dev/null 2>&1 || {
  echo "PDF_GLYPH_CHECK_ERROR: pdftoppm 없음 — PDF glyph 래스터 검증 불가."
  exit 1
}
GLYPH_CHECK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/tickdeck-pdf-glyph.XXXXXX")"
GLYPH_WARN="$GLYPH_CHECK_DIR/pdftoppm.stderr"
if ! pdftoppm -r 30 -png "$PDF_TMP" "$GLYPH_CHECK_DIR/page" >/dev/null 2>"$GLYPH_WARN"; then
  echo "PDF_GLYPH_CHECK_ERROR: PDF 저해상도 래스터 검증 실패."
  tail -5 "$GLYPH_WARN"
  exit 1
fi
if grep -Fq 'Bad bounding box in Type 3 glyph' "$GLYPH_WARN"; then
  echo "PDF_GLYPH_BBOX: Bad bounding box in Type 3 glyph — 한글 글리프 손상 위험, 캡처 중단."
  exit 1
fi

# --- 4층 시각 QA 보강: 세로 오버플로(본문이 푸터로 넘쳐 잘림)·과소밀도 프로그램 검출 ---
# 렌더러가 overflow:hidden로 '조용히' 잘라낸 본문은 PDF만 봐선 안 보인다 → 코드로 신호를 남긴다.
# ponytail: Chrome dump-dom 측정. 측정 실패 시 SKIP만 출력(차단 아님) — 더 정밀하면 puppeteer로 교체.
FIT="${ABS%.html}.__fit__.html"
cp "$CAPTURE_HTML" "$FIT"
cat >> "$FIT" <<'EOF'
<script>
(function(){
  Promise.resolve(window.__tickdeckFontsReady).then(function(fontsReady){
  if(!fontsReady){document.title='FITREPORT_ERROR|font:not-ready';return;}
  var ovf=[], sparse=[], hovf=[], sourceClips=[], bandovf=[], annotationOverlap=[], lowc=[], ovl=[];
  document.querySelectorAll('.slide').forEach(function(s){
    var b=s.querySelector('.body'); if(!b) return;
    var gap=b.clientHeight-b.scrollHeight, id=s.dataset.pageId||'?';
    // 슬라이드 전체 기준도 본다 — body는 멀쩡한데 각주·출처·푸터가 720px 밖으로 밀리거나
    // 그리드 셀 내용이 잘리는 클래스(7/4 dark p10 실측 — body 게이지만으론 무증상).
    if(s.scrollHeight - s.clientHeight > 2 && ovf.indexOf(id)<0) ovf.push(id);
    if(gap < -2 && ovf.indexOf(id)<0) ovf.push(id);
    else if(gap > 240 && !/layout-(divider|closing|cover|index|matrix)/.test(s.className)) sparse.push(id);
    // hero_bleed는 블리드가 문법(수치가 우측 여백 너머로) — 의도된 가로 초과라 hovf 제외
    if(b.scrollWidth - b.clientWidth > 4 && !/layout-hero-bleed/.test(s.className)) hovf.push(id);
    s.querySelectorAll('.source-row,.source-link').forEach(function(el){
      var cs=getComputedStyle(el);
      var hides=/hidden|clip/.test(cs.overflowX+' '+cs.overflowY);
      var noWrap=cs.whiteSpace==='nowrap';
      if((hides || noWrap) && el.scrollWidth - el.clientWidth > 4 && sourceClips.indexOf(id)<0) sourceClips.push(id);
    });
    s.querySelectorAll('.title-band-text,.visual-title-band').forEach(function(el){
      if((el.scrollHeight - el.clientHeight > 2 || el.scrollWidth - el.clientWidth > 2) && bandovf.indexOf(id)<0) {
        bandovf.push(id);
      }
    });
  });
  // 저대비 무독 텍스트 — closing 칩 navy-on-navy처럼 글자색≈배경색이라 실측으로만 잡히던 클래스(7/3).
  // 텍스트 leaf의 색 vs 가장 가까운 불투명 배경색의 명도차. 그라디언트(background-image) 조상은 판정 불가라 skip.
  // color-mix() 결과는 Chrome이 color(srgb r g b) 0-1 float로 돌려줌(7/5 실측) — rgb() 0-255와 스케일 분기.
  function lum(c){var m=c.match(/\d+(\.\d+)?/g);if(!m)return null;var d=/^color\(/.test(c)?1:255;return (0.2126*m[0]+0.7152*m[1]+0.0722*m[2])/d;}
  // 반투명 배경(알파<0.9)은 실효색을 모름 — 다크 테마의 rgba 카드가 "흰 배경"으로 오판되던 사각(7/4). 판정 불가 취급.
  function alphaOf(c){var m=c.match(/rgba\([^)]*,\s*([\d.]+)\s*\)/)||c.match(/^color\([^)]*\/\s*([\d.]+)\s*\)/);return m?parseFloat(m[1]):1;}
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
  var textCache=new Map();
  function textElements(slide){
    if(textCache.has(slide)) return textCache.get(slide);
    var els=[];
    slide.querySelectorAll('*').forEach(function(el){
      if(el.closest('[aria-hidden="true"]')) return;
      if(!el.childNodes.length||el.offsetParent===null) return;
      var hasText=[].some.call(el.childNodes,function(n){return n.nodeType===3&&n.textContent.trim();});
      if(!hasText) return;
      var cs=getComputedStyle(el); if(parseFloat(cs.opacity)<0.05) return;
      // 인라인 요소가 줄바꿈되면 boundingRect가 이웃까지 덮어 오탐 → 줄 단위 client rects 사용
      var rects=[].filter.call(el.getClientRects(),function(r){return r.width>0&&r.height>0;});
      if(!rects.length) return;
      els.push({el:el, rects:rects});
    });
    textCache.set(slide,els);
    return els;
  }
  document.querySelectorAll('.slide').forEach(function(s){
    var id=s.dataset.pageId||'?';
    var els=textElements(s);
    for(var i=0;i<els.length;i++){
      for(var j=i+1;j<els.length;j++){
        var a=els[i], b=els[j], hit=false;
        if(a.el.contains(b.el)||b.el.contains(a.el)) continue;
        a.rects.forEach(function(ra){ b.rects.forEach(function(rb){
          var x=Math.max(0,Math.min(ra.right,rb.right)-Math.max(ra.left,rb.left));
          var y=Math.max(0,Math.min(ra.bottom,rb.bottom)-Math.max(ra.top,rb.top));
          if(x*y>Math.min(ra.width*ra.height,rb.width*rb.height)*0.25) hit=true;
        });});
        if(hit){
          if(ovl.indexOf(id)<0) ovl.push(id);
          i=els.length; break;
        }
      }
    }
  });
  document.querySelectorAll('.slide').forEach(function(s){
    var id=s.dataset.pageId||'?';
    var anns=[].filter.call(s.querySelectorAll('[data-annotation-kind]'),function(el){
      if(el.offsetParent===null && !(el instanceof SVGElement)) return false;
      var r=el.getBoundingClientRect();
      return r.width>0 && r.height>0;
    }).map(function(el){
      var r=el.getBoundingClientRect();
      var svg=el.closest('svg');
      return {el:el, rect:r, svgRect:svg?svg.getBoundingClientRect():null};
    });
    anns.forEach(function(a){
      if(!a.svgRect) return;
      if(a.rect.left<a.svgRect.left-4 || a.rect.right>a.svgRect.right+4 || a.rect.top<a.svgRect.top-4 || a.rect.bottom>a.svgRect.bottom+4){
        if(annotationOverlap.indexOf(id)<0) annotationOverlap.push(id);
      }
    });
    for(var i=0;i<anns.length;i++){
      for(var j=i+1;j<anns.length;j++){
        if(anns[i].el.contains(anns[j].el)||anns[j].el.contains(anns[i].el)) continue;
        var a=anns[i].rect, b=anns[j].rect;
        var x=Math.max(0,Math.min(a.right,b.right)-Math.max(a.left,b.left));
        var y=Math.max(0,Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top));
        if(x*y>Math.min(a.width*a.height,b.width*b.height)*0.28){
          if(annotationOverlap.indexOf(id)<0) annotationOverlap.push(id);
          i=anns.length; break;
        }
      }
    }
  });
  document.title='FITREPORT|ovf:'+ovf.join(',')+'|sparse:'+sparse.join(',')+'|hovf:'+hovf.join(',')+'|sclip:'+sourceClips.join(',')+'|bandovf:'+bandovf.join(',')+'|annovl:'+annotationOverlap.join(',')+'|ovl:'+ovl.join(',')+'|lowc:'+lowc.join(',');
  }).catch(function(){document.title='FITREPORT_ERROR|font:rejected';});
})();
</script>
EOF
RAW="$("$CHROME" --headless=new --disable-gpu --virtual-time-budget=5000 --dump-dom "file://$FIT" 2>/dev/null | grep -Eo 'FITREPORT(_ERROR)?\|[^<]*' | head -1 || true)"
rm -f "$FIT"
if [[ "$RAW" == FITREPORT_ERROR\|* ]]; then
  echo "FIT_FONT_ERROR: ${RAW#FITREPORT_ERROR|} — 캡처와 같은 폰트로 FIT을 측정할 수 없어 중단."
  exit 1
elif [ -n "$RAW" ]; then
  _t="${RAW#*ovf:}"; OVF="${_t%%|*}"
  _t="${RAW#*sparse:}"; SPARSE="${_t%%|*}"
  _t="${RAW#*hovf:}"; HOVF="${_t%%|*}"
  _t="${RAW#*sclip:}"; SCLIP="${_t%%|*}"
  _t="${RAW#*bandovf:}"; BANDOVF="${_t%%|*}"
  _t="${RAW#*annovl:}"; ANNOVL="${_t%%|*}"
  _t="${RAW#*ovl:}"; OVL="${_t%%|*}"
  LOWC="${RAW##*lowc:}"
  if [ -n "$OVF" ]; then
    echo "FIT_OVERFLOW: $OVF — 본문이 세로 공간을 초과해 잘림. Loop B(designer→page-planner)로 분리/압축 필요."
    # PDF는 디버깅용으로 그대로 둔다(아래 mv) — 단 exit 코드로 파이프라인에 실패를 알린다.
    FIT_OVERFLOW_HIT=1
  else
    echo "FIT_OK: 세로 오버플로 없음."
  fi
  if [ -n "$SPARSE" ]; then
    echo "FIT_SPARSE: $SPARSE — 본문 과소밀도(빈 공간 과다). 최소 밀도 가이드 검토(병합·시각 추가)."
  fi
  if [ -n "$HOVF" ]; then
    echo "FIT_HOVERFLOW: $HOVF — 본문 가로 초과(칩·nowrap·SVG 폭). 잘린 글자 확인 필요."
  fi
  if [ -n "$SCLIP" ]; then
    echo "FIT_SOURCE_CLIP: $SCLIP — source-row/source-link가 hidden·nowrap으로 가로 내용을 잘라냄. 출처 랩/축약 필요."
  fi
  if [ -n "$BANDOVF" ]; then
    echo "FIT_BAND_OVERFLOW: $BANDOVF — title band 텍스트가 2줄/밴드 높이를 초과함. 제목 축약 또는 크롬 해제 필요."
  fi
  if [ -n "$ANNOVL" ]; then
    echo "FIT_ANNOTATION_OVERLAP: $ANNOVL — annotation 겹침/차트 밖 이탈 의심. 앵커·형태·차트 분리 확인 필요."
  fi
  if [ -n "$OVL" ]; then
    echo "FIT_TEXT_OVERLAP: $OVL — 텍스트 상호 겹침 의심. 실측 확인 필요."
  fi
  if [ -n "$LOWC" ]; then
    echo "FIT_LOWCONTRAST: $LOWC — 글자색≈배경색 무독 의심(closing 칩 navy-on-navy 클래스). 실측 확인 필요."
  fi
else
  echo "FIT_CHECK_ERROR: DOM 측정 실패(Chrome dump-dom 미동작) — PDF 확정 중단."
  exit 1
fi

mv "$PDF_TMP" "$OUT"
echo "CAPTURED: $OUT"

INK_FAIL_HIT=0
if [ -f "$OUT" ]; then
  INK_SCRIPT="$(cd "$(dirname "$0")" && pwd)/qa_ink.py"
  if [ -f "$INK_SCRIPT" ]; then
    # set -e 아래에서 실패 치환 대입은 그 줄에서 스크립트를 죽인다 - || 목록으로 감싸 중단을 막는다.
    INK_RC=0
    INK_RAW="$(python3 "$INK_SCRIPT" "$OUT" 2>&1)" || INK_RC=$?
    [ -n "$INK_RAW" ] && printf '%s\n' "$INK_RAW"
    # 잉크 분포 게이트 FAIL(exit 2)은 반드시 전파한다 - 신호 삼킴이 8/10 저밀도 납품 사고의 원형.
    # 도구 부재·실행 오류(그 외 비0 코드)만 SKIP으로 낮춘다.
    if [ "$INK_RC" -eq 2 ]; then
      INK_FAIL_HIT=1
    elif [ "$INK_RC" -ne 0 ]; then
      reason="$(printf '%s\n' "$INK_RAW" | tail -1)"
      [ -n "$reason" ] || reason="qa_ink.py 실행 실패"
      echo "INK_CHECK_SKIP: $reason"
    fi
  else
    echo "INK_CHECK_SKIP: qa_ink.py 없음"
  fi
fi

echo "→ 다음: 클차장이 이 PDF를 Read로 직접 읽고 시각 QA (차트 렌더·그레이아웃·깨짐·여백). 보고 안 하고 '됐다' 금지."

if [ "${FIT_OVERFLOW_HIT:-0}" = "1" ] || [ "${INK_FAIL_HIT:-0}" = "1" ]; then
  [ "${INK_FAIL_HIT:-0}" = "1" ] && echo "INK_FAIL - 산출물은 디버깅용, 납품 금지"
  exit 2
fi
