"""
Skill Library — dynamic skill loading, injection, feedback, and versioning.

Skills are .md files that agents borrow temporarily to augment their evaluation.
After use, agents provide feedback on what's missing → skills improve over time.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger

# Default skill directories to scan
_SKILL_DIRS = [
    "docs/engineering/skills",
    "docs/engineering/decision-simulation-skill",
    "docs/engineering",
    ".claude/skills",
]

# Skill → keyword mapping for auto-detection
_SKILL_KEYWORDS: dict[str, list[str]] = {
    "SECURITY-REVIEW": ["security", "auth", "rls", "owasp", "vulnerability", "attack", "injection", "xss"],
    "CODE-REVIEW": ["code", "refactor", "architecture", "pattern", "review", "quality"],
    "TDD-WORKFLOW": ["test", "tdd", "pytest", "coverage", "bug", "regression"],
    "CONTINUOUS-LEARNING": ["learn", "improve", "retrospective", "calibrate"],
    "decision-simulation": ["decision", "dsp", "evaluate", "path", "trade-off"],
    "DESIGN-HANDOFF": ["design", "ui", "ux", "component", "figma", "v0"],
}


class SkillLibrary:
    """Manages skill files: discovery, loading, injection, feedback, versioning."""

    def __init__(self, project_root: Path | None = None):
        self.project_root = project_root or Path.cwd()
        self._skills_cache: dict[str, str] = {}
        self._metadata_path = self.project_root / ".swarm" / "skill_metadata.json"
        self._metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def discover_skills(self) -> dict[str, Path]:
        """Find all .md skill files in known directories."""
        skills: dict[str, Path] = {}

        for dir_rel in _SKILL_DIRS:
            dir_path = self.project_root / dir_rel
            if not dir_path.exists():
                continue
            for f in dir_path.glob("*.md"):
                if f.name.startswith("_") or f.name == "README.md":
                    continue
                skill_name = f.stem
                skills[skill_name] = f

        # Also scan SKILL.md inside subdirectories
        for dir_rel in _SKILL_DIRS:
            dir_path = self.project_root / dir_rel
            if not dir_path.exists():
                continue
            for f in dir_path.glob("*/SKILL.md"):
                skill_name = f.parent.name
                skills[skill_name] = f

        logger.debug("Discovered {n} skills", n=len(skills))
        return skills

    def match_skills(self, task_text: str, max_skills: int = 3) -> list[str]:
        """Auto-detect which skills are relevant for a task."""
        task_lower = task_text.lower()
        scores: dict[str, int] = {}

        for skill_name, keywords in _SKILL_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in task_lower)
            if score > 0:
                scores[skill_name] = score

        # Sort by relevance, return top N
        ranked = sorted(scores.items(), key=lambda x: -x[1])
        return [name for name, _ in ranked[:max_skills]]

    def load_skill(self, skill_name: str) -> str | None:
        """Load skill content. Returns None if not found."""
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name]

        skills = self.discover_skills()
        path = skills.get(skill_name)
        if not path or not path.exists():
            return None

        content = path.read_text(encoding="utf-8")

        # Truncate to ~2000 chars to fit in agent context
        if len(content) > 2000:
            content = content[:2000] + "\n\n[... truncated for context window ...]"

        self._skills_cache[skill_name] = content
        return content

    def inject_into_prompt(self, prompt: str, skill_names: list[str]) -> str:
        """Inject skill content into an agent's prompt."""
        skill_blocks = []
        for name in skill_names:
            content = self.load_skill(name)
            if content:
                skill_blocks.append(f"=== SKILL: {name} ===\n{content}\n=== END SKILL ===")

        if not skill_blocks:
            return prompt

        skills_section = "\n\n".join(skill_blocks)
        # Insert before the JSON response template
        if "Respond ONLY with valid JSON" in prompt:
            parts = prompt.split("Respond ONLY with valid JSON", 1)
            return (
                parts[0]
                + f"\nSKILLS AVAILABLE (use these guidelines in your evaluation):\n{skills_section}\n\n"
                + "Respond ONLY with valid JSON"
                + parts[1]
            )

        return prompt + f"\n\nSKILLS AVAILABLE:\n{skills_section}"

    def record_feedback(
        self,
        skill_name: str,
        agent_model: str,
        helpful: bool,
        gap: str = "",
        suggestion: str = "",
    ) -> None:
        """Record agent feedback on a skill."""
        metadata = self._load_metadata()

        if skill_name not in metadata:
            metadata[skill_name] = {
                "version": 1,
                "usage_count": 0,
                "helpful_count": 0,
                "feedback": [],
                "maturity": "new",
            }

        entry = metadata[skill_name]
        entry["usage_count"] += 1
        if helpful:
            entry["helpful_count"] += 1

        if gap or suggestion:
            entry["feedback"].append({
                "agent": agent_model,
                "helpful": helpful,
                "gap": gap,
                "suggestion": suggestion,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            # Keep last 20 feedback entries
            entry["feedback"] = entry["feedback"][-20:]

        # Update maturity
        if entry["usage_count"] >= 20 and entry["helpful_count"] / max(entry["usage_count"], 1) > 0.8:
            entry["maturity"] = "mature"
        elif entry["usage_count"] >= 5:
            entry["maturity"] = "growing"

        self._save_metadata(metadata)

    def get_pending_improvements(self) -> list[dict]:
        """Get skill improvements suggested by agents (for orchestrator review)."""
        metadata = self._load_metadata()
        pending = []

        for skill_name, entry in metadata.items():
            for fb in entry.get("feedback", []):
                if fb.get("suggestion"):
                    pending.append({
                        "skill": skill_name,
                        "agent": fb["agent"],
                        "suggestion": fb["suggestion"],
                        "gap": fb.get("gap", ""),
                    })

        return pending

    def get_agent_skill_affinity(self) -> dict[str, dict[str, float]]:
        """Which agents work best with which skills."""
        metadata = self._load_metadata()
        affinity: dict[str, dict[str, float]] = {}

        for skill_name, entry in metadata.items():
            for fb in entry.get("feedback", []):
                agent = fb.get("agent", "")
                if agent not in affinity:
                    affinity[agent] = {}
                if skill_name not in affinity[agent]:
                    affinity[agent][skill_name] = 0.0

                affinity[agent][skill_name] += 1.0 if fb.get("helpful") else -0.5

        return affinity

    def _load_metadata(self) -> dict:
        if not self._metadata_path.exists():
            return {}
        try:
            with open(self._metadata_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_metadata(self, data: dict) -> None:
        with open(self._metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
