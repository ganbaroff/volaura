"""Assessment endpoints — start, answer, complete, results, coaching, info.

Rate limited:
- /start: 3/hour per user (prevent assessment farming)
- /answer: 60/hour per user (normal pace ~40 questions/session)
- /{session_id}/coaching: 30/hour (LLM rate limit)
- /info/{slug}: RATE_DISCOVERY (10/min) — metadata read

Business logic lives in app/services/assessment/:
- rewards.py   — crystal + skill_verified events
- helpers.py   — DB lookups + session state builders
- coaching_service.py — Gemini tips + per-competency fallbacks
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.config import settings
from app.core.assessment import antigaming, bars
from app.middleware.rate_limit import (
    limiter,
    RATE_ASSESSMENT_START,
    RATE_ASSESSMENT_ANSWER,
    RATE_ASSESSMENT_COMPLETE,
    RATE_LLM,
    RATE_DISCOVERY,
)
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
    AssessmentInfoOut,
    AssessmentResultOut,
    CoachingResponse,
    CoachingTip,
    SessionOut,
    StartAssessmentRequest,
    SubmitAnswerRequest,
)
from app.services.assessment.coaching_service import generate_coaching_tips
from app.services.assessment.helpers import get_competency_id, fetch_questions, make_session_out
from app.services.assessment.rewards import emit_assessment_rewards

router = APIRouter(prefix="/assessment", tags=["Assessment"])


# ── helpers moved to services (see imports above) ─────────────────────────────
# get_competency_id  ← app.services.assessment.helpers
# fetch_questions    ← app.services.assessment.helpers
# make_session_out   ← app.services.assessment.helpers
# emit_assessment_rewards ← app.services.assessment.rewards
# generate_coaching_tips  ← app.services.assessment.coaching_service
# CoachingTip / CoachingResponse / AssessmentInfoOut ← app.schemas.assessment


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
    competency_id = await get_competency_id(db_admin, payload.competency_slug)

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

    # Retest cooldown: 7 days per competency — prevent score gaming via repeated attempts
    RETEST_COOLDOWN_DAYS = 7
    recent = (
        await db_user.table("assessment_sessions")
        .select("completed_at")
        .eq("volunteer_id", user_id)
        .eq("competency_id", competency_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    if recent.data and recent.data[0].get("completed_at"):
        last_completed = datetime.fromisoformat(recent.data[0]["completed_at"])
        if last_completed.tzinfo is None:
            last_completed = last_completed.replace(tzinfo=timezone.utc)
        days_since = (datetime.now(timezone.utc) - last_completed).days
        if days_since < RETEST_COOLDOWN_DAYS:
            retry_after = RETEST_COOLDOWN_DAYS - days_since
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "RETEST_COOLDOWN",
                    "message": f"You can retake this assessment in {retry_after} day(s)",
                    "retry_after_days": retry_after,
                },
            )

    # Abuse monitoring: flag high-frequency starters (>10 starts in 24h)
    starts_today = (
        await db_user.table("assessment_sessions")
        .select("id", count="exact")
        .eq("volunteer_id", user_id)
        .gte("started_at", (datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)).isoformat())
        .execute()
    )
    daily_count = starts_today.count or 0
    if daily_count >= 10:
        logger.warning(
            "Abuse signal: high assessment start frequency",
            user_id=user_id,
            starts_today=daily_count,
        )

    questions = await fetch_questions(db_admin, competency_id)
    if not questions:
        raise HTTPException(
            status_code=422,
            detail={"code": "NO_QUESTIONS", "message": "No active questions for this competency"},
        )

    # Carry-over theta: use final theta from last completed session as prior
    # SE is widened by 1.5× per 90 days (built-in decay: older sessions = wider prior = more questions needed)
    prior_mean = 0.0
    prior_sd = 1.0
    try:
        prev_result = (
            await db_user.table("assessment_sessions")
            .select("theta_estimate, theta_se, completed_at")
            .eq("volunteer_id", user_id)
            .eq("competency_id", competency_id)
            .eq("status", "completed")
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )
        if prev_result.data:
            prev = prev_result.data[0]
            if prev.get("theta_estimate") is not None and prev.get("completed_at"):
                completed_dt = datetime.fromisoformat(prev["completed_at"])
                if completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=timezone.utc)
                days_elapsed = max(0, (datetime.now(timezone.utc) - completed_dt).days)
                # Widen SE by 1.5× per 90 days — the further in the past, the less we trust it
                decay_factor = 1.5 ** (days_elapsed / 90.0)
                prior_mean = float(prev["theta_estimate"])
                prior_sd = min(float(prev.get("theta_se") or 1.0) * decay_factor, 2.0)
                logger.info(
                    "Carry-over theta for session start",
                    user_id=user_id,
                    prior_mean=round(prior_mean, 3),
                    prior_sd=round(prior_sd, 3),
                    days_elapsed=days_elapsed,
                )
    except Exception as _e:
        logger.warning("Carry-over theta lookup failed, using defaults", error=str(_e))
        prior_mean = 0.0
        prior_sd = 1.0

    state = CATState(theta=prior_mean, theta_se=prior_sd, prior_mean=prior_mean, prior_sd=prior_sd)
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

    return make_session_out(session_id, payload.competency_slug, state, first_q, payload.role_level)


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

        # ADR-010: If evaluation fell back to keyword matching, enqueue for LLM re-eval.
        # The degraded score is used immediately (user sees it now); the worker will
        # silently replace it with a proper LLM score within ~60 seconds.
        if evaluation_log and evaluation_log.get("evaluation_mode") == "degraded":
            _session_competency_id = session["competency_id"]
            comp_result_for_slug = await db_admin.table("competencies").select("slug").eq("id", _session_competency_id).single().execute()
            comp_slug_for_queue = comp_result_for_slug.data["slug"] if comp_result_for_slug.data else ""
            if comp_slug_for_queue:
                from app.services.reeval_worker import enqueue_degraded_answer
                await enqueue_degraded_answer(
                    db_admin,
                    session_id=payload.session_id,
                    volunteer_id=user_id,
                    question_id=payload.question_id,
                    competency_slug=comp_slug_for_queue,
                    question_en=question["scenario_en"],
                    answer_text=payload.answer,
                    expected_concepts=expected_concepts,
                    degraded_score=raw_score,
                )

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
    all_questions = await fetch_questions(db_admin, competency_id) if not stopped else []
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

    session_out = make_session_out(payload.session_id, slug, state, next_q, session.get("role_level", "volunteer"))

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

    # Anti-gaming analysis — run ONCE here, store in session (never re-run in get_results)
    gaming = antigaming.analyse(state.to_dict().get("items", []))
    raw_competency_score = theta_to_score(state.theta)
    competency_score = round(raw_competency_score * gaming.penalty_multiplier, 2)

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
            "gaming_penalty_multiplier": gaming.penalty_multiplier,
            "gaming_flags": gaming.flags,
        }).eq("id", session_id).execute()

    # Get competency slug
    comp_result = (
        await db_admin.table("competencies").select("slug").eq("id", session["competency_id"]).single().execute()
    )
    slug = comp_result.data["slug"] if comp_result.data else ""

    # Store gaming analysis in session (prevents threshold-drift inconsistency in get_results)
    await db_admin.table("assessment_sessions").update({
        "gaming_penalty_multiplier": gaming.penalty_multiplier,
        "gaming_flags": gaming.flags,
    }).eq("id", session_id).execute()

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

    # ── Sprint A1: Emit crystal_earned + skill_verified to character_state ───
    # Best-effort: never blocks the response. Idempotency via game_character_rewards.
    if slug:
        await emit_assessment_rewards(
            db=db_admin,
            user_id=str(user_id),
            skill_slug=slug,
            competency_score=competency_score,
        )

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

    # Read stored gaming data — do NOT re-run antigaming.analyse()
    # Re-running would cause inconsistency if thresholds change after completion
    gaming_penalty_multiplier = session.get("gaming_penalty_multiplier", 1.0)
    gaming_flags = session.get("gaming_flags") or []
    competency_score = round(theta_to_score(state.theta) * gaming_penalty_multiplier, 2)

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
        gaming_flags=gaming_flags,
        completed_at=session.get("completed_at"),
    )


# ── Coaching models → moved to app/schemas/assessment.py ──────────────────────
# CoachingTip, CoachingResponse: imported above from app.schemas.assessment
# _FALLBACK_TIPS, _DEFAULT_FALLBACK_TIPS: in app/services/assessment/coaching_service.py

# ── Coaching endpoint ──────────────────────────────────────────────────────────


@router.post("/{session_id}/coaching", response_model=CoachingResponse)
@limiter.limit(RATE_LLM)
async def get_coaching(
    request: Request,
    session_id: str,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> CoachingResponse:
    """Generate personalised coaching tips for a completed assessment session.

    Uses Gemini to produce 3 specific, actionable improvement tips based on
    the volunteer's competency score. Result is cached in assessment_sessions.coaching_note
    to avoid redundant LLM calls on repeat requests.
    """
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SESSION_ID", "message": "session_id must be a valid UUID"},
        )

    # Fetch session — must belong to user and be completed
    session_result = (
        await db_user.table("assessment_sessions")
        .select("id, competency_id, theta_estimate, coaching_note")
        .eq("id", session_id)
        .eq("volunteer_id", user_id)
        .eq("status", "completed")
        .maybe_single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "SESSION_NOT_FOUND", "message": "Completed session not found"},
        )

    session = session_result.data
    competency_id: str = session["competency_id"]

    # Return cached coaching note if it already exists
    # coaching_note is JSONB — Supabase returns it as a Python list already
    try:
        cached = session.get("coaching_note")
        if cached and isinstance(cached, list):
            tips = [CoachingTip(**t) for t in cached]
            score = round(theta_to_score(session.get("theta_estimate", 0.0)), 2)
            return CoachingResponse(
                session_id=session_id,
                competency_id=competency_id,
                score=score,
                tips=tips,
            )
    except Exception as e:
        logger.warning("Failed to parse cached coaching_note, regenerating: {err}", err=str(e)[:200])

    # Get competency name and slug
    comp_result = (
        await db_admin.table("competencies")
        .select("name, slug")
        .eq("id", competency_id)
        .maybe_single()
        .execute()
    )
    comp_name = comp_result.data.get("name", "this competency") if comp_result.data else "this competency"
    comp_slug = comp_result.data.get("slug", "") if comp_result.data else ""

    score = round(theta_to_score(session.get("theta_estimate", 0.0)), 2)

    tips = await generate_coaching_tips(
        session_id=session_id,
        competency_id=competency_id,
        competency_name=comp_name,
        competency_slug=comp_slug,
        score=score,
        gemini_api_key=settings.gemini_api_key,
    )

    # Cache result in assessment_sessions.coaching_note (graceful if column missing)
    tips_json = [t.model_dump() for t in tips]
    try:
        await db_admin.table("assessment_sessions").update(
            {"coaching_note": tips_json}
        ).eq("id", session_id).execute()
    except Exception as e:
        logger.warning("Could not cache coaching_note (column may not exist yet): {err}", err=str(e)[:200])

    return CoachingResponse(
        session_id=session_id,
        competency_id=competency_id,
        score=score,
        tips=tips,
    )


# ── Assessment info endpoint ────────────────────────────────────────────────


@router.get("/info/{competency_slug}", response_model=AssessmentInfoOut)
@limiter.limit(RATE_DISCOVERY)
async def get_assessment_info(
    request: Request,
    competency_slug: str,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> AssessmentInfoOut:
    """Return metadata for a competency before the volunteer starts the assessment.

    Includes time estimate, retake eligibility, and days until retake becomes available.
    Used by the pre-assessment info page to show the volunteer what to expect.
    """
    RETEST_COOLDOWN_DAYS = 7

    # Fetch competency metadata (name, description, time_estimate_minutes, can_retake)
    comp_result = (
        await db_user.table("competencies")
        .select("id, name, description, slug, time_estimate_minutes, can_retake")
        .eq("slug", competency_slug)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )
    if not comp_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "COMPETENCY_NOT_FOUND", "message": f"Competency '{competency_slug}' not found"},
        )

    comp = comp_result.data
    competency_id: str = comp["id"]
    can_retake: bool = comp.get("can_retake", True)

    # Compute days_until_retake from last completed session
    days_until_retake: int | None = None
    recent = (
        await db_user.table("assessment_sessions")
        .select("completed_at")
        .eq("volunteer_id", user_id)
        .eq("competency_id", competency_id)
        .eq("status", "completed")
        .order("completed_at", desc=True)
        .limit(1)
        .execute()
    )
    if recent.data and recent.data[0].get("completed_at"):
        last_completed = datetime.fromisoformat(recent.data[0]["completed_at"])
        if last_completed.tzinfo is None:
            last_completed = last_completed.replace(tzinfo=timezone.utc)
        days_since = (datetime.now(timezone.utc) - last_completed).days
        if days_since < RETEST_COOLDOWN_DAYS:
            days_until_retake = RETEST_COOLDOWN_DAYS - days_since

    return AssessmentInfoOut(
        competency_slug=competency_slug,
        name=comp["name"],
        description=comp.get("description"),
        time_estimate_minutes=comp.get("time_estimate_minutes", 15),
        can_retake=can_retake,
        days_until_retake=days_until_retake,
    )
