"""
pipeline.py — 메인 AI 파이프라인: run_pipeline()
"""

import os
import sys
import json
import re
import base64
import time
import io
import copy
import requests
from urllib.parse import urlparse

from .config import _client, validate_config, HEADERS, HAS_PIL, logger  # noqa: F401
from .scraper import scrape_website, clean_raw_text
from .brand_extractor import (
    extract_brand_assets, capture_logo_transparent,
    extract_website_images, download_image_b64,
)
from .agents import (
    agent_researcher, agent_strategist, generate_slide_json,
    match_images_semantically, _detect_page_subject,
    _detect_page_subject_from_text, _detect_auto_narrative,
    _call_gemini_with_retry,
)
from .image_pipeline import (
    OVERLAY_OPACITY, IMAGE_SLIDE_TYPES, SLIDE_VISUAL_STRATEGY, TYPOGRAPHY_BG_STYLE,
)
from .quality import _score_slide, _improve_slide
from .utils import _color_vibrancy, extract_dominant_color, _extract_svg_colors, _b64_mime
from .scraper import _playwright_screenshot_color
from .prompts import _PURPOSE_CONTEXT

if HAS_PIL:
    from PIL import Image as _PILImage


# ── 캐시 유틸리티 ──────────────────────────────────────────────────────────────

def _delete_cache(text_cache: str, img_cache: str, legacy_cache: str,
                  progress_fn=None):
    """텍스트/이미지 캐시 파일 삭제 (에러 시 자동 초기화용)"""
    for _cf in [text_cache, img_cache, legacy_cache]:
        try:
            if os.path.exists(_cf):
                os.remove(_cf)
                if progress_fn:
                    progress_fn(f"  → 캐시 삭제: {_cf}")
        except Exception as e:
            logger.debug(f"캐시 파일 삭제 실패 ({_cf}): {e}")


def _save_text_cache(data: dict, text_cache: str):
    """bg_b64/logoB64/faviconB64 제외한 텍스트 캐시 저장 (~1MB)"""
    d = copy.deepcopy(data)
    d.get('brand', {}).pop('logoB64', None)
    d.get('brand', {}).pop('faviconB64', None)
    for s in (d.get('slides') or []):
        s.pop('bg_b64', None)
        s.pop('bg_mime', None)
    with open(text_cache, 'w', encoding='utf-8') as _f:
        json.dump(d, _f, ensure_ascii=False, indent=2)


def _save_img_cache(data: dict, img_cache: str):
    """이미지 b64만 별도 저장 (~11MB, 재사용 시 선택적 로드)"""
    img_data = {
        'ts': int(time.time()),
        'logo_b64': data.get('brand', {}).get('logoB64', ''),
        'favicon_b64': data.get('brand', {}).get('faviconB64', ''),
        'slides': [
            {
                'bg_b64': s.get('bg_b64') or '',
                'bg_mime': s.get('bg_mime') or '',
                'type': s.get('type', ''),
            }
            for s in (data.get('slides') or [])
        ],
    }
    with open(img_cache, 'w', encoding='utf-8') as _f:
        json.dump(img_data, _f, ensure_ascii=False)


# ── TOC 슬라이드 자동 생성 ────────────────────────────────────────────────────

def _build_toc_slide(slides: list) -> dict | None:
    """
    슬라이드 목록을 보고 TOC 슬라이드를 자동 생성.
    cover/cta/toc 제외 + 의미 있는 headline 있는 슬라이드만 수집.
    항목이 2개 미만이면 None 반환.
    """
    skip_types = {'cover', 'title_identity', 'cta', 'cta_session', 'contact', 'toc'}
    items = []
    for s in slides:
        if s.get('type', '') in skip_types:
            continue
        hl = (s.get('headline') or '').strip()
        if hl and hl not in items:
            items.append(hl)
        if len(items) >= 7:
            break

    if len(items) < 2:
        return None

    return {
        "type": "toc",
        "headline": "INDEX",
        "subheadline": "",
        "body": items,
        "bg_b64": "",
        "bg_mime": "png",
        "overlay_opacity": 0,
    }


# ── 메인 파이프라인 ────────────────────────────────────────────────────────────

def run_pipeline(url: str, company_name: str = None, progress_fn=None,
                 narrative_type: str = None, mood: str = 'professional',
                 purpose: str = 'brand', brand_color: str = '', slide_lang: str = 'ko') -> dict:
    """
    AI 데이터 엔진 파이프라인: 크롤링 → Gemini JSON → 이미지 생성 → dict 반환

    Args:
        url: 대상 웹사이트 URL
        company_name: 회사명 (미지정시 URL 도메인에서 자동 추출)
        progress_fn: 진행 상황 콜백 함수 (line: str) -> None
        narrative_type: 내러티브 타입 강제 지정 ('A'/'B'/'C'/'D'/'auto'/None)
        mood: 디자인 무드 ('professional'/'trendy'/'minimal')

    Returns:
        dict: {brand, slides, meta} 형태의 슬라이드 데이터
    """
    validate_config()  # API 키 검증 — 누락 시 ValueError 즉시 발생

    storyline = []        # 모든 코드 경로에서 참조 가능하도록 최상단 초기화
    page_subject = {}     # 아티스트/그룹 페이지 감지 결과

    def _p(msg):
        if progress_fn:
            progress_fn(str(msg))
        else:
            try:
                sys.stderr.write(str(msg) + '\n')
                sys.stderr.flush()
            except Exception:
                pass  # stderr 자체 고장 — logger도 같은 문제, 무시

    # ── 아티스트/그룹 페이지 자동 감지 (URL 패턴 기반) ──────────────────────
    page_subject = _detect_page_subject(url)
    if page_subject:
        _p(f"  [주체 감지] {page_subject['subject_name']} ({page_subject['subject_type']}) 페이지")
        if not company_name:
            company_name = page_subject['subject_name']
            _p(f"  → company_name = '{company_name}'")
        # 아티스트 페이지 → C타입 강제 (이미지 중심 크리에이티브 레이아웃)
        if not narrative_type or narrative_type == 'auto':
            narrative_type = 'C'
            _p(f"  → narrative_type = C (아티스트 페이지 자동 적용)")

    if not company_name:
        domain = re.sub(r'^www\.', '', urlparse(url).netloc)
        company_name = domain.split('.')[0]
        _p(f"  ※ 회사명 미지정 → URL에서 자동 추출: '{company_name}'")

    _p(f"\n=== Web to Slide v4: {url} ===\n")
    _p(f"  [용도] {_PURPOSE_CONTEXT.get(purpose, purpose or 'brand')} (narrative_type={narrative_type or 'auto'})")

    # 분리 캐시 파일 (텍스트/이미지 분리로 ~1MB vs ~11MB 절감)
    _text_cache = f"slide_{company_name}_text.json"
    _img_cache  = f"slide_{company_name}_img.json"
    _legacy_cache = f"slide_{company_name}.json"   # 구버전 통합 캐시 (마이그레이션용)

    json_file = _text_cache   # 기본적으로 텍스트 캐시 사용
    slide_json = None
    assets = {}

    # 신규 텍스트 캐시 우선, 없으면 구버전 통합 캐시로 폴백
    _cache_to_load = _text_cache if os.path.exists(_text_cache) else (
                     _legacy_cache if os.path.exists(_legacy_cache) else None)
    if _cache_to_load:
        try:
            with open(_cache_to_load, "r", encoding="utf-8") as f:
                slide_json = json.load(f)
            # bg_b64는 항상 새로 생성 — 이전 런의 이미지(코인/주식 등 오류 이미지 포함) 재사용 방지
            for _s in (slide_json.get('slides') or []):
                _s.pop('bg_b64', None)
                _s.pop('bg_mime', None)
            _p(f"  → 기존 JSON 로드 완료: {json_file} (크롤링/Gemini 생략)")
            # narrative_type_str 복원 (캐시 로드 경로에서도 4693행 참조 가능하도록)
            narrative_type_str = slide_json.get('brand', {}).get('narrative_type', 'A')
            # 검증 블록이 storyline을 참조하므로 캐시 슬라이드에서 역구성
            storyline = [
                {'slide_num': i + 1, 'type': s.get('type', ''), 'topic': s.get('headline', '')}
                for i, s in enumerate(slide_json.get('slides', []))
            ]
            assets = {
                'logo_url': slide_json.get('logoUrl', ''),
                'logo_b64': slide_json.get('brand', {}).get('logoB64', ''),
                'colors': [slide_json.get('brand', {}).get('primaryColor', '#1A1A1A')],
                'site_img_pool_meta': [],
                'dominant_color': '',
                'hero_colors': [],
                # 캐시에 저장된 CSS 빈도 복원 (신규: top5 리스트+점수, 구버전: 단일값 폴백)
                'css_freq_colors': (slide_json['brand'].get('css_freq_colors_top5')
                                    or ([slide_json['brand']['css_freq_color']]
                                        if slide_json['brand'].get('css_freq_color') else [])),
                'css_freq_scores': slide_json['brand'].get('css_freq_scores_top5', {}),
                'og_image_color': slide_json.get('brand', {}).get('og_image_color', ''),
                # 흰검 지배형 감지용 — 캐시 경로에서도 isMonochrome 올바르게 작동하도록 복원
                'css_dark_total':  slide_json['brand'].get('css_dark_total', 0),
                'css_light_total': slide_json['brand'].get('css_light_total', 0),
                # 다크 사이트 감지용 — siteDarkBg로 폴백 (dark_bg_color는 캐시에 미포함)
                'dark_bg_color':   slide_json['brand'].get('siteDarkBg', ''),
            }
            # 이미지 캐시에서 로고·파비콘·슬라이드 배경 복원 (텍스트 캐시에는 이미지 미포함)
            if os.path.exists(_img_cache):
                try:
                    with open(_img_cache, 'r', encoding='utf-8') as _if:
                        _ic = json.load(_if)
                    if not assets['logo_b64']:
                        assets['logo_b64'] = _ic.get('logo_b64', '')
                        if assets['logo_b64']:
                            slide_json.setdefault('brand', {})['logoB64'] = assets['logo_b64']
                    if _ic.get('favicon_b64'):
                        slide_json['brand']['faviconB64'] = _ic['favicon_b64']
                    # 슬라이드 배경 이미지 복원 — type 기반 매핑 (슬라이드 수 변경에도 안전)
                    cached_by_type = {
                        cs.get('type', ''): cs
                        for cs in _ic.get('slides', [])
                        if cs.get('bg_b64') and cs.get('type')
                    }
                    restored = 0
                    for _s in slide_json.get('slides', []):
                        _cs = cached_by_type.get(_s.get('type', ''))
                        if _cs and not _s.get('bg_b64'):
                            _s['bg_b64'] = _cs['bg_b64']
                            _s['bg_mime'] = _cs.get('bg_mime') or 'png'
                            restored += 1
                    _p(f"  → 이미지 캐시 복원: 배경 {restored}개 / 로고 {'✓' if assets['logo_b64'] else '✗'}")
                except Exception as _e:
                    logger.warning(f"이미지 캐시 로드 실패: {_e}")
                    _p(f"  → 이미지 캐시 로드 실패: {_e}")
            # 캐시 경로: 로고 b64에서 도미넌트 컬러 재추출 (PNG/JPG) 또는 SVG 색 추출
            _cl = assets['logo_b64']
            _cl_mime = _b64_mime(_cl) if _cl else ''
            if _cl and _cl_mime == 'svg+xml':
                _svg_c = _extract_svg_colors(_cl)
                if _svg_c:
                    assets['dominant_color'] = _svg_c[0]
                    _p(f"  → (캐시) SVG 로고 컬러: {_svg_c[0]}")
            elif _cl and _cl_mime not in ['svg+xml']:
                try:
                    _dc = extract_dominant_color(base64.b64decode(_cl))
                    if _dc:
                        assets['dominant_color'] = _dc
                        _p(f"  → (캐시) 로고 도미넌트 컬러: {_dc}")
                except Exception as e:
                    logger.debug(f"캐시 경로 도미넌트 컬러 추출 실패: {e}")
        except Exception as e:
            logger.warning(f"기존 JSON 로드 실패, 새로 시작: {e}")
            _p(f"  → 기존 JSON 로드 실패, 새로 시작합니다: {e}")

    if not slide_json:
        _p("[1단계] 웹페이지 크롤링 중...")
        raw_info = scrape_website(url)
        _p(f"  → 텍스트 {len(raw_info)}자 추출 완료")

        # ── 크롤링 후 2차 주체 감지 (og:title 기반 — URL 패턴보다 신뢰도 높음) ──
        _refined_subject = _detect_page_subject_from_text(raw_info, url)
        if _refined_subject and _refined_subject.get('subject_name'):
            _old_name = company_name
            page_subject = _refined_subject
            company_name = _refined_subject['subject_name']
            # C-type 강제는 아티스트 페이지에만 — 일반 브랜드/에이전시는 Gemini가 결정
            if (not narrative_type or narrative_type == 'auto') and _refined_subject.get('subject_type') == 'artist':
                narrative_type = 'C'
            if company_name != _old_name:
                _p(f"  [주체 확정-og] {company_name} → narrative_type=C 적용")
                # 캐시 파일명 재계산 (company_name이 바뀐 경우)
                _text_cache = f"slide_{company_name}_text.json"
                _img_cache  = f"slide_{company_name}_img.json"
                _legacy_cache = f"slide_{company_name}.json"

        raw_info = clean_raw_text(raw_info)
        _p(f"  → 정제 후 {len(raw_info)}자 (노이즈 제거 + 중복 압축)\n")

        _p("[2단계] 브랜드 에셋 추출 중...")
        assets = extract_brand_assets(url)
        _p(f"  → 로고 URL: {assets['logo_url'] or '없음'}")
        _p(f"  → 컬러: {assets['colors'][:5] or '없음'}")
        fc = assets.get('footer_contact', {})
        _p(f"  → 푸터 연락처: {fc or '없음'}")

        _p("[2b단계] 로고 캐처 중 (SVG/PNG 우선)...")
        logo_b64 = capture_logo_transparent(url, logo_url=assets.get('logo_url', ''))

        # ── 아티스트 페이지: 레이블 로고 필터링 ──────────────────────────────
        # 로고 URL에 레이블(도메인) 식별자가 포함되고 아티스트명은 없으면 → 제거
        if page_subject and page_subject.get('subject_type') in ('artist', 'sub-brand'):
            _logo_url_lower = (assets.get('logo_url') or '').lower()
            _domain_key = urlparse(url).netloc.replace('www.', '').split('.')[0].lower()
            _subject_key2 = page_subject['subject_name'].replace(' ', '').lower()
            if _logo_url_lower and _domain_key in _logo_url_lower and _subject_key2 not in _logo_url_lower:
                _p(f"  → 레이블 로고 감지 ({_domain_key}) → 아티스트 페이지이므로 제거")
                logo_b64 = ''
                assets['logo_url'] = ''   # URL도 함께 제거 (슬라이드 JSON 주입 방지)

        assets['logo_b64'] = logo_b64 or ''

        # 로고에서 도미넌트 브랜드 컬러 추출 (PNG/JPG: 픽셀 분석, SVG: fill 추출)
        _dom_color = ''
        _logo_mime = _b64_mime(logo_b64) if logo_b64 else ''
        if logo_b64 and _logo_mime == 'svg+xml':
            _svg_c = _extract_svg_colors(logo_b64)
            if _svg_c:
                _dom_color = _svg_c[0]
                _p(f"  → SVG 로고 컬러: {_dom_color} (총 {len(_svg_c)}개 후보)")
        elif logo_b64:
            try:
                _dom_color = extract_dominant_color(base64.b64decode(logo_b64))
            except Exception as e:
                logger.debug(f"로고 도미넌트 컬러 추출 실패: {e}")
        if _dom_color:
            assets['dominant_color'] = _dom_color
            _p(f"  → 로고 도미넌트 컬러: {_dom_color}")
        else:
            assets['dominant_color'] = ''
        # hero_colors는 extract_brand_assets에서 이미 수집됨
        assets.setdefault('hero_colors', [])

        _p("[2b2단계] 파비콘 다운로드 중 (워터마크용)...")
        favicon_b64 = ''
        favicon_mime = 'png'
        favicon_url = assets.get('favicon_url', '')
        # 파비콘 도메인 검증: 입력 URL의 도메인과 다르면 외부 로고 → 스킵
        if favicon_url:
            _fav_domain = urlparse(favicon_url).netloc.replace('www.', '').lower()
            _src_domain = urlparse(url).netloc.replace('www.', '').lower()
            if _fav_domain and _src_domain and _fav_domain != _src_domain:
                _p(f"  ⚠ 파비콘 도메인 불일치: {_fav_domain} ≠ {_src_domain} → 스킵")
                favicon_url = ''
        if favicon_url:
            try:
                _r = requests.get(favicon_url, headers=HEADERS, timeout=8)
                if _r.status_code == 200 and 'image' in _r.headers.get('content-type', ''):
                    _fav_bytes = _r.content
                    # ico 파일 → PNG 변환 (PPTX/브라우저 호환성 개선)
                    if favicon_url.lower().endswith('.ico') or b'\x00\x00\x01\x00' == _fav_bytes[:4]:
                        try:
                            from PIL import Image as _PILImg
                            import io as _io
                            _ico_img = _PILImg.open(_io.BytesIO(_fav_bytes))
                            # 가장 큰 크기 선택 (ico에 여러 크기 포함 가능)
                            _sizes = getattr(_ico_img, 'ico', None)
                            if _sizes:
                                _best = max(_sizes.sizes(), key=lambda s: s[0])
                                _ico_img = _sizes.getimage(_best)
                            _buf = _io.BytesIO()
                            _ico_img.convert('RGBA').save(_buf, format='PNG')
                            _fav_bytes = _buf.getvalue()
                            favicon_mime = 'png'
                        except Exception as e:
                            logger.debug(f"favicon ICO→PNG 변환 실패, 원본 사용: {e}")
                    favicon_b64 = base64.b64encode(_fav_bytes).decode('utf-8')
                    if not favicon_mime or favicon_mime == 'png':
                        favicon_mime = _b64_mime(favicon_b64) if favicon_b64 else 'png'
                    _p(f"  → 파비콘 완료: {favicon_url} ({len(favicon_b64)//1024}KB)")
            except Exception as _e:
                logger.warning(f"파비콘 다운로드 실패 ({favicon_url}): {_e}")
                _p(f"  → 파비콘 실패: {_e}")
        else:
            _p("  → 파비콘 URL 없음, 건너뜀")
        assets['favicon_b64'] = favicon_b64
        assets['favicon_mime'] = favicon_mime
        # 파비콘 dominant color 추출 (primaryColor 교차검증용)
        _favicon_dominant = ''
        if favicon_b64 and favicon_mime != 'svg+xml':
            try:
                _fav_bytes_for_color = base64.b64decode(favicon_b64)
                _favicon_dominant = extract_dominant_color(_fav_bytes_for_color)
                if _favicon_dominant:
                    _p(f"  → 파비콘 dominant color: {_favicon_dominant}")
            except Exception as e:
                logger.debug(f"파비콘 dominant color 추출 실패: {e}")
        assets['favicon_dominant'] = _favicon_dominant
        _p("")

        _p("[2c단계] 홈페이지 실제 이미지 수집 중...")
        _is_artist_page = bool((page_subject or {}).get('subject_name'))
        site_img_urls = extract_website_images(url, _progress_fn=_p, _artist_mode=_is_artist_page)
        if _is_artist_page:
            _p(f"  → 아티스트 모드 활성화 (thumb/avatar 허용, 갤러리 링크 추가 스캔)")
        _p(f"  → extract URL: {len(site_img_urls)}개")
        site_img_pool_meta = []
        for img_url, alt, ctx in site_img_urls:
            b64, mime, w, h = download_image_b64(img_url)
            if b64:
                # mime 정규화 (image/jpeg → jpeg)
                _pool_mime = (mime or 'jpeg').split('/')[-1].split(';')[0].strip()
                if _pool_mime not in ('jpeg', 'png', 'webp', 'gif'):
                    _pool_mime = 'jpeg'
                site_img_pool_meta.append({
                    "b64": b64,
                    "mime": _pool_mime,
                    "alt": alt,
                    "context": ctx,
                    "w": w,
                    "h": h,
                })
                if len(site_img_pool_meta) >= 20:
                    break
        # 파비콘/로고 이미지를 풀에 추가 (크기 무관 — 브랜드 아이콘 보장)
        _fav_b64 = assets.get('favicon_b64', '')
        _fav_mime = assets.get('favicon_mime', 'png')
        if _fav_b64 and _fav_mime != 'svg+xml':
            _fav_w, _fav_h = 64, 64
            if HAS_PIL:
                try:
                    _fi = _PILImage.open(io.BytesIO(base64.b64decode(_fav_b64)))
                    _fav_w, _fav_h = _fi.size
                except Exception as e:
                    logger.debug(f"파비콘 크기 감지 실패: {e}")
            site_img_pool_meta.append({
                'b64': _fav_b64, 'alt': 'favicon', 'context': 'brand icon',
                'w': _fav_w, 'h': _fav_h,
            })
        assets['site_img_pool_meta'] = site_img_pool_meta
        _p(f"  → 홈페이지 이미지 {len(site_img_pool_meta)}개 수집 완료 (파비콘 포함)\n")

        # ── 아티스트 전용 아이콘 탐색 (page_subject 감지 시) ──────────────
        _psi_name = (page_subject or {}).get('subject_name', '')
        _psi_b64 = _psi_mime_val = None
        if _psi_name and site_img_pool_meta:
            _psi_kw = _psi_name.lower().replace(' ', '')
            for _pe in site_img_pool_meta:
                _ctx = _pe.get('context', '').lower()
                _alt = _pe.get('alt', '').lower()
                _pw, _ph = _pe.get('w', 0), _pe.get('h', 0)
                _pasp = _pw / max(_ph, 1) if _ph else 1.0
                if (_psi_kw in _ctx or _psi_kw in _alt
                        or any(kw in _ctx for kw in ['logo', 'icon', 'emblem', 'badge'])
                        or (0.8 <= _pasp <= 1.25 and 0 < _pw <= 300 and _pe.get('b64'))):
                    _psi_b64 = _pe['b64']
                    _psi_mime_val = _pe.get('mime', 'png')
                    _p(f"  → page_subject_icon 감지: alt='{_pe.get('alt','')}' ctx='{_pe.get('context','')}'")
                    break
        assets['page_subject_icon_b64'] = _psi_b64 or ''
        assets['page_subject_icon_mime'] = _psi_mime_val or 'png'

        # ── [3단계-A] 리서처 에이전트: 팩트 추출 ──────────────
        # Researcher 전에 URL/회사명으로 사전 감지 → C-type이면 전용 템플릿 적용
        _pre_narrative = narrative_type if narrative_type and narrative_type != 'auto' else None
        if not _pre_narrative:
            _pre_narrative = _detect_auto_narrative('', company_name, url=url)
        _p("[3단계-A] 리서처 에이전트: 팩트북 추출 중...")
        factbook = agent_researcher(raw_info, _p, page_subject=page_subject,
                                    forced_narrative=_pre_narrative)
        # 비용 최적화: factbook 4000자 제한 (Gemini 입력 토큰 30~40% 절감)
        if len(factbook) > 4000:
            factbook = factbook[:4000] + '\n...(이하 생략)'
            _p(f"  → factbook 길이 제한 적용: {len(factbook)}자")
        _p(f"\n{'='*55}")
        _p(factbook[:1000] + ("..." if len(factbook) > 1000 else ""))
        _p('='*55 + "\n")

        # ── [3단계-B] 전략 기획자 에이전트: 목차 기획 ──────────
        _p("[3단계-B] 전략 기획자 에이전트: 목차 기획 중...")
        # 사용자 지정 > Python 사전 감지 > Gemini 자동 결정
        _forced = narrative_type if narrative_type and narrative_type != 'auto' else None
        if not _forced:
            _forced = _detect_auto_narrative(factbook, company_name, url=url)
            if _forced:
                _p(f"  [사전 감지] 업종 키워드 → 내러티브 타입 {_forced} 자동 적용")
        narrative_type_str, storyline = agent_strategist(
            factbook, company_name, _p,
            forced_narrative=_forced,
            purpose=purpose
        )
        _p(f"  내러티브 타입: {narrative_type_str}")
        for item in storyline:
            _p(f"  슬라이드 {item.get('slide_num', '?'):>2} | {item.get('type',''):<28} | {item.get('topic','')}")
        _p("")

        # ── [3단계-C] 카피라이터+포맷터: JSON 생성 ─────────────
        _p("[3단계-C] 카피라이터: 슬라이드 카피 작성 중...")
        slide_json = generate_slide_json(factbook, storyline, narrative_type_str, assets, company_name, mood=mood, page_subject=page_subject, slide_lang=slide_lang)
        if not slide_json:
            raise RuntimeError("Gemini JSON 생성 실패. 파이프라인을 종료합니다.")

        # [물리적 텍스트 정제] 마크다운 제거, 띄어쓰기 강제, 서술형 마침표 제거
        _strip_md = lambda t: t.replace('**', '').replace('*', '') if t else t
        for slide in slide_json.get('slides', []):
            if slide.get('headline'):
                hl_clean = _strip_md(slide['headline'])
                # CTA 슬라이드: 한국어 작은따옴표로 감싼 세션명 제거 (e.g. '그로스 진단 세션' → 그로스 진단 세션)
                if slide.get('type') == 'cta_session':
                    hl_clean = re.sub(r"'([^']+)'", r'\1', hl_clean)
                slide['headline'] = hl_clean
            if slide.get('subheadline'):
                slide['subheadline'] = _strip_md(slide['subheadline'])
            cleaned_body = []
            # 범용 노이즈 필터: 웹사이트 네비/위젯 잔류 텍스트 제거
            _noise_re = re.compile(
                r'^(웹와치|webwatch|바로가기|더보기|클릭하세요|자세히보기|'
                r'로그인|회원가입|검색|메뉴|홈|home|login|sign.?up|'
                r'개인정보|이용약관|쿠키|cookie|팝업|레이어|닫기|close|'
                r'copyright|all rights|©)$',
                re.IGNORECASE
            )
            for b in slide.get('body', []):
                b_clean = _strip_md(b)
                b_clean = re.sub(r'^(\d+)\.(?=[^\s])', r'\1. ', b_clean)
                if b_clean.endswith('다.') or b_clean.endswith('요.'):
                    b_clean = b_clean[:-1]
                # 3글자 미만 무의미 텍스트
                if len(b_clean.strip()) < 3:
                    continue
                # 네비/위젯 잔류 텍스트 (단독 단어)
                if _noise_re.match(b_clean.strip()):
                    continue
                # 네비 텍스트가 본문에 섞인 경우 (5글자 이하 + 의미 없음)
                if len(b_clean.strip()) <= 5 and not re.search(r'[\d%:→·]', b_clean):
                    continue
                cleaned_body.append(b_clean)
            slide['body'] = cleaned_body
        _p("  → [정제] 마크다운/서술형 제거 완료")

        # ── image_en_hint 금지어 필터 ──
        _FORBIDDEN_HINTS = {'handshake', 'puzzle', 'gears', 'compass', 'dart', 'target',
                            'synergy', 'process', 'system', 'flowchart', 'diagram', 'chart', 'strategy'}
        for slide in slide_json.get('slides', []):
            hint = (slide.get('image_en_hint') or '').lower()
            if any(fw in hint for fw in _FORBIDDEN_HINTS):
                slide['image_en_hint'] = 'abstract minimal geometric composition modern studio'
                _p(f"  → [힌트 정제] {slide.get('type','')}: 금지어 감지 → 기본 힌트로 교체")

        # ── body 부족 슬라이드 Gemini 2차 보충 ──
        _keep_types = {'cover', 'cta_session', 'cta', 'contact', 'cta_contact', 'section_intro'}
        _thin_slides = []
        for si, sl in enumerate(slide_json.get('slides', [])):
            if sl.get('type', '') in _keep_types:
                continue
            meaningful = [b for b in sl.get('body', []) if len(b.strip()) >= 10]
            if len(meaningful) < 2:
                _thin_slides.append((si, sl))
        if _thin_slides:
            _p(f"  → body 부족 슬라이드 {len(_thin_slides)}개 감지 → Gemini 보충 중...")
            _patch_items = []
            for si, sl in _thin_slides:
                _patch_items.append({
                    "index": si,
                    "type": sl.get('type', ''),
                    "headline": sl.get('headline', ''),
                    "subheadline": sl.get('subheadline', ''),
                    "current_body": sl.get('body', [])
                })
            _patch_prompt = f"""아래 슬라이드들의 body가 부족합니다 (최소 2개 필요).
크롤링 데이터를 참고하여 각 슬라이드의 body를 2~4개로 보충해주세요.

규칙:
- 기존 body 항목은 유지하고, 부족한 만큼 추가
- 크롤링 데이터에 근거한 내용만 사용 (없으면 해당 업종 공통 서술)
- 각 bullet은 15자 이상, "짧은제목: 설명" 형식 권장
- 마크다운 금지, 문장형(~다/~요) 금지
- 회사명: {company_name}

보충 대상:
{json.dumps(_patch_items, ensure_ascii=False, indent=2)}

참고 데이터 (Factbook 요약):
{factbook[:3000] if factbook else '(없음)'}

출력: JSON 배열 — 각 항목 {{"index": 슬라이드인덱스, "body": ["보충된 전체 body 배열"]}}
기존 body를 포함한 완성된 body 배열을 반환하세요."""
            try:
                _patch_resp = _call_gemini_with_retry(
                    model="models/gemini-2.5-flash",
                    contents=_patch_prompt,
                    config={"temperature": 0.2, "max_output_tokens": 4000}
                )
                _patch_text = _patch_resp.text.strip()
                _patch_text = re.sub(r'```json\s*', '', _patch_text)
                _patch_text = re.sub(r'```', '', _patch_text)
                _start = _patch_text.find('[')
                _end = _patch_text.rfind(']')
                if _start != -1 and _end != -1:
                    _patches = json.loads(_patch_text[_start:_end+1])
                    _patched = 0
                    for p in _patches:
                        idx = p.get('index')
                        new_body = p.get('body', [])
                        if idx is not None and isinstance(new_body, list) and len(new_body) >= 2:
                            if 0 <= idx < len(slide_json['slides']):
                                slide_json['slides'][idx]['body'] = new_body
                                _patched += 1
                    if _patched:
                        _p(f"  → {_patched}개 슬라이드 body 보충 완료")
            except Exception as e:
                _p(f"  → body 보충 실패 (무시): {e}")

        # 빈/허전한 body 슬라이드 제거 (cover/cta/contact 제외)
        _keep_empty = {'cover', 'cta_session', 'cta', 'contact', 'cta_contact', 'section_intro'}
        _nt = slide_json.get('narrative_type', '') or slide_json.get('brand', {}).get('narrative_type', '')
        # C-type 핵심 슬라이드는 body 1개여도 보존 (2차 보충 후에도 부족하면 최소 유지)
        _c_core = {'brand_story', 'creative_approach', 'showcase_work_1', 'showcase_work_2'}
        def _has_meaningful_body(slide):
            """body에 10자 이상인 의미 있는 항목이 2개 이상 있는지 (1개는 허전)"""
            stype = slide.get('type', '')
            body = slide.get('body', [])
            meaningful = [b for b in body if len(b.strip()) >= 10]
            # key_metrics: 값이 0 또는 N/A만 있으면 의미 없음
            if stype == 'key_metrics':
                vals = [b for b in body if b and not all(c in '0N/A ·' for c in b.strip())]
                if not vals:
                    return False
            # C-type 핵심 슬라이드는 1개만 있어도 통과
            if _nt == 'C' and stype in _c_core:
                return len(meaningful) >= 1
            return len(meaningful) >= 2
        slides_before = len(slide_json.get('slides', []))
        slide_json['slides'] = [
            s for s in slide_json.get('slides', [])
            if s.get('type', '') in _keep_empty or _has_meaningful_body(s)
        ]
        _removed = slides_before - len(slide_json.get('slides', []))
        if _removed > 0:
            _p(f"  → 빈 슬라이드 {_removed}개 제거")

        # 로고 정보 주입
        slide_json['logoUrl'] = assets.get('logo_url', '')
        if 'brand' not in slide_json:
            slide_json['brand'] = {}
        slide_json['brand']['logoUrl']    = assets.get('logo_url', '')
        slide_json['brand']['logoB64']    = assets.get('logo_b64', '')
        slide_json['brand']['faviconB64'] = assets.get('favicon_b64', '')
        slide_json['brand']['faviconMime'] = assets.get('favicon_mime', 'png')
        slide_json['brand']['pageSubjectIconB64'] = assets.get('page_subject_icon_b64', '')
        slide_json['brand']['pageSubjectIconMime'] = assets.get('page_subject_icon_mime', 'png')
        fc = assets.get('footer_contact', {})
        # nameKo 검증: 회사명과 관련 없는 짧은 텍스트는 크롤링 노이즈
        _nameKo = fc.get('nameKo', '')
        _co_lower = (company_name or '').lower().replace('-', '').replace(' ', '')
        # 3글자 이하 + 회사명에 포함 안 되면 노이즈
        if _nameKo and len(_nameKo) <= 4 and _nameKo not in (company_name or ''):
            _nameKo = ''
        slide_json['brand']['nameKo']  = _nameKo
        slide_json['brand']['ceoName'] = fc.get('ceoName', '')
        if assets.get('logo_b64'):
            _p(f"  → 로고 b64 주입 완료 ({len(assets['logo_b64'])//1024}KB)")
        elif assets.get('logo_url'):
            _p(f"  → 로고 URL 주입: {assets['logo_url']}")

        _save_text_cache(slide_json, _text_cache)
        _p(f"  → 텍스트 캐시 저장: {_text_cache}")

    # ── 다중 소스 합의 기반 primaryColor 결정 ──────────────────────────────────
    # 소스 우선순위:
    #  0-A. CSS 빈도 최상위 (background/fill 가중치 3 — 버튼·섹션에서 가장 많이 쓰인 색)
    #  0-B. OG/히어로 이미지 픽셀 dominant (페이지 시각 분석)
    #  1. CSS named primary/accent 변수 (vibrancy >= 0.30)
    #  2. hero/header 배경색 + 로고 dominant가 일치 — 교차 검증
    #  3. 로고 dominant (vibrancy >= 0.20)
    #  4. SVG 로고 색
    #  5. hero_colors 중 최고 vibrancy
    #  6. CSS 최상위 vibrancy 색 — 폴백
    #  7. Gemini가 선택한 primaryColor — 최종 폴백

    def _color_close(c1: str, c2: str, threshold: int = 40) -> bool:
        """두 헥스 색이 RGB 거리 threshold 이내인지"""
        try:
            r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
            r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
            return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5 < threshold
        except Exception as e:
            logger.debug(f"색상 거리 계산 오류: {e}")
            return False

    _css_colors      = assets.get('colors', [])        # CSS에서 추출한 컬러 목록 (tier1 우선)
    _dom_color       = assets.get('dominant_color', '') # 로고 픽셀 dominant
    _hero_colors     = assets.get('hero_colors', [])    # 헤더/히어로 배경색
    _freq_colors     = assets.get('css_freq_colors', [])
    _freq_scores     = assets.get('css_freq_scores', {})
    _og_color        = assets.get('og_image_color', '')
    _el_accent       = assets.get('elementor_accent', '')
    _el_cross        = assets.get('elementor_cross_validated', [])  # CSS변수 + background 실사용 교차검증
    _logo_mime       = _b64_mime(assets.get('logo_b64','')) if assets.get('logo_b64') else ''
    _svg_colors      = _extract_svg_colors(assets.get('logo_b64','')) if _logo_mime == 'svg+xml' else []
    _logo_candidates = ([_dom_color] if _dom_color else []) + _svg_colors

    _p(f"  → 교차검증: {_el_cross} / accent변수: {_el_accent or '없음'} / css_freq상위3: {_freq_colors[:3]}")

    final_color = ''
    _reason = ''
    _explicit_primary = assets.get('explicit_primary', '')

    # -4. 사용자 수동 지정 (UI에서 brand_color 입력) — 최최최우선
    if brand_color and brand_color.startswith('#') and len(brand_color) == 7:
        final_color = brand_color.upper()
        _reason = f'사용자 수동 지정 ({brand_color})'
        _p(f"  → 사용자 지정 브랜드 컬러: {brand_color}")

    # -3. --color-primary / --primary-color CSS 변수 최최우선 (vibrancy 무관 — 브랜드 의도 존중)
    if not final_color and _explicit_primary:
        final_color = _explicit_primary
        _reason = f'CSS --color-primary 변수 ({_explicit_primary})'

    # -2. Elementor/CSS 글로벌 accent 변수 최우선 (--e-global-color-accent 등 명시적 브랜드 변수)
    if not final_color and _el_accent and _color_vibrancy(_el_accent) >= 0.20:
        final_color = _el_accent
        _reason = f'CSS 글로벌 accent 변수 ({_el_accent})'

    # -1. 교차검증: CSS 변수 정의 + 실제 배경 사용 모두 등장 (단, 6개 이하일 때만 신뢰 — 워드프레스 기본 팔레트 노이즈 방지)
    if not final_color and _el_cross and len(_el_cross) <= 6:
        best_cross = max(_el_cross, key=_color_vibrancy)
        if _color_vibrancy(best_cross) >= 0.25:
            final_color = best_cross
            _reason = f'CSS 변수 교차검증 (정의+사용, {best_cross})'

    # -0. 흰검 지배형 감지: 명시적 CSS 변수 없음 + 어두운/밝은 색이 vibrant보다 압도적
    # → primary = #111111, 첫 vibrant = accent (예: 디자인 에이전시, 모노크롬 브랜드)
    _dark_total   = assets.get('css_dark_total', 0)
    _light_total  = assets.get('css_light_total', 0)
    _max_vibrant  = max(_freq_scores.values()) if _freq_scores else 0
    _is_monochrome = (
        not final_color                    # 명시적 CSS 변수 / Elementor 없으면
        and not assets.get('dark_bg_color')  # 다크 테마 사이트 제외 (dark-on-dark 충돌 방지)
        and _dark_total > 8
        and _light_total > 8
        and _max_vibrant < 24  # vibrant 색이 배경으로 8회 미만 (포인트 정도만 사용)
    )
    _secondary_color = ''  # 기본값 — isMonochrome 또는 하단 로직에서 설정
    if _is_monochrome:
        _first_vibrant = next((c for c in _freq_colors if _color_vibrancy(c) >= 0.25), '')
        final_color = '#111111'
        _secondary_color = _first_vibrant
        _reason = f'흰검 지배형 → primary=#111, accent={_first_vibrant or "없음"}'

    # 0-A. CSS 사용 빈도 최상위 (버튼·배경·fill에서 가장 많이 쓰인 색 — 변수명 무관)
    if not final_color and _freq_colors and _color_vibrancy(_freq_colors[0]) >= 0.25:
        final_color = _freq_colors[0]
        _reason = f'CSS 빈도 최상위 ({final_color})'

    # 0-B. OG/히어로 이미지 픽셀 dominant
    if not final_color and _og_color and _color_vibrancy(_og_color) >= 0.22:
        final_color = _og_color
        _reason = f'OG/히어로 이미지 dominant ({_og_color})'

    # 1. CSS에 강한 primary/accent 명시 변수가 있으면 최우선
    _strong_css = [c for c in _css_colors if _color_vibrancy(c) >= 0.30]
    if not final_color and _strong_css:
        final_color = _strong_css[0]
        _reason = f'CSS primary (vibrancy={_color_vibrancy(final_color):.2f})'

    # 2. 로고 색과 hero 배경색이 비슷하면 → 교차 검증된 색 (로고 우선)
    if not final_color:
        for lc in _logo_candidates:
            for hc in _hero_colors:
                if _color_close(lc, hc, threshold=35):
                    final_color = lc
                    _reason = f'로고+히어로 교차검증 (logo={lc}, hero={hc})'
                    break
            if final_color:
                break

    # 3. 로고 dominant (vibrancy 충분)
    if not final_color and _dom_color and _color_vibrancy(_dom_color) >= 0.20:
        final_color = _dom_color
        _reason = f'로고 dominant (vibrancy={_color_vibrancy(_dom_color):.2f})'

    # 4. SVG 로고에서 추출한 색 (vibrancy 충분)
    if not final_color and _svg_colors:
        final_color = _svg_colors[0]
        _reason = f'SVG 로고 fill (vibrancy={_color_vibrancy(final_color):.2f})'

    # 5. hero 배경색
    if not final_color and _hero_colors:
        final_color = _hero_colors[0]
        _reason = f'히어로 배경색 (vibrancy={_color_vibrancy(final_color):.2f})'

    # 6. CSS 최상위 컬러 (폴백)
    if not final_color and _css_colors:
        final_color = _css_colors[0]
        _reason = f'CSS 최상위 ({final_color})'

    # Gemini 선택값(기존 primaryColor)은 마지막 폴백
    _gemini_color = (slide_json.get('brand', {}).get('primaryColor') or '').strip()
    if not final_color:
        final_color = _gemini_color or '#1A1A1A'
        _reason = f'Gemini 선택 / 기본값 ({final_color})'

    # ── 파비콘 교차검증: CSS/로고 결정 primaryColor vs 파비콘 dominant ──
    # 파비콘은 <link rel="icon">으로 명시 지정 → 가장 신뢰할 수 있는 브랜드 색상 소스
    _fav_dom = assets.get('favicon_dominant', '')
    if (
        _fav_dom
        and _color_vibrancy(_fav_dom) >= 0.25                 # 파비콘 색이 충분히 선명
    ):
        # 모노크롬 감지됐지만 파비콘에 선명한 색이 있으면 → 파비콘이 진짜 브랜드 컬러
        if _is_monochrome:
            _p(f"  ⚠ 모노크롬 사이트 + 파비콘 선명({_fav_dom}) → 파비콘을 primary로")
            final_color = _fav_dom
            _is_monochrome = False  # 모노크롬 해제 (브랜드 컬러 존재)
            _reason = f'파비콘 교차검증 override (모노크롬→{_fav_dom})'
        elif _color_vibrancy(final_color) < 0.15 and not _color_close(final_color, _fav_dom, threshold=80):
            # CSS 감지 색이 무채색에 가까울 때만 파비콘으로 교체
            # CSS에서 이미 선명한 색(빨강 등)을 잡았으면 파비콘(노랑 등)으로 덮어씌우지 않음
            _p(f"  ⚠ 파비콘 교차검증: primaryColor({final_color}) 무채색 + 파비콘({_fav_dom}) 선명 → 파비콘 우선")
            final_color = _fav_dom
            _reason = f'파비콘 교차검증 override ({_fav_dom})'
        elif not _color_close(final_color, _fav_dom, threshold=80):
            # 파비콘 색이 CSS 상위 5개 안에 있으면 → 파비콘이 진짜 브랜드 컬러일 가능성 높음
            _fav_in_top5 = any(_color_close(_fav_dom, c, threshold=50) for c in _freq_colors[:5])
            if _fav_in_top5:
                # 빈도 차이 체크: CSS 1위 대비 파비콘 매칭 색의 빈도가 50% 이상이면 교체
                _fav_match_score = max(
                    (_freq_scores.get(c, 0) for c in _freq_colors[:5] if _color_close(_fav_dom, c, threshold=50)),
                    default=0
                )
                _top_score = max(_freq_scores.values()) if _freq_scores else 1
                if _fav_match_score >= _top_score * 0.3:  # 30% 이상이면 의미 있는 사용
                    _p(f"  ⚠ 파비콘({_fav_dom})이 CSS 상위5에 존재 (score={_fav_match_score}/{_top_score}) → 파비콘 우선")
                    final_color = _fav_dom
                    _reason = f'파비콘+CSS 상위 교차검증 ({_fav_dom})'
                else:
                    _p(f"  → 파비콘 CSS 상위5 매칭이나 빈도 부족 ({_fav_match_score}/{_top_score}) → CSS 유지")
            else:
                _p(f"  → 파비콘({_fav_dom}) CSS 상위5에 없음 → CSS({final_color}) 유지")
        else:
            _p(f"  → 파비콘 교차검증: CSS({final_color})와 파비콘 유사 → 유지")

    # ── 스크린샷 교차검증: CSS 감지가 의심스러울 때 실제 렌더링 색상으로 보정 ──
    # 조건: 파비콘 교차검증이 작동하지 않았고, CSS 감지 결과가 WP 기본 팔레트일 가능성
    _wp_defaults = {'#F78DA7', '#CF2E2E', '#FF6900', '#FCB900', '#7BDCB5', '#00D084', '#8ED1FC', '#0693E3', '#ABB8C3'}
    if (
        final_color.upper() in _wp_defaults
        and not _is_monochrome
        and not brand_color  # 사용자 수동 지정이 없을 때만
    ):
        _p(f"  ⚠ CSS 감지 결과({final_color})가 WP 기본 팔레트 — 스크린샷 교차검증 시도")
        _ss_color = _playwright_screenshot_color(url)
        if _ss_color and _color_vibrancy(_ss_color) >= 0.20:
            _p(f"  → 스크린샷 dominant color: {_ss_color} → primary 교체")
            final_color = _ss_color
            _reason = f'스크린샷 교차검증 override ({_ss_color})'

    # 두 번째 vibrant 색상 (포인트 악센트 — C2)
    # primary와 다른 첫 번째 vibrant 색 — 블랙리스트 없음, 단순 vibrancy 기준만
    # 없으면 '' → 프론트에서 primary 25% 밝게 fallback
    if not _secondary_color:  # isMonochrome에서 이미 설정된 경우 유지
        _secondary_color = next(
            (c for c in _freq_colors[:8]
             if c.upper() != final_color.upper()
             and _color_vibrancy(c) >= 0.20),
            ''
        )
    _p(f"  → accentColor2 후보: { {c: _freq_scores.get(c,0) for c in _freq_colors[:5]} }")

    # 사이트 다크 테마 감지 — extract_brand_assets에서 수집한 body/html 배경 우선 사용
    _dark_bg_raw = assets.get('dark_bg_color', '')
    def _luma(hex_c):
        h = hex_c.lstrip('#')
        if len(h) != 6: return 1.0
        try: r,g,b = int(h[:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
        except: return 1.0
        return 0.2126*r + 0.7152*g + 0.0722*b
    # 폴백: _freq_colors 중 dark 후보 (기존 로직 유지)
    _site_dark_bg = _dark_bg_raw or next(
        (c for c in _freq_colors[:8]
         if _luma(c) < 0.10 and _color_vibrancy(c) < 0.25 and _freq_scores.get(c, 0) >= 8),
        '')

    # 다크 사이트 판별 + 역할 스왑
    # 조건: 다크 배경 감지 AND vibrant primary가 있음 → primary를 accent로, 다크를 primary로
    _is_dark_site = bool(
        _site_dark_bg
        and final_color
        and _color_vibrancy(final_color) >= 0.20
    )
    if _is_dark_site:
        _vibrant = final_color
        final_color = _site_dark_bg                                  # 다크 → primary
        _secondary_color = _secondary_color or _vibrant              # vibrant → accent
        if not _secondary_color or _secondary_color == final_color:
            _secondary_color = _vibrant
        _reason = f'다크 테마 — primary={final_color}, accent={_secondary_color}'

    _p(f"  → isMonochrome: {_is_monochrome} (dark={_dark_total}, light={_light_total}, maxVibrant={_max_vibrant})")
    _p(f"  → siteDarkBg: {_site_dark_bg or '없음'} / isDarkSite: {_is_dark_site}")

    if slide_json.get('brand'):
        slide_json['brand']['primaryColor'] = final_color
        # accentColor2: 항상 덮어씀 — '' 이면 프론트에서 hue-rotate -30° fallback 사용
        slide_json['brand']['accentColor2'] = _secondary_color
        # siteDarkBg: 커버 배경
        slide_json['brand']['siteDarkBg'] = _site_dark_bg
        slide_json['brand']['isDarkSite']   = _is_dark_site
        slide_json['brand']['isMonochrome'] = _is_monochrome
        # 사이트 밝은 배경색 (크림/파스텔 → 슬라이드 배경 반영)
        _site_light_bg = assets.get('site_light_bg', '')
        if _site_light_bg:
            slide_json['brand']['siteLightBg'] = _site_light_bg
            _p(f"  → 사이트 밝은 배경: {_site_light_bg}")
        slide_json['brand']['fontCategory']  = assets.get('font_category', 'sans')
        slide_json['brand']['detectedFonts'] = assets.get('detected_fonts', [])
        # 다음 캐시 실행 때 복원용으로 저장
        slide_json['brand']['css_dark_total']  = _dark_total
        slide_json['brand']['css_light_total'] = _light_total
        if _freq_colors:
            slide_json['brand']['css_freq_color']       = _freq_colors[0]
            slide_json['brand']['css_freq_colors_top5'] = _freq_colors[:5]
            slide_json['brand']['css_freq_scores_top5'] = {c: _freq_scores.get(c, 0) for c in _freq_colors[:5]}
        if _og_color:
            slide_json['brand']['og_image_color'] = _og_color
    _p(f"  → primaryColor 결정: {final_color} [{_reason}]")
    _p(f"  → accentColor2 (포인트): {_secondary_color or '없음'}")
    _p(f"  → fontCategory: {assets.get('font_category','sans')} / {assets.get('detected_fonts',[])[:3]}")

    # ── 필수 데이터 후처리 ──
    domain = urlparse(url).netloc.replace('www.', '')
    brand = slide_json.get('brand', {})
    for slide in slide_json.get('slides', []):
        if slide.get('type') == 'contact':
            body = slide.get('body', [])
            cleaned_body = []
            for b in body:
                b_clean = b.strip().lower()
                if (b_clean == domain.lower() or b_clean == f"https://{domain}"
                        or "partnership" in b_clean or "inquiry" in b_clean):
                    continue
                cleaned_body.append(b)
            slide['body'] = cleaned_body

            # footer_contact 강제 주입
            footer_contact = assets.get('footer_contact', {})
            if footer_contact:
                inject = []
                if footer_contact.get('address'):
                    inject.append(f"📍 {footer_contact['address']}")
                if footer_contact.get('phone'):
                    inject.append(f"☎ {footer_contact['phone']}")
                if footer_contact.get('email'):
                    inject.append(f"✉ {footer_contact['email']}")
                if footer_contact.get('kakao'):
                    inject.append(f"💬 카카오채널: {footer_contact['kakao']}")
                if footer_contact.get('linkedin'):
                    inject.append(f"🔗 {footer_contact['linkedin']}")
                for item in inject:
                    key = item[2:16].lower()
                    if not any(key in b.lower() for b in slide['body']):
                        slide['body'].insert(0, item)
            break

    slides = slide_json.get('slides', [])
    _p(f"  → 슬라이드 수: {len(slides)}\n")

    # ── 스토리라인 완전성 검증 — 누락 슬라이드 자동 복원 ─────────────────
    _p("[검증] 스토리라인 슬라이드 완전성 검사...")
    _actual_types = [s.get('type', '') for s in slides]
    # CTA/contact 계열은 이미 하나라도 있으면 복원 불필요
    _cta_types = {'cta_session', 'cta_contact', 'cta', 'contact'}
    _has_cta = bool(_cta_types & set(_actual_types))
    _missing_items = [
        (idx, item) for idx, item in enumerate(storyline)
        if item.get('type', '') not in _actual_types
        and not (_has_cta and item.get('type', '') in _cta_types)  # CTA 중복 복원 방지
    ]
    if _missing_items:
        _p(f"  ⚠ 누락 슬라이드 {len(_missing_items)}개 발견 — 원위치 복원")
        for _snum_0, _sitem in reversed(_missing_items):
            _stype = _sitem.get('type', '')
            _stopic = _sitem.get('topic', '')
            # 이 슬라이드보다 앞에 있어야 할 타입들을 역순으로 검색해 삽입 위치 결정
            _prev_types = [it.get('type', '') for it in storyline[:_snum_0]]
            _insert_after = -1
            for _pt in reversed(_prev_types):
                for _si, _s in enumerate(slides):
                    if _s.get('type', '') == _pt:
                        _insert_after = _si
                        break
                if _insert_after >= 0:
                    break
            _insert_idx = _insert_after + 1 if _insert_after >= 0 else 0
            _placeholder = {
                "type": _stype,
                "headline": _stopic,
                "subheadline": "",
                "sub": "",
                "eyebrow": "",
                "body": [],
                "bg_b64": "",
                "bg_mime": "png",
                "overlay_opacity": 0,
            }
            slides.insert(_insert_idx, _placeholder)
            _p(f"    복원: {_stype} @ index {_insert_idx} — '{_stopic}'")
    else:
        _p("  ✅ 모든 스토리라인 슬라이드 정상 포함")

    # ── [4단계] 배경 이미지 설정 (B그룹 company_image 슬라이드만) ──
    brand = slide_json.get('brand', {})
    accent_color = (brand.get('primaryColor') or '').strip() or '#1A1A1A'
    if not accent_color.startswith('#'):
        accent_color = '#' + accent_color
    brand_industry = brand.get('industry', '')
    site_img_pool_meta = assets.get('site_img_pool_meta', [])
    _p(f"[4단계] 이미지 배정 시작 — 수집 이미지 풀: {len(site_img_pool_meta)}개 / accent: {accent_color}")

    # ── 이미지 aspect ratio 계산 헬퍼 ──
    def _calc_aspect(b64_str):
        """base64 이미지 → width/height 비율 (실패 시 1.5 fallback)"""
        try:
            if HAS_PIL:
                from PIL import Image
                _bytes = base64.b64decode(b64_str)
                img = Image.open(io.BytesIO(_bytes))
                w, h = img.size
                if h > 0:
                    return round(w / h, 3)
        except Exception:
            pass
        return 1.5  # 가로형 기본값

    # ── B그룹(company_image) 슬라이드만 필터 ──
    image_slides = [
        (i, s) for i, s in enumerate(slides)
        if SLIDE_VISUAL_STRATEGY.get(s.get('type', ''), 'typography') == 'company_image'
    ]
    _p(f"  → B그룹 슬라이드: {len(image_slides)}개")

    if image_slides and site_img_pool_meta:
        _p(f"\n[이미지 매칭] B그룹 슬라이드 {len(image_slides)}개에 회사 이미지 배정 중...")
        # 1차: 시맨틱 매칭 (이미지 풀 3개 이상일 때)
        if len(site_img_pool_meta) >= 3:
            b_slides_only = [slides[i] for i, _ in image_slides]
            matched_mapping = match_images_semantically(b_slides_only, site_img_pool_meta)
            for local_idx, (slide_idx, slide) in enumerate(image_slides):
                pool_idx = matched_mapping.get(local_idx)
                if pool_idx is not None and pool_idx < len(site_img_pool_meta):
                    img = site_img_pool_meta[pool_idx]
                    slide['bg_b64'] = img['b64']
                    slide['bg_mime'] = img.get('mime', 'jpeg')
                    slide['bg_aspect'] = _calc_aspect(img['b64'])
                    _p(f"  [{slide_idx+1}] {slide.get('type','')} <- 이미지 #{pool_idx} (시맨틱 매칭, aspect={slide['bg_aspect']})")
        # 2차: 순서 배정 (시맨틱 매칭 못 받은 슬라이드)
        used_indices = set()
        for slide_idx, slide in image_slides:
            if slide.get('bg_b64'):
                continue
            for pi, img in enumerate(site_img_pool_meta):
                if pi not in used_indices:
                    slide['bg_b64'] = img['b64']
                    slide['bg_mime'] = img.get('mime', 'jpeg')
                    slide['bg_aspect'] = _calc_aspect(img['b64'])
                    used_indices.add(pi)
                    _p(f"  [{slide_idx+1}] {slide.get('type','')} <- 이미지 #{pi} (순서 배정, aspect={slide['bg_aspect']})")
                    break
    # 이미지 없는 B그룹 슬라이드 → 타이포그래피 폴백 (bg_b64 없음으로 표시)
    for slide_idx, slide in image_slides:
        if not slide.get('bg_b64'):
            _p(f"  [{slide_idx+1}] {slide.get('type','')} -> 이미지 없음, 타이포그래피 전환")

    # ── 각 슬라이드에 overlay_opacity + bg_mime 주입 (B그룹만 opacity 적용) ──
    for slide in slides:
        stype = slide.get('type', '')
        if stype in IMAGE_SLIDE_TYPES and slide.get('bg_b64'):
            slide['overlay_opacity'] = OVERLAY_OPACITY.get(stype, 0.60)
            if not slide.get('bg_mime'):
                slide['bg_mime'] = _b64_mime(slide['bg_b64'])

    # ── visual_style 주입: HTML 렌더러가 배경 모드를 분기하는 데 사용 ──
    for slide in slides:
        stype = slide.get('type', '')
        strategy = SLIDE_VISUAL_STRATEGY.get(stype, 'typography')
        if strategy == 'company_image' and slide.get('bg_b64'):
            slide['visual_style'] = {
                'mode': 'image',
                'overlay_opacity': slide.get('overlay_opacity', 0.65),
            }
        else:
            # A그룹 또는 이미지 없는 B그룹 → 타이포그래피 모드
            slide['visual_style'] = {
                'mode': 'typography',
                'bg_color': accent_color,
                'bg_color2': brand.get('accentColor2', ''),
                'bg_base': brand.get('bgColor', '#0F0F0F'),
                'bg_style': TYPOGRAPHY_BG_STYLE.get(stype, 'solid_dark'),
            }

    # 로고 MIME 주입
    logo_b64_val = brand.get('logoB64', '')
    if logo_b64_val:
        brand['logoMime'] = _b64_mime(logo_b64_val)

    # 최종 저장: 텍스트 캐시(~1MB) + 이미지 캐시(~11MB) 분리
    _save_text_cache(slide_json, _text_cache)
    _save_img_cache(slide_json, _img_cache)
    _p(f"  → 캐시 저장: {_text_cache} (텍스트) + {_img_cache} (이미지)")

    # TOC 슬라이드: 비활성화 (실제 슬라이드 수와 항목이 일치하지 않아 혼란 유발)

    # ── 슬라이드 품질 자동 채점 + 규칙 기반 보완 ────────────────────────
    _p("\n[품질 검사] 슬라이드 품질 채점 중...")
    _slide_scores = [_score_slide(s, slides[i-1] if i > 0 else None) for i, s in enumerate(slides)]
    _avg = sum(r['total'] for r in _slide_scores) / len(_slide_scores) if slides else 0
    for _i, (_s, _r) in enumerate(zip(slides, _slide_scores)):
        _p(f"  [{_i+1:>2}] {_s.get('type',''):<30} {_r['total']:>4.1f}점  {_r['breakdown']}")
    _p(f"  → 평균: {_avg:.1f} / 10.0")

    _LOW = 7.5
    # 평균 무관하게, 개별적으로 낮은 슬라이드 항상 보완 시도
    _low = [(i, slides[i], _slide_scores[i]) for i in range(len(slides))
            if _slide_scores[i]['total'] < _LOW]
    if _low:
        _p(f"  → 낮은 슬라이드 {len(_low)}개 보완 시도...")
        for _idx, _sl, _sc in _low:
            _improved = _improve_slide(_sl, _sc)
            if _improved:
                _new_sc = _score_slide(_improved, slides[_idx-1] if _idx > 0 else None)
                if _new_sc['total'] > _sc['total']:
                    slides[_idx] = _improved
                    # 어떤 항목이 개선됐는지 표시
                    _diff = {k: f"{_sc['breakdown'].get(k,'?')}→{_new_sc['breakdown'].get(k,'?')}"
                             for k in _new_sc['breakdown'] if _new_sc['breakdown'].get(k) != _sc['breakdown'].get(k)}
                    _p(f"    [{_idx+1}] {_sc['total']} → {_new_sc['total']} ✅  {_diff}")
                else:
                    _p(f"    [{_idx+1}] 개선 효과 없음 ({_sc['total']}) — 원본 유지")
            else:
                _p(f"    [{_idx+1}] 보완 규칙 없음 — 원본 유지")
        # 재채점
        _slide_scores = [_score_slide(s, slides[i-1] if i > 0 else None) for i, s in enumerate(slides)]
        _avg = sum(r['total'] for r in _slide_scores) / len(_slide_scores) if slides else 0
        _p(f"  → 보완 후 평균: {_avg:.1f} / 10.0")

    # 품질 점수 brand에 주입 (프론트엔드 표시용)
    slide_json['brand']['qualityScore'] = round(_avg, 1)
    slide_json['brand']['slideScores']  = [r['total'] for r in _slide_scores]

    narrative_type = brand.get('narrative_type', 'A')
    result = {
        "brand": brand,
        "slides": slides,
        "meta": {
            "accent_color": accent_color,
            "accent_color2": brand.get('accentColor2', ''),
            "narrative_type": narrative_type,
            "purpose": purpose,
            "company_name": company_name,
            "url": url,
        },
    }

    _p(f"\n[완료] 슬라이드 {len(slides)}개 생성 완료")
    return result
