"""FastAPI dependencies for Supabase client and auth."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from supabase._async.client import AsyncClient, acreate_client
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
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ")

    client = await acreate_client(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_anon_key,
    )

    # Set the user's JWT for RLS
    client.postgrest.auth(token)

    yield client


async def get_current_user_id(request: Request) -> str:
    """Extract user ID from Supabase JWT (sub claim).

    Validates the JWT and returns the user's UUID.
    """
    from jose import jwt, JWTError

    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth_header.removeprefix("Bearer ")

    try:
        # Supabase JWTs use the anon key as the secret for verification
        payload = jwt.decode(
            token,
            settings.supabase_anon_key,
            algorithms=["HS256"],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")
        return user_id
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Type aliases for cleaner route signatures
SupabaseAdmin = Annotated[AsyncClient, Depends(get_supabase_admin)]
SupabaseUser = Annotated[AsyncClient, Depends(get_supabase_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
