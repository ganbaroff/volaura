"""BrandedBy — AI Twin personality prompt generation.

Reads character_state (verified skills, AURA score, XP, crystal balance)
and generates a personality prompt for the AI Twin via Gemini.

This is the core moat: character_state makes the AI Twin SMART.
Not a generic avatar — a persona grounded in verified real-world achievements.
"""

from loguru import logger

from app.services.llm import evaluate_with_llm

AURA_SKILL_LABELS: dict[str, str] = {
    "communication": "Communication",
    "reliability": "Reliability",
    "english_proficiency": "English",
    "leadership": "Leadership",
    "event_performance": "Event Performance",
    "tech_literacy": "Tech Literacy",
    "adaptability": "Adaptability",
    "empathy_safeguarding": "Empathy & Safeguarding",
}

BADGE_TIERS = {
    "platinum": ("Platinum", "top-tier"),
    "gold": ("Gold", "high-performing"),
    "silver": ("Silver", "skilled"),
    "bronze": ("Bronze", "active"),
}


def _badge_tier_from_score(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 90:
        return "platinum"
    if score >= 75:
        return "gold"
    if score >= 60:
        return "silver"
    if score >= 40:
        return "bronze"
    return None


def _build_character_context(character_state: dict) -> str:
    """Build a human-readable summary of character_state for the prompt."""
    lines: list[str] = []

    xp = character_state.get("xp_total", 0)
    crystals = character_state.get("crystal_balance", 0)
    streak = character_state.get("login_streak", 0)
    skills = character_state.get("verified_skills", [])

    lines.append(f"Total XP earned: {xp}")
    lines.append(f"Crystal balance: {crystals}")
    if streak > 0:
        lines.append(f"Current login streak: {streak} days")

    if skills:
        lines.append("\nVerified competencies:")
        for skill in skills:
            slug = skill.get("slug", "")
            aura = skill.get("aura_score")
            badge = skill.get("badge_tier") or _badge_tier_from_score(aura)
            label = AURA_SKILL_LABELS.get(slug, slug.replace("_", " ").title())
            if aura is not None:
                tier_info = BADGE_TIERS.get(badge or "", ("", ""))[1] if badge else ""
                lines.append(f"  • {label}: AURA {aura:.1f}/100" + (f" ({tier_info})" if tier_info else ""))
            else:
                lines.append(f"  • {label}: verified")
    else:
        lines.append("\nNo verified competencies yet (new user)")

    return "\n".join(lines)


async def generate_twin_personality(
    display_name: str,
    character_state: dict,
    _meta: dict | None = None,
) -> str:
    """Generate a personality prompt for an AI Twin from character_state.

    Args:
        display_name: The user's chosen display name for their twin.
        character_state: Dict from get_character_state RPC.

    Returns:
        A personality prompt string (200-400 words) describing the AI Twin.
    """
    context = _build_character_context(character_state)

    prompt = (
        f"You are generating an AI Twin personality profile for a verified professional"
        f' named "{display_name}".\n\n'
        f"This person's verified data from the Volaura platform:\n{context}\n\n"
        f"Generate a first-person personality profile for their AI Twin. This profile\n"
        f"will power a conversational AI that speaks as them on LinkedIn and professional"
        f" platforms.\n\n"
        f"Requirements:\n"
        f'- Write in first person ("I am...", "My strongest skill is...")\n'
        f"- 150-250 words\n"
        f"- Professional but warm and human\n"
        f"- Ground every claim in the verified data (don't invent achievements)\n"
        f"- Highlight top 2-3 verified skills by name with context\n"
        f'- Mention XP level to show activity level (e.g. "actively building my profile")\n'
        f"- End with 1 sentence about what opportunities they are open to\n"
        f"- NO hashtags, NO emojis, NO marketing speak\n"
        f"- Output ONLY the personality profile text, nothing else\n\n"
        f"Example tone: \"I'm a reliability-focused professional with a Gold badge in\n"
        f"Communication. My AURA score of 81 reflects consistent performance across"
        f' 12+ verified assessments..."\n\n'
        f"Write the personality profile now:"
    )

    try:
        result = await evaluate_with_llm(prompt, response_format="text", timeout=20, _meta=_meta)
        personality = str(result).strip()
        logger.info(
            "AI Twin personality generated",
            display_name=display_name,
            length=len(personality),
            skill_count=len(character_state.get("verified_skills", [])),
        )
        return personality
    except Exception as e:
        logger.error("Personality generation failed", error=str(e))
        # Fallback: rule-based personality (no LLM required)
        return _build_fallback_personality(display_name, character_state)


def _build_fallback_personality(display_name: str, character_state: dict) -> str:
    """Rule-based fallback personality when LLM is unavailable."""
    skills = character_state.get("verified_skills", [])
    xp = character_state.get("xp_total", 0)

    if not skills:
        return (
            f"I'm {display_name}, an active professional building my verified skill"
            f" profile on Volaura. I've earned {xp} XP through assessed activities"
            f" and I'm focused on growing my competencies. I'm open to"
            f" opportunities where I can contribute and learn."
        )

    top_skills = sorted(skills, key=lambda s: s.get("aura_score") or 0, reverse=True)[:3]
    skill_names = [AURA_SKILL_LABELS.get(s["slug"], s["slug"].replace("_", " ").title()) for s in top_skills]

    skill_str = ", ".join(skill_names[:-1]) + f" and {skill_names[-1]}" if len(skill_names) > 1 else skill_names[0]
    level = "experienced" if xp >= 500 else "active" if xp >= 100 else "emerging"

    return (
        f"I'm {display_name}, an {level} professional with verified competencies"
        f" in {skill_str}. My skills are backed by Volaura's assessment platform"
        f" with {xp} XP earned through real assessments. I'm open to opportunities"
        f" where I can apply my verified skills and make a meaningful impact."
    )
