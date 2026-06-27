#!/usr/bin/env python3
"""소스 ingestion — PDF → 텍스트. pdftotext 우선, 이미지 PDF는 tesseract OCR 폴백.

아무 PDF나 던지면 dig_agent로 흘려보낼 텍스트가 나오게(앞 절반 입구).
OCR = research_base/_meta/ocr_pdfs_to_md.py 방식 재사용(pdf2image + tesseract kor+eng).
용법: python dig_source.py <pdf> [out.txt]   (인자 없으면 self-check)
"""
from __future__ import annotations
import subprocess, shutil


def _needs_ocr(text, min_chars):
    return len(text.strip()) < min_chars


def to_text(pdf_path, min_chars=400, dpi=200, max_pages=None):
    """PDF → (텍스트, 방법). pdftotext 결과가 min_chars 미만(=이미지 PDF)이면 OCR 폴백."""
    text = ""
    if shutil.which("pdftotext"):
        r = subprocess.run(["pdftotext", "-layout", str(pdf_path), "-"], capture_output=True, text=True)
        text = r.stdout or ""
    if not _needs_ocr(text, min_chars):
        return text, "pdftotext"
    # 이미지 PDF → OCR (느림: 페이지당 1~3초)
    from pdf2image import convert_from_path
    import pytesseract
    images = convert_from_path(str(pdf_path), dpi=dpi)
    if max_pages:
        images = images[:max_pages]
    text = "\n\n".join(pytesseract.image_to_string(im, lang="kor+eng") for im in images)
    return text, f"ocr({len(images)}p)"


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        txt, how = to_text(sys.argv[1])
        print(f"[{how}] {len(txt)}자")
        if len(sys.argv) > 2:
            open(sys.argv[2], "w", encoding="utf-8").write(txt)
            print(f"→ {sys.argv[2]}")
    else:
        assert _needs_ocr("x" * 10, 400) and not _needs_ocr("x" * 500, 400)
        print("dig_source OK — OCR 폴백 판정 로직")
