#!/usr/bin/env python3
"""Skills Loader — auto-matches task description to CLAUDE.md Skills Matrix.

Usage:
    from packages.swarm.skills_loader import load_skills_for_task

    skills = load_skills_for_task("fix RLS policy for intro_requests table")
    # returns list of (skill_name, file_path, content) for matched skills

Also callable as CLI:
    python -m packages.swarm.skills_loader --task "add new API endpoint for subscriptions"
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)


# ── Skills Matrix — mirrors CLAUDE.md Skills Matrix section ──────────────────
# Format: (trigger_patterns, skill_name, skill_file)
# Patterns are regex (case-insensitive). First match wins per skill.
SKILLS_MATRIX = [
    # Security
    (
        [r"rls", r"security", r"auth", r"grant", r"revoke", r"policy", r"owasp", r"inject"],
        "security-review",
        "docs/engineering/skills/SECURITY-REVIEW.md",
    ),
    # New API endpoint
    (
        [r"new.*endpoint", r"new.*route", r"add.*router", r"create.*api"],
        "security-review",
        "docs/engineering/skills/SECURITY-REVIEW.md",
    ),
    # Testing / TDD
    (
        [r"test", r"tdd", r"coverage", r"regression", r"failing test", r"bug fix"],
        "tdd-workflow",
        "docs/engineering/skills/TDD-WORKFLOW.md",
    ),
    # React hooks
    (
        [r"use[A-Z]\w+", r"useMutation", r"useQuery", r"hook"],
        "react-hooks-patterns",
        "docs/engineering/skills/REACT-HOOKS-PATTERNS.md",
    ),
    # UI / design
    (
        [r"ui", r"component", r"page", r"layout", r"tailwind", r"shadcn", r"design"],
        "design-critique",
        None,  # built-in skill, no file
    ),
    (
        [r"ux.writ", r"button label", r"error message", r"empty state", r"copy"],
        "ux-writing",
        None,
    ),
    # Code review (any large change)
    (
        [r"refactor", r"cleanup", r"code review", r"architecture", r"50.lines"],
        "code-review",
        None,
    ),
    # Deploy
    (
        [r"deploy", r"railway", r"vercel", r"production", r"release"],
        "deploy-checklist",
        None,
    ),
    # Content / LinkedIn
    (
        [r"linkedin", r"post", r"content", r"copywrite"],
        "tone-of-voice",
        "docs/TONE-OF-VOICE.md",
    ),
    (
        [r"linkedin", r"post", r"content", r"copywrite", r"publish"],
        "communications-strategist",
        "memory/swarm/skills/communications-strategist.md",
    ),
    # B2B / sales
    (
        [r"b2b", r"org", r"subscription", r"pricing", r"deal"],
        "sales-deal-strategist",
        "memory/swarm/skills/sales-deal-strategist.md",
    ),
    # Cultural / AZ
    (
        [r"\baz\b", r"azerbaij", r"cultural", r"i18n", r"locali"],
        "cultural-intelligence",
        "memory/swarm/skills/cultural-intelligence-strategist.md",
    ),
    # Behavioral nudge
    (
        [r"onboard", r"assessment.*ux", r"engagement", r"nudge", r"empty state", r"re-engage"],
        "behavioral-nudge",
        "memory/swarm/skills/behavioral-nudge-engine.md",
    ),
    # Accessibility
    (
        [r"accessib", r"a11y", r"wcag", r"aria"],
        "accessibility-auditor",
        "memory/swarm/skills/accessibility-auditor.md",
    ),
    # Mandatory on every sprint start
    (
        [r"sprint", r"session start", r"begin", r"protocol"],
        "mandatory-rules",
        "docs/MANDATORY-RULES.md",
    ),
]


def load_skills_for_task(
    task_description: str,
    max_content_chars: int = 3000,
) -> list[dict]:
    """
    Match task description against Skills Matrix.

    Returns list of:
        {
            "skill_name": str,
            "file_path": str | None,
            "content": str | None,   # file contents if readable
            "matched_by": str,       # which pattern triggered
        }
    """
    matched: list[dict] = []
    seen_skills: set[str] = set()

    for patterns, skill_name, skill_file in SKILLS_MATRIX:
        if skill_name in seen_skills:
            continue

        for pattern in patterns:
            if re.search(pattern, task_description, re.IGNORECASE):
                entry: dict = {
                    "skill_name": skill_name,
                    "file_path": skill_file,
                    "content": None,
                    "matched_by": pattern,
                }

                # Try to read file content
                if skill_file:
                    full_path = project_root / skill_file
                    if full_path.exists():
                        with open(full_path, "r", encoding="utf-8") as f:
                            raw = f.read()
                        entry["content"] = raw[:max_content_chars]
                    else:
                        entry["content"] = f"[File not found: {skill_file}]"

                matched.append(entry)
                seen_skills.add(skill_name)
                break  # next skill

    return matched


def format_for_agent_prompt(skills: list[dict]) -> str:
    """Format loaded skills as a compact block for injection into agent prompts."""
    if not skills:
        return ""

    lines = [
        f"## LOADED SKILLS ({len(skills)} matched)",
        "Apply these guidelines to this task:\n",
    ]

    for skill in skills:
        lines.append(f"### {skill['skill_name']} (triggered by: `{skill['matched_by']}`)")
        if skill["content"]:
            # Take only the first meaningful section
            content_preview = skill["content"][:800].rstrip()
            lines.append(content_preview)
        else:
            lines.append(f"[Built-in skill — no file content]")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-load skills for a task description")
    parser.add_argument("--task", required=True, help="Task description text")
    parser.add_argument(
        "--format",
        choices=["json", "prompt"],
        default="prompt",
        help="Output format",
    )
    args = parser.parse_args()

    skills = load_skills_for_task(args.task)

    if not skills:
        print(f"No skills matched for: {args.task!r}")
        return

    if args.format == "json":
        import json
        # Don't dump full content in CLI mode
        for s in skills:
            s["content"] = s["content"][:200] + "..." if s.get("content") else None
        print(json.dumps(skills, indent=2))
    else:
        print(f"Skills loaded for: {args.task!r}\n")
        for s in skills:
            status = "✓ content loaded" if s["content"] and "[File not found" not in s["content"] else "⚠ no file"
            print(f"  - {s['skill_name']} (matched: `{s['matched_by']}`) [{status}]")


if __name__ == "__main__":
    main()
