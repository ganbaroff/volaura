"""Auth bridge router — Sprint E2.D.2 (ADR-006 Option D).

One endpoint: POST /api/auth/from_external

Called by the MindShift `volaura-bridge-proxy` edge function after it has
validated a MindShift user's JWT against MindShift's own auth. The edge
function passes the user's email + standalone user_id + a pre-shared
X-Bridge-Secret header. We:

  1. Verify X-Bridge-Secret matches settings.external_bridge_secret
  2. Look up existing mapping in public.user_identity_map by
     (standalone_user_id, standalone_project_ref)
  3. If no mapping:
     a. Check auth.users in shared project by email (user might have
        signed up to VOLAURA directly before bridging from MindShift)
     b. If exists → insert mapping using that existing shared_user_id
     c. If not → create shadow user via admin.auth.admin.create_user
        with email_confirm=True and a random password → insert mapping
  4. Mint a shared-project JWT for shared_user_id using
     settings.supabase_jwt_secret (HS256, 1 hour expiry)
  5. Update last_seen_at on the mapping row
  6. Return { shared_user_id, shared_jwt, expires_at }

The returned shared_jwt is then used by the edge function (or cached
client-side) as the Authorization header for subsequent calls to
/api/character/events and friends. Those endpoints use the existing
get_current_user_id dependency which validates via admin.auth.get_user —
this works because the minted JWT is signed with the same secret Supabase
uses for its own tokens, so it is indistinguishable from a real session.

SECURITY:
- Endpoint is feature-flagged: returns 503 if supabase_jwt_secret or
  external_bridge_secret is empty (safe default on dev machines)
- Rate limited separately from user-scoped endpoints
- X-Bridge-Secret is constant-time compared
- Never accepts a user_id from the request body for any auth purpose —
  only the mapping's shared_user_id is authoritative
- Logs every bridge creation for audit
"""

from __future__ import annotations

import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from jose import jwt
from loguru import logger
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.config import settings
from app.deps import SupabaseAdmin
from app.middleware.rate_limit import limiter


router = APIRouter(prefix="/auth", tags=["Auth Bridge"])


# ── Rate limit: tighter than default, it's service-to-service ────────────
# One MindShift user = one call on first bridge + occasional refresh.
# 60/minute leaves room for concurrent sign-ups during a campaign.
RATE_BRIDGE = "60/minute"


# ── Schemas ──────────────────────────────────────────────────────────────


class FromExternalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    standalone_user_id: str = Field(..., min_length=1, max_length=128)
    standalone_project_ref: str = Field(..., min_length=1, max_length=64)
    email: EmailStr
    source_product: str = Field(default="mindshift", max_length=32)


class FromExternalResponse(BaseModel):
    shared_user_id: str
    shared_jwt: str
    expires_at: datetime
    created_new_user: bool  # true if we had to create a shadow auth.users row


# ── JWT minting ──────────────────────────────────────────────────────────


_JWT_ALGORITHM = "HS256"
_JWT_LIFETIME_SECONDS = 3600  # 1 hour — edge function refreshes on each bridge call


def _mint_shared_jwt(shared_user_id: str, email: str) -> tuple[str, datetime]:
    """Mint a Supabase-compatible JWT using the shared project's JWT secret.

    The minted JWT is indistinguishable from a real Supabase auth session
    token because it is signed with the same HS256 secret Supabase uses.
    Existing get_current_user_id dependency will accept it via
    admin.auth.get_user() — that call hits Supabase's auth service which
    verifies signature with the same secret.
    """
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=_JWT_LIFETIME_SECONDS)

    payload = {
        "sub": shared_user_id,
        "email": email,
        "aud": "authenticated",
        "role": "authenticated",
        "iss": "supabase",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        # Supabase also includes these — harmless to mint them
        "app_metadata": {"provider": "external_bridge"},
        "user_metadata": {},
    }

    token = jwt.encode(payload, settings.supabase_jwt_secret, algorithm=_JWT_ALGORITHM)
    return token, exp


# ── Helpers ──────────────────────────────────────────────────────────────


async def _find_user_by_email(admin, email: str) -> str | None:
    """Look up auth.users by email using admin SDK. Returns UUID or None."""
    try:
        # Supabase admin SDK — list users filtered by email. API is slightly
        # awkward: list_users returns a paginated list, so we filter locally.
        # For small-to-medium projects (<10k users) this is fine. If VOLAURA
        # grows past that, swap to a direct SQL lookup via rpc.
        result = await admin.auth.admin.list_users()
        users = getattr(result, "users", None) or result
        for u in users:
            u_email = getattr(u, "email", None)
            if u_email and u_email.lower() == email.lower():
                return str(u.id)
        return None
    except Exception as e:
        logger.warning("admin.auth.admin.list_users failed during bridge lookup", error=str(e))
        return None


async def _create_shadow_user(admin, email: str) -> str:
    """Create a shadow auth.users row in shared project for an external user.

    Password is random and never stored — the user can always recover access
    via magic link or password reset at volaura.app if they want a direct
    VOLAURA account later. For now they use MindShift → bridge pattern.
    """
    random_password = secrets.token_urlsafe(32)
    try:
        result = await admin.auth.admin.create_user({
            "email": email,
            "password": random_password,
            "email_confirm": True,
            "user_metadata": {"origin": "external_bridge"},
        })
        user = getattr(result, "user", None) or result
        user_id = str(getattr(user, "id", None))
        if not user_id or user_id == "None":
            raise RuntimeError("create_user returned no user id")
        logger.info("Shadow user created via bridge", email=email, shared_user_id=user_id)
        return user_id
    except Exception as e:
        logger.error("Failed to create shadow user", email=email, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SHADOW_USER_CREATE_FAILED",
                "message": f"Could not create shadow user for {email}",
            },
        )


# ── Endpoint ─────────────────────────────────────────────────────────────


@router.post("/from_external", response_model=FromExternalResponse, status_code=200)
@limiter.limit(RATE_BRIDGE)
async def bridge_from_external(
    request: Request,
    body: FromExternalRequest,
    admin: SupabaseAdmin,
    x_bridge_secret: Annotated[str | None, Header(alias="X-Bridge-Secret")] = None,
) -> FromExternalResponse:
    """Bridge a user from a standalone Supabase project into shared project.

    Returns a shared-project JWT the caller can use for all /api/character/*
    endpoints. See module docstring for full flow.
    """
    # ── Feature flag: require both secrets to be configured ──────────────
    if not settings.supabase_jwt_secret or not settings.external_bridge_secret:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "BRIDGE_DISABLED",
                "message": "External auth bridge is not configured. Set SUPABASE_JWT_SECRET and EXTERNAL_BRIDGE_SECRET.",
            },
        )

    # ── Auth: constant-time compare of bridge secret ─────────────────────
    if not x_bridge_secret or not hmac.compare_digest(
        x_bridge_secret, settings.external_bridge_secret
    ):
        # Log without revealing whether the header was missing or wrong
        logger.warning(
            "Bridge secret mismatch",
            email=body.email,
            standalone_project=body.standalone_project_ref,
            header_present=bool(x_bridge_secret),
        )
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_BRIDGE_SECRET", "message": "Invalid or missing bridge secret"},
        )

    # ── Step 1: look up existing mapping ──────────────────────────────────
    mapping_result = (
        await admin.table("user_identity_map")
        .select("shared_user_id")
        .eq("standalone_user_id", body.standalone_user_id)
        .eq("standalone_project_ref", body.standalone_project_ref)
        .execute()
    )

    shared_user_id: str | None = None
    created_new_user = False

    if mapping_result.data:
        shared_user_id = str(mapping_result.data[0]["shared_user_id"])
        # Touch last_seen_at
        await (
            admin.table("user_identity_map")
            .update({"last_seen_at": datetime.now(timezone.utc).isoformat()})
            .eq("standalone_user_id", body.standalone_user_id)
            .eq("standalone_project_ref", body.standalone_project_ref)
            .execute()
        )
        logger.info(
            "Bridge reused existing mapping",
            standalone=body.standalone_user_id[:8],
            shared_user_id=shared_user_id[:8],
        )
    else:
        # ── Step 2: look up auth.users by email (direct VOLAURA signup case) ──
        shared_user_id = await _find_user_by_email(admin, body.email)

        # ── Step 3: no existing user — create shadow ──────────────────────
        if not shared_user_id:
            shared_user_id = await _create_shadow_user(admin, body.email)
            created_new_user = True

        # ── Step 4: insert mapping row ────────────────────────────────────
        try:
            await (
                admin.table("user_identity_map")
                .insert(
                    {
                        "standalone_user_id": body.standalone_user_id,
                        "standalone_project_ref": body.standalone_project_ref,
                        "shared_user_id": shared_user_id,
                        "email": body.email,
                        "source_product": body.source_product,
                    }
                )
                .execute()
            )
            logger.info(
                "Bridge created new mapping",
                email=body.email,
                standalone=body.standalone_user_id[:8],
                shared_user_id=shared_user_id[:8],
                created_new_user=created_new_user,
            )
        except Exception as e:
            logger.error(
                "Failed to insert identity mapping",
                error=str(e),
                email=body.email,
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "MAPPING_INSERT_FAILED",
                    "message": "Could not persist identity mapping",
                },
            )

    # ── Step 5: mint the shared JWT ───────────────────────────────────────
    try:
        token, expires_at = _mint_shared_jwt(shared_user_id, body.email)
    except Exception as e:
        logger.error("JWT mint failed", error=str(e), shared_user_id=shared_user_id[:8])
        raise HTTPException(
            status_code=500,
            detail={"code": "JWT_MINT_FAILED", "message": "Could not mint shared JWT"},
        )

    return FromExternalResponse(
        shared_user_id=shared_user_id,
        shared_jwt=token,
        expires_at=expires_at,
        created_new_user=created_new_user,
    )
