"""Health check endpoint."""

import os

from fastapi import APIRouter
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")


@router.get("/health/env-debug")
async def env_debug() -> dict:
    """Temporary debug endpoint — remove after diagnosis."""
    anon_key = settings.supabase_anon_key
    return {
        "anon_key_set": bool(anon_key),
        "anon_key_prefix": anon_key[:15] if anon_key else "",
        "os_anon_key": os.environ.get("SUPABASE_ANON_KEY", "NOT SET")[:15],
        "supabase_url": settings.supabase_url[:30],
    }
