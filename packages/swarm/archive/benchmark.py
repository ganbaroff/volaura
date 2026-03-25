"""
Benchmark Test - runs the same question through ALL available providers.
Compares: quality, speed, cost, JSON compliance, agreement patterns.
Establishes baseline ModelProfile for each provider.

Usage:
    cd "path/to/VOLAURA"
    python -m packages.swarm.benchmark
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from packages.swarm.engine import SwarmEngine
from packages.swarm.types import PathDefinition, StakesLevel, DomainTag, SwarmConfig


BENCHMARK_CONFIG = SwarmConfig(
    question="Should a startup with $50/month budget use a managed database (Supabase) or self-hosted PostgreSQL on a $5 VPS?",
    context=(
        "Early-stage SaaS, 2 developers, expected 1000 users in 6 months. "
        "Needs auth, file storage, realtime subscriptions, row-level security. "
        "Team has FastAPI backend + Next.js frontend. Both devs know SQL but not DBA."
    ),
    constraints=(
        "Budget: $50/month total including hosting. "
        "Timeline: MVP in 6 weeks. No dedicated DevOps. "
        "Must support row-level security for multi-tenant data."
    ),
    paths={
        "supabase": PathDefinition(
            name="Supabase Free Tier",
            description="Use Supabase managed PostgreSQL with built-in auth, storage, realtime, and RLS. Free tier: 500MB DB, 1GB storage, 50K monthly active users.",
            best_case="Zero DB ops overhead, built-in auth + storage, RLS out of box. Ship MVP in 3 weeks.",
            worst_case="Hit free tier limits at 500MB. Migration to self-hosted is painful. Vendor lock-in on auth.",
            effort="S",
        ),
        "self_hosted": PathDefinition(
            name="Self-hosted Postgres on $5 VPS",
            description="Run PostgreSQL on a Hetzner/DigitalOcean $5 VPS. Manual setup: backups, SSL, monitoring. Use pgBouncer for connection pooling.",
            best_case="Full control, no vendor lock-in, unlimited storage for $5/mo. Scale vertically later.",
            worst_case="2 weeks spent on DevOps instead of product. No auto-backups. Security misconfiguration. 3am database is down.",
            effort="L",
        ),
        "hybrid": PathDefinition(
            name="Supabase now, migrate later",
            description="Start with Supabase free tier for speed. Plan migration to self-hosted when hitting limits (6-12 months). Abstract DB layer to minimize migration cost.",
            best_case="Best of both: ship fast now, full control later. Migration is smooth because abstraction layer worked.",
            worst_case="Abstraction layer adds complexity now. Migration never happens (inertia). Supabase-specific features (realtime, auth) are hard to replace.",
            effort="M",
        ),
    },
    stakes=StakesLevel.MEDIUM,
    domain=DomainTag.ARCHITECTURE,
)


async def run_benchmark():
    print("=" * 70)
    print("SWARM ENGINE BENCHMARK - Multi-Model Decision Test")
    print("=" * 70)

    engine = SwarmEngine()
    providers = engine.get_available_providers()
    print(f"\nAvailable providers: {', '.join(providers)}")
    print(f"Provider details:")
    for stat in engine.get_provider_stats():
        free_tag = "FREE" if stat["is_free"] else f"${stat['cost_per_mtok']}/MTok"
        print(f"  {stat['name']:12s} | {stat['model']:35s} | {free_tag:10s} | {stat['rate_limit_rpm']} RPM")

    print(f"\nQuestion: {BENCHMARK_CONFIG.question}")
    print(f"Stakes: {BENCHMARK_CONFIG.stakes.value}")
    print(f"Domain: {BENCHMARK_CONFIG.domain.value}")
    print(f"Paths: {', '.join(BENCHMARK_CONFIG.paths.keys())}")
    print("\nLaunching swarm...")
    print("-" * 70)

    report = await engine.decide(BENCHMARK_CONFIG)

    # Results
    print(f"\n{'=' * 70}")
    print("RESULTS")
    print(f"{'=' * 70}")
    print(f"Agents used:     {report.agents_used}")
    print(f"Agents succeeded: {report.agents_succeeded}")
    print(f"Total latency:   {report.total_latency_ms}ms")

    # Per-provider latencies
    print(f"\nProvider latencies:")
    for provider, avg_ms in sorted(report.provider_latencies.items(), key=lambda x: x[1]):
        print(f"  {provider:12s}: {avg_ms:.0f}ms avg")

    # Scores
    print(f"\nWeighted scores (/50):")
    for path_id, score in sorted(report.weighted_scores.items(), key=lambda x: -x[1]):
        paths = BENCHMARK_CONFIG.paths or {}
        name = paths[path_id].name if path_id in paths else path_id
        marker = " << WINNER" if path_id == report.winner else ""
        print(f"  {path_id:15s} - {name:30s}: {score}/50{marker}")

    # Divergence
    print(f"\nDivergence:")
    print(f"  Winner votes: {report.divergence.winner_votes}")
    print(f"  Consensus:    {report.divergence.consensus_strength:.0%}")
    print(f"  Genuine:      {report.divergence.is_genuine_consensus}")

    # Scaling events
    if report.scaling_events:
        print(f"\nScaling events:")
        for ev in report.scaling_events:
            print(f"  Round {ev.round}: +{ev.agents_added} agents ({ev.provider_used}) - {ev.reason}")

    # Per-agent details
    print(f"\nPer-agent breakdown:")
    print(f"  {'Agent ID':20s} | {'Provider':12s} | {'Model':30s} | {'Perspective':15s} | {'Winner':12s} | {'Conf':5s} | {'ms':6s} | {'OK':3s}")
    print(f"  {'-'*20} | {'-'*12} | {'-'*30} | {'-'*15} | {'-'*12} | {'-'*5} | {'-'*6} | {'-'*3}")
    for r in report.agent_results:
        ok = "✓" if r.json_valid else "✗"
        error_tag = f" ERR: {r.error[:40]}" if r.error else ""
        print(
            f"  {r.agent_id:20s} | {r.provider:12s} | {r.model:30s} | "
            f"{r.perspective:15s} | {r.winner:12s} | {r.confidence:.2f} | "
            f"{r.latency_ms:5d}ms | {ok}{error_tag}"
        )

    # Confidence gate
    gate = "PASSED" if report.passed_confidence_gate else "FAILED (< 35/50)"
    print(f"\nConfidence gate: {gate}")
    print(f"Winner: {report.winner} - {report.winner_score}/50")
    print(f"Decision ID: {report.decision_id}")

    print(f"\n{'=' * 70}")
    print("Benchmark complete. Model profiles saved to ~/.swarm/model_profiles.json")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
