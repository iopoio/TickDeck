"""
agents.py — AI 에이전트 함수 모음
  - agent_researcher: Factbook 추출
  - agent_strategist: 슬라이드 목차 기획
  - generate_slide_json: 슬라이드 JSON 카피라이팅
  - match_images_semantically: 이미지-슬라이드 시맨틱 매칭
  - _detect_page_subject / _detect_page_subject_from_text / _detect_auto_narrative: 주체 감지
"""

import json
import re
import time
from urllib.parse import urlparse, unquote

from google.genai import types as genai_types

from .config import _client, logger
from .utils import _color_vibrancy
from .prompts import (
    RESEARCHER_SYSTEM_PROMPT,
    RESEARCHER_USER_TEMPLATE,
    RESEARCHER_USER_TEMPLATE_C,
    STRATEGIST_SYSTEM_PROMPT,
    SLIDE_SYSTEM_PROMPT,
    MOOD_TONE,
    _PURPOSE_CONTEXT,
)


# ── Gemini 재시도 래퍼 ────────────────────────────────────────────────────────

def _call_gemini_with_retry(model, contents, config, max_retries=2):
    """429/500/503 등 일시 오류 시 지수 백오프 재시도 (10s→20s→40s)"""
    for attempt in range(max_retries + 1):
        try:
            resp = _client.models.generate_content(
                model=model, contents=contents, config=config
            )
            return resp
        except Exception as e:
            err_str = str(e)
            is_retryable = any(x in err_str for x in
                               ['429', 'RESOURCE_EXHAUSTED', '503', '500', 'UNAVAILABLE'])
            if is_retryable and attempt < max_retries:
                wait = 10 * (2 ** attempt)
                logger.warning(f"Gemini API 일시 오류 (attempt {attempt + 1}/{max_retries}) → {wait}초 대기 후 재시도: {err_str[:80]}")
                time.sleep(wait)
            else:
                raise


# ── 업종/내러티브 타입 사전 감지 ──────────────────────────────────────────────

_NT_C_KEYWORDS = {
    # 엔터테인먼트
    'entertainment', 'kpop', 'k-pop', 'k pop', 'music label', 'record label',
    'talent agency', 'artist management', 'idol', 'concert', 'tour', 'album',
    'musician', 'singer', 'rapper', 'band', 'choreography', 'trainee',
    '엔터', '엔터테인먼트', '음악', '레이블', '아티스트', '아이돌', '기획사',
    '연예', '공연', '앨범', '뮤직', '아이돌그룹', '연습생',
    # 스포츠/패션/미디어
    'sports club', 'sports agency', 'fashion brand', 'media production',
    '스포츠', '패션', '미디어',
}

# B-type 키워드 — 제조·인프라·부품 업종 감지 (C-type 이후 체크)
_NT_B_KEYWORDS = {
    # 한국어 제조/부품 업종
    '전자부품', '정밀부품', '중공업', '플랜트', '산업기계', '자동화설비',
    'mlcc', '적층세라믹', '인쇄회로기판', '전자재료', '반도체장비',
    '부품제조', '소재기업', '제조전문', '설비제조',
    # 영문 제조/부품 업종
    'electronic components', 'precision parts', 'heavy industry',
    'industrial machinery', 'semiconductor equipment', 'printed circuit board',
    'electronic materials', 'components manufacturer', 'parts manufacturer',
}

# D-type 키워드 — 럭셔리/프리미엄 브랜드 감지 (C/B 이후 체크)
_NT_D_KEYWORDS = {
    'luxury', 'premium', 'haute couture', 'fine dining', 'bespoke', 'prestige',
    '럭셔리', '프리미엄', '하이엔드', '파인다이닝', '명품', '고급',
}

# 도메인/회사명 기반 감지 — URL에 포함되면 factbook 내용과 무관하게 C타입 적용
_NT_C_DOMAINS = {
    # HYBE 계열
    'ibighit', 'hybe', 'bighit', 'bts', 'weverse',
    # SM/YG/JYP 3대 기획사
    'smtown', 'sment', 'yg-entertainment', 'ygfamily', 'jype', 'jypentertainment',
    # 중소 기획사
    'cube', 'pledis', 'starship', 'mnet', 'cjenm', 'kakaoent',
    'fncent', 'rbw', 'woolim', 'ts entertainment', 'wm entertainment',
    # 스포츠/크리에이티브
    'nba', 'nfl', 'kbo', 'kleague', 'puma', 'fila', 'newera',
}


# ── 브랜드 주체 감지 ──────────────────────────────────────────────────────────

def _detect_page_subject(url: str) -> dict:
    """URL 경로 패턴으로 아티스트/그룹 주체 1차 감지 (빠른 사전 힌트).
    '/artist/profile/LE SSERAFIM' → {'subject_name': 'LE SSERAFIM', 'subject_type': 'artist'}
    일반 기업 홈페이지 → {}
    """
    try:
        path = unquote(urlparse(url).path)
        # /artist/profile/NAME, /artist/NAME, /group/NAME, /talent/NAME, /member/NAME
        m = re.search(r'/(?:artist/profile|artist|group|talent|member)/([^/]+)', path, re.IGNORECASE)
        if m:
            name = m.group(1).strip()
            _SKIP = {'index', 'profile', 'about', 'list', 'all', 'en', 'ko', 'jp', 'zh'}
            if name and len(name) > 1 and name.lower() not in _SKIP:
                return {'subject_name': name, 'subject_type': 'artist'}
    except Exception as e:
        logger.debug(f"URL 주체 감지 파싱 오류: {e}")
    return {}


def _detect_page_subject_from_text(raw_info: str, url: str) -> dict:
    """크롤링 후 og:title / <title> 기반 주체 2차 감지 (더 신뢰도 높음).
    'LE SSERAFIM | SOURCE MUSIC' → {'subject_name': 'LE SSERAFIM', 'subject_type': 'artist', 'parent_org': 'SOURCE MUSIC'}
    일반 기업 홈페이지 → {}
    """
    # scrape_website가 삽입한 [og:title]: 값 추출
    m_og = re.search(r'\[og:title\]:\s*(.+)', raw_info)
    if not m_og:
        return _detect_page_subject(url)   # fallback to URL pattern
    og_title = m_og.group(1).strip()
    # "Sub | Parent" / "Sub - Parent" / "Sub – Parent" 패턴 (업종 무관 범용)
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    domain_parts = re.sub(r'^www\.', '', netloc).split('.')
    domain_name = domain_parts[0]  # 최상위 도메인 (e.g. 'sourcemusic', 'google')

    # 일반적인 페이지 섹션명 — 아티스트/브랜드명이 아님
    _GENERIC_PAGE_TERMS = {
        'profile', 'about', 'discography', 'music', 'members', 'news',
        'media', 'gallery', 'schedule', 'store', 'shop', 'home', 'main',
        'index', 'contact', 'career', 'careers', 'blog', 'press',
        'artist', 'artists', 'group', 'groups', 'official', 'site',
        'biography', 'bio', 'info', 'introduction', 'overview',
    }

    for sep in [' | ', ' ｜ ', ' - ', ' – ', ' — ']:
        parts = og_title.split(sep, 1)
        if len(parts) == 2:
            subject, parent = parts[0].strip(), parts[1].strip()
            # 첫 토큰이 generic 섹션명이면 다음 토큰을 실제 subject로 사용
            if subject.lower() in _GENERIC_PAGE_TERMS:
                # "CORTIS | BIGHIT MUSIC" → subject=CORTIS, parent=BIGHIT MUSIC
                sub_parts = parent.split(sep, 1)
                if len(sub_parts) == 2:
                    subject, parent = sub_parts[0].strip(), sub_parts[1].strip()
                    logger.info(f"[주체 감지-og] 섹션명 건너뜀, 실제 주체: '{subject}' (parent: {parent})")
                else:
                    # 하위 분리 불가 → parent 자체가 subject
                    subject = parent
                    parent = domain_name
                    logger.info(f"[주체 감지-og] 섹션명 건너뜀, parent를 주체로: '{subject}'")
            # 유효성: 주체가 2~50자, 부모·도메인명과 다름, 또 generic 섹션명 아님
            # parent가 4단어 이상 = 태그라인/업종설명 ("전략 중심 그로스 마케팅 에이전시") → 서브 주체 감지 무효
            _parent_is_tagline = len(parent.split()) >= 4
            if (2 <= len(subject) <= 50
                    and subject.lower() != parent.lower()
                    and subject.lower().replace(' ', '') != domain_name
                    and subject.lower() not in _GENERIC_PAGE_TERMS
                    and not _parent_is_tagline):
                _stype = _detect_page_subject(url).get('subject_type', 'sub-brand')
                logger.info(f"[주체 확정-og] '{subject}' (parent: {parent})")
                return {'subject_name': subject, 'subject_type': _stype or 'sub-brand',
                        'parent_org': parent}

    # ── 신호 2: 서브도메인 감지 (gemini.google.com → Gemini) ──────────────
    _SKIP_SUB = {'www', 'm', 'mobile', 'api', 'cdn', 'static', 'assets',
                 'media', 'img', 'images', 'mail', 'ns', 'ns1', 'ns2'}
    if len(domain_parts) >= 3:
        sub = domain_parts[0]
        if sub not in _SKIP_SUB and len(sub) >= 2:
            parent_domain = '.'.join(domain_parts[1:])
            logger.info(f"[주체 감지-subdomain] '{sub}' (parent: {parent_domain})")
            return {'subject_name': sub.capitalize(), 'subject_type': 'sub-brand',
                    'parent_org': parent_domain}

    # fallback: URL 경로 패턴
    return _detect_page_subject(url)


def _detect_auto_narrative(factbook, company_name, url=None):
    """업종 키워드 기반 내러티브 타입 사전 감지. 확신 있을 때만 반환."""
    try:
        # URL/도메인 기반 감지 (factbook보다 먼저, 더 신뢰도 높음)
        url_text = str(url or '').lower()
        if any(d in url_text for d in _NT_C_DOMAINS):
            return 'C'
        # factbook + 회사명 기반 감지
        text = (str(factbook) + ' ' + str(company_name)).lower()
        if any(k in text for k in _NT_C_KEYWORDS):
            return 'C'
        if any(k in text for k in _NT_B_KEYWORDS):
            return 'B'
        if any(k in text for k in _NT_D_KEYWORDS):
            return 'D'
    except Exception as e:
        logger.debug(f"내러티브 타입 자동 감지 오류: {e}")
    return None


# ── 1. 리서처 에이전트 ────────────────────────────────────────────────────────

def agent_researcher(raw_info: str, progress_fn=None, page_subject: dict = None,
                     forced_narrative: str = None) -> str:
    """Factbook 추출 에이전트 — 팩트만 Markdown으로 반환"""
    def _p(m):
        if progress_fn: progress_fn(str(m))

    # C-type(아티스트/크리에이티브)이면 전용 템플릿 사용
    _is_c = (forced_narrative == 'C') or (page_subject and page_subject.get('subject_name'))
    _tmpl = RESEARCHER_USER_TEMPLATE_C if _is_c else RESEARCHER_USER_TEMPLATE

    # 주체 정보 힌트 (아티스트/서브브랜드 페이지 시 Researcher가 올바른 주체에 집중하도록)
    _subject_hint = ''
    if page_subject and page_subject.get('subject_name'):
        _sname = page_subject['subject_name']
        _sparent = page_subject.get('parent_org', '')
        _subject_hint = (
            f"\n\n[중요] 이 페이지의 주체는 '{_sname}'입니다"
            + (f" (소속: {_sparent})" if _sparent else "")
            + f". 팩트북 제목과 분석은 '{_sname}' 중심으로 작성하세요."
            + f" 소속사/레이블({_sparent or '상위 조직'})이 아닌 '{_sname}' 자체의 정보에 집중하세요.\n"
        )

    prompt = _tmpl.format(raw_info=raw_info) + _subject_hint
    try:
        resp = _call_gemini_with_retry(
            model="models/gemini-2.5-pro",
            contents=prompt,
            config={
                "system_instruction": RESEARCHER_SYSTEM_PROMPT,
                "temperature": 0.1,
                "max_output_tokens": 4000,
            }
        )
        factbook = resp.text.strip()
        _p(f"  → Factbook 추출 완료 ({len(factbook)}자)")
        return factbook
    except Exception as e:
        logger.error(f"Researcher 에이전트 실패, raw_info 직접 사용: {e}", exc_info=True)
        _p(f"  ⚠ Researcher 에이전트 실패, raw_info 직접 사용: {e}")
        return raw_info  # 폴백: 원문 그대로


# ── 2. 전략 기획자 에이전트 ───────────────────────────────────────────────────

def agent_strategist(factbook: str, company_name: str, progress_fn=None,
                     forced_narrative: str = None, purpose: str = 'brand'):
    """슬라이드 목차 기획 에이전트 — (narrative_type, storyline_list) 반환"""
    def _p(m):
        if progress_fn: progress_fn(str(m))

    forced_str = (
        f"\n\n[사용자 지정] 내러티브 타입: {forced_narrative}\n"
        f"반드시 TYPE {forced_narrative} 흐름을 사용하세요. 다른 타입으로 변경 금지."
    ) if forced_narrative and forced_narrative != 'auto' else ""
    purpose_str = (
        f"\n\n[발표 목적] {_PURPOSE_CONTEXT.get(purpose, '')}"
    ) if purpose and purpose not in ('brand', 'auto') else ""
    user_prompt = (
        f"회사명: {company_name}{forced_str}{purpose_str}\n\n"
        f"⚠️ 반드시 slides 배열에 7개 이상의 슬라이드 객체를 포함해서 JSON을 반환하세요.\n\n"
        f"[FACTBOOK]\n{factbook}"
    )
    _detected_nt = None  # Gemini 파싱 성공 시 저장, 폴백에서 사용
    try:
        resp = _call_gemini_with_retry(
            model="models/gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": STRATEGIST_SYSTEM_PROMPT,
                "temperature": 0.3,
                "max_output_tokens": 4000,
            }
        )
        text = resp.text.strip()
        # ```json ... ``` 또는 raw JSON 객체 추출
        m = re.search(r'\{[\s\S]*\}', text)
        if m:
            raw = m.group()
            # 스마트 쿼트 → 일반 쿼트 정제
            raw = raw.replace('\u201c', '"').replace('\u201d', '"')
            raw = raw.replace('\u2018', "'").replace('\u2019', "'")
            # 후행 쉼표 제거 (trailing comma)
            raw = re.sub(r',\s*([}\]])', r'\1', raw)
            # 리터럴 줄바꿈 → 공백 (JSON 문자열 내 unescaped \n 처리)
            raw = raw.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
            try:
                result = json.loads(raw)
            except json.JSONDecodeError:
                # 폴백: narrative_type + 슬라이드 항목 개별 추출
                _nt_m = re.search(r'"narrative_type"\s*:\s*"([A-DF])"', raw)
                _items = re.findall(
                    r'"slide_num"\s*:\s*(\d+)[^}]*?"type"\s*:\s*"([^"]+)"[^}]*?"topic"\s*:\s*"([^"]+)"',
                    raw
                )
                if _nt_m and _items:
                    result = {
                        "narrative_type": _nt_m.group(1),
                        "slides": [{"slide_num": int(n), "type": t, "topic": tp} for n, t, tp in _items]
                    }
                else:
                    raise
            narrative_type = result.get("narrative_type", "A")
            if forced_narrative and forced_narrative != 'auto':
                narrative_type = forced_narrative  # Gemini 응답 무시, 강제 타입 적용
            _detected_nt = narrative_type  # 예외 경로에서도 사용
            slides = result.get("slides", [])
            if len(slides) >= 5:
                _p(f"  → 내러티브 타입: {narrative_type} | {len(slides)}개 슬라이드 기획")
                return narrative_type, slides
            elif len(slides) >= 1:
                # 슬라이드 부족 → 1회 재시도 (강제 최소 개수 지정)
                _p(f"  ⚠ Strategist {len(slides)}개 슬라이드 → 재시도 중...")
                _retry_prompt = (
                    f"회사명: {company_name}\n내러티브 타입: {narrative_type}\n\n"
                    f"⚠️ 아래 JSON 형식으로 반드시 9개 슬라이드를 반환하세요. "
                    f"데이터 부족해도 각 TYPE 필수 슬라이드는 모두 포함해야 합니다.\n\n"
                    f"[FACTBOOK]\n{factbook[:3000]}"
                )
                _r2 = _call_gemini_with_retry(
                    model="models/gemini-2.5-flash",
                    contents=_retry_prompt,
                    config={
                        "system_instruction": STRATEGIST_SYSTEM_PROMPT,
                        "temperature": 0.2,
                        "max_output_tokens": 4000,
                    }
                )
                _m2 = re.search(r'\{[\s\S]*\}', _r2.text.strip())
                if _m2:
                    _raw2 = _m2.group()
                    _raw2 = re.sub(r',\s*([}\]])', r'\1', _raw2)
                    _raw2 = _raw2.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
                    try:
                        _res2 = json.loads(_raw2)
                        _slides2 = _res2.get("slides", [])
                        if len(_slides2) >= 5:
                            _p(f"  → 재시도 성공: {narrative_type} | {len(_slides2)}개 슬라이드")
                            return narrative_type, _slides2
                    except Exception as e2:
                        logger.debug(f"Strategist 재시도 JSON 파싱 실패: {e2}")
                _p(f"  ⚠ 재시도도 5개 미달, 기본 목차 사용")
    except Exception as e:
        logger.error(f"Strategist 에이전트 실패, 기본 목차 사용: {e}", exc_info=True)
        _p(f"  ⚠ Strategist 에이전트 실패, 기본 목차 사용: {e}")

    # 폴백 기본 목차 — Gemini 감지 타입 > forced_narrative > 'A' 우선순위
    _fallback_nt = (forced_narrative if forced_narrative and forced_narrative != 'auto'
                    else (_detected_nt or 'A'))
    _p(f"  → 기본 목차(TYPE {_fallback_nt}) 적용")
    _fallback_maps = {
        'C': [
            {"slide_num": 1, "type": "cover",            "topic": "브랜드 포지셔닝 + 핵심 가치"},
            {"slide_num": 2, "type": "brand_story",      "topic": "브랜드 탄생 배경과 철학"},
            {"slide_num": 3, "type": "creative_approach","topic": "우리만의 크리에이티브 방식"},
            {"slide_num": 4, "type": "showcase_work_1",  "topic": "대표 작업/아티스트/프로젝트 1"},
            {"slide_num": 5, "type": "showcase_work_2",  "topic": "대표 작업/아티스트/프로젝트 2"},
            {"slide_num": 6, "type": "key_metrics",      "topic": "주요 성과 수치"},
            {"slide_num": 7, "type": "proof_results",    "topic": "실제 성과 및 수상 이력"},
            {"slide_num": 8, "type": "cta_session",      "topic": "다음 단계 제안"},
            {"slide_num": 9, "type": "contact",          "topic": "연락처"},
        ],
        'B': [
            {"slide_num": 1, "type": "cover",            "topic": "기업 포지셔닝 + 핵심 기술력"},
            {"slide_num": 2, "type": "market_challenge", "topic": "산업 환경 변화와 기술 수요"},
            {"slide_num": 3, "type": "solution_overview","topic": "당사의 핵심 기술 솔루션"},
            {"slide_num": 4, "type": "service_pillar_1", "topic": "주요 제품군 및 기술 스펙"},
            {"slide_num": 5, "type": "service_pillar_2", "topic": "품질 인증 및 생산 역량"},
            {"slide_num": 6, "type": "proof_results",    "topic": "납품 실적 및 글로벌 파트너"},
            {"slide_num": 7, "type": "key_metrics",      "topic": "주요 경영 성과 지표"},
            {"slide_num": 8, "type": "cta_session",      "topic": "협력 제안"},
            {"slide_num": 9, "type": "contact",          "topic": "연락처"},
        ],
    }
    return _fallback_nt, _fallback_maps.get(_fallback_nt, [
        {"slide_num": 1, "type": "cover",             "topic": "회사 포지셔닝 + 핵심 가치 제안"},
        {"slide_num": 2, "type": "market_challenge",  "topic": "지금 이 업계에서 일어나는 변화"},
        {"slide_num": 3, "type": "pain_analysis",     "topic": "고객이 매일 겪는 4가지 문제"},
        {"slide_num": 4, "type": "solution_overview", "topic": "우리의 해결책 전체 그림"},
        {"slide_num": 5, "type": "how_it_works",      "topic": "어떻게 함께 일하는가"},
        {"slide_num": 6, "type": "proof_results",     "topic": "실제 성과 및 변화"},
        {"slide_num": 7, "type": "why_us",            "topic": "왜 우리를 선택해야 하는가"},
        {"slide_num": 8, "type": "cta_session",       "topic": "다음 단계 제안"},
        {"slide_num": 9, "type": "contact",           "topic": "연락처"},
    ])


# ── 3. 카피라이터(포맷터) 에이전트 ───────────────────────────────────────────

def generate_slide_json(factbook: str, storyline: list, narrative_type: str,
                        brand_assets: dict, company_name: str,
                        mood: str = 'professional', page_subject: dict = None,
                        slide_lang: str = 'ko'):
    """카피라이터 + JSON 포맷터 에이전트 — Factbook + Storyline → Slide JSON"""
    colors = brand_assets.get('colors', [])
    logo_url = brand_assets.get('logo_url', '')
    accent = next((c for c in colors if _color_vibrancy(c) >= 0.1), '#1A1A1A')
    tone_instruction = MOOD_TONE.get(mood, MOOD_TONE['professional'])

    # 아티스트 페이지 전용 주의사항
    _subject_hint = ''
    if page_subject and page_subject.get('subject_type') == 'artist':
        _subject_hint = f"""
⚠️ 아티스트 페이지 주의사항:
- brand.name = "{page_subject['subject_name']}" (소속 레이블/기획사명 절대 금지)
- 이 PPT는 레이블이 아닌 아티스트 {page_subject['subject_name']}를 소개하는 자료입니다.
- primaryColor: 레이블 로고색이 아닌, {page_subject['subject_name']}의 아이덴티티에 어울리는 색상.
  현재 추출된 색상 후보: {', '.join(colors[:5]) if colors else '없음'}
  레이블 브랜드색처럼 보이면 크리에이티브/엔터테인먼트 기본값(#1A1A1A 또는 #2C2C2C)으로 교체.
"""

    _lang_override = ''
    if slide_lang == 'en':
        _lang_override = """⚠️ CRITICAL LANGUAGE OVERRIDE ⚠️
ALL slide text (headline, subheadline, body[]) MUST be written in ENGLISH.
Do NOT write in Korean. Every single text field must be in English.
Company name (brand.name) should use the original name from the website.
This is a non-negotiable requirement.

"""
    user_prompt = f"""{_lang_override}회사명: {company_name}
브랜드 색상: {', '.join(colors[:8]) if colors else 'unknown — use industry-appropriate default'}
내러티브 타입: {narrative_type}
{_subject_hint}
━━━━ 톤앤매너 지침 ━━━━
{tone_instruction}

━━━━ STORYLINE (전략 기획자 확정 목차 — 이 순서와 타입을 그대로 따를 것) ━━━━
{json.dumps(storyline, ensure_ascii=False, indent=2)}

⚠️ STORYLINE 준수 규칙 (절대 위반 금지):
- 위 목차에 있는 슬라이드는 데이터가 부족해도 절대 생략하지 마세요.
  전체 스토리의 흐름이 무너집니다.
- 내용이 적으면 body를 2개로 줄이거나 sub를 생략해도 되지만, 슬라이드 자체는 반드시 출력해야 합니다.
- 위 목차에 없는 슬라이드 타입을 임의로 추가하는 것도 금지입니다.
- 슬라이드 순서도 위 목차 순서 그대로 유지할 것.

━━━━ BRAND COLOR RULE ━━━━
primaryColor = most vivid accent from extracted list (NOT near-black/white)
No vivid color found → industry default:
  tech/digital=#1A1A1A | finance/legal=#1A4FBA | construction=#E85D26
  healthcare=#0DA377   | creative/design=#FF3366 | other=#1A1A1A

━━━━ COPY RULES ━━━━
1. [NO MARKDOWN]: NEVER use ** (bold) or * in the text. Return pure plain text ONLY.
2. [SPACING]: When using numbered lists (1., 2.) or bullets, you MUST add a space after the number/bullet (e.g., '1. 데이터', '· 전략').
3. [NO SENTENCES]: For ALL slides (including market_shock), NEVER end a bullet with '~다' or '~요'. You MUST use noun phrases or short fragments (e.g., '~구축', '~제공', '~개선').
   GOOD: "수주 단가 22% 상승 → 영업이익률 구조적 개선"
         "AI 기반 타겟팅 · CTR 3배 · ROAS 995%"
         "데이터 사일로: 통합 분석 불가 → 예산 낭비 고착"
   BAD:  "저희 회사는 다양한 서비스를 제공하여 고객의 성장을 돕습니다" (문장형 금지)
         "고객을 위해 최선을 다하겠습니다" (서술문 금지)
4. CONSOLIDATION: max 2 service_pillar slides (service_pillar_1, service_pillar_2 only).
   If 3+ services exist → bundle them all into service_pillar_1 and service_pillar_2 body[].
4b. [CARD BODY FORMAT] — service_pillar_*, solution_overview, why_us, core_business_* 슬라이드의
    body[] 아이템은 반드시 "짧은제목: 설명" 형식을 사용할 것. 제목은 2-5 단어.
    GOOD: "전략 기획: 시장/고객/트렌드 기반 성장 로드맵 설계"
          "데이터 활용: 통합 분석 환경 구축 → 의사결정 정확도 향상"
          "성과 최적화: A/B 테스트 자동화 · ROAS 개선"
    BAD:  "시장/고객/트렌드 분석 기반으로 명확한 성장 전략을 기획합니다" (제목 없음)
    이 형식은 카드 UI에서 제목/설명을 시각적으로 분리하는 데 필수임.
4c. [ICON PREFIX] — service_pillar_*, solution_overview, why_us, core_business_*, how_it_works,
    pain_analysis, our_process 슬라이드의 body[] 아이템에는 내용에 맞는 아이콘 접두사를 적극 사용할 것.
    형식: "[아이콘명] 짧은제목: 설명"
    사용 가능 아이콘 목록 (항목 성격에 가장 가까운 것 선택):
      target, trending-up, trending-down, bar-chart, pie-chart, activity, zap, settings,
      dollar-sign, credit-card, wallet, coins, plus-circle, search, eye, download, upload,
      list, check, info, lightbulb, map-pin, users, user, briefcase, star, shield, award,
      clock, calendar, mail, phone, link, globe, layers, grid, box, package, truck,
      tool, cpu, database, server, code, terminal, monitor, smartphone, tablet,
      flag, bookmark, tag, lock, key, bell, chat, heart, thumbs-up, rocket,
      compass, map, navigation, wind, sun, moon, cloud, leaf, fire
    GOOD: "[target] 고객 분석: 세그먼트별 행동 패턴 분석 → 타겟 정밀도 향상"
          "[trending-up] 성장 전략: 시장 확대 로드맵 설계 및 실행"
          "[shield] 리스크 관리: 규제 준수 자동화 · 법적 리스크 최소화"
    BAD:  아이콘 없이 텍스트만 사용 (service_pillar_* 등에서는 아이콘 생략 금지)
5. Infographic labels: 2-5 words ONLY
5b. [BODY MINIMUM — 절대 규칙] — 모든 슬라이드의 body[]는 최소 2개 아이템을 포함해야 합니다.
    body 1개만 있으면 슬라이드가 허전해짐. 다만 데이터에 없는 내용을 지어내서 채우지 말 것.
    크롤링 데이터에서 관련 내용이 1개뿐이면, 같은 내용을 다른 관점(예: 기능 vs 효과, 현재 vs 미래)으로 분리하여 2개로 구성.
    ⚠️ C-type 필수 슬라이드(brand_story, creative_approach, showcase_work_1)는 특히 body 2개 이상 필수.
    데이터 부족 시에도 해당 업종/아티스트의 공통 서술로 반드시 2개 이상 채울 것.
6. NEVER fabricate phone numbers, addresses, client names, or KPIs not in data
6b. DATA FIDELITY — service_pillar_*, core_business_*, showcase_work_* 슬라이드의 서비스/역량 내용은
    반드시 크롤링된 데이터에 명시된 것만 사용. 데이터에 없는 서비스 영역을 추론·확장·발명 금지.
    전략적 재프레이밍(표현 고도화)은 허용하나, 회사가 실제로 제공하지 않는 서비스를
    존재하는 것처럼 작성하면 안 됨. 크롤링 데이터에 2개 서비스만 있으면 pillar 2개만 사용.
11. TONE — 회사소개서: 회사의 전문성과 역량을 구체적 사실로 전달하는 신뢰 어조.
    - GOOD: "~방식으로 ~문제를 해결합니다", "~를 통해 ~를 실현합니다", "~개 기업이 선택한 이유"
    - BAD:  "저희 회사를 소개합니다", "최선을 다하겠습니다" (모호하고 평범한 표현 금지)
    - BAD:  데이터에 없는 서비스를 "가능합니다", "지원합니다"로 만들어 내는 것
7. LANGUAGE: {{SLIDE_LANG_INSTRUCTION}}
8. Return ONLY valid JSON. No markdown. No comments.
10. UNIQUENESS: proof_of_concept = BREADTH (여러 고객사·산업의 성과를 한 장에).
    case_study = DEPTH (단일 고객사 하나의 여정: 문제→접근법→결과).
    두 슬라이드에서 동일 고객사 수치를 반복 금지.
    proof_of_concept image_en_hint: multi-client portfolio 스타일 사용.
    case_study image_en_hint: 해당 고객사 업종의 실제 환경 이미지.
9. Each slide MUST include "image_en_hint": 5-8 English words for a BACKGROUND IMAGE.
   CRITICAL: Apply the rule for the slide's category — wrong category = wrong image.

   ── CATEGORY 1: FACTUAL slides (team_intro, case_study, infrastructure_and_scale,
      corporate_overview, showcase_work_*, client_list, proof_of_concept, market_impact,
      flagship_experience, target_audience) ──
   RULE: Use concrete, industry-specific, real-world visual keywords.
   GOOD: "automated logistics warehouse interior wide shot"
         "modern semiconductor cleanroom workers"
         "aerial view busy container port terminals"
         "clean laboratory environment with equipment"
   BAD:  "teamwork", "success", "business people shaking hands"

   ── CATEGORY 2: ABSTRACT/CONCEPT slides (cover, market_shock, market_problem,
      core_philosophy, proprietary_methodology, governance, cta_session, contact,
      creative_philosophy, brand_story, our_process) ──
   RULE: Use VISUAL METAPHOR — architectural, geometric, textural, atmospheric.
         ABSOLUTELY FORBIDDEN words: handshake, puzzle, gears, compass, dart,
         target, synergy, trust, process, system, flowchart, diagram, chart, strategy.
   GOOD: "abstract minimal geometric glass architecture dark studio"
         "soft volumetric light flowing through metallic texture"
         "calm dark ocean surface macro shot long exposure"
         "overlapping translucent acrylic panels diffused backlight"
         "brutalist concrete corridor dramatic shadow perspective"
   BAD:  "business trust handshake partnership", "synergy gears working together",
         "complex process flowchart diagram"

   ── CATEGORY 3: SERVICE/PILLAR slides (service_pillar_1, service_pillar_2, service_pillar_3,
      core_business_1, core_business_2, core_business_3, our_process) ──
   RULE: Show the WORKSPACE, TOOL, or ENVIRONMENT of the service — NOT data outputs.
         ABSOLUTELY FORBIDDEN: chart, charts, dashboard, analytics, data visualization,
         financial, metrics, growth chart, bar graph, performance graph.
   GOOD: "modern creative agency workspace dual monitors design work"
         "professional team brainstorming whiteboard strategy session"
         "close-up hands typing laptop minimal desk setup"
         "marketing campaign print materials spread flat lay"
   BAD:  "data visualization dashboard digital interface"
         "analytics charts financial performance metrics growth"

━━━━ FACTBOOK (리서처 추출 팩트 — 이 내용에 있는 것만 사용, 발명 절대 금지) ━━━━
{factbook}"""

    logger.info("[3단계-C] 카피라이터: 슬라이드 JSON 작성 중...")
    try:
        response = _call_gemini_with_retry(
            model="models/gemini-2.5-flash",
            contents=user_prompt,
            config={
                "system_instruction": SLIDE_SYSTEM_PROMPT.replace(
                    '{{SLIDE_LANG_INSTRUCTION}}',
                    'ALL copy in English. Professional business tone. Company name (brand.name) should use the name as it appears on the website (do not translate company names).'
                    if slide_lang == 'en' else
                    'ALL copy in Korean, formal register (격식체/경어체). 회사명(brand.name)은 홈페이지에서 사용하는 이름 그대로 사용.'
                ),
                "temperature": 0.25,
                "max_output_tokens": 32000,
            }
        )

        text = response.text.strip()

        def clean_json_text(s):
            """LLM 응답에서 순수 JSON 부분만 추출하고 청소"""
            # 1. Markdown 코드 블록 제거
            s = re.sub(r'```json\s*(.*?)\s*```', r'\1', s, flags=re.DOTALL)
            s = re.sub(r'```\s*(.*?)\s*```', r'\1', s, flags=re.DOTALL)
            # 2. 첫 번째 { 와 마지막 } 사이만 추출
            start = s.find('{')
            end = s.rfind('}')
            if start != -1 and end != -1:
                s = s[start:end+1]
            # 3. 제어 문자 제거 (줄바꿈 제외)
            s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', s)
            return s.strip()

        cleaned_text = clean_json_text(text)

        def _inject_narrative(result):
            """Strategist가 결정한 narrative_type을 brand에 강제 주입"""
            if isinstance(result, dict):
                if 'brand' not in result:
                    result['brand'] = {}
                result['brand']['narrative_type'] = narrative_type
            return result

        def _recover_truncated_json(s):
            """토큰 한도로 잘린 JSON을 닫는 괄호 추가로 복구"""
            # 1) trailing comma 제거
            s = re.sub(r',\s*([\]}])', r'\1', s)
            # 2) 단독 줄 쉼표 보정
            s = re.sub(r'(\n[ \t]+\})\s*\n([ \t]+),', r'\1\n\2},', s)
            # 3) 잘린 문자열이 따옴표로 끊긴 경우: 마지막 따옴표 없는 문자열 닫기
            s = re.sub(r':\s*"([^"]*?)$', lambda m: f': "{m.group(1)}"', s)
            # 4) 열린 괄호 개수 세어 부족한 닫는 괄호 추가
            opens = s.count('{') - s.count('}')
            arrs  = s.count('[') - s.count(']')
            # 잘린 위치에서 불완전한 마지막 키-값 쌍 제거
            if opens > 0:
                last_complete = s.rfind('},\n')
                if last_complete == -1:
                    last_complete = s.rfind('}')
                if last_complete > 0:
                    s = s[:last_complete + 1]
                    opens = s.count('{') - s.count('}')
                    arrs  = s.count('[') - s.count(']')
            # 닫는 괄호 추가
            s = s.rstrip().rstrip(',')
            s += ']' * max(arrs, 0) + '}' * max(opens, 0)
            return s

        try:
            return _inject_narrative(json.loads(cleaned_text))
        except json.JSONDecodeError:
            logger.warning("표준 JSON 파싱 실패 → 잘린 JSON 복구 시도...")
            try:
                fixed_text = _recover_truncated_json(cleaned_text)
                result = json.loads(fixed_text)
                logger.info(f"JSON 복구 성공 — 슬라이드 {len(result.get('slides', []))}개")
                return _inject_narrative(result)
            except json.JSONDecodeError as e2:
                logger.warning(f"JSON 복구 실패: {e2}")

    except Exception as e:
        logger.error(f"JSON 생성/파싱 최종 오류: {e}", exc_info=True)
        logger.debug("--- Gemini Raw Response ---\n%s",
                     text if 'text' in locals() else "No response text")
        return None


# ── 4. 이미지 시맨틱 매칭 에이전트 ───────────────────────────────────────────

def match_images_semantically(slides, image_pool_metadata):
    """Gemini를 사용하여 슬라이드 내용과 가장 잘 어울리는 이미지를 매칭"""
    if not image_pool_metadata:
        return {}

    # 슬라이드 요약 정보 구성 (최대한 토큰 절약)
    slide_summaries = []
    for i, s in enumerate(slides):
        slide_summaries.append({
            "idx": i,
            "h": s.get('headline', '')[:40],
            "t": s.get('type', '')
        })

    # 이미지 메타데이터 요약
    image_summaries = []
    for i, img in enumerate(image_pool_metadata):
        image_summaries.append({
            "idx": i,
            "alt": img.get('alt', '')[:40],
            "ctx": img.get('context', '')[:60]
        })

    prompt = f"""
Assign the most relevant image index to each slide index from the pool.
Rules:
1. Match by semantic meaning (e.g., 'Service' slide -> image with project/work context).
2. NO REPETITION: Each image index is used ONLY ONCE.
3. If no image is a good fit for a slide, return null for that slide.
4. Output MUST be a single JSON object mapping slide index -> image index.

SLIDES: {json.dumps(slide_summaries, ensure_ascii=False)}
POOL: {json.dumps(image_summaries, ensure_ascii=False)}
"""

    try:
        resp = _call_gemini_with_retry(
            model="gemini-2.5-flash",
            contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        mapping = json.loads(resp.text)
        return {int(k): int(v) for k, v in mapping.items() if v is not None}
    except Exception as e:
        logger.warning(f"이미지 시맨틱 매칭 실패: {e}")
        return {}
