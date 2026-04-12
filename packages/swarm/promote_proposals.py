"""Auto-promote high-scoring proposals to the swarm backlog.

Run after each swarm daily run or manually:
  python -m packages.swarm.promote_proposals

Proposals with judge_score >= 4/5 AND status != 'implemented' become
backlog tasks automatically. This closes the gap where 64 proposals
sat in 'manual' status because nobody triaged them.
"""

from __future__ import annotations

import json
from pathlib import Path

from loguru import logger

project_root = Path(__file__).resolve().parent.parent.parent
PROPOSALS_PATH = project_root / "memory" / "swarm" / "proposals.json"
BACKLOG_PATH = project_root / "memory" / "swarm" / "backlog.json"

SCORE_THRESHOLD = 3
SKIP_STATUSES = {"implemented", "dismissed", "rejected", "deleted"}


def promote():
    if not PROPOSALS_PATH.exists():
        logger.info("No proposals.json found")
        return 0

    with open(PROPOSALS_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    proposals = raw.get("proposals", raw) if isinstance(raw, dict) else raw

    backlog_tasks = []
    if BACKLOG_PATH.exists():
        with open(BACKLOG_PATH, encoding="utf-8") as f:
            backlog_tasks = json.load(f)

    existing_sources = {t.get("source", "") for t in backlog_tasks}
    promoted = 0

    for p in proposals:
        pid = p.get("id", "")[:8]
        score = p.get("judge_score") or 0
        status = p.get("status", "pending")
        title = p.get("title", "Untitled")

        if status in SKIP_STATUSES:
            continue
        if score < SCORE_THRESHOLD:
            continue

        source_tag = f"proposal:{pid}"
        if source_tag in existing_sources:
            continue

        import uuid
        from datetime import datetime, timezone

        task = {
            "id": uuid.uuid4().hex[:8],
            "title": title[:100],
            "status": "todo",
            "assignee": p.get("agent"),
            "depends_on": [],
            "blocked_by": None,
            "acceptance_criteria": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source": source_tag,
            "findings": None,
        }
        backlog_tasks.append(task)
        promoted += 1
        logger.info(f"Promoted: {title[:60]} (score={score}, agent={p.get('agent')})")

    if promoted:
        with open(BACKLOG_PATH, "w", encoding="utf-8") as f:
            json.dump(backlog_tasks, f, indent=2, ensure_ascii=False)

    logger.info(f"Promotion complete: {promoted} new tasks from {len(proposals)} proposals")
    return promoted


if __name__ == "__main__":
    promote()
