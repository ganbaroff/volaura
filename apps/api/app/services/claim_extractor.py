"""Claim extraction from CV text via LLM.

Sprint 1 of the CV Truth Machine (ADR-017 Layer 1).
Takes plain text CV → returns structured claims (tools, roles, projects, etc.)
that can be verified via experience interview questions.

Uses the existing LLM routing infrastructure (llm.py) — credits-first providers.
"""

from __future__ import annotations

import json
import time

from loguru import logger

from app.schemas.cv import ClaimExtractionResult, ClaimItem, ExtractionMeta
from app.services.llm import evaluate_with_llm

# 8 VOLAURA competencies — same as PoC and AURA weights
COMPETENCIES = {
    "communication": "clear, audience-adapted information exchange under pressure",
    "reliability": "follow-through, deadline discipline, ownership of commitments",
    "english_proficiency": "professional English comprehension and expression",
    "leadership": "directing, motivating and developing people without/with authority",
    "event_performance": "on-site operational execution: venues, crowds, vendors, protocol",
    "tech_literacy": "competent use of digital tools, data accuracy, troubleshooting",
    "adaptability": "effective response to change, ambiguity and setbacks",
    "empathy_safeguarding": "care for people's wellbeing, de-escalation, safeguarding",
}

_SYSTEM_PROMPT = """\
You are a senior CV analyst for VOLAURA, a truth-verification platform.
Your task: extract VERIFIABLE CLAIMS from a candidate's CV.

A claim is a concrete, testable assertion: a tool used, a role held, a project worked on,
an employer, a certification, or a specific skill demonstrated in a stated context.

Rules:
- Extract ONLY claims that can be tested with a question (not "team player" or "hard-working").
- Each claim must have a specific value (ClickUp, not "project management tools").
- Include the CONTEXT from the CV (which project, what team size, what year).
- Quote the SOURCE LINE from the CV verbatim (or near-verbatim).
- Map each claim to the BEST-FIT VOLAURA competency.
- Set confidence 0.0-1.0 based on how specific and testable the claim is.
- Maximum 20 claims. Prioritize the most specific and testable ones.

Return STRICT JSON only, no markdown fences."""

_USER_TEMPLATE = """\
CANDIDATE CV:
---
{cv_text}
---

VOLAURA COMPETENCIES (use these slugs):
{competency_list}

Extract verifiable claims. Return JSON:
{{"claims": [{{
  "id": "claim_001",
  "type": "tool|role|project|employer|certification|skill",
  "value": "<specific thing claimed>",
  "context": "<surrounding context from CV>",
  "source_line": "<verbatim CV text>",
  "suggested_competency": "<slug>",
  "confidence": <float 0-1>
}}]}}"""


async def extract_claims(cv_text: str) -> ClaimExtractionResult:
    """Extract structured claims from CV text via LLM.

    Uses evaluate_with_llm which routes through credits-first providers
    (Vertex → Gemini → Groq → OpenAI).

    Returns ClaimExtractionResult with claims array and extraction metadata.
    Raises ValueError if LLM returns unparseable output.
    """
    t0 = time.monotonic()

    comp_lines = "\n".join(f"- {k}: {v}" for k, v in COMPETENCIES.items())
    user_prompt = _USER_TEMPLATE.format(cv_text=cv_text[:8000], competency_list=comp_lines)

    raw_result = await evaluate_with_llm(
        prompt=user_prompt,
        system=_SYSTEM_PROMPT,
        response_format="json",
    )

    elapsed_ms = int((time.monotonic() - t0) * 1000)

    # Parse LLM response
    try:
        if isinstance(raw_result, str):
            data = json.loads(raw_result)
        elif isinstance(raw_result, dict):
            data = raw_result
        else:
            raise ValueError(f"Unexpected LLM response type: {type(raw_result)}")
    except json.JSONDecodeError as e:
        logger.error("Claim extraction LLM returned invalid JSON", error=str(e))
        raise ValueError(f"LLM returned invalid JSON: {e}") from e

    raw_claims = data.get("claims", [])
    if not isinstance(raw_claims, list):
        raise ValueError("LLM response missing 'claims' array")

    # Validate and build typed claims
    claims: list[ClaimItem] = []
    for i, rc in enumerate(raw_claims[:20]):  # cap at 20
        try:
            claim = ClaimItem(
                id=rc.get("id", f"claim_{i + 1:03d}"),
                type=_normalize_claim_type(rc.get("type", "skill")),
                value=str(rc.get("value", "")),
                context=str(rc.get("context", "")),
                source_line=str(rc.get("source_line", "")),
                suggested_competency=_normalize_competency(rc.get("suggested_competency", "")),
                confidence=float(rc.get("confidence", 0.5)),
            )
            if claim.value.strip():  # skip empty claims
                claims.append(claim)
        except (ValueError, TypeError) as e:
            logger.warning("Skipping malformed claim", index=i, error=str(e))
            continue

    # Determine which model was used (from llm.py internals)
    model_name = "unknown"
    if isinstance(raw_result, dict) and "model" in raw_result:
        model_name = raw_result["model"]

    meta = ExtractionMeta(
        total_claims=len(claims),
        extraction_model=model_name,
        extraction_time_ms=elapsed_ms,
    )

    logger.info(
        "Claims extracted",
        total=len(claims),
        model=model_name,
        elapsed_ms=elapsed_ms,
        types=[c.type for c in claims],
    )

    return ClaimExtractionResult(claims=claims, meta=meta)


def _normalize_claim_type(raw: str) -> str:
    """Normalize claim type to one of the allowed values."""
    allowed = {"tool", "role", "project", "employer", "certification", "skill"}
    lower = raw.lower().strip()
    if lower in allowed:
        return lower
    return "skill"  # fallback


def _normalize_competency(raw: str) -> str:
    """Normalize competency slug to one of the 8 VOLAURA competencies."""
    lower = raw.lower().strip().replace(" ", "_").replace("-", "_")
    if lower in COMPETENCIES:
        return lower
    return "communication"  # fallback — most general
