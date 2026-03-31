"""Tests for /api/verify/{token} endpoints.

Covers:
  GET  /api/verify/{token} — validate token, return volunteer + competency info
    1. Valid token → 200 with volunteer info
    2. Token not found → 404 TOKEN_INVALID
    3. Token already used → 409 TOKEN_ALREADY_USED
    4. Token expired → 410 TOKEN_EXPIRED

  POST /api/verify/{token} — submit rating, mark token used, trigger AURA update
    5. Valid submission → 201, token marked used
    6. Expired token → 410 TOKEN_EXPIRED
    7. Concurrent submission (TOCTOU guard) → 409 TOKEN_ALREADY_USED
    8. Rating out of range → 422
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.deps import get_supabase_admin
from app.middleware.rate_limit import limiter

VALID_TOKEN = "valid-token-abc123"
VOLUNTEER_ID = "11111111-0000-0000-0000-000000000001"
COMPETENCY_ID = "communication"

FUTURE_EXPIRY = (datetime.now(tz=UTC) + timedelta(days=5)).isoformat()
PAST_EXPIRY = (datetime.now(tz=UTC) - timedelta(days=1)).isoformat()

TOKEN_ROW_VALID = {
    "id": "token-row-uuid",
    "token_used": False,
    "token_expires_at": FUTURE_EXPIRY,
    "competency_id": COMPETENCY_ID,
    "verifier_name": "Dr. Expert",
    "verifier_org": "Research Institute",
    "volunteer_id": VOLUNTEER_ID,
    "profiles": {
        "display_name": "Alice Volunteer",
        "username": "alice",
        "avatar_url": None,
    },
}

TOKEN_ROW_USED = {**TOKEN_ROW_VALID, "token_used": True}
TOKEN_ROW_EXPIRED = {**TOKEN_ROW_VALID, "token_expires_at": PAST_EXPIRY}


# ── Dependency helpers ────────────────────────────────────────────────────────

def _admin_override(db):
    async def _dep():
        yield db
    return _dep


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset in-memory rate limiter state before each test."""
    limiter._storage.reset()
    yield
    limiter._storage.reset()


# ── Mock DB factory ───────────────────────────────────────────────────────────

def _make_token_lookup_mock(token_row: dict | None) -> MagicMock:
    """Mock for the expert_verifications table with JOIN result."""
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.single.return_value = t

    if token_row is None:
        t.execute = AsyncMock(return_value=MagicMock(data=None))
    else:
        t.execute = AsyncMock(return_value=MagicMock(data=token_row))

    return t


def _build_submit_mock_db(
    token_row: dict | None = None,
    toctou_race: bool = False,
):
    """Non-circular mock for POST /api/verify/{token}.

    DB calls:
      1. expert_verifications.select (with JOIN) — token validation
      2. expert_verifications.update — mark token used
      3. aura_scores.select — current AURA scores (inside _update_aura_after_verification)
      4. db.rpc("upsert_aura_score", ...) — AURA update
    """
    if token_row is None:
        token_row = TOKEN_ROW_VALID

    call_counts: dict[str, int] = {}

    def make_table_mock(table_name: str) -> MagicMock:
        t = MagicMock()
        call_counts.setdefault(table_name, 0)

        if table_name == "expert_verifications":
            async def _ev_execute(*_a, **_kw):
                n = call_counts["expert_verifications"]
                call_counts["expert_verifications"] += 1
                if n == 0:
                    # Token lookup
                    return MagicMock(data=token_row)
                else:
                    # Update token_used
                    if toctou_race:
                        return MagicMock(data=[])  # empty = race condition
                    return MagicMock(data=[{**token_row, "token_used": True}])

            t.select.return_value = t
            t.update.return_value = t
            t.eq.return_value = t
            t.single.return_value = t
            t.execute = AsyncMock(side_effect=_ev_execute)

        elif table_name == "aura_scores":
            t.select.return_value = t
            t.eq.return_value = t
            t.single.return_value = t
            t.execute = AsyncMock(return_value=MagicMock(
                data={"competency_scores": {COMPETENCY_ID: 70.0}}
            ))

        else:
            t.execute = AsyncMock(return_value=MagicMock(data=None))

        return t

    db = MagicMock()
    db.table = MagicMock(side_effect=make_table_mock)

    # Mock db.rpc() for upsert_aura_score
    rpc_mock = MagicMock()
    rpc_mock.execute = AsyncMock(return_value=MagicMock(data=[{"ok": True}]))
    db.rpc = MagicMock(return_value=rpc_mock)

    return db


# ── GET /api/verify/{token} ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_verification_valid_token():
    """Valid unused token → 200 with volunteer and competency info."""
    db = MagicMock()
    verif_mock = _make_token_lookup_mock(TOKEN_ROW_VALID)
    db.table = MagicMock(return_value=verif_mock)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/verify/{VALID_TOKEN}")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["volunteer_display_name"] == "Alice Volunteer"
    assert body["volunteer_username"] == "alice"
    assert body["competency_id"] == COMPETENCY_ID
    assert body["verifier_name"] == "Dr. Expert"


@pytest.mark.asyncio
async def test_get_verification_token_not_found():
    """Unknown token → 404 TOKEN_INVALID."""
    db = MagicMock()
    verif_mock = _make_token_lookup_mock(None)
    db.table = MagicMock(return_value=verif_mock)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/verify/nonexistent-token")

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "TOKEN_INVALID"


@pytest.mark.asyncio
async def test_get_verification_token_already_used():
    """Token that was already used → 409 TOKEN_ALREADY_USED."""
    db = MagicMock()
    verif_mock = _make_token_lookup_mock(TOKEN_ROW_USED)
    db.table = MagicMock(return_value=verif_mock)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/verify/{VALID_TOKEN}")

    app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "TOKEN_ALREADY_USED"


@pytest.mark.asyncio
async def test_get_verification_token_expired():
    """Expired token (past token_expires_at) → 410 TOKEN_EXPIRED."""
    db = MagicMock()
    verif_mock = _make_token_lookup_mock(TOKEN_ROW_EXPIRED)
    db.table = MagicMock(return_value=verif_mock)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(f"/api/verify/{VALID_TOKEN}")

    app.dependency_overrides.clear()

    assert resp.status_code == 410
    assert resp.json()["detail"]["code"] == "TOKEN_EXPIRED"


# ── POST /api/verify/{token} ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_verification_success():
    """Valid rating submission → 201, token marked used, AURA blend triggered."""
    db = _build_submit_mock_db()

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/verify/{VALID_TOKEN}",
            json={"rating": 4, "comment": "Solid performance."},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "verified"
    assert body["rating"] == 4
    assert body["competency_id"] == COMPETENCY_ID
    assert body["volunteer_display_name"] == "Alice Volunteer"
    # AURA rpc must have been called
    # Blend formula: 70.0 * 0.6 + (4/5 * 100) * 0.4 = 42.0 + 32.0 = 74.0
    db.rpc.assert_called_once_with(
        "upsert_aura_score",
        {
            "p_volunteer_id": VOLUNTEER_ID,
            "p_competency_scores": {"communication": 74.0},
        },
    )


@pytest.mark.asyncio
async def test_submit_verification_expired_token():
    """Expired token on submit → 410 TOKEN_EXPIRED."""
    db = _build_submit_mock_db(token_row=TOKEN_ROW_EXPIRED)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/verify/{VALID_TOKEN}",
            json={"rating": 3},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 410
    assert resp.json()["detail"]["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_submit_verification_toctou_race():
    """TOCTOU: update returns empty (another request won) → 409."""
    db = _build_submit_mock_db(toctou_race=True)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/verify/{VALID_TOKEN}",
            json={"rating": 5},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "TOKEN_ALREADY_USED"


@pytest.mark.asyncio
async def test_submit_verification_rating_out_of_range():
    """Rating > 5 → 422 validation error.
    Note: FastAPI resolves dependencies before body validation,
    so get_supabase_admin must be overridden even for schema rejection tests.
    """
    db = MagicMock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/verify/{VALID_TOKEN}",
            json={"rating": 6},  # max is 5
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_submit_verification_rating_zero():
    """Rating = 0 → 422 validation error (min is 1)."""
    db = MagicMock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/verify/{VALID_TOKEN}",
            json={"rating": 0},
        )

    app.dependency_overrides.clear()
    assert resp.status_code == 422
