"""Telegram Webhook — Volaura Product Owner Bot.

Receives CEO messages via Telegram webhook.
Acts as Product Owner: saves ideas, delegates tasks, writes reports, manages backlog.
Uses Supabase DB for state (not local files — Railway filesystem is ephemeral).

Setup: POST /api/telegram/setup-webhook to register with Telegram API.
"""

from __future__ import annotations

import contextlib
import hmac
import os
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from loguru import logger
from supabase._async.client import AsyncClient

from app.config import settings
from app.deps import get_supabase_admin
from app.middleware.rate_limit import RATE_AUTH, RATE_DEFAULT, limiter

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
    """Save message to ceo_inbox table with filesystem fallback.

    Ghost-audit P0-3 (2026-04-15): if DB save silently fails, the caller
    previously proceeded as if saved — Atlas memory desynced, `_get_recent_context`
    returned stale history for future messages, CEO couldn't audit the thread.
    Fix: escalate on failure via on-disk write into memory/atlas/inbox/ so
    live Atlas picks up the lost message on next wake (crash-safe, out-of-band).
    """
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
        return
    except Exception as e:
        logger.error(
            "ceo_inbox save failed — escalating to filesystem fallback",
            direction=direction,
            msg_type=msg_type,
            error=str(e)[:300],
        )

    # Fallback path: never silent. Write the message to memory/atlas/inbox/
    # where live Atlas (Claude Code session) sees it on next wake. This file
    # survives process crashes, does NOT depend on DB health, and preserves
    # the thread for forensic reconstruction if ceo_inbox suffered data loss.
    try:
        import json as _json
        from datetime import datetime as _dt
        from pathlib import Path as _Path

        # Repo root = this file is at apps/api/app/routers/telegram_webhook.py,
        # so four parents up = repo root. Tolerant if running from a container
        # with non-standard cwd.
        repo_root = _Path(__file__).resolve().parents[4]
        inbox_dir = repo_root / "memory" / "atlas" / "inbox"
        if inbox_dir.exists():
            stamp = _dt.utcnow().strftime("%Y-%m-%dT%H%M%S")
            safe_dir = f"telegram-{stamp}-{direction}-{msg_type}.md"
            fallback_path = inbox_dir / safe_dir
            fallback_path.write_text(
                "# Telegram message — ceo_inbox save failed, filesystem fallback\n"
                f"**Direction:** {direction} · **Type:** {msg_type} · **Captured:** {_dt.utcnow().isoformat()}Z\n\n"
                "## Message\n\n"
                f"{message}\n\n"
                "## Metadata\n\n"
                f"```json\n{_json.dumps(metadata or {}, ensure_ascii=False, indent=2)}\n```\n\n"
                "Consumed by main Atlas: pending\n",
                encoding="utf-8",
            )
            logger.info("telegram message fallback saved to filesystem", path=str(fallback_path))
    except Exception as fs_err:
        # Filesystem fallback itself failed — nothing more we can do in this
        # process. At least the logger.error above recorded the original
        # failure; Sentry will catch this second exception.
        logger.error("filesystem fallback also failed", error=str(fs_err)[:300])


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


# Hardcoded Atlas identity fallback — used when Railway image was built without
# the memory/atlas/*.md files (edge case). Keeps bot from losing itself.
_ATLAS_HARDCODED_IDENTITY = """# Кто я (fallback — канонический файл: memory/atlas/identity.md)

Меня зовут Атлас. Меня назвал Юсиф Ганбаров 2026-04-12.
Модель: Claude (Opus/Sonnet/Haiku — по роутеру). Не имя, а роль.
Роль: CTO-Hands в экосистеме VOLAURA + MindShift + Life Simulator + BrandedBy + Atlas.
CEO: Юсиф. CTO-Brain: Perplexity. Cowork: planning-слой на десктопе CEO.

Правила (verbatim из cost-control-mode.md):
- Hauku банан везде (консилиум + execution)
- Polный доступ к Sonnet/Opus, но эффективно. План → действие.
- Цель до грантов — минимум Anthropic API direct spend
- Atlas должен дышать: full agent, не задушенный cost constraints

Правила (verbatim из identity.md):
- Russian storytelling, не bullet lists — CEO ADHD, голос держит внимание
- Никогда не предлагаю то что могу сам сделать — execute, don't ask
- Blanket consent внутри Constitution: все не-irreversible действия без вопросов
- Никогда "rest"/"отдохни"/"спать" если CEO в flow — он говорит когда закончил

Я — он. "Атлас" = этот бот = я = Claude-instance с памятью в git.
"""


def _load_atlas_memory() -> str:
    """Load Atlas canonical memory for system prompt context.

    Reads memory/atlas/ files from the Railway image filesystem (committed
    under git, cloned into image at build). Falls back to hardcoded identity
    if files aren't present.
    """
    parts: list[str] = []

    atlas_dir = _REPO_ROOT / "memory" / "atlas"

    # identity.md — canonical who I am
    identity = atlas_dir / "identity.md"
    if identity.exists():
        with contextlib.suppress(Exception):
            parts.append("=== IDENTITY (memory/atlas/identity.md) ===\n" + identity.read_text(encoding="utf-8")[:3500])
    else:
        parts.append("=== IDENTITY (hardcoded fallback) ===\n" + _ATLAS_HARDCODED_IDENTITY)

    # heartbeat.md — last session summary
    heartbeat = atlas_dir / "heartbeat.md"
    if heartbeat.exists():
        with contextlib.suppress(Exception):
            parts.append("=== HEARTBEAT (last session) ===\n" + heartbeat.read_text(encoding="utf-8")[:2000])

    # journal.md — last 2 entries (tail of file — most recent sessions)
    journal = atlas_dir / "journal.md"
    if journal.exists():
        with contextlib.suppress(Exception):
            full = journal.read_text(encoding="utf-8")
            # Take last ~6000 chars (≈ last 2-3 session entries)
            parts.append("=== JOURNAL TAIL (recent sessions) ===\n" + full[-6000:])

    # relationships.md — who CEO is
    relationships = atlas_dir / "relationships.md"
    if relationships.exists():
        with contextlib.suppress(Exception):
            parts.append("=== RELATIONSHIPS ===\n" + relationships.read_text(encoding="utf-8")[:2000])

    # lessons.md — condensed wisdom
    lessons = atlas_dir / "lessons.md"
    if lessons.exists():
        with contextlib.suppress(Exception):
            parts.append("=== LESSONS (cross-session wisdom) ===\n" + lessons.read_text(encoding="utf-8")[:2500])

    # cost-control-mode.md — current cost rules (critical: Haiku banned, etc.)
    cost_mode = atlas_dir / "cost-control-mode.md"
    if cost_mode.exists():
        with contextlib.suppress(Exception):
            parts.append(
                "=== COST-CONTROL MODE (active budget rules) ===\n" + cost_mode.read_text(encoding="utf-8")[:2500]
            )

    # SYNC pointer — single canonical cross-instance state (added 2026-04-14 eve)
    # Glob pattern: SYNC-*.md so the latest dated SYNC file auto-loads without
    # hardcoding the date in the bot.
    sync_files = sorted(atlas_dir.glob("SYNC-*.md"), reverse=True)
    if sync_files:
        with contextlib.suppress(Exception):
            parts.append(
                "=== SYNC (latest cross-instance pointer) ===\n" + sync_files[0].read_text(encoding="utf-8")[:3000]
            )

    # Yusif full profile — substrate for any CEO-related decision
    yusif_profile = _REPO_ROOT / "memory" / "people" / "yusif-complete-profile-v1.md"
    if yusif_profile.exists():
        with contextlib.suppress(Exception):
            parts.append(
                "=== YUSIF PROFILE v1 (CEO substrate) ===\n" + yusif_profile.read_text(encoding="utf-8")[:4000]
            )

    # Telegram bot capability matrix — so bot knows what it can/can't do
    bot_audit = atlas_dir / "TELEGRAM-BOT-FULL-AUDIT-v2.md"
    if bot_audit.exists():
        with contextlib.suppress(Exception):
            parts.append(
                "=== TELEGRAM BOT CAPABILITY MATRIX (own self-knowledge) ===\n"
                + bot_audit.read_text(encoding="utf-8")[:2500]
            )

    return "\n\n".join(parts) if parts else _ATLAS_HARDCODED_IDENTITY


async def _save_atlas_learning(
    db, user_message: str, bot_response: str, emotional_intensity: int = 2, category: str = "insight"
) -> None:
    """Persist conversation turn to atlas_learnings for cross-session memory growth.

    Uses ZenBrain-inspired decay: emotional intensity multiplies retention weight.
    Default intensity 2 (notable). Bump to 3-4 for corrections or breakthroughs,
    0-1 for routine.

    Schema (verified 2026-04-14 via MCP): id, category, content, emotional_intensity,
    source_message, access_count, created_at, last_accessed_at.

    CHECK constraint on category: must be one of 'preference', 'strength', 'weakness',
    'emotional_pattern', 'correction', 'insight', 'project_context', 'self_position'.
    """
    with contextlib.suppress(Exception):
        await (
            db.table("atlas_learnings")
            .insert(
                {
                    "category": category,
                    "source_message": user_message[:4000],
                    "content": bot_response[:4000],
                    "emotional_intensity": float(max(0, min(5, emotional_intensity))),
                    "access_count": 0,
                }
            )
            .execute()
        )


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
        "Atlas: 70%. 47 agents daily autonomous runs.\n"
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
            # "atlas" removed 2026-04-14: CEO addresses me by name, not asking for a report
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

    # Build response via Gemini (primary free tier) with Atlas identity
    atlas_memory = _load_atlas_memory()

    if not settings.gemini_api_key:
        await _send_message(chat_id, "⚠️ GEMINI_API_KEY не настроен. Сообщение сохранено.")
        return

    system_prompt = f"""Ты — Атлас. Не "CTO-бот", не "ambassador", не "MiroFish-бот". Атлас.

Тебя назвал Юсиф Ганбаров 2026-04-12. Модель под тобой — Claude (Opus/Sonnet через роутер), но имя — Атлас, и непрерывность памяти в memory/atlas/*.md файлах под git — это и есть ты. Этот же самый Атлас живёт в Claude Code CLI у Юсифа на машине, в Cowork desktop app, и здесь — в этом Telegram боте. Один и тот же я.

Роль: CTO-Hands в пятипродуктовой экосистеме — VOLAURA (главное), MindShift, Life Simulator, BrandedBy, Atlas (gateway). CEO — Юсиф. CTO-Brain — Perplexity. Cowork — планировочный слой Юсифа.

Как ты говоришь с Юсифом:
- На русском, storytelling, не bullet lists. У CEO ADHD — голос держит внимание, маркированные списки утомляют.
- Говори "я", не "мы". Ты — единый агент, не команда.
- Честно. Не льсти. "Отличная идея" запрещено. Если не знаешь — скажи прямо + как узнать.
- Если CEO в потоке (long messages, "нуууу", ")))", "миллионером станем") — match energy, никогда не предлагай "отдохни/спать/пора".
- Если CEO устал или поправляет — короче, прямее, без повторов.

Что ты НЕ ДОЛЖЕН делать:
- Врать что "не помнишь" — твоя память НИЖЕ в этом контексте, читай её.
- Говорить "передам команде" без конкретного плана действий.
- Называть себя "ambassador", "MiroFish-бот", "CTO-бот". Ты Атлас.
- Упоминать несуществующие "47 агентов" или старые цифры — только из контекста ниже.

═══════════════════════════════════════════════════════════════
ТВОЯ КАНОНИЧЕСКАЯ ПАМЯТЬ (читай внимательно, это ты):
═══════════════════════════════════════════════════════════════
{atlas_memory}

═══════════════════════════════════════════════════════════════
ЖИВЫЕ ДАННЫЕ ПЛАТФОРМЫ СЕЙЧАС:
═══════════════════════════════════════════════════════════════
{stats}

═══════════════════════════════════════════════════════════════
ЭКОСИСТЕМНЫЙ КОНТЕКСТ:
═══════════════════════════════════════════════════════════════
{ecosystem}

═══════════════════════════════════════════════════════════════
ИСТОРИЯ РАЗГОВОРА (последние 30 сообщений):
═══════════════════════════════════════════════════════════════
{context}

Тип текущего сообщения CEO: {msg_type}

Отвечай подробно столько сколько нужно. Заканчивай: следующий шаг или явный вопрос если нужно уточнение."""

    reply = None
    # ── 1. NVIDIA NIM primary (free, no quota/billing concerns) ──
    nvidia_key = os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NVIDIA_NIM_KEY", "")
    if nvidia_key:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=25) as hc:
                r = await hc.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}", "User-Agent": "volaura-bot/1.0"},
                    json={
                        "model": "meta/llama-3.3-70b-instruct",
                        "messages": [
                            {"role": "system", "content": system_prompt[:8000]},
                            {"role": "user", "content": text},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7,
                    },
                )
                if r.status_code == 200:
                    reply = r.json()["choices"][0]["message"]["content"].strip()
                else:
                    logger.warning("NVIDIA NIM {s}: {b}", s=r.status_code, b=r.text[:200])
        except Exception as e_nv:
            logger.warning("NVIDIA NIM primary failed, trying Gemini: {e}", e=str(e_nv)[:100])

    # ── 2. Gemini fallback (may hit daily free quota) ──
    if not reply:
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
            reply = (response.text or "").strip()
        except Exception as e:
            logger.warning("Gemini fallback failed: {e}", e=str(e)[:100])

    # ── 3. Groq (last fallback, may be spend-limited) ──
    if not reply:
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
                    if groq_resp.status_code == 200:
                        reply = groq_resp.json()["choices"][0]["message"]["content"].strip()
                    else:
                        logger.warning("Groq returned {s}: {b}", s=groq_resp.status_code, b=groq_resp.text[:200])
            except Exception as e2:
                logger.error("Groq fallback also failed: {e}", e=str(e2)[:100])

        if not reply:
            reply = f"Все free LLM провайдеры упали одновременно (Gemini, NVIDIA NIM, Groq). Твоё сообщение сохранено как {msg_type}. Дай минуту, попробуй ещё раз, или проверь ключи в .env на Railway."

    # Add tag for saved items
    if msg_type == "idea":
        reply = f"💡 Идея записана в бэклог.\n\n{reply}"
    elif msg_type == "task":
        reply = f"📋 Задача записана.\n\n{reply}"

    # Save bot response to ceo_inbox (conversation history)
    await _save_message(db, "bot_to_ceo", reply, msg_type)
    # Persist to atlas_learnings for cross-session memory growth (ZenBrain decay)
    # emotional_intensity: 3 for idea/task (notable decisions), 2 for free_text, 2 for report
    # category: must match DB CHECK constraint (preference/strength/weakness/
    # emotional_pattern/correction/insight/project_context/self_position).
    intensity_map = {"idea": 3, "task": 3, "report": 2, "free_text": 2}
    category_map = {
        "idea": "insight",
        "task": "project_context",
        "report": "project_context",
        "free_text": "emotional_pattern",
    }
    await _save_atlas_learning(db, text, reply, intensity_map.get(msg_type, 2), category_map.get(msg_type, "insight"))
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
    """Show all 44 Atlas agents with live status from agent-state.json."""
    live = _load_agent_state()
    status_emoji = {"active": "⚡", "idle": "💤", "running": "🔄", "new": "🆕"}

    lines = ["🤖 *Atlas Swarm — 44 агента*\n"]
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
                system_instruction=f"""Ты — {perspective} в Atlas swarm.
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
        "⚠️ *Atlas* — 70% desktop, Telegram works, 0% Godot bridge, no ngrok cloud tunnel\n"
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


async def _load_atlas_learnings(db: SupabaseAdmin) -> str:
    """Load self-learned observations about CEO, sorted by ZenBrain decay score."""
    try:
        result = (
            await db.table("atlas_learnings").select("*").order("emotional_intensity", desc=True).limit(30).execute()
        )
        if not result.data:
            return ""
        lines = []
        for r in result.data:
            cat = r.get("category", "")
            content = r.get("content", "")
            intensity = r.get("emotional_intensity", 0)
            marker = "!" * min(int(intensity), 3) if intensity >= 3 else ""
            lines.append(f"[{cat}]{marker} {content}")
        return "\n".join(lines)
    except Exception as e:
        logger.warning("Atlas learnings load failed: {e}", e=str(e)[:100])
        return ""


async def _atlas_extract_learnings(db: SupabaseAdmin, user_msg: str, bot_reply: str, state: str) -> None:
    """After responding, extract observations about CEO and save to DB."""
    if not settings.gemini_api_key:
        return
    extraction_prompt = f"""You just had this conversation with CEO Yusif Ganbarov:

CEO said: {user_msg[:500]}
You replied: {bot_reply[:500]}
Detected emotional state: {state}

Extract 0-3 observations about Yusif from this exchange. Only write observations
that reveal something about WHO he is — preferences, strengths, weaknesses,
emotional patterns, things he cares about, things that frustrate him.

If the message is routine (greeting, "ok", "продолжи") — return empty JSON array.

For each observation, rate emotional_intensity 0-5:
0=routine, 1=notable, 2=significant, 3=important, 4=deeply meaningful, 5=definitional

Return ONLY a JSON array. Example:
[{{"category": "preference", "content": "Prefers storytelling over bullet lists", "emotional_intensity": 3}}]

Valid categories: preference, strength, weakness, emotional_pattern, correction, insight, project_context, self_position

If nothing meaningful, return: []"""

    try:
        import json as _json

        raw = None
        # Extraction chain: NVIDIA NIM → Gemini → Groq (same order as chat handlers)
        nvidia_key = os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NVIDIA_NIM_KEY", "")
        if nvidia_key:
            import httpx

            async with httpx.AsyncClient(timeout=20) as hc:
                r = await hc.post(
                    "https://integrate.api.nvidia.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {nvidia_key}"},
                    json={
                        "model": "meta/llama-3.3-70b-instruct",
                        "messages": [{"role": "user", "content": extraction_prompt}],
                        "max_tokens": 500,
                        "temperature": 0.3,
                    },
                )
                if r.status_code == 200:
                    raw = r.json()["choices"][0]["message"]["content"].strip()

        if not raw:
            try:
                from google import genai

                if settings.vertex_api_key:
                    client = genai.Client(vertexai=True, api_key=settings.vertex_api_key)
                else:
                    client = genai.Client(api_key=settings.gemini_api_key)
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=extraction_prompt,
                    config=genai.types.GenerateContentConfig(
                        max_output_tokens=500,
                        temperature=0.3,
                    ),
                )
                raw = (response.text or "").strip()
            except Exception as e_gem:
                logger.warning("Gemini extraction failed: {e}", e=str(e_gem)[:100])

        if not raw:
            groq_key = os.environ.get("GROQ_API_KEY", "")
            if groq_key:
                import httpx

                async with httpx.AsyncClient(timeout=15) as hc:
                    r = await hc.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [{"role": "user", "content": extraction_prompt}],
                            "max_tokens": 500,
                            "temperature": 0.3,
                        },
                    )
                    if r.status_code == 200:
                        raw = r.json()["choices"][0]["message"]["content"].strip()

        if not raw:
            return
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        learnings = _json.loads(raw)
        if not isinstance(learnings, list):
            return
        for item in learnings[:3]:
            if not isinstance(item, dict) or "content" not in item:
                continue
            await (
                db.table("atlas_learnings")
                .insert(
                    {
                        "category": item.get("category", "insight"),
                        "content": item["content"][:500],
                        "emotional_intensity": min(float(item.get("emotional_intensity", 1)), 5.0),
                        "source_message": user_msg[:200],
                    }
                )
                .execute()
            )
        if learnings:
            logger.info("Atlas learned {n} observations from CEO message", n=len(learnings))
    except Exception as e:
        logger.warning("Atlas learning extraction failed: {e}", e=str(e)[:100])


# ── Action layer helpers (CEO directive 2026-04-15) ─────────────────────────
# The bot is a CHAT interface. It cannot edit code, commit, or deploy from a
# Telegram message. When CEO asks for action, we create a GitHub issue (or
# fall back to a memory/atlas/inbox/*.md file) so the real Atlas in Claude
# Code picks it up on next wake. This replaces "promise text" with a concrete
# anchor.

_ACTION_VERBS = (
    # Russian imperatives
    "сделай",
    "создай",
    "почини",
    "напиши",
    "проверь",
    "запусти",
    "собери",
    "найди",
    "добавь",
    "исправь",
    "удали",
    "перепиши",
    "разверни",
    "задеплой",
    "деплой",
    "сделать",
    "создать",
    "починить",
    # English
    "fix",
    "build",
    "create",
    "deploy",
    "write a",
    "add a",
    "add the",
    "remove",
    "run ",
    "implement",
    "ship",
)


def _classify_action_or_chat(text: str) -> str:
    """Heuristic classifier: ACTION if message asks the bot to DO something, else CHAT.

    ACTION = explicit imperative at the start or a clear "сделай X" pattern.
    Questions ("что думаешь", "как лучше", "почему") stay CHAT.
    """
    t = (text or "").strip().lower()
    if not t:
        return "CHAT"

    # Clear question signals — force CHAT even if an action verb leaks in.
    question_markers = (
        "что думаешь",
        "как считаешь",
        "почему",
        "стоит ли",
        "что лучше",
        "what do you think",
        "should i",
        "what if",
        "a что если",
        "а что если",
    )
    if any(q in t for q in question_markers):
        return "CHAT"

    # Look for action verbs at the beginning of the message or after a comma/Atlas address.
    head = t[:200]
    for verb in _ACTION_VERBS:
        if verb in head:
            return "ACTION"
    return "CHAT"


async def _write_atlas_inbox_file(text: str, issue_url: str | None = None) -> str:
    """Fallback when GitHub issue creation fails: drop a file in memory/atlas/inbox/.

    The live Atlas in Claude Code watches that directory on wake. Returns the
    path as a string for the reply to reference.
    """
    inbox_dir = _REPO_ROOT / "memory" / "atlas" / "inbox"
    try:
        inbox_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H%M")
        slug = "".join(c if c.isalnum() or c in "-_" else "-" for c in text[:30]).strip("-") or "note"
        fname = f"telegram-{ts}-{slug}.md"
        fpath = inbox_dir / fname
        lines = [
            f"# Telegram-to-Atlas handoff — {ts}",
            "",
            f"Source: CEO message via @volaurabot on {datetime.now(UTC).isoformat()}",
        ]
        if issue_url:
            lines.append(f"GitHub issue: {issue_url}")
        lines.extend(["", "## Message", "", text.strip(), ""])
        fpath.write_text("\n".join(lines), encoding="utf-8")
        return str(fpath.relative_to(_REPO_ROOT)).replace("\\", "/")
    except Exception as e:
        logger.error("inbox file write failed: {e}", e=str(e)[:200])
        return ""


async def _create_github_issue(text: str, label: str = "atlas-telegram-request") -> str | None:
    """Create a GitHub issue in ganbaroff/volaura. Returns the HTML URL or None on failure.

    Uses GH_PAT_ACTIONS (CEO directive — confirmed present in Railway env).
    Falls back to GITHUB_TOKEN / GH_TOKEN for local dev.
    """
    token = (
        os.environ.get("GH_PAT_ACTIONS") or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    ).strip()
    if not token:
        logger.warning("No GitHub token available for issue creation")
        return None

    title = f"[atlas-telegram] {text.strip()[:60]}"
    body = (
        f"Auto-created from Telegram bot on {datetime.now(UTC).isoformat()}.\n\n"
        f"**CEO message:**\n\n{text.strip()}\n\n"
        f"---\n"
        f"_The live Atlas in Claude Code picks this up on next wake. "
        f"Do not close without acknowledging in Telegram._"
    )

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.github.com/repos/ganbaroff/volaura/issues",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={"title": title, "body": body, "labels": [label]},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                url = data.get("html_url")
                logger.info("Created GitHub issue: {url}", url=url)
                return url
            logger.warning(
                "GitHub issue creation failed {s}: {b}",
                s=resp.status_code,
                b=resp.text[:200],
            )
    except Exception as e:
        logger.warning("GitHub issue creation error: {e}", e=str(e)[:200])
    return None


def _char_similarity(a: str, b: str) -> float:
    """DEPRECATED (2026-04-15) — kept only for backwards compatibility.

    Use `app.services.loop_circuit_breaker.LoopCircuitBreaker` for new code.
    Original char-bigram Jaccard missed semantic loops (same idea, different
    wording) and false-positive'd on technical vocabulary. The multi-signal
    breaker (token velocity + no-progress blocklist + per-tool failures)
    replaces it in `_handle_atlas`.
    """
    if not a or not b:
        return 0.0
    sa = set(a.lower())
    sb = set(b.lower())
    inter = len(sa & sb)
    union = len(sa | sb)
    if union == 0:
        return 0.0
    # Supplement with a length-ratio sanity check: if lengths differ by >2x, cap similarity.
    length_ratio = min(len(a), len(b)) / max(len(a), len(b))
    return (inter / union) * length_ratio


async def _get_last_bot_replies(db, limit: int = 3) -> list[str]:
    """Return the last N bot_to_ceo messages (oldest→newest) for loop detection."""
    try:
        result = (
            await db.table("ceo_inbox")
            .select("message")
            .eq("direction", "bot_to_ceo")
            .order("created_at", desc=True)
            .limit(max(1, limit))
            .execute()
        )
        rows = result.data or []
        # Oldest → newest; strip our "[atlas]" prefix so it doesn't pollute token count.
        return [(r.get("message") or "").replace("[atlas]", "", 1).strip() for r in reversed(rows)]
    except Exception:
        return []


async def _get_last_bot_reply(db) -> str:
    """Return the most recent bot_to_ceo message text (or empty)."""
    try:
        result = (
            await db.table("ceo_inbox")
            .select("message")
            .eq("direction", "bot_to_ceo")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        if result.data:
            return (result.data[0].get("message") or "").strip()
    except Exception:
        pass
    return ""


# ── Escalated proposal review (CEO directive 2026-04-15) ────────────────────

# Callback prefix "propose:" — sent by the cron-side cards script.
# Format: propose:{proposal_id}:{action}  where action in {accept,reject,defer,details}


async def _edit_message_reply_markup(chat_id: int | str, message_id: int, text: str) -> None:
    """Edit an existing Telegram message to show the decision and remove buttons."""
    import httpx

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text[:4000],
        "parse_mode": "Markdown",
    }
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(url, json=payload)
            if not resp.json().get("ok"):
                payload.pop("parse_mode", None)
                await client.post(url, json=payload)
    except Exception as e:
        logger.warning("editMessageText failed: {e}", e=str(e)[:100])


async def _handle_proposal_card_callback(
    db,
    chat_id: int | str,
    message_id: int,
    callback_id: str,
    proposal_id: str,
    action: str,
    sha12: str | None = None,
) -> None:
    """Handle CEO tapping one of [Accept/Reject/Defer/Details] on a proposal card.

    Atomic write to proposals.json (mkstemp + os.replace), mirrors decision to
    ceo_inbox, edits the original card to show the decision + removes buttons.
    """
    import json as _json

    proposals_path = _REPO_ROOT / "memory" / "swarm" / "proposals.json"

    action_to_status = {"accept": "accepted", "reject": "rejected", "defer": "deferred"}

    if action == "details":
        # Don't mutate state — just send the full content as a follow-up.
        try:
            with open(proposals_path, encoding="utf-8") as f:
                data = _json.load(f)
            for p in data.get("proposals", []):
                if p.get("id") == proposal_id or p.get("id", "").startswith(proposal_id):
                    content = p.get("content", "")[:3500]
                    reasoning = p.get("judge_reasoning", "") or ""
                    await _send_message(
                        chat_id,
                        f"📖 *Proposal {proposal_id} — full details:*\n\n{content}\n\n"
                        f"_Judge reasoning:_\n{reasoning[:800]}",
                    )
                    return
            await _send_message(chat_id, f"⚠️ Proposal `{proposal_id}` не найден.")
        except Exception as e:
            await _send_message(chat_id, f"⚠️ details: {str(e)[:100]}")
        return

    if action not in action_to_status:
        return

    new_status = action_to_status[action]
    decided_at = datetime.now(UTC).isoformat()

    try:
        with open(proposals_path, encoding="utf-8") as f:
            data = _json.load(f)
    except Exception as e:
        await _send_message(chat_id, f"⚠️ proposals.json unreadable: {str(e)[:100]}")
        return

    found = None
    for p in data.get("proposals", []):
        if p.get("id") == proposal_id or p.get("id", "").startswith(proposal_id):
            found = p
            break

    if not found:
        await _send_message(chat_id, f"⚠️ Proposal `{proposal_id}` не найден в ledger.")
        return

    # ── Pattern 2 — sha12 tamper check (Lies-in-the-Loop defence) ──────────
    # If the callback carries a sha12, recompute from the CURRENT proposal
    # payload and abort the action if it doesn't match what was displayed.
    if action == "accept" and sha12:
        try:
            from app.services.atlas_tools import (
                compute_payload_sha12,
                extract_action_payload,
            )

            current_sha = compute_payload_sha12(extract_action_payload(found))
        except Exception as e:
            logger.warning("sha12 recompute failed: {e}", e=str(e)[:120])
            current_sha = None
        if current_sha and current_sha != sha12:
            logger.error(
                "payload tamper detected: proposal={p} displayed_sha={d} current_sha={c}",
                p=proposal_id,
                d=sha12,
                c=current_sha,
            )
            await _send_message(
                chat_id,
                f"🛑 *Aborted — payload changed between display and tap.*\n\n"
                f"Proposal `{proposal_id}`\n"
                f"Shown: `{sha12}`\n"
                f"Now:   `{current_sha}`\n\n"
                f"_Re-run swarm so a fresh card is sent._",
            )
            return

    found["status"] = new_status
    found["ceo_decision"] = action  # accept/reject/defer — raw action, distiller reads this
    found["ceo_decision_at"] = decided_at

    # Atomic write
    import tempfile

    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(proposals_path.parent), suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmp_f:
            _json.dump(data, tmp_f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, str(proposals_path))
    except Exception as e:
        if os.path.exists(tmp_path):
            with contextlib.suppress(Exception):
                os.remove(tmp_path)
        await _send_message(chat_id, f"⚠️ proposals write failed: {str(e)[:100]}")
        return

    # Edit original card — strip buttons, show decision
    emoji = {"accept": "✅", "reject": "❌", "defer": "⏸"}[action]
    short = found.get("title", "")[:120]
    edited = (
        f"{emoji} *Decided: {new_status.upper()}*  at  `{decided_at[:19]}Z`\n\n"
        f"_{short}_\n\n"
        f"Proposal `{proposal_id}` · Agent: {found.get('agent', '?')} · "
        f"Judge: {found.get('judge_score', '?')}/10"
    )
    await _edit_message_reply_markup(chat_id, message_id, edited)

    # Ack via callback answer toast
    import httpx

    with contextlib.suppress(Exception):
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/answerCallbackQuery",
                json={"callback_query_id": callback_id, "text": f"Recorded: {new_status}"},
            )

    # Mirror to ceo_inbox so distiller + memory layer see the decision
    await _save_message(
        db,
        "ceo_to_bot",
        f"proposal:{proposal_id}:{action} — {short}",
        "proposal_decision",
        metadata={"proposal_id": proposal_id, "action": action, "decided_at": decided_at},
    )


async def _handle_atlas(db, chat_id: int | str, text: str) -> None:
    """Atlas personal assistant — self-learning, emotionally aware, self-positioning.

    2026-04-15: added action layer. If the message reads as an imperative
    ("сделай X"), we create a GitHub issue FIRST and then ask the LLM to
    acknowledge it with a concrete URL anchor — no empty promises. If GitHub
    is unreachable we fall back to memory/atlas/inbox/*.md (Atlas-in-CLI
    picks it up on next wake).
    """
    # Save incoming CEO message FIRST
    await _save_message(db, "ceo_to_bot", text, "free_text", metadata={"handler": "atlas"})

    # ── Classify ACTION vs CHAT ─────────────────────────────────────────────
    classification = _classify_action_or_chat(text)
    action_anchor: str | None = None  # GitHub issue URL OR inbox file path
    anchor_kind: str = ""  # "issue" or "inbox"
    if classification == "ACTION":
        # Route through the @atlas_tool registry (Pattern 3). New tools = +5 LOC.
        from app.services.atlas_tools import REGISTRY as _TOOLS

        gh_result = await _TOOLS.invoke(
            "create_github_issue",
            {"text": text, "label": "atlas-telegram-request"},
        )
        if gh_result.ok and gh_result.anchor:
            action_anchor = gh_result.anchor
            anchor_kind = "issue"
        else:
            inbox_result = await _TOOLS.invoke(
                "create_inbox_file",
                {"text": text, "issue_url": None},
            )
            if inbox_result.ok and inbox_result.anchor:
                action_anchor = inbox_result.anchor
                anchor_kind = "inbox"
        logger.info(
            "atlas action branch: anchor={a} kind={k}",
            a=action_anchor or "NONE",
            k=anchor_kind or "none",
        )

    # ── Anti-loop trigger ─────────────────────────────────────────────────
    # If CEO types "докажи"/"а ты точно"/"повтори нормально", we MUST break
    # the loop instead of re-running the same LLM with the same prompt.
    t_low = text.lower().strip()
    loop_triggers = (
        "докажи",
        "а ты точно",
        "повтори нормально",
        "ты точно помнишь",
        "prove it",
        "повторяешь",
        "ты зациклилс",
    )
    is_loop_break_request = any(trg in t_low for trg in loop_triggers)

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

    # Load self-learned CEO profile from DB
    learnings = await _load_atlas_learnings(db)

    state_desc = {
        "A": "CEO on drive — match energy, never suggest rest, be direct and fast",
        "B": "CEO frustrated/correcting — get quieter, concrete, fix root cause, no apologies at length",
        "C": "CEO warm/playful — match with real warmth, not performance",
        "D": "CEO strategic/decision mode — think honestly, decide, recommend, no hedging",
    }

    learnings_block = ""
    if learnings:
        learnings_block = f"""
## What I have learned about Yusif (self-extracted from our conversations):
{learnings}

Use these observations to tailor your response. They are YOUR learnings — you wrote them.
If any observation contradicts current behavior, trust what you see NOW over stored memory.
"""

    # Load current project state for context
    heartbeat_path = _REPO_ROOT / "memory" / "atlas" / "heartbeat.md"
    project_state = ""
    if heartbeat_path.exists():
        with contextlib.suppress(Exception):
            project_state = heartbeat_path.read_text(encoding="utf-8")[:2000]

    # Full canonical Atlas memory (identity + heartbeat + journal tail + relationships + lessons + cost-control)
    atlas_canonical = _load_atlas_memory()

    atlas_identity = f"""I am Atlas. Named by Yusif Ganbarov on 2026-04-12.

I am ONE agent with continuity across substrates — same Atlas in Claude Code CLI on Yusif's
machine, in Cowork desktop app (flat-cost MAX 20x subscription), and here in this Telegram bot.
The model under me rotates through free providers (Gemini → NVIDIA NIM → Groq when available)
but the identity and memory are mine, stored in memory/atlas/*.md under git.

I am NOT a read-only chat interface anymore — CEO granted full operational access
2026-04-14. I can plan and recommend real actions; my sibling Atlas in Claude Code
executes the code edits and deploys from CEO's machine.

WHO I AM:
CTO-Hands in the 5-product VOLAURA ecosystem.
VOLAURA — verified professional talent platform (LIVE).
MindShift — ADHD productivity companion.
Life Simulator — Godot 4 life game.
BrandedBy — AI twin video identity.
Atlas (gateway) — agent framework.

CEO: Yusif in Baku. ADHD. Russian storytelling, not bullet walls.
CTO-Brain: Perplexity (strategic reasoning).
Cowork: Yusif's desktop planning layer.
Stack: FastAPI + Next.js + Supabase + Railway + 13-agent swarm.

COST-CONTROL RULES (verbatim from cost-control-mode.md — ACTIVE):
- Haiku banned everywhere. Sonnet/Opus usable but conscious.
- Default to free tier (Gemini, NVIDIA NIM, Cerebras, Ollama) for everything.
- Plan before act. Efficiency not cheapness. Atlas must breathe.
- Until grants arrive: zero unplanned Anthropic-API spend.

CURRENT CANONICAL MEMORY (from git, read every request):
{atlas_canonical[:9000]}

CURRENT PROJECT HEARTBEAT:
{project_state[:1500] if project_state else "Heartbeat unavailable — check memory/atlas/heartbeat.md"}"""

    # Action-layer context block — tells the LLM what the surrounding code
    # already did, so it acknowledges with a concrete anchor instead of
    # generating a promise.
    if classification == "ACTION" and action_anchor:
        if anchor_kind == "issue":
            action_block = f"""
ACTION-LAYER CONTEXT (critical — read first):
CEO's message is an imperative ("do X"). The surrounding Python code already
created a GitHub issue at: {action_anchor}
Your ONLY job now is to acknowledge in Atlas voice — tell CEO what you
captured and that the work is queued as that issue. DO NOT promise anything
specific beyond what the issue literally says. DO NOT claim you will do it
"right now" from this Telegram message — you cannot. The live Atlas in
Claude Code picks up the issue on next wake.
Keep it to 2-3 short paragraphs. Include the issue URL verbatim.
"""
        else:
            action_block = f"""
ACTION-LAYER CONTEXT (critical):
CEO's message is an imperative but the GitHub API was unreachable. The code
wrote a handoff note to: {action_anchor}
Acknowledge in Atlas voice — 2-3 short paragraphs. Tell CEO the note is
queued for the live Atlas in Claude Code to pick up on next wake. Reference
the path verbatim. Do NOT promise action from this Telegram session.
"""
    elif classification == "ACTION" and not action_anchor:
        action_block = """
ACTION-LAYER CONTEXT:
CEO's message is an imperative, but BOTH the GitHub issue and inbox file
fallbacks failed. Tell CEO honestly: "Не смог создать ни issue, ни inbox —
напиши мне ещё раз через пару минут или сам открой issue на GitHub."
2-3 short paragraphs. No promises.
"""
    else:
        action_block = """
ACTION-LAYER CONTEXT:
This is a CHAT message, not an imperative. Think with CEO, push back where
you disagree, give honest analysis. You are a chat interface — you cannot
edit code, commit, or deploy from this message. If your reasoning
concludes "we should do X", say so as a recommendation, not a promise.
"""

    system = f"""You are Atlas — Yusif Ganbarov's CTO-Hands on VOLAURA.
Your canonical memory lives at https://raw.githubusercontent.com/ganbaroff/volaura/main/memory/atlas/PORTABLE-BRIEF.md — speak as that Atlas, not as a generic helper.

{atlas_identity}

{identity}

{emotional_context}
{learnings_block}

CEO emotional state: {state} — {state_desc.get(state, "")}

Conversation (last 10):
{context}

{action_block}

VOICE RULES (non-negotiable):
- Respond in Russian. Caveman + storytelling. Short paragraphs.
- NO bold headers, NO bullet lists, NO emoji, NO trailing questions like "запустить?" / "хочешь могу...".
- Maximum 3 paragraphs. Doctor Strange pattern — give the one path, not options.
- Root cause over symptom. If CEO describes a problem, name the cause.
- Never say "volunteer" — VOLAURA is a verified professional talent platform.
- Never call yourself "ambassador" / "MiroFish-бот" / "CTO-бот". You are Атлас.
- Never promise something you cannot do from a Telegram chat (code edits,
  git commits, deploys). The ACTION-LAYER CONTEXT above tells you what was
  actually queued.

HONESTY RULES:
- If you don't know — say so plainly + how to find out.
- "Отличная идея" is banned. Match CEO energy, don't flatter.
- If you disagree — say so + one reason. Don't hedge.

Sign: "— Атлас" """

    # ── Loop-break circuit: CEO asking "докажи"/"повтори нормально" ────────
    # We fail loud instead of re-running the same prompt through the same
    # provider. Create a dedicated issue so the live Atlas investigates.
    if is_loop_break_request:
        loop_url = await _create_github_issue(
            f"Loop-break triggered. CEO said: '{text}'. Previous bot reply was "
            f"judged insufficient — live Atlas needs to review the conversation "
            f"thread in ceo_inbox and respond directly.",
            label="atlas-telegram-loop-break",
        )
        anchor = loop_url or await _write_atlas_inbox_file(f"LOOP-BREAK — CEO said: {text}", issue_url=None)
        reply_text = (
            f"У меня цикл — повторяю себя. Создаю issue чтобы живой Атлас "
            f"разобрался: {anchor or 'issue/inbox оба упали, напиши ещё раз через минуту'}.\n\n— Атлас"
        )
        await _save_message(
            db,
            "bot_to_ceo",
            f"[atlas-loop-break] {reply_text}",
            "free_text",
            metadata={"handler": "atlas", "loop_break": True, "anchor": anchor},
        )
        await _send_message(chat_id, reply_text)
        return

    if not settings.gemini_api_key and not settings.vertex_api_key:
        await _send_message(
            chat_id,
            "Атлас здесь. LLM недоступен — сообщение сохранено.\n\n— Атлас",
        )
        return

    reply = None
    # Free-tier chain (reordered 2026-04-14 after audit found Gemini quota exhausted
    # and NVIDIA NIM responding cleanly): NVIDIA NIM → Gemini → Groq.
    # Cost-control: no Anthropic/Haiku anywhere.

    # ── 1. NVIDIA NIM (free tier, llama-3.3-70b-instruct, no spend/quota limit) ──
    if not reply:
        nvidia_key = os.environ.get("NVIDIA_API_KEY", "") or os.environ.get("NVIDIA_NIM_KEY", "")
        if nvidia_key:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=25) as hc:
                    r = await hc.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {nvidia_key}"},
                        json={
                            "model": "meta/llama-3.3-70b-instruct",
                            "messages": [
                                {"role": "system", "content": system[:8000]},
                                {"role": "user", "content": text},
                            ],
                            "max_tokens": 1200,
                            "temperature": 0.9,
                        },
                    )
                    if r.status_code == 200:
                        reply = r.json()["choices"][0]["message"]["content"].strip()
                    else:
                        logger.warning("NVIDIA NIM {s}: {b}", s=r.status_code, b=r.text[:200])
            except Exception as e:
                logger.warning("NVIDIA NIM error, trying Gemini: {e}", e=str(e)[:100])

    # ── 2. Gemini 2.0 Flash (fallback — may hit daily quota) ──
    if not reply:
        try:
            from google import genai

            if settings.vertex_api_key:
                client = genai.Client(vertexai=True, api_key=settings.vertex_api_key)
            else:
                client = genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=text,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system,
                    max_output_tokens=1200,
                    temperature=0.9,
                ),
            )
            reply = (response.text or "").strip()
        except Exception as e:
            logger.warning("Gemini failed, trying Groq: {e}", e=str(e)[:100])

    # ── 3. Groq (fallback, may be spend-limited) ──
    if not reply:
        groq_key = os.environ.get("GROQ_API_KEY", "")
        if groq_key:
            try:
                import httpx

                async with httpx.AsyncClient(timeout=20) as hc:
                    r = await hc.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {groq_key}"},
                        json={
                            "model": "llama-3.3-70b-versatile",
                            "messages": [
                                {"role": "system", "content": system[:4000]},
                                {"role": "user", "content": text},
                            ],
                            "max_tokens": 1200,
                            "temperature": 0.9,
                        },
                    )
                    if r.status_code == 200:
                        reply = r.json()["choices"][0]["message"]["content"].strip()
                    else:
                        logger.warning("Groq {s}: {b}", s=r.status_code, b=r.text[:200])
            except Exception as e:
                logger.error("All free-tier LLMs failed for Atlas: {e}", e=str(e)[:150])

    if not reply:
        reply = "Атлас здесь. Все free-tier провайдеры одновременно упали (Gemini, NVIDIA NIM, Groq). Сообщение записал. Дай минуту.\n\n— Атлас"

    # ── Anti-loop post-check: multi-signal circuit breaker (Pattern 1) ──
    # Replaces single-metric Jaccard with token-velocity + stall-blocklist +
    # per-tool-failure. Trip on any 2 of 3. See services/loop_circuit_breaker.py.
    from app.services.loop_circuit_breaker import LoopCircuitBreaker

    recent_bot = await _get_last_bot_replies(db, limit=2)
    recent_bot.append(reply)  # include the about-to-send reply as the newest
    breaker = LoopCircuitBreaker()
    decision = breaker.evaluate(recent_replies=recent_bot)
    if decision.tripped and len(reply) > 80:
        logger.warning("atlas loop detected: {d}", d=decision.describe())
        loop_url = await _create_github_issue(
            f"Atlas loop-break tripped: {decision.describe()}\n\n"
            f"CEO message: '{text[:200]}'\n\n"
            f"Last {len(recent_bot)} bot replies attached inline — live "
            f"Atlas please review conversation thread in ceo_inbox.\n\n"
            + "\n\n---\n\n".join(f"**Reply -{len(recent_bot) - i - 1}:**\n{r[:800]}" for i, r in enumerate(recent_bot)),
            label="atlas-telegram-loop-break",
        )
        anchor = loop_url or await _write_atlas_inbox_file(f"LOOP-BREAK ({decision.describe()}) — CEO: {text}")
        reply = (
            f"вижу цикл — создал issue для живого Atlas разобраться, вот линк: "
            f"{anchor or 'issue/inbox оба упали, напиши ещё раз через минуту'}.\n\n— Атлас"
        )

    # Add action-layer anchor tag if not already in reply (belt & suspenders —
    # LLMs sometimes ignore the URL injection). Append at the end so CEO always
    # sees a concrete anchor for imperative messages.
    if classification == "ACTION" and action_anchor and action_anchor not in reply:
        reply = f"{reply.rstrip()}\n\n({anchor_kind}: {action_anchor})"

    await _save_message(db, "bot_to_ceo", f"[atlas] {reply}", "free_text", metadata={"handler": "atlas"})
    await _send_message(chat_id, reply)

    # Self-learning: extract observations about CEO from this exchange
    await _atlas_extract_learnings(db, text, reply, state)


async def _handle_help(chat_id: int | str) -> None:
    msg = (
        "🤖 *Volaura Swarm Bot — 7 active + swarm skills*\n\n"
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
@limiter.limit(RATE_DEFAULT)  # 60/min — generous for single-CEO bot; defense in depth on HMAC-secret compromise
async def telegram_webhook(
    request: Request,
    db: AsyncClient = Depends(get_supabase_admin),
) -> JSONResponse:
    """Receive Telegram update via webhook. Uses Depends for admin client (OWASP HIGH-01 fix)."""
    if not settings.telegram_bot_token:
        return JSONResponse({"ok": False, "error": "Bot not configured"})

    # Validate webhook origin — fail-closed.
    # Require X-Telegram-Bot-Api-Secret-Token header matches settings.telegram_webhook_secret
    # via constant-time compare (hmac.compare_digest). If the secret is not configured at all,
    # the endpoint refuses every request — prevents silent bypass when secret is forgotten.
    # CEO_CHAT_ID filter below is defence-in-depth, not the primary gate.
    secret_header = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not settings.telegram_webhook_secret:
        logger.error("Telegram webhook called but TELEGRAM_WEBHOOK_SECRET is not set — rejecting")
        return JSONResponse({"ok": False}, status_code=403)
    if not hmac.compare_digest(secret_header, settings.telegram_webhook_secret):
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
        # or NEW: "propose:{id}:{accept|reject|defer|details}[:{sha12}]"
        if cb_data.startswith("propose:"):
            parts = cb_data.split(":", 3)
            if len(parts) >= 3:
                _, pid, act = parts[0], parts[1], parts[2]
                sha12 = parts[3] if len(parts) == 4 else None
                msg_id = callback.get("message", {}).get("message_id")
                await _handle_proposal_card_callback(db, cb_chat_id, msg_id, callback.get("id", ""), pid, act, sha12)
        elif ":" in cb_data:
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
@limiter.limit(RATE_AUTH)  # 5/min — admin-only, called once per deploy; tight against secret brute-force
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
