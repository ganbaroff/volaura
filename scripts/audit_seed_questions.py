"""Audit all open-ended seed questions for Gaming Resistance Score (GRS).

Run from repo root:
    cd apps/api
    python ../../scripts/audit_seed_questions.py

Requires:
    - apps/api/app must be importable (run from apps/api/ or add to PYTHONPATH)
    - No DB connection needed — pure static analysis of expected_concepts JSON

Output:
    - Per-question GRS score and pass/fail
    - Specific penalties that reduce GRS
    - Redesign recommendations for questions that fail
"""

from __future__ import annotations

import json
import sys
import os

# Allow running from repo root or apps/api/
_api_dir = os.path.join(os.path.dirname(__file__), "..", "apps", "api")
if _api_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_api_dir))

from app.core.assessment.quality_gate import compute_grs, GRS_THRESHOLD  # compute_grs returns float

# ── Questions to audit ────────────────────────────────────────────────────────
# These are the open-ended questions from seed.sql.
# MCQ questions don't use keyword matching, so GRS is irrelevant for them.

SEED_QUESTIONS = [
    {
        "id": "c0000001-0000-0000-0000-000000000003",
        "label": "Q3 — Cross-cultural Communication (medium, communication)",
        "scenario_en": (
            "You are coordinating a registration desk at an international conference. "
            "A foreign delegate approaches and appears confused — they speak limited English and seem frustrated. "
            "Describe exactly what you would do."
        ),
        "expected_concepts": [
            {"name": "calm_tone", "weight": 0.20, "keywords": ["spoke slowly and clearly", "kept my voice soft", "maintained a calm demeanor", "reduced my speaking pace", "stayed patient despite the frustration", "sakit ton saxladım", "yavaş danışdım"]},
            {"name": "nonverbal_support", "weight": 0.20, "keywords": ["used hand gestures to indicate", "drew a quick sketch", "pointed to a map", "used visual aids to guide", "showed them the registration form", "əl hərəkətlərindən istifadə etdim", "xəritəni göstərdim"]},
            {"name": "simplify_language", "weight": 0.20, "keywords": ["used short simple sentences", "avoided technical jargon", "spoke one step at a time", "repeated key information more slowly", "used basic words they might know", "qısa sadə cümlələr işlətdim", "texniki terminlərdən çəkindim"]},
            {"name": "seek_help", "weight": 0.20, "keywords": ["found a bilingual colleague to assist", "used a translation app", "called over a team member who spoke their language", "asked a nearby colleague to help translate", "used Google Translate as a bridge", "ikidilli həmkar tapdım", "tərcümə proqramından istifadə etdim"]},
            {"name": "follow_through", "weight": 0.20, "keywords": ["confirmed they completed registration successfully", "checked they had everything they needed", "ensured the delegate was no longer confused", "stayed with them until the issue was resolved", "followed up after handing them to a colleague", "qeydiyyatı tamamladıqlarını təsdiqlədi", "nəticəni yoxladım"]},
        ],
    },
    {
        "id": "c0000001-0000-0000-0000-000000000004",
        "label": "Q4 — Crisis Communication / Room Change (hard, communication)",
        "scenario_en": (
            'Your team coordinator just texted: "The session room changed to B-14, inform all attendees ASAP." '
            "You have 10 minutes and 50 attendees scattered across the venue. Describe your communication plan."
        ),
        "expected_concepts": [
            {"name": "prioritize_channels", "weight": 0.25, "keywords": ["sent a group message to all attendees", "used the event app to broadcast", "made an announcement over the public address system", "contacted attendees simultaneously through multiple channels", "reached everyone at once via messaging platform", "bütün iştirakçılara qrup mesajı göndərdim", "ictimai elan sistemi ilə xəbər verdim"]},
            {"name": "delegate", "weight": 0.20, "keywords": ["split the venue into sections and assigned each volunteer a zone", "sent a different volunteer to each floor", "divided the team to cover the whole building", "each team member took responsibility for a different area", "coordinated with my team to cover all areas simultaneously", "binayı bölgələrə bölüb hər könüllüyə sahə təyin etdim", "komandanı müxtəlif əraziləri əhatə etmək üçün böldüm"]},
            {"name": "clear_message", "weight": 0.25, "keywords": ["clearly stated the new room is B-14", "gave exact directions to room B-14", "specified the floor and building of the new location", "included the room number in every message", "made sure the message had the room number and timing", "yeni otağın B-14 olduğunu bildirdim", "hər mesajda otaq nömrəsini göstərdim"]},
            {"name": "confirm_coverage", "weight": 0.15, "keywords": ["each volunteer reported back once their area was covered", "confirmed all 50 attendees were reached", "collected confirmation from each zone volunteer", "verified no one was missed before the session started", "did a headcount at the new room to verify everyone arrived", "hər könüllü öz ərazisini əhatə etdikdən sonra bildirdi", "50 iştirakçının hamısına çatdığımı təsdiqlədi"]},
            {"name": "stay_calm", "weight": 0.15, "keywords": ["maintained composure despite the time pressure", "stayed focused and worked systematically through each zone", "kept the team calm while moving quickly", "communicated urgency without causing panic", "worked through the problem in an organized manner", "vaxt təzyiqi altında özünü itirmədi", "panikaya yol vermədən təcililik hissini çatdırdım"]},
        ],
    },
]

# ── Old keyword sets (for comparison) ────────────────────────────────────────

OLD_CONCEPTS_Q3 = [
    {"name": "calm_tone", "weight": 0.20, "keywords": ["calm", "slow", "smile", "patient", "relax", "friendly"]},
    {"name": "nonverbal_support", "weight": 0.20, "keywords": ["gesture", "point", "show", "visual", "map", "sign"]},
    {"name": "simplify_language", "weight": 0.20, "keywords": ["simple", "short", "basic words", "avoid jargon"]},
    {"name": "seek_help", "weight": 0.20, "keywords": ["colleague", "translator", "app", "Google Translate", "supervisor"]},
    {"name": "follow_through", "weight": 0.20, "keywords": ["confirm", "check", "ensure resolved", "follow up"]},
]

OLD_CONCEPTS_Q4 = [
    {"name": "prioritize_channels", "weight": 0.25, "keywords": ["broadcast", "group message", "announce", "speaker", "multiple channels"]},
    {"name": "delegate", "weight": 0.20, "keywords": ["team", "split", "assign", "volunteers", "divide"]},
    {"name": "clear_message", "weight": 0.25, "keywords": ["room number", "B-14", "time", "direction", "clear"]},
    {"name": "confirm_coverage", "weight": 0.15, "keywords": ["check", "confirm all informed", "follow up", "account for"]},
    {"name": "stay_calm", "weight": 0.15, "keywords": ["calm", "systematic", "organized"]},
]


# ── Audit runner ──────────────────────────────────────────────────────────────

def audit_question(q: dict, label_suffix: str = "") -> None:
    label = q["label"] + label_suffix
    score: float = compute_grs(q)  # returns float, not a dataclass
    status = "✅ PASS" if score >= GRS_THRESHOLD else "❌ FAIL"
    print(f"\n{'='*70}")
    print(f"{status}  {label}")
    print(f"  GRS: {score:.3f}  (threshold: {GRS_THRESHOLD})")
    if score >= GRS_THRESHOLD:
        print("  → No redesign needed.")
    else:
        print(f"  → Redesign required. GRS {score:.2f} < {GRS_THRESHOLD}")


def main() -> None:
    print("=" * 70)
    print("VOLAURA — Question Bank GRS Audit")
    print(f"Threshold: {GRS_THRESHOLD} | Questions analysed: {len(SEED_QUESTIONS)}")
    print("=" * 70)

    print("\n── BEFORE (original seed keywords) ─────────────────────────────────")
    old_q3 = {**SEED_QUESTIONS[0], "expected_concepts": OLD_CONCEPTS_Q3}
    old_q4 = {**SEED_QUESTIONS[1], "expected_concepts": OLD_CONCEPTS_Q4}
    audit_question(old_q3, " [OLD]")
    audit_question(old_q4, " [OLD]")

    print("\n\n── AFTER (redesigned behavioral phrase keywords) ────────────────────")
    for q in SEED_QUESTIONS:
        audit_question(q, " [NEW]")

    print("\n\n── SUMMARY ──────────────────────────────────────────────────────────")
    old_results: list[float] = [compute_grs({**q, "expected_concepts": old}) for q, old in [
        (SEED_QUESTIONS[0], OLD_CONCEPTS_Q3),
        (SEED_QUESTIONS[1], OLD_CONCEPTS_Q4),
    ]]
    new_results: list[float] = [compute_grs(q) for q in SEED_QUESTIONS]
    for i, (q, old_r, new_r) in enumerate(zip(SEED_QUESTIONS, old_results, new_results), 1):
        delta = new_r - old_r
        print(f"  Q{i+2}: {old_r:.3f} → {new_r:.3f}  (+{delta:.3f})  {'✅' if new_r >= GRS_THRESHOLD else '❌'}")

    total_pass = sum(1 for r in new_results if r >= GRS_THRESHOLD)
    print(f"\n  Pass rate: {total_pass}/{len(SEED_QUESTIONS)} questions")
    if total_pass == len(SEED_QUESTIONS):
        print("  ✅ All seed questions pass GRS. Question bank is gaming-resistant.")
    else:
        print(f"  ❌ {len(SEED_QUESTIONS) - total_pass} question(s) need redesign.")
        sys.exit(1)


if __name__ == "__main__":
    main()
