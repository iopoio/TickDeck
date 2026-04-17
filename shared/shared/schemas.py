"""TickDeck 공유 Pydantic 스키마"""
from typing import Any, Literal
from pydantic import BaseModel, Field

SlideType = Literal[
    "cover", "problem", "solution", "how_it_works",
    "key_metrics", "proof", "why_us", "cta",
    # 레거시 타입 (하위호환)
    "section_intro", "content",
]


class SlideItem(BaseModel):
    type: str  # SlideType — 유연하게 str 유지 (Gemini 출력 다양)
    headline: str = ""
    subheadline: str = ""
    eyebrow: str = ""
    body: list[str] = Field(default_factory=list)


class BrandInfo(BaseModel):
    companyName: str = ""
    primaryColor: str = "#2563EB"
    industry: str = ""
    narrative_type: str = "A"  # A/B/C/D — 내러티브 타입


class SlideContent(BaseModel):
    """Gemini가 생성하는 슬라이드 전체 구조"""
    brand: BrandInfo = Field(default_factory=BrandInfo)
    slides: list[SlideItem] = Field(default_factory=list)
    language: str = "ko"


class GenerationRequest(BaseModel):
    url: str
    language: str = "ko"


class GenerationStatus(BaseModel):
    generation_id: str
    status: str  # pending / crawling / structuring / ready_to_edit / building_pptx / done / failed
    slide_content: SlideContent | None = None
    error_message: str | None = None
    pptx_url: str | None = None
    pdf_url: str | None = None
