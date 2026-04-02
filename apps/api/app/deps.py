"""FastAPI dependencies for Supabase client and auth.

Security: JWT verification uses admin.auth.get_user() which validates
tokens server-side against Supabase's auth service. This is the ONLY
correct way to verify JWTs — never use the anon key as a JWT secret.
See: docs/engineering/SECURITY-STANDARDS.md
"""

import asyncio
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from supabase._async.client import AsyncClient, create_client as acreate_client
from loguru import logger

from app.config import settings


# --- Admin client singleton ---------------------------------------------------
# httpx.AsyncClient (underlying transport) is coroutine-safe and designed for
# shared use across concurrent requests. A single instance maintains a connection
# pool to Supabase PostgREST, avoiding the "100 requests = 100 TCP connections"
# problem that causes 504s at scale (PostgREST default max_connections=100).
#
# User clients CANNOT be singletons: each request injects a different JWT via
# client.postgrest.auth(token), so they must remain per-request.
# ------------------------------------------------------------------------------

_admin_client: AsyncClient | None = None
_admin_lock = asyncio.Lock()


async def _get_or_create_admin_client() -> AsyncClient:
    """Return the singleton admin client, creating it on first call.

    Double-checked locking: the outer `if` avoids acquiring the lock on
    every request (fast path). The inner `if` prevents double-initialisation
    when two coroutines race through the outer check simultaneously.
    """
    global _admin_client
    if _admin_client is not None:
        return _admin_client
    async with _admin_lock:
        if _admin_client is None:
            _admin_client = await acreate_client(
                supabase_url=settings.supabase_url,
                supabase_key=settings.supabase_service_key,
            )
    return _admin_client


async def get_supabase_admin() -> AsyncGenerator[AsyncClient, None]:
    """Admin Supabase client — singleton, shared across requests for connection pooling.

    Creates once on first use, then reuses the underlying httpx connection pool.
    This prevents per-request TCP connection exhaustion at scale (100+ concurrent
    users would otherwise saturate PostgREST's default max_connections=100).

    Uses service role key which bypasses RLS — use carefully.
    """
    client = await _get_or_create_admin_client()
    yield client


async def get_supabase_user(request: Request) -> AsyncGenerator[AsyncClient, None]:
    """User-scoped Supabase client — respects RLS via user's JWT.

    Extracts the Bearer token from the request Authorization header
    and creates a client that operates with the user's permissions.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"code": "MISSING_TOKEN", "message": "Missing or invalid Authorization header"},
        )

    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=401,
            detail={"code": "EMPTY_TOKEN", "message": "Bearer token is empty"},
        )

    try:
        client = await acreate_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.effective_anon_key,
        )
        # Set the user's JWT for RLS
        client.postgrest.auth(token)
    except Exception as e:
        logger.error("Failed to create user Supabase client: {err}", err=str(e))
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_CLIENT_ERROR", "message": "Internal server error"},
        )

    yield client


async def get_current_user_id(
    request: Request,
    admin: AsyncClient = Depends(get_supabase_admin),
) -> str:
    """Validate JWT server-side via Supabase admin and return user UUID.

    SECURITY FIX (CVSS 9.1): Previous implementation verified JWTs using the
    anon key — which is PUBLIC and shipped to every browser. Any attacker could
    forge valid JWTs. Now we validate via admin.auth.get_user(token) which
    checks the token against Supabase's auth service using the service role key.
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail={"code": "MISSING_TOKEN", "message": "Missing or invalid Authorization header"},
        )

    token = auth_header.removeprefix("Bearer ")

    try:
        user_response = await admin.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=401,
                detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
            )
        return str(user_response.user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("JWT verification failed", error=str(e))
        raise HTTPException(
            status_code=401,
            detail={"code": "INVALID_TOKEN", "message": "Invalid or expired token"},
        )


async def get_supabase_anon() -> AsyncGenerator[AsyncClient, None]:
    """Anon Supabase client — for unauthenticated operations (register, login).

    Uses the public anon key. Supabase RLS applies normally.
    OWASP HIGH-05 fix: auth operations should use anon key, not service role.
    """
    client = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.effective_anon_key,
    )
    yield client


async def get_optional_user_id(
    request: Request,
    admin: AsyncClient = Depends(get_supabase_admin),
) -> str | None:
    """Like get_current_user_id but returns None when no token is present.

    Used for endpoints that are public but can personalise results when
    the caller is authenticated (e.g. leaderboard is_current_user flag).
    """
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header.removeprefix("Bearer ").strip()
    if not token:
        return None
    try:
        user_response = await admin.auth.get_user(token)
        if not user_response or not user_response.user:
            return None
        return str(user_response.user.id)
    except Exception:
        return None


async def require_platform_admin(
    user_id: str = Depends(get_current_user_id),
    admin: AsyncClient = Depends(get_supabase_admin),
) -> str:
    """Verify caller is a platform admin. Fail-closed (Mistake #57 pattern).

    Checks the service-role client so users cannot spoof is_platform_admin
    via a crafted JWT or user-scoped Supabase request.
    """
    result = await admin.table("profiles").select("is_platform_admin").eq("id", user_id).maybe_single().execute()
    if not result.data or not result.data.get("is_platform_admin"):
        raise HTTPException(
            status_code=403,
            detail={"code": "NOT_PLATFORM_ADMIN", "message": "Platform admin access required"},
        )
    return user_id


# Type aliases for cleaner route signatures
SupabaseAdmin = Annotated[AsyncClient, Depends(get_supabase_admin)]
SupabaseUser = Annotated[AsyncClient, Depends(get_supabase_user)]
SupabaseAnon = Annotated[AsyncClient, Depends(get_supabase_anon)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
OptionalCurrentUserId = Annotated[str | None, Depends(get_optional_user_id)]
PlatformAdminId = Annotated[str, Depends(require_platform_admin)]
