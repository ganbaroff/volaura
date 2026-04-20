"""GDPR Article 15 + Article 16 compliance tests.

Art. 15 — Right of Access: data subjects must be able to read all personal data
  the controller holds about them.  Tests verify the access endpoints (GET /auth/me,
  GET /profiles/me) are authentication-gated, scope to the requesting subject, and
  return identity fields required by Art. 15(1).

Art. 16 — Right to Rectification: data subjects must be able to correct inaccurate
  or incomplete personal data.  Tests verify the profile update endpoint (PUT
  /profiles/me) is authentication-gated, scoped to the subject, rejects empty
  updates (no spurious mutations), and emits an audit log on success.

All tests use the ASGI test transport pattern so the full middleware, routing, and
dependency-injection stack is exercised.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

_FAKE_USER_ID = "ccccdddd-aaaa-bbbb-cccc-ddddeeee1111"


# ── dependency helpers ────────────────────────────────────────────────────────


def _admin_override(mock_db):
    async def _override():
        yield mock_db

    return _override


def _user_override(mock_db):
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


# ── shared profile row ────────────────────────────────────────────────────────

_PROFILE_ROW = {
    "id": _FAKE_USER_ID,
    "username": "test_subject",
    "display_name": "Test Subject",
    "avatar_url": None,
    "bio": "Short bio",
    "location": "Baku",
    "languages": ["az", "en"],
    "social_links": {},
    "is_public": True,
    "visible_to_orgs": False,
    "account_type": "professional",
    "org_type": None,
    "badge_issued_at": None,
    "badge_open_badges_url": None,
    "created_at": "2026-04-01T00:00:00+00:00",
    "updated_at": "2026-04-20T00:00:00+00:00",
    "age_confirmed": True,
    "terms_version": "1.0",
    "terms_accepted_at": "2026-04-01T00:00:00+00:00",
    "registration_number": None,
    "registration_tier": None,
    "subscription_status": "trial",
    "trial_ends_at": None,
    "energy_level": "full",
    "referral_code": None,
    "utm_source": None,
    "utm_campaign": None,
}


def _chain_that_returns(data):
    """Build a chainable async mock that ends in .execute() returning data."""
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.update.return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute = AsyncMock(return_value=MagicMock(data=data))
    return chain


# ═══════════════════════════════════════════════════════════════════════════════
# GDPR Article 15 — Right of Access
# ═══════════════════════════════════════════════════════════════════════════════


class TestArt15AccessAuthMe:
    """Art. 15 via GET /auth/me — lightweight identity access."""

    @pytest.mark.asyncio
    async def test_authenticated_subject_can_read_own_identity(self):
        """Art. 15 §1: A data subject may obtain confirmation and access to data held.

        GET /auth/me must return 200 with the subject's identity fields when the
        request carries a valid session token.
        """
        mock_admin = MagicMock()
        mock_chain = MagicMock()
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.maybe_single.return_value = mock_chain
        mock_chain.execute = AsyncMock(
            return_value=MagicMock(
                data={
                    "id": _FAKE_USER_ID,
                    "username": "test_subject",
                    "display_name": "Test Subject",
                    "avatar_url": None,
                }
            )
        )
        mock_admin.table.return_value = mock_chain

        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/auth/me", headers={"Authorization": "Bearer fake"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["user_id"] == _FAKE_USER_ID
        assert body["profile"]["id"] == _FAKE_USER_ID

    @pytest.mark.asyncio
    async def test_unauthenticated_request_cannot_access_identity(self):
        """Art. 15: Access requires identity verification.

        Without a valid session the controller must refuse access — 401 — so
        that personal data is not exposed to unauthenticated callers.
        """
        mock_admin = MagicMock()
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_raises_401()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/auth/me")
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_access_is_scoped_to_requesting_subject(self):
        """Art. 15 + CRIT-02: The access query must target only the authenticated subject.

        The DB query must use the user_id from the verified session — not any
        caller-supplied parameter — so that one user cannot read another's data.
        """
        mock_admin = MagicMock()
        mock_chain = MagicMock()
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.maybe_single.return_value = mock_chain
        mock_chain.execute = AsyncMock(return_value=MagicMock(data=None))
        mock_admin.table.return_value = mock_chain

        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            await ac.get("/api/auth/me", headers={"Authorization": "Bearer fake"})
        app.dependency_overrides.clear()

        # Verify the .eq() call used the session-derived user_id, not a caller value.
        mock_chain.eq.assert_called_once_with("id", _FAKE_USER_ID)

    @pytest.mark.asyncio
    async def test_response_exposes_no_password_or_internal_tokens(self):
        """Art. 5(1)(c) data minimisation + Art. 15 access: response must not leak secrets.

        The /auth/me response must not expose password hashes, raw JWTs, or
        internal session tokens.  Only identity fields belong in the DSAR response.
        """
        mock_admin = MagicMock()
        mock_chain = MagicMock()
        mock_chain.select.return_value = mock_chain
        mock_chain.eq.return_value = mock_chain
        mock_chain.maybe_single.return_value = mock_chain
        mock_chain.execute = AsyncMock(
            return_value=MagicMock(
                data={
                    "id": _FAKE_USER_ID,
                    "username": "test_subject",
                    "display_name": "Test Subject",
                    "avatar_url": None,
                }
            )
        )
        mock_admin.table.return_value = mock_chain

        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/auth/me", headers={"Authorization": "Bearer fake"})
        app.dependency_overrides.clear()

        body = resp.json()
        sensitive = {"password", "hashed_password", "refresh_token", "access_token", "secret"}
        assert not sensitive.intersection(body.keys()), (
            f"Response exposes sensitive key(s): {sensitive.intersection(body.keys())}"
        )


class TestArt15AccessProfilesMe:
    """Art. 15 via GET /profiles/me — full profile access including GDPR consent fields."""

    @pytest.mark.asyncio
    async def test_authenticated_subject_reads_full_profile_with_consent_fields(self):
        """Art. 15 §1(b): Response must include processing purposes.

        ProfileResponse exposes age_confirmed, terms_version, terms_accepted_at so the
        DSAR response can demonstrate the legal basis recorded for the subject.
        """
        chain = MagicMock()
        chain.select.return_value = chain
        chain.eq.return_value = chain
        chain.maybe_single.return_value = chain
        chain.execute = AsyncMock(return_value=MagicMock(data=_PROFILE_ROW))

        mock_user = MagicMock()
        mock_user.table.return_value = chain

        app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/profiles/me", headers={"Authorization": "Bearer fake"})
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        # GDPR consent fields must be present for accountability (Art. 5(2))
        assert "age_confirmed" in body
        assert "terms_version" in body
        assert "terms_accepted_at" in body

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_profile(self):
        """Art. 15: Profile data requires authenticated access."""
        mock_user = MagicMock()
        mock_admin = MagicMock()
        app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_raises_401()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/profiles/me")
        app.dependency_overrides.clear()

        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# GDPR Article 16 — Right to Rectification
# ═══════════════════════════════════════════════════════════════════════════════


class TestArt16Rectification:
    """Art. 16 via PUT /profiles/me — data subjects must be able to correct their data."""

    def _make_update_mocks(self, updated_row: dict | None = None):
        """Return (mock_user, mock_admin) ready for a PUT /profiles/me call."""
        row = updated_row or {**_PROFILE_ROW, "display_name": "Updated Name"}

        mock_user = MagicMock()
        mock_user_chain = MagicMock()
        mock_user_chain.update.return_value = mock_user_chain
        mock_user_chain.eq.return_value = mock_user_chain
        mock_user_chain.execute = AsyncMock(return_value=MagicMock(data=[row]))
        mock_user.table.return_value = mock_user_chain

        mock_admin = MagicMock()
        mock_admin_chain = MagicMock()
        mock_admin_chain.select.return_value = mock_admin_chain
        mock_admin_chain.eq.return_value = mock_admin_chain
        mock_admin_chain.maybe_single.return_value = mock_admin_chain
        mock_admin_chain.execute = AsyncMock(return_value=MagicMock(data=None))
        mock_admin.table.return_value = mock_admin_chain

        return mock_user, mock_admin

    @pytest.mark.asyncio
    async def test_authenticated_subject_can_rectify_display_name(self):
        """Art. 16: A data subject may request correction of inaccurate personal data.

        PUT /profiles/me must accept a valid correction payload and return the
        updated profile.  This is the primary path for the right to rectification.
        """
        mock_user, mock_admin = self._make_update_mocks()

        with patch("app.routers.profiles.upsert_volunteer_embedding", new=AsyncMock()):
            app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
            app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
            app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.put(
                    "/api/profiles/me",
                    json={"display_name": "Updated Name"},
                    headers={"Authorization": "Bearer fake"},
                )
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["display_name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_rectify_data(self):
        """Art. 16: Rectification requires identity verification.

        Anonymous callers must receive 401 and the profile update must never
        reach the database.
        """
        mock_user = MagicMock()
        mock_admin = MagicMock()
        app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_raises_401()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.put(
                "/api/profiles/me",
                json={"display_name": "Hacker"},
            )
        app.dependency_overrides.clear()

        assert resp.status_code == 401
        mock_user.table.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_rectification_payload_is_rejected(self):
        """Art. 16 + controller-side validation: spurious empty updates must be refused.

        Accepting an empty PUT as a valid rectification would generate audit noise
        and could mask bugs in client code.  The endpoint must require at least one
        field to differ from the stored value.
        """
        mock_user = MagicMock()
        mock_admin = MagicMock()
        app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
        app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
        app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.put(
                "/api/profiles/me",
                json={},
                headers={"Authorization": "Bearer fake"},
            )
        app.dependency_overrides.clear()

        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "NO_FIELDS"

    @pytest.mark.asyncio
    async def test_rectification_scoped_to_authenticated_subject(self):
        """Art. 16 + CRIT-02: Update must target only the requesting subject's row.

        The UPDATE query must be filtered by the session-derived user_id so that a
        malicious caller cannot overwrite another user's personal data.
        """
        mock_user, mock_admin = self._make_update_mocks()

        with patch("app.routers.profiles.upsert_volunteer_embedding", new=AsyncMock()):
            app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
            app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
            app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                await ac.put(
                    "/api/profiles/me",
                    json={"display_name": "Updated Name"},
                    headers={"Authorization": "Bearer fake"},
                )
            app.dependency_overrides.clear()

        # The .eq() filter must use the session user_id — not a caller-supplied value.
        user_chain = mock_user.table.return_value
        user_chain.eq.assert_called_once_with("id", _FAKE_USER_ID)

    @pytest.mark.asyncio
    async def test_audit_log_emitted_after_successful_rectification(self):
        """Art. 5(2) accountability: every rectification must produce an audit trace.

        The embedding update log serves as the audit event for profile mutations.
        Without it the controller cannot demonstrate when data was corrected and by whom.
        """
        mock_user, mock_admin = self._make_update_mocks()

        with (
            patch("app.routers.profiles.upsert_volunteer_embedding", new=AsyncMock()),
            patch("app.routers.profiles.logger") as mock_logger,
        ):
            app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
            app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
            app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                await ac.put(
                    "/api/profiles/me",
                    json={"display_name": "Updated Name"},
                    headers={"Authorization": "Bearer fake"},
                )
            app.dependency_overrides.clear()

        # Logger.info must have been called — provides the audit trail.
        assert mock_logger.info.called or mock_logger.warning.called, "No audit log emitted after profile rectification"

    @pytest.mark.asyncio
    async def test_rectification_allows_updating_multiple_fields(self):
        """Art. 16: The right to rectify covers all inaccurate or incomplete personal data.

        A single request correcting multiple fields (bio, location, languages) must
        succeed — partial correction is not mandated but multi-field updates must not
        be artificially restricted.
        """
        updated_row = {
            **_PROFILE_ROW,
            "bio": "Corrected bio",
            "location": "Sumgait",
            "languages": ["az"],
        }
        mock_user, mock_admin = self._make_update_mocks(updated_row=updated_row)

        with patch("app.routers.profiles.upsert_volunteer_embedding", new=AsyncMock()):
            app.dependency_overrides[get_supabase_user] = _user_override(mock_user)
            app.dependency_overrides[get_supabase_admin] = _admin_override(mock_admin)
            app.dependency_overrides[get_current_user_id] = _user_id_override(_FAKE_USER_ID)
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.put(
                    "/api/profiles/me",
                    json={"bio": "Corrected bio", "location": "Sumgait", "languages": ["az"]},
                    headers={"Authorization": "Bearer fake"},
                )
            app.dependency_overrides.clear()

        assert resp.status_code == 200
        body = resp.json()
        assert body["bio"] == "Corrected bio"
        assert body["location"] == "Sumgait"
        assert body["languages"] == ["az"]
