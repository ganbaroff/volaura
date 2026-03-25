"""Telegram Webhook — MiroFish Swarm Ambassador.

Receives Telegram updates via webhook (not polling).
Routes commands and free-text to appropriate handlers.
Only responds to CEO (TELEGRAM_CEO_CHAT_ID).

Setup: POST /api/telegram/setup-webhook to register with Telegram API.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# Paths for state
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
_PROPOSALS_PATH = _PROJECT_ROOT / "memory" / "swarm" / "proposals.json"
_CONTEXT_PATH = _PROJECT_ROOT / "memory" / "swarm" / "ambassador_context.json"
_SPRINT_STATE_PATH = _PROJECT_ROOT / "memory" / "context" / "sprint-state.md"


# ── Helpers ──────────────────────────────────────────────────────────────────

def _load_proposals() -> list[dict]:
    if not _PROPOSALS_PATH.exists():
        return []
    try:
        with open(_PROPOSALS_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("proposals", [])
    except Exception:
        return []


def _get_pending() -> list[dict]:
    return [p for p in _load_proposals() if p.get("status") == "pending"]


def _update_proposal(pid: str, status: str) -> str | None:
    if not _PROPOSALS_PATH.exists():
        return None
    with open(_PROPOSALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    for p in data.get("proposals", []):
        if p.get("id") == pid:
            p["status"] = status
            p["resolved_at"] = datetime.now(timezone.utc).isoformat()
            with open(_PROPOSALS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return p.get("title")
    return None


def _sprint_summary() -> str:
    if not _SPRINT_STATE_PATH.exists():
        return "Sprint state not found."
    try:
        with open(_SPRINT_STATE_PATH, "r", encoding="utf-8") as f:
            return "".join(f.readlines()[:15])
    except Exception:
        return "Error reading sprint state."


def _load_context() -> dict:
    if _CONTEXT_PATH.exists():
        try:
            with open(_CONTEXT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"messages": []}


def _save_context(ctx: dict) -> None:
    ctx["messages"] = ctx["messages"][-20:]
    _CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_CONTEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)


async def _send_message(chat_id: int | str, text: str) -> None:
    """Send a Telegram message via Bot API."""
    import httpx
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        })


async def _ask_llm(question: str, history: list[dict]) -> str:
    """Ask Gemini for a smart response as the swarm ambassador."""
    sprint = _sprint_summary()
    pending = _get_pending()

    system_prompt = f"""You are the MiroFish Swarm Ambassador — one voice for a 14-model AI agent team.
You report to CEO Yusif Ganbarov via Telegram. Be concise, direct, honest.
Speak as "мы" (the team). Keep responses under 400 chars. Use Russian.

Sprint state:
{sprint[:500]}

Pending proposals: {len(pending)}"""

    if not settings.gemini_api_key:
        return "LLM не настроен — нужен GEMINI_API_KEY."

    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=question,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=250,
                temperature=0.7,
            ),
        )
        return response.text.strip()
    except Exception as e:
        logger.error("Ambassador LLM error: {e}", e=str(e))
        return f"Ошибка LLM: не могу ответить сейчас."


# ── Webhook Endpoint ─────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    """Receive Telegram update via webhook."""
    if not settings.telegram_bot_token:
        return JSONResponse({"ok": False, "error": "Bot not configured"})

    # BLOCKER-2 FIX: Validate webhook origin via secret token header
    # Telegram sends X-Telegram-Bot-Api-Secret-Token if set during setWebhook
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if settings.telegram_webhook_secret and secret_header != settings.telegram_webhook_secret:
        logger.warning("Telegram webhook: invalid secret token from {ip}", ip=request.client.host if request.client else "?")
        return JSONResponse({"ok": False}, status_code=403)

    try:
        update = await request.json()
    except Exception:
        return JSONResponse({"ok": False})

    message = update.get("message")
    if not message:
        return JSONResponse({"ok": True})

    chat_id = message.get("chat", {}).get("id")
    user_id = message.get("from", {}).get("id")
    text = message.get("text", "").strip()

    # Only respond to CEO
    ceo_id = settings.telegram_ceo_chat_id
    if ceo_id and str(user_id) != str(ceo_id):
        logger.info("Telegram: ignoring message from non-CEO user {uid}", uid=user_id)
        return JSONResponse({"ok": True})

    if not text:
        return JSONResponse({"ok": True})

    logger.info("Telegram from CEO: {text}", text=text[:100])

    # Route commands
    if text.startswith("/status"):
        pending = _get_pending()
        sprint_lines = [l.strip() for l in _sprint_summary().split("\n") if l.strip()][:5]
        msg = f"🔮 *Swarm Status*\n\n📋 Pending: {len(pending)}\n"
        if pending:
            for p in pending[:3]:
                sev = p.get("severity", "medium").upper()
                msg += f"  [{sev}] {p.get('title', '?')}\n"
        msg += f"\n📍 Sprint:\n" + "\n".join(sprint_lines)
        await _send_message(chat_id, msg)

    elif text.startswith("/proposals"):
        pending = _get_pending()
        if not pending:
            await _send_message(chat_id, "✅ Нет pending proposals.")
        else:
            for p in pending[:5]:
                msg = f"📌 *{p.get('title', '?')}*\n"
                msg += f"Agent: {p.get('agent', '?')} | {p.get('severity', '?').upper()}\n"
                msg += f"{p.get('description', '')[:200]}\n"
                msg += f"\n/approve\\_{p.get('id', '?')} | /dismiss\\_{p.get('id', '?')}"
                await _send_message(chat_id, msg)

    elif text.startswith("/approve"):
        pid = text.replace("/approve", "").replace("_", "").strip()
        if not pid:
            await _send_message(chat_id, "Usage: /approve <id>")
        else:
            title = _update_proposal(pid, "approved")
            if title:
                await _send_message(chat_id, f"✅ Approved: {title}")
            else:
                await _send_message(chat_id, f"❌ Proposal {pid} not found.")

    elif text.startswith("/dismiss"):
        pid = text.replace("/dismiss", "").replace("_", "").strip()
        if not pid:
            await _send_message(chat_id, "Usage: /dismiss <id>")
        else:
            title = _update_proposal(pid, "dismissed")
            if title:
                await _send_message(chat_id, f"🗑 Dismissed: {title}")
            else:
                await _send_message(chat_id, f"❌ Proposal {pid} not found.")

    else:
        # Free-text → LLM response
        ctx = _load_context()
        ctx["messages"].append({"role": "user", "text": text})
        response = await _ask_llm(text, ctx["messages"])
        ctx["messages"].append({"role": "assistant", "text": response})
        _save_context(ctx)
        await _send_message(chat_id, response)

    return JSONResponse({"ok": True})


# ── Setup Webhook ────────────────────────────────────────────────────────────

@router.post("/setup-webhook")
async def setup_webhook(request: Request) -> JSONResponse:
    """Register the webhook URL with Telegram API. Call once after deploy."""
    if not settings.telegram_bot_token:
        return JSONResponse({"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"})

    # Derive webhook URL from Railway production URL
    api_url = settings.app_url.replace("localhost:3000", "volauraapi-production.up.railway.app")
    if "railway" not in api_url and "localhost" not in api_url:
        api_url = "https://volauraapi-production.up.railway.app"

    webhook_url = f"{api_url}/api/telegram/webhook"

    import httpx
    payload: dict = {"url": webhook_url}
    # BLOCKER-2 FIX: Include secret token so Telegram sends it in X-Telegram-Bot-Api-Secret-Token header
    if settings.telegram_webhook_secret:
        payload["secret_token"] = settings.telegram_webhook_secret
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook",
            json=payload,
        )
        result = resp.json()

    logger.info("Telegram webhook setup: {url} → {result}", url=webhook_url, result=result)
    return JSONResponse(result)
