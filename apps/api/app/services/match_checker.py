"""Match Checker — finds new talent that matches org saved searches, sends notifications.

Runs daily via `.github/workflows/match-checker.yml` (GitHub Actions cron).
Can also be triggered manually or via an API endpoint (POST /api/admin/run-match-check).

Algorithm per saved search:
  1. Load JSONB filters → reconstruct VolunteerSearchRequest-compatible query
  2. Query aura_scores WHERE updated_at > last_checked_at AND filters match
  3. Collect matches → load volunteer display names
  4. Update last_checked_at to NOW()
  5. If new matches AND notify_on_match → send Telegram to org owner

Safety:
  - Uses service-role client (RLS bypass — reads all orgs + aura_scores)
  - Filters: only aura_scores.visibility = 'public' (honours user privacy)
  - Per-run cap: max 50 saved searches processed per invocation (prevents timeout)
  - Per-search cap: max 5 match previews in notification (keeps Telegram readable)
  - Circuit breaker: 3 Telegram failures → stop Telegram for this run (log only)
  - Never raises — all errors caught and logged

Usage:
    # As module (called from GitHub Actions):
    python -m apps.api.app.services.match_checker

    # From FastAPI (admin endpoint or cron trigger):
    from app.services.match_checker import run_match_check
    results = await run_match_check(db_admin)
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from loguru import logger

from app.config import settings

# ── Constants ─────────────────────────────────────────────────────────────────

_MAX_SEARCHES_PER_RUN = 50  # Protect DB from runaway queries
_MAX_MATCHES_PER_NOTIF = 5  # Telegram notification preview limit
_CB_THRESHOLD = 3  # Telegram circuit breaker: 3 failures → stop sending


# ── Data structures ───────────────────────────────────────────────────────────

from dataclasses import dataclass, field


@dataclass
class MatchCheckResult:
    """Outcome for one saved search check."""

    search_id: str
    search_name: str
    org_id: str
    new_match_count: int
    notified: bool
    error: str | None = None


@dataclass
class RunSummary:
    """Summary of a full match-checker run."""

    searches_checked: int = 0
    searches_with_matches: int = 0
    notifications_sent: int = 0
    errors: int = 0
    results: list[MatchCheckResult] = field(default_factory=list)


# ── Core logic ────────────────────────────────────────────────────────────────


async def _find_new_matches(
    db_admin: Any,
    filters: dict,
    since: datetime,
    limit: int = _MAX_MATCHES_PER_NOTIF,
) -> list[dict]:
    """Find aura_scores rows that match the saved filters AND were updated after `since`.

    Returns lightweight dicts: {volunteer_id, total_score, badge_tier, display_name}.
    Only returns profiles with visibility='public' — privacy respected at data layer.

    Note: We intentionally use the rule-based approach here (no pgvector embedding).
    The match checker runs in the background without a user query string context,
    and embedding-based search requires a semantic query, not just filter criteria.
    For saved searches that are filter-only (min_aura + badge_tier), rule-based is exact.
    For saved searches with a text query, we use keyword fallback only.
    """
    min_aura = float(filters.get("min_aura", 0.0))
    badge_tier = filters.get("badge_tier")

    query = (
        db_admin.table("aura_scores")
        .select("volunteer_id, total_score, badge_tier")
        .gte("total_score", min_aura)
        .eq("visibility", "public")
        .gt("updated_at", since.isoformat())
        .order("total_score", desc=True)
        .limit(limit)
    )

    if badge_tier:
        query = query.eq("badge_tier", badge_tier)

    result = await query.execute()
    rows = result.data or []

    if not rows:
        return []

    # Load display names — batch fetch to avoid N+1
    vol_ids = [r["volunteer_id"] for r in rows]
    profiles_res = await db_admin.table("profiles").select("id, display_name, username").in_("id", vol_ids).execute()
    profiles_by_id = {p["id"]: p for p in (profiles_res.data or [])}

    # Optionally filter by location (string equality — not geo-aware in MVP)
    location_filter = filters.get("location", "").strip().lower()

    enriched = []
    for row in rows:
        vol_id = row["volunteer_id"]
        profile = profiles_by_id.get(vol_id, {})

        if location_filter:
            # Location stored in profiles — skip if doesn't match (case-insensitive)
            profile_location = (profile.get("location") or "").lower()
            if location_filter not in profile_location:
                continue

        # Find top competency slug for the notification preview
        top_competency = None
        try:
            comp_res = (
                await db_admin.table("aura_scores")
                .select(
                    "communication, reliability, english_proficiency, leadership, "
                    "event_performance, tech_literacy, adaptability, empathy_safeguarding"
                )
                .eq("volunteer_id", vol_id)
                .maybe_single()
                .execute()
            )
            if comp_res.data:
                comp_data = comp_res.data
                competency_keys = [
                    "communication",
                    "reliability",
                    "english_proficiency",
                    "leadership",
                    "event_performance",
                    "tech_literacy",
                    "adaptability",
                    "empathy_safeguarding",
                ]
                scores = {k: comp_data.get(k, 0.0) or 0.0 for k in competency_keys}
                if scores:
                    top_competency = max(scores, key=lambda k: scores[k])
        except Exception:
            pass  # Top competency is just for notification preview — non-fatal

        enriched.append(
            {
                "volunteer_id": vol_id,
                "display_name": profile.get("display_name") or profile.get("username"),
                "overall_score": float(row["total_score"] or 0),
                "badge_tier": row.get("badge_tier") or "none",
                "top_competency": top_competency,
            }
        )

    return enriched[:limit]


async def _send_telegram_notification(
    org_name: str,
    search_name: str,
    matches: list[dict],
) -> bool:
    """Send a Telegram message to the CEO/org owner via the Volaura bot.

    For MVP: sends to the configured CEO chat ID (the platform owner).
    Post-MVP: route to org admin's personal chat ID (requires onboarding step to
    collect org Telegram chat IDs — not implemented yet).

    Returns True on success, False on failure (non-raising).
    """
    # HARD KILL-SWITCH (2026-04-19): see error_alerting.py for context.
    # Remove early-return only after CEO says 'unlock telegram alerts'.
    return False

    if not settings.telegram_bot_token or not settings.telegram_ceo_chat_id:
        logger.debug("Telegram not configured — skipping match notification")
        return False

    try:
        import httpx

        match_lines = []
        for m in matches[:_MAX_MATCHES_PER_NOTIF]:
            name = m.get("display_name") or "Anonymous"
            score = m.get("overall_score", 0)
            tier = (m.get("badge_tier") or "none").capitalize()
            comp = m.get("top_competency", "")
            comp_label = f" | {comp.replace('_', ' ').title()}" if comp else ""
            match_lines.append(f"• {name} — AURA {score:.0f} | {tier}{comp_label}")

        match_text = "\n".join(match_lines)
        count = len(matches)
        message = (
            f"*New talent matches for '{search_name}'*\n"
            f"Org: {org_name}\n"
            f"{count} new professional{'s' if count != 1 else ''} match your saved search:\n\n"
            f"{match_text}\n\n"
            f"[View all matches on Volaura]({settings.app_url}/az/org-professionals)"
        )

        # Central telegram-gate (2026-04-19 spam kill).
        try:
            from packages.swarm.telegram_gate import allow_send as _gate_allow

            if not _gate_allow(category="info", severity="info", preview=message[:120]):
                return False
        except ImportError:
            pass

        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": settings.telegram_ceo_chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
            )
        if resp.status_code == 200:
            return True
        else:
            logger.warning("Telegram notification failed", status=resp.status_code, body=resp.text[:200])
            return False

    except Exception as exc:
        logger.warning("Telegram notification error", error=str(exc))
        return False


async def run_match_check(db_admin: Any) -> RunSummary:
    """Run the full match check for all notification-enabled saved searches.

    Called by GitHub Actions cron (daily) or admin endpoint.
    Processes up to _MAX_SEARCHES_PER_RUN searches per invocation.

    Args:
        db_admin: Supabase admin client (service-role — RLS bypass)

    Returns:
        RunSummary with per-search results.
    """
    summary = RunSummary()
    telegram_failures = 0

    logger.info("Match checker: starting run")

    # Fetch all notification-enabled saved searches (partial index makes this fast)
    # Graceful fallback: if migration not yet applied in this environment, log and exit cleanly.
    try:
        searches_res = (
            await db_admin.table("org_saved_searches")
            .select("id, org_id, name, filters, last_checked_at")
            .eq("notify_on_match", True)
            .order("last_checked_at")
            .limit(_MAX_SEARCHES_PER_RUN)
            .execute()
        )
    except Exception as exc:
        if "org_saved_searches" in str(exc) or "does not exist" in str(exc):
            logger.warning(
                "Match checker: org_saved_searches table not found — "
                "apply migration 20260401171324_org_saved_searches.sql first. Skipping run."
            )
            return summary
        raise

    searches = searches_res.data or []
    logger.info("Match checker: {} searches to process", len(searches))

    for search in searches:
        search_id = search["id"]
        search_name = search["name"]
        org_id = search["org_id"]
        filters = search.get("filters") or {}
        last_checked_raw = search.get("last_checked_at")

        try:
            # Parse last_checked_at
            if isinstance(last_checked_raw, str):
                since = datetime.fromisoformat(last_checked_raw.replace("Z", "+00:00"))
            elif isinstance(last_checked_raw, datetime):
                since = last_checked_raw
            else:
                since = datetime(2020, 1, 1, tzinfo=UTC)

            # Load org info (for notification message and name)
            org_res = await db_admin.table("organizations").select("name").eq("id", org_id).maybe_single().execute()
            org_name = (org_res.data or {}).get("name", "Organization")

            # Find new matches
            matches = await _find_new_matches(db_admin, filters, since)
            new_count = len(matches)

            # Always update last_checked_at — even if zero matches (prevents re-checking same window)
            now_iso = datetime.now(UTC).isoformat()
            await (
                db_admin.table("org_saved_searches").update({"last_checked_at": now_iso}).eq("id", search_id).execute()
            )

            notified = False
            if new_count > 0 and telegram_failures < _CB_THRESHOLD:
                success = await _send_telegram_notification(org_name, search_name, matches)
                notified = success
                if not success:
                    telegram_failures += 1
                    if telegram_failures >= _CB_THRESHOLD:
                        logger.warning(
                            "Match checker: Telegram circuit breaker tripped — {} failures",
                            telegram_failures,
                        )

            result = MatchCheckResult(
                search_id=search_id,
                search_name=search_name,
                org_id=org_id,
                new_match_count=new_count,
                notified=notified,
            )
            summary.searches_checked += 1
            if new_count > 0:
                summary.searches_with_matches += 1
            if notified:
                summary.notifications_sent += 1
            summary.results.append(result)

            logger.info(
                "Match checker: processed search",
                search_id=search_id,
                search_name=search_name,
                new_matches=new_count,
                notified=notified,
            )

        except Exception as exc:
            logger.error(
                "Match checker: error processing search",
                search_id=search_id,
                error=str(exc),
            )
            summary.errors += 1
            summary.results.append(
                MatchCheckResult(
                    search_id=search_id,
                    search_name=search_name,
                    org_id=org_id,
                    new_match_count=0,
                    notified=False,
                    error=str(exc),
                )
            )

    logger.info(
        "Match checker: run complete",
        checked=summary.searches_checked,
        with_matches=summary.searches_with_matches,
        notified=summary.notifications_sent,
        errors=summary.errors,
    )
    return summary


# ── CLI entry point (GitHub Actions) ─────────────────────────────────────────


async def _main() -> None:
    """CLI runner: creates its own Supabase admin client and runs the check."""
    from supabase import acreate_client
    from supabase._async.client import AsyncClient

    if not settings.supabase_url or not settings.supabase_service_key:
        logger.error("Match checker: SUPABASE_URL or SUPABASE_SERVICE_KEY not set — aborting")
        return

    db_admin: AsyncClient = await acreate_client(settings.supabase_url, settings.supabase_service_key)
    await run_match_check(db_admin)


if __name__ == "__main__":
    asyncio.run(_main())
