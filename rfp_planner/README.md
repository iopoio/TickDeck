# rfp_planner — RFP → 배점-매칭 제안 골격

공공 RFP(나라장터) 한 건을 넣으면 **평가배점표를 읽어, 배점 비중대로 분량을 배분한
제안 골격(skeleton)** 을 만든다. TickDeck "수주-제안" vertical의 0순위 층 —
"무엇을 어느 비중으로 쓸지"를 RFP 배점에서 끌어낸다.

> deck_harness / v3(레이아웃 렌더)는 **건드리지 않는다.** 이건 그 앞단 얇은 층.
> 골격 → 슬라이드 렌더 연결은 다음 단계(아래 백로그 B).

## 쓰는 법

```bash
# 라이브 공고번호로 end-to-end (검색→다운로드→추출→배점파싱→골격)
python3 rfp_pipeline.py R26BK01604184 --keyword 해외홍보관

# 이미 받은 RFP 파일로 (네트워크 불필요)
python3 rfp_pipeline.py /path/to/제안요청서.hwp
python3 rfp_pipeline.py /path/to/제안요청서.hwpx

# 셀프체크(두 배점표 양식)
python3 test_parse.py
```

data.go.kr 키 = `pepstocks/.env.local` 의 `DATAGOKR_API_KEY` 재사용.
`.hwp` 표 추출 = `Think/.venv/bin/hwp5html`.

## 지금 되는 것 (2026-06-27, 시범 검증)

- 공고번호 → 첨부 제안요청서 자동 다운로드 (나라장터 OpenAPI + g2b 첨부)
- `.hwp`(인라인 `항목(NN)`) + `.hwpx`(칼럼 `[요소][세부][NN]`) **두 양식** 배점표 파싱
- 배점 비중 → 슬라이드 분량 자동 배분
- RFP 제약(모호어 금지·제출 부수·발표평가·분량 제한) 자동 추출
- **골격 → deck_harness 셸 덱 렌더** (`skeleton_to_slides.py` → `slides.json` → build.py).
  표지 + 평가구조 개요 + 평가항목별 섹션 + 제약 클로징(7슬라이드 PDF). deck_harness 미수정.
- 검증: KOREA360(90+10·4항목) / KIAT(80+20·5항목) 2/2

## 백로그 (다음)

- **A. 일반화** — 배점표 양식 더 수집(현재 2종). 별도 배점 칼럼 변형·병합 셀.
- **B. 렌더 다듬기** ✅셸 렌더 됨 — 단 layout 단조로움(title-hero 연속). 섹션마다 다른 레이아웃 매핑.
- **C. 내용 생성** — 골격(어느 섹션 몇 장)에서 → 각 슬라이드 주장·근거·카피(축1·3). 큰 덩어리. ← 본체
- **D. 과업↔평가 cross-map** — 과업범위(가/나/다)를 평가항목 섹션에 재배치.
- **E. 해자(역분석) 연결** — 유사 과거 낙찰(누가·얼마에 땄나)을 골격에 인텔리전스로 주입.
