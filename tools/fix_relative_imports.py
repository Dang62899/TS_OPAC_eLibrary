#!/usr/bin/env python3
"""Convert top-level imports of sibling modules to explicit relative imports.

This script looks for patterns like `from models import X` in files that live in a
package (a directory with `__init__.py`) and, when a sibling module `models.py`
exists in the same directory, rewrites the import as `from .models import X`.

This is conservative and only rewrites simple `from NAME import ...` forms where
`NAME.py` exists adjacent to the current file.
"""
from pathlib import Path
import re

EXCLUDE_DIRS = {
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
}

IMPORT_RE = re.compile(r"^(from)\s+([A-Za-z_][A-Za-z0-9_]*)\s+import\s+(.*)$")


def is_package_dir(p: Path) -> bool:
    return (p / "__init__.py").exists()


def process_file(path: Path) -> int:
    dirp = path.parent
    if not is_package_dir(dirp):
        return 0
    changed = 0
    lines = path.read_text(encoding="utf8").splitlines()
    out = []
    for line in lines:
        m = IMPORT_RE.match(line.strip())
        if m:
            kind, modname, rest = m.groups()
            candidate = dirp / f"{modname}.py"
            if candidate.exists():
                # preserve indentation
                indent = line[: len(line) - len(line.lstrip())]
                new = f"{indent}from .{modname} import {rest}"
                out.append(new)
                changed += 1
                continue
        out.append(line)

    if changed:
        path.write_text("\n".join(out) + "\n", encoding="utf8")
    return changed


def main():
    root = Path(__file__).resolve().parents[1]
    py_files = list(root.rglob("*.py"))
    total = 0
    for p in py_files:
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.samefile(Path(__file__)):
            continue
        total += process_file(p)
    print(f"Rewrote {total} imports to relative form")


if __name__ == "__main__":
    main()
