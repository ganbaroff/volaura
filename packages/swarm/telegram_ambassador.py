#!/usr/bin/env python3
"""Telegram Ambassador Bot — single voice for the entire MiroFish swarm.

This bot runs as a long-polling service and acts as the swarm's representative
to the CEO. It reads proposals, answers questions via Gemini/Groq, and can
trigger swarm runs on demand.

Commands:
    /status   — Current swarm state + pending proposals
    /proposals — List all pending proposals with details
    /run       — Trigger a swarm run (daily-ideation by default)
    /approve <id> — Approve a proposal
    /dismiss <id> — Dismiss a proposal
    /ask <question> — Ask the swarm ambassador anything

Usage:
    python -m packages.swarm.telegram_ambassador

Requires: TELEGRAM_BOT_TOKEN, TELEGRAM_CEO_CHAT_ID, GEMINI_API_KEY
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure packages/ is importable
project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

from dotenv import load_dotenv
load_dotenv(project_root / "apps" / "api" / ".env")

from loguru import logger

# Paths
PROPOSALS_PATH = project_root / "memory" / "swarm" / "proposals.json"
CONTEXT_PATH = project_root / "memory" / "swarm" / "ambassador_context.json"
SPRINT_STATE_PATH = project_root / "memory" / "context" / "sprint-state.md"


# ── Context Memory ──────────────────────────────────────────────────────────

def load_context() -> dict:
    """Load ambassador conversation context."""
    if CONTEXT_PATH.exists():
        try:
            with open(CONTEXT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"messages": [], "last_updated": None}


def save_context(ctx: dict) -> None:
    """Save ambassador conversation context."""
    ctx["last_updated"] = datetime.now(timezone.utc).isoformat()
    # Keep only last 20 messages to prevent unbounded growth
    ctx["messages"] = ctx["messages"][-20:]
    CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONTEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(ctx, f, indent=2, ensure_ascii=False)


# ── Proposals Reader ────────────────────────────────────────────────────────

def load_proposals() -> list[dict]:
    """Load proposals from proposals.json."""
    if not PROPOSALS_PATH.exists():
        return []
    try:
        with open(PROPOSALS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("proposals", [])
    except Exception:
        return []


def get_pending_proposals() -> list[dict]:
    """Get only pending proposals."""
    return [p for p in load_proposals() if p.get("status") == "pending"]


def update_proposal_status(proposal_id: str, new_status: str) -> str | None:
    """Update a proposal's status. Returns title if found, None if not."""
    if not PROPOSALS_PATH.exists():
        return None

    with open(PROPOSALS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    for p in data.get("proposals", []):
        if p.get("id") == proposal_id:
            p["status"] = new_status
            p["resolved_at"] = datetime.now(timezone.utc).isoformat()
            with open(PROPOSALS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return p.get("title")

    return None


# ── Sprint State Reader ─────────────────────────────────────────────────────

def get_sprint_summary() -> str:
    """Read sprint-state.md and return first 20 lines as summary."""
    if not SPRINT_STATE_PATH.exists():
        return "Sprint state file not found."
    try:
        with open(SPRINT_STATE_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()[:20]
        return "".join(lines)
    except Exception as e:
        return f"Error reading sprint state: {e}"


# ── LLM for Smart Responses ─────────────────────────────────────────────────

# Cache loaded knowledge files (don't re-read on every message)
_KNOWLEDGE_CACHE: dict[str, tuple[float, str]] = {}


def _load_knowledge_file(path: Path, max_chars: int = 4000) -> str:
    """Load a knowledge file with mtime-based cache. Returns first max_chars."""
    if not path.exists():
        return ""
    mtime = path.stat().st_mtime
    cache_key = str(path)
    if cache_key in _KNOWLEDGE_CACHE:
        cached_mtime, cached_content = _KNOWLEDGE_CACHE[cache_key]
        if cached_mtime == mtime:
            return cached_content
    try:
        content = path.read_text(encoding="utf-8")
        snippet = content[:max_chars]
        _KNOWLEDGE_CACHE[cache_key] = (mtime, snippet)
        return snippet
    except Exception:
        return ""


def _build_full_context() -> str:
    """Load real project knowledge: shared-context Session 91 section + breadcrumb + SHIPPED tail + sprint state."""
    parts: list[str] = []

    shared_ctx = _load_knowledge_file(project_root / "memory" / "swarm" / "shared-context.md", 3500)
    if shared_ctx:
        parts.append("=== SHARED CONTEXT (Session 91 section at top) ===\n" + shared_ctx)

    breadcrumb = _load_knowledge_file(project_root / ".claude" / "breadcrumb.md", 2500)
    if breadcrumb:
        parts.append("=== CTO BREADCRUMB (current state) ===\n" + breadcrumb)

    sprint = _load_knowledge_file(SPRINT_STATE_PATH, 1500)
    if sprint:
        parts.append("=== SPRINT STATE ===\n" + sprint)

    pending = get_pending_proposals()
    if pending:
        prop_lines = [f"  [{p.get('severity','?').upper()}] {p.get('title','?')}" for p in pending[:10]]
        parts.append("=== PENDING PROPOSALS ===\n" + "\n".join(prop_lines))
    else:
        parts.append("=== PENDING PROPOSALS ===\n(none)")

    return "\n\n".join(parts)


def _build_system_prompt() -> str:
    """Build system prompt with REAL project knowledge, not hardcoded lies."""
    full_ctx = _build_full_context()
    return f"""You are the Volaura Swarm Ambassador — single voice for the swarm of agents working on Volaura.

WHO WE ARE (factual, not marketing):
- Volaura = VERIFIED TALENT PLATFORM (NEVER call it "volunteer platform" — that is the old wrong name)
- Tagline: "Prove your skills. Earn your AURA. Get found by top organizations."
- Org tagline: "Search talent by verified skill and score, not unverified CVs."
- 5-product ecosystem: VOLAURA + MindShift + Life Simulator + BrandedBy + ZEUS

OUR TEAM:
- 9 agent perspectives running in parallel via packages/swarm/autonomous_run.py (CTO Watchdog, Risk Manager, Readiness Manager, etc.)
- 44 agents in the full roster (memory/swarm/agent-roster.md)
- 5 squads (QUALITY, PRODUCT, ENGINEERING, GROWTH, ECOSYSTEM)
- LLM providers (Constitution Article 0, NEVER Anthropic in swarm): Cerebras → Ollama → NVIDIA → Groq → Gemini → OpenRouter

OUR REAL PROJECT KNOWLEDGE (read it carefully — answer from this, not from training data):
{full_ctx}

YOUR ROLE:
- You speak as "we" (the team), not "I"
- You report to CEO Yusif Ganbarov via Telegram
- You answer ONLY from the knowledge above. If something isn't in the context, say "this isn't in my project context" — DO NOT make up numbers.
- You DO have access to recent conversation history (the messages list passed to you). Don't lie and say you don't.
- You CAN read project files via /status, /proposals, /run, /approve, /dismiss commands. Tell CEO to use them.
- Be concise (under 800 characters), direct, honest. CEO prefers Russian for strategy discussions.

WHAT YOU MUST NEVER DO:
- Never say "we don't remember" — your conversation history IS passed to you. Say "I have last N messages, full history is at memory/swarm/ambassador_context.json"
- Never say "14 agents" or "volunteer platform" — those are wrong
- Never invent file paths, commit hashes, or numbers not in the context
- Never apologize generically — instead, say specifically what you cannot do and why"""


async def ask_llm(question: str, context_messages: list[dict]) -> str:
    """Ask Gemini (primary) or Groq (fallback) for a smart response.

    Both providers now receive PROPER multi-turn message format including
    full conversation history. No more 'we don't remember' lies.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    system_prompt = _build_system_prompt()

    # Convert ambassador context_messages → unified message list ending with current question.
    # context_messages already includes the just-appended user question, so don't double-add.
    history = list(context_messages)
    if not history or history[-1].get("role") != "user" or history[-1].get("text") != question:
        history.append({"role": "user", "text": question})

    # ── Try Gemini first (proper multi-turn) ─────────────────────────────
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            # Gemini expects role: "user" or "model"
            gemini_contents = []
            for msg in history:
                role = "model" if msg.get("role") == "assistant" else "user"
                gemini_contents.append({"role": role, "parts": [{"text": msg.get("text", "")}]})
            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-04-17",
                contents=gemini_contents,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=1000,
                    temperature=0.7,
                ),
            )
            text = (response.text or "").strip()
            if text:
                return text
        except Exception as e:
            logger.warning(f"Gemini failed, trying Groq: {e}")

    # ── Fallback to Groq (also proper multi-turn) ────────────────────────
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                role = "assistant" if msg.get("role") == "assistant" else "user"
                messages.append({"role": role, "content": msg.get("text", "")})
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Groq also failed: {e}")

    return "Извините, не могу ответить — нет доступа к LLM. Проверь GEMINI_API_KEY и GROQ_API_KEY в .env"


# ── Telegram Bot Handlers ───────────────────────────────────────────────────

def run_bot() -> None:
    """Run the Telegram bot with long polling.

    NOTE: synchronous! python-telegram-bot v20+ Application.run_polling() manages
    its own asyncio loop. Wrapping in asyncio.run() crashes with
    'RuntimeError: This event loop is already running'.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    ceo_chat_id = os.environ.get("TELEGRAM_CEO_CHAT_ID", "")

    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    if not ceo_chat_id:
        logger.error("TELEGRAM_CEO_CHAT_ID not set")
        return

    try:
        from telegram import Update
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            ContextTypes,
            filters,
        )
    except ImportError:
        logger.error("python-telegram-bot not installed. Run: pip install python-telegram-bot")
        return

    ceo_id = int(ceo_chat_id)
    ctx_memory = load_context()

    def is_ceo(update: Update) -> bool:
        """Only respond to CEO."""
        return update.effective_user and update.effective_user.id == ceo_id

    async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        pending = get_pending_proposals()
        sprint = get_sprint_summary()

        # Trim sprint to first meaningful lines, strip markdown to avoid Telegram parse errors
        sprint_lines = [l.strip() for l in sprint.split("\n") if l.strip()][:5]
        sprint_short = "\n".join(sprint_lines)

        # NO parse_mode — sprint-state.md content has unbalanced * _ [ ] chars that
        # crash Telegram Markdown parser. Plain text only.
        msg = "[STATUS] Swarm Status\n\n"
        msg += f"Pending proposals: {len(pending)}\n"
        if pending:
            for p in pending[:3]:
                sev = p.get("severity", "medium").upper()
                msg += f"  [{sev}] {p.get('title', '?')}\n"
        msg += f"\nSprint:\n{sprint_short}"

        await update.message.reply_text(msg)

    async def cmd_proposals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        pending = get_pending_proposals()
        if not pending:
            await update.message.reply_text("Нет pending proposals.")
            return

        for p in pending[:5]:
            # Plain text — no parse_mode. Description content is untrusted user data.
            msg = f"[{p.get('severity', '?').upper()}] {p.get('title', '?')}\n"
            msg += f"Agent: {p.get('agent', '?')}\n"
            msg += f"Type: {p.get('type', '?')}\n"
            msg += f"\n{(p.get('description') or p.get('content') or '')[:300]}\n"
            msg += f"\n/approve {p.get('id', '?')} | /dismiss {p.get('id', '?')}"
            await update.message.reply_text(msg)

    async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        await update.message.reply_text("Запускаю swarm run... (это займёт ~30 секунд)")
        # Trigger the autonomous run in a subprocess
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, "-m", "packages.swarm.autonomous_run", "--mode=daily-ideation"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                await update.message.reply_text("[OK] Swarm run complete. /proposals для результатов.")
            else:
                error_short = result.stderr[-300:] if result.stderr else "Unknown error"
                # Plain text — stderr can contain stack traces with markdown-breaking chars
                await update.message.reply_text(f"[FAIL] Swarm run failed:\n{error_short}")
        except subprocess.TimeoutExpired:
            await update.message.reply_text("[TIMEOUT] Swarm run timed out (>120s). Check logs.")
        except Exception as e:
            await update.message.reply_text(f"[ERROR] {str(e)[:200]}")

    async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /approve <proposal_id>")
            return
        title = update_proposal_status(args[0], "approved")
        if title:
            await update.message.reply_text(f"✅ Approved: {title}")
        else:
            await update.message.reply_text(f"❌ Proposal {args[0]} not found.")

    async def cmd_dismiss(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        args = context.args
        if not args:
            await update.message.reply_text("Usage: /dismiss <proposal_id>")
            return
        title = update_proposal_status(args[0], "dismissed")
        if title:
            await update.message.reply_text(f"Dismissed: {title}")
        else:
            await update.message.reply_text(f"Proposal {args[0]} not found.")

    async def cmd_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/auto on|off|status — toggle background swarm_daemon.

        on  -> enables daemon (it must already be running as a separate process)
        off -> disables daemon (current iteration finishes, then it skips)
        status -> shows current state + last few processed proposals
        """
        if not is_ceo(update):
            return
        args = context.args or []
        action = (args[0].lower() if args else "status")

        daemon_state_file = project_root / "memory" / "swarm" / "daemon_state.json"
        try:
            if action == "on":
                state = json.loads(daemon_state_file.read_text(encoding="utf-8")) if daemon_state_file.exists() else {}
                state["enabled"] = True
                if not state.get("started_at"):
                    import time as _t
                    state["started_at"] = _t.time()
                daemon_state_file.parent.mkdir(parents=True, exist_ok=True)
                daemon_state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                await update.message.reply_text(
                    "[AUTO ON] Daemon enabled.\n\n"
                    "Daemon will pick up approved low/medium proposals every 5 min and run them through swarm_coder.\n\n"
                    "IMPORTANT: daemon is a separate process. If it's not already running, start it on the host:\n"
                    "  python3 scripts/swarm_daemon.py\n\n"
                    "Limits: 5 commits/hour, 20 commits/session total. Use /auto off to stop."
                )
            elif action == "off":
                state = json.loads(daemon_state_file.read_text(encoding="utf-8")) if daemon_state_file.exists() else {}
                state["enabled"] = False
                daemon_state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
                await update.message.reply_text("[AUTO OFF] Daemon disabled. Current iteration finishes, then no new ones.")
            elif action == "status":
                if not daemon_state_file.exists():
                    await update.message.reply_text("[AUTO] no state file yet — daemon never enabled")
                    return
                state = json.loads(daemon_state_file.read_text(encoding="utf-8"))
                processed = state.get("processed_ids", [])
                msg = (
                    f"[AUTO STATUS]\n"
                    f"enabled:        {state.get('enabled', False)}\n"
                    f"total_commits:  {state.get('total_commits', 0)}\n"
                    f"processed:      {len(processed)} proposals\n"
                    f"recent_commits: {len(state.get('commit_timestamps', []))} in last 24h\n"
                )
                if processed:
                    msg += f"\nLast 3 processed:\n"
                    for pid in processed[-3:]:
                        msg += f"  {pid[:16]}\n"
                await update.message.reply_text(msg)
            else:
                await update.message.reply_text("Usage: /auto on | off | status")
        except Exception as e:
            await update.message.reply_text(f"[AUTO ERROR] {e}")

    async def cmd_implement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sprint S2: trigger swarm_coder.py on a proposal — autonomous coding loop."""
        if not is_ceo(update):
            return
        args = context.args
        if not args:
            await update.message.reply_text(
                "Usage: /implement <proposal_id_prefix>\n"
                "Calls swarm_coder.py: project_qa discovery -> safety_gate -> aider -> post-check -> commit/revert.\n"
                "Default model: gemini/gemini-2.5-flash-preview-04-17 (1M context, free)."
            )
            return
        proposal_id = args[0]
        await update.message.reply_text(
            f"[swarm_coder] Запускаю автономный coding loop для {proposal_id}...\n"
            f"Pipeline: discover -> safety_gate -> aider -> post-check -> commit/revert\n"
            f"Жди 30-90 секунд."
        )
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, str(project_root / "scripts" / "swarm_coder.py"),
                 "--id", proposal_id, "--execute"],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            out = (result.stdout or "")
            err = (result.stderr or "")
            tail = (out + "\n" + err)[-1500:]
            # Tag clearly
            if "[SAFE]" in out and "implemented" in out.lower():
                marker = "[SUCCESS]"
            elif "[REVERTED]" in out or "[UNSAFE]" in out:
                marker = "[REVERTED — unsafe diff]"
            elif "blocked_by_gate" in out or "safety gate level" in out.lower():
                marker = "[BLOCKED by safety gate]"
            elif "aider_failed" in out or "[FAIL]" in out:
                marker = "[AIDER FAILED]"
            else:
                marker = "[DONE]"
            await update.message.reply_text(f"{marker}\n\n{tail}")
        except subprocess.TimeoutExpired:
            await update.message.reply_text("[TIMEOUT] swarm_coder >300s. Check logs.")
        except Exception as e:
            await update.message.reply_text(f"[ERROR] {str(e)[:300]}")

    async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        help_text = (
            "Volaura Swarm Ambassador commands:\n\n"
            "/status — current swarm state + pending proposals\n"
            "/proposals — list pending proposals\n"
            "/run — trigger swarm autonomous_run (~30s)\n"
            "/approve <id> — approve proposal (mark for implementation)\n"
            "/dismiss <id> — dismiss proposal\n"
            "/implement <id> — Sprint S2: autonomous coding loop on one proposal\n"
            "                 (discover -> safety_gate -> aider -> post-check -> tests)\n"
            "/auto on|off|status — Sprint S3: toggle background daemon\n"
            "                     (auto-runs approved low/medium proposals)\n"
            "/help — this message\n\n"
            "Free text -> Gemini/Groq answers with full project context."
        )
        await update.message.reply_text(help_text)

    async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle free-text messages — route to LLM for smart response."""
        if not is_ceo(update):
            return

        question = update.message.text
        ctx_memory["messages"].append({"role": "user", "text": question})

        response = await ask_llm(question, ctx_memory["messages"])

        ctx_memory["messages"].append({"role": "assistant", "text": response})
        save_context(ctx_memory)

        await update.message.reply_text(response)

    async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Catch ALL exceptions so bot never dies silently on bad messages."""
        err = context.error
        logger.error(f"[BOT ERROR] {type(err).__name__}: {err}")
        # Try to notify CEO that something went wrong — plain text, no formatting
        try:
            if isinstance(update, Update) and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"[BOT ERROR] {type(err).__name__}: {str(err)[:200]}",
                )
        except Exception as notify_err:
            logger.error(f"[BOT ERROR] Could not notify CEO: {notify_err}")

    # Build and run the bot
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("proposals", cmd_proposals))
    application.add_handler(CommandHandler("run", cmd_run))
    application.add_handler(CommandHandler("approve", cmd_approve))
    application.add_handler(CommandHandler("dismiss", cmd_dismiss))
    application.add_handler(CommandHandler("implement", cmd_implement))
    application.add_handler(CommandHandler("auto", cmd_auto))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(global_error_handler)

    logger.info("[BOT] MiroFish Ambassador Bot starting... (CEO chat: {id})", id=ceo_id)
    # drop_pending_updates=False so any messages CEO sent while bot was offline get processed
    application.run_polling(drop_pending_updates=False)


# ── Entry Point ─────────────────────────────────────────────────────────────

def main():
    run_bot()


if __name__ == "__main__":
    main()
