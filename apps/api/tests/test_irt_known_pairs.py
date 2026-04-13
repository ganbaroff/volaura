"""IRT known-value unit tests for the CAT engine.

Each test validates a specific mathematical property against hand-calculated
reference values from IRT literature (Lord 1980, Baker & Kim 2004).

No external IRT library is used — values are derived from the closed-form
3PL equation:

    P(correct | theta) = c + (1 - c) / (1 + exp(-a * (theta - b)))

Fisher information for a 3PL item:

    I(theta) = a^2 * (P - c)^2 * Q / ((1 - c)^2 * P)

theta -> score mapping (logistic centred at 0 -> 50):

    score = 100 * sigmoid(theta) = 100 / (1 + exp(-theta))
"""

import math

from app.core.assessment.engine import (
    MAX_ITEMS,
    MIN_ITEMS_BEFORE_SE_STOP,
    SE_THRESHOLD,
    CATState,
    ItemRecord,
    _estimate_eap,
    _fisher_information,
    _prob_3pl,
    select_next_item,
    should_stop,
    submit_response,
    theta_to_score,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_item(
    question_id: str,
    a: float,
    b: float,
    c: float,
    response: int,
    response_time_ms: int = 8000,
) -> ItemRecord:
    """Convenience constructor for ItemRecord used in tests."""
    return ItemRecord(
        question_id=question_id,
        irt_a=a,
        irt_b=b,
        irt_c=c,
        response=response,
        raw_score=float(response),
        response_time_ms=response_time_ms,
    )


def _make_question(q_id: str, a: float, b: float, c: float) -> dict:
    return {
        "id": q_id,
        "irt_a": a,
        "irt_b": b,
        "irt_c": c,
        "question_type": "mcq",
        "question_en": f"Question {q_id}",
        "question_az": f"Sual {q_id}",
        "options": None,
        "competency_id": "comp1",
    }


# ── Section 1: 3PL probability — known pairs ──────────────────────────────────


class TestProb3PLKnownValues:
    """Validate P(correct | theta) against hand-calculated reference values.

    All tolerances use rel_tol=0 + abs_tol=1e-4 to match 4-decimal-place
    IRT textbook rounding conventions.
    """

    def test_symmetry_point_no_guessing(self):
        """a=1, b=0, c=0, theta=0 → P=0.5 by symmetry of the logistic curve."""
        # exp_val = 1.0 * (0.0 - 0.0) = 0.0
        # P = 0 + 1 / (1 + exp(0)) = 1 / 2 = 0.5
        p = _prob_3pl(theta=0.0, a=1.0, b=0.0, c=0.0)
        assert math.isclose(p, 0.5, abs_tol=1e-9), (
            f"Expected exactly 0.5 by logistic symmetry, got {p}"
        )

    def test_guessing_raises_probability_floor(self):
        """a=1, b=0, c=0.25, theta=0 → P=0.625 (guessing shifts floor to 0.25)."""
        # exp_val = 1.0 * (0.0 - 0.0) = 0.0
        # P = 0.25 + 0.75 / (1 + 1) = 0.25 + 0.375 = 0.625
        p = _prob_3pl(theta=0.0, a=1.0, b=0.0, c=0.25)
        assert math.isclose(p, 0.625, abs_tol=1e-9), (
            f"Expected 0.625, got {p}"
        )

    def test_high_ability_hard_item_no_guessing(self):
        """a=1.5, b=1.0, c=0.0, theta=2.0 → P≈0.8176."""
        # exp_val = 1.5 * (2.0 - 1.0) = 1.5
        # P = 1 / (1 + exp(-1.5)) ≈ 1 / (1 + 0.22313) ≈ 0.81757
        p = _prob_3pl(theta=2.0, a=1.5, b=1.0, c=0.0)
        assert math.isclose(p, 0.81757, abs_tol=1e-4), (
            f"Expected ≈0.8176, got {p}"
        )

    def test_easy_item_high_ability_no_guessing(self):
        """a=1.0, b=-1.0, c=0.0, theta=1.0 → P≈0.8808."""
        # exp_val = 1.0 * (1.0 - (-1.0)) = 2.0
        # P = 1 / (1 + exp(-2.0)) ≈ 1 / (1 + 0.13534) ≈ 0.88080
        p = _prob_3pl(theta=1.0, a=1.0, b=-1.0, c=0.0)
        assert math.isclose(p, 0.88080, abs_tol=1e-4), (
            f"Expected ≈0.8808, got {p}"
        )

    def test_at_difficulty_with_guessing(self):
        """a=2.0, b=0.5, c=0.2, theta=0.5 → P=0.6 (theta==b, c shifts midpoint)."""
        # exp_val = 2.0 * (0.5 - 0.5) = 0.0
        # P = 0.2 + 0.8 / (1 + 1) = 0.2 + 0.4 = 0.6
        p = _prob_3pl(theta=0.5, a=2.0, b=0.5, c=0.2)
        assert math.isclose(p, 0.6, abs_tol=1e-9), (
            f"Expected exactly 0.6, got {p}"
        )

    def test_very_low_theta_near_guessing_floor(self):
        """a=1.0, b=0.0, c=0.3, theta=-5.0 → P approaches c=0.3 from above."""
        # At theta → -∞: P → c
        p = _prob_3pl(theta=-5.0, a=1.0, b=0.0, c=0.3)
        assert p > 0.3, "P must be above guessing floor"
        assert math.isclose(p, 0.3, abs_tol=0.01), (
            f"At theta=-5, P should be near c=0.3, got {p}"
        )

    def test_very_high_theta_approaches_one(self):
        """a=1.0, b=0.0, c=0.0, theta=5.0 → P approaches 1.0."""
        p = _prob_3pl(theta=5.0, a=1.0, b=0.0, c=0.0)
        assert math.isclose(p, 1.0, abs_tol=0.01), (
            f"At theta=5, P should be near 1.0, got {p}"
        )

    def test_probability_always_in_unit_interval(self):
        """P(correct) must always be in [0, 1] across extreme parameter values."""
        test_cases = [
            (-10.0, 3.0, 2.0, 0.5),
            (10.0, 0.5, -3.0, 0.0),
            (0.0, 5.0, 0.0, 0.3),
            (-20.0, 0.1, 5.0, 0.0),
        ]
        for theta, a, b, c in test_cases:
            p = _prob_3pl(theta=theta, a=a, b=b, c=c)
            assert 0.0 <= p <= 1.0, (
                f"P={p} out of [0,1] for theta={theta}, a={a}, b={b}, c={c}"
            )

    def test_monotone_increasing_in_theta(self):
        """P must be strictly increasing in theta for fixed a, b, c (a > 0)."""
        a, b, c = 1.5, 0.5, 0.1
        thetas = [-3.0, -1.5, 0.0, 1.5, 3.0]
        probs = [_prob_3pl(t, a, b, c) for t in thetas]
        for i in range(len(probs) - 1):
            assert probs[i] < probs[i + 1], (
                f"P not monotone: P(theta={thetas[i]})={probs[i]} "
                f">= P(theta={thetas[i+1]})={probs[i+1]}"
            )


# ── Section 2: theta_to_score — known mapping values ─────────────────────────


class TestThetaToScore:
    """Validate the logistic theta → [0, 100] mapping.

    Formula: score = 100 / (1 + exp(-theta)), clamped to [0, 100].
    """

    def test_theta_zero_maps_to_exactly_50(self):
        """theta=0 → score=50 by symmetry of sigmoid."""
        score = theta_to_score(0.0)
        assert math.isclose(score, 50.0, abs_tol=1e-9), (
            f"Expected exactly 50.0, got {score}"
        )

    def test_theta_negative_3_near_zero(self):
        """theta=-3 → score ≈ 4.74 (significantly below 50)."""
        # 100 / (1 + exp(3)) = 100 / (1 + 20.086) ≈ 4.74
        score = theta_to_score(-3.0)
        expected = 100.0 / (1.0 + math.exp(3.0))
        assert math.isclose(score, expected, abs_tol=1e-6), (
            f"Expected ≈{expected:.4f}, got {score}"
        )
        assert score < 10.0, f"theta=-3 should score below 10, got {score}"

    def test_theta_positive_3_near_hundred(self):
        """theta=3 → score ≈ 95.26 (significantly above 50)."""
        # 100 / (1 + exp(-3)) = 100 / (1 + 0.04979) ≈ 95.26
        score = theta_to_score(3.0)
        expected = 100.0 / (1.0 + math.exp(-3.0))
        assert math.isclose(score, expected, abs_tol=1e-6), (
            f"Expected ≈{expected:.4f}, got {score}"
        )
        assert score > 90.0, f"theta=3 should score above 90, got {score}"

    def test_theta_minus_4_near_zero_bound(self):
        """theta=-4 → score ≈ 1.80 (near but not at 0)."""
        score = theta_to_score(-4.0)
        assert 0.0 < score < 5.0, (
            f"theta=-4 should be near 0, got {score}"
        )

    def test_theta_plus_4_near_hundred_bound(self):
        """theta=4 → score ≈ 98.20 (near but not at 100)."""
        score = theta_to_score(4.0)
        assert 95.0 < score <= 100.0, (
            f"theta=4 should be near 100, got {score}"
        )

    def test_clamp_extreme_positive(self):
        """Very large positive theta must not exceed 100."""
        assert theta_to_score(1000.0) == 100.0

    def test_clamp_extreme_negative(self):
        """Very large negative theta must not go below 0 and must not raise."""
        # The engine clamps theta at -500 internally to prevent OverflowError.
        # sigmoid(-500) ≈ 7e-216, which is effectively 0 but > 0 in floating point.
        score = theta_to_score(-1000.0)
        assert score >= 0.0
        assert score < 1e-200, f"Expected score near 0 for theta=-1000, got {score}"

    def test_score_increases_with_theta(self):
        """score(theta) must be strictly monotone increasing."""
        thetas = [-4.0, -2.0, 0.0, 2.0, 4.0]
        scores = [theta_to_score(t) for t in thetas]
        for i in range(len(scores) - 1):
            assert scores[i] < scores[i + 1], (
                f"score not monotone: score({thetas[i]})={scores[i]} "
                f">= score({thetas[i+1]})={scores[i+1]}"
            )

    def test_theta_1_known_value(self):
        """theta=1.0 → score ≈ 73.11."""
        # 100 / (1 + exp(-1)) = 100 / (1 + 0.36788) ≈ 73.106
        score = theta_to_score(1.0)
        expected = 100.0 / (1.0 + math.exp(-1.0))
        assert math.isclose(score, expected, abs_tol=1e-6)

    def test_theta_minus_1_known_value(self):
        """theta=-1.0 → score ≈ 26.89 (symmetric with theta=1 around 50)."""
        score = theta_to_score(-1.0)
        score_pos = theta_to_score(1.0)
        # Symmetry: score(-theta) = 100 - score(theta)
        assert math.isclose(score + score_pos, 100.0, abs_tol=1e-6), (
            f"Symmetry broken: score(-1)={score}, score(1)={score_pos}"
        )


# ── Section 3: EAP estimation — directional tests ─────────────────────────────


class TestEAPEstimation:
    """Validate EAP ability estimation.

    We test directional properties (sign and relative magnitude) rather than
    exact numerical values, because EAP depends on the quadrature grid
    resolution (49 points, [-4, 4]) and the N(0,1) prior.
    """

    def test_all_correct_easy_items_positive_theta(self):
        """All correct on easy items (b=-1) → theta should be moderate positive."""
        items = [
            _make_item(f"q{i}", a=1.0, b=-1.0, c=0.0, response=1)
            for i in range(5)
        ]
        theta_hat, se = _estimate_eap(items)
        assert theta_hat > 0.0, (
            f"All correct on easy items should give positive theta, got {theta_hat}"
        )
        assert se > 0.0, "SE must be positive"

    def test_all_wrong_negative_theta(self):
        """All wrong → theta should be negative (prior drags toward -∞)."""
        items = [
            _make_item(f"q{i}", a=1.0, b=0.0, c=0.0, response=0)
            for i in range(5)
        ]
        theta_hat, se = _estimate_eap(items)
        assert theta_hat < 0.0, (
            f"All wrong should give negative theta, got {theta_hat}"
        )

    def test_mixed_pattern_theta_near_zero(self):
        """Balanced correct/wrong on items near b=0 → theta near prior mean (0)."""
        # 3 correct, 3 wrong on items with b≈0 — posterior should stay near prior
        items = []
        for i in range(3):
            items.append(_make_item(f"c{i}", a=1.0, b=0.0, c=0.0, response=1))
        for i in range(3):
            items.append(_make_item(f"w{i}", a=1.0, b=0.0, c=0.0, response=0))
        theta_hat, se = _estimate_eap(items)
        assert abs(theta_hat) < 1.0, (
            f"Mixed pattern should give theta near 0, got {theta_hat}"
        )

    def test_se_decreases_with_more_items(self):
        """SE should decrease as we add more discriminating items."""
        items_3 = [
            _make_item(f"q{i}", a=1.5, b=0.0, c=0.0, response=1)
            for i in range(3)
        ]
        items_10 = [
            _make_item(f"q{i}", a=1.5, b=0.0, c=0.0, response=1)
            for i in range(10)
        ]
        _, se_3 = _estimate_eap(items_3)
        _, se_10 = _estimate_eap(items_10)
        assert se_10 < se_3, (
            f"SE with 10 items ({se_10}) should be < SE with 3 items ({se_3})"
        )

    def test_all_correct_hard_items_high_theta(self):
        """All correct on hard items (b=2.0) → theta should be substantially > 0."""
        items = [
            _make_item(f"q{i}", a=1.5, b=2.0, c=0.0, response=1)
            for i in range(7)
        ]
        theta_hat, _ = _estimate_eap(items)
        assert theta_hat > 1.0, (
            f"All correct on hard items (b=2) should give theta > 1.0, got {theta_hat}"
        )

    def test_all_wrong_easy_items_very_negative_theta(self):
        """All wrong on easy items (b=-2.0) → theta should be substantially < 0."""
        items = [
            _make_item(f"q{i}", a=1.5, b=-2.0, c=0.0, response=0)
            for i in range(7)
        ]
        theta_hat, _ = _estimate_eap(items)
        assert theta_hat < -1.0, (
            f"All wrong on easy items (b=-2) should give theta < -1.0, got {theta_hat}"
        )

    def test_se_bounds(self):
        """SE must always be non-negative and bounded by prior width."""
        items = [_make_item("q0", a=1.0, b=0.0, c=0.0, response=1)]
        _, se = _estimate_eap(items)
        assert 0.0 <= se <= 4.0, f"SE={se} out of expected range [0, 4]"

    def test_high_discrimination_items_lower_se(self):
        """High-discrimination items (a=3.0) should give lower SE than low-a items."""
        items_low_a = [
            _make_item(f"q{i}", a=0.3, b=0.0, c=0.0, response=1)
            for i in range(5)
        ]
        items_high_a = [
            _make_item(f"q{i}", a=3.0, b=0.0, c=0.0, response=1)
            for i in range(5)
        ]
        _, se_low = _estimate_eap(items_low_a)
        _, se_high = _estimate_eap(items_high_a)
        assert se_high < se_low, (
            f"High-a items should give lower SE ({se_high}) than low-a ({se_low})"
        )


# ── Section 4: Fisher Information / item selection (MFI) ──────────────────────


class TestFisherInformationAndMFI:
    """Validate Fisher information values and Maximum Fisher Information selection."""

    def test_fisher_information_peak_at_b_for_2pl(self):
        """For 2PL (c=0), Fisher information is maximised when theta == b."""
        a, b, c = 1.5, 1.0, 0.0
        # Test symmetrically around b
        thetas = [b - 1.5, b - 0.5, b, b + 0.5, b + 1.5]
        infos = [_fisher_information(t, a, b, c) for t in thetas]
        peak_idx = infos.index(max(infos))
        assert peak_idx == 2, (
            f"Maximum information should be at theta=b={b}, "
            f"but peak was at theta={thetas[peak_idx]}"
        )

    def test_fisher_information_non_negative(self):
        """Fisher information must always be >= 0."""
        test_cases = [
            (0.0, 1.0, 0.0, 0.0),
            (2.0, 1.5, 1.0, 0.25),
            (-3.0, 0.5, -2.0, 0.0),
            (0.0, 2.0, 0.0, 0.3),
        ]
        for theta, a, b, c in test_cases:
            info = _fisher_information(theta, a, b, c)
            assert info >= 0.0, (
                f"Fisher info={info} negative for theta={theta}, a={a}, b={b}, c={c}"
            )

    def test_fisher_information_higher_discrimination_more_info(self):
        """Higher discrimination (a) yields higher Fisher information at theta=b."""
        # At theta=b, 2PL gives I = a^2/4
        b, c = 0.0, 0.0
        theta = 0.0  # == b
        info_low = _fisher_information(theta, a=0.5, b=b, c=c)
        info_high = _fisher_information(theta, a=2.0, b=b, c=c)
        assert info_high > info_low, (
            f"Higher a should give more information: {info_high} vs {info_low}"
        )

    def test_fisher_information_known_value_2pl(self):
        """For 2PL at theta=b: I(theta) = a^2 * P * Q where P=Q=0.5, so I = a^2/4."""
        # a=2.0, b=0.0, c=0.0, theta=0.0
        # P = 0.5, Q = 0.5
        # I = (2^2 * (0.5-0)^2 * 0.5) / ((1-0)^2 * 0.5) = (4 * 0.25 * 0.5) / 0.5 = 1.0
        info = _fisher_information(theta=0.0, a=2.0, b=0.0, c=0.0)
        assert math.isclose(info, 1.0, abs_tol=1e-9), (
            f"Expected I=1.0 for a=2 at theta=b, got {info}"
        )

    def test_fisher_information_a1_at_b_equals_0_25(self):
        """For 2PL with a=1.0 at theta=b: I = 1^2 / 4 = 0.25."""
        info = _fisher_information(theta=0.0, a=1.0, b=0.0, c=0.0)
        assert math.isclose(info, 0.25, abs_tol=1e-9), (
            f"Expected I=0.25 for a=1 at theta=b, got {info}"
        )

    def test_mfi_selects_item_closest_to_theta(self):
        """MFI should prefer items whose b is closest to current theta."""
        # Create 5 items at different difficulty levels
        # With theta=0.0, the item at b=0.0 should have maximum information
        questions = [
            _make_question("q_neg2", a=1.5, b=-2.0, c=0.0),
            _make_question("q_neg1", a=1.5, b=-1.0, c=0.0),
            _make_question("q_zero", a=1.5, b=0.0, c=0.0),   # ← should win
            _make_question("q_pos1", a=1.5, b=1.0, c=0.0),
            _make_question("q_pos2", a=1.5, b=2.0, c=0.0),
        ]
        state = CATState(theta=0.0)
        # epsilon=0 disables ε-greedy — tests deterministic MFI, not exposure-control randomness
        selected = select_next_item(state, questions, epsilon=0)
        assert selected is not None
        assert selected["id"] == "q_zero", (
            f"At theta=0, MFI should select b=0 item, selected b={selected['irt_b']}"
        )

    def test_mfi_shifts_selection_with_theta(self):
        """After ability update, MFI should select items matching new theta."""
        questions = [
            _make_question("q_neg2", a=1.5, b=-2.0, c=0.0),
            _make_question("q_zero", a=1.5, b=0.0, c=0.0),
            _make_question("q_pos2", a=1.5, b=2.0, c=0.0),   # ← should win at theta=2
        ]
        state = CATState(theta=2.0)
        # epsilon=0 disables ε-greedy — tests deterministic MFI, not exposure-control randomness
        selected = select_next_item(state, questions, epsilon=0)
        assert selected is not None
        assert selected["id"] == "q_pos2", (
            f"At theta=2, MFI should select b=2 item, selected b={selected['irt_b']}"
        )

    def test_mfi_skips_already_answered(self):
        """MFI must not re-select an item that was already administered."""
        questions = [
            _make_question("q_zero", a=2.0, b=0.0, c=0.0),  # best item at theta=0
            _make_question("q_pos1", a=1.0, b=1.0, c=0.0),
        ]
        state = CATState(theta=0.0)
        state.items.append(_make_item("q_zero", a=2.0, b=0.0, c=0.0, response=1))
        # epsilon=0 disables ε-greedy — tests deterministic MFI
        selected = select_next_item(state, questions, epsilon=0)
        assert selected is not None
        assert selected["id"] == "q_pos1", (
            "MFI should skip answered item and select next-best"
        )

    def test_mfi_returns_none_when_pool_exhausted(self):
        """Returns None when all items in the pool have been answered."""
        questions = [_make_question("q1", a=1.0, b=0.0, c=0.0)]
        state = CATState()
        state.items.append(_make_item("q1", a=1.0, b=0.0, c=0.0, response=1))
        result = select_next_item(state, questions)
        assert result is None


# ── Section 5: Stopping criteria ──────────────────────────────────────────────


class TestStoppingCriteria:
    """Validate CAT session termination logic."""

    def test_stops_at_max_items(self):
        """Session must stop when MAX_ITEMS responses have been recorded."""
        state = CATState()
        for i in range(MAX_ITEMS):
            state.items.append(_make_item(f"q{i}", a=1.0, b=0.0, c=0.0, response=1))
        stopped, reason = should_stop(state)
        assert stopped is True
        assert reason == "max_items"

    def test_stops_at_se_threshold(self):
        """Session must stop when SE <= SE_THRESHOLD after MIN_ITEMS_BEFORE_SE_STOP."""
        state = CATState(theta=0.5, theta_se=SE_THRESHOLD - 0.01)
        for i in range(MIN_ITEMS_BEFORE_SE_STOP):
            state.items.append(_make_item(f"q{i}", a=1.0, b=0.0, c=0.0, response=1))
        stopped, reason = should_stop(state)
        assert stopped is True
        assert reason == "se_threshold"

    def test_does_not_stop_se_threshold_too_few_items(self):
        """SE threshold should NOT trigger before MIN_ITEMS_BEFORE_SE_STOP items."""
        state = CATState(theta=0.0, theta_se=0.01)  # very low SE
        for i in range(MIN_ITEMS_BEFORE_SE_STOP - 1):
            state.items.append(_make_item(f"q{i}", a=1.0, b=0.0, c=0.0, response=1))
        stopped, _ = should_stop(state)
        assert stopped is False, (
            f"Should not stop before {MIN_ITEMS_BEFORE_SE_STOP} items even with low SE"
        )

    def test_does_not_stop_high_se(self):
        """Session should NOT stop when SE is above threshold."""
        state = CATState(theta=0.0, theta_se=SE_THRESHOLD + 0.1)
        for i in range(MIN_ITEMS_BEFORE_SE_STOP + 2):
            state.items.append(_make_item(f"q{i}", a=1.0, b=0.0, c=0.0, response=1))
        stopped, _ = should_stop(state)
        assert stopped is False

    def test_exactly_at_se_threshold_stops(self):
        """SE exactly equal to SE_THRESHOLD should trigger the stop."""
        state = CATState(theta=0.0, theta_se=SE_THRESHOLD)
        for i in range(MIN_ITEMS_BEFORE_SE_STOP):
            state.items.append(_make_item(f"q{i}", a=1.0, b=0.0, c=0.0, response=1))
        stopped, reason = should_stop(state)
        assert stopped is True
        assert reason == "se_threshold"

    def test_does_not_stop_with_zero_items(self):
        """Empty state should never trigger any stop condition."""
        state = CATState(theta=0.0, theta_se=0.0)
        stopped, _ = should_stop(state)
        assert stopped is False

    def test_submit_response_integration_stops_after_max(self):
        """End-to-end: submitting MAX_ITEMS responses should satisfy stop condition."""
        state = CATState()
        for i in range(MAX_ITEMS):
            state = submit_response(
                state,
                question_id=f"q{i}",
                irt_a=1.0,
                irt_b=float(i % 5 - 2),
                irt_c=0.0,
                raw_score=1.0 if i % 2 == 0 else 0.0,
                response_time_ms=8000,
            )
        stopped, reason = should_stop(state)
        assert stopped is True
        assert reason == "max_items"


# ── Section 6: submit_response — binarisation and theta update ─────────────────


class TestSubmitResponse:
    """Validate response recording and theta update via submit_response."""

    def test_binarise_above_threshold(self):
        """raw_score >= 0.5 → binary response = 1."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.5, 5000)
        assert state.items[0].response == 1

    def test_binarise_below_threshold(self):
        """raw_score < 0.5 → binary response = 0."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.49, 5000)
        assert state.items[0].response == 0

    def test_binarise_exactly_zero(self):
        """raw_score = 0.0 → binary response = 0."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.0, 5000)
        assert state.items[0].response == 0

    def test_binarise_exactly_one(self):
        """raw_score = 1.0 → binary response = 1."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 1.0, 5000)
        assert state.items[0].response == 1

    def test_correct_answers_on_hard_items_increase_theta(self):
        """Correct answers on items harder than ability → theta must increase."""
        state = CATState(theta=0.0)
        for i in range(5):
            state = submit_response(state, f"q{i}", 1.0, 2.0, 0.0, 1.0, 8000)
        assert state.theta > 0.0, (
            f"5 correct answers on hard items (b=2) should raise theta above 0, "
            f"got {state.theta}"
        )

    def test_wrong_answers_decrease_theta(self):
        """Wrong answers on medium items → theta must decrease from default 0."""
        state = CATState(theta=0.0)
        for i in range(5):
            state = submit_response(state, f"q{i}", 1.0, 0.0, 0.0, 0.0, 8000)
        assert state.theta < 0.0, (
            f"5 wrong answers should lower theta below 0, got {state.theta}"
        )

    def test_raw_score_preserved(self):
        """raw_score should be stored as-is (not binarised in the record)."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 0.73, 5000)
        assert math.isclose(state.items[0].raw_score, 0.73, abs_tol=1e-9)

    def test_response_time_preserved(self):
        """response_time_ms should be stored exactly."""
        state = CATState()
        state = submit_response(state, "q1", 1.0, 0.0, 0.0, 1.0, 12345)
        assert state.items[0].response_time_ms == 12345

    def test_theta_se_is_updated(self):
        """After submission, theta_se must be updated (not left at 1.0 default)."""
        state = CATState()
        state = submit_response(state, "q1", 2.0, 0.0, 0.0, 1.0, 5000)
        # After 1 highly discriminating item, SE should be < 1.0 (prior width)
        assert state.theta_se < 1.0, (
            f"SE should be updated after submission, got {state.theta_se}"
        )


# ── Section 7: IRT boundary / edge cases ──────────────────────────────────────


class TestIRTEdgeCases:
    """Validate numerical stability and boundary conditions."""

    def test_prob_3pl_overflow_prevention_high_theta(self):
        """Engine must not raise OverflowError for extreme theta values."""
        # exp_val clamped to [-20, 20]
        p = _prob_3pl(theta=1000.0, a=5.0, b=0.0, c=0.0)
        assert 0.0 <= p <= 1.0

    def test_prob_3pl_overflow_prevention_low_theta(self):
        """Engine must not raise OverflowError for extreme negative theta."""
        p = _prob_3pl(theta=-1000.0, a=5.0, b=0.0, c=0.0)
        assert 0.0 <= p <= 1.0

    def test_fisher_info_zero_at_extreme_theta(self):
        """Fisher information should approach 0 at extreme theta values."""
        # At theta >> b, P≈1, Q≈0, so info → 0
        info_far = _fisher_information(theta=20.0, a=1.0, b=0.0, c=0.0)
        info_near = _fisher_information(theta=0.0, a=1.0, b=0.0, c=0.0)
        assert info_far < info_near, (
            f"Information far from b should be lower: {info_far} vs {info_near}"
        )

    def test_eap_empty_items_returns_prior(self):
        """With no items, EAP should return prior mean (0.0) and prior SE (1.0)."""
        theta_hat, se = _estimate_eap([])
        assert math.isclose(theta_hat, 0.0, abs_tol=1e-6), (
            f"EAP with no items should return prior mean 0.0, got {theta_hat}"
        )
        assert math.isclose(se, 1.0, abs_tol=0.1), (
            f"EAP with no items should return near-prior SE (~1.0), got {se}"
        )

    def test_prob_3pl_c_equals_1_always_correct(self):
        """c=1.0 means P=1 regardless of theta (degenerate but must not crash)."""
        p = _prob_3pl(theta=-5.0, a=1.0, b=0.0, c=1.0)
        assert math.isclose(p, 1.0, abs_tol=1e-9), (
            f"c=1.0 should give P=1 always, got {p}"
        )

    def test_fisher_info_c_equals_1_is_zero(self):
        """Fisher information is 0 when c=1 (P always 1, Q always 0)."""
        info = _fisher_information(theta=0.0, a=1.0, b=0.0, c=1.0)
        assert info == 0.0, f"Fisher info with c=1 should be 0, got {info}"
