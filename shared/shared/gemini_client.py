"""Gemini API 클라이언트 — URL 크롤링 텍스트 → SlideContent JSON"""
import json
import logging
import re
from google import genai
from google.genai import types

from shared.schemas import SlideContent, SlideItem, BrandInfo

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """당신은 웹페이지 콘텐츠를 분석해서 프레젠테이션 슬라이드 JSON을 생성하는 전문가입니다.

규칙:
- 슬라이드는 6~10개 생성
- 슬라이드 타입: cover / section_intro / content / key_metrics / cta
- headline: 15자 이내, 임팩트 있게
- body: 각 항목 20자 이내, 3~4개
- 마크다운 기호(**/*) 금지
- 문장형(~다/~요) 금지, 명사형으로
- language가 "en"이면 영어로 작성

출력: 아래 JSON 스키마 그대로 (코드블록 없이 순수 JSON):
{
  "brand": {"companyName": "", "primaryColor": "#2563EB", "industry": ""},
  "slides": [
    {"type": "cover", "headline": "", "subheadline": "", "eyebrow": "", "body": []},
    ...
  ],
  "language": "ko"
}"""


def _parse_slide_content(raw: str) -> SlideContent:
    """Gemini 응답 텍스트에서 SlideContent 파싱. 실패 시 ValidationError 발생."""
    # 코드블록 제거
    text = re.sub(r'```json\s*', '', raw.strip())
    text = re.sub(r'```', '', text)
    # JSON 영역 추출
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f"JSON 블록 없음: {text[:200]}")
    data = json.loads(text[start:end + 1])
    return SlideContent.model_validate(data)


def generate_slide_content(
    crawled_text: str,
    url: str,
    language: str = "ko",
    api_key: str = "",
) -> SlideContent:
    """크롤링 텍스트 → SlideContent. 실패 시 exception 전파."""
    client = genai.Client(api_key=api_key)

    user_prompt = f"""URL: {url}
언어: {language}

=== 크롤링된 웹페이지 텍스트 ===
{crawled_text[:6000]}
===

위 내용을 분석해서 프레젠테이션 슬라이드 JSON을 생성해주세요."""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=4096,
        ),
    )

    raw = response.text
    logger.info(f"Gemini 응답 ({len(raw)}자)")

    # 1차 파싱
    try:
        return _parse_slide_content(raw)
    except Exception as e:
        logger.warning(f"1차 파싱 실패: {e} — 재시도")

    # 2차 재시도 (JSON만 뽑아달라고 재요청)
    retry_prompt = f"""아래 텍스트에서 JSON만 추출해서 그대로 반환해줘. 코드블록 없이 순수 JSON만:

{raw}"""
    retry_resp = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=retry_prompt,
        config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=4096),
    )
    return _parse_slide_content(retry_resp.text)
