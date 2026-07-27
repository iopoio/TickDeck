# 갤러리 미드나잇 브라스 스타일 정본 (gallery_midnight_brass)

> 발굴원: `knowledge/design/02_layout_gallery.html` (레이아웃 갤러리 30장 — 전 장이 딥 네이비+황동 골드 단일 룩·팔레트 슬라이드에 "Midnight Brass" 명명). 그 룩을 세트화 — 갤러리의 30개 레이아웃 사전은 이 세트의 실루엣 재고로 그대로 참조.
> 산출물 계약·콘텐츠 계약 = senior_orange_editorial 정본 복사 (공통 규칙). 계약 안의 강조색·각주 카드 색만 본 세트 토큰으로 치환.

## 언제 쓰나

- 주제: 연차 실적·경영 보고·재무/전략 리뷰, 정부·공공 제안 등 격식 있는 보고 문서
- 청중: 경영위원회·이사회·심사위원 — 권위와 정밀함을 기대하는 자리
- 정서: 묵직한 신뢰·클래식 보드룸. 트렌디·미래지향 무드가 필요하면 glm_dark_mint_boardroom

## 산출물 계약 (엄수)

- 파일: `pages/pXX.html` — **단독 완결 HTML** (외부 리소스 0 · CSS 인라인 `<style>` · JS 없음)
- 스테이지: `.stage` 고정 **1280×720px**, `overflow:hidden`. 콘텐츠가 720 안에 다 들어와야 함 — 넘칠 것 같으면 요소를 줄인다 (폰트 축소보다 블록 수 축소 우선)
- body: `background:#DDE1E7; display:flex; align-items:center; justify-content:center;` 가운데 스테이지 1개
- 폰트 스택: `"Pretendard Variable",Pretendard,-apple-system,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif`

## 디자인 토큰

```
--navy:#0B1E3D  --navy-2:#13294B  --navy-3:#1C3A66  (배경·패널·강조면 3단계)
--green:#0E2A24  --green-2:#16403A  (섹션 변주 배경·덱당 1~2장)
--gold:#C9A86A (Brass·핵심 강조)  --teal:#4FB3A9 (데이터·긍정)  --coral:#E07A5F (리스크·하락)
--paper:#E8ECEF (본문 텍스트)  --muted:#8A9BB4  --line:#2A3F63
배분: BASE 60 (네이비 3단계) · SUB 30 (페이퍼) · ACCENT 10 (골드)
표지 배경: linear-gradient(135deg,#0B1E3D,#0E2A24) + 80px 그리드선(opacity .03) + 골드 radial 데코
카드: rgba(255,255,255,.04) · border 1px #2A3F63 · 좌 4px 컬러 보더 · radius 8~12px
타이포: h1 64px/800 · h2 40px/700 · 본문 15px/1.6 · eyebrow 13px 골드 대문자 자간 .18em
페이지 프레임: 좌하 footer-bar(STRONG 페이퍼 + 설명 muted) · 우하 "NN / NN"
정직 각주 카드: rgba(201,168,106,.08) 배경 · 보더 rgba(201,168,106,.35)
```

## DNA 8레버 (필수 문법 — exemplar 2장이 정본, 반드시 먼저 열어볼 것: p_cover.html · p_body.html)

1. 네이비 3단계 깊이 — 배경·패널·강조면을 #0B1E3D→#13294B→#1C3A66 층으로 쌓는다. 순검정·순백 면 금지
2. 골드는 점(点) — eyebrow·핵심 수치·구분선에만. 큰 면적 골드 금지 (시선을 모으는 액센트 10%)
3. 시그널 3색 고정 — 골드=성취·목표·핵심 / 틸=데이터·긍정 변화 / 코랄=경고·하락. 코랄은 한 페이지 면적 5% 이하
4. eyebrow → 제목 → 시각물 위계 — 모든 본문 페이지가 골드 대문자 eyebrow + 큰 한글 제목으로 시작
5. 대형 워터마크 숫자 — 섹션 디바이더에 rgba(201,168,106,.12) 200px급 숫자를 우하단에
6. 차트는 수치 라벨 동반 — 막대·도넛·덤벨 어디든 값을 그래픽 위/옆에 직접 표기 (범례 단독 의존 금지)
7. 카드 = 유리판 — rgba(255,255,255,.04) + 1px 라인 + 좌 4px 컬러 보더. 그림자 과장 금지
8. 섹션 변주 = 딥그린 — 흐름 환기가 필요한 1~2장만 딥그린(#0E2A24) 배경으로 전환 (Forest Quartz 변주)

## 콘텐츠 계약 (위반 = 실격)

- **수치는 briefs/pXX.json의 metrics 값만** 사용 — value·unit·scope 그대로. 수치 발명·반올림 변경·단위 생략 금지. 쓰지 않는 metric은 생략 OK
- note의 `==키워드==`는 `<b class="hl">키워드</b>`(골드 #C9A86A)로 변환
- footnote(정직 각주)는 반드시 유지 — 옅은 배경 카드(rgba(201,168,106,.08)·보더 rgba(201,168,106,.35))로, "ⓘ" 머리
- 출처 푸터: brief의 sources에서 그 페이지에 실제 쓴 출처 기관명만
- 문체: 명사형 종결 위주·불릿 끝 마침표 없음·이모지 0·한자 0·brief 원문 워딩 우선 (다듬기 금지 — 원문 그대로 하류 전달)

## 페이지 다양성 (단조 금지)

- 직전·직후 페이지와 같은 실루엣 금지 — 실루엣 재고는 발굴원 갤러리 30종(단일 KPI·수평/수직 막대·전후 비교·타임라인·퍼널·사분면·히트맵·덤벨·도넛·불릿·트리맵…)에서 고른다
- 15장 기준 비정형(인용 선언·풀블리드 KPI·딥그린 변주 장) 최소 2장
- 목차·출처·outro는 조용하게 — 장식 최소, 타이포 위주
