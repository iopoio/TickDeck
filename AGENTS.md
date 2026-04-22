# TickDeck (WebToSlide) 에이전트 공통 규칙

## 등급: 스몰

## 프로젝트 개요
- TickDeck / WebToSlide 프로젝트
- 서버: ssh root@146.190.95.11
- 배포: git push → 자동 배포 (systemctl restart tickdeck tickdeck-worker)

## 조직
- 후추님(CEO) → 방향/결정
- 클과장(Claude) → 시스템 설계/아키텍처/코드 리뷰 총괄
- 제대리(Gemini) → 구현/대규모 리팩토링/코딩 작업
- 양념이(텔레그램 봇) → 수집/검증 (Think 전용)

## 공통 규칙
- 호칭: "후추님" (팀장님/사용자님 금지)
- 한국어 우선. 볼드체(**) 금지, 강조는 이모지로.
- 핸드오프 시 "무엇을 바꿨고 왜 바꿨는지" 2~3줄 요약 필수
- 시간은 KST 기준
- 보안: .env/토큰/키 절대 커밋 금지

## 이 프로젝트만의 규칙
- 거짓 보고 절대 금지 — "모름/못함/확인 안 함"은 그대로 말할 것. 추측이면 "추측" 명시
- 검증 의무: "테스트 통과" → pass/fail/skip 수치 필수. 수치 없으면 거짓으로 간주
- 작업 권한 3단계: allow(단독)/ask(확인 후)/deny(절대 금지). 판단 애매하면 ask
- 배포 전 Playwright 테스트 권장: `npx playwright test`
- 무한루프 방지: 같은 에러 2회 연속 → 멈추고 보고. 같은 파일 3회 이상 수정 → 재검토
- Sprint Contract: 작업 전 pass/fail 기준 사전 명시
- 자기평가 분리: 클과장이 작성한 코드 → 본인 검토 금지. 제대리 또는 후추님 리뷰
- 컨텍스트 70% 또는 20턴 이상 → 새 대화로. 다음 단계는 파일(walkthrough.md)로 핸드오프

## 현재 할 일
- (ROADMAP.md 및 GitHub Issue 확인)

## 참고
- 글로벌 규칙: ~/.claude/CLAUDE.md
- 프로젝트 셋업 가이드: Think/system/프로젝트_셋업_가이드.md
