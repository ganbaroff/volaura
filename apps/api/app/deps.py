"""FastAPI dependencies for Supabase client and auth.

Security: JWT verification uses admin.auth.get_user() which validates
tokens server-side against Supabase's auth service. This is the ONLY
correct way to verify JWTs — never use the anon key as a JWT secret.
See: docs/engineering/SECURITY-STANDARDS.md
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from supabase._async.client import AsyncClient, create_client as acreate_client
from loguru import logger

from app.config import settings


async def get_supabase_admin() -> AsyncGenerator[AsyncClient, None]:
    """Admin Supabase client (service role key) — for server-side operations.

    Creates a per-request client to ensure RLS isolation.
    Uses service role key which bypasses RLS — use carefully.
    """
    client = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
    )
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

    token = auth_header.removeprefix("Bearer ")

    anon_key = settings.supabase_anon_key
    logger.info(
        "get_supabase_user: anon_key_len={len} prefix={prefix}",
        len=len(anon_key),
        prefix=anon_key[:15] if anon_key else "EMPTY",
    )
    try:
        client = await acreate_client(
            supabase_url=settings.supabase_url,
            supabase_key=anon_key,
        )
        # Set the user's JWT for RLS
        client.postgrest.auth(token)
    except Exception as e:
        logger.error("Failed to create user Supabase client: {err}", err=str(e))
        raise HTTPException(
            status_code=500,
            detail={"code": "DB_CLIENT_ERROR", "message": str(e)},
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


# Type aliases for cleaner route signatures
SupabaseAdmin = Annotated[AsyncClient, Depends(get_supabase_admin)]
SupabaseUser = Annotated[AsyncClient, Depends(get_supabase_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
