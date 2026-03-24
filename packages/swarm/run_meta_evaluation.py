"""
Meta-evaluation: Agent team efficiency + Yusif CEO self-assessment.
Yusif asked: "Is my agent workflow optimal? Am I slowing the team down?"
Run: python -m packages.swarm.run_meta_evaluation
"""
import asyncio
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

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
        question="""META-EVALUATION: Evaluate the effectiveness of this human-AI team.

TEAM STRUCTURE:
- Yusif Ganbarov (CEO/Founder): Non-technical. ADHD. Makes all strategic decisions.
  Manages Claude (CTO AI) + MiroFish swarm (13 AI models as evaluators).
  Catches process violations that Claude misses. Redirects when Claude goes off-track.
  BUT: sometimes sends 10+ topics in a single message. Sometimes pivots mid-sprint.
  Self-question: "Am I slowing the team? What can I do better?"

- Claude (CTO AI, Anthropic Sonnet/Opus): Does ALL coding, architecture, planning, docs.
  Has 18 documented mistakes. Consistently skips process (~30% compliance).
  Good at: code, architecture, multi-model orchestration.
  Bad at: following own protocols, validating work before shipping, saving state.

- MiroFish Swarm (13 LLM models): Evaluates decisions, content, architecture, code.
  Used for: business roadmap, LinkedIn content, architecture audit, letter evaluation, Yusif's professional review.
  NOT yet used for: sprint planning, frontend tests, SQL validation (mistake #18).
  Models: Gemini 2.5 Flash, Groq Llama 3.3 70B, DeepSeek V3, Kimi-K2, GPT-OSS-120B, + 8 others.

SESSION STATS (14 sessions over 2 days):
- Code: 9 routers, 31 endpoints, IRT/CAT engine, BARS evaluator, anti-gaming
- Frontend: 27 pages, 40+ components, 17 hooks
- Tests: 74 backend tests, 0 frontend tests
- Security fixes: 7 P0/P1 vulnerabilities fixed
- Agent evaluations run: 5 (business, Yusif review, LinkedIn, architecture, letter)
- Documented mistakes: 18
- Protocol compliance: ~30%

QUESTION TO EVALUATE:
1. Is the agent workflow (Claude + MiroFish swarm) efficient or could it be better?
2. Is Yusif slowing the team down or accelerating it?
3. What specific changes would make this team 2x more productive?
4. Rate Yusif as CEO of an AI-first startup (not just this project).

Which verdict best describes the team dynamic?""",

        paths={
            "yusif_accelerates": PathDefinition(
                name="Yusif is a net accelerator — team is faster WITH him",
                description="His interventions (catching mistakes, redirecting, demanding agent validation) save more time than his pivots cost. ADHD-driven multithreading is a feature, not a bug. The team's biggest problem is Claude's process compliance, not Yusif's management.",
                best_case="Team velocity doubles when Yusif focuses. His catches prevent catastrophic mistakes.",
                worst_case="Some wasted cycles on topic pivots, but net positive.",
                effort="N/A — keep current dynamic, fix Claude's compliance",
            ),
            "yusif_bottleneck": PathDefinition(
                name="Yusif is a bottleneck — too many pivots, not enough focus",
                description="10-topic messages fragment Claude's attention. Mid-sprint pivots waste completed work. ADHD-driven multithreading causes context switching overhead. Team would be faster if Yusif batched requests.",
                best_case="With discipline, 3x improvement. Batch messages, single-topic sessions.",
                worst_case="Yusif feels constrained. Loses the creative spark that generates novel ideas.",
                effort="Yusif changes communication style",
            ),
            "claude_problem": PathDefinition(
                name="The problem is Claude, not Yusif — CTO at 30% compliance is the bottleneck",
                description="18 mistakes in 14 sessions. 30% protocol compliance. Doesn't validate SQL before giving to CEO. Doesn't run agents on architecture. The swarm exists but Claude doesn't use it. Fix Claude's execution, not Yusif's management.",
                best_case="Claude reaches 80%+ compliance → mistakes drop 5x → Yusif trusts more → less micromanagement.",
                worst_case="Claude can't be fixed (model limitation). Need human CTO.",
                effort="Claude needs architectural constraints, not behavioral ones",
            ),
            "workflow_redesign": PathDefinition(
                name="The whole workflow needs redesign — current structure is ad-hoc",
                description="The team grew organically. No clear handoff protocol between Yusif→Claude→Agents. Agents are used reactively (after mistakes) not proactively (before decisions). Needs: structured sprint cycles, agent gates at every decision point, Yusif as product owner not ad-hoc director.",
                best_case="Professional engineering team dynamics. 3-5x velocity. Pasha Bank demo ready in 1 sprint.",
                worst_case="Over-engineering the process kills the startup energy.",
                effort="1 session to redesign workflow, 3 sessions to internalize",
            ),
        },

        stakes=StakesLevel.HIGH,
        domain=DomainTag.BUSINESS,
        context="An AI-first startup team (1 human + 1 AI CTO + 13 AI evaluators) building Volaura. The human CEO asks: am I slowing my team down? The AI CTO has 18 documented mistakes. Be brutally honest.",
        constraints="Do NOT be sycophantic. Do NOT protect Yusif's feelings. Do NOT blame only Claude. Give specific, actionable recommendations.",
        timeout=60,
    )

    print("\n" + "="*70)
    print("META-EVALUATION: Team Efficiency + CEO Assessment")
    print("="*70 + "\n")

    report = await engine.decide(config)

    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"\nVerdict: {report.winner}")
    print(f"Score: {report.winner_score}/50")
    consensus = getattr(report, 'consensus_pct', None) or (getattr(report.divergence, 'consensus_strength', 0) if report.divergence else 0)
    print(f"Consensus: {consensus}")
    print(f"Agents: {len(report.agent_results)}")

    if report.synthesis:
        print(f"\nSynthesis:\n{report.synthesis}")

    print("\n--- Agent Votes ---")
    for r in sorted(report.agent_results, key=lambda x: x.confidence, reverse=True):
        print(f"  {r.model:30s} → {r.winner:30s} (confidence: {r.confidence:.1f})")

    print("\n--- Innovations (specific recommendations) ---")
    for r in report.agent_results:
        innov = r.innovation
        if not innov:
            try:
                raw = json.loads(r.raw_response) if r.raw_response else {}
                innov = raw.get("innovation", "")
            except Exception:
                pass
        if innov and innov not in ("null", ""):
            print(f"  [{r.model}]: {innov}")

    # Save
    output_path = Path(__file__).parent / "meta_evaluation_result.json"
    innovations = {}
    for r in report.agent_results:
        innov = r.innovation
        if not innov:
            try:
                raw = json.loads(r.raw_response) if r.raw_response else {}
                innov = raw.get("innovation", "")
            except Exception:
                pass
        if innov and innov not in ("null", ""):
            innovations[r.model] = innov

    output_data = {
        "verdict": report.winner,
        "score": report.winner_score,
        "consensus": consensus,
        "agents": len(report.agent_results),
        "votes": {r.model: r.winner for r in report.agent_results},
        "innovations": innovations,
        "synthesis": str(report.synthesis) if report.synthesis else "",
    }
    output_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
