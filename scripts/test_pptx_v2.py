import sys
import os
# 프로젝트 루트를 경로에 추가
sys.path.append(os.getcwd())

from web_to_slide.pptx_builder import build_cta, build_contact
from pptx import Presentation
import io

brand = {
    "name": "Antigravity AI",
    "primaryColor": "#3B82F6"
}
steps = [
    "서비스 분석 및 전략 수립",
    "데이터 기반 퍼포먼스 마케팅 실행",
    "최종 결과 대시보드 리포팅"
]
contact_info = {
    "email": "contact@antigravity.ai",
    "phone": "02-1234-5678",
    "address": "서울특별시 강남구 테헤란로 123",
    "website": "https://antigravity.ai"
}

# 1. CTA 생성
cta_bytes = build_cta(brand, "성장을 위한 다음 단계", "Antigravity와 함께 비즈니스 가치를 극대화하세요.", steps)
with open("test_cta.pptx", "wb") as f:
    f.write(cta_bytes)
print("test_cta.pptx 생성 완료")

# 2. Contact 생성
contact_bytes = build_contact(brand, "연락처", contact_info)
with open("test_contact.pptx", "wb") as f:
    f.write(contact_bytes)
print("test_contact.pptx 생성 완료")
