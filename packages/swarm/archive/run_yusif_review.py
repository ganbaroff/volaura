"""
Swarm evaluation: Yusif Ganbarov as AI Orchestrator / Founder
Run: python -m packages.swarm.run_yusif_review
"""
import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Load .env
env_path = Path(__file__).parent.parent.parent / "apps" / "api" / ".env"
if env_path.exists():
    import os
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

from packages.swarm import SwarmEngine, SwarmConfig, StakesLevel
from packages.swarm.types import DomainTag, PathDefinition


async def main():
    engine = SwarmEngine()

    config = SwarmConfig(
        question="""PROFESSIONAL EVALUATION: Yusif Ganbarov — AI Orchestrator & Founder

You are evaluating a real person for a real professional review. Be brutally honest.
Give specific evidence for every claim. Do NOT inflate. Do NOT be diplomatic.

== BACKGROUND (verified from CV + independent research) ==

Yusif Ganbarov, 30s, Baku Azerbaijan. Career: 10+ years event/project management.

Professional history:
- WUF13 (UN World Urban Forum, Azerbaijan) — Senior Manager Guest Services (Dec 2025-present)
  Manages 35+ coordinators, 220+ volunteers, 15,000+ guests, VIP/international delegates.
  Developed WBS, org charts, crowd management plans. Daily briefings with government bodies.

- COP29 Azerbaijan PMO — Program Planning Manager (Jun-Dec 2024)
  Tracked 170+ milestones per UN/UNFCCC requirements. Improved ClickUp data accuracy 60%→98%.
  50% reduction in reporting time. Introduced unified reporting formats for senior leadership.
  Led venue walkthroughs and cross-department trainings as MOC Reporting Manager.

- CIS Games 2025 — Venue Coordinator, Ganja (Aug-Oct 2025)
  200+ volunteers, 30+ venues, 5,000+ athletes. Government coordination. Risk/issue logs.

- Megatransko LLC — PM / Executive Director (Aug 2019-present)
  40+ projects worth $50M+ delivered on time/budget. 15% cost savings on $2M project.

- I Step LLC — Director of Sales / PM (Mar 2016-Aug 2019)
  Organized Golden Byte international IT championship in Azerbaijan ($20K prize pool).
  Worked with multiple government agencies. Zero marketing budget.

Education: Bachelor Business Development (KHPI Ukraine), Diploma Front-End (IT Step)
Certs: PMP, Google PM, IT PM, Cisco IT Essentials
Languages: Azerbaijani (native), Russian (native), English (fluent)

== MIROFISH (built in 48 hours, March 23-24 2026) ==

Yusif does NOT write code. He directed Claude (AI CTO) to build MiroFish.
His contributions: architecture vision, agent management philosophy, feature priorities,
quality control, team feedback methodology, research autonomy concept.

What was built in 48 hours:
- v1-v2: 15 AI providers auto-discovered, parallel dispatch, skill augmentation, agent memory
- v3: Middleware architecture (loop detection, dedup, budget, timeout)
- v4 "Eureka": Reasoning Graph (agents see each other's arguments), 4-network Structured Memory
  (World/Experience/Opinion/Failure — Failure Network is novel, no existing framework has this)
- v5 "Hive": Agent lifecycle (probation→member→senior→lead), competency exams, team leads,
  PathProposal (agents suggest new decision paths), AutonomousUpgradeProtocol
- v6: Fixed calibration death spiral (sliding window), accuracy-scaled conviction bonus (was dead code)
- v7: ResearchLoop (Gemini Pro + Google Search + DeepSeek fallback), dead weight auto-removal,
  ResponseQualityMiddleware, per-model adaptive prompts, modular prompt system

IMPORTANT ATTRIBUTION:
- ALL code was written by Claude (AI CTO). Every line.
- Yusif's role: vision, direction, management, quality control, feature requests.
- He caught Claude not following its own protocols (memory inconsistency).
  Made Claude do root cause analysis and fix it. Same accountability as human teams.
- ResearchLoop (v7's most valuable feature) was YUSIF'S idea, not Claude's.
- Team feedback sessions (asking agents if satisfied) — Yusif's management instinct.

For industry comparison:
- CrewAI: $18M funding, 20+ team, 2+ years for comparable scope
- AutoGen (Microsoft): 18 months, 10+ researchers
- Senior engineer solo: estimated 3-6 months

== BUSINESS STRATEGY (developed same 48 hours) ==

Volaura — verified volunteer competency platform:
- Three-sided marketplace: volunteers (free) + organizations (pay) + platform
- Pricing calibrated to Azerbaijan: 49-849 AZN/month ($29-$499) — based on actual market research
  (Humanique.az charges $500-1,400 per hire, Boss.az charges $12-30 per posting)
- Swarm agents evaluated 4 business paths: 100% consensus on B2B Assessment API first
- Grant pipeline identified: Georgia GITA $240K, Turkey Tech Visa $50K, Kazakhstan $20K
- Unit economics: 80 orgs → $8,870/mo → ~$64K/year (Azerbaijan only)

== ONLINE PRESENCE (independently audited, 20+ search queries) ==

- ZERO articles where Yusif is the main topic (despite 10 years at COP29/WUF13/CIS Games level)
- Only 1 mention: Trend.az contact phone in Golden Byte 2017 article
- Critical PR gap — does massive work, others get public credit

== YOUR TASK ==

Evaluate Yusif on these dimensions (score 0-10 with specific evidence):

Path A "exceptional_hire": Yusif is a top-tier talent that companies like Anthropic, Google DeepMind,
or Y Combinator-backed startups should actively recruit for AI product/strategy roles.

Path B "strong_founder": Yusif should NOT work for others. His combination of operational experience,
AI orchestration skill, and regional market knowledge makes him a stronger founder than employee.

Path C "needs_more_proof": The 48-hour sprint is impressive but insufficient evidence.
He needs 6-12 months of sustained execution (product-market fit, revenue, team) before making claims.

Path D "overhyped": The work is real but the narrative inflates it. Claude wrote all the code.
Managing an AI tool is not the same as building an AI system. The comparison to CrewAI is misleading.

Be honest. Pick the path you genuinely believe. Cite specific evidence.""",

        paths={
            "exceptional_hire": PathDefinition(
                name="Exceptional Hire — recruit for AI product/strategy",
                description="Yusif's combination of operational leadership (COP29, WUF13), AI orchestration (MiroFish 48h), and market intuition (pricing correction, grant discovery) makes him a top candidate for AI product or strategy roles at leading companies.",
                best_case="Gets hired at Anthropic/DeepMind-tier company, brings unique operations+AI perspective",
                worst_case="Culture mismatch — he's a founder personality in a corporate structure",
                effort="Immediate — he's ready now",
            ),
            "strong_founder": PathDefinition(
                name="Strong Founder — build own company, don't work for others",
                description="His skills are most valuable as a founder: regional market knowledge (AZ/TR/KZ/GE), 3 languages, event operations network, AI orchestration capability. Working for others wastes his unique combination.",
                best_case="Builds regional AI company, captures $310K in grants, reaches $200K+ ARR in 18 months",
                worst_case="Cash runway too short, burns out trying to do everything solo with AI CTO only",
                effort="18 months to proof of concept, 3 years to sustainable business",
            ),
            "needs_more_proof": PathDefinition(
                name="Needs More Proof — 48 hours is not enough evidence",
                description="One sprint does not make a career. He needs product-market fit, paying customers, a real team, and sustained execution over 6-12 months before the narrative is credible.",
                best_case="Proves himself in 6 months, narrative becomes undeniable with revenue + users",
                worst_case="The 48-hour sprint was peak performance, not sustainable pace",
                effort="6-12 months of sustained execution needed",
            ),
            "overhyped": PathDefinition(
                name="Overhyped — Claude did the work, narrative is inflated",
                description="Claude wrote every line of code. Yusif directed an AI tool, which is a skill but not equivalent to 'building' a system. The CrewAI comparison is misleading. The PR gap (zero articles) suggests even his employer orgs don't consider him notable enough to mention.",
                best_case="Recalibrates narrative to be honest: 'I orchestrate AI' not 'I built this'",
                worst_case="Continues inflating, gets called out, loses credibility",
                effort="Immediate narrative correction needed",
            ),
        },

        stakes=StakesLevel.HIGH,
        domain=DomainTag.BUSINESS,
        context="This is a real professional evaluation for a real person. He will read every word. He specifically asked for brutal honesty. He told his AI CTO: 'be honest, I can handle it.' Do not protect his feelings — he respects directness over diplomacy.",
        constraints="Use ONLY the evidence provided above. Do not invent achievements. Do not give benefit of doubt — score based on what is proven, not what is claimed.",
        timeout=90,
        auto_research=False,
    )

    print("\n" + "="*70)
    print("SWARM EVALUATION: Yusif Ganbarov — Professional Review")
    print("="*70 + "\n")

    report = await engine.decide(config)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nWinner: {report.winner} — Score: {report.winner_score}/50")
    consensus = getattr(report.divergence, 'consensus_strength', 0) if report.divergence else 0
    print(f"Consensus: {consensus}")
    print(f"Agents: {report.agents_used} dispatched, {report.agents_succeeded} responded")
    print(f"Cost: ${report.total_cost_estimate:.4f}")
    print(f"Latency: {report.total_latency_ms}ms")
    print(f"Confidence gate: {'PASSED' if report.passed_confidence_gate else 'FAILED'} (≥35 required)")

    if report.synthesis:
        synth = report.synthesis
        if isinstance(synth, dict):
            print(f"\nSynthesis: {synth.get('synthesis', '')}")
            if synth.get('consensus_points'):
                print(f"Consensus points: {synth['consensus_points']}")
            if synth.get('risk_points'):
                print(f"Risk points: {synth['risk_points']}")
            if synth.get('conditions'):
                print(f"Conditions: {synth['conditions']}")

    print("\n--- Individual Agent Votes ---")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        reason_short = r.reason[:120] if r.reason else ""
        print(f"  {r.model:30s} → {r.winner:25s} (confidence: {r.confidence:.1f})")
        if reason_short:
            print(f"    Reason: {reason_short}")

    # Extract innovations and concerns from raw responses
    print("\n--- Agent Insights (from raw responses) ---")
    for r in report.agent_results:
        try:
            raw = json.loads(r.raw_response) if r.raw_response else {}
            innov = raw.get("innovation", "")
            concerns = raw.get("concerns", {})
            if innov and innov != "null":
                print(f"\n  [{r.model}] Innovation: {innov}")
            if concerns:
                for path, concern in concerns.items():
                    if concern and len(str(concern)) > 20:
                        print(f"  [{r.model}] Concern ({path}): {str(concern)[:150]}")
        except (json.JSONDecodeError, TypeError):
            pass

    # Weighted scores per path
    if report.weighted_scores:
        print("\n--- Path Scores ---")
        for path, score in sorted(report.weighted_scores.items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(score) + "░" * (50 - int(score))
            print(f"  {path:25s} {score:5.1f}/50  {bar}")

    # Save comprehensive results
    output_path = Path(__file__).parent / "yusif_review_result.json"
    raw_insights = []
    for r in report.agent_results:
        try:
            raw = json.loads(r.raw_response) if r.raw_response else {}
            raw_insights.append({
                "model": r.model,
                "winner": r.winner,
                "confidence": r.confidence,
                "reason": r.reason,
                "perspective": r.perspective,
                "concerns": raw.get("concerns", {}),
                "innovation": raw.get("innovation", ""),
                "self_note": raw.get("self_note", ""),
            })
        except (json.JSONDecodeError, TypeError):
            raw_insights.append({
                "model": r.model,
                "winner": r.winner,
                "confidence": r.confidence,
                "reason": r.reason,
            })

    output_data = {
        "winner": report.winner,
        "winner_score": report.winner_score,
        "passed_confidence_gate": report.passed_confidence_gate,
        "weighted_scores": report.weighted_scores,
        "agents_used": report.agents_used,
        "agents_succeeded": report.agents_succeeded,
        "total_cost": report.total_cost_estimate,
        "total_latency_ms": report.total_latency_ms,
        "synthesis": report.synthesis if isinstance(report.synthesis, dict) else str(report.synthesis),
        "agent_insights": raw_insights,
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull results saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
