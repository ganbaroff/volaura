"""Multi-signal loop circuit breaker (Pattern 1 — LangGraph-inspired).

Replaces the single-metric `_char_similarity` Jaccard check in
`telegram_webhook.py`. A loop is flagged when ANY 2 of 3 independent signals
fire across the last N bot responses:

  * TOKEN VELOCITY — last 3 replies each emit fewer unique tokens than the
    configured minimum (low signal density = stall).
  * NO-PROGRESS    — reply matches a generic-stall phrase blocklist
    ("я понимаю что X является важным", "я могу создавать документы", ...).
  * PER-TOOL FAILURE — same tool has returned errors (HTTP 5xx / parse /
    timeout) on the last 3 consecutive invocations.

Design goals:
  * Stateless by default — caller feeds recent history in.
  * Zero external deps (Pydantic v2 only, already in stack).
  * Replaces `_char_similarity` for loop detection; the old function is kept
    for backwards compatibility with existing tests and is now deprecated.

Source: docs/research/agent-action-layer/summary.md Pattern 1.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

# ── Defaults (tuned for Atlas Telegram bot traffic — revisit after 1 week) ──
DEFAULT_MIN_UNIQUE_TOKENS = 30
DEFAULT_WINDOW_SIZE = 3

# Russian + English generic-stall phrases. Lowercased, partial-match.
# Add sparingly — every entry is a false-positive risk.
DEFAULT_STALL_BLOCKLIST: tuple[str, ...] = (
    "я понимаю что",
    "я могу создавать",
    "является важным",
    "является ключевым",
    "давай разберём по порядку",
    "как я уже говорил",
    "i understand that",
    "i can create",
    "as i mentioned before",
    "let me break this down",
)


_TOKEN_RE = re.compile(r"[a-zA-Zа-яА-ЯёЁ0-9]+", re.UNICODE)


def _unique_tokens(text: str) -> int:
    """Count unique lowercased word-tokens in `text`."""
    if not text:
        return 0
    return len({m.group(0).lower() for m in _TOKEN_RE.finditer(text)})


class LoopBreakDecision(BaseModel):
    """Result of a circuit-breaker evaluation."""

    model_config = ConfigDict(frozen=True)

    tripped: bool
    signals: list[str] = Field(default_factory=list)
    reason: str = ""

    def describe(self) -> str:
        if not self.tripped:
            return "no loop"
        return f"LOOP ({', '.join(self.signals)}): {self.reason}"


@dataclass
class LoopCircuitBreaker:
    """Stateless-ish multi-signal loop detector.

    Call `.evaluate(...)` with the last N bot responses + optional per-tool
    error history. Returns a `LoopBreakDecision`. Two-of-three signals → trip.

    Example:
        breaker = LoopCircuitBreaker()
        decision = breaker.evaluate(
            recent_replies=["...", "...", "..."],
            tool_error_streak={"github_issue": 3},
        )
        if decision.tripped:
            # open issue, notify CEO
            ...
    """

    min_unique_tokens: int = DEFAULT_MIN_UNIQUE_TOKENS
    window_size: int = DEFAULT_WINDOW_SIZE
    stall_phrases: tuple[str, ...] = DEFAULT_STALL_BLOCKLIST
    # Number of consecutive per-tool errors before the per-tool signal fires.
    tool_failure_threshold: int = 3

    # Per-tool consecutive-failure counter (mutable shared state for long-lived
    # instances). Callers may supply their own dict via `evaluate(...)` to stay
    # stateless if preferred.
    _tool_error_counter: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # ── Signal detectors ────────────────────────────────────────────────────

    def _signal_token_velocity(self, recent_replies: list[str]) -> bool:
        """True iff last `window_size` replies ALL fall below the unique-token floor."""
        if len(recent_replies) < self.window_size:
            return False
        window = recent_replies[-self.window_size :]
        return all(_unique_tokens(r) < self.min_unique_tokens for r in window)

    def _signal_no_progress(self, recent_replies: list[str]) -> tuple[bool, str]:
        """True if the most recent reply contains any stall phrase."""
        if not recent_replies:
            return False, ""
        latest = recent_replies[-1].lower()
        for phrase in self.stall_phrases:
            if phrase in latest:
                return True, phrase
        return False, ""

    def _signal_tool_failure(self, tool_error_streak: dict[str, int] | None) -> tuple[bool, str]:
        """True if any tool has >= `tool_failure_threshold` consecutive failures."""
        streak = tool_error_streak if tool_error_streak is not None else self._tool_error_counter
        for tool, count in streak.items():
            if count >= self.tool_failure_threshold:
                return True, tool
        return False, ""

    # ── Counter helpers (optional, for long-lived instances) ────────────────

    def record_tool_success(self, tool: str) -> None:
        """Reset the failure counter for `tool`."""
        self._tool_error_counter[tool] = 0

    def record_tool_failure(self, tool: str) -> None:
        """Increment the failure counter for `tool`."""
        self._tool_error_counter[tool] += 1

    # ── Public API ──────────────────────────────────────────────────────────

    def evaluate(
        self,
        recent_replies: list[str],
        tool_error_streak: dict[str, int] | None = None,
    ) -> LoopBreakDecision:
        """Evaluate the three signals. Trip if >= 2 fire."""
        fired: list[str] = []
        reasons: list[str] = []

        if self._signal_token_velocity(recent_replies):
            fired.append("token_velocity")
            reasons.append(f"last {self.window_size} replies < {self.min_unique_tokens} unique tokens")

        no_progress, phrase = self._signal_no_progress(recent_replies)
        if no_progress:
            fired.append("no_progress")
            reasons.append(f"stall phrase: {phrase!r}")

        tool_fail, tool = self._signal_tool_failure(tool_error_streak)
        if tool_fail:
            fired.append("per_tool_failure")
            reasons.append(f"tool {tool!r} >= {self.tool_failure_threshold} failures")

        tripped = len(fired) >= 2
        decision = LoopBreakDecision(
            tripped=tripped,
            signals=fired,
            reason="; ".join(reasons),
        )
        if tripped:
            logger.warning("loop circuit-breaker tripped: {d}", d=decision.describe())
        return decision


__all__ = ["LoopCircuitBreaker", "LoopBreakDecision"]
