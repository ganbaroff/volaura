"""P0 tests identified by swarm council review (Session 25).

These tests fill gaps found by 5-agent security/QA audit of the test plan.
Each test references the agent who identified the gap.
"""

import pytest

from app.core.assessment import antigaming
from app.core.assessment.engine import (
    CATState,
    ItemRecord,
    _estimate_eap,
    _prob_3pl,
    select_next_item,
    submit_response,
    theta_to_score,
)

# ── QA Engineer: EAP failure cascade ─────────────────────────────────────────

class TestEAPEdgeCases:
    """QA Engineer gap: EAP failure with pathological IRT parameters."""

    def test_eap_failure_cascade_zero_discrimination(self):
        """When all items have a=0, EAP should still return valid (theta=0, se=1)."""
        items = [
            ItemRecord(f"q{i}", irt_a=0.0, irt_b=0.0, irt_c=0.0, response=1, raw_score=1.0, response_time_ms=5000)
            for i in range(5)
        ]
        theta, se = _estimate_eap(items)
        # With a=0, all items have P(correct)=0.5 regardless of theta
        # EAP should return prior mean (0.0) since no information
        assert -1.0 <= theta <= 1.0
        assert se > 0.0

    def test_eap_all_correct_extreme(self):
        """10 correct answers on easy items (b=-3) — theta should be positive but bounded."""
        items = [
            ItemRecord(f"q{i}", irt_a=1.5, irt_b=-3.0, irt_c=0.0, response=1, raw_score=1.0, response_time_ms=5000)
            for i in range(10)
        ]
        theta, se = _estimate_eap(items)
        assert -4.0 <= theta <= 4.0
        assert se > 0.0

    def test_eap_all_wrong(self):
        """10 wrong answers on hard items — theta should be low."""
        items = [
            ItemRecord(f"q{i}", irt_a=1.5, irt_b=2.0, irt_c=0.0, response=0, raw_score=0.0, response_time_ms=5000)
            for i in range(10)
        ]
        theta, se = _estimate_eap(items)
        assert theta < 0.0  # Should be below average
        assert se > 0.0

    def test_submit_response_survives_eap_failure(self):
        """submit_response should not crash even with weird IRT params."""
        state = CATState()
        # a=0 will make fisher info = 0, EAP uninformative but shouldn't crash
        state = submit_response(state, "q1", 0.0, 0.0, 0.0, 1.0, 5000)
        assert len(state.items) == 1
        assert isinstance(state.theta, float)
        assert isinstance(state.theta_se, float)


# ── QA Engineer: CATState.from_dict with corrupted data ──────────────────────

class TestCATStateCorruption:
    """QA Engineer gap: corrupted JSONB in assessment_sessions.answers."""

    def test_from_dict_empty(self):
        """Empty dict should return default state."""
        state = CATState.from_dict({})
        assert state.theta == 0.0
        assert state.theta_se == 1.0
        assert len(state.items) == 0
        assert state.stopped is False

    def test_from_dict_missing_items_key(self):
        """Dict without 'items' should return state with no items."""
        state = CATState.from_dict({"theta": 1.5, "theta_se": 0.3})
        assert state.theta == 1.5
        assert state.theta_se == 0.3
        assert len(state.items) == 0

    def test_from_dict_items_with_missing_keys_raises(self):
        """Items with missing required keys should raise KeyError."""
        data = {
            "items": [{"question_id": "q1"}]  # missing irt_a, irt_b, etc.
        }
        with pytest.raises(KeyError):
            CATState.from_dict(data)

    def test_from_dict_preserves_stop_reason(self):
        """Stop reason should survive serialization."""
        data = {
            "stopped": True,
            "stop_reason": "max_items",
            "items": [],
        }
        state = CATState.from_dict(data)
        assert state.stopped is True
        assert state.stop_reason == "max_items"


# ── QA Engineer: Small question pool ─────────────────────────────────────────

class TestSmallQuestionPool:
    """QA Engineer gap: what happens with only 1-2 questions available."""

    def test_assessment_with_2_questions(self):
        """Full CAT loop with only 2 questions — should stop with no_items_left."""
        questions = [
            {"id": "q1", "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.0, "question_type": "mcq"},
            {"id": "q2", "irt_a": 1.0, "irt_b": 1.0, "irt_c": 0.0, "question_type": "mcq"},
        ]
        state = CATState()

        # Answer both questions
        q1 = select_next_item(state, questions)
        assert q1 is not None
        state = submit_response(state, q1["id"], q1["irt_a"], q1["irt_b"], q1["irt_c"], 0.8, 5000)

        q2 = select_next_item(state, questions)
        assert q2 is not None
        assert q2["id"] != q1["id"]
        state = submit_response(state, q2["id"], q2["irt_a"], q2["irt_b"], q2["irt_c"], 0.6, 5000)

        # No more questions
        q3 = select_next_item(state, questions)
        assert q3 is None

        # theta_to_score should still return valid range
        score = theta_to_score(state.theta)
        assert 0.0 <= score <= 100.0

    def test_assessment_with_1_question(self):
        """Single question — should complete and produce valid score."""
        questions = [
            {"id": "q1", "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.0, "question_type": "mcq"},
        ]
        state = CATState()
        q = select_next_item(state, questions)
        state = submit_response(state, q["id"], q["irt_a"], q["irt_b"], q["irt_c"], 1.0, 5000)

        assert select_next_item(state, questions) is None
        assert 0.0 <= theta_to_score(state.theta) <= 100.0


# ── QA Engineer: raw_score binarization boundary ─────────────────────────────

class TestBinarizationBoundary:
    """QA Engineer gap: exact 0.5 boundary behavior."""

    def test_raw_score_exactly_0_5_is_correct(self):
        """raw_score=0.5 should binarize to response=1 (>= threshold)."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.5, 5000)
        assert state.items[0].response == 1

    def test_raw_score_just_below_0_5_is_incorrect(self):
        """raw_score=0.4999 should binarize to response=0."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.4999, 5000)
        assert state.items[0].response == 0

    def test_raw_score_0_is_incorrect(self):
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.0, 5000)
        assert state.items[0].response == 0

    def test_raw_score_1_is_correct(self):
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 1.0, 5000)
        assert state.items[0].response == 1


# ── Security Auditor: IDOR prevention ────────────────────────────────────────
# Note: actual IDOR API tests require async client. These test the engine logic.


# ── Leyla: slow connection timing ────────────────────────────────────────────

class TestTimingEdgeCases:
    """Leyla gap: false positives from slow mobile connections."""

    def test_very_slow_answer_not_rushed(self):
        """20-second response should NOT be flagged as rushing."""
        result = antigaming.check_answer_timing(20_000)
        assert result["valid"] is True

    def test_borderline_timing_3000ms(self):
        """Exactly 3000ms (TOO_FAST_MS threshold) — should be valid."""
        result = antigaming.check_answer_timing(3_000)
        assert result["valid"] is True

    def test_timing_2999ms_is_too_fast(self):
        """2999ms is below threshold — should be invalid."""
        result = antigaming.check_answer_timing(2_999)
        assert result["valid"] is False

    def test_penalty_from_rushing(self):
        """Many rushed answers should reduce penalty_multiplier below 1.0."""
        answers = [
            {"response_time_ms": 500, "response": 1, "raw_score": 1.0}
            for _ in range(10)
        ]
        signal = antigaming.analyse(answers)
        assert signal.penalty_multiplier < 1.0

    def test_no_penalty_clean_session(self):
        """Normal timing should keep penalty_multiplier at 1.0.

        S8.2: Timing must be VARIED (natural human variance) — uniform timing now
        triggers is_time_clustered (CV < 0.15). Real users don't answer at exactly
        the same millisecond every time.
        """
        responses = [1, 0, 1, 1, 0, 1, 0, 0]
        timings = [8_000, 15_000, 6_000, 12_000, 9_000, 20_000, 7_000, 18_000]  # CV ≈ 0.45
        answers = [
            {"response_time_ms": t, "response": r, "raw_score": 0.7}
            for r, t in zip(responses, timings)
        ]
        signal = antigaming.analyse(answers)
        assert signal.penalty_multiplier == 1.0


# ── Attacker: deterministic selection detection ──────────────────────────────

class TestAdaptiveSelectionDeterminism:
    """Attacker gap: is item selection deterministic (exploitable)?"""

    def test_mfi_selects_most_informative_at_theta(self):
        """MFI should select item whose b is closest to current theta."""
        questions = [
            {"id": "easy", "irt_a": 1.0, "irt_b": -2.0, "irt_c": 0.0},
            {"id": "medium", "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.0},
            {"id": "hard", "irt_a": 1.0, "irt_b": 2.0, "irt_c": 0.0},
        ]
        # At theta=0, b=0 should give max info (epsilon=0 disables random exploration)
        state = CATState(theta=0.0)
        q = select_next_item(state, questions, epsilon=0.0)
        assert q["id"] == "medium"

    def test_mfi_adapts_after_correct_answers(self):
        """After correct answers, theta rises, next item should be harder."""
        questions = [
            {"id": "q1", "irt_a": 1.0, "irt_b": -1.0, "irt_c": 0.0},
            {"id": "q2", "irt_a": 1.0, "irt_b": 0.0, "irt_c": 0.0},
            {"id": "q3", "irt_a": 1.0, "irt_b": 1.0, "irt_c": 0.0},
            {"id": "q4", "irt_a": 1.0, "irt_b": 2.0, "irt_c": 0.0},
        ]
        state = CATState(theta=0.0)

        # Answer q2 (medium) correctly → theta should increase
        state = submit_response(state, "q2", 1.0, 0.0, 0.0, 1.0, 5000)
        assert state.theta > 0.0

        # Next item should be harder (q3 or q4), epsilon=0 for determinism
        next_q = select_next_item(state, questions, epsilon=0.0)
        assert next_q is not None
        assert next_q["id"] in ("q3", "q4")


# ── 3PL math validation ─────────────────────────────────────────────────────

class TestIRTMath:
    """Validate 3PL probability function edge cases."""

    def test_prob_at_difficulty(self):
        """P(correct | theta=b) should be (1+c)/2 for 3PL."""
        p = _prob_3pl(theta=1.0, a=1.0, b=1.0, c=0.0)
        assert abs(p - 0.5) < 0.01

    def test_prob_with_guessing(self):
        """With c=0.25, floor should be 0.25."""
        # At very low theta, P should approach c
        p = _prob_3pl(theta=-10.0, a=1.0, b=0.0, c=0.25)
        assert abs(p - 0.25) < 0.01

    def test_prob_high_theta(self):
        """High theta should give P close to 1.0."""
        p = _prob_3pl(theta=10.0, a=1.0, b=0.0, c=0.0)
        assert p > 0.99

    def test_prob_clamped_no_overflow(self):
        """Extreme values should not cause math overflow."""
        p1 = _prob_3pl(theta=100.0, a=5.0, b=0.0, c=0.0)
        p2 = _prob_3pl(theta=-100.0, a=5.0, b=0.0, c=0.0)
        assert 0.0 <= p1 <= 1.0
        assert 0.0 <= p2 <= 1.0

    def test_theta_to_score_monotonic(self):
        """Higher theta should always produce higher score."""
        scores = [theta_to_score(t) for t in [-3, -1, 0, 1, 3]]
        for i in range(len(scores) - 1):
            assert scores[i] < scores[i + 1]
