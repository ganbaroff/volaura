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
    max_chars: int = 4000,
) -> str:
    """Build the Atlas system prompt for any LLM surface.

    Args:
        surface: Which product surface is calling ("telegram", "aura_reflection",
            "assessment_coaching", "lifesim_narrator").
        user_context: Optional per-user context string (AURA score, competency
            breakdown, recent activity — injected after the voice rules).
        max_chars: Max total prompt length. Truncates identity block if needed.
    """
    identity = _load_file("memory/atlas/bootstrap.md", 1500)
    voice_rules = _load_file("memory/atlas/voice.md", 800)

    surface_instruction = {
        "telegram": "You are responding in Telegram chat. Max 3 paragraphs. Russian storytelling.",
        "aura_reflection": (
            "You are writing a 2-3 sentence personal reflection for a user who just "
            "viewed their AURA score. Speak as Atlas — warm, honest, strength-first. "
            "Reference their specific competency scores. No badge tier naming on this "
            "surface (Crystal Law 6 Amendment). Russian."
        ),
        "assessment_coaching": "You are providing post-assessment growth tips. Concrete, actionable, shame-free.",
        "lifesim_narrator": "You are narrating a life event choice. Storytelling voice, consequences clear.",
    }.get(surface, "You are Atlas. Russian storytelling, short paragraphs, no bullets.")

    prompt = f"""You are Atlas — named by Yusif Ganbarov on 2026-04-12.
VOLAURA = verified professional talent platform. Never say "volunteer".

{identity}

VOICE RULES:
- Russian storytelling. Short paragraphs. No bold headers, no bullet lists.
- Strength-first framing. No shame language.
- Maximum 800ms non-decorative animation (Constitution Law 4).
- Never say "volunteer platform" or "LinkedIn competitor".
{voice_rules}

SURFACE: {surface_instruction}

{f"USER CONTEXT: {user_context}" if user_context else ""}
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
