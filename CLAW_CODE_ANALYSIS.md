# Claw-Code 패턴 → TickDeck 적용 분석

> instructkr/claw-code의 Coordinator 패턴을 분석하고
> TickDeck(Web to Slide) 서비스에 적용할 수 있는 것을 정리

---

## Claw-Code에서 발견한 핵심 패턴

### 1. Coordinator 패턴 (멀티 에이전트 오케스트레이션)

```
$team mode   → 병렬 리뷰 + 아키텍처 피드백 (설계 단계)
$ralph mode  → 실행 + 검증 + 완료 규율 (구현 단계)
```

핵심: **한 에이전트가 모든 걸 하지 않는다.** 역할별로 모드를 전환하며,
실행 에이전트와 검증 에이전트가 분리됨.

### 2. ExecutionRegistry (실행 등록부)

```python
ExecutionRegistry {
    commands: tuple[MirroredCommand, ...]  # 사용 가능한 명령어
    tools: tuple[MirroredTool, ...]        # 사용 가능한 도구
}
```

모든 실행 가능한 작업이 **등록부에 등록**되어 있고,
이름으로 조회해서 실행. 확장 시 등록부만 추가.

### 3. PortContext (불변 컨텍스트)

```python
@dataclass(frozen=True)
class PortContext:
    # 프로젝트 상태를 한번 계산하고 불변으로 유지
```

프로젝트 상태를 **한번 계산 → 이후 변경 불가**.
실행 중 상태가 바뀌면 새 컨텍스트를 만들지, 기존 걸 수정하지 않음.

### 4. Task → Review 자기 검증 루프

```
Plan → Execute → Self-Review → (실패 시) Re-plan
     ↑                              ↓
     └──────── 2회 실패 → 보고 ────┘
```

"persistent execution loops with architect-level verification"
— 실행 후 반드시 검증, 검증 실패 시 재시도, N회 실패 시 에스컬레이션.

---

## 30년차 프로덕트 디렉터 관점 — "이걸 왜 하고, 뭘 얻나?"

### 현재 TickDeck의 에이전트 구조

```
[후추님] → 지시 → [클과장] → 설계/리뷰
                      ↓
               [제대리] → 구현 → [클과장] → 리뷰 → [배포]
```

문제:
- **후추님이 인간 릴레이** — 클과장 지시 → 제대리 전달 → 결과 받기 → 클과장 리뷰 → 다시 전달
- 릴레이 1회당 5~10분 소요, 하루에 10회면 1~2시간이 릴레이에 소비됨
- 제대리가 루프 돌면 후추님이 감지 못하고 시간/토큰 낭비

### Claw-Code 패턴 적용 시 목표 구조

```
[후추님] → 방향만 지시 → [Coordinator]
                              ↓
                    ┌── Task 분배 ──┐
                    ↓               ↓
              [실행 에이전트]   [검증 에이전트]
              (제대리)         (클과장 or 자동)
                    ↓               ↓
                    └── 결과 취합 ──┘
                              ↓
                         [후추님] ← 완료 보고
```

**후추님은 "뭘 만들어"만 말하고, 중간 릴레이 없이 완료 보고만 받는 구조.**

### 현실적 제약

| 제약 | 설명 |
|------|------|
| Claude ↔ Gemini 직접 통신 불가 | API 연결 없음, GitHub 파일만 공유 |
| 자동 Coordinator 구현 어려움 | 지금은 후추님이 Coordinator 역할 |
| 비용 | Claude Opus가 Coordinator까지 하면 토큰 폭증 |

### PD 결론: 3단계 접근

**Phase A (지금)**: 후추님 = Coordinator. CLAUDE.md 규칙으로 프로토콜 표준화. 이미 하고 있음.

**Phase B (중기)**: GitHub Issue 기반 핸드오프.
```
후추님 → GitHub Issue 생성 ("CTA 리디자인")
제대리 → Issue 읽고 PR 생성
클과장 → PR 리뷰 코멘트
제대리 → 수정 후 머지
```
후추님의 릴레이 역할이 "Issue 생성" 한번으로 줄어듦.

**Phase C (장기)**: 자동 Coordinator 스크립트.
```python
# coordinator.py (개념)
def run_task(task_description):
    # 1. 제대리에게 구현 요청 (Gemini API)
    result = gemini.generate(task_description + CLAUDE_MD_RULES)
    # 2. 클과장에게 리뷰 요청 (Claude API)  
    review = claude.review(result)
    # 3. 리뷰 통과 시 커밋, 실패 시 재시도
    if review.approved:
        git_commit(result)
    else:
        run_task(task_description + review.feedback)  # 최대 2회
```
이건 양쪽 API 비용이 들지만, 후추님 시간은 0에 수렴.

---

## 50년차 개발자 관점 — "코드로 뭘 바꿔야 하나?"

### 패턴 1: Task → Review 자기 검증 루프 (즉시 적용 가능)

현재:
```
제대리가 코드 수정 → "완료했습니다" → 클과장이 pull → 리뷰 → 이슈 발견 → 재수정
```

Claw-Code 패턴 적용:
```
제대리가 코드 수정 → 자체 검증(Playwright + lint) → 통과 시 "완료" → 클과장 리뷰
                    ↓ 실패 시
                    자동 수정 시도 (최대 2회) → 그래도 실패 → "막혔습니다" 보고
```

**CLAUDE.md에 추가할 규칙:**
```markdown
## 제대리 자기 검증 루프
1. 코드 수정 완료
2. `npx playwright test` 실행
3. 통과 → 커밋 + "완료" 보고
4. 실패 → 에러 분석 → 수정 (최대 2회)
5. 2회 실패 → "막혔습니다 + 에러 내용" 보고. 무한 재시도 금지.
```

### 패턴 2: ExecutionRegistry (중기 적용)

현재 TickDeck 파이프라인:
```python
# pipeline.py — 순차 실행, 하드코딩
raw_info = scrape(url)
factbook = agent_researcher(raw_info)
storyline = agent_strategist(factbook)
slides = generate_slide_json(factbook, storyline)
```

ExecutionRegistry 패턴 적용:
```python
# pipeline.py — 등록부 기반, 확장 가능
PIPELINE_STEPS = [
    Step("scrape", scrape_fn, retry=2),
    Step("research", researcher_fn, retry=1),
    Step("strategize", strategist_fn, retry=1),
    Step("generate", copywriter_fn, retry=2),
    Step("match_images", image_fn, retry=1),
]

def run_pipeline(url, **kwargs):
    context = {}
    for step in PIPELINE_STEPS:
        try:
            context[step.name] = step.execute(context, **kwargs)
        except Exception as e:
            if step.retries_left > 0:
                step.retry(context, **kwargs)
            else:
                raise PipelineStepError(step.name, e)
```

장점:
- 단계 추가/제거가 설정으로 가능 (코드 수정 없이)
- 실패 시 해당 단계부터 재시도 (전체 재실행 아님)
- 단계별 실행 시간/성공률 메트릭 수집 용이

### 패턴 3: 불변 컨텍스트 (장기 적용)

현재: `_slideData`가 전역 mutable 변수로 프론트에서 수정됨.
Claw-Code: `@dataclass(frozen=True)` — 불변.

적용 시:
```python
@dataclass(frozen=True)
class PipelineContext:
    url: str
    company: str
    factbook: str = ""
    storyline: list = field(default_factory=list)
    slides: dict = field(default_factory=dict)
    
    def with_factbook(self, fb):
        return replace(self, factbook=fb)  # 새 객체 반환
```

각 단계가 이전 컨텍스트를 받아서 **새 컨텍스트를 반환**하는 구조.
디버깅이 훨씬 쉬워짐 (어느 단계에서 뭐가 바뀌었는지 추적 가능).

---

## 우선순위 정리

| 순서 | 항목 | 난이도 | 임팩트 | 담당 |
|------|------|--------|--------|------|
| 1 | Task→Review 자기 검증 (CLAUDE.md 규칙) | 쉬움 | 높음 | 클과장 |
| 2 | GitHub Issue 핸드오프 | 쉬움 | 높음 | 후추님+클과장 |
| 3 | Pipeline Step Registry | 중간 | 중간 | 제대리 |
| 4 | 불변 컨텍스트 | 어려움 | 중간 | 클과장 설계 |
| 5 | 자동 Coordinator | 어려움 | 높음 | 장기 검토 |

---

## 한 줄 결론

> Claw-Code의 진짜 교훈은 "멋진 아키텍처"가 아니라
> **"실행하고 검증하고 실패하면 멈추는 규율"**이에요.
> 이건 코드가 아니라 **팀 규칙**으로 먼저 적용하는 거고,
> 코드 구조는 그 다음이에요.

---

*Analyzed by Claude Opus 4.6 (클과장)*
*Sources: instructkr/claw-code, TickDeck codebase*
