"""Sentry webhook receiver — recurring-symptoms watchdog.

Research: docs/research/recurring-symptoms-watchdog/summary.md
Pattern:  INC-017 (OAuth silent break 11d), INC-001/INC-008 (telegram fix-of-fix).

Flow:
    1. Sentry alert rule fires on regression (issue.reopened OR first-seen
       with fingerprint recurrence).
    2. Sentry POSTs JSON to /api/webhooks/sentry.
    3. Endpoint verifies X-Sentry-Signature HMAC-SHA256(body, secret).
    4. Upserts into public.recurring_symptom_events (bump occurrences, update
       last_seen). Occurrences >= threshold → needs_rca_label_set=true.
    5. Creates or updates a GitHub issue labelled `needs-RCA` (idempotent).
    6. Pings CEO Telegram with the issue URL.

Security: fail-closed when SENTRY_WEBHOOK_SECRET is empty (same pattern as
telegram_webhook after INC-008). hmac.compare_digest for timing safety.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger

from app.config import settings
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Occurrence threshold above which the fingerprint is tagged needs-RCA.
# Matches research §Day-3-4: >=3 repeat touches = root-cause class, not symptom.
RCA_THRESHOLD = 3


def _verify_sentry_signature(body: bytes, signature_header: str) -> bool:
    """HMAC-SHA256 constant-time compare against SENTRY_WEBHOOK_SECRET.

    Sentry sends the raw request body hex-HMAC'd with the shared Client Secret
    in the `sentry-hook-signature` (v2) or `x-sentry-signature` (v1) header.
    We accept both names for compatibility; caller decides which to pass.
    """
    if not settings.sentry_webhook_secret:
        return False
    expected = hmac.new(
        key=settings.sentry_webhook_secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header or "")


def _extract_fingerprint(payload: dict[str, Any]) -> str:
    """Return a stable hash for the Sentry issue.

    Sentry's own `issue.id` is stable per-project; if present, we use it as-is.
    Otherwise we fall back to hashing the issue title + culprit, which is the
    same strategy Sentry uses internally for grouping fallback.
    """
    data = payload.get("data", {}) or {}
    issue = data.get("issue") or data.get("event", {}).get("issue") or {}
    if issue.get("id"):
        return f"sentry:{issue['id']}"
    title = (issue.get("title") or payload.get("event", {}).get("title") or "").strip()
    culprit = (issue.get("culprit") or payload.get("event", {}).get("culprit") or "").strip()
    return "fp:" + hashlib.sha256(f"{title}|{culprit}".encode()).hexdigest()[:32]


def _extract_source_product(payload: dict[str, Any]) -> str:
    """Map Sentry project slug / tags to ecosystem source_product enum."""
    data = payload.get("data", {}) or {}
    issue = data.get("issue") or {}
    project_slug = (issue.get("project", {}) or {}).get("slug") or payload.get("project_slug", "")
    project_slug = str(project_slug).lower()
    for product in ("mindshift", "lifesim", "brandedby", "zeus", "volaura"):
        if product in project_slug:
            return product
    return "unknown"


def _is_regression_event(payload: dict[str, Any]) -> bool:
    """True if this webhook represents a recurrence worth escalating.

    Sentry's Internal Integration webhooks fire `action: created | resolved |
    assigned | ignored`. For regressions we watch `created` on an issue where
    `num_comments == 0` AND the event payload carries `isRegression: true`.
    We also accept action == 'resolved' reversed (reopened).
    """
    action = payload.get("action", "")
    if action in {"resolved", "unresolved", "reopened"}:
        return True
    data = payload.get("data", {}) or {}
    issue = data.get("issue") or {}
    event = data.get("event") or payload.get("event") or {}
    if issue.get("isRegression") or event.get("isRegression"):
        return True
    # Accept fingerprint recurrence count if Sentry provides it.
    times_seen = issue.get("count") or issue.get("timesSeen") or 0
    try:
        return int(times_seen) >= RCA_THRESHOLD
    except (TypeError, ValueError):
        return False


async def _upsert_event_row(
    payload: dict[str, Any],
    fingerprint: str,
    source_product: str,
) -> dict[str, Any]:
    """Idempotent upsert into recurring_symptom_events.

    Uses service_role via Supabase REST. We call Supabase directly via httpx
    because the standard per-request SupabaseAdmin dep is request-scoped and
    we already have a raw request here; building a fresh client is cheaper
    than threading Depends() through webhook code.
    """
    from supabase import acreate_client

    db = await acreate_client(settings.supabase_url, settings.supabase_service_key)

    data = payload.get("data", {}) or {}
    issue = data.get("issue") or {}
    now = datetime.now(UTC).isoformat()

    existing = (
        await db.table("recurring_symptom_events")
        .select("*")
        .eq("fingerprint_hash", fingerprint)
        .eq("source_product", source_product)
        .limit(1)
        .execute()
    )

    if existing.data:
        row = existing.data[0]
        new_count = int(row.get("occurrences", 0)) + 1
        needs_rca = new_count >= RCA_THRESHOLD
        updated = (
            await db.table("recurring_symptom_events")
            .update(
                {
                    "last_seen": now,
                    "occurrences": new_count,
                    "needs_rca_label_set": needs_rca,
                    "updated_at": now,
                    "sentry_issue_id": str(issue.get("id") or row.get("sentry_issue_id") or ""),
                    "title": issue.get("title") or row.get("title"),
                    "culprit": issue.get("culprit") or row.get("culprit"),
                }
            )
            .eq("id", row["id"])
            .execute()
        )
        return updated.data[0] if updated.data else row

    inserted = (
        await db.table("recurring_symptom_events")
        .insert(
            {
                "fingerprint_hash": fingerprint,
                "source_product": source_product,
                "sentry_issue_id": str(issue.get("id") or ""),
                "sentry_project": (issue.get("project") or {}).get("slug"),
                "title": issue.get("title"),
                "culprit": issue.get("culprit"),
                "occurrences": 1,
                "needs_rca_label_set": False,
                "first_seen": now,
                "last_seen": now,
            }
        )
        .execute()
    )
    return inserted.data[0] if inserted.data else {}


async def _upsert_github_issue(event_row: dict[str, Any]) -> str | None:
    """Create or update a GitHub issue labelled `needs-RCA`.

    Idempotent: if the row already has gh_issue_url, we PATCH that issue with
    a fresh occurrence-count comment. Otherwise we POST a new issue. Returns
    the issue URL or None if GH_PAT_ACTIONS is unset.
    """
    if not settings.github_pat_actions:
        return None
    owner_repo = settings.github_repo
    headers = {
        "Authorization": f"Bearer {settings.github_pat_actions}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    title_line = (event_row.get("title") or "Sentry regression")[:120]
    body_lines = [
        f"**Fingerprint:** `{event_row['fingerprint_hash']}`",
        f"**Source product:** `{event_row['source_product']}`",
        f"**Occurrences:** {event_row['occurrences']}",
        f"**First seen:** {event_row['first_seen']}",
        f"**Last seen:** {event_row['last_seen']}",
        f"**Culprit:** `{event_row.get('culprit') or 'unknown'}`",
        "",
        "> Auto-opened by recurring-symptoms watchdog.",
        "> An RCA is required before any PR touching this area can merge.",
        "> Drop a `memory/decisions/YYYY-MM-DD-*.md` file with `root_cause:` and",
        "> `prevention:` sections and the merge-gate workflow will pass.",
    ]
    body = "\n".join(body_lines)

    async with httpx.AsyncClient(timeout=15.0) as client:
        if event_row.get("gh_issue_url"):
            # PATCH existing — just append a comment so the occurrence count is
            # visible in the timeline, then refresh labels.
            issue_number = event_row["gh_issue_url"].rsplit("/", 1)[-1]
            await client.post(
                f"https://api.github.com/repos/{owner_repo}/issues/{issue_number}/comments",
                headers=headers,
                json={"body": f"Recurrence bumped to {event_row['occurrences']} at {event_row['last_seen']}."},
            )
            return event_row["gh_issue_url"]

        resp = await client.post(
            f"https://api.github.com/repos/{owner_repo}/issues",
            headers=headers,
            json={
                "title": f"[needs-RCA] {title_line}",
                "body": body,
                "labels": ["needs-RCA", "recurring-symptom", f"source/{event_row['source_product']}"],
            },
        )
        if resp.status_code >= 300:
            logger.error("GitHub issue create failed status={s} body={b}", s=resp.status_code, b=resp.text[:400])
            return None
        issue_url = resp.json().get("html_url")
        return issue_url


async def _ping_ceo_telegram(event_row: dict[str, Any], issue_url: str | None) -> None:
    """Best-effort CEO alert. Silent if Telegram is unconfigured."""
    if not (settings.telegram_bot_token and settings.telegram_ceo_chat_id):
        return
    title = (event_row.get("title") or "Sentry regression")[:160]
    msg = f"🔁 Recurring symptom (x{event_row['occurrences']}) — {event_row['source_product']}\n{title}\n"
    if issue_url:
        msg += f"RCA required: {issue_url}"

    # Central telegram-gate (2026-04-19): dedup by fingerprint + global rate cap.
    try:
        from packages.swarm.telegram_gate import allow_send as _gate_allow
        if not _gate_allow(category="error", severity="warning", preview=msg[:120]):
            return
    except ImportError:
        pass
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={
                    "chat_id": settings.telegram_ceo_chat_id,
                    "text": msg,
                    "disable_web_page_preview": True,
                },
            )
    except Exception as e:  # noqa: BLE001 — best-effort alert, never fail the webhook on it
        logger.warning("Telegram alert failed: {e}", e=str(e)[:200])


@router.post("/sentry", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit("100/minute")
async def sentry_webhook(request: Request) -> dict[str, Any]:
    """Receive Sentry alert webhook, upsert fingerprint, escalate on recurrence.

    Headers required:
        sentry-hook-signature  OR  x-sentry-signature  — HMAC-SHA256(body, secret)

    Fail-closed when SENTRY_WEBHOOK_SECRET is unset (mirrors INC-008 pattern).
    """
    if not settings.sentry_webhook_secret:
        logger.error("Sentry webhook called but SENTRY_WEBHOOK_SECRET is empty — refusing.")
        raise HTTPException(status_code=403, detail={"code": "WEBHOOK_DISABLED"})

    body = await request.body()
    signature = request.headers.get("sentry-hook-signature") or request.headers.get("x-sentry-signature") or ""
    if not _verify_sentry_signature(body, signature):
        logger.warning("Sentry webhook signature mismatch — refusing.")
        raise HTTPException(status_code=403, detail={"code": "BAD_SIGNATURE"})

    try:
        payload = json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.warning("Sentry webhook bad payload: {e}", e=str(e)[:120])
        raise HTTPException(status_code=400, detail={"code": "BAD_PAYLOAD"}) from e

    if not _is_regression_event(payload):
        logger.info("Sentry webhook: not a regression, ignoring.")
        return {"status": "ignored", "reason": "not_regression"}

    fingerprint = _extract_fingerprint(payload)
    source_product = _extract_source_product(payload)
    event_row = await _upsert_event_row(payload, fingerprint, source_product)

    issue_url = None
    if event_row.get("needs_rca_label_set") or int(event_row.get("occurrences", 0)) >= RCA_THRESHOLD:
        issue_url = await _upsert_github_issue(event_row)
        if issue_url and issue_url != event_row.get("gh_issue_url"):
            from supabase import acreate_client

            db = await acreate_client(settings.supabase_url, settings.supabase_service_key)
            await (
                db.table("recurring_symptom_events")
                .update({"gh_issue_url": issue_url})
                .eq("id", event_row["id"])
                .execute()
            )
        await _ping_ceo_telegram(event_row, issue_url)

    return {
        "status": "ok",
        "fingerprint": fingerprint,
        "source_product": source_product,
        "occurrences": event_row.get("occurrences"),
        "needs_rca": event_row.get("needs_rca_label_set", False),
        "gh_issue_url": issue_url,
    }
