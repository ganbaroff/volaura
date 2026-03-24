"""
Universal evaluator prompt builder - domain-agnostic.
Generates structured prompts for any decision, any LLM.

v7: Modular prompt system. Instead of hardcoded architecture context,
prompts load live state from prompt_modules/ directory:
  - team_identity.md: stable (who we are, rules, leadership)
  - architecture_state.md: auto-updated (current files, providers, numbers)
  - current_gaps.md: auto-updated (what's missing, reference repos)

Research-backed design:
- ACL 2025: answer diversity > protocol choice. Sub-perspectives maximize diversity.
- MoA: synthesis > selection. Final synthesis prompt included.
- ICML 2024: debate with targeted correction works for heterogeneous agents.
"""

from __future__ import annotations

import random
from pathlib import Path

from .types import SwarmConfig


# ── Modular prompt loading ──────────────────────────
_MODULES_DIR = Path(__file__).parent / "prompt_modules"


def load_prompt_module(name: str) -> str:
    """Load a prompt module file. Returns empty string if not found."""
    path = _MODULES_DIR / name
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def get_team_context() -> str:
    """Load full team context from modules (identity + architecture + gaps)."""
    identity = load_prompt_module("team_identity.md")
    architecture = load_prompt_module("architecture_state.md")
    gaps = load_prompt_module("current_gaps.md")

    parts = []
    if identity:
        parts.append(identity)
    if architecture:
        parts.append(architecture)
    if gaps:
        parts.append(gaps)
    return "\n\n---\n\n".join(parts)

# Each group topic has 3 sub-perspectives for diversity within the group
GROUP_PERSPECTIVES: dict[str, list[tuple[str, str]]] = {
    "security": [
        ("attacker", "Find OWASP vulnerabilities. How would you exploit this?"),
        ("victim", "What user data leaks if this is breached? What's the blast radius?"),
        ("auditor", "Does this meet compliance standards? What's missing from defense?"),
    ],
    "cost": [
        ("bootstrapper", "How to do this for $0? What free alternatives exist?"),
        ("accountant", "Total cost over 12 months including hidden costs and maintenance?"),
        ("investor", "What's the ROI? Is this spend generating value or burning runway?"),
    ],
    "ux": [
        ("new_user", "Can I figure this out in 30 seconds without a tutorial?"),
        ("power_user", "Does this scale to my daily workflow? What's missing for pros?"),
        ("accessibility", "Screen reader? Keyboard nav? Color blind? Slow connection?"),
    ],
    "speed": [
        ("pragmatist", "What ships in 1 day? Cut everything non-essential."),
        ("architect", "Will this quick solution create 2x rework later?"),
        ("parallel", "What can we do simultaneously? Where's the critical path?"),
    ],
    "scalability": [
        ("load_tester", "What breaks at 10x users? Where's the first bottleneck?"),
        ("data_architect", "Will the schema support this at scale? Missing indexes?"),
        ("ops", "Can this be deployed, monitored, and rolled back in 1 command?"),
    ],
    "quality": [
        ("tester", "What edge cases break this? What's NOT tested that should be?"),
        ("reviewer", "Does this follow existing patterns? Is the code maintainable?"),
        ("pessimist", "What can go wrong that nobody's thinking about?"),
    ],
}

# Flat list for when no group structure is used
FLAT_PERSPECTIVES = [
    ("pragmatist", "What's the fastest way to ship this and move on?"),
    ("pessimist", "What can go wrong? Find the hidden failure mode."),
    ("security", "How can this be exploited or abused? Attack vectors."),
    ("scalability", "What breaks at 10x? Where are the bottlenecks?"),
    ("user", "What does the end user actually experience? Pain points?"),
    ("cost", "What's the total cost - money, time, opportunity cost?"),
    ("maintainability", "Will we regret this in 6 months? Technical debt?"),
    ("contrarian", "Argue AGAINST the obvious winner. Why is it actually wrong?"),
]


def _is_small_model(model_name: str) -> bool:
    """Detect small models that need shorter prompts to perform well.

    Small models (< 20B params) struggle with long prompts:
    - They lose focus on the actual question
    - JSON compliance drops with prompt length
    - They're better at direct, focused tasks

    v7: requested by compound-mini, kimi-k2-0905 in team feedback.
    """
    small_markers = ["8b", "7b", "2b", "1b", "4b", "mini", "lite", "scout-17b"]
    name_lower = model_name.lower()
    return any(m in name_lower for m in small_markers)


def build_evaluator_prompt(
    config: SwarmConfig,
    agent_id: str,
    perspective: str | None = None,
    perspective_desc: str | None = None,
    agent_memory_context: str = "",
    group_name: str = "",
    model_name: str = "",
) -> str:
    """Build a universal evaluation prompt for any decision.

    Supports: skill injection (via SkillLibrary.inject_into_prompt after),
    agent memory, group context, innovation field, and model-adaptive length.

    v7: small models (< 20B) get a compressed prompt that focuses on scoring.
    Large models (70B+) get full context with memory and research instructions.
    """

    if not perspective:
        p = random.choice(FLAT_PERSPECTIVES)
        perspective, perspective_desc = p[0], p[1]
    elif not perspective_desc:
        for name, desc in FLAT_PERSPECTIVES:
            if name == perspective:
                perspective_desc = desc
                break
        else:
            perspective_desc = perspective

    # Build paths section
    if config.paths:
        paths_text = "\n\n".join(
            f"PATH {pid.upper()} - {p.name}:\n"
            f"  Description: {p.description}\n"
            + (f"  Best case: {p.best_case}\n" if p.best_case else "")
            + (f"  Worst case: {p.worst_case}\n" if p.worst_case else "")
            + (f"  Effort: {p.effort}" if p.effort else "")
            for pid, p in config.paths.items()
        )
        path_ids = list(config.paths.keys())
        scores_template = ",\n    ".join(
            f'"{pid}": {{"technical": 0, "user_impact": 0, "dev_speed": 0, "flexibility": 0, "risk": 0}}'
            for pid in path_ids
        )
        concerns_template = ",\n    ".join(
            f'"{pid}": "specific concern"' for pid in path_ids
        )
    else:
        paths_text = (
            "No predefined paths. First generate 3-4 alternative approaches, "
            "then evaluate each one."
        )
        scores_template = '"path_a": {"technical": 0, "user_impact": 0, "dev_speed": 0, "flexibility": 0, "risk": 0}'
        concerns_template = '"path_a": "specific concern"'

    context_block = f"\nCONTEXT: {config.context}" if config.context else ""
    constraints_block = f"\nCONSTRAINTS: {config.constraints}" if config.constraints else ""

    group_line = f"\nGROUP: {group_name} (you are in a specialized group)" if group_name else ""
    memory_block = f"\n{agent_memory_context}" if agent_memory_context else ""

    # v7: Small models get focused prompt (no optional sections that confuse them)
    small = _is_small_model(model_name) if model_name else False

    if small:
        return f"""Evaluate this decision. Respond with valid JSON only.

PERSPECTIVE: {perspective} - {perspective_desc}

DECISION: {config.question}
{context_block}{constraints_block}

PATHS:
{paths_text}

SCORING: Score each path 0-10 on: technical, user_impact, dev_speed, flexibility, risk.
risk: 0=dangerous, 10=safe. Pick the winner you believe is best. Write one concern per path.

JSON response:
{{
  "evaluator": "{agent_id}",
  "perspective": "{perspective}",
  "scores": {{ {scores_template} }},
  "concerns": {{ {concerns_template} }},
  "winner": "path_id",
  "reason": "why this path wins with specific evidence",
  "confidence": 0.0,
  "proposed_path": null,
  "research_request": null,
  "innovation": "one creative idea",
  "skill_used": null,
  "skill_helpful": true,
  "skill_gap": null,
  "self_note": "what I learned"
}}"""

    # Full prompt for large models (70B+, kimi-k2, deepseek, gpt-oss-120b, gemini)
    return f"""You are an independent evaluator for a decision. You have NOT seen any other evaluator's opinion. Be brutally honest and specific.

PERSPECTIVE: {perspective} - {perspective_desc}{group_line}

DECISION: {config.question}
{context_block}
{constraints_block}{memory_block}

PATHS TO EVALUATE:
{paths_text}

SCORING RULES:
- Score each path 0-10 on each dimension. Be harsh - 10 is near-impossible.
- risk: 0 = catastrophic failure likely, 10 = very safe (INVERTED scale - higher is safer)
- Write ONE specific concern per path. Cite concrete evidence, not vague worries.
- "I don't know" is valid - do NOT invent information you don't have.
- Pick the winner YOU genuinely believe is best from YOUR perspective.

PATH PROPOSAL (optional): If you see an important approach NOT listed above that you believe should be considered, propose it. Only propose if genuinely valuable — do not pad. Set to null if nothing is missing.

RESEARCH REQUEST (optional): If making this decision well requires information you DON'T currently have — recent data, a benchmark, a study, a comparison — request a specific web search topic.
Rules:
- Be SPECIFIC: not "AI safety" but "comparison of ELO vs Glicko-2 for multi-agent weight calibration"
- Include WHY: what gap does this fill? What decision would it change?
- Set to null if your current knowledge is sufficient
This request will be executed by a web researcher (Gemini Pro with Google Search) and the findings will be available to all agents in future decisions.

INNOVATION: After your evaluation, propose ONE unexpected/creative idea related to this decision that nobody asked about. Must be actionable in 1 session. Think outside the box.

SKILL FEEDBACK: If a SKILL was injected above, rate it: was it helpful? What's missing?

Respond ONLY with valid JSON (no markdown, no extra text):
{{
  "evaluator": "{agent_id}",
  "perspective": "{perspective}",
  "scores": {{
    {scores_template}
  }},
  "concerns": {{
    {concerns_template}
  }},
  "winner": "path_id",
  "reason": "one sentence with specific evidence",
  "confidence": 0.0,
  "proposed_path": {{
    "name": "short name for proposed path",
    "description": "what this approach involves (1-2 sentences)",
    "rationale": "why this path was not listed but should be considered"
  }},
  "research_request": {{
    "topic": "specific research question to investigate via web search",
    "rationale": "what gap this fills and what decision it would change",
    "domain": "architecture|code|security|business|general",
    "priority": "high|medium|low"
  }},
  "innovation": "one creative idea, actionable in 1 session",
  "skill_used": "skill name or null",
  "skill_helpful": true,
  "skill_gap": "what was missing from the skill, or null",
  "self_note": "what I learned from this evaluation for next time"
}}

Note: set "proposed_path" and "research_request" to null if you have nothing meaningful to propose."""


def build_debate_prompt(
    config: SwarmConfig,
    agent_id: str,
    own_result: dict,
    opponent_results: list[dict],
) -> str:
    """Build a targeted correction prompt for debate round.

    Only used when divergence > 50%. Agent sees opponents' answers
    and must point out SPECIFIC errors (not just disagree).
    Research: ICML 2024 - targeted correction works for heterogeneous agents.
    """
    opponents_text = ""
    for i, opp in enumerate(opponent_results):
        opponents_text += (
            f"\nOPPONENT {i+1} ({opp.get('perspective', '?')}):\n"
            f"  Winner: {opp.get('winner', '?')}\n"
            f"  Reason: {opp.get('reason', '?')}\n"
            f"  Concerns: {opp.get('concerns', {})}\n"
        )

    return f"""You previously evaluated a decision and chose "{own_result.get('winner', '?')}".
Other evaluators DISAGREED with you. Here are their positions:
{opponents_text}

YOUR TASK: Review their arguments. Be specific:
1. If they found a real error in YOUR reasoning - acknowledge it and change your vote.
2. If THEIR reasoning has a specific flaw - point it out with evidence.
3. Do NOT just repeat "I disagree". Cite specifics.

DECISION: {config.question}

Respond ONLY with valid JSON:
{{
  "evaluator": "{agent_id}",
  "changed_vote": true or false,
  "new_winner": "path_id (same or different)",
  "correction": "what specific error you found (in your own or opponent's reasoning)",
  "confidence": 0.0
}}"""


def build_synthesis_prompt(
    config: SwarmConfig,
    group_winners: list[dict],
) -> str:
    """Build the final LLM synthesis prompt (MoA-style).

    Instead of just picking the top-scored path, the synthesizer
    creates a NEW answer that combines the best insights from all groups.
    Research: MoA showed synthesis > selection by ~12%.
    """
    groups_text = ""
    for gw in group_winners:
        groups_text += (
            f"\nGROUP: {gw.get('group', '?')}\n"
            f"  Winner: {gw.get('winner', '?')} (score: {gw.get('score', '?')}/50)\n"
            f"  Key concern: {gw.get('top_concern', '?')}\n"
            f"  Consensus: {gw.get('consensus', '?')}%\n"
            f"  Dissent: {gw.get('dissent', 'none')}\n"
        )

    path_names = ""
    if config.paths:
        path_names = "\n".join(
            f"  {pid}: {p.name}" for pid, p in config.paths.items()
        )

    return f"""You are the final synthesis agent. Multiple specialist groups independently evaluated a decision. You must SYNTHESIZE their findings into one recommendation.

Do NOT just pick the most popular answer. Instead:
1. Find what ALL groups agree on (consensus signal)
2. Find where groups DISAGREE (risk signal - this is where real danger lives)
3. Check if any group found something critical that others missed
4. Synthesize a recommendation that addresses ALL major concerns

DECISION: {config.question}

PATHS:
{path_names}

GROUP RESULTS:
{groups_text}

Respond with valid JSON:
{{
  "winner": "path_id",
  "synthesis": "2-3 sentences explaining WHY, citing specific group findings",
  "consensus_points": ["what all groups agreed on"],
  "risk_points": ["where groups disagreed - these need attention"],
  "surprise_insight": "anything one group found that others missed (or null)",
  "confidence": 0.0,
  "conditions": "under what conditions should we switch to a different path"
}}"""


def get_group_perspectives(group_name: str) -> list[tuple[str, str]]:
    """Get 3 diverse sub-perspectives for a named group."""
    return GROUP_PERSPECTIVES.get(
        group_name,
        # Fallback: generate generic sub-perspectives
        [
            (f"{group_name}_analyst", f"Analyze {group_name} implications thoroughly."),
            (f"{group_name}_critic", f"Find flaws in {group_name} approach."),
            (f"{group_name}_advocate", f"Make the strongest case for {group_name} priorities."),
        ],
    )


def get_random_perspectives(count: int) -> list[tuple[str, str]]:
    """Get N unique random perspectives for a flat (non-grouped) swarm run."""
    pool = list(FLAT_PERSPECTIVES)
    random.shuffle(pool)

    if count <= len(pool):
        return pool[:count]

    result = list(pool)
    extra = count - len(pool)
    for i in range(extra):
        base = pool[i % len(pool)]
        result.append((f"{base[0]}_{i+2}", base[1]))

    return result
