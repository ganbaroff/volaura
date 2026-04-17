"""Unit tests for events router — _validate_uuid + schema validation.

Covers: UUID validation, EventCreate status validator, rating validators,
RegistrationResponse alias mapping, EventAttendeeRow construction.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.routers.events import _validate_uuid
from app.schemas.event import (
    CheckInRequest,
    CoordinatorRatingRequest,
    EventAttendeeRow,
    EventCreate,
    EventUpdate,
    ProfessionalRatingRequest,
    RegistrationResponse,
)


class TestValidateUuid:
    def test_valid_uuid(self):
        _validate_uuid("12345678-1234-1234-1234-123456789abc", "test")

    def test_invalid_uuid_raises_422(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid("not-a-uuid", "event_id")
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INVALID_UUID"

    def test_empty_string_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid("", "event_id")
        assert exc_info.value.status_code == 422

    def test_none_raises(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid(None, "event_id")
        assert exc_info.value.status_code == 422

    def test_uuid_without_dashes(self):
        _validate_uuid("12345678123412341234123456789abc", "test")


class TestEventCreate:
    def test_valid_minimal(self):
        e = EventCreate(
            title_en="Test Event",
            title_az="Test Tədbir",
            start_date="2026-05-01T10:00:00Z",
            end_date="2026-05-01T18:00:00Z",
        )
        assert e.status == "draft"
        assert e.is_public is True
        assert e.capacity is None

    def test_valid_full(self):
        e = EventCreate(
            title_en="WUF13",
            title_az="WUF13",
            description_en="World Urban Forum",
            description_az="Dünya Şəhər Forumu",
            event_type="conference",
            location="Baku",
            start_date="2026-06-01T09:00:00Z",
            end_date="2026-06-05T18:00:00Z",
            capacity=500,
            required_min_aura=60.0,
            required_languages=["az", "en"],
            status="open",
            is_public=True,
        )
        assert e.capacity == 500
        assert e.status == "open"

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            EventCreate(
                title_en="X",
                title_az="X",
                start_date="2026-05-01T10:00:00Z",
                end_date="2026-05-01T18:00:00Z",
                status="invalid",
            )

    def test_all_valid_statuses(self):
        for status in ("draft", "open", "closed", "cancelled", "completed"):
            e = EventCreate(
                title_en="X",
                title_az="X",
                start_date="2026-05-01T10:00:00Z",
                end_date="2026-05-01T18:00:00Z",
                status=status,
            )
            assert e.status == status

    def test_missing_required_fields_raises(self):
        with pytest.raises(ValidationError):
            EventCreate(title_en="X")


class TestEventUpdate:
    def test_all_none_valid(self):
        u = EventUpdate()
        assert u.title_en is None
        assert u.status is None

    def test_partial_update(self):
        u = EventUpdate(title_en="Updated Title", status="open")
        assert u.title_en == "Updated Title"
        assert u.title_az is None


class TestCoordinatorRatingRequest:
    def test_valid_rating(self):
        r = CoordinatorRatingRequest(
            registration_id="abc-123",
            rating=4.5,
            feedback="Great work",
        )
        assert r.rating == 4.5

    def test_rating_below_1_raises(self):
        with pytest.raises(ValidationError, match="rating must be between 1 and 5"):
            CoordinatorRatingRequest(registration_id="abc", rating=0.5)

    def test_rating_above_5_raises(self):
        with pytest.raises(ValidationError, match="rating must be between 1 and 5"):
            CoordinatorRatingRequest(registration_id="abc", rating=5.5)

    def test_boundary_1(self):
        r = CoordinatorRatingRequest(registration_id="abc", rating=1.0)
        assert r.rating == 1.0

    def test_boundary_5(self):
        r = CoordinatorRatingRequest(registration_id="abc", rating=5.0)
        assert r.rating == 5.0

    def test_feedback_optional(self):
        r = CoordinatorRatingRequest(registration_id="abc", rating=3.0)
        assert r.feedback is None


class TestProfessionalRatingRequest:
    def test_valid(self):
        r = ProfessionalRatingRequest(rating=4.0, feedback="Good event")
        assert r.rating == 4.0

    def test_rating_below_1_raises(self):
        with pytest.raises(ValidationError):
            ProfessionalRatingRequest(rating=0.0)

    def test_rating_above_5_raises(self):
        with pytest.raises(ValidationError):
            ProfessionalRatingRequest(rating=6.0)


class TestRegistrationResponse:
    def test_alias_mapping(self):
        r = RegistrationResponse(
            id="reg-1",
            event_id="evt-1",
            volunteer_id="usr-1",
            status="pending",
            registered_at="2026-05-01T10:00:00Z",
        )
        assert r.professional_id == "usr-1"

    def test_optional_fields(self):
        r = RegistrationResponse(
            id="reg-1",
            event_id="evt-1",
            volunteer_id="usr-1",
            status="approved",
            registered_at="2026-05-01T10:00:00Z",
        )
        assert r.checked_in_at is None
        assert r.coordinator_rating is None
        assert r.professional_rating is None


class TestEventAttendeeRow:
    def test_construction(self):
        a = EventAttendeeRow(
            registration_id="reg-1",
            volunteer_id="usr-1",
            status="approved",
            registered_at="2026-05-01T10:00:00Z",
            checked_in_at="2026-05-01T10:30:00Z",
            display_name="Leyla",
            username="leyla_a",
            total_score=85.0,
            badge_tier="Gold",
        )
        assert a.professional_id == "usr-1"
        assert a.display_name == "Leyla"
        assert a.total_score == 85.0

    def test_minimal(self):
        a = EventAttendeeRow(
            registration_id="reg-1",
            volunteer_id="usr-1",
            status="pending",
            registered_at="2026-05-01T10:00:00Z",
        )
        assert a.display_name is None
        assert a.total_score is None
        assert a.badge_tier is None


class TestCheckInRequest:
    def test_valid(self):
        c = CheckInRequest(check_in_code="abc123xyz")
        assert c.check_in_code == "abc123xyz"

    def test_missing_code_raises(self):
        with pytest.raises(ValidationError):
            CheckInRequest()
