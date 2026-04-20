"""GDPR Article 17 compliance tests — Right to Erasure (DELETE /auth/me).

HTTP-level tests that verify the erasure endpoint satisfies GDPR Art. 17
controller obligations:

1. Authenticated data subject can successfully request and receive erasure.
2. Unauthenticated requests are rejected — identity must be verified first.
3. Erasure is scoped exclusively to the authenticated subject's data (CRIT-02).
4. Audit log fires on every successful erasure for controller accountability.
5. Erasure failures surface a DELETION_FAILED code — no silent false-success.

All tests use the ASGI test transport pattern (ASGITransport + AsyncClient) so
the full middleware, routing, and dependency-injection stack is exercised.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

_FAKE_USER_ID = "aaaabbbb-1111-2222-3333-444455556666"


# ── dependency helpers ────────────────────────────────────────────────────────


def _admin_override(mock_db):
    async def _override():
        yield mock_db

    return _override


def _user_id_override(uid: str):
    async def _override():
        return uid

    return _override


def _user_id_raises_401():
    async def _override():
        raise HTTPException(
            status_code=401,
            detail={"code": "MISSING_TOKEN", "message": "Not authenticated"},
        )

    return _override


# ── fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_admin_db():
    db = MagicMock()
    db.auth = MagicMock()
    db.auth.admin = MagicMock()
    db.auth.admin.delete_user = AsyncMock(return_value=None)
    return db


# ── tests ─────────────────────────────────────────────────────────────────────


class TestArt17DeleteAccount:
    """GDPR Article 17 — Right to Erasure: DELETE /auth/me HTTP-level tests."""

    @pytest.mark.asyncio
    async def test_authenticated_user_can_delete_own_account(self, mock_admin_db):
        """Art. 17 §1: A data subject may request erasure; the system must honour it.

        The endpoint must return 200 with a confirmation message so the client
        can surface unambiguous feedback to the user.
        """
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin_db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.delete(
                "/api/auth/me",
                headers={"Authorization": "Bearer fake-token"},
            )
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert "deleted" in body["message"].lower()
        assert "successfully" in body["message"].lower()

    @pytest.mark.asyncio
    async def test_unauthenticated_request_cannot_trigger_erasure(self, mock_admin_db):
        """Art. 17: The erasure endpoint must be identity-verified.

        Anonymous or unauthenticated callers must receive 401 and the actual
        Supabase admin.delete_user must never be invoked — preventing accidental
        or malicious mass-deletion.
        """
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin_db)
        app.dependency_overrides[get_current_user_id] = _user_id_raises_401()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.delete("/api/auth/me")
        app.dependency_overrides.clear()

        assert resp.status_code == 401
        # Critical gate: deletion backend must never be reached on unauth request.
        mock_admin_db.auth.admin.delete_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_erasure_is_scoped_to_authenticated_subject_only(self, mock_admin_db):
        """Art. 17 + CRIT-02: Erasure must target only the requesting data subject.

        The admin.delete_user call must receive exactly the user_id that was
        resolved from the authenticated session — not a caller-supplied value.
        This prevents cross-user deletion via request body tampering.
        """
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin_db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.delete(
                "/api/auth/me",
                headers={"Authorization": "Bearer fake-token"},
            )
        app.dependency_overrides.clear()

        mock_admin_db.auth.admin.delete_user.assert_called_once_with(_FAKE_USER_ID)

    @pytest.mark.asyncio
    async def test_audit_log_fires_on_successful_erasure(self, mock_admin_db):
        """Art. 17 + Art. 5(2) accountability: every erasure must be logged.

        GDPR Art. 5(2) obliges controllers to demonstrate compliance.  An audit
        log entry on each successful deletion supports that obligation.
        """
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin_db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        with patch("app.routers.auth.logger") as mock_logger:
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                await ac.delete(
                    "/api/auth/me",
                    headers={"Authorization": "Bearer fake-token"},
                )
        app.dependency_overrides.clear()

        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert "deleted" in log_message.lower()

    @pytest.mark.asyncio
    async def test_backend_failure_returns_deletion_failed_code(self, mock_admin_db):
        """Art. 17: When erasure cannot complete the controller must report the failure.

        A silent 200 on a failed deletion would give the user false assurance that
        their data was erased.  The endpoint must propagate the error as DELETION_FAILED
        so the client can inform the user and allow re-attempt.
        """
        mock_admin_db.auth.admin.delete_user = AsyncMock(side_effect=Exception("Supabase admin API unavailable"))
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin_db)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.delete(
                "/api/auth/me",
                headers={"Authorization": "Bearer fake-token"},
            )
        app.dependency_overrides.clear()

        assert resp.status_code == 500
        assert resp.json()["detail"]["code"] == "DELETION_FAILED"
