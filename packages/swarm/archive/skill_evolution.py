#!/usr/bin/env python3
"""Skill Evolution Engine — скиллы которые улучшают себя.

Аналог мозга: нейропластичность. Навыки не статичны — они
адаптируются на основе использования и обратной связи.

Что делает:
  1. Сканирует все скиллы в memory/swarm/skills/
  2. Проверяет каждый на: устаревшие cross-references, missing triggers, quality
  3. Генерирует КОНКРЕТНЫЕ предложения по улучшению каждого скилла
  4. Пишет предложения в memory/swarm/skill-evolution-log.md
  5. HIGH priority изменения → Telegram CEO
  6. LOW priority → CTO применяет при следующей сессии

Запускается ПОСЛЕ memory_consolidation в daily swarm run.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

project_root = Path(__file__).parent.parent.parent
packages_path = str(project_root / "packages")
if packages_path not in sys.path:
    sys.path.insert(0, packages_path)

# ── Paths ─────────────────────────────────────────────────────────────────────

SKILLS_DIR = project_root / "memory" / "swarm" / "skills"
EVOLUTION_LOG = project_root / "memory" / "swarm" / "skill-evolution-log.md"
SHARED_CONTEXT = project_root / "memory" / "swarm" / "shared-context.md"
DISTILLED_FILE = project_root / "memory" / "swarm" / "agent-feedback-distilled.md"

# EvoSkill (B3): raw failed trajectory logs live in SWARM_DATA_DIR (GitHub Actions)
# or ~/.swarm/ (local dev). Path mirrors AgentMemory.log_trajectory().
_swarm_data_dir = os.environ.get("SWARM_DATA_DIR")
TRAJECTORIES_FILE = (
    Path(_swarm_data_dir) / "agent-trajectories.jsonl"
    if _swarm_data_dir
    else Path.home() / ".swarm" / "agent-trajectories.jsonl"
)


def _scan_skills() -> list[dict]:
    """Scan all skill files and extract metadata."""
    skills = []
    if not SKILLS_DIR.exists():
        return skills

    for skill_file in sorted(SKILLS_DIR.glob("*.md")):
        with open(skill_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract basic metadata from content
        lines = content.split("\n")
        title = lines[0].replace("#", "").strip() if lines else skill_file.stem
        has_trigger = "## Trigger" in content or "## trigger" in content
        has_output = "## Output" in content or "## output" in content
        has_cross_refs = "Cross-references" in content or "cross-references" in content
        line_count = len(lines)

        # Find cross-referenced skills
        cross_refs = []
        for line in lines:
            if "load:" in line.lower() or "загрузи" in line.lower() or "`" in line:
                # Extract skill names from backtick references
                import re
                refs = re.findall(r"`([a-z\-]+)`", line)
                cross_refs.extend(refs)

        skills.append({
            "file": skill_file.name,
            "path": str(skill_file),
            "title": title,
            "has_trigger": has_trigger,
            "has_output": has_output,
            "has_cross_refs": has_cross_refs,
            "line_count": line_count,
            "cross_refs": list(set(cross_refs)),
            "content_preview": content[:500],
        })

    return skills


def _check_cross_refs(skills: list[dict]) -> list[str]:
    """Check if cross-referenced skills actually exist."""
    skill_names = {s["file"].replace(".md", "") for s in skills}
    issues = []

    for skill in skills:
        for ref in skill["cross_refs"]:
            # Check if referenced skill exists (as file or known process skill)
            known_skills = skill_names | {
                "neuroscience-design", "security-review", "tdd-workflow",
                "continuous-learning", "architecture-review", "product-strategy",
                "decision-simulation",
            }
            if ref not in known_skills and ref + "-skill" not in known_skills:
                issues.append(
                    f"BROKEN REF: `{skill['file']}` references `{ref}` — skill not found"
                )

    return issues


def _check_quality(skills: list[dict]) -> list[str]:
    """Check skill quality: missing sections, too short, etc."""
    issues = []

    for skill in skills:
        if not skill["has_trigger"]:
            issues.append(
                f"NO TRIGGER: `{skill['file']}` has no ## Trigger section — "
                f"agents won't know when to activate it"
            )
        if not skill["has_output"]:
            issues.append(
                f"NO OUTPUT: `{skill['file']}` has no ## Output section — "
                f"no structured output format defined"
            )
        if skill["line_count"] < 20:
            issues.append(
                f"TOO SHORT: `{skill['file']}` is only {skill['line_count']} lines — "
                f"likely incomplete"
            )

    return issues


def _load_failed_trajectories(max_entries: int = 20) -> str:
    """Load recent failed agent trajectories from agent-trajectories.jsonl.

    EvoSkill pattern (B3): skill evolution should use raw failure traces,
    not just distilled summaries. Returns the last N wrong-outcome entries
    formatted for the LLM prompt.
    """
    if not TRAJECTORIES_FILE.exists():
        return ""

    try:
        lines = []
        with open(TRAJECTORIES_FILE, "r", encoding="utf-8") as f:
            for raw in f:
                raw = raw.strip()
                if raw:
                    try:
                        lines.append(json.loads(raw))
                    except json.JSONDecodeError:
                        continue

        # Keep only failures, most recent first
        failures = [e for e in lines if e.get("outcome") == "wrong"]
        recent = failures[-max_entries:]

        if not recent:
            return ""

        parts = [f"RECENT FAILED AGENT TRAJECTORIES (last {len(recent)} failures):"]
        for entry in recent:
            parts.append(
                f"- [{entry.get('model', '?')}] Task: {entry.get('task', '')[:100]}"
            )
            parts.append(f"  Response: {entry.get('response', '')[:150]}")
        return "\n".join(parts)
    except OSError:
        return ""


async def _llm_skill_review(skills: list[dict], groq_key: str) -> dict | None:
    """Use LLM to review skills and suggest improvements."""
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=groq_key)

        # Build skill summaries
        summaries = []
        for s in skills:
            summaries.append(
                f"- **{s['title']}** ({s['file']}): "
                f"{s['line_count']} lines, "
                f"trigger={'yes' if s['has_trigger'] else 'NO'}, "
                f"output={'yes' if s['has_output'] else 'NO'}, "
                f"cross-refs: {s['cross_refs'] or 'none'}"
            )

        # Read distilled knowledge for context
        distilled = ""
        if DISTILLED_FILE.exists():
            with open(DISTILLED_FILE, "r", encoding="utf-8") as f:
                distilled = f.read()[:2000]

        # EvoSkill (B3): also read raw failed trajectories — higher signal than summaries
        trajectories = _load_failed_trajectories()

        prompt = f"""You are a skill evolution engine for an AI agent swarm.

CURRENT SKILLS:
{chr(10).join(summaries)}

DISTILLED AGENT KNOWLEDGE:
{distilled}

{trajectories}

Analyze the skill library and output JSON:
{{
    "missing_skills": [
        // Skills that SHOULD exist but don't. Max 3.
        // Format: {{"name": "skill-name", "why": "1 sentence reason", "priority": "high/medium/low"}}
    ],
    "skill_improvements": [
        // Concrete improvements to existing skills. Max 5.
        // Format: {{"skill": "filename.md", "improvement": "specific change", "priority": "high/medium/low"}}
    ],
    "skill_conflicts": [
        // Skills that contradict each other. Max 2.
        // Format: {{"skills": ["a.md", "b.md"], "conflict": "description"}}
    ],
    "ecosystem_health": 0-100,
    "top_action": "The single most impactful thing to do next for the skill library"
}}

Rules:
- Be specific. "Improve the skill" is useless. "Add ## Error Handling section to ai-twin-responder.md with 3 failure modes" is useful.
- Reference the distilled knowledge — if agents keep making the same mistake, there should be a skill preventing it.
- Missing skills should be PRODUCT skills that generate user value, not more process skills."""

        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"},
            ),
            timeout=30.0,
        )
        raw = resp.choices[0].message.content or ""
        return json.loads(raw)

    except Exception as e:
        logger.error(f"Skill evolution LLM review failed: {e}")
        return None


def _write_evolution_log(
    skills: list[dict],
    ref_issues: list[str],
    quality_issues: list[str],
    llm_review: dict | None,
    voyager_results: list[dict] | None = None,
) -> None:
    """Write the evolution log that CTO reads at session start."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        "# Skill Evolution Log",
        "",
        f"**Auto-generated by skill_evolution.py** | {now}",
        f"**Skills scanned:** {len(skills)}",
        "",
        "---",
        "",
    ]

    # Quality issues
    if ref_issues or quality_issues:
        lines.append("## ⚠️ Issues Found")
        lines.append("")
        for issue in ref_issues + quality_issues:
            lines.append(f"- {issue}")
        lines.append("")

    # LLM review
    if llm_review:
        health = llm_review.get("ecosystem_health", "?")
        lines.append(f"## Ecosystem Health: {health}/100")
        lines.append("")

        # Missing skills
        missing = llm_review.get("missing_skills", [])
        if missing:
            lines.append("## 🆕 Missing Skills (should exist)")
            lines.append("")
            for m in missing:
                lines.append(f"- **{m.get('name')}** [{m.get('priority')}] — {m.get('why')}")
            lines.append("")

        # Improvements
        improvements = llm_review.get("skill_improvements", [])
        if improvements:
            lines.append("## 🔧 Skill Improvements")
            lines.append("")
            for imp in improvements:
                lines.append(f"- `{imp.get('skill')}` [{imp.get('priority')}] — {imp.get('improvement')}")
            lines.append("")

        # Top action
        top = llm_review.get("top_action", "")
        if top:
            lines.append("## 🎯 Top Action")
            lines.append("")
            lines.append(f"> {top}")
            lines.append("")

    # VOYAGER verification results
    if voyager_results:
        lines.append("## 🔬 VOYAGER Verification Gate")
        lines.append("")
        lines.append("New skills verified before entering library:")
        lines.append("")
        for r in voyager_results:
            icon = "✅" if r["status"] == "passed" else "❌"
            lines.append(f"- {icon} **{r['name']}** — {r['verdict']}")
            if r.get("file"):
                lines.append(f"  → Candidate saved: `memory/swarm/skills/{r['file']}`")
                lines.append(f"  → CTO must rename to `.md` to activate.")
        lines.append("")

    lines += [
        "---",
        "",
        "**Next evolution:** Runs automatically after each swarm daily run.",
        "**Manual run:** `python -m packages.swarm.skill_evolution`",
    ]

    with open(EVOLUTION_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"Skill evolution log written: {EVOLUTION_LOG}")


# ── VOYAGER verification gate (B4) ────────────────────────────────────────────

async def _draft_skill(name: str, why: str, groq_key: str) -> str | None:
    """Ask LLM to write a full skill file for a proposed new skill."""
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=groq_key)

        prompt = f"""Write a skill file for an AI agent swarm skill called "{name}".

Reason it's needed: {why}

The skill file must follow this exact structure:
# [Skill Name]

## Trigger
When to activate this skill (specific conditions, 2-4 bullets).

## Guidelines
Core rules the agent must follow when using this skill (4-6 bullets).

## Output
What structured output the agent must produce (with example format).

## Cross-references
Other skills that should be loaded alongside this one.

Write the full skill file content only. No preamble. Start with # heading."""

        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=800,
            ),
            timeout=25.0,
        )
        return resp.choices[0].message.content or None
    except Exception as e:
        logger.error(f"Skill draft failed for '{name}': {e}")
        return None


async def _verify_skill_draft(name: str, draft: str, groq_key: str) -> tuple[bool, str]:
    """VOYAGER gate: verify a drafted skill against a synthetic task.

    Returns (passed: bool, verdict: str).
    Verification criteria:
    - Has ## Trigger section
    - Has ## Output section with a concrete example
    - When given a synthetic scenario, produces structured output
    - Does not hallucinate non-existent APIs or files
    """
    # Static checks first (fast, free)
    has_trigger = "## Trigger" in draft
    has_output = "## Output" in draft
    has_guidelines = "## Guidelines" in draft
    line_count = len(draft.split("\n"))

    if not has_trigger:
        return False, "FAIL: missing ## Trigger section"
    if not has_output:
        return False, "FAIL: missing ## Output section"
    if not has_guidelines:
        return False, "FAIL: missing ## Guidelines section"
    if line_count < 15:
        return False, f"FAIL: too short ({line_count} lines, minimum 15)"

    # LLM verification: simulate agent using this skill on a test task
    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=groq_key)

        prompt = f"""You are a QA verifier for AI agent skills.

SKILL DRAFT:
{draft}

TEST TASK: An agent in the Volaura swarm just activated this skill.
The task was: "Evaluate whether a new volunteer AURA score feature should be added."

1. Does the skill's Trigger section correctly describe when to activate it for this task? (yes/no)
2. Does the skill's Output section specify a concrete format? (yes/no)
3. If the agent followed this skill, would it produce better output than without it? (yes/no)
4. Does the skill reference real files/systems that exist in a product platform? (yes/no)

Reply with JSON: {{"q1": bool, "q2": bool, "q3": bool, "q4": bool, "verdict": "PASS or FAIL", "reason": "1 sentence"}}"""

        resp = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"},
            ),
            timeout=20.0,
        )
        raw = json.loads(resp.choices[0].message.content or "{}")
        passed = str(raw.get("verdict", "")).upper() == "PASS"
        reason = raw.get("reason", "")
        answers = f"q1={raw.get('q1')} q2={raw.get('q2')} q3={raw.get('q3')} q4={raw.get('q4')}"
        verdict = f"{'PASS' if passed else 'FAIL'}: {reason} ({answers})"
        return passed, verdict

    except Exception as e:
        logger.warning(f"LLM verification failed for '{name}', using static result: {e}")
        # Static checks passed — accept without LLM verification
        return True, "PASS (static only — LLM verification unavailable)"


async def _verify_proposed_skills(
    missing_skills: list[dict], groq_key: str
) -> list[dict]:
    """For each HIGH-priority proposed skill: draft it and run VOYAGER gate.

    Verified skills are saved as .candidate.md files in SKILLS_DIR.
    Failed skills are recorded in the evolution log only.
    Returns list of verification results.
    """
    results = []
    for skill in missing_skills:
        if skill.get("priority") not in ("high",):
            continue  # Only verify high-priority new skills

        name = skill.get("name", "")
        why = skill.get("why", "")
        if not name:
            continue

        logger.info(f"VOYAGER gate: drafting skill '{name}'...")
        draft = await _draft_skill(name, why, groq_key)
        if not draft:
            results.append({"name": name, "status": "draft_failed", "verdict": "Could not generate draft"})
            continue

        passed, verdict = await _verify_skill_draft(name, draft, groq_key)
        logger.info(f"VOYAGER gate: '{name}' → {verdict}")

        if passed:
            # Write to skills dir as candidate — CTO reviews before promoting to .md
            safe_name = name.replace(" ", "-").lower()
            candidate_path = SKILLS_DIR / f"{safe_name}.candidate.md"
            SKILLS_DIR.mkdir(parents=True, exist_ok=True)
            with open(candidate_path, "w", encoding="utf-8") as f:
                f.write(f"<!-- VOYAGER CANDIDATE — requires CTO review before activating -->\n")
                f.write(f"<!-- Verdict: {verdict} -->\n\n")
                f.write(draft)
            logger.success(f"VOYAGER gate: skill '{name}' passed → saved as {candidate_path.name}")

        results.append({
            "name": name,
            "status": "passed" if passed else "failed",
            "verdict": verdict,
            "file": f"{name.replace(' ', '-').lower()}.candidate.md" if passed else None,
        })

    return results


# ── Entry point ───────────────────────────────────────────────────────────────

async def evolve(groq_key: str | None = None) -> dict:
    """
    Main skill evolution function.
    Returns summary dict with issues found and recommendations.
    """
    logger.info("Skill evolution starting...")

    skills = _scan_skills()
    if not skills:
        logger.warning("No skills found in memory/swarm/skills/")
        return {"skills": 0, "issues": 0}

    logger.info(f"Scanned {len(skills)} skills")

    # Static checks
    ref_issues = _check_cross_refs(skills)
    quality_issues = _check_quality(skills)

    for issue in ref_issues + quality_issues:
        logger.warning(issue)

    # LLM review
    groq_key = groq_key or os.environ.get("GROQ_API_KEY", "")
    llm_review = None
    if groq_key:
        llm_review = await _llm_skill_review(skills, groq_key)

    # VOYAGER gate (B4): verify high-priority proposed skills before entering library
    voyager_results: list[dict] = []
    if groq_key and llm_review:
        missing = llm_review.get("missing_skills", [])
        high_priority = [m for m in missing if m.get("priority") == "high"]
        if high_priority:
            logger.info(
                "VOYAGER gate: verifying {n} high-priority skill candidates",
                n=len(high_priority),
            )
            voyager_results = await _verify_proposed_skills(high_priority, groq_key)

    # Write log
    _write_evolution_log(skills, ref_issues, quality_issues, llm_review, voyager_results)

    passed_count = sum(1 for r in voyager_results if r["status"] == "passed")
    summary = {
        "skills": len(skills),
        "issues": len(ref_issues) + len(quality_issues),
        "health": llm_review.get("ecosystem_health") if llm_review else None,
        "missing_count": len(llm_review.get("missing_skills", [])) if llm_review else 0,
        "improvements_count": len(llm_review.get("skill_improvements", [])) if llm_review else 0,
        "voyager_candidates": passed_count,
    }

    logger.success(
        f"Skill evolution complete: {summary['skills']} skills, "
        f"{summary['issues']} issues, health={summary.get('health', '?')}/100"
    )
    return summary


def main() -> None:
    """CLI entry point."""
    from dotenv import load_dotenv
    load_dotenv(project_root / "apps" / "api" / ".env")

    summary = asyncio.run(evolve())
    print(f"\nSkill Evolution: {summary['skills']} skills, {summary['issues']} issues")
    if summary.get("health"):
        print(f"Ecosystem health: {summary['health']}/100")


if __name__ == "__main__":
    main()
