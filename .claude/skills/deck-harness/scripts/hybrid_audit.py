#!/usr/bin/env python3
"""하이브리드 사후 C6 감사 (usage: python3 hybrid_audit.py <hybrid_run_dir>)
사후 C6 감사: 페이지 HTML의 가시 텍스트 수치를 brief 허용값과 대조.
허용 = brief metrics 값 + content_blocks 원문에 등장하는 수치 + 페이지번호/연도/저작권.
미허용 수치 = 사람 검토 대상으로 보고 (자동 실격 아님 — 스파이크용 감사)."""
import json, re, sys, html as H
from pathlib import Path

run = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
NUM = re.compile(r'\d[\d,]*\.?\d*')
ALWAYS_OK = {'2026','15','1280','720','34'}  # 저작권 연도·페이지수·스테이지·팩트체크 34/34 배지(원 런 08_factcheck 실적)

def visible_text(p):
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'<style.*?</style>', '', s, flags=re.S)
    s = re.sub(r'<script.*?</script>', '', s, flags=re.S)
    # SVG 좌표 속성 제거(텍스트 노드만 남김)
    s = re.sub(r'<(?!text|tspan)[^>]+>', ' ', s)
    s = re.sub(r'<[^>]+>', ' ', s)
    return H.unescape(s)

def allowed_set(brief):
    ok = set(ALWAYS_OK)
    ok.add(f"{brief['page_no']:02d}")
    for m in brief['metrics'].values():
        v = str(m['value'])
        ok.add(v); ok.add(v.replace(',',''))
        if '.' in v: ok.add(v.rstrip('0').rstrip('.'))
        try: ok.add(f"{float(v.replace(',','')):,.0f}")
        except: pass
    blob = ' '.join(str(m.get('scope','')) for m in brief['metrics'].values()) + json.dumps(brief['content_blocks'], ensure_ascii=False) + json.dumps(brief.get('sources',{}), ensure_ascii=False) + brief.get('short_title','')
    for n in NUM.findall(blob):
        ok.add(n); ok.add(n.replace(',',''))
    return ok

report = {}
for pf in sorted(run.glob('pages/p*.html')):
    pid = pf.stem
    bf = run / 'briefs' / f'{pid}.json'
    if not bf.exists(): continue
    brief = json.load(open(bf))
    ok = allowed_set(brief)
    found = NUM.findall(visible_text(pf))
    unknown = sorted({n for n in found if n not in ok and n.replace(',','') not in ok})
    report[pid] = {'nums_visible': len(found), 'unknown': unknown}
    flag = '⚠' if unknown else '✓'
    print(f"{flag} {pid}: {len(found)} nums, unknown={unknown if unknown else '없음'}")
json.dump(report, open(run/'qa'/'number_audit.json','w'), ensure_ascii=False, indent=1)
