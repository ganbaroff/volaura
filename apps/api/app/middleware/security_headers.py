"""Security headers middleware.

Adds standard security headers to all responses:
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security (HSTS) in production
- Content-Security-Policy: strict policy (API returns JSON, no scripts needed)

Hardened after architecture audit (2026-03-24, 18 agents).
Agent concern (Kimi-K2-0905): "No CSP + LLM-evaluated answers = prompt-injection XSS".
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# CSP for API: JSON responses only, no scripts/styles/images needed.
# This blocks any XSS payload that might leak through LLM-evaluated content.
_CSP_PRODUCTION = "; ".join([
    "default-src 'none'",
    "frame-ancestors 'none'",
    "base-uri 'none'",
    "form-action 'none'",
])


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"  # Disabled: CSP is the real protection
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        if not settings.is_dev:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )
            response.headers["Content-Security-Policy"] = _CSP_PRODUCTION

        return response
