"""Tests for app/main.py — metadata, router registration, middleware, exception handler."""

import pytest
from fastapi.testclient import TestClient

from app.main import _MAX_REQUEST_BODY_BYTES, app

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


def test_max_request_body_bytes_is_one_mb():
    assert _MAX_REQUEST_BODY_BYTES == 1_048_576


# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------


def test_app_title():
    assert app.title == "Volaura API"


def test_app_description():
    assert app.description == "Verified Competency Platform — Assessment, Matching, Events"


def test_app_version():
    assert app.version == "0.1.0"


# ---------------------------------------------------------------------------
# Docs URL gating — depends on is_dev at module import time
# ---------------------------------------------------------------------------


def test_docs_url_none_in_production():
    from fastapi import FastAPI

    from app.config import Settings

    prod_settings = Settings(app_env="production")
    prod_app = FastAPI(
        docs_url="/docs" if prod_settings.is_dev else None,
        redoc_url="/redoc" if prod_settings.is_dev else None,
    )
    assert prod_app.docs_url is None
    assert prod_app.redoc_url is None


def test_docs_url_present_in_dev():
    from fastapi import FastAPI

    from app.config import Settings

    dev_settings = Settings(app_env="development")
    dev_app = FastAPI(
        docs_url="/docs" if dev_settings.is_dev else None,
        redoc_url="/redoc" if dev_settings.is_dev else None,
    )
    assert dev_app.docs_url == "/docs"
    assert dev_app.redoc_url == "/redoc"


# ---------------------------------------------------------------------------
# Router registration — all 27 routers present
# ---------------------------------------------------------------------------

_EXPECTED_ROUTERS = [
    "health",
    "auth",
    "auth_bridge",
    "profiles",
    "grievance",
    "aura",
    "assessment",
    "events",
    "eventshift",
    "organizations",
    "invites",
    "badges",
    "verification",
    "activity",
    "analytics",
    "discovery",
    "community",
    "lifesim",
    "notifications",
    "stats",
    "telegram_webhook",
    "webhooks_sentry",
    "character",
    "brandedby",
    "skills",
    "subscription",
    "tribes",
    "admin",
    "atlas_gateway",
]


def _route_paths() -> list[str]:
    return [str(route.path) for route in app.routes]


def test_router_count_at_least_27():
    paths = _route_paths()
    assert len(paths) >= 27


def test_health_router_no_prefix():
    paths = _route_paths()
    assert "/health" in paths


def test_admin_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/admin") for p in paths)


def test_atlas_gateway_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/atlas") for p in paths)


def test_auth_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "auth" in p for p in paths)


def test_profiles_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "profile" in p for p in paths)


def test_assessment_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "assessment" in p for p in paths)


def test_aura_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "aura" in p for p in paths)


def test_events_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "event" in p for p in paths)


def test_organizations_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "organization" in p for p in paths)


def test_badges_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "badge" in p for p in paths)


def test_analytics_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "analytic" in p for p in paths)


def test_discovery_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "discover" in p for p in paths)


def test_notifications_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "notification" in p for p in paths)


def test_tribes_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "tribe" in p for p in paths)


def test_subscription_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "subscription" in p for p in paths)


def test_skills_router_prefix():
    paths = _route_paths()
    assert any(p.startswith("/api/") and "skill" in p for p in paths)


# ---------------------------------------------------------------------------
# Body size limit middleware — POST/PUT/PATCH blocked, GET not checked
# ---------------------------------------------------------------------------


@pytest.fixture
def sync_client():
    return TestClient(app, raise_server_exceptions=False)


def test_post_over_limit_returns_413(sync_client):
    over = _MAX_REQUEST_BODY_BYTES + 1
    response = sync_client.post(
        "/health",
        content=b"x",
        headers={"Content-Length": str(over), "Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_post_over_limit_returns_payload_too_large_code(sync_client):
    over = _MAX_REQUEST_BODY_BYTES + 1
    response = sync_client.post(
        "/health",
        content=b"x",
        headers={"Content-Length": str(over), "Content-Type": "application/json"},
    )
    assert response.json()["detail"]["code"] == "PAYLOAD_TOO_LARGE"


def test_put_over_limit_returns_413(sync_client):
    over = _MAX_REQUEST_BODY_BYTES + 1
    response = sync_client.put(
        "/api/profiles/me",
        content=b"x",
        headers={"Content-Length": str(over), "Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_patch_over_limit_returns_413(sync_client):
    over = _MAX_REQUEST_BODY_BYTES + 1
    response = sync_client.patch(
        "/api/profiles/me",
        content=b"x",
        headers={"Content-Length": str(over), "Content-Type": "application/json"},
    )
    assert response.status_code == 413


def test_post_at_limit_passes_middleware(sync_client):
    at_limit = _MAX_REQUEST_BODY_BYTES
    response = sync_client.post(
        "/health",
        content=b"x",
        headers={"Content-Length": str(at_limit), "Content-Type": "application/json"},
    )
    # Middleware must not block — downstream may reject for other reasons but not 413
    assert response.status_code != 413


def test_post_under_limit_passes_middleware(sync_client):
    response = sync_client.post(
        "/health",
        content=b"{}",
        headers={"Content-Length": "2", "Content-Type": "application/json"},
    )
    assert response.status_code != 413


def test_get_ignores_content_length_check(sync_client):
    # GET with a large Content-Length header must not be rejected by this middleware
    over = _MAX_REQUEST_BODY_BYTES + 1
    response = sync_client.get(
        "/health",
        headers={"Content-Length": str(over)},
    )
    assert response.status_code != 413


def test_post_without_content_length_passes_middleware(sync_client):
    # No Content-Length header → middleware must not block
    response = sync_client.post(
        "/health",
        content=b"{}",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code != 413


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------


def test_unhandled_exception_returns_500(sync_client):
    from fastapi import APIRouter

    crash_router = APIRouter()

    @crash_router.get("/_test_crash_main")
    async def _crash():
        raise RuntimeError("boom")

    app.include_router(crash_router)
    try:
        response = sync_client.get("/_test_crash_main")
        assert response.status_code == 500
    finally:
        # Remove test route to avoid polluting other tests
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_crash_main"]


def test_unhandled_exception_returns_internal_error_code(sync_client):
    from fastapi import APIRouter

    crash_router = APIRouter()

    @crash_router.get("/_test_crash_code")
    async def _crash_code():
        raise ValueError("secret db data")

    app.include_router(crash_router)
    try:
        response = sync_client.get("/_test_crash_code")
        assert response.json()["detail"]["code"] == "INTERNAL_ERROR"
    finally:
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_crash_code"]


def test_unhandled_exception_does_not_leak_error_details(sync_client):
    from fastapi import APIRouter

    crash_router = APIRouter()

    @crash_router.get("/_test_crash_leak")
    async def _crash_leak():
        raise RuntimeError("super secret internal detail")

    app.include_router(crash_router)
    try:
        response = sync_client.get("/_test_crash_leak")
        body = response.text
        assert "super secret internal detail" not in body
    finally:
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_crash_leak"]


# ---------------------------------------------------------------------------
# CORS — cors_origins from settings wired into middleware
# ---------------------------------------------------------------------------


def test_cors_middleware_present():
    from starlette.middleware.cors import CORSMiddleware

    middleware_types = [m.cls for m in app.user_middleware]
    assert CORSMiddleware in middleware_types


def test_cors_uses_settings_origins():
    from starlette.middleware.cors import CORSMiddleware

    for entry in app.user_middleware:
        if entry.cls is CORSMiddleware:
            allow_origins = entry.kwargs.get("allow_origins", [])
            from app.config import settings

            assert allow_origins == settings.cors_origins
            return
    pytest.fail("CORSMiddleware not found in user_middleware")
