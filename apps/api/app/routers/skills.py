"""Skills Execution Router — one endpoint, all skills alive.

POST /api/skills/{skill_name} — takes user context, runs LLM with skill prompt,
returns structured output per skill's ## Output spec.

This is the v0Laura engine: 1 platform + skill library.
Skills live as markdown in memory/swarm/skills/.
This router reads them, injects user data, calls LLM, returns output.

Wave 3 additions (2026-04-15):
- atlas_signature on every response (audit trail)
- voice validation against atlas_core.voice (observability, non-blocking)
- compliance logging into public.automated_decision_log (GDPR Art.22 / AI Act)
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict

from app.deps import CurrentUserId, SupabaseAdmin, SupabaseUser
from app.middleware.rate_limit import RATE_DEFAULT, RATE_LLM, limiter
from app.services.llm import evaluate_with_llm

router = APIRouter(prefix="/skills", tags=["skills"])

# ── Paths ─────────────────────────────────────────────────────────────────────

# Navigate from routers/ → project root → memory/swarm/skills/
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
SKILLS_DIR = PROJECT_ROOT / "memory" / "swarm" / "skills"

# ── Wave-3 package bootstrap ─────────────────────────────────────────────────
# `packages/ecosystem-compliance` and `packages/atlas-core` are monorepo siblings
# not installed into the API venv. Until we wire a workspace install
# (`pip install -e ../../packages/atlas-core/python` in Railway build), we do a
# guarded sys.path prepend. Idempotent — multiple imports of this module don't
# bloat sys.path.
# TODO(v0laura): migrate to `pip install -e` in apps/api/pyproject.toml or a
# Railway nixpacks step once the packages stabilise.
_PKG_PATHS = [
    PROJECT_ROOT / "packages" / "ecosystem-compliance" / "python",
    PROJECT_ROOT / "packages" / "atlas-core" / "python",
]
for _p in _PKG_PATHS:
    _s = str(_p)
    if _p.exists() and _s not in sys.path:
        sys.path.insert(0, _s)

try:
    from atlas_core.voice import validate_voice  # type: ignore
    from ecosystem_compliance.models import AutomatedDecisionCreate  # type: ignore

    _WAVE3_READY = True
except Exception as _e:  # pragma: no cover — defensive
    logger.warning(f"Wave-3 modules unavailable ({_e}); skills will run without voice/compliance")
    _WAVE3_READY = False

# ── ALLOWED_SKILLS — auto-detected from disk + manual block-list ─────────────
#
# A skill is API-exposable iff:
#   1) Its .md has both `## Input` and `## Output` sections (READY contract)
#   2) Its name is NOT in INTERNAL_ONLY_SKILLS (produces reports for backend / CEO,
#      not end-users; these are called internally via the swarm, never via HTTP)
#
# To add a new user-facing skill: just ship the .md with ## Input and ## Output
# sections. No code change required. To keep one internal: add its stem here.

INTERNAL_ONLY_SKILLS: set[str] = {
    "assessment-generator",  # writes question bank — admin-only
    "ceo-report-agent",  # batch close summaries for CEO — no end-user shape
}

_INPUT_RE = re.compile(r"^##\s+Input\b", re.MULTILINE)
_OUTPUT_RE = re.compile(r"^##\s+Output\b", re.MULTILINE)


def _scan_allowed_skills() -> set[str]:
    """Scan SKILLS_DIR (non-archive) for READY skills; drop internal-only ones."""
    found: set[str] = set()
    if not SKILLS_DIR.exists():
        return found
    for f in SKILLS_DIR.glob("*.md"):
        if f.name.startswith("_"):
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        if _INPUT_RE.search(txt) and _OUTPUT_RE.search(txt):
            if f.stem in INTERNAL_ONLY_SKILLS:
                continue
            found.add(f.stem)
    return found


# Computed once at import time. Re-scan requires process restart (intentional —
# skill surface area is a security boundary; hot-adding skills = risk).
ALLOWED_SKILLS: set[str] = _scan_allowed_skills() or {
    # Fallback for test envs that may monkey-patch SKILLS_DIR or run before the
    # repo's memory/swarm/skills/ is mounted. Keeps the 5 canonical user-facing
    # skills green even if disk scan returns nothing.
    "aura-coach",
    "feed-curator",
    "content-formatter",
    "behavior-pattern-analyzer",
}


# ── Schemas ───────────────────────────────────────────────────────────────────


class SkillRequest(BaseModel):
    """Input for skill execution."""

    model_config = ConfigDict(extra="allow")

    # Optional overrides — skill determines what it needs
    context: dict[str, Any] | None = None
    question: str | None = None
    language: str = "en"


class SkillResponse(BaseModel):
    """Output from skill execution."""

    skill: str
    output: dict[str, Any] | str
    model_used: str = "gemini"

    # Wave-3: audit + observability
    atlas_signature: str = ""
    voice_breaches: list[str] = []
    compliance_logged: bool = False


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_skill(skill_name: str) -> str:
    """Load skill markdown content. Path-traversal safe."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", skill_name):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_SKILL_NAME", "message": "Skill name contains invalid characters"},
        )
    skill_path = (SKILLS_DIR / f"{skill_name}.md").resolve()
    if not str(skill_path).startswith(str(SKILLS_DIR.resolve())):
        raise HTTPException(status_code=400, detail={"code": "INVALID_SKILL_NAME", "message": "Invalid skill path"})
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


def _atlas_signature(skill_name: str) -> str:
    """Per-invocation audit tag — one line per skill call."""
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"atlas-{skill_name}-{ts}"


def _hash_inputs(skill_name: str, body: SkillRequest, user_id: str) -> str:
    """SHA-256 of the invocation inputs. Used for compliance log — NO raw PII."""
    payload = {
        "skill": skill_name,
        "user_id": user_id,
        "language": body.language,
        "has_question": bool(body.question),
        "has_context": bool(body.context),
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _voice_check(output: Any) -> list[str]:
    """Run atlas_core voice validator on string outputs. Non-blocking — returns breach types."""
    if not _WAVE3_READY:
        return []
    if not isinstance(output, str):
        return []  # dict/json outputs are not free-text, voice rules don't apply
    try:
        result = validate_voice(output)  # noqa: F821 — guarded by _WAVE3_READY
        if result.passed:
            return []
        breach_types = [b.type for b in result.breaches]
        logger.warning(
            "skill voice breach",
            extra={"breaches": breach_types, "first_sample": result.breaches[0].sample if result.breaches else ""},
        )
        return breach_types
    except Exception as e:
        logger.debug(f"voice validator failed: {e}")
        return []


def _output_summary(output: Any, max_len: int = 200) -> str:
    """Small preview (no full PII) for explanation_text. First N chars."""
    try:
        s = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
    except Exception:
        s = str(output)
    s = s.replace("\n", " ").strip()
    return s[:max_len]


async def _log_automated_decision(
    db_admin: Any,
    *,
    user_id: str,
    skill_name: str,
    body: SkillRequest,
    output: Any,
) -> bool:
    """Insert a row into public.automated_decision_log. Never raises — log-and-swallow.

    GDPR Art.22 + EU AI Act: any LLM decision shown to a user must be auditable.
    We persist: skill name, language, output summary, inputs hash — NEVER raw user text.
    """
    if not _WAVE3_READY:
        return False
    try:
        model = AutomatedDecisionCreate(  # noqa: F821 — guarded
            user_id=user_id,  # type: ignore[arg-type]
            source_product="volaura",
            decision_type=f"skill_invoked_{skill_name}",
            decision_output={
                "skill": skill_name,
                "has_output": output is not None,
                "output_summary": _output_summary(output),
                "language": body.language,
            },
            algorithm_version="skills-engine-v1",
            model_inputs_hash=_hash_inputs(skill_name, body, user_id),
            explanation_text=f"Skill {skill_name} ran with language={body.language}",
        )
        # Pydantic → dict; dump to JSON-safe types (UUID/datetime serialisation)
        row = json.loads(model.model_dump_json())
        await db_admin.table("automated_decision_log").insert(row).execute()
        return True
    except Exception as e:
        # Compliance log failure MUST NEVER break the user response.
        logger.error(f"automated_decision_log insert failed for {skill_name}: {e}")
        return False


# ── Routes ────────────────────────────────────────────────────────────────────


@router.get("/")
@limiter.limit(RATE_DEFAULT)
async def list_skills(request: Request, _user: CurrentUserId):
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
    db_admin: SupabaseAdmin,
    user_id: CurrentUserId,
):
    """Execute a product skill with user's context.

    Loads the skill markdown, injects user data (profile, AURA, competencies),
    calls LLM, returns structured output + Wave-3 audit fields.
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

        # Wave-3: audit trail + voice check + compliance log
        signature = _atlas_signature(skill_name)
        voice_breaches = _voice_check(result)
        compliance_logged = await _log_automated_decision(
            db_admin,
            user_id=user_id,
            skill_name=skill_name,
            body=body,
            output=result,
        )

        return SkillResponse(
            skill=skill_name,
            output=result,
            model_used="gemini",
            atlas_signature=signature,
            voice_breaches=voice_breaches,
            compliance_logged=compliance_logged,
        )

    except HTTPException:
        raise
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
