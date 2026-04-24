from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.assessment_completion_reconciler import _reconcile_job, run_once

USER_ID = "00000000-1111-2222-3333-444444444444"
SESSION_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


def _job(*, status: str = "partial", attempts: int = 1, side_effects: dict | None = None) -> dict:
    base_side_effects = {
        "aura_sync": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "rewards": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "streak": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "analytics": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "email": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "ecosystem_events": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "aura_events": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
        "decision_log": {"status": "done", "attempts": 1, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"},
    }
    if side_effects:
        base_side_effects.update(side_effects)
    return {
        "id": "job-1",
        "session_id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_slug": "communication",
        "status": status,
        "attempts": attempts,
        "side_effects": base_side_effects,
        "result_context": {
            "competency_slug": "communication",
            "competency_score": 72.5,
            "questions_answered": 1,
            "stop_reason": "manual_complete",
            "gaming_flags": [],
            "completed_at": "2026-04-23T10:00:00Z",
            "aura_updated": True,
            "crystals_earned": 0,
            "energy_level": "full",
            "old_badge_tier": "bronze",
            "aura_snapshot": {
                "total_score": 72.5,
                "badge_tier": "silver",
                "competency_scores": {"communication": 72.5},
                "elite_status": False,
                "percentile_rank": 55.0,
            },
        },
        "last_error": None,
        "completed_at": None,
    }


def _session(*, status: str = "completed") -> dict:
    return {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "status": status,
        "answers": {"items": [{"question_id": "q1", "response": 1}]},
        "gaming_flags": [],
    }


def _save_side_effect():
    async def _save(_db, job, **kwargs):
        next_job = dict(job)
        next_job.update(kwargs)
        return next_job

    return _save


@pytest.mark.asyncio
async def test_reconcile_job_replays_pending_rewards_and_completes():
    db = MagicMock()
    rewards_pending = {
        "rewards": {"status": "pending", "attempts": 0, "last_error": None, "updated_at": "2026-04-23T00:00:00Z"}
    }
    job = _job(side_effects=rewards_pending)

    with (
        patch("app.services.assessment_completion_reconciler._fetch_session", new=AsyncMock(return_value=_session())),
        patch("app.services.assessment_completion_reconciler.save_completion_job", new=AsyncMock(side_effect=_save_side_effect())) as save_job,
        patch("app.services.assessment_completion_reconciler.emit_assessment_rewards", new=AsyncMock(return_value=50)) as emit_rewards,
    ):
        outcome = await _reconcile_job(db, job)

    assert outcome == "ok"
    assert emit_rewards.await_count == 1
    assert any(call.kwargs.get("status") == "completed" for call in save_job.await_args_list)


@pytest.mark.asyncio
async def test_reconcile_job_gives_up_after_max_attempts():
    db = MagicMock()
    job = _job(attempts=6)

    with patch("app.services.assessment_completion_reconciler.save_completion_job", new=AsyncMock(side_effect=_save_side_effect())) as save_job:
        outcome = await _reconcile_job(db, job)

    assert outcome == "gave_up"
    assert save_job.await_count == 1
    assert save_job.await_args.kwargs["last_error"].startswith("max_attempts_exceeded")


@pytest.mark.asyncio
async def test_run_once_counts_retry_outcomes():
    db = MagicMock()
    jobs = [_job(), _job()]

    with (
        patch("app.services.assessment_completion_reconciler._admin", new=AsyncMock(return_value=db)),
        patch("app.services.assessment_completion_reconciler._fetch_incomplete_jobs", new=AsyncMock(return_value=jobs)),
        patch("app.services.assessment_completion_reconciler._reconcile_job", new=AsyncMock(side_effect=["ok", "retry"])),
    ):
        stats = await run_once()

    assert stats == {"found": 2, "ok": 1, "retry": 1, "gave_up": 0}
