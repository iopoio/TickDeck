#!/usr/bin/env python3
"""실전 PDF 리포트(컨설팅·투자사) → inbox 아이템 변환.

사용: python3 pdf_intake.py <PDF_URL> <슬러그> <style_family>
예:   python3 pdf_intake.py https://.../report.pdf bond_trends_ai_2025 data_dashboard

결과: inbox/pdf_<슬러그>/{000.jpg.., source.pdf, meta.txt}
meta.txt의 name·sub_tags는 생성 후 손으로 채운다 (실측 보고 태깅).
"""
import datetime
import pathlib
import subprocess
import sys

INBOX = pathlib.Path(__file__).parent / "inbox"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    url, slug, family = sys.argv[1:4]
    d = INBOX / f"pdf_{slug}"
    if d.exists():
        sys.exit(f"이미 있음: {d}")
    d.mkdir(parents=True)
    pdf = d / "source.pdf"
    subprocess.run(
        ["curl", "-sL", "-A", "Mozilla/5.0", "--max-time", "300", "-o", str(pdf), url],
        check=True,
    )
    if pdf.read_bytes()[:5] != b"%PDF-":
        # ponytail: 게이트(이메일월·Drive 보기전용)는 자동 우회 안 함 — 사람이 다른 소스 찾기
        pdf.unlink()
        d.rmdir()
        sys.exit(f"PDF 아님 (다운로드 게이트에 막힘): {url}")
    subprocess.run(
        ["pdftoppm", "-jpeg", "-r", "120", "-jpegopt", "quality=85", str(pdf), str(d / "page")],
        check=True,
    )
    for i, f in enumerate(sorted(d.glob("page-*.jpg"))):
        f.rename(d / f"{i:03d}.jpg")
    n = len(list(d.glob("[0-9]*.jpg")))
    (d / "meta.txt").write_text(
        f"""url: {url}
name: {slug} (TODO: 정식 제목으로)
source: 기타(pdf_report)
style_family: {family}
sub_tags: 실전덱, 원본PDF포함
mosaic: no
collected: {datetime.date.today()}
""",
        encoding="utf-8",
    )
    print(f"{d.name}: {n}페이지 완료 — meta.txt name·sub_tags 채울 것")


if __name__ == "__main__":
    main()
