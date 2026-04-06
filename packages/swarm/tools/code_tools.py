"""Code tools — agents can READ and SEARCH the codebase.

These tools give agents the same visibility a developer has.
Agents call these during autonomous runs to ground their proposals
in real code, not assumptions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from loguru import logger


_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def read_file(relative_path: str, max_lines: int = 100) -> str:
    """Read a file from the project. Returns first max_lines lines.

    Agent usage: "Read apps/api/app/routers/assessment.py to check if role_level exists"
    """
    full_path = _PROJECT_ROOT / relative_path
    if not full_path.exists():
        return f"FILE NOT FOUND: {relative_path}"
    if not full_path.is_file():
        return f"NOT A FILE: {relative_path}"
    # Security: don't read outside project
    try:
        full_path.resolve().relative_to(_PROJECT_ROOT.resolve())
    except ValueError:
        return f"ACCESS DENIED: {relative_path} is outside project root"

    try:
        lines = full_path.read_text(encoding="utf-8").splitlines()
        total = len(lines)
        truncated = lines[:max_lines]
        result = "\n".join(f"{i+1}: {line}" for i, line in enumerate(truncated))
        if total > max_lines:
            result += f"\n... ({total - max_lines} more lines)"
        return result
    except Exception as e:
        return f"READ ERROR: {e}"


def grep_codebase(pattern: str, file_glob: str = "*.py", max_results: int = 20) -> str:
    """Search codebase for a regex pattern. Returns matching lines with file:line.

    Agent usage: "Search for text-red- in all .tsx files"
    """
    results: list[str] = []
    search_dirs = [
        _PROJECT_ROOT / "apps" / "api" / "app",
        _PROJECT_ROOT / "apps" / "web" / "src",
        _PROJECT_ROOT / "packages" / "swarm",
        _PROJECT_ROOT / "supabase",
    ]

    compiled = re.compile(pattern, re.IGNORECASE)

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for f in search_dir.rglob(file_glob):
            if f.is_file() and f.stat().st_size < 500_000:  # skip huge files
                try:
                    for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                        if compiled.search(line):
                            rel = f.relative_to(_PROJECT_ROOT)
                            results.append(f"{rel}:{i}: {line.strip()[:120]}")
                            if len(results) >= max_results:
                                return "\n".join(results) + f"\n... (capped at {max_results})"
                except (UnicodeDecodeError, PermissionError):
                    continue

    return "\n".join(results) if results else f"NO MATCHES for /{pattern}/ in {file_glob}"


def search_code_index(query: str, top_k: int = 10) -> str:
    """Search the pre-built code index (1207 files). Keyword-based ranking.

    Agent usage: "Find all files related to assessment scoring"
    """
    index_path = _PROJECT_ROOT / "memory" / "swarm" / "code-index.json"
    if not index_path.exists():
        return "CODE INDEX NOT FOUND. Run: python -m packages.swarm.code_index build"

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            index = json.load(f)
    except Exception as e:
        return f"INDEX LOAD ERROR: {e}"

    # Import the search function from code_index
    try:
        from swarm.code_index import find_elements
        results = find_elements(query, index, top_k=top_k)
        if not results:
            return f"NO RESULTS for '{query}' in code index"
        lines = []
        for r in results:
            lines.append(f"[score={r.get('score', 0):.1f}] {r.get('path', '?')}")
            if r.get("functions"):
                lines.append(f"  functions: {', '.join(r['functions'][:5])}")
            if r.get("classes"):
                lines.append(f"  classes: {', '.join(r['classes'][:3])}")
        return "\n".join(lines)
    except Exception as e:
        return f"SEARCH ERROR: {e}"


def list_directory(relative_path: str) -> str:
    """List files in a directory. Agent usage: "What files are in apps/api/app/routers/"
    """
    full_path = _PROJECT_ROOT / relative_path
    if not full_path.exists():
        return f"DIRECTORY NOT FOUND: {relative_path}"
    if not full_path.is_dir():
        return f"NOT A DIRECTORY: {relative_path}"

    entries = sorted(full_path.iterdir())
    lines = []
    for e in entries[:50]:
        suffix = "/" if e.is_dir() else f" ({e.stat().st_size} bytes)"
        lines.append(f"  {e.name}{suffix}")

    total = len(list(full_path.iterdir()))
    if total > 50:
        lines.append(f"  ... ({total - 50} more)")
    return f"{relative_path}/\n" + "\n".join(lines)


def check_constitution_law1(file_glob: str = "*.tsx") -> str:
    """Check for Law 1 violations (red color). Returns all instances.

    Agent usage: "Audit Law 1 compliance across all React components"
    """
    return grep_codebase(
        r"text-red-|bg-red-|border-red-|#[Ff][Ff]0000|#[Dd][Cc]2626|#[Ee][Ff]4444",
        file_glob=file_glob,
        max_results=50,
    )
