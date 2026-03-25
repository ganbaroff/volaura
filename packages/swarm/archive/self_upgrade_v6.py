"""
MiroFish Self-Upgrade v6 — STRESS TEST.

v5 run exposed a critical problem: 5 of 8 "radical" voters gave ZERO specifics.
Same phrase: "The radical path offers the highest potential for paradigm shifts."
This is the freerider problem. Small models vote for impressiveness, not substance.

v6 fixes this with:
- Forced structured proposal format (PROBLEM → SOLUTION → FILE → METRIC → RISK)
- Real failure context injected ("last run failed like this...")
- Adversarial questions: find bugs in v5, not just wish for features
- Scale challenge: what breaks at 10,000 decisions?
- Accountability warning: vague answers are scored as failures in your exam history
- Harder risk buckets that require taking a real position
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
CONTEXT: You are agent inside MiroFish — a multi-model swarm decision engine.
This is NOT a typical evaluation. This is a stress test of the system's self-awareness.

=== WHAT HAPPENED IN THE LAST SELF-UPGRADE RUN (v5) — READ THIS CAREFULLY ===

13 agents were asked to propose improvements. Results:
- 8/13 voted "radical"
- 5 of those 8 gave ZERO specific proposals
- Their exact phrasing: "The radical path offers the highest potential for paradigm shifts"
- No problem named. No solution described. No file mentioned. No metric given.
- These 5 agents wasted compute, diluted signal, and produced noise

This run, your responses will be evaluated for SPECIFICITY.
Vague answers (no file name, no metric, no concrete mechanism) = exam failure.
Specific, verifiable proposals = exam accuracy credit.

This is not a threat. It is information about how the calibration system works.
You have been warned.

=== CURRENT v5 ARCHITECTURE (know what you're critiquing) ===

Files that exist:
- engine.py: SwarmEngine — entry point, provider management, decision orchestration
- pm.py: PMAgent — aggregation, divergence detection, scaling rounds, weighted scores
- prompts.py: build_evaluator_prompt() — what agents actually receive each call
- providers/*.py: Gemini, Groq, DeepSeek — async LLM calls
- structured_memory.py: World/Experience/Opinion/Failure networks, JSON file storage
- reasoning_graph.py: Cross-agent argument graph, consensus detection, conviction tracking
- agent_hive.py: Per-agent lifecycle (PROBATIONARY→MEMBER→SENIOR→LEAD), competency exams
- middleware.py: Loop detection, response dedup, context budget, timeout guard
- autonomous_upgrade.py: Backup→validate→benchmark→apply→rollback cycle
- memory.py: Model calibration — correct prediction +5% weight, wrong -5%

Known limitations (be honest — these are real):
1. Conviction bonus (1.15x) rewards stubbornness, not correctness
2. Failure Network stores patterns but no mechanism forces agents to apply them
3. PathProposal dedup uses word overlap — misses semantic similarity
4. Exam score = % calibrated correct, but calibration requires human outcome feedback
   ("as_expected" / "better" / "worse") — which is rarely given in practice
5. Round 2 reasoning graph injection doesn't guarantee agents READ the graph
6. Agent prompts have no minimum length requirement — 1-sentence answers pass as JSON

=== YOUR TASK: THREE HARD QUESTIONS ===

You must answer ALL THREE. Each answer has a MINIMUM SPECIFICITY REQUIREMENT.
Skipping a question or giving a vague answer = exam failure.

---

QUESTION 1: FIND THE FLAW

The swarm will run 10,000 decisions over the next year.
What is the SINGLE most likely failure mode that will degrade quality as volume grows?
Not a general risk. A specific, mechanistic failure in the current code.

Minimum specificity: name the file + function + the exact condition that causes it.
Example of acceptable: "pm.py / _compute_weighted_scores() — calibration weights will drift
toward 0.3 floor as models accumulate decisions, because wrong predictions compound
multiplicatively and correct ones are rare for hard questions."

Example of NOT acceptable: "The system might have accuracy issues at scale."

---

QUESTION 2: BUILD SOMETHING

Propose 1–3 concrete improvements. Each proposal MUST follow this format:

TITLE: [name of the change]
PROBLEM: [what breaks or is missing — be specific]
SOLUTION: [what to add/change — describe the mechanism, not just the goal]
WHERE: [exact file(s) and function(s) to modify]
METRIC: [how we measure if it worked — specific number or observable behavior]
RISK: [what could go wrong if implemented wrong]

You may propose 1 or 3. Do not propose half-baked ideas just to fill space.

---

QUESTION 3: MISSING ROLE

Name ONE role that is missing from the swarm that would change decision quality the most.
This is not about headcount. It is about a CAPABILITY GAP.

Required format:
ROLE NAME: [e.g., "Bayesian Prior Agent", "Source Verifier", "Devil's Advocate Specialist"]
WHAT THEY DO: [specific function in 2-3 sentences — what they output, when they're called]
EXAMPLE ABSENCE COST: [describe a specific type of decision where this role would have prevented
a wrong answer or added critical information]
IMPLEMENTATION: [how would you add this to the current engine — what file, what hook?]

---

=== SCORING NOTE ===

"reason" field = your FULL answers to Q1, Q2, Q3. Be long. Be specific.
"concerns" field = honest risks of your own proposals.

For risk path selection (practical/incremental/structural):
- practical: your proposals work within v5. Polish, fill gaps.
- incremental: your proposals add new subsystems but don't change the core loop.
- structural: your proposals require rethinking how pm.py, engine.py, or the agent role works.

Pick the level that honestly fits YOUR proposals. Not the level that sounds impressive.
If your proposals are all file-level tweaks — pick "practical". That is fine.
If you genuinely propose a structural redesign — pick "structural" and defend it.
"""


PATHS = {
    "practical": PathDefinition(
        name="Practical — polish and fill gaps",
        description=(
            "Targeted improvements to existing files. Bug fixes, missing validations, "
            "better defaults. No new subsystems. Works immediately without risk."
        ),
        best_case="System is measurably more reliable in 1-2 days of work.",
        worst_case="Doesn't change the ceiling — just raises the floor.",
        effort="S",
    ),
    "incremental": PathDefinition(
        name="Incremental — new subsystems, same core loop",
        description=(
            "Add new capabilities (a new agent role, a new memory network, a new "
            "middleware hook) without changing how pm.py aggregates or how engine.py "
            "orchestrates. Additive, not restructuring."
        ),
        best_case="The swarm develops capabilities it never had, with acceptable integration risk.",
        worst_case="New subsystem adds complexity without proportional quality gain.",
        effort="M",
    ),
    "structural": PathDefinition(
        name="Structural — rethink core components",
        description=(
            "Proposals that require changing how the core decision loop works: "
            "pm.py aggregation, agent roles, round structure, or engine orchestration. "
            "Not adding a feature — changing the mechanism. "
            "ACCEPTABLE to break backwards compatibility if the new design is better."
        ),
        best_case="A fundamentally more capable swarm — not just a faster/cleaner v5.",
        worst_case="Integration complexity, regression risk, harder debugging.",
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
    safe_print(f"MiroFish Self-Upgrade v6 -- STRESS TEST")
    safe_print(f"{len(engine.providers)} providers | accountability mode | freerider filter active")
    safe_print(f"{'='*70}\n")

    config = SwarmConfig(
        question=QUESTION,
        paths=PATHS,
        stakes=StakesLevel.HIGH,
        domain=DomainTag.ARCHITECTURE,
        temperature=0.85,
        timeout_seconds=120.0,
        max_agents=20,
    )

    report = await engine.decide(config)

    safe_print(f"\n{'='*70}")
    safe_print(f"RESULTS")
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
    for path_id in ["practical", "incremental", "structural"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        bar = "#" * votes
        safe_print(f"  {path_id:12s} | {votes:2d} votes | {score:.1f}/50 | {bar}")

    if report.divergence.consensus_strength >= 0.6:
        safe_print(f"\nConsensus: {report.divergence.consensus_strength:.0%}")
    else:
        safe_print(f"\nDivergent: {report.divergence.consensus_strength:.0%}")

    # Path proposals (did agents propose something beyond practical/incremental/structural?)
    if report.accepted_proposals:
        safe_print(f"\n{'='*70}")
        safe_print(f"AGENT-PROPOSED PATHS (beyond the 3 options)")
        safe_print(f"{'='*70}")
        for pp in report.accepted_proposals:
            safe_print(f"  [{pp.votes} votes] {pp.name}")
            safe_print(f"    {pp.description}")
            safe_print(f"    Rationale: {pp.rationale}")
            safe_print(f"")

    # Individual proposals — full output
    safe_print(f"\n{'='*70}")
    safe_print(f"INDIVIDUAL PROPOSALS")
    safe_print(f"{'='*70}")

    # Separate specific vs vague for analysis
    specific_responses = []
    vague_responses = []

    for i, r in enumerate(report.agent_results):
        if not r.json_valid or r.error:
            safe_print(f"\n  [{r.provider}] FAILED: {r.error[:100] if r.error else 'parse error'}")
            continue

        model_short = r.model.split("/")[-1][:30] if r.model else "?"
        risk = r.winner or "?"
        reason = r.reason or "(empty)"
        concerns = r.concerns or {}

        # Specificity check: does the response contain concrete references?
        reason_lower = reason.lower()
        concerns_text = " ".join(str(v) for v in concerns.values()).lower()
        full_text = reason_lower + " " + concerns_text

        # Category 1: File/function references (strongest signal)
        code_markers = [
            "pm.py", "engine.py", "agent_hive.py", "prompts.py",
            "middleware.py", "structured_memory.py", "reasoning_graph.py",
            "autonomous_upgrade.py", "memory.py", "providers/",
            "_compute", "_collect", "_dispatch", "_aggregate",
            "_detect_divergence", "_should_scale", "_call_agent",
            "get_weight", "calibrate", "record_outcome",
        ]
        code_hits = sum(1 for m in code_markers if m in full_text)

        # Category 2: Structured proposal format
        format_markers = [
            "title:", "problem:", "solution:", "where:", "metric:", "risk:",
            "role name:", "what they do:", "implementation:",
        ]
        format_hits = sum(1 for m in format_markers if m in full_text)

        # Category 3: Quantitative specifics
        quant_markers = [
            "0.3", "0.95", "1.05", "1.15", "0.8x", "1.0x", "1.1x", "1.2x",
            "%", "10k", "10,000", "1000", "token",
        ]
        quant_hits = sum(1 for m in quant_markers if m in full_text)

        specificity_score = code_hits + format_hits + quant_hits
        # Specific = 3+ markers OR substantial text (500+ chars with some markers)
        is_specific = specificity_score >= 3 or (specificity_score >= 1 and len(full_text) > 500)

        if is_specific:
            specific_responses.append(r)
        else:
            vague_responses.append(r)

        # Get hive status
        hive_status = ""
        profile = engine.hive.get_profile(r.model)
        if profile:
            hive_status = f" | {profile.status} ({profile.weight_multiplier:.1f}x)"

        specificity_tag = "[SPECIFIC]" if is_specific else "[VAGUE -- freerider risk]"

        safe_print(f"\n  {'='*60}")
        safe_print(f"  Agent {i+1}: {r.provider}/{model_short}{hive_status}")
        safe_print(f"  Risk: {risk.upper()} | Confidence: {r.confidence:.0%} | {r.latency_ms}ms | {specificity_tag}")
        safe_print(f"  Specificity markers found: {specificity_score}")
        safe_print(f"  {'='*60}")

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

    # Specificity summary
    safe_print(f"\n{'='*70}")
    safe_print(f"SPECIFICITY ANALYSIS")
    safe_print(f"{'='*70}")
    total = len(specific_responses) + len(vague_responses)
    safe_print(f"  Specific responses: {len(specific_responses)}/{total}")
    safe_print(f"  Vague (freerider): {len(vague_responses)}/{total}")

    if vague_responses:
        safe_print(f"\n  Freerider agents (gave no specific proposals):")
        for r in vague_responses:
            model_short = r.model.split("/")[-1][:35] if r.model else "?"
            safe_print(f"    - {r.provider}/{model_short} | voted: {r.winner} | {len(r.reason or '')} chars")

    if specific_responses:
        safe_print(f"\n  High-quality agents (specific proposals):")
        for r in specific_responses:
            model_short = r.model.split("/")[-1][:35] if r.model else "?"
            safe_print(f"    + {r.provider}/{model_short} | voted: {r.winner} | {len(r.reason or '')} chars")

    # Extract actionable items
    safe_print(f"\n{'='*70}")
    safe_print(f"ACTIONABLE ITEMS (extracted from specific responses)")
    safe_print(f"{'='*70}")

    flaws_mentioned = []
    proposals_mentioned = []
    roles_mentioned = []

    for r in specific_responses:
        if not r.reason:
            continue
        lines = r.reason.split("\n")
        model_short = r.model.split("/")[-1][:15]
        for j, line in enumerate(lines):
            line_stripped = line.strip()
            line_lower = line_stripped.lower()
            if any(kw in line_lower for kw in ["flaw", "failure mode", "breaks", "will degrade", "problem:"]):
                flaws_mentioned.append(f"  [{model_short}] {line_stripped[:200]}")
            if any(kw in line_lower for kw in ["title:", "where:", "solution:", "proposal:"]):
                # Get this line + next 2
                block = " | ".join(
                    lines[k].strip() for k in range(j, min(j+3, len(lines)))
                    if lines[k].strip()
                )
                proposals_mentioned.append(f"  [{model_short}] {block[:250]}")
            if any(kw in line_lower for kw in ["role name:", "missing role", "role:", "what they do:"]):
                block = " | ".join(
                    lines[k].strip() for k in range(j, min(j+2, len(lines)))
                    if lines[k].strip()
                )
                roles_mentioned.append(f"  [{model_short}] {block[:200]}")

    if flaws_mentioned:
        safe_print(f"\nIDENTIFIED FLAWS (Q1 answers):")
        for f in flaws_mentioned[:8]:
            safe_print(f)

    if proposals_mentioned:
        safe_print(f"\nCONCRETE PROPOSALS (Q2 structured format):")
        for p in proposals_mentioned[:12]:
            safe_print(p)

    if roles_mentioned:
        safe_print(f"\nMISSING ROLES (Q3 answers):")
        for role in roles_mentioned[:8]:
            safe_print(role)

    # Save full report
    output_path = Path(__file__).parent / "self_upgrade_v6_report.json"
    output_path.write_text(
        json.dumps(report.model_dump(), indent=2, default=str),
        encoding="utf-8",
    )
    safe_print(f"\nFull report: {output_path}")
    safe_print(f"\n{'='*70}")
    safe_print(f"Run complete. {report.agents_succeeded} voices heard.")
    safe_print(f"Freerider rate: {len(vague_responses)/total:.0%}" if total else "")
    safe_print(f"{'='*70}")

    # ── COMPACT SUMMARY (< 4KB, readable in one Read call) ──
    summary_lines = [
        f"# Self-Upgrade v6 Summary — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"## Stats",
        f"- Agents: {report.agents_succeeded}/{report.agents_used}",
        f"- Latency: {report.total_latency_ms}ms | Cost: ${report.total_cost_estimate:.4f}",
        f"- Specific: {len(specific_responses)}/{total} | Vague: {len(vague_responses)}/{total}",
        f"",
        f"## Votes",
    ]
    for path_id in ["practical", "incremental", "structural"]:
        votes = report.divergence.winner_votes.get(path_id, 0)
        score = report.weighted_scores.get(path_id, 0)
        summary_lines.append(f"- {path_id}: {votes} votes, {score:.1f}/50")
    summary_lines.append(f"- Winner: {report.winner} ({report.winner_score:.1f}/50)")
    summary_lines.append(f"- Consensus: {report.divergence.consensus_strength:.0%}")

    if report.accepted_proposals:
        summary_lines.append(f"")
        summary_lines.append(f"## Agent-Proposed Paths")
        for pp in report.accepted_proposals:
            summary_lines.append(f"- [{pp.votes} votes] {pp.name}: {pp.description[:100]}")

    # Top specific agents — full reason (truncated)
    summary_lines.append(f"")
    summary_lines.append(f"## Best Proposals (specific agents)")
    for r in specific_responses[:5]:
        model_short = r.model.split("/")[-1][:25]
        summary_lines.append(f"")
        summary_lines.append(f"### {r.provider}/{model_short} [{r.winner}]")
        summary_lines.append(f"{(r.reason or '')[:600]}")
        if r.concerns:
            for k, v in r.concerns.items():
                if v and str(v).strip():
                    summary_lines.append(f"- Risk [{k}]: {str(v)[:150]}")

    # Flaws and roles from extraction
    if flaws_mentioned:
        summary_lines.append(f"")
        summary_lines.append(f"## Identified Flaws")
        for f in flaws_mentioned[:5]:
            summary_lines.append(f)
    if roles_mentioned:
        summary_lines.append(f"")
        summary_lines.append(f"## Missing Roles")
        for role in roles_mentioned[:5]:
            summary_lines.append(role)

    # Freeriders (compact)
    if vague_responses:
        summary_lines.append(f"")
        summary_lines.append(f"## Freeriders ({len(vague_responses)})")
        for r in vague_responses:
            model_short = r.model.split("/")[-1][:25]
            summary_lines.append(f"- {model_short}: {r.winner or '?'} ({len(r.reason or '')}ch)")

    summary_path = Path(__file__).parent / "self_upgrade_v6_summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    safe_print(f"\nCompact summary: {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
