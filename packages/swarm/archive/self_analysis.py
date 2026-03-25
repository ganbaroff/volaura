"""
MiroFish Self-Analysis — ask the swarm to evaluate its own weaknesses.

Constraint: only suggest improvements with >15% estimated impact.
No cosmetic changes. No theoretical improvements. Only concrete, measurable gains.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Load env vars from apps/api/.env
env_path = Path(__file__).parent.parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

sys.path.insert(0, str(Path(__file__).parent.parent))
from swarm.engine import SwarmEngine
from swarm.types import SwarmConfig, StakesLevel, DomainTag, PathDefinition


SELF_ANALYSIS_QUESTION = """
You are evaluating MiroFish — a multi-model AI decision engine.
Here is what MiroFish currently does:

ARCHITECTURE:
- 14+ LLM providers from 5 APIs (Gemini, Groq, DeepSeek, OpenAI, OpenRouter)
- Auto-discovery of available models via API scanning
- PMAgent orchestrates: dispatch → aggregate → debate → scale → synthesize
- Middleware chain: LoopDetection, ResponseDedup, ContextBudget, TimeoutGuard
- Per-model calibration weights by domain (correct +5%, wrong -5%)
- Conditional debate: triggered only when divergence >50% (ICML 2024)
- MoA synthesis: LLM aggregation for MEDIUM+ stakes decisions
- Skill library: 14 skills auto-matched to tasks, maturity tracking
- Agent memory: per-model experience logs
- Self-scaling: adds agents when consensus too low (<40%) or too high (>90%)

CURRENT WEAKNESSES (known):
- Memory is flat JSON files — no structure, no confidence scoring
- No streaming — all results batched at end
- Cost estimation stubbed out (always 0.0)
- No parallel tournament runs for CRITICAL decisions
- No graph-based orchestration (linear pipeline only)

YOUR TASK:
Evaluate each path below. For each, estimate the PERCENTAGE IMPROVEMENT
to overall decision quality, speed, or cost efficiency.

HARD CONSTRAINT: Only recommend paths where estimated improvement is >15%.
If a path gives <15% improvement, score it LOW on user_impact and dev_speed.
We want HIGH-ROI changes only, not incremental polish.
"""

PATHS = {
    "structured_memory": PathDefinition(
        name="Structured Memory (Episodic/Semantic/Metric layers)",
        description="Replace flat JSON with 3-layer memory: episodic (decisions), semantic (extracted facts with confidence), metric (performance stats). Add MemoryEnrichmentMiddleware to auto-inject relevant facts into agent prompts.",
        best_case="Agents make 30% better decisions by accessing relevant past context. Calibration becomes automatic.",
        worst_case="Over-engineering for current scale. 2-3 days of work for marginal gain.",
        effort="M",
    ),
    "parallel_dispatch": PathDefinition(
        name="True Parallel Dispatch with Per-Provider Timeouts",
        description="Replace asyncio.gather() with asyncio.wait() + per-provider timeout. Fast providers (Groq 200ms) don't wait for slow ones (DeepSeek 3s). Process results as they arrive.",
        best_case="50% reduction in total latency for MEDIUM stakes (7-10 agents).",
        worst_case="Minimal improvement if all providers are similarly fast.",
        effort="S",
    ),
    "cost_tracking": PathDefinition(
        name="Real Token Counting + Cost Tracking",
        description="Count actual tokens per agent call (via response metadata). Calculate real costs. Use cost data to optimize provider allocation (prefer cheaper models when quality is equal).",
        best_case="20-40% cost reduction by routing to cheapest-adequate model per task type.",
        worst_case="Minimal savings since most providers are free tier.",
        effort="S",
    ),
    "decision_graph": PathDefinition(
        name="DAG-based Decision Graph (mini-LangGraph)",
        description="Replace linear pipeline with directed graph: nodes = stages (dispatch, debate, synthesize, etc.), edges = conditional transitions. Enables skip-debate for high-consensus, parallel-committee for complex decisions.",
        best_case="More flexible orchestration. Can handle 3x more complex decision types.",
        worst_case="Heavy abstraction for simple decisions. Adds 500+ lines of code.",
        effort="L",
    ),
    "smart_early_exit": PathDefinition(
        name="Smart Early Exit — Stop When Consensus Reached",
        description="After each agent returns, check if consensus already reached (e.g., 5/7 agree). Cancel remaining slow agents immediately. Return partial results.",
        best_case="40-60% faster for easy decisions where consensus forms early.",
        worst_case="No improvement for contentious decisions where all agents needed.",
        effort="S",
    ),
}


async def main():
    engine = SwarmEngine()
    print(f"\n{'='*60}")
    print(f"MiroFish Self-Analysis — {len(engine.providers)} providers loaded")
    print(f"{'='*60}\n")

    config = SwarmConfig(
        question=SELF_ANALYSIS_QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.ARCHITECTURE,
        temperature=0.7,
        timeout_seconds=45.0,
        max_agents=12,
    )

    report = await engine.decide(config)

    print(f"\n{'='*60}")
    print(f"SELF-ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Agents used: {report.agents_succeeded}/{report.agents_used}")
    print(f"Latency: {report.total_latency_ms}ms")
    print(f"Winner: {report.winner} (score: {report.winner_score}/50)")
    print(f"Confidence gate: {'PASSED' if report.passed_confidence_gate else 'FAILED'}")
    print(f"Consensus: {report.divergence.consensus_strength:.0%}")

    print(f"\nWeighted Scores:")
    for path_id, score in sorted(report.weighted_scores.items(), key=lambda x: -x[1]):
        print(f"  {path_id}: {score}/50")

    print(f"\nVote Distribution:")
    for path_id, votes in sorted(report.divergence.winner_votes.items(), key=lambda x: -x[1]):
        print(f"  {path_id}: {votes} votes")

    if report.divergence.high_divergence:
        print(f"\n⚠️  HIGH DIVERGENCE — agents disagree significantly")

    if report.synthesis:
        print(f"\nSynthesis:")
        synth = report.synthesis
        for key in ["winner", "reasoning", "recommendation", "accepted_risks"]:
            if key in synth:
                val = synth[key]
                if isinstance(val, str) and len(val) > 300:
                    val = val[:300] + "..."
                print(f"  {key}: {val}")

    # Middleware stats
    budget = report.synthesis or {}
    if "token_budget_used" in budget:
        print(f"\nMiddleware Stats:")
        print(f"  Token budget: {budget.get('token_budget_used', 0)}/{budget.get('token_budget_max', 0)}")
        print(f"  Dedup removed: {budget.get('dedup_removed', 0)}")
        print(f"  Loop warnings: {budget.get('loop_warnings', 0)}")

    # Save full report
    output_path = Path(__file__).parent / "self_analysis_report.json"
    output_path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    print(f"\nFull report saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
