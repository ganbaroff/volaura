"""
PM Agent - deterministic synthesis layer + LLM synthesis for final aggregation.

Research-backed design:
- ACL 2025: weighted majority for inner-group voting
- MoA: LLM synthesis for cross-group aggregation (synthesis > selection)
- ICML 2024: conditional debate only when divergence > 50%
- NeurIPS 2025: debate alone is martingale, but targeted correction works
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from loguru import logger

from .agent_hive import HiveExaminer
try:
    from .agent_memory import AgentMemory
except ImportError:
    AgentMemory = None
from .memory import DecisionMemory
from .middleware import MiddlewareChain, MiddlewareContext
try:
    from .reasoning_graph import ReasoningGraph
except ImportError:
    ReasoningGraph = None
from .structured_memory import StructuredMemory
from .prompts import (
    build_debate_prompt,
    build_evaluator_prompt,
    build_synthesis_prompt,
    get_group_perspectives,
    get_random_perspectives,
)
from .providers import ProviderRegistry
from .providers.base import LLMProvider
from .skills import SkillLibrary
from .swarm_types import (
    AgentResult,
    DimensionScores,
    DivergenceReport,
    DomainTag,
    PathDefinition,
    PathProposal,
    ScalingEvent,
    StakesLevel,
    SwarmConfig,
    SwarmReport,
)

# Divergence threshold for triggering debate round
DEBATE_THRESHOLD = 0.50


def _word_overlap(a: str, b: str) -> float:
    """Jaccard word overlap between two strings. Used for dedup in PathProposal + ResearchRequest."""
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa | wb), 1)


class PMAgent:
    """Manages the swarm: dispatch, aggregate, debate, synthesize, report."""

    # Tournament group definitions: 4 groups x 4 models
    TOURNAMENT_GROUPS = ["security", "cost", "ux", "quality"]

    def __init__(
        self,
        registry: ProviderRegistry,
        memory: DecisionMemory,
        skills: SkillLibrary | None = None,
        agent_memory: AgentMemory | None = None,
        middleware: MiddlewareChain | None = None,
        structured_memory: StructuredMemory | None = None,
        hive: HiveExaminer | None = None,
    ):
        self.registry = registry
        self.memory = memory
        self.skills = skills
        self.agent_memory = agent_memory
        self.middleware = middleware or MiddlewareChain()
        self.structured_memory = structured_memory
        self.hive = hive

    async def run(
        self,
        config: SwarmConfig,
        available: list[LLMProvider],
    ) -> SwarmReport:
        """Full decision run: select -> dispatch -> aggregate -> debate? -> synthesize -> report."""
        ctx = MiddlewareContext(config=config)
        profiles = self.memory.get_model_profiles() if config.use_calibration else None

        # 1. Allocate initial agents
        agent_pool = self.registry.allocate_agents(
            stakes=config.stakes,
            available=available,
            profiles=profiles,
            domain=config.domain,
            max_agents=config.max_agents,
        )

        if not agent_pool:
            return SwarmReport(config=config, agents_used=0)

        # MW: before_dispatch — budget trimming, timeout guard
        agent_pool = self.middleware.run_before_dispatch(ctx, agent_pool)

        # 2. Assign perspectives
        perspectives = get_random_perspectives(len(agent_pool))

        # 3. Round 1: Independent evaluation (all agents blind)
        results = await self._dispatch(config, agent_pool, perspectives, ctx=ctx)

        # MW: after_dispatch — post-processing
        results = self.middleware.run_after_dispatch(ctx, results)

        # MW: before_aggregation — dedup, filtering
        results = self.middleware.run_before_aggregation(ctx, results)

        # 4. Aggregate Round 1
        report = self._aggregate(config, results)
        scaling_events: list[ScalingEvent] = []

        # 4.3 Path Proposal Collection (v5)
        # Agents propose novel paths → PM deduplicates → adds to scoring
        accepted_proposals = self._collect_proposals(results, config.paths)
        if accepted_proposals:
            # Extend config.paths with proposed paths for re-aggregation
            extended_paths = dict(config.paths or {})
            for prop in accepted_proposals:
                extended_paths[prop.path_id] = PathDefinition(
                    name=prop.name,
                    description=prop.description,
                    best_case="As proposed by agent(s)",
                    worst_case="Untested — agent-proposed path",
                )
            # Rebuild config with extended paths (shallow copy)
            config = config.model_copy(update={"paths": extended_paths})
            report = self._aggregate(config, results)
            report.accepted_proposals = accepted_proposals
            scaling_events.append(ScalingEvent(
                round=0,
                reason=f"PathProposal: {len(accepted_proposals)} novel paths added by agents",
                agents_added=0,
                provider_used="path_proposal",
            ))
        else:
            report.accepted_proposals = []

        # 4.5 Reasoning Graph Round 2 (v4 — agents see each other's reasoning)
        # Only for MEDIUM+ stakes with enough valid results
        valid_r1 = [r for r in results if r.json_valid and not r.error]
        if (
            config.stakes != StakesLevel.LOW
            and len(valid_r1) >= 3
            and not ctx.scaling_blocked
        ):
            graph = ReasoningGraph.build(valid_r1)
            if graph.nodes and graph.consensus_strength < 0.90:
                # Don't run Round 2 if already near-unanimous — waste of tokens
                logger.info(
                    "Reasoning Graph: {n} nodes, consensus {c:.0%}. Launching Round 2.",
                    n=len(graph.nodes), c=graph.consensus_strength,
                )
                r2_results = await self._dispatch(
                    config, agent_pool, perspectives,
                    agent_id_offset=len(results),
                    ctx=ctx,
                    reasoning_graph=graph,
                )
                if r2_results:
                    r2_valid = [r for r in r2_results if r.json_valid and not r.error]
                    # v6: Track conviction — agents who held firm after seeing the graph
                    r1_votes = {r.model: r.winner for r in valid_r1 if r.winner}
                    for r in r2_valid:
                        if r.model in r1_votes and r.winner == r1_votes[r.model]:
                            r.held_firm = True
                    results.extend(r2_results)
                    # Re-aggregate with both rounds
                    results = self.middleware.run_before_aggregation(ctx, results)
                    report = self._aggregate(config, results)
                    scaling_events.append(ScalingEvent(
                        round=1,
                        reason=f"Reasoning Graph Round 2: {len(r2_valid)} agents revised",
                        agents_added=len(r2_valid),
                        provider_used="round2",
                    ))

        # 5. Conditional debate (only if divergence > 50%)
        if report.divergence.consensus_strength < DEBATE_THRESHOLD and len(
            [r for r in results if r.json_valid]
        ) >= 3:
            logger.info(
                "Divergence {d:.0%} > threshold {t:.0%} - launching debate round",
                d=1 - report.divergence.consensus_strength,
                t=1 - DEBATE_THRESHOLD,
            )

            debate_results = await self._debate_round(config, results, agent_pool)
            if debate_results:
                # Merge debate corrections into results
                results = self._apply_debate_corrections(results, debate_results)
                report = self._aggregate(config, results)

                scaling_events.append(ScalingEvent(
                    round=1,
                    reason=f"Debate triggered: consensus was {report.divergence.consensus_strength:.0%}",
                    agents_added=0,
                    provider_used="debate",
                ))

        # 6. Self-scaling (max 2 rounds) - add more agents if still divergent
        for scale_round in range(2):
            # MW: timeout guard can block scaling
            if ctx.scaling_blocked:
                logger.info("Scaling blocked by middleware (timeout guard)")
                break

            should_scale, reason = self._should_scale(report.divergence, config)
            if not should_scale:
                break

            fast_provider = self._pick_fastest(available)
            if not fast_provider:
                break

            extra_count = 3 if report.divergence.high_divergence else 1
            extra_pool = [
                (fast_provider, 1.0, 0.5 + i * 0.2)
                for i in range(extra_count)
            ]

            extra_perspectives = get_random_perspectives(extra_count)
            if not report.divergence.high_divergence:
                extra_perspectives = [("contrarian", "Argue AGAINST the obvious winner.")]

            # MW: budget check on scaling pool
            extra_pool = self.middleware.run_before_dispatch(ctx, extra_pool)

            extra_results = await self._dispatch(
                config, extra_pool, extra_perspectives,
                agent_id_offset=len(results),
                ctx=ctx,
            )

            results.extend(extra_results)

            # MW: dedup before re-aggregation
            results = self.middleware.run_before_aggregation(ctx, results)
            report = self._aggregate(config, results)

            scaling_events.append(ScalingEvent(
                round=scale_round + 2,
                reason=reason,
                agents_added=extra_count,
                provider_used=fast_provider.get_provider_name(),
            ))

            logger.info(
                "Scaling round {r}: +{n} agents ({p}). Reason: {reason}",
                r=scale_round + 1,
                n=extra_count,
                p=fast_provider.get_provider_name(),
                reason=reason,
            )

        report.scaling_events = scaling_events

        # 7. LLM Synthesis for final answer (MoA-style, synthesis > selection)
        # Only for MEDIUM+ stakes - LOW uses math aggregation only
        if config.stakes != StakesLevel.LOW:
            synthesis_result = await self._synthesize(config, report, available)
            if synthesis_result:
                report.synthesis = synthesis_result

        # MW: after_report — annotate with budget/dedup stats
        report = self.middleware.run_after_report(ctx, report)

        # 8. Update memory with run stats + skill feedback
        for r in results:
            if not r.error:
                self.memory.update_after_run(
                    model_name=r.model,
                    provider=r.provider,
                    latency_ms=r.latency_ms,
                    json_valid=r.json_valid,
                )

                # Record skill feedback from agent response
                if self.skills and r.raw_response:
                    try:
                        raw = json.loads(r.raw_response) if isinstance(r.raw_response, str) else {}
                        skill_name = raw.get("skill_used")
                        if skill_name:
                            self.skills.record_feedback(
                                skill_name=skill_name,
                                agent_model=r.model,
                                helpful=raw.get("skill_helpful", True),
                                gap=raw.get("skill_gap", ""),
                                suggestion="",
                            )
                    except (json.JSONDecodeError, TypeError):
                        pass

        # 9. Collect research requests from all agents (v7)
        # Agents propose specific topics they want investigated via web search.
        # PM deduplicates and stores on report. Engine executes top requests post-decision.
        from .research import collect_and_prioritize_research
        all_valid = [r for r in results if r.json_valid and not r.error]
        research_requests = collect_and_prioritize_research(all_valid)
        if research_requests:
            report.research_requests = research_requests
            logger.info(
                "Research requests collected: {n} unique topics from {a} agents",
                n=len(research_requests),
                a=sum(1 for r in all_valid if r.research_request),
            )

        return report

    # Per-provider timeout (seconds) — fast providers don't wait for slow ones
    _PROVIDER_TIMEOUTS: dict[str, float] = {
        "groq": 12.0,
        "openrouter": 20.0,
        "openai": 20.0,
        "gemini": 30.0,
        "deepseek": 35.0,
    }
    _DEFAULT_PROVIDER_TIMEOUT = 30.0

    # Minimum valid results before early exit can trigger, by stakes level
    _MIN_AGENTS_FOR_EXIT: dict[StakesLevel, int] = {
        StakesLevel.LOW: 3,
        StakesLevel.MEDIUM: 4,
        StakesLevel.HIGH: 5,
        StakesLevel.CRITICAL: 7,
    }
    _EARLY_EXIT_THRESHOLD = 0.75  # consensus fraction to exit early

    async def _dispatch(
        self,
        config: SwarmConfig,
        agent_pool: list[tuple[LLMProvider, float, float]],
        perspectives: list[tuple[str, str]],
        agent_id_offset: int = 0,
        group_name: str = "",
        ctx: MiddlewareContext | None = None,
        reasoning_graph: ReasoningGraph | None = None,
    ) -> list[AgentResult]:
        """Send prompts to all agents in parallel.

        Uses asyncio.wait() so fast providers (Groq ~1s) return immediately
        without waiting for slow ones (DeepSeek ~18s). Applies smart early
        exit when 75%+ consensus is reached to cancel remaining slow tasks.

        If reasoning_graph is provided (Round 2), injects the graph into prompts
        so agents can see each other's structured reasoning.
        """
        matched_skills = []
        if self.skills:
            matched_skills = self.skills.match_skills(
                config.question + " " + config.context, max_skills=2
            )
            if matched_skills:
                logger.info("Skills matched: {s}", s=", ".join(matched_skills))

        # Pre-compute structured memory context (shared across agents)
        structured_ctx = ""
        if self.structured_memory:
            structured_ctx = self.structured_memory.get_context_for_task(
                task_text=config.question,
                domain=config.domain.value,
                max_entries=5,
            )

        # Pre-compute reasoning graph prompt (for Round 2)
        graph_prompt = reasoning_graph.to_agent_prompt() if reasoning_graph else ""

        # Build tasks with per-provider timeouts
        task_to_agent: dict[asyncio.Task, str] = {}

        for i, ((provider, weight, temp), (persp_name, persp_desc)) in enumerate(
            zip(agent_pool, perspectives)
        ):
            agent_id = f"{provider.get_provider_name()}-{agent_id_offset + i}"

            # Agent-specific memory (from old flat system)
            memory_ctx = ""
            if self.agent_memory:
                memory_ctx = self.agent_memory.get_context_for_agent(
                    provider.get_model_name(), max_entries=3
                )

            # Model-specific structured memory (failures + facts)
            model_memory = ""
            if self.structured_memory:
                model_memory = self.structured_memory.get_context_for_task(
                    task_text=config.question,
                    domain=config.domain.value,
                    agent_model=provider.get_model_name(),
                    max_entries=5,
                )

            # Combine memory sources: structured > flat
            combined_memory = ""
            if model_memory:
                combined_memory = model_memory
            elif structured_ctx:
                combined_memory = structured_ctx
            if memory_ctx:
                combined_memory = f"{combined_memory}\n\n{memory_ctx}" if combined_memory else memory_ctx

            prompt = build_evaluator_prompt(
                config, agent_id, persp_name, persp_desc,
                agent_memory_context=combined_memory,
                group_name=group_name,
                model_name=provider.get_model_name(),
            )

            # Inject reasoning graph for Round 2
            if graph_prompt:
                prompt = f"{prompt}\n\n{graph_prompt}"

            if self.skills and matched_skills:
                prompt = self.skills.inject_into_prompt(prompt, matched_skills)

            timeout = self._PROVIDER_TIMEOUTS.get(
                provider.get_provider_name(), self._DEFAULT_PROVIDER_TIMEOUT
            )
            task = asyncio.create_task(
                self._call_agent_timed(provider, prompt, temp, agent_id, weight, timeout)
            )
            task_to_agent[task] = agent_id

        results: list[AgentResult] = []
        winner_votes: dict[str, int] = {}
        min_agents = self._MIN_AGENTS_FOR_EXIT.get(config.stakes, 4)
        pending = set(task_to_agent.keys())
        early_exit = False

        while pending and not early_exit:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                try:
                    result = task.result()
                except Exception as exc:
                    result = AgentResult(
                        agent_id=task_to_agent.get(task, "error"),
                        provider="unknown",
                        model="unknown",
                        error=str(exc)[:500],
                    )

                if ctx:
                    result = self.middleware.run_after_agent_call(ctx, result)
                results.append(result)

                # Track winner votes for early exit
                if result.json_valid and not result.error and result.winner:
                    winner_votes[result.winner] = winner_votes.get(result.winner, 0) + 1

                # Smart early exit: cancel slow agents if consensus already reached
                total_valid = sum(winner_votes.values())
                if total_valid >= min_agents and winner_votes and pending:
                    top_votes = max(winner_votes.values())
                    consensus = top_votes / total_valid
                    if consensus >= self._EARLY_EXIT_THRESHOLD:
                        top_winner = max(winner_votes, key=lambda k: winner_votes[k])
                        logger.info(
                            "Early exit: {n}/{t} agents agree on '{w}' "
                            "({c:.0%} consensus). Cancelling {p} slow task(s).",
                            n=top_votes, t=total_valid, w=top_winner,
                            c=consensus, p=len(pending),
                        )
                        for slow_task in pending:
                            slow_task.cancel()
                        await asyncio.gather(*pending, return_exceptions=True)
                        pending = set()
                        early_exit = True
                        break

        return results

    async def _call_agent_timed(
        self,
        provider: LLMProvider,
        prompt: str,
        temperature: float,
        agent_id: str,
        weight: float,
        timeout: float,
    ) -> AgentResult:
        """Call a single agent with a per-provider timeout."""
        try:
            return await asyncio.wait_for(
                self._call_agent(provider, prompt, temperature, agent_id, weight),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            logger.warning(
                "Provider {p} timed out after {t}s (agent {a})",
                p=provider.get_provider_name(), t=timeout, a=agent_id,
            )
            return AgentResult(
                agent_id=agent_id,
                provider=provider.get_provider_name(),
                model=provider.get_model_name(),
                error=f"Timeout after {timeout:.0f}s",
                latency_ms=int(timeout * 1000),
            )

    async def _call_agent(
        self,
        provider: LLMProvider,
        prompt: str,
        temperature: float,
        agent_id: str,
        weight: float,
    ) -> AgentResult:
        """Call a single agent and parse the response into AgentResult."""
        raw = await provider.safe_evaluate(prompt, temperature)

        if raw.get("error"):
            return AgentResult(
                agent_id=agent_id,
                provider=raw.get("provider", provider.get_provider_name()),
                model=raw.get("model", provider.get_model_name()),
                latency_ms=raw.get("latency_ms", 0),
                json_valid=False,
                error=raw["error"],
            )

        # Parse scores
        scores: dict[str, DimensionScores] = {}
        raw_scores = raw.get("scores", {})
        for path_id, dims in raw_scores.items():
            if isinstance(dims, dict):
                scores[path_id] = DimensionScores(**{
                    k: float(v) for k, v in dims.items()
                    if k in DimensionScores.model_fields
                })

        # Parse optional path proposal (v5)
        proposed_path: PathProposal | None = None
        raw_proposal = raw.get("proposed_path")
        if isinstance(raw_proposal, dict):
            name = str(raw_proposal.get("name", "")).strip()
            desc = str(raw_proposal.get("description", "")).strip()
            if name and desc and name.lower() not in ("null", "none", ""):
                proposed_path = PathProposal(
                    name=name,
                    description=desc,
                    rationale=str(raw_proposal.get("rationale", "")),
                    proposed_by=agent_id,
                    confidence=float(raw.get("confidence", 0.0)),
                )

        # Parse optional research request (v7)
        from .swarm_types import ResearchRequest
        research_request: ResearchRequest | None = None
        raw_research = raw.get("research_request")
        if isinstance(raw_research, dict):
            topic = str(raw_research.get("topic", "")).strip()
            if topic and topic.lower() not in ("null", "none", ""):
                research_request = ResearchRequest(
                    topic=topic,
                    rationale=str(raw_research.get("rationale", "")),
                    domain=str(raw_research.get("domain", "general")),
                    priority=str(raw_research.get("priority", "medium")),
                    proposed_by=agent_id,
                )

        return AgentResult(
            agent_id=agent_id,
            provider=raw.get("provider", provider.get_provider_name()),
            model=raw.get("model", provider.get_model_name()),
            perspective=raw.get("perspective", ""),
            scores=scores,
            concerns=raw.get("concerns", {}),
            winner=str(raw.get("winner", "")),
            reason=str(raw.get("reason", "")),
            confidence=float(raw.get("confidence", 0.0)),
            latency_ms=raw.get("latency_ms", 0),
            cost_estimate=0.0,
            json_valid=True,
            proposed_path=proposed_path,
            research_request=research_request,
            # v8: fields present in prompts since v2, now properly stored
            innovation=str(raw.get("innovation", "") or ""),
            skill_used=raw.get("skill_used"),
            skill_helpful=raw.get("skill_helpful"),
            skill_gap=raw.get("skill_gap"),
            self_note=str(raw.get("self_note", "") or ""),
        )

    async def _debate_round(
        self,
        config: SwarmConfig,
        results: list[AgentResult],
        agent_pool: list[tuple[LLMProvider, float, float]],
    ) -> list[dict]:
        """Launch targeted correction debate for agents that disagree.

        Only agents who chose a DIFFERENT winner than the majority see
        the majority's arguments and must respond with specific corrections.
        Research: ICML 2024 - targeted correction, not free-form debate.
        """
        valid = [r for r in results if r.json_valid and not r.error]
        if len(valid) < 3:
            return []

        # Find majority winner
        votes: dict[str, list[AgentResult]] = {}
        for r in valid:
            votes.setdefault(r.winner, []).append(r)

        if not votes:
            return []

        majority_winner = max(votes, key=lambda k: len(votes[k]))
        minority = [r for r in valid if r.winner != majority_winner]

        if not minority:
            return []  # No disagreement to debate

        # Build debate prompts for minority agents only (save tokens)
        majority_args = [
            {
                "perspective": r.perspective,
                "winner": r.winner,
                "reason": r.reason,
                "concerns": r.concerns,
            }
            for r in votes[majority_winner][:3]  # Max 3 opponent arguments
        ]

        tasks = []
        for r in minority:
            # Find the provider for this agent
            provider = None
            for p, _, _ in agent_pool:
                if p.get_provider_name() in r.agent_id:
                    provider = p
                    break

            if not provider:
                provider = agent_pool[0][0] if agent_pool else None

            if provider:
                own = {
                    "winner": r.winner,
                    "reason": r.reason,
                    "concerns": r.concerns,
                    "perspective": r.perspective,
                }
                prompt = build_debate_prompt(config, r.agent_id, own, majority_args)
                tasks.append(provider.safe_evaluate(prompt, temperature=0.5))

        if not tasks:
            return []

        debate_raw = await asyncio.gather(*tasks, return_exceptions=True)

        debate_results = []
        for raw in debate_raw:
            if isinstance(raw, dict) and not raw.get("error"):
                debate_results.append(raw)

        logger.info(
            "Debate round: {n} minority agents challenged, {s} responded",
            n=len(minority),
            s=len(debate_results),
        )

        return debate_results

    def _apply_debate_corrections(
        self,
        results: list[AgentResult],
        debate_results: list[dict],
    ) -> list[AgentResult]:
        """Apply debate corrections: if an agent changed their vote, update it."""
        corrections = {
            d.get("evaluator", ""): d
            for d in debate_results
            if d.get("changed_vote")
        }

        if not corrections:
            return results

        updated = []
        for r in results:
            if r.agent_id in corrections:
                correction = corrections[r.agent_id]
                new_winner = correction.get("new_winner", r.winner)
                logger.info(
                    "Agent {a} changed vote: {old} -> {new} (reason: {r})",
                    a=r.agent_id,
                    old=r.winner,
                    new=new_winner,
                    r=correction.get("correction", "?")[:100],
                )
                updated.append(AgentResult(
                    **{**r.model_dump(), "winner": new_winner,
                       "reason": correction.get("correction", r.reason)}
                ))
            else:
                updated.append(r)

        return updated

    async def _synthesize(
        self,
        config: SwarmConfig,
        report: SwarmReport,
        available: list[LLMProvider],
    ) -> dict | None:
        """LLM synthesis for final answer (MoA-style).

        Uses the best available provider to synthesize group results
        into a final recommendation. Research: MoA synthesis > selection by ~12%.
        """
        if not report.agent_results:
            return None

        # Build group summaries from agent results
        valid = [r for r in report.agent_results if r.json_valid and not r.error]
        if not valid:
            return None

        # Group by perspective for synthesis input
        perspective_groups: dict[str, list[AgentResult]] = {}
        for r in valid:
            key = r.perspective or "general"
            perspective_groups.setdefault(key, []).append(r)

        group_winners = []
        for group_name, agents in perspective_groups.items():
            if not agents:
                continue

            # Find group winner by votes
            group_votes: dict[str, int] = {}
            for a in agents:
                group_votes[a.winner] = group_votes.get(a.winner, 0) + 1

            group_winner = max(group_votes, key=lambda k: group_votes[k])
            top_concern = ""
            for a in agents:
                if a.winner == group_winner and a.concerns:
                    first_concern = next(iter(a.concerns.values()), "")
                    if first_concern:
                        top_concern = first_concern
                        break

            dissent = [a for a in agents if a.winner != group_winner]

            group_winners.append({
                "group": group_name,
                "winner": group_winner,
                "score": report.weighted_scores.get(group_winner, 0),
                "top_concern": top_concern[:200],
                "consensus": f"{len([a for a in agents if a.winner == group_winner])}/{len(agents)}",
                "dissent": dissent[0].reason[:100] if dissent else "none",
            })

        if not group_winners:
            return None

        synthesis_prompt = build_synthesis_prompt(config, group_winners)

        # Use best available provider for synthesis (prefer Gemini for quality)
        synth_provider = self._pick_best_for_synthesis(available)
        if not synth_provider:
            return None

        logger.info(
            "Running LLM synthesis via {p}",
            p=synth_provider.get_provider_name(),
        )

        raw = await synth_provider.safe_evaluate(synthesis_prompt, temperature=0.3)
        if raw.get("error"):
            logger.warning("Synthesis failed: {e}", e=raw["error"][:200])
            return None

        return raw

    def _aggregate(
        self,
        config: SwarmConfig,
        results: list[AgentResult],
    ) -> SwarmReport:
        """Compute weighted scores and divergence from all agent results."""
        valid = [r for r in results if r.json_valid and not r.error]
        if not valid:
            return SwarmReport(
                config=config,
                agents_used=len(results),
                agents_succeeded=0,
                agent_results=results,
            )

        path_ids: set[str] = set()
        for r in valid:
            path_ids.update(r.scores.keys())

        if not path_ids:
            return SwarmReport(
                config=config,
                agents_used=len(results),
                agents_succeeded=len(valid),
                agent_results=results,
            )

        profiles = self.memory.get_model_profiles()
        weighted_scores = self._compute_weighted_scores(valid, path_ids, profiles, config.domain)
        divergence = self._detect_divergence(valid, path_ids)

        winner = max(weighted_scores, key=lambda k: weighted_scores[k]) if weighted_scores else ""
        winner_score = weighted_scores.get(winner, 0.0)

        provider_latencies: dict[str, list[int]] = {}
        for r in valid:
            provider_latencies.setdefault(r.provider, []).append(r.latency_ms)

        avg_latencies = {
            p: sum(lats) / len(lats)
            for p, lats in provider_latencies.items()
        }

        return SwarmReport(
            config=config,
            agents_used=len(results),
            agents_succeeded=len(valid),
            agent_results=results,
            weighted_scores=weighted_scores,
            divergence=divergence,
            winner=winner,
            winner_score=winner_score,
            passed_confidence_gate=winner_score >= 30.0,  # calibrated from benchmarks (agents score 29-35 range)
            provider_latencies=avg_latencies,
            total_latency_ms=max((r.latency_ms for r in valid), default=0),
            total_cost_estimate=sum(r.cost_estimate for r in valid),
        )

    def _compute_weighted_scores(
        self,
        results: list[AgentResult],
        path_ids: set[str],
        profiles: dict[str, Any],
        domain: DomainTag,
    ) -> dict[str, float]:
        """Compute weighted scores normalized to /50 scale."""
        totals: dict[str, float] = {p: 0.0 for p in path_ids}
        total_weight = 0.0

        for r in results:
            weight = 1.0
            if profiles and r.model in profiles:
                profile = profiles[r.model]
                if isinstance(profile, dict):
                    weight = profile.get("domain_weights", {}).get(
                        domain.value, profile.get("base_weight", 1.0)
                    )
                else:
                    weight = profile.get_weight(domain)

            # Hive multiplier: PROBATIONARY=0.8x, MEMBER=1.0x, SENIOR=1.1x, LEAD=1.2x
            if self.hive:
                weight *= self.hive.get_weight_multiplier(r.model)

            # v6: Conviction bonus — only for accurate agents who held firm
            # Old: flat 1.15x for all who held firm (rewarded stubbornness)
            # New: bonus = 0.15 * model_accuracy (rewards informed conviction)
            # 90% accurate + firm = 1.135x; 50% accurate + firm = 1.075x
            if r.held_firm and self.hive:
                hive_profile = self.hive.get_profile(r.model)
                if hive_profile and hive_profile.accuracy_overall > 0.5:
                    weight *= 1.0 + 0.15 * hive_profile.accuracy_overall

            total_weight += weight

            for pid in path_ids:
                path_scores = r.scores.get(pid)
                if path_scores:
                    raw = path_scores.total()
                    totals[pid] += (raw / 50.0) * weight

        if total_weight == 0:
            return totals

        return {p: round((v / total_weight) * 50, 1) for p, v in totals.items()}

    def _detect_divergence(
        self,
        results: list[AgentResult],
        path_ids: set[str],
    ) -> DivergenceReport:
        """Detect where evaluators disagree."""
        winner_votes: dict[str, int] = {p: 0 for p in path_ids}

        for r in results:
            w = r.winner
            if w in winner_votes:
                winner_votes[w] += 1

        total_votes = sum(winner_votes.values())
        if total_votes == 0:
            return DivergenceReport()

        top_winner = max(winner_votes, key=lambda k: winner_votes[k])
        consensus = winner_votes[top_winner] / total_votes

        return DivergenceReport(
            winner_votes=winner_votes,
            top_winner=top_winner,
            consensus_strength=round(consensus, 2),
            is_genuine_consensus=consensus >= 0.6,
            high_divergence=consensus < 0.4,
            split_paths=[p for p, v in winner_votes.items() if v > 0],
        )

    def _should_scale(
        self,
        divergence: DivergenceReport,
        config: SwarmConfig,
    ) -> tuple[bool, str]:
        """Decide if more agents are needed."""
        if divergence.high_divergence:
            return True, f"High divergence: consensus {divergence.consensus_strength:.0%} < 40%"

        if divergence.consensus_strength > 0.9 and config.stakes in (
            StakesLevel.HIGH, StakesLevel.CRITICAL
        ):
            return True, f"Suspicious consensus {divergence.consensus_strength:.0%} > 90% on high stakes"

        return False, ""

    def _collect_proposals(
        self,
        results: list[AgentResult],
        existing_paths: dict[str, PathDefinition] | None,
    ) -> list[PathProposal]:
        """
        Collect path proposals from all agents, deduplicate, and return novel ones.

        Deduplication: proposals with >40% word overlap in name+description are merged.
        Novelty check: proposals that duplicate existing paths are filtered out.
        Returns at most 3 accepted proposals (top by vote count, then confidence).
        """
        raw_proposals: list[PathProposal] = []
        for r in results:
            if r.proposed_path and r.json_valid and not r.error:
                p = r.proposed_path
                if p.name and p.description and len(p.name) > 2:
                    raw_proposals.append(p)

        if not raw_proposals:
            return []

        # Deduplicate: merge proposals with high name similarity
        def _words(s: str) -> set[str]:
            return set(s.lower().split())

        merged: list[PathProposal] = []
        for prop in raw_proposals:
            prop_words = _words(prop.name + " " + prop.description)
            found = False
            for existing in merged:
                ex_words = _words(existing.name + " " + existing.description)
                if not prop_words or not ex_words:
                    continue
                overlap = len(prop_words & ex_words) / max(len(prop_words | ex_words), 1)
                if overlap >= 0.40:
                    # Merge: keep highest confidence, increment votes
                    if prop.confidence > existing.confidence:
                        existing.name = prop.name
                        existing.description = prop.description
                        existing.rationale = prop.rationale
                        existing.confidence = prop.confidence
                    existing.votes += 1
                    found = True
                    break
            if not found:
                merged.append(prop.model_copy())

        # Filter out proposals that overlap with EXISTING paths
        if existing_paths:
            filtered: list[PathProposal] = []
            for prop in merged:
                prop_words = _words(prop.name + " " + prop.description)
                is_duplicate = False
                for pid, pdef in existing_paths.items():
                    if pdef is None:
                        continue
                    ex_words = _words(pdef.name + " " + pdef.description)
                    if not prop_words or not ex_words:
                        continue
                    overlap = len(prop_words & ex_words) / max(len(prop_words | ex_words), 1)
                    if overlap >= 0.50:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    filtered.append(prop)
            merged = filtered

        # Sort by votes DESC, then confidence DESC; take top 3
        merged.sort(key=lambda p: (-p.votes, -p.confidence))
        accepted = merged[:3]

        # Assign path IDs
        for i, prop in enumerate(accepted):
            prop.path_id = f"prop_{i}"

        if accepted:
            logger.info(
                "PathProposal: {n} novel paths proposed by agents (from {t} raw proposals)",
                n=len(accepted), t=len(raw_proposals),
            )
            for p in accepted:
                logger.info("  + [{v} votes] {name}: {desc}", v=p.votes, name=p.name, desc=p.description[:80])

        return accepted

    def _pick_fastest(self, available: list[LLMProvider]) -> LLMProvider | None:
        """Pick the fastest free provider for scaling."""
        free = [p for p in available if p.is_free()]
        if not free:
            return available[0] if available else None
        priority = {"groq": 0, "gemini": 1, "openrouter": 2}
        return min(free, key=lambda p: priority.get(p.get_provider_name(), 99))

    def _pick_best_for_synthesis(self, available: list[LLMProvider]) -> LLMProvider | None:
        """Pick best provider for LLM synthesis (quality > speed)."""
        # Prefer Gemini (good quality, free), then Groq, then others
        quality_priority = {"gemini": 0, "openai": 1, "deepseek": 2, "groq": 3, "openrouter": 4}
        if not available:
            return None
        return min(available, key=lambda p: quality_priority.get(p.get_provider_name(), 99))
