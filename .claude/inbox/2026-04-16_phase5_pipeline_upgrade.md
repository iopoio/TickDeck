# Phase 5: AI 파이프라인 업그레이드 스펙

작성: 클과장 (2026-04-16)
목적: WebToSlide에서 검증된 패턴을 TickDeck에 이식. 슬라이드 품질 대폭 개선.

---

## 배경

현재 TickDeck 파이프라인:
```
crawl(URL) → generate_slide_content(text) → DB 저장
```
Gemini 단일 호출 → 슬라이드 내용 얕음, 6~8개, 헤드라인 단조로움

목표 파이프라인:
```
crawl(URL) → researcher(text) → strategist(factbook) → copywriter(storyline) → quality_check → DB 저장
```

---

## 작업 파일 목록

| 파일 | 작업 | 난이도 |
|------|------|--------|
| `shared/shared/crawler.py` | Playwright 감지 개선 + 텍스트 정제 강화 | 낮음 |
| `shared/shared/gemini_client.py` | 3단계 에이전트 구조로 교체 | 높음 |
| `shared/shared/quality.py` | 신규 — 슬라이드 품질 검증 | 중간 |
| `worker/tasks/generate.py` | 새 파이프라인 호출로 업데이트 | 낮음 |

`shared/shared/schemas.py`는 클과장이 별도 처리.

---

## 상세 스펙

### 1. `crawler.py` 개선

현재: HTML 텍스트 < 500자일 때만 Playwright 시도

변경:
- Playwright 감지 기준 추가: `<noscript>` 태그 존재 시에도 트리거
- 텍스트 정제 강화:
  - 쿠키 동의, 저작권, SNS 공유 유도 문구 제거 패턴 추가
  - `re.sub(r'(쿠키|Cookie|저작권|Copyright|All Rights Reserved|개인정보|privacy policy).{0,100}', '', text, flags=re.IGNORECASE)`
  - 35자 이상 동일 구문 반복 제거 (nav 중복)
- 텍스트 한도: 8000자 → 12000자 (Gemini Researcher에 더 많은 원문 제공)
- `CrawlResult`에 `raw_html: str = ""` 필드 추가 (brand color 추출 미래 대비)

### 2. `gemini_client.py` — 3단계 에이전트

현재 `generate_slide_content()` 함수를 내부적으로 3단계로 분리. **외부 인터페이스(함수 시그니처)는 그대로 유지** — `worker/tasks/generate.py` 호출부 변경 최소화.

```python
def generate_slide_content(
    crawled_text: str,
    url: str,
    language: str = "ko",
    api_key: str = "",
) -> SlideContent:
    """외부 인터페이스 유지. 내부적으로 3단계 파이프라인 실행."""
    factbook = _agent_researcher(crawled_text, url, language, client)
    storyline = _agent_strategist(factbook, url, language, client)
    return _agent_copywriter(factbook, storyline, url, language, client)
```

#### 단계 1: `_agent_researcher()`

모델: `gemini-3.1-flash-lite-preview` (현재 사용 모델 유지)
temperature: 0.1
max_output_tokens: 3000

시스템 프롬프트:
```
당신은 B2B 분석 전문가입니다.
원칙: 크롤링된 텍스트에 없는 내용은 절대 지어내지 않습니다.
데이터가 없으면 "정보 없음"이라고 명시합니다.
```

유저 프롬프트:
```
URL: {url}
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
(슬라이드에 쓸 만한 특이점)
```

출력: Markdown 텍스트 (Factbook)

#### 단계 2: `_agent_strategist()`

모델: `gemini-3.1-flash-lite-preview`
temperature: 0.2
max_output_tokens: 1500

시스템 프롬프트:
```
당신은 프레젠테이션 전략가입니다.
Factbook을 바탕으로 가장 설득력 있는 슬라이드 목차를 구성합니다.
```

유저 프롬프트:
```
URL: {url}
언어: {language}

=== Factbook ===
{factbook}
===

아래 슬라이드 타입 중에서 7~10개를 선택해 목차를 JSON으로 구성해주세요.
타입: cover / problem / solution / how_it_works / key_metrics / proof / why_us / cta

규칙:
- cover와 cta는 반드시 포함
- key_metrics는 Factbook에 수치가 2개 이상일 때만 포함
- 데이터가 없는 타입은 제외

출력 형식 (코드블록 없이 순수 JSON):
{"slides": [{"slide_num": 1, "type": "cover", "topic": "한 줄 설명"}, ...]}
```

출력: JSON (슬라이드 목차)

#### 단계 3: `_agent_copywriter()`

모델: `gemini-3.1-flash-lite-preview`
temperature: 0.3
max_output_tokens: 4096

시스템 프롬프트 (현재 `_SYSTEM_PROMPT` 대체):
```
당신은 프레젠테이션 카피라이터입니다.

카피 원칙:
- headline: 20자 이내, 명사형, 임팩트 있게 (문장형 ~다/~요 금지)
- body: 각 항목 25자 이내, 3~5개 (마크다운 ** 금지)
- Factbook에 없는 내용은 절대 지어내지 않음
- key_metrics 타입: body 항목 형식 = "수치: 설명" (예: "500만+: 누적 사용자")
- language가 "en"이면 전체 영어로

출력: 코드블록 없이 순수 JSON
```

유저 프롬프트:
```
URL: {url}
언어: {language}

=== Factbook ===
{factbook}

=== 슬라이드 목차 ===
{storyline}
===

위 목차대로 각 슬라이드의 headline, subheadline, eyebrow, body를 채워주세요.

브랜드 정보도 추출해주세요 (primaryColor는 #2563EB 기본값 사용):

출력 JSON 스키마:
{
  "brand": {"companyName": "", "primaryColor": "#2563EB", "industry": ""},
  "slides": [
    {"type": "cover", "headline": "", "subheadline": "", "eyebrow": "", "body": []},
    ...
  ],
  "language": "ko"
}
```

#### 파싱 로직

`_agent_strategist()` 출력에서 JSON 파싱 실패 시 → 기본 목차 폴백:
```python
_DEFAULT_STORYLINE = [
    {"slide_num": 1, "type": "cover"},
    {"slide_num": 2, "type": "problem"},
    {"slide_num": 3, "type": "solution"},
    {"slide_num": 4, "type": "how_it_works"},
    {"slide_num": 5, "type": "proof"},
    {"slide_num": 6, "type": "cta"},
]
```

### 3. `quality.py` — 신규 파일

```python
"""슬라이드 품질 자동 검증 + 수정"""
import re

def validate_and_fix(slide_data: dict) -> dict:
    """SlideContent dict를 받아 품질 문제 자동 수정 후 반환"""
    slides = slide_data.get("slides", [])
    for slide in slides:
        _fix_headline_length(slide)
        _fix_rule_j(slide)
        _fix_body_minimum(slide)
    return slide_data
```

#### RULE A: 헤드라인 길이 제한
```python
def _fix_headline_length(slide: dict):
    headline = slide.get("headline", "")
    if len(headline) > 22:
        # 마지막 단어 경계에서 자름
        cut = headline[:22]
        last_space = max(cut.rfind(" "), cut.rfind(","))
        slide["headline"] = cut[:last_space] if last_space > 12 else cut
```

#### RULE J: 헤드라인 숫자 ↔ body 개수 일치
```python
def _fix_rule_j(slide: dict):
    headline = slide.get("headline", "")
    body = slide.get("body", [])
    nums = re.findall(r'(\d+)\s*(?:가지|단계|개|가)', headline)
    if nums and len(body) >= 2:
        expected = int(nums[0])
        actual = len(body)
        if expected != actual:
            slide["headline"] = headline.replace(nums[0], str(actual), 1)
```

#### RULE B: body 최소 2개 (cover/cta 제외)
```python
def _fix_body_minimum(slide: dict):
    if slide.get("type") in ("cover", "cta", "contact"):
        return
    body = slide.get("body", [])
    if len(body) < 2:
        sub = slide.get("subheadline", "")
        if sub and sub not in body:
            slide["body"] = [sub] + body
```

### 4. `worker/tasks/generate.py` 업데이트

변경 최소. `generate_slide_content()` 호출 후 quality check 추가:

```python
from shared.quality import validate_and_fix

# 기존:
slide_content = generate_slide_content(...)

# 변경:
slide_content = generate_slide_content(...)
slide_dict = slide_content.model_dump()
slide_dict = validate_and_fix(slide_dict)
slide_json_str = _json.dumps(_clean(slide_dict), ensure_ascii=False)
```

---

## Sprint Contract (Pass/Fail 기준)

### Pass 조건
- [ ] `generate_slide_content()` 외부 시그니처 변경 없음
- [ ] Gemini 3회 호출 후 `SlideContent` 객체 반환 성공
- [ ] 3단계 중 어느 단계 실패해도 폴백 동작 (전체 파이프라인 크래시 없음)
- [ ] `quality.py` import 후 `validate_and_fix({})` 에러 없음
- [ ] `worker/tasks/generate.py` 기존 흐름 (`_set_status` 순서) 그대로 유지
- [ ] surrogate 문자 처리 기존 `_clean()` 로직 건드리지 않음

### Fail 조건 (즉시 멈추고 보고)
- `SlideContent` 스키마 변경 → 클과장에게 먼저 확인
- 새 패키지 설치 필요 → 클과장에게 먼저 확인
- Celery 태스크 시그니처 변경
- `.env` 변수 추가 필요

---

## 검증 방법

구현 완료 후 다음 명령으로 E2E 테스트:

```bash
# 백엔드 실행 (TickDeck/ 루트에서)
backend/.venv/Scripts/uvicorn backend.main:app --reload --port 8000

# Celery (TickDeck/ 루트에서)
backend/.venv/Scripts/celery -A worker.celery_app worker --pool=solo --concurrency=1 --loglevel=info

# 테스트 요청
curl -X POST http://localhost:8000/api/slides/generate \
  -H "Authorization: Bearer DEV_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.example.com", "language": "ko"}'
```

로그에서 확인:
1. `[generation_id] 크롤링 완료` ✅
2. `[generation_id] Researcher 완료` ✅ (신규)
3. `[generation_id] Strategist 완료` ✅ (신규)
4. `[generation_id] Copywriter 완료` ✅ (신규)
5. DB status = `ready_to_edit` ✅

슬라이드 개수: 7개 이상, headline 길이: 22자 이하 확인.

---

## 핸드오프 메모

- `shared/shared/schemas.py`는 클과장이 별도 처리 (SlideItem에 type 확장, `narrative_type` 필드 추가)
- Gemini 모델: `gemini-3.1-flash-lite-preview` 고정. 다른 모델로 변경 금지
- Windows 환경: async 처리는 `worker/tasks/generate.py`에서 `asyncio.new_event_loop()` 방식 유지
- 로깅: `[{generation_id}] {단계명} 완료` 형식 유지
