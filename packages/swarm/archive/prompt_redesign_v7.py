"""
Swarm task: Redesign the MiroFish team prompt.

The CEO (Yusif) wrote a system prompt for a specialist team to work on MiroFish.
The CTO (Claude) found it architecturally outdated (describes v3, we're at v7).
Now the agents themselves will redesign it — they know the system from the inside.

Rules:
- Agents are FREE to completely rethink the prompt if they see a better path
- They must consider: who should be on the team, what context matters, what's missing
- They know the architecture because they LIVE in it
- auto_research=True so they can look up best practices for team prompts
"""

import asyncio
import json
import os
import sys
from datetime import datetime
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
You are part of MiroFish — a multi-model swarm decision engine.
This is a DESIGN task, not a self-improvement task.

=== CONTEXT ===

The CEO (Yusif) wrote a system prompt to create a specialist team that works on MiroFish.
The prompt defines: who the team is, what context they have, what gaps to fix, what rules to follow.

The CTO (Claude) reviewed the prompt and found critical issues:
1. It describes v3 architecture but we're at v7 — 5 of 8 "missing features" are already built
2. It doesn't mention: AgentHive, ReasoningGraph, StructuredMemory, ResearchLoop,
   Dead weight removal, Adaptive prompts, ResponseQualityMiddleware
3. Key numbers are wrong (calibration is sliding-window now, not multiplicative)
4. Reference repos section is 40% outdated

=== YOUR TASK ===

The CEO wants YOU (the swarm) to redesign this prompt. You have permission to:
- Rewrite it completely
- Add sections the CEO didn't think of
- Remove sections that don't matter
- Change the team composition rules
- Change what context is provided
- Change the tone, format, or structure

You are NOT limited to "suggestions." You are writing the ACTUAL new prompt.

=== THE ORIGINAL PROMPT (v1) ===

The original prompt has these sections:
1. Role definition ("You are the lead of a self-organizing specialist team")
2. Full Architecture Context (engine, types, pm, memory, middleware, providers, pipeline)
3. What's already built (list of completed features)
4. What's missing (v4 targets — mostly outdated)
5. Reference repos (5 repos for specific gaps)
6. Team rules ("Specialists, not tools" + behavioral rules)
7. User context ("Solo founder, late nights in Baku")
8. Start instruction ("Introduce your team, ask one question")

=== WHAT'S ACTUALLY TRUE NOW (v7) ===

Built and working:
- SwarmEngine with 13 providers (Groq, Gemini, DeepSeek)
- PMAgent: 12-step pipeline (dispatch → aggregate → debate → scale → synthesize)
- ReasoningGraph: agents see each other's structured arguments, Round 2 revision
- StructuredMemory: World/Experience/Opinion/Failure networks (not flat JSON)
- AgentHive: PROBATIONARY→MEMBER→SENIOR→LEAD lifecycle, competency exams
- PathProposal: agents propose new paths not in original question
- ResearchLoop: agents request web research → Gemini Pro + Google Search → World Network
- DeepSeek fallback for research when Gemini fails
- TokenCountingMiddleware: real per-provider costs
- ResponseQualityMiddleware: rejects freerider responses (<120ch)
- Dead weight auto-removal: allam-2-7b blacklisted, 3-failed-exams filter
- Per-model adaptive prompts: small models get focused prompt
- AutonomousUpgradeProtocol: Godel pattern, kill-switch, immutable files
- Sliding-window calibration (not multiplicative — old death-spiraled)
- Accuracy-scaled conviction bonus (not flat 1.15x)

Actually missing (v8 targets):
1. Linear pipeline → DAG/graph orchestration
2. Skill A/B testing framework
3. Streaming results (currently all batched)
4. Semantic PathProposal dedup (word overlap → embeddings)
5. Direct inter-agent communication beyond ReasoningGraph
6. Nightly autonomous self-upgrade cycles
7. Skills-as-a-service (agents fetch/return/upgrade skills)

=== EVALUATION CRITERIA ===

You're voting on how the prompt should be redesigned:

PATH A — "polish": Keep the original structure, update facts, fix numbers
PATH B — "restructure": Same intent, different format (maybe shorter, maybe modular)
PATH C — "rethink": Fundamentally different approach to team prompt design

For each path, provide your SPECIFIC proposed changes in the "reason" field.
Include actual text you'd write, not just "add a section about X."

If you vote "rethink" — explain what's wrong with the original approach and
what your alternative looks like. Be concrete.
"""

PATHS = {
    "polish": PathDefinition(
        name="Polish — update facts, keep structure",
        description="The original structure works. Update architecture to v7, fix numbers, refresh reference repos. Minimal changes to format or approach.",
        best_case="Quick, accurate, maintains what's already good.",
        worst_case="Misses opportunity to improve the prompt's fundamental design.",
        effort="S",
    ),
    "restructure": PathDefinition(
        name="Restructure — same intent, better format",
        description="The original INTENT is right but the FORMAT could be better. Maybe shorter. Maybe modular (separate files for architecture vs team rules). Maybe different information hierarchy.",
        best_case="More usable prompt that's easier to maintain as MiroFish evolves.",
        worst_case="Change for change's sake. Breaks what works.",
        effort="M",
    ),
    "rethink": PathDefinition(
        name="Rethink — fundamentally different approach",
        description="The original prompt makes wrong assumptions about what the team needs. Maybe the team shouldn't get a giant context dump. Maybe they should discover the architecture themselves. Maybe the prompt should be task-specific, not general.",
        best_case="A prompt design pattern that scales and evolves with MiroFish.",
        worst_case="Over-engineering a prompt. Complexity without clarity.",
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
    safe_print(f"PROMPT REDESIGN — Swarm designs its own team prompt")
    safe_print(f"{len(engine.providers)} providers | research enabled")
    safe_print(f"{'='*70}\n")

    config = SwarmConfig(
        question=QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.ARCHITECTURE,
        temperature=0.85,
        timeout_seconds=120.0,
        max_agents=15,
        auto_research=True,
    )

    report = await engine.decide(config)

    safe_print(f"\n{'='*70}")
    safe_print(f"RESULTS")
    safe_print(f"{'='*70}")
    safe_print(f"Agents: {report.agents_succeeded}/{report.agents_used}")

    for path_id in ["polish", "restructure", "rethink"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        safe_print(f"  {path_id:12s} | {votes:2d} votes | {score:.1f}/50")
    safe_print(f"Winner: {report.winner} ({report.winner_score:.1f}/50)")

    # Individual proposals
    safe_print(f"\n{'='*70}")
    safe_print(f"PROPOSALS")
    safe_print(f"{'='*70}")

    for i, r in enumerate(report.agent_results):
        if not r.json_valid or r.error:
            continue
        model_short = r.model.split("/")[-1][:25] if r.model else "?"
        safe_print(f"\n--- {model_short} [{r.winner}] ---")
        for line in (r.reason or "").split("\n"):
            line = line.strip()
            if line:
                safe_print(f"  {line}")

    if report.research_conducted:
        safe_print(f"\n--- RESEARCH ---")
        for rc in report.research_conducted:
            safe_print(f"  {rc['topic'][:80]}: {rc['summary'][:150]}")

    # Save
    output_path = Path(__file__).parent / "prompt_redesign_report.json"
    output_path.write_text(json.dumps(report.model_dump(), indent=2, default=str), encoding="utf-8")

    # Compact summary
    lines = [
        f"# Prompt Redesign Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Votes",
        f"- polish: {report.divergence.winner_votes.get('polish', 0)}",
        f"- restructure: {report.divergence.winner_votes.get('restructure', 0)}",
        f"- rethink: {report.divergence.winner_votes.get('rethink', 0)}",
        f"- Winner: {report.winner}",
        f"",
        f"## Top Proposals",
    ]
    detailed = sorted(
        [r for r in report.agent_results if r.json_valid and not r.error and r.reason],
        key=lambda r: len(r.reason), reverse=True,
    )[:5]
    for r in detailed:
        model_short = r.model.split("/")[-1][:25]
        lines.append(f"")
        lines.append(f"### {model_short} [{r.winner}]")
        lines.append(f"{(r.reason or '')[:800]}")

    if report.research_conducted:
        lines.append(f"")
        lines.append(f"## Research")
        for rc in report.research_conducted:
            lines.append(f"- {rc['topic'][:80]}: {rc['summary'][:150]}")

    summary_path = Path(__file__).parent / "prompt_redesign_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    safe_print(f"\nSummary: {summary_path}")
    safe_print(f"Full: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
