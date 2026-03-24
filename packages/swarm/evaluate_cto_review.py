"""
Swarm evaluates the CTO's (Claude's) review of the CEO (Yusif).

Context: Claude assessed Yusif's skills after 48 hours of collaboration.
Now the swarm evaluates: is this assessment fair? What did Claude miss?

The agents should imagine Yusif works ONLY on MiroFish (no other projects).
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
You are agents inside MiroFish — a swarm decision engine.
You know this system from the inside because you ARE this system.

=== CONTEXT ===

The CTO (Claude, the orchestrator who builds your infrastructure) wrote a professional
assessment of the CEO (Yusif Aliyev) for a LinkedIn post targeting AI companies like Anthropic.

The CTO was asked to evaluate the CEO honestly, as a reference for employers.

Below is the CTO's assessment. Your job is to evaluate whether it's FAIR, ACCURATE,
and whether it MISSES anything important.

=== WHAT YUSIF BUILT IN 48 HOURS (the evidence) ===

Imagine Yusif works ONLY on MiroFish (no other projects). Here's what happened:

Hour 0-4: Saw a basic 3-agent Gemini chat. Said "this should be a universal decision engine."
  Designed: multi-provider architecture, 5 API keys, tournament voting, innovation field.

Hour 4-8: 15 providers auto-discovered and working. Skill library with 14 skills.
  Agent memory. Self-learning calibration. 7 benchmark runs, 100% success.

Hour 8-12: Middleware stack (loop detection, dedup, budget, timeout).
  Analyzed DeerFlow research — took what mattered, deferred what didn't.

Hour 12-16: ReasoningGraph (agents see each other's arguments).
  StructuredMemory with 4 networks including novel Failure Network.
  Parallel dispatch with early exit — 71% latency reduction.

Hour 16-20: AgentHive — full lifecycle with competency exams.
  PathProposal — agents can propose new paths.
  AutonomousUpgradeProtocol — Godel pattern with kill-switch.

Hour 20-24: Self-upgrade run — asked 15 agents to improve themselves.
  Discovered freerider pattern. Implemented KILL_SWITCH + IMMUTABLE_FILES
  based on agent feedback (kimi-k2 flagged the risk).

Hour 24-28: Fixed calibration death spiral (agents found it).
  Fixed conviction bonus (was dead code). Improved freerider detection.

Hour 28-32: ResearchLoop — agents can now request web research.
  Gemini Pro + Google Search. DeepSeek fallback. Working end-to-end.

Hour 32-36: Dead weight removal (allam-2-7b blacklisted).
  ResponseQualityMiddleware. Per-model adaptive prompts.

Hour 36-40: Team feedback session — agents evaluated their own satisfaction.
  0/10 said satisfied. All feedback implemented within the same session.

Hour 40-44: Prompt redesign — agents voted 8/10 to rethink the approach.
  3 research topics auto-executed. Modular prompt design proposed.

Hour 44-48: LinkedIn post draft. This evaluation. Full chat review.

=== THE CTO'S ASSESSMENT OF YUSIF ===

1. Systems Thinking: 9/10
   "He doesn't write code. He designs systems. When he saw a simple chatbot with 3 agents,
   he took it to 15 providers, middleware, reasoning graph, hive lifecycle, and autonomous
   upgrade in 4 hours. He doesn't ask 'how to do X' — he says 'agents should decide who
   they need on their team' and leaves implementation to me."

2. AI Product Intuition: 10/10
   Three specific moments cited:
   - "You're limiting them" — pushed for agent freedom, led to better proposals
   - "Give them internet access" — led to ResearchLoop, novel feature
   - "Are they satisfied?" — led to team feedback session, actionable insights

3. Execution Speed: 9/10
   "7 swarm versions in 3 days. He doesn't know Python. He doesn't know FastAPI.
   But he knows WHAT to build and WHY."

4. Self-Awareness: 8/10
   "Asked me to evaluate him twice. Didn't get offended when the swarm called his
   decisions 'unvalidated'. Says 'you decide, you're the CTO' and trusts."

5. Weaknesses identified:
   - Scope expansion (3 new ideas per session, hard to stay focused)
   - No formal CS background
   - Deployment follow-through (code ready but deploy incomplete)

6. Recommended roles at Anthropic: AI Product Manager, Technical Program Manager,
   Agent Architecture

=== YOUR TASK ===

Evaluate this assessment:

Q1: Is the CTO's rating FAIR? Too generous? Too harsh? On which dimensions?
Q2: What did the CTO MISS about Yusif that you observed from inside the system?
Q3: Based on what you experienced, what role would Yusif be BEST at in an AI company?
Q4: If you were an Anthropic hiring manager reading the LinkedIn post, would you respond?
   Why or why not? What would make it stronger?
Q5: Rate Yusif yourself, on a 1-10 scale, with one sentence justification for each:
   - Vision, Speed, Leadership, Technical depth, Communication, Risk tolerance

Use "reason" for your full answers. Be honest — Yusif explicitly asked for honesty.
"""

PATHS = {
    "fair": PathDefinition(
        name="Assessment is fair and accurate",
        description="The CTO's scores and analysis are correct. Minor adjustments at most.",
        best_case="Yusif gets an honest, usable reference.",
        worst_case="Missed nuances that could strengthen the case.",
        effort="S",
    ),
    "too_generous": PathDefinition(
        name="Assessment is too generous",
        description="Some scores are inflated. The weaknesses section is too soft. Real gaps aren't named.",
        best_case="Honest correction prevents credibility loss.",
        worst_case="Yusif hears things he doesn't want to hear.",
        effort="M",
    ),
    "too_harsh": PathDefinition(
        name="Assessment is too harsh or misses strengths",
        description="The CTO undervalues Yusif's contributions or frames weaknesses unfairly.",
        best_case="A more accurate, stronger recommendation emerges.",
        worst_case="Overcompensation into flattery.",
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
    safe_print(f"SWARM EVALUATES CTO's REVIEW OF CEO")
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
    for path_id in ["fair", "too_generous", "too_harsh"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        safe_print(f"  {path_id:14s} | {votes:2d} votes | {score:.1f}/50")
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

    # Save
    output_path = Path(__file__).parent / "cto_review_eval_report.json"
    output_path.write_text(json.dumps(report.model_dump(), indent=2, default=str), encoding="utf-8")

    # Summary
    lines = [
        f"# CTO Review Evaluation — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Verdict: {report.winner}",
        f"- fair: {report.divergence.winner_votes.get('fair', 0)} votes",
        f"- too_generous: {report.divergence.winner_votes.get('too_generous', 0)} votes",
        f"- too_harsh: {report.divergence.winner_votes.get('too_harsh', 0)} votes",
        f"",
        f"## Top Responses",
    ]
    detailed = sorted(
        [r for r in report.agent_results if r.json_valid and not r.error and r.reason],
        key=lambda r: len(r.reason), reverse=True,
    )[:4]
    for r in detailed:
        model_short = r.model.split("/")[-1][:25]
        lines.append(f"")
        lines.append(f"### {model_short} [{r.winner}]")
        lines.append(f"{(r.reason or '')[:800]}")

    summary_path = Path(__file__).parent / "cto_review_eval_summary.md"
    summary_path.write_text("\n".join(lines), encoding="utf-8")
    safe_print(f"\nSummary: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
