"""Typed output contracts for all swarm agents.

Every agent MUST return a FindingContract. No more free-text proposals.
This enables: career ladder scoring, blackboard storage, dashboard display,
coordinator routing, and automated triage.

CEO research (Session 88, section 4.2):
"Сейчас вывод многих агентов — свободный текст; это сложно агрегировать и оценивать."
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    P0 = "P0"  # Critical — blocks launch, security exploit, data loss
    P1 = "P1"  # High — significant impact, fix this sprint
    P2 = "P2"  # Medium — should fix, not blocking
    INFO = "INFO"  # Informational — nice to know


class Category(str, Enum):
    SECURITY = "security"
    UX = "ux"
    PERFORMANCE = "perf"
    GROWTH = "growth"
    INFRA = "infra"
    PRODUCT = "product"
    QA = "qa"
    LEGAL = "legal"
    ECOSYSTEM = "ecosystem"


class Impact(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class FindingContract(BaseModel):
    """Universal output schema for all swarm agents.

    Every agent finding, proposal, and audit result must conform to this schema.
    Free-text outputs are rejected by the coordinator.
    """

    severity: Severity = Field(description="P0=critical, P1=high, P2=medium, INFO=informational")
    category: Category = Field(description="Domain category for routing and filtering")
    files: list[str] = Field(default_factory=list, description="Affected file paths relative to project root")
    summary: str = Field(min_length=10, max_length=500, description="What was found — one paragraph")
    recommendation: str = Field(min_length=10, max_length=500, description="What to do about it — specific action")
    confidence: float = Field(ge=0.0, le=1.0, description="Agent's confidence in this finding")
    est_impact: Impact = Field(default=Impact.MEDIUM, description="Estimated impact if not addressed")

    # Evidence-gate (Session 121, 2026-04-19): no claim without receipts.
    # Free-text quotes of grep output, file snippets, command results, URL status
    # codes. Coordinator rejects findings where this is empty OR all `files`
    # paths are bogus by flagging UNVERIFIED and capping severity at INFO.
    evidence: str = Field(
        default="",
        max_length=1200,
        description="Observed proof backing the finding — file snippets, command output, URL status. Empty = UNVERIFIED.",
    )

    # Metadata (set by coordinator, not by agent)
    agent_id: str = Field(default="", description="Which agent produced this finding")
    task_id: str = Field(default="", description="Which task this finding belongs to")
    run_id: str = Field(default="", description="Which swarm run produced this")

    @field_validator("files", mode="before")
    @classmethod
    def ensure_list(cls, v):
        if isinstance(v, str):
            return [v]
        return v or []


class SubtaskContract(BaseModel):
    """Input contract for a subtask assigned by coordinator to an agent."""

    task_id: str = Field(description="Unique ID for this subtask")
    agent_id: str = Field(description="Which agent should execute this")
    instruction: str = Field(description="What the agent should do")
    context: dict = Field(default_factory=dict, description="Context from coordinator or previous agents")
    depends_on: list[str] = Field(default_factory=list, description="Task IDs that must complete first")
    max_tokens: int = Field(default=2048, description="Token budget for this subtask")


class CoordinatorResult(BaseModel):
    """Output of the coordinator after aggregating all agent findings."""

    task_id: str
    findings: list[FindingContract]
    total_agents: int
    succeeded: int
    failed: int
    synthesis: str = Field(default="", description="Coordinator's synthesis of all findings (mechanical)")
    priority_action: Optional[str] = Field(default=None, description="Single most important action to take")
    team_recommendation: Optional[str] = Field(
        default=None,
        description=(
            "LLM-synthesized team answer in Atlas voice (Russian, storytelling, 3-5 paragraphs). "
            "Populated by llm_synthesize_team_answer() when ANTHROPIC_API_KEY is set. Falls back to None silently."
        ),
    )


# ── Prompt injection helper ──────────────────────────────────────────

FINDING_SCHEMA_FOR_PROMPT = """
RESPONSE FORMAT (strict JSON — no markdown, no extra fields):
{
    "severity": "P0|P1|P2|INFO",
    "category": "security|ux|perf|growth|infra|product|qa|legal|ecosystem",
    "files": ["path/to/file.py"],
    "summary": "What you found (10-500 chars)",
    "recommendation": "What to do about it (10-500 chars)",
    "confidence": 0.0-1.0,
    "est_impact": "low|medium|high",
    "evidence": "Observed proof — file snippet / grep output / HTTP status / command result (20-1200 chars)"
}

RULES:
- "files" must be REAL paths that exist in the repo. Bogus paths trigger UNVERIFIED flag + severity cap at INFO.
- "evidence" must quote observed output (file line, grep result, curl status). NO speculation. NO "I think". Empty or <20 chars → UNVERIFIED.
- "summary" and "recommendation" are REQUIRED strings, not objects.
- Return ONLY the JSON object. No ```json``` wrapper. No explanation outside JSON.
"""
