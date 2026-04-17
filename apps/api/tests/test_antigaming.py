"""Unit tests for app.core.assessment.antigaming — anti-gaming detection engine."""

import pytest

from app.core.assessment.antigaming import (
    MIN_ITEMS_FOR_PATTERN_CHECK,
    MIN_ITEMS_FOR_TIME_CHECK,
    MIN_RAPID_GUESS_COUNT,
    TOO_FAST_MS,
    TOO_SLOW_MS,
    GamingSignal,
    analyse,
    check_answer_timing,
)


def _make_answer(response_time_ms=5000, response=1, raw_score=0.8, irt_b=0.0, theta_at_answer=0.0):
    return {
        "response_time_ms": response_time_ms,
        "response": response,
        "raw_score": raw_score,
        "irt_b": irt_b,
        "theta_at_answer": theta_at_answer,
    }


# ── GamingSignal.flags ──────────────────────────────────────────────────────


class TestGamingSignalFlags:
    def test_no_flags_default(self):
        s = GamingSignal()
        assert s.flags == []

    def test_excessive_rushing(self):
        s = GamingSignal(rushed_count=4)
        assert "excessive_rushing" in s.flags

    def test_rushing_below_threshold(self):
        s = GamingSignal(rushed_count=3)
        assert "excessive_rushing" not in s.flags

    def test_excessive_slowness(self):
        s = GamingSignal(slow_count=3)
        assert "excessive_slowness" in s.flags

    def test_slowness_below_threshold(self):
        s = GamingSignal(slow_count=2)
        assert "excessive_slowness" not in s.flags

    def test_alternating_flag(self):
        s = GamingSignal(is_alternating=True)
        assert "alternating_pattern" in s.flags

    def test_all_identical_flag(self):
        s = GamingSignal(is_all_identical=True)
        assert "all_identical_responses" in s.flags

    def test_group_alternating_flag(self):
        s = GamingSignal(is_group_alternating=True)
        assert "group_alternating_pattern" in s.flags

    def test_time_clustering_flag(self):
        s = GamingSignal(is_time_clustered=True)
        assert "time_clustering" in s.flags

    def test_rapid_guessing_flag(self):
        s = GamingSignal(rapid_guess_count=MIN_RAPID_GUESS_COUNT)
        assert "rapid_guessing" in s.flags

    def test_rapid_guessing_below_threshold(self):
        s = GamingSignal(rapid_guess_count=MIN_RAPID_GUESS_COUNT - 1)
        assert "rapid_guessing" not in s.flags


# ── analyse() — empty/basic ─────────────────────────────────────────────────


class TestAnalyseBasic:
    def test_empty_answers(self):
        result = analyse([])
        assert result.overall_flag is False
        assert result.penalty_multiplier == 1.0

    def test_single_normal_answer(self):
        result = analyse([_make_answer()])
        assert result.rushed_count == 0
        assert result.slow_count == 0
        assert result.overall_flag is False

    def test_single_fast_answer(self):
        result = analyse([_make_answer(response_time_ms=1000)])
        assert result.rushed_count == 1

    def test_single_slow_answer(self):
        result = analyse([_make_answer(response_time_ms=TOO_SLOW_MS + 1)])
        assert result.slow_count == 1


# ── analyse() — timing ──────────────────────────────────────────────────────


class TestAnalyseTiming:
    def test_zero_ms_counts_as_rushed(self):
        result = analyse([_make_answer(response_time_ms=0)])
        assert result.rushed_count == 1

    def test_negative_ms_counts_as_rushed(self):
        result = analyse([_make_answer(response_time_ms=-100)])
        assert result.rushed_count == 1

    def test_boundary_too_fast(self):
        result = analyse([_make_answer(response_time_ms=TOO_FAST_MS - 1)])
        assert result.rushed_count == 1

    def test_boundary_exactly_too_fast(self):
        result = analyse([_make_answer(response_time_ms=TOO_FAST_MS)])
        assert result.rushed_count == 0

    def test_boundary_too_slow(self):
        result = analyse([_make_answer(response_time_ms=TOO_SLOW_MS)])
        assert result.slow_count == 0

    def test_boundary_above_too_slow(self):
        result = analyse([_make_answer(response_time_ms=TOO_SLOW_MS + 1)])
        assert result.slow_count == 1


# ── analyse() — alternating pattern ─────────────────────────────────────────


class TestAnalyseAlternating:
    def test_perfect_alternating(self):
        answers = [_make_answer(response=i % 2) for i in range(10)]
        result = analyse(answers)
        assert result.is_alternating is True

    def test_not_alternating(self):
        answers = [_make_answer(response=1)] * 5 + [_make_answer(response=0)] * 5
        result = analyse(answers)
        assert result.is_alternating is False

    def test_below_min_items_no_pattern_check(self):
        answers = [_make_answer(response=i % 2) for i in range(MIN_ITEMS_FOR_PATTERN_CHECK - 1)]
        result = analyse(answers)
        assert result.is_alternating is False


# ── analyse() — all identical ────────────────────────────────────────────────


class TestAnalyseIdentical:
    def test_all_zeros(self):
        answers = [_make_answer(response=0)] * 10
        result = analyse(answers)
        assert result.is_all_identical is True

    def test_all_ones(self):
        answers = [_make_answer(response=1)] * 10
        result = analyse(answers)
        assert result.is_all_identical is True

    def test_mixed_responses(self):
        answers = [_make_answer(response=1)] * 5 + [_make_answer(response=0)] * 5
        result = analyse(answers)
        assert result.is_all_identical is False


# ── analyse() — group alternating (S8.2) ────────────────────────────────────


class TestAnalyseGroupAlternating:
    def test_grouped_pattern(self):
        responses = [1, 1, 0, 0, 1, 1, 0, 0]
        answers = [_make_answer(response=r) for r in responses]
        result = analyse(answers)
        assert result.is_group_alternating is True

    def test_non_grouped_pattern(self):
        responses = [1, 0, 1, 1, 0, 1, 0, 0, 1, 0]
        answers = [_make_answer(response=r) for r in responses]
        result = analyse(answers)
        assert result.is_group_alternating is False

    def test_groups_of_three(self):
        responses = [1, 1, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0]
        answers = [_make_answer(response=r) for r in responses]
        result = analyse(answers)
        assert result.is_group_alternating is True


# ── analyse() — time clustering (S8.2) ──────────────────────────────────────


class TestAnalyseTimeClustering:
    def test_uniform_timing_flags(self):
        answers = [_make_answer(response_time_ms=5000) for _ in range(MIN_ITEMS_FOR_TIME_CHECK)]
        result = analyse(answers)
        assert result.is_time_clustered is True

    def test_varied_timing_no_flag(self):
        times = [3000, 8000, 5000, 12000, 4000, 15000]
        answers = [_make_answer(response_time_ms=t) for t in times]
        result = analyse(answers)
        assert result.is_time_clustered is False

    def test_below_min_items_no_time_check(self):
        answers = [_make_answer(response_time_ms=5000) for _ in range(MIN_ITEMS_FOR_TIME_CHECK - 1)]
        result = analyse(answers)
        assert result.is_time_clustered is False


# ── analyse() — rapid guessing (RT-IRT) ─────────────────────────────────────


class TestAnalyseRapidGuessing:
    def test_correct_hard_fast_flags(self):
        # Median must be high so rapid answers (1s) fall below 40% of expected time.
        # expected_time = median * (1 + 0.3 * min(gap, 3)) = median * 1.9 for gap=3.
        # threshold = 0.4 * expected = 0.76 * median. Need 1000 < 0.76 * median → median > 1316.
        normal = [_make_answer(response_time_ms=20000, raw_score=0.5, irt_b=0.0, theta_at_answer=0.0) for _ in range(5)]
        rapid = [_make_answer(response_time_ms=1000, raw_score=0.8, irt_b=3.0, theta_at_answer=0.0) for _ in range(3)]
        answers = normal + rapid
        result = analyse(answers)
        assert result.rapid_guess_count >= MIN_RAPID_GUESS_COUNT

    def test_incorrect_hard_fast_no_flag(self):
        answers = [
            _make_answer(
                response_time_ms=1000,
                raw_score=0.3,
                irt_b=3.0,
                theta_at_answer=0.0,
            )
            for _ in range(5)
        ]
        result = analyse(answers)
        assert result.rapid_guess_count == 0

    def test_correct_easy_fast_no_flag(self):
        answers = [
            _make_answer(
                response_time_ms=1000,
                raw_score=0.8,
                irt_b=0.0,
                theta_at_answer=0.0,
            )
            for _ in range(5)
        ]
        result = analyse(answers)
        assert result.rapid_guess_count == 0


# ── analyse() — penalty multiplier ──────────────────────────────────────────


class TestAnalysePenalty:
    def test_no_flags_no_penalty(self):
        result = analyse([_make_answer()])
        assert result.penalty_multiplier == 1.0

    def test_one_flag_penalty(self):
        answers = [_make_answer(response=1)] * 10
        result = analyse(answers)
        assert result.overall_flag is True
        num_flags = len(result.flags)
        expected = max(0.1, 1.0 - 0.15 * num_flags)
        assert result.penalty_multiplier == pytest.approx(expected)

    def test_multiple_flags_stacking(self):
        answers = [_make_answer(response_time_ms=5000, response=i % 2) for i in range(10)]
        result = analyse(answers)
        if len(result.flags) >= 2:
            assert result.penalty_multiplier < 0.85

    def test_penalty_floor(self):
        s = GamingSignal(
            rushed_count=10,
            is_alternating=True,
            is_all_identical=True,
            is_group_alternating=True,
            is_time_clustered=True,
            rapid_guess_count=5,
        )
        flags = s.flags
        penalty = max(0.1, 1.0 - 0.15 * len(flags))
        assert penalty >= 0.1


# ── check_answer_timing() ───────────────────────────────────────────────────


class TestCheckAnswerTiming:
    def test_too_fast(self):
        result = check_answer_timing(1000)
        assert result["valid"] is False
        assert result["warning"] is not None

    def test_too_slow(self):
        result = check_answer_timing(TOO_SLOW_MS + 1)
        assert result["valid"] is True
        assert result["warning"] is not None

    def test_normal(self):
        result = check_answer_timing(10000)
        assert result["valid"] is True
        assert result["warning"] is None

    def test_boundary_fast(self):
        result = check_answer_timing(TOO_FAST_MS)
        assert result["valid"] is True

    def test_boundary_slow(self):
        result = check_answer_timing(TOO_SLOW_MS)
        assert result["valid"] is True
        assert result["warning"] is None
