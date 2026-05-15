"""
이미지 기반 PDF (PPT 캡처·스캔 등) OCR → Markdown.

타깃: 변환된 .md가 텍스트 거의 X (≤15KB) 자료. tesseract kor+eng 사용.
사용:
    python _meta/ocr_pdfs_to_md.py <pdf path>
    python _meta/ocr_pdfs_to_md.py --auto  # md 크기 ≤15KB 자료 자동
"""

import argparse
import json
import tempfile
from datetime import date
from pathlib import Path

import pymupdf
import pytesseract
import yaml
from pdf2image import convert_from_path

BASE = Path(__file__).parent.parent
CITATION_MAP = BASE / "_meta" / "citations.yaml"
SIZE_THRESHOLD = 15_000  # 15KB 미만 .md = OCR 후보


def load_citations():
    if CITATION_MAP.exists():
        return yaml.safe_load(CITATION_MAP.read_text(encoding="utf-8")) or {}
    return {}


def pdf_meta(path: Path):
    try:
        doc = pymupdf.open(path)
        return {"pages": doc.page_count}
    except Exception as e:
        return {"pages": 0, "error": str(e)}


def build_frontmatter(pdf_path: Path, citations: dict):
    key = str(pdf_path.relative_to(BASE))
    cite = citations.get(key, {})
    meta = pdf_meta(pdf_path)
    category = pdf_path.parent.name
    title = cite.get("title") or pdf_path.stem
    publisher = cite.get("publisher") or ""
    pub_date = cite.get("publication_date") or ""
    keywords = cite.get("keywords") or []
    license_text = cite.get("license") or "공개 자료 · 인용·요약·출처 명시 OK · 전체 복사 X"
    citation_short = cite.get("citation_short") or f"{publisher} ({pub_date}). {title}."

    fm = {
        "title": title,
        "publisher": publisher,
        "publication_date": str(pub_date),
        "source_file": pdf_path.name,
        "category": category,
        "pages": meta.get("pages", 0),
        "keywords": keywords,
        "license": license_text,
        "citation_short": citation_short,
        "extracted_at": str(date.today()),
        "extraction_tool": "tesseract OCR (kor+eng) via pytesseract",
    }
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            value_str = str(v).replace('"', '\\"')
            lines.append(f'{k}: "{value_str}"')
    lines.append("---")
    lines.append("")
    lines.append("> ⚠️ **사용 규칙**: 본 markdown은 OCR 추출본 (이미지 기반 PDF). 텍스트 오류 가능. deck 생성 시 *요약·핵심 인용*만 사용·**전체 복사 X**. 인용 시 위 `citation_short` 출처 표기 의무.")
    lines.append("")
    return "\n".join(lines)


def ocr_pdf(pdf_path: Path, dpi: int = 200) -> str:
    """PDF 각 페이지 → PNG → tesseract OCR → markdown 합치기."""
    pages_text = []
    with tempfile.TemporaryDirectory() as tmpdir:
        images = convert_from_path(str(pdf_path), dpi=dpi, output_folder=tmpdir)
        for i, img in enumerate(images, 1):
            text = pytesseract.image_to_string(img, lang="kor+eng")
            text = text.strip()
            if text:
                pages_text.append(f"## 페이지 {i}\n\n{text}\n")
    return "\n---\n\n".join(pages_text)


def process(pdf_path: Path, citations: dict, force: bool = False) -> str:
    md_path = pdf_path.with_suffix(".md")
    if md_path.exists() and md_path.stat().st_size > SIZE_THRESHOLD and not force:
        return f"skip (md 이미 {md_path.stat().st_size:,}B)"
    try:
        body = ocr_pdf(pdf_path)
        fm = build_frontmatter(pdf_path, citations)
        md_path.write_text(fm + body, encoding="utf-8")
        return f"ok ({md_path.stat().st_size:,}B · {len(body.split()):,} 단어)"
    except Exception as e:
        return f"FAIL: {e}"


def find_ocr_candidates() -> list[Path]:
    """변환된 .md 크기 ≤15KB 자료 = OCR 후보."""
    candidates = []
    for md in BASE.rglob("*.md"):
        if md.name == "README.md":
            continue
        if md.stat().st_size <= SIZE_THRESHOLD:
            pdf = md.with_suffix(".pdf")
            if pdf.exists():
                candidates.append(pdf)
    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?", help="단일 PDF 경로 (생략 시 --auto 필요)")
    parser.add_argument("--auto", action="store_true", help="md ≤15KB 후보 자동 처리")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    citations = load_citations()

    if args.auto:
        targets = find_ocr_candidates()
        print(f"OCR 후보: {len(targets)}건")
    elif args.pdf:
        targets = [Path(args.pdf)]
    else:
        parser.error("PDF 경로 또는 --auto 필요")

    for pdf in targets:
        rel = pdf.relative_to(BASE) if pdf.is_absolute() else pdf
        print(f"  처리 시작: {rel}")
        result = process(pdf, citations, force=args.force)
        print(f"  [{result}] {rel}")


if __name__ == "__main__":
    main()
