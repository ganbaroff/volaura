"""
Reasoning Graph — structured inter-agent communication layer.

Innovation: agents don't see each other's full responses (prevents herding).
Instead, they see a GRAPH of reasoning nodes — structured summaries with
confidence scores and evidence references. Each agent can trace WHY another
agent reached their conclusion.

Architecture:
  Round 1: Blind dispatch (as before)
      ↓
  PM extracts ReasoningNodes from each AgentResult
      ↓
  Round 2: Each agent sees the graph (not raw answers)
  - Can update their vote with explanation of what changed
  - PM tracks who influenced whom (provenance)
      ↓
  Final aggregation weights "conviction" (agents who held firm) higher

No existing system does this:
- Moltbook: agents share outputs, not reasoning chains
- A2A protocol: task delegation, not reasoning visibility
- Hindsight: single-agent memory, no cross-agent reasoning
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from .types import AgentResult, DimensionScores


class ReasoningNode(BaseModel):
    """One agent's reasoning, structured for other agents to read.

    This is NOT the full AgentResult — it's a compressed, structured
    summary that preserves the key argument without the noise.
    """

    node_id: str = ""  # hash of agent_id + winner + key_argument
    agent_id: str = ""
    provider: str = ""
    model: str = ""

    # What they decided
    winner: str = ""
    confidence: float = 0.0  # 0.0-1.0

    # WHY they decided it (structured, not free text)
    key_argument: str = ""  # 1-2 sentence core reasoning (max 200 chars)
    evidence_type: str = ""  # "empirical" | "theoretical" | "experiential" | "intuitive"
    strongest_dimension: str = ""  # which dimension drove the decision
    weakest_dimension: str = ""  # which dimension they're least confident about

    # What they're worried about
    top_concern: str = ""  # single biggest risk (max 150 chars)
    concern_severity: float = 0.0  # 0.0 (minor) to 1.0 (critical)

    # Meta
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @classmethod
    def from_agent_result(cls, result: AgentResult) -> ReasoningNode:
        """Extract structured reasoning from an agent's response."""
        if not result.json_valid or result.error:
            return cls(agent_id=result.agent_id, provider=result.provider)

        # Find strongest and weakest dimension across all scored paths
        strongest = ""
        weakest = ""
        if result.scores:
            winner_scores = result.scores.get(result.winner)
            if winner_scores:
                dims = {
                    "technical": winner_scores.technical,
                    "user_impact": winner_scores.user_impact,
                    "dev_speed": winner_scores.dev_speed,
                    "flexibility": winner_scores.flexibility,
                    "risk": winner_scores.risk,
                }
                strongest = max(dims, key=lambda k: dims[k])
                weakest = min(dims, key=lambda k: dims[k])

        # Extract top concern
        top_concern = ""
        concern_severity = 0.0
        if result.concerns:
            # Pick the concern for the winner path (most relevant)
            top_concern = result.concerns.get(result.winner, "")
            if not top_concern:
                # Fallback to any concern
                top_concern = next(iter(result.concerns.values()), "")
            top_concern = top_concern[:150]
            # Estimate severity from risk score
            if result.scores and result.winner in result.scores:
                risk = result.scores[result.winner].risk
                concern_severity = max(0.0, 1.0 - risk / 10.0)

        # Classify evidence type from reasoning
        reason = result.reason or ""
        evidence_type = _classify_evidence(reason)

        key_arg = reason[:200] if reason else ""

        node_id = hashlib.md5(
            f"{result.agent_id}:{result.winner}:{key_arg[:50]}".encode()
        ).hexdigest()[:12]

        return cls(
            node_id=node_id,
            agent_id=result.agent_id,
            provider=result.provider,
            model=result.model,
            winner=result.winner,
            confidence=result.confidence,
            key_argument=key_arg,
            evidence_type=evidence_type,
            strongest_dimension=strongest,
            weakest_dimension=weakest,
            top_concern=top_concern,
            concern_severity=concern_severity,
        )


class ReasoningGraph(BaseModel):
    """The shared reasoning graph that agents see in Round 2.

    Contains all nodes from Round 1, plus computed meta-signals
    that help agents understand the collective state.
    """

    nodes: list[ReasoningNode] = []

    # Computed signals (filled by build())
    consensus_winner: str = ""
    consensus_strength: float = 0.0
    dominant_argument: str = ""  # most common evidence type
    unaddressed_concerns: list[str] = []  # concerns nobody countered
    dimension_disagreements: list[str] = []  # dimensions where agents disagree most

    @classmethod
    def build(cls, results: list[AgentResult]) -> ReasoningGraph:
        """Build a reasoning graph from Round 1 results."""
        nodes = []
        for r in results:
            if r.json_valid and not r.error:
                nodes.append(ReasoningNode.from_agent_result(r))

        if not nodes:
            return cls()

        # Compute consensus
        votes: dict[str, int] = {}
        for n in nodes:
            if n.winner:
                votes[n.winner] = votes.get(n.winner, 0) + 1

        total = sum(votes.values())
        consensus_winner = max(votes, key=lambda k: votes[k]) if votes else ""
        consensus_strength = votes.get(consensus_winner, 0) / total if total else 0.0

        # Find dominant evidence type
        evidence_types: dict[str, int] = {}
        for n in nodes:
            if n.evidence_type:
                evidence_types[n.evidence_type] = evidence_types.get(n.evidence_type, 0) + 1
        dominant = max(evidence_types, key=lambda k: evidence_types[k]) if evidence_types else ""

        # Find unaddressed concerns (high severity, from minority)
        minority_concerns = [
            n.top_concern
            for n in nodes
            if n.winner != consensus_winner and n.concern_severity > 0.5 and n.top_concern
        ]

        # Find dimension disagreements
        dim_winners: dict[str, set[str]] = {}
        for n in nodes:
            if n.strongest_dimension:
                dim_winners.setdefault(n.strongest_dimension, set()).add(n.winner)
        disagreements = [dim for dim, winners in dim_winners.items() if len(winners) > 1]

        return cls(
            nodes=nodes,
            consensus_winner=consensus_winner,
            consensus_strength=round(consensus_strength, 2),
            dominant_argument=dominant,
            unaddressed_concerns=minority_concerns[:5],
            dimension_disagreements=disagreements,
        )

    def to_agent_prompt(self) -> str:
        """Render the graph as text for injection into Round 2 prompts.

        Agents see structured reasoning, NOT raw responses.
        This prevents herding while enabling informed revision.
        """
        if not self.nodes:
            return ""

        lines = [
            "=== REASONING GRAPH FROM ROUND 1 ===",
            f"Agents participated: {len(self.nodes)}",
            f"Current consensus: {self.consensus_winner} ({self.consensus_strength:.0%})",
            "",
            "INDIVIDUAL REASONING NODES:",
        ]

        for n in self.nodes:
            lines.append(
                f"  [{n.provider}/{n.model.split('/')[-1][:15]}] "
                f"chose '{n.winner}' (confidence: {n.confidence:.0%})"
            )
            if n.key_argument:
                lines.append(f"    Argument: {n.key_argument[:150]}")
            if n.strongest_dimension:
                lines.append(
                    f"    Strongest dim: {n.strongest_dimension} | "
                    f"Weakest: {n.weakest_dimension}"
                )
            if n.top_concern:
                lines.append(
                    f"    Concern ({n.concern_severity:.0%} severity): {n.top_concern}"
                )
            lines.append("")

        if self.unaddressed_concerns:
            lines.append("UNADDRESSED CONCERNS (nobody countered these):")
            for c in self.unaddressed_concerns:
                lines.append(f"  - {c}")
            lines.append("")

        if self.dimension_disagreements:
            lines.append(
                f"DIMENSION DISAGREEMENTS (agents disagree on: "
                f"{', '.join(self.dimension_disagreements)})"
            )
            lines.append("")

        lines.extend([
            "YOUR TASK IN ROUND 2:",
            "- Review the graph above. Has any agent raised a point you missed?",
            "- You MAY change your vote. If you do, explain WHAT changed and WHY.",
            "- You MAY keep your vote. Conviction is valued — don't change just to conform.",
            "- Focus on UNADDRESSED CONCERNS — these are blind spots.",
            "=== END REASONING GRAPH ===",
        ])

        return "\n".join(lines)


class RevisionRecord(BaseModel):
    """Tracks what an agent changed between Round 1 and Round 2."""

    agent_id: str
    round1_winner: str
    round2_winner: str
    changed: bool = False
    revision_reason: str = ""  # why they changed (or why they held firm)
    influenced_by: list[str] = []  # node_ids that influenced the change


class GraphAggregation(BaseModel):
    """Final aggregation after Round 2, incorporating conviction tracking."""

    graph: ReasoningGraph = Field(default_factory=ReasoningGraph)
    revisions: list[RevisionRecord] = []

    # Conviction metrics
    agents_who_held_firm: int = 0
    agents_who_changed: int = 0
    conviction_ratio: float = 0.0  # held_firm / total

    def compute_conviction_weights(self) -> dict[str, float]:
        """Agents who held their position get a conviction bonus.

        This prevents herding: if everyone switches to the majority,
        those who originally held get weighted higher (they saw the
        graph and STILL believed their answer was right).
        """
        weights: dict[str, float] = {}
        for rev in self.revisions:
            if rev.changed:
                # Changed vote — standard weight (they were influenced)
                weights[rev.agent_id] = 1.0
            else:
                # Held firm — conviction bonus
                weights[rev.agent_id] = 1.15
        return weights


def _classify_evidence(reason: str) -> str:
    """Classify what type of evidence the agent used."""
    reason_lower = reason.lower()

    empirical_markers = ["data", "benchmark", "measured", "test", "result", "evidence", "proven"]
    theoretical_markers = ["research", "paper", "study", "theory", "principle", "framework"]
    experiential_markers = ["experience", "past", "previously", "learned", "seen", "tried"]

    if any(m in reason_lower for m in empirical_markers):
        return "empirical"
    if any(m in reason_lower for m in theoretical_markers):
        return "theoretical"
    if any(m in reason_lower for m in experiential_markers):
        return "experiential"
    return "intuitive"
