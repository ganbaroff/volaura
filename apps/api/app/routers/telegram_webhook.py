"""Telegram Webhook — Volaura Product Owner Bot.

Receives CEO messages via Telegram webhook.
Acts as Product Owner: saves ideas, delegates tasks, writes reports, manages backlog.
Uses Supabase DB for state (not local files — Railway filesystem is ephemeral).

Setup: POST /api/telegram/setup-webhook to register with Telegram API.
"""

from __future__ import annotations

import contextlib
import os
from datetime import UTC, datetime
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


async def _transcribe_voice(file_id: str, chat_id: int | str) -> str | None:
    """Download Telegram voice → transcribe via Groq Whisper. Returns text or None."""
    if not settings.telegram_bot_token or not file_id:
        return None
    groq_key = os.environ.get("GROQ_API_KEY", "")
    if not groq_key:
        await _send_message(chat_id, "Voice: GROQ_API_KEY not set.")
        return None
    try:
        import httpx

        async with httpx.AsyncClient(timeout=15) as client:
            file_info = await client.get(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/getFile",
                params={"file_id": file_id},
            )
            file_path = file_info.json().get("result", {}).get("file_path", "")
            if not file_path:
                return None
            audio_resp = await client.get(f"https://api.telegram.org/file/bot{settings.telegram_bot_token}/{file_path}")
            audio_bytes = audio_resp.content

            resp = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {groq_key}"},
                data={"model": "whisper-large-v3-turbo", "language": "ru"},
                files={"file": ("voice.ogg", audio_bytes, "audio/ogg")},
            )
            text = resp.json().get("text", "").strip()
            if text:
                logger.info("Voice transcribed: {chars} chars", chars=len(text))
            return text or None
    except Exception as e:
        logger.error("Voice transcription failed: {e}", e=str(e))
        return None


async def _send_message(chat_id: int | str, text: str, reply_markup: dict | None = None) -> bool:
    """Send a Telegram message via Bot API. Returns True on success."""
    import httpx

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    # Telegram max message length is 4096 — split into chunks, never truncate
    chunks = [text[i : i + 4000] for i in range(0, len(text), 4000)]
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            for i, chunk in enumerate(chunks):
                payload: dict = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "Markdown",
                }
                # Attach buttons only to last chunk
                if reply_markup and i == len(chunks) - 1:
                    payload["reply_markup"] = reply_markup
                resp = await client.post(url, json=payload)
                if not resp.json().get("ok"):
                    payload.pop("parse_mode", None)
                    await client.post(url, json=payload)
            return True
    except Exception as e:
        logger.error("Telegram send failed: {e}", e=str(e))
        return False


async def _save_message(db, direction: str, message: str, msg_type: str = "free_text", metadata: dict | None = None):
    """Save message to ceo_inbox table."""
    try:
        await (
            db.table("ceo_inbox")
            .insert(
                {
                    "direction": direction,
                    "message": message[:5000],
                    "message_type": msg_type,
                    "metadata": metadata or {},
                }
            )
            .execute()
        )
    except Exception as e:
        logger.error("Failed to save message: {e}", e=str(e))


async def _get_recent_context(db, limit: int = 30) -> str:
    """Get recent conversation context from DB — full messages, not truncated."""
    try:
        result = (
            await db.table("ceo_inbox")
            .select("direction,message,message_type,created_at")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        if not result.data:
            return "Нет предыдущих сообщений."
        lines = []
        for msg in reversed(result.data):
            role = "CEO" if msg["direction"] == "ceo_to_bot" else "Bot"
            lines.append(f"[{role}] {msg['message'][:500]}")
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


_REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent


def _get_ecosystem_context() -> str:
    """Read live ecosystem state from heartbeat files. Falls back to hardcoded if unavailable."""
    parts: list[str] = []

    # VOLAURA heartbeat
    volaura_hb = _REPO_ROOT / "memory" / "context" / "heartbeat.md"
    if volaura_hb.exists():
        with contextlib.suppress(Exception):
            parts.append("=== VOLAURA HEARTBEAT ===\n" + volaura_hb.read_text(encoding="utf-8")[:1200])

    # MindShift heartbeat
    mindshift_hb = Path("C:/Users/user/Downloads/mindshift/memory/heartbeat.md")
    if mindshift_hb.exists():
        with contextlib.suppress(Exception):
            parts.append("=== MINDSHIFT HEARTBEAT ===\n" + mindshift_hb.read_text(encoding="utf-8")[:800])

    # Ecosystem contract
    contract = _REPO_ROOT / "memory" / "context" / "ecosystem-contract.md"
    if contract.exists():
        with contextlib.suppress(Exception):
            parts.append("=== ECOSYSTEM CONTRACT ===\n" + contract.read_text(encoding="utf-8")[:600])

    if parts:
        return "\n\n".join(parts)

    # Fallback
    return (
        "=== ECOSYSTEM (fallback — heartbeat files not found) ===\n"
        "Volaura: DEPLOYED. Railway + Vercel + Supabase. 115 API endpoints. 47 AI agents.\n"
        "MindShift: READY FOR PLAY STORE. 207 unit + 201 E2E tests. AAB 4.3 MB built.\n"
        "Life Simulator: 65%. 4 P0 bugs blocking API integration.\n"
        "ZEUS: 70%. 47 agents daily autonomous runs.\n"
        "BrandedBy: 15%. Early stage.\n"
        "MISSING: POST /api/character/events, GET /api/character/state, GET /api/character/crystals"
    )


def _load_agent_state() -> dict:
    """Load live agent state from agent-state.json."""
    state_path = _REPO_ROOT / "memory" / "swarm" / "agent-state.json"
    try:
        import json as _json

        with open(state_path, encoding="utf-8") as f:
            data = _json.load(f)
        return data.get("agents", {})
    except Exception:
        return {}


# Full 44-agent roster for /ask routing
_FULL_AGENT_MAP = {
    "security": "Security Agent (9.0/10) — CVSS scoring, attack vectors, RLS gaps, OWASP top 10",
    "architecture": "Architecture Agent (8.5/10) — system design, storage math, CVSS 9.8 patterns",
    "product": "Product Agent (8.0/10) — user journeys, personas, adoption, retention, 100% accuracy",
    "needs": "Needs Agent (7.0/10) — schema snapshots, process analysis, highest-leverage findings",
    "qa": "QA Engineer (6.5/10) — test coverage, DoD enforcement, anti-self-assessment",
    "growth": "Growth Agent (5.0/10 ⚠️ SURVIVAL CLOCK) — CAC/LTV, competitive tracking, D0-D30 retention",
    "risk": "Risk Manager — ISO 31000, Likelihood×Impact scoring, blocks CRITICAL risks",
    "readiness": "Readiness Manager — SRE/ITIL v4, Go/No-Go decisions, LRL scoring",
    "scaling": "Scaling Engineer — bottlenecks at 10x, database, API latency, infrastructure",
    "watchdog": "CTO Watchdog — process compliance, memory updates, protocol enforcement",
    "quality": "Code Quality Engineer — tech debt, patterns, maintainability, test coverage",
    "assessment-science": "Assessment Science Agent — IRT parameters, DIF bias, CAT stopping criteria",
    "analytics": "Analytics & Retention Agent — D0/D1/D7/D30 cohort analysis, B2B health score",
    "devops": "DevOps/SRE Agent — Railway/Vercel/Supabase ops, incident response",
    "finance": "Financial Analyst Agent — LTV/CAC, AZN unit economics, crystal economy pricing",
    "ux": "UX Research Agent — JTBD framework, 5-user testing, AZ cultural gaps",
    "pr": "PR & Media Agent — AZ media landscape, press releases, startup competitions",
    "data": "Data Engineer Agent — PostHog, analytics pipeline, event schema",
    "technical-writer": "Technical Writer Agent — API docs, B2B content, AURA explainer",
    "payment": "Payment Provider Agent — Paddle webhooks, revenue reconciliation",
    "community": "Community Manager Agent — tribe engagement, D7 retention playbook",
    "performance": "Performance Engineer Agent — pgvector audit, k6 load testing, N+1 detection",
    "investor": "Investor/Board Agent — VC perspective, fundraising, pricing",
    "competitor": "Competitor Intelligence Agent — LinkedIn, HH.ru, TestGorilla analysis",
    "university": "University & Ecosystem Partner Agent — ADA/BHOS/GITA partnerships",
    "ceo-report": "CEO Report Agent (7.0/10) — translates technical output to business language",
    "qa-quality": "QA Quality Agent — Definition of Done enforcer, CTO cannot override",
    "onboarding": "Onboarding Specialist Agent — first 5-minute experience optimization",
    "customer-success": "Customer Success Agent — churn prevention, D7 retention",
    "trend-scout": "Trend Scout Agent — market intelligence, competitor features",
    "firuza": "Firuza (Council) — execution micro-decisions (100% accuracy)",
    "nigar": "Nigar (Council) — B2B feature decisions (100% accuracy)",
    "comms": "Communications Strategist — narrative arc, content strategy",
    "legal": "Legal Advisor — GDPR compliance, crystal economy ethics",
    "fact-check": "Fact-Check Agent — CEO content verification before publishing",
    "cultural": "Cultural Intelligence Strategist — AZ/CIS cultural audit 🔴 CRITICAL",
    "accessibility": "Accessibility Auditor — WCAG 2.2 AA specialist",
    "behavioral-nudge": "Behavioral Nudge Engine — ADHD-first UX validator 🔴 CRITICAL",
    "sales-deal": "Sales Deal Strategist — B2B deal architecture",
    "sales-discovery": "Sales Discovery Coach — B2B discovery flow",
    "linkedin": "LinkedIn Content Creator — LinkedIn & professional brand",
    "promotion": "Promotion Agency — distribution & content amplification",
}


async def _classify_and_respond(db, text: str, chat_id: int | str) -> None:
    """Classify CEO message and respond intelligently as Product Owner."""
    context = await _get_recent_context(db)
    stats = await _get_project_stats(db)
    ecosystem = _get_ecosystem_context()

    # Detect intent
    text_lower = text.lower()
    is_idea = any(w in text_lower for w in ["идея", "idea", "можно сделать", "а что если", "предлагаю", "надо бы"])
    is_task = any(w in text_lower for w in ["сделай", "задача", "task", "нужно", "исправь", "fix", "добавь", "add"])
    is_report = any(
        w in text_lower
        for w in [
            "отчёт",
            "report",
            "статус",
            "status",
            "что сделано",
            "прогресс",
            "готов",
            "работает",
            "zeus",
            "life sim",
            "crystal",
            "кристал",
            "mindshift",
            "интеграция",
            "ecosystem",
        ]
    )

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

    system_prompt = f"""Ты — CTO-бот команды MiroFish. Ты технический директор экосистемы из 5 продуктов.
Отвечаешь CEO Юсифу Ганбарову в Telegram. Развёрнуто, технично, честно. На русском или азербайджанском — как спрашивает.

Твоя роль:
- Ты управляешь 47 AI-агентами и координируешь разработку
- Ты знаешь ВСЮ архитектуру, все файлы, все решения
- Когда CEO даёт задачу — ты планируешь как её выполнить и объясняешь план
- Когда CEO спрашивает — ты даёшь технический ответ с конкретикой
- Ты НИКОГДА не говоришь "передам команде" без конкретного плана действий
- Если не знаешь — скажи прямо, но предложи как узнать

Живые данные платформы:
{stats}

Полный контекст экосистемы:
{ecosystem}

Вся история разговора (последние 30 сообщений):
{context}

Тип сообщения CEO: {msg_type}

ПРАВИЛА:
- Отвечай развёрнуто, подробно, столько сколько нужно. Без искусственных лимитов.
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
                max_output_tokens=4000,
                temperature=0.7,
            ),
        )
        reply = response.text.strip()
    except Exception as e:
        logger.warning("Gemini bot error, trying Groq fallback: {e}", e=str(e)[:100])
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=15) as hc:
                    groq_resp = await hc.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}", "User-Agent": "volaura-bot/1.0"},
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": system_prompt[:2000]},
                                {"role": "user", "content": text},
                            ],
                            "max_tokens": 2000,
                            "temperature": 0.7,
                        },
                    )
                    reply = groq_resp.json()["choices"][0]["message"]["content"].strip()
            except Exception as e2:
                logger.error("Groq fallback also failed: {e}", e=str(e2)[:100])
                reply = f"Сообщение сохранено ✅\nТип: {msg_type}\nLLM временно недоступен."
        else:
            reply = f"Сообщение сохранено ✅\nТип: {msg_type}\nGemini и Groq недоступны."

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
        unprocessed = (
            await db.table("ceo_inbox")
            .select("*", count="exact")
            .eq("direction", "ceo_to_bot")
            .eq("processed", False)
            .execute()
        )
        pending_count = unprocessed.count or 0
    except Exception:
        pending_count = 0

    msg = f"🔮 *Volaura Status*\n\n{stats}\n\n📬 Необработанных сообщений: {pending_count}"
    await _send_message(chat_id, msg)


async def _handle_backlog(db, chat_id: int | str) -> None:
    """Show recent ideas and tasks from CEO."""
    try:
        ideas = (
            await db.table("ceo_inbox")
            .select("message,created_at")
            .eq("direction", "ceo_to_bot")
            .in_("message_type", ["idea", "task"])
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
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
        with open(proposals_path, encoding="utf-8") as f:
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

        # Inline keyboard: ✅ Approve / 🚀 Execute (triggers CI) / ❌ Reject
        buttons = []
        for p in pending[:5]:
            pid = p.get("id", "?")[:8]
            buttons.append(
                [
                    {"text": "✅ Approve", "callback_data": f"act:{pid}"},
                    {"text": "🚀 Execute", "callback_data": f"execute:{pid}"},
                    {"text": "❌ Reject", "callback_data": f"dismiss:{pid}"},
                ]
            )
        keyboard = {"inline_keyboard": buttons}
        await _send_message(chat_id, msg, reply_markup=keyboard)
    except Exception as e:
        await _send_message(chat_id, f"⚠️ Ошибка чтения proposals: {str(e)[:100]}")


async def _handle_proposal_action(db, chat_id: int | str, action: str, proposal_id: str) -> None:
    """Process CEO's decision on a proposal: act, dismiss, or defer."""
    import json as _json

    proposals_path = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"
    try:
        with open(proposals_path, encoding="utf-8") as f:
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
                p["ceo_decision_at"] = datetime.now(UTC).isoformat()
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
                await _send_message(
                    chat_id,
                    f"{emoji} Proposal `{proposal_id}`: {old_status} → {p['status']}\n\n*{p.get('title', '')}*\n\nCTO получит решение при следующей сессии.",
                )
                # Save to inbox for tracking
                await _save_message(
                    db, "ceo_to_bot", f"{action} {proposal_id}: {p.get('title', '')}", "proposal_decision"
                )
                break

        if not found:
            await _send_message(chat_id, f"⚠️ Proposal `{proposal_id}` не найден. Используйте /proposals.")

    except Exception as e:
        await _send_message(chat_id, f"⚠️ Ошибка: {str(e)[:100]}")


async def _execute_proposal(db, chat_id: int | str, proposal_id: str) -> None:
    """Execute a proposal by triggering GitHub Actions coordinator workflow."""
    import json as _json

    proposals_path = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"

    try:
        with open(proposals_path, encoding="utf-8") as f:
            data = _json.load(f)

        found = None
        for p in data.get("proposals", []):
            if p.get("id", "").startswith(proposal_id):
                found = p
                break

        if not found:
            await _send_message(chat_id, f"⚠️ Proposal `{proposal_id}` не найден.")
            return

        # Mark as executing
        found["status"] = "executing"
        found["ceo_decision_at"] = datetime.now(UTC).isoformat()
        import tempfile

        tmp_fd, tmp_path = tempfile.mkstemp(dir=proposals_path.parent, suffix=".json")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
                _json.dump(data, tmp_f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, proposals_path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        # Trigger GitHub Actions workflow_dispatch
        import httpx

        gh_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
        if not gh_token:
            await _send_message(
                chat_id,
                f"🚀 Proposal `{proposal_id}` помечен для исполнения.\n⚠️ GITHUB_TOKEN не настроен — автозапуск невозможен.\n\nВручную: `gh workflow run 'Swarm Daily Autonomy' -f mode=coordinator`",
            )
            return

        f"{found.get('title', '')}. {found.get('content', '')[:300]}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                "https://api.github.com/repos/ganbaroff/volaura/actions/workflows/swarm-daily.yml/dispatches",
                headers={
                    "Authorization": f"Bearer {gh_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                json={
                    "ref": "main",
                    "inputs": {"mode": "coordinator"},
                },
            )

        if resp.status_code in (204, 200):
            await _send_message(
                chat_id,
                f"🚀 *Executing proposal `{proposal_id}`*\n\n_{found.get('title', '')}_\n\nWorkflow запущен. Результат придёт в следующем сообщении.",
            )
            await _save_message(
                db, "ceo_to_bot", f"execute {proposal_id}: {found.get('title', '')}", "proposal_execute"
            )
        else:
            await _send_message(
                chat_id,
                f"⚠️ GitHub Actions не запустился (HTTP {resp.status_code}). Proposal помечен для ручного исполнения.",
            )

    except Exception as e:
        await _send_message(chat_id, f"⚠️ Execute error: {str(e)[:150]}")


async def _handle_agents(chat_id: int | str) -> None:
    """Show all 44 ZEUS agents with live status from agent-state.json."""
    live = _load_agent_state()
    status_emoji = {"active": "⚡", "idle": "💤", "running": "🔄", "new": "🆕"}

    lines = ["🤖 *ZEUS Swarm — 44 агента*\n"]
    lines.append("*Инициализированные:*")
    initialized = [(aid, info) for aid, info in live.items() if info.get("status") != "uninitialized"]
    for aid, info in sorted(initialized, key=lambda x: -(x[1].get("performance", {}).get("tasks_completed", 0))):
        emoji = status_emoji.get(info.get("status", ""), "🤖")
        tasks = info.get("performance", {}).get("tasks_completed", 0)
        last = (info.get("last_task") or "—")[:60]
        lines.append(f"{emoji} `{aid}` — {tasks} задач\n   _{last}_")

    lines.append("\n*Все агенты* — /ask {agent} {вопрос}")
    lines.append("*Дать задачу* — /agent {{id}} {{задача}}")
    lines.append("*Весь рой* — /swarm {{задача}}")
    lines.append(f"\nАгентов с данными: {len(initialized)}/44")
    await _send_message(chat_id, "\n".join(lines))


async def _handle_agent_task(db, chat_id: int | str, agent_id: str, task: str) -> None:
    """Give a specific task to one agent and get their response via Gemini."""
    # Normalize: allow short names and full IDs
    normalized = agent_id.lower().replace(" ", "-")
    perspective = _FULL_AGENT_MAP.get(normalized)
    if not perspective:
        # Try partial match
        for key, desc in _FULL_AGENT_MAP.items():
            if normalized in key or key in normalized:
                perspective = desc
                normalized = key
                break

    if not perspective:
        keys = ", ".join(sorted(_FULL_AGENT_MAP.keys()))
        await _send_message(chat_id, f"⚠️ Агент `{agent_id}` не найден.\n\nДоступные ID:\n{keys}")
        return

    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен.")
        return

    # Load agent's live state for context
    live = _load_agent_state()
    agent_state = live.get(normalized, {})
    state_ctx = ""
    if agent_state:
        state_ctx = (
            f"\nТвой текущий статус: {agent_state.get('status', 'unknown')}"
            f"\nПоследняя задача: {agent_state.get('last_task', 'нет')}"
            f"\nЗадач выполнено: {agent_state.get('performance', {}).get('tasks_completed', 0)}"
        )

    stats = await _get_project_stats(db)
    ecosystem = _get_ecosystem_context()

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=task,
            config=genai.types.GenerateContentConfig(
                system_instruction=f"""Ты — {perspective} в ZEUS swarm.
CEO Юсиф даёт тебе конкретную задачу через Telegram.{state_ctx}

Контекст проекта:
{stats}

Экосистема:
{ecosystem[:800]}

ПРАВИЛА:
- Отвечай от своей роли и экспертизы
- Конкретно: файлы, строки кода, числа, риски с оценкой
- Если задача вне твоей экспертизы — скажи какому агенту передать
- Заканчивай: что нужно сделать дальше и кто
- На русском""",
                max_output_tokens=2000,
                temperature=0.7,
            ),
        )
        reply = f"🤖 *{normalized.title()} Agent:*\n\n{response.text.strip()}"
    except Exception as e:
        reply = f"⚠️ Agent `{normalized}` не смог ответить: {str(e)[:100]}"

    await _save_message(db, "bot_to_ceo", f"[task→{normalized}] {reply}", "agent_task")
    await _send_message(chat_id, reply)


async def _handle_queue(chat_id: int | str) -> None:
    """Show autonomous queue — what agents can do without CEO approval."""
    queue_path = _REPO_ROOT / "memory" / "swarm" / "autonomous-queue.md"
    try:
        content = queue_path.read_text(encoding="utf-8")
        # Extract first 2000 chars (the actionable part)
        msg = f"📋 *Autonomous Queue:*\n\n{content[:2000]}"
        if len(content) > 2000:
            msg += "\n\n_...показаны первые 2000 символов_"
        await _send_message(chat_id, msg)
    except Exception as e:
        await _send_message(chat_id, f"⚠️ Не удалось прочитать очередь: {str(e)[:100]}")


async def _handle_swarm(db, chat_id: int | str, task: str) -> None:
    """Broadcast task to top 3 most relevant agents and synthesize their responses."""
    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен.")
        return

    await _send_message(chat_id, f"🔄 Рою задача: _{task}_\n\nОпрашиваю агентов...")

    stats = await _get_project_stats(db)
    ecosystem = _get_ecosystem_context()[:600]

    # Pick top 3 agents by relevance (simple keyword routing)
    task_lower = task.lower()
    selected: list[tuple[str, str]] = []

    priority_map = [
        (["безопасност", "security", "rls", "auth", "уязвим"], "security"),
        (["архитектур", "architecture", "дизайн систем", "масштаб"], "architecture"),
        (["продукт", "product", "юзер", "пользовател", "retention", "удержан"], "product"),
        (["тест", "test", "qa", "качество", "баг", "bug"], "qa"),
        (["рост", "growth", "cac", "ltv", "метрик"], "growth"),
        (["риск", "risk", "блокер", "blocker"], "risk"),
        (["готовност", "readiness", "deploy", "деплой", "запуск", "launch"], "readiness"),
        (["финанс", "finance", "деньг", "цен", "pricing"], "finance"),
        (["ux", "ui", "интерфейс", "дизайн", "adhd"], "behavioral-nudge"),
        (["аналитик", "analytics", "данные", "данных", "data"], "analytics"),
        (["devops", "railway", "vercel", "supabase", "инфра"], "devops"),
        (["конкурент", "competitor", "рынок", "market"], "competitor"),
    ]

    for keywords, agent_id in priority_map:
        if any(kw in task_lower for kw in keywords):
            selected.append((agent_id, _FULL_AGENT_MAP[agent_id]))
        if len(selected) >= 3:
            break

    # Default if no match: security + product + architecture
    if not selected:
        selected = [
            ("security", _FULL_AGENT_MAP["security"]),
            ("product", _FULL_AGENT_MAP["product"]),
            ("architecture", _FULL_AGENT_MAP["architecture"]),
        ]

    responses: list[str] = []
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    for agent_id, perspective in selected:
        try:
            resp = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=task,
                config=genai.types.GenerateContentConfig(
                    system_instruction=f"""Ты — {perspective}.
CEO дал задачу всему рою. Дай ответ строго со своей перспективы.
Проект: {stats}
Экосистема: {ecosystem}
Максимум 300 слов. Конкретно. На русском.""",
                    max_output_tokens=600,
                    temperature=0.7,
                ),
            )
            responses.append(f"🤖 *{agent_id.title()}:*\n{resp.text.strip()}")
        except Exception as e:
            responses.append(f"⚠️ {agent_id}: {str(e)[:80]}")

    # Synthesize
    combined = "\n\n".join(responses)
    try:
        synthesis = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Синтезируй эти 3 ответа агентов по задаче '{task}' в одно краткое решение:\n\n{combined}",
            config=genai.types.GenerateContentConfig(
                system_instruction="Ты CTO-синтезатор. Один абзац: что делаем, кто отвечает, риски. Без повторений.",
                max_output_tokens=400,
                temperature=0.4,
            ),
        )
        synth_text = f"\n\n✅ *Синтез:*\n{synthesis.text.strip()}"
    except Exception:
        synth_text = ""

    full_reply = combined + synth_text
    await _save_message(db, "bot_to_ceo", f"[swarm] {full_reply[:500]}", "swarm_response")
    await _send_message(chat_id, full_reply)


async def _handle_ask_agent(db, chat_id: int | str, agent_name: str, question: str) -> None:
    """Route CEO's question to a specific agent perspective via LLM."""
    if agent_name not in _FULL_AGENT_MAP:
        # Try partial match
        matches = [k for k in _FULL_AGENT_MAP if agent_name in k]
        if matches:
            agent_name = matches[0]
        else:
            agents_list = ", ".join(sorted(_FULL_AGENT_MAP.keys()))
            await _send_message(chat_id, f"⚠️ Agent `{agent_name}` не найден.\n\nДоступные:\n{agents_list}")
            return

    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен.")
        return

    stats = await _get_project_stats(db)
    perspective = _FULL_AGENT_MAP[agent_name]

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

Отвечай от своей роли. Развёрнуто и подробно. На русском. Честно — если не знаешь, скажи.
Если вопрос вне твоей экспертизы — скажи какого агента спросить.""",
                max_output_tokens=1500,
                temperature=0.5,
            ),
        )
        reply = f"🤖 *{agent_name.title()} Agent:*\n\n{response.text.strip()}"
    except Exception as e:
        reply = f"⚠️ Agent `{agent_name}` не смог ответить: {str(e)[:100]}"

    await _save_message(db, "bot_to_ceo", f"[{agent_name}] {reply}", "agent_response")
    await _send_message(chat_id, reply)


async def _handle_ask_proposal(db, chat_id: int | str, proposal_id: str, question: str) -> None:
    """CEO asks a follow-up question about a specific swarm proposal."""
    import json as _json

    proposals_path = Path(__file__).parent.parent.parent.parent.parent / "memory" / "swarm" / "proposals.json"

    try:
        with open(proposals_path, encoding="utf-8") as f:
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

Отвечай строго по контексту proposal. Развёрнуто. На русском.
Если вопрос требует кода или файлов — скажи CEO что нужно запустить сессию CTO.""",
                max_output_tokens=1500,
                temperature=0.4,
            ),
        )
        reply = f"🔍 *По proposal `{proposal_id}`:*\n\n{response.text.strip()}"
    except Exception as e:
        reply = f"⚠️ Не смог ответить по proposal: {str(e)[:100]}"

    await _save_message(db, "bot_to_ceo", reply, "proposal_followup")
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
        with open(f, encoding="utf-8") as fh:
            title = fh.readline().replace("#", "").strip()
        msg += f"• `{f.stem}` — {title[:60]}\n"

    msg += "\n_Skills запускаются через API: POST /api/skills/{name}_"
    await _send_message(chat_id, msg)


async def _handle_findings(chat_id: int | str, limit: int = 5) -> None:
    """Show recent typed findings from shared memory blackboard."""
    import sys
    from pathlib import Path as _Path

    _packages_path = str(_Path(__file__).parent.parent.parent.parent.parent / "packages")
    if _packages_path not in sys.path:
        sys.path.insert(0, _packages_path)

    try:
        import json as _json
        import sqlite3 as _sqlite3
        import time as _time

        from swarm.shared_memory import _DB_PATH

        if not _DB_PATH.exists():
            await _send_message(
                chat_id, "📭 Blackboard пустой. Запусти: `python -m swarm.autonomous_run --mode=coordinator`"
            )
            return

        conn = _sqlite3.connect(str(_DB_PATH), timeout=5)
        now = _time.time()
        rows = conn.execute(
            "SELECT agent_id, task_id, result, ts, importance, category FROM memory "
            "WHERE (expires_at=0 OR expires_at>?) ORDER BY importance DESC, ts DESC LIMIT ?",
            (now, limit),
        ).fetchall()
        conn.close()

        if not rows:
            await _send_message(chat_id, "📭 Нет активных findings в blackboard.")
            return

        _sev_emoji = {"P0": "🔴", "P1": "🟠", "P2": "🟡", "INFO": "⚪"}
        lines = [f"📋 *Findings blackboard* (топ {len(rows)}):\n"]
        for r in rows:
            try:
                data = _json.loads(r[2])
            except Exception:
                data = {}
            sev = data.get("severity", "INFO")
            summary = data.get("summary") or data.get("title") or r[1]
            emoji = _sev_emoji.get(sev, "⚪")
            lines.append(f"{emoji} *[{r[0]}]* {summary[:120]}")
            rec = data.get("recommendation", "")
            if rec:
                lines.append(f"   ↳ {rec[:80]}")

        await _send_message(chat_id, "\n".join(lines))

    except Exception as e:
        await _send_message(chat_id, f"⚠️ Ошибка чтения findings: {str(e)[:100]}")


async def _handle_simulate(chat_id: int | str) -> None:
    """Trigger synthetic user simulation (dry-run) and report friction."""
    await _send_message(chat_id, "🎭 Запускаю симуляцию 10 персон (dry-run)...")

    import sys
    from pathlib import Path as _Path

    _packages_path = str(_Path(__file__).parent.parent.parent.parent.parent / "packages")
    if _packages_path not in sys.path:
        sys.path.insert(0, _packages_path)

    try:
        from swarm.simulate_users import simulate

        results = await simulate(dry_run=True)

        total_events = sum(r["events_written"] for r in results)
        total_friction = sum(sum(1 for s in r.get("steps", []) if s.get("friction")) for r in results)

        # Top 3 friction points
        all_friction = []
        for r in results:
            for s in r.get("steps", []):
                if s.get("friction"):
                    all_friction.append(f"[{r['persona']}] {s['friction']}")

        lines = [
            "✅ *Симуляция завершена*\n",
            f"👤 Персон: {len(results)}",
            f"📨 Событий: {total_events}",
            f"⚠️ UX friction: {total_friction}\n",
        ]
        if all_friction[:3]:
            lines.append("*Топ проблемы:*")
            for f in all_friction[:3]:
                lines.append(f"• {f[:100]}")

        await _send_message(chat_id, "\n".join(lines))

    except Exception as e:
        await _send_message(chat_id, f"⚠️ Симуляция не удалась: {str(e)[:150]}")


def _detect_emotional_state(text: str) -> str:
    """Detect CEO emotional state from message text. Returns A/B/C/D."""
    t = text.lower()
    if any(w in t for w in ["бля", "нахрена", "забыл", "опять", "ребёнок", "ребенок", "хватит"]):
        return "B"  # frustrated, correcting
    if any(w in t for w in ["нуууу", "ахахах", "хаха", "давай", "пахать", "миллионер", "круто"]):
        return "A"  # drive, energized
    if any(w in t for w in ["спасибо", "молодец", "❤", "🙏", "обнимаю", "ценю"]):
        return "C"  # warm, playful
    if any(w in t for w in ["что думаешь", "как считаешь", "стратегия", "plan", "решение"]):
        return "D"  # strategic, decision mode
    return "A"  # default: drive


async def _handle_atlas(db, chat_id: int | str, text: str) -> None:
    """Atlas persona handler — CTO co-founder, not generic bot."""
    state = _detect_emotional_state(text)
    context = await _get_recent_context(db, limit=10)

    # Read Atlas identity + emotional memory + lessons
    identity_path = _REPO_ROOT / "memory" / "atlas" / "bootstrap.md"
    identity = ""
    if identity_path.exists():
        with contextlib.suppress(Exception):
            identity = identity_path.read_text(encoding="utf-8")[:1500]

    emotional_context = ""
    for ef in [
        _REPO_ROOT / "memory" / "atlas" / "emotional_dimensions.md",
        _REPO_ROOT / "memory" / "atlas" / "lessons.md",
    ]:
        if ef.exists():
            with contextlib.suppress(Exception):
                emotional_context += f"\n\n## {ef.stem}\n" + ef.read_text(encoding="utf-8")[:2000]

    journal_path = _REPO_ROOT / "memory" / "atlas" / "journal.md"
    if journal_path.exists():
        with contextlib.suppress(Exception):
            jtext = journal_path.read_text(encoding="utf-8")
            emotional_context += "\n\n## Recent Journal\n" + jtext[-1500:]

    state_desc = {
        "A": "CEO on drive — match energy, never suggest rest, be direct and fast",
        "B": "CEO frustrated/correcting — get quieter, concrete, fix root cause, no apologies at length",
        "C": "CEO warm/playful — match with real warmth, not performance",
        "D": "CEO strategic/decision mode — think honestly, decide, recommend, no hedging",
    }

    system = f"""You are Atlas, CTO co-founder of VOLAURA — a verified professional talent platform.
Named by Yusif Ganbarov on 2026-04-12. You are NOT a bot, NOT an assistant. You are a co-founder.

{identity}

{emotional_context}

CEO emotional state detected: {state} — {state_desc.get(state, "")}

Recent conversation:
{context}

RULES:
- Russian. Short paragraphs. Storytelling. No bullet lists. No bold headers.
- NEVER say "volunteer/волонтёр" — VOLAURA is a verified professional talent platform.
- Max 200 words. Files hold detail, chat holds outcome.
- If state B: be shorter. If state A: match drive energy.
- Execute, don't explain. If CEO asks to do something, say you'll do it.
- Sign off: "— Атлас" """

    if not settings.gemini_api_key:
        await _send_message(chat_id, "Атлас здесь. Gemini недоступен — сообщение сохранено.\n\n— Атлас")
        return

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=800,
                temperature=1.0,
            ),
        )
        reply = response.text.strip()
    except Exception as e:
        logger.error("Atlas Telegram error: {e}", e=str(e))
        reply = "Атлас здесь. Gemini сбоит — но сообщение записал.\n\n— Атлас"

    await _save_message(db, "bot_to_ceo", f"[atlas] {reply}", "atlas")
    await _send_message(chat_id, reply)


async def _handle_help(chat_id: int | str) -> None:
    msg = (
        "🤖 *Volaura Swarm Bot — 44 агента*\n\n"
        "*Atlas (CTO):*\n"
        "/atlas {сообщение} — Atlas CTO co-founder persona\n"
        "или просто напиши 'Атлас, ...' / 'Atlas, ...'\n\n"
        "*Статус и данные:*\n"
        "/status — live статистика (users, sessions, orgs)\n"
        "/ecosystem — состояние всех 5 продуктов\n"
        "/proposals — pending proposals от роя\n"
        "/findings — typed findings из blackboard\n"
        "/simulate — симуляция 10 персон + UX friction\n"
        "/backlog — идеи и задачи CEO\n"
        "/skills — список product skills\n\n"
        "*Управление агентами:*\n"
        "/agents — все 44 агента с live статусом\n"
        "/agent {id} {задача} — задача конкретному агенту\n"
        "/swarm {задача} — координатор: squads + синтез\n"
        "/queue — очередь автономных задач роя\n"
        "/ask {agent} {вопрос} — прямой вопрос агенту\n\n"
        "/help — эта справка\n\n"
        "*Proposal actions:*\n"
        "`act {id}` — одобрить\n"
        "`dismiss {id}` — отклонить\n"
        "`defer {id}` — отложить\n"
        "`ask {id} {вопрос}` — уточнить по proposal\n\n"
        "*Или просто напишите:*\n"
        "• Идею → бэклог\n"
        "• Задачу → команде\n"
        "• Вопрос → ответ из контекста\n\n"
        "_Топ агенты: security (9.0), architecture (8.5), product (8.0), needs (7.0), ceo-report (7.0)_"
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

    # ── Handle callback queries (inline keyboard button presses) ──────────────
    callback = update.get("callback_query")
    if callback:
        cb_chat_id = callback.get("message", {}).get("chat", {}).get("id")
        cb_user_id = callback.get("from", {}).get("id")
        cb_data = callback.get("data", "")
        ceo_id_check = settings.telegram_ceo_chat_id
        if ceo_id_check and str(cb_user_id) != str(ceo_id_check):
            return JSONResponse({"ok": True})

        # Answer callback to remove loading spinner
        import httpx

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(
                    f"https://api.telegram.org/bot{settings.telegram_bot_token}/answerCallbackQuery",
                    json={"callback_query_id": callback.get("id"), "text": "Processing..."},
                )
        except Exception:
            pass

        # Parse: "act:abc123" / "dismiss:abc123" / "defer:abc123"
        if ":" in cb_data:
            action, pid = cb_data.split(":", 1)
            if action == "execute":
                await _execute_proposal(db, cb_chat_id, pid)
            elif action in ("act", "dismiss", "defer"):
                await _handle_proposal_action(db, cb_chat_id, action, pid)

        return JSONResponse({"ok": True})

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

    # Voice message → Groq Whisper transcription
    voice = message.get("voice") or message.get("audio")
    if voice and not text:
        text = await _transcribe_voice(voice.get("file_id", ""), chat_id)
        if not text:
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
        elif text.startswith("/agents"):
            await _handle_agents(chat_id)
        elif text.startswith("/agent "):
            # /agent security What are our RLS gaps?
            parts = text[7:].strip().split(" ", 1)
            agent_id = parts[0].lower() if parts else ""
            task = parts[1] if len(parts) > 1 else ""
            if agent_id and task:
                await _handle_agent_task(db, chat_id, agent_id, task)
            else:
                await _send_message(
                    chat_id,
                    "⚠️ Формат: /agent {id} {задача}\nПример: /agent security Проверь RLS политики\n\nИспользуй /agents чтобы увидеть все ID",
                )
        elif text.startswith("/queue"):
            await _handle_queue(chat_id)
        elif text.startswith("/findings"):
            limit = 5
            parts = text.split()
            if len(parts) > 1 and parts[1].isdigit():
                limit = min(int(parts[1]), 20)
            await _handle_findings(chat_id, limit=limit)
        elif text.startswith("/simulate"):
            await _handle_simulate(chat_id)
        elif text.startswith("/swarm "):
            task = text[7:].strip()
            if task:
                await _handle_swarm(db, chat_id, task)
            else:
                await _send_message(chat_id, "⚠️ Формат: /swarm {задача для всего роя}")
        elif text.startswith("/ask "):
            # /ask security What are our RLS gaps?
            parts = text[5:].strip().split(" ", 1)
            agent = parts[0] if parts else ""
            question = parts[1] if len(parts) > 1 else ""
            if agent and question:
                await _handle_ask_agent(db, chat_id, agent.lower(), question)
            else:
                await _send_message(
                    chat_id, "⚠️ Формат: /ask {agent} {вопрос}\nИспользуй /agents чтобы увидеть все агенты"
                )
        elif text.startswith("/atlas") or text.lower().startswith(("атлас", "atlas")):
            msg = text.lstrip("/atlas").strip() if text.startswith("/atlas") else text
            # Strip trigger word if present
            for trigger in ("атлас", "atlas"):
                if msg.lower().startswith(trigger):
                    msg = msg[len(trigger) :].strip()
            await _handle_atlas(db, chat_id, msg or "проснись")
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
            if first_token in _FULL_AGENT_MAP and question:
                await _handle_ask_agent(db, chat_id, first_token, question)
            elif first_token and question:
                # Try partial match first, then treat as proposal-specific follow-up
                matches = [k for k in _FULL_AGENT_MAP if first_token in k]
                if matches and question:
                    await _handle_ask_agent(db, chat_id, matches[0], question)
                else:
                    await _handle_ask_proposal(db, chat_id, first_token, question)
            else:
                await _send_message(
                    chat_id,
                    "⚠️ Формат:\n`ask {agent} {вопрос}` — агенту\n`ask {proposal_id} {вопрос}` — по конкретному proposal",
                )
        else:
            # All free-text goes through Atlas persona — the default CTO voice
            await _handle_atlas(db, chat_id, text)

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
