#!/usr/bin/env python3
"""Collect final external review for a rendered TickDeck deck."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


LENSES = [
    "논리 비약·근거-주장 불일치",
    "어색한 한국어·제목/부제 관계·흐름 단절",
    "차트-주장 일치",
    "독자 가치",
]
CODEX_REVIEW_FILE = "review_codex.txt"
GEMINI_REVIEW_FILE = "review_gemini.txt"
REVIEW_JSON_FILE = "08_external_review.json"
GEMINI_WRAPPER = Path("/Users/hwa/Projects/Automation/Think/.claude/scripts/gemini_call_wrapper.py")
GEMINI_PYTHON = Path("/Users/hwa/Projects/Automation/Think/.venv/bin/python")


class _DeckPageTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.pages: list[dict[str, Any]] = []
        self._current: dict[str, Any] | None = None
        self._section_depth = 0
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1
            return

        attr_map = {key: value or "" for key, value in attrs}
        if tag == "section" and "data-page-id" in attr_map:
            if self._current is not None:
                self._finish_current()
            self._current = {"page_id": attr_map["data-page-id"], "chunks": []}
            self._section_depth = 1
            return

        if self._current is not None and tag == "section":
            self._section_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1
            return

        if self._current is not None and tag == "section":
            self._section_depth -= 1
            if self._section_depth <= 0:
                self._finish_current()

    def handle_data(self, data: str) -> None:
        if self._ignored_depth or self._current is None:
            return
        text = " ".join(data.split())
        if text:
            self._current["chunks"].append(text)

    def close(self) -> None:
        super().close()
        if self._current is not None:
            self._finish_current()

    def _finish_current(self) -> None:
        assert self._current is not None
        text = " ".join(self._current["chunks"]).strip()
        self.pages.append({"page_id": self._current["page_id"], "text": text})
        self._current = None
        self._section_depth = 0


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._ignored_depth:
            return
        text = " ".join(data.split())
        if text:
            self.chunks.append(text)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_page_texts(deck_html: Path) -> list[dict[str, str]]:
    html = deck_html.read_text(encoding="utf-8")
    parser = _DeckPageTextParser()
    parser.feed(html)
    parser.close()
    pages = [
        {"page_id": str(page["page_id"]), "text": str(page["text"])}
        for page in parser.pages
    ]
    if pages:
        return pages

    fallback = _VisibleTextParser()
    fallback.feed(html)
    fallback.close()
    return [{"page_id": "document", "text": " ".join(fallback.chunks).strip()}]


def build_review_prompt(pages: list[dict[str, str]]) -> str:
    page_lines = []
    for index, page in enumerate(pages, start=1):
        text = page["text"] or "(텍스트 없음)"
        page_lines.append(f"페이지 {index} ({page['page_id']}):\n{text}")

    return "\n\n".join(
        [
            "너는 TickDeck 최종 외부 리뷰어다. 칭찬하지 말고, 전달 직전 덱의 결함만 냉정하게 찾는다.",
            "아래 4개 렌즈를 각각 적용해서 지적하라.",
            "1. 논리 비약·근거-주장 불일치: 근거가 주장까지 못 가거나 비교 기준이 빠진 곳.",
            "2. 어색한 한국어·제목/부제 관계·흐름 단절: 제목과 부제가 따로 놀거나 페이지 사이 전환이 끊기는 곳.",
            "3. 차트-주장 일치: 본문 주장(예: '중가')과 수치·비교 기준이 화면의 차트/표/문장과 어긋나는 곳.",
            "4. 독자 가치: 뭉뚱그림·겉핥기. 독자가 참고할 실체(비교·사례·성과 신호)가 없는데 있는 척하는 페이지.",
            "출력 규칙: 페이지 번호를 반드시 명시한다. 최대 12건만 쓴다. 칭찬 금지. 결함이 없으면 정확히 '없음'이라고만 쓴다.",
            "형식: N. [렌즈] 페이지 번호 — 문제 / 왜 문제인지 / 고칠 방향",
            "[덱 텍스트]",
            "\n\n".join(page_lines),
        ]
    )


def run_reviewer(command: list[str], output_path: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=output_path.parent,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        output_path.write_text(f"REVIEWER_FAILED_TO_START\n{exc}\n", encoding="utf-8")
        return {"ok": False, "file": output_path.name, "error": str(exc)}

    parts = []
    if completed.stdout:
        parts.append(completed.stdout.rstrip())
    if completed.stderr:
        parts.append("[stderr]\n" + completed.stderr.rstrip())
    if not parts:
        parts.append(f"(no output; exit={completed.returncode})")
    output_path.write_text("\n\n".join(parts) + "\n", encoding="utf-8")

    result: dict[str, Any] = {"ok": completed.returncode == 0, "file": output_path.name}
    if completed.returncode != 0:
        result["error"] = f"exit {completed.returncode}"
    return result


def write_review_json(run_dir: Path, deck_hash: str, codex: dict[str, Any], gemini: dict[str, Any]) -> Path:
    payload = {
        "deck_html_sha256": deck_hash,
        "reviewed_at_kst": datetime.now(ZoneInfo("Asia/Seoul")).isoformat(timespec="seconds"),
        "codex": codex,
        "gemini": gemini,
        "lenses": LENSES,
    }
    output_path = run_dir / REVIEW_JSON_FILE
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run final codex/gemini external review for a TickDeck run.")
    parser.add_argument("run_dir", help="Run directory containing deck.html, for example _workspace/20260705_clo_market")
    parser.add_argument("--dry-run", action="store_true", help="Build prompt and write 08 JSON without calling LLMs.")
    args = parser.parse_args(argv)

    run_dir = Path(args.run_dir)
    if not run_dir.is_dir():
        print(f"NO_RUN_DIR: {run_dir}", file=sys.stderr)
        return 2
    deck_html = run_dir / "deck.html"
    if not deck_html.exists():
        print(f"NO_DECK_HTML: {deck_html}", file=sys.stderr)
        return 2

    deck_hash = sha256_file(deck_html)
    prompt = build_review_prompt(extract_page_texts(deck_html))

    codex_file = run_dir / CODEX_REVIEW_FILE
    gemini_file = run_dir / GEMINI_REVIEW_FILE
    if args.dry_run:
        codex = {"ok": False, "file": codex_file.name, "error": "dry-run skipped"}
        gemini = {"ok": False, "file": gemini_file.name, "error": "dry-run skipped"}
    else:
        codex = run_reviewer(["codex", "exec", "--skip-git-repo-check", prompt], codex_file)
        gemini = run_reviewer([str(GEMINI_PYTHON), str(GEMINI_WRAPPER), "--prompt", prompt, "--no-cache"], gemini_file)

    json_path = write_review_json(run_dir, deck_hash, codex, gemini)

    print(f"deck_html_sha256: {deck_hash}")
    print(f"prompt_pages: {len(extract_page_texts(deck_html))}")
    print(f"codex: {'ok' if codex.get('ok') else 'fail'} -> {codex_file}")
    print(f"gemini: {'ok' if gemini.get('ok') else 'fail'} -> {gemini_file}")
    print(f"json: {json_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
