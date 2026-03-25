"""
quality.py — 슬라이드 품질 채점 + 규칙 기반 보완
"""

import re
import copy


def _score_slide(slide: dict, prev_slide: dict = None) -> dict:
    """슬라이드 품질 채점 — 5개 항목 각 0~10점, 평균 반환

    설계 원칙: 올바르게 구성된 슬라이드는 자연스럽게 7.5 이상을 받아야 한다.
    보완 루프는 진짜 문제(이미지 누락, 수량 불일치 등)에만 개입.
    """
    stype = slide.get('type', '')
    scores = {}

    # ── 1. 헤드라인 길이 ──────────────────────────────────────
    # 22자 이하 = 임팩트 있는 슬라이드 헤드라인 (한/영 기준)
    # 길어질수록 슬라이드에서 가독성 저하 → 엄격하게 감점
    hl_text = (slide.get('headline') or '').strip()
    hl_len = len(hl_text)
    _VAGUE_HL = ['좋은', '최고의', '다양한', '훌륭한', '뛰어난', '혁신적', '전문적',
                 '맞춤형', '최적화된', '특별한', '더 나은', '새로운 시대', '가능성']
    if hl_len == 0:
        scores['headline'] = 10
    elif hl_len <= 22:
        _hl_base = 10
        if any(kw in hl_text for kw in _VAGUE_HL):
            _hl_base = max(_hl_base - 2, 4)
        scores['headline'] = _hl_base
    else:
        _hl_base = max(4, 10 - (hl_len - 22) // 3)
        if any(kw in hl_text for kw in _VAGUE_HL):
            _hl_base = max(_hl_base - 2, 4)
        scores['headline'] = _hl_base

    # ── 2. Body 밀도 ───────────────────────────────────────────
    nb = len(slide.get('body') or [])
    # 헤드라인/인용 중심 레이아웃: body 0이어도 정상
    _no_body_ok = {
        'cover', 'cta_session', 'section_break', 'contact',
        'pull_quote', 'big_statement', 'key_insight', 'quote_slide',
        'section_intro', 'section_header', 'chapter_break',
    }
    if nb == 0:         scores['body'] = 8 if stype in _no_body_ok else 3
    elif 2 <= nb <= 5:  scores['body'] = 10
    elif nb == 1:       scores['body'] = 7
    else:               scores['body'] = 6   # 6개 이상은 밀도 과잉

    # ── 3. 정보 계층 완성도 ────────────────────────────────────
    # sub: 있으면 최상. eyebrow는 stype에서 자동생성되므로 항상 존재로 간주.
    # Gemini가 명시적으로 eyebrow/sub를 설정했는지가 품질 지표
    has_sub = bool((slide.get('sub') or '').strip())
    has_ew_explicit = bool((slide.get('eyebrow') or slide.get('section_label') or '').strip())
    if stype in ('cover', 'cta_session'):
        scores['hierarchy'] = 10 if has_sub else 7
    elif has_sub:
        scores['hierarchy'] = 10
    elif has_ew_explicit:
        scores['hierarchy'] = 8
    else:
        scores['hierarchy'] = 7    # eyebrow 미설정 — _improve_slide()에서 보완

    # ── 4. 이미지 유무 ─────────────────────────────────────────
    # 이미지가 디자인에 쓰이지 않는 레이아웃은 평가 제외(만점)
    # 이미지가 필수인 레이아웃(split/portfolio)은 없으면 강하게 감점
    has_img = bool(slide.get('bg_b64'))
    _img_required = {'split', 'portfolio', 'comparison', 'mosaic'}
    _img_irrelevant = {
        'contact', 'cta_session', 'cta',
        'toc', 'table_of_contents', 'index',
        'section_intro', 'section_break', 'section_header',
        'section_divider', 'chapter_break',
        'numbered_process', 'process_cards', 'kpi_cards',
        'timeline_h', 'ruled_list', 'data_table',
        'pull_quote', 'big_statement', 'key_insight', 'quote_slide',
        'problem_solution', 'before_after_compare', 'asis_tobe',
    }
    if has_img or stype in _img_irrelevant:
        scores['image'] = 10
    elif stype in _img_required:
        scores['image'] = 4        # 필수 타입에 이미지 없음 — 실제 문제
    else:
        scores['image'] = 7        # 선택적 타입, 이미지 없음

    # ── 5. 헤드라인-바디 수량 일관성 ──────────────────────────
    # "5단계", "3가지", "4개" 등 숫자 언급이 실제 body 수와 일치하는지 검사
    _num_match = re.search(r'([2-9]|1[0-2])\s*(단계|가지|개|종|항목|스텝|step)', hl_text, re.IGNORECASE)
    if _num_match:
        claimed_n = int(_num_match.group(1))
        if nb >= claimed_n:
            scores['consistency'] = 10
        elif nb == claimed_n - 1:
            scores['consistency'] = 6   # 1개 부족 — 경고
        else:
            scores['consistency'] = max(2, 10 - (claimed_n - nb) * 3)   # 2개+ 부족
    else:
        scores['consistency'] = 10  # 수량 언급 없으면 만점

    # ── 6. 인접 슬라이드 body 중복 패널티 ─────────────────────────
    if prev_slide:
        _prev_tokens = set(' '.join(prev_slide.get('body') or []).split())
        _curr_tokens = set(' '.join(slide.get('body') or []).split())
        if _prev_tokens and _curr_tokens:
            _overlap = len(_prev_tokens & _curr_tokens) / max(len(_curr_tokens), 1)
            if _overlap >= 0.55:
                scores['consistency'] = max(scores['consistency'] - 3, 2)

    total = round(sum(scores.values()) / len(scores), 1)
    return {'breakdown': scores, 'total': total}


def _improve_slide(slide: dict, score: dict):
    """점수 낮은 항목을 규칙 기반으로 보완 — 변경 없으면 None 반환"""
    bd = score['breakdown']
    improved = copy.deepcopy(slide)
    changed = False

    # 헤드라인이 길면 구두점 기준으로 자르기
    if bd.get('headline', 10) < 7:
        hl = improved.get('headline', '')
        for sep in [':', ' - ', ',', '·', '—']:
            if sep in hl:
                improved['headline'] = hl.split(sep)[0].strip()
                changed = True; break
        else:
            improved['headline'] = hl[:22].strip()
            changed = True

    # eyebrow 없으면 슬라이드 타입에서 자동 생성
    if bd.get('hierarchy', 10) < 8 and not (improved.get('eyebrow') or '').strip():
        _ew_map = {
            'service_pillar': '핵심 서비스', 'problem': '문제 인식',
            'solution': '솔루션',            'benefit': '주요 이점',
            'feature': '주요 기능',          'case_study': '성공 사례',
            'team': '팀 소개',               'contact': '문의',
            'toc': '목차',                   'market': '시장 분석',
            'pain': '문제 분석',             'proof': '성과 증명',
            'why': '차별점',                 'how': '실행 방법',
            'key_metric': '핵심 지표',       'overview': '솔루션 개요',
            'challenge': '시장 현황',        'cta': '지금 시작하기',
        }
        stype2 = improved.get('type', '')
        for key, label in _ew_map.items():
            if key in stype2 and label:
                improved['eyebrow'] = label
                changed = True; break

    # body 없는데 sub 내용 있으면 sub → body[0] 승격
    if bd.get('body', 10) < 5 and not (improved.get('body') or []) and (improved.get('sub') or '').strip():
        improved['body'] = [improved['sub']]
        changed = True

    # sub 없으면 body 첫 항목에서 자동 파생
    # hierarchy < 8이고 cover/contact 제외 슬라이드에 적용
    stype_local = improved.get('type', '')
    _sub_skip = {'cover', 'contact', 'cta_session', 'section_intro', 'section_break',
                 'section_header', 'chapter_break', 'toc'}
    if (bd.get('hierarchy', 10) < 8
            and stype_local not in _sub_skip
            and not (improved.get('sub') or '').strip()):
        _body_items = improved.get('body') or []
        if _body_items:
            _first = str(_body_items[0])
            # 콜론 뒤 결과 부분 추출 (RULE H 포맷: "원인: 결과")
            _colon = _first.find(':')
            if _colon > 0 and _colon < len(_first) - 3:
                _sub_cand = _first[_colon + 1:].strip()
            else:
                _sub_cand = _first
            # 화살표 이후 최종 결과만 남기기
            if '→' in _sub_cand:
                _sub_cand = _sub_cand.split('→')[-1].strip()
            # 25자 이내로 자르기
            _sub_cand = _sub_cand[:30].strip()
            if len(_sub_cand) >= 8:
                improved['sub'] = _sub_cand
                changed = True

    # 헤드라인-바디 수량 불일치: 헤드라인에서 숫자 제거
    # (예: "5단계 프로세스" → "프로세스", body가 4개뿐일 때)
    if bd.get('consistency', 10) < 8:
        hl = improved.get('headline', '')
        hl_fixed = re.sub(
            r'\s*([2-9]|1[0-2])\s*(단계|가지|개|종|항목|스텝|step)\s*',
            ' ', hl, flags=re.IGNORECASE
        ).strip()
        if hl_fixed != hl and len(hl_fixed) > 3:
            improved['headline'] = hl_fixed
            changed = True

    return improved if changed else None
