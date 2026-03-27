"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="0.1.0")

# CRIT-01 FIXED (Session 51 OWASP audit): /health/env-debug DELETED.
# Was exposing partial Supabase keys + URL in production. Unauthenticated.
