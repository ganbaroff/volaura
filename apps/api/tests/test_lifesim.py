"""Unit tests for lifesim router schemas and constants.

Covers: ChoicePayload, PurchasePayload, FeedItem, FeedResponse,
NextChoiceResponse, ChoiceResponse, PurchaseResponse validation,
plus _CRYSTAL_SHOP catalogue integrity.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.routers.lifesim import (
    _CRYSTAL_SHOP,
    ChoicePayload,
    ChoiceResponse,
    FeedItem,
    FeedResponse,
    NextChoiceResponse,
    PurchasePayload,
    PurchaseResponse,
)

# ── _CRYSTAL_SHOP catalogue ──────────────────────────────────────────────


class TestCrystalShop:
    def test_has_four_items(self):
        assert len(_CRYSTAL_SHOP) == 4

    def test_all_items_have_cost_and_boost(self):
        for item_id, item in _CRYSTAL_SHOP.items():
            assert "cost" in item, f"{item_id} missing cost"
            assert "boost" in item, f"{item_id} missing boost"
            assert isinstance(item["cost"], (int, float))
            assert isinstance(item["boost"], dict)
            assert item["cost"] > 0

    def test_known_item_ids(self):
        expected = {
            "premium_training_course",
            "social_event_ticket",
            "health_insurance",
            "career_coach",
        }
        assert set(_CRYSTAL_SHOP.keys()) == expected

    def test_boost_values_are_positive(self):
        for item_id, item in _CRYSTAL_SHOP.items():
            for stat, val in item["boost"].items():
                assert val > 0, f"{item_id}.boost.{stat} must be positive"


# ── ChoicePayload ─────────────────────────────────────────────────────────


class TestChoicePayload:
    def test_valid(self):
        p = ChoicePayload(event_id="ev-001", choice_index=0)
        assert p.event_id == "ev-001"
        assert p.choice_index == 0
        assert p.stats_before == {}

    def test_with_stats_before(self):
        p = ChoicePayload(
            event_id="ev-002",
            choice_index=3,
            stats_before={"health": 80.0, "money": -10.0},
        )
        assert p.stats_before["health"] == 80.0

    def test_event_id_empty_rejected(self):
        with pytest.raises(ValidationError):
            ChoicePayload(event_id="", choice_index=0)

    def test_event_id_too_long_rejected(self):
        with pytest.raises(ValidationError):
            ChoicePayload(event_id="x" * 65, choice_index=0)

    def test_choice_index_negative_rejected(self):
        with pytest.raises(ValidationError):
            ChoicePayload(event_id="ev-001", choice_index=-1)

    def test_choice_index_over_9_rejected(self):
        with pytest.raises(ValidationError):
            ChoicePayload(event_id="ev-001", choice_index=10)

    def test_choice_index_boundary_9_accepted(self):
        p = ChoicePayload(event_id="ev-001", choice_index=9)
        assert p.choice_index == 9

    def test_missing_event_id_rejected(self):
        with pytest.raises(ValidationError):
            ChoicePayload(choice_index=0)


# ── PurchasePayload ───────────────────────────────────────────────────────


class TestPurchasePayload:
    def test_valid(self):
        p = PurchasePayload(shop_item="health_insurance", current_crystals=200)
        assert p.shop_item == "health_insurance"
        assert p.current_crystals == 200

    def test_shop_item_empty_rejected(self):
        with pytest.raises(ValidationError):
            PurchasePayload(shop_item="", current_crystals=100)

    def test_shop_item_too_long_rejected(self):
        with pytest.raises(ValidationError):
            PurchasePayload(shop_item="x" * 65, current_crystals=100)

    def test_negative_crystals_rejected(self):
        with pytest.raises(ValidationError):
            PurchasePayload(shop_item="career_coach", current_crystals=-1)

    def test_zero_crystals_accepted(self):
        p = PurchasePayload(shop_item="career_coach", current_crystals=0)
        assert p.current_crystals == 0


# ── FeedItem ──────────────────────────────────────────────────────────────


class TestFeedItem:
    def test_valid(self):
        fi = FeedItem(
            id="abc-123",
            event_type="lifesim_choice",
            payload={"event_id": "ev-001"},
            created_at="2026-04-18T00:00:00Z",
        )
        assert fi.event_type == "lifesim_choice"

    def test_empty_payload_accepted(self):
        fi = FeedItem(
            id="abc",
            event_type="lifesim_crystal_spent",
            payload={},
            created_at="2026-04-18",
        )
        assert fi.payload == {}


# ── FeedResponse ──────────────────────────────────────────────────────────


class TestFeedResponse:
    def test_empty_data(self):
        r = FeedResponse(data=[])
        assert r.data == []

    def test_with_items(self):
        items = [
            FeedItem(
                id=f"id-{i}",
                event_type="lifesim_choice",
                payload={},
                created_at="2026-04-18",
            )
            for i in range(3)
        ]
        r = FeedResponse(data=items)
        assert len(r.data) == 3


# ── NextChoiceResponse ────────────────────────────────────────────────────


class TestNextChoiceResponse:
    def test_no_event(self):
        r = NextChoiceResponse(event=None, pool_size=0)
        assert r.event is None
        assert r.pool_size == 0

    def test_with_event(self):
        r = NextChoiceResponse(
            event={"id": "ev-001", "title_ru": "Выбор"},
            pool_size=5,
        )
        assert r.event["id"] == "ev-001"
        assert r.pool_size == 5


# ── ChoiceResponse ────────────────────────────────────────────────────────


class TestChoiceResponse:
    def test_valid(self):
        r = ChoiceResponse(
            event_id="ev-001",
            choice_index=2,
            consequences={"health": -5},
            stats_after={"health": 45.0, "money": 100.0},
        )
        assert r.event_id == "ev-001"
        assert r.consequences == {"health": -5}

    def test_empty_consequences(self):
        r = ChoiceResponse(
            event_id="ev-002",
            choice_index=0,
            consequences={},
            stats_after={},
        )
        assert r.consequences == {}


# ── PurchaseResponse ──────────────────────────────────────────────────────


class TestPurchaseResponse:
    def test_valid(self):
        r = PurchaseResponse(
            shop_item="social_event_ticket",
            cost=30,
            remaining_crystals=170,
            stat_boost={"social": 5.0, "happiness": 5.0},
        )
        assert r.cost == 30
        assert r.remaining_crystals == 170

    def test_zero_remaining(self):
        r = PurchaseResponse(
            shop_item="health_insurance",
            cost=100,
            remaining_crystals=0,
            stat_boost={"health": 10.0},
        )
        assert r.remaining_crystals == 0


# ── Shop cost affordability logic (unit, no DB) ──────────────────────────


class TestShopAffordability:
    @pytest.mark.parametrize(
        "item_id,balance,affordable",
        [
            ("premium_training_course", 50, True),
            ("premium_training_course", 49, False),
            ("social_event_ticket", 30, True),
            ("social_event_ticket", 0, False),
            ("health_insurance", 100, True),
            ("health_insurance", 99, False),
            ("career_coach", 75, True),
            ("career_coach", 74, False),
        ],
    )
    def test_affordability(self, item_id: str, balance: int, affordable: bool):
        cost = _CRYSTAL_SHOP[item_id]["cost"]
        assert (balance >= cost) == affordable
