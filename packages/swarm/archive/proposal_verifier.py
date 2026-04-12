#!/usr/bin/env python3
"""Proposal Verifier — grounds proposals in real code.

Problem: agents cite files that don't exist (e.g. "fix apps/api/app/routers/foo.py"
when foo.py was renamed or never existed). CTO acts on bad intel.

Solution: before storing a proposal, extract all file paths mentioned in the
proposal text, verify they exist in the repo, and score groundedness.

Groundedness score:
  is_grounded = True  if reference_score >= 0.70
  is_grounded = False if reference_score <  0.70 OR no files cited

Proposals with is_grounded=False are:
  - Still stored (never silently dropped)
  - Tagged with [UNGROUNDED] in title for CTO visibility
  - Logged to memory/swarm/ungrounded-proposals.jsonl for audit

Usage:
    from swarm.proposal_verifier import verify_proposal_references
    result = verify_proposal_references(proposal_content, project_root)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ── Patterns ──────────────────────────────────────────────────────────────────

# Match common Volaura repo paths:
# apps/api/..., apps/web/..., packages/..., supabase/..., memory/..., docs/..., scripts/...
_FILE_PATH_RE = re.compile(
    r"(?:^|[\s`'\"])("
    r"(?:apps/(?:api|web)|packages|supabase|memory|docs|scripts|\.github)"
    r"[/\w.\-]+"                # path segments
    r"(?:\.[a-zA-Z]{1,6})"     # extension required
    r")",
    re.MULTILINE,
)

# Match Python function/class references (may not exist as files but are useful to track)
_FUNCTION_RE = re.compile(r"`(\w+(?:\.\w+)+)\(\)`")

GROUNDEDNESS_THRESHOLD = 0.70
UNGROUNDED_LOG = Path(__file__).parent.parent.parent / "memory" / "swarm" / "ungrounded-proposals.jsonl"


# ── Core verification ──────────────────────────────────────────────────────────

def verify_proposal_references(
    proposal_content: str,
    project_root: Path,
    proposal_title: str = "",
) -> dict:
    """Check if file paths cited in a proposal actually exist.

    Args:
        proposal_content: Full text of the proposal
        project_root: Repo root path
        proposal_title: For logging purposes

    Returns:
        {
            "claimed_files": list[str],    # all paths found in text
            "valid_files": list[str],      # paths that exist
            "invalid_files": list[str],    # paths that don't exist
            "reference_score": float,      # valid / claimed (0.0 if no claims)
            "is_grounded": bool,           # score >= threshold OR no files cited
            "missing_summary": str,        # human-readable summary of missing files
        }
    """
    # Extract all file path mentions
    claimed_files = list(dict.fromkeys(  # deduplicate, preserve order
        m.group(1) for m in _FILE_PATH_RE.finditer(proposal_content)
    ))

    if not claimed_files:
        # No file references — not ungrounded, just abstract. Mark as grounded.
        return {
            "claimed_files": [],
            "valid_files": [],
            "invalid_files": [],
            "reference_score": 1.0,
            "is_grounded": True,
            "missing_summary": "No file paths cited — abstract proposal.",
        }

    valid_files = []
    invalid_files = []

    for path_str in claimed_files:
        full_path = project_root / path_str
        if full_path.exists():
            valid_files.append(path_str)
        else:
            invalid_files.append(path_str)

    reference_score = len(valid_files) / len(claimed_files) if claimed_files else 1.0
    is_grounded = reference_score >= GROUNDEDNESS_THRESHOLD

    missing_summary = ""
    if invalid_files:
        missing_summary = f"{len(invalid_files)}/{len(claimed_files)} files not found: {', '.join(invalid_files[:5])}"
        if len(invalid_files) > 5:
            missing_summary += f" (+{len(invalid_files) - 5} more)"

    return {
        "claimed_files": claimed_files,
        "valid_files": valid_files,
        "invalid_files": invalid_files,
        "reference_score": round(reference_score, 3),
        "is_grounded": is_grounded,
        "missing_summary": missing_summary,
    }


def tag_proposal_if_ungrounded(proposal: dict, project_root: Path) -> dict:
    """Run verification and mutate proposal in-place if ungrounded.

    Adds to proposal:
      - "groundedness": the verification result dict
      - Prepends "[UNGROUNDED] " to title if not grounded (CTO visibility)

    Also logs to ungrounded-proposals.jsonl for audit trail.

    Args:
        proposal: Proposal dict with "title" and "content" keys
        project_root: Repo root

    Returns:
        Mutated proposal dict
    """
    content = proposal.get("content", "")
    if isinstance(content, dict):
        content = json.dumps(content)
    content = str(content)

    result = verify_proposal_references(
        content,
        project_root,
        proposal_title=proposal.get("title", ""),
    )
    proposal["groundedness"] = result

    if not result["is_grounded"] and result["claimed_files"]:
        # Tag title for CTO visibility — never silently hide
        if not proposal.get("title", "").startswith("[UNGROUNDED]"):
            proposal["title"] = f"[UNGROUNDED] {proposal.get('title', '')}"

        # Log to audit file
        _log_ungrounded(proposal, result)

    return proposal


def _log_ungrounded(proposal: dict, groundedness: dict) -> None:
    """Append ungrounded proposal to audit log."""
    UNGROUNDED_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": proposal.get("agent", "unknown"),
        "title": proposal.get("title", ""),
        "reference_score": groundedness["reference_score"],
        "invalid_files": groundedness["invalid_files"],
        "missing_summary": groundedness["missing_summary"],
    }
    with open(UNGROUNDED_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


# ── Batch verification (for auditing existing proposals) ──────────────────────

def audit_proposals_file(proposals_file: Path, project_root: Path) -> dict:
    """Audit all proposals in proposals.json and return groundedness report.

    Args:
        proposals_file: Path to proposals.json
        project_root: Repo root

    Returns:
        {
            "total": int,
            "grounded": int,
            "ungrounded": int,
            "avg_score": float,
            "ungrounded_list": list[dict],
        }
    """
    if not proposals_file.exists():
        return {"total": 0, "grounded": 0, "ungrounded": 0, "avg_score": 0.0, "ungrounded_list": []}

    with open(proposals_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    proposals = data if isinstance(data, list) else data.get("proposals", [])
    scores = []
    ungrounded_list = []

    for p in proposals:
        content = p.get("content", "")
        if isinstance(content, dict):
            content = json.dumps(content)
        result = verify_proposal_references(str(content), project_root, p.get("title", ""))
        scores.append(result["reference_score"])
        if not result["is_grounded"] and result["claimed_files"]:
            ungrounded_list.append({
                "title": p.get("title", ""),
                "agent": p.get("agent", ""),
                "score": result["reference_score"],
                "missing": result["missing_summary"],
            })

    return {
        "total": len(proposals),
        "grounded": len(proposals) - len(ungrounded_list),
        "ungrounded": len(ungrounded_list),
        "avg_score": round(sum(scores) / len(scores), 3) if scores else 0.0,
        "ungrounded_list": ungrounded_list,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    _root = Path(__file__).parent.parent.parent
    _proposals = _root / "memory" / "swarm" / "proposals.json"
    report = audit_proposals_file(_proposals, _root)
    print(f"Proposals: {report['total']}")
    print(f"Grounded:  {report['grounded']}")
    print(f"Ungrounded:{report['ungrounded']}")
    print(f"Avg score: {report['avg_score']:.1%}")
    if report["ungrounded_list"]:
        print("\nUngrounded proposals:")
        for item in report["ungrounded_list"]:
            print(f"  [{item['score']:.0%}] {item['title'][:70]} — {item['missing']}")
