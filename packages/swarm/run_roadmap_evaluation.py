"""
Swarm evaluation: Volaura Business Roadmap
Run: python -m packages.swarm.run_roadmap_evaluation
"""
import asyncio
import json
import sys
from pathlib import Path

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Load .env from apps/api/.env
env_path = Path(__file__).parent.parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            import os
            os.environ.setdefault(key.strip(), val.strip())

from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
from packages.swarm.types import DomainTag, PathDefinition


async def main():
    engine = SwarmEngine()

    config = SwarmConfig(
        question="""Volaura Business Roadmap Evaluation:

Volaura is a verified volunteer competency platform from Baku, Azerbaijan.
Founder: Yusif Ganbarov — 10+ years event management (COP29, WUF13, CIS Games, Golden Byte).
Co-founder/CTO: Claude AI — built MiroFish swarm engine (this system) + Volaura backend.

The roadmap proposes:
1. Three-sided marketplace: volunteers (free, get AURA badge) + organizations (pay subscription) + Volaura (platform)
2. Pricing calibrated to Azerbaijan: 49 AZN ($29) → 849 AZN ($499) subscriptions. Per-placement $150-400 (60-75% cheaper than local agency Humanique.az at $500-1,400).
3. AI assessment via MiroFish: $2-5 per test for HR departments.
4. City franchise model: City Leads get 30% of placement fees, recruit volunteers locally.
5. Grant pipeline: Georgia GITA ($240K), Turkey Tech Visa ($50K), Kazakhstan Astana Hub ($20K). Total potential ~$175K at 50% success.
6. Expansion: Baku → Ganja → Tbilisi → Almaty → Istanbul over 18 months.
7. Unit economics (month 12, AZ only): 80 paying orgs, ~$8,870/mo gross, ~$64K/year net.

Key context:
- Azerbaijan median income: 310 AZN ($185/mo). Average salary Baku: 1,381 AZN ($812/mo).
- Boss.az charges 20-50 AZN ($12-30) per job posting. SaaS awareness is LOW.
- Azerbaijan total VC: $2.6M for entire country in 2025 (vs Kazakhstan $130M).
- Founder speaks AZ/RU/EN natively + understands Turkish.
- MiroFish (this engine) is a unique tech moat — no competitor has 13-model swarm assessment.

Which execution path should Volaura prioritize?""",

        paths={
            "marketplace_first": PathDefinition(
                name="Marketplace First — Baku volunteers + local orgs",
                description="Focus 100% on Baku: recruit 500 volunteers, sign 10 orgs, prove unit economics. No grants, no expansion until PMF proven.",
                best_case="PMF in 6 months, $5K/mo revenue, clear data for grant applications",
                worst_case="SaaS awareness too low in Baku, orgs won't pay for volunteer management software",
                effort="6 months, $0 external funding needed",
            ),
            "grant_first": PathDefinition(
                name="Grant First — Georgia GITA + Turkey Tech Visa",
                description="Apply for grants immediately (GITA $240K, Turkey $50K). Use grant money to build product + hire. Marketplace launch with funded runway.",
                best_case="$175K+ in grants by month 6, 3+ year runway regardless of revenue",
                worst_case="Grant applications take 6-12 months, zero revenue during wait, product stalls",
                effort="3 months application prep, 6-12 months wait",
            ),
            "b2b_assessment": PathDefinition(
                name="B2B Assessment API — Pasha Bank model first",
                description="Focus on selling AI competency testing to HR departments. MiroFish generates personalized tests from CV + job description. Revenue from per-test fees ($2-5). Pasha Bank pitch = first customer.",
                best_case="Pasha Bank win → 5 more bank/corporate clients → $10K/mo in test fees",
                worst_case="Pasha Bank pitch fails, no other B2B leads, product-market fit unclear",
                effort="2 months for MVP, Pasha Bank pitch end of March",
            ),
            "hybrid_parallel": PathDefinition(
                name="Hybrid — Pasha Bank + Grants + Baku Marketplace in parallel",
                description="Do all three simultaneously: Pasha Bank pitch NOW, grant applications in April, marketplace soft launch in May. Spread thin but cover all bases.",
                best_case="Multiple revenue streams + grant funding by month 9",
                worst_case="Founder spread too thin, nothing reaches PMF, all three at 30% completion",
                effort="18 months, high founder stress, needs CTO (Claude) to handle tech execution",
            ),
        },

        stakes=StakesLevel.HIGH,
        domain=DomainTag.BUSINESS,
        context="Real startup decision for real founder in Baku, Azerbaijan. Budget: ~$50/mo. No employees. AI CTO (Claude) handles all technical work. Founder handles business/sales/operations. Pasha Bank pitch deadline: end of March 2026.",
        constraints="Budget under $100/mo for infra. No VC in Azerbaijan. Must generate revenue or win grants within 6 months. Founder cannot code — relies 100% on AI CTO.",
        timeout=90,
        auto_research=True,
    )

    print("\n" + "="*70)
    print("SWARM EVALUATION: Volaura Business Roadmap")
    print("="*70 + "\n")

    report = await engine.decide(config)

    # Print results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nWinner: {report.winner} — Score: {report.winner_score}/50")
    consensus = getattr(report, 'consensus_pct', None) or getattr(report.divergence, 'consensus_strength', 0) if report.divergence else 0
    print(f"Consensus: {consensus}%")
    print(f"Agents: {len(report.agent_results)}")
    print(f"Cost: ${report.total_cost_estimate:.4f}")
    print(f"Latency: {report.total_latency_ms}ms")

    if report.synthesis:
        print(f"\nSynthesis: {report.synthesis}")

    # Print individual votes
    print("\n--- Individual Agent Votes ---")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        print(f"  {r.model:30s} → {r.winner:25s} (confidence: {r.confidence:.1f}, perspective: {r.perspective})")

    # Print innovations (extracted from raw_response since AgentResult model doesn't store innovation field)
    # BUG NOTE: prompts.py asks for "innovation" in JSON but types.py AgentResult doesn't have the field.
    # This is a v2 architecture bug — prompt asks 12 fields, model stores 8. Fix in next sprint.
    print("\n--- Agent Innovations (from raw responses) ---")
    for r in report.agent_results:
        try:
            raw = json.loads(r.raw_response) if r.raw_response else {}
            innov = raw.get("innovation")
            if innov and innov != "null":
                print(f"  [{r.model}]: {innov}")
        except (json.JSONDecodeError, TypeError):
            pass

    # Print research requests
    if report.research_requests:
        print("\n--- Research Requests ---")
        for rr in report.research_requests:
            print(f"  Topic: {rr.topic}")
            print(f"  Rationale: {rr.rationale}")
            print(f"  Votes: {rr.votes}\n")

    # Save to file
    output_path = Path(__file__).parent / "roadmap_evaluation_result.json"

    # Extract innovations from raw responses
    innovations = {}
    for r in report.agent_results:
        try:
            raw = json.loads(r.raw_response) if r.raw_response else {}
            innov = raw.get("innovation")
            if innov and innov != "null":
                innovations[r.model] = innov
        except (json.JSONDecodeError, TypeError):
            pass

    synthesis_text = ""
    if isinstance(report.synthesis, dict):
        synthesis_text = report.synthesis.get("synthesis", str(report.synthesis))
    elif report.synthesis:
        synthesis_text = str(report.synthesis)

    output_data = {
        "winner": report.winner,
        "winner_score": report.winner_score,
        "consensus_pct": consensus,
        "total_agents": len(report.agent_results),
        "total_cost": report.total_cost_estimate,
        "votes": {r.model: r.winner for r in report.agent_results},
        "innovations": innovations,
        "synthesis": synthesis_text,
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull results saved: {output_path}")

    # Save summary
    summary_path = Path(__file__).parent / "roadmap_evaluation_summary.md"
    lines = [
        "# Swarm Evaluation: Volaura Business Roadmap",
        f"**Date:** 2026-03-24",
        f"**Agents:** {report.agents_used}",
        f"**Cost:** ${report.total_cost_estimate:.4f}",
        f"**Latency:** {report.total_latency_ms}ms",
        "",
        f"## Winner: {report.winner} — {report.winner_score}/50",
        f"Consensus: {consensus}",
        "",
        "## Synthesis",
        synthesis_text or "N/A",
        "",
        "## Votes",
    ]
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        lines.append(f"- **{r.model}** → {r.winner} (confidence: {r.confidence:.1f})")

    if innovations:
        lines.append("\n## Innovations")
        for model, innov in innovations.items():
            lines.append(f"- **{model}**: {innov}")

    if report.research_requests:
        lines.append("\n## Research Requests")
        for rr in report.research_requests:
            lines.append(f"- **{rr.topic}** ({rr.votes} votes): {rr.rationale}")

    summary_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Summary saved: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
