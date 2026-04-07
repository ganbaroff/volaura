"""IRT/CAT adaptive assessment engine.

Pure-Python implementation (no external IRT library dependency):
- 3PL model: P(correct | theta) = c + (1-c) / (1 + exp(-a*(theta-b)))
- EAP (Expected A Posteriori) ability estimation with normal prior
- Maximum Fisher Information item selection
- Stopping: SE <= 0.3 OR 20 questions max

Math references:
- EAP: Lord (1980), Baker & Kim (2004)
- MFI: van der Linden (1998)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Any


# Stopping criteria constants (Full energy defaults)
MAX_ITEMS = 20
SE_THRESHOLD = 0.3
MIN_ITEMS_BEFORE_SE_STOP = 5  # Need at least 3 answers before SE stop

# Constitution Law 2: Energy Adaptation — per-energy stopping profiles
# Full: full precision, normal cognitive load
# Mid:  shorter, acceptable precision, entrance-only animations
# Low:  minimal, hard cap at 5 items, lax SE threshold
ENERGY_STOPPING: dict[str, dict[str, float]] = {
    "full": {"max_items": 20, "se_threshold": 0.3, "min_before_se": 5},
    "mid":  {"max_items": 12, "se_threshold": 0.4, "min_before_se": 4},
    "low":  {"max_items": 5,  "se_threshold": 0.5, "min_before_se": 3},
}
ABILITY_SCALE_MIN = -4.0
ABILITY_SCALE_MAX = 4.0

# EAP quadrature settings
NUM_QUADRATURE_POINTS = 49  # Odd number for symmetric grid


@dataclass
class ItemRecord:
    """One administered item with the volunteer's response."""
    question_id: str
    irt_a: float
    irt_b: float
    irt_c: float
    response: int  # 0 or 1 (for open-ended: binarised via BARS threshold)
    raw_score: float  # 0.0-1.0 continuous score (BARS output)
    response_time_ms: int
    theta_at_answer: float = 0.0   # RT-IRT: theta snapshot BEFORE this item was administered
    evaluation_log: dict | None = None  # Phase 2: BARS per-concept breakdown


@dataclass
class CATState:
    """Full mutable state of an in-progress CAT session.

    This is serialised/deserialised from the Supabase `assessment_sessions.answers`
    JSONB column so we can resume across HTTP requests.
    """
    theta: float = 0.0          # current ability estimate (logit scale)
    theta_se: float = 1.0       # standard error of estimate
    items: list[ItemRecord] = field(default_factory=list)
    stopped: bool = False
    stop_reason: str | None = None  # "se_threshold" | "max_items" | "no_items_left" | "eap_degraded"
    eap_failures: int = 0       # S8.1: count of EAP estimation failures across requests
    prior_mean: float = 0.0   # stored for EAP re-estimation across session
    prior_sd: float = 1.0     # stored for EAP re-estimation across session

    # --- serialisation helpers ----------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "theta": self.theta,
            "theta_se": self.theta_se,
            "stopped": self.stopped,
            "stop_reason": self.stop_reason,
            "eap_failures": self.eap_failures,
            "prior_mean": self.prior_mean,
            "prior_sd": self.prior_sd,
            "items": [
                {
                    "question_id": r.question_id,
                    "irt_a": r.irt_a,
                    "irt_b": r.irt_b,
                    "irt_c": r.irt_c,
                    "response": r.response,
                    "raw_score": r.raw_score,
                    "response_time_ms": r.response_time_ms,
                    "theta_at_answer": r.theta_at_answer,
                    **({"evaluation_log": r.evaluation_log} if r.evaluation_log else {}),
                }
                for r in self.items
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CATState":
        items = [
            ItemRecord(
                question_id=r["question_id"],
                irt_a=r["irt_a"],
                irt_b=r["irt_b"],
                irt_c=r["irt_c"],
                response=r["response"],
                raw_score=r["raw_score"],
                response_time_ms=r["response_time_ms"],
                theta_at_answer=r.get("theta_at_answer", 0.0),
                evaluation_log=r.get("evaluation_log"),
            )
            for r in data.get("items", [])
        ]
        return cls(
            theta=data.get("theta", 0.0),
            theta_se=data.get("theta_se", 1.0),
            stopped=data.get("stopped", False),
            stop_reason=data.get("stop_reason"),
            eap_failures=data.get("eap_failures", 0),  # S8.1: backward-compat default=0
            prior_mean=data.get("prior_mean", 0.0),
            prior_sd=data.get("prior_sd", 1.0),
            items=items,
        )


# ── 3PL IRT math ──────────────────────────────────────────────────────────────


def _prob_3pl(theta: float, a: float, b: float, c: float) -> float:
    """3PL probability: P(correct | theta) = c + (1-c) / (1 + exp(-a*(theta-b)))"""
    exp_val = a * (theta - b)
    # Clamp to prevent overflow
    exp_val = max(-20.0, min(20.0, exp_val))
    return c + (1.0 - c) / (1.0 + math.exp(-exp_val))


def _fisher_information(theta: float, a: float, b: float, c: float) -> float:
    """Fisher information for a 3PL item at a given theta.

    I(theta) = a^2 * (P - c)^2 * Q / ((1-c)^2 * P)
    where P = P(theta), Q = 1 - P
    """
    p = _prob_3pl(theta, a, b, c)
    q = 1.0 - p
    if p < 1e-10 or q < 1e-10:
        return 0.0
    numerator = (a ** 2) * ((p - c) ** 2) * q
    denominator = ((1.0 - c) ** 2) * p
    if denominator < 1e-10:
        return 0.0
    return numerator / denominator


def _normal_density(x: float, mean: float = 0.0, sd: float = 1.0) -> float:
    """Standard normal density function."""
    # BUG-QA-021 FIX: guard against sd<=0 — would cause ZeroDivisionError in EAP estimation
    if sd <= 0.0:
        sd = 1e-6
    z = (x - mean) / sd
    return math.exp(-0.5 * z * z) / (sd * math.sqrt(2.0 * math.pi))


def _estimate_eap(
    items: list[ItemRecord],
    prior_mean: float = 0.0,
    prior_sd: float = 1.0,
) -> tuple[float, float]:
    """Estimate ability (theta) and SE via EAP with Gauss-Hermite-like quadrature.

    EAP = E[theta | responses] = integral(theta * L(theta) * prior(theta)) / integral(L(theta) * prior(theta))

    Returns:
        (theta_hat, se)
    """
    # Create quadrature grid
    step = (ABILITY_SCALE_MAX - ABILITY_SCALE_MIN) / (NUM_QUADRATURE_POINTS - 1)
    thetas = [ABILITY_SCALE_MIN + i * step for i in range(NUM_QUADRATURE_POINTS)]

    # For each quadrature point, compute likelihood * prior
    log_posteriors = []
    for t in thetas:
        log_like = 0.0
        for item in items:
            p = _prob_3pl(t, item.irt_a, item.irt_b, item.irt_c)
            p = max(1e-10, min(1.0 - 1e-10, p))
            if item.response == 1:
                log_like += math.log(p)
            else:
                log_like += math.log(1.0 - p)
        log_prior = math.log(max(1e-30, _normal_density(t, prior_mean, prior_sd)))
        log_posteriors.append(log_like + log_prior)

    # Numerically stable softmax to get posterior weights
    max_log = max(log_posteriors)
    posteriors = [math.exp(lp - max_log) for lp in log_posteriors]
    total = sum(posteriors)
    if total < 1e-30:
        return 0.0, 1.0

    weights = [p / total for p in posteriors]

    # EAP estimate
    theta_hat = sum(w * t for w, t in zip(weights, thetas))

    # SE = sqrt(posterior variance)
    variance = sum(w * (t - theta_hat) ** 2 for w, t in zip(weights, thetas))
    se = math.sqrt(max(0.0, variance))

    return theta_hat, se


# ── Item selection ─────────────────────────────────────────────────────────────


def select_next_item(
    state: CATState,
    available_questions: list[dict[str, Any]],
    epsilon: float = 0.15,
) -> dict[str, Any] | None:
    """Select the next item to administer using Maximum Fisher Information (MFI).

    Args:
        state: current CAT state (theta estimate)
        available_questions: list of question dicts from DB, each must have
            `id`, `irt_a`, `irt_b`, `irt_c`, `question_type`, and i18n fields.

    Returns:
        The selected question dict, or None if no items remain.
    """
    answered_ids = {r.question_id for r in state.items}
    remaining = [q for q in available_questions if q["id"] not in answered_ids]

    if not remaining:
        return None

    # ε-greedy: with probability epsilon, select a random item (anti-gaming / exposure control)
    # Prevents hot items from receiving 80%+ of traffic and leaking via coordination channels
    if len(remaining) > 1 and random.random() < epsilon:
        return random.choice(remaining)

    # Select item with maximum Fisher information at current theta
    best_q = None
    best_info = -1.0

    for q in remaining:
        info = _fisher_information(
            state.theta,
            float(q.get("irt_a", 1.0)),
            float(q.get("irt_b", 0.0)),
            float(q.get("irt_c", 0.0)),
        )
        if info > best_info:
            best_info = info
            best_q = q

    return best_q


def submit_response(
    state: CATState,
    question_id: str,
    irt_a: float,
    irt_b: float,
    irt_c: float,
    raw_score: float,
    response_time_ms: int,
    evaluation_log: dict | None = None,
) -> CATState:
    """Record a response and update theta estimate.

    `raw_score` is a 0.0-1.0 continuous value (from BARS for open-ended,
    or 0/1 for MCQ). We binarise at 0.5 for the IRT model.

    Returns:
        Updated CATState.
    """
    binary_response = 1 if raw_score >= 0.5 else 0
    theta_snapshot = state.theta  # RT-IRT: capture theta BEFORE updating with this response

    record = ItemRecord(
        question_id=question_id,
        irt_a=irt_a,
        irt_b=irt_b,
        irt_c=irt_c,
        response=binary_response,
        raw_score=raw_score,
        theta_at_answer=theta_snapshot,
        response_time_ms=response_time_ms,
        evaluation_log=evaluation_log,
    )
    state.items.append(record)

    # Re-estimate theta with all answered items
    try:
        theta, se = _estimate_eap(state.items, prior_mean=state.prior_mean, prior_sd=state.prior_sd)
        state.theta = theta
        state.theta_se = se
    except Exception as e:
        # S8.1: eap_failures is a proper dataclass field — survives to_dict/from_dict
        # across HTTP requests. Dynamic _eap_failures attribute was lost on every
        # deserialization, allowing silent score corruption to accumulate indefinitely.
        from loguru import logger
        state.eap_failures += 1
        logger.warning(
            f"EAP estimation failed (attempt #{state.eap_failures}), "
            f"keeping theta={state.theta:.4f}: {e}"
        )
        # Abort session after 3 cumulative EAP failures (prevents bogus scores)
        if state.eap_failures >= 3:
            state.stopped = True
            state.stop_reason = "eap_degraded"
            logger.error(
                f"EAP failed {state.eap_failures} times — stopping session (eap_degraded)"
            )

    return state


def should_stop(state: CATState, energy_level: str = "full") -> tuple[bool, str | None]:
    """Check whether the CAT session should terminate.

    Constitution Law 2: Energy Adaptation
    - Full energy: 20 items max, SE < 0.3 (precise assessment)
    - Mid energy:  12 items max, SE < 0.4 (balanced, shorter)
    - Low energy:  5 items max, SE < 0.5 (minimal, respect user state)

    Args:
        state: Current CAT state
        energy_level: User self-reported energy ("full" | "mid" | "low")

    Returns:
        (stop: bool, reason: str | None)
    """
    profile = ENERGY_STOPPING.get(energy_level, ENERGY_STOPPING["full"])
    n = len(state.items)

    if n >= profile["max_items"]:
        return True, "max_items"

    if n >= profile["min_before_se"] and state.theta_se <= profile["se_threshold"]:
        return True, "se_threshold"

    return False, None


def theta_to_score(theta: float) -> float:
    """Convert IRT theta (logit scale) to 0-100 AURA competency score.

    Uses a logistic mapping:
        score = 100 * sigmoid(theta)  (centred at 0 -> 50)

    Clamped to [0, 100].
    """
    # Clamp theta before exp to prevent OverflowError on extreme values.
    # Beyond ±20 the sigmoid saturates (score < 2e-7 or > 99.9999998), so
    # clamping here is mathematically equivalent to clamping the output.
    theta_clamped = max(-500.0, min(500.0, theta))
    raw = 100.0 / (1.0 + math.exp(-theta_clamped))
    return max(0.0, min(100.0, raw))
