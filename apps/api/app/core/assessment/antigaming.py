"""Anti-gaming checks for the adaptive assessment.

Detects suspicious response patterns that might indicate:
- Rushing (too fast to have genuinely read the question)
- Abandonment (extremely long pauses)
- Alternating patterns (1010101...)
- All-identical responses (all 0 or all 1 throughout)

Returns a `GamingSignal` dataclass. Severe signals cause the session
to be flagged; score penalties are applied downstream in AURA calculation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── Thresholds ────────────────────────────────────────────────────────────────

TOO_FAST_MS = 3_000       # < 3 s → almost certainly not reading
TOO_SLOW_MS = 5 * 60_000  # > 5 min → likely abandoned / distracted
MIN_ITEMS_FOR_PATTERN_CHECK = 5  # Need at least 5 answers to detect patterns
ALTERNATING_RATIO_THRESHOLD = 0.8  # 80%+ alternations → suspicious
IDENTICAL_RATIO_THRESHOLD = 0.9   # 90%+ identical → suspicious


@dataclass
class GamingSignal:
    """Summary of anti-gaming analysis for a session."""
    rushed_count: int = 0          # answers submitted < TOO_FAST_MS
    slow_count: int = 0            # answers that took > TOO_SLOW_MS
    is_alternating: bool = False   # 101010 or 010101 pattern
    is_all_identical: bool = False # all same binary response
    overall_flag: bool = False     # True if any serious flag raised
    penalty_multiplier: float = 1.0  # 1.0 = no penalty, 0.0 = zero score

    @property
    def flags(self) -> list[str]:
        out: list[str] = []
        if self.rushed_count > 3:
            out.append("excessive_rushing")
        if self.slow_count > 2:
            out.append("excessive_slowness")
        if self.is_alternating:
            out.append("alternating_pattern")
        if self.is_all_identical:
            out.append("all_identical_responses")
        return out


def analyse(answers: list[dict[str, Any]]) -> GamingSignal:
    """Run all anti-gaming checks on a list of answer records.

    Each answer dict should contain:
        - `response_time_ms` (int)
        - `response` (int: 0 or 1)
        - `raw_score` (float)

    Returns:
        GamingSignal with all flags populated.
    """
    signal = GamingSignal()

    if not answers:
        return signal

    # ── Response-time checks ─────────────────────────────────────────────────
    for ans in answers:
        ms = int(ans.get("response_time_ms", 0))
        # ms <= 0 means client sent invalid/spoofed timing — treat as rushed
        if ms <= 0 or ms < TOO_FAST_MS:
            signal.rushed_count += 1
        elif ms > TOO_SLOW_MS:
            signal.slow_count += 1

    # ── Pattern checks (only meaningful with enough data) ────────────────────
    responses = [int(ans.get("response", 0)) for ans in answers]
    n = len(responses)

    if n >= MIN_ITEMS_FOR_PATTERN_CHECK:
        # Alternating pattern: count adjacent pairs that differ
        alternations = sum(
            1 for i in range(n - 1) if responses[i] != responses[i + 1]
        )
        alternation_ratio = alternations / (n - 1)
        if alternation_ratio >= ALTERNATING_RATIO_THRESHOLD:
            signal.is_alternating = True

        # All-identical: one value dominates
        dominant = max(responses.count(0), responses.count(1))
        identical_ratio = dominant / n
        if identical_ratio >= IDENTICAL_RATIO_THRESHOLD:
            signal.is_all_identical = True

    # ── Overall flag & penalty ────────────────────────────────────────────────
    flags = signal.flags
    if flags:
        signal.overall_flag = True
        # Progressive penalty: each flag reduces multiplier by 0.15
        signal.penalty_multiplier = max(0.1, 1.0 - 0.15 * len(flags))

    return signal


def check_answer_timing(response_time_ms: int) -> dict[str, Any]:
    """Validate a single response's timing.

    Returns a dict with `valid` bool and optional `warning` string.
    Used at answer-submit time to give immediate feedback to the frontend.
    """
    if response_time_ms < TOO_FAST_MS:
        return {"valid": False, "warning": "Response too fast — please read the question carefully"}
    if response_time_ms > TOO_SLOW_MS:
        return {"valid": True, "warning": "Very slow response — connection timeout risk"}
    return {"valid": True, "warning": None}
