"""Assessment endpoints — start, answer, complete, results, coaching.

Rate limited:
- /start: 3/hour per user (prevent assessment farming)
- /answer: 60/hour per user (normal pace ~40 questions/session)
- /{session_id}/coaching: 30/hour (LLM rate limit)
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.config import settings
from app.core.assessment import antigaming, bars
from app.middleware.rate_limit import limiter, RATE_ASSESSMENT_START, RATE_ASSESSMENT_ANSWER, RATE_ASSESSMENT_COMPLETE, RATE_LLM
from app.core.assessment.aura_calc import (
    BADGE_TIERS,
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

# Crystal reward per competency completion (completion-based, NOT score-based)
_CRYSTAL_REWARD = 50


# ── helpers ───────────────────────────────────────────────────────────────────


def _competency_badge_tier(score: float) -> str | None:
    """Return badge tier name for a competency score using the same thresholds as AURA."""
    for tier_name, threshold in BADGE_TIERS:
        if score >= threshold:
            return tier_name
    return None


async def _emit_assessment_rewards(
    db: SupabaseAdmin,
    user_id: str,
    skill_slug: str,
    competency_score: float,
) -> None:
    """Emit crystal_earned + skill_verified character events after assessment completion.

    Best-effort: logs errors but never raises — must not fail the complete_assessment response.
    Idempotency: game_character_rewards table ensures one crystal claim per user per competency.
    Anti-farming: idempotency check happens BEFORE any write.
    """
    # ── Idempotency check: already rewarded for this competency? ─────────────
    reward_check = (
        await db.table("game_character_rewards")
        .select("claimed")
        .eq("user_id", user_id)
        .eq("skill_slug", skill_slug)
        .execute()
    )
    crystals_already_claimed = bool(reward_check.data)

    # ── crystal_earned event (50 per competency, once only) ──────────────────
    if not crystals_already_claimed:
        try:
            # Insert character event
            await db.table("character_events").insert({
                "user_id": user_id,
                "event_type": "crystal_earned",
                "payload": {
                    "amount": _CRYSTAL_REWARD,
                    "source": "volaura_assessment",
                    "skill_slug": skill_slug,
                    "_schema_version": 1,
                },
                "source_product": "volaura",
            }).execute()

            # Insert crystal ledger entry
            await db.table("game_crystal_ledger").insert({
                "user_id": user_id,
                "amount": _CRYSTAL_REWARD,
                "source": "volaura_assessment",
                "reference_id": skill_slug,
            }).execute()

            # Mark reward as claimed (idempotency lock)
            await db.table("game_character_rewards").upsert({
                "user_id": user_id,
                "skill_slug": skill_slug,
                "crystals": _CRYSTAL_REWARD,
                "claimed": True,
                "claimed_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

            logger.info(
                "Crystal reward emitted",
                user_id=user_id,
                skill_slug=skill_slug,
                crystals=_CRYSTAL_REWARD,
            )
        except Exception as exc:
            logger.error(
                "Failed to emit crystal reward — manual reconciliation needed",
                user_id=user_id,
                skill_slug=skill_slug,
                error=str(exc),
            )

    # ── skill_verified event (only if score >= Bronze threshold) ────────────
    badge_tier = _competency_badge_tier(competency_score)
    if badge_tier is not None:
        try:
            await db.table("character_events").insert({
                "user_id": user_id,
                "event_type": "skill_verified",
                "payload": {
                    "skill_slug": skill_slug,
                    "aura_score": round(competency_score, 2),
                    "badge_tier": badge_tier,
                    "_schema_version": 1,
                },
                "source_product": "volaura",
            }).execute()

            logger.info(
                "Skill verified event emitted",
                user_id=user_id,
                skill_slug=skill_slug,
                score=competency_score,
                badge_tier=badge_tier,
            )
        except Exception as exc:
            logger.error(
                "Failed to emit skill_verified event",
                user_id=user_id,
                skill_slug=skill_slug,
                error=str(exc),
            )


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

    questions = await _fetch_questions(db_admin, competency_id)
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
        await _emit_assessment_rewards(
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


# ── Coaching models ────────────────────────────────────────────────────────────

class CoachingTip(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str
    action: str


class CoachingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    competency_id: str
    score: float
    tips: list[CoachingTip]


# Generic fallback tips per competency slug
_FALLBACK_TIPS: dict[str, list[dict]] = {
    "communication": [
        {"title": "Practice active listening", "description": "In your next meeting, focus entirely on the speaker without planning your reply.", "action": "After each meeting this week, write 3 key points you heard from others."},
        {"title": "Write daily summaries", "description": "Summarising your day in 3 sentences sharpens clarity and captures learning.", "action": "Spend 5 minutes each evening writing what you accomplished and communicated."},
        {"title": "Join a public speaking group", "description": "Structured practice in low-stakes environments builds confidence fast.", "action": "Find a local Toastmasters chapter or online equivalent and attend one session."},
    ],
    "reliability": [
        {"title": "Use a task tracker", "description": "External systems beat memory. A visible to-do list reduces forgotten commitments.", "action": "Pick one app (Notion, Todoist, or pen+paper) and log every commitment for 7 days."},
        {"title": "Set a 30-minute early reminder", "description": "Arriving or delivering 30 minutes early prevents last-minute failures.", "action": "For every deadline this week, set a calendar alarm 30 minutes before."},
        {"title": "Communicate delays proactively", "description": "Telling people early about a delay preserves trust far better than silence.", "action": "Next time you sense a deadline risk, notify stakeholders before they ask."},
    ],
    "leadership": [
        {"title": "Volunteer to lead a small task", "description": "Leadership skill grows fastest through practice, even on minor tasks.", "action": "Offer to coordinate the next team activity, however small."},
        {"title": "Give specific feedback", "description": "Vague praise helps nobody. Specific observations accelerate growth.", "action": "This week, give one team member a specific, actionable observation about their work."},
        {"title": "Read one leadership case study", "description": "Real-world examples provide mental models you can apply immediately.", "action": "Find a 10-minute case study on a leader you admire and extract one principle."},
    ],
    "english_proficiency": [
        {"title": "Read one English article daily", "description": "Exposure to real written English expands vocabulary and grammar intuitively.", "action": "Choose a topic you care about and read one short article in English every morning."},
        {"title": "Write emails in English", "description": "Writing forces more precise language use than speaking.", "action": "For the next week, write at least one professional email per day in English."},
        {"title": "Watch content with subtitles", "description": "Subtitled video links spoken and written forms of the language.", "action": "Watch 20 minutes of English content with English subtitles today."},
    ],
    "adaptability": [
        {"title": "Embrace one new tool or process", "description": "Deliberately using unfamiliar tools builds comfort with change.", "action": "This week, try a tool or workflow you've been avoiding."},
        {"title": "Reflect on a past change", "description": "Identifying how you handled change before reveals your default patterns.", "action": "Write 3 sentences about a time you adapted successfully. What made it work?"},
        {"title": "Seek feedback on your flexibility", "description": "Others often see our rigidity before we do.", "action": "Ask a colleague: 'In what situations do you think I could be more flexible?'"},
    ],
    "tech_literacy": [
        {"title": "Complete one online tutorial", "description": "Structured tutorials build foundational skills faster than exploration alone.", "action": "Pick a free tutorial on a tool relevant to your volunteer work and finish one module today."},
        {"title": "Document a process you use", "description": "Writing a process down reveals gaps and forces understanding.", "action": "Choose one digital tool you use daily and write a 5-step how-to guide."},
        {"title": "Ask a tech-savvy colleague one question", "description": "Peer learning is faster than documentation for practical skills.", "action": "Identify the most tech-skilled person in your team and ask them one specific question this week."},
    ],
    "event_performance": [
        {"title": "Debrief after every event", "description": "A 10-minute debrief with your team catches lessons while they're fresh.", "action": "After your next event, write: what went well, what didn't, and one thing to change."},
        {"title": "Arrive early and help setup", "description": "Early presence demonstrates commitment and builds event intuition.", "action": "For your next event, arrive 30 minutes before your scheduled start."},
        {"title": "Introduce yourself to 3 new people", "description": "Events are also about building community. Relationships compound over time.", "action": "At your next event, make a point of meeting 3 people you haven't worked with before."},
    ],
    "empathy_safeguarding": [
        {"title": "Practice perspective-taking", "description": "Before responding to a difficult situation, pause and ask: what might this person be experiencing?", "action": "This week, in one challenging interaction, spend 30 seconds thinking from the other person's view before responding."},
        {"title": "Learn one safeguarding principle", "description": "Safeguarding knowledge protects both volunteers and beneficiaries.", "action": "Read your organisation's safeguarding policy or one external resource on volunteer safeguarding today."},
        {"title": "Check in with a quieter teammate", "description": "Empathy in practice means noticing who isn't speaking.", "action": "In your next group setting, notice who is quiet and create space for them to contribute."},
    ],
}

_DEFAULT_FALLBACK_TIPS: list[dict] = [
    {"title": "Set a learning goal", "description": "Clear goals direct effort and make progress visible.", "action": "Write down one specific skill you want to improve this month."},
    {"title": "Seek feedback regularly", "description": "Feedback is the fastest path to improvement when acted upon.", "action": "Ask a teammate or supervisor for one piece of constructive feedback this week."},
    {"title": "Reflect on recent experiences", "description": "Unexamined experience doesn't produce growth.", "action": "Spend 10 minutes writing about a recent challenge: what happened, what you learned."},
]


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
    # Validate session_id is a proper UUID
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
    try:
        cached = session.get("coaching_note")
        if cached:
            tips_data = cached if isinstance(cached, list) else json.loads(cached)
            tips = [CoachingTip(**t) for t in tips_data]
            from app.core.assessment.engine import theta_to_score
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

    # Convert theta to 0-100 score
    from app.core.assessment.engine import theta_to_score
    score = round(theta_to_score(session.get("theta_estimate", 0.0)), 2)

    # Attempt Gemini coaching generation
    tips: list[CoachingTip] = []
    gemini_succeeded = False

    if settings.gemini_api_key:
        try:
            from google import genai as google_genai

            prompt = (
                f"You are a volunteer development coach. "
                f"The volunteer scored {score}/100 in {comp_name}. "
                f"Give exactly 3 specific, actionable improvement tips. "
                f"Return valid JSON only, no markdown, no explanation: "
                f'{{ "tips": [ {{ "title": "str", "description": "str", "action": "str" }}, ... ] }} '
                f"Each tip must be practical and focused on real volunteer scenarios. "
                f"Avoid generic advice like \'read more\' or \'practice more\'."
            )

            client = google_genai.Client(api_key=settings.gemini_api_key)

            async def _call_gemini() -> str:
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt,
                )
                return response.text or ""

            raw_text = await asyncio.wait_for(_call_gemini(), timeout=15.0)

            # Strip markdown fences if present
            clean = raw_text.strip()
            if clean.startswith("```"):
                clean = clean.split("```", 2)[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.rsplit("```", 1)[0].strip()

            parsed = json.loads(clean)
            raw_tips = parsed.get("tips", [])
            tips = [CoachingTip(**t) for t in raw_tips[:3]]
            gemini_succeeded = True

        except asyncio.TimeoutError:
            logger.warning("Gemini coaching timed out for session {sid}", sid=session_id)
        except Exception as e:
            logger.warning("Gemini coaching failed for session {sid}: {err}", sid=session_id, err=str(e)[:300])

    # Fallback tips if Gemini unavailable or failed
    if not gemini_succeeded or not tips:
        fallback_data = _FALLBACK_TIPS.get(comp_slug, _DEFAULT_FALLBACK_TIPS)
        tips = [CoachingTip(**t) for t in fallback_data[:3]]

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
