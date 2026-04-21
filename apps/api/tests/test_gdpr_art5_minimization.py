"""GDPR Article 5 compliance tests — Data Minimisation (Art. 5(1)(c)).

Verifies that every API response exposed to data subjects contains only the
minimum personal data necessary for the stated purpose. No leakage of:
  - password hashes or secrets
  - internal admin flags (is_platform_admin)
  - raw user_metadata JSONB from Supabase auth
  - refresh tokens or session internals
  - other users' data

Also covers Art. 6 (lawful basis) at the schema level — registration requires
explicit consent fields; no consent → processing fields default to non-consented
state, not silently assumed.

Tests are unit-level (no DB, no HTTP server) using ASGI transport where needed.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.routers.auth import (
    AuthResponse,
    MeResponse,
    RegisterRequest,
    get_me,
    login,
    register,
)

# ── Shared constants ──────────────────────────────────────────────────────────

_USER_ID = str(uuid.uuid4())
_ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"  # noqa: S105 — fake
_VALID_PW = "TestPass1"  # noqa: S105 — not a real credential
_FAKE_REQUEST = MagicMock()
_FAKE_REQUEST.client.host = "127.0.0.1"
_FAKE_REQUEST.headers = {"user-agent": "test-agent", "authorization": f"Bearer {_ACCESS_TOKEN}"}


def _result(data=None) -> MagicMock:
    r = MagicMock()
    r.data = data
    return r


def _make_db(*execute_returns) -> MagicMock:
    db = MagicMock()
    chain = MagicMock()
    for method in [
        "schema",
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "neq",
        "maybe_single",
        "order",
        "limit",
        "single",
        "upsert",
        "is_",
        "filter",
        "range",
    ]:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain
    if len(execute_returns) == 1:
        chain.execute = AsyncMock(return_value=execute_returns[0])
    else:
        chain.execute = AsyncMock(side_effect=list(execute_returns))
    db.auth = MagicMock()
    db.auth.admin = MagicMock()
    return db


def _make_auth_resp(*, has_session: bool = True) -> MagicMock:
    resp = MagicMock()
    resp.user = MagicMock()
    resp.user.id = _USER_ID
    if has_session:
        resp.session = MagicMock()
        resp.session.access_token = _ACCESS_TOKEN
        resp.session.expires_in = 3600
    else:
        resp.session = None
    return resp


# ══════════════════════════════════════════════════════════════════════════════
# 1. AuthResponse schema — Art. 5(1)(c) minimisation
# ══════════════════════════════════════════════════════════════════════════════


class TestAuthResponseMinimisation:
    """AuthResponse exposes only the 4 fields the client strictly needs."""

    def test_model_fields_are_exactly_four(self):
        """AuthResponse has exactly 4 fields — no hidden extras added over time."""
        fields = set(AuthResponse.model_fields.keys())
        assert fields == {"access_token", "token_type", "expires_in", "user_id"}

    def test_no_refresh_token_field(self):
        """Refresh tokens must not be surfaced in the API response (session leak risk)."""
        assert "refresh_token" not in AuthResponse.model_fields

    def test_no_password_field(self):
        """Passwords must never appear in any outbound response schema."""
        assert "password" not in AuthResponse.model_fields

    def test_no_user_metadata_field(self):
        """raw user_metadata JSONB from Supabase must not be forwarded to clients."""
        assert "user_metadata" not in AuthResponse.model_fields

    def test_token_type_defaults_to_bearer(self):
        """Default token_type is 'bearer' — client can rely on this without extra field."""
        resp = AuthResponse(
            access_token=_ACCESS_TOKEN,
            expires_in=3600,
            user_id=_USER_ID,
        )
        assert resp.token_type == "bearer"


# ══════════════════════════════════════════════════════════════════════════════
# 2. MeResponse schema — minimal profile exposure
# ══════════════════════════════════════════════════════════════════════════════


class TestMeResponseMinimisation:
    """GET /auth/me returns only the minimum fields needed to identify the session."""

    def test_model_has_user_id_and_profile(self):
        """MeResponse exposes user_id + profile dict — no additional internal fields."""
        assert set(MeResponse.model_fields.keys()) == {"user_id", "profile"}

    def test_profile_can_be_none_for_new_users(self):
        """New users with no profile row get profile=None — no fake data injected."""
        resp = MeResponse(user_id=_USER_ID, profile=None)
        assert resp.profile is None
        assert resp.user_id == _USER_ID

    def test_profile_dict_is_untyped_passthrough(self):
        """profile is dict | None — minimisation is enforced at DB query level (select cols)."""
        # The DB query selects: id, username, display_name, avatar_url — 4 columns only.
        # This test verifies the schema accepts that exact shape without adding extras.
        minimal = {
            "id": _USER_ID,
            "username": "alice",
            "display_name": "Alice Test",
            "avatar_url": None,
        }
        resp = MeResponse(user_id=_USER_ID, profile=minimal)
        assert resp.profile == minimal

    @pytest.mark.asyncio
    async def test_get_me_selects_only_minimal_columns(self):
        """get_me queries exactly: id, username, display_name, avatar_url — no admin flags."""
        db = _make_db(_result(data={"id": _USER_ID, "username": "alice", "display_name": "Alice", "avatar_url": None}))

        await get_me(request=_FAKE_REQUEST, user_id=_USER_ID, db=db)

        # Verify the select call was called with the minimal column list
        select_call = db.table().select
        select_call.assert_called_once_with("id, username, display_name, avatar_url")

    @pytest.mark.asyncio
    async def test_get_me_does_not_select_is_platform_admin(self):
        """is_platform_admin must never be returned to the requesting user (privilege leak)."""
        db = _make_db(_result(data={"id": _USER_ID, "username": "alice", "display_name": "Alice", "avatar_url": None}))

        await get_me(request=_FAKE_REQUEST, user_id=_USER_ID, db=db)

        select_args = db.table().select.call_args[0][0]
        assert "is_platform_admin" not in select_args

    @pytest.mark.asyncio
    async def test_get_me_does_not_select_email(self):
        """Email is auth-layer data — must not be duplicated into the profile API response."""
        db = _make_db(_result(data=None))

        await get_me(request=_FAKE_REQUEST, user_id=_USER_ID, db=db)

        select_args = db.table().select.call_args[0][0]
        assert "email" not in select_args


# ══════════════════════════════════════════════════════════════════════════════
# 3. RegisterRequest consent fields — Art. 6 lawful basis
# ══════════════════════════════════════════════════════════════════════════════


class TestRegisterRequestLawfulBasis:
    """Art. 6: personal data processing must have a lawful basis — here, explicit consent."""

    def test_age_confirmed_defaults_to_false(self):
        """age_confirmed defaults False — no implicit consent on behalf of data subject."""
        r = RegisterRequest(email="a@b.com", password=_VALID_PW, username="alice")
        assert r.age_confirmed is False

    def test_terms_version_defaults_to_none_when_omitted(self):
        """terms_version defaults None when client omits it — server sets it on registration."""
        r = RegisterRequest(email="a@b.com", password=_VALID_PW, username="alice")
        assert r.terms_version is None

    def test_terms_accepted_at_defaults_to_none_when_omitted(self):
        """terms_accepted_at defaults None — server injects UTC timestamp at processing time."""
        r = RegisterRequest(email="a@b.com", password=_VALID_PW, username="alice")
        assert r.terms_accepted_at is None

    def test_consent_can_be_given_explicitly(self):
        """Data subject can provide all consent fields explicitly — round-trip preserved."""
        r = RegisterRequest(
            email="a@b.com",
            password=_VALID_PW,
            username="alice",
            age_confirmed=True,
            terms_version="2.0",
            terms_accepted_at="2026-04-20T14:00:00+00:00",
        )
        assert r.age_confirmed is True
        assert r.terms_version == "2.0"
        assert r.terms_accepted_at == "2026-04-20T14:00:00+00:00"

    @pytest.mark.asyncio
    async def test_register_stores_consent_meta_in_sign_up_user_data(self):
        """Art. 6: consent metadata forwarded to auth layer so it is stored at the user level."""
        db_anon = _make_db(_result(data=None))
        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(return_value=_make_auth_resp())

        db_admin = _make_db(_result(data=[{"id": str(uuid.uuid4())}]))

        payload = RegisterRequest(
            email="consent@example.com",
            password=_VALID_PW,
            username="consentuser",
            age_confirmed=True,
            terms_version="1.0",
        )

        with patch("app.routers.auth.limiter") as mock_limiter:
            mock_limiter.limit.return_value = lambda f: f
            await register(
                request=_FAKE_REQUEST,
                payload=payload,
                db=db_anon,
                db_admin=db_admin,
            )

        sign_up_call = db_anon.auth.sign_up.call_args[0][0]
        user_data = sign_up_call["options"]["data"]
        assert user_data["age_confirmed"] is True
        assert user_data["terms_version"] == "1.0"
        assert "terms_accepted_at" in user_data  # server injects if omitted

    @pytest.mark.asyncio
    async def test_register_response_excludes_password(self):
        """Registration response must never echo the password back (even hashed)."""
        db_anon = _make_db(_result(data=None))
        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(return_value=_make_auth_resp())

        db_admin = _make_db(_result(data=None))

        payload = RegisterRequest(
            email="user@example.com",
            password=_VALID_PW,
            username="newuser",
            age_confirmed=True,
        )

        with patch("app.routers.auth.limiter") as mock_limiter:
            mock_limiter.limit.return_value = lambda f: f
            resp = await register(
                request=_FAKE_REQUEST,
                payload=payload,
                db=db_anon,
                db_admin=db_admin,
            )

        resp_dict = resp.model_dump()
        assert "password" not in resp_dict
        assert "hash" not in str(resp_dict).lower()

    @pytest.mark.asyncio
    async def test_login_response_excludes_password_and_metadata(self):
        """Login response is AuthResponse — same minimisation guarantee as registration."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.sign_in_with_password = AsyncMock(return_value=_make_auth_resp())

        payload_obj = MagicMock()
        payload_obj.email = "user@example.com"
        payload_obj.password = _VALID_PW

        with patch("app.routers.auth.limiter") as mock_limiter:
            mock_limiter.limit.return_value = lambda f: f
            resp = await login(request=_FAKE_REQUEST, payload=payload_obj, db=db)

        resp_dict = resp.model_dump()
        assert "password" not in resp_dict
        assert "user_metadata" not in resp_dict
        assert "refresh_token" not in resp_dict
        # Only the four expected keys
        assert set(resp_dict.keys()) == {"access_token", "token_type", "expires_in", "user_id"}
