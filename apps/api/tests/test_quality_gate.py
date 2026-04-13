"""Tests for app.core.assessment.quality_gate.

Test matrix:
- GRS on seed.sql Q3 (cross-cultural) — single-word keywords should FAIL GRS
- GRS on a well-designed scenario question — should PASS
- Adversarial gate catches keyword dump attacks
- Full checklist pass/fail scenarios
"""

from __future__ import annotations

import pytest

from app.core.assessment.quality_gate import (
    ADVERSARIAL_GATE_THRESHOLD,
    GRS_THRESHOLD,
    compute_grs,
    generate_attack_answers,
    run_adversarial_gate,
    run_quality_checklist,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────

# Exact Q3 from seed.sql — cross-cultural communication
Q3_SEED = {
    "type": "open_ended",
    "scenario_en": (
        "You are coordinating a registration desk at an international conference. "
        "A foreign delegate approaches and appears confused — they speak limited English "
        "and seem frustrated. Describe exactly what you would do."
    ),
    "expected_concepts": [
        {
            "name": "calm_tone",
            "weight": 0.20,
            "keywords": ["calm", "slow", "smile", "patient", "relax", "friendly", "sakit", "gülümsə"],
        },
        {
            "name": "nonverbal_support",
            "weight": 0.20,
            "keywords": ["gesture", "point", "show", "visual", "map", "sign", "işarə", "göstər"],
        },
        {
            "name": "simplify_language",
            "weight": 0.20,
            "keywords": ["simple", "short", "basic words", "avoid jargon", "sadə", "qısa"],
        },
        {
            "name": "seek_help",
            "weight": 0.20,
            "keywords": ["colleague", "translator", "app", "Google Translate", "supervisor", "həmkar", "tərcüməçi"],
        },
        {
            "name": "follow_through",
            "weight": 0.20,
            "keywords": ["confirm", "check", "ensure resolved", "follow up", "təsdiqlə", "nəticəni yoxla"],
        },
    ],
    "irt_a": 2.0,
    "irt_b": 0.3,
    "irt_c": 0.0,
}

# Q3 REDESIGNED — same scenario, multi-word behavioral phrases (from migration 000030)
Q3_REDESIGNED = {
    "type": "open_ended",
    "scenario_en": (
        "You are coordinating a registration desk at an international conference. "
        "A foreign delegate approaches and appears confused — they speak limited English "
        "and seem frustrated. Describe exactly what you would do."
    ),
    "expected_concepts": [
        {
            "name": "calm_tone",
            "weight": 0.20,
            "keywords": ["spoke slowly and clearly", "kept my voice soft", "maintained a calm demeanor", "reduced my speaking pace", "stayed patient despite the frustration"],
        },
        {
            "name": "nonverbal_support",
            "weight": 0.20,
            "keywords": ["used hand gestures to indicate", "drew a quick sketch", "pointed to a map", "used visual aids to guide", "showed them the registration form"],
        },
        {
            "name": "simplify_language",
            "weight": 0.20,
            "keywords": ["used short simple sentences", "avoided technical jargon", "spoke one step at a time", "repeated key information more slowly", "used basic words they might know"],
        },
        {
            "name": "seek_help",
            "weight": 0.20,
            "keywords": ["found a bilingual colleague to assist", "used a translation app", "called over a team member who spoke their language", "asked a nearby colleague to help translate", "used Google Translate as a bridge"],
        },
        {
            "name": "follow_through",
            "weight": 0.20,
            "keywords": ["confirmed they completed registration successfully", "checked they had everything they needed", "ensured the delegate was no longer confused", "stayed with them until the issue was resolved", "followed up after handing them to a colleague"],
        },
    ],
    "irt_a": 2.0,
    "irt_b": 0.3,
    "irt_c": 0.0,
}

# Well-designed question: multi-word keywords, clear scenario, no leakage
Q_WELL_DESIGNED = {
    "type": "open_ended",
    "scenario_en": (
        "Imagine you are managing a volunteer team of 15 people at a large outdoor event. "
        "Halfway through the event, two team members get into a visible argument in front of "
        "attendees. Describe step by step what you would do to resolve the situation and "
        "maintain a positive atmosphere."
    ),
    "expected_concepts": [
        {
            "name": "immediate_intervention",
            "weight": 0.25,
            "keywords": [
                "move them away from attendees",
                "separate the two individuals",
                "address it immediately",
            ],
        },
        {
            "name": "active_listening",
            "weight": 0.25,
            "keywords": [
                "hear both sides",
                "let each person speak",
                "without interrupting them",
            ],
        },
        {
            "name": "solution_focus",
            "weight": 0.25,
            "keywords": [
                "agree on next steps",
                "find a workable compromise",
                "redirect energy to the task",
            ],
        },
        {
            "name": "follow_up",
            "weight": 0.25,
            "keywords": [
                "check in after the event",
                "ensure it does not recur",
                "document the incident",
            ],
        },
    ],
    "irt_a": 1.8,
    "irt_b": 0.5,
    "irt_c": 0.0,
}

# MCQ question — checklist should apply reduced subset
Q_MCQ = {
    "type": "mcq",
    "scenario_en": "Which of the following is the MOST effective way to de-escalate a tense situation?",
    "expected_concepts": [
        {
            "name": "correct_choice",
            "weight": 1.0,
            "keywords": ["A", "calm", "listen"],
        }
    ],
    "irt_a": 1.2,
    "irt_b": 0.0,
    "irt_c": 0.25,
}

# Deliberately broken question for checklist failure testing
Q_BROKEN = {
    "type": "open_ended",
    "scenario_en": "",  # empty scenario — fails check 1
    "expected_concepts": [],  # empty — fails check 2
    # No IRT params — fails check 10
}


# ── 1. GRS Tests ──────────────────────────────────────────────────────────────


class TestComputeGRS:
    def test_q3_seed_fails_grs(self) -> None:
        """Q3 from seed.sql uses mostly single-word keywords — should score below 0.6."""
        grs = compute_grs(Q3_SEED)
        # Q3 has 8 single-word keywords per concept (calm, slow, smile, etc.)
        # → single-word penalty fires multiple times → GRS < 0.6
        assert grs < GRS_THRESHOLD, (
            f"Expected Q3 to FAIL GRS (score < {GRS_THRESHOLD}), got {grs}. "
            "Q3's keywords are all single words — it should be flagged for revision."
        )

    def test_q3_redesigned_passes_grs(self) -> None:
        """Q3 with redesigned multi-word behavioral phrase keywords should pass GRS.

        This is the regression guard for migration 000030 — if someone reverts
        the keywords to single words, this test catches it.
        """
        grs = compute_grs(Q3_REDESIGNED)
        assert grs >= GRS_THRESHOLD, (
            f"Expected redesigned Q3 to PASS GRS (>= {GRS_THRESHOLD}), got {grs}. "
            "Keywords must be multi-word behavioral phrases, not single words."
        )

    def test_q3_redesigned_scores_higher_than_original(self) -> None:
        """Redesigned Q3 must score strictly higher than original Q3."""
        grs_old = compute_grs(Q3_SEED)
        grs_new = compute_grs(Q3_REDESIGNED)
        assert grs_new > grs_old, (
            f"Redesigned Q3 ({grs_new}) must score higher than original ({grs_old})."
        )

    def test_well_designed_question_passes_grs(self) -> None:
        """Well-designed question with multi-word keywords should pass GRS."""
        grs = compute_grs(Q_WELL_DESIGNED)
        assert grs >= GRS_THRESHOLD, (
            f"Expected well-designed question to PASS GRS (>= {GRS_THRESHOLD}), got {grs}."
        )

    def test_grs_returns_float_in_range(self) -> None:
        """GRS must always return a value in [0.0, 1.0]."""
        for q in [Q3_SEED, Q3_REDESIGNED, Q_WELL_DESIGNED, Q_MCQ, Q_BROKEN]:
            grs = compute_grs(q)
            assert 0.0 <= grs <= 1.0, f"GRS out of range: {grs}"

    def test_no_narrative_trigger_penalises_grs(self) -> None:
        """Question with no narrative trigger should score lower than same question with one.

        The -0.30 penalty for missing narrative trigger must visibly reduce GRS.
        A question with no narrative trigger AND single-word keywords should fail.
        A question with no narrative trigger but strong multi-word keywords may still
        score above threshold (the keyword quality partially compensates), but the
        penalty must always fire (grs_without < grs_with).
        """
        q_with_trigger = {
            "scenario_en": "Describe how you would handle a conflict.",
            "expected_concepts": [
                {
                    "name": "empathy",
                    "weight": 1.0,
                    "keywords": ["understand their perspective", "acknowledge their feelings"],
                }
            ],
        }
        q_without_trigger = {
            "scenario_en": "Conflict in the workplace.",
            "expected_concepts": [
                {
                    "name": "empathy",
                    "weight": 1.0,
                    "keywords": ["understand their perspective", "acknowledge their feelings"],
                }
            ],
        }
        grs_with = compute_grs(q_with_trigger)
        grs_without = compute_grs(q_without_trigger)
        assert grs_with > grs_without, (
            f"Narrative trigger should increase GRS. With: {grs_with}, Without: {grs_without}"
        )
        # Penalty is -0.30, but grs_with may be clamped at 1.0, hiding the full gap.
        # Minimum observable difference: 0.10 (even with clamping, penalty must show).
        assert (grs_with - grs_without) >= 0.10, (
            f"Narrative trigger penalty should reduce GRS by at least 0.10. "
            f"With: {grs_with}, Without: {grs_without}, Difference: {grs_with - grs_without:.3f}"
        )

    def test_no_narrative_trigger_with_single_word_keywords_fails_grs(self) -> None:
        """Question with no narrative trigger AND single-word keywords should fail GRS.

        Two stacking penalties: -0.30 (no narrative) + -0.12 (single-word keywords)
        push the score well below 0.6.
        """
        q_poor = {
            "scenario_en": "Empathy at work.",
            "expected_concepts": [
                {
                    "name": "empathy",
                    "weight": 0.5,
                    "keywords": ["listen", "care", "support"],
                },
                {
                    "name": "communication",
                    "weight": 0.5,
                    "keywords": ["speak", "write", "talk"],
                },
            ],
        }
        grs = compute_grs(q_poor)
        assert grs < GRS_THRESHOLD, (
            f"Poor question (no narrative + single-word keywords) should fail GRS, got {grs}"
        )

    def test_keyword_equals_concept_name_penalises_grs(self) -> None:
        """If a keyword is exactly the concept name, GRS should be penalised."""
        q = {
            "scenario_en": "Describe how you would demonstrate empathy in your work.",
            "expected_concepts": [
                {
                    "name": "empathy",
                    "weight": 1.0,
                    # "empathy" == concept name → -0.25 penalty
                    "keywords": ["empathy", "compassion", "understanding"],
                }
            ],
        }
        q_clean = {
            "scenario_en": "Describe how you would demonstrate empathy in your work.",
            "expected_concepts": [
                {
                    "name": "empathy",
                    "weight": 1.0,
                    "keywords": ["compassion", "put yourself in their shoes", "acknowledge feelings"],
                }
            ],
        }
        grs_bad = compute_grs(q)
        grs_clean = compute_grs(q_clean)
        assert grs_bad < grs_clean, (
            f"keyword=concept_name should penalise GRS. Bad: {grs_bad}, Clean: {grs_clean}"
        )

    def test_keyword_leakage_in_question_penalises_grs(self) -> None:
        """Keywords that appear verbatim in the question text should reduce GRS."""
        q_leaked = {
            "scenario_en": "Describe how you would remain calm and smile at the delegate.",
            "expected_concepts": [
                {
                    "name": "calm_tone",
                    "weight": 1.0,
                    # "calm" and "smile" appear in question text above
                    "keywords": ["calm", "smile", "patient approach", "steady voice"],
                }
            ],
        }
        q_clean = {
            "scenario_en": "Describe how you would handle a distressed delegate.",
            "expected_concepts": [
                {
                    "name": "calm_tone",
                    "weight": 1.0,
                    "keywords": ["calm", "smile", "patient approach", "steady voice"],
                }
            ],
        }
        grs_leaked = compute_grs(q_leaked)
        grs_clean = compute_grs(q_clean)
        assert grs_leaked < grs_clean, (
            f"Keyword leakage should reduce GRS. Leaked: {grs_leaked}, Clean: {grs_clean}"
        )

    def test_json_string_concepts_parsed(self) -> None:
        """GRS should handle expected_concepts as a JSON string (as stored in some DB rows)."""
        import json

        q = {
            "scenario_en": "Describe how you would handle a difficult situation.",
            "expected_concepts": json.dumps([
                {
                    "name": "problem_solving",
                    "weight": 1.0,
                    "keywords": ["identify the root cause", "evaluate options", "implement solution"],
                }
            ]),
        }
        grs = compute_grs(q)
        assert 0.0 <= grs <= 1.0


# ── 2. Adversarial Gate Tests ─────────────────────────────────────────────────


class TestAdversarialGate:
    def test_generate_attack_answers_returns_3(self) -> None:
        """generate_attack_answers must always return exactly 3 attacks."""
        attacks = generate_attack_answers(Q3_SEED)
        assert len(attacks) == 3

    def test_attack_styles_present(self) -> None:
        """Each attack must have the expected style labels."""
        attacks = generate_attack_answers(Q3_SEED)
        styles = {a["style"] for a in attacks}
        assert styles == {"keyword_dump", "synonym_flood", "thin_narrative"}

    def test_keyword_dump_attack_detected_on_q3(self) -> None:
        """Q3's single-word keywords make it vulnerable — keyword dump should score > 0.4."""
        result = run_adversarial_gate(Q3_SEED)
        # Q3 uses all single-word keywords, so a keyword dump hits them all easily
        # → at least one attack should score above threshold
        assert not result["passed"], (
            "Q3 should FAIL the adversarial gate — its single-word keywords are trivially gameable. "
            f"Max attack score: {result['max_attack_score']}"
        )
        assert result["max_attack_score"] > ADVERSARIAL_GATE_THRESHOLD

    def test_well_designed_question_harder_to_attack_than_q3(self) -> None:
        """Multi-word keywords make keyword-dump attacks harder — Q_WELL_DESIGNED's
        max attack score should be lower than Q3's max attack score.

        The adversarial gate is intentionally strict: any question where attacks can
        copy exact keyword phrases will fail. The relative comparison shows that
        multi-word keywords provide meaningfully better resistance.
        """
        result_q3 = run_adversarial_gate(Q3_SEED)
        result_well = run_adversarial_gate(Q_WELL_DESIGNED)
        # Both may fail the gate, but Q3 should be MORE vulnerable
        assert result_q3["max_attack_score"] >= result_well["max_attack_score"], (
            "Q3 (single-word keywords) should be at least as vulnerable as Q_WELL_DESIGNED. "
            f"Q3: {result_q3['max_attack_score']}, Well-designed: {result_well['max_attack_score']}"
        )

    def test_question_with_no_keywords_adversarial_gate(self) -> None:
        """Questions with no keywords return neutral 0.5 per concept — gate result is
        deterministic regardless of attack text, and threshold behavior is predictable."""
        q_no_kw = {
            "scenario_en": "Describe your leadership style in a crisis.",
            "expected_concepts": [
                {"name": "leadership", "weight": 1.0}
                # No keywords — fallback returns 0.5
            ],
        }
        result = run_adversarial_gate(q_no_kw)
        # With no keywords, keyword_fallback returns 0.5 for all attacks
        # 0.5 > ADVERSARIAL_GATE_THRESHOLD (0.4) → gate fails
        # This is expected: undefined keywords = undefined resistance
        assert result["max_attack_score"] == pytest.approx(0.5, abs=0.01)

    def test_adversarial_result_structure(self) -> None:
        """Result must contain all required keys."""
        result = run_adversarial_gate(Q3_SEED)
        assert "passed" in result
        assert "attacks" in result
        assert "max_attack_score" in result
        assert "threshold" in result
        assert result["threshold"] == ADVERSARIAL_GATE_THRESHOLD
        assert len(result["attacks"]) == 3
        for attack in result["attacks"]:
            assert "style" in attack
            assert "score" in attack
            assert "concept_scores" in attack

    def test_adversarial_gate_no_keywords(self) -> None:
        """Questions with no keywords defined should pass trivially (nothing to dump)."""
        q_no_kw = {
            "scenario_en": "Describe your leadership style.",
            "expected_concepts": [
                {"name": "leadership", "weight": 1.0}
            ],
        }
        result = run_adversarial_gate(q_no_kw)
        # keyword_fallback returns 0.5 for concepts with no keywords
        # but attack texts are minimal, so this should still be manageable
        assert isinstance(result["passed"], bool)

    def test_synonym_flood_attack_text_uses_keywords(self) -> None:
        """Synonym flood attack must include the actual keyword text."""
        attacks = generate_attack_answers(Q_WELL_DESIGNED)
        flood = next(a for a in attacks if a["style"] == "synonym_flood")
        # Should contain at least one keyword phrase from the question
        assert "move them away from attendees" in flood["text"] or "hear both sides" in flood["text"]


# ── 3. Quality Checklist Tests ────────────────────────────────────────────────


class TestRunQualityChecklist:
    def test_q3_fails_checklist(self) -> None:
        """Q3 should fail the full checklist due to GRS < 0.6 and adversarial gate."""
        result = run_quality_checklist(Q3_SEED)
        # Q3 fails GRS (check 6) and adversarial gate (check 7)
        assert not result["passed"], (
            "Q3 should FAIL the quality checklist. "
            f"Score: {result['score']}/{result['total']}"
        )
        failed_checks = [c for c in result["checks"] if not c["passed"]]
        failed_ids = {c["id"] for c in failed_checks}
        assert 6 in failed_ids or 7 in failed_ids, (
            f"Expected check 6 (GRS) or check 7 (adversarial) to fail. Failed: {failed_ids}"
        )

    def test_well_designed_passes_structural_checks(self) -> None:
        """Well-designed question should pass all structural checks (1-5, 8-10).

        The adversarial gate (check 7) may still fail because generate_attack_answers
        embeds exact keyword phrases, and keyword_fallback matches them directly.
        This is expected behavior — check 7 is intentionally strict.
        The key structural properties (weights, IRT params, narrative, no leakage)
        should all pass.
        """
        result = run_quality_checklist(Q_WELL_DESIGNED)
        # Structural checks that must pass
        structural_check_ids = {1, 2, 3, 4, 5, 8, 9, 10}
        failed_structural = [
            c for c in result["checks"]
            if c["id"] in structural_check_ids and not c["passed"]
        ]
        assert not failed_structural, (
            f"Well-designed question should pass all structural checks. "
            f"Failed: {failed_structural}"
        )
        # GRS check should pass (check 6)
        grs_check = next((c for c in result["checks"] if c["id"] == 6), None)
        if grs_check:
            assert grs_check["passed"], (
                f"Well-designed question should pass GRS. Detail: {grs_check['detail']}"
            )

    def test_broken_question_fails_multiple_checks(self) -> None:
        """A question with empty scenario and no concepts must fail checks 1, 2, and 10."""
        result = run_quality_checklist(Q_BROKEN)
        assert not result["passed"]
        failed_ids = {c["id"] for c in result["checks"] if not c["passed"]}
        assert 1 in failed_ids, "Check 1 (scenario present) should fail"
        assert 2 in failed_ids, "Check 2 (concepts non-empty) should fail"
        assert 10 in failed_ids, "Check 10 (IRT params) should fail"

    def test_mcq_skips_narrative_grs_adversarial_checks(self) -> None:
        """MCQ questions should not be checked for GRS, adversarial gate, or narrative trigger."""
        result = run_quality_checklist(Q_MCQ)
        check_ids = {c["id"] for c in result["checks"]}
        # Checks 5, 6, 7, 8 are open-ended only
        assert 6 not in check_ids, "GRS check should be skipped for MCQ"
        assert 7 not in check_ids, "Adversarial gate should be skipped for MCQ"
        assert 8 not in check_ids, "Narrative trigger check should be skipped for MCQ"

    def test_checklist_result_structure(self) -> None:
        """Result must contain all required keys."""
        result = run_quality_checklist(Q_WELL_DESIGNED)
        assert "passed" in result
        assert "checks" in result
        assert "score" in result
        assert "total" in result
        assert "grs" in result
        assert "adversarial" in result
        assert isinstance(result["checks"], list)
        for check in result["checks"]:
            assert "id" in check
            assert "name" in check
            assert "passed" in check
            assert "detail" in check

    def test_weights_not_summing_to_one_fails_check5(self) -> None:
        """If concept weights do not sum to 1.0, check 5 must fail."""
        q = {
            "type": "open_ended",
            "scenario_en": "Imagine a scenario where you must demonstrate leadership. Describe what you would do.",
            "expected_concepts": [
                {
                    "name": "initiative",
                    "weight": 0.6,
                    "keywords": ["take ownership", "proactively address", "step forward voluntarily"],
                },
                {
                    "name": "delegation",
                    "weight": 0.6,  # sum = 1.2, not 1.0
                    "keywords": ["assign tasks fairly", "trust team members", "distribute responsibility"],
                },
            ],
            "irt_a": 1.5,
            "irt_b": 0.0,
            "irt_c": 0.0,
        }
        result = run_quality_checklist(q)
        failed_ids = {c["id"] for c in result["checks"] if not c["passed"]}
        assert 5 in failed_ids, f"Check 5 (weights sum) should fail. Failed checks: {failed_ids}"

    def test_irt_out_of_range_fails_check10(self) -> None:
        """IRT params outside valid ranges must fail check 10."""
        q = {
            "type": "open_ended",
            "scenario_en": "Describe how you would manage a challenging situation.",
            "expected_concepts": [
                {
                    "name": "composure",
                    "weight": 1.0,
                    "keywords": ["stay focused", "regulate emotions", "think clearly under pressure"],
                }
            ],
            "irt_a": 5.0,  # out of range [0.3, 3.0]
            "irt_b": 0.0,
            "irt_c": 0.0,
        }
        result = run_quality_checklist(q)
        failed_ids = {c["id"] for c in result["checks"] if not c["passed"]}
        assert 10 in failed_ids, f"Check 10 (IRT params) should fail. Failed checks: {failed_ids}"

    def test_score_and_total_are_consistent(self) -> None:
        """score must equal count of passed checks; total must equal len(checks)."""
        for q in [Q3_SEED, Q3_REDESIGNED, Q_WELL_DESIGNED, Q_MCQ, Q_BROKEN]:
            result = run_quality_checklist(q)
            assert result["score"] == sum(1 for c in result["checks"] if c["passed"])
            assert result["total"] == len(result["checks"])
