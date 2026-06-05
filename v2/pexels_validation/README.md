# TickDeck v2 — Pexels 사진 "마땅함" 검증

## 목적

TickDeck 데모 PDF(M01·M08·M12)의 사진 placeholder를 무료 스톡(Pexels)으로
**마땅하게** 자동 채울 수 있는가를 정직하게 판정한다.

"Pexels 연동"이 목적이 아니다. 후추님이 WebToSlide를 접은 이유("사진이 마땅한 게
안 나와서")가 검색 정교화로 극복되는가, 아니면 재현되는가를 실물로 확인하는 게 목적.

## 구성

- `pexels_client.py` — Pexels REST 검색·다운로드 (API key는 os.environ/.env 로드, 하드코딩 X)
- `placeholders.py` — 데모 PDF의 사진 placeholder 좌표 + 검색 키워드 + 톤/비율 명세
- `build.py` — 검색 → 톤 매칭 → crop → PDF 삽입(after) + search_spec.json
- `output/search_spec.json` — 검색 메트릭 (git 추적). after PDF·캐시 이미지는 .gitignore

## 실행

```bash
# PEXELS_API_KEY는 환경변수 또는 _env_handoff/WebToSlide/.env 에서 로드
python3 build.py
```

## 검색 방식 명세

| 항목 | 방식 |
|------|------|
| 키워드 | 슬라이드 헤드라인+본문에서 핵심 명사구 추출 |
| 톤 매칭 | 슬라이드 dark/light vs Pexels avg_color 밝기(luma) 점수 0~1 |
| 비율 | 박스 비율에 맞춰 orientation 필터 + center-crop (왜곡 0) |
| 고화질 | size=large + 긴 변 2000px 이상만 채택, large2x 다운로드 |
| 정직 규칙 | 특정 인물/특정 장소(pexels_suitable=False)는 검증용으로만 채우고 ❌ 분류 |

## 결론 (정직)

상세 판정표는 `inbox/from_kogwajang/2026-06-05_TickDeck_Pexels_검증_결과.md` 참조.
요지: 연동·고화질·톤 매칭은 기술적으로 성공. 그러나 "메시지에 정확히 맞는가"
기준에서 보조/배경(인테리어 디테일·시네마틱 배경)은 마땅, 제품 특정/특정 인물/
특정 장소는 안 마땅. 후추님의 "안 마땅" 경험이 사진 의존도가 높은 슬라이드에서
재현됨. 메인 hero는 자동화 제외(후추님 수동 안목) 전제가 데이터로 뒷받침됨.
