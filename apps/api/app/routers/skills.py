"""Skills Execution Router — one endpoint, all skills alive.

POST /api/skills/{skill_name} — takes user context, runs LLM with skill prompt,
returns structured output per skill's ## Output spec.

This is the v0Laura engine: 1 platform + skill library.
Skills live as markdown in memory/swarm/skills/.
This router reads them, injects user data, calls LLM, returns output.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.deps import CurrentUserId, SupabaseUser
from app.middleware.rate_limit import RATE_DEFAULT, RATE_LLM, limiter
from app.services.llm import evaluate_with_llm

router = APIRouter(prefix="/skills", tags=["skills"])

# ── Paths ─────────────────────────────────────────────────────────────────────

# Navigate from routers/ → project root → memory/swarm/skills/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "memory" / "swarm" / "skills"

# Product skills that are allowed to be executed via API
ALLOWED_SKILLS = {
    "aura-coach",
    "feed-curator",
    "ai-twin-responder",
    "content-formatter",
    "behavior-pattern-analyzer",
    # assessment-generator is internal (not user-facing API)
}


# ── Schemas ───────────────────────────────────────────────────────────────────


class SkillRequest(BaseModel):
    """Input for skill execution."""

    model_config = ConfigDict(extra="allow")

    # Optional overrides — skill determines what it needs
    context: dict[str, Any] | None = None
    question: str | None = None  # For ai-twin-responder
    language: str = "en"


class SkillResponse(BaseModel):
    """Output from skill execution."""

    skill: str
    output: dict[str, Any] | str
    model_used: str = "gemini"


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_skill(skill_name: str) -> str:
    """Load skill markdown content."""
    skill_path = SKILLS_DIR / f"{skill_name}.md"
    if not skill_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "SKILL_NOT_FOUND", "message": f"Skill '{skill_name}' not found"},
        )
    with open(skill_path, encoding="utf-8") as f:
        return f.read()


async def _get_user_context(db: Any, user_id: str) -> dict[str, Any]:
    """Fetch user's profile + AURA scores + recent assessments for skill context."""
    context: dict[str, Any] = {"user_id": user_id}

    try:
        # Profile
        profile_resp = await db.table("profiles").select("*").eq("id", user_id).single().execute()
        if profile_resp.data:
            context["profile"] = {
                "display_name": profile_resp.data.get("display_name", ""),
                "bio": profile_resp.data.get("bio", ""),
                "location": profile_resp.data.get("location", ""),
                "languages": profile_resp.data.get("languages", []),
            }
    except Exception as e:
        logger.debug(f"Profile fetch failed: {e}")

    try:
        # AURA scores
        aura_resp = await db.table("aura_scores").select("*").eq("volunteer_id", user_id).execute()
        if aura_resp.data:
            context["aura_scores"] = aura_resp.data
    except Exception as e:
        logger.debug(f"AURA fetch failed: {e}")

    try:
        # Competency scores — stored as JSONB in aura_scores.competency_scores, NOT a separate table.
        # Old code queried db.table("competency_scores") which doesn't exist → always empty.
        aura_row = (
            await db.table("aura_scores").select("competency_scores").eq("volunteer_id", user_id).single().execute()
        )
        if aura_row.data:
            raw = aura_row.data.get("competency_scores")
            if isinstance(raw, dict) and raw:
                # Convert {slug: score} dict → list of {competency_slug, score} for template compatibility
                context["competency_scores"] = [
                    {"competency_slug": slug, "score": score}
                    for slug, score in raw.items()
                    if isinstance(score, (int, float))
                ]
    except Exception as e:
        logger.debug(f"Competency scores fetch failed: {e}")

    return context


def _build_skill_prompt(skill_content: str, user_context: dict, request: SkillRequest) -> str:
    """Combine skill instructions + user context into LLM prompt."""
    # Strip the markdown metadata, keep the skill instructions
    # Remove ## Trigger section (not needed at execution time)
    lines = skill_content.split("\n")
    filtered = []
    skip_section = False
    for line in lines:
        if line.startswith("## Trigger"):
            skip_section = True
            continue
        if skip_section and line.startswith("## "):
            skip_section = False
        if not skip_section:
            filtered.append(line)

    skill_instructions = "\n".join(filtered)

    prompt = f"""You are executing a Volaura product skill. Follow the instructions EXACTLY.

{skill_instructions}

---

USER CONTEXT:
{_format_context(user_context)}

USER REQUEST:
{request.question or request.context or "Generate default output for this user"}

Language: {request.language}

RESPOND WITH VALID JSON matching the ## Output spec above. Nothing else."""

    return prompt


def _format_context(ctx: dict) -> str:
    """Format user context for LLM prompt."""
    parts = []
    if "profile" in ctx:
        p = ctx["profile"]
        parts.append(f"Name: {p.get('display_name', 'Unknown')}")
        if p.get("bio"):
            parts.append(f"Bio: {p['bio']}")
        if p.get("location"):
            parts.append(f"Location: {p['location']}")

    if "aura_scores" in ctx and ctx["aura_scores"]:
        score = ctx["aura_scores"][0]
        parts.append(f"AURA Total: {score.get('total_score', 'N/A')}")
        parts.append(f"Badge Tier: {score.get('badge_tier', 'none')}")

    if "competency_scores" in ctx and ctx["competency_scores"]:
        parts.append("Competency Scores:")
        for cs in ctx["competency_scores"][:8]:
            parts.append(f"  - {cs['competency_slug']}: {cs['score']}")

    return "\n".join(parts) if parts else "No user data available yet."


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/")
@limiter.limit(RATE_DEFAULT)
async def list_skills(request: Request):
    """List all available product skills."""
    skills = []
    if SKILLS_DIR.exists():
        for f in sorted(SKILLS_DIR.glob("*.md")):
            name = f.stem
            if name in ALLOWED_SKILLS:
                # Read first line as title
                with open(f, encoding="utf-8") as fh:
                    title = fh.readline().replace("#", "").strip()
                skills.append({"name": name, "title": title, "endpoint": f"/api/skills/{name}"})

    return {"data": skills, "meta": {"count": len(skills)}}


@router.post("/{skill_name}", response_model=SkillResponse)
@limiter.limit(RATE_LLM)
async def execute_skill(
    request: Request,
    skill_name: str,
    body: SkillRequest,
    db: SupabaseUser,
    user_id: CurrentUserId,
):
    """Execute a product skill with user's context.

    Loads the skill markdown, injects user data (profile, AURA, competencies),
    calls LLM, returns structured output.
    """
    if skill_name not in ALLOWED_SKILLS:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "SKILL_NOT_ALLOWED",
                "message": f"Skill '{skill_name}' is not available for API execution",
            },
        )

    # Load skill — wrapped in asyncio.to_thread to avoid blocking the event loop.
    # _load_skill raises HTTPException(404) on missing skill; to_thread propagates it correctly.
    skill_content = await asyncio.to_thread(_load_skill, skill_name)

    # Get user context from DB
    user_context = await _get_user_context(db, user_id)

    # Build prompt
    prompt = _build_skill_prompt(skill_content, user_context, body)

    # Execute via LLM
    try:
        result = await evaluate_with_llm(prompt, response_format="json", timeout=20.0)
        logger.info(f"Skill '{skill_name}' executed for user {user_id[:8]}...")

        return SkillResponse(
            skill=skill_name,
            output=result,
            model_used="gemini",
        )

    except Exception as e:
        logger.error(f"Skill '{skill_name}' execution failed: {e}")
        # MED-03 FIX: Don't leak internal error details to client
        raise HTTPException(
            status_code=502,
            detail={
                "code": "SKILL_EXECUTION_FAILED",
                "message": "Skill execution failed. Try again later.",
            },
        )
