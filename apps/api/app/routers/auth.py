"""Auth endpoints — thin layer on top of Supabase Auth.

Rate limited: 5 requests/minute per IP (brute force prevention).
"""

import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseAnon
from app.middleware.rate_limit import limiter, RATE_AUTH
from app.schemas.profile import ProfileResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

# Username validation: 3-30 chars, alphanumeric + underscore/hyphen + Azerbaijani chars
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\-əğıöüşçƏĞİÖÜŞÇ]{3,30}$")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str
    display_name: str | None = None

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


@router.post("/register", response_model=AuthResponse, status_code=201)
@limiter.limit(RATE_AUTH)
async def register(
    request: Request,
    payload: RegisterRequest,
    db: SupabaseAnon,
) -> AuthResponse:
    """Register a new volunteer via Supabase Auth (anon key — OWASP HIGH-05 fix)."""
    try:
        auth_response = await db.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
            "options": {
                "data": {
                    "username": payload.username,
                    "display_name": payload.display_name or payload.username,
                }
            },
        })
    except Exception as e:
        # Security: don't leak internal error details to client
        from loguru import logger
        logger.warning(f"Registration failed for {payload.email}: {e}")
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
        auth_response = await db.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })
    except Exception as e:
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )

    return AuthResponse(
        access_token=auth_response.session.access_token,
        expires_in=auth_response.session.expires_in or 3600,
        user_id=str(auth_response.user.id),
    )


@router.get("/me")
async def get_me(
    user_id: CurrentUserId,
    db: SupabaseAdmin,
) -> dict:
    """Get current user info from JWT."""
    result = (
        await db.table("profiles")
        .select("id, username, display_name, avatar_url")
        .eq("id", user_id)
        .single()
        .execute()
    )
    if not result.data:
        return {"user_id": user_id, "profile": None}
    return {"user_id": user_id, "profile": result.data}


@router.post("/logout", status_code=200)
@limiter.limit(RATE_AUTH)
async def logout(
    request: Request,
    user_id: CurrentUserId,
) -> dict:
    """Logout — audit log entry for session termination (OWASP A07 compliance).

    JWT invalidation happens client-side via supabase.auth.signOut().
    This endpoint serves as an audit trail so session endings are recorded.
    """
    from loguru import logger

    logger.info("User logout", user_id=str(user_id))
    return {"message": "Logged out"}
