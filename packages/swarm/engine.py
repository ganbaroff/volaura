"""
SwarmEngine v2 — full architecture:
  - Auto-discovery of all available models (14+ from discovered_models.json)
  - Tournament mode: 4 groups x 4 models for HIGH+ stakes
  - Skill augmentation: agents borrow skills from library
  - Agent memory: models learn from past experiences
  - Innovation field: every agent proposes 1 creative idea
  - Debate: triggered within groups on divergence > 50%
  - LLM synthesis: MoA-style cross-group aggregation

v4 "Eureka" additions:
  - ReasoningGraph: agents see each other's structured reasoning in Round 2
  - StructuredMemory: 4-network system (World/Experience/Opinion/Failure)
  - TokenCountingMiddleware: real cost tracking per provider

v5 "Hive" additions:
  - AgentHive: per-agent lifecycle, competency exams, knowledge transfer
  - Status ladder: PROBATIONARY → MEMBER → SENIOR → LEAD
  - Team leads elected per group, report to HiveExaminer
  - Progress history per agent (append-only JSONL)

v7 "Research Autonomy" additions:
  - ResearchLoop: agents propose specific web research topics in every response
  - WebResearcher: Gemini Pro + google_search executes top-voted topics
  - Findings injected into StructuredMemory World Network
  - All future agents benefit from grounded, current facts
  - Auto-research: set auto_research=True on SwarmConfig to trigger after each decision
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from .agent_hive import AgentStatus, HiveExaminer
try:
    from .agent_memory import AgentMemory
except ImportError:
    AgentMemory = None
from .memory import DecisionMemory
from .memory_logger import inject_global_memory, log_episodic_run
from .middleware import MiddlewareChain
from .pm import PMAgent
from .providers import ProviderRegistry
from .providers.base import LLMProvider
from .providers.dynamic import load_discovered_providers
from .research import WebResearcher, inject_findings_into_memory
from .skills import SkillLibrary
from .structured_memory import StructuredMemory
from .swarm_types import (
    CalibrationEntry,
    DomainTag,
    StakesLevel,
    SwarmConfig,
    SwarmReport,
)


class SwarmEngine:
    """Universal multi-model decision engine.

    Usage:
        engine = SwarmEngine()
        report = await engine.quick_decide("Redis vs Postgres?")
        print(report.winner, report.winner_score)
    """

    def __init__(
        self,
        env: dict[str, str] | None = None,
        data_dir: Path | None = None,
        project_root: Path | None = None,
    ):
        env = env or dict(os.environ)
        self.memory = DecisionMemory(data_dir)
        self.agent_memory = AgentMemory(data_dir)
        self.structured_memory = StructuredMemory(data_dir)
        self.hive = HiveExaminer(data_dir)
        self.skills = SkillLibrary(project_root)

        # Auto-discover: try discovered_models.json first, fallback to static providers
        self.providers = load_discovered_providers(env)
        if not self.providers:
            self.registry = ProviderRegistry()
            self.providers = self.registry.discover(env)
        else:
            self.registry = ProviderRegistry()
            logger.info(
                "Loaded {n} providers from discovered_models.json",
                n=len(self.providers),
            )

        # Onboard any providers not yet in the hive
        for prov in self.providers:
            model = prov.get_model_name()
            if self.hive.get_profile(model) is None:
                self.hive.onboard(model, prov.get_provider_name(), self.structured_memory)

        # v7: Auto-remove dead weight agents from the provider pool
        # Agents that consistently fail JSON or exams get excluded from dispatch.
        # This was requested by kimi-k2, deepseek, and gpt-oss-120b in v7 team feedback.
        before_count = len(self.providers)
        self.providers = self._filter_dead_weight(self.providers)
        removed = before_count - len(self.providers)
        if removed:
            logger.info(
                "Dead weight filter: removed {n} unreliable providers",
                n=removed,
            )

        self.middleware = MiddlewareChain()
        self.pm = PMAgent(
            self.registry, self.memory, self.skills, self.agent_memory,
            middleware=self.middleware,
            structured_memory=self.structured_memory,
            hive=self.hive,
        )

        # v7: WebResearcher — Gemini Pro primary, DeepSeek fallback
        gemini_key = env.get("GEMINI_API_KEY", "")
        deepseek_key = env.get("DEEPSEEK_API_KEY", "")
        self.researcher = WebResearcher(api_key=gemini_key, deepseek_key=deepseek_key)

        # Log summary
        free = [p for p in self.providers if p.is_free()]
        paid = [p for p in self.providers if not p.is_free()]
        logger.info(
            "SwarmEngine v2: {n} providers ({f} free, {p} paid)",
            n=len(self.providers), f=len(free), p=len(paid),
        )

    def _filter_dead_weight(self, providers: list[LLMProvider]) -> list[LLMProvider]:
        """Remove providers that consistently fail from the active pool.

        Criteria for removal:
        1. JSON compliance < 20% over 5+ evaluations (allam-2-7b pattern)
        2. 3+ consecutive exam failures in hive (chronic underperformer)

        Removed models stay in hive history but don't get dispatched.
        """
        # Hard blacklist: models known to fail reliably
        # allam-2-7b: never produces valid JSON
        # kimi-k2-*: chronically 503 over-capacity on Groq (discovered 2026-03-24)
        BLACKLIST = {
            "allam-2-7b",
            "moonshotai/kimi-k2-instruct",
            "moonshotai/kimi-k2-instruct-0905",
        }

        kept: list[LLMProvider] = []
        for prov in providers:
            model = prov.get_model_name()

            # Hard blacklist check
            if model in BLACKLIST:
                logger.info("Dead weight: {m} blacklisted (never produces valid JSON)", m=model)
                continue

            # Check hive profile for chronic failure or quarantine
            profile = self.hive.get_profile(model)
            if profile:
                # Remove if SentinelNet QUARANTINE — credibility too low to dispatch
                if profile.status == AgentStatus.QUARANTINE:
                    logger.info(
                        "Dead weight: {m} quarantined ({r})",
                        m=model, r=profile.quarantine_reason[:60] if profile.quarantine_reason else "?",
                    )
                    continue

                # Remove if 3+ consecutive exam failures
                if profile.exams_failed >= 3 and profile.exams_passed == 0:
                    logger.info(
                        "Dead weight: {m} removed (0/{n} exams passed)",
                        m=model, n=profile.exams_failed,
                    )
                    continue

                # Remove if JSON compliance is terrible (< 20% over 5+ evaluations)
                if profile.decisions_made >= 5 and profile.json_compliance_rate < 0.20:
                    logger.info(
                        "Dead weight: {m} removed (JSON compliance {c:.0%})",
                        m=model, c=profile.json_compliance_rate,
                    )
                    continue

            kept.append(prov)
        return kept

    def _maybe_consolidate_memory(self) -> None:
        """Auto-trigger sleep_cycle_consolidation when inbox is full enough.

        Checks episodic inbox — if 10+ entries, runs consolidation with Gemini.
        This is the "sleep daemon" that turns raw agent logs into Global_Context.md.
        Without this, agents never learn from past runs.
        """
        from .memory_logger import _INBOX_DIR

        try:
            inbox_files = list(_INBOX_DIR.glob("*.json"))
        except Exception:
            return

        if len(inbox_files) < 10:
            return

        logger.info(
            "Auto-consolidation: {n} inbox entries — running sleep cycle",
            n=len(inbox_files),
        )

        # Use Gemini client for consolidation if available
        gemini_key = os.environ.get("GEMINI_API_KEY", "")
        if not gemini_key:
            logger.warning("Auto-consolidation skipped: GEMINI_API_KEY not set")
            return

        try:
            from google import genai
            from .memory_logger import sleep_cycle_consolidation

            client = genai.Client(api_key=gemini_key)
            insights = sleep_cycle_consolidation(client)
            if insights:
                logger.info("Auto-consolidation: {n} insight blocks written to Global_Context.md", n=insights)
        except Exception as e:
            logger.warning("Auto-consolidation failed: {e}", e=str(e)[:200])

    def _load_ecosystem_context(self) -> str:
        """Load ecosystem map + accumulated global memory for agent prompt injection.

        This closes the broken chain: agents now read accumulated knowledge from
        Global_Context.md (consolidated from episodic runs) and ECOSYSTEM-MAP.md
        (the living map of all 5 products). Without this, agents work blind.

        Fixed 2026-04-06: CEO caught that inject_global_memory() existed but was
        never called. This method is now wired into decide() before every run.
        """
        context_parts: list[str] = []

        # 1. Ecosystem map — what agents MUST know about all 5 products
        ecosystem_map = Path(__file__).parent / "memory" / "ECOSYSTEM-MAP.md"
        if ecosystem_map.exists():
            try:
                text = ecosystem_map.read_text(encoding="utf-8").strip()
                # Truncate to ~3000 chars to not blow up prompt budget
                if len(text) > 3000:
                    text = text[:3000] + "\n[... truncated — read full ECOSYSTEM-MAP.md for details]"
                context_parts.append(f"--- ECOSYSTEM MAP ---\n{text}")
            except Exception:
                pass

        # 2. Global Context — consolidated knowledge from past swarm runs
        global_ctx = inject_global_memory("")
        if global_ctx.strip():
            context_parts.append(global_ctx)

        return "\n\n".join(context_parts) if context_parts else ""

    async def decide(self, config: SwarmConfig) -> SwarmReport:
        """Make a decision. Returns the full SwarmReport."""
        if not self.providers:
            logger.error("No providers available.")
            return SwarmReport(config=config)

        # v9: Inject ecosystem context + accumulated memory into agent prompts.
        # This ensures every agent sees: ECOSYSTEM-MAP (5 products, Constitution laws),
        # Global_Context (consolidated findings from past runs).
        eco_context = self._load_ecosystem_context()
        if eco_context:
            existing = config.context or ""
            config = SwarmConfig(
                question=config.question,
                context=f"{existing}\n\n{eco_context}" if existing else eco_context,
                constraints=config.constraints,
                domain=config.domain,
                stakes=config.stakes,
                paths=config.paths,
            )
            logger.info("Ecosystem context injected ({n} chars)", n=len(eco_context))

        # v8: Domain-aware provider selection via TeamLead.
        # GENERAL → full pool (round-robin, no domain bias).
        # Specific domain → filter through TeamLead preferred pool with fallback.
        # Fallback: if filtering would empty the pool, use full pool minus avoided models.
        active_providers = self.providers
        if config.domain != DomainTag.GENERAL:
            try:
                from .team_leads import get_tilead_for_domain
                tilead = get_tilead_for_domain(config.domain)
                filtered = tilead.filter_providers(self.providers)
                if filtered:
                    active_providers = filtered
            except ImportError:
                pass  # team_leads archived — use full pool
                logger.info(
                    "TeamLead({domain}): {n}/{total} providers active",
                    domain=config.domain.value,
                    n=len(filtered),
                    total=len(self.providers),
                )
            else:
                logger.warning(
                    "TeamLead({domain}): filtered pool empty — using full pool",
                    domain=config.domain.value,
                )

        report = await self.pm.run(config, active_providers)

        # Store in memory
        decision_id = self.memory.store_decision(report)
        report.decision_id = decision_id

        # Log agent experiences (flat memory — legacy)
        for r in report.agent_results:
            if r.json_valid and not r.error:
                self.agent_memory.log_experience(
                    model=r.model,
                    task_summary=config.question[:200],
                    skill_used=r.raw_response[:50] if "skill_used" in r.raw_response else None,
                    skill_helpful=None,
                    chose_winner=r.winner,
                    was_correct=None,  # calibrate later
                    self_note=r.reason[:200],
                    full_prompt=config.question,
                    full_response=r.reason,
                )

                # Structured memory — experience network (v4)
                self.structured_memory.store_experience(
                    agent_id=r.agent_id,
                    model=r.model,
                    decision_id=decision_id,
                    action="evaluated",
                    chose_winner=r.winner,
                    task_summary=config.question[:200],
                    task_domain=config.domain.value,
                )

            # Hive lifecycle — record every agent (v5), was_correct=None until calibration
            self.hive.record_decision(
                model=r.model,
                provider=r.provider.split(":")[0],
                domain=config.domain.value,
                was_correct=None,  # updated in calibrate()
                latency_ms=r.latency_ms,
                confidence=r.confidence,
                json_valid=r.json_valid,
                decision_id=decision_id,
                was_notable=r.confidence >= 0.85 and r.winner == report.winner,
            )

            # Episodic memory logger (v8) — EDM-filtered: keeps ≥0.8 (success) and ≤0.2 (failure)
            if r.error or not r.json_valid:
                episodic_score = 0.1  # failure → hindsight/ECHO processing
            elif r.winner and r.winner == report.winner:
                episodic_score = 0.9  # winning agent → consolidate success pattern
            else:
                episodic_score = r.confidence  # noise zone (0.2–0.8) → discarded by sleep daemon
            log_episodic_run(
                agent_id=f"{r.provider}:{r.model}",
                prompt=config.question[:300],
                response=r.reason[:500] if r.reason else "",
                score=episodic_score,
            )

            # EvoSkill trajectory logging (B3) — raw failed trajectories into agent-trajectories.jsonl.
            # skill_evolution.py reads this alongside summaries to close the gap with EvoSkill/VOYAGER.
            # Log failures always; log successes only when agent was the winner (high-signal).
            if r.error or not r.json_valid:
                self.agent_memory.log_trajectory(
                    model=r.model,
                    task=config.question,
                    full_prompt=config.question,
                    full_response=r.raw_response or r.error or "",
                    outcome="wrong",
                )
            elif r.winner and r.winner == report.winner:
                self.agent_memory.log_trajectory(
                    model=r.model,
                    task=config.question,
                    full_prompt=config.question,
                    full_response=r.reason or "",
                    outcome="correct",
                )

        logger.info(
            "Decision: winner={w} score={s}/50 agents={a}/{t} latency={ms}ms id={id}",
            w=report.winner, s=report.winner_score,
            a=report.agents_succeeded, t=report.agents_used,
            ms=report.total_latency_ms, id=decision_id,
        )

        # v7: ResearchLoop — execute top research requests autonomously
        # Agents proposed research topics → PM collected + deduped → we execute here
        # Findings go into World Network → available to all future agents
        if report.research_requests and getattr(config, "auto_research", False):
            top_requests = report.research_requests[:3]  # max 3 parallel topics
            logger.info(
                "ResearchLoop: executing {n} research topics (auto_research=True)",
                n=len(top_requests),
            )
            findings = await self.researcher.conduct_parallel(top_requests)
            if findings:
                stored = await inject_findings_into_memory(
                    findings, self.structured_memory, decision_id
                )
                report.research_conducted = [f.to_dict() for f in findings]
                logger.info(
                    "ResearchLoop: {n} findings stored in World Network",
                    n=stored,
                )
        elif report.research_requests:
            logger.info(
                "ResearchLoop: {n} topics proposed (call engine.research(report) to execute)",
                n=len(report.research_requests),
            )

        # v9: Auto-consolidate episodic memory after significant runs.
        # If inbox has 10+ entries, run sleep_cycle_consolidation to update Global_Context.md.
        # This keeps the knowledge loop alive: agents write → consolidate → inject into next run.
        self._maybe_consolidate_memory()

        return report

    async def research(self, report: SwarmReport, max_topics: int = 3) -> SwarmReport:
        """Manually trigger research on topics proposed in a previous decision.

        Use this when you want to control WHEN research happens:
            report = await engine.decide(config)          # fast decision
            report = await engine.research(report)         # research in background
            # next decide() call benefits from findings
        """
        if not report.research_requests:
            logger.info("No research requests in this report.")
            return report

        top_requests = report.research_requests[:max_topics]
        logger.info(
            "Executing {n} research topics manually: {topics}",
            n=len(top_requests),
            topics=[r.topic[:50] for r in top_requests],
        )
        findings = await self.researcher.conduct_parallel(top_requests)
        if findings:
            stored = await inject_findings_into_memory(
                findings, self.structured_memory, report.decision_id
            )
            report.research_conducted = [f.to_dict() for f in findings]
            logger.info("Research complete: {n} facts added to World Network", n=stored)
        return report

    async def quick_decide(
        self,
        question: str,
        stakes: str = "medium",
        context: str = "",
        domain: str = "general",
    ) -> SwarmReport:
        """Convenience: just a question, minimal config."""
        config = SwarmConfig(
            question=question,
            stakes=StakesLevel(stakes),
            context=context,
            domain=DomainTag(domain),
        )
        return await self.decide(config)

    def calibrate(
        self, decision_id: str, actual_outcome: str
    ) -> CalibrationEntry | None:
        """After observing outcome, calibrate model weights + update hive accuracy."""
        entry = self.memory.calibrate(decision_id, actual_outcome)
        if entry:
            # Backfill hive accuracy for agents who participated in this decision
            domain = entry.domain.value if hasattr(entry.domain, "value") else str(entry.domain)
            for model in entry.models_correct:
                p = self.hive.get_profile(model)
                if p:
                    prov = p.provider
                    self.hive.record_decision(
                        model=model, provider=prov, domain=domain,
                        was_correct=True, decision_id=decision_id,
                    )
            for model in entry.models_wrong:
                p = self.hive.get_profile(model)
                if p:
                    prov = p.provider
                    self.hive.record_decision(
                        model=model, provider=prov, domain=domain,
                        was_correct=False, decision_id=decision_id,
                    )
        return entry

    def get_competency_matrix(self) -> dict[str, dict[str, float]]:
        return self.memory.get_competency_matrix()

    def get_available_providers(self) -> list[str]:
        return [p.get_provider_name() for p in self.providers]

    def get_provider_stats(self) -> list[dict[str, Any]]:
        return [
            {
                "name": p.get_provider_name(),
                "model": p.get_model_name(),
                "cost_per_mtok": p.get_cost_per_mtok(),
                "rate_limit_rpm": p.get_rate_limit_rpm(),
                "is_free": p.is_free(),
            }
            for p in self.providers
        ]

    def get_skill_improvements(self) -> list[dict]:
        """Get pending skill improvements suggested by agents."""
        return self.skills.get_pending_improvements()

    def get_agent_stats(self) -> dict[str, dict]:
        """Get experience stats for all models."""
        stats = {}
        for p in self.providers:
            model = p.get_model_name()
            stats[model] = self.agent_memory.get_model_stats(model)
        return stats

    def get_hive_status(self) -> dict:
        """Get hive health: agent statuses, top performers, team leads."""
        status = self.hive.get_hive_status()
        return status.model_dump()

    def get_agent_profile(self, model: str) -> str:
        """Human-readable profile for a specific agent."""
        return self.hive.get_agent_summary(model)

    def get_agent_history(self, model: str) -> list[dict]:
        """Full progress history for an agent (chronological)."""
        return self.hive.get_progress_history(model)

    def print_hive_report(self) -> None:
        """Print formatted hive status to console."""
        self.hive.print_hive_report()
