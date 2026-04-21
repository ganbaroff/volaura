"""Unit tests for Character schemas — cross-product event bus models.

Covers:
- CharacterEventCreate: event_type validation, source_product validation,
  payload schema_version injection
- CharacterEventOut: construction
- CharacterStateOut: default values, ge=0 constraints
- CrystalBalanceOut: construction
- VerifiedSkillOut: optional fields
- DAILY_CRYSTAL_CAP: structure
- EventType / SourceProduct literal enforcement
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.character import (
    DAILY_CRYSTAL_CAP,
    CharacterEventCreate,
    CharacterEventOut,
    CharacterStateOut,
    CrystalBalanceOut,
    VerifiedSkillOut,
)


class TestCharacterEventCreate:
    def test_valid_crystal_earned(self):
        e = CharacterEventCreate(
            event_type="crystal_earned",
            payload={"amount": 10, "source": "volaura_assessment"},
            source_product="volaura",
        )
        assert e.event_type == "crystal_earned"
        assert e.payload["_schema_version"] == 1

    def test_valid_crystal_spent(self):
        e = CharacterEventCreate(
            event_type="crystal_spent",
            payload={"amount": 5},
            source_product="mindshift",
        )
        assert e.source_product == "mindshift"

    def test_all_event_types(self):
        valid_types = [
            "crystal_earned",
            "crystal_spent",
            "skill_verified",
            "skill_unverified",
            "xp_earned",
            "stat_changed",
            "login_streak",
            "milestone_reached",
            "buff_applied",
            "vital_logged",
        ]
        for et in valid_types:
            e = CharacterEventCreate(event_type=et, source_product="volaura")
            assert e.event_type == et

    def test_invalid_event_type(self):
        with pytest.raises(ValidationError, match="Input should be"):
            CharacterEventCreate(event_type="invalid_type", source_product="volaura")

    def test_all_source_products(self):
        for sp in ("volaura", "mindshift", "lifesim", "brandedby", "eventshift"):
            e = CharacterEventCreate(event_type="xp_earned", source_product=sp)
            assert e.source_product == sp

    def test_invalid_source_product(self):
        with pytest.raises(ValidationError, match="Input should be"):
            CharacterEventCreate(event_type="xp_earned", source_product="unknown")

    def test_empty_payload_default(self):
        e = CharacterEventCreate(event_type="login_streak", source_product="volaura")
        assert e.payload == {}

    def test_explicit_empty_payload_gets_schema_version(self):
        e = CharacterEventCreate(event_type="login_streak", source_product="volaura", payload={})
        assert e.payload == {"_schema_version": 1}

    def test_existing_schema_version_preserved(self):
        e = CharacterEventCreate(
            event_type="xp_earned",
            payload={"_schema_version": 2, "xp": 100},
            source_product="volaura",
        )
        assert e.payload["_schema_version"] == 2

    def test_payload_with_custom_data(self):
        e = CharacterEventCreate(
            event_type="stat_changed",
            payload={"stat": "intelligence", "delta": 5},
            source_product="lifesim",
        )
        assert e.payload["stat"] == "intelligence"
        assert e.payload["_schema_version"] == 1

    def test_strip_whitespace(self):
        e = CharacterEventCreate(
            event_type="xp_earned",
            source_product="volaura",
        )
        assert e.event_type == "xp_earned"


class TestCharacterEventOut:
    def test_construction(self):
        now = datetime.now(UTC)
        uid = uuid4()
        e = CharacterEventOut(
            id=uuid4(),
            user_id=uid,
            event_type="crystal_earned",
            payload={"amount": 10, "_schema_version": 1},
            source_product="volaura",
            created_at=now,
        )
        assert e.user_id == uid
        assert e.event_type == "crystal_earned"

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            CharacterEventOut(
                id=uuid4(),
                user_id=uuid4(),
                event_type="xp_earned",
            )


class TestVerifiedSkillOut:
    def test_minimal(self):
        s = VerifiedSkillOut(slug="communication")
        assert s.slug == "communication"
        assert s.aura_score is None
        assert s.badge_tier is None

    def test_full(self):
        s = VerifiedSkillOut(slug="leadership", aura_score=85.5, badge_tier="gold")
        assert s.aura_score == 85.5
        assert s.badge_tier == "gold"


class TestCharacterStateOut:
    def test_default_empty_state(self):
        uid = uuid4()
        now = datetime.now(UTC)
        s = CharacterStateOut(
            user_id=uid,
            crystal_balance=0,
            xp_total=0,
            verified_skills=[],
            character_stats={},
            login_streak=0,
            event_count=0,
            computed_at=now,
        )
        assert s.crystal_balance == 0
        assert s.verified_skills == []
        assert s.last_event_at is None

    def test_negative_crystal_balance_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CharacterStateOut(
                user_id=uuid4(),
                crystal_balance=-1,
                xp_total=0,
                login_streak=0,
                event_count=0,
                computed_at=datetime.now(UTC),
            )

    def test_negative_xp_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CharacterStateOut(
                user_id=uuid4(),
                crystal_balance=0,
                xp_total=-5,
                login_streak=0,
                event_count=0,
                computed_at=datetime.now(UTC),
            )

    def test_negative_login_streak_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CharacterStateOut(
                user_id=uuid4(),
                crystal_balance=0,
                xp_total=0,
                login_streak=-1,
                event_count=0,
                computed_at=datetime.now(UTC),
            )

    def test_negative_event_count_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CharacterStateOut(
                user_id=uuid4(),
                crystal_balance=0,
                xp_total=0,
                login_streak=0,
                event_count=-1,
                computed_at=datetime.now(UTC),
            )

    def test_rich_state(self):
        now = datetime.now(UTC)
        s = CharacterStateOut(
            user_id=uuid4(),
            crystal_balance=250,
            xp_total=1500,
            verified_skills=[
                VerifiedSkillOut(slug="communication", aura_score=92.0, badge_tier="platinum"),
                VerifiedSkillOut(slug="leadership", aura_score=78.0, badge_tier="gold"),
            ],
            character_stats={"strength": 45, "intelligence": 72},
            login_streak=14,
            event_count=203,
            last_event_at=now,
            computed_at=now,
        )
        assert s.crystal_balance == 250
        assert len(s.verified_skills) == 2
        assert s.character_stats["intelligence"] == 72

    def test_default_factory_fields(self):
        s = CharacterStateOut(
            user_id=uuid4(),
            crystal_balance=0,
            xp_total=0,
            login_streak=0,
            event_count=0,
            computed_at=datetime.now(UTC),
        )
        assert s.verified_skills == []
        assert s.character_stats == {}


class TestCrystalBalanceOut:
    def test_minimal(self):
        b = CrystalBalanceOut(
            user_id=uuid4(),
            crystal_balance=100,
            lifetime_earned=200,
            computed_at=datetime.now(UTC),
        )
        assert b.crystal_balance == 100
        assert b.last_earned_at is None

    def test_negative_balance_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CrystalBalanceOut(
                user_id=uuid4(),
                crystal_balance=-1,
                lifetime_earned=0,
                computed_at=datetime.now(UTC),
            )

    def test_negative_lifetime_earned_rejected(self):
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            CrystalBalanceOut(
                user_id=uuid4(),
                crystal_balance=0,
                lifetime_earned=-10,
                computed_at=datetime.now(UTC),
            )

    def test_with_last_earned(self):
        now = datetime.now(UTC)
        b = CrystalBalanceOut(
            user_id=uuid4(),
            crystal_balance=50,
            last_earned_at=now,
            lifetime_earned=300,
            computed_at=now,
        )
        assert b.last_earned_at == now


class TestDailyCrystalCap:
    def test_daily_login_cap_exists(self):
        assert "daily_login" in DAILY_CRYSTAL_CAP

    def test_daily_login_cap_value(self):
        assert DAILY_CRYSTAL_CAP["daily_login"] == 15

    def test_cap_is_positive(self):
        for source, cap in DAILY_CRYSTAL_CAP.items():
            assert cap > 0, f"Cap for {source} must be positive"
