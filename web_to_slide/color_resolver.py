"""
color_resolver.py — 브랜드 primaryColor + accentColor2 결정 로직
pipeline.py에서 추출한 260줄 — 로직 변경 없이 함수 분리만 수행
"""

from .config import logger
from .scraper import _playwright_screenshot_color


def _color_vibrancy(hex_color: str) -> float:
    """0~1 범위 색 선명도 (채도×명도 근사) — pipeline.py에서 공유"""
    try:
        h = hex_color.lstrip('#')
        r, g, b = int(h[:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
        mx, mn = max(r, g, b), min(r, g, b)
        if mx == 0:
            return 0.0
        s = (mx - mn) / mx
        return s * mx
    except Exception:
        return 0.0


def _b64_mime(b64_str: str) -> str:
    if b64_str.startswith('data:image/svg'):
        return 'svg+xml'
    if b64_str.startswith('data:image/png'):
        return 'png'
    return ''


def _extract_svg_colors(logo_b64: str) -> list:
    """SVG base64에서 fill/stroke 색상 추출"""
    import re, base64
    try:
        if not logo_b64 or 'svg' not in logo_b64[:50]:
            return []
        raw = logo_b64.split(',', 1)[-1] if ',' in logo_b64 else logo_b64
        svg_text = base64.b64decode(raw).decode('utf-8', errors='ignore')
        colors = re.findall(r'(?:fill|stroke)\s*[:=]\s*["\']?(#[0-9a-fA-F]{6})', svg_text)
        seen = set()
        unique = []
        for c in colors:
            cu = c.upper()
            if cu not in seen and cu not in ('#FFFFFF', '#000000', '#NONE'):
                seen.add(cu)
                unique.append(cu)
        return unique[:5]
    except Exception:
        return []


def determine_brand_colors(slide_json: dict, assets: dict, url: str, brand_color: str, _p):
    """
    다중 소스 합의 기반으로 primaryColor + accentColor2를 결정하고
    slide_json['brand']에 직접 기록합니다.

    소스 우선순위:
     0-A. CSS 빈도 최상위 (background/fill 가중치)
     0-B. OG/히어로 이미지 픽셀 dominant
     1. CSS named primary/accent 변수
     2. hero/header 배경색 + 로고 dominant 교차 검증
     3. 로고 dominant
     4. SVG 로고 색
     5. hero_colors 중 최고 vibrancy
     6. CSS 최상위 vibrancy — 폴백
     7. Gemini 선택 primaryColor — 최종 폴백
    """

    def _color_close(c1: str, c2: str, threshold: int = 40) -> bool:
        try:
            r1, g1, b1 = int(c1[1:3],16), int(c1[3:5],16), int(c1[5:7],16)
            r2, g2, b2 = int(c2[1:3],16), int(c2[3:5],16), int(c2[5:7],16)
            return ((r1-r2)**2 + (g1-g2)**2 + (b1-b2)**2) ** 0.5 < threshold
        except Exception:
            return False

    _css_colors      = assets.get('colors', [])
    _dom_color       = assets.get('dominant_color', '')
    _hero_colors     = assets.get('hero_colors', [])
    _freq_colors     = assets.get('css_freq_colors', [])
    _freq_scores     = assets.get('css_freq_scores', {})
    _og_color        = assets.get('og_image_color', '')
    _el_accent       = assets.get('elementor_accent', '')
    _el_cross        = assets.get('elementor_cross_validated', [])
    _logo_mime       = _b64_mime(assets.get('logo_b64','')) if assets.get('logo_b64') else ''
    _svg_colors      = _extract_svg_colors(assets.get('logo_b64','')) if _logo_mime == 'svg+xml' else []
    _logo_candidates = ([_dom_color] if _dom_color else []) + _svg_colors

    _p(f"  → 교차검증: {_el_cross} / accent변수: {_el_accent or '없음'} / css_freq상위3: {_freq_colors[:3]}")

    final_color = ''
    _reason = ''
    _explicit_primary = assets.get('explicit_primary', '')

    # -4. 사용자 수동 지정
    if brand_color and brand_color.startswith('#') and len(brand_color) == 7:
        final_color = brand_color.upper()
        _reason = f'사용자 수동 지정 ({brand_color})'
        _p(f"  → 사용자 지정 브랜드 컬러: {brand_color}")

    # -3. --color-primary CSS 변수
    if not final_color and _explicit_primary:
        final_color = _explicit_primary
        _reason = f'CSS --color-primary 변수 ({_explicit_primary})'

    # -2. Elementor/CSS 글로벌 accent 변수
    if not final_color and _el_accent and _color_vibrancy(_el_accent) >= 0.20:
        final_color = _el_accent
        _reason = f'CSS 글로벌 accent 변수 ({_el_accent})'

    # -1. CSS 변수 교차검증
    if not final_color and _el_cross and len(_el_cross) <= 6:
        best_cross = max(_el_cross, key=_color_vibrancy)
        if _color_vibrancy(best_cross) >= 0.25:
            final_color = best_cross
            _reason = f'CSS 변수 교차검증 (정의+사용, {best_cross})'

    # -0. 흰검 지배형 감지
    _dark_total   = assets.get('css_dark_total', 0)
    _light_total  = assets.get('css_light_total', 0)
    _max_vibrant  = max(_freq_scores.values()) if _freq_scores else 0
    _is_monochrome = (
        not final_color
        and not assets.get('dark_bg_color')
        and _dark_total > 8
        and _light_total > 8
        and _max_vibrant < 24
    )
    _secondary_color = ''
    if _is_monochrome:
        _first_vibrant = next((c for c in _freq_colors if _color_vibrancy(c) >= 0.25), '')
        final_color = '#111111'
        _secondary_color = _first_vibrant
        _reason = f'흰검 지배형 → primary=#111, accent={_first_vibrant or "없음"}'

    # 0-A. CSS 사용 빈도 최상위
    if not final_color and _freq_colors and _color_vibrancy(_freq_colors[0]) >= 0.25:
        final_color = _freq_colors[0]
        _reason = f'CSS 빈도 최상위 ({final_color})'

    # 0-B. OG/히어로 이미지 dominant
    if not final_color and _og_color and _color_vibrancy(_og_color) >= 0.22:
        final_color = _og_color
        _reason = f'OG/히어로 이미지 dominant ({_og_color})'

    # 1. CSS 강한 primary/accent 변수
    _strong_css = [c for c in _css_colors if _color_vibrancy(c) >= 0.30]
    if not final_color and _strong_css:
        final_color = _strong_css[0]
        _reason = f'CSS primary (vibrancy={_color_vibrancy(final_color):.2f})'

    # 2. 로고+히어로 교차검증
    if not final_color:
        for lc in _logo_candidates:
            for hc in _hero_colors:
                if _color_close(lc, hc, threshold=35):
                    final_color = lc
                    _reason = f'로고+히어로 교차검증 (logo={lc}, hero={hc})'
                    break
            if final_color:
                break

    # 3. 로고 dominant
    if not final_color and _dom_color and _color_vibrancy(_dom_color) >= 0.20:
        final_color = _dom_color
        _reason = f'로고 dominant (vibrancy={_color_vibrancy(_dom_color):.2f})'

    # 4. SVG 로고 fill
    if not final_color and _svg_colors:
        final_color = _svg_colors[0]
        _reason = f'SVG 로고 fill (vibrancy={_color_vibrancy(final_color):.2f})'

    # 5. hero 배경색
    if not final_color and _hero_colors:
        final_color = _hero_colors[0]
        _reason = f'히어로 배경색 (vibrancy={_color_vibrancy(final_color):.2f})'

    # 6. CSS 최상위 (폴백)
    if not final_color and _css_colors:
        final_color = _css_colors[0]
        _reason = f'CSS 최상위 ({final_color})'

    # 7. Gemini 선택 / 기본값
    _gemini_color = (slide_json.get('brand', {}).get('primaryColor') or '').strip()
    if not final_color:
        final_color = _gemini_color or '#1A1A1A'
        _reason = f'Gemini 선택 / 기본값 ({final_color})'

    # ── 파비콘 교차검증 ──
    _fav_dom = assets.get('favicon_dominant', '')
    if _fav_dom and _color_vibrancy(_fav_dom) >= 0.25:
        if _is_monochrome:
            _p(f"  ⚠ 모노크롬 사이트 + 파비콘 선명({_fav_dom}) → 파비콘을 primary로")
            final_color = _fav_dom
            _is_monochrome = False
            _reason = f'파비콘 교차검증 override (모노크롬→{_fav_dom})'
        elif _color_vibrancy(final_color) < 0.15 and not _color_close(final_color, _fav_dom, threshold=80):
            _p(f"  ⚠ 파비콘 교차검증: primaryColor({final_color}) 무채색 + 파비콘({_fav_dom}) 선명 → 파비콘 우선")
            final_color = _fav_dom
            _reason = f'파비콘 교차검증 override ({_fav_dom})'
        elif not _color_close(final_color, _fav_dom, threshold=80):
            _fav_in_top5 = any(_color_close(_fav_dom, c, threshold=50) for c in _freq_colors[:5])
            if _fav_in_top5:
                _fav_match_score = max(
                    (_freq_scores.get(c, 0) for c in _freq_colors[:5] if _color_close(_fav_dom, c, threshold=50)),
                    default=0
                )
                _top_score = max(_freq_scores.values()) if _freq_scores else 1
                if _fav_match_score >= _top_score * 0.3:
                    _p(f"  ⚠ 파비콘({_fav_dom})이 CSS 상위5에 존재 (score={_fav_match_score}/{_top_score}) → 파비콘 우선")
                    final_color = _fav_dom
                    _reason = f'파비콘+CSS 상위 교차검증 ({_fav_dom})'
                else:
                    _p(f"  → 파비콘 CSS 상위5 매칭이나 빈도 부족 ({_fav_match_score}/{_top_score}) → CSS 유지")
            else:
                _p(f"  → 파비콘({_fav_dom}) CSS 상위5에 없음 → CSS({final_color}) 유지")
        else:
            _p(f"  → 파비콘 교차검증: CSS({final_color})와 파비콘 유사 → 유지")

    # ── 스크린샷 교차검증 (WP 기본 팔레트) ──
    _wp_defaults = {'#F78DA7', '#CF2E2E', '#FF6900', '#FCB900', '#7BDCB5', '#00D084', '#8ED1FC', '#0693E3', '#ABB8C3'}
    if (
        final_color.upper() in _wp_defaults
        and not _is_monochrome
        and not brand_color
    ):
        _p(f"  ⚠ CSS 감지 결과({final_color})가 WP 기본 팔레트 — 스크린샷 교차검증 시도")
        _ss_color = _playwright_screenshot_color(url)
        if _ss_color and _color_vibrancy(_ss_color) >= 0.20:
            _p(f"  → 스크린샷 dominant color: {_ss_color} → primary 교체")
            final_color = _ss_color
            _reason = f'스크린샷 교차검증 override ({_ss_color})'

    # ── accentColor2 (포인트) ──
    if not _secondary_color:
        _secondary_color = next(
            (c for c in _freq_colors[:8]
             if c.upper() != final_color.upper()
             and _color_vibrancy(c) >= 0.20),
            ''
        )
    _p(f"  → accentColor2 후보: { {c: _freq_scores.get(c,0) for c in _freq_colors[:5]} }")

    # ── 사이트 다크 테마 감지 ──
    _dark_bg_raw = assets.get('dark_bg_color', '')
    def _luma(hex_c):
        h = hex_c.lstrip('#')
        if len(h) != 6: return 1.0
        try: r,g,b = int(h[:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
        except: return 1.0
        return 0.2126*r + 0.7152*g + 0.0722*b

    _site_dark_bg = _dark_bg_raw or next(
        (c for c in _freq_colors[:8]
         if _luma(c) < 0.10 and _color_vibrancy(c) < 0.25 and _freq_scores.get(c, 0) >= 8),
        '')

    _is_dark_site = bool(
        _site_dark_bg
        and final_color
        and _color_vibrancy(final_color) >= 0.20
    )
    if _is_dark_site:
        _vibrant = final_color
        final_color = _site_dark_bg
        _secondary_color = _secondary_color or _vibrant
        if not _secondary_color or _secondary_color == final_color:
            _secondary_color = _vibrant
        _reason = f'다크 테마 — primary={final_color}, accent={_secondary_color}'

    _p(f"  → isMonochrome: {_is_monochrome} (dark={_dark_total}, light={_light_total}, maxVibrant={_max_vibrant})")
    _p(f"  → siteDarkBg: {_site_dark_bg or '없음'} / isDarkSite: {_is_dark_site}")

    # ── slide_json['brand']에 기록 ──
    if slide_json.get('brand'):
        slide_json['brand']['primaryColor'] = final_color
        slide_json['brand']['accentColor2'] = _secondary_color
        slide_json['brand']['siteDarkBg'] = _site_dark_bg
        slide_json['brand']['isDarkSite']   = _is_dark_site
        slide_json['brand']['isMonochrome'] = _is_monochrome
        _site_light_bg = assets.get('site_light_bg', '')
        if _site_light_bg:
            slide_json['brand']['siteLightBg'] = _site_light_bg
            _p(f"  → 사이트 밝은 배경: {_site_light_bg}")
        slide_json['brand']['fontCategory']  = assets.get('font_category', 'sans')
        slide_json['brand']['detectedFonts'] = assets.get('detected_fonts', [])
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
