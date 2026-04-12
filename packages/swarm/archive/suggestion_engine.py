#!/usr/bin/env python3
"""Suggestion Engine — Predictive Next Actions (Sprint 2).

Swarm vote winner (42/50). After every batch close, generates 2-3 predictions
of what the CEO will probably want next, based on:
  1. What was just completed (task context)
  2. What's in the backlog (unacted proposals)
  3. What patterns exist (patterns.md)
  4. What mistakes to avoid (mistakes.md)

Output format (in ceo-inbox.md):
  ## 🔮 Predicted Next Actions (auto-generated)
  1. **[Title]** (~Xh) — [Why now: trigger reason]
  2. **[Title]** (~Xh) — [Why now: trigger reason]

Usage:
    from swarm.suggestion_engine import generate_suggestions, append_to_ceo_inbox

    suggestions = generate_suggestions(
        completed_proposals=proposals,
        project_root=project_root,
        env=dict(os.environ),
    )
    append_to_ceo_inbox(suggestions, project_root)
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

project_root = Path(__file__).parent.parent.parent
CEO_INBOX = project_root / "memory" / "swarm" / "ceo-inbox.md"
PROPOSALS_FILE = project_root / "memory" / "swarm" / "proposals.json"
PATTERNS_FILE = project_root / "memory" / "context" / "patterns.md"
MISTAKES_FILE = project_root / "memory" / "context" / "mistakes.md"
SPRINT_STATE_FILE = project_root / "memory" / "context" / "sprint-state.md"
IMPLEMENTATION_ROADMAP = project_root / "docs" / "IMPLEMENTATION-ROADMAP.md"


# ── Data types ─────────────────────────────────────────────────────────────────

@dataclass
class Suggestion:
    """A predicted next action for the CEO."""
    title: str
    description: str
    trigger_reason: str          # WHY NOW — what recent event makes this timely
    estimated_hours: float
    priority: str                # "urgent" | "high" | "medium" | "low"
    linked_files: list[str] = field(default_factory=list)
    confidence: float = 0.7      # 0.0 – 1.0


# ── Context readers ───────────────────────────────────────────────────────────

def _read_file_tail(path: Path, lines: int = 30) -> str:
    """Read last N lines of a file."""
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        all_lines = f.readlines()
    return "".join(all_lines[-lines:])


def _read_backlog(project_root: Path) -> list[dict]:
    """Read pending proposals from proposals.json."""
    if not PROPOSALS_FILE.exists():
        return []
    try:
        with open(PROPOSALS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        proposals = data if isinstance(data, list) else data.get("proposals", [])
        return [p for p in proposals if p.get("status", "pending") == "pending"]
    except (json.JSONDecodeError, OSError):
        return []


def _read_roadmap_sprints(project_root: Path) -> str:
    """Read the implementation roadmap sprint overview."""
    if not IMPLEMENTATION_ROADMAP.exists():
        return ""
    with open(IMPLEMENTATION_ROADMAP, "r", encoding="utf-8") as f:
        content = f.read()
    # Extract just the Sprints Overview table
    start = content.find("## Sprints Overview")
    if start == -1:
        return content[:2000]
    end = content.find("## Sprint 1 —", start)
    return content[start:end] if end != -1 else content[start:start + 1500]


# ── LLM suggestion generation ─────────────────────────────────────────────────

async def _generate_via_llm(
    context: str,
    env: dict[str, str],
) -> list[dict]:
    """Generate suggestions via LLM. Returns list of {title, description, trigger_reason, estimated_hours, priority}."""

    prompt = f"""You are the CTO's predictive advisor for a startup called Volaura (verified talent platform in Azerbaijan).

Based on what was just completed and what's in the backlog, predict the 2-3 most important next actions.

CONTEXT:
{context}

Generate exactly 3 suggestions. Each must:
1. Follow directly from something that just happened (trigger_reason = WHAT RECENT EVENT makes this timely)
2. Be actionable within 1-4 hours
3. Have a clear measurable outcome

Reply with JSON only:
{{
  "suggestions": [
    {{
      "title": "short action title",
      "description": "what to do and why",
      "trigger_reason": "because X was just completed/discovered/failed",
      "estimated_hours": 1.5,
      "priority": "urgent|high|medium|low",
      "linked_files": ["path/to/file.py"]
    }}
  ]
}}"""

    groq_key = env.get("GROQ_API_KEY", "")
    gemini_key = env.get("GEMINI_API_KEY", "")

    try:
        if groq_key:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=800,
                    response_format={"type": "json_object"},
                ),
                timeout=15.0,
            )
            raw = resp.choices[0].message.content or "{}"
        elif gemini_key:
            from google import genai
            gclient = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    gclient.models.generate_content,
                    model="gemini-1.5-flash",
                    contents=prompt,
                    config={"response_mime_type": "application/json"},
                ),
                timeout=15.0,
            )
            raw = resp.text or "{}"
        else:
            return []

        data = json.loads(raw)
        return data.get("suggestions", [])

    except Exception:
        return []


def _generate_rule_based(
    completed_titles: list[str],
    backlog: list[dict],
    roadmap: str,
) -> list[Suggestion]:
    """Rule-based fallback when LLM unavailable.

    Maps completed work → predictable next steps based on known sprint plan.
    """
    suggestions = []

    # If swarm infra just shipped → suggest running it + then predictive suggestions product feature
    if any("heartbeat" in t.lower() or "verifier" in t.lower() or "outcome" in t.lower() for t in completed_titles):
        suggestions.append(Suggestion(
            title="Test heartbeat gate on swarm-daily.yml (dry run)",
            description="Run `python -m packages.swarm.heartbeat_gate` to verify it correctly detects recent activity and pending proposals before wiring into CI.",
            trigger_reason="because heartbeat_gate.py was just created — needs validation before GitHub Actions wire-up",
            estimated_hours=0.5,
            priority="urgent",
            linked_files=["packages/swarm/heartbeat_gate.py", ".github/workflows/swarm-daily.yml"],
            confidence=0.95,
        ))
        suggestions.append(Suggestion(
            title="Wire proposal_verifier into autonomous_run.py",
            description="Call tag_proposal_if_ungrounded() on each proposal before storing to proposals.json. Measure groundedness delta on next swarm run.",
            trigger_reason="because proposal_verifier.py exists but isn't called from the main run loop yet",
            estimated_hours=1.0,
            priority="high",
            linked_files=["packages/swarm/autonomous_run.py", "packages/swarm/proposal_verifier.py"],
            confidence=0.90,
        ))

    # If sprint 1 nearly done → suggest sprint 2 (Adaptive Executor)
    if len(suggestions) < 3 and backlog:
        high_backlog = [p for p in backlog if p.get("severity") in ("critical", "high")]
        if high_backlog:
            p = high_backlog[0]
            suggestions.append(Suggestion(
                title=f"Act on HIGH proposal: {p.get('title', '')[:50]}",
                description=p.get("content", "")[:200],
                trigger_reason="because this HIGH priority proposal has been pending since the last swarm run",
                estimated_hours=2.0,
                priority="high",
                confidence=0.80,
            ))

    # Fill to 3 if needed
    if len(suggestions) < 3:
        suggestions.append(Suggestion(
            title="Run Sprint 1 self-verification (outcome_verifier.py)",
            description="Run `python -m packages.swarm.outcome_verifier` to verify all Sprint 1 files were created correctly.",
            trigger_reason="because Sprint 1 files were just written and need verification before moving to Sprint 2",
            estimated_hours=0.25,
            priority="high",
            linked_files=["packages/swarm/outcome_verifier.py"],
            confidence=0.95,
        ))

    return suggestions[:3]


# ── Public API ─────────────────────────────────────────────────────────────────

def generate_suggestions(
    completed_proposals: list | None = None,
    project_root_override: Path | None = None,
    env: dict[str, str] | None = None,
) -> list[Suggestion]:
    """Generate 2-3 predicted next actions.

    Args:
        completed_proposals: List of proposal dicts just processed in this batch
        project_root_override: Override project root (for testing)
        env: Environment variables for LLM access

    Returns:
        List of 2-3 Suggestion objects
    """
    root = project_root_override or project_root
    _env = env or dict(os.environ)

    completed_titles = [p.get("title", "") for p in (completed_proposals or [])]
    backlog = _read_backlog(root)
    roadmap = _read_roadmap_sprints(root)
    patterns = _read_file_tail(PATTERNS_FILE, 20)
    sprint_state = _read_file_tail(SPRINT_STATE_FILE, 15)

    context = f"""JUST COMPLETED ({len(completed_titles)} proposals processed):
{chr(10).join(f'- {t}' for t in completed_titles[:10]) or 'No proposals this run'}

PENDING BACKLOG ({len(backlog)} items):
{chr(10).join(f'- [{p.get("severity", "?")}] {p.get("title", "")}' for p in backlog[:8])}

SPRINT ROADMAP:
{roadmap[:1000]}

CURRENT STATE:
{sprint_state}

KEY PATTERNS:
{patterns[:500]}"""

    # Try LLM first, fall back to rule-based.
    # generate_suggestions() is sync but called from an async context (autonomous_run.py).
    # asyncio.run() crashes inside a running loop. Run in a fresh thread with its own loop.
    import concurrent.futures

    def _run_in_new_loop():
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_generate_via_llm(context, _env))
        finally:
            loop.close()

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as _ex:
            llm_results = _ex.submit(_run_in_new_loop).result(timeout=30)
    except Exception:
        llm_results = []

    if llm_results:
        suggestions = []
        for raw in llm_results[:3]:
            suggestions.append(Suggestion(
                title=raw.get("title", ""),
                description=raw.get("description", ""),
                trigger_reason=raw.get("trigger_reason", ""),
                estimated_hours=float(raw.get("estimated_hours", 2.0)),
                priority=raw.get("priority", "medium"),
                linked_files=raw.get("linked_files", []),
                confidence=0.75,
            ))
        return suggestions

    return _generate_rule_based(completed_titles, backlog, roadmap)


def append_to_ceo_inbox(
    suggestions: list[Suggestion],
    project_root_override: Path | None = None,
) -> None:
    """Append predicted next actions section to ceo-inbox.md.

    Args:
        suggestions: List of Suggestion objects
        project_root_override: Override project root
    """
    root = project_root_override or project_root
    inbox_path = root / "memory" / "swarm" / "ceo-inbox.md"
    inbox_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"\n\n## 🔮 Predicted Next Actions — {timestamp}\n",
        "_Auto-generated by suggestion_engine.py. Each has a trigger_reason explaining WHY NOW._\n\n",
    ]
    for i, s in enumerate(suggestions, 1):
        priority_emoji = {"urgent": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}.get(s.priority, "⚪")
        lines.append(f"{i}. {priority_emoji} **{s.title}** (~{s.estimated_hours:.1f}h)\n")
        lines.append(f"   {s.description}\n")
        lines.append(f"   _Trigger: {s.trigger_reason}_\n")
        if s.linked_files:
            lines.append(f"   Files: `{'`, `'.join(s.linked_files[:3])}`\n")
        lines.append("\n")

    with open(inbox_path, "a", encoding="utf-8") as f:
        f.writelines(lines)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating predictions...")
    suggestions = generate_suggestions()
    print(f"\n[PREDICTIONS] Predicted Next Actions ({len(suggestions)} generated):\n")
    for i, s in enumerate(suggestions, 1):
        print(f"{i}. [{s.priority.upper()}] {s.title} (~{s.estimated_hours:.1f}h)")
        print(f"   Trigger: {s.trigger_reason}")
        print(f"   Confidence: {s.confidence:.0%}\n")

    # Append to inbox
    append_to_ceo_inbox(suggestions)
    print("[OK] Appended to memory/swarm/ceo-inbox.md")
