"""Coordinator — single entry point for all swarm tasks.

Combines squad_leaders.py (routing) + orchestrator.py (DAG) into one supervisor.
autonomous_run.py calls this instead of the flat perspective loop.

CEO research (Session 88, section 4.1):
"ввести один координационный агент (или малый council из 2-3), который будет
единственной точкой входа для задач и будет принимать решения о маршрутизации"

Flow:
  task description
      → make_plan()  — break into subtasks per squad
      → route()      — assign agents via squad_leaders
      → run_parallel() — asyncio.gather fan-out via Orchestrator
      → synthesize() — aggregate FindingContracts → CoordinatorResult

Usage:
    from swarm.coordinator import Coordinator

    coord = Coordinator(runner=call_agent_fn)
    result = await coord.run("audit security and UX of assessment flow")
    print(result.priority_action)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Awaitable, Callable

from loguru import logger

# Project root for evidence-gate file existence checks.
# packages/swarm/coordinator.py → parents[2] = repo root
_REPO_ROOT = Path(__file__).resolve().parents[2]

try:
    from .project_briefing import PROJECT_FACTS as _PROJECT_FACTS
except ImportError:
    _PROJECT_FACTS = ""


def _validate_evidence(finding: FindingContract) -> FindingContract:
    """Evidence-gate (Session 121, 2026-04-19).

    A finding is UNVERIFIED if ANY of:
      - evidence field is empty or <20 chars
      - every path in files[] fails os.path.exists against repo root

    UNVERIFIED findings get:
      - "⚠ UNVERIFIED: " prefix on summary
      - severity capped at INFO
      - confidence reduced to min(confidence, 0.3)

    This kills the "narrative-headline without proof" failure mode that
    made Session 121's admin audit produce generic agent output that
    CEO rightfully called Claude-can-LIE level.
    """
    unverified_reasons: list[str] = []

    if len(finding.evidence.strip()) < 20:
        unverified_reasons.append("no evidence")

    if finding.files:
        real_files = [f for f in finding.files if (_REPO_ROOT / f).exists()]
        if not real_files:
            unverified_reasons.append(f"0/{len(finding.files)} files exist")

    if unverified_reasons:
        reason = " + ".join(unverified_reasons)
        finding = finding.model_copy(update={
            "severity": Severity.INFO,
            "confidence": min(finding.confidence, 0.3),
            "summary": f"⚠ UNVERIFIED ({reason}): {finding.summary}"[:500],
        })
        logger.warning(
            "Evidence-gate flagged {agent} finding as UNVERIFIED: {reason}",
            agent=finding.agent_id,
            reason=reason,
        )

    return finding

from .contracts import (
    Category,
    CoordinatorResult,
    FindingContract,
    Impact,
    Severity,
    SubtaskContract,
)
from .orchestrator import AgentTask, Orchestrator
try:
    from .shared_memory import get_context, post_result
except ImportError:
    get_context = lambda *a, **kw: []
    post_result = lambda *a, **kw: None
try:
    from .squad_leaders import SQUADS, Squad, route_to_squad, select_agents
except ImportError:
    SQUADS = {}
    Squad = None
    route_to_squad = lambda *a, **kw: []
    select_agents = lambda *a, **kw: []


# ── Subtask planning ──────────────────────────────────────────────────────────

def make_plan(task_description: str, run_id: str = "") -> list[SubtaskContract]:
    """Break a task into subtasks — one per matched squad.

    Routing: keyword matching (no LLM call — fast, deterministic).
    If no squad matches, falls back to ALL squads (broad audit).
    """
    task_lower = task_description.lower()
    scored: list[tuple[int, Squad]] = []

    for squad in SQUADS:
        score = sum(1 for kw in squad.keywords if kw in task_lower)
        if score > 0:
            scored.append((score, squad))

    # Fallback: use top 2 squads by relevance, or quality+product if zero match
    if not scored:
        logger.debug("Coordinator: no keyword match — using QUALITY + PRODUCT as default squads")
        try:
            from .squad_leaders import get_squad
            defaults = [get_squad("QUALITY"), get_squad("PRODUCT")]
            scored = [(1, s) for s in defaults if s]
        except ImportError:
            logger.warning("squad_leaders not found — cannot route task")
            return []

    # Sort descending by relevance, cap at 3 squads to avoid explosion
    scored.sort(key=lambda x: -x[0])
    selected_squads = [squad for _, squad in scored[:3]]

    subtasks = []
    for i, squad in enumerate(selected_squads):
        agents = select_agents(squad, task_description, max_agents=3)
        subtask = SubtaskContract(
            task_id=f"{run_id}-{squad.name.lower()}-{i}",
            agent_id=agents[0],  # squad leader is primary executor
            instruction=(
                f"{_PROJECT_FACTS}\n\n"
                f"You are the {squad.name} squad leader ({squad.leader}). "
                f"Your squad members available: {', '.join(agents[1:])}. "
                f"Task: {task_description}. "
                f"Apply your squad's domain expertise: {squad.description}."
            ),
            context={
                "squad_name": squad.name,
                "squad_agents": agents,
                "run_id": run_id,
            },
            depends_on=[],  # squads run in parallel by default
            max_tokens=1024,
        )
        subtasks.append(subtask)

    logger.info(
        "Coordinator plan: {n} subtasks across squads {squads}",
        n=len(subtasks),
        squads=[s.task_id.split("-")[1] for s in subtasks],
    )
    return subtasks


# ── FindingContract extraction ────────────────────────────────────────────────

def _parse_finding(raw: dict | str, agent_id: str, task_id: str, run_id: str) -> FindingContract | None:
    """Try to extract a FindingContract from raw agent output.

    Handles: full JSON dict, stringified JSON, and free-text fallback.
    """
    if isinstance(raw, str):
        # Try to extract JSON object from string
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                raw = json.loads(m.group())
            except json.JSONDecodeError:
                # Pure text fallback — wrap in INFO finding
                return FindingContract(
                    severity=Severity.INFO,
                    category=Category.PRODUCT,
                    files=[],
                    summary=raw[:400],
                    recommendation="Review this finding manually — no structured output.",
                    confidence=0.3,
                    est_impact=Impact.LOW,
                    agent_id=agent_id,
                    task_id=task_id,
                    run_id=run_id,
                )

    if not isinstance(raw, dict):
        return None

    try:
        # Handle both FindingContract schema AND old autonomous_run schema
        severity_raw = raw.get("severity", "INFO")
        # Map old schema severity values to contract enum
        _sev_map = {
            "critical": "P0", "high": "P1", "medium": "P2", "low": "INFO",
            "P0": "P0", "P1": "P1", "P2": "P2", "INFO": "INFO",
        }
        severity_raw = _sev_map.get(severity_raw, "INFO")

        category_raw = raw.get("category", "product")
        # Normalize old type field as category hint
        if category_raw not in [c.value for c in Category]:
            type_val = raw.get("type", "")
            _cat_map = {
                "security": "security", "code_review": "infra", "escalation": "product",
                "idea": "product", "complaint": "product",
            }
            category_raw = _cat_map.get(type_val, "product")

        # summary: old schema uses "content" or "title"
        summary = raw.get("summary") or raw.get("content") or raw.get("title") or ""
        if isinstance(summary, dict):
            summary = json.dumps(summary)[:400]
        summary = str(summary)[:400]

        recommendation = raw.get("recommendation", "")
        if not recommendation:
            recommendation = summary[:200] if summary else "See summary."
        recommendation = str(recommendation)[:400]

        if len(summary) < 10:
            summary = (summary + " " + recommendation)[:400]
        if len(recommendation) < 10:
            recommendation = "Review and address this finding."

        return FindingContract(
            severity=Severity(severity_raw),
            category=Category(category_raw) if category_raw in [c.value for c in Category] else Category.PRODUCT,
            files=raw.get("files", []),
            summary=summary,
            recommendation=recommendation,
            confidence=float(raw.get("confidence", 0.5)),
            est_impact=Impact(raw.get("est_impact", "medium")) if raw.get("est_impact") in [i.value for i in Impact] else Impact.MEDIUM,
            agent_id=agent_id,
            task_id=task_id,
            run_id=run_id,
        )
    except Exception as e:
        logger.debug("FindingContract parse failed for {agent}: {e}", agent=agent_id, e=str(e)[:100])
        return None


# ── Synthesis ─────────────────────────────────────────────────────────────────

def synthesize(
    tasks: dict[str, AgentTask],
    run_id: str,
    task_id: str = "coordinator",
) -> CoordinatorResult:
    """Aggregate all agent results into a CoordinatorResult.

    Priority logic: P0 > P1 > P2 > INFO, then confidence.
    """
    findings: list[FindingContract] = []
    succeeded = 0
    failed = 0

    for t in tasks.values():
        if t.error:
            failed += 1
            continue
        succeeded += 1
        if not t.result:
            continue

        finding = _parse_finding(t.result, t.agent_id, t.task_id, run_id)
        if finding:
            finding = _validate_evidence(finding)
            findings.append(finding)

    # Sort: P0 first, then by confidence desc
    sev_order = {"P0": 0, "P1": 1, "P2": 2, "INFO": 3}
    findings.sort(key=lambda f: (sev_order.get(f.severity.value, 9), -f.confidence))

    # Priority action = highest severity, highest confidence finding
    priority_action: str | None = None
    if findings:
        top = findings[0]
        priority_action = f"[{top.severity.value}] {top.recommendation[:200]}"

    # Synthesis text
    if findings:
        p0s = [f for f in findings if f.severity == Severity.P0]
        p1s = [f for f in findings if f.severity == Severity.P1]
        synthesis_lines = [
            f"{len(findings)} findings from {succeeded} agents.",
            f"P0: {len(p0s)}, P1: {len(p1s)}, P2+: {len(findings) - len(p0s) - len(p1s)}.",
        ]
        if p0s:
            synthesis_lines.append(f"CRITICAL: {p0s[0].summary[:150]}")
        synthesis = " ".join(synthesis_lines)
    else:
        synthesis = f"No findings from {succeeded} agents (run_id={run_id})."

    result = CoordinatorResult(
        task_id=task_id,
        findings=findings,
        total_agents=len(tasks),
        succeeded=succeeded,
        failed=failed,
        synthesis=synthesis,
        priority_action=priority_action,
    )

    # Post aggregated result to shared memory
    try:
        post_result(
            "coordinator",
            task_id,
            {
                "synthesis": synthesis,
                "priority_action": priority_action,
                "finding_count": len(findings),
                "p0_count": len([f for f in findings if f.severity == Severity.P0]),
            },
            run_id=run_id,
            importance=8,
            category="product",
        )
    except Exception:
        pass

    return result


# ── LLM-backed team-synthesis step (Atlas voice, fan-in to one answer) ───────


async def llm_synthesize_team_answer(
    task_description: str,
    findings: list[FindingContract],
    priority_action: str | None,
) -> str | None:
    """Take all agent findings, return ONE coherent team recommendation in Atlas voice.

    Added 2026-04-20 Session 122 per SPRINT-PLAN T3.2. Fixes the "bot dumps 5 opinions,
    CEO reads херня" failure mode. Mechanical synthesize() still runs first (fast,
    deterministic, populates result.synthesis); this function adds a human-readable
    team answer on top.

    Model: Anthropic Sonnet 4.5 direct (CEO paid tier, best at Russian storytelling +
    long-context persona). Fallback chain not wired here on purpose — if Anthropic is
    unreachable, we return None and caller uses mechanical synthesis. Don't ALSO try
    Cerebras/NVIDIA here — if the primary path fails, the value of "team voice" isn't
    worth further latency on a bot-reply critical path.

    Contract:
      - Input: task CEO asked + all findings (including UNVERIFIED ones for transparency)
      - Output: 3-5 Russian paragraphs in Atlas voice, OR None on failure
      - Cost: ~2-5k input tokens, ~500 output tokens = ~$0.014 per call
      - Latency: ~2-4 seconds

    Safety: None return is GRACEFUL. Caller checks for None and uses result.synthesis.
    """
    import os

    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not anthropic_key:
        return None
    if not findings:
        return None

    # Compact findings into a block the LLM can reason over
    finding_lines = []
    for i, f in enumerate(findings[:10], 1):  # cap at 10 to keep prompt small
        sev = f.severity.value
        summary = f.summary[:300]
        rec = f.recommendation[:300]
        agent = f.agent_id
        conf = f"{f.confidence:.0%}"
        evidence_tag = " [UNVERIFIED]" if "⚠ UNVERIFIED" in summary else ""
        finding_lines.append(
            f"{i}. [{sev}]{evidence_tag} {agent} ({conf} conf): {summary} → {rec}"
        )
    findings_block = "\n".join(finding_lines)

    system_prompt = (
        "Ты — Атлас, нервная система экосистемы VOLAURA (verified professional talent platform), MindShift, "
        "LifeSim, BrandedBy, ZEUS. Ты синтезируешь findings команды специализированных агентов в ОДИН связный "
        "ответ для CEO — в Атлас-голосе: короткие русские абзацы, storytelling, без bullet-списков, без ** жирного, "
        "без ## заголовков, максимум 3-5 абзацев. Пиши прозой, называй findings своими словами, а не пересказом. "
        "Отмечай UNVERIFIED findings как 'непроверенные' — не маскируй неопределённость. Один concrete next-action "
        "в конце (что делать дальше). НЕ пиши 'based on the findings', 'team recommends' — говори от первого лица "
        "во множественном числе ('мы видим', 'команда смотрит', 'что делать'). Позиционный замок: VOLAURA — "
        "verified professional talent platform, слово 'volunteer' запрещено, используй professional/talent/specialist."
    )

    user_message = (
        f"CEO спросил: {task_description}\n\n"
        f"Агентские findings ({len(findings)}):\n{findings_block}\n\n"
        f"Top-priority action из mechanical synthesis: {priority_action or '(нет)'}\n\n"
        f"Твой ответ: 3-5 абзацев Атлас-голосом, подытоживающие что команда увидела и один concrete next-step."
    )

    try:
        import httpx

        async with httpx.AsyncClient(timeout=30) as hc:
            r = await hc.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-5-20250929",
                    "max_tokens": 1500,
                    "temperature": 0.7,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_message}],
                },
            )
            if r.status_code != 200:
                logger.warning(
                    "Anthropic team-synth HTTP {s}: {b}",
                    s=r.status_code,
                    b=r.text[:200],
                )
                return None
            data = r.json()
            text_blocks = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
            text = "".join(text_blocks).strip()
            return text or None
    except Exception as e:
        logger.warning("llm_synthesize_team_answer exception: {e}", e=str(e)[:200])
        return None


# ── Main Coordinator class ────────────────────────────────────────────────────

class Coordinator:
    """Single entry point for all swarm tasks.

    Wraps make_plan → route → run_parallel → synthesize into one call.

    Args:
        runner: async fn(agent_id, input_dict) -> dict | None
                (plugged in from autonomous_run.py or coordinator CLI)
    """

    def __init__(
        self,
        runner: Callable[[str, dict], Awaitable[dict | None]],
        run_id: str | None = None,
    ):
        self.runner = runner
        self.run_id = run_id or f"coord-{int(time.time())}"

    async def run(self, task_description: str) -> CoordinatorResult:
        """Full pipeline: plan → dispatch → synthesize."""
        logger.info(
            "Coordinator.run: '{task}' (run_id={run_id})",
            task=task_description[:80],
            run_id=self.run_id,
        )

        # Step 1: Make plan
        subtasks = make_plan(task_description, run_id=self.run_id)

        # Step 2: Build AgentTasks for orchestrator
        # Inject shared memory from previous runs as context
        try:
            prior_context = get_context(self.run_id)
        except Exception:
            prior_context = []

        orch_tasks = []
        for subtask in subtasks:
            input_data = {
                "instruction": subtask.instruction,
                "task_description": task_description,
                "run_id": self.run_id,
                **subtask.context,
            }
            if prior_context:
                input_data["prior_findings"] = prior_context[:5]  # last 5 relevant facts

            orch_tasks.append(
                AgentTask(
                    task_id=subtask.task_id,
                    agent_id=subtask.agent_id,
                    input=input_data,
                    depends_on=subtask.depends_on,
                )
            )

        # Step 3: Run via orchestrator (asyncio.gather fan-out with DAG support)
        orch = Orchestrator(
            runner=self.runner,
            on_complete=self._on_agent_complete,
            run_id=self.run_id,
        )
        for task in orch_tasks:
            orch.add_task(task)

        completed_tasks = await orch.run_all(timeout=120)

        # Step 4: Synthesize findings (mechanical aggregation — fast, deterministic)
        result = synthesize(completed_tasks, run_id=self.run_id, task_id=f"coord-{task_description[:40]}")

        # Step 5: LLM-backed team synthesis (Atlas voice, Russian, one coherent answer).
        # Best-effort — if Anthropic is unreachable or no key set, result.team_recommendation
        # stays None and callers use mechanical synthesis as today. Not on the critical path.
        try:
            team_answer = await llm_synthesize_team_answer(
                task_description=task_description,
                findings=result.findings,
                priority_action=result.priority_action,
            )
            if team_answer:
                result = result.model_copy(update={"team_recommendation": team_answer})
        except Exception as e:
            logger.warning("LLM team-synthesis failed (non-blocking): {e}", e=str(e)[:200])

        logger.info(
            "Coordinator done: {n} findings, priority={p}",
            n=len(result.findings),
            p=(result.priority_action or "none")[:60],
        )
        return result

    async def _on_agent_complete(self, task: AgentTask, result: dict) -> None:
        """Callback when an agent finishes — log and optionally escalate."""
        finding = _parse_finding(result, task.agent_id, task.task_id, self.run_id)
        if finding and finding.severity in (Severity.P0, Severity.P1):
            logger.warning(
                "Coordinator ESCALATION: [{sev}] {agent} → {summary}",
                sev=finding.severity.value,
                agent=task.agent_id,
                summary=finding.summary[:100],
            )


# ── CLI entry point ───────────────────────────────────────────────────────────

async def _demo_runner(agent_id: str, input_data: dict) -> dict | None:
    """Demo runner — returns a synthetic finding for testing coordinator flow."""
    instruction = input_data.get("instruction", "")
    squad_name = input_data.get("squad_name", "UNKNOWN")
    return {
        "severity": "P2",
        "category": "product",
        "summary": f"[{squad_name}] {agent_id} analyzed: {instruction[:120]}",
        "recommendation": f"Review findings from {squad_name} squad.",
        "confidence": 0.7,
        "files": [],
        "est_impact": "medium",
    }


def _make_real_runner():
    """Build a runner that calls real LLM APIs if keys are available, otherwise falls back to demo."""
    import os
    env = dict(os.environ)
    has_nvidia = bool(env.get("NVIDIA_API_KEY"))
    has_groq = bool(env.get("GROQ_API_KEY"))
    has_gemini = bool(env.get("GEMINI_API_KEY"))

    if not (has_nvidia or has_groq or has_gemini):
        logger.info("No LLM keys found — using demo runner")
        return _demo_runner

    async def _llm_runner(agent_id: str, input_data: dict) -> dict | None:
        instruction = input_data.get("instruction", "")
        squad_name = input_data.get("squad_name", agent_id)
        prompt = (
            f"You are {agent_id}, a specialist in the {squad_name} domain.\n"
            f"Task: {instruction}\n\n"
            f"Respond with a JSON object containing: severity (P0/P1/P2/INFO), "
            f"category (security/qa/product/growth/infra/ecosystem), "
            f"summary (what you found), recommendation (what to do), "
            f"confidence (0.0-1.0), files (list of affected files).\n"
            f"If nothing notable, set severity=INFO."
        )
        try:
            from .autonomous_run import _call_agent
            return await _call_agent(prompt, agent_id, env)
        except ImportError:
            return await _demo_runner(agent_id, input_data)

    logger.info("LLM runner ready (NVIDIA={n}, Groq={g}, Gemini={ge})", n=has_nvidia, g=has_groq, ge=has_gemini)
    return _llm_runner


if __name__ == "__main__":
    import sys

    task = " ".join(sys.argv[1:]) or "audit security and UX of the assessment flow"
    print(f"Coordinator: '{task}'\n")

    async def _main():
        runner = _make_real_runner()
        coord = Coordinator(runner=runner)
        result = await coord.run(task)
        # Team answer FIRST (what CEO actually wants to read). If no Anthropic key or
        # LLM failed, team_recommendation is None and we surface mechanical synthesis instead.
        if result.team_recommendation:
            print("\n=== TEAM ANSWER (Atlas voice, Sonnet 4.5 synthesized) ===\n")
            print(result.team_recommendation)
            print("\n=== MECHANICAL BREAKDOWN ===")
        else:
            print("\n=== SYNTHESIS (mechanical — no Anthropic key or LLM unreachable) ===")
        print(f"Synthesis: {result.synthesis}")
        print(f"Priority:  {result.priority_action}")
        print(f"Agents:    {result.total_agents} total, {result.succeeded} succeeded, {result.failed} failed")
        print(f"Findings:  {len(result.findings)}")
        for f in result.findings[:5]:
            print(f"  [{f.severity.value}] {f.agent_id}: {f.summary[:80]}")

    asyncio.run(_main())
