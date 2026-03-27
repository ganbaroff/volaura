"""Volaura API — Verified Competency Platform.

Security hardening applied:
- JWT verification via admin.auth.get_user() (not anon key)
- Rate limiting per IP + user (slowapi)
- CORS whitelist (no wildcards in production)
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Structured error responses on all endpoints
"""

import asyncio
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

import sentry_sdk

from app.config import settings, validate_production_settings
from app.middleware.rate_limit import setup_rate_limiting

# Sentry error monitoring — silent if DSN not set
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=0.1,
    )
    logger.info("Sentry monitoring enabled")

from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import activity, assessment, auth, aura, badges, character, discovery, events, health, invites, leaderboard, organizations, profiles, stats, telegram_webhook, verification
from app.services.reeval_worker import run_reeval_worker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    logger.info("Volaura API starting up...")
    logger.info("Environment: {env}", env=settings.app_env)
    # Validate production-critical settings
    for warning in validate_production_settings():
        logger.warning(warning)

    # Start async re-evaluation worker (ADR-010: keyword_fallback → LLM upgrade queue)
    reeval_task = asyncio.create_task(run_reeval_worker(), name="reeval_worker")

    yield

    # Graceful shutdown: cancel background worker and wait for it to stop
    reeval_task.cancel()
    try:
        await asyncio.wait_for(asyncio.shield(reeval_task), timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass
    logger.info("Volaura API shutting down...")


app = FastAPI(
    title="Volaura API",
    description="Verified Competency Platform — Assessment, Matching, Events",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_dev else None,
    redoc_url="/redoc" if settings.is_dev else None,
)

# Security: Rate limiting
setup_rate_limiting(app)

# Security: Headers (HSTS, CSP, X-Frame-Options, etc.)
app.add_middleware(SecurityHeadersMiddleware)

# CORS — whitelist only, no wildcards in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Accept-Language"],
)

# CRIT-01 fix: catch unhandled exceptions — never leak DB/internal errors to client
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return generic 500 for any unhandled exception. Log the real error server-side."""
    logger.error(
        "Unhandled exception on {method} {path}: {error}",
        method=request.method,
        path=request.url.path,
        error=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"detail": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}},
    )


# Routers
app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(aura.router, prefix="/api")
app.include_router(assessment.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(invites.router, prefix="/api")
app.include_router(badges.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
app.include_router(discovery.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(telegram_webhook.router, prefix="/api")
app.include_router(character.router, prefix="/api")
