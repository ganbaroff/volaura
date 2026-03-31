"""
simulate_irt.py -- VOLAURA CAT/IRT Assessment Simulation

Simulates 100,000 assessment sessions to analyse:
  1. Engine accuracy across ability levels
  2. Item exposure and bank gaps
  3. Question writer guidance

Mirrors engine.py exactly:
  - 3PL: P(theta) = c + (1-c) / (1 + exp(-a*(theta-b)))   <- no 1.702 scaling (engine.py line 126)
  - EAP with 49 quadrature points on [-4, 4]               <- engine.py _estimate_eap
  - MFI item selection with epsilon=0.15 greedy             <- engine.py select_next_item
  - Stop: SE <= 0.3 OR 20 questions, min 5 items            <- engine.py should_stop

Performance: fully numpy-vectorised.  100k sessions < 60s on standard laptop.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone

import numpy as np

# -- Constants (mirror engine.py exactly) --------------------------------------
MAX_ITEMS = 20
SE_THRESHOLD = 0.3
MIN_ITEMS_BEFORE_SE_STOP = 5
ABILITY_SCALE_MIN = -4.0
ABILITY_SCALE_MAX = 4.0
NUM_QUADRATURE_POINTS = 49
EPSILON = 0.15       # epsilon-greedy exploration rate

RNG_SEED = 42
N_SIMULATIONS = 100_000

COMPETENCIES = [
    "communication",
    "reliability",
    "english_proficiency",
    "leadership",
    "event_performance",
    "tech_literacy",
    "adaptability",
    "empathy_safeguarding",
]

# Real questions from seed.sql (5 Communication questions)
REAL_QUESTIONS = [
    {"id": "Q1", "a": 1.5, "b": -1.2, "c": 0.10, "label": "Active Listening (Easy)"},
    {"id": "Q2", "a": 1.8, "b":  0.1, "c": 0.15, "label": "Conflict Communication (Medium)"},
    {"id": "Q3", "a": 2.0, "b":  0.3, "c": 0.00, "label": "Cross-cultural (Medium)"},
    {"id": "Q4", "a": 2.2, "b":  0.8, "c": 0.00, "label": "Written Communication (Hard)"},
    {"id": "Q5", "a": 2.5, "b": -0.5, "c": 0.10, "label": "SJT Reliability (Easy-Med)"},
]


# -- Pre-computed quadrature grid -----------------------------------------------
QUAD_THETAS = np.linspace(ABILITY_SCALE_MIN, ABILITY_SCALE_MAX, NUM_QUADRATURE_POINTS)  # (49,)
# Normal(0,1) log-prior on grid (constant across all sessions)
LOG_PRIOR = -0.5 * QUAD_THETAS ** 2 - 0.5 * np.log(2 * np.pi)   # (49,)


# -- IRT math -------------------------------------------------------------------

def prob_3pl(theta_grid: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """P(correct|theta) for each theta in grid.  Engine: c + (1-c)/(1+exp(-a*(t-b)))."""
    ev = np.clip(a * (theta_grid - b), -20.0, 20.0)
    return c + (1.0 - c) / (1.0 + np.exp(-ev))


def fisher_info_grid(theta_grid: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Fisher information at every theta in grid.  Used for item selection."""
    p = prob_3pl(theta_grid, a, b, c)
    q = 1.0 - p
    num = (a ** 2) * ((p - c) ** 2) * q
    den = ((1.0 - c) ** 2) * np.where(p > 1e-10, p, 1e-10)
    return np.where((p > 1e-10) & (q > 1e-10), num / den, 0.0)


# -- Synthetic question bank ----------------------------------------------------

def build_bank(rng: np.random.Generator, n_per_comp: int = 20):
    """
    Returns arrays a, b, c each of shape (n_items,) and comp_labels list.
    n_items = n_per_comp * 8 = 160
    """
    n_total = n_per_comp * len(COMPETENCIES)
    a = rng.uniform(0.5, 2.5, n_total)
    b = rng.uniform(-2.0, 2.0, n_total)
    c = rng.uniform(0.05, 0.25, n_total)
    comps = []
    for comp in COMPETENCIES:
        comps.extend([comp] * n_per_comp)
    return a, b, c, comps


# -- Core simulation (session-by-session loop, numpy EAP) ----------------------

def simulate_all(
    bank_a: np.ndarray,
    bank_b: np.ndarray,
    bank_c: np.ndarray,
    rng: np.random.Generator,
    n_sim: int = N_SIMULATIONS,
) -> dict:
    """
    Run n_sim CAT sessions.  Returns aggregated arrays.

    Key optimisation: EAP is a numpy operation over 49 quadrature points,
    not a Python loop.  Item selection still loops over remaining items (max 160)
    but uses numpy dot products for Fisher info.

    On a standard laptop: ~30-50 seconds for 100k sessions.
    """
    n_items_bank = len(bank_a)

    # Pre-compute P(theta_grid | item) matrices for all items: shape (n_items, 49)
    # This lets us look up probabilities with array indexing during EAP updates.
    print("  Pre-computing item probability matrices...", flush=True)
    t0 = time.time()
    P_all = np.zeros((n_items_bank, NUM_QUADRATURE_POINTS))   # (160, 49)
    FI_all = np.zeros((n_items_bank, NUM_QUADRATURE_POINTS))  # (160, 49) Fisher info
    for i in range(n_items_bank):
        P_all[i] = prob_3pl(QUAD_THETAS, bank_a[i], bank_b[i], bank_c[i])
        FI_all[i] = fisher_info_grid(QUAD_THETAS, bank_a[i], bank_b[i], bank_c[i])

    # Fisher info at a single theta: FI_at_theta[i] = FI_all[i, idx_nearest_theta]
    # We'll interpolate by finding the nearest quadrature point to current theta estimate.
    print(f"  Done ({time.time()-t0:.2f}s).  Running {n_sim:,} sessions...", flush=True)

    true_thetas = rng.normal(0.0, 1.0, n_sim)

    est_thetas      = np.zeros(n_sim)
    final_ses       = np.zeros(n_sim)
    n_items_used    = np.zeros(n_sim, dtype=np.int32)
    exposure_counts = np.zeros(n_items_bank, dtype=np.int64)

    # Pre-draw ALL random numbers upfront (faster than per-session calls)
    # For each session: up to MAX_ITEMS item selections need:
    #   - 1 float for epsilon check
    #   - 1 int for random item choice (if epsilon triggered)
    #   - 1 float for response (correct/incorrect)
    epsilon_draws  = rng.random((n_sim, MAX_ITEMS))          # (100k, 20)
    rand_choice    = rng.integers(0, n_items_bank,           # (100k, 20)
                                  size=(n_sim, MAX_ITEMS))
    response_draws = rng.random((n_sim, MAX_ITEMS))          # (100k, 20)

    report_at = set(range(0, n_sim, n_sim // 10))

    for s in range(n_sim):
        if s in report_at and s > 0:
            elapsed = time.time() - t0
            pct = 100 * s / n_sim
            eta = elapsed / s * (n_sim - s)
            print(f"    {pct:.0f}%  ({s:,}/{n_sim:,}) -- {elapsed:.1f}s, ~{eta:.0f}s remaining", flush=True)

        true_t = true_thetas[s]
        answered = np.zeros(n_items_bank, dtype=bool)

        # Running log-likelihood accumulator over quadrature grid (49,)
        log_like_acc = np.zeros(NUM_QUADRATURE_POINTS)

        current_theta = 0.0
        current_se    = 1.0

        for step in range(MAX_ITEMS):
            n_answered = step  # items answered so far

            # --- Item selection ---
            remaining_mask = ~answered   # (160,) bool

            # Nearest quadrature index to current_theta for MFI lookup
            q_idx = int(np.searchsorted(QUAD_THETAS, current_theta, side="left"))
            q_idx = max(0, min(NUM_QUADRATURE_POINTS - 1, q_idx))

            remaining_indices = np.where(remaining_mask)[0]
            if len(remaining_indices) == 0:
                break

            if len(remaining_indices) > 1 and epsilon_draws[s, step] < EPSILON:
                # Epsilon-greedy: pick random remaining item
                rand_i = rand_choice[s, step] % len(remaining_indices)
                chosen_idx = remaining_indices[rand_i]
            else:
                # Max Fisher Information at current theta
                fi_vals = FI_all[remaining_indices, q_idx]
                chosen_idx = remaining_indices[int(np.argmax(fi_vals))]

            answered[chosen_idx] = True
            exposure_counts[chosen_idx] += 1

            # --- Simulate response ---
            p_correct = float(prob_3pl(np.array([true_t]),
                                       bank_a[chosen_idx],
                                       bank_b[chosen_idx],
                                       bank_c[chosen_idx])[0])
            response = 1 if response_draws[s, step] < p_correct else 0

            # --- EAP update (numpy, no Python loop) ---
            p_grid = P_all[chosen_idx]                           # (49,)
            p_grid_safe = np.clip(p_grid, 1e-10, 1.0 - 1e-10)
            if response == 1:
                log_like_acc += np.log(p_grid_safe)
            else:
                log_like_acc += np.log(1.0 - p_grid_safe)

            log_post = log_like_acc + LOG_PRIOR
            log_post -= log_post.max()        # numeric stability
            post = np.exp(log_post)
            total = post.sum()
            if total < 1e-30:
                current_theta, current_se = 0.0, 1.0
            else:
                weights = post / total
                current_theta = float((weights * QUAD_THETAS).sum())
                variance = float((weights * (QUAD_THETAS - current_theta) ** 2).sum())
                current_se = float(np.sqrt(max(0.0, variance)))

            # --- Stopping check (mirrors engine.py should_stop) ---
            n_now = step + 1
            if n_now >= MIN_ITEMS_BEFORE_SE_STOP and current_se <= SE_THRESHOLD:
                n_answered = n_now
                break
        else:
            n_answered = MAX_ITEMS

        est_thetas[s]   = current_theta
        final_ses[s]    = current_se
        n_items_used[s] = n_answered if n_answered > 0 else step + 1

    return {
        "true_thetas":     true_thetas,
        "est_thetas":      est_thetas,
        "final_ses":       final_ses,
        "n_items_used":    n_items_used,
        "exposure_counts": exposure_counts,
    }


# -- Analysis -------------------------------------------------------------------

def overall_accuracy(true_t, est_t):
    err = est_t - true_t
    return {
        "rmse":        float(np.sqrt(np.mean(err ** 2))),
        "mae":         float(np.mean(np.abs(err))),
        "bias":        float(np.mean(err)),
        "correlation": float(np.corrcoef(true_t, est_t)[0, 1]),
    }


def by_ability_level(true_t, est_t, ses, n_items):
    buckets = {
        "very_low":  (true_t < -1.5),
        "low":       (true_t >= -1.5) & (true_t < -0.5),
        "medium":    (true_t >= -0.5) & (true_t <= 0.5),
        "high":      (true_t > 0.5)   & (true_t <= 1.5),
        "very_high": (true_t > 1.5),
    }
    result = {}
    for name, mask in buckets.items():
        if mask.sum() == 0:
            continue
        err = est_t[mask] - true_t[mask]
        result[name] = {
            "n":             int(mask.sum()),
            "rmse":          float(np.sqrt(np.mean(err ** 2))),
            "mae":           float(np.mean(np.abs(err))),
            "mean_se":       float(np.mean(ses[mask])),
            "mean_n_items":  float(np.mean(n_items[mask])),
        }
    return result


def item_exposure_analysis(bank_b, bank_comp, exposure_counts):
    n = len(bank_b)
    result = {}
    for i in range(n):
        rate = float(exposure_counts[i] / N_SIMULATIONS)
        result[i] = {
            "comp":          bank_comp[i],
            "b":             round(float(bank_b[i]), 3),
            "exposure_rate": round(rate, 4),
            "overexposed":   rate > 0.30,
            "underexposed":  rate < 0.05,
        }
    return result


def gap_analysis(bank_b, exposure_counts):
    easy_mask   = bank_b < -0.5
    medium_mask = (bank_b >= -0.5) & (bank_b <= 0.5)
    hard_mask   = bank_b > 0.5

    def stats(mask):
        count = int(mask.sum())
        if count == 0:
            return {"count": 0, "total_exposure_pct": 0.0, "mean_item_exposure_rate": 0.0, "needed": 20}
        total_exp_rate = float(exposure_counts[mask].sum()) / N_SIMULATIONS
        mean_rate = total_exp_rate / count
        return {
            "count": count,
            "total_exposure_pct": round(100.0 * total_exp_rate / count, 1),
            "mean_item_exposure_rate": round(mean_rate, 4),
            "needed": max(0, 20 - count),
        }

    return {
        "easy":   stats(easy_mask),
        "medium": stats(medium_mask),
        "hard":   stats(hard_mask),
    }


def real_question_analysis(real_qs):
    theta_range = np.linspace(-3, 3, 300)
    result = []
    for q in real_qs:
        a, b, c = q["a"], q["b"], q["c"]
        p = prob_3pl(theta_range, a, b, c)
        q_p = 1.0 - p
        num = (a ** 2) * ((p - c) ** 2) * q_p
        den = ((1.0 - c) ** 2) * np.where(p > 1e-10, p, 1e-10)
        info = np.where((p > 1e-10) & (q_p > 1e-10), num / den, 0.0)
        peak_theta = float(theta_range[np.argmax(info)])
        max_info   = float(info.max())
        bucket = "easy" if b < -0.5 else ("hard" if b > 0.5 else "medium")
        result.append({
            "id":               q["id"],
            "label":            q["label"],
            "a": a, "b": b, "c": c,
            "difficulty_bucket": bucket,
            "peak_info_theta":  round(peak_theta, 2),
            "max_fisher_info":  round(max_info, 3),
        })
    return result


# -- Printing -------------------------------------------------------------------

def hdr(title):
    print()
    print("=" * 65)
    print(f"  {title}")
    print("=" * 65)


def print_overall(s):
    hdr("A) OVERALL ACCURACY (100,000 sessions)")
    passed = s["rmse"] < 0.40 and abs(s["bias"]) < 0.05
    print(f"  RMSE (Root Mean Square Error):  {s['rmse']:.4f}   (target < 0.40)")
    print(f"  Mean Absolute Error:            {s['mae']:.4f}")
    print(f"  Bias (mean est - true):         {s['bias']:+.4f}  (target ~= 0)")
    print(f"  Correlation (true vs est):      {s['correlation']:.4f}  (target > 0.95)")
    verdict = "PASS" if passed else "NEEDS IMPROVEMENT"
    sign    = "<" if s["rmse"] < 0.40 else ">="
    print(f"\n  [{verdict}] RMSE {s['rmse']:.4f} {sign} 0.40 threshold")


def print_by_ability(by_level):
    hdr("B) PERFORMANCE BY ABILITY LEVEL")
    labels = {
        "very_low":  "Very Low  (theta < -1.5)",
        "low":       "Low       (-1.5 to -0.5)",
        "medium":    "Medium    (-0.5 to 0.5) ",
        "high":      "High      (0.5 to 1.5)  ",
        "very_high": "Very High (theta > 1.5) ",
    }
    print(f"  {'Bucket':<28} {'N':>7} {'RMSE':>7} {'MAE':>7} {'MeanSE':>8} {'AvgQ':>6}")
    print("  " + "-" * 63)
    for key, label in labels.items():
        d = by_level.get(key)
        if not d:
            continue
        print(
            f"  {label:<28} {d['n']:>7,} {d['rmse']:>7.4f} {d['mae']:>7.4f} "
            f"{d['mean_se']:>8.4f} {d['mean_n_items']:>6.1f}"
        )


def print_exposure(exposure, bank_b):
    hdr("C) ITEM EXPOSURE ANALYSIS")
    over   = [v for v in exposure.values() if v["overexposed"]]
    under  = [v for v in exposure.values() if v["underexposed"]]
    print(f"  Total items: {len(exposure)}")
    print(f"  Overexposed  (rate > 30%): {len(over)}")
    print(f"  Underexposed (rate <  5%): {len(under)}")

    if over:
        print("\n  Top overexposed items (security risk):")
        print(f"  {'Comp':<22} {'b':>6} {'Rate':>7}")
        print("  " + "-" * 38)
        for v in sorted(over, key=lambda x: -x["exposure_rate"])[:10]:
            print(f"  {v['comp']:<22} {v['b']:>6.2f} {v['exposure_rate']:>6.1%}")

    if under:
        b_vals = np.array([v["b"] for v in under])
        print(f"\n  {len(under)} underexposed items -- difficulty range [{b_vals.min():.2f}, {b_vals.max():.2f}]")
        print(f"  Mean b of underexposed: {b_vals.mean():.2f}")
        print("  These items are never reached -- indicates a bank gap at this difficulty level.")


def print_gaps(gaps):
    hdr("D) QUESTION BANK GAP REPORT")
    print(f"  {'Bucket':<10} {'Count':>7} {'MeanExp%':>10} {'Needed':>8}")
    print("  " + "-" * 40)
    for bucket, d in gaps.items():
        print(
            f"  {bucket:<10} {d['count']:>7} {d['total_exposure_pct']:>9.1f}% "
            f"{d['needed']:>8}"
        )
    total_needed = sum(d["needed"] for d in gaps.values())
    print(f"\n  Total additional questions needed: {total_needed}")


def print_writer_guide(overall, gaps, bank_b):
    hdr("E) QUESTION WRITER GUIDE")
    easy_n   = int((bank_b < -0.5).sum())
    medium_n = int(((bank_b >= -0.5) & (bank_b <= 0.5)).sum())
    hard_n   = int((bank_b > 0.5).sum())
    rmse = overall["rmse"]
    verdict = "PASS" if rmse < 0.40 else "NEEDS IMPROVEMENT"
    print(f"""
  === QUESTION WRITER GUIDE ===
  For a well-calibrated assessment:
  - Target RMSE < 0.40 (we achieved: {rmse:.4f} [{verdict}])
  - Easy questions   (b: -2.0 to -0.5): needed for users with LOW ability
  - Medium questions (b: -0.5 to 0.5):  MOST important -- covers ~68% of users
  - Hard questions   (b: 0.5 to 2.0):   needed for HIGH-ability discrimination
  - Discrimination (a): aim for 1.2-2.0 -- higher = more informative
  - Guessing (c): keep < 0.25 for MCQ, use 0.0 for open-ended

  Current synthetic bank (160 items):
    Easy:   {easy_n:3d} items
    Medium: {medium_n:3d} items
    Hard:   {hard_n:3d} items

  Recommendation for REAL question bank (target 20 per bucket per competency):
    Add {gaps['easy']['needed']:2d} easy   questions  (b between -2.0 and -0.5)
    Add {gaps['medium']['needed']:2d} medium questions  (b between -0.5 and  0.5)
    Add {gaps['hard']['needed']:2d} hard   questions  (b between  0.5 and  2.0)
""")


def print_real_qs(analysis):
    hdr("F) REAL QUESTION BANK ANALYSIS (5 Communication questions)")
    print(f"  {'Label':<38} {'b':>5} {'a':>5} {'c':>5} {'Bucket':<8} {'PeakTh':>8} {'MaxFI':>8}")
    print("  " + "-" * 82)
    for q in analysis:
        print(
            f"  {q['label']:<38} {q['b']:>5.2f} {q['a']:>5.2f} {q['c']:>5.2f} "
            f"{q['difficulty_bucket']:<8} {q['peak_info_theta']:>8.2f} {q['max_fisher_info']:>8.3f}"
        )
    b_vals = np.array([q["b"] for q in analysis])
    print(f"\n  Difficulty (b) range: [{b_vals.min():.2f}, {b_vals.max():.2f}]  |  Mean: {b_vals.mean():.2f}")
    e = sum(1 for q in analysis if q["difficulty_bucket"] == "easy")
    m = sum(1 for q in analysis if q["difficulty_bucket"] == "medium")
    h = sum(1 for q in analysis if q["difficulty_bucket"] == "hard")
    print(f"  Distribution: {e} easy | {m} medium | {h} hard")
    print("""
  Gap findings for the real bank:
  - No questions with b < -1.2: very-low-ability users see same easy question every time
  - No questions with b > 0.8:  high-ability users exhaust hard items and hit max_items
  - Only 5 questions total: CAT will always use all 5 (can't converge before max_items)
  - Priority adds: 3 hard (b: 1.0-2.0, a: 1.8-2.2) + 2 very-easy (b: -1.5 to -2.0)
  - For production: minimum 15 questions per competency for valid CAT operation
""")


def print_session_stats(n_items, ses):
    hdr("G) SESSION STATISTICS")
    stopped_se  = int((ses <= SE_THRESHOLD).sum())
    stopped_max = int((n_items == MAX_ITEMS).sum())
    print(f"  Mean questions per session:      {n_items.mean():.2f}")
    print(f"  Median questions per session:    {float(np.median(n_items)):.1f}")
    print(f"  Min / Max:                       {n_items.min()} / {n_items.max()}")
    print(f"  Stopped at SE <= 0.30:           {stopped_se:,} ({100*stopped_se/N_SIMULATIONS:.1f}%)")
    print(f"  Stopped at max items (20):       {stopped_max:,} ({100*stopped_max/N_SIMULATIONS:.1f}%)")
    print(f"  Mean final SE:                   {ses.mean():.4f}")
    print(f"  % sessions achieving SE <= 0.30: {100*(ses <= 0.30).mean():.1f}%")
    print(f"  % sessions achieving SE <= 0.40: {100*(ses <= 0.40).mean():.1f}%")


# -- Main -----------------------------------------------------------------------

def main():
    print("=" * 65)
    print("  VOLAURA CAT/IRT Simulation")
    print(f"  N = {N_SIMULATIONS:,} | Seed = {RNG_SEED}")
    print(f"  {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 65)

    rng = np.random.default_rng(RNG_SEED)

    # Build bank
    bank_a, bank_b, bank_c, bank_comp = build_bank(rng, n_per_comp=20)
    print(f"\nSynthetic bank: {len(bank_a)} items ({len(COMPETENCIES)} competencies x 20)")

    # Run
    t_start = time.time()
    sim = simulate_all(bank_a, bank_b, bank_c, rng)
    t_end = time.time()
    print(f"\nSimulation complete: {t_end - t_start:.1f}s total")

    true_t  = sim["true_thetas"]
    est_t   = sim["est_thetas"]
    ses     = sim["final_ses"]
    n_items = sim["n_items_used"]
    exp_cnt = sim["exposure_counts"]

    # Analysis
    ov   = overall_accuracy(true_t, est_t)
    by_l = by_ability_level(true_t, est_t, ses, n_items)
    exp  = item_exposure_analysis(bank_b, bank_comp, exp_cnt)
    gaps = gap_analysis(bank_b, exp_cnt)
    rq   = real_question_analysis(REAL_QUESTIONS)

    # Print
    print_overall(ov)
    print_by_ability(by_l)
    print_exposure(exp, bank_b)
    print_gaps(gaps)
    print_writer_guide(ov, gaps, bank_b)
    print_real_qs(rq)
    print_session_stats(n_items, ses)

    # Save JSON
    output_path = "C:/Projects/VOLAURA/scripts/simulation_results.json"
    stopped_se  = int((ses <= SE_THRESHOLD).sum())
    stopped_max = int((n_items == MAX_ITEMS).sum())
    results = {
        "metadata": {
            "n_simulations": N_SIMULATIONS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "seed": RNG_SEED,
            "bank_size": len(bank_a),
            "elapsed_seconds": round(t_end - t_start, 1),
        },
        "overall": ov,
        "by_ability_level": by_l,
        "item_exposure": {
            "overexposed_count": sum(1 for v in exp.values() if v["overexposed"]),
            "underexposed_count": sum(1 for v in exp.values() if v["underexposed"]),
            "top_10_overexposed": sorted(
                [{"idx": k, **v} for k, v in exp.items() if v["overexposed"]],
                key=lambda x: -x["exposure_rate"],
            )[:10],
        },
        "gap_analysis": {
            "easy_count":   gaps["easy"]["count"],
            "easy_needed":  gaps["easy"]["needed"],
            "medium_count": gaps["medium"]["count"],
            "medium_needed":gaps["medium"]["needed"],
            "hard_count":   gaps["hard"]["count"],
            "hard_needed":  gaps["hard"]["needed"],
        },
        "session_stats": {
            "mean_questions":    round(float(n_items.mean()), 2),
            "median_questions":  float(np.median(n_items)),
            "pct_stopped_at_se": round(100 * stopped_se / N_SIMULATIONS, 2),
            "pct_stopped_at_max":round(100 * stopped_max / N_SIMULATIONS, 2),
            "mean_final_se":     round(float(ses.mean()), 4),
            "pct_se_below_030":  round(100 * float((ses <= 0.30).mean()), 2),
        },
        "real_questions_analysis": rq,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved: {output_path}")
    print()
    hdr("Simulation complete")
    print()


if __name__ == "__main__":
    main()
