#!/usr/bin/env python3
"""Conservative remover of unused imports using the AST.

This script parses each .py file (excluding venv, migrations, __pycache__, etc.),
finds top-level Import and ImportFrom statements, checks for usage of the
imported names in the AST, and removes or reduces import clauses that are
unused. It attempts to preserve formatting and comments on the same line.

Run: `python tools/remove_unused_imports.py` and review the changes.
"""
import ast
from pathlib import Path
from typing import Set, Tuple

EXCLUDE_PATTERNS = [".venv", "venv", "env", "ENV", "build", "dist", "__pycache__", "migrations", "static", "media", "templates"]


def is_excluded(path: Path) -> bool:
    parts = [p.lower() for p in path.parts]
    for pat in EXCLUDE_PATTERNS:
        if pat.lower() in parts:
            return True
    return False


class ImportCleaner(ast.NodeVisitor):
    def __init__(self):
        self.used_names: Set[str] = set()
        self.imports: list[Tuple[int, ast.AST]] = []

    def visit_Name(self, node: ast.Name):
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # capture attribute base names (e.g., models.Publication -> models)
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        self.imports.append((node.lineno, node))

    def visit_ImportFrom(self, node: ast.ImportFrom):
        self.imports.append((node.lineno, node))


def process_file(path: Path) -> int:
    text = path.read_text(encoding="utf8")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0

    cleaner = ImportCleaner()
    cleaner.visit(tree)

    lines = text.splitlines()
    modified = False

    # process imports in reverse lineno order to avoid shifting lines
    for lineno, node in sorted(cleaner.imports, key=lambda x: -x[0]):
        idx = lineno - 1
        if isinstance(node, ast.Import):
            # build list of names and see which are used
            keep_aliases = []
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                if name in cleaner.used_names:
                    keep_aliases.append(alias)
            if not keep_aliases:
                # remove the import line
                lines.pop(idx)
                modified = True
            else:
                # rewrite the line to keep only used aliases
                new_names = ", ".join([a.name + (" as " + a.asname if a.asname else "") for a in keep_aliases])
                lines[idx] = f"import {new_names}"
                modified = True

        elif isinstance(node, ast.ImportFrom):
            # skip star imports
            if any(alias.name == "*" for alias in node.names):
                continue
            keep_aliases = []
            for alias in node.names:
                name = alias.asname or alias.name
                if name in cleaner.used_names:
                    keep_aliases.append(alias)
            if not keep_aliases:
                # remove the import-from line
                lines.pop(idx)
                modified = True
            else:
                module = node.module or ""
                new_names = ", ".join([a.name + (" as " + a.asname if a.asname else "") for a in keep_aliases])
                lines[idx] = f"from {module} import {new_names}"
                modified = True

    if modified:
        path.write_text("\n".join(lines) + "\n", encoding="utf8")
        return 1
    return 0


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
            changed += process_file(p)
        except Exception as exc:
            print(f"Error processing {p}: {exc}")

    print(f"Files modified (imports cleanup): {changed}")


if __name__ == "__main__":
    main()
