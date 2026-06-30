#!/usr/bin/env python3
"""Load sprint-5 agent-evolved questions into the prod question bank.

IRREVERSIBLE: inserts 70 questions. Run validate_question_bank.py first.
Requires: SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY in env or apps/api/.env.

Usage:
    python scripts/load_sprint5_to_prod.py --dry-run   # preview only
    python scripts/load_sprint5_to_prod.py              # load to prod
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from uuid import uuid4

SPRINT_DIR = Path(__file__).parent / "question-evolution" / "sprint-5"

# Load env from apps/api/.env if not in environment
def _load_env():
    env_path = Path(__file__).parent.parent / "apps" / "api" / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_load_env()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")


def supabase_insert(table: str, rows: list[dict]) -> int:
    """Insert rows via Supabase REST API. Returns count inserted."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set", file=sys.stderr)
        sys.exit(1)

    data = json.dumps(rows).encode("utf-8")
    req = urllib.request.Request(
        f"{SUPABASE_URL}/rest/v1/{table}",
        data=data,
        method="POST",
        headers={
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
    )
    try:
        urllib.request.urlopen(req, timeout=30)
        return len(rows)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        print(f"ERROR: Supabase {e.code}: {body}", file=sys.stderr)
        sys.exit(1)


def load_sprint5(dry_run: bool = True) -> None:
    """Load all sprint-5 questions into the questions table."""
    if not SPRINT_DIR.exists():
        print(f"ERROR: {SPRINT_DIR} not found", file=sys.stderr)
        sys.exit(1)

    all_rows: list[dict] = []
    for f in sorted(SPRINT_DIR.glob("*.json")):
        if f.name == "voting-results.json":
            continue
        with open(f, "r", encoding="utf-8") as fh:
            questions = json.load(fh)
        if not isinstance(questions, list):
            continue

        for q in questions:
            row = {
                "id": q.get("id", str(uuid4())),
                "competency_id": q["competency_id"],
                "difficulty": q.get("difficulty", "medium"),
                "type": q.get("type", "mcq"),
                "scenario_en": q.get("scenario_en"),
                "scenario_az": q.get("scenario_az"),
                "options": q.get("options"),
                "correct_answer": q.get("correct_answer"),
                "expected_concepts": json.dumps({
                    "london_delta": q.get("london_delta"),
                    "az_institutions": q.get("az_institutions"),
                    "tags": q.get("tags"),
                }) if any(q.get(k) for k in ("london_delta", "az_institutions", "tags")) else None,
                "feedback_en": q.get("feedback_en"),
                "feedback_az": q.get("feedback_az"),
                "development_tip_en": q.get("development_tip_en"),
                "development_tip_az": q.get("development_tip_az"),
                "irt_a": q.get("irt_a", 1.0),
                "irt_b": q.get("irt_b", 0.0),
                "irt_c": q.get("irt_c", 0.0),
                "is_ai_generated": True,
                "calibration_status": "estimated",
                "generation_source": "agent_evolved",
                "response_count": 0,
                "is_active": True,
            }
            all_rows.append(row)

        print(f"  {f.name}: {len(questions)} questions")

    print(f"\nTotal: {len(all_rows)} questions ready")

    if dry_run:
        print("\n[DRY RUN] No changes made. Run without --dry-run to load.")
        return

    inserted = supabase_insert("questions", all_rows)
    print(f"\nLoaded {inserted} questions to prod (generation_source=agent_evolved, calibration_status=estimated)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't insert")
    args = parser.parse_args()
    load_sprint5(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
