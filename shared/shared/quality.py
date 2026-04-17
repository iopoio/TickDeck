"""슬라이드 품질 자동 검증 + 수정"""
import re

def validate_and_fix(slide_data: dict) -> dict:
    """SlideContent dict를 받아 품질 문제 자동 수정 후 반환"""
    if not slide_data or "slides" not in slide_data:
        return slide_data
        
    slides = slide_data.get("slides", [])
    for slide in slides:
        _fix_headline_length(slide)
        _fix_rule_j(slide)
        _fix_body_minimum(slide)
    return slide_data

def _fix_headline_length(slide: dict):
    """RULE A: 헤드라인 길이 제한 (22자)"""
    headline = slide.get("headline", "")
    if len(headline) > 22:
        # 마지막 단어 경계에서 자름
        cut = headline[:22]
        # 공백이나 콤마 기준으로 마지막 단어 경계 탐색
        last_space = max(cut.rfind(" "), cut.rfind(","))
        if last_space > 12:
            slide["headline"] = cut[:last_space].strip()
        else:
            slide["headline"] = cut.strip()

def _fix_rule_j(slide: dict):
    """RULE J: 헤드라인 숫자 ↔ body 개수 일치"""
    headline = slide.get("headline", "")
    body = slide.get("body", [])
    # '3가지', '5단계', '2개' 등의 패턴 매칭
    nums = re.findall(r'(\d+)\s*(?:가지|단계|개|가)', headline)
    if nums and len(body) >= 2:
        expected = int(nums[0])
        actual = len(body)
        if expected != actual:
            # 헤드라인의 숫자를 실제 body 개수로 교체
            slide["headline"] = headline.replace(nums[0], str(actual), 1)

def _fix_body_minimum(slide: dict):
    """RULE B: body 최소 2개 (cover/cta 제외)"""
    if slide.get("type") in ("cover", "cta", "contact"):
        return
        
    body = slide.get("body", [])
    if len(body) < 2:
        sub = slide.get("subheadline", "")
        # subheadline이 있고 body에 아직 없다면 추가
        if sub and sub not in body:
            slide["body"] = [sub] + body
        
        # 여전히 2개 미만이면 기본 문구 추가 (혹은 기존 내용 복제 방지)
        if len(slide.get("body", [])) < 2:
            # 리스트가 비어있지 않다면 첫번째 항목 보존, 아니면 빈 리스트 시작
            current_body = slide.get("body", [])
            if not current_body:
                slide["body"] = ["주요 내용을 확인하세요.", "상세 설명을 참조하세요."]
            else:
                slide["body"].append("상세 내용을 확인하세요.")
