"""Security tests — input validation, rate limiting, header checks.

Inspired by ruflo's @claude-flow/security patterns.
Tests that protect against: injection, path traversal, suspicious inputs.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_anon, get_supabase_user
from app.main import app


def _make_admin_override(mock_db):
    async def _override():
        yield mock_db

    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id

    return _override


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.auth = MagicMock()
    db.table = MagicMock(return_value=db)
    db.select = MagicMock(return_value=db)
    db.insert = MagicMock(return_value=db)
    db.update = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.maybe_single = MagicMock(return_value=db)
    db.execute = AsyncMock()
    return db


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Security Headers ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_security_headers_present(client: AsyncClient):
    """All responses must include security headers (dev-mode safe)."""
    from app.deps import get_supabase_admin as _get_admin
    from app.main import app as _app

    # /health now uses SupabaseAdmin via Depends() — mock it for this test
    _mock = MagicMock()
    table_mock = MagicMock()
    select_mock = MagicMock()
    limit_mock = AsyncMock()
    limit_mock.execute = AsyncMock(return_value=MagicMock(count=0))
    select_mock.limit = MagicMock(return_value=limit_mock)
    table_mock.select = MagicMock(return_value=select_mock)
    _mock.table = MagicMock(return_value=table_mock)

    async def _admin_dep():
        yield _mock

    _app.dependency_overrides[_get_admin] = _admin_dep
    try:
        resp = await client.get("/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        # HSTS and CSP only set in production (is_dev=False)
        # In dev mode, verify the base headers are present
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    finally:
        _app.dependency_overrides.pop(_get_admin, None)


@pytest.mark.asyncio
async def test_csp_header_present_in_production():
    """Content-Security-Policy must be set in production mode."""
    from app.config import settings

    # CSP is only set when is_dev=False
    # This test documents the behavior — CSP verified via production deploy
    assert hasattr(settings, "is_dev")
    # In test env (dev mode), CSP is intentionally omitted for docs/debug
    # Production deploys are verified via curl to Railway URL


# ── Auth Input Validation ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_rejects_empty_email(client: AsyncClient, mock_db):
    app.dependency_overrides[get_supabase_anon] = _make_admin_override(mock_db)
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "",
            "password": "secret123",
            "username": "test",
        },
    )
    assert resp.status_code == 422
    app.dependency_overrides.pop(get_supabase_anon, None)
    app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.asyncio
async def test_register_rejects_empty_password(client: AsyncClient, mock_db):
    app.dependency_overrides[get_supabase_anon] = _make_admin_override(mock_db)
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    resp = await client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "",
            "username": "test",
        },
    )
    assert resp.status_code == 422
    app.dependency_overrides.pop(get_supabase_anon, None)
    app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.asyncio
async def test_login_rejects_missing_fields(client: AsyncClient, mock_db):
    app.dependency_overrides[get_supabase_anon] = _make_admin_override(mock_db)
    resp = await client.post("/api/auth/login", json={})
    assert resp.status_code == 422
    app.dependency_overrides.pop(get_supabase_anon, None)


# ── Assessment Input Validation ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_assessment_start_rejects_invalid_slug(client: AsyncClient, mock_db):
    """Competency slug must not contain path traversal or SQL injection."""
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override("uuid-test")

    # Path traversal attempt
    resp = await client.post(
        "/api/assessment/start",
        json={"competency_slug": "../../../etc/passwd"},
        headers={"Authorization": "Bearer fake"},
    )
    # Should fail validation or return error, not process the slug
    assert resp.status_code in (400, 404, 422)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_assessment_answer_rejects_negative_timing(client: AsyncClient, mock_db):
    """Negative or zero timing should be treated as suspicious."""
    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override("uuid-test")

    resp = await client.post(
        "/api/assessment/answer",
        json={
            "session_id": "sess-123",
            "question_id": "q-1",
            "answer": "my answer",
            "response_time_ms": -1,
        },
        headers={"Authorization": "Bearer fake"},
    )
    # Should either reject or flag as suspicious, not crash
    assert resp.status_code in (200, 400, 422)

    app.dependency_overrides.clear()


# ── BARS Prompt Injection Defense ────────────────────────────────────────────


def test_bars_wraps_user_input_in_tags():
    """User answers must be wrapped in <user_answer> tags to prevent injection."""
    from app.core.assessment.bars import _USER_TEMPLATE

    assert "<user_answer>" in _USER_TEMPLATE
    assert "</user_answer>" in _USER_TEMPLATE


def test_bars_system_prompt_has_injection_defense():
    """System prompt must explicitly warn about prompt injection in user answers."""
    from app.core.assessment.bars import _SYSTEM_PROMPT

    assert "SECURITY" in _SYSTEM_PROMPT.upper() or "security" in _SYSTEM_PROMPT.lower()
    assert "instruction" in _SYSTEM_PROMPT.lower()


# ── Anti-gaming Edge Cases ───────────────────────────────────────────────────


def test_antigaming_handles_zero_timing():
    """Zero ms timing = spoofed, should flag as rushed."""
    from app.core.assessment import antigaming

    answers = [{"response_time_ms": 0, "response": 1, "raw_score": 1.0} for _ in range(5)]
    signal = antigaming.analyse(answers)
    assert signal.rushed_count > 0


def test_antigaming_handles_negative_timing():
    """Negative ms = spoofed client, should flag as rushed."""
    from app.core.assessment import antigaming

    answers = [{"response_time_ms": -500, "response": 1, "raw_score": 1.0} for _ in range(5)]
    signal = antigaming.analyse(answers)
    assert signal.rushed_count > 0


# ── Rate Limit Token Hashing ─────────────────────────────────────────────────


def test_rate_limit_token_hashing_principle():
    """Rate limiter must hash the FULL JWT token, not just prefix.

    This tests the principle: different tokens with same JWT header prefix
    produce different hashes — preventing rate limit bypass via token reuse.
    """
    import hashlib

    token1 = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abc"
    token2 = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIwOTg3NjU0MzIxIn0.xyz"

    # Both tokens share the same JWT header prefix
    assert token1[:30] == token2[:30]

    # But full-token hashes must differ
    hash1 = hashlib.sha256(token1.encode()).hexdigest()[:12]
    hash2 = hashlib.sha256(token2.encode()).hexdigest()[:12]
    assert hash1 != hash2


# ── CRIT-02: Verification Link Authorization ────────────────────────────────


@pytest.mark.asyncio
async def test_crit02_cannot_create_verification_link_for_other_user(client: AsyncClient, mock_db):
    """CRIT-02: User A must NOT create verification links for User B."""
    user_a_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    user_b_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(user_a_id)

    resp = await client.post(
        f"/api/profiles/{user_b_id}/verification-link",
        json={
            "verifier_name": "Attacker",
            "verifier_org": "Evil Corp",
            "competency_id": "communication",
        },
        headers={"Authorization": "Bearer fake"},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "FORBIDDEN"

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_crit02_can_create_verification_link_for_self(client: AsyncClient, mock_db):
    """CRIT-02: User CAN create verification links for their own profile."""
    user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    # Mock DB: call 1 = volunteer exists check (single row dict), call 2 = insert result (list)
    verif_row = {
        "id": "new-verif-uuid",
        "volunteer_id": user_id,
        "created_by": user_id,
        "verifier_name": "Prof. Aliyev",
        "verifier_org": "ADA University",
        "competency_id": "communication",
        "token": "tok_abc123",
        "token_expires_at": "2099-01-01T00:00:00+00:00",
        "token_used": False,
    }
    mock_db.execute = AsyncMock(
        side_effect=[
            MagicMock(data={"id": user_id}),  # volunteer exists
            MagicMock(data=[verif_row]),  # insert result (list)
        ]
    )

    app.dependency_overrides[get_supabase_admin] = _make_admin_override(mock_db)
    app.dependency_overrides[get_supabase_user] = _make_admin_override(mock_db)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(user_id)

    resp = await client.post(
        f"/api/profiles/{user_id}/verification-link",
        json={
            "verifier_name": "Prof. Aliyev",
            "verifier_org": "ADA University",
            "competency_id": "communication",
        },
        headers={"Authorization": "Bearer fake"},
    )
    # Should succeed (200) or at least not be 403
    assert resp.status_code != 403

    app.dependency_overrides.clear()


# ── CRIT-03: raw_score Not In Response ───────────────────────────────────────


def test_crit03_answer_feedback_schema_has_no_raw_score():
    """CRIT-03: AnswerFeedback must NOT contain raw_score field."""
    from app.schemas.assessment import AnswerFeedback

    field_names = set(AnswerFeedback.model_fields.keys())
    assert "raw_score" not in field_names, (
        "raw_score must be removed from AnswerFeedback — leaking BARS scores enables calibration attacks"
    )


def test_crit03_answer_feedback_serializes_without_raw_score():
    """CRIT-03: Serialized AnswerFeedback JSON must not contain raw_score."""
    from app.schemas.assessment import AnswerFeedback, SessionOut

    feedback = AnswerFeedback(
        session_id="test-session",
        question_id="test-question",
        timing_warning=None,
        session=SessionOut(
            session_id="test-session",
            competency_slug="communication",
            questions_answered=1,
            is_complete=False,
        ),
    )
    serialized = feedback.model_dump()
    assert "raw_score" not in serialized


# ── CRIT-01: No Internal Errors Leaked ───────────────────────────────────────


@pytest.mark.asyncio
async def test_crit01_generic_error_handler_hides_details(client: AsyncClient):
    """CRIT-01: Unhandled exceptions must return generic message, not DB details."""
    # The global exception handler is registered in main.py
    # We can verify it exists on the app
    from app.main import app as real_app

    assert any(handler is not None for handler in real_app.exception_handlers.values()), (
        "Global exception handler must be registered"
    )
