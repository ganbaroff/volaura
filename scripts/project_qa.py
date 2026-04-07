"""
project_qa.py — Per-project Q&A Agent.

Built Session 91 after CEO observation: "CTO reads 504 files every time.
Can't we have a project agent that answers questions so nobody re-reads manually?"

REPLACES the pattern of CTO manually grepping/reading docs for every question.
Instead: `python3 scripts/project_qa.py "your question"` → concise answer with sources.

HOW IT WORKS:
1. Builds keyword index of all .md files in docs/ + memory/ + user-level memory.
   Index cached in `.claude/project_qa_index.json`. Rebuild with `--rebuild-index`.
2. For each question: finds top 5 most relevant files via keyword overlap scoring.
3. Reads first 3000 chars of each relevant file as context.
4. Passes context + question to swarm_agent.py (--profile smart) — Groq Kimi K2 or
   Groq Llama 3.3 70B. Zero Anthropic (Constitution Article 0).
5. Returns answer with source file citations + model name.

USAGE:
    # First-time or after docs change:
    python3 scripts/project_qa.py --rebuild-index

    # Ask a question:
    python3 scripts/project_qa.py "what did CTO do in session 91?"
    python3 scripts/project_qa.py "где находится shared_memory.py?"
    python3 scripts/project_qa.py "какие mistakes были this session?"
    python3 scripts/project_qa.py "is the swarm alive?"
    python3 scripts/project_qa.py "что делают agents в coordinator mode?"

    # Force specific model:
    python3 scripts/project_qa.py --profile code "is there a coordinator.py?"
    python3 scripts/project_qa.py --provider groq --model llama-3.3-70b-versatile "..."

DESIGN NOTES:
- No external dependencies beyond what swarm_agent.py already uses (cerebras-sdk, openai).
- Index is keyword-based (not vector embedding) — simpler, faster, zero extra deps.
  Upgrade path: replace find_relevant() with Mem0 or Letta for semantic search.
- 3000 char limit per file is approximate token budget safety for 1500 token context.
- This is intentionally ONE-AGENT-PER-PROJECT. For multi-project Q&A use separate invocations.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
from pathlib import Path


# UTF-8 stdout on Windows — idempotent (only wrap if not already utf-8)
# Prevents "I/O operation on closed file" when swarm_agent.py also tries to wrap
def _ensure_utf8_stream(stream):
    enc = getattr(stream, "encoding", "") or ""
    if "utf" in enc.lower():
        return stream  # already utf-8, skip
    if hasattr(stream, "buffer"):
        return io.TextIOWrapper(stream.buffer, encoding="utf-8", errors="replace")
    return stream

sys.stdout = _ensure_utf8_stream(sys.stdout)
sys.stderr = _ensure_utf8_stream(sys.stderr)


# ── Path resolution (supports main repo + worktree) ────────────────────
def resolve_project_root() -> Path:
    """Find VOLAURA project root regardless of cwd."""
    cwd = Path.cwd()
    # Walk up looking for apps/api/.env
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "apps" / "api" / ".env").exists():
            return candidate
    # Fallback to hardcoded
    return Path("C:/Projects/VOLAURA")


PROJECT_ROOT = resolve_project_root()
USER_MEMORY = Path("C:/Users/user/.claude/projects/C--Projects-VOLAURA/memory")
INDEX_FILE = PROJECT_ROOT / ".claude" / "project_qa_index.json"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


# ── Index building ─────────────────────────────────────────────────────
def _extract_keywords(text: str, max_words: int = 300) -> list[str]:
    """Keyword extraction: top N unique words of length >= 4, lowercased."""
    # Focus on first 3000 chars + any heading-like lines
    heading_lines = re.findall(r"^#+\s+.+$", text[:5000], re.MULTILINE)
    corpus = text[:3000] + "\n" + "\n".join(heading_lines)
    words = re.findall(r"[\w\-]{4,}", corpus.lower())
    # Dedupe preserving order
    seen = set()
    result = []
    for w in words:
        if w not in seen:
            seen.add(w)
            result.append(w)
            if len(result) >= max_words:
                break
    return result


def build_index() -> dict:
    """Scan all .md files in docs/ + memory/ + user-memory. Cache to JSON."""
    index: dict = {}
    search_roots = [
        PROJECT_ROOT / "docs",
        PROJECT_ROOT / "memory",
        USER_MEMORY,
        PROJECT_ROOT / ".claude" / "rules",
        PROJECT_ROOT / ".claude" / "skills",
    ]

    file_count = 0
    for base in search_roots:
        if not base.exists():
            continue
        for md in base.rglob("*.md"):
            # Skip node_modules, .git, archive
            parts = set(md.parts)
            if any(x in parts for x in ("node_modules", ".git", "__pycache__", "dist", ".next")):
                continue
            try:
                content = md.read_text(encoding="utf-8", errors="replace")
                if not content.strip():
                    continue
                index[str(md).replace("\\", "/")] = {
                    "title": md.stem,
                    "keywords": _extract_keywords(content),
                    "size": len(content),
                    "mtime": md.stat().st_mtime,
                }
                file_count += 1
            except Exception:
                pass

    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump({"built_at": time.time(), "files": index}, f, ensure_ascii=False)

    return index


def load_index() -> dict:
    """Load cached index, build if missing."""
    if not INDEX_FILE.exists():
        return build_index()
    try:
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Rebuild if index is older than 1 hour (docs change frequently)
        if time.time() - data.get("built_at", 0) > 3600:
            return build_index()
        return data.get("files", {})
    except Exception:
        return build_index()


# ── Relevance scoring ──────────────────────────────────────────────────
def find_relevant(question: str, index: dict, top_k: int = 5) -> list[tuple[str, int]]:
    """Score each indexed file by keyword overlap + title match. Return top K."""
    q_words = set(re.findall(r"[\w\-]{4,}", question.lower()))
    if not q_words:
        return []

    scores: list[tuple[int, float, str]] = []
    for path, data in index.items():
        kw = set(data.get("keywords", []))
        overlap = len(q_words & kw)

        # Boost: title match (title keyword in question)
        title_lower = data.get("title", "").lower()
        title_words = set(re.findall(r"[\w\-]{4,}", title_lower))
        title_match = len(q_words & title_words)
        if title_match > 0:
            overlap += title_match * 3  # 3x boost for title hits

        # Boost: recency (newer files ranked higher on tie)
        mtime = data.get("mtime", 0)

        if overlap > 0:
            scores.append((overlap, mtime, path))

    # Sort by overlap desc, then mtime desc
    scores.sort(key=lambda x: (-x[0], -x[1]))
    return [(path, score) for score, _, path in scores[:top_k]]


# ── Context building ───────────────────────────────────────────────────
def build_context(relevant_files: list[tuple[str, int]], chars_per_file: int = 3000) -> str:
    """Read snippets from relevant files into a single context string."""
    parts = []
    for path, score in relevant_files:
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            # Smart snippet: beginning + end if large
            if len(content) > chars_per_file:
                snippet = content[:chars_per_file - 500] + "\n...[middle truncated]...\n" + content[-500:]
            else:
                snippet = content
            short_path = path.replace(str(PROJECT_ROOT).replace("\\", "/") + "/", "")
            parts.append(f"=== {short_path} (relevance={score}) ===\n{snippet}\n")
        except Exception:
            pass
    return "\n".join(parts)


# ── LLM call via swarm_agent ───────────────────────────────────────────
def answer_question(question: str, profile: str = "smart", provider: str | None = None, model: str | None = None) -> dict:
    """Main Q&A flow. Returns dict with answer, sources, model, errors."""
    # Import swarm_agent dynamically (might be in scripts/ or worktree scripts/)
    sys.path.insert(0, str(SCRIPTS_DIR))
    # Also try worktree
    worktree_scripts = PROJECT_ROOT / ".claude" / "worktrees"
    if worktree_scripts.exists():
        for wt in worktree_scripts.iterdir():
            wt_scripts = wt / "scripts"
            if wt_scripts.exists():
                sys.path.insert(0, str(wt_scripts))

    try:
        from swarm_agent import call as swarm_call
    except ImportError as e:
        return {
            "ok": False,
            "error": f"swarm_agent.py not found: {e}. Ensure scripts/swarm_agent.py exists.",
        }

    # Build index + find relevant docs
    index = load_index()
    relevant = find_relevant(question, index, top_k=5)

    if not relevant:
        return {
            "ok": False,
            "error": "No relevant documents found. Question keywords didn't match any file.",
            "hint": "Try simpler terms or run --rebuild-index if docs were added recently.",
        }

    context = build_context(relevant)

    system_prompt = (
        "You are the VOLAURA project Q&A agent. "
        "Your job: answer the user's question based ONLY on the provided documentation context. "
        "Rules:\n"
        "1. If the answer is not in the context, say 'Not found in provided docs.'\n"
        "2. Cite file names in your answer when possible.\n"
        "3. Be concise: 3-5 sentences unless user asks for detail.\n"
        "4. For 'what exists' / 'where is X' questions — give exact file path.\n"
        "5. For 'what changed' / 'what did CTO do' — list 3-5 bullets with commit refs if present.\n"
        "6. Never invent information. If unsure, say so."
    )

    user_prompt = f"QUESTION: {question}\n\n--- DOCUMENTATION CONTEXT ---\n{context}\n--- END CONTEXT ---\n\nAnswer the question using only the context above."

    # Call swarm_agent
    kwargs = {"profile": profile, "system": system_prompt, "max_tokens": 1500}
    if provider and model:
        kwargs["provider"] = provider
        kwargs["model"] = model

    result = swarm_call(user_prompt, **kwargs)

    if result.get("ok"):
        sources = [Path(p).name for p, _ in relevant]
        return {
            "ok": True,
            "answer": result["text"],
            "sources": sources,
            "provider": result.get("provider", "?"),
            "model": result.get("model", "?"),
            "tokens": result.get("tokens", 0),
            "elapsed_s": result.get("elapsed_s", 0),
        }
    else:
        return {
            "ok": False,
            "error": result.get("error", "swarm_agent call failed"),
            "attempts": result.get("attempts", []),
        }


# ── CLI ────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="VOLAURA Project Q&A agent — ask questions about docs/code/memory",
        epilog="Examples:\n"
        "  python3 scripts/project_qa.py 'what did CTO do in session 91?'\n"
        "  python3 scripts/project_qa.py --rebuild-index\n"
        "  python3 scripts/project_qa.py --profile code 'is there a coordinator.py?'",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("question", nargs="*", help="The question to answer")
    parser.add_argument("--rebuild-index", action="store_true", help="Rebuild file index")
    parser.add_argument("--profile", default="smart", choices=["fast", "smart", "code", "reason", "translation"])
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.rebuild_index:
        print("Rebuilding index...")
        index = build_index()
        print(f"[OK] Indexed {len(index)} markdown files to {INDEX_FILE}")
        return

    if not args.question:
        parser.print_help()
        sys.exit(1)

    question = " ".join(args.question)
    print(f"Question: {question}")
    print()

    result = answer_question(
        question,
        profile=args.profile,
        provider=args.provider,
        model=args.model,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if result["ok"]:
        print(result["answer"])
        print()
        print(f"--- Sources: {', '.join(result['sources'])}")
        print(f"--- Model: {result['provider']}/{result['model']} | {result['tokens']} tokens | {result['elapsed_s']}s")
    else:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        if "hint" in result:
            print(f"Hint: {result['hint']}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
