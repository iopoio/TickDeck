#!/usr/bin/env python3
"""하이브리드 designer 1단계: 06_deck_spec + 02_verified → 페이지별 자기완결 브리프.
usage: python3 hybrid_brief.py <src_run_dir> <hybrid_run_dir>"""
import json, sys
from pathlib import Path

src, out = Path(sys.argv[1]), Path(sys.argv[2])
(out / 'briefs').mkdir(parents=True, exist_ok=True)
(out / 'pages').mkdir(exist_ok=True)
(out / 'qa').mkdir(exist_ok=True)
spec = json.load(open(src / '06_deck_spec.json'))
reg = json.load(open(src / '02_verified.json'))
mr, sr = reg['metric_registry'], reg['source_registry']
n = len(spec['pages'])
for p in spec['pages']:
    pid = p['page_id']
    brief = {
        'page_id': pid, 'page_no': int(pid[1:]), 'page_count': n,
        'short_title': p.get('short_title', ''),
        'layout_hint_from_old_engine': p.get('layout', ''),
        'content_blocks': p.get('content', []),
        'metrics': {m: {k: mr[m].get(k) for k in ('value', 'unit', 'scope', 'source_ids', 'label')}
                    for m in p.get('allowed_metric_ids', []) if m in mr},
        'sources': {s: {'publisher': sr[s].get('publisher'), 'title': sr[s].get('title')}
                    for s in p.get('allowed_source_ids', []) if s in sr},
    }
    json.dump(brief, open(out / 'briefs' / f'{pid}.json', 'w'), ensure_ascii=False, indent=1)
print(f'briefs: {n}')
