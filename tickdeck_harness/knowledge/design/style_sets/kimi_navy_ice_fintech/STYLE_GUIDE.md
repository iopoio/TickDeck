# Kimi 네이비 아이스 핀테크 스타일 정본 (kimi_navy_ice_fintech)

> 발굴원: `knowledge/design/05_kimi_system.md` (Kimi Code-Native Layout Engine 명세 v1.0 — 32px 리듬·밀도 예산·레이아웃 사전). 명세의 판단 규칙을 스타일 세트로 변환.
> **exemplar 미보유 — 첫 실전 런에서 생성** (표지 1 + 본문 1을 이 폴더에 p_cover.html·p_body.html로 남길 것).
> 원 명세는 1920×1080 기준 — 본 세트에서는 산출물 계약의 1280×720 스테이지가 우선, px 수치는 2/3 감각으로 적용하되 32px 리듬은 유지.
> 산출물 계약·콘텐츠 계약 = senior_orange_editorial 정본 복사 (공통 규칙). 계약 안의 강조색·각주 카드 색만 본 세트 토큰으로 치환.

## 언제 쓰나

- 주제: 기업 실적·핀테크·엔터프라이즈 제안, 프로세스·타임라인·시스템 구조 설명이 많은 덱
- 청중: 기업 의사결정자·파트너사 — 정돈된 리듬과 규격에서 신뢰를 읽는 사람들
- 정서: 구조적 신뢰·차분한 질서. 파격·감성 무드가 목적이면 다른 세트 (교체 팔레트로 제한적 전환만 가능)

## 산출물 계약 (엄수)

- 파일: `pages/pXX.html` — **단독 완결 HTML** (외부 리소스 0 · CSS 인라인 `<style>` · JS 없음)
- 스테이지: `.stage` 고정 **1280×720px**, `overflow:hidden`. 콘텐츠가 720 안에 다 들어와야 함 — 넘칠 것 같으면 요소를 줄인다 (폰트 축소보다 블록 수 축소 우선)
- body: `background:#DDE1E7; display:flex; align-items:center; justify-content:center;` 가운데 스테이지 1개
- 폰트 스택: `"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif`

## 디자인 토큰

```
기본 팔레트 CORP_B2B: 60% #0A2540 (딥 네이비·큰 면) · 30% #00D4AA (민트·강조) · 10% #F6F9FC (아이스 블루·카드)
  텍스트: #FFFFFF (on navy) / #0A2540 (on ice)
교체 팔레트 (주제 따라 1개·한 덱 혼용 금지):
  CREATIVE_BRAND — #1A1A2E / #E94560 / #16213E (피칭·엔터테인먼트)
  TECH_INNOVATION — #0F172A / #38BDF8 / #1E293B (AI·개발자 도구)
  SOCIAL_IMPACT — #FFFFFF / #FF6B6B / #FFE66D (비영리·교육·ESG)
수직 리듬: 모든 top margin = 32px 배수 (마이크로 조정만 16px 허용)
타이포 clamp: hero 40~64 · h1 32~48 · h2 24~32 · body 18~24 · meta 14~18
  leading 본문 1.5 · 헤드 1.2 / font-weight 2개만 (400+700 또는 300+600)
radius: 0 / 8 / 16px+ 만 (4px 이하 금지) · 대비 WCAG AA 4.5:1 이상
불릿 마커: ● 금지 → ▸ · 01. · →
정직 각주 카드: #F6F9FC 배경 · 보더 #DCE6F2 (다크 팔레트에서는 rgba(0,212,170,.07) 배경 · 보더 rgba(0,212,170,.3))
```

## DNA 8레버 (필수 문법)

1. Main Claim 상단대 고정 — 핵심 주장을 세로 22~35% 대에 배치 (물리 중심보다 5% 상향·시선 진입점 통일)
2. 밀도 예산 — 페이지 콘텐츠 밀도 0.35~0.75 유지. 부족하면 fill(보조 그래픽·워터마크 키워드·인용 장식), 초과면 페이지 분할
3. 하단 여백 차단 — 마지막 요소~하단 여백 과다 금지: gap 축소 → 폰트 1단계 다운 → space-between → 푸터 앵커(출처·번호 그룹) 순으로 흡수
4. 시그니처 비정형 레이아웃 — DIAGONAL_SLICE(대립·전/후 사선 분할)·FLOATING_ISLAND(중심+위성)·STAGGERED_STAIR(지그재그 단계)·DEEP_LAYER(허브-스포크) — 직사각형 피로 해소용, 덱당 2~4장
5. 비대칭 30% — 전 페이지 중앙정렬 금지. 38/62·45/55 비대칭 분할이 최소 30%
6. 레이아웃 쿨다운 — 최근 3장과 같은 레이아웃 금지, 강한 레이아웃(DIAGONAL·BLEED·OVERLAP)은 4장 간격 후 재사용
7. 텍스트 색 깊이 — 한 페이지 텍스트 3색 금지. opacity 100 / 70 / 40%로 위계를 만든다
8. 이미지 위 텍스트 = scrim 의무 — gradient overlay 또는 배경 박스 없이 이미지 위 텍스트 금지

## 콘텐츠 계약 (위반 = 실격)

- **수치는 briefs/pXX.json의 metrics 값만** 사용 — value·unit·scope 그대로. 수치 발명·반올림 변경·단위 생략 금지. 쓰지 않는 metric은 생략 OK
- note의 `==키워드==`는 `<b class="hl">키워드</b>`(민트 #00D4AA)로 변환
- footnote(정직 각주)는 반드시 유지 — 옅은 배경 카드(#F6F9FC·보더 #DCE6F2, 다크 면에서는 민트 틴트)로, "ⓘ" 머리
- 출처 푸터: brief의 sources에서 그 페이지에 실제 쓴 출처 기관명만
- 문체: 명사형 종결 위주·불릿 끝 마침표 없음·이모지 0·한자 0·brief 원문 워딩 우선 (다듬기 금지 — 원문 그대로 하류 전달)

## 페이지 다양성 (단조 금지)

- 직전·직후 페이지와 같은 실루엣 금지 (레버 6이 코드화된 형태)
- 15장 기준 시그니처 비정형(레버 4) 최소 2장 — statement·전환 장이 후보
- 목차·출처·outro는 조용하게 — 장식 최소, 타이포 위주
