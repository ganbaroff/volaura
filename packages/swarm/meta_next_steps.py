"""
Meta-evaluation: swarm proposes its own next steps.
Full context: what we built, what research says, what's missing.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.swarm.engine import SwarmEngine
from packages.swarm.types import PathDefinition, StakesLevel, DomainTag, SwarmConfig

FULL_CONTEXT = """
## WHO WE ARE
- Yusif: founder of Volaura (verified volunteer platform for Azerbaijan)
- Claude Opus: CTO/orchestrator
- MiroFish Swarm Engine: universal multi-model decision engine we just built
- Budget: $50/month total for everything

## WHAT WE BUILT (packages/swarm/ - 2366 lines Python)
A working multi-model decision engine with:
- 3 providers: Gemini 2.0 Flash (FREE, 3.4s), Groq Llama 70B (FREE, 1.2s), DeepSeek V3 (PAID $0.14/MTok, 15s)
- OpenRouter REMOVED (failed 100% of tests - 404/429/401 errors)
- OpenAI REMOVED from default (quota exceeded - needs billing setup)
- Parallel async dispatch via asyncio.gather()
- Weighted majority voting (calibrated by past accuracy)
- Conditional debate: IF divergence > 50%, minority agents see majority arguments, must cite specific errors
- LLM synthesis (MoA-style): Gemini synthesizes group results for MEDIUM+ stakes
- Self-scaling: high divergence -> +3 agents, suspicious consensus -> +1 devil's advocate
- Persistent memory: JSON files for model profiles, decision history, calibration log
- Self-learning: after outcome observed, correct models get +5% weight, wrong get -5%
- Retry logic: transient errors (429, 503) retry 2x with backoff, non-transient fail fast

## BENCHMARK RESULTS (4 runs on same question)
Run 1: 3/7 success (43%) - Gemini model wrong + OpenRouter dead
Run 2: 5/7 success (71%) - OpenRouter still dead, debate + synthesis added
Run 3: 5/7 success - DEBATE WORKED: 3 agents changed votes after targeted correction!
Run 4: 6/6 success (100%) - Clean 3-provider engine. Gate PASSED. 0 errors.

Key finding: Groq + DeepSeek consistently choose "hybrid", Gemini chooses "supabase".
Real bias diversity across model families confirmed.

## RESEARCH WE APPLIED (best practices baked in)
1. MoA (arXiv 2406.04692): synthesis > selection by ~12% -> APPLIED: LLM synthesis in pm.py
2. ACL 2025 (Kaesberg): weighted voting > k-ahead for small groups -> APPLIED: weighted majority
3. ACL 2025: answer diversity > protocol choice -> APPLIED: varied perspectives + temperatures
4. ICML 2024 (Du et al): debate works for heterogeneous agents -> APPLIED: conditional debate
5. NeurIPS 2025: debate is martingale UNLESS targeted correction -> APPLIED: agents must cite specific errors
6. RouteLLM (LMSYS): smart routing saves 85% cost -> PARTIALLY: stakes-based routing, no trained classifier
7. RouterBench: 5 axes of evaluation -> NOT YET: only track accuracy + latency, missing cost/robustness/optimality

## WHAT WE DISCUSSED BUT HAVEN'T BUILT
1. TOURNAMENT GROUP ARCHITECTURE:
   - PM splits question into topic groups (security, cost, UX, speed, etc.)
   - Each group has 3 agents (one per provider) with diverse sub-perspectives
   - Inner-group: weighted vote -> group winner
   - Cross-group: LLM synthesis combines group winners
   - Debate only within divergent groups (save tokens)
   - Sub-perspectives defined in prompts.py but not wired into pm.py

2. EVOLUTIONARY SELECTION (10-20 sprint tracking):
   - Track which provider wins in which domain over time
   - Build model-domain competency matrix
   - After enough data: drop worst provider, upgrade best to paid
   - Memory system exists but no calibration data yet (0 calibrations run)

3. COLD START PROBLEM:
   - Model profiles empty until calibrations happen
   - No baseline weights - all start at 1.0
   - Need initial benchmarks to seed profiles

4. VOLAURA INTEGRATION:
   - Engine is standalone in packages/swarm/
   - Not wired into Volaura's apps/api/ or decision-making flow
   - DSP v4.0 SKILL.md references Agent(haiku) not SwarmEngine
   - Session 14 planning should use SwarmEngine

5. RouterBench-STYLE 5-AXIS EVALUATION:
   - Currently only: accuracy (did winner match outcome?) + latency
   - Missing: cost tracking per agent, robustness (retry success rate), optimality (cheapest correct)

## CONSTRAINTS
- Budget $50/month (hosting $8 + LLM ~$6 = $14, $36 buffer)
- Gemini 15 RPM limit = max ~5 concurrent agents
- Groq 30 RPM = max ~10 concurrent agents
- DeepSeek is 10x slower than Groq (15s vs 1.2s)
- Must be universal (not Volaura-specific)
- Must be production-quality Python, async, Pydantic v2
"""

CONFIG = SwarmConfig(
    question=(
        "What should be the next 3-5 steps for the MiroFish Swarm Engine? "
        "Consider: what gives the highest ROI (quality improvement per effort)? "
        "What's blocking us from production use? What research finding haven't "
        "we applied yet that we should? Should we build tournament groups now "
        "or optimize the flat engine more first? "
        "Be specific - name files, functions, line changes."
    ),
    context=FULL_CONTEXT,
    constraints=(
        "Budget: $50/month. Must stay free-tier primary. "
        "Time: propose steps that can each be done in 1 session (~2 hours). "
        "Each step must be independently valuable (not blocked by later steps). "
        "Prioritize: reliability > quality > features > performance."
    ),
    paths={
        "path_a": PathDefinition(
            name="Tournament groups architecture",
            description=(
                "Build the topic-group system: PM splits question into 3-4 groups, "
                "each group has 1 agent per provider with sub-perspectives, "
                "inner-group weighted vote, cross-group LLM synthesis. "
                "This is the discussed architecture but needs significant pm.py rewrite."
            ),
            best_case="Deep specialized analysis. Higher quality decisions. Tournament brackets.",
            worst_case="3 agents per group = thin coverage. Complex code. Slower (sequential groups).",
            effort="L",
        ),
        "path_b": PathDefinition(
            name="Calibration + cold start + Volaura integration",
            description=(
                "Run 5-10 real decisions, calibrate each, seed model profiles. "
                "Wire SwarmEngine into Volaura's session planning (replace pseudo-DSP). "
                "Add 5-axis evaluation. Solve cold start with initial benchmark suite."
            ),
            best_case="Engine learns from real data. Volaura decisions improve. Profiles populated.",
            worst_case="Calibration takes many sprints to be meaningful. Early data noisy.",
            effort="M",
        ),
        "path_c": PathDefinition(
            name="Reliability hardening + provider optimization",
            description=(
                "Add timeout per provider (kill DeepSeek if >20s). "
                "Add cost tracking per agent call. "
                "Add provider health checks (ping before dispatch). "
                "Implement RouteLLM-style trained routing. "
                "Add structured output schemas (not just json_object mode)."
            ),
            best_case="100% reliability. Cost visibility. Faster (no DeepSeek timeout waste).",
            worst_case="Engineering work with no visible quality improvement.",
            effort="M",
        ),
        "path_d": PathDefinition(
            name="Hybrid: flat for now + prepare tournament interface",
            description=(
                "Keep flat engine for daily use (it works). "
                "Define GroupConfig, GroupResult types in types.py. "
                "Add group_perspectives to prompts.py (already partially done). "
                "Wire tournament mode as optional flag in SwarmConfig. "
                "Don't rewrite pm.py yet - just prepare the interface."
            ),
            best_case="Ship today's working engine while laying groundwork for tournament.",
            worst_case="Interface designed without implementation may not match reality.",
            effort="S",
        ),
    },
    stakes=StakesLevel.HIGH,
    domain=DomainTag.ARCHITECTURE,
)


async def run():
    print("=" * 70)
    print("SWARM: What should we do next?")
    print("=" * 70)

    engine = SwarmEngine()
    print(f"Providers: {', '.join(engine.get_available_providers())}")
    print(f"Stakes: HIGH | Domain: ARCHITECTURE")
    print("-" * 70)

    report = await engine.decide(CONFIG)

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"Agents: {report.agents_succeeded}/{report.agents_used} | Latency: {report.total_latency_ms}ms")

    print(f"\nScores:")
    for pid, score in sorted(report.weighted_scores.items(), key=lambda x: -x[1]):
        name = CONFIG.paths[pid].name if pid in CONFIG.paths else pid
        marker = " << WINNER" if pid == report.winner else ""
        print(f"  {pid:8s} - {name:50s}: {score}/50{marker}")

    print(f"\nVotes: {report.divergence.winner_votes}")
    print(f"Consensus: {report.divergence.consensus_strength:.0%}")

    if report.scaling_events:
        print(f"\nScaling:")
        for ev in report.scaling_events:
            print(f"  Round {ev.round}: {ev.reason}")

    print(f"\nPer agent:")
    for r in report.agent_results:
        if not r.json_valid:
            print(f"  [x] {r.agent_id:20s} | ERR: {r.error[:60] if r.error else '?'}")
            continue
        print(f"  [+] {r.agent_id:20s} | {r.perspective:15s} | {r.winner:8s} | {r.latency_ms}ms")
        if r.reason:
            print(f"      {r.reason[:150]}")
        # Print top concern for winner path
        if r.concerns:
            winner_concern = r.concerns.get(r.winner, "")
            if winner_concern:
                print(f"      Concern: {winner_concern[:150]}")

    if report.synthesis:
        print(f"\n{'=' * 70}")
        print("SYNTHESIS")
        print(f"{'=' * 70}")
        s = report.synthesis
        print(f"Winner: {s.get('winner', '?')}")
        print(f"\n{s.get('synthesis', '?')}")
        if s.get('consensus_points'):
            print(f"\nConsensus:")
            for p in s['consensus_points']:
                print(f"  - {p}")
        if s.get('risk_points'):
            print(f"\nRisks:")
            for p in s['risk_points']:
                print(f"  - {p}")
        if s.get('surprise_insight'):
            print(f"\nSurprise: {s['surprise_insight']}")
        if s.get('conditions'):
            print(f"\nSwitch if: {s['conditions']}")

    print(f"\nGate: {'PASSED' if report.passed_confidence_gate else 'FAILED'}")
    print(f"ID: {report.decision_id}")


if __name__ == "__main__":
    asyncio.run(run())
