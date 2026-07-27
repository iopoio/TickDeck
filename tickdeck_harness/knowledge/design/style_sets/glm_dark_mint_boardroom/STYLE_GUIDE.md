# GLM 다크 민트 보드룸 스타일 정본 (glm_dark_mint_boardroom)

> 발굴원: `knowledge/design/00_glm_sample_deck.html` (GLM 완성 덱 16장 · 2026 마케팅 트렌드). 룩만 세트화 — 콘텐츠는 매 런 briefs에서 새로.
> 산출물 계약·콘텐츠 계약 = senior_orange_editorial 정본 복사 (공통 규칙). 계약 안의 강조색·각주 카드 색만 본 세트 토큰으로 치환.

## 언제 쓰나

- 주제: 테크·마케팅·산업 트렌드 브리핑, 스타트업 IR, 전략 컨설팅형 보고
- 청중: 어두운 회의실 스크린 발표 — 경영진·투자자·업계 세미나
- 정서: 세련·미래지향·컨설팅펌 권위. 따뜻함·친근함이 핵심인 주제(소비재 감성·시니어 대상)는 senior_orange_editorial이 낫다

## 산출물 계약 (엄수)

- 파일: `pages/pXX.html` — **단독 완결 HTML** (외부 리소스 0 · CSS 인라인 `<style>` · JS 없음)
- 스테이지: `.stage` 고정 **1280×720px**, `overflow:hidden`. 콘텐츠가 720 안에 다 들어와야 함 — 넘칠 것 같으면 요소를 줄인다 (폰트 축소보다 블록 수 축소 우선)
- body: `background:#DDE1E7; display:flex; align-items:center; justify-content:center;` 가운데 스테이지 1개
- 폰트 스택: `"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif`

## 디자인 토큰

```
--navy:#0A1626  --navy2:#0E1D30  --panel:#142436  --panel2:#1B2F48
--green:#3DD9B3 (주 강조·데이터 기본)  --green-deep:#1A7A63  --green-dim:#0F3A32
--gold:#F0C674 (1위·전환점·READ 노트)  --amber:#E9B949
--text:#EAF0F7  --muted:#7D92A8  --muted2:#5A6F86
라인: rgba(255,255,255,.08) / 강조 .14
표지·결론 배경: radial-gradient(ellipse at 70% 30%, #15324A 0%, #0A1626 55%, #060E1A 100%)
카드: linear-gradient(160deg, var(--panel), var(--navy2)) · border 1px 라인 · radius 10px
chrome 라벨: 12px · 대문자 · 자간 .18em
보조 시그널: 장기/미래 #6FB8E8 · 리스크/함정 한정 #D87070 (그 외 빨강 금지)
정직 각주 카드: rgba(240,198,116,.06) 배경 · 보더 rgba(240,198,116,.3)
```

## DNA 8레버 (필수 문법 — exemplar 2장이 정본, 반드시 먼저 열어볼 것: p_cover.html · p_body.html)

1. 풀다크 단일 무드 — 전 페이지 네이비 다크. 라이트 페이지·틴트 배경·흰 카드 금지
2. 아웃라인 메가 타이포 — `-webkit-text-stroke` 투명 대형 숫자/연도(표지 520px·디바이더 380px·카드 60px)가 시그니처. 표지 1 + 섹션 디바이더 + 결론 워터마크
3. 민트 = 데이터 기본, 골드 = 승격 — 차트 시리즈는 민트 그라디언트, 최상위 항목·전환점 1개만 골드로 승격. 두 색 동시 남발 금지
4. 섹션 디바이더 리듬 — 대형 아웃라인 숫자 + 동심원 데코, 4~6장마다 1장으로 호흡을 끊는다
5. 모서리 chrome 프레임 — 좌상 brand-dot(8px 민트 사각)+섹션 경로 · 우상 페이지 타입(CHART·TABLE·EVIDENCE…) · 우하 "NN / NN"
6. READ 노트 — 차트·표 아래 골드 좌보더 박스에 `READ · 해석 한 줄` — 주장 해석을 데이터에 붙여서 내보낸다
7. 국·영 병기 위계 — 한글 주 카피 + 영문 대문자 자간 라벨을 짝으로. 영문은 장식 위계로만 (본문 영문 금지)
8. 스탯 카드 문법 — 좌상단 4px 컬러 탭 + 대형 수치(96px·민트/골드) + 설명 + 출처 소형. 3열 그리드 기본

## 콘텐츠 계약 (위반 = 실격)

- **수치는 briefs/pXX.json의 metrics 값만** 사용 — value·unit·scope 그대로. 수치 발명·반올림 변경·단위 생략 금지. 쓰지 않는 metric은 생략 OK
- note의 `==키워드==`는 `<b class="hl">키워드</b>`(민트 #3DD9B3)로 변환
- footnote(정직 각주)는 반드시 유지 — 옅은 배경 카드(rgba(240,198,116,.06)·보더 rgba(240,198,116,.3))로, "ⓘ" 머리
- 출처 푸터: brief의 sources에서 그 페이지에 실제 쓴 출처 기관명만
- 문체: 명사형 종결 위주·불릿 끝 마침표 없음·이모지 0·한자 0·brief 원문 워딩 우선 (다듬기 금지 — 원문 그대로 하류 전달)

## 페이지 다양성 (단조 금지)

- 직전·직후 페이지와 같은 실루엣 금지
- 섹션 디바이더(레버 4)가 리듬 축 — 디바이더 사이 본문 페이지는 차트·카드·비교·표를 섞는다
- 목차·출처·outro는 조용하게 — 장식 최소, 타이포 위주
