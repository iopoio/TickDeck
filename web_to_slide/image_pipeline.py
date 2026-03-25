"""
image_pipeline.py — 슬라이드 비주얼 전략 + 회사 이미지 매칭
  - SLIDE_VISUAL_STRATEGY      : 슬라이드 타입별 비주얼 전략 분류표
  - IMAGE_SLIDE_TYPES          : 회사 이미지 사용 타입 세트 (B그룹, SLIDE_VISUAL_STRATEGY에서 파생)
  - OVERLAY_OPACITY            : B그룹 이미지 슬라이드 오버레이 불투명도
  - _HINT_BLACKLIST            : 이미지 매칭 쿼리 정제용 블랙리스트
  - _extract_en_hint           : 슬라이드에서 이미지 매칭용 영어 힌트 추출
  - _build_image_search_query  : 회사 이미지 풀 시맨틱 매칭 쿼리 조립
"""

import re


# ── 슬라이드 비주얼 전략 분류표 ───────────────────────────────────────────────
#
# 'typography'   : 이미지 없음 — 브랜드 컬러 배경 + 타이포그래피 + 인포그래픽
# 'company_image': 홈페이지 수집 이미지 풀에서 매칭 — 없으면 typography로 fallback
#
# McKinsey/BCG 스타일: 텍스트·데이터가 주인공. Pexels·Imagen 없음.
#
SLIDE_VISUAL_STRATEGY = {
    # ── A그룹: 순수 타이포그래피 + 브랜드 컬러 ──────────────────────────────
    # 표지/섹션 구분자
    'cover':                  'typography',
    'title_identity':         'typography',
    'section_intro':          'typography',
    'section_divider':        'typography',
    'chapter_break':          'typography',
    'section_break':          'typography',
    'section_header':         'typography',
    'toc':                    'typography',
    'table_of_contents':      'typography',

    # 문제/시장 분석
    'market_challenge':       'typography',
    'market_problem':         'typography',
    'market_shock':           'typography',
    'market_insights':        'typography',
    'market_analysis':        'typography',
    'market_overview':        'typography',
    'market_size':            'typography',
    'tam_sam_som':            'typography',
    'competitive_landscape':  'typography',
    'pain_analysis':          'typography',
    'pain_points':            'typography',
    'problem_solution':       'typography',
    'before_after_compare':   'typography',
    'asis_tobe':              'typography',

    # 솔루션/프로세스
    'solution_overview':      'typography',
    'our_solution':           'typography',
    'how_it_works':           'typography',
    'our_process':            'typography',
    'process_steps':          'typography',
    'methodology':            'typography',
    'approach':               'typography',
    'delivery_model':         'typography',
    'implementation':         'typography',
    'workflow':               'typography',

    # 성과/수치
    'proof_results':          'typography',
    'key_metrics':            'typography',
    'metrics':                'typography',
    'kpi':                    'typography',
    'results':                'typography',
    'impact':                 'typography',
    'performance_metrics':    'typography',
    'growth_metrics':         'typography',
    'financial_highlights':   'typography',
    'business_results':       'typography',
    'scalability_proof':      'typography',

    # 차별화/강점/팀
    'why_us':                 'typography',
    'competitive_advantage':  'typography',
    'differentiators':        'typography',
    'key_strengths':          'typography',
    'team_credibility':       'typography',
    'team_intro':             'typography',
    'ecosystem_partners':     'typography',

    # 히스토리/로드맵
    'company_history':        'typography',
    'growth_story':           'typography',
    'roadmap':                'typography',
    'milestones':             'typography',
    'evolution':              'typography',

    # 가치/철학
    'brand_story':            'typography',
    'core_values':            'typography',
    'brand_values':           'typography',
    'value_proposition':      'typography',
    'corporate_overview':     'typography',
    'about_us':               'typography',
    'dual_sided_value':       'typography',
    'curriculum_structure':   'typography',
    'creative_approach':      'typography',

    # 레이아웃 전용 (인포그래픽 중심)
    'pull_quote':             'typography',
    'big_statement':          'typography',
    'two_col_text':           'typography',
    'positioning_matrix':     'typography',
    'swot_analysis':          'typography',
    'comparison_table':       'typography',
    'feature_comparison':     'typography',

    # CTA/마무리
    'cta_session':            'typography',
    'cta':                    'typography',
    'contact':                'typography',

    # ── B그룹: 회사 실제 이미지 (없으면 typography fallback) ─────────────────
    'showcase_work_1':        'company_image',
    'showcase_work_2':        'company_image',
    'showcase_work_3':        'company_image',
    'case_study':             'company_image',
    'core_business_1':        'company_image',
    'core_business_2':        'company_image',
    'flagship_experience':    'company_image',
    'scale_proof':            'company_image',
    'client_list':            'company_image',
}


# ── IMAGE_SLIDE_TYPES: B그룹 타입 세트 ────────────────────────────────────────
IMAGE_SLIDE_TYPES = {k for k, v in SLIDE_VISUAL_STRATEGY.items() if v == 'company_image'}


# ── OVERLAY_OPACITY: B그룹 이미지 슬라이드 오버레이 불투명도 ──────────────────
OVERLAY_OPACITY = {
    "showcase_work_1":    0.55,
    "showcase_work_2":    0.55,
    "showcase_work_3":    0.58,
    "case_study":         0.65,
    "core_business_1":    0.62,
    "core_business_2":    0.62,
    "flagship_experience":0.58,
    "scale_proof":        0.60,
    "client_list":        0.68,
}


# ── A그룹 슬라이드 배경 스타일 추천 ─────────────────────────────────────────
# HTML 렌더러가 visual_style.bg_style 값으로 배경을 분기 렌더링
# solid_dark      : 어두운 단색 (기본)
# solid_light     : 밝은 단색 + 다크 텍스트
# gradient_accent : 브랜드 컬러 그라디언트
# gradient_diagonal: 대각선 그라디언트 (커버/스토리용)
# gradient_bold   : 강한 브랜드 컬러 (CTA용)
TYPOGRAPHY_BG_STYLE = {
    'cover':               'gradient_diagonal',
    'brand_story':         'gradient_diagonal',
    'section_intro':       'gradient_diagonal',
    'market_challenge':    'solid_dark',
    'market_shock':        'solid_dark',
    'pain_analysis':       'solid_dark',
    'pain_points':         'solid_dark',
    'market_problem':      'solid_dark',
    'key_metrics':         'solid_dark',
    'contact':             'solid_dark',
    'solution_overview':   'gradient_accent',
    'our_solution':        'gradient_accent',
    'proof_results':       'gradient_accent',
    'why_us':              'gradient_accent',
    'competitive_advantage': 'gradient_accent',
    'value_proposition':   'gradient_accent',
    'how_it_works':        'solid_light',
    'our_process':         'solid_light',
    'team_credibility':    'solid_light',
    'team_intro':          'solid_light',
    'company_history':     'solid_light',
    'ecosystem_partners':  'solid_light',
    'cta_session':         'gradient_bold',
    'cta':                 'gradient_bold',
}

# ── 클리셰/비관련 블랙리스트 ──────────────────────────────────────────────────
# 이미지 매칭 쿼리에서 제외할 단어 (스톡사진 클리셰 + 금융/코인 계열)

_HINT_BLACKLIST = re.compile(
    r'\b(handshake|puzzle|gear|gears|compass|dart|dartboard|target|'
    r'synergy|teamwork|strategy|workflow|flowchart|diagram|chart|'
    r'checklist|clipboard|trophy|lightbulb|magnifying|shaking.hands|high.five|'
    r'coin|coins|bitcoin|crypto|cryptocurrency|token|blockchain|wallet|nft|'
    r'stock|stocks|trading|forex|candlestick|'
    r'money|dollar|dollars|currency|cash|banknote|'
    r'bar.chart|pie.chart|line.chart|bar.graph|pie.graph|'
    r'charts|financial|analytics|dashboard|graph|graphs|'
    r'metrics|metric|visualization|performance.chart|growth.chart)\b',
    re.IGNORECASE
)
_HINT_FALLBACK = 'abstract minimal geometric architecture dark moody'


# ── 유틸리티 함수 ─────────────────────────────────────────────────────────────

def _build_image_search_query(slide: dict, industry: str = "", company_name: str = "") -> str:
    """회사 이미지 풀 시맨틱 매칭용 쿼리 생성
    - image_en_hint 앞 3단어 + 산업 키워드 조합
    - 추상 수식어(AI 생성 이미지 스타일 단어) 제거
    """
    _ABSTRACT_WORDS = re.compile(
        r'\b(abstract|glowing|geometric|futuristic|volumetric|cinematic|'
        r'photorealistic|visualization|dimensional|neon|holographic|'
        r'flowing|dynamic|ethereal|3d|cgi|render)\b', re.I)

    hint = (slide.get('image_en_hint') or '').strip()
    if hint:
        hint = _ABSTRACT_WORDS.sub('', hint)
        hint = re.sub(r'\s+', ' ', hint).strip()
        words = [w for w in hint.split() if len(w) > 3][:3]
        if words:
            if industry:
                words.append(industry.strip().split()[0])
            return ' '.join(words)

    ind = industry.strip().split()[0] if industry else 'business'
    return f"{ind} professional"


def _extract_en_hint(slide: dict, company_name: str = "") -> str:
    """슬라이드에서 회사 이미지 매칭용 영어 힌트 추출 (회사명 제외)"""
    exclude = (company_name or "").lower().strip()

    def clean_hint(text):
        if not text: return ""
        if exclude:
            text = re.sub(re.escape(exclude), '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip(', ')
        return text

    def apply_blacklist(text: str) -> str:
        cleaned = _HINT_BLACKLIST.sub('', text).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip(', ')
        return cleaned if len(cleaned) > 8 else _HINT_FALLBACK

    # 1순위: Gemini가 생성한 image_en_hint (블랙리스트 필터 적용)
    hint = clean_hint(slide.get('image_en_hint', ''))
    if hint:
        if _HINT_BLACKLIST.search(hint):
            hint = "abstract digital network connections and glowing geometric data structures"
        else:
            hint = apply_blacklist(hint)
        words = hint.split()
        return " ".join(words[:8])

    # 2순위: keywords 배열 중 영문만 (회사명 제외)
    kws = []
    for kw in (slide.get('keywords') or []):
        kw = clean_hint(str(kw))
        if kw and re.match(r'^[A-Za-z0-9 \-]+$', kw):
            kws.append(kw)
    if kws:
        return " ".join(kws[:3])

    # 3순위: 영문 subheadline (회사명 제외)
    sub = clean_hint(slide.get('subheadline', ''))
    if sub and re.match(r'^[A-Za-z0-9 ,\-&./]+$', sub):
        return " ".join(sub.split()[:4])

    # 4순위: headline에서 영어 단어 추출 (회사명 제외)
    headline = clean_hint(slide.get('headline', ''))
    en_words = re.findall(r'[A-Za-z][A-Za-z0-9\-]{2,}', headline)
    if en_words:
        return " ".join(en_words[:3])

    # 슬라이드 타입별 폴백
    stype = slide.get('type', '')
    _type_fallbacks = {
        'showcase_work_1':   'creative design craftsmanship precision',
        'showcase_work_2':   'digital experience interface elegance',
        'showcase_work_3':   'brand identity visual storytelling',
        'case_study':        'business results success professional',
        'core_business_1':   'industrial precision technology solution',
        'core_business_2':   'global network digital connectivity',
        'flagship_experience': 'premium quality elevation refinement',
        'scale_proof':       'growth achievement scale impact',
        'client_list':       'clients portfolio excellence professional',
    }
    return _type_fallbacks.get(stype, 'professional workspace modern')
