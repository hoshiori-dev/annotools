"""Check that README.md and README.zh.md have the same section structure and code blocks.

Compares the heading depth sequence and fenced code blocks (language + content with trailing `#`
comments removed, so comments may be translated), so a change to one README that is not mirrored in the
other fails fast. Prose is not compared.
Exit 0 when in sync, 1 with a diff-style report otherwise.
"""

import re
import sys
from pathlib import Path

HEADING = re.compile(r"^(#{1,6})\s", re.MULTILINE)
FENCE = re.compile(r"^```(\w*)\n(.*?)^```", re.MULTILINE | re.DOTALL)
COMMENT = re.compile(r"\s+#.*$", re.MULTILINE)


def normalize(code: str) -> str:
    return COMMENT.sub("", code).strip()


def structure(path: Path) -> tuple[list[int], list[tuple[str, str]]]:
    text = path.read_text(encoding="utf-8")
    return [len(m.group(1)) for m in HEADING.finditer(text)], [
        (m.group(1), normalize(m.group(2))) for m in FENCE.finditer(text)
    ]


def main() -> int:
    en, zh = Path("README.md"), Path("README.zh.md")
    en_heads, en_code = structure(en)
    zh_heads, zh_code = structure(zh)
    problems = []
    if en_heads != zh_heads:
        problems.append(f"heading structure differs: README.md {en_heads} vs README.zh.md {zh_heads}")
    if en_code != zh_code:
        problems.append("fenced code blocks differ (language or content); keep commands identical in both files")
    for p in problems:
        print(f"check_readme_sync: {p}")
    print("README.md and README.zh.md are in sync." if not problems else "Fix: mirror the change in the other README.")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
