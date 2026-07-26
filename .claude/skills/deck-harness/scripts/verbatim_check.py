#!/usr/bin/env python3
"""소화 원칙 게이트 (후추님 7/27 — "틱덱은 소화한 내용만, 복붙은 없어").
덱 산출물의 가시 텍스트를 수집 원문(evidence pool PDF)과 대조해
연속 N자 원문 일치(=복붙)를 검출한다. 검출 = 게이트 실패(exit 1).

usage: python3 verbatim_check.py <run_dir(pages/)> <src_run_dir(01_evidence_pool.json)>
허용: 출처 서지(기관명·리포트 제목), 20자 미만 일치(고유명사·관용구 우연 일치).
한계(정직): 코퍼스는 로컬 PDF 원문만 — 웹 관찰 소스는 대조 불가(리포트에 커버리지 명시)."""
import json, re, sys, html as H
from pathlib import Path

N = 20  # 정규화 후 연속 일치 임계(한국어 20자 우연 일치는 사실상 불가)

def norm(s):
    return re.sub(r'[\s\W_]+', '', s, flags=re.UNICODE)

def visible_text(p):
    s = p.read_text(encoding='utf-8')
    s = re.sub(r'<style.*?</style>|<script.*?</script>', '', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return H.unescape(s)

def main():
    run, src = Path(sys.argv[1]), Path(sys.argv[2])
    ep = json.load(open(src / '01_evidence_pool.json'))
    allow = set()          # 서지 정보(제목·기관)는 복붙 아님
    corpus_parts, covered, uncovered = [], [], []
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit("pypdf 필요 (Think/.venv 사용)")
    for it in ep['items']:
        allow.add(norm(it.get('title', ''))); allow.add(norm(it.get('publisher', '')))
        lp = it.get('local_path', '')
        pdf = src.parent.parent / lp if lp.startswith('_workspace') else (src / lp if lp else None)
        if pdf and pdf.exists() and pdf.suffix == '.pdf':
            try:
                corpus_parts.append(norm(''.join(pg.extract_text() or '' for pg in PdfReader(pdf).pages)))
                covered.append(it['source_id'])
            except Exception as e:
                uncovered.append(f"{it['source_id']}(추출실패)")
        else:
            uncovered.append(it['source_id'])
    corpus = '\x00'.join(corpus_parts)
    print(f"코퍼스: PDF {len(covered)}건 {len(corpus)//1000}k자 · 대조 불가 {len(uncovered)}건 {uncovered}")

    fail = False
    for pf in sorted(run.glob('pages/p*.html')):
        text = norm(visible_text(pf))
        hits, i = [], 0
        while i + N <= len(text):
            win = text[i:i+N]
            if win in corpus:
                j = i + N          # 일치 구간 최대로 늘리기
                while j < len(text) and text[i:j+1] in corpus:
                    j += 1
                seg = text[i:j]
                import re as _re
                # 수치·단위 나열은 복붙이 아니라 데이터(C6가 원문 일치를 요구) — 숫자 제거 후
                # 남는 표현이 12자 미만이면 데이터 골격으로 판정·허용
                bare = _re.sub(r'[0-9]+', '', seg)
                if len(bare) >= 12 and not any(seg in a or a in seg for a in allow if len(a) >= 10):
                    hits.append(seg[:60] + ('…' if len(seg) > 60 else ''))
                i = j
            else:
                i += 1
        if hits:
            fail = True
            print(f"✗ {pf.stem}: 원문 연속 일치 {len(hits)}건 — {hits[:3]}")
        else:
            print(f"✓ {pf.stem}: 복붙 0")
    if fail:
        print("\n✗ 소화 원칙 게이트 실패 — 일치 구간을 자기 문장으로 재서술 후 재실행")
        sys.exit(1)
    print("\n✓ 소화 원칙 통과 — 산출물에 원문 연속 20자+ 복제 없음")

main()
