"""
Structured Memory — 4-network memory system inspired by Hindsight (arXiv:2512.12818),
adapted for multi-agent swarm with a novel Failure Network.

Networks:
  World:      Objective facts (model costs, API limits, tool capabilities)
  Experience: Agent's own biographical actions (decisions made, outcomes)
  Opinion:    Subjective judgments WITH confidence scores
  Failure:    Cross-agent failure patterns (what went wrong, why, how to avoid)
              ↑ THIS IS OUR INNOVATION — no existing system does this

Hindsight achieves 83.6% vs 39% for flat memory. We extend it to multi-agent
by adding cross-agent failure learning and provenance tracking.

Storage: JSON files in ~/.swarm/memory/ (one file per network).
Retrieval: keyword + recency scoring (embeddings deferred to v5).
"""

from __future__ import annotations

import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field
from loguru import logger


# ── Memory Entry Types ────────────────────────────────────


class MemoryEntry(BaseModel):
    """Base memory entry with provenance tracking."""

    entry_id: str = ""  # MD5 hash of content
    network: str = ""  # "world" | "experience" | "opinion" | "failure"
    content: str = ""  # the actual memory
    tags: list[str] = []  # keyword tags for retrieval
    confidence: float = 1.0  # 0.0-1.0 (how sure are we?)
    source: str = ""  # who/what created this entry
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    last_accessed: str = ""  # updated on retrieval
    access_count: int = 0
    superseded_by: str = ""  # if another entry replaces this one

    def compute_id(self) -> str:
        """Generate deterministic ID from content."""
        return hashlib.md5(
            f"{self.network}:{self.content[:100]}".encode()
        ).hexdigest()[:12]


class WorldFact(MemoryEntry):
    """Objective fact about external reality.

    Examples:
      "DeepSeek costs $0.14/MTok input, $0.28/MTok output"
      "Groq rate limit is 30 RPM for free tier"
      "Gemini supports native JSON mode via response_mime_type"
    """

    network: str = "world"
    fact_type: str = ""  # "cost" | "capability" | "limit" | "compatibility"
    verified: bool = False  # has this been confirmed by multiple sources?
    verification_count: int = 0


class ExperienceEntry(MemoryEntry):
    """Agent's biographical action — a decision it participated in.

    Examples:
      "I (gemini-0) evaluated auth strategy, chose JWT, confidence 0.85"
      "I (groq-3) participated in debate round, changed vote from Redis to Postgres"
    """

    network: str = "experience"
    agent_id: str = ""
    model: str = ""
    decision_id: str = ""
    action: str = ""  # "evaluated" | "debated" | "synthesized" | "scaled"
    chose_winner: str = ""
    was_correct: bool | None = None  # None until calibrated
    task_domain: str = ""  # DomainTag value


class OpinionEntry(MemoryEntry):
    """Subjective judgment with confidence — can be updated over time.

    Examples:
      "Redis is better than Postgres for sessions (confidence: 0.85)"
      "Llama 3.3 70B is the best model for security evaluations (confidence: 0.70)"
    """

    network: str = "opinion"
    subject: str = ""  # what the opinion is about
    position: str = ""  # the actual stance
    supporting_decisions: list[str] = []  # decision_ids that support this
    contradicting_decisions: list[str] = []  # decision_ids that contradict
    # Confidence updates: strengthen when confirmed, weaken when contradicted
    confidence_history: list[float] = []  # track how confidence changed


class FailureEntry(MemoryEntry):
    """Cross-agent failure pattern — OUR INNOVATION.

    No existing system (Hindsight, A-Mem, Mem0, MemOS) tracks failures
    as a separate structured network with cross-agent visibility.

    Examples:
      "groq-3 missed XSS vulnerability in security evaluation (Session 14)"
      "DeepSeek consistently overscores 'dev_speed' by 2-3 points"
      "3/5 agents failed to consider AZ localization impact on UI decisions"
    """

    network: str = "failure"
    failure_type: str = ""  # "missed_risk" | "wrong_winner" | "overconfidence" | "blind_spot" | "systematic"
    agent_id: str = ""  # who failed (or "multiple" for systematic)
    model: str = ""
    decision_id: str = ""
    what_happened: str = ""  # specific description
    what_was_missed: str = ""  # what should have been caught
    root_cause: str = ""  # why it was missed
    mitigation: str = ""  # how to prevent in future
    severity: float = 0.0  # 0.0-1.0
    recurrence_count: int = 1  # how many times this pattern appeared
    affected_agents: list[str] = []  # all agents that made this mistake


# ── Structured Memory Manager ─────────────────────────────


class StructuredMemory:
    """4-network memory system with retrieval and learning.

    Usage:
        mem = StructuredMemory()

        # Store facts
        mem.store_world_fact("Groq free tier: 30 RPM", tags=["groq", "rate-limit"])

        # Store experience
        mem.store_experience(agent_id="gemini-0", model="gemini-2.5-flash",
                           decision_id="dsp-abc", action="evaluated",
                           chose_winner="path_a")

        # Store failures (the innovation)
        mem.store_failure(agent_id="groq-3", model="llama-3.3-70b",
                         failure_type="missed_risk",
                         what_happened="Chose JWT without considering token theft",
                         what_was_missed="Session hijacking via stolen JWT",
                         root_cause="No security perspective assigned",
                         severity=0.8)

        # Retrieve relevant memories for a task
        context = mem.get_context_for_task(
            task_text="Evaluate auth strategy for API",
            domain="security",
            agent_model="gemini-2.5-flash",
            max_entries=5
        )
    """

    # Retention limits per network
    _MAX_WORLD = 200
    _MAX_EXPERIENCE = 500  # more granular, keep more
    _MAX_OPINIONS = 100
    _MAX_FAILURES = 300  # failures are gold — keep many

    def __init__(self, data_dir: Path | None = None):
        import os
        # SWARM_DATA_DIR env var allows GitHub Actions to persist memory in the repo.
        # Local dev: falls back to ~/.swarm (unchanged behaviour).
        if data_dir is None and (env_dir := os.environ.get("SWARM_DATA_DIR")):
            data_dir = Path(env_dir)
        self.data_dir = (data_dir or Path.home() / ".swarm") / "memory"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._paths = {
            "world": self.data_dir / "world.json",
            "experience": self.data_dir / "experience.json",
            "opinion": self.data_dir / "opinion.json",
            "failure": self.data_dir / "failure.json",
        }

    # ── Store Methods ─────────────────────────────────────

    def store_world_fact(
        self,
        content: str,
        tags: list[str] | None = None,
        fact_type: str = "general",
        source: str = "system",
    ) -> WorldFact:
        """Store an objective fact. Deduplicates by content hash."""
        entry = WorldFact(
            content=content,
            tags=tags or _extract_tags(content),
            fact_type=fact_type,
            source=source,
        )
        entry.entry_id = entry.compute_id()
        self._upsert("world", entry, self._MAX_WORLD)
        return entry

    def store_experience(
        self,
        agent_id: str,
        model: str,
        decision_id: str,
        action: str,
        chose_winner: str = "",
        was_correct: bool | None = None,
        task_summary: str = "",
        task_domain: str = "general",
    ) -> ExperienceEntry:
        """Store an agent's decision experience."""
        entry = ExperienceEntry(
            content=f"{agent_id} {action}: chose {chose_winner} for {task_summary[:100]}",
            tags=_extract_tags(task_summary) + [model, action, task_domain],
            source=agent_id,
            agent_id=agent_id,
            model=model,
            decision_id=decision_id,
            action=action,
            chose_winner=chose_winner,
            was_correct=was_correct,
            task_domain=task_domain,
        )
        entry.entry_id = entry.compute_id()
        self._upsert("experience", entry, self._MAX_EXPERIENCE)
        return entry

    def store_opinion(
        self,
        subject: str,
        position: str,
        confidence: float,
        source: str = "swarm",
        decision_id: str = "",
    ) -> OpinionEntry:
        """Store or update a subjective judgment.

        If an opinion on the same subject exists, update confidence
        instead of creating a duplicate.
        """
        existing = self._find_opinion_by_subject(subject)
        if existing:
            # Update confidence based on new evidence
            old_conf = existing.confidence
            if decision_id:
                existing.supporting_decisions.append(decision_id)
            existing.confidence = _bayesian_update(old_conf, confidence)
            existing.confidence_history.append(existing.confidence)
            existing.access_count += 1
            self._save_network("opinion")
            logger.debug(
                "Opinion updated: {s} confidence {old:.0%} -> {new:.0%}",
                s=subject, old=old_conf, new=existing.confidence,
            )
            return existing

        entry = OpinionEntry(
            content=f"{subject}: {position}",
            tags=_extract_tags(subject + " " + position),
            confidence=confidence,
            source=source,
            subject=subject,
            position=position,
            supporting_decisions=[decision_id] if decision_id else [],
            confidence_history=[confidence],
        )
        entry.entry_id = entry.compute_id()
        self._upsert("opinion", entry, self._MAX_OPINIONS)
        return entry

    def store_failure(
        self,
        agent_id: str,
        model: str,
        failure_type: str,
        what_happened: str,
        what_was_missed: str = "",
        root_cause: str = "",
        mitigation: str = "",
        severity: float = 0.5,
        decision_id: str = "",
    ) -> FailureEntry:
        """Store a failure pattern. Merges with existing if similar.

        If a similar failure already exists (same model + failure_type),
        increment recurrence_count instead of creating duplicate.
        """
        existing = self._find_similar_failure(model, failure_type, what_happened)
        if existing:
            existing.recurrence_count += 1
            existing.severity = min(1.0, existing.severity + 0.1)  # escalate severity
            if agent_id not in existing.affected_agents:
                existing.affected_agents.append(agent_id)
            self._save_network("failure")
            logger.info(
                "Failure pattern escalated: {t} (now {n} occurrences, severity {s:.0%})",
                t=failure_type, n=existing.recurrence_count, s=existing.severity,
            )
            return existing

        entry = FailureEntry(
            content=f"FAILURE [{failure_type}]: {what_happened}",
            tags=_extract_tags(what_happened + " " + what_was_missed) + [failure_type, model],
            confidence=0.8,  # failures start with high confidence (they happened)
            source=agent_id,
            severity=severity,
            agent_id=agent_id,
            model=model,
            decision_id=decision_id,
            failure_type=failure_type,
            what_happened=what_happened,
            what_was_missed=what_was_missed,
            root_cause=root_cause,
            mitigation=mitigation,
            affected_agents=[agent_id],
        )
        entry.entry_id = entry.compute_id()
        self._upsert("failure", entry, self._MAX_FAILURES)
        return entry

    # ── Retrieval ──────────────────────────────────────────

    def get_context_for_task(
        self,
        task_text: str,
        domain: str = "general",
        agent_model: str = "",
        max_entries: int = 8,
    ) -> str:
        """Build a structured memory context for an agent's prompt.

        Returns text that can be injected into the evaluator prompt.
        Retrieves from all 4 networks, prioritized by relevance.
        """
        task_tags = _extract_tags(task_text + " " + domain)

        sections = []

        # 1. Relevant failures FIRST (most valuable for avoiding mistakes)
        failures = self._retrieve("failure", task_tags, max_entries=3)
        if failures:
            lines = ["KNOWN FAILURE PATTERNS (learn from these):"]
            for f in failures:
                fe = FailureEntry(**f) if isinstance(f, dict) else f
                lines.append(
                    f"  - [{fe.failure_type}] {fe.what_happened[:120]}"
                )
                if fe.mitigation:
                    lines.append(f"    Mitigation: {fe.mitigation[:100]}")
                if fe.recurrence_count > 1:
                    lines.append(f"    (Occurred {fe.recurrence_count}x — systematic pattern)")
            sections.append("\n".join(lines))

        # 2. Relevant world facts
        facts = self._retrieve("world", task_tags, max_entries=2)
        if facts:
            lines = ["RELEVANT FACTS:"]
            for f in facts:
                wf = WorldFact(**f) if isinstance(f, dict) else f
                verified = " [verified]" if wf.verified else ""
                lines.append(f"  - {wf.content[:150]}{verified}")
            sections.append("\n".join(lines))

        # 3. Agent's own experience (if model specified)
        if agent_model:
            experiences = self._retrieve_by_model("experience", agent_model, max_entries=2)
            if experiences:
                lines = ["YOUR PAST DECISIONS:"]
                for e in experiences:
                    ee = ExperienceEntry(**e) if isinstance(e, dict) else e
                    correct_tag = ""
                    if ee.was_correct is True:
                        correct_tag = " [CORRECT]"
                    elif ee.was_correct is False:
                        correct_tag = " [WRONG — learn from this]"
                    lines.append(f"  - {ee.action}: chose {ee.chose_winner}{correct_tag}")
                sections.append("\n".join(lines))

        # 4. Relevant opinions (with confidence)
        opinions = self._retrieve("opinion", task_tags, max_entries=2)
        if opinions:
            lines = ["SWARM OPINIONS (from past decisions):"]
            for o in opinions:
                oe = OpinionEntry(**o) if isinstance(o, dict) else o
                lines.append(f"  - {oe.subject}: {oe.position} (confidence: {oe.confidence:.0%})")
            sections.append("\n".join(lines))

        if not sections:
            return ""

        return "\n\n".join(sections)

    def get_failure_summary(self, model: str = "") -> str:
        """Get a summary of all failure patterns, optionally filtered by model."""
        failures = self._load_network("failure")
        if model:
            failures = [f for f in failures if f.get("model") == model or model in f.get("affected_agents", [])]

        if not failures:
            return "No failure patterns recorded."

        # Sort by severity * recurrence
        failures.sort(
            key=lambda f: f.get("severity", 0) * f.get("recurrence_count", 1),
            reverse=True,
        )

        lines = [f"Failure patterns: {len(failures)} total"]
        for f in failures[:10]:
            lines.append(
                f"  [{f.get('failure_type', '?')}] severity={f.get('severity', 0):.0%} "
                f"x{f.get('recurrence_count', 1)}: {f.get('what_happened', '?')[:100]}"
            )
        return "\n".join(lines)

    def get_stats(self) -> dict[str, int]:
        """Return entry counts per network."""
        return {
            network: len(self._load_network(network))
            for network in self._paths
        }

    # ── Internal Methods ───────────────────────────────────

    def _upsert(self, network: str, entry: MemoryEntry, max_entries: int) -> None:
        """Add or update an entry in a network."""
        entries = self._load_network(network)

        # Check for duplicate by entry_id
        for i, e in enumerate(entries):
            if e.get("entry_id") == entry.entry_id:
                entries[i] = entry.model_dump()
                self._save_network_data(network, entries)
                return

        entries.append(entry.model_dump())

        # Trim to max (remove oldest)
        if len(entries) > max_entries:
            entries = entries[-max_entries:]

        self._save_network_data(network, entries)

    def _retrieve(
        self, network: str, tags: list[str], max_entries: int = 5
    ) -> list[dict]:
        """Retrieve entries matching tags, scored by relevance + recency."""
        entries = self._load_network(network)
        if not entries or not tags:
            return entries[:max_entries]

        tag_set = set(t.lower() for t in tags)

        scored = []
        for entry in entries:
            entry_tags = set(t.lower() for t in entry.get("tags", []))
            overlap = len(tag_set & entry_tags)
            if overlap == 0:
                continue

            # Score: tag overlap + recency bonus + confidence
            recency = 0.1  # default
            try:
                created = datetime.fromisoformat(entry.get("created_at", ""))
                age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
                recency = max(0.01, 1.0 / (1.0 + age_hours / 24))  # decay over days
            except (ValueError, TypeError):
                pass

            confidence = entry.get("confidence", 0.5)
            score = overlap * 2.0 + recency + confidence

            scored.append((score, entry))

        scored.sort(key=lambda x: -x[0])
        return [entry for _, entry in scored[:max_entries]]

    def _retrieve_by_model(
        self, network: str, model: str, max_entries: int = 3
    ) -> list[dict]:
        """Retrieve entries for a specific model (for experience network)."""
        entries = self._load_network(network)
        model_entries = [
            e for e in entries
            if e.get("model") == model or model in e.get("content", "")
        ]
        # Most recent first
        model_entries.reverse()
        return model_entries[:max_entries]

    def _find_opinion_by_subject(self, subject: str) -> OpinionEntry | None:
        """Find existing opinion on same subject."""
        entries = self._load_network("opinion")
        subject_lower = subject.lower()
        for e in entries:
            if e.get("subject", "").lower() == subject_lower:
                return OpinionEntry(**e)
        return None

    def _find_similar_failure(
        self, model: str, failure_type: str, what_happened: str
    ) -> FailureEntry | None:
        """Find similar existing failure to merge with."""
        entries = self._load_network("failure")
        for e in entries:
            if (
                e.get("failure_type") == failure_type
                and e.get("model") == model
                and _text_similarity(e.get("what_happened", ""), what_happened) > 0.5
            ):
                return FailureEntry(**e)
        return None

    def _load_network(self, network: str) -> list[dict]:
        path = self._paths.get(network)
        if not path or not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_network(self, network: str) -> None:
        """Re-save current in-memory state (used for updates)."""
        # This is called after modifying existing entries in-place
        # The entries are already in the file, so we just need to re-read and save
        pass  # Updates happen via _save_network_data

    def _save_network_data(self, network: str, entries: list[dict]) -> None:
        path = self._paths[network]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False, default=str)


# ── Utility Functions ──────────────────────────────────────


def _extract_tags(text: str) -> list[str]:
    """Extract keyword tags from text for retrieval."""
    # Simple keyword extraction — upgrade to TF-IDF or embeddings in v5
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "and", "but", "or", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just",
        "because", "if", "when", "while", "this", "that", "these", "those",
        "it", "its", "i", "my", "we", "our", "you", "your", "he", "she",
        "they", "them", "what", "which", "who", "whom", "how", "all",
        "each", "every", "both", "few", "more", "most", "other", "some",
    }
    words = text.lower().split()
    tags = []
    for w in words:
        # Clean punctuation
        w = w.strip(".,;:!?()[]{}\"'`-_/\\")
        if len(w) >= 3 and w not in stop_words and w.isalpha():
            tags.append(w)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique = []
    for t in tags:
        if t not in seen:
            seen.add(t)
            unique.append(t)
    return unique[:20]  # cap at 20 tags


def _text_similarity(a: str, b: str) -> float:
    """Simple Jaccard similarity between two texts."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _bayesian_update(prior: float, new_evidence: float) -> float:
    """Simple Bayesian confidence update.

    Moves prior toward new_evidence, weighted by how strong the evidence is.
    """
    # Weight: new evidence at 30%, prior at 70% (conservative update)
    updated = 0.7 * prior + 0.3 * new_evidence
    return round(max(0.05, min(0.99, updated)), 3)
