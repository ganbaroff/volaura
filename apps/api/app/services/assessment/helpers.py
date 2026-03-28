"""Assessment helper utilities — DB lookups and session state builders.

Rule: This module NEVER imports from app.routers.*
"""

from __future__ import annotations

from fastapi import HTTPException

from app.core.assessment.engine import CATState
from app.deps import SupabaseAdmin
from app.schemas.assessment import QuestionOut, SessionOut


async def get_competency_id(db: SupabaseAdmin, slug: str) -> str:
    """Fetch competency UUID by slug. Raises 404 if not found."""
    result = (
        await db.table("competencies")
        .select("id")
        .eq("slug", slug)
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "COMPETENCY_NOT_FOUND", "message": f"Competency '{slug}' not found"},
        )
    return result.data["id"]


async def fetch_questions(db: SupabaseAdmin, competency_id: str) -> list[dict]:
    """Fetch all active questions for a competency."""
    result = (
        await db.table("questions")
        .select("id, type, scenario_en, scenario_az, options, irt_a, irt_b, irt_c, expected_concepts, correct_answer, competency_id")
        .eq("competency_id", competency_id)
        .eq("is_active", True)
        .execute()
    )
    return result.data or []


def make_session_out(
    session_id: str,
    competency_slug: str,
    state: CATState,
    next_q: dict | None,
    role_level: str = "volunteer",
) -> SessionOut:
    """Build SessionOut from CAT state + next question dict."""
    nq = None
    if next_q and not state.stopped:
        nq = QuestionOut(
            id=next_q["id"],
            question_type=next_q["type"],
            question_en=next_q["scenario_en"],
            question_az=next_q["scenario_az"],
            options=next_q.get("options"),
            competency_id=next_q["competency_id"],
        )
    return SessionOut(
        session_id=session_id,
        competency_slug=competency_slug,
        role_level=role_level,
        questions_answered=len(state.items),
        is_complete=state.stopped,
        stop_reason=state.stop_reason,
        next_question=nq,
    )
