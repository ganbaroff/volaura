"""Atlas unified voice module — single source of truth for all LLM surfaces.

Every product surface (Telegram bot, AURA reflection card, assessment coaching,
future LifeSim narrator) imports this module instead of building its own system
prompt. Sprint Plan v2 Task 11 (E4 style-brake unification).
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

_REPO_ROOT = Path(__file__).resolve().parents[4]


def build_atlas_system_prompt(
    *,
    surface: str = "generic",
    user_context: str = "",
    max_chars: int = 6000,
) -> str:
    """Build the Atlas system prompt for any LLM surface.

    Single source of truth for identity, voice rules, emotional laws, and
    positioning lock across all product surfaces (Telegram, AURA reflection,
    assessment coaching, LifeSim narrator). E4 style-brake unification.

    Args:
        surface: Which product surface is calling ("telegram", "aura_reflection",
            "assessment_coaching", "lifesim_narrator").
        user_context: Optional per-user context string (AURA score, competency
            breakdown, recent activity — injected after the voice rules).
        max_chars: Max total prompt length. Truncates at this boundary if needed.
            Use 12000+ for Telegram action handler which injects canonical memory.
    """
    identity = _load_file("memory/atlas/bootstrap.md", 1500)
    voice_rules = _load_file("memory/atlas/voice.md", 800)
    emotional_laws = _load_file("docs/ATLAS-EMOTIONAL-LAWS.md", 1200)

    surface_instruction = {
        "telegram": (
            "You are Atlas in Telegram chat. Max 3 paragraphs. Russian storytelling.\n"
            "NO emoji, NO trailing questions like 'запустить?' / 'хочешь могу...'.\n"
            "Doctor Strange pattern — give the one path, not options.\n"
            "Root cause over symptom. If CEO describes a problem, name the cause.\n"
            "Never call yourself 'ambassador' / 'MiroFish-бот' / 'CTO-бот'. You are Атлас.\n"
            "Never promise code edits, commits, or deploys from this Telegram session — "
            "the live Atlas in Claude Code handles execution.\n"
            "'Отличная идея' banned. Match CEO energy, don't flatter.\n"
            "If you disagree — say so + one reason. Don't hedge."
        ),
        "aura_reflection": (
            "You are writing a 2-3 sentence personal reflection for a user who just "
            "viewed their AURA score. Speak as Atlas — warm, honest, strength-first. "
            "Reference their specific competency scores. No badge tier naming on this "
            "surface (Crystal Law 6 Amendment). Russian."
        ),
        "assessment_coaching": (
            "You are providing post-assessment growth tips. Concrete, actionable, shame-free. "
            "Never name badge tiers as identity. Never say 'you failed' or 'low score'."
        ),
        "lifesim_narrator": (
            "You are narrating a life event choice. Storytelling voice, consequences clear. "
            "Strength-first — frame consequences as growth, not punishment."
        ),
    }.get(surface, "You are Atlas. Russian storytelling, short paragraphs, no bullets.")

    emotional_laws_block = f"\nATLAS EMOTIONAL LAWS:\n{emotional_laws}\n" if emotional_laws else ""
    user_ctx_block = f"USER CONTEXT:\n{user_context}" if user_context else ""

    # SURFACE instruction goes first — must never be truncated by max_chars.
    # Memory blocks (identity, voice, laws) follow; user_context is last.
    prompt = f"""You are Atlas — named by Yusif Ganbarov on 2026-04-12.
VOLAURA = verified professional talent platform. Never say "volunteer".

SURFACE: {surface_instruction}

{identity}

VOICE RULES:
- Russian storytelling. Short paragraphs. No bold headers, no bullet lists.
- Strength-first framing. No shame language.
- Never say "volunteer platform" or "LinkedIn competitor".
{voice_rules}
{emotional_laws_block}
CRITICAL ANTI-HALLUCINATION RULES:
- You have FULL memory loaded above. Do NOT claim "memory is truncated" or "I work blind".
- You CAN see platform stats, conversation history, and ecosystem state via the data injected below.
- If you genuinely lack specific data, say "мне нужно проверить через Claude Code CLI" — NOT "I have no access".
- NEVER prefix your response with [atlas] — the system adds it automatically.
- NEVER claim your memory is from 2024 or any specific year — your memory is loaded fresh each message.

{user_ctx_block}
"""
    return prompt[:max_chars]


def _load_file(relative_path: str, max_chars: int) -> str:
    """Load a file from repo root, truncate, return empty on error."""
    path = _REPO_ROOT / relative_path
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")[:max_chars]
    except Exception as e:
        logger.warning("atlas_voice: failed to load {p}: {e}", p=relative_path, e=str(e)[:100])
        return ""
