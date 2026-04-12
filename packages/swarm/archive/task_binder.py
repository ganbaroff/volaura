#!/usr/bin/env python3
"""Task Binder — Sprint 4: Context Intelligence Engine.

Maps a task description to the specific files agents must read.
Eliminates file-guessing. Agents get a pre-computed, verified list.

Before:
  Agent receives: "Fix the login error message"
  Agent guesses: maybe login.tsx? or auth.ts? or...
  Result: agent reads wrong files, proposes changes to non-existent code

After:
  Task binder runs: "Fix the login error message"
  Queries code index: finds apps/web/.../login/page.tsx (score: 9)
  Agent receives: "BOUND FILES: apps/web/src/app/[locale]/(auth)/login/page.tsx"
  Result: agent reads the right file, proposal is grounded

Usage:
    from swarm.task_binder import bind_task_to_files, inject_bound_files_into_briefing

    bound = bind_task_to_files("Fix login error message", code_index)
    # Returns: {
    #   "primary_files": ["apps/web/.../login/page.tsx"],
    #   "secondary_files": ["apps/api/app/routers/auth.py"],
    #   "affected_tests": ["apps/api/tests/test_auth.py"],
    #   "binding_confidence": 0.85,
    # }

    briefing_with_files = inject_bound_files_into_briefing(briefing_text, bound)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Ensure packages/ is importable when run as __main__
_project_root = Path(__file__).parent.parent.parent
_packages_path = str(_project_root / "packages")
if _packages_path not in sys.path:
    sys.path.insert(0, _packages_path)

# ── Domain keyword → file category mappings ───────────────────────────────────
# When a task mentions a domain keyword, these file patterns are likely relevant.
# Tuned for Volaura's specific codebase structure.

DOMAIN_MAPPINGS: list[tuple[set[str], list[str]]] = [
    # Assessment & evaluation
    (
        {"assessment", "answer", "submit", "session", "competency", "question", "irt", "cat"},
        ["apps/api/app/routers/assessment.py", "apps/api/app/core/assessment/engine.py",
         "apps/web/src/app/[locale]/(dashboard)/assessment"],
    ),
    # AURA score
    (
        {"aura", "score", "badge", "radar", "chart", "platinum", "gold"},
        ["apps/api/app/routers/aura.py", "apps/web/src/app/[locale]/(dashboard)/aura",
         "apps/web/src/components/aura"],
    ),
    # Auth / login / registration
    (
        {"login", "signup", "register", "auth", "oauth", "github", "google", "session", "jwt", "token"},
        ["apps/api/app/routers/auth.py", "apps/web/src/app/[locale]/(auth)",
         "apps/web/src/lib/supabase"],
    ),
    # Profile / public profile
    (
        {"profile", "username", "public", "visibility", "display_name", "onboarding"},
        ["apps/api/app/routers/profiles.py", "apps/web/src/app/[locale]/(dashboard)/dashboard",
         "apps/web/src/app/[locale]/(public)/u"],
    ),
    # Organizations / B2B
    (
        {"org", "organization", "invite", "talent", "search", "discovery", "volunteer"},
        ["apps/api/app/routers/organizations.py", "apps/api/app/routers/discovery.py",
         "apps/web/src/app/[locale]/(org)"],
    ),
    # Subscription / payment
    (
        {"subscription", "stripe", "payment", "billing", "checkout", "trial", "polar"},
        ["apps/api/app/routers/subscription.py", "apps/web/src/app/[locale]/(dashboard)/subscription"],
    ),
    # Swarm / agents
    (
        {"swarm", "agent", "proposal", "autonomous", "skill", "memory"},
        ["packages/swarm/autonomous_run.py", "packages/swarm/inbox_protocol.py",
         "memory/swarm"],
    ),
    # Database / migrations
    (
        {"migration", "table", "schema", "rls", "policy", "supabase", "postgres"},
        ["supabase/migrations", "apps/api/app/schemas"],
    ),
    # LLM / AI / evaluation
    (
        {"llm", "gemini", "groq", "openai", "vertex", "evaluation", "bars", "keyword"},
        ["apps/api/app/services/llm.py", "apps/api/app/services/bars.py"],
    ),
    # Config / environment
    (
        {"config", "env", "environment", "startup", "settings", "railway", "vercel"},
        ["apps/api/app/config.py", "apps/api/.env"],
    ),
    # Notifications / Telegram
    (
        {"notification", "telegram", "email", "alert", "webhook"},
        ["apps/api/app/services/notification_service.py", "apps/api/app/routers/telegram.py"],
    ),
    # i18n
    (
        {"i18n", "translation", "locale", "az", "azerbaijani", "language", "locales"},
        ["apps/web/src/locales/en/common.json", "apps/web/src/locales/az/common.json"],
    ),
    # Ecosystem / crystal / character
    (
        {"crystal", "character", "mindshift", "life", "simulator", "xp", "ecosystem"},
        ["apps/api/app/routers/rewards.py", "apps/api/app/services/cross_product_bridge.py"],
    ),
    # Tests
    (
        {"test", "spec", "fixture", "mock", "pytest"},
        ["apps/api/tests"],
    ),
    # CI/CD / deployment
    (
        {"deploy", "github", "actions", "workflow", "ci", "cd"},
        [".github/workflows"],
    ),
]

# Test file patterns (mapped from source file patterns)
_TEST_PATTERNS = {
    "apps/api/app/routers/assessment.py": "apps/api/tests/test_assessment_api",
    "apps/api/app/routers/auth.py": "apps/api/tests/test_auth",
    "apps/api/app/routers/profiles.py": "apps/api/tests/test_profiles",
    "apps/api/app/routers/organizations.py": "apps/api/tests/test_org",
    "apps/api/app/routers/subscription.py": "apps/api/tests/test_paywall",
    "apps/api/app/routers/aura.py": "apps/api/tests/test_aura",
    "apps/api/app/services/bars.py": "apps/api/tests/test_bars",
    "apps/api/app/services/llm.py": "apps/api/tests/test_bars",
}


# ── Task binding ───────────────────────────────────────────────────────────────

class BoundTask:
    """A task with pre-computed file bindings."""

    def __init__(
        self,
        task_title: str,
        primary_files: list[str],
        secondary_files: list[str],
        affected_tests: list[str],
        binding_confidence: float,
        query_words: set[str],
    ):
        self.task_title = task_title
        self.primary_files = primary_files         # MUST read
        self.secondary_files = secondary_files     # SHOULD read
        self.affected_tests = affected_tests       # must run after change
        self.binding_confidence = binding_confidence
        self.query_words = query_words

    def all_files(self) -> list[str]:
        """All unique files, primary first."""
        seen = set()
        result = []
        for f in self.primary_files + self.secondary_files:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result

    def to_briefing_section(self) -> str:
        """Format as BOUND FILES section for agent briefing."""
        lines = [
            "## BOUND FILES (pre-computed by task_binder — read THESE files, not guesses)",
            f"Binding confidence: {self.binding_confidence:.0%}",
            "",
        ]
        if self.primary_files:
            lines.append("### Primary (MUST READ):")
            for f in self.primary_files:
                lines.append(f"  - {f}")
        if self.secondary_files:
            lines.append("")
            lines.append("### Secondary (SHOULD READ for context):")
            for f in self.secondary_files[:5]:
                lines.append(f"  - {f}")
        if self.affected_tests:
            lines.append("")
            lines.append("### Tests to run after change:")
            for f in self.affected_tests[:3]:
                lines.append(f"  - {f}")
        return "\n".join(lines)


def bind_task_to_files(
    task_description: str,
    code_index: dict | None = None,
    project_root_override: Path | None = None,
    top_k: int = 5,
) -> BoundTask:
    """Map task description to relevant files.

    Two-phase approach:
      Phase 1: Domain mappings (fast, rule-based) — check domain keywords
      Phase 2: Code index search (scored) — find specific matching files

    Args:
        task_description: Task title + description combined
        code_index: Pre-loaded index (loads from disk if None)
        project_root_override: Override for testing
        top_k: Max primary files to return

    Returns:
        BoundTask with primary_files, secondary_files, affected_tests, confidence
    """
    from swarm.code_index import load_index, find_elements

    root = project_root_override or Path(__file__).parent.parent.parent
    index = code_index or load_index(root)

    text_lower = task_description.lower()
    query_words = set(re.split(r"[\s\-_./]", text_lower))
    query_words = {w for w in query_words if len(w) > 2}

    primary_files: list[str] = []
    secondary_files: list[str] = []
    affected_tests: list[str] = []

    # Phase 1: Domain keyword matching
    for keyword_set, file_patterns in DOMAIN_MAPPINGS:
        if keyword_set & query_words:
            for pattern in file_patterns:
                # Check if pattern is a specific file
                specific = root / pattern
                if specific.is_file():
                    rel = str(specific.relative_to(root)).replace("\\", "/")
                    if rel not in primary_files:
                        primary_files.append(rel)
                # If pattern is a directory, add it as context
                elif specific.is_dir():
                    # Find the most relevant file in this directory
                    dir_results = find_elements(task_description, index, top_k=3, file_type_filter=None)
                    for r in dir_results:
                        if r["path"].startswith(pattern.replace("\\", "/")):
                            if r["path"] not in primary_files:
                                primary_files.append(r["path"])

    # Phase 2: Code index search for additional context
    index_results = find_elements(task_description, index, top_k=top_k + 5)
    for result in index_results:
        path = result["path"]
        if path not in primary_files and result["score"] >= 5:
            secondary_files.append(path)
        elif path not in primary_files and path not in secondary_files:
            secondary_files.append(path)

    # Deduplicate and cap
    seen = set()
    clean_primary = []
    for f in primary_files[:top_k]:
        if f not in seen:
            seen.add(f)
            clean_primary.append(f)

    clean_secondary = []
    for f in secondary_files:
        if f not in seen and len(clean_secondary) < 8:
            seen.add(f)
            clean_secondary.append(f)

    # Find test files
    for source_file in clean_primary:
        for src_pattern, test_pattern in _TEST_PATTERNS.items():
            if source_file == src_pattern or source_file.startswith(src_pattern.rstrip("py")):
                # Find matching test files in index
                test_results = find_elements(Path(test_pattern).name, index, top_k=2,
                                              file_type_filter="python")
                for tr in test_results:
                    if "test" in tr["path"] and tr["path"] not in affected_tests:
                        affected_tests.append(tr["path"])

    # Compute confidence
    if not clean_primary and not clean_secondary:
        confidence = 0.0
    elif clean_primary:
        # Verify primary files actually exist
        existing = [f for f in clean_primary if (root / f).exists()]
        confidence = len(existing) / len(clean_primary) if clean_primary else 0.5
    else:
        confidence = 0.4  # secondary only — lower confidence

    return BoundTask(
        task_title=task_description[:100],
        primary_files=clean_primary,
        secondary_files=clean_secondary,
        affected_tests=affected_tests,
        binding_confidence=confidence,
        query_words=query_words,
    )


def inject_bound_files_into_briefing(briefing: str, bound: BoundTask) -> str:
    """Prepend BOUND FILES section to an agent briefing.

    Args:
        briefing: Existing agent briefing text
        bound: BoundTask from bind_task_to_files()

    Returns:
        Briefing with BOUND FILES section prepended after any header
    """
    section = bound.to_briefing_section()
    # Insert after first two lines (title/version) of briefing if it has one
    lines = briefing.split("\n")
    header_end = 0
    for i, line in enumerate(lines[:5]):
        if line.startswith("#") or line.startswith("**"):
            header_end = i + 1

    if header_end > 0:
        return "\n".join(lines[:header_end]) + "\n\n" + section + "\n\n" + "\n".join(lines[header_end:])
    else:
        return section + "\n\n" + briefing


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m packages.swarm.task_binder <task description>")
        sys.exit(1)

    task_desc = " ".join(sys.argv[1:])
    print(f"Binding task: '{task_desc}'")
    print()

    bound = bind_task_to_files(task_desc)
    print(bound.to_briefing_section())
    print(f"\nConfidence: {bound.binding_confidence:.0%}")
