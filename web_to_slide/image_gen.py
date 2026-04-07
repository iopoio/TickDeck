import os
import io
import time
import logging
from .config import _client, logger, genai

try:
    from PIL import Image, ImageChops
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _crop_to_16_9(image_bytes):
    """1024x1024 등 정사각형 이미지를 16:9로 가공.
    1단계: 검정 letterbox 패딩 제거 (있으면)
    2단계: 결과를 16:9 가운데 crop
    """
    if not HAS_PIL:
        return image_bytes
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # 1단계: letterbox 자동 제거 (검정 패딩 있으면)
        # threshold 검정: 픽셀 합이 30 미만이면 검정으로 간주
        bg = Image.new('RGB', img.size, (0, 0, 0))
        diff = ImageChops.difference(img, bg)
        bbox = diff.getbbox()
        if bbox:
            cropped_w = bbox[2] - bbox[0]
            cropped_h = bbox[3] - bbox[1]
            # 의미있는 crop만 적용 (90% 이상 살아있을 때)
            if cropped_w * cropped_h > img.size[0] * img.size[1] * 0.5:
                img = img.crop(bbox)

        # 2단계: 16:9로 가운데 crop
        w, h = img.size
        target = 16 / 9
        cur = w / h
        if cur > target:
            new_w = int(h * target)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        elif cur < target:
            new_h = int(w / target)
            top = (h - new_h) // 2
            img = img.crop((0, top, w, top + new_h))

        out = io.BytesIO()
        img.save(out, format='PNG', optimize=True)
        return out.getvalue()
    except Exception as e:
        logger.warning(f"[image_gen] crop 실패, 원본 사용: {e}")
        return image_bytes

# ── Gemini 재시도 래퍼 ────────────────────────────────────────────────────────

def _call_gemini_with_retry(model, contents, config, max_retries=2):
    """429/500/503 등 일시 오류 시 지수 백오프 재시도 (10s→20s→40s)"""
    if _client is None:
        return None
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
                logger.warning(f"Gemini API (Image) 일시 오류 (attempt {attempt + 1}/{max_retries}) → {wait}초 대기 후 재시도: {err_str[:80]}")
                time.sleep(wait)
            else:
                raise

# ── 이미지 생성 메인 함수 ───────────────────────────────────────────────────

def generate_cover_background(brand_name: str, primary_hex: str, mood: str = "professional") -> bytes | None:
    """Gemini 2.5 Flash Image를 사용하여 추상 배경 이미지 생성 (PNG bytes)"""
    if _client is None:
        logger.debug("Gemini 클라이언트(google-genai)가 설치되지 않아 배경 생성을 건너뜁니다.")
        return None
    
    # 0. 환경 변수 토글 체크 (기본 OFF)
    enabled = os.getenv("GEMINI_IMAGE_ENABLED", "false").lower() == "true"
    if not enabled:
        return None

    # 1. 프롬프트 구성 (full-bleed 강조)
    prompt = (
        f"Full-bleed wide cinematic abstract background, edge-to-edge composition, "
        f"no padding, no border, no letterbox, no frame, fills entire canvas. "
        f"Brand color {primary_hex}, {mood} mood, dark tone, gradient mesh waves, "
        f"wide horizontal landscape orientation for presentation cover slide."
    )

    try:
        # 2. API 호출
        # 모델: models/gemini-2.5-flash-image (Nano Banana)
        # 타임아웃: SDK 기본값 사용 (http_options 제거)
        resp = _call_gemini_with_retry(
            model="models/gemini-2.5-flash-image",
            contents=prompt,
            config={
                "temperature": 1.0,
            }
        )



        
        if not resp or not resp.candidates:
            return None
            
        # 3. 이미지 바이트 데이터 추출
        # Gemini 2.x 멀티모달 출력은 parts 내부의 inline_data 또는 blob에 포함됨
        raw_bytes = None
        for part in resp.candidates[0].content.parts:
            if part.inline_data:
                raw_bytes = part.inline_data.data
                break
            if hasattr(part, 'blob') and part.blob:
                raw_bytes = part.blob.data
                break

        if raw_bytes is None:
            return None

        # 4. 16:9 crop (Gemini는 1024x1024 정사각형 출력 → 가운데 16:9로 가공)
        return _crop_to_16_9(raw_bytes)
        
    except Exception as e:
        logger.error(f"[image_gen] 배경 이미지 생성 실패: {e}")
        return None
