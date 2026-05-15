# TickDeck v2 Research Base (Layer A)

> 사전 학습 자료 base. Gamma·Beautiful.ai가 못 하는 *고급 데이터 layer* — 사용자 input 받기 전에 이미 깔려 있어야 함.

## 사상 (5/15 후추님 인사이트)

Gamma = 사용자 input → LLM 즉답 (1 step·base 자료 X).

TickDeck v2 = **4 step**:
1. Layer A = 2026 트렌드·산업별 pre-built knowledge base (본 폴더)
2. Layer B = 사용자 input 받음
3. Layer C = A ↔ B cross-check·gap 찾기·능동 컨설팅 (KPMG·BCG 컨설턴트 역할)
4. Layer D = A + B + C 합쳐 enriched deck (자동 인용·출처 표시)

= base 자체가 차별. Gamma 영어권 점령자도 한국 컨설팅 데이터 layer 흉내 X.

## 폴더 구조

```
research_base/
├── README.md           # 본 파일
├── _meta/              # 출처 매핑·라이선스·갱신 plan
│   ├── SOURCES.md
│   ├── LICENSE.md
│   └── UPDATE_PLAN.md
├── _공통/              # cross-industry (매크로·CEO survey·ARK Big Ideas·CES)
├── 01_AI_반도체/        # 생성 AI·LLM·NPU·반도체
├── 02_이차전지_EV/      # 배터리·전기차·충전 인프라
├── 03_바이오_헬스/      # 디지털 헬스·면역치료·신약
├── 04_핀테크_금융IT/    # 디지털 금융·증권·은행 IT
├── 05_SaaS_B2B/        # B2B 소프트웨어·기업용
├── 06_소비재/           # 식음료·뷰티·라이프스타일
├── 07_콘텐츠_엔터/      # K-콘텐츠·게임·OTT
├── 08_모빌리티/         # 자율주행·로보틱스·UAM
├── 09_부동산_PropTech/  # PropTech·건설
└── 10_ESG_기후/         # ESG·기후·녹색 금융
```

## 산업별 폴더 안 표준 구조

```
0X_<산업>/
├── README.md           # 자료 inventory·갱신일·핵심 키워드
├── pdfs/               # PDF 원본 (5MB 미만)
├── pdfs_oversize/      # PDF 원본 (5MB 이상·git lfs 또는 외부 저장)
├── summaries/          # 요약 markdown (LLM-readable)
│   └── <자료>_summary.md
└── metadata.json       # 자료 메타 (출처·발행일·태그·인용 가능 영역)
```

## 자료 신뢰도 등급 (5/13 정합)

- 🟢 1차 = 컨설팅펌 공개 Outlook·증권사 리서치센터·정부 통계 (KOSIS·OECD·통계청)
- 🟡 2차 = 언론 종합·산업 협회·민간 리서치
- 🔴 X = 블로그·SNS·출처 불명·paywall 내부 자료

## 라이선스 룰 (5/13 메모리 정합·5/15 재확인)

- ✅ 공개 발표 자료·정부 자유 자료·후추님 137개 본인 저작권
- ❌ paywall·내부 컨설팅 자료·전체 복사
- 인용·요약·출처 명시 OK

자세한 룰 = `_meta/LICENSE.md`.

## 갱신 빈도

- 분기 (3·6·9·12월) = 컨설팅펌 Outlook·증권사 산업 전망
- 반기 = 정부 통계·산업 협회 보고서
- 연 1회 = ARK Big Ideas·CES Outlook

자세한 plan = `_meta/UPDATE_PLAN.md`.

## 5/15 시점 보유 자료 현황

후추님 5/13 노클 송부 PDF 136개 (2.4GB) 중 **03_리서치_리포트 34건 (618MB)** = Layer A 후보.

산업 매핑 (gap 분석):

| 산업 | 등급 | 비고 |
|---|---|---|
| 01 AI·반도체 | 🟢 충분 | 삼정KPMG AI에이전트·2026 Agentic·state-of-ai·ARK |
| 02 이차전지·EV | 🔴 갱신 필요 | 자동차산업 전망 (2019)·hmc sustainability (2019) |
| 03 바이오·헬스 | 🟢 충분 | KPMG AI Healthcare·웰리스헬스케어·마크로젠·저출생 |
| 04 핀테크·금융IT | 🟡 추가 권장 | kr_2025fsi·CEO survey·하나금융 일반산업 |
| 05 SaaS·B2B | 🟡 추가 권장 | Publace AI Space·이커머스 AI |
| 06 소비재 | 🔴 신규 | 없음 |
| 07 콘텐츠·엔터 | 🟡 갱신 권장 | KPMG 게임 트렌드·문화예술 (2019) |
| 08 모빌리티 | 🔴 갱신 필요 | 자동차 자료 2019 |
| 09 부동산·PropTech | 🔴 신규 | 없음 |
| 10 ESG·기후 | 🔴 갱신 필요 | hmc sustainability (2019) |

## 자료 매핑 진행 작업

1. 후추님 보유 34건 → 산업별 폴더 이관 (본진 자동·5/15)
2. 신규 자료 5영역 (이차전지·소비재·PropTech·ESG·핀테크 추가) → 후추님 수집 (병렬)
3. 본진 분기 자동 갱신 = Researcher agent 호출 (v1 3에이전트 영역 1번 강화)

## 출처

- 후추님 5/15 발화·차별 재정의
- 5/13 메모리 `project_tickdeck.md` v2 (5/12 재시작·5/13 wedge 재정의·5/14 자율 가이드)
- 노클 5/13 PDF 송부 (`Think/inbox/from_nokl/2026-05-13_1528_TickDeck_v2_PDF_송부_결과.md`)
