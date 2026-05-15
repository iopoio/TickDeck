"""
PDF → Markdown 자동 변환 스크립트 (Layer A 자료 RAG 준비).

- 각 산업 폴더 안 *.pdf 모두 변환
- frontmatter (citation·라이선스·발행처·키워드) 자동 박지(넣지) 말고 박음
- citation map은 _meta/citations.yaml SoT 사용

사용:
    python _meta/convert_pdfs_to_md.py
    python _meta/convert_pdfs_to_md.py --force  # 기존 .md 덮어쓰기
"""

import argparse
import json
from datetime import date
from pathlib import Path

import pymupdf
import pymupdf4llm
import yaml

BASE = Path(__file__).parent.parent
CITATION_MAP = BASE / "_meta" / "citations.yaml"


def load_citations():
    if CITATION_MAP.exists():
        return yaml.safe_load(CITATION_MAP.read_text(encoding="utf-8")) or {}
    return {}


def pdf_meta(path: Path):
    """pdfinfo 메타 read."""
    try:
        doc = pymupdf.open(path)
        return {
            "title": doc.metadata.get("title") or "",
            "author": doc.metadata.get("author") or "",
            "pages": doc.page_count,
        }
    except Exception as e:
        return {"title": "", "author": "", "pages": 0, "error": str(e)}


def build_frontmatter(pdf_path: Path, citations: dict):
    """PDF 메타 + citations.yaml 합쳐 frontmatter 생성."""
    key = str(pdf_path.relative_to(BASE))
    cite = citations.get(key, {})
    meta = pdf_meta(pdf_path)

    category = pdf_path.parent.name
    title = cite.get("title") or meta.get("title") or pdf_path.stem
    publisher = cite.get("publisher") or meta.get("author") or ""
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
        "extraction_tool": "pymupdf4llm",
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
    lines.append("> ⚠️ **사용 규칙**: 본 markdown은 RAG·LLM 처리용. deck 생성 시 *요약·핵심 인용*만 사용·**전체 복사 X**. 인용 시 위 `citation_short` 출처 표기 의무.")
    lines.append("")
    return "\n".join(lines)


def convert_pdf(pdf_path: Path, citations: dict, force: bool = False):
    md_path = pdf_path.with_suffix(".md")
    if md_path.exists() and not force:
        return "skip"

    try:
        body = pymupdf4llm.to_markdown(str(pdf_path))
        fm = build_frontmatter(pdf_path, citations)
        md_path.write_text(fm + body, encoding="utf-8")
        return f"ok ({md_path.stat().st_size:,}B)"
    except Exception as e:
        return f"FAIL: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="기존 .md 덮어쓰기")
    args = parser.parse_args()

    citations = load_citations()
    pdfs = sorted(BASE.rglob("*.pdf"))

    print(f"발견 PDF: {len(pdfs)}건")
    print(f"citation_map: {len(citations)}건 등록")
    print()

    for pdf in pdfs:
        rel = pdf.relative_to(BASE)
        result = convert_pdf(pdf, citations, force=args.force)
        print(f"  [{result}] {rel}")


if __name__ == "__main__":
    main()
