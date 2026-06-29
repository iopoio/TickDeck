from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


# Add one-off translationese or cliche patterns here.
REGEX_BLACKLIST: list[tuple[str, str]] = [
    ("월요일_미국식클리셰", r"월요일에\s*시작(?:할|하는|하기|한다|합니다)?"),
    ("monday_morning_cliche", r"Monday\s+morning(?:\s+actions?)?"),
    ("게임체인저_클리셰", r"게임\s*체인저"),
    ("다름아니다_직역투", r"에\s*다름\s*아니다"),
    ("이중수동_되어진다", r"되어진다"),
    ("이중수동_지게된다", r"지게\s*된다"),
    ("라는사실_직역투", r"라는\s*사실"),
    ("당신의_직역투", r"당신의"),
    ("무의미비유_반대편", r"(?:격차|간극|차이|갭)의\s*반대편"),
]

# Add file-level overuse patterns here. A violation is reported only when
# total matches exceed max_allowed; all matches are printed to help editing.
COUNT_BLACKLIST: list[tuple[str, str, int]] = [
    ("통해_8회초과", r"[0-9A-Za-z가-힣_]+[을를]\s*통해", 8),
]


@dataclass(frozen=True)
class NaturalnessViolation:
    line_number: int
    phrase: str
    pattern_name: str
    path: Path | None = None

    def format(self) -> str:
        location = str(self.path) if self.path else "<text>"
        return f"{location}:{self.line_number}: {self.pattern_name}: {self.phrase}"


def find_violations(text: str, path: Path | None = None) -> list[NaturalnessViolation]:
    violations: list[NaturalnessViolation] = []
    lines = text.splitlines()

    for line_number, line in enumerate(lines, start=1):
        for pattern_name, pattern in REGEX_BLACKLIST:
            for match in re.finditer(pattern, line, flags=re.IGNORECASE):
                violations.append(
                    NaturalnessViolation(
                        line_number=line_number,
                        phrase=match.group(0),
                        pattern_name=pattern_name,
                        path=path,
                    )
                )

    for pattern_name, pattern, max_allowed in COUNT_BLACKLIST:
        matches: list[NaturalnessViolation] = []
        for line_number, line in enumerate(lines, start=1):
            for match in re.finditer(pattern, line, flags=re.IGNORECASE):
                matches.append(
                    NaturalnessViolation(
                        line_number=line_number,
                        phrase=match.group(0),
                        pattern_name=pattern_name,
                        path=path,
                    )
                )
        if len(matches) > max_allowed:
            violations.extend(matches)

    return sorted(violations, key=lambda item: (item.line_number, item.pattern_name, item.phrase))


def scan_file(path: Path) -> list[NaturalnessViolation]:
    return find_violations(path.read_text(encoding="utf-8"), path=path)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan markdown files for Korean translationese and borrowed cliches.")
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown file path(s) to scan.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    all_violations: list[NaturalnessViolation] = []

    for path in args.paths:
        if not path.exists():
            print(f"{path}: file not found", file=sys.stderr)
            return 2
        all_violations.extend(scan_file(path))

    for violation in all_violations:
        print(violation.format())

    return 1 if all_violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
