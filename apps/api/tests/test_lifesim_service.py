"""Unit tests for app.services.lifesim — pure functions only.

Covers:
  - apply_stat_boosts_from_verified_skills
  - apply_consequences_to_stats (clamping)
  - filter_pool_for_user (age + required_stats filtering)
  - _extract_category_bias (E3 atlas_learnings bias)
  - pick_event_with_bias (E3 weighted selection)

DB-side helpers (query_event_pool, emit_lifesim_*) are covered by integration
tests in a later iteration that wires the router.
"""

from __future__ import annotations

import pytest

from app.services.lifesim import (
    _extract_category_bias,
    apply_consequences_to_stats,
    apply_stat_boosts_from_verified_skills,
    filter_pool_for_user,
    pick_event_with_bias,
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


# ── _extract_category_bias ────────────────────────────────────────────────────


def test_extract_bias_empty_learnings():
    assert _extract_category_bias([]) == {}


def test_extract_bias_finance_keyword():
    learnings = [{"category": "preference", "content": "финансовую независимость", "emotional_intensity": 3.0}]
    bias = _extract_category_bias(learnings)
    # "финанс" maps to finance, "независимост" maps to finance — two hits
    assert "finance" in bias
    assert bias["finance"] > 0.0


def test_extract_bias_high_intensity_bigger_than_low():
    keyword = "карьер"
    high = _extract_category_bias([{"content": keyword, "emotional_intensity": 5.0}])
    low = _extract_category_bias([{"content": keyword, "emotional_intensity": 1.0}])
    assert high.get("career", 0.0) > low.get("career", 0.0)


def test_extract_bias_multiple_learnings_accumulate():
    learnings = [
        {"content": "карьер", "emotional_intensity": 2.0},
        {"content": "карьер", "emotional_intensity": 2.0},
    ]
    single = _extract_category_bias([{"content": "карьер", "emotional_intensity": 2.0}])
    both = _extract_category_bias(learnings)
    assert both.get("career", 0.0) > single.get("career", 0.0)


def test_extract_bias_unknown_keyword_returns_empty():
    learnings = [{"content": "xyzzy foobar quux", "emotional_intensity": 5.0}]
    assert _extract_category_bias(learnings) == {}


def test_extract_bias_multiple_categories_from_one_learning():
    # "деньг" → finance, "образован" → education in same content
    learnings = [{"content": "деньги и образование", "emotional_intensity": 2.0}]
    bias = _extract_category_bias(learnings)
    assert "finance" in bias
    assert "education" in bias


def test_extract_bias_intensity_zero_gives_min_boost():
    learnings = [{"content": "здоровье", "emotional_intensity": 0.0}]
    bias = _extract_category_bias(learnings)
    # At intensity=0: weight_boost = 0.5 + (0/5)*1.5 = 0.5
    assert abs(bias.get("health", 0.0) - 0.5) < 0.001


def test_extract_bias_intensity_five_gives_max_boost():
    learnings = [{"content": "здоровье", "emotional_intensity": 5.0}]
    bias = _extract_category_bias(learnings)
    # At intensity=5: weight_boost = 0.5 + (5/5)*1.5 = 2.0
    assert abs(bias.get("health", 0.0) - 2.0) < 0.001


# ── pick_event_with_bias ──────────────────────────────────────────────────────


def test_pick_event_empty_raises():
    with pytest.raises((IndexError, ValueError)):
        pick_event_with_bias([], {})


def test_pick_event_single_always_returned():
    event = {"id": "solo", "category": "career"}
    result = pick_event_with_bias([event], {})
    assert result == event


def test_pick_event_single_with_bias_still_returns_it():
    event = {"id": "solo", "category": "education"}
    result = pick_event_with_bias([event], {"education": 5.0})
    assert result == event


def test_pick_event_biased_category_dominates_statistically():
    biased = {"id": "biased", "category": "finance"}
    other = {"id": "other", "category": "hobby"}
    eligible = [biased, other]
    bias = {"finance": 99.0}  # heavy bias
    counts = {"biased": 0, "other": 0}
    for _ in range(100):
        result = pick_event_with_bias(eligible, bias)
        counts[result["id"]] += 1
    # With weight ratio 100:1, biased event must appear far more than 60 times
    assert counts["biased"] > 60


def test_pick_event_empty_bias_uniform():
    events = [{"id": str(i), "category": "education"} for i in range(10)]
    counts: dict[str, int] = {e["id"]: 0 for e in events}
    for _ in range(1000):
        result = pick_event_with_bias(events, {})
        counts[result["id"]] += 1
    # Each event should appear roughly 100 times; no event should be absent
    assert all(c > 0 for c in counts.values())


def test_pick_event_no_category_key_uses_default_weight():
    # Event with no "category" key should get default weight 1.0 (no KeyError)
    no_cat = {"id": "nc"}
    with_cat = {"id": "wc", "category": "finance"}
    bias = {"finance": 0.0}  # both effectively weight 1.0
    seen = set()
    for _ in range(200):
        seen.add(pick_event_with_bias([no_cat, with_cat], bias)["id"])
    # Both events must appear — no crash on missing category key
    assert "nc" in seen
    assert "wc" in seen
