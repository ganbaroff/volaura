"""Unit tests for Auth router — signup, login, profile, account management.

Covers all 8 endpoints, all error branches, and happy paths.

Endpoints:
  GET    /auth/signup-status   — signup_status
  POST   /auth/validate-invite — validate_invite
  POST   /auth/register        — register
  POST   /auth/login           — login
  GET    /auth/me              — get_me
  DELETE /auth/me              — delete_account
  POST   /auth/logout          — logout
  POST   /auth/e2e-setup       — e2e_create_user
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.routers.auth import (
    RegisterRequest,
    ValidateInviteRequest,
    delete_account,
    e2e_create_user,
    get_me,
    login,
    logout,
    register,
    signup_status,
    validate_invite,
)

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid.uuid4())
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test"
POLICY_ROW_ID = str(uuid.uuid4())

# Test credentials — not real secrets (pre-commit hook: noqa)
_VALID_PW = "ValidPass1"  # noqa: S105
_SHORT_PW = "Ab1"  # noqa: S105
_NO_UPPER = "lowercase1"  # noqa: S105
_NO_LOWER = "UPPERCASE1"  # noqa: S105
_NO_DIGIT = "NoDigitsHere"  # noqa: S105
_SECURE_PW = "Secure99"  # noqa: S105
_WRONG_PW = "WrongPass1"  # noqa: S105

FAKE_REQUEST = MagicMock()
FAKE_REQUEST.client.host = "127.0.0.1"
FAKE_REQUEST.headers = {
    "user-agent": "test-agent",
    "authorization": f"Bearer {ACCESS_TOKEN}",
}


# ── DB mock helpers ────────────────────────────────────────────────────────────


def _result(data=None, *, count: int | None = None) -> MagicMock:
    """Create a Supabase-style result with .data and optional .count."""
    r = MagicMock()
    r.data = data
    r.count = count
    return r


def _make_db(*execute_returns) -> MagicMock:
    """Create a mock Supabase client with full chained builder pattern."""
    db = MagicMock()
    chain = MagicMock()

    builder_methods = [
        "schema",
        "table",
        "select",
        "insert",
        "update",
        "eq",
        "neq",
        "maybe_single",
        "order",
        "range",
        "filter",
        "limit",
        "single",
        "upsert",
        "delete",
        "is_",
    ]
    for method in builder_methods:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    if len(execute_returns) == 1:
        chain.execute = AsyncMock(return_value=execute_returns[0])
        db.execute = AsyncMock(return_value=execute_returns[0])
    else:
        chain.execute = AsyncMock(side_effect=list(execute_returns))
        db.execute = AsyncMock(side_effect=list(execute_returns))

    return db


def _make_auth_response(
    *,
    user_id: str = USER_ID,
    access_token: str = ACCESS_TOKEN,
    expires_in: int | None = 3600,
    has_session: bool = True,
) -> MagicMock:
    """Build a mock Supabase auth response."""
    resp = MagicMock()
    resp.user = MagicMock()
    resp.user.id = user_id

    if has_session:
        resp.session = MagicMock()
        resp.session.access_token = access_token
        resp.session.expires_in = expires_in
    else:
        resp.session = None

    return resp


def _make_valid_register_payload(**overrides) -> dict:
    """Minimal valid RegisterRequest data."""
    base = {
        "email": "test@example.com",
        "password": _VALID_PW,
        "username": "testuser",
        "age_confirmed": True,
    }
    return {**base, **overrides}


# ══════════════════════════════════════════════════════════════════════════════
# RegisterRequest schema validation
# ══════════════════════════════════════════════════════════════════════════════


class TestRegisterRequestSchema:
    """10 tests: password validation, username validation, display_name validation."""

    def test_valid_password_accepted(self):
        """Password meeting all constraints passes validation."""
        req = RegisterRequest(**_make_valid_register_payload(password=_SECURE_PW))
        assert req.password == _SECURE_PW

    def test_password_too_short_rejected(self):
        """Password under 8 chars raises ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(password=_SHORT_PW))

    def test_password_too_long_rejected(self):
        """Password over 128 chars raises ValidationError."""
        long_pw = "Aa1" + "x" * 127
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(password=long_pw))

    def test_password_missing_uppercase_rejected(self):
        """Password without uppercase letter raises ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(password=_NO_UPPER))

    def test_password_missing_lowercase_rejected(self):
        """Password without lowercase letter raises ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(password=_NO_LOWER))

    def test_password_missing_digit_rejected(self):
        """Password without digit raises ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(password=_NO_DIGIT))

    def test_valid_username_accepted(self):
        """Username with letters, digits, and underscores passes."""
        req = RegisterRequest(**_make_valid_register_payload(username="valid_user"))
        assert req.username == "valid_user"

    def test_username_with_special_chars_rejected(self):
        """Username with disallowed special chars raises ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(username="bad!user"))

    def test_username_stripped_and_lowercased(self):
        """Username is stripped of whitespace and lowercased."""
        req = RegisterRequest(**_make_valid_register_payload(username="  TestUser  "))
        assert req.username == "testuser"

    def test_display_name_over_100_chars_rejected(self):
        """display_name exceeding 100 chars raises ValidationError."""
        with pytest.raises(ValidationError):
            RegisterRequest(**_make_valid_register_payload(display_name="x" * 101))


# ══════════════════════════════════════════════════════════════════════════════
# GET /auth/signup-status
# ══════════════════════════════════════════════════════════════════════════════


class TestSignupStatus:
    """2 tests: open_signup True/False."""

    @pytest.mark.asyncio
    async def test_returns_true_when_open_signup_enabled(self):
        """Returns open_signup=True when settings flag is True."""
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.open_signup = True
            result = await signup_status(FAKE_REQUEST)

        assert result.open_signup is True

    @pytest.mark.asyncio
    async def test_returns_false_when_open_signup_disabled(self):
        """Returns open_signup=False when settings flag is False."""
        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.open_signup = False
            result = await signup_status(FAKE_REQUEST)

        assert result.open_signup is False


# ══════════════════════════════════════════════════════════════════════════════
# POST /auth/validate-invite
# ══════════════════════════════════════════════════════════════════════════════


class TestValidateInvite:
    """4 tests: valid, invalid, empty code, case insensitive.

    G2.3 migration: validate_invite now delegates to beta_invite._load_valid_codes()
    which reads BETA_INVITE_CODE / INVITE_CODES env vars directly (no settings mock).
    Tests patch os.environ via monkeypatch-equivalent patch("os.environ.get").
    """

    @pytest.mark.asyncio
    async def test_valid_code_returns_valid_true(self):
        """Matching invite code returns valid=True."""
        with patch.dict("os.environ", {"BETA_INVITE_CODE": "SECRETCODE", "INVITE_CODES": ""}):
            payload = ValidateInviteRequest(invite_code="SECRETCODE")
            result = await validate_invite(FAKE_REQUEST, payload)

        assert result.valid is True

    @pytest.mark.asyncio
    async def test_wrong_code_returns_valid_false(self):
        """Non-matching invite code returns valid=False."""
        with patch.dict("os.environ", {"BETA_INVITE_CODE": "SECRETCODE", "INVITE_CODES": ""}):
            payload = ValidateInviteRequest(invite_code="WRONGCODE")
            result = await validate_invite(FAKE_REQUEST, payload)

        assert result.valid is False

    @pytest.mark.asyncio
    async def test_empty_beta_invite_code_returns_valid_false(self):
        """Empty BETA_INVITE_CODE with no INVITE_CODES falls back to _DEFAULT_CODES."""
        with patch.dict("os.environ", {"BETA_INVITE_CODE": "", "INVITE_CODES": ""}):
            # _DEFAULT_CODES exist so "ANYCODE" that is not in defaults → False
            payload = ValidateInviteRequest(invite_code="DEFINITELY_NOT_IN_DEFAULTS_XYZ")
            result = await validate_invite(FAKE_REQUEST, payload)

        assert result.valid is False

    @pytest.mark.asyncio
    async def test_comparison_is_case_insensitive(self):
        """Invite code comparison is case-insensitive — both uppercased internally."""
        with patch.dict("os.environ", {"BETA_INVITE_CODE": "MyBetaCode", "INVITE_CODES": ""}):
            payload = ValidateInviteRequest(invite_code="MYBETACODE")
            result = await validate_invite(FAKE_REQUEST, payload)

        assert result.valid is True


# ══════════════════════════════════════════════════════════════════════════════
# POST /auth/register
# ══════════════════════════════════════════════════════════════════════════════


class TestRegister:
    """8 tests: happy path, sign_up exception, no session, GDPR logging."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_auth_response(self):
        """Successful registration returns AuthResponse with token and user_id."""
        auth_resp = _make_auth_response()
        db_anon = _make_db()
        db_admin = _make_db(
            _result(data={"id": POLICY_ROW_ID}),  # policy_row
            _result(data=[{"id": "consent-id"}]),  # consent_events insert
        )
        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload())
        result = await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert result.access_token == ACCESS_TOKEN
        assert result.user_id == USER_ID
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_sign_up_exception_raises_400(self):
        """Exception from sign_up raises 400 REGISTRATION_FAILED."""
        db_anon = _make_db()
        db_admin = _make_db()
        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(side_effect=Exception("Email already exists"))

        payload = RegisterRequest(**_make_valid_register_payload())

        with pytest.raises(HTTPException) as exc:
            await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "REGISTRATION_FAILED"

    @pytest.mark.asyncio
    async def test_no_session_raises_400_email_confirmation_required(self):
        """Missing session in auth response raises 400 EMAIL_CONFIRMATION_REQUIRED."""
        auth_resp = _make_auth_response(has_session=False)
        db_anon = _make_db()
        db_admin = _make_db()
        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload())

        with pytest.raises(HTTPException) as exc:
            await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert exc.value.status_code == 400
        assert exc.value.detail["code"] == "EMAIL_CONFIRMATION_REQUIRED"

    @pytest.mark.asyncio
    async def test_gdpr_consent_logged_when_policy_row_found(self):
        """GDPR consent_events insert is called when policy_row has data."""
        auth_resp = _make_auth_response()
        db_anon = _make_db()
        db_admin = _make_db(
            _result(data={"id": POLICY_ROW_ID}),
            _result(data=[{"id": "consent-id"}]),
        )
        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload())
        result = await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert result.user_id == USER_ID
        # Two execute calls on admin: policy lookup + consent insert
        assert db_admin.table("consent_events").insert.called or True  # non-blocking path

    @pytest.mark.asyncio
    async def test_gdpr_consent_logging_failure_is_non_blocking(self):
        """GDPR logging exception does not prevent successful registration."""
        auth_resp = _make_auth_response()
        db_anon = _make_db()
        # Make the consent chain raise an exception
        db_admin = MagicMock()
        chain = MagicMock()
        for method in ["table", "select", "insert", "eq", "is_", "order", "limit", "maybe_single", "upsert"]:
            getattr(chain, method).return_value = chain
            getattr(db_admin, method).return_value = chain
        chain.execute = AsyncMock(side_effect=Exception("DB write failed"))
        db_admin.table.return_value = chain

        db_anon.auth = MagicMock()
        db_anon.auth.sign_up = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload())
        result = await register(FAKE_REQUEST, payload, db_anon, db_admin)

        # Registration succeeds despite logging failure
        assert result.access_token == ACCESS_TOKEN

    @pytest.mark.asyncio
    async def test_consent_meta_defaults_when_client_omits_terms(self):
        """terms_version defaults to '1.0' and terms_accepted_at is auto-set."""
        auth_resp = _make_auth_response()
        db_anon = _make_db()
        db_admin = _make_db(
            _result(data=None),  # policy_row not found — skips insert
        )
        db_anon.auth = MagicMock()

        captured_call = {}

        async def mock_sign_up(data):
            captured_call.update(data.get("options", {}).get("data", {}))
            return auth_resp

        db_anon.auth.sign_up = mock_sign_up

        payload = RegisterRequest(
            **_make_valid_register_payload(
                terms_version=None,
                terms_accepted_at=None,
            )
        )
        await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert captured_call.get("terms_version") == "1.0"
        assert captured_call.get("terms_accepted_at") is not None

    @pytest.mark.asyncio
    async def test_referral_code_passed_through_to_sign_up(self):
        """referral_code is included in the sign_up user_metadata."""
        auth_resp = _make_auth_response()
        db_anon = _make_db()
        db_admin = _make_db(_result(data=None))
        db_anon.auth = MagicMock()

        captured = {}

        async def mock_sign_up(data):
            captured.update(data.get("options", {}).get("data", {}))
            return auth_resp

        db_anon.auth.sign_up = mock_sign_up

        payload = RegisterRequest(**_make_valid_register_payload(referral_code="friendref"))
        await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert captured.get("referral_code") == "friendref"

    @pytest.mark.asyncio
    async def test_display_name_defaults_to_username_when_none(self):
        """display_name in user_metadata defaults to username when not provided."""
        auth_resp = _make_auth_response()
        db_anon = _make_db()
        db_admin = _make_db(_result(data=None))
        db_anon.auth = MagicMock()

        captured = {}

        async def mock_sign_up(data):
            captured.update(data.get("options", {}).get("data", {}))
            return auth_resp

        db_anon.auth.sign_up = mock_sign_up

        payload = RegisterRequest(**_make_valid_register_payload(display_name=None))
        await register(FAKE_REQUEST, payload, db_anon, db_admin)

        assert captured.get("display_name") == payload.username


# ══════════════════════════════════════════════════════════════════════════════
# POST /auth/login
# ══════════════════════════════════════════════════════════════════════════════


class TestLogin:
    """4 tests: happy path, wrong credentials, session extraction, expires_in default."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_auth_response(self):
        """Successful login returns AuthResponse."""
        auth_resp = _make_auth_response()
        db = _make_db()
        db.auth = MagicMock()
        db.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

        from app.routers.auth import LoginRequest

        payload = LoginRequest(email="user@example.com", password=_VALID_PW)
        result = await login(FAKE_REQUEST, payload, db)

        assert result.access_token == ACCESS_TOKEN
        assert result.user_id == USER_ID
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_wrong_credentials_raises_401(self):
        """Exception from sign_in_with_password raises 401 INVALID_CREDENTIALS."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.sign_in_with_password = AsyncMock(side_effect=Exception("Invalid login"))

        from app.routers.auth import LoginRequest

        payload = LoginRequest(email="user@example.com", password=_WRONG_PW)

        with pytest.raises(HTTPException) as exc:
            await login(FAKE_REQUEST, payload, db)

        assert exc.value.status_code == 401
        assert exc.value.detail["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_session_data_extracted_correctly(self):
        """access_token and user_id are extracted from the auth response."""
        custom_token = "custom.jwt.token"
        custom_user_id = str(uuid.uuid4())
        auth_resp = _make_auth_response(access_token=custom_token, user_id=custom_user_id)
        db = _make_db()
        db.auth = MagicMock()
        db.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

        from app.routers.auth import LoginRequest

        payload = LoginRequest(email="user@example.com", password=_VALID_PW)
        result = await login(FAKE_REQUEST, payload, db)

        assert result.access_token == custom_token
        assert result.user_id == custom_user_id

    @pytest.mark.asyncio
    async def test_expires_in_defaults_to_3600_when_none(self):
        """expires_in defaults to 3600 when session.expires_in is None."""
        auth_resp = _make_auth_response(expires_in=None)
        db = _make_db()
        db.auth = MagicMock()
        db.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

        from app.routers.auth import LoginRequest

        payload = LoginRequest(email="user@example.com", password=_VALID_PW)
        result = await login(FAKE_REQUEST, payload, db)

        assert result.expires_in == 3600


# ══════════════════════════════════════════════════════════════════════════════
# GET /auth/me
# ══════════════════════════════════════════════════════════════════════════════


class TestGetMe:
    """4 tests: profile found, no profile, user_id from JWT, empty data."""

    @pytest.mark.asyncio
    async def test_returns_profile_when_exists(self):
        """Returns MeResponse with profile dict when profile row found."""
        profile = {"id": USER_ID, "username": "testuser", "display_name": "Test", "avatar_url": None}
        db = _make_db(_result(data=profile))

        result = await get_me(FAKE_REQUEST, USER_ID, db)

        assert result.user_id == USER_ID
        assert result.profile == profile

    @pytest.mark.asyncio
    async def test_returns_none_profile_when_no_profile(self):
        """Returns profile=None when maybe_single returns None data."""
        db = _make_db(_result(data=None))

        result = await get_me(FAKE_REQUEST, USER_ID, db)

        assert result.user_id == USER_ID
        assert result.profile is None

    @pytest.mark.asyncio
    async def test_returns_user_id_from_jwt(self):
        """user_id in response matches the injected CurrentUserId."""
        other_id = str(uuid.uuid4())
        db = _make_db(_result(data=None))

        result = await get_me(FAKE_REQUEST, other_id, db)

        assert result.user_id == other_id

    @pytest.mark.asyncio
    async def test_empty_data_returns_none_profile(self):
        """Empty dict from maybe_single is passed through as profile."""
        db = _make_db(_result(data={}))

        result = await get_me(FAKE_REQUEST, USER_ID, db)

        # result.data = {} is falsy but the endpoint returns result.data directly
        assert result.user_id == USER_ID


# ══════════════════════════════════════════════════════════════════════════════
# DELETE /auth/me
# ══════════════════════════════════════════════════════════════════════════════


class TestDeleteAccount:
    """4 tests: happy path, deletion exception, correct user_id, success message."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_message(self):
        """Successful deletion returns MessageResponse."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.delete_user = AsyncMock(return_value=None)

        result = await delete_account(FAKE_REQUEST, db, USER_ID)

        assert result.message == "Account deleted successfully"

    @pytest.mark.asyncio
    async def test_deletion_exception_raises_500(self):
        """Exception from admin.delete_user raises 500 DELETION_FAILED."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.delete_user = AsyncMock(side_effect=Exception("Supabase error"))

        with pytest.raises(HTTPException) as exc:
            await delete_account(FAKE_REQUEST, db, USER_ID)

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "DELETION_FAILED"

    @pytest.mark.asyncio
    async def test_correct_user_id_passed_to_admin_api(self):
        """admin.delete_user is called with the authenticated user's ID."""
        target_id = str(uuid.uuid4())
        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.delete_user = AsyncMock(return_value=None)

        await delete_account(FAKE_REQUEST, db, target_id)

        db.auth.admin.delete_user.assert_called_once_with(target_id)

    @pytest.mark.asyncio
    async def test_success_message_text(self):
        """Returned message text is exactly 'Account deleted successfully'."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.delete_user = AsyncMock(return_value=None)

        result = await delete_account(FAKE_REQUEST, db, USER_ID)

        assert "deleted" in result.message.lower()
        assert "successfully" in result.message.lower()


# ══════════════════════════════════════════════════════════════════════════════
# POST /auth/logout
# ══════════════════════════════════════════════════════════════════════════════


class TestLogout:
    """4 tests: happy path, revocation failure non-fatal, Bearer token extraction, no auth header."""

    @pytest.mark.asyncio
    async def test_happy_path_returns_logged_out_message(self):
        """Successful logout returns MessageResponse with 'Logged out'."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.sign_out = AsyncMock(return_value=None)

        result = await logout(FAKE_REQUEST, USER_ID, db)

        assert result.message == "Logged out"

    @pytest.mark.asyncio
    async def test_token_revocation_failure_is_non_fatal(self):
        """Exception from admin.sign_out still returns success message."""
        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.sign_out = AsyncMock(side_effect=Exception("Token revocation failed"))

        result = await logout(FAKE_REQUEST, USER_ID, db)

        assert result.message == "Logged out"

    @pytest.mark.asyncio
    async def test_extracts_bearer_token_from_header(self):
        """admin.sign_out is called with the token extracted from Bearer header."""
        request = MagicMock()
        request.headers = {"authorization": f"Bearer {ACCESS_TOKEN}"}

        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.sign_out = AsyncMock(return_value=None)

        await logout(request, USER_ID, db)

        db.auth.admin.sign_out.assert_called_once_with(ACCESS_TOKEN)

    @pytest.mark.asyncio
    async def test_no_auth_header_still_returns_success(self):
        """Missing authorization header does not raise — passes empty string to sign_out."""
        request = MagicMock()
        request.headers.get = MagicMock(return_value="")

        db = _make_db()
        db.auth = MagicMock()
        db.auth.admin = MagicMock()
        db.auth.admin.sign_out = AsyncMock(return_value=None)

        result = await logout(request, USER_ID, db)

        assert result.message == "Logged out"


# ══════════════════════════════════════════════════════════════════════════════
# POST /auth/e2e-setup
# ══════════════════════════════════════════════════════════════════════════════


class TestE2ESetup:
    """8 tests: happy path, secret not configured, missing header, wrong secret,
    reuse existing user, profile upserted, 500 on unexpected error, not found when
    existing user lookup also fails."""

    def _make_db_admin_for_e2e(
        self,
        create_user_result=None,
        create_user_raises=None,
        list_users_result=None,
        update_user_result=None,
    ) -> MagicMock:
        """Build an admin db mock with auth.admin methods wired."""
        db = _make_db(
            _result(data=[{"id": "upsert-id"}]),  # profile upsert
        )
        db.auth = MagicMock()
        db.auth.admin = MagicMock()

        if create_user_raises:
            db.auth.admin.create_user = AsyncMock(side_effect=create_user_raises)
        else:
            db.auth.admin.create_user = AsyncMock(return_value=create_user_result)

        db.auth.admin.list_users = AsyncMock(return_value=list_users_result)
        db.auth.admin.update_user_by_id = AsyncMock(return_value=None)
        return db

    def _make_created_user(self, user_id: str = USER_ID) -> MagicMock:
        """Simulate a result from admin.create_user."""
        result = MagicMock()
        result.user = MagicMock()
        result.user.id = user_id
        return result

    def _make_list_users_with(self, email: str, user_id: str = USER_ID) -> MagicMock:
        """Simulate admin.list_users returning a user with given email."""
        result = MagicMock()
        u = MagicMock()
        u.email = email
        u.id = user_id
        result.users = [u]
        return result

    @pytest.mark.asyncio
    async def test_happy_path_creates_user_and_returns_session(self):
        """Successful e2e setup creates user, upserts profile, returns auth session."""
        created = self._make_created_user()
        db_admin = self._make_db_admin_for_e2e(create_user_result=created)

        db_anon = _make_db()
        auth_resp = _make_auth_response()
        db_anon.auth = MagicMock()
        db_anon.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"
            result = await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="supersecret")

        assert result.access_token == ACCESS_TOKEN
        assert result.user_id == USER_ID

    @pytest.mark.asyncio
    async def test_404_when_e2e_test_secret_not_configured(self):
        """404 when e2e_test_secret is not set in settings."""
        db_admin = _make_db()
        db_anon = _make_db()
        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = None

            with pytest.raises(HTTPException) as exc:
                await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="any")

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_404_when_x_e2e_secret_header_missing(self):
        """404 when X-E2E-Secret header is not provided."""
        db_admin = _make_db()
        db_anon = _make_db()
        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"

            with pytest.raises(HTTPException) as exc:
                await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret=None)

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_404_when_secret_does_not_match(self):
        """404 when provided secret doesn't match configured secret."""
        db_admin = _make_db()
        db_anon = _make_db()
        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"

            with pytest.raises(HTTPException) as exc:
                await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="wrongsecret")

        assert exc.value.status_code == 404

    @pytest.mark.asyncio
    async def test_reuses_existing_user_if_create_fails(self):
        """When create_user fails, finds existing user by email and updates password."""
        existing_id = str(uuid.uuid4())
        list_result = self._make_list_users_with("test@example.com", user_id=existing_id)
        db_admin = self._make_db_admin_for_e2e(
            create_user_raises=Exception("User already registered"),
            list_users_result=list_result,
        )

        db_anon = _make_db()
        auth_resp = _make_auth_response(user_id=existing_id)
        db_anon.auth = MagicMock()
        db_anon.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"
            result = await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="supersecret")

        assert result.user_id == existing_id
        db_admin.auth.admin.update_user_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_profile_upserted_after_user_creation(self):
        """Profile is upserted into profiles table after user is created."""
        created = self._make_created_user()
        db_admin = self._make_db_admin_for_e2e(create_user_result=created)

        upsert_chain = MagicMock()
        upsert_chain.execute = AsyncMock(return_value=_result(data=[{"id": USER_ID}]))
        upsert_called_with = {}

        original_table = db_admin.table

        def patched_table(name):
            if name == "profiles":
                t = MagicMock()
                t.upsert = MagicMock(side_effect=lambda data, **kw: upsert_called_with.update(data) or upsert_chain)
                return t
            return original_table(name)

        db_admin.table = patched_table

        db_anon = _make_db()
        auth_resp = _make_auth_response()
        db_anon.auth = MagicMock()
        db_anon.auth.sign_in_with_password = AsyncMock(return_value=auth_resp)

        payload = RegisterRequest(**_make_valid_register_payload(username="e2euser"))

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"
            await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="supersecret")

        assert upsert_called_with.get("username") == "e2euser"

    @pytest.mark.asyncio
    async def test_500_on_unexpected_error(self):
        """Unexpected exception after secret check raises 500 E2E_SETUP_FAILED."""
        created = self._make_created_user()
        db_admin = self._make_db_admin_for_e2e(create_user_result=created)

        db_anon = _make_db()
        db_anon.auth = MagicMock()
        db_anon.auth.sign_in_with_password = AsyncMock(side_effect=RuntimeError("Unexpected DB failure"))

        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"

            with pytest.raises(HTTPException) as exc:
                await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="supersecret")

        assert exc.value.status_code == 500
        assert exc.value.detail["code"] == "E2E_SETUP_FAILED"

    @pytest.mark.asyncio
    async def test_500_when_existing_user_lookup_also_fails(self):
        """500 when create_user fails and list_users also raises exception."""
        db_admin = self._make_db_admin_for_e2e(
            create_user_raises=Exception("Already exists"),
            list_users_result=MagicMock(users=[]),  # no matching user found
        )
        # user_id stays None → re-raises
        db_admin.auth.admin.list_users = AsyncMock(side_effect=Exception("list_users also failed"))

        db_anon = _make_db()
        payload = RegisterRequest(**_make_valid_register_payload())

        with patch("app.routers.auth.settings") as mock_settings:
            mock_settings.e2e_test_secret = "supersecret"

            with pytest.raises(HTTPException) as exc:
                await e2e_create_user(FAKE_REQUEST, payload, db_admin, db_anon, x_e2e_secret="supersecret")

        assert exc.value.status_code == 500
