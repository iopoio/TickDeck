"""TickDeck 공유 Pydantic 스키마"""
from typing import Any
from pydantic import BaseModel, Field


class SlideItem(BaseModel):
    type: str
    headline: str = ""
    subheadline: str = ""
    eyebrow: str = ""
    body: list[str] = Field(default_factory=list)


class BrandInfo(BaseModel):
    companyName: str = ""
    primaryColor: str = "#1A1A1A"
    industry: str = ""


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
