#!/usr/bin/env python3
"""One-shot seed of atlas_obligations from memory/atlas/deadlines.md.

Spec: memory/atlas/OBLIGATION-SYSTEM-SPEC-2026-04-18.md §Migration-from-deadlines.md

Idempotent: the table has UNIQUE (title) in migration 20260418170000_atlas_obligations.sql.
PostgREST does not expose ON CONFLICT DO NOTHING directly through `insert`, so we use
`upsert(on_conflict='title', ignore_duplicates=True)` which lowers to
`INSERT ... ON CONFLICT (title) DO NOTHING`. Re-runs are safe.

Run:
    export SUPABASE_URL=...
    export SUPABASE_SERVICE_KEY=...
    python scripts/seed_atlas_obligations.py

After a clean run, add DEPRECATED banner to memory/atlas/deadlines.md pointing
to the DB and admin/obligations route.
"""

from __future__ import annotations

import os
import sys

try:
    from supabase import create_client
except ImportError:
    sys.stderr.write("supabase package not installed — pip install supabase\n")
    sys.exit(2)

from loguru import logger


SEEDS: list[dict] = [
    {
        "title": "83(b) election — DHL Express Baku → IRS",
        "description": (
            "Mail 83(b) election to IRS within 30 days of incorporation (2026-04-14). "
            "Postmark must be on/before 2026-05-14. Deliver via DHL Express Baku for tracked proof."
        ),
        "category": "tax",
        "deadline": "2026-05-14T23:59:59+04:00",  # Baku EOD
        "consequence_if_missed": (
            "Future equity appreciation taxed as ordinary income at vesting. "
            "For $7M post-money 85% CEO stake — 7-figure ordinary-income penalty over 4yr vest."
        ),
        "owner": "CEO",
        "status": "open",
        "proof_required": [
            "DHL Express tracking number Baku → IRS",
            "Photo of postmarked envelope (Apr 28 or earlier)",
            "Photo of IRS delivery confirmation",
        ],
        "nag_schedule": "aggressive",
        "source": "deadlines.md L29 + company-state.md 2026-04-18",
    },
    {
        "title": "ITIN application — IRS Form W-7",
        "description": (
            "File W-7 in parallel with Stripe Atlas filing. IRS processing ~6 weeks. "
            "ITIN is required for any program payout (Stripe, many US partners)."
        ),
        "category": "tax",
        "deadline": None,  # trigger-based
        "trigger_event": "Run in parallel with Stripe Atlas filing (processing ~6 weeks)",
        "consequence_if_missed": (
            "~6 week delay on any program payout requiring ITIN/SSN (most do)."
        ),
        "owner": "CEO",
        "status": "open",
        "proof_required": [
            "W-7 submission confirmation",
            "ITIN letter from IRS",
        ],
        "nag_schedule": "standard",
        "source": "deadlines.md L38",
    },
    {
        "title": "WUF13 Baku — VOLAURA launch readiness",
        "description": (
            "All P0 launch blockers closed ahead of WUF13 Baku (13 June 2026). "
            "No equivalent AZ-local media window for ~12 months after this."
        ),
        "category": "launch",
        "deadline": "2026-06-13T00:00:00+04:00",
        "consequence_if_missed": (
            "No alternative launch moment with equivalent AZ-local media weight. "
            "Next window ~12 months."
        ),
        "owner": "both",
        "status": "open",
        "proof_required": [
            "All P0 items in docs/PRE-LAUNCH-BLOCKERS-STATUS.md closed",
            "WUF13 registration + badge confirmation",
        ],
        "nag_schedule": "standard",
        "source": "deadlines.md L22",
    },
    {
        "title": "GITA grant + provisional patent (NOT PURSUING)",
        "description": (
            "GITA grant was reviewed and rejected as funding source (terms not aligned). "
            "Provisional patent strategy deferred until post-launch (post-WUF13) per CEO decision. "
            "Kept as deferred row so the deadlines.md archive has a pointer — not a forgotten commitment."
        ),
        "category": "funding",
        "deadline": None,
        "consequence_if_missed": "None — both items explicitly de-scoped by CEO.",
        "owner": "CEO",
        "status": "deferred",
        "proof_required": [],
        "nag_schedule": "silent",
        "deferred_until": "2026-07-01T00:00:00+04:00",  # revisit window after WUF13
        "source": "deadlines.md (historical)",
    },
]


def main() -> int:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
    if not url or not key:
        logger.error("SUPABASE_URL / SUPABASE_SERVICE_KEY must be set in env.")
        return 2

    client = create_client(url, key)
    inserted = 0
    skipped = 0

    for seed in SEEDS:
        try:
            # ignore_duplicates=True → INSERT ... ON CONFLICT (title) DO NOTHING
            res = (
                client.table("atlas_obligations")
                .upsert(seed, on_conflict="title", ignore_duplicates=True)
                .execute()
            )
            if res.data:
                inserted += 1
                logger.info("Inserted: {t}", t=seed["title"])
            else:
                skipped += 1
                logger.info("Already present (skipped): {t}", t=seed["title"])
        except Exception as e:  # noqa: BLE001 — surface the specific row that failed
            logger.error("Seed failed for {t}: {e}", t=seed["title"], e=str(e))
            return 3

    logger.info("Seed complete: inserted={i} skipped={s} total={t}", i=inserted, s=skipped, t=len(SEEDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
