"""Rate limiting middleware using slowapi.

Limits are calibrated for Volaura's scale (free tier Railway, ~$8/mo):
- Auth endpoints: strict (prevent brute force)
- Assessment: moderate (prevent automated testing)
- General API: relaxed (normal usage)

See: docs/engineering/SECURITY-STANDARDS.md
"""

import hashlib

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from loguru import logger


def _key_func(request: Request) -> str:
    """Rate limit key: IP address + user ID if authenticated."""
    ip = get_remote_address(request)
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        # Deterministic hash — consistent across workers
        token_hash = hashlib.sha256(auth[7:40].encode()).hexdigest()[:12]
        return f"{ip}:{token_hash}"
    return ip


limiter = Limiter(key_func=_key_func)


# Rate limit constants — import these in routers
RATE_AUTH = "5/minute"
RATE_ASSESSMENT_START = "3/hour"
RATE_ASSESSMENT_ANSWER = "60/hour"
RATE_LLM = "30/hour"
RATE_PROFILE_WRITE = "10/minute"
RATE_DEFAULT = "60/minute"


def setup_rate_limiting(app):
    """Attach rate limiter to FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled")
