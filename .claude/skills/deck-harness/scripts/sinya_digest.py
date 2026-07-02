#!/usr/bin/env python3
"""신야 소화 레인 — 로컬 코퍼스(공개 발행 PDF 텍스트)를 중국 모델이 1차 소화해
collector 스키마 partial JSON을 만든다. 클로드 collector는 검수·승격만 (비용 절감 구조).

품질의 핵심 = 디테일 프롬프트(후추님 7/2): 스키마·티어링·재인용 판정·COI·반대신호·
수치 구조화(value 숫자만/unit 순수/scope에 표본·시점)·Loop L 표현 관찰까지 명령에 박는다.
v3 dig_agent의 규율(티어·재인용·confidence) 승계.

⚠️ 경계(v3 승계): 공개 발행물만 이 레인으로. 후추님 개인·클라이언트 자료는 클로드 소화.

용법 (신야 venv python으로 실행):
  /Users/hwa/Projects/Automation/sinya/venv/bin/python .claude/skills/deck-harness/scripts/sinya_digest.py \
    <text.txt> --publisher "KPMG" --title "Global Tech Report 2026" --local-path "/path/to.pdf" \
    [-o partial.json] [--model qwen/qwen3.7-plus] [--max-chars 60000]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SINYA_DIR = Path("/Users/hwa/Projects/Automation/sinya")

DIGEST_PROMPT = """너는 트렌드 리포트 수집 애널리스트다. 아래 [문서]를 소화해 **JSON 하나만** 출력한다(설명·마크다운 금지).

## 출력 스키마 (모든 필드 필수)
{
 "publisher_confirmed": "문서에서 확인한 발행 기관(못 찾으면 빈칸)",
 "year": "발행 연도(문서 근거·못 찾으면 빈칸)",
 "tier_opinion": "Tier-A|Tier-B|FLAG — 아래 티어 규칙으로 판정 + 한 줄 이유",
 "source_type": "report|article|dataset|filing",
 "region": "문서가 다루는 지역(global|US|EU|KR 등)",
 "sample": "설문·데이터 표본 명세(예: '기술 임원 2,500명, 2025.9'· 없으면 빈칸)",
 "method": "조사 방법 한 줄(없으면 빈칸)",
 "coi": "이해상충 판정 — 벤더 자사 서비스 판매 프레이밍이면 구체적으로, 없으면 빈칸",
 "claims": ["핵심 주장 4~8개. 문서에 실제로 있는 것만. 한국 관련이면 문장 앞에 [KR]"],
 "metrics": [{"value":"숫자 문자열만(단위·괄호·영문 금지)","unit":"순수 단위만(%·억 달러·명·건 등)","scope":"무엇의 수치인지 + 기준시점·표본·비교기준을 이 필드에","page_hint":"원문 근처 소제목이나 페이지 단서","quote":"수치가 등장한 원문 문장 그대로(검증용)"}] — 문서 전체에서 덱에 쓸 만한 핵심 수치를 6~12개, 시계열·전후 비교를 우선으로 최대한 캐라,
 "from_to_pairs": [{"from_metric":"이전 값","to_metric":"현재/전망 값","what":"무엇의 전이인지"}],
 "counter_signals": ["문서 안의 마찰·리스크·실패·반대 신호 최소 1개(낙관 일변도면 '문서 내 반증 부재'라고 쓰기)"],
 "limitations": ["표본/방법 한계·재인용 여부·예측치 여부 — 정직하게"],
 "loop_l_observations": [{"expression":"반복 관찰된 헤드라인 말투·어휘·수치 어법·구성 관례","meaning":"뜻","count":"관찰 횟수"}]
}

## 규율 (어기면 해당 항목 폐기)
1. **문서에 실제로 있는 수치만.** 기억·추정으로 채우지 마라. 각 metric에는 원문 인용(quote)을 붙인다 — 검증자가 대조한다.
2. **value는 순수 숫자 문자열**("85"·"1655"·"44.5"). 단위는 unit에, 한정어(계획/전망/기준연도)는 scope에. "85% (planned)" 같은 오염 금지.
3. **티어**: Tier-A = 정부·통계청·규제기관·학술 + 컨설팅/투자사/증권사 1차 리서치. Tier-B = 언론·마케팅 벤더·출처 각주 없는 통계. FLAG = 유료 샘플·리드젠 축약본.
4. **재인용 판정**: 문서가 타 기관 수치를 인용한 거면 limitations에 "원출처 OOO 재인용" 명시.
5. **시계열 우선**: 같은 지표의 이전→현재/전망 쌍을 찾으면 metrics에 둘 다 넣고 from_to_pairs에 등록(트렌드=상태전이).
6. 한국(KR) 신호는 빠짐없이 claims에 [KR]로.
7. 출력은 JSON 객체 하나. 코드펜스·주석·설명 금지.

[문서: {doc_label}]
{doc_text}
"""


def load_env() -> str:
    for line in (SINYA_DIR / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("OPENROUTER_API_KEY not found in sinya/.env")


def call_model(model: str, prompt: str, api_key: str) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"), api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=8000,
    )
    return resp.choices[0].message.content or ""


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.S)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < 0:
        raise ValueError("no JSON object in model output")
    return json.loads(text[start : end + 1])


def main() -> int:
    ap = argparse.ArgumentParser(description="신야 소화 레인 — 로컬 텍스트 → collector partial JSON")
    ap.add_argument("text_file", type=Path)
    ap.add_argument("--publisher", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--local-path", default="")
    ap.add_argument("-o", "--out", type=Path, default=None)
    ap.add_argument("--model", default="qwen/qwen3.7-plus")
    ap.add_argument("--max-chars", type=int, default=60000)
    args = ap.parse_args()

    doc = args.text_file.read_text(encoding="utf-8", errors="ignore")
    truncated = len(doc) > args.max_chars
    doc = doc[: args.max_chars]
    label = args.title or args.text_file.stem
    prompt = DIGEST_PROMPT.replace("{doc_label}", label).replace("{doc_text}", doc)

    raw = call_model(args.model, prompt, load_env())
    data = parse_json(raw)

    item = {
        "source_id": "PENDING",  # 병합 시 부여
        "url": "",
        "local_path": args.local_path,
        "title": args.title or data.get("publisher_confirmed", "") or args.text_file.stem,
        "publisher": args.publisher or data.get("publisher_confirmed", ""),
        "year": str(data.get("year", "")),
        "tier": str(data.get("tier_opinion", "Tier-B")).split()[0].split("—")[0].strip() or "Tier-B",
        "tier_reason": data.get("tier_opinion", ""),
        "source_type": data.get("source_type", "report"),
        "region": data.get("region", ""),
        "sample": data.get("sample", ""),
        "method": data.get("method", ""),
        "coi": data.get("coi", ""),
        "paywall_flag": False,
        "zombie_flag": False,
        "circular_citation_flag": any("재인용" in str(l) for l in data.get("limitations", [])),
        "claims": data.get("claims", []),
        "metrics": data.get("metrics", []),
        "from_to_pairs": data.get("from_to_pairs", []),
        "counter_signals": data.get("counter_signals", []),
        "limitations": data.get("limitations", []) + (["텍스트 앞부분만 소화(잘림)"] if truncated else []),
        "digested_by": args.model + " (sinya_digest — 클로드 verifier 승격 전 원본)",
    }
    out = {"items": [item], "loop_l_observations": data.get("loop_l_observations", [])}
    out_path = args.out or args.text_file.with_suffix(".digest.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"OK {out_path} — claims {len(item['claims'])} · metrics {len(item['metrics'])} · counter {len(item['counter_signals'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
