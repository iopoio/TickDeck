"""Gemini API 클라이언트 — 3단계 에이전트 파이프라인 (Researcher → Strategist → Copywriter)"""
import json
import logging
import re
from google import genai
from google.genai import types

from shared.schemas import SlideContent, SlideItem, BrandInfo

logger = logging.getLogger(__name__)

_MODEL = "gemini-3.1-flash-lite-preview"

_DEFAULT_STORYLINE = [
    {"slide_num": 1, "type": "cover", "topic": "브랜드 소개"},
    {"slide_num": 2, "type": "problem", "topic": "시장 문제"},
    {"slide_num": 3, "type": "solution", "topic": "솔루션 소개"},
    {"slide_num": 4, "type": "how_it_works", "topic": "동작 방식"},
    {"slide_num": 5, "type": "proof", "topic": "실적 및 고객"},
    {"slide_num": 6, "type": "cta", "topic": "시작하기"},
]

_RESEARCHER_SYSTEM = """당신은 B2B 분석 전문가입니다.
원칙: 크롤링된 텍스트에 없는 내용은 절대 지어내지 않습니다.
데이터가 없으면 "정보 없음"이라고 명시합니다."""

_STRATEGIST_SYSTEM = """당신은 프레젠테이션 전략가입니다.
Factbook을 바탕으로 가장 설득력 있는 슬라이드 목차를 JSON으로 구성합니다.
코드블록 없이 순수 JSON만 출력합니다."""

_COPYWRITER_SYSTEM = """당신은 프레젠테이션 카피라이터입니다.

카피 원칙:
- headline: 20자 이내, 명사형, 임팩트 있게 (문장형 ~다/~요 금지)
- body: 각 항목 25자 이내, 3~5개 (마크다운 ** 금지)
- Factbook에 없는 내용은 절대 지어내지 않음
- key_metrics 타입 body 형식: "수치: 설명" (예: "500만+: 누적 사용자")
- language가 "en"이면 전체 영어로

출력: 코드블록 없이 순수 JSON"""


def _clean_surrogates(text: str) -> str:
    """Gemini 응답에 섞인 surrogate 문자 제거."""
    return text.encode('utf-8', errors='ignore').decode('utf-8')


def _extract_json(raw: str) -> dict:
    """텍스트에서 JSON 블록 추출 및 파싱."""
    raw = _clean_surrogates(raw)
    text = re.sub(r'```json\s*', '', raw.strip())
    text = re.sub(r'```', '', text)
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError(f"JSON 블록 없음: {text[:200]}")
    return json.loads(text[start:end + 1])


def _agent_researcher(client, crawled_text: str, url: str, language: str) -> str:
    """1단계: 크롤링 텍스트 → Factbook (팩트 추출)"""
    user_prompt = f"""URL: {url}
언어: {language}

=== 크롤링된 웹페이지 텍스트 ===
{crawled_text[:8000]}
===

아래 항목별로 텍스트에서 팩트만 추출해주세요:

## 1. 기업/브랜드 기본 정보
(이름, 업종, 설립/운영 규모 — 없으면 "정보 없음")

## 2. 핵심 제품/서비스
(구체적 기능, 특징, 차별점)

## 3. 고객 대상 및 문제 해결
(타겟, 해결하는 Pain Point)

## 4. 수치/성과
(매출, 고객 수, 수상, 파트너 등 — 없으면 "정보 없음")

## 5. 기타 인상적인 내용
(슬라이드에 쓸 만한 특이점)"""

    response = client.models.generate_content(
        model=_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_RESEARCHER_SYSTEM,
            temperature=0.1,
            max_output_tokens=3000,
        ),
    )
    result = _clean_surrogates(response.text)
    logger.info(f"Researcher 완료 ({len(result)}자)")
    return result


def _agent_strategist(client, factbook: str, url: str, language: str) -> list:
    """2단계: Factbook → 슬라이드 목차 (storyline). 실패 시 기본 목차 반환."""
    user_prompt = f"""URL: {url}
언어: {language}

=== Factbook ===
{factbook}
===

아래 슬라이드 타입 중 7~10개를 선택해 목차를 JSON으로 구성해주세요.
타입: cover / problem / solution / how_it_works / key_metrics / proof / why_us / cta

규칙:
- cover와 cta는 반드시 포함
- key_metrics는 Factbook에 수치가 2개 이상일 때만 포함
- 데이터가 없는 타입은 제외

출력 형식 (코드블록 없이 순수 JSON):
{{"slides": [{{"slide_num": 1, "type": "cover", "topic": "한 줄 설명"}}, ...]}}"""

    try:
        response = client.models.generate_content(
            model=_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=_STRATEGIST_SYSTEM,
                temperature=0.2,
                max_output_tokens=1500,
            ),
        )
        data = _extract_json(_clean_surrogates(response.text))
        storyline = data.get("slides", [])
        if len(storyline) >= 4:
            logger.info(f"Strategist 완료 ({len(storyline)}개 슬라이드)")
            return storyline
        logger.warning(f"Strategist 슬라이드 부족({len(storyline)}개) → 기본 목차 사용")
    except Exception as e:
        logger.warning(f"Strategist 실패: {e} → 기본 목차 사용")
    return _DEFAULT_STORYLINE


def _agent_copywriter(client, factbook: str, storyline: list, url: str, language: str) -> SlideContent:
    """3단계: Factbook + Storyline → 완성 슬라이드 JSON"""
    storyline_str = json.dumps(storyline, ensure_ascii=False)
    user_prompt = f"""URL: {url}
언어: {language}

=== Factbook ===
{factbook}

=== 슬라이드 목차 ===
{storyline_str}
===

위 목차대로 각 슬라이드의 headline, subheadline, eyebrow, body를 채워주세요.
중요: 각 슬라이드의 "type" 필드는 목차의 type 값을 반드시 그대로 사용하세요 (변경 금지).
브랜드 정보도 추출해주세요.

출력 JSON 스키마:
{{
  "brand": {{"companyName": "", "primaryColor": "#2563EB", "industry": ""}},
  "slides": [
    {{"type": "cover", "headline": "", "subheadline": "", "eyebrow": "", "body": []}},
    ...
  ],
  "language": "{language}"
}}"""

    response = client.models.generate_content(
        model=_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=_COPYWRITER_SYSTEM,
            temperature=0.3,
            max_output_tokens=4096,
        ),
    )
    raw = _clean_surrogates(response.text)
    logger.info(f"Copywriter 완료 ({len(raw)}자)")

    # 1차 파싱
    try:
        data = _extract_json(raw)
        return SlideContent.model_validate(data)
    except Exception as e:
        logger.warning(f"1차 파싱 실패: {e} — 재시도")

    # 2차 재시도
    retry_prompt = f"""아래 텍스트에서 JSON만 추출해서 반환해줘. 코드블록 없이 순수 JSON만:

{raw}"""
    retry_resp = client.models.generate_content(
        model=_MODEL,
        contents=retry_prompt,
        config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=4096),
    )
    data = _extract_json(_clean_surrogates(retry_resp.text))
    return SlideContent.model_validate(data)


def generate_slide_content(
    crawled_text: str,
    url: str,
    language: str = "ko",
    api_key: str = "",
) -> SlideContent:
    """크롤링 텍스트 → SlideContent. 3단계 에이전트 파이프라인.

    외부 인터페이스 유지 — worker/tasks/generate.py 호출부 변경 없음.
    """
    client = genai.Client(api_key=api_key)

    factbook = _agent_researcher(client, crawled_text, url, language)
    storyline = _agent_strategist(client, factbook, url, language)
    return _agent_copywriter(client, factbook, storyline, url, language)
