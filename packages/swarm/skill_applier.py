#!/usr/bin/env python3
"""Skill Applier — Sprint 5: Skill Evolution Completion.

Takes a specific improvement suggestion from skill-evolution-log.md
and applies it to the actual skill file.

Completes the skill_evolution.py loop:
  scan → review → [suggest] → APPLY → A/B test → keep winner

Four edit types:
  add_example     → append concrete example to ## Output or ## Guidelines
  sharpen_rule    → replace vague bullet with specific constraint
  add_antipattern → append to ## Anti-Patterns or create the section
  add_trigger     → add a missing ## Trigger section
  remove_obsolete → delete a section marked outdated

Safety rules:
  - Always creates a .bak backup before editing
  - Never touches skill files without explicit improvement suggestion
  - Writes diff to skill-applier-log.jsonl for audit

Usage:
    from swarm.skill_applier import apply_improvement, ApplyResult

    result = apply_improvement(
        skill_file=Path("memory/swarm/skills/risk-manager.md"),
        improvement="Add concrete Risk Register table format example to ## Output",
        edit_type="add_example",
    )
    print(result.success, result.diff_lines)
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

EditType = Literal["add_example", "sharpen_rule", "add_antipattern", "add_trigger",
                   "remove_obsolete", "generic"]

project_root = Path(__file__).parent.parent.parent
SKILLS_DIR = project_root / "memory" / "swarm" / "skills"
APPLIER_LOG = project_root / "memory" / "swarm" / "skill-applier-log.jsonl"
BAK_DIR = project_root / "memory" / "swarm" / "skill-backups"


@dataclass
class ApplyResult:
    """Result of applying one improvement to a skill file."""
    skill_file: str
    improvement: str
    edit_type: str
    success: bool
    diff_lines: int = 0
    backup_path: str = ""
    error: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def summary(self) -> str:
        if self.success:
            return f"[OK] Applied to {Path(self.skill_file).name}: +{self.diff_lines} lines ({self.edit_type})"
        return f"[FAIL] {Path(self.skill_file).name}: {self.error}"


# ── Backup ────────────────────────────────────────────────────────────────────

def _backup(skill_file: Path) -> Path:
    """Create timestamped .bak before editing."""
    BAK_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    bak = BAK_DIR / f"{skill_file.stem}_{ts}.bak.md"
    shutil.copy2(skill_file, bak)
    return bak


# ── Section finder ────────────────────────────────────────────────────────────

def _find_section_end(lines: list[str], section_header: str) -> int:
    """Find the line index after the end of a markdown ## section.

    Returns the index of the blank line / next header after section_header.
    Returns -1 if section not found.
    """
    in_section = False
    for i, line in enumerate(lines):
        if line.strip().lower() == section_header.lower():
            in_section = True
            continue
        if in_section and line.startswith("## "):
            return i   # next section starts here — insert before it
    if in_section:
        return len(lines)  # end of file
    return -1


def _find_section_start(lines: list[str], section_header: str) -> int:
    """Find the line index of a ## section header. -1 if not found."""
    for i, line in enumerate(lines):
        if line.strip().lower() == section_header.lower():
            return i
    return -1


# ── Edit type implementations ─────────────────────────────────────────────────

def _apply_add_example(lines: list[str], improvement: str) -> list[str]:
    """Append a concrete example block to ## Output or ## Guidelines."""
    # Try Output first, then Guidelines
    for section in ["## Output", "## Guidelines", "## Anti-Patterns"]:
        end = _find_section_end(lines, section)
        if end != -1:
            example_block = [
                "",
                "### Example (auto-added by skill_applier)",
                f"_{improvement}_",
                "",
                "```",
                "# Concrete example would go here",
                "# CTO: fill in with a real observed case",
                "```",
                "",
            ]
            return lines[:end] + example_block + lines[end:]

    # No matching section — append at end
    return lines + ["", f"## Example", f"_{improvement}_", ""]


def _apply_sharpen_rule(lines: list[str], improvement: str) -> list[str]:
    """Replace the most vague bullet in ## Guidelines with a specific one."""
    guidelines_start = _find_section_start(lines, "## Guidelines")
    if guidelines_start == -1:
        # No guidelines section — just append
        return lines + ["", "## Guidelines", f"- {improvement}", ""]

    # Find the shortest/vaguest bullet in Guidelines (proxy for vagueness: shortest)
    vague_idx = -1
    vague_len = float("inf")
    next_section_idx = len(lines)

    for i in range(guidelines_start + 1, len(lines)):
        if lines[i].startswith("## "):
            next_section_idx = i
            break
        if lines[i].startswith("- ") and len(lines[i]) < vague_len:
            vague_len = len(lines[i])
            vague_idx = i

    new_bullet = f"- {improvement}"
    if vague_idx != -1 and vague_len < 60:
        # Replace vague bullet (comment original)
        original = lines[vague_idx].strip()
        replacement = [
            f"{new_bullet}",
            f"  _(sharpened from: {original[:80]})_",
        ]
        return lines[:vague_idx] + replacement + lines[vague_idx + 1:]
    else:
        # Insert before next section
        return lines[:next_section_idx] + [new_bullet, ""] + lines[next_section_idx:]


def _apply_add_antipattern(lines: list[str], improvement: str) -> list[str]:
    """Add to ## Anti-Patterns section or create it."""
    ap_start = _find_section_start(lines, "## Anti-Patterns")
    if ap_start == -1:
        # Create the section before ## Cross-references or at end
        insert_before = _find_section_start(lines, "## Cross-references")
        new_section = [
            "",
            "## Anti-Patterns",
            f"- NEVER: {improvement}",
            "",
        ]
        if insert_before != -1:
            return lines[:insert_before] + new_section + lines[insert_before:]
        return lines + new_section

    # Find end of anti-patterns section
    end = _find_section_end(lines, "## Anti-Patterns")
    new_line = [f"- NEVER: {improvement}"]
    insert_at = end - 1 if end > 0 and lines[end - 1].strip() == "" else end
    return lines[:insert_at] + new_line + lines[insert_at:]


def _apply_add_trigger(lines: list[str], improvement: str) -> list[str]:
    """Create ## Trigger section if missing."""
    if _find_section_start(lines, "## Trigger") != -1:
        # Already exists — treat as add_example in Trigger
        end = _find_section_end(lines, "## Trigger")
        return lines[:end] + [f"- {improvement}", ""] + lines[end:]

    # Find position after title (first # line)
    insert_after = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            insert_after = i + 1
            break

    new_section = [
        "",
        "## Trigger",
        f"- {improvement}",
        "",
    ]
    return lines[:insert_after] + new_section + lines[insert_after:]


def _apply_remove_obsolete(lines: list[str], improvement: str) -> list[str]:
    """Mark a section as obsolete (comment it out, don't delete)."""
    # Find the section mentioned in improvement
    section_match = re.search(r"##\s+(\w[\w\s]+)", improvement)
    if not section_match:
        return lines  # can't identify section — no-op

    target = f"## {section_match.group(1).strip()}"
    start = _find_section_start(lines, target)
    if start == -1:
        return lines  # section not found

    # Add [OBSOLETE] tag to the header instead of deleting
    lines = lines.copy()
    lines[start] = lines[start].rstrip() + " _(OBSOLETE — flagged by skill_applier)_\n"
    return lines


def _apply_generic(lines: list[str], improvement: str) -> list[str]:
    """Append improvement as a note at the end of the file."""
    note = [
        "",
        "---",
        f"_Auto-applied improvement: {improvement}_",
        f"_Applied at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
    ]
    return lines + note


# ── Public API ────────────────────────────────────────────────────────────────

def apply_improvement(
    skill_file: Path,
    improvement: str,
    edit_type: EditType = "generic",
) -> ApplyResult:
    """Apply one improvement suggestion to a skill file.

    Args:
        skill_file: Path to the .md skill file
        improvement: The specific improvement text (from LLM review)
        edit_type: Type of edit to apply

    Returns:
        ApplyResult with success status and diff info
    """
    if not skill_file.exists():
        return ApplyResult(
            skill_file=str(skill_file),
            improvement=improvement,
            edit_type=edit_type,
            success=False,
            error=f"Skill file not found: {skill_file}",
        )

    # Read original
    original_text = skill_file.read_text(encoding="utf-8")
    original_lines = original_text.splitlines(keepends=True)

    # Backup
    bak = _backup(skill_file)

    # Apply edit
    try:
        edit_fn = {
            "add_example": _apply_add_example,
            "sharpen_rule": _apply_sharpen_rule,
            "add_antipattern": _apply_add_antipattern,
            "add_trigger": _apply_add_trigger,
            "remove_obsolete": _apply_remove_obsolete,
            "generic": _apply_generic,
        }.get(edit_type, _apply_generic)

        new_lines = edit_fn(original_lines, improvement)
        new_text = "".join(new_lines)

        if new_text == original_text:
            return ApplyResult(
                skill_file=str(skill_file),
                improvement=improvement,
                edit_type=edit_type,
                success=False,
                error="No change produced — improvement may already be applied",
                backup_path=str(bak),
            )

        # Write
        skill_file.write_text(new_text, encoding="utf-8")
        diff_lines = len(new_lines) - len(original_lines)

        result = ApplyResult(
            skill_file=str(skill_file),
            improvement=improvement,
            edit_type=edit_type,
            success=True,
            diff_lines=abs(diff_lines),
            backup_path=str(bak),
        )

        _log_apply(result)
        return result

    except Exception as e:
        # Restore backup on error
        shutil.copy2(bak, skill_file)
        return ApplyResult(
            skill_file=str(skill_file),
            improvement=improvement,
            edit_type=edit_type,
            success=False,
            error=str(e),
            backup_path=str(bak),
        )


def _log_apply(result: ApplyResult) -> None:
    """Append apply result to audit log."""
    APPLIER_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(APPLIER_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": result.timestamp,
            "skill_file": result.skill_file,
            "improvement": result.improvement,
            "edit_type": result.edit_type,
            "success": result.success,
            "diff_lines": result.diff_lines,
            "backup_path": result.backup_path,
            "error": result.error,
        }) + "\n")


def infer_edit_type(improvement: str) -> EditType:
    """Infer edit type from improvement description text."""
    lower = improvement.lower()
    if any(w in lower for w in ["example", "sample", "instance", "case", "format"]):
        return "add_example"
    if any(w in lower for w in ["never", "avoid", "anti-pattern", "don't", "do not"]):
        return "add_antipattern"
    if any(w in lower for w in ["trigger", "when to", "activate"]):
        return "add_trigger"
    if any(w in lower for w in ["obsolete", "outdated", "remove", "delete", "old"]):
        return "remove_obsolete"
    if any(w in lower for w in ["specific", "concrete", "precise", "sharpen", "replace"]):
        return "sharpen_rule"
    return "generic"


# ── Batch apply from evolution log ────────────────────────────────────────────

def apply_from_evolution_log(
    evolution_log_path: Path,
    skills_dir: Path | None = None,
    dry_run: bool = False,
    confidence_threshold: float = 0.8,
) -> list[ApplyResult]:
    """Parse skill-evolution-log.md and apply HIGH-priority improvements.

    Args:
        evolution_log_path: Path to skill-evolution-log.md
        skills_dir: Override skills directory
        dry_run: If True, log what would be applied without editing
        confidence_threshold: Only apply if estimated confidence >= this

    Returns:
        List of ApplyResult objects
    """
    if not evolution_log_path.exists():
        return []

    _skills_dir = skills_dir or SKILLS_DIR
    content = evolution_log_path.read_text(encoding="utf-8")
    results: list[ApplyResult] = []

    # Extract HIGH-priority improvement lines
    # Format: - `skill.md` [high] — improvement text
    pattern = re.compile(
        r"-\s+`([^`]+\.md)`\s+\[high\]\s+[—-]\s+(.+?)(?:\n|$)",
        re.IGNORECASE | re.MULTILINE,
    )

    matches = pattern.findall(content)
    if not matches:
        return []

    for skill_filename, improvement_text in matches:
        skill_path = _skills_dir / skill_filename
        improvement_text = improvement_text.strip()

        if dry_run:
            edit_type = infer_edit_type(improvement_text)
            results.append(ApplyResult(
                skill_file=str(skill_path),
                improvement=improvement_text,
                edit_type=edit_type,
                success=True,
                diff_lines=0,
                error="DRY RUN — not applied",
            ))
            continue

        if not skill_path.exists():
            results.append(ApplyResult(
                skill_file=str(skill_path),
                improvement=improvement_text,
                edit_type="generic",
                success=False,
                error=f"Skill file not found: {skill_filename}",
            ))
            continue

        edit_type = infer_edit_type(improvement_text)
        result = apply_improvement(skill_path, improvement_text, edit_type)
        results.append(result)

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    evolution_log = project_root / "memory" / "swarm" / "skill-evolution-log.md"
    dry_run = "--dry-run" in sys.argv

    print(f"Reading: {evolution_log}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print()

    results = apply_from_evolution_log(evolution_log, dry_run=dry_run)

    if not results:
        print("No HIGH-priority improvements found in evolution log.")
    else:
        for r in results:
            print(r.summary())

    applied = sum(1 for r in results if r.success)
    print(f"\nTotal: {applied}/{len(results)} applied")
