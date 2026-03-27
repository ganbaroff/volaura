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
                distilled = f.read()[:3000]

        prompt = f"""You are a skill evolution engine for an AI agent swarm.

CURRENT SKILLS:
{chr(10).join(summaries)}

DISTILLED AGENT KNOWLEDGE:
{distilled}

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

    lines += [
        "---",
        "",
        "**Next evolution:** Runs automatically after each swarm daily run.",
        "**Manual run:** `python -m packages.swarm.skill_evolution`",
    ]

    with open(EVOLUTION_LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    logger.info(f"Skill evolution log written: {EVOLUTION_LOG}")


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

    # Write log
    _write_evolution_log(skills, ref_issues, quality_issues, llm_review)

    summary = {
        "skills": len(skills),
        "issues": len(ref_issues) + len(quality_issues),
        "health": llm_review.get("ecosystem_health") if llm_review else None,
        "missing_count": len(llm_review.get("missing_skills", [])) if llm_review else 0,
        "improvements_count": len(llm_review.get("skill_improvements", [])) if llm_review else 0,
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
