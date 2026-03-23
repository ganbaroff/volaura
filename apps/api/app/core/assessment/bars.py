"""BARS (Behaviourally Anchored Rating Scale) LLM evaluator.

For open-ended assessment questions, this module uses Gemini 2.5 Flash
(with OpenAI GPT-4o-mini fallback, then keyword-based rule matching) to
score a volunteer's answer against the expected BARS concepts.

The evaluator returns a 0.0–1.0 composite score.
"""

from __future__ import annotations

import json
import re
from typing import Any

from loguru import logger

from app.config import settings


# ── Prompt ──────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are an expert volunteer assessment evaluator. "
    "Evaluate the provided answer against each expected BARS concept. "
    "Return ONLY a valid JSON object — no markdown, no explanation."
)

_USER_TEMPLATE = """\
Question (EN): {question_en}
Volunteer's answer: {answer}

Expected BARS concepts to evaluate (score each 0.0 to 1.0):
{concepts_json}

Return a JSON object where each key is a concept name and the value is a float score between 0.0 and 1.0.
Example: {{"active_listening": 0.8, "empathy": 0.6}}
"""


# ── Main entry point ─────────────────────────────────────────────────────────

async def evaluate_answer(
    question_en: str,
    answer: str,
    expected_concepts: list[dict[str, Any]],
) -> float:
    """Score an open-ended answer using BARS rubric via LLM.

    Args:
        question_en: The question text in English.
        answer: The volunteer's raw text answer.
        expected_concepts: List of concept dicts, each with at least a `name` key.
            e.g. [{"name": "active_listening", "weight": 0.5}, ...]

    Returns:
        Composite score 0.0–1.0.
    """
    if not answer.strip():
        return 0.0

    concept_names = [c["name"] for c in expected_concepts]
    concepts_json = json.dumps(concept_names)

    prompt = _USER_TEMPLATE.format(
        question_en=question_en,
        answer=answer.strip()[:2000],  # cap at 2000 chars
        concepts_json=concepts_json,
    )

    # Try primary (Gemini) → fallback (OpenAI) → keyword rule matching
    scores: dict[str, float] | None = None

    scores = await _try_gemini(prompt)

    if scores is None:
        logger.warning("Gemini evaluation failed — trying OpenAI fallback")
        scores = await _try_openai(prompt, concept_names)

    if scores is None:
        logger.warning("OpenAI evaluation failed — using keyword rule matching")
        scores = _keyword_fallback(answer, expected_concepts)

    return _aggregate(scores, expected_concepts)


# ── LLM backends ─────────────────────────────────────────────────────────────

async def _try_gemini(prompt: str) -> dict[str, float] | None:
    """Call Gemini 2.5 Flash with JSON mode."""
    try:
        from google import genai  # type: ignore

        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": _SYSTEM_PROMPT,
                "response_mime_type": "application/json",
            },
        )
        raw = response.text
        return _parse_json_scores(raw)
    except Exception as e:
        logger.warning(f"Gemini BARS evaluation error: {e}")
        return None


async def _try_openai(prompt: str, concept_names: list[str]) -> dict[str, float] | None:
    """Call OpenAI GPT-4o-mini as fallback."""
    try:
        import openai  # type: ignore

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=256,
            temperature=0.1,
        )
        raw = response.choices[0].message.content or ""
        return _parse_json_scores(raw)
    except Exception as e:
        logger.warning(f"OpenAI BARS evaluation error: {e}")
        return None


# ── Keyword fallback ──────────────────────────────────────────────────────────

def _keyword_fallback(
    answer: str,
    expected_concepts: list[dict[str, Any]],
) -> dict[str, float]:
    """Simple keyword matching when all LLMs fail.

    Each concept can optionally carry a `keywords` list.
    Score = fraction of keywords found in the answer (case-insensitive).
    If no keywords defined, defaults to 0.5 (neutral).
    """
    answer_lower = answer.lower()
    scores: dict[str, float] = {}

    for concept in expected_concepts:
        name = concept["name"]
        keywords: list[str] = concept.get("keywords", [])

        if not keywords:
            scores[name] = 0.5
            continue

        hits = sum(1 for kw in keywords if kw.lower() in answer_lower)
        scores[name] = min(1.0, hits / len(keywords))

    return scores


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_json_scores(raw: str) -> dict[str, float] | None:
    """Extract a JSON object from LLM output and coerce values to float [0,1]."""
    try:
        # Strip potential markdown code fences
        text = re.sub(r"```(?:json)?", "", raw).strip()
        data = json.loads(text)
        if not isinstance(data, dict):
            return None
        return {k: max(0.0, min(1.0, float(v))) for k, v in data.items()}
    except Exception:
        return None


def _aggregate(
    scores: dict[str, float],
    expected_concepts: list[dict[str, Any]],
) -> float:
    """Weighted average of concept scores.

    Concepts with a `weight` key use that; others get equal weight.
    """
    if not scores:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for concept in expected_concepts:
        name = concept["name"]
        weight = float(concept.get("weight", 1.0))
        score = scores.get(name, 0.0)
        weighted_sum += score * weight
        total_weight += weight

    if total_weight == 0:
        return 0.0

    return max(0.0, min(1.0, weighted_sum / total_weight))
