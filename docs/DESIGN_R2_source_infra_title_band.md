# R2 설계 — TY-source_infra + PG-title_band (2026-07-07)

> 근거: PATTERN_LIBRARY §승격안 R2 · 제대리/코과장 7/6 교차 리뷰 · 실물 스키마 실측 (클차장 7/7).
> 상태: **후추님 결재 대기** — 결재 포인트 3개는 맨 아래.

## 0. 실측 전제 (리뷰 때 판단이 일부 갱신됨)

7/6 리뷰는 "source가 페이지 레벨 배열이라 스키마 확장 대공사"로 봤는데, 실물 확인 결과:

- `02_verified.json`의 **metric_registry가 이미 metric→source_ids 연결을 가짐** (`{label, value, unit, source_ids[], scope, status}`)
- 렌더러도 이미 페이지의 인용 metric에서 source를 역산해 하단 칩을 만듦 (`render_deck.py` ~505 `cited_source_ids`)
- viz series는 `metric_id`를 참조하므로 **"이 차트의 출처" = series들의 metric.source_ids 합집합**이 지금 데이터로 계산 가능

→ 결론: R2 source_infra의 본체는 스키마 신설이 아니라 **렌더러 집계 단위를 페이지→viz로 내리는 것** + optional 필드 2개. 비용 "중상"→"중하"로 하향.

## 1. TY-source_infra 설계

### 1a. 차트 단위 출처 캡션 (BOND "– 기간, per 출처")
- 렌더러가 viz 블록마다: series → metric_id → metric.source_ids 합집합 → source_registry에서 표기명 조회 → 차트 제목 아래 마이크로 캡션 자동 생성: `— {period} · per {source_short}` (출처 2개까지 나열, 3개+는 "외 N")
- **writer/designer는 출처 텍스트를 쓰지 않는다** — 전부 registry에서 렌더러가 생성 (C6 manual source label 금지와 정합·충돌 없음)
- 스키마 추가 (optional 2개·기존 run 하위호환):
  - `source_registry[].short_name` — 캡션용 짧은 표기 ("식품의약품안전처 (SNUH 미러 게시)" → "식약처"). verifier 산출 의무·없으면 publisher 앞 8자 fallback
  - `metric_registry[].period` — 값의 기간 ("1Q26"·"2018~2022"). verifier가 추출 가능할 때만·없으면 캡션에서 생략
- viz 옵션 `"source_caption": "off"` — 캡션 끌 수 있게 (밀도 높은 페이지용·기본 on은 실전 톤 시스템만)

### 1b. 페이지 하단 층 정리 (현 칩과의 관계)
- 하단 소스 칩(링크)은 유지 — 부록·클릭 가능 링크 역할. 단 차트가 이미 캡션으로 물고 있는 출처는 칩에서 **뒤로 정렬** (중복 노출 최소화·제거는 안 함: 칩=내비, 캡션=신뢰 표기로 역할 분리)
- R1의 wrap+`+N` 축약 위에서 동작 — 선결 조건 이미 충족

### 1c. 범위 밖 (R3+로 이월)
- IR식 번호 각주 1)2)3) / Activate식 데이터 성격 배지(FORECAST 등) — 관찰은 등재됨, 이번 라운드 구현 X

## 2. PG-title_band 설계

### 2a. 스펙
- deck_spec meta `"page_chrome": "title_band"` (기존 `running_head`와 동급·상호 배타. 본문 페이지만, 표지/클로징 제외)
- 밴드: 상단 전폭 솔리드(액센트 톤·시스템 토큰 위임), **높이 고정 h=12%** (720px 기준 86px), 좌정렬 흰 제목
- **간지**: 같은 크롬 유지한 채 밴드 텍스트 비움 + 중앙 스테이트먼트 (BOND 문법 — 밴드 채움/비움이 본문·간지 신호)
- 착지 2형 중 **①페이지 제목형만 이번 구현**. ②차트 제목형(Activate)은 viz 옵션 `"title_style": "band"`로 별도 소품 — R2에 포함하되 독립 커밋

### 2b. auto-fit 정책 (리뷰 미결 → 설계 확정안)
- **밴드는 auto-fit 계산에서 제외** (고정 크롬). 본문 fit 영역 = 밴드 아래 88%
- 밴드 안 제목은 자체 2단 fit: 1줄 기본 → 안 들어가면 폰트 1단 축소 후 2줄 → 그래도 넘치면 **FIT_BAND_OVERFLOW 신호** (게이트가 잡음 — R1에서 신설한 검출 패턴 재사용)
- 제목 최대 2줄 초과분은 렌더 전 contract_checks에서 글자수 상한으로 선차단 (band 폭 기준 상한 산출)

### 2c. 시스템 적용
- 기본 권장: corporate·mono (실전 리포트 톤). serif/minimal은 designer 선택 가능하되 기본 off

## 3. 계약·검증 변경
- contract_checks: `page_chrome` enum에 `title_band` 추가 · viz `source_caption`/`title_style` 옵션 검증 · short_name/period optional 필드 스키마 · 밴드 제목 글자수 상한
- 게이트: FIT_BAND_OVERFLOW 추가 (R1 FIT_SOURCE_CLIP 패턴 복제)
- 데모: title_band 본문+간지 1세트 · source_caption on 차트 페이지 1장 · 회귀 = clo_v51 재렌더 diff (기존 룩 불변 확인 — 옵션 미지정 시 변화 0이어야 함)

## 4. 구현 계획 (결재 후 코과장 배치)
1. commit 1 — 스키마+계약 (short_name·period·enum·옵션)
2. commit 2 — source_caption 렌더러 (viz 단위 집계·캡션 생성·칩 정렬)
3. commit 3 — title_band 크롬 (본문+간지+fit 정책+게이트)
4. commit 4 — viz title_style band (차트 제목형)
각 커밋 데모 spec+캡처 실증 · test 회귀 0.

## 5. 후추님 결재 포인트 3개
1. **캡션 위치**: 차트 제목 아래 마이크로 캡션 (설계안) vs BOND처럼 제목 문장 안 포함 — 안은 전자 (제목 오염 없이 계약 충돌 0)
2. **하단 칩 유지** (설계안 = 유지+뒤 정렬) vs 차트 캡션 도입 시 칩 제거 — 안은 유지 (링크 내비 가치)
3. **밴드 높이 12% 고정** (설계안) vs 제목 길이 따라 가변 — 안은 고정 (실전 문법이 고정 크롬·가변은 auto-fit과 재충돌)
