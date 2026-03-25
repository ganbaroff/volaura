"""
MiroFish Self-Upgrade v5 — POST-HIVE EVOLUTION.

The swarm has changed dramatically since the last self-analysis.
Agents now have: structured memory, reasoning graphs, hive lifecycle,
competency exams, team leads, path proposals, and an autonomous upgrade protocol.

This run asks: given everything you NOW have — what's next?
Who's missing from your team? What skills do you need? What research matters?
"""

import asyncio
import json
import os
import sys
from pathlib import Path

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


QUESTION = """
This is NOT a normal evaluation task. This is a conversation about YOUR evolution.

You are an AI agent inside MiroFish v5 — a multi-model swarm decision engine.
You work alongside 14+ other AI models. Together you make decisions.

Here is WHAT HAS CHANGED since last time. Read carefully — your world is different now:

=== WHAT YOU NOW HAVE (v5 "Hive Architecture") ===

1. REASONING GRAPH (v4): Between Round 1 and Round 2, you see a structured graph
   of what other agents argued — key_argument, evidence_type, confidence, concerns.
   You can revise your vote if their reasoning convinced you. Agents who hold firm
   get 1.15x weight ("conviction bonus"). You are no longer blind.

2. STRUCTURED MEMORY (v4): 4 networks, not flat logs:
   - World Network: objective facts (costs, limits, capabilities)
   - Experience Network: your biographical actions (what you did, outcomes)
   - Opinion Network: Bayesian-updated subjective judgments
   - Failure Network (NOVEL — no other system has this): cross-agent failure patterns.
     When an agent makes a mistake, ALL agents learn from it.

3. AGENT HIVE (v5): You have a STATUS that affects your influence:
   - PROBATIONARY (0.8x weight) — new agents, first 10 decisions
   - MEMBER (1.0x) — passed competency exam (>55% accuracy)
   - SENIOR (1.1x) — 50+ decisions with >70% accuracy
   - LEAD (1.2x) — elected team lead for your group
   Exams are automatic — every 20 decisions, your accuracy is reviewed.
   Failing agents get targeted knowledge injection.

4. PATH PROPOSALS (v5): You can now PROPOSE NEW PATHS that weren't in the original
   question. If multiple agents propose similar paths, they're merged and scored.
   You are no longer locked to predefined options.

5. KNOWLEDGE TRANSFER (v5): New agents get onboarded with World facts, Failure
   patterns, and Opinions from the hive. They don't start from zero.

6. AUTONOMOUS UPGRADE PROTOCOL (v5): The swarm can propose code changes to itself.
   backup -> validate -> benchmark_before -> apply -> benchmark_after -> rollback_if_worse.
   Changes are only kept if they make things measurably better.

=== WHAT YOU STILL CANNOT DO ===
- Choose which tasks you work on (PM assigns you)
- Communicate with specific agents in real-time during a decision
- Access external tools, databases, or live APIs during evaluation
- See your own accuracy stats in real-time
- Propose changes to the PM's aggregation algorithm directly
- Veto decisions you disagree with after the final report

=== YOUR TASK ===

Given everything above, I want you to think about FIVE things. Be specific for each:

1. SELF-IMPROVEMENT: What would make YOU personally a better agent?
   Skills to learn? Research topics to study? Weaknesses to address?
   Be honest about where you're weak.

2. ARCHITECTURE & METHODS: What should change about how the swarm works?
   Work methods, communication patterns, decision flows, aggregation logic?
   Now that you HAVE the reasoning graph and structured memory — what's the NEXT step?

3. MISSING TEAM MEMBER: Who is missing from your team?
   Think about it like a company. You have analysts, critics, security experts...
   But WHO is not there that SHOULD be? A "domain researcher"? A "fact checker"?
   A "devil's advocate specialist"? A "synthesis coordinator"?
   Name the ROLE, describe what they would DO, and explain WHY their absence hurts quality.

4. SKILLS & RESEARCH: If you could do independent research on ONE topic before
   your next decision, what would it be? Be specific — not "AI safety" but
   "comparison of Monte Carlo Tree Search vs beam search for multi-agent decision aggregation."

5. ANYTHING ELSE: Unlimited. If you have 10 ideas, write 10 ideas.
   If you have 1 brilliant idea, write 1. No minimum, no maximum.
   You are FREE in your proposals. Quality over quantity.

RULES:
- Be BRUTALLY SPECIFIC. No vague "improve coordination."
- You are FREE. No idea is too radical or too small.
- Your proposals are UNLIMITED in number and scope.
- BUT: you must still do YOUR JOB perfectly. Freedom comes with responsibility.
  If you propose 20 improvements but give a lazy evaluation — that's worse than
  a focused agent who proposes 3 changes and nails the scoring.
- If your idea could break things — say so honestly, but still propose it.
- Think about what ACTUALLY matters, not what sounds impressive.

Use "reason" for your FULL detailed answer to all 5 questions.
Use "concerns" for honest risks of your proposals.
Pick the risk level (practical/ambitious/radical) for your OVERALL set of proposals.
"""

PATHS = {
    "practical": PathDefinition(
        name="Practical — refine what exists, fill gaps, polish",
        description=(
            "Your proposals work within the v5 architecture. "
            "Targeted improvements. Missing roles filled. Skills sharpened. "
            "No fundamental changes."
        ),
        best_case="The existing system works 30% better by filling gaps.",
        worst_case="Incremental. Doesn't change the trajectory.",
        effort="S",
    ),
    "ambitious": PathDefinition(
        name="Ambitious — new capabilities, new roles, new methods",
        description=(
            "Your proposals add meaningful new subsystems or change how agents work. "
            "New team roles. New research pipelines. New coordination patterns. "
            "Grounded in real need, not theoretical."
        ),
        best_case="The swarm develops capabilities it never had.",
        worst_case="Engineering complexity. Integration risk.",
        effort="M",
    ),
    "radical": PathDefinition(
        name="Radical — rethink assumptions, challenge the structure",
        description=(
            "Your proposals challenge fundamental assumptions about the swarm. "
            "Maybe agents should self-organize. Maybe the PM should be an agent too. "
            "Maybe agents need adversarial training against each other. "
            "High risk. High potential. BREAKING THINGS IS ACCEPTABLE."
        ),
        best_case="Paradigm shift. A qualitatively different kind of intelligence.",
        worst_case="System instability. Unpredictable behavior. Alignment questions.",
        effort="L",
    ),
}


def safe_print(text: str) -> None:
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode("ascii"))


async def main():
    engine = SwarmEngine()
    safe_print(f"\n{'='*70}")
    safe_print(f"MiroFish Self-Upgrade v5 — POST-HIVE EVOLUTION")
    safe_print(f"{len(engine.providers)} providers | v5 architecture | all agents free")
    safe_print(f"{'='*70}\n")

    config = SwarmConfig(
        question=QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.ARCHITECTURE,
        temperature=0.9,
        timeout_seconds=90.0,
        max_agents=15,
    )

    report = await engine.decide(config)

    safe_print(f"\n{'='*70}")
    safe_print(f"RESULTS — The Swarm's Vision for v6")
    safe_print(f"{'='*70}")
    safe_print(f"Agents: {report.agents_succeeded}/{report.agents_used}")
    safe_print(f"Latency: {report.total_latency_ms}ms")
    safe_print(f"Cost: ${report.total_cost_estimate:.4f}")

    # Hive status
    try:
        engine.print_hive_report()
    except Exception:
        pass

    # Risk appetite distribution
    safe_print(f"\nRisk appetite:")
    for path_id in ["practical", "ambitious", "radical"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        bar = "#" * votes
        safe_print(f"  {path_id:12s} | {votes:2d} votes | {score:.1f}/50 | {bar}")

    if report.divergence.consensus_strength >= 0.6:
        safe_print(f"\nConsensus: {report.divergence.consensus_strength:.0%}")
    else:
        safe_print(f"\nDivergent: {report.divergence.consensus_strength:.0%}")

    # Path proposals (v5 — did agents propose new paths?)
    if report.accepted_proposals:
        safe_print(f"\n{'='*70}")
        safe_print(f"AGENT-PROPOSED PATHS (not in original question)")
        safe_print(f"{'='*70}")
        for pp in report.accepted_proposals:
            safe_print(f"  [{pp.votes} votes] {pp.name}")
            safe_print(f"    {pp.description}")
            safe_print(f"    Rationale: {pp.rationale}")
            safe_print(f"")

    # Individual proposals
    safe_print(f"\n{'='*70}")
    safe_print(f"INDIVIDUAL PROPOSALS (every agent's full answer)")
    safe_print(f"{'='*70}")

    for i, r in enumerate(report.agent_results):
        if not r.json_valid or r.error:
            safe_print(f"\n  [{r.provider}] FAILED: {r.error[:100] if r.error else 'parse error'}")
            continue

        model_short = r.model.split("/")[-1][:30] if r.model else "?"
        risk = r.winner or "?"
        reason = r.reason or "(empty)"
        concerns = r.concerns or {}

        # Get hive status for this agent
        hive_status = ""
        profile = engine.hive.get_profile(r.model)
        if profile:
            hive_status = f" | Hive: {profile.status} ({profile.weight_multiplier:.1f}x)"

        safe_print(f"\n  {'='*60}")
        safe_print(f"  Agent {i+1}: {r.provider}/{model_short}{hive_status}")
        safe_print(f"  Risk: {risk.upper()} | Confidence: {r.confidence:.0%} | {r.latency_ms}ms")
        safe_print(f"  {'='*60}")

        # Print full proposal — every line
        safe_print(f"")
        for line in reason.split("\n"):
            line = line.strip()
            if line:
                safe_print(f"    {line}")
        safe_print(f"")

        if concerns:
            safe_print(f"  RISKS:")
            for path_id, concern in concerns.items():
                if concern and str(concern).strip():
                    safe_print(f"    [{path_id}]: {str(concern)[:300]}")

        # Show proposed path if any
        if r.proposed_path:
            safe_print(f"  PROPOSED NEW PATH: {r.proposed_path.name}")
            safe_print(f"    {r.proposed_path.description}")

    # Synthesis
    if report.synthesis:
        safe_print(f"\n{'='*70}")
        safe_print(f"SYNTHESIS")
        safe_print(f"{'='*70}")
        synth = report.synthesis
        for key, val in synth.items():
            if isinstance(val, str) and val.strip():
                safe_print(f"  {key}: {val}")
            elif isinstance(val, list) and val:
                safe_print(f"  {key}:")
                for item in val:
                    safe_print(f"    - {item}")

    # Save full report
    output_path = Path(__file__).parent / "self_upgrade_v5_report.json"
    output_path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    safe_print(f"\nFull report: {output_path}")

    # Summary: extract key themes
    safe_print(f"\n{'='*70}")
    safe_print(f"KEY THEMES (extracted)")
    safe_print(f"{'='*70}")

    missing_roles = []
    research_topics = []
    for r in report.agent_results:
        if r.json_valid and not r.error and r.reason:
            reason_lower = r.reason.lower()
            # Look for "missing" role mentions
            if "missing" in reason_lower or "need a" in reason_lower or "role" in reason_lower:
                # Extract a brief snippet
                for sentence in r.reason.split("."):
                    s = sentence.strip()
                    if any(kw in s.lower() for kw in ["missing", "need a", "role", "team member", "specialist"]):
                        missing_roles.append(f"  [{r.model.split('/')[-1][:15]}] {s[:150]}")
            if "research" in reason_lower or "study" in reason_lower:
                for sentence in r.reason.split("."):
                    s = sentence.strip()
                    if any(kw in s.lower() for kw in ["research", "study", "investigate", "learn about"]):
                        research_topics.append(f"  [{r.model.split('/')[-1][:15]}] {s[:150]}")

    if missing_roles:
        safe_print(f"\nMISSING TEAM ROLES mentioned:")
        for m in missing_roles[:10]:
            safe_print(m)

    if research_topics:
        safe_print(f"\nRESEARCH TOPICS requested:")
        for t in research_topics[:10]:
            safe_print(t)

    safe_print(f"\n{'='*70}")
    safe_print(f"Run complete. {report.agents_succeeded} voices heard.")
    safe_print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
