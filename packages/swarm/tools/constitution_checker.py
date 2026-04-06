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

    # Law 4: Animation > 800ms
    animation_violations = grep_codebase(
        r"duration[:\s=]+[\"']?\d{4,}|duration[:\s=]+[89]\d{2,}|duration[:\s=]+[1-9]\d{3,}",
        file_glob="*.tsx",
        max_results=20,
    )
    results["LAW_4_ANIMATION_SAFETY"] = [
        line for line in animation_violations.split("\n")
        if line and not line.startswith("NO MATCHES")
    ]

    # Law 3: Shame language
    shame_violations = grep_codebase(
        r"haven't done|not completed|days behind|0 of \d|you failed|wrong answer|% complete",
        file_glob="*.tsx",
        max_results=20,
    )
    results["LAW_3_SHAME_FREE"] = [
        line for line in shame_violations.split("\n")
        if line and not line.startswith("NO MATCHES")
    ]

    # Crystal Law 5 + G9: Leaderboard
    leaderboard_violations = grep_codebase(
        r"leaderboard|ranking|ranked|top \d+%",
        file_glob="*.tsx",
        max_results=20,
    )
    results["CRYSTAL_LAW_5_NO_LEADERBOARD"] = [
        line for line in leaderboard_violations.split("\n")
        if line and not line.startswith("NO MATCHES")
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
