#!/usr/bin/env python3
"""50개 코덱스 다관점 무자비+건설적 리뷰 드라이버.
각 perspective = 독립 `codex exec` (read-only), JSON findings 반환. 병렬 배치 실행."""
import json, subprocess, concurrent.futures as cf, time, sys
from pathlib import Path

REVIEW = Path(__file__).resolve().parent
OUT = REVIEW / "out"
OUT.mkdir(exist_ok=True)

PERSPECTIVES = [
    # A. 종합 전문가 (10)
    ("01_consulting_partner", "맥킨지/PwC급 컨설팅 파트너", "논증 사슬(주장→근거→함의)이 슬라이드끼리 이어지는가. 구조 결함·빈 논증."),
    ("02_ceo_founder", "트렌드 덱을 읽는 CEO/창업자", "so-what이 명확한가. '왜 지금' 당위. 의사결정에 바로 쓸 수 있나."),
    ("03_design_director", "시니어 디자인 디렉터", "타이포 위계 일관성·여백·정렬. 한 덱 한 시스템 commit 깨진 곳(JSON 구조·길이 기준)."),
    ("04_data_honesty", "데이터 정직성 감사관", "모든 수치 출처추적 가능한가. 평균/가짜 정밀/cherry-pick. MarTech 범위 정직성."),
    ("05_huchu_logic", "후추님 사업화형 논리 심사관", "골격(변화→문제→비교→해결→실행→다음액션) 충실? 변화에 오래 머물지 않고 실행 단위로 내려가나."),
    ("06_huchu_voice", "후추님 개조식 말투 심사관", "개조식(~함/~임/~됨) 일관? 합니다체/평서체(~다) 잔재. 명사구 헤드라인·화살표 시그니처."),
    ("07_korean_natural", "한국어 자연스러움 교정관", "번역체(수동태·~를 통해·~에 대해·어색 어순)·CJK 혼용. 어색한 표현 콕 집기."),
    ("08_marketing_sme", "2026 마케팅 도메인 전문가", "트렌드 사실성·최신성. 빠진 핵심 트렌드. 틀리거나 한물간 주장."),
    ("09_stats_verifier", "통계 검증가", "각 수치(60/80/75/43/18-47/527/$173B/$660B/36.6%) 신뢰·맥락. 과장·오용."),
    ("10_headline_copy", "헤드라인 카피라이터", "헤드라인이 주장 담은 명사구(액션타이틀)인가·14자 안팎·라벨화된 것."),
    # B. 청중·맥락 (8)
    ("11_cmo_audience", "이 덱을 받는 실무 CMO", "내 팀에 바로 쓸 실행 단서가 있나. 추상적이라 안 와닿는 곳."),
    ("12_skeptic_exec", "회의적 임원", "반대 증거·약점·한계가 충분히 노출됐나. 낙관 일변도인 곳."),
    ("13_junior_marketer", "신입 마케터", "용어 풀이 충분한가. 이해 안 되는 점프."),
    ("14_vs_competitor_deck", "PwC/메조미디어 트렌드덱 대비 평가관", "그 펌 덱 대비 떨어지는 점. 격차."),
    ("15_read_only_deck", "발표자 없는 '읽는 덱' 적합성 심사", "본문 절제 vs 과밀·빈약. 혼자 읽어도 이해되나."),
    ("16_story_arc", "스토리 아크 편집자", "현재→전개→결론 응집. 흐름 끊김·순서 어색."),
    ("17_governing_echo", "지배 메시지 일관성 심사", "거버닝 thought(AI=기본값·차별화=신뢰)가 표지·전개·결론에 메아리치나."),
    ("18_reframe_diff", "자체 재분류 차별성 심사", "원시 트렌드 나열이 아니라 '우리 렌즈'로 재해석됐나(다섯 갈래 등)."),
    # C. 슬라이드 deep-dive (12)
    ("19_cover_agenda", "표지·목차(p1-2) 심사", "첫인상·아젠다 명료성·기대 형성."),
    ("20_section01", "섹션01 판이 바뀐다(p3-4) 심사", "변화 정의 설득력·전제 교체 논증."),
    ("21_timeline", "타임라인(p5) 심사", "3단계 진화(실험21%→통합60%→에이전틱 2/3) 논리·수치 적절성."),
    ("22_martech_size", "MarTech 규모(p6) 심사", "정의 스프레드 4배 정직성·거대숫자 콜아웃 효과·오해 소지."),
    ("23_adoption_chart", "도입률 차트(p7) 심사", "차트 정확(60/80/75)·메시지('얼마나 잘')·sparse."),
    ("24_five_forces", "섹션02 다섯 갈래(p8-9) 심사", "5축 MECE·중복·누락. 5±2 적정."),
    ("25_compare_table", "5축 비교표(p9) 심사", "행/열 논리·셀 간결·과밀."),
    ("26_growth_cards", "성장 4동력 카드(p10) 심사", "병렬성·중복·밀도(4카드 과밀?)."),
    ("27_volume_pov", "볼륨→확신 before/after(p11) 심사", "대비 선명도·POV 논증."),
    ("28_section03", "섹션03 신뢰의 역설(p12) 심사", "역설 논증 설득력."),
    ("29_ai_vs_human", "AI vs 사람(p13)+43% metric 심사", "통찰 강도·43% 개인화 갭 활용·대비."),
    ("30_search_chart", "검색 재편 차트(p15) 심사", "Improvado 수치(18-47/527/34)·AEO 함의·% 종류 혼동."),
    # D. 마감·신뢰·디테일 (10)
    ("31_conclusion", "결론(p19) 심사", "so-what·액션 3개 구체성·해석주의 적정·착지 강도."),
    ("32_references", "참고자료(p20·15소스) 심사", "출처 신뢰·표기·URL 누락."),
    ("33_source_consistency", "출처 표기 일관성 심사", "인라인+footer·헤드라인 기관명 규칙·핵심통계 주어 승격."),
    ("34_glossary", "용어 풀이 심사", "영문 병기·풀이 과잉/부족. 첫 등장 풀이 누락."),
    ("35_chart_accuracy", "차트 데이터 정확성 심사", "값·단위·축 혼동(예: 이질 단위 한 축)·라벨."),
    ("36_color_theme", "색·테마 심사", "펜톤 톤다운·주제 적응. 파랑 과용? 마케팅 주제에 맞나."),
    ("37_density_balance", "과밀/빈약 균형 심사", "density 경고 13건 관점. 비차트 슬라이드 빈약·차트 sparse."),
    ("38_transitions", "섹션 간 전환 심사", "01→02→03→04 연결 매끄러움·논리 도약."),
    ("39_dividers", "간지 4장 심사", "긴장(통념→균열)·다음 섹션 예고 효과."),
    ("40_quant_balance", "정량/정성 균형 심사", "'숫자로 말하기' 충분? 정성 주장 과다·근거 빈약."),
    # E. 무자비 적대 (10)
    ("41_destroyer", "destroyer(적대 파괴자)", "이 덱이 죽는·무시당할 이유 5가지. 가차없이."),
    ("42_sowhat_attack", "'그래서 뭐' 공격수", "so-what 없이 사실만 있는 슬라이드 콕 집기."),
    ("43_cliche_detector", "진부함 검출관", "누구나 아는 얘기·차별 없는 주장. 식상."),
    ("44_hype_detector", "과장·허세 검출관", "근거 없는 단정·빈 수식어·낙관 과장."),
    ("45_logic_gap", "논리 비약 검출관", "주장↔근거 연결 끊긴 곳·비약."),
    ("46_contrarian", "반대론자", "이 트렌드 주장이 틀릴 수 있는 지점·반례."),
    ("47_omission", "누락 검출관", "빠진 핵심 트렌드·관점·반대 데이터."),
    ("48_inconsistency", "일관성 파괴 검출관", "한 장이 전체 톤·위계 깨는 곳."),
    ("49_huchu_cringe", "후추님이 직접 볼 때 어색할 곳 예측", "후추님 눈에 1순위로 손볼 곳."),
    ("50_final_score", "총괄 심사위원장", "0-10 종합 점수(논리/문체/디자인/정직성)·가장 시급한 fix 3개."),
]

PROMPT_TMPL = """너는 '{role}' 관점의 무자비하면서 건설적인 리뷰어다.
한국어 컨설팅 트렌드 덱(자동 작가 엔진 산출물)을 심사한다. 제1 사용자=후추님(15년차 기획자).

먼저 두 파일을 읽어라:
- ./dna_brief.md (이 덱이 통과해야 할 기준 = 작가 원칙 9·후추님 문체/논리·컨설팅 보이스·한국어·정직성)
- ./deck_text.md (심사 대상 덱 전문: 헤드라인·테이크어웨이·본문·수치·출처)
정확한 원본 JSON이 필요하면 ../authored/2026_마케팅_트렌드_page_specs.json 도 읽어도 된다.

너의 렌즈: {focus}

규칙:
- 칭찬 말고 '고칠 것'만. 구체적·실행 가능하게. 두루뭉술 금지.
- 진짜 문제만. 없으면 적게. 억지로 채우지 마라.
- 슬라이드 번호(page_no) 명시. 전역이면 "global".
- DNA 기준 위반은 어느 원칙인지 짚어라.

출력은 **오직 JSON 배열** 하나. 다른 텍스트·설명·코드펜스 금지:
[{{"severity":"high|med|low","slide":"<page_no 또는 global>","issue":"<무엇이 문제인가·왜>","fix":"<어떻게 고치나·구체적>","principle":"<위반한 DNA 원칙/없으면 ''>"}}]
최대 5개. 한국어로.
"""

def run_one(pid, role, focus):
    prompt = PROMPT_TMPL.format(role=role, focus=focus)
    outfile = OUT / f"codex_{pid}.json"
    cmd = [
        "codex", "exec", "--skip-git-repo-check",
        "-s", "read-only", "-C", str(REVIEW),
        "-o", str(outfile), prompt,
    ]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=420)
        dt = time.time() - t0
        ok = outfile.exists() and outfile.stat().st_size > 0
        return (pid, ok, round(dt,1), r.returncode)
    except subprocess.TimeoutExpired:
        return (pid, False, 420.0, "TIMEOUT")
    except Exception as e:
        return (pid, False, round(time.time()-t0,1), str(e)[:60])

def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    log = REVIEW / "progress.log"
    done = 0
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(run_one, p, r, f): p for p, r, f in PERSPECTIVES}
        for fut in cf.as_completed(futs):
            pid, ok, dt, rc = fut.result()
            done += 1
            line = f"[{done}/{len(PERSPECTIVES)}] {pid} ok={ok} {dt}s rc={rc}"
            print(line, flush=True)
            log.write_text((log.read_text() if log.exists() else "") + line + "\n")
    print("ALL DONE", flush=True)

if __name__ == "__main__":
    main()
