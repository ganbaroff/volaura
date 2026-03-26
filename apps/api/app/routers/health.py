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
    svc_key = settings.supabase_service_key
    return {
        "anon_key_set": bool(anon_key),
        "anon_key_len": len(anon_key),
        "anon_key_prefix": anon_key[:15] if anon_key else "",
        "svc_key_set": bool(svc_key),
        "os_anon_key": os.environ.get("SUPABASE_ANON_KEY", "NOT SET")[:20],
        "os_svc_key": os.environ.get("SUPABASE_SERVICE_KEY", "NOT SET")[:15],
        "supabase_url": settings.supabase_url[:40],
        "build_v": "2",
    }
