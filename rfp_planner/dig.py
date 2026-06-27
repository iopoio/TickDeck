#!/usr/bin/env python3
"""웹 디깅 = 신야 경유 중국 모델(GLM·Qwen) + OpenRouter 웹검색(:online).

출처 있는 리서치를 싼 채널(신야 예산)로 돌린다. **공개 주제만**(신야 격리 룰 —
후추님 개인정보 X). 2026-06-27 후추님 표준화: 키미·딥시크 → GLM·Qwen로 교체.

모델 고르기(상황 따라):
  glm  = z-ai/glm-5.2:online   — 빠름·저지연·구조적·agentic (기본)
  qwen = qwen/qwen3.7-max:online — 지능·긴 출력 (깊은 종합·복잡 추론)
  qwen-plus = qwen/qwen3.7-plus:online — 더 싸고 충분 (대량·단순 디깅)

쓰는 법:
  python3 dig.py "네바다 J-1 비자 정부 sponsor 절차" qwen
  from dig import dig; dig("...", "glm")
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "sinya/src"))
import sinya_core  # noqa: E402

MODELS = {
    "glm": "z-ai/glm-5.2:online",
    "qwen": "qwen/qwen3.7-max:online",
    "qwen-plus": "qwen/qwen3.7-plus:online",
}
SYS = ("너는 출처 기반 리서치 전문가다. 웹을 검색해 사실을 확인하고, 각 핵심 사실에 "
       "출처 URL을 붙여라. 추측·미확인은 '확인 안 됨'으로 표기. 한국어, 간결·구조적 마크다운.")


def dig(query: str, model: str = "glm") -> str:
    """질문 → 출처 있는 디깅 결과(텍스트). model = glm|qwen|qwen-plus."""
    return sinya_core.ask(query, model=MODELS.get(model, MODELS["glm"]), system=SYS)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 dig.py \"질문\" [glm|qwen|qwen-plus]")
    m = sys.argv[2] if len(sys.argv) > 2 else "glm"
    print(f"[{MODELS.get(m, MODELS['glm'])}]\n")
    print(dig(sys.argv[1], m))
