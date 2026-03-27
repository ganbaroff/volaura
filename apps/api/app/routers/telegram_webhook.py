"""Telegram Webhook — Volaura Product Owner Bot.

Receives CEO messages via Telegram webhook.
Acts as Product Owner: saves ideas, delegates tasks, writes reports, manages backlog.
Uses Supabase DB for state (not local files — Railway filesystem is ephemeral).

Setup: POST /api/telegram/setup-webhook to register with Telegram API.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import settings

router = APIRouter(prefix="/telegram", tags=["Telegram"])


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_db():
    """Get admin Supabase client for bot operations."""
    from supabase._async.client import AsyncClient, acreate_client
    return await acreate_client(settings.supabase_url, settings.supabase_service_key)


async def _send_message(chat_id: int | str, text: str) -> bool:
    """Send a Telegram message via Bot API. Returns True on success."""
    import httpx
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    # Telegram max message length is 4096
    if len(text) > 4000:
        text = text[:4000] + "\n\n... (обрезано)"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            })
            if not resp.json().get("ok"):
                # Retry without markdown if parse fails
                await client.post(url, json={
                    "chat_id": chat_id,
                    "text": text,
                })
            return True
    except Exception as e:
        logger.error("Telegram send failed: {e}", e=str(e))
        return False


async def _save_message(db, direction: str, message: str, msg_type: str = "free_text", metadata: dict | None = None):
    """Save message to ceo_inbox table."""
    try:
        await db.table("ceo_inbox").insert({
            "direction": direction,
            "message": message[:5000],
            "message_type": msg_type,
            "metadata": metadata or {},
        }).execute()
    except Exception as e:
        logger.error("Failed to save message: {e}", e=str(e))


async def _get_recent_context(db, limit: int = 10) -> str:
    """Get recent conversation context from DB."""
    try:
        result = await db.table("ceo_inbox").select("direction,message,message_type,created_at").order("created_at", desc=True).limit(limit).execute()
        if not result.data:
            return "Нет предыдущих сообщений."
        lines = []
        for msg in reversed(result.data):
            role = "CEO" if msg["direction"] == "ceo_to_bot" else "Bot"
            lines.append(f"[{role}] {msg['message'][:200]}")
        return "\n".join(lines)
    except Exception:
        return "Контекст недоступен."


async def _get_project_stats(db) -> str:
    """Get quick project stats from DB."""
    try:
        scores = await db.table("aura_scores").select("*", count="exact").execute()
        sessions = await db.table("assessment_sessions").select("*", count="exact").execute()
        orgs = await db.table("organizations").select("*", count="exact").execute()
        return (
            f"Users with AURA: {scores.count or 0}\n"
            f"Assessment sessions: {sessions.count or 0}\n"
            f"Organizations: {orgs.count or 0}"
        )
    except Exception:
        return "Статистика недоступна."


async def _classify_and_respond(db, text: str, chat_id: int | str) -> None:
    """Classify CEO message and respond intelligently as Product Owner."""
    context = await _get_recent_context(db)
    stats = await _get_project_stats(db)

    # Detect intent
    text_lower = text.lower()
    is_idea = any(w in text_lower for w in ["идея", "idea", "можно сделать", "а что если", "предлагаю", "надо бы"])
    is_task = any(w in text_lower for w in ["сделай", "задача", "task", "нужно", "исправь", "fix", "добавь", "add"])
    is_question = "?" in text
    is_report = any(w in text_lower for w in ["отчёт", "report", "статус", "status", "что сделано", "прогресс"])

    if is_idea:
        msg_type = "idea"
    elif is_task:
        msg_type = "task"
    elif is_report:
        msg_type = "report"
    else:
        msg_type = "free_text"

    # Save CEO message
    await _save_message(db, "ceo_to_bot", text, msg_type)

    # Build response via Gemini
    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен. Сообщение сохранено в базу.")
        return

    system_prompt = f"""Ты — Product Owner бот команды Volaura. Говоришь от имени команды ("мы").
Отвечаешь CEO Юсифу Ганбарову в Telegram. Коротко, по делу, на русском.

Твои обязанности:
1. ИДЕИ — если CEO делится идеей, подтверди что записал, кратко оцени (сильно/слабо/надо подумать), скажи что передашь команде
2. ЗАДАЧИ — если CEO даёт задачу, подтверди, скажи ориентировочный срок, спроси если что-то неясно
3. ОТЧЁТЫ — если спрашивает статус, дай краткую сводку из данных ниже
4. ВОПРОСЫ — отвечай честно, если не знаешь — скажи прямо

Статистика проекта:
{stats}

Последние сообщения:
{context[-1000:]}

Тип сообщения CEO: {msg_type}

ПРАВИЛА:
- Максимум 300 символов в ответе
- Не льсти. Не используй слова "отличная идея" — скажи что думаешь честно
- Если идея слабая — скажи мягко но прямо
- Если задача непонятная — спроси уточнение
- Всегда заканчивай: что делаем дальше / что передам команде"""

    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=200,
                temperature=0.5,
            ),
        )
        reply = response.text.strip()
    except Exception as e:
        logger.error("Gemini error in bot: {e}", e=str(e))
        reply = f"Сообщение сохранено ✅\nТип: {msg_type}\nОтвечу когда LLM будет доступен."

    # Add tag for saved items
    if msg_type == "idea":
        reply = f"💡 Идея записана в бэклог.\n\n{reply}"
    elif msg_type == "task":
        reply = f"📋 Задача записана.\n\n{reply}"

    # Save bot response
    await _save_message(db, "bot_to_ceo", reply, msg_type)
    await _send_message(chat_id, reply)


# ── Commands ─────────────────────────────────────────────────────────────────

async def _handle_status(db, chat_id: int | str) -> None:
    stats = await _get_project_stats(db)
    # Count unprocessed messages
    try:
        unprocessed = await db.table("ceo_inbox").select("*", count="exact").eq("direction", "ceo_to_bot").eq("processed", False).execute()
        pending_count = unprocessed.count or 0
    except Exception:
        pending_count = 0

    msg = f"🔮 *Volaura Status*\n\n{stats}\n\n📬 Необработанных сообщений: {pending_count}"
    await _send_message(chat_id, msg)


async def _handle_backlog(db, chat_id: int | str) -> None:
    """Show recent ideas and tasks from CEO."""
    try:
        ideas = await db.table("ceo_inbox").select("message,created_at").eq("direction", "ceo_to_bot").in_("message_type", ["idea", "task"]).order("created_at", desc=True).limit(5).execute()
        if not ideas.data:
            await _send_message(chat_id, "📋 Бэклог пуст.")
            return
        msg = "📋 *Последние идеи/задачи CEO:*\n\n"
        for i, item in enumerate(ideas.data, 1):
            ts = item["created_at"][:10]
            msg += f"{i}. [{ts}] {item['message'][:100]}\n"
        await _send_message(chat_id, msg)
    except Exception as e:
        await _send_message(chat_id, f"Ошибка чтения бэклога: {str(e)[:100]}")


async def _handle_proposals(db, chat_id: int | str) -> None:
    """Show latest swarm proposals for CEO to act on."""
    import json as _json
    proposals_path = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"
    try:
        if not proposals_path.exists():
            await _send_message(chat_id, "📭 Нет активных proposals.")
            return
        with open(proposals_path, "r", encoding="utf-8") as f:
            data = _json.load(f)

        pending = [p for p in data.get("proposals", []) if p.get("status") == "pending"]
        if not pending:
            await _send_message(chat_id, "✅ Все proposals обработаны.")
            return

        msg = f"📋 *Pending Proposals ({len(pending)}):*\n\n"
        for p in pending[:5]:
            sev = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(p.get("severity", ""), "⚪")
            pid = p.get("id", "?")[:8]
            msg += f"{sev} `{pid}` {p.get('title', '?')}\n"
            msg += f"   Agent: {p.get('agent', '?')} | Votes: +{p.get('votes_for', 0)}/-{p.get('votes_against', 0)}\n\n"

        msg += "Ответьте: `act {id}` / `dismiss {id}` / `defer {id}`"
        await _send_message(chat_id, msg)
    except Exception as e:
        await _send_message(chat_id, f"⚠️ Ошибка чтения proposals: {str(e)[:100]}")


async def _handle_proposal_action(db, chat_id: int | str, action: str, proposal_id: str) -> None:
    """Process CEO's decision on a proposal: act, dismiss, or defer."""
    import json as _json
    proposals_path = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"
    try:
        with open(proposals_path, "r", encoding="utf-8") as f:
            data = _json.load(f)

        found = False
        for p in data.get("proposals", []):
            if p.get("id", "").startswith(proposal_id):
                old_status = p.get("status")
                if action == "act":
                    p["status"] = "approved"
                elif action == "dismiss":
                    p["status"] = "rejected"
                elif action == "defer":
                    p["status"] = "deferred"
                p["ceo_decision_at"] = datetime.now(timezone.utc).isoformat()
                found = True

                with open(proposals_path, "w", encoding="utf-8") as f:
                    _json.dump(data, f, indent=2, ensure_ascii=False)

                emoji = {"act": "✅", "dismiss": "❌", "defer": "⏸️"}.get(action, "")
                await _send_message(chat_id, f"{emoji} Proposal `{proposal_id}`: {old_status} → {p['status']}\n\n*{p.get('title', '')}*\n\nCTO получит решение при следующей сессии.")
                # Save to inbox for tracking
                await _save_message(db, "ceo_to_bot", f"{action} {proposal_id}: {p.get('title', '')}", "proposal_decision")
                break

        if not found:
            await _send_message(chat_id, f"⚠️ Proposal `{proposal_id}` не найден. Используйте /proposals.")

    except Exception as e:
        await _send_message(chat_id, f"⚠️ Ошибка: {str(e)[:100]}")


async def _handle_ask_agent(db, chat_id: int | str, agent_name: str, question: str) -> None:
    """Route CEO's question to a specific agent perspective via LLM."""
    agent_map = {
        "security": "Security Auditor — CVSS scoring, attack vectors, RLS gaps, OWASP top 10",
        "scaling": "Scaling Engineer — bottlenecks at 10x, database, API latency, infrastructure",
        "product": "Product Strategist — user journeys, Leyla/Nigar personas, adoption, retention",
        "quality": "Code Quality Engineer — tech debt, patterns, maintainability, test coverage",
        "watchdog": "CTO Watchdog — process compliance, memory updates, protocol v4.0",
    }

    if agent_name not in agent_map:
        agents_list = ", ".join(agent_map.keys())
        await _send_message(chat_id, f"⚠️ Agent `{agent_name}` не найден.\n\nДоступные: {agents_list}")
        return

    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен.")
        return

    stats = await _get_project_stats(db)
    perspective = agent_map[agent_name]

    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=question,
            config=genai.types.GenerateContentConfig(
                system_instruction=f"""Ты — {perspective} в swarm команде Volaura.
CEO (Юсиф) задаёт тебе прямой вопрос через Telegram.

Проект: verified professional platform, 51 API route, 512 tests, $50/mo budget.
Stats: {stats}

Отвечай от своей роли. Коротко (макс 200 слов). На русском. Честно — если не знаешь, скажи.
Если вопрос вне твоей экспертизы — скажи какого агента спросить.""",
                max_output_tokens=300,
                temperature=0.5,
            ),
        )
        reply = f"🤖 *{agent_name.title()} Agent:*\n\n{response.text.strip()}"
    except Exception as e:
        reply = f"⚠️ Agent `{agent_name}` не смог ответить: {str(e)[:100]}"

    await _save_message(db, "bot_to_ceo", f"[{agent_name}] {reply[:500]}", "agent_response")
    await _send_message(chat_id, reply)


async def _handle_skills(chat_id: int | str) -> None:
    """List available product skills."""
    skills_dir = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "skills"
    if not skills_dir.exists():
        await _send_message(chat_id, "⚠️ Папка skills не найдена.")
        return

    msg = "🧠 *Product Skills:*\n\n"
    for f in sorted(skills_dir.glob("*.md")):
        with open(f, "r", encoding="utf-8") as fh:
            title = fh.readline().replace("#", "").strip()
        msg += f"• `{f.stem}` — {title[:60]}\n"

    msg += "\n_Skills запускаются через API: POST /api/skills/{name}_"
    await _send_message(chat_id, msg)


async def _handle_help(chat_id: int | str) -> None:
    msg = (
        "🤖 *Volaura Swarm Bot*\n\n"
        "*Команды:*\n"
        "/status — статус проекта\n"
        "/proposals — pending proposals от роя\n"
        "/backlog — идеи и задачи CEO\n"
        "/skills — список product skills\n"
        "/ask {agent} {вопрос} — спросить агента\n"
        "/help — эта справка\n\n"
        "*Agents:* security, scaling, product, quality, watchdog\n\n"
        "*Proposal actions:*\n"
        "`act {id}` — одобрить\n"
        "`dismiss {id}` — отклонить\n"
        "`defer {id}` — отложить\n\n"
        "*Или просто напишите:*\n"
        "• Идею → бэклог\n"
        "• Задачу → команде\n"
        "• Вопрос → ответ из контекста"
    )
    await _send_message(chat_id, msg)


# ── Webhook Endpoint ─────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    """Receive Telegram update via webhook."""
    if not settings.telegram_bot_token:
        return JSONResponse({"ok": False, "error": "Bot not configured"})

    # Validate webhook origin
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not settings.telegram_webhook_secret:
        # No secret configured — block all requests in production, allow in dev
        if not settings.is_dev:
            logger.error("Telegram webhook: TELEGRAM_WEBHOOK_SECRET not set in production — rejecting request")
            return JSONResponse({"ok": False}, status_code=403)
    elif secret_header != settings.telegram_webhook_secret:
        logger.warning("Telegram webhook: invalid secret from {ip}", ip=request.client.host if request.client else "?")
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
        return JSONResponse({"ok": True})

    if not text:
        return JSONResponse({"ok": True})

    logger.info("Telegram CEO: {text}", text=text[:100])

    try:
        db = await _get_db()

        # Route commands
        if text.startswith("/status"):
            await _handle_status(db, chat_id)
        elif text.startswith("/proposals"):
            await _handle_proposals(db, chat_id)
        elif text.startswith("/backlog"):
            await _handle_backlog(db, chat_id)
        elif text.startswith("/skills"):
            await _handle_skills(chat_id)
        elif text.startswith("/ask "):
            # /ask security What are our RLS gaps?
            parts = text[5:].strip().split(" ", 1)
            agent = parts[0] if parts else ""
            question = parts[1] if len(parts) > 1 else ""
            if agent and question:
                await _handle_ask_agent(db, chat_id, agent.lower(), question)
            else:
                await _send_message(chat_id, "⚠️ Формат: /ask {agent} {вопрос}\nAgents: security, scaling, product, quality, watchdog")
        elif text.startswith("/help") or text.startswith("/start"):
            await _handle_help(chat_id)
        elif text.lower().startswith(("act ", "dismiss ", "defer ")):
            # Proposal actions: act abc123 / dismiss abc123 / defer abc123
            parts = text.split(" ", 1)
            action = parts[0].lower()
            pid = parts[1].strip() if len(parts) > 1 else ""
            if pid:
                await _handle_proposal_action(db, chat_id, action, pid)
            else:
                await _send_message(chat_id, "⚠️ Формат: `act {proposal_id}` / `dismiss {id}` / `defer {id}`")
        else:
            # Free-text → classify + respond + save
            await _classify_and_respond(db, text, chat_id)

    except Exception as e:
        logger.error("Telegram handler error: {e}", e=str(e))
        # Always try to respond even on error
        await _send_message(chat_id, f"⚠️ Ошибка обработки. Сообщение может не быть сохранено.\n{str(e)[:100]}")

    return JSONResponse({"ok": True})


# ── Setup Webhook ────────────────────────────────────────────────────────────

@router.post("/setup-webhook")
async def setup_webhook(request: Request) -> JSONResponse:
    """Register the webhook URL with Telegram API. Call once after deploy.

    CRIT-03 FIX: Requires secret header to prevent unauthorized webhook re-registration.
    Call with: curl -X POST .../api/telegram/setup-webhook -H "X-Admin-Secret: <TELEGRAM_WEBHOOK_SECRET>"
    """
    if not settings.telegram_bot_token:
        return JSONResponse({"ok": False, "error": "TELEGRAM_BOT_TOKEN not set"})

    # Auth check: require webhook secret as admin header
    admin_secret = request.headers.get("X-Admin-Secret", "")
    if not settings.telegram_webhook_secret or admin_secret != settings.telegram_webhook_secret:
        return JSONResponse({"ok": False, "error": "Unauthorized"}, status_code=403)

    webhook_url = "https://volauraapi-production.up.railway.app/api/telegram/webhook"

    import httpx
    payload: dict = {"url": webhook_url}
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
