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
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request
from loguru import logger

from app.config import settings
from app.core.assessment import antigaming, bars
from app.core.assessment.engine import (
    CATState,
    select_next_item,
    should_stop,
    submit_response,
    theta_to_score,
)
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import (
    RATE_ASSESSMENT_ANSWER,
    RATE_ASSESSMENT_COMPLETE,
    RATE_ASSESSMENT_START,
    RATE_DISCOVERY,
    RATE_LLM,
    limiter,
)
from app.schemas.assessment import (
    AnswerFeedback,
    AssessmentInfoOut,
    AssessmentResultOut,
    CoachingResponse,
    CoachingTip,
    PublicVerificationOut,
    QuestionBreakdownOut,
    QuestionResultOut,
    SessionOut,
    StartAssessmentRequest,
    SubmitAnswerRequest,
)
from app.services.analytics import track_event
from app.services.assessment.coaching_service import generate_coaching_tips
from app.services.assessment.helpers import (
    fetch_questions,
    get_competency_id,
    get_competency_slug,
    make_session_out,
)
from app.services.assessment.rewards import emit_assessment_rewards
from app.services.email import send_aura_ready_email
from app.services.notification_service import notify
from app.services.tribe_streak_tracker import record_assessment_activity

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

    # PAYWALL: check subscription status before allowing new session
    # Gated by PAYMENT_ENABLED kill switch — False during beta, True when billing is live.
    if settings.payment_enabled:
        sub_result = (
            await db_user.table("profiles").select("subscription_status").eq("id", user_id).maybe_single().execute()
        )
        # Fail-closed: if no profile row exists (shouldn't happen post-onboarding),
        # block by default. A missing profile is not a free pass to unlimited assessments.
        if not sub_result.data:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "SUBSCRIPTION_REQUIRED",
                    "message": "Your trial has ended. Subscribe to continue.",
                },
            )
        sub_status = sub_result.data.get("subscription_status", "trial")
        if sub_status in ("expired", "cancelled"):
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "SUBSCRIPTION_REQUIRED",
                    "message": "Your trial has ended. Subscribe to continue.",
                },
            )

    # GDPR Article 22: require explicit consent for automated decision-making.
    # The AURA score is computed by an automated system (IRT/CAT + LLM evaluation)
    # and affects discoverability by organizations — a "significant effect" under Art. 22.
    if not payload.automated_decision_consent:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "CONSENT_REQUIRED",
                "message": "You must acknowledge that this assessment uses automated scoring before starting.",
            },
        )

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

    # SECURITY: Rapid-restart cooldown — 30 minutes between ANY starts (including abandoned).
    # Prevents answer-fishing: start → see hard question → abandon → restart to cherry-pick.
    # The 7-day cooldown below only gates COMPLETED sessions; this gates ALL starts.
    RAPID_RESTART_COOLDOWN_MINUTES = 30
    recent_start = (
        await db_user.table("assessment_sessions")
        .select("started_at, status")
        .eq("volunteer_id", user_id)
        .eq("competency_id", competency_id)
        .neq("status", "completed")  # completed sessions use the 7-day cooldown below
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )
    if recent_start.data and recent_start.data[0].get("started_at"):
        try:
            last_start = datetime.fromisoformat(recent_start.data[0]["started_at"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            last_start = None
        if last_start is not None:
            if last_start.tzinfo is None:
                last_start = last_start.replace(tzinfo=UTC)
            minutes_since = (datetime.now(UTC) - last_start).total_seconds() / 60
            if minutes_since < RAPID_RESTART_COOLDOWN_MINUTES:
                retry_in = int(RAPID_RESTART_COOLDOWN_MINUTES - minutes_since) + 1
                logger.warning(
                    "Rapid-restart attempt blocked",
                    user_id=user_id,
                    competency_id=competency_id,
                    minutes_since=round(minutes_since, 1),
                )
                # Re-engagement notification: fire-and-forget, never blocks the 429 response.
                # Tells the user exactly when they can come back — turns a dead end into a nudge.
                await notify(
                    db_admin,
                    user_id,
                    "assessment_cooldown",
                    "Retake window opens soon",
                    body=f"Your {payload.competency_slug.replace('_', ' ').title()} retake is ready in {retry_in} minute(s) — come back to improve your AURA score.",
                )
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "RAPID_RESTART_COOLDOWN",
                        "message": f"Please wait {retry_in} minute(s) before starting a new session for this competency",
                        "retry_after_minutes": retry_in,
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
            last_completed = last_completed.replace(tzinfo=UTC)
        # BUG-009 FIX: use total_seconds() not .days — .days truncates (1d 23h = 1, not 2)
        days_since = int((datetime.now(UTC) - last_completed).total_seconds() // 86400)
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
        .gte("started_at", (datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)).isoformat())
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
                    completed_dt = completed_dt.replace(tzinfo=UTC)
                days_elapsed = max(0.0, (datetime.now(UTC) - completed_dt).total_seconds() / 86400)
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
    session_data: dict = {
        "id": session_id,
        "volunteer_id": user_id,
        "competency_id": competency_id,
        "status": "in_progress",
        "role_level": payload.role_level,  # Phase 1: role-level tracking
        "theta_estimate": state.theta,
        "theta_se": state.theta_se,
        "answers": state.to_dict(),
        "current_question_id": first_q["id"] if first_q else None,
        "question_delivered_at": datetime.now(UTC).isoformat(),  # HIGH-03: server-side timing
        "started_at": datetime.now(UTC).isoformat(),
    }
    # Session metadata: energy level + GDPR Article 22 consent timestamp
    metadata: dict = {}
    if payload.energy_level != "full":
        metadata["energy_level"] = payload.energy_level
    metadata["article22_consent_at"] = datetime.now(UTC).isoformat()
    session_data["metadata"] = metadata
    await db_user.table("assessment_sessions").insert(session_data).execute()

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
    # Capture now_utc once — used for expiry check, timing, and session update timestamps
    now_utc = datetime.now(UTC)
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

    # SEC-ANSWER-01: Subscription gate on every answer submission — fail-closed.
    # A user could start a session while on trial (gated), let subscription expire,
    # then continue submitting answers indefinitely. This closes that gap.
    # Pattern mirrors start_assessment paywall (lines ~90-117). Both must stay in sync.
    if settings.payment_enabled:
        sub_result = (
            await db_user.table("profiles").select("subscription_status").eq("id", user_id).maybe_single().execute()
        )
        if not sub_result.data:
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "SUBSCRIPTION_REQUIRED",
                    "message": "Your trial has ended. Subscribe to continue.",
                },
            )
        sub_status = sub_result.data.get("subscription_status", "trial")
        if sub_status in ("expired", "cancelled"):
            raise HTTPException(
                status_code=402,
                detail={
                    "code": "SUBSCRIPTION_REQUIRED",
                    "message": "Your trial has ended. Subscribe to continue.",
                },
            )

    # BUG-010 FIX: reject answers to expired sessions
    # BUG-QA-023 FIX: wrap fromisoformat in try/except — malformed expires_at must not crash
    expires_at_str = session.get("expires_at")
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            logger.warning(
                "Malformed expires_at in session — skipping expiry check",
                session_id=session.get("id"),
                expires_at_raw=expires_at_str,
            )
            expires_at = None
        if expires_at and now_utc > expires_at:
            raise HTTPException(
                status_code=410,
                detail={
                    "code": "SESSION_EXPIRED",
                    "message": "This assessment session has expired. Please start a new one.",
                },
            )

    if session.get("current_question_id") != payload.question_id:
        raise HTTPException(
            status_code=422,
            detail={"code": "WRONG_QUESTION", "message": "This is not the current active question"},
        )

    # HIGH-01: Read current version for optimistic locking
    current_version = session.get("answer_version", 0)

    # Load question details
    q_result = await db_admin.table("questions").select("*").eq("id", payload.question_id).single().execute()
    if not q_result.data:
        raise HTTPException(status_code=404, detail={"code": "QUESTION_NOT_FOUND", "message": "Question not found"})

    question = q_result.data

    # HIGH-03: Server-side timing — don't trust client response_time_ms
    # SECURITY: Reject future question_delivered_at (DB manipulation detection).
    # If a user tampers with assessment_sessions directly, question_delivered_at
    # could be a future timestamp — server_elapsed_ms would be negative, bypassing
    # all timing anti-gaming checks. Clamp to 0 and log the anomaly.
    question_delivered_at = session.get("question_delivered_at")
    if question_delivered_at:
        try:
            delivered_dt = datetime.fromisoformat(question_delivered_at.replace("Z", "+00:00"))
            if delivered_dt.tzinfo is None:
                delivered_dt = delivered_dt.replace(tzinfo=UTC)
            if delivered_dt > now_utc:
                # Future timestamp = tampered session — log and treat as 0ms elapsed
                logger.warning(
                    "Future question_delivered_at detected — possible DB manipulation",
                    user_id=user_id,
                    session_id=payload.session_id,
                    delivered_at=question_delivered_at,
                    server_now=now_utc.isoformat(),
                    skew_ms=int((delivered_dt - now_utc).total_seconds() * 1000),
                )
                server_elapsed_ms = 0  # treat as instant answer — triggers timing flag
            else:
                server_elapsed_ms = int((now_utc - delivered_dt).total_seconds() * 1000)
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
        if not correct_answer:
            logger.warning("MCQ question has no correct_answer", question_id=question.get("id"))
        raw_score = (
            1.0 if (correct_answer and payload.answer.strip().lower() == correct_answer.strip().lower()) else 0.0
        )
    else:
        # Open-ended → LLM evaluation (multi-model swarm or single-model BARS)
        expected_concepts: list[dict] = question.get("expected_concepts") or []
        evaluation_log = None

        # ── Per-user daily LLM cap (RISK-013) ────────────────────────────────
        # Cap open-ended LLM evaluations at 20/day per user to prevent Gemini
        # RPM saturation by adversarial accounts (60 answers/hour × 5 accounts
        # = 300 LLM calls → saturates 15 RPM in seconds).
        # Strategy: count all answered items in today's sessions for this user.
        # Each session stores items in answers JSONB — fetch answers field only.
        # Max payload: ~3 sessions × ~8 items × ~200 bytes = tiny, no joins needed.
        # Over the cap → force keyword_fallback (same as normal LLM failure path).
        # The reeval_worker picks up degraded answers and rescores within ~60s.
        _DAILY_LLM_CAP = 20
        _force_degraded = False
        try:
            today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            today_sessions_result = (
                await db_admin.table("assessment_sessions")
                .select("answers")
                .eq("volunteer_id", user_id)
                .gte("started_at", today_start)
                .execute()
            )
            daily_llm_count = 0
            for _sess in today_sessions_result.data or []:
                _answers_blob = _sess.get("answers") or {}
                daily_llm_count += len(_answers_blob.get("items", []))

            if daily_llm_count >= _DAILY_LLM_CAP:
                _force_degraded = True
                logger.warning(
                    "daily_llm_cap_hit",
                    user_id=user_id,
                    daily_count=daily_llm_count,
                    cap=_DAILY_LLM_CAP,
                )
        except Exception as _cap_err:
            # Cap check failure → fail-closed: degrade to keyword fallback rather than
            # allowing unlimited LLM calls. Supabase timeout/network error must not
            # defeat the anti-saturation guard (RISK-013).
            _force_degraded = True
            logger.warning(
                "daily_llm_cap_check_failed — degrading to keyword fallback",
                user_id=user_id,
                error=str(_cap_err)[:120],
            )

        if settings.swarm_enabled and not _force_degraded:
            # BUG-01 fix (2026-03-25): use return_details=True so swarm path
            # produces evaluation_log for Phase 2 Transparent Logs.
            # Daily cap (_force_degraded=True) bypasses swarm — bars keyword_fallback used instead.
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
                force_degraded=_force_degraded,
            )
            raw_score = eval_result.composite
            evaluation_log = eval_result.to_log()

        # ADR-010: If evaluation fell back to keyword matching, enqueue for LLM re-eval.
        # The degraded score is used immediately (user sees it now); the worker will
        # silently replace it with a proper LLM score within ~60 seconds.
        if evaluation_log and evaluation_log.get("evaluation_mode") == "degraded":
            comp_slug_for_queue = await get_competency_slug(db_admin, session["competency_id"])
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

    # Check stopping criteria (Constitution Law 2: Energy Adaptation)
    # Read energy_level from session metadata; defaults to "full" if not set
    session_metadata = session.get("metadata") or {}
    energy_level = session_metadata.get("energy_level", "full") if isinstance(session_metadata, dict) else "full"
    stopped, stop_reason = should_stop(state, energy_level=energy_level)
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
        "question_delivered_at": now_utc.isoformat() if next_q else None,
        "answer_version": current_version + 1,  # HIGH-01: increment version
    }
    # NOTE: we intentionally do NOT mark status="completed" here, even when the
    # CAT engine signals state.stopped. The `/complete/{session_id}` endpoint
    # owns the full finalisation pipeline (anti-gaming recompute, upsert_aura_score,
    # emit_rewards, analytics). If we marked status=completed here, /complete would
    # hit its BUG-015 idempotency branch and skip the RPC, leaving the user with a
    # completed session but no AURA row. E2E smoke (2026-04-11) caught this: every
    # naturally-completed assessment returned aura_updated=False and /aura/me 404.
    # The client still sees is_complete=true in the returned SessionOut and should
    # call POST /api/assessment/complete/{session_id} next.

    # HIGH-01: Optimistic locking — only update if version hasn't changed
    # BLOCKER-1 FIX: Use db_admin (service_role) for updates — user-level UPDATE policy removed
    # to prevent direct PostgREST theta manipulation
    update_result = (
        await db_admin.table("assessment_sessions")
        .update(update_payload)
        .eq("id", payload.session_id)
        .eq("volunteer_id", user_id)
        .eq("answer_version", current_version)
        .execute()
    )

    if not update_result.data:
        raise HTTPException(
            status_code=409,
            detail={"code": "CONCURRENT_SUBMIT", "message": "This answer was already submitted. Please refresh."},
        )

    # Get competency slug for response (cached — 8-row static table)
    slug = await get_competency_slug(db_admin, competency_id)

    session_out = make_session_out(payload.session_id, slug, state, next_q, session.get("role_level", "professional"))

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
        raise HTTPException(
            status_code=422, detail={"code": "INVALID_SESSION_ID", "message": "session_id must be a valid UUID"}
        )

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

    # BUG-015 FIX: if session already completed, return stored results without re-running pipeline.
    # Prevents: double upsert_aura_score, duplicate aura_history entries, double emit_rewards.
    # Race scenario: submit_answer(last Q) + complete_assessment fire simultaneously.
    if session.get("status") == "completed":
        comp_result_early = (
            await db_admin.table("competencies").select("slug").eq("id", session["competency_id"]).single().execute()
        )
        slug_early = comp_result_early.data["slug"] if comp_result_early.data else ""
        state_early = CATState.from_dict(session["answers"] or {})
        stored_multiplier = float(session.get("gaming_penalty_multiplier") or 1.0)
        stored_flags = session.get("gaming_flags") or []
        competency_score_early = round(theta_to_score(state_early.theta) * stored_multiplier, 2)
        return AssessmentResultOut(
            session_id=session_id,
            competency_slug=slug_early,
            competency_score=competency_score_early,
            questions_answered=len(state_early.items),
            stop_reason=state_early.stop_reason,
            aura_updated=False,  # already updated in the original complete call
            gaming_flags=stored_flags,
            completed_at=session.get("completed_at") or datetime.now(UTC),
        )

    # BUG-010 FIX: reject completion of expired sessions (expired but in_progress sessions)
    expires_at_str = session.get("expires_at")
    if expires_at_str and session.get("status") == "in_progress":
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        if datetime.now(UTC) > expires_at:
            raise HTTPException(
                status_code=410,
                detail={
                    "code": "SESSION_EXPIRED",
                    "message": "This assessment session has expired. Please start a new one.",
                },
            )

    state = CATState.from_dict(session["answers"] or {})

    # Anti-gaming analysis — run ONCE here, store in session (never re-run in get_results)
    gaming = antigaming.analyse(state.to_dict().get("items", []))
    raw_competency_score = theta_to_score(state.theta)
    competency_score = round(raw_competency_score * gaming.penalty_multiplier, 2)

    # Force-complete if somehow still open — single UPDATE merging all fields (no race condition)
    if session["status"] == "in_progress":
        state.stopped = True
        state.stop_reason = "manual_complete"
        # BLOCKER-1 FIX: Use db_admin for updates (user-level UPDATE policy removed)
        # BUG-001 FIX: merged gaming columns into single UPDATE — eliminates double-write race
        await (
            db_admin.table("assessment_sessions")
            .update(
                {
                    "status": "completed",
                    "theta_estimate": state.theta,
                    "theta_se": state.theta_se,
                    "answers": state.to_dict(),
                    "completed_at": datetime.now(UTC).isoformat(),
                    "gaming_penalty_multiplier": gaming.penalty_multiplier,
                    "gaming_flags": gaming.flags,
                }
            )
            .eq("id", session_id)
            .execute()
        )
    else:
        # Session was already completed — still sync final gaming analysis in one update
        await (
            db_admin.table("assessment_sessions")
            .update(
                {
                    "gaming_penalty_multiplier": gaming.penalty_multiplier,
                    "gaming_flags": gaming.flags,
                }
            )
            .eq("id", session_id)
            .execute()
        )

    # Get competency slug
    comp_result = (
        await db_admin.table("competencies").select("slug").eq("id", session["competency_id"]).single().execute()
    )
    slug = comp_result.data["slug"] if comp_result.data else ""

    # Upsert AURA score via DB RPC
    aura_updated = False
    if slug:
        try:
            rpc_result = await db_admin.rpc(
                "upsert_aura_score",
                {
                    "p_volunteer_id": user_id,
                    "p_competency_scores": {slug: competency_score},
                },
            ).execute()
            aura_updated = rpc_result.data is not None
            if not aura_updated:
                logger.warning(
                    "upsert_aura_score returned no data",
                    user_id=str(user_id),
                    competency_slug=slug,
                    session_id=session_id,
                )
        except Exception as rpc_error:
            logger.error(
                "upsert_aura_score RPC failed — AURA score not updated",
                user_id=str(user_id),
                competency_slug=slug,
                session_id=session_id,
                error=str(rpc_error),
            )
            aura_updated = False
            # Best-effort: mark session as needing AURA sync so CTO can query
            # SELECT id FROM assessment_sessions WHERE pending_aura_sync = true
            try:
                await (
                    db_admin.table("assessment_sessions")
                    .update({"pending_aura_sync": True})
                    .eq("id", session_id)
                    .execute()
                )
            except Exception:
                pass  # non-fatal — primary error is already logged above

    # ── Sprint A1: Emit crystal_earned + skill_verified to character_state ───
    # Best-effort: never blocks the response. Idempotency via game_character_rewards.
    # Sprint 7: pass user JWT so cross_product_bridge can authenticate with MindShift.
    crystals_earned = 0
    if slug:
        _auth_header = request.headers.get("Authorization", "")
        _user_jwt: str | None = _auth_header.removeprefix("Bearer ").strip() or None
        crystals_earned = int(
            await emit_assessment_rewards(
                db=db_admin,
                user_id=str(user_id),
                skill_slug=slug,
                competency_score=competency_score,
                user_jwt=_user_jwt,
            )
            or 0
        )

    # Tribe streak: record activity for current week (fire-and-forget, never blocks response)
    try:
        await record_assessment_activity(db=db_admin, user_id=str(user_id))
    except Exception:
        pass  # tribe streak failure must never fail assessment completion

    # Analytics: assessment_completed event (fire-and-forget, never blocks response)
    try:
        await track_event(
            db=db_admin,
            user_id=str(user_id),
            event_name="assessment_completed",
            session_id=session_id,
            properties={
                "competency_slug": slug,
                "competency_score": competency_score,
                "questions_answered": len(state.items),
                "stop_reason": state.stop_reason,
                "aura_updated": aura_updated,
                "crystals_earned": crystals_earned,
                "gaming_flags": gaming.flags,
            },
        )
    except Exception:
        pass  # analytics failure must never fail assessment completion

    # Transactional email: AURA score ready (fire-and-forget, kill switch: EMAIL_ENABLED)
    try:
        user_resp = await db_admin.auth.admin.get_user_by_id(str(user_id))
        user_email = user_resp.user.email if user_resp and user_resp.user else None
        if user_email:
            # Resolve badge tier from aura_scores (best-effort; defaults to "bronze" if missing)
            badge_resp = (
                await db_admin.table("aura_scores")
                .select("badge_tier")
                .eq("volunteer_id", str(user_id))
                .maybe_single()
                .execute()
            )
            badge_tier = (badge_resp.data or {}).get("badge_tier", "bronze")

            # display_name from profiles (best-effort; falls back to "there")
            prof_resp = (
                await db_admin.table("profiles").select("display_name").eq("id", str(user_id)).maybe_single().execute()
            )
            display_name = (prof_resp.data or {}).get("display_name") or ""

            await send_aura_ready_email(
                to_email=user_email,
                display_name=display_name,
                competency_slug=slug,
                competency_score=competency_score,
                badge_tier=badge_tier,
                crystals_earned=crystals_earned,
            )
    except Exception:
        pass  # email failure must never fail assessment completion

    return AssessmentResultOut(
        session_id=session_id,
        competency_slug=slug,
        # theta/theta_se intentionally NOT sent to client (security audit P1)
        competency_score=competency_score,
        questions_answered=len(state.items),
        stop_reason=state.stop_reason,
        aura_updated=aura_updated,
        gaming_flags=gaming.flags,
        completed_at=datetime.now(UTC),
        crystals_earned=crystals_earned,
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
        raise HTTPException(
            status_code=422, detail={"code": "INVALID_SESSION_ID", "message": "session_id must be a valid UUID"}
        )

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
        await db_admin.table("competencies").select("name_en, slug").eq("id", competency_id).maybe_single().execute()
    )
    comp_name = comp_result.data.get("name_en", "this competency") if comp_result.data else "this competency"
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
        await db_admin.table("assessment_sessions").update({"coaching_note": tips_json}).eq("id", session_id).execute()
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
        .select("id, name_en, description_en, slug, time_estimate_minutes, can_retake")
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
            last_completed = last_completed.replace(tzinfo=UTC)
        # BUG-009 FIX: use total_seconds() not .days — .days truncates (1d 23h = 1, not 2)
        days_since = int((datetime.now(UTC) - last_completed).total_seconds() // 86400)
        if days_since < RETEST_COOLDOWN_DAYS:
            days_until_retake = RETEST_COOLDOWN_DAYS - days_since

    return AssessmentInfoOut(
        competency_slug=competency_slug,
        name=comp["name_en"],
        description=comp.get("description_en"),
        time_estimate_minutes=comp.get("time_estimate_minutes", 15),
        can_retake=can_retake,
        days_until_retake=days_until_retake,
    )


# ── Per-question breakdown ──────────────────────────────────────────────────

# IRT difficulty mapping: irt_b → human-readable label
# Thresholds chosen to map the standard normal range to 4 buckets.
_DIFFICULTY_THRESHOLDS: list[tuple[float, str]] = [
    (1.5, "expert"),  # irt_b >= 1.5
    (0.5, "hard"),  # 0.5 <= irt_b < 1.5
    (-0.5, "medium"),  # -0.5 <= irt_b < 0.5
]
_DIFFICULTY_DEFAULT = "easy"  # irt_b < -0.5


def _irt_b_to_label(irt_b: float) -> str:
    """Map IRT difficulty parameter to a human-readable label. Never exposes numeric value."""
    for threshold, label in _DIFFICULTY_THRESHOLDS:
        if irt_b >= threshold:
            return label
    return _DIFFICULTY_DEFAULT


@router.get("/results/{session_id}/questions", response_model=QuestionBreakdownOut)
@limiter.limit(RATE_DISCOVERY)
async def get_question_breakdown(
    request: Request,
    session_id: str,
    db_admin: SupabaseAdmin,
    db_user: SupabaseUser,
    user_id: CurrentUserId,
) -> QuestionBreakdownOut:
    """Return per-question breakdown for a completed session.

    Each question shows: text (EN/AZ), difficulty label, correctness, response time.
    IRT parameters and raw scores are NEVER exposed (security audit CRIT-03).
    """
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SESSION_ID", "message": "session_id must be a valid UUID"},
        )

    # Fetch completed session — user can only see own
    session_result = (
        await db_user.table("assessment_sessions")
        .select("id, competency_id, answers, theta_estimate, gaming_penalty_multiplier")
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
    state = CATState.from_dict(session["answers"] or {})

    if not state.items:
        raise HTTPException(
            status_code=404,
            detail={"code": "NO_ANSWERS", "message": "Session has no answered questions"},
        )

    # Batch-fetch question texts (single query, not N+1)
    question_ids = [item.question_id for item in state.items]
    q_result = (
        await db_admin.table("questions")
        .select("id, scenario_en, scenario_az, scenario_ru")
        .in_("id", question_ids)
        .execute()
    )
    q_map = {q["id"]: q for q in (q_result.data or [])}

    # Get competency slug for response
    comp_result = (
        await db_admin.table("competencies").select("slug").eq("id", session["competency_id"]).maybe_single().execute()
    )
    comp_slug = comp_result.data["slug"] if comp_result.data else "unknown"

    # Build per-question results — IRT params mapped to labels, raw_score → boolean
    questions_out: list[QuestionResultOut] = []
    for item in state.items:
        q_data = q_map.get(item.question_id, {})
        questions_out.append(
            QuestionResultOut(
                question_id=item.question_id,
                question_en=q_data.get("scenario_en"),
                question_az=q_data.get("scenario_az"),
                question_ru=q_data.get("scenario_ru"),
                difficulty_label=_irt_b_to_label(item.irt_b),
                is_correct=item.raw_score > 0,
                response_time_ms=item.response_time_ms,
            )
        )

    competency_score = round(theta_to_score(state.theta) * (session.get("gaming_penalty_multiplier") or 1.0), 2)

    return QuestionBreakdownOut(
        session_id=session_id,
        competency_slug=comp_slug,
        competency_score=competency_score,
        questions=questions_out,
    )


# ── Public verification (no auth — for LinkedIn badge click-through) ─────────


@router.get("/verify/{session_id}", response_model=PublicVerificationOut)
@limiter.limit(RATE_DISCOVERY)
async def verify_assessment(
    request: Request,
    session_id: str,
    db_admin: SupabaseAdmin,
) -> PublicVerificationOut:
    """Public verification endpoint — no auth required.

    When someone clicks a shared badge link on LinkedIn, they land on a page
    that calls this endpoint to prove the assessment is real.

    Returns: competency, score, badge tier, questions answered, completion date.
    Does NOT return: questions, answers, IRT parameters, theta.
    """
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_SESSION_ID", "message": "Invalid session ID"},
        )

    # Fetch completed session (service-role — no RLS, but only completed sessions)
    session_result = (
        await db_admin.table("assessment_sessions")
        .select("id, volunteer_id, competency_id, status, answers, completed_at, gaming_penalty_multiplier")
        .eq("id", session_id)
        .eq("status", "completed")
        .maybe_single()
        .execute()
    )
    if not session_result.data:
        raise HTTPException(
            status_code=404,
            detail={"code": "SESSION_NOT_FOUND", "message": "Completed assessment not found"},
        )

    session = session_result.data
    state = CATState.from_dict(session["answers"] or {})
    competency_score = round(theta_to_score(state.theta) * (session.get("gaming_penalty_multiplier") or 1.0), 2)

    # Competency name
    comp_result = (
        await db_admin.table("competencies")
        .select("slug, name_en")
        .eq("id", session["competency_id"])
        .maybe_single()
        .execute()
    )
    comp_data = comp_result.data or {}

    # Badge tier from aura_scores
    aura_result = (
        await db_admin.table("aura_scores")
        .select("badge_tier")
        .eq("volunteer_id", session["volunteer_id"])
        .maybe_single()
        .execute()
    )
    badge_tier = (aura_result.data or {}).get("badge_tier", "none")

    # User display info (public-safe)
    profile_result = (
        await db_admin.table("profiles")
        .select("display_name, username")
        .eq("id", session["volunteer_id"])
        .maybe_single()
        .execute()
    )
    profile = profile_result.data or {}

    return PublicVerificationOut(
        session_id=session_id,
        competency_slug=comp_data.get("slug", ""),
        competency_name=comp_data.get("name_en"),
        competency_score=competency_score,
        badge_tier=badge_tier,
        questions_answered=len(state.items),
        completed_at=session.get("completed_at"),
        display_name=profile.get("display_name"),
        username=profile.get("username"),
    )
