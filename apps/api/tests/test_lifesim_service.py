"""Unit tests for app.services.lifesim — pure functions only.

Covers:
  - apply_stat_boosts_from_verified_skills
  - apply_consequences_to_stats (clamping)
  - filter_pool_for_user (age + required_stats filtering)

DB-side helpers (query_event_pool, emit_lifesim_*) are covered by integration
tests in a later iteration that wires the router.
"""

from __future__ import annotations

from app.services.lifesim import (
    apply_consequences_to_stats,
    apply_stat_boosts_from_verified_skills,
    filter_pool_for_user,
)

# ── apply_stat_boosts_from_verified_skills ────────────────────────────────


def test_stat_boosts_empty_skills():
    assert apply_stat_boosts_from_verified_skills([]) == {
        "social": 0.0,
        "intelligence": 0.0,
        "energy": 0.0,
        "happiness": 0.0,
    }


def test_stat_boosts_single_communication():
    skills = [{"slug": "communication", "aura_score": 80}]
    boosts = apply_stat_boosts_from_verified_skills(skills)
    # communication → social * 0.10
    assert boosts["social"] == 8.0
    assert boosts["intelligence"] == 0.0


def test_stat_boosts_leadership_splits_across_two_stats():
    skills = [{"slug": "leadership", "aura_score": 100}]
    boosts = apply_stat_boosts_from_verified_skills(skills)
    # leadership → social * 0.05 + happiness * 0.03
    assert boosts["social"] == 5.0
    assert boosts["happiness"] == 3.0


def test_stat_boosts_zero_score_ignored():
    skills = [{"slug": "communication", "aura_score": 0}]
    boosts = apply_stat_boosts_from_verified_skills(skills)
    assert boosts["social"] == 0.0


def test_stat_boosts_unknown_slug_ignored():
    skills = [{"slug": "unknown_competency", "aura_score": 100}]
    boosts = apply_stat_boosts_from_verified_skills(skills)
    assert boosts == {"social": 0.0, "intelligence": 0.0, "energy": 0.0, "happiness": 0.0}


def test_stat_boosts_multiple_skills_accumulate():
    skills = [
        {"slug": "communication", "aura_score": 50},
        {"slug": "leadership", "aura_score": 60},
    ]
    boosts = apply_stat_boosts_from_verified_skills(skills)
    # social = 50*0.10 + 60*0.05 = 5 + 3 = 8
    assert boosts["social"] == 8.0
    # happiness = 60*0.03 = 1.8
    assert abs(boosts["happiness"] - 1.8) < 0.001


# ── apply_consequences_to_stats ────────────────────────────────────────────


def test_consequences_basic_add():
    stats = {"health": 50, "social": 30}
    new = apply_consequences_to_stats(stats, {"health": 10, "social": 5})
    assert new["health"] == 60
    assert new["social"] == 35


def test_consequences_clamp_top():
    stats = {"health": 95}
    new = apply_consequences_to_stats(stats, {"health": 20})
    # Clamped to 100
    assert new["health"] == 100


def test_consequences_clamp_bottom():
    stats = {"energy": 5}
    new = apply_consequences_to_stats(stats, {"energy": -20})
    assert new["energy"] == 0


def test_consequences_money_unbounded():
    stats = {"money": 50}
    new = apply_consequences_to_stats(stats, {"money": 200})
    # Money not clamped at 100 (it's currency, not a stat)
    assert new["money"] == 250


def test_consequences_money_can_go_negative():
    stats = {"money": 10}
    new = apply_consequences_to_stats(stats, {"money": -50})
    assert new["money"] == -40


def test_consequences_missing_stat_starts_at_zero():
    stats = {}
    new = apply_consequences_to_stats(stats, {"happiness": 20})
    assert new["happiness"] == 20


# ── filter_pool_for_user ────────────────────────────────────────────────────

_SAMPLE_POOL = [
    {
        "id": "e1",
        "is_active": True,
        "min_age": 18,
        "max_age": 25,
        "required_stats": {},
    },
    {
        "id": "e2",
        "is_active": True,
        "min_age": 30,
        "max_age": 50,
        "required_stats": {"intelligence": 60},
    },
    {
        "id": "e3",
        "is_active": False,  # inactive — must be filtered out
        "min_age": 20,
        "max_age": 40,
        "required_stats": {},
    },
    {
        "id": "e4",
        "is_active": True,
        "min_age": None,
        "max_age": None,
        "required_stats": {"social": 30, "energy": 20},
    },
]


def test_filter_pool_age_match():
    out = filter_pool_for_user(_SAMPLE_POOL, age=22, stats={})
    ids = {e["id"] for e in out}
    # e1 matches (18-25), e4 matches (no age limit, no stat req -> but needs social+energy)
    # since stats empty, e4 should be filtered by required_stats
    assert "e1" in ids
    assert "e2" not in ids  # age 22 < min 30
    assert "e3" not in ids  # inactive
    assert "e4" not in ids  # missing required social/energy


def test_filter_pool_required_stats_met():
    out = filter_pool_for_user(_SAMPLE_POOL, age=35, stats={"intelligence": 70, "social": 50, "energy": 30})
    ids = {e["id"] for e in out}
    assert "e2" in ids  # intelligence 70 >= 60
    assert "e4" in ids  # social 50 >= 30 and energy 30 >= 20


def test_filter_pool_required_stats_not_met():
    out = filter_pool_for_user(_SAMPLE_POOL, age=35, stats={"intelligence": 40})
    ids = {e["id"] for e in out}
    assert "e2" not in ids  # intelligence 40 < 60


def test_filter_pool_no_age_limits():
    # e4 has no age limits — should match any age if stats OK
    out = filter_pool_for_user(_SAMPLE_POOL, age=100, stats={"social": 99, "energy": 99})
    ids = {e["id"] for e in out}
    assert "e4" in ids
    assert "e1" not in ids  # age 100 > max 25
    assert "e2" not in ids  # age 100 > max 50


def test_filter_pool_inactive_always_excluded():
    out = filter_pool_for_user(_SAMPLE_POOL, age=25, stats={})
    ids = {e["id"] for e in out}
    assert "e3" not in ids
