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

# ─ 문체 게이트 (후추님 7/27 "개발로 무조건 확인하고 거르게") ─
# SoT = references/writing-standard.md "기계 검출 금지 표현" 절 — 목록 수정은 반드시 양쪽 동시.
# 은유 동사·압축 명사구: 실무 보고서 톤 위반. 검출 = 게이트 실패(exit 1) → 교정 후 재실행.
STYLE_BANNED = [
    "비어 있",   # → 공급이 없다·사실상 한 곳뿐이다
    "막힌다", "막혀 있",  # → 부족하다·못 미친다·좁다
    "닿는다", "닿는 길", "못 닿",  # → 접근하다·경로
    "성장을 끈",  # → 성장 동력은 ~다
    "걷어낸", "걷어내",  # → 뺀·제외한
    "몸통", "판독", "덩어리", "실물최대",  # 압축 은유 명사구 (7/26·7/27 후추님 실지적)
    "계정성 자산",  # → 연금·보험 같은 금융 자산 (7/26)
]

report = {}
style_fail = False
for pf in sorted(run.glob('pages/p*.html')):
    pid = pf.stem
    bf = run / 'briefs' / f'{pid}.json'
    if not bf.exists(): continue
    brief = json.load(open(bf))
    ok = allowed_set(brief)
    text = visible_text(pf)
    found = NUM.findall(text)
    unknown = sorted({n for n in found if n not in ok and n.replace(',','') not in ok})
    style_hits = [w for w in STYLE_BANNED if w in text]
    if style_hits: style_fail = True
    report[pid] = {'nums_visible': len(found), 'unknown': unknown, 'style_banned': style_hits}
    flag = '✗' if style_hits else ('⚠' if unknown else '✓')
    line = f"{flag} {pid}: {len(found)} nums, unknown={unknown if unknown else '없음'}"
    if style_hits: line += f" · 문체 위반={style_hits}"
    print(line)
json.dump(report, open(run/'qa'/'number_audit.json','w'), ensure_ascii=False, indent=1)
if style_fail:
    print("\n✗ 문체 게이트 실패 — writing-standard.md 기준으로 교정 후 재실행")
    sys.exit(1)
