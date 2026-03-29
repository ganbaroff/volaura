"""Health check endpoint — verifies DB connectivity, not just HTTP alive."""

from fastapi import APIRouter
from loguru import logger
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    llm_configured: bool


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Real health check: verifies Supabase is reachable and LLM keys are set."""
    db_status = "unknown"

    # Check Supabase connectivity
    try:
        from supabase._async.client import AsyncClient, create_client as acreate_client

        client: AsyncClient = await acreate_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.effective_anon_key,
        )
        result = await client.table("competencies").select("id", count="exact").limit(1).execute()
        db_status = "connected" if result.count and result.count > 0 else "empty"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        logger.error("Health check DB failure", error=str(e)[:200])

    # Check LLM configuration
    llm_ok = bool(settings.gemini_api_key)

    status = "ok" if db_status == "connected" and llm_ok else "degraded"

    return HealthResponse(
        status=status,
        version="0.1.0",
        database=db_status,
        llm_configured=llm_ok,
    )


# CRIT-01 FIXED (Session 51 OWASP audit): /health/env-debug DELETED.
# Was exposing partial Supabase keys + URL in production. Unauthenticated.
