"""Volaura API — Verified Competency Platform.

Security hardening applied:
- JWT verification via admin.auth.get_user() (not anon key)
- Rate limiting per IP + user (slowapi)
- CORS whitelist (no wildcards in production)
- Security headers (HSTS, CSP, X-Frame-Options, etc.)
- Structured error responses on all endpoints
"""

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings, validate_production_settings
from app.middleware.rate_limit import setup_rate_limiting
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import activity, assessment, auth, aura, badges, events, health, organizations, profiles, verification


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan — startup and shutdown events."""
    logger.info("Volaura API starting up...")
    logger.info("Environment: {env}", env=settings.app_env)
    # Validate production-critical settings
    for warning in validate_production_settings():
        logger.warning(warning)
    yield
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
app.include_router(badges.router, prefix="/api")
app.include_router(verification.router, prefix="/api")
app.include_router(activity.router, prefix="/api")
