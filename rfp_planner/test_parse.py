"""parse_scoring 셀프체크 — 두 배점표 양식을 합성 셀로 검증(실 파일 불필요).
실행: python3 test_parse.py  (또는 pytest)"""
from rfp_pipeline import parse_scoring


def test_inline():  # KOREA360형: 항목명(NN) 인라인
    cells = ["평가항목", "세부평가내용", "배점",
             "수행기관 전문성(25)", "질문", "25점",
             "사업 이해도(25)", "질문", "25점",
             "사업 수행능력(25)", "질문", "25점",
             "사업 관리방안(15)", "질문", "15점",
             "가격평가(10)", "10점", "【별지 제1호 서식】"]
    s = parse_scoring(cells)
    assert s["기술합"] == 90, s
    assert len(s["기술항목"]) == 4, s
    assert s["가격"]["배점"] == 10, s


def test_column():  # KIAT형: [요소][세부][NN] 칼럼 + 소계(NN점)
    cells = ["평가 요소", "배점", "기술능력평가(80점)",
             "1) 과업에 대한 이해도", "ㅇ 설명", "20",
             "2) 제안 기관의 역량", "ㅇ 설명", "20",
             "3) 투입 인력의 적정성", "ㅇ 설명", "10",
             "4) 수행계획의 우수성", "ㅇ 설명", "20",
             "5) 과업 관리 및 추진 능력", "ㅇ 설명", "10",
             "입찰가격평가(20점)", "ㅇ 산식", "20", "합 계", "100"]
    s = parse_scoring(cells)
    assert s["기술합"] == 80, s
    assert len(s["기술항목"]) == 5, s
    assert s["가격"]["배점"] == 20, s


if __name__ == "__main__":
    test_inline(); test_column()
    print("OK 2/2 — 인라인·칼럼 양식 통과")
