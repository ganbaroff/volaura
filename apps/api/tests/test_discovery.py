"""Unit tests for discovery router — _anonymize_name helper + schema validation.

Covers: name anonymization edge cases, competency slug validation,
DiscoveryRequest field validators, DiscoveryProfessional alias mapping.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.routers.discovery import _anonymize_name
from app.schemas.discovery import (
    COMPETENCY_SLUGS,
    DiscoveryMeta,
    DiscoveryProfessional,
    DiscoveryRequest,
    DiscoveryResponse,
)


class TestAnonymizeName:
    def test_full_name(self):
        assert _anonymize_name("Leyla Aliyeva") == "Leyla A."

    def test_single_name(self):
        assert _anonymize_name("Leyla") == "Leyla"

    def test_three_part_name(self):
        assert _anonymize_name("Leyla Kamal Aliyeva") == "Leyla A."

    def test_none_returns_professional(self):
        assert _anonymize_name(None) == "Professional"

    def test_empty_string_returns_professional(self):
        assert _anonymize_name("") == "Professional"

    def test_whitespace_only_returns_professional(self):
        assert _anonymize_name("   ") == "Professional"

    def test_name_with_extra_spaces(self):
        assert _anonymize_name("  Leyla   Aliyeva  ") == "Leyla A."

    def test_long_first_name_capped_at_20(self):
        long_name = "A" * 30 + " Bey"
        result = _anonymize_name(long_name)
        assert result == "A" * 20 + " B."

    def test_last_initial_uppercased(self):
        assert _anonymize_name("leyla aliyeva") == "leyla A."

    def test_unicode_azerbaijani(self):
        assert _anonymize_name("Əli Şərifov") == "Əli Ş."


class TestDiscoveryRequest:
    def test_valid_minimal(self):
        r = DiscoveryRequest()
        assert r.competency is None
        assert r.score_min == 0.0
        assert r.limit == 20
        assert r.sort_by == "score"

    def test_valid_full(self):
        r = DiscoveryRequest(
            competency="communication",
            score_min=50.0,
            role_level="coordinator",
            badge_tier="Gold",
            sort_by="events",
            limit=10,
        )
        assert r.competency == "communication"
        assert r.score_min == 50.0

    def test_invalid_competency_raises(self):
        with pytest.raises(ValidationError, match="Invalid competency slug"):
            DiscoveryRequest(competency="nonexistent")

    def test_all_competency_slugs_valid(self):
        for slug in COMPETENCY_SLUGS:
            r = DiscoveryRequest(competency=slug)
            assert r.competency == slug

    def test_score_min_below_zero_raises(self):
        with pytest.raises(ValidationError):
            DiscoveryRequest(score_min=-1.0)

    def test_score_min_above_100_raises(self):
        with pytest.raises(ValidationError):
            DiscoveryRequest(score_min=101.0)

    def test_limit_zero_raises(self):
        with pytest.raises(ValidationError):
            DiscoveryRequest(limit=0)

    def test_limit_above_50_raises(self):
        with pytest.raises(ValidationError):
            DiscoveryRequest(limit=51)

    def test_invalid_after_id_raises(self):
        with pytest.raises(ValidationError, match="valid UUID"):
            DiscoveryRequest(after_id="not-a-uuid")

    def test_valid_after_id(self):
        r = DiscoveryRequest(after_id="12345678-1234-1234-1234-123456789abc")
        assert r.after_id == "12345678-1234-1234-1234-123456789abc"


class TestDiscoveryProfessional:
    def test_alias_mapping(self):
        p = DiscoveryProfessional(
            volunteer_id="abc-123",
            display_name="Leyla A.",
            badge_tier="Gold",
            total_score=85.5,
        )
        assert p.professional_id == "abc-123"

    def test_optional_fields_default(self):
        p = DiscoveryProfessional(
            volunteer_id="abc-123",
            display_name="Test",
            badge_tier="Bronze",
            total_score=40.0,
        )
        assert p.competency_score is None
        assert p.role_level is None
        assert p.events_attended == 0
        assert p.last_updated is None


class TestDiscoveryMeta:
    def test_no_more_pages(self):
        m = DiscoveryMeta(returned=5, limit=20, has_more=False)
        assert m.next_after_score is None
        assert m.next_after_id is None

    def test_has_more_with_score_cursor(self):
        m = DiscoveryMeta(
            returned=20,
            limit=20,
            has_more=True,
            next_after_score=75.0,
            next_after_id="abc",
        )
        assert m.has_more is True
        assert m.next_after_score == 75.0


class TestDiscoveryResponse:
    def test_empty_response(self):
        r = DiscoveryResponse(
            data=[],
            meta=DiscoveryMeta(returned=0, limit=20, has_more=False),
        )
        assert len(r.data) == 0
        assert r.meta.returned == 0
