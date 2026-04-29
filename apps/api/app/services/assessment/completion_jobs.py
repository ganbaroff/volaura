from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from typing import Any

from loguru import logger
from supabase._async.client import AsyncClient

SIDE_EFFECT_KEYS = (
    "aura_sync",
    "rewards",
    "streak",
    "analytics",
    "email",
    "ecosystem_events",
    "aura_events",
    "decision_log",
)

_TERMINAL_STATUSES = {"done", "skipped"}


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def default_side_effects() -> dict[str, dict[str, Any]]:
    now = _now_iso()
    return {
        key: {
            "status": "pending",
            "attempts": 0,
            "last_error": None,
            "updated_at": now,
        }
        for key in SIDE_EFFECT_KEYS
    }


def normalize_side_effects(side_effects: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    normalized = default_side_effects()
    if not isinstance(side_effects, dict):
        return normalized

    for key in SIDE_EFFECT_KEYS:
        payload = side_effects.get(key) or {}
        if not isinstance(payload, dict):
            continue
        normalized[key] = {
            "status": str(payload.get("status") or normalized[key]["status"]),
            "attempts": int(payload.get("attempts") or 0),
            "last_error": payload.get("last_error"),
            "updated_at": payload.get("updated_at") or normalized[key]["updated_at"],
        }
    return normalized


def is_side_effect_complete(side_effects: dict[str, Any] | None, key: str) -> bool:
    normalized = normalize_side_effects(side_effects)
    return normalized.get(key, {}).get("status") in _TERMINAL_STATUSES


def all_side_effects_complete(side_effects: dict[str, Any] | None) -> bool:
    normalized = normalize_side_effects(side_effects)
    return all(item.get("status") in _TERMINAL_STATUSES for item in normalized.values())


def mark_side_effect(
    side_effects: dict[str, Any] | None,
    key: str,
    *,
    status: str,
    error: str | None = None,
    increment_attempts: bool = True,
) -> dict[str, dict[str, Any]]:
    normalized = normalize_side_effects(side_effects)
    previous = normalized.get(key) or {
        "status": "pending",
        "attempts": 0,
        "last_error": None,
        "updated_at": _now_iso(),
    }
    normalized[key] = {
        "status": status,
        "attempts": int(previous.get("attempts") or 0) + (1 if increment_attempts else 0),
        "last_error": error,
        "updated_at": _now_iso(),
    }
    return normalized


async def get_completion_job(db: AsyncClient, session_id: str) -> dict[str, Any] | None:
    # Tolerate missing/uncreated table during tests + early prod boot.
    # Caller treats None as "no existing job" and proceeds to create fresh path.
    try:
        result = (
            await db.table("assessment_completion_jobs")
            .select("*")
            .eq("session_id", session_id)
            .maybe_single()
            .execute()
        )
    except Exception:
        return None
    return getattr(result, "data", None) or None


async def ensure_completion_job(
    db: AsyncClient,
    *,
    session_id: str,
    volunteer_id: str,
    competency_slug: str,
    result_context: dict[str, Any],
) -> dict[str, Any]:
    existing = await get_completion_job(db, session_id)
    if existing:
        merged_context = deepcopy(existing.get("result_context") or {})
        merged_context.update(result_context)
        side_effects = normalize_side_effects(existing.get("side_effects"))
        return await save_completion_job(
            db,
            existing,
            result_context=merged_context,
            side_effects=side_effects,
        )

    row = {
        "session_id": session_id,
        "volunteer_id": volunteer_id,
        "competency_slug": competency_slug,
        "status": "pending",
        "attempts": 0,
        "side_effects": default_side_effects(),
        "result_context": deepcopy(result_context),
        "last_error": None,
    }
    try:
        resp = await db.table("assessment_completion_jobs").insert(row).execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0]
    except Exception as exc:
        logger.warning("completion_job_insert_conflict", session_id=session_id, error=str(exc)[:120])
        winner = await get_completion_job(db, session_id)
        if winner:
            return winner
    return {
        "id": None,
        **row,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "completed_at": None,
    }


async def save_completion_job(
    db: AsyncClient,
    job: dict[str, Any],
    *,
    side_effects: dict[str, Any] | None = None,
    result_context: dict[str, Any] | None = None,
    status: str | None = None,
    last_error: str | None = None,
    increment_attempts: bool = False,
    completed_at: str | None = None,
) -> dict[str, Any]:
    next_job = deepcopy(job)
    next_side_effects = normalize_side_effects(side_effects or next_job.get("side_effects"))
    next_result_context = deepcopy(next_job.get("result_context") or {})
    if result_context:
        next_result_context.update(result_context)

    next_attempts = int(next_job.get("attempts") or 0) + (1 if increment_attempts else 0)
    next_status = status or next_job.get("status") or "pending"
    payload: dict[str, Any] = {
        "side_effects": next_side_effects,
        "result_context": next_result_context,
        "attempts": next_attempts,
        "status": next_status,
        "updated_at": _now_iso(),
        "last_error": last_error,
    }
    if completed_at is not None:
        payload["completed_at"] = completed_at

    try:
        await db.table("assessment_completion_jobs").update(payload).eq("session_id", job["session_id"]).execute()
    except Exception as exc:
        logger.warning("completion_job_update_failed", session_id=job.get("session_id"), error=str(exc)[:120])

    next_job.update(payload)
    return next_job
