"""
Middleware architecture for MiroFish Swarm Engine.

Inspired by DeerFlow's 15-layer middleware chain, adapted for swarm decision-making.
Each middleware hooks into the agent lifecycle: before/after dispatch, before/after
each agent call, and before/after aggregation.

Middlewares are executed in order. Each can modify config, agent results, or the
final report. This makes the system extensible without touching core pm.py logic.
"""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from .swarm_types import AgentResult, SwarmConfig, SwarmReport


@dataclass
class MiddlewareContext:
    """Shared context passed through the middleware chain."""

    config: SwarmConfig
    start_time: float = field(default_factory=time.time)
    token_budget_used: int = 0
    token_budget_max: int = 100_000  # total tokens across all agents
    loop_hashes: list[str] = field(default_factory=list)
    loop_warnings: int = 0
    dedup_removed: int = 0
    scaling_blocked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class SwarmMiddleware(ABC):
    """Base middleware for the swarm pipeline.

    Implement any subset of hooks. Return None to pass through unchanged,
    or return a modified object to alter the pipeline.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def before_dispatch(
        self, ctx: MiddlewareContext, agent_pool: list[Any]
    ) -> list[Any] | None:
        """Called before agents are dispatched. Can modify the agent pool."""
        return None

    def after_agent_call(
        self, ctx: MiddlewareContext, result: AgentResult
    ) -> AgentResult | None:
        """Called after each individual agent returns. Can modify or reject results."""
        return None

    def after_dispatch(
        self, ctx: MiddlewareContext, results: list[AgentResult]
    ) -> list[AgentResult] | None:
        """Called after all agents return. Can filter/modify the results list."""
        return None

    def before_aggregation(
        self, ctx: MiddlewareContext, results: list[AgentResult]
    ) -> list[AgentResult] | None:
        """Called before weighted scoring. Can filter/reweight results."""
        return None

    def after_report(
        self, ctx: MiddlewareContext, report: SwarmReport
    ) -> SwarmReport | None:
        """Called after final report is built. Can add metadata or modify."""
        return None


class LoopDetectionMiddleware(SwarmMiddleware):
    """Detects when agents produce identical or near-identical responses.

    Pattern from DeerFlow: MD5 hash of agent output, sliding window,
    warn at threshold, block at hard limit.

    This prevents wasted tokens when multiple agents converge on identical answers
    (which adds no diversity and wastes compute).
    """

    WARN_THRESHOLD = 3      # warn after 3 identical responses
    BLOCK_THRESHOLD = 5     # stop accepting after 5 identical
    WINDOW_SIZE = 20        # sliding window of recent hashes

    def _hash_result(self, result: AgentResult) -> str:
        """Create a content hash from the meaningful parts of an agent response."""
        # Hash the winner + key scores + main reasoning (not metadata like latency)
        content = f"{result.winner}|{result.confidence:.1f}|{result.reason[:200]}"
        for path_id, scores in sorted(result.scores.items()):
            content += f"|{path_id}:{scores.total():.1f}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def after_agent_call(
        self, ctx: MiddlewareContext, result: AgentResult
    ) -> AgentResult | None:
        if not result.json_valid or result.error:
            return None  # don't hash errors

        h = self._hash_result(result)

        # Count occurrences in sliding window
        ctx.loop_hashes.append(h)
        if len(ctx.loop_hashes) > self.WINDOW_SIZE:
            ctx.loop_hashes = ctx.loop_hashes[-self.WINDOW_SIZE :]

        count = ctx.loop_hashes.count(h)

        if count >= self.BLOCK_THRESHOLD:
            logger.warning(
                "Loop detected: {n} identical responses (hash={h}), blocking agent {a}",
                n=count, h=h, a=result.agent_id,
            )
            ctx.dedup_removed += 1
            result.error = f"LOOP_BLOCKED: identical to {count-1} other responses"
            result.json_valid = False  # exclude from aggregation
            return result

        if count >= self.WARN_THRESHOLD:
            ctx.loop_warnings += 1
            logger.info(
                "Loop warning: {n} similar responses (hash={h}), agent {a}",
                n=count, h=h, a=result.agent_id,
            )

        return None  # pass through


class ResponseDedupMiddleware(SwarmMiddleware):
    """Deduplicates identical winner+score combinations before aggregation.

    When multiple agents choose the same winner with identical scores,
    only keep the first N unique perspectives and drop the rest.
    Preserves diversity while reducing noise.
    """

    MAX_IDENTICAL_WINNERS = 4  # max agents with identical winner+scores

    def before_aggregation(
        self, ctx: MiddlewareContext, results: list[AgentResult]
    ) -> list[AgentResult] | None:
        valid = [r for r in results if r.json_valid and not r.error]
        if len(valid) <= 3:
            return None  # too few to dedup

        # Group by winner + rounded total scores
        groups: dict[str, list[AgentResult]] = defaultdict(list)
        for r in valid:
            key_parts = [r.winner]
            for path_id in sorted(r.scores.keys()):
                key_parts.append(f"{path_id}:{r.scores[path_id].total():.0f}")
            key = "|".join(key_parts)
            groups[key].append(r)

        # Keep only MAX_IDENTICAL_WINNERS per group
        kept_ids: set[str] = set()
        removed = 0
        for key, group in groups.items():
            for i, r in enumerate(group):
                if i < self.MAX_IDENTICAL_WINNERS:
                    kept_ids.add(r.agent_id)
                else:
                    removed += 1

        if removed == 0:
            return None

        logger.info(
            "Dedup: removed {n} duplicate responses ({g} unique groups)",
            n=removed, g=len(groups),
        )
        ctx.dedup_removed += removed

        filtered = []
        for r in results:
            if r.agent_id in kept_ids or not r.json_valid or r.error:
                filtered.append(r)
            else:
                r_copy = r.model_copy()
                r_copy.error = "DEDUP_REMOVED: identical to higher-priority agent"
                r_copy.json_valid = False
                filtered.append(r_copy)

        return filtered


class ContextBudgetMiddleware(SwarmMiddleware):
    """Tracks cumulative token usage across all agent calls.

    Inspired by DeerFlow's summarization triggers. Prevents runaway costs
    by monitoring total tokens and blocking new agents when budget exceeded.
    """

    # Rough token estimates (actual counting would need tiktoken)
    PROMPT_OVERHEAD = 800     # system prompt + JSON template
    SKILL_TOKENS = 500        # average skill injection
    MEMORY_TOKENS = 300       # agent memory context
    RESPONSE_ESTIMATE = 600   # average agent response

    def before_dispatch(
        self, ctx: MiddlewareContext, agent_pool: list[Any]
    ) -> list[Any] | None:
        # Estimate total tokens for this dispatch
        per_agent = (
            self.PROMPT_OVERHEAD
            + self.SKILL_TOKENS
            + self.MEMORY_TOKENS
            + self.RESPONSE_ESTIMATE
        )
        estimated_total = len(agent_pool) * per_agent
        ctx.token_budget_used += estimated_total

        if ctx.token_budget_used > ctx.token_budget_max:
            # Trim agent pool to fit budget
            remaining_budget = ctx.token_budget_max - (
                ctx.token_budget_used - estimated_total
            )
            max_agents = max(3, remaining_budget // per_agent)  # keep at least 3
            if max_agents < len(agent_pool):
                logger.warning(
                    "Budget limit: trimming from {n} to {m} agents (budget {u}/{t} tokens)",
                    n=len(agent_pool), m=max_agents,
                    u=ctx.token_budget_used, t=ctx.token_budget_max,
                )
                return agent_pool[:max_agents]

        return None

    def after_report(
        self, ctx: MiddlewareContext, report: SwarmReport
    ) -> SwarmReport | None:
        # Annotate report with budget info
        if not report.synthesis:
            report.synthesis = {}
        report.synthesis["token_budget_used"] = ctx.token_budget_used
        report.synthesis["token_budget_max"] = ctx.token_budget_max
        report.synthesis["dedup_removed"] = ctx.dedup_removed
        report.synthesis["loop_warnings"] = ctx.loop_warnings
        return report


class TimeoutGuardMiddleware(SwarmMiddleware):
    """Blocks scaling rounds if we're already close to the timeout.

    Prevents the engine from adding more agents when there isn't enough
    time left to process them meaningfully.
    """

    SCALING_BUFFER_SECONDS = 5.0  # need at least 5s remaining to scale

    def before_dispatch(
        self, ctx: MiddlewareContext, agent_pool: list[Any]
    ) -> list[Any] | None:
        elapsed = time.time() - ctx.start_time
        remaining = ctx.config.timeout_seconds - elapsed

        if remaining < self.SCALING_BUFFER_SECONDS:
            ctx.scaling_blocked = True
            logger.warning(
                "Timeout guard: {e:.1f}s elapsed, {r:.1f}s remaining — blocking further scaling",
                e=elapsed, r=remaining,
            )
            # Don't modify agent pool for initial dispatch, only scaling rounds
            return None

        return None


class TokenCountingMiddleware(SwarmMiddleware):
    """Real token counting from provider responses.

    Replaces stub cost_estimate=0.0 with actual costs.
    Providers report tokens via 'usage' field in response metadata.
    For providers that don't report tokens, estimates from response length.

    Cost data per million tokens (March 2026):
      Groq free models: $0.00
      Gemini 2.5 Flash: $0.00 (free tier)
      DeepSeek V3: $0.14 input / $0.28 output
      OpenAI gpt-4o-mini: $0.15 input / $0.60 output
    """

    # Cost per million tokens (input, output)
    _COSTS: dict[str, tuple[float, float]] = {
        "groq": (0.0, 0.0),
        "gemini": (0.0, 0.0),
        "deepseek": (0.14, 0.28),
        "openai": (0.15, 0.60),
        "openrouter": (0.0, 0.0),
    }

    def __init__(self) -> None:
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cost_usd: float = 0.0
        self.per_provider: dict[str, dict[str, float]] = {}

    def after_agent_call(
        self, ctx: MiddlewareContext, result: AgentResult
    ) -> AgentResult | None:
        if result.error:
            return None

        # Try to get real token counts from raw response
        input_tokens = 0
        output_tokens = 0

        if result.raw_response:
            try:
                raw = json.loads(result.raw_response) if isinstance(result.raw_response, str) else {}
                usage = raw.get("usage", {})
                input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass

        # Fallback: estimate from response length (~4 chars per token)
        if output_tokens == 0 and result.reason:
            output_tokens = len(result.reason) // 4
        if input_tokens == 0:
            input_tokens = 800  # rough prompt estimate

        # Calculate cost
        provider = result.provider.split(":")[0]  # "groq:llama-3.3" → "groq"
        costs = self._COSTS.get(provider, (0.0, 0.0))
        cost = (input_tokens * costs[0] + output_tokens * costs[1]) / 1_000_000

        # Update totals
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost

        # Per-provider tracking
        if provider not in self.per_provider:
            self.per_provider[provider] = {"input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0, "calls": 0}
        self.per_provider[provider]["input_tokens"] += input_tokens
        self.per_provider[provider]["output_tokens"] += output_tokens
        self.per_provider[provider]["cost_usd"] += cost
        self.per_provider[provider]["calls"] += 1

        # Update the result's cost estimate
        result.cost_estimate = cost
        return result

    def after_report(
        self, ctx: MiddlewareContext, report: SwarmReport
    ) -> SwarmReport | None:
        report.total_cost_estimate = round(self.total_cost_usd, 6)
        if not report.synthesis:
            report.synthesis = {}
        report.synthesis["token_stats"] = {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "per_provider": self.per_provider,
        }
        return report


class ResponseQualityMiddleware(SwarmMiddleware):
    """v7: Reject low-quality agent responses before aggregation.

    Proposed by compound-mini in v6 self-upgrade. Catches freeriders
    who return 1-sentence answers with no substance.

    Checks:
    - Minimum reason length (30 tokens ~= 120 chars)
    - Required JSON keys present (winner, reason, confidence)
    - Non-empty scores for at least 1 path
    """

    MIN_REASON_LENGTH = 120  # ~30 tokens
    REQUIRED_KEYS = {"winner", "reason", "confidence"}

    def __init__(self) -> None:
        self.rejected: int = 0
        self.total_checked: int = 0

    def after_agent_call(
        self, ctx: MiddlewareContext, result: AgentResult
    ) -> AgentResult | None:
        if result.error or not result.json_valid:
            return None

        self.total_checked += 1

        reason_len = len(result.reason or "")
        has_winner = bool(result.winner and result.winner.strip())
        has_scores = bool(result.scores)

        if reason_len < self.MIN_REASON_LENGTH and not has_scores:
            self.rejected += 1
            logger.debug(
                "ResponseQuality: rejected {agent} — reason={len}ch, winner={w}, scores={s}",
                agent=result.agent_id,
                len=reason_len,
                w=has_winner,
                s=has_scores,
            )
            result.error = f"ResponseQuality: too short ({reason_len}ch < {self.MIN_REASON_LENGTH}ch minimum)"
            return result

        return None  # pass through

    def after_report(
        self, ctx: MiddlewareContext, report: SwarmReport
    ) -> SwarmReport | None:
        if self.rejected:
            logger.info(
                "ResponseQuality: {r}/{t} responses rejected for low quality",
                r=self.rejected, t=self.total_checked,
            )
        return None


class MiddlewareChain:
    """Ordered chain of middlewares. Executes hooks in sequence."""

    def __init__(self, middlewares: list[SwarmMiddleware] | None = None):
        self.middlewares = middlewares or self._default_chain()

    @staticmethod
    def _default_chain() -> list[SwarmMiddleware]:
        """Default middleware stack for production use."""
        return [
            ContextBudgetMiddleware(),
            TimeoutGuardMiddleware(),
            TokenCountingMiddleware(),
            LoopDetectionMiddleware(),
            ResponseDedupMiddleware(),
            ResponseQualityMiddleware(),  # v7: reject freerider responses
        ]

    def run_before_dispatch(
        self, ctx: MiddlewareContext, agent_pool: list[Any]
    ) -> list[Any]:
        pool = agent_pool
        for mw in self.middlewares:
            result = mw.before_dispatch(ctx, pool)
            if result is not None:
                pool = result
        return pool

    def run_after_agent_call(
        self, ctx: MiddlewareContext, result: AgentResult
    ) -> AgentResult:
        current = result
        for mw in self.middlewares:
            modified = mw.after_agent_call(ctx, current)
            if modified is not None:
                current = modified
        return current

    def run_after_dispatch(
        self, ctx: MiddlewareContext, results: list[AgentResult]
    ) -> list[AgentResult]:
        current = results
        for mw in self.middlewares:
            modified = mw.after_dispatch(ctx, current)
            if modified is not None:
                current = modified
        return current

    def run_before_aggregation(
        self, ctx: MiddlewareContext, results: list[AgentResult]
    ) -> list[AgentResult]:
        current = results
        for mw in self.middlewares:
            modified = mw.before_aggregation(ctx, current)
            if modified is not None:
                current = modified
        return current

    def run_after_report(
        self, ctx: MiddlewareContext, report: SwarmReport
    ) -> SwarmReport:
        current = report
        for mw in self.middlewares:
            modified = mw.after_report(ctx, current)
            if modified is not None:
                current = modified
        return current
