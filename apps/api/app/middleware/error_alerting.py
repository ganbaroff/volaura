"""Error alerting — sends 5xx errors to CEO Telegram.

Fires on any 500+ response. Rate-limited to max 1 alert per 5 minutes
to prevent Telegram spam during cascading failures.
"""

import time

import httpx
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

_ALERT_COOLDOWN = 300  # 5 minutes between alerts
_last_alert_time: float = 0


async def _send_telegram_alert(status_code: int, path: str, method: str) -> None:
    """Send error alert to CEO Telegram. Fire-and-forget.

    HARD KILL-SWITCH (2026-04-19) — CEO reported 100+ Telegram alerts/day and
    three silence-gate iterations (PR #18 gate, PR #19 cron disable, PR #20
    full cron/push sweep, PR #21 Dockerfile gate-ship) didn't get him to zero
    fast enough. Short-circuiting here at the function boundary guarantees
    zero sends regardless of gate import state, silence-file presence, or
    cooldown timing. Remove this early-return after CEO explicitly says
    'unlock telegram alerts' — until then this path is dead code.
    """
    return

    global _last_alert_time

    now = time.time()
    if now - _last_alert_time < _ALERT_COOLDOWN:
        return  # Cooldown — don't spam

    token = settings.telegram_bot_token
    chat_id = settings.telegram_ceo_chat_id
    if not token or not chat_id:
        return  # Not configured

    # Central telegram-gate (2026-04-19 spam kill): global rate-limit, dedup,
    # kill-switch. Bypasses don't bypass the gate.
    try:
        from packages.swarm.telegram_gate import allow_send as _gate_allow

        preview = f"5xx alert {method} {path} status={status_code}"
        if not _gate_allow(category="error", severity="error", preview=preview):
            return
    except ImportError:
        pass  # gate unavailable in some contexts — fall through to local cooldown only

    _last_alert_time = now

    text = (
        f"🚨 *VOLAURA API Error*\n\n"
        f"Status: `{status_code}`\n"
        f"Endpoint: `{method} {path}`\n"
        f"Time: `{time.strftime('%H:%M:%S UTC', time.gmtime())}`\n\n"
        f"Check Railway logs."
    )

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            )
    except Exception as e:
        logger.warning("Failed to send Telegram error alert", error=str(e)[:100])


class ErrorAlertingMiddleware(BaseHTTPMiddleware):
    """Middleware that alerts on 5xx responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        if response.status_code >= 500:
            logger.error(
                "5xx response",
                status=response.status_code,
                path=request.url.path,
                method=request.method,
            )
            # Fire-and-forget — don't block the response
            try:
                await _send_telegram_alert(
                    response.status_code,
                    request.url.path,
                    request.method,
                )
            except Exception:
                pass  # Alert failure must never break the API

        return response
