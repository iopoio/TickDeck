# Qwen 슬레이트 딥테크 스타일 정본 (qwen_slate_deeptech)

> 발굴원: `knowledge/design/04_qwen_system.md` (Qwen 디자인 시스템 명세 v1.0 — 수치 임계값 엔진). 명세의 판단 규칙을 스타일 세트로 변환.
> **exemplar 미보유 — 첫 실전 런에서 생성** (표지 1 + 본문 1을 이 폴더에 p_cover.html·p_body.html로 남길 것).
> 산출물 계약·콘텐츠 계약 = senior_orange_editorial 정본 복사 (공통 규칙). 계약 안의 강조색·각주 카드 색만 본 세트 토큰으로 치환.

## 언제 쓰나

- 주제: B2B SaaS·개발자 도구·AI 제품 소개, 기술 벤치마크·아키텍처 비교, 데이터 밀도 높은 브리핑
- 청중: 엔지니어·CTO·기술 심사역 — 수치와 구조로 설득되는 사람들
- 정서: 엔지니어링 정밀·차분한 신뢰. 감성 스토리텔링이 중심이면(브랜드 무드·소비재) 다른 세트

## 산출물 계약 (엄수)

- 파일: `pages/pXX.html` — **단독 완결 HTML** (외부 리소스 0 · CSS 인라인 `<style>` · JS 없음)
- 스테이지: `.stage` 고정 **1280×720px**, `overflow:hidden`. 콘텐츠가 720 안에 다 들어와야 함 — 넘칠 것 같으면 요소를 줄인다 (폰트 축소보다 블록 수 축소 우선)
- body: `background:#DDE1E7; display:flex; align-items:center; justify-content:center;` 가운데 스테이지 1개
- 폰트 스택: `"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif`

## 디자인 토큰 (기본 예시)

```
기본 팔레트 Deep Tech: Base #0F172A (Slate 900) · Surface #1E293B (Slate 800)
                       Primary #38BDF8 (Sky 400) · Accent #34D399 (Emerald 400)
교체 팔레트 (주제 따라 1개 선택·한 덱 혼용 금지):
  Warm Human — #FAF9F6 / #F3EFE9 / #E07A5F (Terracotta) / #3D405B (소비자·라이프스타일)
  High-Contrast Data — #000000 / #121212 / #FF3366 / #00FFCC (대규모 컨퍼런스·강한 대비)
배분: 60% Surface · 30% Base/Text · 10% Primary · +1% Semantic Alert
타이포 (Major Third): H1 48px · H2 32px · Body 20px · Caption 14px
  line-height 본문 1.5 · 제목 1.1 / 콘텐츠 최대폭 84% · 안전 여백 = 스테이지 단축 8% 이상
광학 중심: 세로 중앙 배치는 top 46.5% + translateY(-50%) (기하 50% 금지)
레이어: z0 그레인 노이즈(2%·SVG 필터) · z10 구조 그리드선(opacity .05) · z20 콘텐츠 · z30 강조 콜아웃
차트: 축 #CBD5E1 1px · 그리드 점선 opacity .3 · 막대 테두리 없음 (data-ink 원칙)
정직 각주 카드: rgba(56,189,248,.07) 배경 · 보더 rgba(56,189,248,.3)
```

## 색 체계 (교체 가능 — 브랜드·주제에 맞게 갈아 끼운다)

**패턴명**: 다크 베이스 + Primary(강조 10%) / Accent(보조 시맨틱) 이중 액센트 · 60/30/10+1 면적 배분

**유지할 것** (색을 바꿔도 이 관계는 그대로):
- 면적 배분 60% Surface · 30% Base/Text · 10% Primary · +1% Semantic Alert — Primary는 강조 10%만 (레버 4)
- 액센트 2개 역할 분리 — Primary = 하이라이트·`==키워드==` 변환색, Accent = 보조 시맨틱. 의미 없는 색 사용 금지
- Base/Surface 2단 톤스케일 — Surface가 Base보다 한 단 밝음
- 정직 각주 카드 = Primary 틴트 (rgba 배경 .07 · 보더 .3) — Primary를 바꾸면 각주 틴트도 따라간다
- 차트 저대비 규율 — 축 1px · 그리드 점선 opacity .3 · 막대 테두리 없음 (data-ink 원칙)

**위 "디자인 토큰"의 hex는 예시 기본값** — 브랜드 팔레트로 교체 가능. 대체 후보 = 토큰 블록의 교체 팔레트 2종(Warm Human·High-Contrast Data) + 추가 1종:
- Violet Research — Base #13111C · Surface #1D1930 · Primary #A78BFA · Accent #F472B6 (리서치·아카데믹 브리핑)

## DNA 8레버 (필수 문법)

1. 1페이지 1메시지 강제 — 메인 카피 + 서브 + 시각화 1개(또는 텍스트 블록 3개) 이하. 본문 45단어 초과 = 페이지 분할
2. 광학 중심 — 짧은 콘텐츠는 46.5% 광학 중심 배치, 긴 콘텐츠는 상단 고정 + flex-grow로 하단 빈 공간 흡수 (텅 빈 하단 금지)
3. 4레이어 깊이 — 그레인 노이즈 + 미세 그리드선이 배경에 항상 깔린다 (순수 플랫 금지·신뢰감 레이어)
4. 시맨틱 색 — Primary는 강조 10%만. 상태 표시는 색+모양 중첩(▲/▼ 등·색맹 안전). 의미 없는 색 사용 금지
5. 안티패턴 필터 — 불릿 3개+ = 카드 그리드로 변환 · 본문 중앙정렬 금지(왼끝 맞춤) · 텍스트 그림자 금지 · 파이 차트 금지(도넛/와플로) · 3D 효과 금지
6. 레이아웃 사전에서 선택 — Manifesto·Split(5050/비대칭)·BentoBox·Vs_Duel·Zoom_Inset·Timeline_Zigzag·Funnel·Quote_Kinetic·Iceberg_Reveal 등 조건 매칭으로. 같은 레이아웃 3연속 금지
7. 텐션-릴리즈 — 고밀도 페이지(차트·표·벤치마크) 다음엔 저밀도(Manifesto·풀블리드 인용) 강제 배치
8. 대문자 타이틀 자간 — ALL CAPS = letter-spacing .05em + weight 600 / A·V·W·Y 포함 대형 제목 = -0.02em

## 콘텐츠 계약 (위반 = 실격)

- **수치는 briefs/pXX.json의 metrics 값만** 사용 — value·unit·scope 그대로. 수치 발명·반올림 변경·단위 생략 금지. 쓰지 않는 metric은 생략 OK
- note의 `==키워드==`는 `<b class="hl">키워드</b>`(Sky #38BDF8)로 변환
- footnote(정직 각주)는 반드시 유지 — 옅은 배경 카드(rgba(56,189,248,.07)·보더 rgba(56,189,248,.3))로, "ⓘ" 머리
- 출처 푸터: brief의 sources에서 그 페이지에 실제 쓴 출처 기관명만
- 문체: 명사형 종결 위주·불릿 끝 마침표 없음·이모지 0·한자 0·brief 원문 워딩 우선 (다듬기 금지 — 원문 그대로 하류 전달)

## 페이지 다양성 (단조 금지)

- 직전·직후 페이지와 같은 실루엣 금지 (레버 6·7이 코드화된 형태)
- 15장 기준 비정형(Quote_Kinetic·Iceberg_Reveal·풀블리드 Manifesto) 최소 2장
- 목차·출처·outro는 조용하게 — 장식 최소, 타이포 위주
