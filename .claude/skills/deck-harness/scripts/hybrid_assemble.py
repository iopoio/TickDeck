#!/usr/bin/env python3
"""usage: python3 hybrid_assemble.py <hybrid_run_dir>
pages/p*.html → deck.html (iframe 뷰어 — 페이지 CSS 완전 격리, 스코핑 변환 없음)
qa/shot_p*.png 있으면 → deck.pdf (헤드리스 실렌더 스크린샷 그대로 = 픽셀 정확).
왜 iframe: CSS 재작성(스코핑)은 변수 정의 룰을 깨뜨린 전례(7/27 회색 덱 사고) — 원본을 안 건드리는 격리가 정답."""
import sys
from pathlib import Path

run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
pages = sorted(run.glob('pages/p*.html'))
frames = '\n'.join(
    f'<div class="pg"><iframe src="pages/{p.name}" scrolling="no" loading="eager"></iframe></div>'
    for p in pages)
viewer = f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>deck — {run.name}</title>
<style>
body{{margin:0;background:#3A3D42;display:flex;flex-direction:column;align-items:center;gap:26px;padding:26px 0}}
.pg{{width:1280px;height:720px;box-shadow:0 8px 40px rgba(0,0,0,.4);flex:none;overflow:hidden}}
iframe{{width:1280px;height:720px;border:0;display:block}}
@media print{{ body{{background:#fff;padding:0;gap:0}} .pg{{box-shadow:none;page-break-after:always}} @page{{size:1280px 720px;margin:0}} }}
</style></head><body>
{frames}
</body></html>"""
(run / 'deck.html').write_text(viewer, encoding='utf-8')
print(f'deck.html: iframe viewer, {len(pages)} pages')

print("PDF는 크롬 인쇄로: chrome --headless=new --print-to-pdf=deck.pdf --no-pdf-header-footer file://<run>/deck.html")
