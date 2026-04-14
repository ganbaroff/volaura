"""Constitution compliance checker — agents verify code against the 5 Foundation Laws.

This is the automated enforcement of the Constitution. Every agent can call
these checks to ground proposals in actual code violations.
"""

from __future__ import annotations

from pathlib import Path

from .code_tools import grep_codebase, read_file


def check_all_laws() -> dict[str, list[str]]:
    """Run all Constitution law checks. Returns {law: [violations]}."""
    results = {}

    # Law 1: NEVER RED
    red_violations = grep_codebase(
        r"text-red-|bg-red-|border-red-|#[Ff][Ff]0000|#[Dd][Cc]2626|#[Ee][Ff]4444",
        file_glob="*.tsx",
        max_results=50,
    )
    results["LAW_1_NEVER_RED"] = [
        line for line in red_violations.split("\n")
        if line and not line.startswith("NO MATCHES")
    ]

    # Law 4: Animation > 800ms (strictly OVER 800 — 800 is allowed maximum)
    # Matches: duration = 850, duration: 1000, duration = 2000, etc.
    # Does NOT match: duration = 800 (exactly at limit is fine)
    animation_violations = grep_codebase(
        r"duration[:\s=]+[\"']?(?:8[1-9]\d|9\d{2}|[1-9]\d{3,})",
        file_glob="*.tsx",
        max_results=20,
    )
    results["LAW_4_ANIMATION_SAFETY"] = [
        line for line in animation_violations.split("\n")
        if line
        and not line.startswith("NO MATCHES")
        # Exclude comments explaining the rule
        and "// " not in line.split(":")[0]
        and not line.lstrip().startswith("*")
        and not line.lstrip().startswith("//")
    ]

    # Law 3: Shame language — exclude comment lines / JSDoc that describe the rule
    shame_violations = grep_codebase(
        r"haven't done|not completed|days behind|0 of \d|you failed|wrong answer|% complete",
        file_glob="*.tsx",
        max_results=20,
    )
    def _is_comment_line(grep_line: str) -> bool:
        """Check if the matched grep line is inside a comment (not live code)."""
        # grep format: "path:linenum: <content>"
        parts = grep_line.split(":", 2)
        content = parts[2].lstrip() if len(parts) >= 3 else grep_line.lstrip()
        return (
            content.startswith("*")
            or content.startswith("//")
            or content.startswith("/*")
            or content.startswith("{/*")   # JSX comment
        )

    results["LAW_3_SHAME_FREE"] = [
        line for line in shame_violations.split("\n")
        if line
        and not line.startswith("NO MATCHES")
        # Exclude JSDoc/comment lines that are documenting the rule, not violating it
        and not _is_comment_line(line)
    ]

    # Crystal Law 5 + G9: Leaderboard
    leaderboard_violations = grep_codebase(
        r"leaderboard|ranking|ranked|top \d+%",
        file_glob="*.tsx",
        max_results=20,
    )
    results["CRYSTAL_LAW_5_NO_LEADERBOARD"] = [
        line for line in leaderboard_violations.split("\n")
        if line
        and not line.startswith("NO MATCHES")
        # Exclude comment-only lines (removals/notes about the rule are not violations)
        and not _is_comment_line(line)
        # Exclude the deleted/redirect leaderboard page itself (it's a tombstone, not active UI)
        and "/leaderboard/page.tsx" not in line.split(":")[0]
    ]

    return results


def format_report(results: dict[str, list[str]]) -> str:
    """Format constitution check results for agent consumption."""
    lines = ["# CONSTITUTION COMPLIANCE REPORT\n"]
    total_violations = 0

    for law, violations in results.items():
        count = len(violations)
        total_violations += count
        status = "PASS" if count == 0 else f"FAIL ({count} violations)"
        lines.append(f"## {law}: {status}")
        for v in violations[:10]:
            lines.append(f"  - {v}")
        if count > 10:
            lines.append(f"  ... ({count - 10} more)")
        lines.append("")

    lines.insert(1, f"**Total violations: {total_violations}**\n")
    return "\n".join(lines)


def run_full_audit() -> str:
    """Run full constitution audit and return formatted report."""
    results = check_all_laws()
    return format_report(results)
