"""
Swarm re-evaluates the CTO's review of the CEO — with CORRECT attribution.

v1 problem: Agents blamed Yusif for bugs that Claude (CTO) wrote.
The calibration death spiral was in Claude's code. The dead conviction bonus was Claude's bug.
Yusif doesn't write code. He designs systems and directs development.

This v2 makes the division of labor crystal clear.
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
You are agents inside MiroFish. This is a CORRECTED re-evaluation.

=== CRITICAL CORRECTION FROM v1 ===

In the v1 evaluation, some of you said the CTO's review was "too generous" because
"Yusif's decisions triggered the freerider pattern and calibration death spiral."

THIS IS WRONG. Here is what actually happened:

- The calibration death spiral (w *= 0.95 compounding to floor) was CLAUDE'S CODE BUG.
  Claude wrote memory.py with multiplicative weights. Yusif never saw this code.

- The conviction bonus being dead code was CLAUDE'S IMPLEMENTATION BUG.
  Claude defined compute_conviction_weights() in reasoning_graph.py but never wired it into pm.py.

- The freerider pattern (small models giving empty "radical" votes) was a PROMPT DESIGN issue.
  Claude wrote the v5 prompt that made it easy to game.

Yusif's role is IDEA GENERATION AND DIRECTION. He does NOT write Python.
Claude's role is TECHNICAL IMPLEMENTATION. He writes ALL the code.

When Yusif said "give them internet access" — that's vision.
When the ResearchLoop had a JSON mode incompatibility with Google Search — that's Claude's bug.

When Yusif said "agents should evaluate themselves" — that's leadership instinct.
When 0/10 agents said "satisfied" — that's the SYSTEM telling Yusif it needs work,
which is EXACTLY why he asked the question. He diagnosed correctly.

=== WHO DID WHAT — COMPLETE ATTRIBUTION ===

YUSIF (CEO, idea generator, zero code):
- Conceived: universal decision engine from a 3-agent chatbot
- Designed: tournament voting, innovation field, multi-provider architecture
- Decided: "agents should propose their own improvements" → led to self-upgrade runs
- Decided: "don't limit them" → freedom led to 3 novel PathProposals
- Decided: "give them internet access" → led to ResearchLoop (novel feature)
- Decided: "are they satisfied?" → led to team feedback session (0/10 satisfied → actionable)
- Decided: "remove dead weight" → led to allam-2-7b removal
- Decided: "they should discuss the prompt themselves" → agents voted 8/10 for rethink
- Speed: ALL of the above in 48 hours, while ALSO building Volaura (separate full-stack project)
- Context: works late nights from Baku, Azerbaijan. Solo founder. No team. No funding.

CLAUDE (CTO, all code, zero ideas):
- Wrote: ALL Python code (~5000 lines across 15+ files)
- Bugs introduced by Claude: calibration death spiral, dead conviction bonus, broken specificity filter
- Bugs found by agents, fixed by Claude: same session, every time
- Claude's strength: fast implementation, good at turning Yusif's vision into code
- Claude's weakness: writes bugs that agents catch, sometimes over-engineers

=== INDUSTRY COMPARISON — HOW LONG DOES THIS TAKE? ===

What was built in 48 hours:
- Multi-model swarm engine with 13 providers
- 12-step decision pipeline (dispatch → aggregate → debate → scale → synthesize)
- Middleware stack (5 middlewares)
- ReasoningGraph with Round 2 revision
- StructuredMemory with 4 semantic networks
- AgentHive with lifecycle, exams, knowledge transfer
- PathProposal system
- AutonomousUpgradeProtocol with kill-switch
- ResearchLoop with Gemini Pro + Google Search + DeepSeek fallback
- Dead weight auto-removal
- Per-model adaptive prompts
- 3 self-upgrade runs with analysis
- Team feedback session
- Prompt redesign vote

Industry comparison for similar scope (without AI assistance):
- CrewAI: founded 2023, team of 20+, raised $18M, ~2 years to reach comparable features
- AutoGen (Microsoft): team of 10+ researchers, ~18 months development
- LangGraph: Backed by LangChain ($25M raised), team of 15+, ~1 year to production
- A single senior engineer without AI: 3-6 months for this scope
- A team of 3 engineers: 6-8 weeks

Yusif + Claude did it in 48 hours. With Yusif having ZERO prior Python experience.

=== YOUR TASK ===

Re-evaluate with correct attribution:

Q1: Given the CORRECT division of labor (Yusif = ideas/direction, Claude = code),
    are the CTO's scores fair now?
    - Systems Thinking: 9/10
    - AI Product Intuition: 9/10 (revised down from 10 after v1 feedback)
    - Execution Speed: 9/10
    - Self-Awareness: 8/10

Q2: How does Yusif's output compare to industry professionals you're aware of?
    Consider: speed, scope, novelty, and the constraint of working alone from Baku.

Q3: If you were hiring at Anthropic, Google DeepMind, or OpenAI —
    would this 48-hour body of work make you want to interview Yusif?
    What role? What would concern you?

Q4: Rate Yusif yourself (1-10) with one sentence each:
    Vision, Speed, Leadership, Strategic thinking, Communication, Risk tolerance

Use "reason" for full answers. Be honest but attribute correctly.
"""

PATHS = {
    "fair": PathDefinition(
        name="Assessment is fair with corrected attribution",
        description="The CTO's scores are accurate when you properly separate idea generation from implementation bugs.",
        best_case="Accurate reference that gets Yusif interviews.",
        worst_case="Some nuances still missed.",
        effort="S",
    ),
    "still_too_generous": PathDefinition(
        name="Still too generous even with corrections",
        description="Even separating code bugs from vision, some scores are inflated.",
        best_case="Honest correction prevents credibility loss.",
        worst_case="Over-correction into harshness.",
        effort="M",
    ),
    "undervalued": PathDefinition(
        name="Yusif is undervalued — scores should be higher",
        description="Given the constraints (solo, no funding, Baku, 48 hours, zero Python), the scores don't capture how exceptional this is.",
        best_case="A stronger, more accurate recommendation.",
        worst_case="Inflation that damages credibility.",
        effort="M",
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
    safe_print(f"RE-EVALUATION v2 — Correct Attribution")
    safe_print(f"{len(engine.providers)} providers")
    safe_print(f"{'='*70}\n")

    config = SwarmConfig(
        question=QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.GENERAL,
        temperature=0.8,
        timeout_seconds=90.0,
        max_agents=15,
        auto_research=False,
    )

    report = await engine.decide(config)

    safe_print(f"\nAgents: {report.agents_succeeded}/{report.agents_used}")
    for path_id in ["fair", "still_too_generous", "undervalued"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        safe_print(f"  {path_id:20s} | {votes:2d} votes | {score:.1f}/50")
    safe_print(f"Winner: {report.winner}")

    safe_print(f"\n{'='*70}")
    for r in report.agent_results:
        if not r.json_valid or r.error:
            continue
        model_short = r.model.split("/")[-1][:25] if r.model else "?"
        safe_print(f"\n--- {model_short} [{r.winner}] ---")
        for line in (r.reason or "").split("\n"):
            if line.strip():
                safe_print(f"  {line.strip()}")

    output_path = Path(__file__).parent / "cto_review_v2_report.json"
    output_path.write_text(json.dumps(report.model_dump(), indent=2, default=str), encoding="utf-8")

    lines = [
        f"# CTO Review v2 — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Verdict: {report.winner}",
        f"- fair: {report.divergence.winner_votes.get('fair', 0)}",
        f"- still_too_generous: {report.divergence.winner_votes.get('still_too_generous', 0)}",
        f"- undervalued: {report.divergence.winner_votes.get('undervalued', 0)}",
        f"",
        f"## Top Responses",
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

    summary_path = Path(__file__).parent / "cto_review_v2_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    safe_print(f"\nSummary: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
