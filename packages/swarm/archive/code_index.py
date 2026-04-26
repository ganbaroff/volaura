#!/usr/bin/env python3
"""Code Index — Sprint 4: Context Intelligence Engine.

Builds a searchable index of the Volaura codebase. Agents query this
index to get a pre-computed list of files to read before executing a task.

Replaces guesswork: "I think the login button is in login/page.tsx" →
"The login button is confirmed at apps/web/src/app/[locale]/(auth)/login/page.tsx"

Index structure (stored as memory/swarm/code-index.json):
{
  "built_at": "ISO timestamp",
  "total_files": N,
  "files": {
    "apps/api/app/routers/assessment.py": {
      "path": "apps/api/app/routers/assessment.py",
      "type": "python",
      "size": 12345,
      "functions": ["start_assessment", "submit_answer", "complete_assessment"],
      "classes": ["AssessmentRouter"],
      "imports": ["fastapi", "app.schemas"],
      "keywords": ["assessment", "answer", "session", "competency"],
    },
    "apps/web/src/app/.../page.tsx": {
      "path": "...",
      "type": "typescript",
      "size": 3456,
      "exports": ["LoginPage", "LoginContent"],
      "keywords": ["login", "auth", "signup"],
    }
  }
}

Usage:
    from swarm.code_index import build_index, find_elements, load_index

    # Build (run once or on every push via GitHub Actions)
    index = build_index(project_root)

    # Query
    elements = find_elements("login button", index)
    # Returns: [{"path": "apps/web/.../login/page.tsx", "score": 0.9, ...}]
"""

from __future__ import annotations

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

# File is in packages/swarm/archive/, so 4 parents up = repo root
project_root = Path(__file__).parent.parent.parent.parent
INDEX_FILE = project_root / "memory" / "swarm" / "code-index.json"

# Files/dirs to skip
SKIP_DIRS = {
    "__pycache__", ".git", "node_modules", ".next", "dist", "build",
    "coverage", ".pytest_cache", "archive", ".venv", "venv",
}
SKIP_EXTENSIONS = {".pyc", ".pyo", ".map", ".lock", ".ico", ".png", ".svg",
                   ".jpg", ".jpeg", ".gif", ".woff", ".woff2", ".ttf"}

# File types we index
INDEXED_EXTENSIONS = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".sql": "sql",
    ".md": "markdown",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
}

# Paths we focus on (ignore everything else)
INDEXED_PATHS = [
    "apps/api/app",
    "apps/web/src",
    "packages/swarm",
    "supabase/migrations",
    "memory/swarm",
    "docs",
    ".github/workflows",
]

# Max file size to index (bytes) — skip huge generated files
MAX_FILE_SIZE = 200_000


# ── Python parsing ─────────────────────────────────────────────────────────────

def _parse_python(source: str) -> dict:
    """Extract functions, classes, imports from Python source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {"functions": [], "classes": [], "imports": []}

    functions, classes, imports = [], [], []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Only top-level and class-method functions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])

    return {
        "functions": list(dict.fromkeys(functions))[:30],  # deduplicate, cap
        "classes": list(dict.fromkeys(classes))[:10],
        "imports": list(dict.fromkeys(imports))[:20],
    }


# ── TypeScript/TSX parsing (regex-based — no TS parser) ───────────────────────

_TS_EXPORT_RE = re.compile(
    r"export\s+(?:default\s+)?(?:function|const|class|interface|type)\s+(\w+)"
)
_TS_IMPORT_RE = re.compile(r"from\s+['\"]([^'\"]+)['\"]")
_TS_COMPONENT_RE = re.compile(r"(?:function|const)\s+([A-Z]\w+)\s*(?:=|\()")


def _parse_typescript(source: str) -> dict:
    """Extract exports, imports, component names from TypeScript source."""
    exports = list(dict.fromkeys(_TS_EXPORT_RE.findall(source)))[:20]
    imports = list(dict.fromkeys(_TS_IMPORT_RE.findall(source)))[:20]
    components = list(dict.fromkeys(_TS_COMPONENT_RE.findall(source)))[:20]

    # Deduplicate components vs exports
    all_names = list(dict.fromkeys(exports + components))

    return {
        "exports": all_names[:20],
        "imports": imports[:20],
    }


# ── SQL parsing ───────────────────────────────────────────────────────────────

_SQL_TABLE_RE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:public\.)?(\w+)", re.IGNORECASE)
_SQL_FUNC_RE = re.compile(r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+(?:public\.)?(\w+)", re.IGNORECASE)


def _parse_sql(source: str) -> dict:
    """Extract table names and function names from SQL."""
    return {
        "tables": list(dict.fromkeys(_SQL_TABLE_RE.findall(source)))[:10],
        "functions": list(dict.fromkeys(_SQL_FUNC_RE.findall(source)))[:10],
    }


# ── Keyword extraction ────────────────────────────────────────────────────────

def _extract_keywords(path_str: str, content: str, parsed: dict) -> list[str]:
    """Extract searchable keywords from path + parsed metadata."""
    keywords = set()

    # From path segments (most reliable signal)
    for part in Path(path_str).parts:
        # Split on common separators
        for word in re.split(r"[-_.\[\]()]", part):
            if len(word) > 2 and word not in ("the", "and", "for", "tsx", "py", "ts"):
                keywords.add(word.lower())

    # From parsed names (functions, classes, exports)
    for name in (
        parsed.get("functions", []) +
        parsed.get("classes", []) +
        parsed.get("exports", []) +
        parsed.get("tables", [])
    ):
        # CamelCase → individual words
        words = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)", name)
        keywords.update(w.lower() for w in words if len(w) > 2)
        keywords.add(name.lower())

    # From content: extract meaningful identifiers (camelCase, snake_case)
    # Cap at 50 keywords from content to avoid bloat
    content_names = re.findall(r"\b[a-z][a-z_]{3,}[a-z]\b", content[:5000])
    keywords.update(list(dict.fromkeys(content_names))[:30])

    return sorted(keywords)[:60]  # cap total keywords per file


# ── Index builder ─────────────────────────────────────────────────────────────

def build_index(project_root_override: Path | None = None) -> dict:
    """Scan the codebase and build a searchable index.

    Args:
        project_root_override: Override project root (for testing)

    Returns:
        Index dict (also written to memory/swarm/code-index.json)
    """
    root = project_root_override or project_root
    files_index: dict[str, dict] = {}
    total_scanned = 0

    for indexed_path in INDEXED_PATHS:
        base = root / indexed_path
        if not base.exists():
            continue

        for file_path in base.rglob("*"):
            if not file_path.is_file():
                continue

            # Skip dirs
            if any(skip in file_path.parts for skip in SKIP_DIRS):
                continue

            # Skip extensions
            if file_path.suffix in SKIP_EXTENSIONS:
                continue

            file_type = INDEXED_EXTENSIONS.get(file_path.suffix)
            if file_type is None:
                continue

            # Skip large files
            size = file_path.stat().st_size
            if size > MAX_FILE_SIZE:
                continue

            total_scanned += 1
            rel_path = str(file_path.relative_to(root)).replace("\\", "/")

            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

            # Parse based on type
            parsed: dict = {}
            if file_type == "python":
                parsed = _parse_python(content)
            elif file_type == "typescript":
                parsed = _parse_typescript(content)
            elif file_type == "sql":
                parsed = _parse_sql(content)

            keywords = _extract_keywords(rel_path, content, parsed)

            entry: dict = {
                "path": rel_path,
                "type": file_type,
                "size": size,
                "keywords": keywords,
            }
            entry.update(parsed)
            files_index[rel_path] = entry

    index = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "total_files": len(files_index),
        "scanned": total_scanned,
        "files": files_index,
    }

    # Write to disk
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

    return index


def load_index(project_root_override: Path | None = None) -> dict:
    """Load existing index from disk. Build if not found."""
    index_path = (project_root_override or project_root) / "memory" / "swarm" / "code-index.json"
    if not index_path.exists():
        return build_index(project_root_override)
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ── Search ────────────────────────────────────────────────────────────────────

def find_elements(
    query: str,
    index: dict | None = None,
    top_k: int = 10,
    file_type_filter: str | None = None,
) -> list[dict]:
    """Search index for files matching a query.

    Scoring:
      - Each query word found in file keywords: +1
      - Query word found in file path: +2 (path match is stronger signal)
      - Query word found in function/class/export names: +3 (name match is strongest)
      - Exact path segment match: +5

    Args:
        query: Natural language query ("login button", "assessment router", etc.)
        index: Pre-loaded index dict (loads from disk if None)
        top_k: Maximum results to return
        file_type_filter: Limit to "python", "typescript", "sql", etc.

    Returns:
        List of dicts sorted by relevance score (highest first):
        [{"path": str, "score": int, "type": str, "functions": list, ...}]
    """
    if index is None:
        index = load_index()

    files = index.get("files", {})
    query_words = set(re.split(r"[\s\-_./]", query.lower()))
    query_words = {w for w in query_words if len(w) > 2}

    scored: list[tuple[int, dict]] = []

    for path, entry in files.items():
        if file_type_filter and entry.get("type") != file_type_filter:
            continue

        score = 0
        path_lower = path.lower()

        # Path match (strong signal)
        for word in query_words:
            if word in path_lower:
                score += 2
            # Exact path segment match
            if word in path_lower.split("/"):
                score += 5

        # Keyword match
        keywords = set(entry.get("keywords", []))
        overlap = query_words & keywords
        score += len(overlap)

        # Function/class/export name match (strongest signal)
        all_names = (
            entry.get("functions", []) +
            entry.get("classes", []) +
            entry.get("exports", []) +
            entry.get("tables", [])
        )
        name_words = set()
        for name in all_names:
            name_words.update(re.findall(r"[a-z]{3,}", name.lower()))

        name_overlap = query_words & name_words
        score += len(name_overlap) * 3

        if score > 0:
            result = {"path": path, "score": score}
            result.update({k: v for k, v in entry.items() if k not in ("keywords",)})
            scored.append((score, result))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "build":
        print("Building code index...")
        idx = build_index()
        print(f"[OK] Indexed {idx['total_files']} files (scanned {idx['scanned']})")
        print(f"     Written to: memory/swarm/code-index.json")
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Searching index for: '{query}'")
        idx = load_index()
        results = find_elements(query, idx, top_k=8)
        if results:
            for r in results:
                names = r.get("functions", r.get("exports", []))[:3]
                names_str = f" — {', '.join(names)}" if names else ""
                print(f"  [{r['score']:2d}] {r['path']}{names_str}")
        else:
            print("  No results found.")
    else:
        print("Usage:")
        print("  python -m packages.swarm.code_index build      # build index")
        print("  python -m packages.swarm.code_index <query>    # search")
