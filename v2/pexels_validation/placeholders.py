"""TickDeck 데모 PDF의 사진 placeholder 정의 + 검색 키워드 명세.

좌표 단위 = PDF point (페이지 960x540pt 기준). PyMuPDF get_drawings()로 추출한
실제 박스 좌표를 사용. rect = (x0, y0, x1, y1).

각 placeholder는 슬라이드 헤드라인/본문에서 추출한 키워드로 검색.
tone: dark|light → Pexels avg_color 밝기로 톤 매칭.
orient: landscape|portrait → 박스 비율에 맞춤.

pexels_suitable=False 인 항목은 "Pexels 스톡으로 마땅하게 채울 수 없는" 종류
(특정 인물 컨셉포토·특정 장소 위성지도). 정직 판정의 핵심 — 억지로 채우지 않음.
"""

# rect: (x0, y0, x1, y1) in PDF points
PLACEHOLDERS = [
    # ===== M01 자동차 이벤트 제안 =====
    {
        "deck": "M01", "page": 1, "slot": "S01_cover_dark",
        "rect": (0, 60, 960, 480), "tone": "dark", "orient": "landscape",
        "role": "hero",  # 후추님 수동 영역 → 자동화 제외
        "pexels_suitable": None,  # hero, 평가 대상 아님
        "query": None,
        "note": "메인 hero 비주얼. 후추님 수동 안목 영역 → 자동화 제외(시동 메모 2-금지).",
    },
    {
        "deck": "M01", "page": 3, "slot": "S03_map_route_satellite",
        "rect": (60, 150, 900, 480), "tone": "dark", "orient": "landscape",
        "role": "section_map",
        "pexels_suitable": False,  # 특정 행사장 위성지도 → 스톡 불가
        "query": "aerial city map satellite view night",
        "note": "행사장 도착 경로 위성지도. 스톡 항공사진은 '그 장소'가 아님 → 마땅 불가 예상. 검증용으로만 채워봄.",
    },
    # ===== M08 자동차 브로슈어 (가장 사진 친화) =====
    {
        "deck": "M08", "page": 1, "slot": "S23_lifestyle_cover_photo",
        "rect": (0, 48, 960, 478), "tone": "light", "orient": "landscape",
        "role": "cover_background",
        "pexels_suitable": True,
        "query": "luxury car lifestyle elegant studio neutral background",
        "note": "표지 라이프스타일 배경 사진. 보조/배경(hero 아님) → 자동화 대상.",
    },
    {
        "deck": "M08", "page": 3, "slot": "S24_seat_photo_left",
        "rect": (212, 114, 548, 391), "tone": "dark", "orient": "landscape",
        "role": "product_detail",
        "pexels_suitable": True,
        "query": "carbon fiber bucket racing car seat dark studio",
        "note": "R8 비전 시트 사진 (좌). 헤드라인 '원심력에 맞선다'·풀카본 시트.",
    },
    {
        "deck": "M08", "page": 3, "slot": "S24_seat_photo_right",
        "rect": (484, 140, 795, 402), "tone": "dark", "orient": "landscape",
        "role": "product_detail",
        "pexels_suitable": True,
        "query": "car sport seat detail leather dark",
        "note": "R8 비전 시트 사진 (우).",
    },
    {
        "deck": "M08", "page": 5, "slot": "S23_automotive_lifestyle_spread",
        "rect": (480, 0, 960, 540), "tone": "dark", "orient": "portrait",
        "role": "lifestyle_spread",
        "pexels_suitable": True,
        "query": "luxury sedan driving night city cinematic dark",
        "note": "우측 전면 라이프스타일 스프레드. 헤드라인 'Refined motion, quiet confidence'.",
    },
    {
        "deck": "M08", "page": 6, "slot": "S27_interior_detail_dark",
        "rect": (441, 51, 999, 483), "tone": "dark", "orient": "landscape",
        "role": "interior_detail",
        "pexels_suitable": True,
        "query": "luxury car interior detail ambient led dark leather",
        "note": "인테리어 디테일. 헤드라인 'Where every touch becomes intention'·앰비언트 LED.",
    },
    # ===== M12 음악 앨범 컨셉포토 =====
    {
        "deck": "M12", "page": 4, "slot": "S08_member_polaroid_grid",
        "rect": (200, 70, 384, 359), "tone": "dark", "orient": "portrait",
        "role": "member_concept_photo",
        "pexels_suitable": False,  # 특정 아이돌 멤버 컨셉포토 → 스톡 절대 불가
        "query": "moody portrait young person red light cinematic",
        "note": "TXT 멤버(MESS/SOOBIN/YEONJUN) 폴라로이드. 특정 실존 인물 → 스톡 대체 불가. 검증용으로만 무드 포트레이트 시도.",
    },
]


def for_deck(deck: str):
    return [p for p in PLACEHOLDERS if p["deck"] == deck]
