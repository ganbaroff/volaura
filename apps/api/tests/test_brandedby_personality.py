"""Tests for app.services.brandedby_personality — pure function coverage."""

from __future__ import annotations

import pytest

from app.services.brandedby_personality import (
    AURA_SKILL_LABELS,
    BADGE_TIERS,
    _badge_tier_from_score,
    _build_character_context,
    _build_fallback_personality,
)


class TestBadgeTierFromScore:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (100, "platinum"),
            (90, "platinum"),
            (89.9, "gold"),
            (75, "gold"),
            (74.9, "silver"),
            (60, "silver"),
            (59.9, "bronze"),
            (40, "bronze"),
            (39.9, None),
            (0, None),
            (-1, None),
        ],
    )
    def test_thresholds(self, score: float, expected: str | None):
        assert _badge_tier_from_score(score) == expected

    def test_none_input(self):
        assert _badge_tier_from_score(None) is None


class TestBuildCharacterContext:
    def test_empty_state(self):
        ctx = _build_character_context({})
        assert "Total XP earned: 0" in ctx
        assert "Crystal balance: 0" in ctx
        assert "No verified competencies yet" in ctx

    def test_with_xp_and_crystals(self):
        ctx = _build_character_context({"xp_total": 500, "crystal_balance": 120})
        assert "Total XP earned: 500" in ctx
        assert "Crystal balance: 120" in ctx

    def test_streak_shown_when_positive(self):
        ctx = _build_character_context({"login_streak": 7})
        assert "Current login streak: 7 days" in ctx

    def test_streak_hidden_when_zero(self):
        ctx = _build_character_context({"login_streak": 0})
        assert "login streak" not in ctx

    def test_verified_skills_with_aura(self):
        state = {
            "verified_skills": [
                {"slug": "communication", "aura_score": 85.3, "badge_tier": "gold"},
            ],
        }
        ctx = _build_character_context(state)
        assert "Communication" in ctx
        assert "AURA 85.3/100" in ctx
        assert "high-performing" in ctx

    def test_verified_skills_without_aura(self):
        state = {
            "verified_skills": [
                {"slug": "leadership", "aura_score": None},
            ],
        }
        ctx = _build_character_context(state)
        assert "Leadership" in ctx
        assert "verified" in ctx

    def test_unknown_slug_titlecased(self):
        state = {
            "verified_skills": [
                {"slug": "data_science", "aura_score": 72.0},
            ],
        }
        ctx = _build_character_context(state)
        assert "Data Science" in ctx

    def test_badge_tier_inferred_from_score(self):
        state = {
            "verified_skills": [
                {"slug": "reliability", "aura_score": 92.0},
            ],
        }
        ctx = _build_character_context(state)
        assert "top-tier" in ctx


class TestBuildFallbackPersonality:
    def test_no_skills(self):
        result = _build_fallback_personality("Alice", {"xp_total": 50})
        assert "Alice" in result
        assert "50 XP" in result
        assert "open to" in result

    def test_single_skill(self):
        state = {
            "xp_total": 200,
            "verified_skills": [
                {"slug": "communication", "aura_score": 80},
            ],
        }
        result = _build_fallback_personality("Bob", state)
        assert "Bob" in result
        assert "Communication" in result
        assert "active" in result

    def test_multiple_skills_joined(self):
        state = {
            "xp_total": 600,
            "verified_skills": [
                {"slug": "leadership", "aura_score": 90},
                {"slug": "reliability", "aura_score": 85},
                {"slug": "communication", "aura_score": 70},
            ],
        }
        result = _build_fallback_personality("Carol", state)
        assert "experienced" in result
        assert " and " in result

    def test_emerging_level(self):
        state = {"xp_total": 10, "verified_skills": [{"slug": "adaptability", "aura_score": 50}]}
        result = _build_fallback_personality("Dan", state)
        assert "emerging" in result

    def test_skills_sorted_by_score(self):
        state = {
            "xp_total": 100,
            "verified_skills": [
                {"slug": "adaptability", "aura_score": 40},
                {"slug": "leadership", "aura_score": 95},
                {"slug": "communication", "aura_score": 60},
                {"slug": "reliability", "aura_score": 88},
            ],
        }
        result = _build_fallback_personality("Eve", state)
        assert "Leadership" in result
        assert "Reliability" in result
        assert "Communication" in result
        assert "Adaptability" not in result


class TestConstants:
    def test_all_8_competencies_in_labels(self):
        expected = {
            "communication", "reliability", "english_proficiency", "leadership",
            "event_performance", "tech_literacy", "adaptability", "empathy_safeguarding",
        }
        assert set(AURA_SKILL_LABELS.keys()) == expected

    def test_badge_tiers_complete(self):
        assert set(BADGE_TIERS.keys()) == {"platinum", "gold", "silver", "bronze"}
        for _tier, (name, desc) in BADGE_TIERS.items():
            assert isinstance(name, str)
            assert isinstance(desc, str)
