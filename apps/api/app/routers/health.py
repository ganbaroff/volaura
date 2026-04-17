"""Health check endpoint — verifies DB connectivity, not just HTTP alive."""

import os
import re

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from app.config import settings
from app.deps import SupabaseAdmin

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    llm_configured: bool
    supabase_project_ref: str
    openrouter: bool = False
    nvidia: bool = False


def _extract_project_ref(url: str) -> str:
    """Extract Supabase project ref from URL. Returns 'local' for local dev URLs."""
    match = re.search(r"//([a-z0-9]+)\.supabase\.co", url)
    return match.group(1) if match else "local"


@router.get("/health", response_model=HealthResponse)
async def health_check(db: SupabaseAdmin) -> HealthResponse:
    """Real health check: verifies Supabase is reachable and LLM keys are set."""
    db_status = "unknown"

    # Check Supabase connectivity
    try:
        result = await db.table("competencies").select("id", count="exact").limit(1).execute()
        db_status = "connected" if result.count and result.count > 0 else "empty"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        logger.error("Health check DB failure", error=str(e)[:200])

    # Check LLM configuration
    llm_ok = bool(settings.gemini_api_key or settings.vertex_api_key)
    openrouter_set = bool(os.environ.get("OPENROUTER_API_KEY", ""))
    nvidia_set = bool(os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NVIDIA_NIM_KEY", ""))

    status = "ok" if db_status == "connected" and llm_ok else "degraded"

    return HealthResponse(
        status=status,
        version="0.2.0",
        database=db_status,
        llm_configured=llm_ok,
        supabase_project_ref=_extract_project_ref(settings.supabase_url),
        openrouter=openrouter_set,
        nvidia=nvidia_set,
    )


# CRIT-01 FIXED (Session 51 OWASP audit): /health/env-debug DELETED.
# Was exposing partial Supabase keys + URL in production. Unauthenticated.


# anon-key-check DELETED — P0 security: leaked key prefix + infra details unauthenticated.
# Removed 2026-04-15 per ecosystem audit FULL-ECOSYSTEM-AUDIT-2026-04-15.md
