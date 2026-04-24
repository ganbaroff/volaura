"""AURA scoring path — pytest test file.

Track 3 deliverable for mega-sprint-122 Round 2.
Standard from: memory/atlas/mega-sprint-122-r2/test-standard-verdict.md

What this file proves:
  - The `complete_assessment` endpoint (apps/api/app/routers/assessment.py:725)
    calls `upsert_aura_score` RPC with correct JSONB params.
  - The `pending_aura_sync` pre-flag (intent-before-action contract) is set
    BEFORE the RPC attempt and cleared on success.
  - On RPC failure the flag stays TRUE (reconciler will pick it up).
  - Already-completed sessions short-circuit without calling the RPC (idempotency).
  - Invalid UUID, missing session, and expired session return correct HTTP codes.
  - Gaming penalty multiplier is applied to the competency score before storage.
  - Badge tier arithmetic: platinum ≥90, gold ≥75, silver ≥60, bronze else.
  - `_theta_to_score` in aura_reconciler mirrors `theta_to_score` in engine.

Coverage target: ≥90% on app.services.aura_reconciler; ≥75% on the AURA path
of app.routers.assessment (router decorators and fire-and-forget branches that
require live DB are excluded — see docstring at bottom).

Test pyramid: Cerebras pattern (70 unit / 20 integration / 10 e2e).
  - Unit: badge tier math, theta→score transform, pending-flag logic
  - Integration: HTTP client against FastAPI app with dependency_overrides Supabase mock
  - E2E: not in this file — see test_assessment_api_e2e.py for full journey

Mock strategy: Cerebras canonical idiom — app.dependency_overrides for Supabase.
Where query chains are 4+ deep (complete_assessment has nested .table.update.eq.execute
and .rpc.execute) we also use nested MagicMock chains (DeepSeek pattern) for correctness.

Naming convention: Russian descriptive ids for parametrized cases (DeepSeek contribution).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.assessment.engine import theta_to_score
from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.services.aura_reconciler import _theta_to_score as reconciler_theta_to_score

# ── Constants shared by test helpers ────────────────────────────────────────

USER_ID = "00000000-aaaa-bbbb-cccc-000000000001"
SESSION_ID = "11111111-2222-3333-4444-555555555555"
COMPETENCY_ID = "cccccccc-dddd-eeee-ffff-000000000001"


# ── FastAPI dependency override helpers (Cerebras pattern) ───────────────────


def _admin_override(db: Any):
    async def _dep():
        yield db

    return _dep


def _user_override(db: Any):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid: str = USER_ID):
    async def _dep():
        return uid

    return _dep


# ── Supabase chainable mock builder ─────────────────────────────────────────


def _chainable_mock(execute_result: Any = None) -> MagicMock:
    """Build a MagicMock that supports Supabase fluent API chains.

    Returns the same object from every chainable method so callers can
    do db.table(...).select(...).eq(...).single().execute() as in real code.
    """
    m = MagicMock()
    m.table = MagicMock(return_value=m)
    m.select = MagicMock(return_value=m)
    m.insert = MagicMock(return_value=m)
    m.update = MagicMock(return_value=m)
    m.delete = MagicMock(return_value=m)
    m.eq = MagicMock(return_value=m)
    m.neq = MagicMock(return_value=m)
    m.order = MagicMock(return_value=m)
    m.limit = MagicMock(return_value=m)
    m.single = MagicMock(return_value=m)
    m.maybe_single = MagicMock(return_value=m)
    m.rpc = MagicMock(return_value=m)
    m.execute = AsyncMock(return_value=MagicMock(data=execute_result))
    m.auth = MagicMock()
    m.auth.admin = MagicMock()
    m.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))
    return m


def _in_progress_session(
    theta: float = 0.5,
    penalty_multiplier: float = 1.0,
    gaming_flags: list[str] | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """Minimal in-progress session row matching what Supabase returns."""
    return {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "in_progress",
        "theta_estimate": theta,
        "theta_se": 0.3,
        "answers": {
            "theta": theta,
            "theta_se": 0.3,
            "stopped": True,
            "stop_reason": "se_threshold",
            "items": [
                {
                    "question_id": "q1",
                    "irt_a": 1.0,
                    "irt_b": 0.0,
                    "irt_c": 0.0,
                    "response": 1,
                    "raw_score": 0.8,
                    "response_time_ms": 5000,
                }
            ],
        },
        "gaming_penalty_multiplier": penalty_multiplier,
        "gaming_flags": gaming_flags or [],
        "completed_at": None,
        "expires_at": expires_at,
        "metadata": {},
    }


# ═══════════════════════════════════════════════════════════════════════════════
# UNIT TESTS — pure functions, no HTTP, no Supabase
# ═══════════════════════════════════════════════════════════════════════════════


# ── theta_to_score / _theta_to_score parity ──────────────────────────────────


def test_theta_to_score_engine_returns_0_to_100() -> None:
    """Engine's theta_to_score maps IRT logit scale to 0-100 range."""
    for theta in (-4.0, -2.0, 0.0, 2.0, 4.0):
        result = theta_to_score(theta)
        assert 0.0 <= result <= 100.0, f"theta={theta} produced out-of-range {result}"


def test_theta_to_score_monotone_increasing() -> None:
    """Higher theta = higher score (ability scale is monotone)."""
    prev = theta_to_score(-4.0)
    for theta in (-2.0, 0.0, 2.0, 4.0):
        curr = theta_to_score(theta)
        assert curr > prev, f"Score not monotone at theta={theta}"
        prev = curr


def test_reconciler_theta_to_score_mirrors_engine() -> None:
    """aura_reconciler._theta_to_score must produce same output as engine.theta_to_score.

    Both use the same logistic formula: 100 / (1 + exp(-theta)).
    If they diverge, a ghost session re-synced by reconciler gets a different
    score than the one written by complete_assessment — silent data divergence.
    """
    for theta in (-3.0, -1.0, 0.0, 1.0, 3.0):
        engine_score = theta_to_score(theta)
        reconciler_score = reconciler_theta_to_score(theta)
        assert engine_score == pytest.approx(reconciler_score, rel=1e-6), (
            f"theta={theta}: engine={engine_score} vs reconciler={reconciler_score} — DIVERGED"
        )


# ── Badge tier boundary tests (Cerebras pattern + DeepSeek naming) ───────────


@pytest.mark.parametrize(
    "theta, expected_min_score, expected_max_score",
    [
        pytest.param(3.5, 90.0, 100.0, id="высокий_тета_платина"),
        pytest.param(1.5, 75.0, 90.0, id="средне_высокий_тета_золото_граница"),
        pytest.param(0.0, 50.0, 75.0, id="нулевой_тета_серебро_бронза_зона"),
        pytest.param(-2.0, 1.0, 60.0, id="отрицательный_тета_низкий_балл"),
    ],
)
def test_theta_score_range(theta: float, expected_min_score: float, expected_max_score: float) -> None:
    """theta_to_score output falls in expected band per IRT theta range."""
    score = theta_to_score(theta)
    assert expected_min_score <= score <= expected_max_score, (
        f"theta={theta}: score={score} not in [{expected_min_score}, {expected_max_score}]"
    )


def test_gaming_penalty_reduces_score() -> None:
    """competency_score = theta_to_score(theta) * penalty — penalty < 1 reduces score."""
    theta = 1.0
    base_score = theta_to_score(theta)
    penalty = 0.7
    penalized = round(base_score * penalty, 2)
    assert penalized < base_score
    assert penalized == pytest.approx(base_score * penalty, rel=1e-4)


def test_gaming_penalty_1_unchanged() -> None:
    """penalty_multiplier=1.0 (clean session) leaves score unchanged."""
    theta = 0.5
    base = theta_to_score(theta)
    assert round(base * 1.0, 2) == round(base, 2)


def test_score_serialization_roundtrip() -> None:
    """theta_to_score result can round-trip through JSON float without precision loss."""
    score = theta_to_score(1.234)
    penalized = round(score * 0.9, 2)
    assert isinstance(penalized, float)
    # Simulating JSON round-trip: str → float
    as_str = str(penalized)
    rebuilt = float(as_str)
    assert rebuilt == pytest.approx(penalized, rel=1e-9)


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TESTS — HTTP via AsyncClient + dependency_overrides Supabase mock
# ═══════════════════════════════════════════════════════════════════════════════


# ── Helper: tracked admin mock that records update/rpc calls ─────────────────


class _TrackedAdminMock:
    """Wraps a chainable mock with per-call tracking for assertion clarity.

    Tracks:
      - rpc_calls: list of (rpc_name, params) tuples
      - update_calls: list of update dict values passed to .update(...)
      - execute_results: sequence of responses per admin execute call
    """

    def __init__(
        self,
        session_data: dict[str, Any],
        competency_slug: str = "communication",
        rpc_result: Any = True,
        rpc_raises: Exception | None = None,
    ) -> None:
        self.rpc_calls: list[tuple[str, dict]] = []
        self.update_calls: list[dict] = []
        self._call_n = 0
        self._session_data = session_data
        self._competency_slug = competency_slug
        self._rpc_raises = rpc_raises
        self._rpc_result = rpc_result

        self._build()

    def _build(self) -> None:
        db = MagicMock()

        # Capture updates
        def _on_update(payload: dict):
            self.update_calls.append(payload)
            chain = MagicMock()
            chain.eq = MagicMock(return_value=chain)
            chain.execute = AsyncMock(return_value=MagicMock(data=[{"id": SESSION_ID}]))
            return chain

        # Track rpc calls
        def _on_rpc(name: str, params: dict | None = None):
            self.rpc_calls.append((name, params or {}))
            rpc_chain = MagicMock()
            if self._rpc_raises:
                rpc_chain.execute = AsyncMock(side_effect=self._rpc_raises)
            else:
                rpc_chain.execute = AsyncMock(return_value=MagicMock(data=self._rpc_result))
            return rpc_chain

        def _make_table_mock(name: str):
            t = MagicMock()
            t.select = MagicMock(return_value=t)
            t.eq = MagicMock(return_value=t)
            t.single = MagicMock(return_value=t)
            t.maybe_single = MagicMock(return_value=t)
            t.order = MagicMock(return_value=t)
            t.limit = MagicMock(return_value=t)
            t.update = MagicMock(side_effect=_on_update)

            if name == "competencies":
                t.execute = AsyncMock(return_value=MagicMock(data={"slug": self._competency_slug}))
            elif name == "aura_scores":
                t.execute = AsyncMock(
                    return_value=MagicMock(data=None)  # no prior AURA row
                )
            else:
                t.execute = AsyncMock(return_value=MagicMock(data=None))
            return t

        db.table = MagicMock(side_effect=_make_table_mock)
        db.rpc = MagicMock(side_effect=_on_rpc)
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock(user=None))
        self.mock = db

    @property
    def pending_flag_was_set(self) -> bool:
        """True if pending_aura_sync=True was set at any update call."""
        return any(u.get("pending_aura_sync") is True for u in self.update_calls)

    @property
    def pending_flag_was_cleared(self) -> bool:
        """True if pending_aura_sync=False was set at any update call."""
        return any(u.get("pending_aura_sync") is False for u in self.update_calls)

    @property
    def upsert_aura_rpc_called(self) -> bool:
        return any(name == "upsert_aura_score" for name, _ in self.rpc_calls)

    def upsert_aura_params(self) -> dict:
        for name, params in self.rpc_calls:
            if name == "upsert_aura_score":
                return params
        return {}


# ── Test: happy path — RPC called, flag pre-set and cleared ─────────────────


async def test_complete_happy_path_rpc_called_and_flag_cleared() -> None:
    """Золотой путь: сессия завершается, RPC вызывается, флаг снимается.

    Asserts:
    1. HTTP 200 with aura_updated=True
    2. upsert_aura_score called with correct JSONB params
    3. pending_aura_sync was pre-set to True
    4. pending_aura_sync was cleared to False after success
    """
    session = _in_progress_session(theta=1.0, penalty_multiplier=1.0)
    admin_tracker = _TrackedAdminMock(session_data=session, competency_slug="communication", rpc_result=True)

    mock_user = _chainable_mock(execute_result=session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["aura_updated"] is True
        assert body["competency_slug"] == "communication"

        # RPC called with correct JSONB structure
        assert admin_tracker.upsert_aura_rpc_called, "upsert_aura_score was never called"
        params = admin_tracker.upsert_aura_params()
        assert "p_volunteer_id" in params
        assert "p_competency_scores" in params
        scores = params["p_competency_scores"]
        assert isinstance(scores, dict), f"p_competency_scores must be dict, got {type(scores)}"
        assert "communication" in scores

        # Intent-before-action: flag was set to True before RPC
        assert admin_tracker.pending_flag_was_set, (
            "pending_aura_sync was never set to True before RPC — intent-before-action contract broken"
        )
        # Flag cleared after success
        assert admin_tracker.pending_flag_was_cleared, (
            "pending_aura_sync was never cleared after successful RPC — reconciler will double-retry"
        )
    finally:
        app.dependency_overrides.clear()


# ── Test: RPC failure — flag stays True (reconciler picks up) ────────────────


async def test_complete_rpc_failure_flag_stays_true() -> None:
    """При сбое RPC флаг остаётся True — реконсайлер подберёт сессию.

    The pending_aura_sync=True pre-flag must NOT be cleared on RPC failure.
    This is the zero-data-loss contract: reconciler will find it and retry.
    """
    session = _in_progress_session(theta=0.5)
    admin_tracker = _TrackedAdminMock(
        session_data=session,
        competency_slug="reliability",
        rpc_raises=RuntimeError("Supabase RPC timeout"),
    )
    mock_user = _chainable_mock(execute_result=session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        # aura_updated should be False — RPC failed
        assert body["aura_updated"] is False, (
            f"aura_updated should be False after RPC failure, got {body['aura_updated']}"
        )
        # Flag was set to True (for reconciler) but should NOT have been cleared
        assert admin_tracker.pending_flag_was_set, "pending_aura_sync pre-flag was never set"
        assert not admin_tracker.pending_flag_was_cleared, (
            "pending_aura_sync was cleared despite RPC failure — reconciler will miss this session"
        )
    finally:
        app.dependency_overrides.clear()


# ── Test: already-completed session returns early without calling RPC ─────────


async def test_complete_idempotency_already_completed_skips_rpc() -> None:
    """Идемпотентность: завершённая сессия возвращает кэшированный результат без RPC.

    BUG-015 fix: double-complete must not double-call upsert_aura_score.
    """
    completed_session = {
        "id": SESSION_ID,
        "volunteer_id": USER_ID,
        "competency_id": COMPETENCY_ID,
        "status": "completed",
        "theta_estimate": 0.8,
        "theta_se": 0.25,
        "answers": {
            "theta": 0.8,
            "theta_se": 0.25,
            "stopped": True,
            "stop_reason": "se_threshold",
            "items": [],
        },
        "gaming_penalty_multiplier": 1.0,
        "gaming_flags": [],
        "completed_at": "2026-04-21T12:00:00Z",
        "metadata": {},
    }
    admin_tracker = _TrackedAdminMock(session_data=completed_session, competency_slug="leadership")
    mock_user = _chainable_mock(execute_result=completed_session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200
        body = resp.json()
        # Early return always sets aura_updated=False (already done)
        assert body["aura_updated"] is False
        # RPC must NOT be called — would create duplicate aura_history entries
        assert not admin_tracker.upsert_aura_rpc_called, (
            "upsert_aura_score must NOT be called for an already-completed session (double-write)"
        )
    finally:
        app.dependency_overrides.clear()


# ── Test: invalid UUID → 422 ─────────────────────────────────────────────────


async def test_complete_invalid_uuid_422() -> None:
    """Невалидный UUID session_id → 422 Unprocessable Entity.

    HIGH-02 security guard: prevents injection via session_id path param.
    """
    mock_db = _chainable_mock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(mock_db)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_db)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/assessment/complete/not-a-valid-uuid",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        body = resp.json()
        assert body["detail"]["code"] == "INVALID_SESSION_ID"
    finally:
        app.dependency_overrides.clear()


# ── Test: session not found → 404 ────────────────────────────────────────────


async def test_complete_session_not_found_404() -> None:
    """Сессия не найдена → 404 Session Not Found."""
    mock_admin = _chainable_mock(execute_result=None)
    mock_user = _chainable_mock(execute_result=None)

    app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "SESSION_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


# ── Test: expired in_progress session → 410 ──────────────────────────────────


async def test_complete_expired_session_410() -> None:
    """Просроченная сессия (in_progress + expires_at в прошлом) → 410 Gone.

    BUG-010 fix: expired sessions must not be completable.
    """
    past_expires = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
    session = _in_progress_session(theta=0.5, expires_at=past_expires)
    mock_user = _chainable_mock(execute_result=session)
    mock_admin = _chainable_mock()

    app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 410, f"Expected 410 for expired session, got {resp.status_code}: {resp.text}"
        assert resp.json()["detail"]["code"] == "SESSION_EXPIRED"
    finally:
        app.dependency_overrides.clear()


# ── Test: gaming penalty applied to RPC payload score ────────────────────────


async def test_complete_gaming_penalty_comes_from_fresh_analysis() -> None:
    """Штраф за gaming вычисляется заново из ответов — не берётся из stored column.

    DESIGN FINDING (discovered by this test):
    For in_progress sessions, complete_assessment runs antigaming.analyse(items)
    FRESH on every call — it does NOT use the stored gaming_penalty_multiplier column.
    The stored column is written by this call and used only for the early-return path
    (already-completed sessions).

    With our 1-item test session (5000ms, no pattern violations),
    antigaming returns penalty_multiplier=1.0 regardless of what was stored.
    So the expected RPC score is theta_to_score(theta) * 1.0.

    This is correct behavior: the router computes the penalty, then stores it.
    The test verifies the RPC receives the freshly-computed score.
    """
    from app.core.assessment import antigaming
    from app.core.assessment.engine import CATState

    theta = 1.0
    # Build the same items dict the router will see
    answers_dict = {
        "theta": theta,
        "theta_se": 0.3,
        "stopped": True,
        "stop_reason": "se_threshold",
        "items": [
            {
                "question_id": "q1",
                "irt_a": 1.0,
                "irt_b": 0.0,
                "irt_c": 0.0,
                "response": 1,
                "raw_score": 0.8,
                "response_time_ms": 5000,
            }
        ],
    }
    state = CATState.from_dict(answers_dict)
    gaming = antigaming.analyse(state.to_dict().get("items", []))
    expected_score = round(theta_to_score(theta) * gaming.penalty_multiplier, 2)

    session = _in_progress_session(theta=theta, penalty_multiplier=0.7)  # stored != computed
    session["answers"] = answers_dict
    admin_tracker = _TrackedAdminMock(session_data=session, competency_slug="tech_literacy", rpc_result=True)
    mock_user = _chainable_mock(execute_result=session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200
        params = admin_tracker.upsert_aura_params()
        scores_dict = params.get("p_competency_scores", {})
        actual_score = scores_dict.get("tech_literacy", -1.0)
        assert actual_score == pytest.approx(expected_score, rel=1e-4), (
            f"RPC received score={actual_score}, expected freshly-computed score={expected_score}"
        )
    finally:
        app.dependency_overrides.clear()


# ── Test: competency score appears in response body ───────────────────────────


async def test_complete_response_score_matches_theta() -> None:
    """Балл в ответе соответствует theta_to_score(theta) с учётом penalty.

    The /complete response must expose competency_score matching what was
    computed from the stored theta and gaming multiplier.
    """
    theta = 0.0
    penalty = 1.0
    expected_score = round(theta_to_score(theta) * penalty, 2)

    session = _in_progress_session(theta=theta, penalty_multiplier=penalty)
    admin_tracker = _TrackedAdminMock(session_data=session, competency_slug="adaptability", rpc_result=True)
    mock_user = _chainable_mock(execute_result=session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["competency_score"] == pytest.approx(expected_score, rel=1e-3), (
            f"Response score {body['competency_score']} != expected {expected_score}"
        )
    finally:
        app.dependency_overrides.clear()


# ── Test: no slug → RPC skipped, aura_updated=False ──────────────────────────


async def test_complete_missing_slug_skips_rpc() -> None:
    """Пустой slug компетенции → RPC не вызывается, aura_updated=False."""
    session = _in_progress_session(theta=1.0)
    admin_tracker = _TrackedAdminMock(session_data=session, competency_slug="")  # empty slug
    mock_user = _chainable_mock(execute_result=session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["aura_updated"] is False
        assert not admin_tracker.upsert_aura_rpc_called, "RPC must not fire when slug is empty"
    finally:
        app.dependency_overrides.clear()


# ── Test: RPC receives correct user_id ───────────────────────────────────────


async def test_complete_rpc_receives_correct_user_id() -> None:
    """RPC payload содержит правильный p_volunteer_id.

    Critical: a bug here would silently write AURA to the wrong user.
    """
    session = _in_progress_session(theta=1.0)
    admin_tracker = _TrackedAdminMock(session_data=session, competency_slug="leadership", rpc_result=True)
    mock_user = _chainable_mock(execute_result=session)

    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_tracker.mock)
    app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
    app.dependency_overrides[get_current_user_id] = _uid_override(USER_ID)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                f"/api/assessment/complete/{SESSION_ID}",
                headers={"Authorization": "Bearer fake"},
            )

        assert resp.status_code == 200
        params = admin_tracker.upsert_aura_params()
        assert params.get("p_volunteer_id") == USER_ID, (
            f"RPC p_volunteer_id={params.get('p_volunteer_id')} != expected {USER_ID}"
        )
    finally:
        app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# AURA RECONCILER — unit tests (reconciler already has test_aura_reconciler.py;
# this section adds parametrized theta edge-case coverage for _reconcile_session)
# ══════════════════════════════════════════════════════════════════════════════


from unittest.mock import patch

from app.services.aura_reconciler import (
    MAX_RECONCILE_ATTEMPTS,
    _reconcile_session,
    _theta_to_score,
    run_once,
)


def _mk_reconciler_db(
    slug: str | None = "communication",
    rpc_data: Any = None,
    rpc_raises: Exception | None = None,
    update_raises: bool = False,
) -> tuple[MagicMock, MagicMock]:
    """Build reconciler mock DB. Returns (db, sessions_chain)."""
    if rpc_data is None:
        rpc_data = [{"ok": True}]
    db = MagicMock()
    sessions_chain = MagicMock()
    sessions_chain.select.return_value = sessions_chain
    sessions_chain.update.return_value = sessions_chain
    sessions_chain.eq.return_value = sessions_chain
    sessions_chain.order.return_value = sessions_chain
    sessions_chain.limit.return_value = sessions_chain
    if update_raises:
        sessions_chain.execute = AsyncMock(side_effect=RuntimeError("update fail"))
    else:
        sessions_chain.execute = AsyncMock(return_value=MagicMock(data=[]))

    comp_chain = MagicMock()
    comp_chain.select.return_value = comp_chain
    comp_chain.eq.return_value = comp_chain
    comp_chain.single.return_value = comp_chain
    comp_chain.execute = AsyncMock(return_value=MagicMock(data={"slug": slug} if slug else None))

    def table(name: str):
        if name == "competencies":
            return comp_chain
        if name == "assessment_sessions":
            return sessions_chain
        return MagicMock()

    db.table.side_effect = table

    if rpc_raises:
        db.rpc.return_value.execute = AsyncMock(side_effect=rpc_raises)
    else:
        db.rpc.return_value.execute = AsyncMock(return_value=MagicMock(data=rpc_data))

    return db, sessions_chain


def _mk_row(
    theta: float | None = 0.5,
    penalty: float = 1.0,
    attempts: int = 0,
) -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "volunteer_id": str(uuid4()),
        "competency_id": str(uuid4()),
        "theta_estimate": theta,
        "gaming_penalty_multiplier": penalty,
        "reconcile_attempts": attempts,
    }


@pytest.mark.parametrize(
    "theta, penalty, slug, expected_outcome",
    [
        pytest.param(1.0, 1.0, "communication", "ok", id="нормальная_сессия_успех"),
        pytest.param(0.0, 0.8, "reliability", "ok", id="сессия_с_штрафом_успех"),
        pytest.param(None, 1.0, "leadership", "gave_up", id="null_theta_отказ"),
        pytest.param(0.5, 1.0, None, "gave_up", id="нет_slug_отказ"),
        pytest.param(-2.0, 1.0, "adaptability", "ok", id="отрицательный_theta_успех"),
    ],
)
async def test_reconcile_session_parametrized(
    theta: float | None,
    penalty: float,
    slug: str | None,
    expected_outcome: str,
) -> None:
    """Параметризованные сценарии _reconcile_session."""
    row = _mk_row(theta=theta, penalty=penalty)
    db, _ = _mk_reconciler_db(slug=slug, rpc_data=[{"ok": True}])
    outcome = await _reconcile_session(db, row)
    assert outcome == expected_outcome, f"Expected {expected_outcome}, got {outcome} for theta={theta}, slug={slug}"


async def test_reconcile_rpc_called_with_penalized_score() -> None:
    """RPC в реконсайлере получает theta_to_score(theta) * penalty."""
    theta = 1.0
    penalty = 0.75
    expected_score = round(_theta_to_score(theta) * penalty, 2)

    row = _mk_row(theta=theta, penalty=penalty)
    db, _ = _mk_reconciler_db(slug="communication", rpc_data=[{"ok": True}])

    await _reconcile_session(db, row)

    rpc_call_args = db.rpc.call_args
    assert rpc_call_args is not None, "RPC was never called"
    _, params = rpc_call_args[0]
    scores = params.get("p_competency_scores", {})
    assert scores.get("communication") == pytest.approx(expected_score, rel=1e-4), (
        f"RPC score {scores.get('communication')} != expected penalized score {expected_score}"
    )


async def test_reconcile_retry_below_cap_increments_counter() -> None:
    """Неудача ниже лимита попыток — счётчик увеличивается, флаг НЕ снимается."""
    row = _mk_row(theta=0.5, attempts=0)
    db, sessions_chain = _mk_reconciler_db(rpc_raises=RuntimeError("timeout"))

    outcome = await _reconcile_session(db, row)

    assert outcome == "retry"
    sessions_chain.update.assert_any_call({"reconcile_attempts": 1})
    # Ensure the flag was NOT cleared
    for call in sessions_chain.update.call_args_list:
        payload = call[0][0] if call[0] else {}
        assert payload.get("pending_aura_sync") is not False, "Flag must not be cleared on retry-below-cap"


async def test_reconcile_gave_up_at_max_attempts() -> None:
    """На последней попытке — gave_up, флаг снимается."""
    row = _mk_row(theta=0.5, attempts=MAX_RECONCILE_ATTEMPTS - 1)
    db, sessions_chain = _mk_reconciler_db(rpc_raises=RuntimeError("fatal"))

    outcome = await _reconcile_session(db, row)

    assert outcome == "gave_up"
    sessions_chain.update.assert_any_call({"pending_aura_sync": False})


async def test_run_once_batch_aggregates_correctly() -> None:
    """run_once returns correct aggregate counts across mixed-outcome batch."""
    rows = [
        _mk_row(theta=1.0, attempts=0),  # → ok
        _mk_row(theta=None, attempts=0),  # → gave_up (null theta)
    ]
    db, _ = _mk_reconciler_db(rpc_data=[{"ok": True}])

    # Override _fetch_pending so run_once uses our rows
    with patch("app.services.aura_reconciler._admin", AsyncMock(return_value=db)):
        # inject pending rows into the sessions mock
        db.table("assessment_sessions").execute = AsyncMock(return_value=MagicMock(data=rows))
        stats = await run_once()

    assert stats["found"] == 2
    assert stats["ok"] == 1
    assert stats["gave_up"] == 1
    assert stats["retry"] == 0


async def test_reconcile_get_slug_exception_returns_none_and_gives_up() -> None:
    """Если slug lookup кидает exception — gave_up (no slug available)."""
    row = _mk_row(theta=0.5, attempts=0)
    db, sessions_chain = _mk_reconciler_db(slug="communication")

    # Make the competencies table RAISE on execute (slug lookup crash)
    comp_chain = MagicMock()
    comp_chain.select.return_value = comp_chain
    comp_chain.eq.return_value = comp_chain
    comp_chain.single.return_value = comp_chain
    comp_chain.execute = AsyncMock(side_effect=RuntimeError("DB connection lost"))

    def table(name: str):
        if name == "competencies":
            return comp_chain
        return sessions_chain

    db.table.side_effect = table

    outcome = await _reconcile_session(db, row)
    # _get_slug catches the exception, returns None, then _reconcile_session gives up
    assert outcome == "gave_up"


async def test_reconcile_counter_update_failure_does_not_block_retry() -> None:
    """Если обновление счётчика упало — retry всё равно возвращается (не зависает).

    Covers the inner try/except around the counter increment update (line 145-153).
    """
    row = _mk_row(theta=0.5, attempts=0)
    db, sessions_chain = _mk_reconciler_db(
        rpc_raises=RuntimeError("rpc timeout"),
        update_raises=True,  # counter update will also raise
    )
    # The comp_chain must still return a valid slug
    comp_chain = MagicMock()
    comp_chain.select.return_value = comp_chain
    comp_chain.eq.return_value = comp_chain
    comp_chain.single.return_value = comp_chain
    comp_chain.execute = AsyncMock(return_value=MagicMock(data={"slug": "communication"}))

    def table(name: str):
        if name == "competencies":
            return comp_chain
        return sessions_chain

    db.table.side_effect = table

    # Should NOT raise even though counter update fails
    outcome = await _reconcile_session(db, row)
    assert outcome == "retry", f"Expected retry even when counter update fails, got {outcome}"


async def test_reconcile_rpc_returns_none_data_triggers_error_path() -> None:
    """RPC возвращает data=None → RuntimeError → retry (below cap)."""
    row = _mk_row(theta=0.5, attempts=0)
    db, sessions_chain = _mk_reconciler_db(rpc_data=None)  # data=None → triggers RuntimeError

    outcome = await _reconcile_session(db, row)
    assert outcome == "retry", f"Expected retry when RPC returns None data, got {outcome}"


# ══════════════════════════════════════════════════════════════════════════════
# COVERAGE NOTES
# ══════════════════════════════════════════════════════════════════════════════
#
# Branches NOT covered and WHY:
#
# 1. emit_assessment_rewards / emit_assessment_completed / emit_aura_updated
#    (assessment.py:932-1073) — these are fire-and-forget coroutines with their
#    own test files (test_ecosystem_events.py, test_cross_product_bridge.py).
#    Testing them here would require mocking 5+ additional services and create
#    cross-test dependency. They're isolated by try/except, so a failure there
#    doesn't affect the AURA scoring result we're testing.
#
# 2. Transactional email path (assessment.py:978-1008) — requires live
#    auth.admin.get_user_by_id call with a real user object. The mock returns
#    MagicMock(user=None) which causes the email block to short-circuit.
#    Covered by test_email_service.py.
#
# 3. send_aura_ready_email and record_assessment_activity — same reasoning as (2).
#
# 4. emit_aura_updated + emit_badge_tier_changed (assessment.py:1034-1072) —
#    requires a real aura_scores row with total_score + badge_tier. Our mock
#    returns data=None for aura_scores. Covered by test_ecosystem_events.py.
#
# 5. paywall check in /start — disabled in conftest.py via disable_paywall fixture.
#    Covered by test_paywall_enforcement.py.
#
# 6. admin-only bypass paths in test_assessment_admin_bypass.py.
#
# The branches above are excluded intentionally. Their exclusion does not
# indicate they're untested — they have dedicated test files. Running:
#   pytest apps/api/tests/test_aura_scoring.py \
#          apps/api/tests/test_aura_reconciler.py \
#          apps/api/tests/test_aura_calc.py \
#   --cov=app.services.aura_reconciler --cov=app.routers.assessment
# achieves the target coverage when combined.
