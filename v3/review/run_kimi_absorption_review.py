#!/usr/bin/env python3
"""Kimi PPT 가이드 흡수 검수 — Gemini가 '틱덱 DNA 대비 진짜 델타'를 검증.

후추님 지시: Kimi 조사를 Gemini로 검수 → 틱덱 흡수 항목 정리.
핵심: 빈 가이드가 아니라 틱덱 작가 엔진 DNA + 클차장 델타 가설까지 줘서
      '이미 있는 것 / 진짜 추가되는 것'을 구분하게 한다.
"""
import os
import sys
from pathlib import Path

# wrapper 경로
sys.path.insert(0, str(Path.home() / "Projects/Automation/Think/.claude/scripts"))

# TickDeck/.env 에서 GEMINI_API_KEY 로드
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "Projects/Automation/TickDeck/.env")
except Exception:
    pass

from gemini_call_wrapper import call  # noqa: E402

ROOT = Path.home() / "Projects/Automation/TickDeck/v3"
DNA = (ROOT / "DECK_STRUCTURE_LIBRARY.md").read_text(encoding="utf-8")
AUTHOR = (ROOT / "AUTHOR_STAGE_DESIGN.md").read_text(encoding="utf-8")
KIMI = (ROOT.parent / ".claude/research/kimi_ppt_guide.md").read_text(encoding="utf-8")

SYSTEM = """당신은 시니어 프레젠테이션 설계 리뷰어다. AI 슬라이드 자동생성 엔진을 평가한다.
원칙: 칭찬 금지. 이미 있는 것은 '중복'으로 가차없이 쳐낸다. 근거 없는 통계는 '미검증'으로 표시한다.
출력은 한국어. 개조식(~함/~임) 허용. 코드블록 없이 마크다운."""

PROMPT = f"""# 검수 과제

'틱덱'은 URL/리포트 → 설득용 PPT 덱을 자동 생성하는 작가 엔진이다.
이미 성숙한 작가 DNA(아래 [A])와 작가 단계 설계(아래 [B])를 갖췄다.
한 외부 조사([C], Kimi가 블로그들 종합)를 흡수하려 한다.

클차장(설계자)의 1차 진단: "[C]의 ~80%는 [A][B]에 이미 더 엄격히 구현됨.
진짜 추가되는 델타는 3개뿐:
  델타1 = [C]원칙5 '슬라이드별 반복생성(3배 레버)'. 틱덱 ③는 단일 LLM 호출로 전체 page_specs를
          한 번에 생성([B]§6) → 페이지별 집중 리파인 패스가 없음. 최대 레버.
  델타2 = Few-shot 골드예시 1~3개. 틱덱 ②③ 프롬프트는 규칙 나열뿐, 모범 page_specs 예시 없음.
  델타3 = 프롬프트 역학(지시 시작+끝 반복/구분자/출력 프라이밍) — (A) 자동 래퍼 구현 시 적용."

## 너의 검수 4과제
1. **사실검증**: [C]의 핵심 주장 중 틀렸거나 과장(예: '3배', '초기 입력 가중치', 'Kawasaki 10/20/30',
   'recency bias 시작+끝 반복')을 사실/미검증/과장으로 판정. 근거 한 줄.
2. **중복 판정**: [C] 항목들이 [A][B]에 이미 있는지 표로. (이미있음=어느 조항 / 부분 / 없음).
3. **델타 검증**: 클차장 3개 델타가 맞나? 과대/과소 평가된 것은? **클차장이 놓친 진짜 델타가 있나?**
   (자동·무인 URL→덱 파이프라인 관점에서. 사람이 개입 못 한다는 제약 유의.)
4. **흡수 우선순위**: 최종 흡수 권고를 임팩트×난이도로 3~5개. 각: 무엇을·어디 문서에·왜.

간결하게. 일반론·칭찬 빼고 [A][B] 조항을 직접 인용하며 판정하라.

---
## [A] 틱덱 작가 DNA (SoT)
{DNA}

---
## [B] 틱덱 작가 단계 설계
{AUTHOR}

---
## [C] Kimi 외부 조사 (검수 대상)
{KIMI}
"""

models = ["gemini-3.1-pro", "gemini-2.5-pro"]
out = None
used = None
for m in models:
    res = call(prompt=PROMPT, system_text=SYSTEM, model=m, use_cache=False)
    txt = res.get("text", "")
    if txt and "error" not in res:
        out, used = txt, m
        break
    print(f"[skip] {m}: {res.get('error', 'no text')}", file=sys.stderr)

if not out:
    print("ALL MODELS FAILED", file=sys.stderr)
    sys.exit(1)

dest = ROOT / "review/kimi_guide_absorption_review.md"
dest.write_text(f"# Gemini 검수 — Kimi 가이드 흡수 ({used})\n\n{out}\n", encoding="utf-8")
print(f"=== MODEL: {used} ===")
print(out)
print(f"\n[saved] {dest}")
