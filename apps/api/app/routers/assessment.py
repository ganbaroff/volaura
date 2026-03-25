"""Assessment endpoints — start, answer, complete, results.

Rate limited:
- /start: 3/hour per user (prevent assessment farming)
- /answer: 60/hour per user (normal pace ~40 questions/session)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.config import settings
from app.core.assessment import antigaming, bars
from app.middleware.rate_limit import limiter, RATE_ASSESSMENT_START, RATE_ASSESSMENT_ANSWER, RATE_ASSESSMENT_COMPLETE
from app.core.assessment.aura_calc import (
    calculate_overall,
    get_badge_tier,
    is_elite,
)
from app.core.assessment.engine import (
    CATState,
    select_next_item,
    should_stop,
    submit_response,
    theta_to_score,
)
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.schemas.assessment import (
    AnswerFeedback,
    AssessmentResultOut,
    QuestionOut,
    SessionOut,
    StartAssessmentRequest,
    SubmitAnswerRequest,
)

router = APIRouter(prefix="/assessment", tags=["Assessment"])


# ── helpers ───────────────────────────────────────────────────────────────────


async def _get_competency_id(db: SupabaseAdmin, slug: str) -> str:
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


async def _fetch_questions(db: SupabaseAdmin, competency_id: str) -> list[dict]:
    result = (
        await db.table("questions")
        .select("id, type, scenario_en, scenario_az, options, irt_a, irt_b, irt_c, expected_concepts, correct_answer, competency_id")
        .eq("competency_id", competency_id)
        .eq("is_active", True)
        .execute()
    )
    return result.data or []


def _make_session_out(
    session_id: str,
    competency_slug: str,
    state: CATState,
    next_q: dict | None,
    role_level: str = "volunteer",
) -> SessionOut:
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
        # theta/theta_se intentionally NOT sent to client (security audit P1)
        is_complete=state.stopped,
        stop_reason=state.stop_reason,
        next_question=nq,
    )


# ── endpoints ─────────────────────────────────────────────────────────────────


@router.post("/start", response_model=SessionOut, status_code=201)
@limiter.limit(RATE_ASSESSMENT_START)
async def start_assessment(
    request: Request,
    payload: StartAssessmentRequest,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> SessionOut:
    """Start a new CAT session for a given competency."""
    competency_id = await _get_competency_id(db_admin, payload.competency_slug)

    # Check for in-progress session
    existing = (
        await db_user.table("assessment_sessions")
        .select("id")
        .eq("volunteer_id", user_id)
        .eq("competency_id", competency_id)
        .eq("status", "in_progress")
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "SESSION_IN_PROGRESS",
                "message": "An active session already exists for this competency",
                "session_id": existing.data[0]["id"],
            },
        )

    questions = await _fetch_questions(db_admin, competency_id)
    if not questions:
        raise HTTPException(
            status_code=422,
            detail={"code": "NO_QUESTIONS", "message": "No active questions for this competency"},
        )

    state = CATState()
    first_q = select_next_item(state, questions)

    session_id = str(uuid.uuid4())
    await db_user.table("assessment_sessions").insert({
        "id": session_id,
        "volunteer_id": user_id,
        "competency_id": competency_id,
        "status": "in_progress",
        "role_level": payload.role_level,  # Phase 1: role-level tracking
        "theta_estimate": state.theta,
        "theta_se": state.theta_se,
        "answers": state.to_dict(),
        "current_question_id": first_q["id"] if first_q else None,
        "question_delivered_at": datetime.now(timezone.utc).isoformat(),  # HIGH-03: server-side timing
        "started_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    return _make_session_out(session_id, payload.competency_slug, state, first_q, payload.role_level)


@router.post("/answer", response_model=AnswerFeedback)
@limiter.limit(RATE_ASSESSMENT_ANSWER)
async def submit_answer(
    request: Request,
    payload: SubmitAnswerRequest,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> AnswerFeedback:
    """Submit an answer to the current question and get the next item."""
    # Load session
    session_result = (
        await db_user.table("assessment_sessions")
        .select("*")
        .eq("id", payload.session_id)
        .eq("volunteer_id", user_id)
        .single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "SESSION_NOT_FOUND", "message": "Assessment session not found"},
        )
    session = session_result.data

    if session["status"] != "in_progress":
        raise HTTPException(
            status_code=409,
            detail={"code": "SESSION_NOT_ACTIVE", "message": "This session is already completed"},
        )

    if session.get("current_question_id") != payload.question_id:
        raise HTTPException(
            status_code=422,
            detail={"code": "WRONG_QUESTION", "message": "This is not the current active question"},
        )

    # HIGH-01: Read current version for optimistic locking
    current_version = session.get("answer_version", 0)

    # Load question details
    q_result = (
        await db_admin.table("questions")
        .select("*")
        .eq("id", payload.question_id)
        .single()
        .execute()
    )
    if not q_result.data:
        raise HTTPException(status_code=404, detail={"code": "QUESTION_NOT_FOUND", "message": "Question not found"})

    question = q_result.data

    # HIGH-03: Server-side timing — don't trust client response_time_ms
    question_delivered_at = session.get("question_delivered_at")
    if question_delivered_at:
        try:
            delivered_dt = datetime.fromisoformat(question_delivered_at)
            server_elapsed_ms = int((datetime.now(timezone.utc) - delivered_dt).total_seconds() * 1000)
        except (ValueError, TypeError):
            server_elapsed_ms = payload.response_time_ms  # fallback to client
    else:
        server_elapsed_ms = payload.response_time_ms  # no server timestamp available

    # Anti-gaming timing check — uses server time when available
    timing = antigaming.check_answer_timing(server_elapsed_ms)

    # Score the answer
    raw_score: float
    evaluation_log: dict | None = None
    if question["type"] == "mcq":
        correct_answer: str | None = question.get("correct_answer")
        raw_score = 1.0 if (correct_answer and payload.answer.strip() == correct_answer) else 0.0
    else:
        # Open-ended → LLM evaluation (multi-model swarm or single-model BARS)
        expected_concepts: list[dict] = question.get("expected_concepts") or []
        evaluation_log = None
        if settings.swarm_enabled:
            # BUG-01 fix (2026-03-25): use return_details=True so swarm path
            # produces evaluation_log for Phase 2 Transparent Logs.
            from app.services.swarm_service import evaluate_answer as swarm_evaluate
            eval_result = await swarm_evaluate(
                question_en=question["scenario_en"],
                answer=payload.answer,
                expected_concepts=expected_concepts,
                return_details=True,
            )
            raw_score = eval_result.composite
            evaluation_log = eval_result.to_log()
        else:
            eval_result = await bars.evaluate_answer(
                question_en=question["scenario_en"],
                answer=payload.answer,
                expected_concepts=expected_concepts,
                return_details=True,
            )
            raw_score = eval_result.composite
            evaluation_log = eval_result.to_log()

    # Update CAT state (with evaluation log if available — Phase 2: Transparent Logs)
    state = CATState.from_dict(session["answers"] or {})
    state = submit_response(
        state,
        question_id=payload.question_id,
        irt_a=float(question.get("irt_a", 1.0)),
        irt_b=float(question.get("irt_b", 0.0)),
        irt_c=float(question.get("irt_c", 0.0)),
        raw_score=raw_score,
        response_time_ms=payload.response_time_ms,
        evaluation_log=evaluation_log,
    )

    # Check stopping criteria
    stopped, stop_reason = should_stop(state)
    state.stopped = stopped
    state.stop_reason = stop_reason

    # Get next question (if not stopped)
    competency_id = session["competency_id"]
    all_questions = await _fetch_questions(db_admin, competency_id) if not stopped else []
    next_q = select_next_item(state, all_questions) if not stopped else None

    if not next_q and not stopped:
        state.stopped = True
        state.stop_reason = "no_items_left"

    # Persist updated session + record when next question is delivered (HIGH-03)
    update_payload: dict = {
        "theta_estimate": state.theta,
        "theta_se": state.theta_se,
        "answers": state.to_dict(),
        "current_question_id": next_q["id"] if next_q else None,
        "question_delivered_at": datetime.now(timezone.utc).isoformat() if next_q else None,
        "answer_version": current_version + 1,  # HIGH-01: increment version
    }
    if state.stopped:
        update_payload["status"] = "completed"
        update_payload["completed_at"] = datetime.now(timezone.utc).isoformat()

    # HIGH-01: Optimistic locking — only update if version hasn't changed
    # BLOCKER-1 FIX: Use db_admin (service_role) for updates — user-level UPDATE policy removed
    # to prevent direct PostgREST theta manipulation
    update_result = await db_admin.table("assessment_sessions").update(
        update_payload
    ).eq("id", payload.session_id).eq("volunteer_id", user_id).eq("answer_version", current_version).execute()

    if not update_result.data:
        raise HTTPException(
            status_code=409,
            detail={"code": "CONCURRENT_SUBMIT", "message": "This answer was already submitted. Please refresh."},
        )

    # Get competency slug for response
    comp_result = (
        await db_admin.table("competencies").select("slug").eq("id", competency_id).single().execute()
    )
    slug = comp_result.data["slug"] if comp_result.data else ""

    session_out = _make_session_out(payload.session_id, slug, state, next_q, session.get("role_level", "volunteer"))

    return AnswerFeedback(
        session_id=payload.session_id,
        question_id=payload.question_id,
        # raw_score REMOVED — CRIT-03: prevents BARS calibration attacks
        timing_warning=timing.get("warning"),
        session=session_out,
    )


@router.post("/complete/{session_id}", response_model=AssessmentResultOut)
@limiter.limit(RATE_ASSESSMENT_COMPLETE)
async def complete_assessment(
    request: Request,
    session_id: str,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> AssessmentResultOut:
    """Finalise a session, run anti-gaming analysis, and upsert AURA score."""
    # HIGH-02: Validate session_id is a proper UUID
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail={"code": "INVALID_SESSION_ID", "message": "session_id must be a valid UUID"})

    session_result = (
        await db_user.table("assessment_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("volunteer_id", user_id)
        .single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": "Session not found"})

    session = session_result.data
    state = CATState.from_dict(session["answers"] or {})

    # Force-complete if somehow still open
    if session["status"] == "in_progress":
        state.stopped = True
        state.stop_reason = "manual_complete"
        # BLOCKER-1 FIX: Use db_admin for updates (user-level UPDATE policy removed)
        await db_admin.table("assessment_sessions").update({
            "status": "completed",
            "theta_estimate": state.theta,
            "theta_se": state.theta_se,
            "answers": state.to_dict(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", session_id).execute()

    # Anti-gaming analysis
    gaming = antigaming.analyse(state.to_dict().get("items", []))
    raw_competency_score = theta_to_score(state.theta)
    # Apply gaming penalty
    competency_score = round(raw_competency_score * gaming.penalty_multiplier, 2)

    # Get competency slug
    comp_result = (
        await db_admin.table("competencies").select("slug").eq("id", session["competency_id"]).single().execute()
    )
    slug = comp_result.data["slug"] if comp_result.data else ""

    # Upsert AURA score via DB RPC
    aura_updated = False
    if slug:
        rpc_result = await db_admin.rpc(
            "upsert_aura_score",
            {
                "p_volunteer_id": user_id,
                "p_competency_scores": {slug: competency_score},
            },
        ).execute()
        aura_updated = rpc_result.data is not None

    return AssessmentResultOut(
        session_id=session_id,
        competency_slug=slug,
        # theta/theta_se intentionally NOT sent to client (security audit P1)
        competency_score=competency_score,
        questions_answered=len(state.items),
        stop_reason=state.stop_reason,
        aura_updated=aura_updated,
        gaming_flags=gaming.flags,
        completed_at=datetime.now(timezone.utc),
    )


@router.get("/results/{session_id}", response_model=AssessmentResultOut)
@limiter.limit(RATE_ASSESSMENT_COMPLETE)
async def get_results(
    request: Request,
    session_id: str,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> AssessmentResultOut:
    """Retrieve results for a completed session."""
    session_result = (
        await db_user.table("assessment_sessions")
        .select("*")
        .eq("id", session_id)
        .eq("volunteer_id", user_id)
        .single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(status_code=404, detail={"code": "SESSION_NOT_FOUND", "message": "Session not found"})

    session = session_result.data
    state = CATState.from_dict(session["answers"] or {})
    gaming = antigaming.analyse(state.to_dict().get("items", []))
    competency_score = round(theta_to_score(state.theta) * gaming.penalty_multiplier, 2)

    comp_result = (
        await db_admin.table("competencies").select("slug").eq("id", session["competency_id"]).single().execute()
    )
    slug = comp_result.data["slug"] if comp_result.data else ""

    return AssessmentResultOut(
        session_id=session_id,
        competency_slug=slug,
        # theta/theta_se intentionally NOT sent to client (security audit P1)
        competency_score=competency_score,
        questions_answered=len(state.items),
        stop_reason=state.stop_reason,
        aura_updated=False,
        gaming_flags=gaming.flags,
        completed_at=session.get("completed_at"),
    )
