"""
Meta-evaluation: the swarm engine evaluates and proposes improvements to ITSELF.
Runs all available providers on the question of how to improve the engine.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.swarm.engine import SwarmEngine
from packages.swarm.types import PathDefinition, StakesLevel, DomainTag, SwarmConfig

# The engine's own architecture, compressed for prompt
SELF_DESCRIPTION = """
## MiroFish Swarm Engine - Current Architecture (2366 lines Python)

### What it does
Universal multi-model AI decision engine. Takes ANY question, routes to parallel
LLM agents from multiple providers, aggregates with weighted voting, detects
divergence, runs conditional debates, and produces a final LLM synthesis.

### Providers (3 free, 2 paid fallback)
1. Gemini 2.0 Flash - FREE, 15 RPM, 3.4s avg, good JSON, best for synthesis
2. Groq Llama 3.3 70B - FREE, 30 RPM, 1.2s avg, FASTEST, good reasoning
3. OpenRouter - FREE models available but UNSTABLE (404 errors on every test)
4. DeepSeek V3 - PAID $0.14/MTok, 13s avg, SLOW but highest confidence scores
5. OpenAI gpt-4o-mini - PAID $0.15/MTok, not reached yet (round-robin stops before it)

### Current Flow
1. ProviderRegistry auto-discovers available providers from env vars
2. PMAgent allocates agents based on stakes (LOW:5, MEDIUM:7, HIGH:10, CRITICAL:15)
3. Round-robin distribution across providers with temperature variation (0.5, 0.7, 0.9)
4. All agents dispatched in parallel via asyncio.gather()
5. Weighted majority voting for aggregation (calibrated by past accuracy)
6. IF divergence > 50%: debate round (minority agents see majority arguments, must cite specific errors)
7. IF stakes >= MEDIUM: LLM synthesis via best provider (Gemini) - MoA-style
8. Self-scaling: high divergence -> +3 agents, suspicious consensus -> +1 devil's advocate
9. Memory: JSON files store model profiles, decision history, calibration log
10. Calibration: after outcome observed, models that predicted correctly get weight += 5%

### Benchmark Results (3 runs)
- Run 1: 3/7 agents succeeded (Gemini model name wrong + OpenRouter 429)
- Run 2: 5/7 succeeded. Winner: supabase 33.4/50. Consensus 60%.
- Run 3: 5/7 succeeded. DEBATE TRIGGERED. 3 agents changed votes after seeing
  opponents' arguments. Consensus went from 40% to 100%. Winner changed from
  supabase to hybrid. This is the key validation - targeted correction works.

### Research-backed decisions baked in
- ACL 2025: weighted majority > k-ahead voting for small groups
- MoA (arXiv 2406.04692): LLM synthesis > selection by ~12%
- ICML 2024: debate works for heterogeneous agents with targeted correction
- NeurIPS 2025: debate alone is martingale, but correction bias fixes it
- ACL 2025: answer diversity > protocol choice

### Known Problems
1. OpenRouter never works (3/3 runs failed - free models return 404 or 429)
2. OpenAI never fires (round-robin stops before reaching paid providers)
3. DeepSeek is 10x slower than Groq (13s vs 1.2s) - bottleneck for total latency
4. No group/tournament architecture yet (all agents in flat pool, no topic clustering)
5. Confidence gate (>=35/50) never passes - scores consistently 29-33/50
6. No retry logic for failed providers
7. Memory profiles are empty until calibration runs (cold start problem)

### Architecture we WANT but haven't built yet
Tournament architecture with groups:
- PM splits question into topics (security, cost, UX, speed, etc.)
- Each topic = a GROUP with 3 agents (one per free provider)
- Within group: diverse sub-perspectives (e.g., security group has attacker + victim + auditor)
- Inner-group: weighted majority vote -> group winner
- Cross-group: LLM synthesis combines group winners (MoA-style)
- IF inner-group divergence > 50%: targeted debate within that group only
- Over 10-20 sprints: track which provider wins in which domain -> evolutionary selection
- Drop worst provider, keep/upgrade best

### Files
types.py (166 lines) - 15 Pydantic v2 models
providers/base.py (104) - abstract LLMProvider + safe_evaluate wrapper
providers/gemini.py (45) - google-genai async
providers/groq_provider.py (42) - groq AsyncGroq
providers/deepseek.py (43) - openai SDK with deepseek base_url
providers/openrouter.py (50) - openai SDK with openrouter base_url
providers/openai_provider.py (42) - openai SDK native
providers/__init__.py (148) - ProviderRegistry + agent allocation
prompts.py (269) - evaluator + debate + synthesis prompt builders
pm.py (594) - PMAgent: dispatch, aggregate, debate, synthesize, scale
engine.py (120) - SwarmEngine public API
memory.py (205) - JSON file persistence + calibration loop
"""

META_CONFIG = SwarmConfig(
    question=(
        "You are evaluating the MiroFish Swarm Engine's own code. "
        "How should this engine be rewritten to implement the tournament "
        "group architecture, fix the known problems, and maximize decision quality? "
        "Also: should we keep OpenRouter (always fails) or drop it and use only "
        "Gemini + Groq + DeepSeek? Propose the specific architecture changes."
    ),
    context=SELF_DESCRIPTION,
    constraints=(
        "Budget: $50/month total. Must stay free-tier for primary providers. "
        "Python 3.11+, Pydantic v2, async everywhere. "
        "Must be UNIVERSAL - not tied to any specific project. "
        "Code must be production-quality, not prototype. "
        "Debate round must only trigger when divergence > 50% (save tokens). "
        "Self-learning calibration must work from first run (solve cold start)."
    ),
    paths={
        "path_a": PathDefinition(
            name="Incremental: fix bugs, keep flat architecture",
            description=(
                "Fix OpenRouter (try different free models or drop it). "
                "Add retry logic. Fix confidence gate threshold. "
                "Add OpenAI to round-robin. Keep flat agent pool. "
                "Minimal code changes, maximum stability."
            ),
            best_case="All 5 providers work, scores reach 35+/50, stable.",
            worst_case="Flat pool still has no topic specialization. Quality ceiling.",
            effort="S",
        ),
        "path_b": PathDefinition(
            name="Tournament: full group architecture rewrite",
            description=(
                "Implement topic groups (security, cost, UX, speed). "
                "3 agents per group (one per provider). "
                "Inner-group voting + cross-group LLM synthesis. "
                "Debate within groups only. Tournament brackets."
            ),
            best_case="Deep specialized analysis per topic. Higher quality decisions.",
            worst_case="3 agents per group with 3 providers = only 1 agent per provider per group. Low diversity within group.",
            effort="L",
        ),
        "path_c": PathDefinition(
            name="Hybrid: groups for HIGH stakes, flat for LOW/MEDIUM",
            description=(
                "LOW/MEDIUM stakes: keep current flat pool (fast, cheap). "
                "HIGH/CRITICAL stakes: switch to tournament groups. "
                "Auto-detect which mode based on stakes level. "
                "Reuse existing code, add group layer on top."
            ),
            best_case="Best of both: fast for simple, deep for complex. Code reuse.",
            worst_case="Two code paths to maintain. Complexity.",
            effort="M",
        ),
        "path_d": PathDefinition(
            name="Drop OpenRouter, optimize 3-provider engine",
            description=(
                "Remove OpenRouter entirely (never worked). "
                "Optimize for Gemini + Groq + DeepSeek only. "
                "Gemini = quality + synthesis, Groq = speed + volume, "
                "DeepSeek = deep reasoning (use sparingly, paid). "
                "Simpler code, fewer failure modes."
            ),
            best_case="100% success rate (no 404s). Simpler. Cheaper.",
            worst_case="Less model diversity (3 vs 5). Bias overlap possible.",
            effort="S",
        ),
    },
    stakes=StakesLevel.HIGH,
    domain=DomainTag.ARCHITECTURE,
)


async def run_meta_eval():
    print("=" * 70)
    print("META-EVALUATION: Swarm Engine evaluates ITSELF")
    print("=" * 70)

    engine = SwarmEngine()
    providers = engine.get_available_providers()
    print(f"Providers: {', '.join(providers)}")
    print(f"Question: How should MiroFish be rewritten?")
    print(f"Stakes: HIGH (10+ agents)")
    print("-" * 70)

    report = await engine.decide(META_CONFIG)

    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"Agents: {report.agents_succeeded}/{report.agents_used}")
    print(f"Latency: {report.total_latency_ms}ms")

    print(f"\nProvider latencies:")
    for p, ms in sorted(report.provider_latencies.items(), key=lambda x: x[1]):
        print(f"  {p:12s}: {ms:.0f}ms")

    print(f"\nScores (/50):")
    for pid, score in sorted(report.weighted_scores.items(), key=lambda x: -x[1]):
        name = META_CONFIG.paths[pid].name if pid in META_CONFIG.paths else pid
        marker = " << WINNER" if pid == report.winner else ""
        print(f"  {pid:8s} - {name:50s}: {score}/50{marker}")

    print(f"\nDivergence:")
    print(f"  Votes: {report.divergence.winner_votes}")
    print(f"  Consensus: {report.divergence.consensus_strength:.0%}")

    if report.scaling_events:
        print(f"\nScaling:")
        for ev in report.scaling_events:
            print(f"  Round {ev.round}: +{ev.agents_added} ({ev.provider_used}) - {ev.reason}")

    print(f"\nAgents:")
    for r in report.agent_results:
        ok = "+" if r.json_valid else "x"
        err = f" ERR:{r.error[:50]}" if r.error else ""
        print(f"  [{ok}] {r.agent_id:20s} | {r.perspective:15s} | {r.winner:8s} | conf={r.confidence:.2f} | {r.latency_ms}ms{err}")
        if r.reason and r.json_valid:
            print(f"      Reason: {r.reason[:120]}")

    if report.synthesis:
        print(f"\n{'=' * 70}")
        print("LLM SYNTHESIS (MoA-style)")
        print(f"{'=' * 70}")
        synth = report.synthesis
        print(f"Winner: {synth.get('winner', '?')}")
        print(f"Synthesis: {synth.get('synthesis', '?')}")
        if synth.get('consensus_points'):
            print(f"Consensus: {synth.get('consensus_points')}")
        if synth.get('risk_points'):
            print(f"Risks: {synth.get('risk_points')}")
        if synth.get('surprise_insight'):
            print(f"Surprise: {synth.get('surprise_insight')}")
        if synth.get('conditions'):
            print(f"Switch condition: {synth.get('conditions')}")

    print(f"\nDecision ID: {report.decision_id}")
    print(f"Confidence gate: {'PASSED' if report.passed_confidence_gate else 'FAILED (<35/50)'}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(run_meta_eval())
