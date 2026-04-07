"""
Phase 1+2 슬라이드 3종 미리보기 생성
- Cover / CTA / Contact 각각 .pptx로 저장
"""
import sys
import os
sys.path.append(os.getcwd())

from web_to_slide.pptx_builder import build_cover, build_cta, build_contact

brand = {
    "name": "TickDeck",
    "primaryColor": "#6366F1"  # Indigo
}

# 1. Cover
cover_bytes = build_cover(
    brand,
    headline="딸깍 한 번으로\n완성되는 제안서",
    sub="URL만 넣으면 AI가 회사를 분석하고 슬라이드를 만듭니다."
)
with open("preview_cover.pptx", "wb") as f:
    f.write(cover_bytes)
print("✓ preview_cover.pptx")

# 2. CTA
steps = [
    "URL 입력 후 생성 버튼 클릭",
    "AI가 브랜드 컬러/로고/핵심 메시지 자동 추출",
    "텍스트 편집 후 PPT/PDF 다운로드"
]
cta_bytes = build_cta(
    brand,
    headline="3단계로 끝나는 제안서",
    sub="복잡한 디자인 없이, 핵심만 빠르게.",
    steps=steps
)
with open("preview_cta.pptx", "wb") as f:
    f.write(cta_bytes)
print("✓ preview_cta.pptx")

# 3. Contact
contact_info = {
    "email": "hello@tickdeck.site",
    "phone": "010-0000-0000",
    "address": "Seoul, Korea",
    "website": "https://tickdeck.site"
}
contact_bytes = build_contact(brand, "Contact", contact_info)
with open("preview_contact.pptx", "wb") as f:
    f.write(contact_bytes)
print("✓ preview_contact.pptx")

print("\n3개 파일 생성 완료. 프로젝트 루트에 있습니다.")
