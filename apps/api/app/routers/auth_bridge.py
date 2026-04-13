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
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Header, HTTPException, Request
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
    now = datetime.now(UTC)
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
    """Look up auth.users by email via service-role RPC. Returns UUID or None.

    Uses the find_shared_user_id_by_email() SQL function (defined in migration
    20260408000001_user_identity_map.sql). That function runs SECURITY DEFINER
    and does a single indexed lookup — O(1), no pagination, no user count
    ceiling. Agents (Qwen 235B, Kimi K2, Nemotron 120B, Gemma 4) all flagged
    the previous list_users() pagination approach as failing at scale.
    """
    target = (email or "").strip().lower()
    if not target:
        return None
    try:
        result = await admin.rpc(
            "find_shared_user_id_by_email",
            {"p_email": target},
        ).execute()
        data = result.data
        # RPC returns UUID or None. Supabase wraps scalar in a list sometimes.
        if isinstance(data, list):
            data = data[0] if data else None
        if not data:
            return None
        return str(data)
    except Exception as e:
        logger.warning(
            "find_shared_user_id_by_email RPC failed during bridge lookup",
            error=str(e),
        )
        return None


async def _ensure_profile_row(admin, shared_user_id: str) -> None:
    """Ensure a profiles row exists for a bridged user.

    Fix for E2E smoke finding (2026-04-11): bridged users had an auth.users
    row but no public.profiles row, so every FK to profiles (assessment_sessions,
    aura_scores, badges, events, embeddings, ...) broke on first write. The
    /api/auth/register flow creates profiles as part of signup; the bridge
    path bypassed that and left users unable to complete assessments.

    Idempotent: uses UPSERT with on_conflict=id so repeated bridge calls for
    the same user are safe. Username is derived from the UUID (hex, 16 chars)
    which guarantees uniqueness without consulting the DB.
    """
    # Derive a stable, unique, format-safe username from the user's UUID.
    # 16 hex chars of a UUID = 64 bits of entropy → collision probability ~0.
    username = f"u{shared_user_id.replace('-', '')[:16]}"
    try:
        await (
            admin.table("profiles")
            .upsert(
                {"id": shared_user_id, "username": username},
                on_conflict="id",
            )
            .execute()
        )
    except Exception as e:
        logger.warning(
            "profiles upsert failed during bridge — user may hit FK errors later",
            shared_user_id=shared_user_id[:8],
            error=str(e)[:200],
        )


async def _create_shadow_user(admin, email: str) -> str:
    """Create a shadow auth.users row in shared project for an external user.

    Race-tolerant: two concurrent bridge calls for the same new email can
    both pass the _find_user_by_email check and both reach create_user. The
    second call catches the "email already exists" error from GoTrue and
    falls back to a fresh _find_user_by_email lookup, returning the UUID
    created by the winner of the race. This prevents duplicate shadow users
    for the same email (per-email idempotency).

    Password is random and never stored — the user recovers access via
    magic link / password reset at volaura.app if they ever need direct
    VOLAURA access. For now they use MindShift → bridge pattern.
    """
    email_norm = email.strip().lower()
    random_password = secrets.token_urlsafe(32)
    try:
        result = await admin.auth.admin.create_user(
            {
                "email": email_norm,
                "password": random_password,
                "email_confirm": True,
                "user_metadata": {"origin": "external_bridge"},
            }
        )
        user = getattr(result, "user", None) or result
        user_id = str(getattr(user, "id", None))
        if not user_id or user_id == "None":
            raise RuntimeError("create_user returned no user id")
        logger.info("Shadow user created via bridge", email=email_norm, shared_user_id=user_id)
        return user_id
    except Exception as e:
        # Race-condition fallback: GoTrue raises "User already registered" or
        # "email_exists" when a concurrent request created the user between
        # our _find_user_by_email and this create_user call. Re-lookup and
        # return the existing UUID.
        err_text = str(e).lower()
        if any(
            marker in err_text
            for marker in ("already registered", "email_exists", "already exists", "duplicate key", "unique constraint")
        ):
            logger.info(
                "Shadow user create hit race — re-looking up existing user",
                email=email_norm,
                error=str(e)[:200],
            )
            existing_id = await _find_user_by_email(admin, email_norm)
            if existing_id:
                return existing_id
            # Race winner hasn't committed yet — give it a moment and retry once
            import asyncio as _a

            await _a.sleep(0.25)
            existing_id = await _find_user_by_email(admin, email_norm)
            if existing_id:
                return existing_id
            # Still nothing — treat as real error
        logger.error("Failed to create shadow user", email=email_norm, error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "code": "SHADOW_USER_CREATE_FAILED",
                "message": f"Could not create shadow user for {email_norm}",
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
    if not x_bridge_secret or not hmac.compare_digest(x_bridge_secret, settings.external_bridge_secret):
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

    # ── Normalize email once — used for all lookups, create, and upsert ──
    email_norm = body.email.strip().lower()

    # ── Step 1: look up existing mapping by (standalone_user_id, project_ref) ──
    # Keyed on standalone_user_id (not email) so that email drift in MindShift
    # does NOT split user identity. If the MindShift user later changes email,
    # we find them by their stable standalone UUID and only the email column
    # on the mapping row drifts forward.
    mapping_result = (
        await admin.table("user_identity_map")
        .select("shared_user_id, email")
        .eq("standalone_user_id", body.standalone_user_id)
        .eq("standalone_project_ref", body.standalone_project_ref)
        .execute()
    )

    shared_user_id: str | None = None
    created_new_user = False

    if mapping_result.data:
        shared_user_id = str(mapping_result.data[0]["shared_user_id"])
        # Touch last_seen_at + update stored email on every bridge call so
        # email drift in MindShift is reflected in our mapping. Does NOT
        # update auth.users.email — that's a separate admin action the user
        # must do via volaura.app or a future reconciliation job.
        await (
            admin.table("user_identity_map")
            .update(
                {
                    "last_seen_at": datetime.now(UTC).isoformat(),
                    "email": email_norm,
                }
            )
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
        shared_user_id = await _find_user_by_email(admin, email_norm)

        # ── Step 3: no existing user — create shadow ──────────────────────
        if not shared_user_id:
            shared_user_id = await _create_shadow_user(admin, email_norm)
            created_new_user = True

        # ── Step 4: UPSERT mapping row ────────────────────────────────────
        # Upsert on PK (standalone_user_id, standalone_project_ref) prevents
        # the race where two concurrent bridge calls both reach this step
        # and the second INSERT would 500 on PK conflict. Idempotent.
        try:
            await (
                admin.table("user_identity_map")
                .upsert(
                    {
                        "standalone_user_id": body.standalone_user_id,
                        "standalone_project_ref": body.standalone_project_ref,
                        "shared_user_id": shared_user_id,
                        "email": email_norm,
                        "source_product": body.source_product,
                        "last_seen_at": datetime.now(UTC).isoformat(),
                    },
                    on_conflict="standalone_user_id,standalone_project_ref",
                )
                .execute()
            )
            logger.info(
                "Bridge upserted mapping",
                email=email_norm,
                standalone=body.standalone_user_id[:8],
                shared_user_id=shared_user_id[:8],
                created_new_user=created_new_user,
            )
        except Exception as e:
            logger.error(
                "Failed to upsert identity mapping",
                error=str(e),
                email=email_norm,
            )
            raise HTTPException(
                status_code=500,
                detail={
                    "code": "MAPPING_UPSERT_FAILED",
                    "message": "Could not persist identity mapping",
                },
            )

    # ── Step 4.5: ensure profiles row exists (bridged users need this for
    # assessment/AURA/badge flows — the register endpoint creates profiles
    # explicitly, but the bridge path bypassed that until the E2E smoke caught
    # it). Idempotent upsert; safe for both new shadow users and existing ones
    # that predate this fix. Failures are logged but non-fatal — the JWT mint
    # still proceeds so the caller can at least read-only features work.
    await _ensure_profile_row(admin, shared_user_id)

    # ── Step 5: mint the shared JWT ───────────────────────────────────────
    try:
        token, expires_at = _mint_shared_jwt(shared_user_id, email_norm)
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
