#!/usr/bin/env python3
"""비판가 패스(critic pass) 실증 — 살아있는 덱에 DNA 게이트 루브릭으로 비판 LLM 1회.

목적: Gemini가 '최상 임팩트'로 꼽은 critic pass를 실제 마케팅 덱(page_specs)에 돌려,
      비판이 날카로운지(=채택 가치) 후추님이 직접 보고 판단.
SoT 미수정. 산출 = v3/review/critic_pass_output.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "Projects/Automation/Think/.claude/scripts"))
try:
    from dotenv import load_dotenv
    load_dotenv(Path.home() / "Projects/Automation/TickDeck/.env")
except Exception:
    pass
from gemini_call_wrapper import call  # noqa: E402

ROOT = Path.home() / "Projects/Automation/TickDeck/v3"
specs = json.loads((ROOT / "authored/2026_마케팅_트렌드_page_specs.json").read_text(encoding="utf-8"))

SYSTEM = """당신은 컨설팅 덱 적대적 비판가다. 칭찬 금지. 약점만 찾는다.
루브릭 = 이 엔진의 작가 DNA 게이트:
  G1 지배메시지 일관성: 각 페이지가 governing_thought를 실제로 증명/전진시키나? 곁가지·이탈 페이지?
  G2 액션타이틀: headline이 라벨('시장 규모')이 아니라 서술어 있는 주장인가? (간지·목차·표지 예외)
  G3 claim→evidence→so-what: takeaways에 결론이 먼저 오고, payload가 그 근거이며, 함의(so-what)가 있나?
  G4 종합하되 평균하지마라: 이질적 수치를 평균/뭉뚱그린 가짜 빅넘버 없나? 단위 충돌(예: 수익+시장규모 한 축)?
  G5 출처 규율: 수치 주장에 source가 붙나? 출처 공백 주장은?
  G6 불확실성 노출: 추정·기관차이·데이터시점·반대증거가 숨겨졌나? 과잉 단정?
  G7 사업화형 착지: 나열로 끝나지 않고 '그래서 무엇을·다음 액션'으로 내려오나? (결론/시사 페이지 특히)
  G8 한 장 한 메시지: 한 페이지에 두 주제 섞임?
출력: 한국어 개조식. 페이지별 '치명도(상/중/하)' + 어느 게이트 위반 + 한 줄 처방. 코드블록 X.
끝에 '덱 전체 3대 약점' + '가장 먼저 고칠 1개'."""

PROMPT = f"""아래는 자동생성된 설득 덱의 작가 원고(page_specs.json)다.
지배메시지 = "{specs.get('governing_thought')}"
이 덱을 위 8개 게이트로 무자비하게 비판하라. 진짜 약점만. 멀쩡한 페이지는 '이상 없음' 한 줄.

=== PAGE_SPECS (작가 원고) ===
{json.dumps(specs, ensure_ascii=False, indent=1)}
=== 끝 ===

페이지별 비판 후, 덱 전체 3대 약점과 '가장 먼저 고칠 1개'를 명시하라.
이 비판이 작가에게 그대로 전달돼 원고를 고치는 데 쓰인다. 추상론 금지, 페이지 번호·구체 문구 인용."""

for m in ["gemini-2.5-pro"]:
    res = call(prompt=PROMPT, system_text=SYSTEM, model=m, use_cache=False)
    txt = res.get("text", "")
    if txt and "error" not in res:
        dest = ROOT / "review/critic_pass_output.md"
        dest.write_text(f"# 비판가 패스 실증 — 2026 마케팅 트렌드 덱 ({m})\n\n{txt}\n", encoding="utf-8")
        print(txt)
        print(f"\n[saved] {dest}")
        break
    print(f"[skip] {m}: {res.get('error','no text')}", file=sys.stderr)
else:
    sys.exit(1)
