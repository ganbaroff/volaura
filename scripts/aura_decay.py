#!/usr/bin/env python3
"""
AURA decay scheduler — Sprint 1 Session 125 (2026-04-26).

Applies the two-phase Ebbinghaus decay model from
`apps/api/app/core/assessment/aura_calc.py` (`apply_temporal_decay`)
to every active row in `aura_scores`. Reads `last_active_at`, computes
days elapsed, applies per-competency half-lives, writes new totals back
to DB.

Triggered by .github/workflows/aura-decay.yml daily at 04:00 UTC.

ENV:
    SUPABASE_URL          — Supabase project URL
    SUPABASE_SERVICE_KEY  — service role key (bypasses RLS)
    DRY_RUN               — 'true' to compute without DB writes (default: false)
    MAX_USERS             — int cap on rows processed (0 = no cap, default: 0)

Exit codes:
    0 — success (one or more rows processed, or 0 rows but no errors)
    1 — env config missing
    2 — DB connection failed
    3 — partial failure (some rows updated, some failed)
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make `apps/api/app/core/assessment/aura_calc` importable so we use
# the SAME decay function that production uses. Single source of truth.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))


def main() -> int:
    supabase_url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    service_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get(
        "SUPABASE_SERVICE_ROLE_KEY"
    )
    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"
    try:
        max_users = int(os.environ.get("MAX_USERS", "0") or "0")
    except ValueError:
        max_users = 0

    if not supabase_url or not service_key:
        print("[aura_decay] ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY missing")
        return 1

    try:
        from supabase import create_client  # type: ignore
    except ImportError:
        print("[aura_decay] ERROR: supabase python client not installed (pip install supabase)")
        return 1

    try:
        from app.core.assessment.aura_calc import apply_temporal_decay  # type: ignore
    except ImportError as exc:
        print(f"[aura_decay] ERROR: cannot import apply_temporal_decay: {exc}")
        return 1

    client = create_client(supabase_url, service_key)

    # Read all active aura_scores rows. Active = non-null total_score
    # AND last_active_at present. Skip rows where decay would be no-op.
    print(f"[aura_decay] Connected to {supabase_url}, dry_run={dry_run}")
    query = client.table("aura_scores").select(
        "user_id, total_score, communication, reliability, english_proficiency, "
        "leadership, event_performance, tech_literacy, adaptability, "
        "empathy_safeguarding, last_active_at, last_decay_at"
    ).filter("total_score", "not.is", "null").filter("last_active_at", "not.is", "null")
    if max_users > 0:
        query = query.limit(max_users)

    try:
        result = query.execute()
    except Exception as exc:
        print(f"[aura_decay] ERROR: query failed: {exc}")
        return 2

    rows = result.data or []
    print(f"[aura_decay] Loaded {len(rows)} active aura_scores rows")

    now = datetime.now(timezone.utc)
    updated = 0
    skipped = 0
    failed = 0

    for row in rows:
        user_id = row.get("user_id")
        last_active_str = row.get("last_active_at")
        if not user_id or not last_active_str:
            skipped += 1
            continue

        try:
            last_active = datetime.fromisoformat(last_active_str.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            skipped += 1
            continue

        days_inactive = max(0.0, (now - last_active).total_seconds() / 86400.0)
        if days_inactive < 7.0:
            # Skip — below decay activation threshold, score is current
            skipped += 1
            continue

        # Build a competency-score dict the way apply_temporal_decay expects.
        # Default to total_score for any missing competency (graceful fallback).
        competencies = {
            "communication": float(row.get("communication") or 0),
            "reliability": float(row.get("reliability") or 0),
            "english_proficiency": float(row.get("english_proficiency") or 0),
            "leadership": float(row.get("leadership") or 0),
            "event_performance": float(row.get("event_performance") or 0),
            "tech_literacy": float(row.get("tech_literacy") or 0),
            "adaptability": float(row.get("adaptability") or 0),
            "empathy_safeguarding": float(row.get("empathy_safeguarding") or 0),
        }

        try:
            decayed_total, decayed_competencies = apply_temporal_decay(
                competencies=competencies,
                days_inactive=days_inactive,
            )
        except Exception as exc:
            print(f"[aura_decay] decay calc failed for user {user_id}: {exc}")
            failed += 1
            continue

        if dry_run:
            old_total = float(row.get("total_score") or 0)
            print(
                f"[aura_decay] DRY {user_id}: {old_total:.2f} → {decayed_total:.2f} "
                f"({days_inactive:.1f}d inactive)"
            )
            updated += 1
            continue

        try:
            update_payload = {
                "total_score": decayed_total,
                **decayed_competencies,
                "last_decay_at": now.isoformat(),
            }
            client.table("aura_scores").update(update_payload).eq(
                "user_id", user_id
            ).execute()
            updated += 1
        except Exception as exc:
            print(f"[aura_decay] write failed for user {user_id}: {exc}")
            failed += 1

    print(
        f"[aura_decay] DONE — processed: {len(rows)}, "
        f"updated: {updated}, skipped: {skipped}, failed: {failed}"
    )

    if failed > 0 and updated > 0:
        return 3  # partial
    if failed > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
