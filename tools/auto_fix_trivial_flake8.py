#!/usr/bin/env python3
"""Auto-fix trivial flake8 issues across the repo.

Fixes performed:
- Remove trailing whitespace
- Remove whitespace-only blank lines
- Ensure file ends with a single newline
- Convert f-strings with no placeholders (no { or }) to plain strings

This script is conservative and only modifies .py files under the repo,
skipping virtualenvs, migrations, __pycache__, static, media, and templates.
Run: `python tools/auto_fix_trivial_flake8.py`
"""
import re
from pathlib import Path

EXCLUDE_PATTERNS = [
    ".venv",
    "venv",
    "env",
    "ENV",
    "build",
    "dist",
    "__pycache__",
    "migrations",
    "static",
    "media",
    "templates",
]


def is_excluded(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    for pat in EXCLUDE_PATTERNS:
        if pat.lower() in parts:
            return True
    return False


FSTRING_NO_PLACEHOLDERS_RE = re.compile(r"(?P<prefix>\b)f(?P<quote>\"\'\"\'|\'\'\'|\"\"\")(?P<body>[^{}]*?)(?P=quote)")


def fix_file(path: Path) -> int:
    text = path.read_text(encoding="utf8")
    orig = text

    # Split lines, strip trailing whitespace, remove whitespace-only blank lines
    lines = [line.rstrip() for line in text.splitlines()]
    new_lines = []
    for line in lines:
        # keep non-empty lines and keep single blank lines between content
        if line.strip() == "":
            if not new_lines or new_lines[-1].strip() == "":
                # skip duplicate blank line
                continue
            new_lines.append("")
        else:
            new_lines.append(line)

    text = "\n".join(new_lines) + "\n"

    # Replace f-strings that contain no { or } with plain strings: f"abc" -> "abc"
    # Conservative: only replace when there is no { or } in the body
    def _f_replace(m):
        body = m.group("body")
        quote = m.group("quote")
        # if braces present, skip
        if "{" in body or "}" in body:
            return m.group(0)
        return m.group("prefix") + quote + body + quote

    text = FSTRING_NO_PLACEHOLDERS_RE.sub(_f_replace, text)

    if text != orig:
        path.write_text(text, encoding="utf8")
        return 1
    return 0


def main():
    repo_root = Path(__file__).resolve().parents[1]
    py_files = list(repo_root.rglob("*.py"))
    changed = 0
    for p in py_files:
        if is_excluded(p):
            continue
        # skip this fixer itself
        if p.samefile(Path(__file__)):
            continue
        try:
            changed += fix_file(p)
        except Exception as exc:
            print(f"Failed to process {p}: {exc}")

    print(f"Files changed: {changed}")


if __name__ == "__main__":
    main()
