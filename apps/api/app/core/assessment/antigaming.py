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

# S8.2: Grouped alternating bypass detection (e.g. [1,1,0,0,1,1,0,0])
MIN_RUNS_FOR_GROUP_CHECK = 4     # need ≥4 runs to establish grouped pattern
MIN_RUN_LENGTH_FOR_GROUP = 2     # all runs must be ≥2 items to qualify as "grouped"

# S8.2: Time clustering detection — robotic uniform timing
MIN_ITEMS_FOR_TIME_CHECK = 6     # insufficient data below this threshold
TIME_CLUSTERING_CV_THRESHOLD = 0.15  # CV (std/mean) < 0.15 → suspiciously uniform

# RT-IRT: Rapid guessing detection (van der Linden 2006, Gemini research 2026-03-26)
# Flags: correct answer on hard item (b >> theta) answered too fast
# Threshold: response < 40% of expected time for that difficulty gap
RAPID_GUESS_TIME_RATIO = 0.40    # answered in < 40% of expected time
RAPID_GUESS_DIFFICULTY_GAP = 1.0  # item difficulty (b) must exceed theta by ≥ 1.0 logits
MIN_RAPID_GUESS_COUNT = 2        # need ≥2 such events to flag (single could be luck)


@dataclass
class GamingSignal:
    """Summary of anti-gaming analysis for a session."""
    rushed_count: int = 0             # answers submitted < TOO_FAST_MS
    slow_count: int = 0               # answers that took > TOO_SLOW_MS
    is_alternating: bool = False      # 101010 or 010101 pattern
    is_all_identical: bool = False    # all same binary response
    is_group_alternating: bool = False  # S8.2: grouped bypass [1,1,0,0,1,1,0,0]
    is_time_clustered: bool = False     # S8.2: robotic uniform timing (CV < 0.15)
    rapid_guess_count: int = 0          # RT-IRT: correct on hard item answered too fast
    overall_flag: bool = False        # True if any serious flag raised
    penalty_multiplier: float = 1.0   # 1.0 = no penalty, 0.0 = zero score

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
        if self.is_group_alternating:
            out.append("group_alternating_pattern")
        if self.is_time_clustered:
            out.append("time_clustering")
        if self.rapid_guess_count >= MIN_RAPID_GUESS_COUNT:
            out.append("rapid_guessing")
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

        # S8.2: Grouped alternating bypass detection [1,1,0,0,1,1,0,0]
        # Run-length encode → check values alternate AND all run lengths ≥ 2.
        # This catches the bypass where test-takers group answers to avoid the
        # strict 1010 check, while correctly skipping natural patterns like
        # [1,0,1,1,0,1,0,0,1,0] which mix run lengths of 1 and 2.
        runs: list[tuple[int, int]] = []
        cur_val = responses[0]
        cur_len = 1
        for r in responses[1:]:
            if r == cur_val:
                cur_len += 1
            else:
                runs.append((cur_val, cur_len))
                cur_val = r
                cur_len = 1
        runs.append((cur_val, cur_len))

        if len(runs) >= MIN_RUNS_FOR_GROUP_CHECK:
            run_values_alternate = all(
                runs[i][0] != runs[i + 1][0] for i in range(len(runs) - 1)
            )
            all_runs_grouped = all(length >= MIN_RUN_LENGTH_FOR_GROUP for _, length in runs)
            if run_values_alternate and all_runs_grouped:
                signal.is_group_alternating = True

    # S8.2: Time clustering — robotic uniform timing (CV < threshold)
    # Requires at least MIN_ITEMS_FOR_TIME_CHECK answers to avoid false positives.
    if n >= MIN_ITEMS_FOR_TIME_CHECK:
        times = [int(ans.get("response_time_ms", 0)) for ans in answers]
        mean_time = sum(times) / len(times)
        if mean_time > 0:
            variance = sum((t - mean_time) ** 2 for t in times) / len(times)
            std_dev = variance ** 0.5
            cv = std_dev / mean_time
            if cv < TIME_CLUSTERING_CV_THRESHOLD:
                signal.is_time_clustered = True

    # ── RT-IRT: Rapid guessing detection (van der Linden 2006) ───────────────
    # Flags: correct answer on a HARD item (b >> theta) answered suspiciously fast.
    # Uses estimated theta from the session's current ability estimate.
    # Expected time is derived from item difficulty relative to median session time.
    if n >= MIN_ITEMS_FOR_PATTERN_CHECK:
        times = [int(ans.get("response_time_ms", 0)) for ans in answers]
        median_time = sorted(times)[n // 2]

        for ans in answers:
            # Only flag correct answers (raw_score >= 0.5)
            if float(ans.get("raw_score", 0)) < 0.5:
                continue

            irt_b = float(ans.get("irt_b", 0.0))
            theta = float(ans.get("theta_at_answer", 0.0))  # snapshot theta (optional)
            difficulty_gap = irt_b - theta

            # Only flag if item was genuinely harder than current ability
            if difficulty_gap < RAPID_GUESS_DIFFICULTY_GAP:
                continue

            # Expected time scales with difficulty: harder item → longer expected time
            expected_time_ms = median_time * (1.0 + 0.3 * min(difficulty_gap, 3.0))
            actual_time_ms = int(ans.get("response_time_ms", 0))

            if actual_time_ms > 0 and actual_time_ms < RAPID_GUESS_TIME_RATIO * expected_time_ms:
                signal.rapid_guess_count += 1

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
