"""Unit tests for app.core.assessment.engine — IRT/CAT adaptive engine."""

import math

import pytest

from app.core.assessment.engine import (
    ENERGY_STOPPING,
    MAX_ITEMS,
    CATState,
    ItemRecord,
    _fisher_information,
    _normal_density,
    _prob_3pl,
    select_next_item,
    should_stop,
    submit_response,
    theta_to_score,
)

# ── _prob_3pl ───────────────────────────────────────────────────────────────


class TestProb3PL:
    def test_at_difficulty(self):
        p = _prob_3pl(theta=0.0, a=1.0, b=0.0, c=0.0)
        assert p == pytest.approx(0.5, abs=0.01)

    def test_high_ability(self):
        p = _prob_3pl(theta=3.0, a=1.0, b=0.0, c=0.0)
        assert p > 0.9

    def test_low_ability(self):
        p = _prob_3pl(theta=-3.0, a=1.0, b=0.0, c=0.0)
        assert p < 0.1

    def test_guessing_parameter(self):
        p = _prob_3pl(theta=-10.0, a=1.0, b=0.0, c=0.25)
        assert p == pytest.approx(0.25, abs=0.01)

    def test_extreme_positive_theta(self):
        p = _prob_3pl(theta=100.0, a=1.0, b=0.0, c=0.0)
        assert p == pytest.approx(1.0, abs=0.01)

    def test_extreme_negative_theta(self):
        p = _prob_3pl(theta=-100.0, a=1.0, b=0.0, c=0.0)
        assert p == pytest.approx(0.0, abs=0.01)

    def test_high_discrimination(self):
        p_above = _prob_3pl(theta=0.5, a=3.0, b=0.0, c=0.0)
        p_below = _prob_3pl(theta=-0.5, a=3.0, b=0.0, c=0.0)
        assert p_above - p_below > 0.6

    def test_returns_between_c_and_1(self):
        for c in [0.0, 0.1, 0.25]:
            p = _prob_3pl(theta=-5.0, a=1.0, b=0.0, c=c)
            assert p >= c - 0.01
            assert p <= 1.0


# ── _fisher_information ─────────────────────────────────────────────────────


class TestFisherInformation:
    def test_max_info_at_difficulty(self):
        info_at = _fisher_information(theta=0.0, a=1.0, b=0.0, c=0.0)
        info_away = _fisher_information(theta=3.0, a=1.0, b=0.0, c=0.0)
        assert info_at > info_away

    def test_higher_discrimination_more_info(self):
        info_low = _fisher_information(theta=0.0, a=0.5, b=0.0, c=0.0)
        info_high = _fisher_information(theta=0.0, a=2.0, b=0.0, c=0.0)
        assert info_high > info_low

    def test_non_negative(self):
        info = _fisher_information(theta=0.0, a=1.0, b=0.0, c=0.25)
        assert info >= 0.0

    def test_extreme_theta_low_info(self):
        info = _fisher_information(theta=20.0, a=1.0, b=0.0, c=0.0)
        assert info < 0.01


# ── _normal_density ─────────────────────────────────────────────────────────


class TestNormalDensity:
    def test_standard_normal_peak(self):
        d = _normal_density(0.0, mean=0.0, sd=1.0)
        assert d == pytest.approx(1.0 / math.sqrt(2 * math.pi), abs=0.001)

    def test_symmetry(self):
        d1 = _normal_density(1.0)
        d2 = _normal_density(-1.0)
        assert d1 == pytest.approx(d2, abs=1e-10)

    def test_sd_zero_guard(self):
        d = _normal_density(0.0, sd=0.0)
        assert math.isfinite(d)

    def test_negative_sd_guard(self):
        d = _normal_density(0.0, sd=-1.0)
        assert math.isfinite(d)


# ── CATState serialization ──────────────────────────────────────────────────


class TestCATStateSerialization:
    def test_round_trip(self):
        state = CATState(theta=1.5, theta_se=0.4, stopped=True, stop_reason="max_items", eap_failures=2)
        state.items.append(
            ItemRecord(
                question_id="q1",
                irt_a=1.0,
                irt_b=0.5,
                irt_c=0.2,
                response=1,
                raw_score=0.8,
                response_time_ms=5000,
                theta_at_answer=0.5,
            )
        )
        d = state.to_dict()
        restored = CATState.from_dict(d)
        assert restored.theta == 1.5
        assert restored.theta_se == 0.4
        assert restored.stopped is True
        assert restored.stop_reason == "max_items"
        assert restored.eap_failures == 2
        assert len(restored.items) == 1
        assert restored.items[0].question_id == "q1"
        assert restored.items[0].theta_at_answer == 0.5

    def test_empty_state(self):
        state = CATState()
        d = state.to_dict()
        restored = CATState.from_dict(d)
        assert restored.theta == 0.0
        assert len(restored.items) == 0

    def test_backward_compat_no_eap_failures(self):
        d = {"theta": 1.0, "theta_se": 0.5}
        restored = CATState.from_dict(d)
        assert restored.eap_failures == 0

    def test_evaluation_log_preserved(self):
        state = CATState()
        state.items.append(
            ItemRecord(
                question_id="q1",
                irt_a=1.0,
                irt_b=0.0,
                irt_c=0.0,
                response=1,
                raw_score=0.9,
                response_time_ms=5000,
                evaluation_log={"model": "gemini", "score": 0.9},
            )
        )
        d = state.to_dict()
        assert d["items"][0]["evaluation_log"]["model"] == "gemini"

    def test_evaluation_log_absent_not_serialized(self):
        state = CATState()
        state.items.append(
            ItemRecord(
                question_id="q1",
                irt_a=1.0,
                irt_b=0.0,
                irt_c=0.0,
                response=1,
                raw_score=0.5,
                response_time_ms=5000,
            )
        )
        d = state.to_dict()
        assert "evaluation_log" not in d["items"][0]


# ── select_next_item ────────────────────────────────────────────────────────


class TestSelectNextItem:
    def _questions(self):
        return [
            {"id": "q1", "irt_a": 1.0, "irt_b": -1.0, "irt_c": 0.2},
            {"id": "q2", "irt_a": 1.5, "irt_b": 0.0, "irt_c": 0.2},
            {"id": "q3", "irt_a": 1.0, "irt_b": 1.0, "irt_c": 0.2},
        ]

    def test_returns_question(self):
        state = CATState(theta=0.0)
        q = select_next_item(state, self._questions(), epsilon=0.0)
        assert q is not None
        assert q["id"] in {"q1", "q2", "q3"}

    def test_excludes_answered(self):
        state = CATState(theta=0.0)
        state.items.append(ItemRecord("q2", 1.5, 0.0, 0.2, 1, 0.8, 5000))
        q = select_next_item(state, self._questions(), epsilon=0.0)
        assert q is not None
        assert q["id"] != "q2"

    def test_no_items_left(self):
        state = CATState(theta=0.0)
        for qid in ["q1", "q2", "q3"]:
            state.items.append(ItemRecord(qid, 1.0, 0.0, 0.0, 1, 0.8, 5000))
        q = select_next_item(state, self._questions(), epsilon=0.0)
        assert q is None

    def test_mfi_prefers_matching_difficulty(self):
        state = CATState(theta=0.0)
        q = select_next_item(state, self._questions(), epsilon=0.0)
        assert q["id"] == "q2"

    def test_skips_out_of_bounds_irt(self):
        bad_questions = [
            {"id": "bad", "irt_a": 0.1, "irt_b": 0.0, "irt_c": 0.0},
            {"id": "good", "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.2},
        ]
        state = CATState(theta=0.0)
        q = select_next_item(state, bad_questions, epsilon=0.0)
        assert q["id"] == "good"


# ── submit_response ─────────────────────────────────────────────────────────


class TestSubmitResponse:
    def test_updates_theta(self):
        state = CATState(theta=0.0)
        state = submit_response(state, "q1", 1.0, 0.0, 0.2, 1.0, 5000)
        assert state.theta != 0.0
        assert len(state.items) == 1

    def test_binarizes_at_half(self):
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.49, 5000)
        assert state.items[0].response == 0
        state = submit_response(state, "q2", 1.0, 0.0, 0.0, 0.5, 5000)
        assert state.items[1].response == 1

    def test_theta_snapshot_recorded(self):
        state = CATState(theta=1.5)
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.8, 5000)
        assert state.items[0].theta_at_answer == 1.5

    def test_correct_raises_theta(self):
        state = CATState(theta=0.0)
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 1.0, 5000)
        assert state.theta > 0.0

    def test_incorrect_lowers_theta(self):
        state = CATState(theta=0.0)
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.0, 5000)
        assert state.theta < 0.0

    def test_evaluation_log_stored(self):
        state = CATState()
        log = {"model": "test", "score": 0.5}
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.5, 5000, evaluation_log=log)
        assert state.items[0].evaluation_log == log


# ── should_stop ─────────────────────────────────────────────────────────────


class TestShouldStop:
    def test_empty_state_no_stop(self):
        state = CATState()
        stop, reason = should_stop(state)
        assert stop is False

    def test_max_items_stop(self):
        state = CATState()
        for i in range(MAX_ITEMS):
            state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 0.8, 5000))
        stop, reason = should_stop(state)
        assert stop is True
        assert reason == "max_items"

    def test_se_threshold_stop(self):
        state = CATState(theta_se=0.2)
        for i in range(6):
            state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 0.8, 5000))
        stop, reason = should_stop(state)
        assert stop is True
        assert reason == "se_threshold"

    def test_se_too_few_items_no_stop(self):
        state = CATState(theta_se=0.1)
        for i in range(3):
            state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 0.8, 5000))
        stop, reason = should_stop(state, "full")
        assert stop is False

    def test_energy_mid(self):
        state = CATState()
        for i in range(12):
            state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 0.8, 5000))
        stop, reason = should_stop(state, "mid")
        assert stop is True

    def test_energy_low(self):
        state = CATState()
        for i in range(5):
            state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 0.8, 5000))
        stop, reason = should_stop(state, "low")
        assert stop is True

    def test_unknown_energy_defaults_to_full(self):
        state = CATState()
        for i in range(MAX_ITEMS):
            state.items.append(ItemRecord(f"q{i}", 1.0, 0.0, 0.0, 1, 0.8, 5000))
        stop, _ = should_stop(state, "unknown")
        assert stop is True

    def test_all_energy_profiles_exist(self):
        for level in ["full", "mid", "low"]:
            assert level in ENERGY_STOPPING
            profile = ENERGY_STOPPING[level]
            assert "max_items" in profile
            assert "se_threshold" in profile
            assert "min_before_se" in profile


# ── theta_to_score ──────────────────────────────────────────────────────────


class TestThetaToScore:
    def test_zero_theta_gives_50(self):
        assert theta_to_score(0.0) == pytest.approx(50.0, abs=0.01)

    def test_positive_theta_above_50(self):
        assert theta_to_score(2.0) > 50.0

    def test_negative_theta_below_50(self):
        assert theta_to_score(-2.0) < 50.0

    def test_extreme_positive(self):
        assert theta_to_score(500.0) == pytest.approx(100.0, abs=0.01)

    def test_extreme_negative(self):
        assert theta_to_score(-500.0) == pytest.approx(0.0, abs=0.01)

    def test_clamped_to_range(self):
        for theta in [-1000, -100, -10, 0, 10, 100, 1000]:
            score = theta_to_score(float(theta))
            assert 0.0 <= score <= 100.0

    def test_monotonic(self):
        prev = theta_to_score(-4.0)
        for t in range(-3, 5):
            curr = theta_to_score(float(t))
            assert curr >= prev
            prev = curr
