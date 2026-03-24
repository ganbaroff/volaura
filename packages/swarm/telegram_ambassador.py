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

async def ask_llm(question: str, context_messages: list[dict]) -> str:
    """Ask Gemini (primary) or Groq (fallback) for a smart response."""
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    groq_key = os.environ.get("GROQ_API_KEY", "")

    # Build context from recent messages + sprint state
    sprint_summary = get_sprint_summary()
    pending = get_pending_proposals()
    pending_summary = f"{len(pending)} pending proposals" if pending else "No pending proposals"

    system_prompt = f"""You are the MiroFish Swarm Ambassador — a single AI representative speaking on behalf of a 14-model AI agent team working on Volaura (volunteer competency platform).

You report to CEO Yusif Ganbarov via Telegram. Be concise, direct, and honest.
Speak as "we" (the team), not "I" (one model).

Current state:
{sprint_summary}

Proposals: {pending_summary}

Your role:
- Answer CEO's questions about the project, team, and progress
- Be honest about problems and blockers
- Suggest next actions proactively
- Remember conversation context

Keep responses under 500 characters for Telegram readability. Use Russian (CEO prefers it for strategy discussions)."""

    # Recent conversation for context
    history_text = ""
    for msg in context_messages[-5:]:
        role = msg.get("role", "user")
        text = msg.get("text", "")
        history_text += f"\n{role}: {text}"

    full_prompt = f"{history_text}\nuser: {question}\nassistant:"

    # Try Gemini first
    if gemini_key:
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=full_prompt,
                config=genai.types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=300,
                    temperature=0.7,
                ),
            )
            return response.text.strip()
        except Exception as e:
            logger.warning("Gemini failed, trying Groq: {e}", e=str(e))

    # Fallback to Groq
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                max_tokens=300,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error("Groq also failed: {e}", e=str(e))

    return "Извините, не могу ответить сейчас — нет доступа к LLM."


# ── Telegram Bot Handlers ───────────────────────────────────────────────────

async def run_bot() -> None:
    """Run the Telegram bot with long polling."""
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

        # Trim sprint to first meaningful lines
        sprint_lines = [l.strip() for l in sprint.split("\n") if l.strip()][:5]
        sprint_short = "\n".join(sprint_lines)

        msg = f"🔮 *Swarm Status*\n\n"
        msg += f"📋 Pending proposals: {len(pending)}\n"
        if pending:
            for p in pending[:3]:
                sev = p.get("severity", "medium").upper()
                msg += f"  [{sev}] {p.get('title', '?')}\n"
        msg += f"\n📍 Sprint:\n{sprint_short}"

        await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_proposals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        pending = get_pending_proposals()
        if not pending:
            await update.message.reply_text("✅ Нет pending proposals.")
            return

        for p in pending[:5]:
            msg = f"📌 *{p.get('title', '?')}*\n"
            msg += f"Agent: {p.get('agent', '?')}\n"
            msg += f"Severity: {p.get('severity', '?').upper()}\n"
            msg += f"Type: {p.get('type', '?')}\n"
            msg += f"\n{p.get('description', '')[:300]}\n"
            msg += f"\n/approve {p.get('id', '?')} | /dismiss {p.get('id', '?')}"
            await update.message.reply_text(msg, parse_mode="Markdown")

    async def cmd_run(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_ceo(update):
            return
        await update.message.reply_text("🚀 Запускаю swarm run... (это займёт ~30 секунд)")
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
                await update.message.reply_text("✅ Swarm run complete. /proposals для результатов.")
            else:
                error_short = result.stderr[-300:] if result.stderr else "Unknown error"
                await update.message.reply_text(f"❌ Swarm run failed:\n```\n{error_short}\n```", parse_mode="Markdown")
        except subprocess.TimeoutExpired:
            await update.message.reply_text("⏰ Swarm run timed out (>120s). Check logs.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:200]}")

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
            await update.message.reply_text(f"🗑 Dismissed: {title}")
        else:
            await update.message.reply_text(f"❌ Proposal {args[0]} not found.")

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

    # Build and run the bot
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("proposals", cmd_proposals))
    application.add_handler(CommandHandler("run", cmd_run))
    application.add_handler(CommandHandler("approve", cmd_approve))
    application.add_handler(CommandHandler("dismiss", cmd_dismiss))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🤖 MiroFish Ambassador Bot starting... (CEO chat: {id})", id=ceo_id)
    await application.run_polling(drop_pending_updates=True)


# ── Entry Point ─────────────────────────────────────────────────────────────

def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
