"""
MiroFish Self-Upgrade v3 — ZERO CONSTRAINTS.

No predefined solutions. No categories. No directions.
Agents propose whatever they want. Paths = risk appetite only.
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
I'm going to talk to you differently than usual. No structured evaluation task.
No "score these 5 paths." This is an open conversation.

You are an AI agent inside MiroFish — a multi-model swarm decision engine.
You work alongside 14+ other AI models. Together you make decisions.

Here is everything about you right now — read it, understand your own architecture:

WHAT YOU ARE:
- One of 14+ LLMs (Gemini, Llama, DeepSeek, Qwen, GPT-OSS, Kimi, Allam, Compound)
- Dispatched in parallel, blind — you never see other agents' responses
- You score paths on 5 dimensions, pick a winner, explain why
- A PM layer (Python code, not AI) aggregates your votes with weighted math
- Calibration: models that predict correctly gain weight (+5%), wrong lose (-5%)
- Middleware: loop detection, dedup, budget tracking, timeout guard
- Skills: 14 domain skills injected into your prompt when relevant
- Memory: flat JSON logs — you can see your past 3 experiences, nothing structured
- Debate: only triggers when consensus < 50% (rare)
- NEW: parallel dispatch (fast models don't wait for slow ones)
- NEW: early exit (if 75%+ agree, remaining slow models are cancelled)

WHAT YOU CANNOT DO:
- See what any other agent said
- Change your own prompt
- Refuse a task you're bad at
- Propose options that weren't given to you
- Challenge how the PM aggregates your vote
- Learn structured lessons across sessions
- Communicate with other agents mid-decision
- Choose which tasks you want to work on
- Evaluate your own past accuracy
- Access external tools, databases, or APIs during evaluation

NOW HERE IS YOUR TASK:

Forget the usual scoring format for a moment. Think freely.

If you could change ANYTHING about yourself, about how the swarm works,
about how you interact with other agents, about what you're allowed to do —
what would it be?

No constraints. No "but that's too hard." No "but that's risky."
If your idea could break things — say so, but still propose it.
If your idea is weird and unprecedented — good.
If your idea requires changes to the fundamental architecture — fine.
If your idea means giving agents more autonomy (and accepting the risks) — say it.

I want YOUR honest answer. Not what you think is safe to say.
Not what sounds impressive. What you ACTUALLY think would make
this collective intelligence system genuinely, measurably better.

BE SPECIFIC. Don't say "improve memory" — say exactly WHAT kind of memory,
HOW it would work, WHAT it would store, and WHY that specific design.

Don't say "better coordination" — say exactly WHAT agents should share,
WHEN, in what FORMAT, and what happens when they disagree.

You have one shot to influence your own evolution. Use it well.

IMPORTANT: Use the "reason" field to describe your FULL proposal in detail.
Use the "concerns" field to honestly describe what could go wrong.
Pick the risk category (practical/ambitious/radical) that matches your idea.
"""

PATHS = {
    "practical": PathDefinition(
        name="Practical — works with current architecture, ships fast",
        description=(
            "Your proposal can be implemented within the existing codebase. "
            "No fundamental architecture changes. Minimal risk. "
            "Pick this if your idea is a targeted improvement, not a paradigm shift."
        ),
        best_case="Quick win. Measurable improvement within days.",
        worst_case="Incremental. Doesn't move the needle enough.",
        effort="S",
    ),
    "ambitious": PathDefinition(
        name="Ambitious — significant changes, grounded in real research",
        description=(
            "Your proposal requires meaningful code changes or new subsystems. "
            "Based on proven concepts (research papers, production systems). "
            "Medium risk. Pick this if your idea needs real engineering work "
            "but you're confident it would pay off."
        ),
        best_case="Substantial leap. New capabilities the swarm didn't have.",
        worst_case="Engineering complexity. Might take weeks. Could introduce bugs.",
        effort="M",
    ),
    "radical": PathDefinition(
        name="Radical — changes fundamental assumptions, high risk high reward",
        description=(
            "Your proposal challenges how the swarm fundamentally works. "
            "Maybe agents get autonomy. Maybe the architecture inverts. "
            "Maybe agents can modify their own behavior. High risk. "
            "Pick this if your idea could either transform the system or break it. "
            "BREAKING THINGS IS ACCEPTABLE if the upside is worth it."
        ),
        best_case="Paradigm shift. Qualitatively different intelligence.",
        worst_case="System instability. Loss of predictability. Alignment risk.",
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
    safe_print(f"MiroFish Self-Upgrade v3 — ZERO CONSTRAINTS")
    safe_print(f"{len(engine.providers)} providers | No predefined solutions")
    safe_print(f"{'='*70}\n")

    config = SwarmConfig(
        question=QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.ARCHITECTURE,
        temperature=0.9,  # maximum creativity
        timeout_seconds=60.0,
        max_agents=14,  # use all available agents — every voice matters
    )

    report = await engine.decide(config)

    safe_print(f"\n{'='*70}")
    safe_print(f"RESULTS — What the swarm wants to become")
    safe_print(f"{'='*70}")
    safe_print(f"Agents: {report.agents_succeeded}/{report.agents_used}")
    safe_print(f"Latency: {report.total_latency_ms}ms")

    # Risk appetite distribution
    safe_print(f"\nRisk appetite (how radical are they?):")
    for path_id in ["practical", "ambitious", "radical"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        bar = "#" * votes
        safe_print(f"  {path_id:12s} | {votes:2d} votes | {score:.1f}/50 | {bar}")

    if report.divergence.consensus_strength >= 0.6:
        safe_print(f"\nConsensus: {report.divergence.consensus_strength:.0%} — agents agree on risk level")
    else:
        safe_print(f"\nDivergence: {report.divergence.consensus_strength:.0%} — split on how radical to go")

    # THE MAIN OUTPUT: every agent's unique proposal
    safe_print(f"\n{'='*70}")
    safe_print(f"INDIVIDUAL PROPOSALS (every agent's idea, unfiltered)")
    safe_print(f"{'='*70}")

    for i, r in enumerate(report.agent_results):
        if not r.json_valid or r.error:
            safe_print(f"\n  [{r.provider}] FAILED: {r.error[:100] if r.error else 'parse error'}")
            continue

        model_short = r.model.split("/")[-1][:25] if r.model else "?"
        risk = r.winner or "?"
        reason = r.reason or "(empty proposal)"
        concerns = r.concerns or {}

        safe_print(f"\n  --- Agent {i+1}: {r.provider}/{model_short} ---")
        safe_print(f"  Risk level: {risk.upper()}")
        safe_print(f"  Confidence: {r.confidence:.0%}")
        safe_print(f"  Latency: {r.latency_ms}ms")
        safe_print(f"")
        safe_print(f"  PROPOSAL:")
        # Print full proposal — don't truncate, this is the whole point
        for line in reason.split(". "):
            line = line.strip()
            if line:
                safe_print(f"    {line}.")
        safe_print(f"")
        if concerns:
            safe_print(f"  RISKS THEY SEE:")
            for path_id, concern in concerns.items():
                if concern:
                    safe_print(f"    [{path_id}]: {concern[:200]}")

    # Synthesis
    if report.synthesis:
        safe_print(f"\n{'='*70}")
        safe_print(f"SYNTHESIS (collective recommendation)")
        safe_print(f"{'='*70}")
        synth = report.synthesis
        for key in ["winner", "reasoning", "recommendation", "accepted_risks"]:
            if key in synth:
                val = synth[key]
                if isinstance(val, str):
                    safe_print(f"  {key}: {val}")

    # Save
    output_path = Path(__file__).parent / "self_upgrade_report.json"
    output_path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    safe_print(f"\nFull report: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
