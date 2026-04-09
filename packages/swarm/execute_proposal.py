"""Execute Proposal — run pending high/critical proposals through the Coordinator.

Reads proposals.json, filters actionable items, calls Coordinator.run() for each,
and updates proposal status to "implemented" with a result summary.

Fulfils UNFULFILLED-PROMISES.md item #23.

Usage:
    python -m packages.swarm.execute_proposal --dry-run
    python -m packages.swarm.execute_proposal --id 08c72c82
    python -m packages.swarm.execute_proposal --limit 3
    python -m packages.swarm.execute_proposal  # runs up to 5 high/critical pending proposals
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure packages/ is importable when invoked as `python -m packages.swarm.execute_proposal`
project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from dotenv import load_dotenv
load_dotenv(project_root / "apps" / "api" / ".env")

from loguru import logger


# ── Constants ─────────────────────────────────────────────────────────────────

PROPOSALS_FILE = project_root / "memory" / "swarm" / "proposals.json"
DEFAULT_LIMIT = 5
ACTIONABLE_STATUSES = {"pending", "manual"}
ACTIONABLE_SEVERITIES = {"high", "critical"}


# ── Proposal I/O ──────────────────────────────────────────────────────────────

def _load_proposals() -> dict:
    """Load the proposals store from disk."""
    if not PROPOSALS_FILE.exists():
        logger.warning("proposals.json not found at {p}", p=PROPOSALS_FILE)
        return {"schema_version": "1.0", "proposals": []}
    with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_proposals(data: dict) -> None:
    """Persist the proposals store to disk (atomic-ish write)."""
    tmp = PROPOSALS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(PROPOSALS_FILE)


def _filter_proposals(
    proposals: list[dict],
    proposal_id: str | None = None,
) -> list[dict]:
    """Return proposals eligible for execution.

    Eligibility:
      - status in {"pending", "manual"}
      - severity in {"high", "critical"}
      - is_grounded == True (skipped when field absent — field does not exist yet)

    If proposal_id is given, only that specific proposal is returned (regardless
    of its status/severity — allows force-running a single item).
    """
    if proposal_id:
        matches = [p for p in proposals if p.get("id") == proposal_id]
        if not matches:
            logger.warning("No proposal found with id={id}", id=proposal_id)
        return matches

    result = []
    for p in proposals:
        status = p.get("status", "")
        severity = p.get("severity", "")
        # is_grounded gate — only active when field is explicitly present
        is_grounded = p.get("is_grounded")
        if is_grounded is not None and not is_grounded:
            continue
        if status in ACTIONABLE_STATUSES and severity in ACTIONABLE_SEVERITIES:
            result.append(p)

    # Deterministic order: critical first, then high; then by timestamp ascending
    _sev_rank = {"critical": 0, "high": 1}
    result.sort(key=lambda p: (_sev_rank.get(p.get("severity", ""), 9), p.get("timestamp", "")))
    return result


# ── Runner (reuses autonomous_run._call_agent pattern) ────────────────────────

def _build_proposal_prompt(proposal: dict, project_state: str) -> str:
    """Build an agent prompt from a proposal dict."""
    title = proposal.get("title", "Untitled")
    content = proposal.get("content", "")
    agent = proposal.get("agent", "Unknown Agent")
    severity = proposal.get("severity", "unknown").upper()
    pid = proposal.get("id", "?")

    return f"""You are a senior VOLAURA engineer executing a swarm proposal.

PROPOSAL [{pid}] — {severity}
Title: {title}
Proposed by: {agent}
Details: {content}

PROJECT STATE:
{project_state[:3000]}

YOUR TASK:
Execute this proposal by producing a concrete implementation plan.
- Identify the specific files, functions, or configs that must change.
- Write a step-by-step implementation plan (be specific, no vague advice).
- Estimate effort in hours.
- Confirm whether this proposal is still relevant given the current project state.
- If already implemented, say so clearly.

RESPONSE FORMAT (strict JSON — no markdown wrapper):
{{
    "severity": "P1",
    "category": "infra",
    "files": ["path/to/file.py"],
    "summary": "What this proposal addresses and current status (10-500 chars)",
    "recommendation": "Concrete next action or confirmation it is done (10-500 chars)",
    "confidence": 0.85,
    "est_impact": "high"
}}
"""


async def _make_runner(env: dict[str, str], project_state: str):
    """Return an async runner fn compatible with Coordinator(runner=...)."""
    from swarm.autonomous_run import _call_agent  # type: ignore[import]

    async def _coordinator_runner(agent_id: str, input_data: dict) -> dict | None:
        instruction = input_data.get("instruction", "")
        squad_name = input_data.get("squad_name", agent_id)
        perspective = {
            "name": agent_id,
            "lens": f"[{squad_name}] {instruction}",
            "routed_skills": [],
            "bound_files": "",
        }
        from swarm.autonomous_run import _build_agent_prompt  # type: ignore[import]
        prompt = _build_agent_prompt(perspective, project_state, "coordinator", project_root=project_root)
        return await _call_agent(prompt, agent_id, env)

    return _coordinator_runner


# ── Core execution ─────────────────────────────────────────────────────────────

async def execute_one(
    proposal: dict,
    env: dict[str, str],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Execute a single proposal through the Coordinator.

    Returns a result dict with keys: proposal_id, status, summary, error.
    """
    pid = proposal.get("id", "?")
    title = proposal.get("title", "Untitled")[:80]
    severity = proposal.get("severity", "?").upper()

    logger.info(
        "Executing proposal [{pid}] [{sev}] {title}",
        pid=pid,
        sev=severity,
        title=title,
    )

    if dry_run:
        logger.info("  DRY RUN — would call Coordinator.run('{title}')", title=title)
        return {
            "proposal_id": pid,
            "status": "dry_run",
            "summary": f"[DRY RUN] Would execute: {title}",
            "error": None,
        }

    try:
        from swarm.autonomous_run import _read_project_state  # type: ignore[import]
        from swarm.coordinator import Coordinator  # type: ignore[import]

        project_state = _read_project_state(project_root)
        runner = await _make_runner(env, project_state)

        run_id = f"exec-{pid}-{int(time.time())}"
        coord = Coordinator(runner=runner, run_id=run_id)

        task_desc = (
            f"Execute proposal [{pid}] [{severity}]: {title}. "
            f"Details: {proposal.get('content', '')[:300]}"
        )
        result = await coord.run(task_desc)

        summary = result.synthesis or f"{len(result.findings)} findings from {result.succeeded} agents."
        if result.priority_action:
            summary += f" PRIORITY: {result.priority_action[:150]}"

        logger.success(
            "Proposal [{pid}] done — {n} findings, priority={p}",
            pid=pid,
            n=len(result.findings),
            p=(result.priority_action or "none")[:60],
        )

        return {
            "proposal_id": pid,
            "status": "implemented",
            "summary": summary[:500],
            "error": None,
            "finding_count": len(result.findings),
            "succeeded_agents": result.succeeded,
            "failed_agents": result.failed,
        }

    except Exception as exc:
        logger.error("Proposal [{pid}] failed: {e}", pid=pid, e=str(exc)[:200])
        return {
            "proposal_id": pid,
            "status": "error",
            "summary": "",
            "error": str(exc)[:300],
        }


def _update_proposals(
    data: dict,
    results: list[dict[str, Any]],
    dry_run: bool = False,
) -> int:
    """Update proposal statuses in-place based on execution results.

    Returns the count of proposals updated.
    """
    if dry_run:
        return 0

    result_map = {r["proposal_id"]: r for r in results}
    updated = 0
    now = datetime.now(timezone.utc).isoformat()

    for proposal in data.get("proposals", []):
        pid = proposal.get("id")
        if pid not in result_map:
            continue
        res = result_map[pid]
        if res["status"] in ("implemented", "error"):
            proposal["status"] = "implemented" if res["status"] == "implemented" else proposal["status"]
            proposal["resolved_at"] = now
            proposal["ceo_decision"] = f"[execute_proposal.py] {res['summary'] or res['error'] or ''}".strip()[:500]
            proposal["ceo_decision_at"] = now
            updated += 1

    return updated


# ── CLI ───────────────────────────────────────────────────────────────────────

async def run(
    proposal_id: str | None = None,
    limit: int = DEFAULT_LIMIT,
    dry_run: bool = False,
) -> None:
    """Main async entrypoint."""
    data = _load_proposals()
    proposals = data.get("proposals", [])

    eligible = _filter_proposals(proposals, proposal_id=proposal_id)

    if not eligible:
        logger.info("No eligible proposals found (status=pending/manual, severity=high/critical).")
        return

    # Apply limit
    batch = eligible[:limit]
    skipped = len(eligible) - len(batch)

    logger.info(
        "execute_proposal: {n} eligible, running {b}, skipping {s} (limit={lim})",
        n=len(eligible),
        b=len(batch),
        s=skipped,
        lim=limit,
    )

    if dry_run:
        print(f"\n{'='*60}")
        print(f"DRY RUN — would execute {len(batch)} proposal(s):")
        print(f"{'='*60}")
        for p in batch:
            print(
                f"  [{p.get('id')}] [{p.get('severity','?').upper()}] "
                f"{p.get('title','Untitled')[:70]}"
            )
        if skipped:
            print(f"  ... and {skipped} more (increase --limit to include)")
        print(f"{'='*60}\n")

    env = dict(os.environ)
    results: list[dict[str, Any]] = []

    for proposal in batch:
        result = await execute_one(proposal, env, dry_run=dry_run)
        results.append(result)

    updated = _update_proposals(data, results, dry_run=dry_run)

    if not dry_run and updated:
        _save_proposals(data)
        logger.info("proposals.json updated — {n} proposals marked implemented.", n=updated)

    # Summary report
    print(f"\n{'='*60}")
    print(f"execute_proposal summary ({len(results)} processed)")
    print(f"{'='*60}")
    for r in results:
        icon = "OK" if r["status"] in ("implemented", "dry_run") else "FAIL"
        agents = f" [{r.get('succeeded_agents', 0)} agents]" if "succeeded_agents" in r else ""
        print(f"  {icon} [{r['proposal_id']}] {r['status']}{agents}")
        if r.get("summary"):
            print(f"      {r['summary'][:120]}")
        if r.get("error"):
            print(f"      ERROR: {r['error'][:120]}")
    if skipped:
        print(f"\n  {skipped} proposal(s) skipped (limit={limit}, use --limit to increase)")
    print(f"{'='*60}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute pending high/critical swarm proposals via the Coordinator.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m packages.swarm.execute_proposal --dry-run
  python -m packages.swarm.execute_proposal --id 08c72c82
  python -m packages.swarm.execute_proposal --limit 3
  python -m packages.swarm.execute_proposal  # runs up to 5 proposals
        """,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would run without executing or writing anything.",
    )
    parser.add_argument(
        "--id",
        dest="proposal_id",
        default=None,
        metavar="PROPOSAL_ID",
        help="Run a single specific proposal by ID (bypasses severity/status filter).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        metavar="N",
        help=f"Max proposals to execute per invocation (default: {DEFAULT_LIMIT}).",
    )
    args = parser.parse_args()

    asyncio.run(
        run(
            proposal_id=args.proposal_id,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    )


if __name__ == "__main__":
    main()
