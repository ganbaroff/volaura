#!/usr/bin/env python3
"""Outcome Verifier — gives "done" a definition.

Problem: agents declare tasks DONE with no evidence. CTO cannot tell if
a task was actually completed or just marked as such.

Solution: two-tier verification.
  Tier 1 (deterministic, free):
    - File existence checks (does the promised file exist?)
    - Test count delta (did tests increase?)
    - Import check (can the new module be imported?)
  Tier 2 (LLM judge, ~$0.001):
    - Given: task description + before state + after state
    - Returns: confidence that the task was actually completed
    - Only runs when Tier 1 confidence < 0.9

Usage:
    from swarm.outcome_verifier import verify_outcome, record_outcome

    result = verify_outcome(
        task={"title": "Add heartbeat_gate.py", "expected_files": ["packages/swarm/heartbeat_gate.py"]},
        before_state={"test_count": 667, "files": []},
        after_state={"test_count": 667, "files": ["packages/swarm/heartbeat_gate.py"]},
    )
    record_outcome(task_id="sprint1-1.1", result=result)
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Paths ─────────────────────────────────────────────────────────────────────

project_root = Path(__file__).parent.parent.parent
OUTCOMES_LOG = project_root / "memory" / "swarm" / "outcome-log.jsonl"


# ── Result types ───────────────────────────────────────────────────────────────

@dataclass
class VerificationResult:
    """Result of a task outcome verification."""
    task_id: str
    task_title: str
    tier: int                          # 1 = deterministic, 2 = LLM judge
    confidence: float                  # 0.0 – 1.0
    verdict: str                       # "complete" | "partial" | "incomplete" | "unknown"
    evidence: list[str] = field(default_factory=list)   # what was verified
    gaps: list[str] = field(default_factory=list)       # what was missing
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_done(self) -> bool:
        return self.confidence >= 0.8 and self.verdict in ("complete", "partial")

    def summary(self) -> str:
        icon = "[OK]" if self.is_done else ("[PARTIAL]" if self.verdict == "partial" else "[FAIL]")
        return f"{icon} {self.verdict.upper()} ({self.confidence:.0%}) -- {self.task_title[:60]}"


# ── Tier 1: Deterministic checks ──────────────────────────────────────────────

def _check_expected_files(
    expected_files: list[str],
    project_root: Path,
) -> tuple[list[str], list[str]]:
    """Return (found, missing) for expected files."""
    found, missing = [], []
    for f in expected_files:
        if (project_root / f).exists():
            found.append(f)
        else:
            missing.append(f)
    return found, missing


def _check_test_delta(before_count: int | None, after_count: int | None) -> tuple[str, float]:
    """Evaluate test count change. Returns (evidence, confidence_delta)."""
    if before_count is None or after_count is None:
        return "test count not provided — skipped", 0.0
    delta = after_count - before_count
    if delta > 0:
        return f"tests: +{delta} new tests (was {before_count}, now {after_count})", 0.2
    elif delta == 0:
        return f"tests: unchanged at {after_count} — may be OK for infra tasks", 0.0
    else:
        return f"tests: REGRESSION — dropped {abs(delta)} tests (was {before_count}, now {after_count})", -0.3


def _check_import_safe(module_path: str, project_root: Path) -> tuple[str, bool]:
    """Try to import a module (syntax check without execution)."""
    full_path = project_root / module_path
    if not full_path.exists():
        return f"cannot check import — {module_path} not found", False
    try:
        import ast
        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        return f"syntax valid: {module_path}", True
    except SyntaxError as e:
        return f"SYNTAX ERROR in {module_path}: {e}", False
    except Exception as e:
        return f"import check error: {e}", False


def _tier1_check(task: dict[str, Any], project_root: Path) -> VerificationResult:
    """Run deterministic Tier 1 checks."""
    task_id = task.get("id", "unknown")
    task_title = task.get("title", "Untitled task")
    expected_files = task.get("expected_files", [])
    before_tests = task.get("before_test_count")
    after_tests = task.get("after_test_count")
    check_imports = task.get("check_imports", [])

    evidence: list[str] = []
    gaps: list[str] = []
    confidence = 0.0

    # File existence checks (primary signal)
    if expected_files:
        found, missing = _check_expected_files(expected_files, project_root)
        file_ratio = len(found) / len(expected_files)
        confidence += file_ratio * 0.6   # files are 60% of confidence

        if found:
            evidence.append(f"files found ({len(found)}/{len(expected_files)}): {', '.join(found)}")
        if missing:
            gaps.append(f"files missing: {', '.join(missing)}")
    else:
        # No expected files specified — give partial credit (can't verify but can't penalize)
        confidence += 0.3
        evidence.append("no expected_files specified — file check skipped")

    # Test delta check
    test_ev, test_delta = _check_test_delta(before_tests, after_tests)
    evidence.append(test_ev)
    confidence = min(1.0, max(0.0, confidence + test_delta))

    # Import checks
    for module_path in check_imports:
        msg, ok = _check_import_safe(module_path, project_root)
        if ok:
            evidence.append(msg)
            confidence = min(1.0, confidence + 0.05)
        else:
            gaps.append(msg)
            confidence = max(0.0, confidence - 0.1)

    # Verdict from confidence
    confidence = round(confidence, 3)
    if confidence >= 0.85:
        verdict = "complete"
    elif confidence >= 0.50:
        verdict = "partial"
    elif confidence >= 0.20:
        verdict = "incomplete"
    else:
        verdict = "unknown"

    return VerificationResult(
        task_id=task_id,
        task_title=task_title,
        tier=1,
        confidence=confidence,
        verdict=verdict,
        evidence=evidence,
        gaps=gaps,
    )


# ── Tier 2: LLM judge ─────────────────────────────────────────────────────────

async def _tier2_llm_judge(
    task: dict[str, Any],
    tier1_result: VerificationResult,
    env: dict[str, str],
) -> VerificationResult:
    """LLM judge for ambiguous Tier 1 results.

    Only called when Tier 1 confidence < 0.9 to save tokens.
    Uses Groq haiku-equivalent (llama-3.3-70b) for cost efficiency.
    """
    task_title = task.get("title", "")
    task_description = task.get("description", task.get("content", ""))[:600]
    tier1_summary = f"Evidence: {tier1_result.evidence}\nGaps: {tier1_result.gaps}"

    judge_prompt = f"""You are a task completion judge. Based on the evidence, determine if this task was actually completed.

TASK: {task_title}
DESCRIPTION: {task_description}

TIER 1 VERIFICATION:
{tier1_summary}

Rate completion confidence from 0.0 to 1.0 and give a verdict.

Reply with JSON only:
{{"confidence": 0.0-1.0, "verdict": "complete|partial|incomplete|unknown", "reasoning": "1 sentence"}}"""

    groq_key = env.get("GROQ_API_KEY", "")
    gemini_key = env.get("GEMINI_API_KEY", "")

    try:
        if groq_key:
            from groq import AsyncGroq
            client = AsyncGroq(api_key=groq_key)
            resp = await asyncio.wait_for(
                client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": judge_prompt}],
                    temperature=0.1,
                    max_tokens=200,
                    response_format={"type": "json_object"},
                ),
                timeout=10.0,
            )
            raw = resp.choices[0].message.content or "{}"
        elif gemini_key:
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
            raw = resp.text or "{}"
        else:
            return tier1_result  # No LLM available — return Tier 1 result

        data = json.loads(raw)
        llm_confidence = float(data.get("confidence", tier1_result.confidence))
        llm_verdict = data.get("verdict", tier1_result.verdict)
        llm_reasoning = data.get("reasoning", "")

        # Blend Tier 1 + Tier 2 (weighted: T1=40%, T2=60%)
        blended = round(0.4 * tier1_result.confidence + 0.6 * llm_confidence, 3)

        return VerificationResult(
            task_id=tier1_result.task_id,
            task_title=tier1_result.task_title,
            tier=2,
            confidence=blended,
            verdict=llm_verdict,
            evidence=tier1_result.evidence + [f"LLM judge: {llm_reasoning}"],
            gaps=tier1_result.gaps,
        )

    except Exception:
        return tier1_result  # LLM failed — fall back to Tier 1


# ── Public API ─────────────────────────────────────────────────────────────────

def verify_outcome(
    task: dict[str, Any],
    use_llm: bool = True,
    env: dict[str, str] | None = None,
) -> VerificationResult:
    """Verify task completion. Synchronous wrapper.

    Args:
        task: Task dict with keys:
            id (str): unique task ID
            title (str): human-readable title
            expected_files (list[str]): files that should exist after task
            before_test_count (int): test count before task
            after_test_count (int): test count after task
            check_imports (list[str]): Python file paths to check for syntax validity
            description (str): full task description (for Tier 2 judge)
        use_llm (bool): whether to run Tier 2 if Tier 1 < 0.9
        env (dict): environment variables (for LLM keys)

    Returns:
        VerificationResult
    """
    tier1 = _tier1_check(task, project_root)

    if not use_llm or tier1.confidence >= 0.9:
        return tier1

    # Tier 2 needed
    _env = env or dict(os.environ)
    return asyncio.run(_tier2_llm_judge(task, tier1, _env))


def record_outcome(task_id: str, result: VerificationResult) -> None:
    """Append verification result to outcome log.

    Args:
        task_id: Identifier for the task
        result: VerificationResult to record
    """
    OUTCOMES_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = asdict(result)
    entry["task_id"] = task_id
    with open(OUTCOMES_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_recent_outcomes(n: int = 10) -> list[dict]:
    """Read the last N outcome records."""
    if not OUTCOMES_LOG.exists():
        return []
    with open(OUTCOMES_LOG, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]
    records = []
    for line in lines[-n:]:
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return records


# ── Convenience: Sprint 1 self-verification ────────────────────────────────────

SPRINT_1_TASKS = [
    {
        "id": "sprint1-1.1",
        "title": "Heartbeat Gate",
        "expected_files": ["packages/swarm/heartbeat_gate.py"],
        "check_imports": ["packages/swarm/heartbeat_gate.py"],
        "description": "Create heartbeat_gate.py with should_run_swarm() function",
    },
    {
        "id": "sprint1-1.2",
        "title": "Proposal Verifier",
        "expected_files": ["packages/swarm/proposal_verifier.py"],
        "check_imports": ["packages/swarm/proposal_verifier.py"],
        "description": "Create proposal_verifier.py with verify_proposal_references()",
    },
    {
        "id": "sprint1-1.3",
        "title": "Outcome Verifier",
        "expected_files": ["packages/swarm/outcome_verifier.py"],
        "check_imports": ["packages/swarm/outcome_verifier.py"],
        "description": "Create outcome_verifier.py with verify_outcome() and record_outcome()",
    },
    {
        "id": "sprint1-2.1",
        "title": "Suggestion Engine",
        "expected_files": ["packages/swarm/suggestion_engine.py"],
        "check_imports": ["packages/swarm/suggestion_engine.py"],
        "description": "Create suggestion_engine.py with generate_suggestions()",
    },
]


if __name__ == "__main__":
    print("=== Sprint 1 Self-Verification ===\n")
    all_done = True
    for task in SPRINT_1_TASKS:
        result = verify_outcome(task, use_llm=False)  # Tier 1 only for self-check
        print(result.summary())
        if result.gaps:
            for gap in result.gaps:
                print(f"    ⚠ {gap}")
        record_outcome(task["id"], result)
        if not result.is_done:
            all_done = False
    print(f"\n{'[ALL OK] ALL SPRINT 1 TASKS VERIFIED' if all_done else '[INCOMPLETE] SOME TASKS NEED ATTENTION'}")
