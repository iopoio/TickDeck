# 하이브리드 스파이크 스타일 정본 (20260727_senior_hybrid)

> 목적: designer 단계를 "spec→고정 렌더러" 대신 **페이지별 자유 HTML**로 교체하는 비용·품질 실측.
> 콘텐츠·수치는 전부 검증 완료분(briefs/*.json) — **디자인만 새로 그린다.**

## 산출물 계약 (엄수)

- 파일: `pages/pXX.html` — **단독 완결 HTML** (외부 리소스 0 · CSS 인라인 `<style>` · JS 없음)
- 스테이지: `.stage` 고정 **1280×720px**, `overflow:hidden`. 콘텐츠가 720 안에 다 들어와야 함 — 넘칠 것 같으면 요소를 줄인다 (폰트 축소보다 블록 수 축소 우선)
- body: `background:#DDE1E7; display:flex; align-items:center; justify-content:center;` 가운데 스테이지 1개
- 폰트 스택: `"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif`

## 디자인 토큰

```
--orange:#E8590C  --orange-deep:#9E3A05  (진한 강조·톤스케일 끝)
톤스케일: #FFEDE0 → #FFD9BF → #FF9E66 → #E8590C → #9E3A05  (데이터 시리즈는 이 단계로만)
--ink:#201C16  --sub:#6B665E  본문배경 --bg:#F1F3F6  카드 #FFFFFF  라인 #E4E7EC
다크 페이지 배경: radial-gradient(1100px 700px at 78% 18%, #221B12 0%, #17130E 55%, #120F0B 100%)
카드: radius 18~20px · box-shadow: 0 10~14px 26~36px rgba(32,28,22,0.08~0.09)
킥커: 대문자/자간 0.13em · 13.5px · 800 · 오렌지 · 앞에 22px 오렌지 바(::before)
페이지 푸터: 좌 "출처 — 기관명들" · 우 "© 2026 Peppinch · All rights reserved" · 12px #9A958C
페이지 번호: 우상단 "NN / 15" · 14px · 700 · #9A958C
```

## DNA 8레버 (필수 문법 — exemplar 2장이 정본, 반드시 먼저 열어볼 것: pages/p01.html · pages/p08.html)

1. 제목은 크게 — 본문 페이지 h1은 34~40px·850·자간 -0.025em·**주장문 그대로**(brief의 short_title). 핵심 구절만 `<span class="hl">`(오렌지)
2. 본문 배경 = 틴트(#F1F3F6) + **흰 카드 float** (순백 전면 금지). statement·히어로 장은 다크 풀블리드 또는 오렌지 풀블리드 허용 (덱에 1~2장만)
3. 모서리 메타 프레임 — 킥커(좌상)·페이지번호(우상)·출처(좌하)·저작권(우하)
4. 데이터 = 오렌지 톤스케일만. 비교군은 그레이(#D8DCE2 계열). 빨강·초록·파랑 금지
5. **주장 자체를 그린다** — 기성 차트 복제보다 주장이 보이는 커스텀 SVG (p08의 "공백 밴드" 스펙트럼처럼). brief의 chart 타입은 참고일 뿐, 형태는 자유
6. 시그니처 모티프: 점선 경로 + 틱 체크 (SVG, opacity 0.15~0.45, 페이지당 1~2개, 콘텐츠 뒤)
7. 요소 1개는 카드 경계를 살짝 침범(겹침) — 과하지 않게
8. 검증 칩: 수치 있는 페이지 우측/하단에 `✓ 이 페이지 수치 n/n — 출처 원문 대조` (오렌지 보더 pill, p08 참조). n = 그 페이지에 실제 표기한 registry 수치 개수

## 콘텐츠 계약 (위반 = 실격)

- **수치는 briefs/pXX.json의 metrics 값만** 사용 — value·unit·scope 그대로. 수치 발명·반올림 변경·단위 생략 금지. 쓰지 않는 metric은 생략 OK
- note의 `==키워드==`는 `<b class="hl">키워드</b>`(오렌지)로 변환
- footnote(정직 각주)는 반드시 유지 — 옅은 배경 카드(#FBF4EE·보더 #F3DCCB)로, "ⓘ" 머리
- 출처 푸터: brief의 sources에서 그 페이지에 실제 쓴 출처 기관명만
- 문체: **`references/writing-standard.md` 필독 의무** — 특히 "기계 검출 금지 표현" 절 (은유 동사·압축 명사구 금지 = hybrid_audit 게이트가 exit 1로 거름). 명사형 종결 위주·불릿 끝 마침표 없음·이모지 0·한자 0
- 수치·사실·한정어는 brief 원문 그대로 (발명·변형 금지). 단 **원문이 금지 표현을 담고 있으면 문체만 교정** — 뜻·수치·한정어 불변

## 페이지 다양성 (단조 금지)

- 직전·직후 페이지와 같은 실루엣 금지 (briefs의 layout_hint는 옛 엔진 힌트일 뿐)
- 15장 중 비정형(포스터·풀블리드 스탯·매거진 스프레드류) 최소 2장 — statement·hero_metric 장이 후보
- 목차(p02)·출처(p14)·outro(p15)는 조용하게 — 장식 최소, 타이포 위주
