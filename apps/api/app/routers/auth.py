"""Auth endpoints — thin layer on top of Supabase Auth.

Rate limited: 5 requests/minute per IP (brute force prevention).
"""

import hmac
import re
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, EmailStr, field_validator

from app.config import settings
from app.deps import CurrentUserId, SupabaseAdmin, SupabaseAnon
from app.middleware.rate_limit import RATE_AUTH, RATE_DEFAULT, limiter

router = APIRouter(prefix="/auth", tags=["Auth"])

# Username validation: 3-30 chars, alphanumeric + underscore/hyphen + Azerbaijani chars
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-əğıöüşçƏĞİÖÜŞÇ]{3,30}$")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    display_name: str | None = None
    referral_code: str | None = None  # username of the person who referred this user

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip().lower()
        if not USERNAME_RE.match(v):
            raise ValueError("Username must be 3-30 characters: letters, numbers, underscore, hyphen")
        return v

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if len(v) > 100:
                raise ValueError("Display name must be at most 100 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str


class MeResponse(BaseModel):
    user_id: str
    profile: dict | None = None


class MessageResponse(BaseModel):
    message: str


class SignupStatusResponse(BaseModel):
    open_signup: bool


class ValidateInviteRequest(BaseModel):
    invite_code: str


class ValidateInviteResponse(BaseModel):
    valid: bool


@router.get("/signup-status", response_model=SignupStatusResponse)
async def signup_status() -> SignupStatusResponse:
    """Return whether signup is open. Public — no auth required.

    open_signup=True  → anyone can register (dev mode, or fully launched)
    open_signup=False → invite code required (controlled beta)
    """
    return SignupStatusResponse(open_signup=settings.open_signup)


@router.post("/validate-invite", response_model=ValidateInviteResponse)
@limiter.limit(RATE_AUTH)
async def validate_invite(
    request: Request,
    payload: ValidateInviteRequest,
) -> ValidateInviteResponse:
    """Validate a beta invite code. Returns {valid: bool}.

    Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
    If BETA_INVITE_CODE is empty, always returns valid=False (gate is armed but
    misconfigured — prevents silent bypass when code is not yet set on Railway).
    """
    code = settings.beta_invite_code
    if not code:
        # Code not configured — gate armed but no valid code exists
        return ValidateInviteResponse(valid=False)
    is_valid = hmac.compare_digest(
        payload.invite_code.strip().lower(),
        code.strip().lower(),
    )
    return ValidateInviteResponse(valid=is_valid)


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit(RATE_AUTH)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: SupabaseAnon,
) -> AuthResponse:
    """Register a new user via Supabase Auth (anon key — OWASP HIGH-05 fix)."""
    try:
        auth_response = await db.auth.sign_up(
            {
                "email": payload.email,
                "password": payload.password,
                "options": {
                    "data": {
                        "username": payload.username,
                        "display_name": payload.display_name or payload.username,
                        "referral_code": payload.referral_code or "",
                    }
                },
            }
        )
    except Exception as e:
        # Security: don't leak internal error details to client
        from loguru import logger

        logger.warning("Registration failed", email_domain=payload.email.split("@")[-1], error=str(e)[:200])
        raise HTTPException(
            status_code=400,
            detail={"code": "REGISTRATION_FAILED", "message": "Registration failed. Email may already be in use."},
        )

    if not auth_response.session:
        raise HTTPException(
            status_code=400,
            detail={"code": "EMAIL_CONFIRMATION_REQUIRED", "message": "Check your email to confirm registration"},
        )

    return AuthResponse(
        access_token=auth_response.session.access_token,
        expires_in=auth_response.session.expires_in or 3600,
        user_id=str(auth_response.user.id),
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(RATE_AUTH)
async def login(
    request: Request,
    payload: LoginRequest,
    db: SupabaseAnon,
) -> AuthResponse:
    """Login with email + password (anon key — OWASP HIGH-05 fix)."""
    try:
        auth_response = await db.auth.sign_in_with_password(
            {
                "email": payload.email,
                "password": payload.password,
            }
        )
    except Exception:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    return AuthResponse(
        access_token=auth_response.session.access_token,
        expires_in=auth_response.session.expires_in or 3600,
        user_id=str(auth_response.user.id),
    )


@router.get("/me", response_model=MeResponse)
@limiter.limit(RATE_DEFAULT)
async def get_me(
    request: Request,
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> MeResponse:
    """Get current user info from JWT."""
    # maybe_single() returns None (not an exception) when no row exists.
    # .single() throws APIError 406 when no profile — breaks new users who skipped onboarding.
    result = (
        await db.table("profiles")
        .select("id, username, display_name, avatar_url")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    return MeResponse(user_id=user_id, profile=result.data)


@router.delete("/me", status_code=200, response_model=MessageResponse)
@limiter.limit(RATE_AUTH)
async def delete_account(
    request: Request,
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
) -> MessageResponse:
    """Permanently delete the current user's account and all associated data.

    Steps:
    1. Delete auth user via Supabase admin API (cascades to profiles, sessions, etc.)
    2. Return success — client must call supabase.auth.signOut() to clear local state.

    GDPR compliance: all user data removed. This action is irreversible.
    """
    from loguru import logger

    try:
        await db_admin.auth.admin.delete_user(user_id)
        logger.info("Account deleted", user_id=str(user_id))
    except Exception as e:
        logger.error("Account deletion failed", user_id=str(user_id), error=str(e))
        raise HTTPException(
            status_code=500,
            detail={"code": "DELETION_FAILED", "message": "Account deletion failed. Please try again."},
        )
    return MessageResponse(message="Account deleted successfully")


@router.post("/logout", status_code=200, response_model=MessageResponse)
@limiter.limit(RATE_AUTH)
async def logout(
    request: Request,
    user_id: CurrentUserId,
    db_admin: SupabaseAdmin,
) -> MessageResponse:
    """Logout — revoke token server-side (BUG-016 fix).

    Calls Supabase admin sign_out with the current JWT. Because auth validation
    uses admin.auth.get_user(token), any subsequent request with this token will
    fail with 401 immediately — no need for a local blacklist table.

    Scope: "global" — invalidates ALL sessions for this user (all devices).
    """
    from loguru import logger

    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").strip()

    try:
        await db_admin.auth.admin.sign_out(token)
        logger.info("User logout — token revoked", user_id=str(user_id))
    except Exception as e:
        # sign_out failure is non-fatal — token expires naturally; log and proceed
        logger.warning("Token revocation failed (non-fatal)", user_id=str(user_id), error=str(e)[:200])

    return MessageResponse(message="Logged out")


@router.post("/e2e-setup", response_model=AuthResponse, status_code=201)
async def e2e_create_user(
    request: Request,
    payload: RegisterRequest,
    db_admin: SupabaseAdmin,
    db_anon: SupabaseAnon,
    x_e2e_secret: Annotated[str | None, Header(alias="X-E2E-Secret")] = None,
) -> AuthResponse:
    """Create a confirmed test user and return a real session token.

    Protected by E2E_TEST_SECRET — returns 404 when not configured (safe default).
    Uses admin API to bypass email confirmation, then signs in for a real session.
    """
    if not settings.e2e_test_secret or not x_e2e_secret:
        raise HTTPException(status_code=404, detail="Not found")
    if not hmac.compare_digest(x_e2e_secret, settings.e2e_test_secret):
        raise HTTPException(status_code=404, detail="Not found")

    try:
        result = await db_admin.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {
                    "username": payload.username,
                    "display_name": payload.display_name or payload.username,
                },
            }
        )
        user = getattr(result, "user", None) or result
        user_id = str(getattr(user, "id", None))

        await (
            db_admin.table("profiles")
            .upsert(
                {
                    "id": user_id,
                    "username": payload.username,
                    "display_name": payload.display_name or payload.username,
                },
                on_conflict="id",
            )
            .execute()
        )

        auth_response = await db_anon.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )

        return AuthResponse(
            access_token=auth_response.session.access_token,
            expires_in=auth_response.session.expires_in or 3600,
            user_id=user_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("E2E setup failed", error=str(e)[:200])
        raise HTTPException(
            status_code=500,
            detail={"code": "E2E_SETUP_FAILED", "message": str(e)[:200]},
        )
