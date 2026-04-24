"""Assessment helper utilities — DB lookups and session state builders.

Rule: This module NEVER imports from app.routers.*
"""

from __future__ import annotations

import json
import time

from fastapi import HTTPException
from loguru import logger

from app.core.assessment.engine import CATState
from app.deps import SupabaseAdmin
from app.schemas.assessment import QuestionOut, SessionOut


async def get_competency_id(db: SupabaseAdmin, slug: str) -> str:
    """Fetch competency UUID by slug. Raises 404 if not found."""
    result = await db.table("competencies").select("id").eq("slug", slug).single().execute()
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "COMPETENCY_NOT_FOUND", "message": f"Competency '{slug}' not found"},
        )
    return result.data["id"]


# Module-level question cache: {competency_id: (fetched_at, questions)}
# TTL: 5 minutes — questions are effectively static (new questions added by admin, not users)
_QUESTION_CACHE: dict[str, tuple[float, list[dict]]] = {}
_QUESTION_CACHE_TTL: float = 300.0  # seconds


def clear_question_cache() -> None:
    """Clear the question cache. Used by tests to prevent cross-test pollution."""
    _QUESTION_CACHE.clear()
    _COMPETENCY_SLUG_CACHE.clear()


# Module-level competency slug cache: {competency_id: slug}
# Competencies are static (never renamed in production) — no TTL needed.
_COMPETENCY_SLUG_CACHE: dict[str, str] = {}


async def get_competency_slug(db: SupabaseAdmin, competency_id: str) -> str:
    """Return the slug for a competency UUID, using an in-process cache.

    Competencies table has 8 rows and is effectively static.
    Caching eliminates 2 round trips per answer in the submit_answer hot path.
    """
    cached = _COMPETENCY_SLUG_CACHE.get(competency_id)
    if cached is not None:
        return cached

    result = await db.table("competencies").select("slug").eq("id", competency_id).single().execute()
    slug = result.data["slug"] if result.data else ""
    if slug:
        _COMPETENCY_SLUG_CACHE[competency_id] = slug
    return slug


async def fetch_questions(db: SupabaseAdmin, competency_id: str) -> list[dict]:
    """Fetch all active questions for a competency.

    Results are cached in memory for 5 minutes — questions are static and this
    is the hottest DB read in the submit_answer path (called on every answer).
    """
    now = time.monotonic()
    cached = _QUESTION_CACHE.get(competency_id)
    if cached is not None:
        fetched_at, questions = cached
        if now - fetched_at < _QUESTION_CACHE_TTL:
            # Return shallow copies — callers must not mutate the shared cache.
            # deepcopy omitted for performance; options is already normalized at write time.
            return [q.copy() for q in questions]

    result = (
        await db.table("questions")
        .select(
            "id, type, scenario_en, scenario_az, scenario_ru, options, irt_a, irt_b, irt_c, expected_concepts, correct_answer, competency_id"
        )
        .eq("competency_id", competency_id)
        .eq("is_active", True)
        .eq("needs_review", False)
        .execute()
    )
    questions = result.data or []
    # Normalize: options may be stored as a JSON string in the JSONB column
    # (double-encoded). Parse to list so QuestionOut(options=...) doesn't fail.
    for q in questions:
        if isinstance(q.get("options"), str):
            try:
                parsed = json.loads(q["options"])
                # Guard: parsed value must be a list — valid JSON but wrong type
                # (e.g. `{}` or `42`) would still fail Pydantic's list[dict] check.
                q["options"] = parsed if isinstance(parsed, list) else None
            except (json.JSONDecodeError, TypeError):
                q["options"] = None
    # Validate: MCQ questions must have options after normalization.
    # Silent None = corrupt session. Log as error so monitoring catches it.
    for q in questions:
        if q.get("type") == "mcq" and not q.get("options"):
            logger.error(
                "MCQ question has no options after decode — will be served broken",
                question_id=q.get("id"),
                competency_id=competency_id,
            )
    _QUESTION_CACHE[competency_id] = (now, questions)
    return [q.copy() for q in questions]


def make_question_out(question: dict) -> QuestionOut:
    """Build QuestionOut from a raw DB question row."""
    return QuestionOut(
        id=question["id"],
        question_type=question["type"],
        question_en=question["scenario_en"],
        question_az=question["scenario_az"],
        question_ru=question.get("scenario_ru"),
        options=question.get("options"),
        competency_id=question["competency_id"],
    )


def make_session_out(
    session_id: str,
    competency_slug: str,
    state: CATState,
    next_q: dict | None,
    role_level: str = "professional",
) -> SessionOut:
    """Build SessionOut from CAT state + next question dict."""
    nq = None
    if next_q and not state.stopped:
        nq = make_question_out(next_q)
    return SessionOut(
        session_id=session_id,
        competency_slug=competency_slug,
        role_level=role_level,
        questions_answered=len(state.items),
        is_complete=state.stopped,
        stop_reason=state.stop_reason,
        next_question=nq,
    )
