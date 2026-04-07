import os
import sys

# 프로젝트 루트를 PYTHONPATH에 추가하여 모듈 임포트 가능하게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_to_slide.image_gen import generate_cover_background
from web_to_slide.pptx_builder import build_cover

def test_image_gen_flow():
    # 0. 테스트를 위해 환경 변수 임시 활성화
    os.environ["GEMINI_IMAGE_ENABLED"] = "true"
    
    print("1. Gemini 이미지 생성 테스트 시작...")
    # 더미 데이터
    brand = {
        "name": "Antigravity Lab",
        "primaryColor": "#FF5733"
    }
    headline = "The Future of Generative Presentation"
    sub = "Powered by Gemini 2.5 Flash Image & Antigravity"
    
    # 이미지 생성 호출 (최대 30초 대기 예상)
    img_bytes = generate_cover_background(
        brand_name=brand["name"],
        primary_hex=brand["primaryColor"],
        mood="professional"
    )
    
    if img_bytes:
        print(f"   → 이미지 생성 성공! ({len(img_bytes)} bytes)")
    else:
        print("   → 이미지 생성 실패 (HAS_GENAI=False이거나 API 오류/전환 OFF)")
        # 실패하더라도 build_cover 회귀 테스트를 위해 None으로 진행 가능

    print("2. PPTX 빌드 테스트 (build_cover)...")
    try:
        pptx_bytes = build_cover(
            brand=brand,
            headline=headline,
            sub=sub,
            background_image_bytes=img_bytes
        )
        
        output_file = "preview_cover_with_image.pptx"
        with open(output_file, "wb") as f:
            f.write(pptx_bytes)
        print(f"   → PPTX 저장 완료: {output_file}")
    except Exception as e:
        print(f"   ⚠ PPTX 빌드 중 오류 발생: {e}")

if __name__ == "__main__":
    test_image_gen_flow()
