# 신야 실행 지시서 — GLM-5.2 자율 HTML 덱 (디자인 능력 테스트)

> 목적: **우리 파이프라인(deck_author / axis1_to_deck / deck_harness) 전부 우회.**
> GLM-5.2가 **리서치 + 서사 + 디자인까지 자율로** "2026 마케팅 트렌드" 발표 덱을 **HTML/CSS**로 생성하게 한다.
> → GLM의 *디자인 능력*과 *할루시네이션 정도*를 실물로 평가한다.
> 비교 대상: 기존 Qwen 파이프라인 결과물 + (옵션) 앞선 GLM 파이프라인판.
> 범위: 비교 테스트 1회용. 기본 경로/품질 가드와 무관(이 런은 가드 없음).

OpenRouter 슬러그: **`z-ai/glm-5.2`**  ·  실행 위치: **신야 sandbox 안** (중국모델 격리)

---

## 입력

- **주제:** `2026 마케팅 트렌드`
- **청중:** 일반 직장인 (마케터 아님 — 실무에 "그래서 뭘 해야 하나"가 와닿게)
- **분량:** 20~30장
- **자료:** GLM 자율. (옵션: 공정 비교를 원하면 기존 corpus
  `v3/axis1_research/runs/2026_마케팅_트렌드_*_corpus.json` 를 컨텍스트로 넣어 동일 사실 기반으로 통제)

## GLM에 줄 작가+디자인 지시 (프롬프트)

다음을 그대로 시스템/유저 프롬프트에 싣는다:

1. **역할:** 너는 발표 덱 작가이자 디자이너다. 주제를 리서치하고, 스토리를 짜고,
   **완성된 HTML 슬라이드 덱**을 직접 디자인해 출력한다.
2. **청중:** 일반 직장인. 전문용어는 풀어쓰고, 각 슬라이드에 실무 시사점("그래서 내 업무엔?")을 담아라.
3. **구성:** 20~30장. 표지 → 목차 → 본문(섹션별) → 결론 → 출처.
   한 장 한 메시지, 결론 먼저(BLUF). 지배 메시지 한 문장을 표지·결론에 반복.
4. **사실성:** 수치·인용은 출처를 슬라이드 하단에 명기. **추측이면 추측이라고 표시. 출처 없는 구체 수치 지어내기 금지.**
5. **디자인 자유:** 레이아웃·색·타이포·차트(인라인 SVG 또는 CSS)·아이콘 전부 네가 정한다.
   전문 컨설팅 덱 수준의 시각 완성도를 목표로.

## HTML 출력 규격 (렌더 호환)

- **16:9.** 슬라이드 1장 = `<section class="slide">` 하나. 슬라이드 크기 `1280×720`(또는 1920×1080) 고정.
- **자기완결(self-contained):** CSS는 `<style>`로 인라인. 이미지·아이콘은 인라인 SVG 권장(외부 의존 최소화).
  - 한글 폰트: Pretendard / Noto Sans KR 등 웹폰트 `<link>` 허용(렌더 시 네트워크 ON).
- 차트는 **인라인 SVG 또는 순수 CSS**로(JS 차트 라이브러리 비권장 — 정적 렌더라 동작 안 할 수 있음).
- 슬라이드 사이 `page-break-after: always;` (PDF 분할용).
- 파일: 단일 `deck.html` (또는 슬라이드별 파일도 가능).

## 렌더 (신야 안, GLM 아님 — 결정적 변환)

Chromium(Playwright)로 HTML → PDF / PNG:

```bash
# PDF (한 파일)
python -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto('file:///ABS/PATH/deck.html')
    pg.pdf(path='deck_glm_html.pdf', width='1280px', height='720px', print_background=True)
    b.close()
"
# 또는 슬라이드별 PNG: 각 .slide 를 screenshot
```

## 산출물 → 저장소로 가져오기

- `deck.html`  →  `TickDeck/v3/generated_glm_html/deck.html`
- `deck_glm_html.pdf` (+ PNG들)  →  같은 폴더
- 이게 들어오면 비교/리뷰는 인세션 클로드(나)가 진행.

---

## 금지 / 주의

- GLM/OpenRouter/Tavily 호출은 **신야 안에서만.** `TickDeck/v3/` 코드에서 직접 호출 금지.
- 이 런은 **품질 가드 없음**(자율 평가가 목적). 수치는 사람이 사후 검토 전제.

## 비교 매트릭스

| 런 | 리서치 | 작가 | 디자인 | 산출 |
|---|---|---|---|---|
| 기존 베이스라인 | Qwen | (파이프라인) | deck_harness 템플릿 | PDF |
| GLM 파이프라인 (옵션) | GLM | GLM(deck_author) | deck_harness 템플릿 | PDF |
| **GLM 자율 HTML (이 문서)** | **GLM** | **GLM** | **GLM 자율** | **HTML/PDF** |

→ 보는 관점: 디자인 완성도 · 서사 설득력 · 일반 직장인 눈높이 · 수치 사실성(지어냄 여부).
