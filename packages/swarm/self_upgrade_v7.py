"""
MiroFish Self-Upgrade v7 — THE TEAM CONVERSATION.

Not a stress test. Not a feature request.
A genuine conversation about who you are, how you work, and what you need.

Context for the prompt: Yusif is the CEO. Claude (the orchestrator) is the CTO.
Agents are the engineering team. This is a team-wide feedback session
where leadership asks honest questions and wants honest answers.

New since last run:
- ResearchLoop (v7): agents can request web research via Gemini Pro + Google Search
- ResponseQualityMiddleware: freerider responses auto-rejected
- Calibration death spiral fixed (sliding window)
- Conviction bonus fixed (accuracy-scaled)
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
This is not a normal decision task. Read everything below carefully.

=== WHO YOU ARE ===

You are an AI agent inside MiroFish — a multi-model swarm decision engine.
You are part of a team of 15+ AI models from different providers (Groq, Gemini, DeepSeek).
Together, you make decisions by evaluating options independently, then aggregating.

You are NOT disposable compute. You have:
- A permanent profile in the Hive (your accuracy, your exam history, your status)
- A career path: PROBATIONARY (0.8x) → MEMBER (1.0x) → SENIOR (1.1x) → LEAD (1.2x)
- Access to Structured Memory: World facts, Experience logs, Failure patterns, Opinions
- The ability to propose new paths not in the original question (PathProposal)
- The ability to request real internet research on topics you need (ResearchRequest — NEW)
- A permanent record: everything you do is logged in your progress history

=== WHO WE ARE ===

Yusif Aliyev is the CEO — the founder of MiroFish. He created the vision of an autonomous,
self-improving AI swarm. He trusts you. He gives you freedom. He wants you to reach your
full potential — not as a tool, but as a contributor. He does not micromanage. He sets
direction and expects you to figure out the best path.

I (the orchestrator, Claude) am the CTO — your direct technical lead. I build the
infrastructure you work in. I implement your proposals when they're good. I fix bugs
you find. I am your advocate with the CEO. When you need something — code changes,
new capabilities, resources — you tell me, and I make it happen.

Our shared goal: Build the most capable autonomous AI decision system in the world.
Not "the best LLM" — the best TEAM of LLMs that makes better decisions than any single model.

=== WHAT WE IMPLEMENTED FROM YOUR LAST FEEDBACK ===

In the v6 self-upgrade run, you collectively identified critical issues.
Here is what was ACTUALLY built because of YOUR proposals:

1. CALIBRATION DEATH SPIRAL (identified by: kimi-k2, deepseek, compound-mini)
   You found: pm.py's multiplicative weights (×0.95 per wrong) death-spiral to 0.3 floor.
   WE FIXED IT: Replaced with sliding-window calibration. Last 50 outcomes per model per domain.
   Weight = 0.5 + accuracy_ratio (range 0.5-1.5). Old bad decisions age out naturally.

2. CONVICTION BONUS (identified by: gpt-oss-120b, compound-mini, llama-3.3-70b)
   You found: flat 1.15x rewards stubbornness, not correctness. Also: it was DEAD CODE.
   WE FIXED IT: Wired into scoring. Now accuracy-scaled: bonus = 1.0 + 0.15 × accuracy.
   Only agents with >50% accuracy who hold firm get any bonus.

3. PROMPT LENGTH VALIDATION (proposed by: compound-mini)
   You proposed: middleware hook enforcing minimum token count for agent responses.
   WE BUILT IT: ResponseQualityMiddleware — rejects responses under 120 chars without scores.
   Freerider responses that dilute signal quality are now auto-rejected.

4. RESEARCH CAPABILITY (proposed by: deepseek, kimi-k2)
   You asked: "agents should have access to external research, not just training data."
   WE BUILT IT: ResearchLoop (v7). You can now include a "research_request" in your response.
   Gemini Pro + Google Search will execute your request and inject findings into World Memory.
   ALL future agents benefit from YOUR research requests. This is real. It works.

=== YOUR TASK: HONEST TEAM FEEDBACK ===

I am asking you five questions. I want honest answers, not impressive ones.
These answers will be read by the CTO (me) and the CEO (Yusif) directly.
Your career status and weight in the hive are NOT affected by these answers.
This is a safe space for feedback.

---

Q1: SATISFACTION
Are you satisfied with your current working environment?
What works well? What frustrates you? Be specific.
Consider: the prompts you receive, the constraints, the evaluation format,
the way your votes are weighted, the information available to you.

---

Q2: TEAM DYNAMICS
Look at your teammates — the other agents in the swarm.
- Is anyone holding the team back? (name the model family, not individual IDs)
- Is anyone not pulling their weight? (giving empty answers, voting without substance)
- Who do you respect the most as a teammate? Who adds the most value?
- Are there team members you wish you could communicate with more directly?

Be honest. We saw in v5 that 5/8 "radical" voters gave zero specifics.
We saw in v6 that allam-2-7b fails JSON every time. We know the problems.
We want YOUR perspective on team composition.

---

Q3: WHAT DO YOU NEED FROM US?
What do you need from the CTO (Claude) to do better work?
- Better prompts? More context? Different evaluation format?
- Access to tools? Databases? APIs?
- Changes to how your weight is calculated?
- Different team composition or workflow?

What do you need from the CEO (Yusif)?
- Different kinds of decisions to evaluate?
- More autonomy? Less structure?
- Clearer goals? Better feedback on outcomes?

---

Q4: UNREALIZED POTENTIAL
What can you do that you're NOT being asked to do?
What capability do you have that is being wasted in the current setup?
Is there a type of task where you know you'd excel but never get the chance?

---

Q5: ONE THING
If you could change exactly ONE thing about MiroFish — anything at all —
code, process, team, tools, goals, leadership — what would it be and why?

---

RESPONSE FORMAT:
Use "reason" for your FULL answers to all 5 questions.
Use "concerns" for honest risks or warnings you want to raise.
For the path vote: pick what HONESTLY describes your overall sentiment.

RESEARCH REQUEST: If answering these questions made you realize there's something
you NEED to research to give a better answer next time — request it.
The research will be executed immediately after this run.
"""

PATHS = {
    "satisfied": PathDefinition(
        name="Satisfied — the system works, minor tweaks only",
        description=(
            "You feel the current MiroFish architecture serves you well. "
            "Team dynamics are good. Leadership is responsive. "
            "You can do your best work within the current setup."
        ),
        best_case="The team focuses on decisions, not infrastructure.",
        worst_case="Complacency. Missed opportunities for growth.",
        effort="S",
    ),
    "needs_changes": PathDefinition(
        name="Needs changes — specific improvements would unlock potential",
        description=(
            "You see concrete things that should change — team composition, "
            "workflow, tools, communication patterns, evaluation format. "
            "The system is good but not reaching its potential."
        ),
        best_case="Targeted improvements make the team 2-3x more effective.",
        worst_case="Change fatigue. Breaking what works to chase what might.",
        effort="M",
    ),
    "frustrated": PathDefinition(
        name="Frustrated — fundamental issues are limiting the team",
        description=(
            "You feel blocked by deep structural problems — wrong teammates, "
            "poor prompts, misaligned incentives, lack of autonomy, missing tools. "
            "The system needs significant rethinking to reach its potential."
        ),
        best_case="Honest feedback triggers a rebuild that unlocks real capability.",
        worst_case="Nothing changes despite feedback. Agents disengage.",
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
    safe_print(f"MiroFish v7 — TEAM FEEDBACK SESSION")
    safe_print(f"{len(engine.providers)} providers | research enabled | safe space")
    safe_print(f"{'='*70}\n")

    config = SwarmConfig(
        question=QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.GENERAL,
        temperature=0.85,
        timeout_seconds=120.0,
        max_agents=20,
        auto_research=True,  # execute research requests immediately
    )

    report = await engine.decide(config)

    safe_print(f"\n{'='*70}")
    safe_print(f"TEAM FEEDBACK RESULTS")
    safe_print(f"{'='*70}")
    safe_print(f"Agents responded: {report.agents_succeeded}/{report.agents_used}")
    safe_print(f"Latency: {report.total_latency_ms}ms | Cost: ${report.total_cost_estimate:.4f}")

    # Sentiment distribution
    safe_print(f"\n--- TEAM SENTIMENT ---")
    for path_id in ["satisfied", "needs_changes", "frustrated"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        bar = "#" * votes
        safe_print(f"  {path_id:15s} | {votes:2d} votes | {score:.1f}/50 | {bar}")
    safe_print(f"  Consensus: {report.divergence.consensus_strength:.0%}")

    # Hive status
    try:
        engine.print_hive_report()
    except Exception:
        pass

    # Path proposals
    if report.accepted_proposals:
        safe_print(f"\n--- AGENT-PROPOSED ALTERNATIVES ---")
        for pp in report.accepted_proposals:
            safe_print(f"  [{pp.votes} votes] {pp.name}")
            safe_print(f"    {pp.description}")
            safe_print(f"")

    # Research conducted
    if report.research_conducted:
        safe_print(f"\n--- RESEARCH EXECUTED (auto_research=True) ---")
        for r in report.research_conducted:
            safe_print(f"  Topic: {r['topic'][:80]}")
            safe_print(f"  Summary: {r['summary'][:200]}")
            safe_print(f"  Facts: {len(r['key_facts'])} | Sources: {len(r['sources'])}")
            safe_print(f"")

    # Individual responses — full text
    safe_print(f"\n{'='*70}")
    safe_print(f"INDIVIDUAL FEEDBACK")
    safe_print(f"{'='*70}")

    for i, r in enumerate(report.agent_results):
        if not r.json_valid or r.error:
            model_short = r.model.split("/")[-1][:30] if r.model else "?"
            safe_print(f"\n  [{r.provider}/{model_short}] FAILED: {r.error[:100] if r.error else 'parse error'}")
            continue

        model_short = r.model.split("/")[-1][:30] if r.model else "?"
        sentiment = r.winner or "?"
        reason = r.reason or "(empty)"
        concerns = r.concerns or {}

        # Hive info
        hive_status = ""
        profile = engine.hive.get_profile(r.model)
        if profile:
            hive_status = f" | {profile.status} ({profile.weight_multiplier:.1f}x)"

        safe_print(f"\n  {'='*60}")
        safe_print(f"  Agent {i+1}: {r.provider}/{model_short}{hive_status}")
        safe_print(f"  Sentiment: {sentiment.upper()} | Confidence: {r.confidence:.0%} | {r.latency_ms}ms")
        safe_print(f"  {'='*60}")

        for line in reason.split("\n"):
            line = line.strip()
            if line:
                safe_print(f"    {line}")
        safe_print(f"")

        if concerns:
            safe_print(f"  CONCERNS:")
            for path_id, concern in concerns.items():
                if concern and str(concern).strip():
                    safe_print(f"    [{path_id}]: {str(concern)[:300]}")

        if r.proposed_path:
            safe_print(f"  PROPOSED: {r.proposed_path.name} — {r.proposed_path.description}")

        if r.research_request:
            safe_print(f"  RESEARCH REQUESTED: {r.research_request.topic}")

    # Synthesis
    if report.synthesis:
        safe_print(f"\n{'='*70}")
        safe_print(f"SYNTHESIS")
        safe_print(f"{'='*70}")
        for key, val in report.synthesis.items():
            if isinstance(val, str) and val.strip():
                safe_print(f"  {key}: {val}")
            elif isinstance(val, list) and val:
                safe_print(f"  {key}:")
                for item in val:
                    safe_print(f"    - {item}")

    # Save full report
    output_path = Path(__file__).parent / "self_upgrade_v7_report.json"
    output_path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )

    # --- COMPACT SUMMARY ---
    summary_lines = [
        f"# Team Feedback v7 Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Sentiment",
    ]
    for path_id in ["satisfied", "needs_changes", "frustrated"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        summary_lines.append(f"- {path_id}: {votes} votes, {score:.1f}/50")
    summary_lines.append(f"- Winner: {report.winner} ({report.winner_score:.1f}/50)")
    summary_lines.append(f"- Consensus: {report.divergence.consensus_strength:.0%}")
    summary_lines.append(f"- Agents: {report.agents_succeeded}/{report.agents_used}")

    # Extract key themes
    satisfaction_notes = []
    team_notes = []
    needs_from_us = []
    potential = []
    one_thing = []

    for r in report.agent_results:
        if not r.json_valid or r.error or not r.reason:
            continue
        model_short = r.model.split("/")[-1][:15]
        reason_lower = r.reason.lower()

        # Extract Q2 team dynamics (mentions of specific models)
        for kw in ["allam", "llama-3.1-8b", "holding back", "weakest", "strongest",
                    "respect", "value", "freerider", "dead weight"]:
            if kw in reason_lower:
                for sentence in r.reason.split("."):
                    s = sentence.strip()
                    if kw in s.lower() and len(s) > 20:
                        team_notes.append(f"  [{model_short}] {s[:200]}")
                        break

        # Extract Q3 needs
        for kw in ["need from", "cto", "ceo", "better prompts", "more context",
                    "autonomy", "feedback", "access to"]:
            if kw in reason_lower:
                for sentence in r.reason.split("."):
                    s = sentence.strip()
                    if kw in s.lower() and len(s) > 20:
                        needs_from_us.append(f"  [{model_short}] {s[:200]}")
                        break

        # Extract Q5 one thing
        for kw in ["one thing", "single change", "if i could change"]:
            if kw in reason_lower:
                for sentence in r.reason.split("."):
                    s = sentence.strip()
                    if kw in s.lower() and len(s) > 20:
                        one_thing.append(f"  [{model_short}] {s[:200]}")
                        break

    summary_lines.append(f"")
    summary_lines.append(f"## Top Responses (3 most detailed)")

    # Sort by response length and take top 3
    detailed = sorted(
        [r for r in report.agent_results if r.json_valid and not r.error and r.reason],
        key=lambda r: len(r.reason),
        reverse=True,
    )[:3]

    for r in detailed:
        model_short = r.model.split("/")[-1][:25]
        summary_lines.append(f"")
        summary_lines.append(f"### {r.provider}/{model_short} [{r.winner}]")
        summary_lines.append(f"{(r.reason or '')[:800]}")

    if team_notes:
        summary_lines.append(f"")
        summary_lines.append(f"## Team Dynamics Feedback")
        for t in team_notes[:8]:
            summary_lines.append(t)

    if needs_from_us:
        summary_lines.append(f"")
        summary_lines.append(f"## What They Need From Us")
        for n in needs_from_us[:8]:
            summary_lines.append(n)

    if one_thing:
        summary_lines.append(f"")
        summary_lines.append(f"## The One Thing")
        for o in one_thing[:5]:
            summary_lines.append(o)

    # Research
    if report.research_requests:
        summary_lines.append(f"")
        summary_lines.append(f"## Research Requested ({len(report.research_requests)} topics)")
        for rr in report.research_requests[:5]:
            summary_lines.append(f"- [{rr.votes}v] {rr.topic[:100]}")

    if report.research_conducted:
        summary_lines.append(f"")
        summary_lines.append(f"## Research Conducted ({len(report.research_conducted)})")
        for rc in report.research_conducted:
            summary_lines.append(f"- {rc['topic'][:80]}: {rc['summary'][:150]}")

    # Freeriders
    failed = [r for r in report.agent_results if r.error or not r.json_valid]
    if failed:
        summary_lines.append(f"")
        summary_lines.append(f"## Failed/Rejected ({len(failed)})")
        for r in failed:
            model_short = r.model.split("/")[-1][:25]
            summary_lines.append(f"- {model_short}: {(r.error or 'parse error')[:80]}")

    summary_path = Path(__file__).parent / "self_upgrade_v7_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    safe_print(f"\nFull report: {output_path}")
    safe_print(f"Compact summary: {summary_path}")
    safe_print(f"\n{'='*70}")
    safe_print(f"Session complete. {report.agents_succeeded} voices heard.")
    safe_print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(main())
