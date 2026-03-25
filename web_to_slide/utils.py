"""
utils.py — 색상 유틸리티 + 이미지 디코딩 헬퍼
"""

import base64
import io
import re

from .config import HAS_PIL, logger

if HAS_PIL:
    from PIL import Image as _PILImage


# ── 색상 유틸리티 ─────────────────────────────────────────────────────────────

def _color_hue(hex_color):
    """0~360° 색상각(hue) 반환. 무채색=−1"""
    h = hex_color.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        return -1
    try:
        r, g, b = int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255
    except ValueError:
        return -1
    mx, mn = max(r, g, b), min(r, g, b)
    if mx == mn:
        return -1
    d = mx - mn
    if mx == r:
        hue = (g - b) / d % 6
    elif mx == g:
        hue = (b - r) / d + 2
    else:
        hue = (r - g) / d + 4
    return hue * 60


def _color_hue_diff(c1, c2):
    """두 색의 색상각 차이(0~180°). 무채색 포함 시 180 반환"""
    h1, h2 = _color_hue(c1), _color_hue(c2)
    if h1 < 0 or h2 < 0:
        return 180
    diff = abs(h1 - h2)
    return min(diff, 360 - diff)


def _color_vibrancy(hex_color):
    """채도·명도 기반 비비드 점수 반환 (0~1). 검정/흰색/회색 = 0"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    if len(hex_color) != 6:
        return 0
    try:
        r = int(hex_color[0:2], 16) / 255
        g = int(hex_color[2:4], 16) / 255
        b = int(hex_color[4:6], 16) / 255
    except ValueError:
        return 0
    max_c, min_c = max(r, g, b), min(r, g, b)
    l = (max_c + min_c) / 2
    if max_c == min_c:
        return 0  # 완전 회색
    d = max_c - min_c
    s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
    # 너무 어둡거나 너무 밝으면 배경색 취급
    if l < 0.15 or l > 0.85:
        return 0
    return s


def extract_dominant_color(img_bytes: bytes) -> str:
    """PIL로 이미지에서 가장 선명한 브랜드 컬러(비중립색) 추출 → '#RRGGBB' or ''
    - 16색 양자화로 세밀하게 분리 + vibrancy 0.20 이상만 허용
    - 흰/검 배경 픽셀을 먼저 제거 후 양자화 (배경색 오염 방지)
    """
    if not HAS_PIL or not img_bytes:
        return ''
    try:
        img = _PILImage.open(io.BytesIO(img_bytes)).convert('RGBA').resize((120, 120))
        # 투명 픽셀·흰 배경·검 배경을 제거한 픽셀만 남긴 RGB 이미지 생성
        pixels_rgb = []
        for r, g, b, a in img.getdata():
            if a < 100:
                continue  # 투명 픽셀 제외
            brightness = (r * 299 + g * 587 + b * 114) // 1000
            if brightness > 240 or brightness < 15:
                continue  # 흰/검 배경 제외
            pixels_rgb.append((r, g, b))
        if len(pixels_rgb) < 50:  # 유효 픽셀 부족 → 원본 전체 사용
            img_rgb = img.convert('RGB')
        else:
            img_rgb = _PILImage.new('RGB', (len(pixels_rgb), 1))
            img_rgb.putdata(pixels_rgb)

        quantized = img_rgb.quantize(colors=16, method=2)
        palette = quantized.getpalette()[:16 * 3]
        counts = [0] * 16
        for p in quantized.getdata():
            counts[p] += 1
        # vibrancy 기준으로 가장 선명한 색 선택 (빈도 상위 8개 중)
        top = sorted(enumerate(counts), key=lambda x: -x[1])[:8]
        candidates = []
        for idx, cnt in top:
            r, g, b = palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]
            hex_c = f'#{r:02x}{g:02x}{b:02x}'.upper()
            v = _color_vibrancy(hex_c)
            if v >= 0.20:
                candidates.append((hex_c, v, cnt))
        if candidates:
            # vibrancy와 빈도를 함께 고려해 최적 색 선택
            max_cnt = max(c[2] for c in candidates)
            return max(candidates, key=lambda x: x[1] * 0.7 + (x[2] / max_cnt) * 0.3)[0]
    except Exception as e:
        logger.debug(f"도미넌트 컬러 추출 실패: {e}")
    return ''


def _extract_svg_colors(svg_b64: str) -> list:
    """SVG base64에서 fill/stroke/stop-color 색 추출 → vibrancy 높은 순 리스트"""
    try:
        svg_text = base64.b64decode(svg_b64).decode('utf-8', errors='ignore')
        found = re.findall(
            r'(?:fill|stroke|stop-color)\s*[=:]\s*["\']?\s*(#[0-9a-fA-F]{3,6})\b',
            svg_text, re.I
        )
        # 3자리 헥스 → 6자리 변환
        expanded = []
        for c in found:
            c = c.lstrip('#')
            if len(c) == 3:
                c = ''.join(ch * 2 for ch in c)
            if len(c) == 6:
                expanded.append('#' + c.upper())
        # 중복 제거 + vibrancy 필터 + 정렬
        seen = set()
        result = []
        for c in expanded:
            if c not in seen and _color_vibrancy(c) >= 0.15:
                seen.add(c)
                result.append(c)
        return sorted(result, key=_color_vibrancy, reverse=True)
    except Exception as e:
        logger.debug(f"SVG 색 추출 실패: {e}")
        return []


# ── MIME / base64 헬퍼 ────────────────────────────────────────────────────────

def _b64_mime(b64: str) -> str:
    """base64 문자열에서 MIME 타입 감지 (png/jpeg/webp/svg+xml)"""
    if not b64:
        return 'png'
    try:
        head = base64.b64decode(b64[:80] + '==')[:40].decode('utf-8', errors='ignore')
        if '<svg' in head or '<?xml' in head:
            return 'svg+xml'
    except Exception as e:
        logger.debug(f"MIME 헤더 디코딩 실패: {e}")
    if b64.startswith('/9j/'):
        return 'jpeg'
    if b64.startswith('UklGR'):
        return 'webp'
    return 'png'
