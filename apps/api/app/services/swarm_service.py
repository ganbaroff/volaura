"""Swarm-powered BARS evaluation — multi-model consensus scoring.

When settings.swarm_enabled is True, open-ended answers are scored by
multiple LLM models in parallel (via MiroFish SwarmEngine) instead of
a single Gemini call. The consensus-aggregated concept scores are then
passed through the same BARS `_aggregate()` logic.

Falls back to standard BARS evaluation on any swarm failure.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from app.config import settings


async def evaluate_answer(
    question_en: str,
    answer: str,
    expected_concepts: list[dict[str, Any]],
) -> float:
    """Score an open-ended answer using multi-model swarm consensus.

    Same interface as bars.evaluate_answer() — drop-in replacement.
    Falls back to bars.evaluate_answer() on any failure.
    """
    if not answer.strip():
        return 0.0

    try:
        return await _swarm_evaluate(question_en, answer, expected_concepts)
    except Exception as e:
        logger.warning(f"Swarm evaluation failed, falling back to BARS: {e}")
        from app.core.assessment.bars import evaluate_answer as bars_evaluate
        return await bars_evaluate(question_en, answer, expected_concepts)


async def _swarm_evaluate(
    question_en: str,
    answer: str,
    expected_concepts: list[dict[str, Any]],
) -> float:
    """Run SwarmEngine to get multi-model concept scores."""
    import sys
    import os

    # Add packages/ to path so swarm package is importable
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )))
    packages_path = os.path.join(project_root, "packages")
    if packages_path not in sys.path:
        sys.path.insert(0, packages_path)

    from swarm import SwarmEngine, SwarmConfig, StakesLevel, DomainTag

    concept_names = [c["name"] for c in expected_concepts]
    concepts_json = json.dumps(concept_names)

    # Build the same prompt structure BARS uses, but for multi-model consensus
    swarm_prompt = (
        f"Score this volunteer's answer on each competency concept (0.0 to 1.0).\n\n"
        f"Question: {question_en}\n\n"
        f"Answer (first 2000 chars): {answer.strip()[:2000]}\n\n"
        f"Concepts to score: {concepts_json}\n\n"
        f"Return ONLY a JSON object mapping concept names to float scores.\n"
        f'Example: {{"active_listening": 0.8, "empathy": 0.6}}'
    )

    # Inject API keys from FastAPI settings into swarm env
    env = dict(os.environ)
    if settings.gemini_api_key:
        env["GEMINI_API_KEY"] = settings.gemini_api_key
    if settings.openai_api_key:
        env["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.groq_api_key:
        env["GROQ_API_KEY"] = settings.groq_api_key

    engine = SwarmEngine(env=env)

    config = SwarmConfig(
        question=swarm_prompt,
        context="Volunteer competency assessment evaluation for Volaura platform.",
        stakes=StakesLevel.LOW,  # 3-5 agents, fast
        domain=DomainTag.GENERAL,
        timeout_seconds=20.0,
        auto_research=False,
    )

    report = await asyncio.wait_for(
        engine.decide(config),
        timeout=25.0,
    )

    logger.info(
        "Swarm BARS evaluation complete",
        agents=len(report.agent_results),
        winner=report.winner,
        score=report.winner_score,
        latency_ms=report.total_latency_ms,
    )

    # Extract concept scores from agent results
    concept_scores = _extract_consensus_scores(report, concept_names)

    if not concept_scores:
        raise ValueError("Swarm returned no parseable concept scores")

    # Use BARS aggregation logic
    from app.core.assessment.bars import _aggregate
    return _aggregate(concept_scores, expected_concepts)


def _extract_consensus_scores(
    report: Any,
    concept_names: list[str],
) -> dict[str, float]:
    """Extract averaged concept scores from all successful agent results."""
    all_scores: dict[str, list[float]] = {name: [] for name in concept_names}

    for agent in report.agent_results:
        # Each agent's response may contain JSON concept scores
        raw = getattr(agent, "raw_response", "") or ""
        try:
            # Try to parse JSON from agent response
            import re
            text = re.sub(r"```(?:json)?", "", raw).strip()
            if text.startswith("{"):
                data = json.loads(text)
                if isinstance(data, dict):
                    for name in concept_names:
                        if name in data:
                            score = max(0.0, min(1.0, float(data[name])))
                            all_scores[name].append(score)
        except (json.JSONDecodeError, ValueError, TypeError):
            continue

    # Average scores across agents (consensus)
    consensus: dict[str, float] = {}
    for name, scores in all_scores.items():
        if scores:
            consensus[name] = sum(scores) / len(scores)
        else:
            consensus[name] = 0.5  # neutral if no agent scored this concept

    return consensus
