"""Rate limiting middleware using slowapi.

Limits are calibrated for Volaura's scale (free tier Railway, ~$8/mo):
- Auth endpoints: strict (prevent brute force)
- Assessment: moderate (prevent automated testing)
- General API: relaxed (normal usage)

Architecture audit (2026-03-24): Agents flagged in-memory limiter as single-instance
vulnerability (resets on Railway restart). DeepSeek proposed hybrid approach:
in-memory for speed + periodic state awareness. For single-instance Railway,
slowapi is sufficient — Redis or Supabase Edge Functions when scaling to 2+ instances.

See: docs/engineering/SECURITY-STANDARDS.md
"""

import hashlib

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request

from loguru import logger


def _key_func(request: Request) -> str:
    """Rate limit key: IP address + user ID if authenticated.

    Uses IP + truncated token hash for authenticated users.
    This ensures rate limits apply per-user even behind shared IPs.
    """
    ip = get_remote_address(request)
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        # Hash the FULL token, not just prefix — JWT headers share common prefix
        # Security audit P1: auth[7:40] caused collisions across all Supabase users
        token_hash = hashlib.sha256(auth[7:].encode()).hexdigest()[:12]
        return f"{ip}:{token_hash}"
    return ip


limiter = Limiter(key_func=_key_func)


# Rate limit constants — import these in routers
# Auth: strict to prevent brute force (Kimi-K2 flagged: "1000 login attempts in <60s")
RATE_AUTH = "5/minute"
RATE_ASSESSMENT_START = "3/hour"
RATE_ASSESSMENT_ANSWER = "60/hour"
RATE_ASSESSMENT_COMPLETE = "10/hour"
RATE_LLM = "30/hour"
RATE_PROFILE_WRITE = "10/minute"
RATE_DEFAULT = "60/minute"
# Discovery: tighter limit — prevents volunteer enumeration via pagination loop
# Agent review (2026-03-25): 60/min → 10/min (60 reqs @ limit=50 = all 3K users exposed)
RATE_DISCOVERY = "10/minute"


def setup_rate_limiting(app):
    """Attach rate limiter to FastAPI app.

    NOTE (architecture audit 2026-03-24):
    slowapi uses in-memory storage. This is fine for single Railway instance.
    When scaling to 2+ instances, migrate to:
    - Option A: Supabase Edge Function rate limiter ($0, agents' top recommendation)
    - Option B: Redis via Railway add-on (+$5-10/mo)
    - Option C: SQL-based counter in Supabase (DeepSeek innovation, $0, slower)
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    logger.info("Rate limiting enabled (in-memory, single-instance mode)")
