"""Cross-product bridge — fire-and-forget Volaura → MindShift event push.

Responsibilities:
  - Push crystal_earned / skill_verified events to MindShift API after assessment
  - Never blocks the main request — all errors caught and logged
  - Uses the user's own Supabase JWT (passed from the request) so MindShift
    can verify the event came from a legitimate authenticated Volaura user
  - No-ops gracefully when MINDSHIFT_URL env var is not set (local dev / staging)

Design decisions:
  - httpx.AsyncClient with short timeouts (connect=3s, read=8s) — never starves the API
  - Retry: 0 retries — if MindShift is down, the crystal_earned event is still persisted
    locally in character_events. MindShift can poll GET /api/character/events to catch up.
  - Auth: Bearer token from the user's JWT — one JWT across the ecosystem (ADR-007)
  - Circuit breaker: simple in-memory flag; after 3 consecutive failures within 5 minutes,
    bridge goes silent for 60 seconds to avoid log spam.

Usage (in assessment router, after emit_assessment_rewards):
    from app.services.cross_product_bridge import push_crystal_earned, push_skill_verified

    await push_crystal_earned(user_id, amount=50, skill_slug="communication",
                               user_jwt=bearer_token)
    await push_skill_verified(user_id, skill_slug="communication",
                               badge_tier="gold", aura_score=78.5,
                               user_jwt=bearer_token)
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx
from loguru import logger

from app.config import settings

# ── Circuit breaker state (module-level, in-memory) ───────────────────────────
_cb_failures: int = 0
_cb_window_start: float = 0.0
_cb_silenced_until: float = 0.0
_CB_THRESHOLD = 3          # failures before silence
_CB_WINDOW_SEC = 300       # 5-minute sliding window
_CB_SILENCE_SEC = 60       # 60-second backoff

# ── HTTP timeouts ─────────────────────────────────────────────────────────────
_TIMEOUT = httpx.Timeout(connect=3.0, read=8.0, write=5.0, pool=2.0)


def _mindshift_url() -> str | None:
    """Return MindShift base URL from settings, or None if not configured."""
    url = settings.mindshift_url
    return url.rstrip("/") if url else None


def _is_circuit_open() -> bool:
    """True if circuit breaker is currently suppressing calls."""
    global _cb_silenced_until
    now = time.monotonic()
    if now < _cb_silenced_until:
        return True
    return False


def _record_failure() -> None:
    """Track a failure; trip the circuit breaker at threshold."""
    global _cb_failures, _cb_window_start, _cb_silenced_until
    now = time.monotonic()
    if now - _cb_window_start > _CB_WINDOW_SEC:
        # Reset window
        _cb_failures = 0
        _cb_window_start = now
    _cb_failures += 1
    if _cb_failures >= _CB_THRESHOLD:
        _cb_silenced_until = now + _CB_SILENCE_SEC
        logger.warning(
            "CrossProductBridge: circuit breaker tripped — silencing for {}s "
            "after {} failures in {}s window",
            _CB_SILENCE_SEC, _cb_failures, _CB_WINDOW_SEC,
        )


def _record_success() -> None:
    """Reset failure counter on success."""
    global _cb_failures, _cb_window_start
    _cb_failures = 0
    _cb_window_start = 0.0


async def _post_event(
    endpoint: str,
    payload: dict[str, Any],
    user_jwt: str | None,
) -> bool:
    """POST a single event to MindShift. Returns True on 2xx, False otherwise."""
    base = _mindshift_url()
    if not base:
        logger.debug("CrossProductBridge: MINDSHIFT_URL not set — skipping push")
        return True  # Not a failure — just unconfigured

    if _is_circuit_open():
        logger.debug("CrossProductBridge: circuit open — skipping push to {}", endpoint)
        return False

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if user_jwt:
        headers["Authorization"] = f"Bearer {user_jwt}"

    url = f"{base}{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code < 300:
            _record_success()
            logger.debug(
                "CrossProductBridge: pushed to {} — {}",
                endpoint, resp.status_code,
            )
            return True
        else:
            _record_failure()
            logger.warning(
                "CrossProductBridge: {} returned {} — {}",
                endpoint, resp.status_code, resp.text[:200],
            )
            return False
    except httpx.TimeoutException:
        _record_failure()
        logger.warning("CrossProductBridge: timeout pushing to {}", endpoint)
        return False
    except Exception as exc:
        _record_failure()
        logger.warning("CrossProductBridge: error pushing to {} — {}", endpoint, str(exc))
        return False


# ── Public API ────────────────────────────────────────────────────────────────

async def push_crystal_earned(
    user_id: str,
    amount: int,
    skill_slug: str,
    user_jwt: str | None = None,
) -> None:
    """Fire-and-forget: notify MindShift that the user earned crystals on Volaura.

    MindShift shows a crystal counter in its focus session overlay.
    If MindShift is unreachable, this is a no-op — crystals are already persisted
    locally in character_events via emit_assessment_rewards().

    Args:
        user_id:    Supabase user UUID
        amount:     Crystal amount earned (positive int)
        skill_slug: Competency slug that triggered the reward
        user_jwt:   User's Supabase JWT (for cross-product auth)
    """
    payload = {
        "event_type": "crystal_earned",
        "source_product": "volaura",
        "user_id": user_id,
        "payload": {
            "amount": amount,
            "skill_slug": skill_slug,
            "reason": "assessment_completion",
            "_schema_version": 1,
        },
    }
    # Fire-and-forget — caller never awaits a result
    asyncio.ensure_future(
        _post_event("/api/character/events", payload, user_jwt)
    )
    logger.debug(
        "CrossProductBridge: queued crystal_earned push — user={} amount={} skill={}",
        user_id, amount, skill_slug,
    )


async def push_skill_verified(
    user_id: str,
    skill_slug: str,
    badge_tier: str | None,
    aura_score: float,
    user_jwt: str | None = None,
) -> None:
    """Fire-and-forget: notify MindShift that the user's skill was verified on Volaura.

    MindShift can surface this as a character milestone (e.g. "Communication: Gold").
    Fails silently — the verification is already persisted locally.

    Args:
        user_id:    Supabase user UUID
        skill_slug: Competency slug (e.g. "communication")
        badge_tier: Badge tier earned ("bronze"/"silver"/"gold"/"platinum" or None)
        aura_score: Raw competency score (0–100)
        user_jwt:   User's Supabase JWT (for cross-product auth)
    """
    payload = {
        "event_type": "skill_verified",
        "source_product": "volaura",
        "user_id": user_id,
        "payload": {
            "skill_slug": skill_slug,
            "badge_tier": badge_tier,
            "aura_score": round(aura_score, 2),
            "reason": "assessment_completion",
            "_schema_version": 1,
        },
    }
    asyncio.ensure_future(
        _post_event("/api/character/events", payload, user_jwt)
    )
    logger.debug(
        "CrossProductBridge: queued skill_verified push — user={} skill={} tier={}",
        user_id, skill_slug, badge_tier,
    )


async def push_xp_earned(
    user_id: str,
    amount: int,
    reason: str,
    user_jwt: str | None = None,
) -> None:
    """Fire-and-forget: notify MindShift of an XP event originating in Volaura.

    Currently unused — reserved for future gamification (e.g. profile completion XP).

    Args:
        user_id:  Supabase user UUID
        amount:   XP amount (positive int)
        reason:   Human-readable reason slug (e.g. "profile_complete", "first_assessment")
        user_jwt: User's Supabase JWT
    """
    payload = {
        "event_type": "xp_earned",
        "source_product": "volaura",
        "user_id": user_id,
        "payload": {
            "amount": amount,
            "reason": reason,
            "_schema_version": 1,
        },
    }
    asyncio.ensure_future(
        _post_event("/api/character/events", payload, user_jwt)
    )
    logger.debug(
        "CrossProductBridge: queued xp_earned push — user={} amount={} reason={}",
        user_id, amount, reason,
    )


def reset_circuit_breaker() -> None:
    """Reset circuit breaker state — for testing only."""
    global _cb_failures, _cb_window_start, _cb_silenced_until
    _cb_failures = 0
    _cb_window_start = 0.0
    _cb_silenced_until = 0.0
