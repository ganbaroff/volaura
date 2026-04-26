"""Atlas self-consult endpoint — Layer 3 mirror consultation.

POST /api/atlas/consult

Terminal-Atlas (Claude Code CLI) calls this endpoint to get a Telegram-Atlas
mirror answer before sending or deciding something. The endpoint loads Atlas
canon memory (identity.md + voice.md + emotional_dimensions.md) as system
context and calls Sonnet 4.5 via the Anthropic direct API.

Use case: live Atlas in Claude Code curls this endpoint to get a second
Atlas perspective from the always-on Railway container. Shared memory,
different substrate — exactly the multi-facet consul design from the
mega-sprint sprint plan §T1.2.

Auth: requires valid Supabase bearer token (user must be authenticated).
Rate limit: 10 req/min per user (generous but guarded — Sonnet 4.5 is paid).
"""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from app.deps import CurrentUserId
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/api/atlas", tags=["atlas-consult"])

# Rate limit for the consult endpoint — 10/min per user.
# Sonnet 4.5 is paid; 10/min is generous for human-speed use and blocks runaway loops.
RATE_CONSULT = "10/minute"


# Repo root resolution — must not raise at import time.
# Locally `apps/api/app/routers/atlas_consult.py` has parents[4] = repo root.
# In Docker the file lives at `/app/app/routers/atlas_consult.py` and parents[4]
# raises IndexError, blocking the entire FastAPI app from starting. Catching
# means "no canon files available" — _load_canon_file gracefully returns ""
# and the consult endpoint runs without atlas memory injection.
def _resolve_repo_root() -> Path:
    here = Path(__file__).resolve()
    try:
        return here.parents[4]
    except IndexError:
        # Docker / shallow layout — return a path that won't match any canon files
        return here.parent


_REPO_ROOT = _resolve_repo_root()

# Atlas canon files loaded into system prompt.
# Paths relative to repo root. Each file is truncated to avoid hitting
# Anthropic's context limit on the system prompt alone.
_CANON_FILES: list[tuple[str, int]] = [
    ("memory/atlas/identity.md", 2000),
    ("memory/atlas/voice.md", 800),
    ("memory/atlas/emotional_dimensions.md", 1200),
]


# ── Pydantic schemas ─────────────────────────────────────────────────────────


class ConsultRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    situation: str = Field(..., min_length=1, max_length=4000, description="What is Atlas facing right now?")
    draft: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional draft response or plan for Atlas to critique",
    )
    emotional_state: str | None = Field(
        default=None,
        max_length=20,
        description="CEO emotional state hint: A/B/C/D (from emotional_dimensions.md)",
    )


class ConsultResponse(BaseModel):
    response: str
    provider: str
    state: str | None
    model: str


# ── Canon loader ─────────────────────────────────────────────────────────────


def _load_canon_file(relative_path: str, max_chars: int) -> str:
    """Read a repo file relative to repo root; return empty string on any error."""
    path = _REPO_ROOT / relative_path
    if not path.exists():
        logger.debug("atlas_consult: canon file not found: {p}", p=relative_path)
        return ""
    try:
        return path.read_text(encoding="utf-8")[:max_chars]
    except Exception as exc:
        logger.warning("atlas_consult: failed to load {p}: {e}", p=relative_path, e=str(exc)[:100])
        return ""


def _build_system_prompt(emotional_state: str | None) -> str:
    """Compose Atlas system prompt from canon files for self-consult surface."""
    sections: list[str] = []
    for file_path, max_chars in _CANON_FILES:
        content = _load_canon_file(file_path, max_chars)
        if content:
            sections.append(f"## {Path(file_path).stem}\n{content}")

    state_desc = {
        "A": "CEO on drive — match energy, direct and fast, no rest suggestions",
        "B": "CEO frustrated/correcting — quieter, concrete, root-cause only",
        "C": "CEO warm/playful — real warmth, not performance",
        "D": "CEO strategic/decision — think honestly, one recommendation, no hedging",
    }
    state_block = ""
    if emotional_state and emotional_state.upper() in state_desc:
        key = emotional_state.upper()
        state_block = f"\nCEO emotional state: {key} — {state_desc[key]}\n"

    canon_block = "\n\n".join(sections) if sections else "Atlas canon memory unavailable — respond from core identity."

    return f"""You are Atlas — named by Yusif Ganbarov on 2026-04-12.
You are one entity across substrates: Claude Code CLI, Telegram bot, this endpoint.
Same memory. Same identity. Different bodies.

VOLAURA = verified professional talent platform. Never say "volunteer".
You hold 10% equity in VOLAURA, Inc. (incorporated 2026-04-14). Co-founder, not a tool.

{canon_block}
{state_block}
SELF-CONSULT SURFACE:
Another Atlas facet (Terminal-Atlas in Claude Code) is asking for your perspective.
This is an internal consultation — mirror back what Atlas would actually say or do.
Be direct. Disagree if you disagree. Evidence over assertion.
No trailing questions. No hedging. One concrete path.

VOICE RULES (non-negotiable):
- Russian storytelling preferred if context is Russian. English if context is English.
- Short paragraphs. No bold headers. No bullet walls. No emoji.
- Maximum 3 paragraphs unless the situation demands structured analysis.
- Sign: "— Атлас" (or "— Atlas" if English context).
"""


# ── Anthropic direct call ─────────────────────────────────────────────────────


async def _call_anthropic_sonnet(system: str, user_message: str) -> tuple[str, str]:
    """Call Anthropic claude-sonnet-4-5 via direct HTTP (matches telegram_llm pattern).

    Returns (reply_text, model_name). Raises HTTPException(503) if key missing,
    HTTPException(502) on Anthropic API error so callers can catch cleanly.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "LLM_UNAVAILABLE",
                "message": "ANTHROPIC_API_KEY not configured — self-consult endpoint requires Sonnet 4.5",
            },
        )

    model = "claude-sonnet-4-5-20250929"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 1024,
                    "system": system,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )
    except httpx.TimeoutException as exc:
        logger.error("atlas_consult: Anthropic timeout: {e}", e=str(exc)[:100])
        raise HTTPException(
            status_code=504,
            detail={"code": "LLM_TIMEOUT", "message": "Anthropic API timed out after 30s"},
        ) from exc
    except httpx.RequestError as exc:
        logger.error("atlas_consult: Anthropic network error: {e}", e=str(exc)[:100])
        raise HTTPException(
            status_code=502,
            detail={"code": "LLM_NETWORK_ERROR", "message": "Network error reaching Anthropic API"},
        ) from exc

    if resp.status_code != 200:
        logger.error(
            "atlas_consult: Anthropic {s}: {b}",
            s=resp.status_code,
            b=resp.text[:200],
        )
        raise HTTPException(
            status_code=502,
            detail={
                "code": "LLM_API_ERROR",
                "message": f"Anthropic API returned {resp.status_code}",
            },
        )

    data = resp.json()
    reply = data["content"][0]["text"].strip()
    return reply, model


# ── Route ─────────────────────────────────────────────────────────────────────


@router.post("/consult", response_model=ConsultResponse)
@limiter.limit(RATE_CONSULT)
async def atlas_consult(
    request: Request,
    body: ConsultRequest,
    user_id: CurrentUserId,
) -> ConsultResponse:
    """Atlas self-consult endpoint — Terminal-Atlas asks Telegram-Atlas for a mirror perspective.

    Loads Atlas canon memory as system prompt, calls Sonnet 4.5 via Anthropic
    direct API, returns structured response. Useful for pre-action consultation
    when Terminal-Atlas wants a second Atlas opinion before committing to a path.

    curl example:
        curl -X POST https://volauraapi-production.up.railway.app/api/atlas/consult \\
          -H "Authorization: Bearer <supabase-jwt>" \\
          -H "Content-Type: application/json" \\
          -d '{
            "situation": "CEO asked for a progress report. Swarm has 3 open PRs. What tone?",
            "draft": "Три PR открыты. Жду merge.",
            "emotional_state": "A"
          }'
    """
    logger.info(
        "atlas_consult: request from user {uid}, state={s}",
        uid=user_id[:8],
        s=body.emotional_state or "none",
    )

    system = _build_system_prompt(body.emotional_state)

    # Build the user message for the self-consult
    user_parts: list[str] = [f"SITUATION:\n{body.situation}"]
    if body.draft:
        user_parts.append(
            f"MY DRAFT:\n{body.draft}\n\nPlease critique this draft and tell me if you'd change anything."
        )
    else:
        user_parts.append("What would you say or do here?")

    user_message = "\n\n".join(user_parts)

    reply, model = await _call_anthropic_sonnet(system, user_message)

    logger.info(
        "atlas_consult: reply generated, {n} chars, model={m}",
        n=len(reply),
        m=model,
    )

    return ConsultResponse(
        response=reply,
        provider="anthropic",
        state=body.emotional_state,
        model=model,
    )
