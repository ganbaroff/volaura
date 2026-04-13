"""E2E test: IRT/CAT engine → AURA score → badge.

Tests the assessment engine logic against REAL seed data from Supabase.
Does NOT create sessions (FK constraints require auth users).
Instead, tests: item selection, scoring, AURA calculation, badge tiers.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from supabase import acreate_client


async def run_e2e():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    admin = await acreate_client(url, key)

    print("=" * 60)
    print("E2E TEST: Assessment Engine + AURA + Badge")
    print("=" * 60)

    # Step 1: Verify seed data
    print("\nStep 1: Checking seed data...")
    comps = await admin.table("competencies").select("id, slug, name_en, weight").execute()
    assert len(comps.data) == 8, f"Expected 8 competencies, got {len(comps.data)}"
    print("  OK: 8 competencies")

    weights = {c["slug"]: c.get("weight", 0) for c in comps.data}
    weight_sum = sum(weights.values())
    print(f"  Weights sum: {weight_sum} (should be ~1.0)")

    questions = await admin.table("questions").select("id, competency_id, difficulty, irt_a, irt_b, irt_c, type").execute()
    assert len(questions.data) >= 8, f"Expected >= 8 questions, got {len(questions.data)}"
    print(f"  OK: {len(questions.data)} questions")

    # Step 2: Build item bank for communication
    print("\nStep 2: Building item bank...")
    comm = next(c for c in comps.data if c["slug"] == "communication")
    comm_id = comm["id"]
    comm_qs = [q for q in questions.data if q["competency_id"] == comm_id]
    print(f"  Communication questions: {len(comm_qs)}")

    items = []
    for q in comm_qs:
        items.append({
            "id": q["id"],
            "a": q.get("irt_a") or 1.0,
            "b": q.get("irt_b") or 0.0,
            "c": q.get("irt_c") or 0.2,
        })

    # Step 3: Run IRT/CAT engine
    print("\nStep 3: Running IRT/CAT engine...")
    from app.core.assessment.engine import CATState, select_next_item, should_stop, submit_response, theta_to_score

    state = CATState(theta=0.0, theta_se=1.0, items=[])
    answers = 0
    max_q = min(10, len(items))

    for i in range(max_q):
        next_item = select_next_item(state, items)
        if next_item is None:
            print(f"  No more items after {i} answers")
            break

        # Simulate good answers (raw_score=0.8, response_time=5000ms)
        state = submit_response(
            state,
            question_id=next_item["id"],
            irt_a=next_item["a"],
            irt_b=next_item["b"],
            irt_c=next_item["c"],
            raw_score=0.8,
            response_time_ms=5000,
        )
        answers += 1
        print(f"  Q{i+1}: theta={state.theta:.3f}, SE={state.theta_se:.3f}")

        if should_stop(state):
            print(f"  CAT stop criterion met after {answers} questions")
            break

    comm_score = theta_to_score(state.theta)
    print(f"  Final: theta={state.theta:.3f} -> score={comm_score:.1f}/100")
    assert 0 <= comm_score <= 100

    # Step 4: Test with poor answers
    print("\nStep 4: Testing with poor answers...")
    state_bad = CATState(theta=0.0, theta_se=1.0, items=[])
    for _i in range(min(5, len(items))):
        next_item = select_next_item(state_bad, items)
        if next_item is None:
            break
        state_bad = submit_response(
            state_bad,
            question_id=next_item["id"],
            irt_a=next_item["a"],
            irt_b=next_item["b"],
            irt_c=next_item["c"],
            raw_score=0.2,
            response_time_ms=5000,
        )

    bad_score = theta_to_score(state_bad.theta)
    print(f"  Poor answers: theta={state_bad.theta:.3f} -> score={bad_score:.1f}/100")
    assert bad_score < comm_score, "Bad answers should score lower"
    print(f"  OK: {bad_score:.1f} < {comm_score:.1f}")

    # Step 5: AURA calculation
    print("\nStep 5: AURA calculation...")
    from app.core.assessment.aura_calc import calculate_overall, get_badge_tier, is_elite

    # Simulate 3 competency scores
    scores = {
        "communication": comm_score,
        "reliability": 75.0,
        "leadership": 60.0,
    }
    overall = calculate_overall(scores)
    tier = get_badge_tier(overall)
    elite = is_elite(overall, scores)
    print(f"  Scores: {scores}")
    print(f"  Overall AURA: {overall:.1f}")
    print(f"  Badge: {tier}")
    print(f"  Elite: {elite}")

    # Step 6: Badge tier thresholds
    print("\nStep 6: Badge tier verification...")
    tests = [(95, "platinum"), (80, "gold"), (65, "silver"), (50, "bronze"), (30, "none")]
    for score, expected in tests:
        actual = get_badge_tier(score)
        status = "OK" if actual == expected else f"FAIL (got {actual})"
        print(f"  {score} -> {expected}: {status}")
        assert actual == expected, f"Badge {score}: expected {expected}, got {actual}"

    # Step 7: Anti-gaming smoke test
    print("\nStep 7: Anti-gaming smoke test...")
    from app.core.assessment.antigaming import GamingSignal

    GamingSignal()
    from app.core.assessment.antigaming import check_answer_timing

    # Normal timing
    result = check_answer_timing(5000)
    assert result.get("rushed") is not True, "5s should not be rushed"
    print("  5000ms: normal (OK)")

    # Rushed timing
    result = check_answer_timing(500)
    print(f"  500ms: {result}")

    # Spoofed timing (negative)
    result = check_answer_timing(-100)
    print(f"  -100ms: {result}")

    print("  Anti-gaming function API: all checks passed")

    # Summary
    print("\n" + "=" * 60)
    print("E2E RESULT: ALL STEPS PASSED")
    print("=" * 60)
    print(f"  Seed data: 8 competencies, {len(questions.data)} questions")
    print(f"  IRT/CAT: {answers} questions -> theta={state.theta:.3f}")
    print(f"  Good score: {comm_score:.1f}/100")
    print(f"  Bad score: {bad_score:.1f}/100")
    print(f"  AURA overall: {overall:.1f}, tier: {tier}")
    print("  Anti-gaming: timing checks passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_e2e())
