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
from app.core.assessment.bars import EvaluationResult


async def evaluate_answer(
    question_en: str,
    answer: str,
    expected_concepts: list[dict[str, Any]],
    return_details: bool = False,
) -> float | EvaluationResult:
    """Score an open-ended answer using multi-model swarm consensus.

    Same interface as bars.evaluate_answer() — drop-in replacement.
    Falls back to bars.evaluate_answer() on any failure.

    BUG-01 fix (2026-03-25): Added return_details=True support so swarm path
    produces evaluation_log for Phase 2 Transparent Logs. Without this, the
    /aura/me/explanation endpoint returned empty for all swarm-evaluated sessions.
    """
    from app.core.assessment.bars import EvaluationResult

    if not answer.strip():
        result = EvaluationResult(0.0, {}, "swarm")
        return result if return_details else 0.0

    try:
        concept_scores = await _swarm_evaluate_scores(question_en, answer, expected_concepts)
        from app.core.assessment.bars import _aggregate

        composite = _aggregate(concept_scores, expected_concepts)
        if return_details:
            return EvaluationResult(composite, concept_scores, "swarm")
        return composite
    except Exception as e:
        logger.warning(f"Swarm evaluation failed, falling back to BARS: {e}")
        from app.core.assessment.bars import evaluate_answer as bars_evaluate

        return await bars_evaluate(question_en, answer, expected_concepts, return_details=return_details)


async def _swarm_evaluate_scores(
    question_en: str,
    answer: str,
    expected_concepts: list[dict[str, Any]],
) -> dict[str, float]:
    """Run SwarmEngine to get multi-model concept scores. Returns raw concept scores dict.

    Lazy-imports the `docker` library inside the function body so that hosts
    without the docker pip package (e.g. Railway production container) never
    trigger ModuleNotFoundError at import time. If docker is missing OR the
    Docker daemon is unreachable (`docker.from_env()` raises), this function
    raises RuntimeError, which the outer `evaluate_answer` catches and falls
    back to bars.evaluate_answer — preserving the documented contract that
    swarm failures degrade gracefully to BARS.
    """
    import os
    import sys

    # Add packages/ to path so swarm package is importable
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    )
    packages_path = os.path.join(project_root, "packages")
    if packages_path not in sys.path:
        sys.path.insert(0, packages_path)

    # Lazy import — fails closed with a RuntimeError that the outer
    # evaluate_answer try/except converts into a BARS fallback.
    try:
        import docker as _docker
    except ImportError as e:
        logger.warning(
            "swarm_service: docker library not installed in this runtime — "
            "falling back to BARS evaluation"
        )
        raise RuntimeError(f"docker library unavailable: {e}") from e

    from swarm import DomainTag, StakesLevel, SwarmConfig, SwarmEngine

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

    # Create a new Docker container for the ANUS agent.
    # Both `from_env()` and `containers.run()` raise docker.errors.DockerException
    # if the daemon is unreachable (e.g. Railway container has no Docker daemon).
    # Caught and re-raised as RuntimeError so the outer fallback engages.
    try:
        client = _docker.from_env()
        container = client.containers.run("anus-agent", detach=True)
    except Exception as e:
        logger.warning(
            "swarm_service: docker daemon unreachable or anus-agent image missing — "
            "falling back to BARS evaluation",
            error=str(e)[:200],
        )
        raise RuntimeError(f"docker runtime unavailable: {e}") from e

    engine = SwarmEngine(env=env, container=container)

    config = SwarmConfig(
        question=swarm_prompt,
        context="Professional competency assessment evaluation for Volaura platform.",
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

    return concept_scores


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
