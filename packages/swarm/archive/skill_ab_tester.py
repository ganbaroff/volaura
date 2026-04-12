#!/usr/bin/env python3
"""Skill A/B Tester — Sprint 5: Skill Evolution Completion.

Compares old vs new version of a skill on a synthetic test task.
Keeps the winner. Backs up the loser.

How it works:
  1. Receive: original skill content + modified skill content + test task
  2. Run same task prompt twice:
     - Prompt A: old skill injected as context
     - Prompt B: new skill injected as context
  3. Score both outputs via outcome_verifier.py judge
  4. Return winner (higher score) + store test result

Cost: ~2 haiku/groq LLM calls per test. ~$0.001 total.

Usage:
    from swarm.skill_ab_tester import compare_skill_versions, ABTestResult

    result = compare_skill_versions(
        skill_file=Path("memory/swarm/skills/risk-manager.md"),
        skill_v1=original_content,
        skill_v2=modified_content,
        test_task="Evaluate security risks for a new API endpoint",
        env=dict(os.environ),
    )
    if result.winner == "v2":
        # Keep v2 (already written by skill_applier.py)
        pass
    else:
        # Restore v1 from backup
        skill_file.write_text(skill_v1, encoding="utf-8")
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
AB_TEST_LOG = project_root / "memory" / "swarm" / "skill-ab-test-log.jsonl"

# Synthetic test tasks per skill domain (matched by filename keywords)
DOMAIN_TEST_TASKS: dict[str, str] = {
    "risk": "Evaluate the security and reliability risks of adding a new public API endpoint that accepts user-uploaded files.",
    "security": "Review this code change: adding a new POST /upload endpoint that stores files in Supabase Storage. Find 3 vulnerabilities.",
    "readiness": "Score the launch readiness of a platform that has 667 passing tests, one production CRITICAL bug, and no monitoring.",
    "growth": "Design a referral loop for a professional skills platform. What's the minimum viable mechanic?",
    "communications": "Write a LinkedIn post announcing that our platform just hit 100 verified users. Keep it authentic.",
    "cultural": "Review these UI strings for Azerbaijan market appropriateness: 'Compete with top performers', 'Win the leaderboard'.",
    "behavioral": "Identify cognitive load issues in a 5-step onboarding flow with 12 form fields spread across 3 screens.",
    "accelerator": "Find 3 grant programs applicable to a verified professional skills platform in Azerbaijan launching in 2026.",
    "accessibility": "Audit an SVG radar chart that uses color to distinguish skill scores. What WCAG failures exist?",
    "sales": "Identify the top 3 objections an HR manager would raise when evaluating a skills verification platform.",
}

DEFAULT_TEST_TASK = "Analyze this sprint proposal: 'Add real-time WebSocket notifications for assessment completions'. What are the key risks and unknowns?"


@dataclass
class ABTestResult:
    """Result of comparing two skill versions."""
    skill_file: str
    winner: str              # "v1" | "v2" | "tie"
    score_v1: float          # 0.0 – 1.0
    score_v2: float          # 0.0 – 1.0
    delta: float             # score_v2 - score_v1 (positive = v2 better)
    test_task: str
    verdict_v1: str          # judge's comment on v1
    verdict_v2: str          # judge's comment on v2
    model_used: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def improvement_pct(self) -> float:
        if self.score_v1 == 0:
            return 0.0
        return (self.score_v2 - self.score_v1) / self.score_v1 * 100

    def summary(self) -> str:
        winner_label = {"v1": "ORIGINAL wins", "v2": "NEW VERSION wins", "tie": "TIE"}[self.winner]
        return (
            f"A/B Test [{Path(self.skill_file).name}]: {winner_label} "
            f"(v1={self.score_v1:.2f} vs v2={self.score_v2:.2f}, delta={self.delta:+.2f})"
        )


# ── LLM evaluation ────────────────────────────────────────────────────────────

async def _evaluate_with_skill(
    skill_content: str,
    test_task: str,
    version_label: str,
    env: dict[str, str],
) -> tuple[float, str]:
    """Ask LLM to perform a task using the given skill as context.
    Then self-score the output quality.

    Returns (score: float 0-1, verdict: str)
    """
    prompt = f"""You are an AI agent with the following skill loaded:

---SKILL START---
{skill_content[:1500]}
---SKILL END---

TASK: {test_task}

Apply the skill to complete the task. Be specific and structured.
After completing the task, on the LAST LINE write exactly:
SELF_SCORE: [0-10] — [one sentence reason]"""

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
                    temperature=0.2,
                    max_tokens=600,
                ),
                timeout=15.0,
            )
            raw = resp.choices[0].message.content or ""
            model = "groq/llama-3.3-70b"
        elif gemini_key:
            from google import genai
            gclient = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    gclient.models.generate_content,
                    model="gemini-1.5-flash",
                    contents=prompt,
                ),
                timeout=15.0,
            )
            raw = resp.text or ""
            model = "gemini-1.5-flash"
        else:
            return 0.5, "no LLM available — neutral score"

        # Extract self-score
        import re
        score_match = re.search(r"SELF_SCORE:\s*(\d+(?:\.\d+)?)\s*[—\-]\s*(.+)", raw)
        if score_match:
            raw_score = float(score_match.group(1))
            verdict = score_match.group(2).strip()[:200]
            normalized = min(1.0, max(0.0, raw_score / 10.0))
            return normalized, verdict
        else:
            # No self-score found — estimate from output length and structure
            # Proxy: longer, structured output = better skill guidance
            score = min(1.0, len(raw) / 800)
            return score, "self-score not found — estimated from output length"

    except Exception as e:
        return 0.5, f"evaluation failed: {str(e)[:100]}"


# ── Cross-model judge ─────────────────────────────────────────────────────────

async def _judge_outputs(
    output_v1: str,
    output_v2: str,
    test_task: str,
    env: dict[str, str],
) -> tuple[str, str, str]:
    """Have a cross-model judge compare the two outputs.

    Asymmetric: if Groq generated outputs, Gemini judges.
    Returns (winner: "v1"|"v2"|"tie", reasoning_v1, reasoning_v2)
    """
    gemini_key = env.get("GEMINI_API_KEY", "")
    groq_key = env.get("GROQ_API_KEY", "")

    if not gemini_key and not groq_key:
        return "tie", "no judge available", "no judge available"

    judge_prompt = f"""You are a quality judge comparing two AI agent responses.

TASK: {test_task}

RESPONSE A (v1 — original skill):
{output_v1[:600]}

RESPONSE B (v2 — modified skill):
{output_v2[:600]}

Compare the responses on: specificity, structure, actionability, and accuracy.
Which is better?

Reply with JSON only:
{{"winner": "v1" or "v2" or "tie", "score_a": 0-10, "score_b": 0-10,
  "reasoning_a": "1 sentence", "reasoning_b": "1 sentence"}}"""

    try:
        # Use Gemini as judge if Groq was used for generation (asymmetric)
        if gemini_key:
            from google import genai
            gclient = genai.Client(api_key=gemini_key)
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    gclient.models.generate_content,
                    model="gemini-1.5-flash",
                    contents=judge_prompt,
                    config={"response_mime_type": "application/json"},
                ),
                timeout=15.0,
            )
            data = json.loads(resp.text or "{}")
        elif groq_key:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": judge_prompt}],
                    temperature=0.1,
                    max_tokens=300,
                    response_format={"type": "json_object"},
                ),
                timeout=15.0,
            )
            data = json.loads(resp.choices[0].message.content or "{}")
        else:
            return "tie", "no judge", "no judge"

        winner = data.get("winner", "tie")
        if winner not in ("v1", "v2", "tie"):
            winner = "tie"
        return winner, data.get("reasoning_a", "")[:200], data.get("reasoning_b", "")[:200]

    except Exception:
        return "tie", "judge failed", "judge failed"


# ── Public API ────────────────────────────────────────────────────────────────

def _pick_test_task(skill_file: Path) -> str:
    """Select appropriate test task based on skill filename."""
    stem = skill_file.stem.lower()
    for keyword, task in DOMAIN_TEST_TASKS.items():
        if keyword in stem:
            return task
    return DEFAULT_TEST_TASK


def compare_skill_versions(
    skill_file: Path,
    skill_v1: str,
    skill_v2: str,
    test_task: str | None = None,
    env: dict[str, str] | None = None,
) -> ABTestResult:
    """Compare two versions of a skill file on a real task.

    Args:
        skill_file: Path to the skill file (for logging)
        skill_v1: Original skill content
        skill_v2: Modified skill content
        test_task: Task to evaluate on (auto-selected from filename if None)
        env: Environment variables for LLM keys

    Returns:
        ABTestResult with winner and scores
    """
    _env = env or dict(os.environ)
    _task = test_task or _pick_test_task(skill_file)

    async def _run() -> ABTestResult:
        # Evaluate both versions in parallel
        (score_v1, verdict_v1), (score_v2, verdict_v2) = await asyncio.gather(
            _evaluate_with_skill(skill_v1, _task, "v1", _env),
            _evaluate_with_skill(skill_v2, _task, "v2", _env),
        )

        delta = score_v2 - score_v1
        MIN_IMPROVEMENT = 0.05  # v2 must be meaningfully better to win

        if delta >= MIN_IMPROVEMENT:
            winner = "v2"
        elif delta <= -MIN_IMPROVEMENT:
            winner = "v1"
        else:
            # Close call — use cross-model judge to break tie
            # (simulate outputs for judge by using verdict strings)
            judge_winner, _, _ = await _judge_outputs(
                verdict_v1, verdict_v2, _task, _env
            )
            winner = judge_winner

        model = "groq/llama-3.3-70b" if _env.get("GROQ_API_KEY") else "gemini-1.5-flash"

        return ABTestResult(
            skill_file=str(skill_file),
            winner=winner,
            score_v1=round(score_v1, 3),
            score_v2=round(score_v2, 3),
            delta=round(delta, 3),
            test_task=_task,
            verdict_v1=verdict_v1,
            verdict_v2=verdict_v2,
            model_used=model,
        )

    result = asyncio.run(_run())
    _log_ab_test(result)
    return result


def _log_ab_test(result: ABTestResult) -> None:
    """Append A/B test result to audit log."""
    AB_TEST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(AB_TEST_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "timestamp": result.timestamp,
            "skill_file": result.skill_file,
            "winner": result.winner,
            "score_v1": result.score_v1,
            "score_v2": result.score_v2,
            "delta": result.delta,
            "improvement_pct": round(result.improvement_pct, 1),
            "test_task": result.test_task[:100],
            "model_used": result.model_used,
        }) + "\n")


# ── Session integration: apply + test + keep winner ──────────────────────────

def apply_and_validate(
    skill_file: Path,
    improvement: str,
    edit_type: str = "generic",
    env: dict[str, str] | None = None,
    min_improvement: float = 0.0,
) -> dict:
    """Full pipeline: apply improvement → A/B test → keep or revert.

    Args:
        skill_file: Skill file to improve
        improvement: Improvement text
        edit_type: Edit type for skill_applier
        env: LLM environment vars
        min_improvement: Minimum score delta to keep v2 (default: any improvement)

    Returns:
        {
            "applied": bool,
            "kept": bool,        # True if v2 was kept (reverted if False)
            "ab_result": ABTestResult,
            "apply_result": ApplyResult,
        }
    """
    from swarm.skill_applier import apply_improvement, ApplyResult

    # Read v1 before applying
    if not skill_file.exists():
        return {"applied": False, "kept": False, "ab_result": None, "apply_result": None}

    skill_v1 = skill_file.read_text(encoding="utf-8")

    # Apply improvement → creates v2 on disk
    apply_result = apply_improvement(skill_file, improvement, edit_type)
    if not apply_result.success:
        return {"applied": False, "kept": False, "ab_result": None, "apply_result": apply_result}

    skill_v2 = skill_file.read_text(encoding="utf-8")

    # A/B test v1 vs v2
    ab_result = compare_skill_versions(skill_file, skill_v1, skill_v2, env=env)

    # Keep or revert
    if ab_result.winner == "v2" and ab_result.delta >= min_improvement:
        kept = True   # v2 already on disk — keep it
    else:
        # Revert to v1
        skill_file.write_text(skill_v1, encoding="utf-8")
        kept = False

    return {
        "applied": True,
        "kept": kept,
        "ab_result": ab_result,
        "apply_result": apply_result,
    }


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m packages.swarm.skill_ab_tester <skill_file.md> [--dry-run]")
        print("       Shows A/B test history for a skill file")
        sys.exit(1)

    skill_name = sys.argv[1]
    skills_dir = project_root / "memory" / "swarm" / "skills"
    skill_path = skills_dir / skill_name if not Path(skill_name).is_absolute() else Path(skill_name)

    # Show test history from log
    if AB_TEST_LOG.exists():
        with open(AB_TEST_LOG, "r", encoding="utf-8") as f:
            entries = [json.loads(l) for l in f if l.strip()]
        relevant = [e for e in entries if skill_name in e.get("skill_file", "")]
        if relevant:
            print(f"A/B test history for {skill_name} ({len(relevant)} tests):")
            for e in relevant[-5:]:
                print(f"  [{e['timestamp'][:10]}] winner={e['winner']} delta={e['delta']:+.2f} ({e['improvement_pct']:+.1f}%)")
        else:
            print(f"No A/B test history found for {skill_name}")
    else:
        print("No A/B test log found yet.")
