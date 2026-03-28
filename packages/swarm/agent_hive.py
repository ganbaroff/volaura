"""
AgentHive — Per-agent lifecycle management, competency examinations, and knowledge transfer.

Inspired by:
  - Volaura's AURA competency system (examination → certification → advancement)
  - Bee colony structure (new recruits trained by senior workers before field duty)
  - Military chain of command (team leads → examiner → reporting chain)

Architecture:
  AgentProfile    — full record per agent: status, accuracy history, exam results, progress
  HiveExaminer    — central coordinator: onboarding, exams, promotions, team leads, reports
  TeamLeadReport  — structured summary from best agent per group → examiner

Status ladder:
  PROBATIONARY (0.8x) → MEMBER (1.0x) → SENIOR (1.1x) → LEAD (1.2x)

System load: MINIMAL.
  - All operations are file-based JSON/JSONL + math.
  - No extra LLM calls during normal decisions.
  - Exams are retrospective analysis of calibration data — zero tokens spent.
  - Knowledge transfer injects existing structured_memory context — also zero tokens.

Usage:
    hive = HiveExaminer()
    hive.onboard("gemini-2.5-flash", "gemini", structured_memory)

    # After each decision (called by engine.py):
    hive.record_decision("gemini-2.5-flash", "gemini", domain="code", was_correct=True, ...)

    # Before scoring (called by pm.py):
    mult = hive.get_weight_multiplier("gemini-2.5-flash")  # e.g. 1.1 for SENIOR

    # After group decision:
    report = hive.generate_team_report("security_group", agent_results, domain="security")

    # Inspect:
    print(hive.get_agent_summary("gemini-2.5-flash"))
    print(hive.get_hive_status())
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Enums & Constants
# ---------------------------------------------------------------------------


class AgentStatus(str, Enum):
    PROBATIONARY = "probationary"  # New recruit — weight 0.8x, first N decisions
    MEMBER = "member"              # Competency confirmed — full 1.0x weight
    SENIOR = "senior"              # 50+ decisions, accuracy ≥ 70% — 1.1x weight
    LEAD = "lead"                  # Team lead for their group — 1.2x weight
    QUARANTINE = "quarantine"      # Chronic underperformer — weight 0.3x, proposals flagged
                                   # SentinelNet pattern (arXiv 2509.14956): credibility-based
                                   # isolation. Agent stays active (not removed) but outputs
                                   # go to quarantine-inbox for CTO review before acting.
                                   # Rehabilitation: accuracy must recover to ≥ MEMBER threshold
                                   # over next 10 calibrated decisions to auto-restore.


STATUS_WEIGHTS: dict[str, float] = {
    AgentStatus.PROBATIONARY: 0.8,
    AgentStatus.MEMBER: 1.0,
    AgentStatus.SENIOR: 1.1,
    AgentStatus.LEAD: 1.2,
    AgentStatus.QUARANTINE: 0.3,  # Still contributes but with minimal weight
}

STATUS_ORDER = [
    AgentStatus.QUARANTINE,   # lowest
    AgentStatus.PROBATIONARY,
    AgentStatus.MEMBER,
    AgentStatus.SENIOR,
    AgentStatus.LEAD,
]


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


class ExamResult(BaseModel):
    """Record of one competency examination for an agent."""

    exam_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    exam_type: str = "retrospective"  # "retrospective" | "first_probation"
    decisions_reviewed: int = 0
    decisions_correct: int = 0
    score: float = 0.0  # 0–100
    domains_tested: list[str] = []
    weak_areas: list[str] = []    # domains below threshold
    strong_areas: list[str] = []  # domains above senior threshold
    passed: bool = False
    study_material: list[str] = []    # skills/domains to study if failed
    knowledge_received: list[str] = []  # knowledge transferred on passing
    notes: str = ""


class ProgressSnapshot(BaseModel):
    """One entry in an agent's progress history (append-only JSONL)."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    decisions_made: int = 0
    accuracy_overall: float = 0.0
    accuracy_by_domain: dict[str, float] = {}
    status: str = AgentStatus.PROBATIONARY
    weight_multiplier: float = 0.8
    event: str = ""   # "joined", "exam_passed", "exam_failed", "promoted", "became_lead", etc.
    notes: str = ""


class AgentProfile(BaseModel):
    """Full per-agent record in the hive."""

    model_config = ConfigDict(use_enum_values=True)

    # Identity
    model: str
    provider: str
    status: str = AgentStatus.PROBATIONARY
    joined_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # Decision history
    decisions_made: int = 0
    decisions_correct: int = 0
    decisions_wrong: int = 0
    accuracy_overall: float = 0.0
    accuracy_by_domain: dict[str, float] = {}
    domain_decision_counts: dict[str, int] = {}

    # Performance metrics
    avg_latency_ms: float = 0.0
    avg_confidence: float = 0.0
    json_compliance_rate: float = 1.0

    # Competency examination
    exam_results: list[ExamResult] = []
    exams_passed: int = 0
    exams_failed: int = 0
    skill_mastery: dict[str, float] = {}  # skill_name → 0–1

    # Notable moments
    notable_decisions: list[str] = []  # decision_ids where agent was uniquely correct

    # SentinelNet (arXiv 2509.14956) — credibility tracking
    credibility_score: float = 1.0     # 0.0–1.0. Decays on wrong, recovers on correct.
    consecutive_failures: int = 0      # reset on any correct decision
    quarantine_reason: str = ""        # why this agent was quarantined (empty if not)
    quarantine_since: str | None = None  # timestamp when quarantine started

    # Hive position
    current_group: str | None = None
    is_team_lead: bool = False
    weight_multiplier: float = 0.8  # starts probationary

    # Knowledge received during onboarding / exams
    knowledge_received: list[str] = []

    last_updated: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def recompute_accuracy(self) -> None:
        calibrated = self.decisions_correct + self.decisions_wrong
        self.accuracy_overall = self.decisions_correct / max(calibrated, 1)
        self.last_updated = datetime.now(timezone.utc).isoformat()


class TeamLeadReport(BaseModel):
    """Structured summary sent from team lead to HiveExaminer after each group decision."""

    group_id: str
    lead_model: str
    decision_id: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    group_size: int = 0
    valid_responses: int = 0
    consensus_strength: float = 0.0
    domain: str = ""
    winner_chosen: str = ""
    notable_agents: list[str] = []     # above senior threshold
    struggling_agents: list[str] = []  # below 80% of member threshold
    concerns: list[str] = []
    recommendations: list[str] = []


class HiveStatus(BaseModel):
    """Overall hive health snapshot."""

    total_agents: int = 0
    agents_by_status: dict[str, int] = {}
    top_agents: list[str] = []        # top 3 by accuracy (≥5 decisions)
    total_decisions: int = 0
    total_knowledge_transfers: int = 0
    total_exams_run: int = 0
    team_leads: dict[str, str] = {}   # group_id → lead model
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ---------------------------------------------------------------------------
# HiveExaminer
# ---------------------------------------------------------------------------


class HiveExaminer:
    """
    Central coordinator for the agent hive.

    Manages:
    - Onboarding new agents (probationary → knowledge transfer)
    - Retrospective competency exams (math on calibration data, zero LLM calls)
    - Promotion/demotion based on exam results
    - Team lead election (best performer per group)
    - Team lead → examiner reporting chain
    - Per-agent progress history (append-only JSONL)

    Data layout (~/.swarm/hive/):
      profiles/{safe_model}.json   — AgentProfile
      progress/{safe_model}.jsonl  — ProgressSnapshot log (append-only)
      exams/{exam_id}.json         — ExamResult archive
    """

    # Exam & promotion thresholds
    PROBATIONARY_DECISIONS: int = 10       # decisions before first exam
    MEMBER_ACCURACY_THRESHOLD: float = 0.55
    SENIOR_DECISIONS: int = 50
    SENIOR_ACCURACY_THRESHOLD: float = 0.70
    EXAM_INTERVAL: int = 20                # exam every N decisions
    MIN_DOMAIN_SAMPLES: int = 3            # min decisions per domain to judge
    NOTABLE_CONFIDENCE_THRESHOLD: float = 0.85  # confidence needed to mark decision notable

    # SentinelNet quarantine thresholds (arXiv 2509.14956)
    QUARANTINE_MIN_DECISIONS: int = 15     # minimum calibrated decisions before quarantine is possible
    QUARANTINE_ACCURACY_THRESHOLD: float = 0.25  # accuracy below this → quarantine
    QUARANTINE_CONSECUTIVE_FAILURES: int = 5     # 5 wrong in a row → quarantine regardless of total

    def __init__(self, data_dir: Path | None = None):
        base = (data_dir or Path.home() / ".swarm") / "hive"
        self.profiles_dir = base / "profiles"
        self.progress_dir = base / "progress"
        self.exams_dir = base / "exams"
        for d in [self.profiles_dir, self.progress_dir, self.exams_dir]:
            d.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Public: Profile access
    # ------------------------------------------------------------------

    def get_profile(self, model: str) -> AgentProfile | None:
        path = self._profile_path(model)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return AgentProfile.model_validate(json.load(f))
        except (json.JSONDecodeError, OSError, ValueError):
            return None

    def get_or_create_profile(self, model: str, provider: str) -> AgentProfile:
        p = self.get_profile(model)
        if p is not None:
            return p
        return self._create_profile(model, provider)

    def get_weight_multiplier(self, model: str) -> float:
        """
        Return the hive weight multiplier for a model.

        Called by pm.py during score aggregation. Stacks on top of
        calibration weights so hive status further refines who is trusted.
        Returns 1.0 (neutral) if no profile exists yet.
        """
        p = self.get_profile(model)
        return p.weight_multiplier if p else 1.0

    def get_weight_map(self, models: list[str]) -> dict[str, float]:
        """Return {model: multiplier} for a list of models."""
        return {m: self.get_weight_multiplier(m) for m in models}

    def is_quarantined(self, model: str) -> bool:
        """Return True if this agent is currently in QUARANTINE status.

        Used by engine.py to flag proposals before committing to inbox.
        Quarantined agents still run and can contribute (weight 0.3x),
        but their proposals are marked for CTO review.
        """
        p = self.get_profile(model)
        return p is not None and p.status == AgentStatus.QUARANTINE

    def get_quarantine_summary(self) -> list[dict]:
        """Return all currently quarantined agents with their reason."""
        all_profiles = self._load_all_profiles()
        return [
            {
                "model": p.model,
                "reason": p.quarantine_reason,
                "since": p.quarantine_since,
                "accuracy": p.accuracy_overall,
                "decisions": p.decisions_made,
                "credibility": p.credibility_score,
            }
            for p in all_profiles
            if p.status == AgentStatus.QUARANTINE
        ]

    # ------------------------------------------------------------------
    # Public: Onboarding
    # ------------------------------------------------------------------

    def onboard(
        self,
        model: str,
        provider: str,
        structured_memory: Any | None = None,  # StructuredMemory
    ) -> dict[str, Any]:
        """
        Onboard a new agent into the hive.

        1. Create AgentProfile (probationary status, 0.8x weight)
        2. Immediately transfer relevant knowledge from structured_memory
           so the agent doesn't start blind — it receives what the hive knows
        3. Agent stays probationary until PROBATIONARY_DECISIONS decisions pass

        Returns onboarding summary dict.
        """
        profile = self.get_or_create_profile(model, provider)
        knowledge_received: list[str] = []

        if structured_memory is not None:
            # World knowledge — general facts the hive has collected
            world_ctx = structured_memory.get_context_for_task(
                task_text="general decision making knowledge",
                domain="general",
                agent_model=model,
                max_entries=5,
            )
            if world_ctx:
                knowledge_received.append("world_facts")

            # Cross-agent failure patterns — most valuable for new agents
            failures = structured_memory._retrieve("failure", [], max_entries=5)
            if failures:
                knowledge_received.append(f"failure_patterns:{len(failures)}")

            # Aggregate opinions from experienced agents
            opinions = structured_memory._retrieve("opinion", [], max_entries=3)
            if opinions:
                knowledge_received.append(f"opinions:{len(opinions)}")

        profile.knowledge_received.extend(knowledge_received)
        profile.last_updated = datetime.now(timezone.utc).isoformat()
        self._save_profile(profile)

        logger.info(
            "Hive: onboarded {m} ({p}) — transferred {n} knowledge items",
            m=model, p=provider, n=len(knowledge_received),
        )

        return {
            "model": model,
            "provider": provider,
            "status": profile.status,
            "weight_multiplier": profile.weight_multiplier,
            "knowledge_received": knowledge_received,
            "decisions_until_exam": self.PROBATIONARY_DECISIONS - profile.decisions_made,
        }

    # ------------------------------------------------------------------
    # Public: Record decisions
    # ------------------------------------------------------------------

    def record_decision(
        self,
        model: str,
        provider: str,
        domain: str,
        was_correct: bool | None,
        latency_ms: int = 0,
        confidence: float = 0.0,
        json_valid: bool = True,
        decision_id: str = "",
        was_notable: bool = False,
    ) -> None:
        """
        Record one decision outcome for an agent.

        Called by engine.py after calibration data is available.
        When was_correct=None (not yet calibrated), only counts total decisions.

        Side effects:
        - Updates running accuracy, latency, confidence averages
        - Triggers competency exam at PROBATIONARY_DECISIONS and every EXAM_INTERVAL
        - Marks notable decisions (agent was correct + high confidence + unique)
        """
        profile = self.get_or_create_profile(model, provider)
        profile.decisions_made += 1

        if was_correct is True:
            profile.decisions_correct += 1
            profile.consecutive_failures = 0  # reset streak
            # Credibility recovery: +5% per correct (capped at 1.0)
            profile.credibility_score = min(1.0, profile.credibility_score + 0.05)
            # Update domain accuracy
            n = profile.domain_decision_counts.get(domain, 0) + 1
            profile.domain_decision_counts[domain] = n
            old_acc = profile.accuracy_by_domain.get(domain, 0.0)
            # Running average for domain (counts only calibrated decisions)
            profile.accuracy_by_domain[domain] = old_acc + (1.0 - old_acc) / n
        elif was_correct is False:
            profile.decisions_wrong += 1
            profile.consecutive_failures += 1
            # Credibility decay: -10% per wrong (capped at 0.0)
            profile.credibility_score = max(0.0, profile.credibility_score - 0.10)
            n = profile.domain_decision_counts.get(domain, 0) + 1
            profile.domain_decision_counts[domain] = n
            old_acc = profile.accuracy_by_domain.get(domain, 0.0)
            profile.accuracy_by_domain[domain] = old_acc * (n - 1) / n  # decay toward 0
        else:
            # Uncalibrated — track domain count but not accuracy
            profile.domain_decision_counts[domain] = profile.domain_decision_counts.get(domain, 0) + 1

        # Running averages for performance metrics
        n = profile.decisions_made
        if latency_ms > 0:
            profile.avg_latency_ms = (profile.avg_latency_ms * (n - 1) + latency_ms) / n
        if confidence > 0:
            profile.avg_confidence = (profile.avg_confidence * (n - 1) + confidence) / n
        jv = 1.0 if json_valid else 0.0
        profile.json_compliance_rate = (profile.json_compliance_rate * (n - 1) + jv) / n

        profile.recompute_accuracy()

        # Notable decision: correct + high confidence + unique minority win
        if was_correct and confidence >= self.NOTABLE_CONFIDENCE_THRESHOLD and decision_id:
            profile.notable_decisions.append(decision_id)
            profile.notable_decisions = profile.notable_decisions[-20:]

        # Exam trigger: first exam after probationary period, then every EXAM_INTERVAL
        should_exam = (
            profile.decisions_made == self.PROBATIONARY_DECISIONS
            or (profile.decisions_made > self.PROBATIONARY_DECISIONS
                and profile.decisions_made % self.EXAM_INTERVAL == 0)
        )
        if should_exam:
            self._run_exam(profile)

        self._save_profile(profile)

    # ------------------------------------------------------------------
    # Public: Team leads
    # ------------------------------------------------------------------

    def elect_team_lead(
        self,
        group_id: str,
        agent_models: list[str],
        provider: str = "",
        domain: str = "general",
    ) -> str | None:
        """
        Elect the team lead for a group from a list of agent models.

        Election criteria (priority order):
        1. Highest domain accuracy (or overall accuracy if domain data sparse)
        2. Most calibrated decisions (experience counts)
        3. Lowest average latency (tiebreaker — speed matters)

        Returns the winning model name, or None if no profiles exist yet.
        Updates all group member profiles.
        """
        candidates: list[tuple[str, float, int, float]] = []
        for m in agent_models:
            p = self.get_profile(m)
            if p and p.decisions_made >= 3:
                d_acc = p.accuracy_by_domain.get(domain, p.accuracy_overall)
                candidates.append((m, d_acc, p.decisions_made, p.avg_latency_ms))

        if not candidates:
            return None

        # Sort: domain_accuracy DESC, decisions DESC, latency ASC
        candidates.sort(key=lambda x: (-x[1], -x[2], x[3]))
        lead_model = candidates[0][0]

        # Update all group profiles
        for m in agent_models:
            p = self.get_profile(m)
            if p is None:
                continue
            was_lead = p.is_team_lead
            p.is_team_lead = (m == lead_model)
            p.current_group = group_id

            if p.is_team_lead and not was_lead:
                p.status = AgentStatus.LEAD
                p.weight_multiplier = STATUS_WEIGHTS[AgentStatus.LEAD]
                self._record_progress(
                    m, "became_lead",
                    f"Elected team lead of group '{group_id}' (domain={domain})",
                    p,
                )
            elif was_lead and not p.is_team_lead:
                # Dethroned — revert to earned status
                self._recompute_status(p)

            self._save_profile(p)

        logger.info(
            "Hive: {m} elected as team lead for group '{g}' (domain={d})",
            m=lead_model, g=group_id, d=domain,
        )
        return lead_model

    def generate_team_report(
        self,
        group_id: str,
        agent_results: list[Any],  # list[AgentResult]
        domain: str = "general",
        decision_id: str = "",
    ) -> TeamLeadReport | None:
        """
        Generate a team lead report after a group decision.

        Summarizes group performance, flags struggling agents, makes
        recommendations to the HiveExaminer (e.g. "trigger exam for X").
        Returns None if no results.
        """
        if not agent_results:
            return None

        group_models = [r.model for r in agent_results]
        lead_model = self.elect_team_lead(group_id, group_models, domain=domain)
        if not lead_model:
            lead_model = group_models[0] if group_models else "unknown"

        valid = [r for r in agent_results if r.json_valid and not r.error]
        votes = Counter(r.winner for r in valid if r.winner)
        top_winner = votes.most_common(1)[0][0] if votes else ""
        consensus = votes[top_winner] / max(len(valid), 1) if top_winner else 0.0

        notable: list[str] = []
        struggling: list[str] = []
        for r in valid:
            p = self.get_profile(r.model)
            if p:
                if p.accuracy_overall >= self.SENIOR_ACCURACY_THRESHOLD:
                    notable.append(r.model)
                elif p.accuracy_overall < self.MEMBER_ACCURACY_THRESHOLD * 0.8 and p.decisions_made >= 5:
                    struggling.append(r.model)

        concerns: list[str] = []
        if consensus < 0.5:
            concerns.append(f"Low group consensus ({consensus:.0%}) — divergent signals")
        if len(valid) < len(agent_results) * 0.7:
            concerns.append(
                f"Response quality issue: only {len(valid)}/{len(agent_results)} valid"
            )
        if struggling:
            concerns.append(f"Under-performing agents: {', '.join(struggling[:3])}")

        recommendations: list[str] = []
        if struggling:
            recommendations.append(f"Schedule exam for: {', '.join(struggling[:2])}")
        if consensus < 0.4:
            recommendations.append(
                f"High divergence in '{domain}' — consider adding domain specialists"
            )

        return TeamLeadReport(
            group_id=group_id,
            lead_model=lead_model,
            decision_id=decision_id,
            group_size=len(agent_results),
            valid_responses=len(valid),
            consensus_strength=consensus,
            domain=domain,
            winner_chosen=top_winner,
            notable_agents=notable[:3],
            struggling_agents=struggling[:3],
            concerns=concerns,
            recommendations=recommendations,
        )

    # ------------------------------------------------------------------
    # Public: Knowledge transfer
    # ------------------------------------------------------------------

    def transfer_knowledge(
        self,
        model: str,
        structured_memory: Any,
        domain_focus: str = "general",
    ) -> list[str]:
        """
        Transfer hive knowledge to an agent (typically after a failed exam).

        Targets:
        - Failures in agent's weak domains
        - World facts relevant to domain_focus
        - Cross-agent failure patterns (the Failure Network)

        Returns list of knowledge item descriptors transferred.
        """
        profile = self.get_profile(model)
        if not profile:
            return []

        transferred: list[str] = []

        # World knowledge for this domain
        ctx = structured_memory.get_context_for_task(
            task_text=f"competency in {domain_focus}",
            domain=domain_focus,
            agent_model=model,
            max_entries=6,
        )
        if ctx:
            transferred.append(f"world_context:{domain_focus}")

        # Remedial injection for weak areas
        weak = profile.exam_results[-1].weak_areas if profile.exam_results else []
        for area in weak[:3]:
            ctx = structured_memory.get_context_for_task(
                task_text=f"failures and lessons in {area}",
                domain=area,
                agent_model=model,
                max_entries=3,
            )
            if ctx:
                transferred.append(f"remedial:{area}")

        profile.knowledge_received.extend(transferred)
        profile.knowledge_received = profile.knowledge_received[-50:]
        self._save_profile(profile)

        logger.info(
            "Hive: transferred {n} knowledge items to {m}",
            n=len(transferred), m=model,
        )
        return transferred

    # ------------------------------------------------------------------
    # Public: Reporting
    # ------------------------------------------------------------------

    def get_hive_status(self) -> HiveStatus:
        """Build an overall hive health snapshot from all agent profiles."""
        all_profiles = self._load_all_profiles()

        by_status: dict[str, int] = {}
        total_decisions = 0
        total_kt = 0
        total_exams = 0

        for p in all_profiles:
            s = str(p.status)
            by_status[s] = by_status.get(s, 0) + 1
            total_decisions += p.decisions_made
            total_kt += len(p.knowledge_received)
            total_exams += p.exams_passed + p.exams_failed

        # Top 3 by accuracy (need at least 5 decisions to qualify)
        qualified = sorted(
            [p for p in all_profiles if p.decisions_made >= 5],
            key=lambda p: p.accuracy_overall,
            reverse=True,
        )
        top_agents = [p.model for p in qualified[:3]]

        # Team leads per group
        leads = {
            p.current_group: p.model
            for p in all_profiles
            if p.is_team_lead and p.current_group
        }

        return HiveStatus(
            total_agents=len(all_profiles),
            agents_by_status=by_status,
            top_agents=top_agents,
            total_decisions=total_decisions,
            total_knowledge_transfers=total_kt,
            total_exams_run=total_exams,
            team_leads=leads,
        )

    def get_agent_summary(self, model: str) -> str:
        """Human-readable one-page profile for an agent."""
        p = self.get_profile(model)
        if not p:
            return f"No hive profile for '{model}' — agent not yet registered."

        lines = [
            f"+-- Agent: {p.model}",
            f"|  Provider : {p.provider}",
            f"|  Status   : {p.status}  (weight {p.weight_multiplier:.1f}x)",
            f"|  Joined   : {p.joined_at[:10]}",
            f"|  Decisions: {p.decisions_made}  "
            f"(correct={p.decisions_correct}  wrong={p.decisions_wrong}  "
            f"accuracy={p.accuracy_overall:.1%})",
        ]

        if p.accuracy_by_domain:
            dom = "  ".join(
                f"{d}:{a:.0%}"
                for d, a in sorted(p.accuracy_by_domain.items())
            )
            lines.append(f"|  By domain: {dom}")

        if p.exam_results:
            last = p.exam_results[-1]
            tag = "PASS" if last.passed else "FAIL"
            lines.append(
                f"|  Last exam : {last.score:.0f}%  [{tag}]  "
                f"({p.exams_passed} passed / {p.exams_failed} failed total)"
            )
            if last.weak_areas:
                lines.append(f"|  Weak areas: {', '.join(last.weak_areas)}")
            if last.strong_areas:
                lines.append(f"|  Strong    : {', '.join(last.strong_areas)}")

        if p.is_team_lead:
            lines.append(f"|  Role      : Team Lead  (group: {p.current_group})")

        if p.notable_decisions:
            lines.append(f"|  Notable decisions: {len(p.notable_decisions)}")

        if p.knowledge_received:
            lines.append(f"|  Knowledge items received: {len(p.knowledge_received)}")

        lines.append("+" + "-" * 50)
        return "\n".join(lines)

    def get_progress_history(self, model: str) -> list[dict]:
        """Full progress history for an agent (append-only JSONL)."""
        path = self._progress_path(model)
        if not path.exists():
            return []
        records: list[dict] = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        except (OSError, json.JSONDecodeError):
            pass
        return records

    def print_hive_report(self) -> None:
        """Print formatted hive status to console."""
        status = self.get_hive_status()
        print(f"\n{'='*55}")
        print(f" HIVE STATUS REPORT  |  {status.generated_at[:19]}")
        print(f"{'='*55}")
        print(f" Total agents  : {status.total_agents}")
        for s, n in sorted(status.agents_by_status.items()):
            print(f"   {s:<16}: {n}")
        print(f" Total decisions recorded : {status.total_decisions}")
        print(f" Total exams run          : {status.total_exams_run}")
        print(f" Knowledge transfers      : {status.total_knowledge_transfers}")
        if status.top_agents:
            print(f" Top performers           : {', '.join(status.top_agents)}")
        if status.team_leads:
            for group, lead in status.team_leads.items():
                print(f" Lead ({group}): {lead}")
        print(f"{'='*55}\n")

    # ------------------------------------------------------------------
    # Internal: Exam
    # ------------------------------------------------------------------

    def _run_exam(self, profile: AgentProfile) -> ExamResult:
        """
        Retrospective competency exam — pure math, zero LLM calls.

        Scoring = % of calibrated decisions correct.
        Domain analysis = accuracy per domain (with enough samples).
        Pass = score >= MEMBER_ACCURACY_THRESHOLD * 100.
        """
        exam_id = (
            f"exam_{self._safe(profile.model)}_{profile.decisions_made:04d}"
        )
        calibrated = profile.decisions_correct + profile.decisions_wrong
        score = (profile.decisions_correct / max(calibrated, 1)) * 100.0

        passed = score >= (self.MEMBER_ACCURACY_THRESHOLD * 100)

        weak: list[str] = []
        strong: list[str] = []
        for domain, count in profile.domain_decision_counts.items():
            if count < self.MIN_DOMAIN_SAMPLES:
                continue
            acc = profile.accuracy_by_domain.get(domain, profile.accuracy_overall)
            if acc < self.MEMBER_ACCURACY_THRESHOLD:
                weak.append(domain)
            elif acc >= self.SENIOR_ACCURACY_THRESHOLD:
                strong.append(domain)

        study = [f"skill:{area}" for area in weak]

        exam = ExamResult(
            exam_id=exam_id,
            exam_type="first_probation" if profile.decisions_made == self.PROBATIONARY_DECISIONS
            else "retrospective",
            decisions_reviewed=calibrated,
            decisions_correct=profile.decisions_correct,
            score=round(score, 1),
            domains_tested=list(profile.domain_decision_counts.keys()),
            weak_areas=weak,
            strong_areas=strong,
            passed=passed,
            study_material=study,
            notes=(
                f"After {profile.decisions_made} decisions. "
                f"Calibrated: {calibrated}. Accuracy: {score:.1f}%."
            ),
        )

        profile.exam_results.append(exam)
        if passed:
            profile.exams_passed += 1
        else:
            profile.exams_failed += 1
        # Trim to last 20 exams
        profile.exam_results = profile.exam_results[-20:]

        # Persist exam record
        exam_path = self.exams_dir / f"{exam_id}.json"
        try:
            with open(exam_path, "w", encoding="utf-8") as f:
                json.dump(exam.model_dump(), f, indent=2, ensure_ascii=False, default=str)
        except OSError:
            pass

        # Promotion/demotion based on new data
        old_status = profile.status
        self._recompute_status(profile)

        if profile.status != old_status:
            direction = "promoted" if self._is_higher(profile.status, old_status) else "demoted"
            event = f"{direction}_to_{profile.status}"
            notes = f"Exam score: {score:.1f}%  ({'PASS' if passed else 'FAIL'})"
        else:
            event = "exam_passed" if passed else "exam_failed"
            notes = f"Score: {score:.1f}%. Weak: {weak}"

        self._record_progress(profile.model, event, notes, profile)

        logger.info(
            "Hive exam [{m}]: {s:.1f}%  {r}  status={st}  weak={w}",
            m=profile.model, s=score, r="PASS" if passed else "FAIL",
            st=profile.status, w=weak,
        )

        return exam

    # ------------------------------------------------------------------
    # Internal: Status management
    # ------------------------------------------------------------------

    def _recompute_status(self, profile: AgentProfile) -> None:
        """Recompute status and weight based on performance data.

        SentinelNet (B6): agents can now enter QUARANTINE (downward path).
        Two conditions trigger quarantine:
        1. Chronic underperformer: 15+ calibrated decisions AND accuracy < 25%
        2. Streak: 5 consecutive wrong answers regardless of total count

        Rehabilitation: quarantined agents auto-restore when accuracy recovers
        to ≥ MEMBER threshold over their recent decisions.
        """
        if profile.is_team_lead:
            return  # leads keep their status until dethroned

        d = profile.decisions_made
        calibrated = profile.decisions_correct + profile.decisions_wrong
        a = profile.accuracy_overall

        # --- QUARANTINE check (takes priority over promotion) ---
        chronic = (
            calibrated >= self.QUARANTINE_MIN_DECISIONS
            and a < self.QUARANTINE_ACCURACY_THRESHOLD
        )
        streak = profile.consecutive_failures >= self.QUARANTINE_CONSECUTIVE_FAILURES

        if chronic or streak:
            if profile.status != AgentStatus.QUARANTINE:
                # New quarantine event — log the reason
                if chronic:
                    profile.quarantine_reason = (
                        f"Chronic underperformer: {calibrated} decisions, "
                        f"accuracy {a:.0%} < {self.QUARANTINE_ACCURACY_THRESHOLD:.0%} threshold"
                    )
                else:
                    profile.quarantine_reason = (
                        f"Streak: {profile.consecutive_failures} consecutive wrong answers"
                    )
                profile.quarantine_since = datetime.now(timezone.utc).isoformat()
                logger.warning(
                    "Hive: {m} QUARANTINED — {r}",
                    m=profile.model, r=profile.quarantine_reason,
                )
            profile.status = AgentStatus.QUARANTINE
            profile.weight_multiplier = STATUS_WEIGHTS[AgentStatus.QUARANTINE]
            return

        # --- REHABILITATION: was quarantined, now recovering ---
        if profile.status == AgentStatus.QUARANTINE and a >= self.MEMBER_ACCURACY_THRESHOLD:
            logger.info(
                "Hive: {m} rehabilitated — accuracy {a:.0%} restored to member threshold",
                m=profile.model, a=a,
            )
            profile.quarantine_reason = ""
            profile.quarantine_since = None

        # --- Normal promotion logic ---
        if d >= self.SENIOR_DECISIONS and a >= self.SENIOR_ACCURACY_THRESHOLD:
            new = AgentStatus.SENIOR
        elif d >= self.PROBATIONARY_DECISIONS and a >= self.MEMBER_ACCURACY_THRESHOLD:
            new = AgentStatus.MEMBER
        else:
            new = AgentStatus.PROBATIONARY

        profile.status = new
        profile.weight_multiplier = STATUS_WEIGHTS[new]

    @staticmethod
    def _is_higher(new: str, old: str) -> bool:
        try:
            return STATUS_ORDER.index(new) > STATUS_ORDER.index(old)
        except ValueError:
            return False

    # ------------------------------------------------------------------
    # Internal: Persistence
    # ------------------------------------------------------------------

    def _create_profile(self, model: str, provider: str) -> AgentProfile:
        profile = AgentProfile(model=model, provider=provider)
        self._save_profile(profile)
        self._record_progress(model, "joined", "New agent joined the hive", profile)
        logger.info("Hive: new agent registered — {m} ({p})", m=model, p=provider)
        return profile

    def _save_profile(self, profile: AgentProfile) -> None:
        path = self._profile_path(profile.model)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(
                    profile.model_dump(), f,
                    indent=2, ensure_ascii=False, default=str,
                )
        except OSError as e:
            logger.warning("Hive: cannot save profile for {m}: {e}", m=profile.model, e=e)

    def _record_progress(
        self,
        model: str,
        event: str,
        notes: str,
        profile: AgentProfile,
    ) -> None:
        snapshot = ProgressSnapshot(
            decisions_made=profile.decisions_made,
            accuracy_overall=profile.accuracy_overall,
            accuracy_by_domain=dict(profile.accuracy_by_domain),
            status=str(profile.status),
            weight_multiplier=profile.weight_multiplier,
            event=event,
            notes=notes,
        )
        path = self._progress_path(model)
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(
                    json.dumps(snapshot.model_dump(), ensure_ascii=False, default=str)
                    + "\n"
                )
        except OSError as e:
            logger.warning("Hive: cannot write progress for {m}: {e}", m=model, e=e)

    def _load_all_profiles(self) -> list[AgentProfile]:
        profiles: list[AgentProfile] = []
        for path in self.profiles_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    profiles.append(AgentProfile.model_validate(json.load(f)))
            except (json.JSONDecodeError, OSError, ValueError):
                continue
        return profiles

    def _profile_path(self, model: str) -> Path:
        return self.profiles_dir / f"{self._safe(model)}.json"

    def _progress_path(self, model: str) -> Path:
        return self.progress_dir / f"{self._safe(model)}.jsonl"

    @staticmethod
    def _safe(model: str) -> str:
        return model.replace("/", "_").replace(":", "_").replace(" ", "_")
