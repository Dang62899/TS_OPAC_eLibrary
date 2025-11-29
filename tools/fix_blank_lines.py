#!/usr/bin/env python3
"""Fix E302/E305 blank-line spacing violations.

Ensures 2 blank lines before top-level function/class definitions and 2 blank
lines after them (before the next definition).
"""
import ast
from pathlib import Path
from typing import List

EXCLUDE_PATTERNS = [".venv", "venv", "env", "ENV", "build", "dist", "__pycache__", "migrations", "static", "media", "templates"]


def is_excluded(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    for pat in EXCLUDE_PATTERNS:
        if pat.lower() in parts:
            return True
    return False


def fix_blank_lines(path: Path) -> bool:
    text = path.read_text(encoding="utf8")
    lines = text.splitlines(keepends=False)
    
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    
    # Collect line numbers of top-level definitions
    top_level_defs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            top_level_defs.append(node.lineno)
    
    if not top_level_defs:
        return False
    
    # Sort descending to avoid index shifting
    top_level_defs.sort(reverse=True)
    
    modified = False
    for lineno in top_level_defs:
        idx = lineno - 1
        if idx < 0 or idx >= len(lines):
            continue
        
        # Count blank lines before this definition
        blank_before = 0
        check_idx = idx - 1
        while check_idx >= 0 and lines[check_idx].strip() == '':
            blank_before += 1
            check_idx -= 1
        
        # If not first top-level item and we have < 2 blank lines before, add some
        if check_idx >= 0 and blank_before < 2:
            lines_to_add = 2 - blank_before
            for _ in range(lines_to_add):
                lines.insert(idx, '')
            modified = True
    
    if modified:
        path.write_text('\n'.join(lines) + '\n', encoding='utf8')
        return True
    
    return False


def main():
    repo_root = Path(__file__).resolve().parents[1]
    py_files = list(repo_root.rglob("*.py"))
    changed = 0
    
    for p in py_files:
        if is_excluded(p):
            continue
        if p.samefile(Path(__file__)):
            continue
        try:
            if fix_blank_lines(p):
                changed += 1
        except Exception as exc:
            print(f"Error processing {p}: {exc}")
    
    print(f"Files modified (blank-line fixes): {changed}")


if __name__ == "__main__":
    main()
