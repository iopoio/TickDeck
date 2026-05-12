# TickDeck v2 — 5/13 작업 plan

> 작성: 2026-05-12 21:00 KST
> 영역: 후추님 내일 시작 영역 정리 (PRD 5/13 7단계 정합·5/12 살짝 1단계 user_flow 완료 영역 후)
> 기준: `TickDeck/v2/PRD_v2.md` line 250~262

## 시작 영역 점검 (5/13 첫 영역)

1. `cd Think && git pull` — 본진 sync
2. `cd /Users/hwa/Projects/Automation/TickDeck && git pull` — TickDeck repo sync
3. `Think/.claude/inbox/from_nokl/` 점검 — 노클이 PDF 송부했는지 (7단계 영역)
4. 외부 공모전 마감 영역 점검 (5/14 고용노동 결과 발표 영역·5/15 모두의 창업 결과 영역)
5. 본 PLAN 파일 read·진행

## 7단계 영역 (어제 1번 완료 영역 후)

| # | 단계 | 도구 | 시간 | 비고 |
|---|---|---|---|---|
| ✅ 1 | user flow | `user-flow:index` skill | 30분 | 5/12 완료·`v2/user_flow.md` |
| ⏳ 2 | UI 와이어프레임 | **Claude Design** (claude.ai/design) | 1시간 | 후추님 직접 영역·prompt 아래 정리 |
| ⏳ 3 | 기능 명세 | `feature-spec:index` skill | 30분 | PRD 자동 추출 영역 多 |
| ⏳ 4 | 테스트 시나리오 | `pm-execution:test-scenarios` | 30분 | 1번·3번 결과 정합 |
| ⏳ 5 | pre-mortem (위험 분석) | `pm-execution:pre-mortem` | 30분 | 출시 전 위험 영역 |
| ⏳ 6 | writing-plans (실 구현 계획) | `superpowers:writing-plans` skill | 1시간 | 2~5단위 task 영역 |
| ⏳ 7 | 노클 PDF 송부 받고 본진+제대리 교차 분석 | 자동 (수동 트리거) | 1~2일 | 노클 sync 영역 |

합: 약 4시간 (2~6번)·7번 자동.

## 2번 영역 — Claude Design 와이어프레임 prompt

후추님 claude.ai/design 영역에서 바로 입력 영역. 결과 = PNG 또는 HTML 영역·`TickDeck/v2/wireframe/` 폴더 새로 만들고 commit.

```
TickDeck v2 — PDF→PPTX 자동 생성 도구. Streamlit 단일 페이지 앱.

5개 화면 와이어프레임 만들어줘:

1. 랜딩·첫 화면
   - 차별 한 줄: "PDF 한 장 → PPTX 1-딸깍·일반인용"
   - 프라이버시 안내: "세션 종료 시 자동 삭제·DB X·계정 X"
   - 시작 버튼 1개

2. PDF 업로드
   - drag·drop 영역
   - "텍스트 PDF만 지원·스캔 PDF X" 안내
   - 다음 버튼

3. 청중·목적 입력
   - 청중 한 줄 (placeholder: "대학생·면접관·잠재 고객")
   - 목적 한 줄 (placeholder: "발표용·제출용·내부 공유")
   - skip OK (default 적용)
   - 시작 버튼·1-딸깍

4. 자동 파이프라인 진행
   - 7단계 시각화 (PDF 파싱 → AI 조사 → 통합 → 내러티브 → 품질 → 디자인 → PPTX)
   - 현재 단계 강조
   - 예상 시간 (1~5분)

5. 완료·다운로드
   - PPTX 파일 1개 다운로드 버튼 (큰)
   - "스타일 변경 1회 영역" 보조 버튼
   - 외부 도구 안내 (PowerPoint·Google Slides에서 편집)
   - 종료 시 자동 삭제 재안내

톤: 미니멀·여백 多·Pretendard 영역. 모바일 OK·데스크탑 권장. 옵션 폭발 X·일반인용.
```

### 결과 import 영역

```bash
mkdir -p /Users/hwa/Projects/Automation/TickDeck/v2/wireframe
# Claude Design 결과 PNG·HTML 저장 후
cd /Users/hwa/Projects/Automation/TickDeck
git add v2/wireframe/
git commit -m "docs: 5/13 TickDeck v2 와이어프레임 5개 (Claude Design)"
git push
```

## 3~6번 영역 — 본진 클차장 skill 영역

후추님 영역 X·본진 클차장 자율 진행 영역. 후추님 review·OK 영역만.

- 3번 feature-spec:index → `v2/feature_spec.md`
- 4번 test-scenarios → `v2/test_scenarios.md`
- 5번 pre-mortem → `v2/pre_mortem.md`
- 6번 writing-plans → `v2/PLAN_implementation.md` (실 빌드 task 영역)

## 7번 영역 — 노클 PDF 송부 (병렬·자동)

- 노클이 PDF 일괄 송부 영역 = `Think/inbox-pdf/research/`
- 본진 = 송부 받자마자 자동 read·제대리 (gemini CLI) 교차 분석
- 결과 = `TickDeck/v2/templates.json`
- 노클 송부 시점 = 5/13~5/14 영역·노클 자율

## 6/1 사보원 영역 자국 (양보 룰 정합)

5/30경 사보원 (국민행복서비스) 작업 영역 = TickDeck 빌드 3·4단계 영역과 충돌 가능. 본진이 6/1 마감 영역 우선·TickDeck 단계 양보. PRD line 140 정합.

오늘 살짝 user_flow + 내일 plan만 = 6/1 영역과 자국 X.

## 외부 마감 영역 (5/13 시작 시 점검 의무)

| 일자 | 영역 | 비고 |
|---|---|---|
| 5/14 | 고용노동 마감 (잡솔트) | 결과 발표 영역·이미 제출 |
| 5/15 | 모두의 창업 마감 (EatScan) | 결과 발표 영역·이미 제출 |
| 5/18 | 혁신창업리그 dropped 최종 결정 | 후추님 99% dropped 의향 |
| 6/1 | 사보원 (국민행복서비스) 제출 | 5/30경 작성 영역 |

→ 5/14·5/15 결과 영역 들어오면 TickDeck 일시 정지·공모전 우선 룰 정합 (PRD 결정 영역).

## 가시성 (한 줄)

내일 후추님 영역 = 2번 Claude Design 와이어프레임 (1시간). 나머지 = 본진 자율 + 노클 PDF 자동 영역.
