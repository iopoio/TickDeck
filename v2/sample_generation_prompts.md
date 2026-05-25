# TickDeck 시장 demand 부족 카테고리 — sample 생성 프롬프트 모음

> 후추님이 claude.design 또는 별 Claude 인스턴스에 던질 프롬프트.
> 받은 sample은 본진이 분석 → master_layout + content_slot 추출 → templates.json 등재.

---

## 공통 가이드 (모든 프롬프트에 자동 포함된 셈)

각 프롬프트에 들어간 공통 룰 (별 인스턴스가 본진 디자인-가이드 모르니까 명시):

- 한국어 텍스트
- 실제 사용 가능한 수준의 콘텐츠 (Lorem ipsum·"여기에 텍스트" 같은 placeholder 금지)
- AI 디자인 함정 회피:
  - 보라/핑크 그라디언트 배경 금지 (Stable Diffusion 톤)
  - 카드마다 이모지 도배 금지 (✨🚀💡 폭격)
  - Inter / Poppins 단독 금지 → Pretendard 또는 Pretendard + serif display 조합
  - 카드마다 그라디언트 보더 + glow 금지
  - 모든 버튼 hover scale-105 같은 애니메이션 인플레 금지
  - 8px 미만 폰트 금지
- 출력 형식: HTML 단일 파일. 인쇄 시 1 page = 1 slide (CSS `@page { size: 1280px 720px; margin: 0; }` + `.slide { page-break-after: always; }` 사용)
- 슬라이드 6~8장
- 한 deck 안에서 layout·color·typography 일관성 유지 (master + content_slot 사상)
- 받은 후 본진이 PDF로 export해서 master_layout 추출 예정

---

## 1. 이력서·포트폴리오 deck (resume_deck)

```
TickDeck라는 URL → PPTX 변환 도구의 템플릿 카테고리를 확장 중인데, "이력서/포트폴리오 deck" 카테고리 sample 1개가 필요합니다.

대상: 30대 IT 직장인이 이직·프리랜서 영업·면접 자리에서 본인 경력을 8장 안팎으로 발표하는 자료.

다음 구성으로 한국어 HTML 단일 파일 1개를 만들어 주세요. 1 page = 1 slide (1280x720), CSS @page rule 사용.

- p1: 표지 (이름·직무·연락처·간단한 한 줄 introduction)
- p2: 경력 요약 (지난 7~10년의 핵심 성과 3~4개를 timeline으로)
- p3: 대표 프로젝트 1 (역할·기여도·결과 수치)
- p4: 대표 프로젝트 2 (동일 구조)
- p5: 스킬 스택 (언어·도구·역량을 카테고리별로)
- p6: 정량 성과 (KPI 그래프·수치·전후 비교)
- p7: 가치관·일하는 방식 (3~4개 키워드 + 짧은 설명)
- p8: closing (지원 동기·연락처 재표시·간단한 CTA)

디자인 요건:
- 한국어 기본 Pretendard, 영문 강조는 serif display (예: Playfair Display, EB Garamond) 조합
- 메인 색 1개 + 보조 1개 + 그레이 스케일. 다채로운 색 X
- 모든 slide에 공통된 header/footer 영역 유지 (master layout 사상)
- 보라/핑크 그라디언트 배경 금지, 이모지 도배 금지, placeholder 텍스트 금지
- 실제 사용 가능한 수준의 콘텐츠 (가상 인물 예시 OK, 단 placeholder X)

출력: HTML 단일 파일.
```

---

## 2. 학회·세미나 발표 자료 (academic_presentation)

```
TickDeck 템플릿 카테고리 확장 중. "학회·세미나 발표 자료" 카테고리 sample 1개 필요.

대상: 대학원생·연구자·실무 발표자가 컨퍼런스·세미나에서 15~20분 분량으로 본인 연구·분석 결과 발표하는 자료.

다음 구성으로 한국어 HTML 단일 파일 1개. 1 page = 1 slide (1280x720), CSS @page rule.

- p1: 표지 (논문·발표 제목·발표자·소속·일자)
- p2: 연구 배경 (problem statement·왜 이 연구가 필요한지)
- p3: 선행 연구 review (3~5개 reference·각각 한 줄 요약)
- p4: 연구 질문·가설
- p5: 방법론 (다이어그램·flow chart 형태로)
- p6: 결과 1 (그래프 또는 표·핵심 발견)
- p7: 결과 2 (추가 분석·교차 검증)
- p8: 논의·한계·향후 연구
- p9: 결론 (3줄)
- p10: 감사·Q&A·연락처

디자인 요건:
- 학술 톤 = 진지함·여백 충분·과한 장식 X
- 한국어 Pretendard, 영문은 serif (Times New Roman 대신 EB Garamond 같은 모던 serif)
- 색은 monochrome 또는 dark navy + accent 1색 (학회 슬라이드 톤)
- 본문에 인용 출처 표기 (각주 또는 본문 안)
- 모든 slide에 공통 header (논문 제목 짧게·발표자 성·page 번호) 유지
- 그래프·표는 SVG 또는 HTML/CSS로 직접 (이미지 X)
- 보라 그라디언트·이모지 도배·placeholder 금지

출력: HTML 단일 파일.
```

---

## 3. 대학생 과제·조모임 발표 (student_assignment)

```
TickDeck 템플릿 카테고리 확장 중. "대학생 과제 발표" 카테고리 sample 1개 필요.

대상: 학부생이 수업 과제·조모임 결과 발표·중간/기말 프로젝트 발표를 10~15분 분량으로 하는 자료.

학회 자료보다 톤이 조금 가볍고, 이력서보다 캐주얼. 가독성·논리 흐름 우선.

다음 구성으로 한국어 HTML 단일 파일 1개. 1 page = 1 slide (1280x720).

- p1: 표지 (과목명·과제 제목·조원 이름·발표일)
- p2: 주제 선정 이유 (왜 이 주제인지·일상 사례 1~2개)
- p3: 조사 방법 (인터뷰·설문·문헌·관찰 등)
- p4: 핵심 발견 1
- p5: 핵심 발견 2
- p6: 핵심 발견 3
- p7: 시사점·우리 생활에의 적용
- p8: 결론·한 줄 요약·Q&A

디자인 요건:
- 친근하지만 진지한 톤. 너무 캐주얼하면 "장난" 느낌, 너무 진지하면 학회 카피
- Pretendard + 한 가지 accent 폰트 (Gowun Dodum 또는 Nanum Pen Script 같은 자연스러운 한국 폰트)
- 색 2~3개 (메인·보조·강조). 무지개 색 사용 금지
- 일러스트는 단순 SVG icon만 (Lucide 또는 Heroicons 스타일). 일러스트 image 금지
- 모든 slide에 공통 footer (과목명·조 번호·page) 유지
- 본문 글자 크기는 본인이 청중에게 발표한다 가정 → 24pt 이상
- 보라 그라디언트·이모지 도배·placeholder 금지

출력: HTML 단일 파일.
```

---

## 4. 회의 메모·기획 deck (meeting_memo)

```
TickDeck 템플릿 카테고리 확장 중. "회의 메모·기획 deck" 카테고리 sample 1개 필요.

대상: 실무자가 30분~1시간 회의에서 의사결정·진행 상황 공유·다음 단계 합의를 위해 사용하는 6장 안팎의 짧고 단단한 자료. 외부 클라이언트 자료 아닌 사내 빠른 공유용.

다음 구성으로 한국어 HTML 단일 파일 1개. 1 page = 1 slide (1280x720).

- p1: 표지 (회의 제목·일자·참석자·진행자)
- p2: 오늘 어젠다 (3~5 항목·예상 시간 분배)
- p3: 지난 회의 결정 사항 review (action items 진행 상황·완료/지연/취소)
- p4: 현재 이슈 또는 결정 필요 사항 1 (배경·옵션·추천)
- p5: 현재 이슈 2 (필요 시)
- p6: 다음 action items (담당·기한·산출물 명시)
- p7: 다음 회의 일정·closing

디자인 요건:
- 실무 톤. 화려함 금지·정보 밀도 우선
- Pretendard 단일 폰트 (display·body 같은 size 분리만)
- 색 2개만 (메인 1·강조 1). 그레이 스케일 활용
- 모든 slide 공통 header에 회의 제목 + 일자, footer에 page + 진행자
- 표·체크리스트·status badge (완료/진행중/지연) 사용
- 보라 그라디언트·이모지 도배·placeholder 금지
- "지난 회의 결정 사항" 같은 영역은 ✅⏳⚠️ 같은 기능적 아이콘 1~2개만 허용 (장식 이모지 X)

출력: HTML 단일 파일.
```

---

## 후추님 사용 흐름

1. 위 프롬프트 1~4번 중 필요한 것 선택
2. claude.design 또는 새 Claude 인스턴스에 던지기 (한 번에 1개씩)
3. 받은 HTML을 본진에 push (Think/inbox/from_huchu/ 또는 TickDeck/v2/samples_external/)
4. 본진이 PDF로 export·layout 분석·master_layout + content_slot 추출·templates.json 등재
5. 4 카테고리 완료 후 추가 카테고리 (사업계획서·강의·workshop·컨설팅 리포트 등) 다음 사이클에서 확장

## 본진 정리 사항

- 본 프롬프트는 별 Claude 인스턴스용 (claude.design 또는 일반 Claude). 본진 디자인-가이드.md 룰을 외부 인스턴스가 모르니까 핵심 함정만 명시
- master + content_slot 사상이 외부 인스턴스에는 어려우니까 "모든 slide 공통 header/footer 유지"로 풀어서 전달
- 카테고리는 시장 demand 기준 ⭐⭐⭐ 4개. 다음 sample push 후 확장 결정
