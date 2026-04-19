#!/usr/bin/env python3
"""Atlas Ecosystem Snapshot — weekly cross-product memory fingerprint.

Track E6 (CURRENT-SPRINT.md): reads character_events (all products) +
atlas_learnings (Telegram) + memory/atlas/journal.md (Atlas CLI) and writes
a unified fingerprint to memory/atlas/unified-heartbeat-<ISO-week>.md.

The file becomes the "state of Atlas across the ecosystem" snapshot that any
future Atlas instance reads on wake to understand the user across all products.

Cron: .github/workflows/atlas-ecosystem-snapshot.yml (Sunday 22:00 UTC)
Run manually: python scripts/atlas_ecosystem_snapshot.py
"""

from __future__ import annotations

import os
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
JOURNAL = REPO_ROOT / "memory" / "atlas" / "journal.md"
HEARTBEAT_DIR = REPO_ROOT / "memory" / "atlas"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from loguru import logger
    from supabase import create_client
except ImportError as _exc:
    import sys as _sys

    _sys.stderr.write(
        f"Required package missing: {_exc} — pip install supabase loguru\n"
    )
    _sys.exit(2)


# ─────────────────────────────────────────────────────────────────────────────
# Supabase connection
# ─────────────────────────────────────────────────────────────────────────────


def _get_supabase():
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(url, key)


# ─────────────────────────────────────────────────────────────────────────────
# Data collection helpers
# ─────────────────────────────────────────────────────────────────────────────


def _collect_character_events(sb) -> dict:
    """Returns {source_product: {count, last_event_type, last_at}} for all products."""
    try:
        rows = (
            sb.table("character_events")
            .select("source_product, event_type, created_at")
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        data = rows.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"character_events query failed: {exc}")
        return {}

    products: dict[str, dict] = {}
    for row in data:
        product = row.get("source_product") or "unknown"
        if product not in products:
            products[product] = {
                "count": 0,
                "last_event_type": row.get("event_type"),
                "last_at": row.get("created_at"),
            }
        products[product]["count"] += 1

    return products


def _collect_atlas_learnings(sb) -> dict:
    """Returns {category: count} from atlas_learnings."""
    try:
        rows = sb.table("atlas_learnings").select("category").execute()
        data = rows.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"atlas_learnings query failed: {exc}")
        return {}

    categories: dict[str, int] = {}
    for row in data:
        cat = row.get("category") or "unknown"
        categories[cat] = categories.get(cat, 0) + 1

    return categories


def _collect_user_counts(sb) -> dict:
    """Returns {auth_users, profiles, orphans} from VOLAURA Supabase."""
    result: dict[str, int] = {}
    try:
        # auth.users count
        auth_r = sb.rpc(
            "get_auth_user_count",
            {},
        ).execute()
        result["auth_users"] = auth_r.data or 0
    except Exception:  # noqa: BLE001
        pass

    try:
        prof_r = sb.table("profiles").select("id", count="exact").execute()
        result["profiles"] = prof_r.count or 0
    except Exception:  # noqa: BLE001
        pass

    return result


def _collect_top_learnings(sb, limit: int = 5) -> list[dict]:
    """Returns the most recent atlas_learnings rows for CEO context."""
    try:
        rows = (
            sb.table("atlas_learnings")
            .select("category, insight, created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return rows.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"atlas_learnings top query failed: {exc}")
        return []


def _collect_obligations(sb) -> list[dict]:
    """Returns open obligations ordered by deadline proximity."""
    try:
        rows = (
            sb.table("atlas_obligations")
            .select("title, category, deadline, status, owner")
            .in_("status", ["open", "in_progress"])
            .order("deadline")
            .execute()
        )
        return rows.data or []
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"atlas_obligations query failed: {exc}")
        return []


def _collect_journal_entries(n: int = 3) -> list[str]:
    """Extract the last n journal entry titles from journal.md."""
    if not JOURNAL.exists():
        return []
    text = JOURNAL.read_text(encoding="utf-8")
    # Entries start with "## YYYY-MM-DD" or "---\n\n## "
    entries = re.findall(r"^## (\d{4}-\d{2}-\d{2}[^\n]*)", text, re.MULTILINE)
    return entries[-n:] if entries else []


# ─────────────────────────────────────────────────────────────────────────────
# Fingerprint builder
# ─────────────────────────────────────────────────────────────────────────────


def _build_fingerprint(
    now: datetime,
    char_events: dict,
    learnings_by_cat: dict,
    top_learnings: list[dict],
    user_counts: dict,
    obligations: list[dict],
    journal_entries: list[str],
) -> str:
    iso_week = now.strftime("%G-W%V")
    timestamp = now.strftime("%Y-%m-%d %H:%M UTC")

    # Character events table
    event_rows = ""
    if char_events:
        event_rows = "\n".join(
            f"| {product} | {meta['count']} | {meta.get('last_event_type', '—')} | {(meta.get('last_at') or '')[:10]} |"
            for product, meta in sorted(char_events.items())
        )
    else:
        event_rows = "| — | 0 | — | — |"

    # Learnings breakdown
    learning_rows = ""
    if learnings_by_cat:
        learning_rows = "\n".join(
            f"| {cat} | {count} |"
            for cat, count in sorted(learnings_by_cat.items(), key=lambda x: -x[1])
        )
        total_learnings = sum(learnings_by_cat.values())
    else:
        learning_rows = "| — | 0 |"
        total_learnings = 0

    # Top learnings
    top_rows = ""
    for learning in top_learnings:
        insight = (learning.get("insight") or "")[:80].replace("\n", " ")
        top_rows += f"- [{learning.get('category', '?')}] {insight}\n"

    # Obligations
    obl_rows = ""
    if obligations:
        for o in obligations:
            deadline = (o.get("deadline") or "no deadline")[:10]
            obl_rows += f"- **{o.get('title', '?')}** ({o.get('status', '?')}) · deadline {deadline} · owner {o.get('owner', '?')}\n"
    else:
        obl_rows = "- None open\n"

    # User counts
    auth_count = user_counts.get("auth_users", "?")
    profile_count = user_counts.get("profiles", "?")

    # Journal
    journal_lines = (
        "\n".join(f"- {e}" for e in reversed(journal_entries))
        if journal_entries
        else "- (none captured)"
    )

    return f"""# Atlas Unified Ecosystem Snapshot — {iso_week}

**Generated:** {timestamp}
**Purpose:** Cross-product state of Atlas. Read on wake to understand the user across all 5 products without scanning 5 repos.

---

## Product Activity (character_events)

| Source Product | Events | Last Event Type | Last Event Date |
|---|---:|---|---|
{event_rows}

---

## Atlas Learnings (Telegram memory, {total_learnings} total)

| Category | Count |
|---|---:|
{learning_rows}

**Most recent learnings:**
{top_rows}
---

## User State

| Metric | Value |
|---|---:|
| auth.users (VOLAURA) | {auth_count} |
| profiles (VOLAURA) | {profile_count} |

---

## Open Obligations

{obl_rows}
---

## Journal Highlights (last 3 entries)

{journal_lines}

---

## Cross-Product Notes

- MindShift character_events: not yet bridging (E2 track pending)
- Life Feed: tracked under source_product=volaura (integrated)
- EventShift: writes to character_events via `source_product='eventshift'`
- BrandedBy: no events yet (video generation blocked on Azure/ElevenLabs keys)
- ZEUS/ZEUS-terminal: architectural layer, no end-user events

Track E DoD marker: this file proves Atlas reads a single unified state at week boundary.
When E2 lands, MindShift rows will appear in the character_events table above.

---

*Written by `scripts/atlas_ecosystem_snapshot.py` · cron `.github/workflows/atlas-ecosystem-snapshot.yml`*
"""


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────


def main() -> int:
    now = datetime.now(UTC)
    iso_week = now.strftime("%G-W%V")
    out_path = HEARTBEAT_DIR / f"unified-heartbeat-{iso_week}.md"

    logger.info(f"Atlas ecosystem snapshot — week {iso_week}")

    # Connect
    try:
        sb = _get_supabase()
    except RuntimeError as exc:
        logger.error(str(exc))
        return 1

    # Collect
    char_events = _collect_character_events(sb)
    learnings_by_cat = _collect_atlas_learnings(sb)
    top_learnings = _collect_top_learnings(sb, limit=5)
    user_counts = _collect_user_counts(sb)
    obligations = _collect_obligations(sb)
    journal_entries = _collect_journal_entries(n=3)

    logger.info(
        f"Collected: {sum(v['count'] for v in char_events.values())} char_events across "
        f"{len(char_events)} products, {sum(learnings_by_cat.values())} learnings"
    )

    # Build and write
    content = _build_fingerprint(
        now=now,
        char_events=char_events,
        learnings_by_cat=learnings_by_cat,
        top_learnings=top_learnings,
        user_counts=user_counts,
        obligations=obligations,
        journal_entries=journal_entries,
    )

    out_path.write_text(content, encoding="utf-8")
    logger.info(f"Written: {out_path.relative_to(REPO_ROOT)}")

    # Print summary for GitHub Actions logs
    print(
        f"[atlas-snapshot] Week {iso_week}: "
        f"{len(char_events)} active products, "
        f"{sum(learnings_by_cat.values())} learnings, "
        f"{len(obligations)} open obligations"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
