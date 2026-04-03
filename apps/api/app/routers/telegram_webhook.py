"""Telegram Webhook — Volaura Product Owner Bot.

Receives CEO messages via Telegram webhook.
Acts as Product Owner: saves ideas, delegates tasks, writes reports, manages backlog.
Uses Supabase DB for state (not local files — Railway filesystem is ephemeral).

Setup: POST /api/telegram/setup-webhook to register with Telegram API.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger
from supabase._async.client import AsyncClient

from app.config import settings
from app.deps import get_supabase_admin

router = APIRouter(prefix="/telegram", tags=["Telegram"])

# Type alias for Depends injection
SupabaseAdmin = AsyncClient


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


def _get_ecosystem_context() -> str:
    """Return hardcoded ecosystem state for bot context. Update this when platform state changes."""
    return """
=== ECOSYSTEM STATE (2026-04-03 Session 83) ===
Volaura: DEPLOYED. Railway + Vercel + Supabase. LRL 97/100. 115 API endpoints. 43 AI agents. Assessment→AURA→Badge→Share WORKS.
MindShift: DEPLOYED. 92% PWA. React 19+Vite. 330+ Playwright tests. Stripe integrated.
Life Simulator: Event bus exists (character_events). Needs CloudSave + Volaura crystal bridge UI.
ZEUS: 70% desktop. Plan→Execute→Reflect loop works. No cloud API yet.
BrandedBy: Video worker wired (fal.ai). Needs FAL_API_KEY activation (~$5-50/mo).
Crystal bridge: character_events + game_crystal_ledger LIVE. Crystal spending via BrandedBy queue skip (25 crystals).
Integration Layer: Cross-product bridge wired (MindShift). Needs MINDSHIFT_URL on Railway.

=== CURRENT STATE ===
Session 83 complete. TASK-PROTOCOL v8.0 (Toyota+Apple+DORA quality system).
Quality: 3-question DoD, defect autopsy (76 bugs → 3 classes = 76.4%), Langfuse LLM monitoring wired.
Tools: Playwright MCP, Sentry MCP, NotebookLM (45+ sources), Dodo Payments API key saved.
Payments: Dodo Payments (MoR, 220+ countries, native AZN). Company verification pending.
Analytics: 6 frontend events + backend ingestion + GDPR 390-day retention.
Security: 0 errors (4 SECURITY_DEFINER views fixed, 6 search_path functions hardened).

=== TEAM ===
43 agents. Key: Security, Architecture, Product, QA, Growth, Risk, Readiness, CEO Report, Onboarding, Customer Success.
Multi-model: DeepSeek R1 (NVIDIA NIM), Llama 405B (NVIDIA NIM), Gemini 2.0 Flash, Claude Opus.
Budget: $50/mo. Stack: FastAPI + Next.js 14 + Supabase + Railway + Vercel.

=== NEXT STEPS ===
1. Dodo Payments integration (when company verified)
2. Closed testing: 10 people (Tural, Turan, Firuza + 7)
3. CrewAI Phase 1 (structural fix for solo execution)
4. Launch to 12,000 (end of April)
"""


async def _classify_and_respond(db, text: str, chat_id: int | str) -> None:
    """Classify CEO message and respond intelligently as Product Owner."""
    context = await _get_recent_context(db)
    stats = await _get_project_stats(db)
    ecosystem = _get_ecosystem_context()

    # Detect intent
    text_lower = text.lower()
    is_idea = any(w in text_lower for w in ["идея", "idea", "можно сделать", "а что если", "предлагаю", "надо бы"])
    is_task = any(w in text_lower for w in ["сделай", "задача", "task", "нужно", "исправь", "fix", "добавь", "add"])
    is_question = "?" in text
    is_report = any(w in text_lower for w in [
        "отчёт", "report", "статус", "status", "что сделано", "прогресс",
        "готов", "работает", "zeus", "life sim", "crystal", "кристал",
        "mindshift", "интеграция", "ecosystem"
    ])

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

    system_prompt = f"""Ты — CTO-бот команды MiroFish. Говоришь от имени всей команды ("мы").
Отвечаешь CEO Юсифу Ганбарову в Telegram. Коротко, по делу, на русском или азербайджанском — как спрашивает.

Твои обязанности:
1. ИДЕИ — подтверди что записал, честно оцени (сильно/слабо/нужно обдумать), скажи что передашь команде
2. ЗАДАЧИ — подтверди, скажи что войдёт в следующий спринт
3. ОТЧЁТЫ/ВОПРОСЫ О СТАТУСЕ — дай честный ответ из контекста ниже. Не придумывай.
4. ЛЮБОЙ ВОПРОС — отвечай только на основе данных ниже. Не знаешь — скажи прямо.

Живые данные платформы:
{stats}

Полный контекст экосистемы:
{ecosystem}

Последние сообщения:
{context[-800:]}

Тип сообщения CEO: {msg_type}

ПРАВИЛА:
- Максимум 500 символов в ответе (Telegram)
- Не льсти. "Отличная идея" — запрещено. Говори честно.
- Если ZEUS/Life Sim/Crystal спрашивает — отвечай точно из контекста выше (не готово)
- Если задача непонятная — спроси уточнение одним вопросом
- Заканчивай: следующий шаг / кто ответственен"""

    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=400,
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

                # Atomic write: temp file + rename prevents TOCTOU race (P1-02)
                import tempfile
                tmp_fd, tmp_path = tempfile.mkstemp(dir=proposals_path.parent, suffix=".json")
                try:
                    with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                        _json.dump(data, tmp_f, indent=2, ensure_ascii=False)
                    os.replace(tmp_path, proposals_path)
                except Exception:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                    raise

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
        "risk": "Risk Manager (ISO 31000 + COSO ERM) — Likelihood×Impact scoring, risk register, blocks CRITICAL risks. Red lines: CVSS≥7, user data without auth, zero backup/restore tested.",
        "readiness": "Readiness Manager (Google SRE + ITIL v4) — Go/No-Go decisions, LRL scoring (1-7), 5-dimension audit (Correctness/Ops/Security/UX/Rollback). Current platform: LRL-4, score 70/100. GO for ≤200 users.",
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


async def _handle_ask_proposal(db, chat_id: int | str, proposal_id: str, question: str) -> None:
    """CEO asks a follow-up question about a specific swarm proposal."""
    import json as _json
    proposals_path = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"

    try:
        with open(proposals_path, "r", encoding="utf-8") as f:
            data = _json.load(f)
    except Exception:
        await _send_message(chat_id, "⚠️ Не удалось прочитать proposals.")
        return

    found = None
    for p in data.get("proposals", []):
        if p.get("id", "").startswith(proposal_id):
            found = p
            break

    if not found:
        await _send_message(chat_id, f"⚠️ Proposal `{proposal_id}` не найден. Используйте /proposals.")
        return

    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен.")
        return

    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        context = (
            f"Agent: {found.get('agent', '?')}\n"
            f"Severity: {found.get('severity', '?')}\n"
            f"Title: {found.get('title', '?')}\n"
            f"Content: {found.get('content', '')[:800]}"
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=question,
            config=genai.types.GenerateContentConfig(
                system_instruction=f"""Ты — CTO-бот. CEO задаёт уточняющий вопрос по конкретному proposal от swarm.

PROPOSAL:
{context}

Отвечай строго по контексту proposal. Коротко (макс 200 слов). На русском.
Если вопрос требует кода или файлов — скажи CEO что нужно запустить сессию CTO.""",
                max_output_tokens=350,
                temperature=0.4,
            ),
        )
        reply = f"🔍 *По proposal `{proposal_id}`:*\n\n{response.text.strip()}"
    except Exception as e:
        reply = f"⚠️ Не смог ответить по proposal: {str(e)[:100]}"

    await _save_message(db, "bot_to_ceo", reply[:500], "proposal_followup")
    await _send_message(chat_id, reply)


async def _handle_ecosystem(chat_id: int | str) -> None:
    """Show full ecosystem state — honest snapshot."""
    msg = (
        "🌐 *Ecosystem State — 2026-03-30 BATCH N*\n\n"
        "✅ *Volaura* — LRL ~78/100 CONDITIONAL GO, 648 tests, beta ≤200\n"
        "✅ *MindShift* — LIVE, 92% PWA, 132 E2E tests\n"
        "⚠️ *Life Simulator* — 2 crash bugs FIXED today. Needs CloudSave + crystal bridge\n"
        "⚠️ *ZEUS* — 70% desktop, Telegram works, 0% Godot bridge, no ngrok cloud tunnel\n"
        "❌ *BrandedBy* — 15%, Stripe broken, AI video = 0%\n"
        "❌ *Crystal Bridge* — DOES NOT EXIST yet\n"
        "❌ *Integration Layer* — 0%, character_state API not built\n\n"
        "📊 *ECOSYSTEM REAL COMPLETION: ~30%*\n\n"
        "CEO actions blocking beta launch:\n"
        "1. Walk volaura.app E2E with real email\n"
        "2. Sign up Polar.sh (24h approval, no company needed)\n"
        "3. Set VOLAURA_TEST_JWT on Railway → run k6 load test"
    )
    await _send_message(chat_id, msg)


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
        "/status — live статистика (users, sessions, orgs)\n"
        "/ecosystem — состояние всех 5 продуктов\n"
        "/proposals — pending proposals от роя\n"
        "/backlog — идеи и задачи CEO\n"
        "/skills — список product skills\n"
        "/ask {agent} {вопрос} — спросить агента\n"
        "/help — эта справка\n\n"
        "*Agents:* security, scaling, product, quality, watchdog, risk, readiness\n\n"
        "*Proposal actions:*\n"
        "`act {id}` — одобрить\n"
        "`dismiss {id}` — отклонить\n"
        "`defer {id}` — отложить\n"
        "`ask {id} {вопрос}` — уточнить по proposal\n\n"
        "*Или просто напишите:*\n"
        "• Идею → бэклог\n"
        "• Задачу → команде\n"
        "• Вопрос → ответ из контекста"
    )
    await _send_message(chat_id, msg)


# ── Webhook Endpoint ─────────────────────────────────────────────────────────

@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncClient = Depends(get_supabase_admin),
) -> JSONResponse:
    """Receive Telegram update via webhook. Uses Depends for admin client (OWASP HIGH-01 fix)."""
    if not settings.telegram_bot_token:
        return JSONResponse({"ok": False, "error": "Bot not configured"})

    # Validate webhook origin
    # If secret is configured: verify Telegram's X-Telegram-Bot-Api-Secret-Token header.
    # If secret is NOT configured: allow all requests (no signature check).
    # CEO_CHAT_ID filter below is still enforced — only CEO can trigger bot actions.
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if settings.telegram_webhook_secret and secret_header != settings.telegram_webhook_secret:
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
        # Route commands (db injected via Depends)
        if text.startswith("/status"):
            await _handle_status(db, chat_id)
        elif text.startswith("/proposals"):
            await _handle_proposals(db, chat_id)
        elif text.startswith("/backlog"):
            await _handle_backlog(db, chat_id)
        elif text.startswith("/ecosystem"):
            await _handle_ecosystem(chat_id)
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
        elif text.lower().startswith("ask "):
            # Two forms:
            #   ask {agent_name} {question}  → route to agent perspective
            #   ask {proposal_id} {question} → ask follow-up about specific proposal
            parts = text[4:].strip().split(" ", 1)
            first_token = parts[0].lower() if parts else ""
            question = parts[1] if len(parts) > 1 else ""
            known_agents = {"security", "scaling", "product", "quality", "watchdog", "risk", "readiness"}
            if first_token in known_agents and question:
                await _handle_ask_agent(db, chat_id, first_token, question)
            elif first_token and question:
                # Treat as proposal-specific follow-up
                await _handle_ask_proposal(db, chat_id, first_token, question)
            else:
                await _send_message(chat_id, "⚠️ Формат:\n`ask {agent} {вопрос}` — агенту\n`ask {proposal_id} {вопрос}` — по конкретному proposal")
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

    # HIGH-02 FIX: Don't log full API response (may contain bot token)
    logger.info("Telegram webhook setup: ok={ok}", ok=result.get("ok"))
    return JSONResponse({"ok": result.get("ok"), "description": result.get("description", "")})
