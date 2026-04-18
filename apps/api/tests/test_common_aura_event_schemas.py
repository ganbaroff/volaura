"""Unit tests for common, aura, and event Pydantic schemas.

Covers:
  common.py  — ErrorDetail, ErrorResponse, MessageResponse, PaginatedMeta
  aura.py    — CompetencyScore, AuraScoreResponse, AuraEvaluationItem,
               AuraCompetencyExplanation, AuraExplanationResponse,
               UpdateVisibilityRequest, SharingPermissionRequest
  event.py   — EventCreate, EventUpdate, EventResponse, RegistrationResponse,
               CheckInRequest, EventAttendeeRow, CoordinatorRatingRequest,
               ProfessionalRatingRequest
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.aura import (
    AuraCompetencyExplanation,
    AuraEvaluationItem,
    AuraExplanationResponse,
    AuraScoreResponse,
    CompetencyScore,
    SharingPermissionRequest,
    UpdateVisibilityRequest,
)
from app.schemas.common import (
    ErrorDetail,
    ErrorResponse,
    MessageResponse,
    PaginatedMeta,
)
from app.schemas.event import (
    CheckInRequest,
    CoordinatorRatingRequest,
    EventAttendeeRow,
    EventCreate,
    EventResponse,
    EventUpdate,
    ProfessionalRatingRequest,
    RegistrationResponse,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

UID = str(uuid.uuid4())
NOW = datetime.now(UTC)
NOW_ISO = NOW.isoformat()


# ══════════════════════════════════════════════════════════════════════════════
# common.py
# ══════════════════════════════════════════════════════════════════════════════


class TestErrorDetail:
    def test_valid(self):
        ed = ErrorDetail(code="NOT_FOUND", message="Resource not found")
        assert ed.code == "NOT_FOUND"
        assert ed.message == "Resource not found"

    def test_empty_strings_allowed(self):
        ed = ErrorDetail(code="", message="")
        assert ed.code == ""

    def test_missing_code_raises(self):
        with pytest.raises(ValidationError):
            ErrorDetail(message="oops")  # type: ignore[call-arg]

    def test_missing_message_raises(self):
        with pytest.raises(ValidationError):
            ErrorDetail(code="E1")  # type: ignore[call-arg]


class TestErrorResponse:
    def test_valid(self):
        er = ErrorResponse(error=ErrorDetail(code="E1", message="bad"))
        assert er.error.code == "E1"

    def test_nested_dict(self):
        er = ErrorResponse(error={"code": "E2", "message": "worse"})
        assert isinstance(er.error, ErrorDetail)
        assert er.error.code == "E2"

    def test_missing_error_raises(self):
        with pytest.raises(ValidationError):
            ErrorResponse()  # type: ignore[call-arg]


class TestMessageResponse:
    def test_valid(self):
        mr = MessageResponse(message="ok")
        assert mr.message == "ok"

    def test_empty_string(self):
        mr = MessageResponse(message="")
        assert mr.message == ""

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            MessageResponse()  # type: ignore[call-arg]


class TestPaginatedMeta:
    def test_valid(self):
        pm = PaginatedMeta(total=100, page=2, per_page=20, pages=5)
        assert pm.total == 100
        assert pm.page == 2
        assert pm.per_page == 20
        assert pm.pages == 5

    def test_zero_values(self):
        pm = PaginatedMeta(total=0, page=1, per_page=10, pages=0)
        assert pm.total == 0
        assert pm.pages == 0

    @pytest.mark.parametrize("missing_field", ["total", "page", "per_page", "pages"])
    def test_missing_required_field(self, missing_field):
        data = {"total": 10, "page": 1, "per_page": 5, "pages": 2}
        del data[missing_field]
        with pytest.raises(ValidationError):
            PaginatedMeta(**data)


# ══════════════════════════════════════════════════════════════════════════════
# aura.py
# ══════════════════════════════════════════════════════════════════════════════


class TestCompetencyScore:
    def test_valid(self):
        cs = CompetencyScore(
            slug="communication",
            name_en="Communication",
            name_az="Kommunikasiya",
            score=0.85,
            weight=0.20,
        )
        assert cs.slug == "communication"
        assert cs.score == 0.85
        assert cs.weight == 0.20

    @pytest.mark.parametrize("missing", ["slug", "name_en", "name_az", "score", "weight"])
    def test_missing_required(self, missing):
        data = {
            "slug": "s",
            "name_en": "N",
            "name_az": "A",
            "score": 0.5,
            "weight": 0.1,
        }
        del data[missing]
        with pytest.raises(ValidationError):
            CompetencyScore(**data)

    def test_float_coercion(self):
        cs = CompetencyScore(slug="s", name_en="N", name_az="A", score=1, weight=0)
        assert isinstance(cs.score, float)
        assert isinstance(cs.weight, float)


class TestAuraScoreResponse:
    def _base(self, **kwargs):
        defaults = {
            "volunteer_id": UID,
            "total_score": 72.5,
            "badge_tier": "Gold",
            "elite_status": False,
            "competency_scores": {"communication": 0.8},
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_minimal(self):
        asr = AuraScoreResponse(**self._base())
        assert asr.professional_id == UID
        assert asr.total_score == 72.5
        assert asr.badge_tier == "Gold"
        assert asr.elite_status is False

    def test_defaults(self):
        asr = AuraScoreResponse(**self._base())
        assert asr.visibility == "public"
        assert asr.reliability_score == 0.0
        assert asr.reliability_status == "pending"
        assert asr.events_attended == 0
        assert asr.events_no_show == 0
        assert asr.percentile_rank is None
        assert asr.effective_score is None
        assert asr.aura_history == []
        assert asr.last_updated is None

    def test_validation_alias_volunteer_id(self):
        asr = AuraScoreResponse(**self._base())
        assert asr.professional_id == UID

    def test_optional_fields_populated(self):
        asr = AuraScoreResponse(
            **self._base(
                percentile_rank=88.0,
                effective_score=70.1,
                last_updated=NOW,
                aura_history=[{"date": "2026-01-01", "score": 60.0}],
            )
        )
        assert asr.percentile_rank == 88.0
        assert asr.effective_score == 70.1
        assert asr.last_updated == NOW
        assert len(asr.aura_history) == 1

    @pytest.mark.parametrize("missing", ["volunteer_id", "total_score", "badge_tier", "elite_status", "competency_scores"])
    def test_missing_required(self, missing):
        data = self._base()
        del data[missing]
        with pytest.raises(ValidationError):
            AuraScoreResponse(**data)

    def test_from_attributes(self):
        class FakeRow:
            volunteer_id = UID
            total_score = 50.0
            badge_tier = "Bronze"
            elite_status = False
            competency_scores = {}
            visibility = "hidden"
            reliability_score = 0.5
            reliability_status = "ok"
            events_attended = 3
            events_no_show = 1
            percentile_rank = None
            effective_score = None
            aura_history = []
            last_updated = None

        asr = AuraScoreResponse.model_validate(FakeRow())
        assert asr.professional_id == UID
        assert asr.badge_tier == "Bronze"


class TestAuraEvaluationItem:
    def test_valid_minimal(self):
        item = AuraEvaluationItem(
            concept_scores={"leadership": 0.7},
            evaluation_confidence="high",
            methodology="IRT-CAT",
        )
        assert item.question_id is None
        assert item.concept_details is None
        assert item.concept_scores == {"leadership": 0.7}

    def test_all_fields(self):
        item = AuraEvaluationItem(
            question_id="q-001",
            concept_scores={"empathy": 0.9},
            evaluation_confidence="pattern_matched",
            methodology="DeCE",
            concept_details=[{"concept": "empathy", "quote": "..."}],
        )
        assert item.question_id == "q-001"
        assert item.concept_details is not None
        assert len(item.concept_details) == 1

    @pytest.mark.parametrize("missing", ["concept_scores", "evaluation_confidence", "methodology"])
    def test_missing_required(self, missing):
        data = {
            "concept_scores": {"x": 0.5},
            "evaluation_confidence": "high",
            "methodology": "IRT",
        }
        del data[missing]
        with pytest.raises(ValidationError):
            AuraEvaluationItem(**data)


class TestAuraCompetencyExplanation:
    def _item(self):
        return AuraEvaluationItem(
            concept_scores={"comm": 0.6},
            evaluation_confidence="high",
            methodology="IRT",
        )

    def test_valid(self):
        ace = AuraCompetencyExplanation(
            role_level="junior",
            items_evaluated=3,
            evaluations=[self._item()],
        )
        assert ace.competency_id is None
        assert ace.completed_at is None
        assert ace.role_level == "junior"
        assert len(ace.evaluations) == 1

    def test_with_optional_fields(self):
        ace = AuraCompetencyExplanation(
            competency_id="comm-001",
            role_level="senior",
            completed_at="2026-04-01T12:00:00Z",
            items_evaluated=5,
            evaluations=[],
        )
        assert ace.competency_id == "comm-001"
        assert ace.completed_at == "2026-04-01T12:00:00Z"

    @pytest.mark.parametrize("missing", ["role_level", "items_evaluated", "evaluations"])
    def test_missing_required(self, missing):
        data = {
            "role_level": "mid",
            "items_evaluated": 2,
            "evaluations": [],
        }
        del data[missing]
        with pytest.raises(ValidationError):
            AuraCompetencyExplanation(**data)


class TestAuraExplanationResponse:
    def _base(self, **kwargs):
        defaults = {
            "volunteer_id": UID,
            "explanation_count": 2,
            "has_pending_evaluations": False,
            "pending_reeval_count": 0,
            "methodology_reference": "IRT-CAT v2",
            "explanations": [],
        }
        defaults.update(kwargs)
        return defaults

    def test_valid(self):
        aer = AuraExplanationResponse(**self._base())
        assert aer.professional_id == UID
        assert aer.explanation_count == 2
        assert aer.has_pending_evaluations is False
        assert aer.pending_reeval_count == 0

    def test_validation_alias(self):
        aer = AuraExplanationResponse(**self._base())
        assert aer.professional_id == UID

    def test_with_pending(self):
        aer = AuraExplanationResponse(**self._base(has_pending_evaluations=True, pending_reeval_count=3))
        assert aer.has_pending_evaluations is True
        assert aer.pending_reeval_count == 3

    @pytest.mark.parametrize(
        "missing",
        ["volunteer_id", "explanation_count", "has_pending_evaluations", "pending_reeval_count", "methodology_reference", "explanations"],
    )
    def test_missing_required(self, missing):
        data = self._base()
        del data[missing]
        with pytest.raises(ValidationError):
            AuraExplanationResponse(**data)


class TestUpdateVisibilityRequest:
    @pytest.mark.parametrize("vis", ["public", "badge_only", "hidden"])
    def test_valid_literals(self, vis):
        uvr = UpdateVisibilityRequest(visibility=vis)
        assert uvr.visibility == vis

    def test_invalid_literal_raises(self):
        with pytest.raises(ValidationError):
            UpdateVisibilityRequest(visibility="private")

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            UpdateVisibilityRequest()  # type: ignore[call-arg]


class TestSharingPermissionRequest:
    @pytest.mark.parametrize("perm", ["read_score", "read_full_eval", "export_report"])
    @pytest.mark.parametrize("action", ["grant", "revoke"])
    def test_valid_combinations(self, perm, action):
        spr = SharingPermissionRequest(org_id=UID, permission_type=perm, action=action)
        assert spr.org_id == UID
        assert spr.permission_type == perm
        assert spr.action == action

    def test_invalid_permission_raises(self):
        with pytest.raises(ValidationError):
            SharingPermissionRequest(org_id=UID, permission_type="write_score", action="grant")

    def test_invalid_action_raises(self):
        with pytest.raises(ValidationError):
            SharingPermissionRequest(org_id=UID, permission_type="read_score", action="deny")

    @pytest.mark.parametrize("missing", ["org_id", "permission_type", "action"])
    def test_missing_required(self, missing):
        data = {"org_id": UID, "permission_type": "read_score", "action": "grant"}
        del data[missing]
        with pytest.raises(ValidationError):
            SharingPermissionRequest(**data)


# ══════════════════════════════════════════════════════════════════════════════
# event.py
# ══════════════════════════════════════════════════════════════════════════════


class TestEventCreate:
    def _base(self, **kwargs):
        defaults = {
            "title_en": "Hack Day",
            "title_az": "Hak Günü",
            "start_date": NOW,
            "end_date": NOW,
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_minimal(self):
        ec = EventCreate(**self._base())
        assert ec.title_en == "Hack Day"
        assert ec.title_az == "Hak Günü"
        assert ec.status == "draft"
        assert ec.is_public is True
        assert ec.required_min_aura == 0.0
        assert ec.required_languages == []

    def test_defaults(self):
        ec = EventCreate(**self._base())
        assert ec.description_en is None
        assert ec.description_az is None
        assert ec.event_type is None
        assert ec.location is None
        assert ec.location_coords is None
        assert ec.capacity is None

    @pytest.mark.parametrize("status", ["draft", "open", "closed", "cancelled", "completed"])
    def test_valid_statuses(self, status):
        ec = EventCreate(**self._base(status=status))
        assert ec.status == status

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError, match="status must be one of"):
            EventCreate(**self._base(status="pending"))

    def test_location_coords(self):
        ec = EventCreate(**self._base(location_coords={"lat": 40.4, "lon": 49.8}))
        assert ec.location_coords == {"lat": 40.4, "lon": 49.8}

    @pytest.mark.parametrize("missing", ["title_en", "title_az", "start_date", "end_date"])
    def test_missing_required(self, missing):
        data = self._base()
        del data[missing]
        with pytest.raises(ValidationError):
            EventCreate(**data)

    def test_full_fields(self):
        ec = EventCreate(
            title_en="Full Event",
            title_az="Tam Tədbiр",
            description_en="Desc EN",
            description_az="Desc AZ",
            event_type="workshop",
            location="Baku, AZ",
            location_coords={"lat": 40.4, "lon": 49.8},
            start_date=NOW,
            end_date=NOW,
            capacity=100,
            required_min_aura=50.0,
            required_languages=["az", "en"],
            status="open",
            is_public=False,
        )
        assert ec.capacity == 100
        assert ec.required_min_aura == 50.0
        assert ec.required_languages == ["az", "en"]
        assert ec.is_public is False


class TestEventUpdate:
    def test_all_none_by_default(self):
        eu = EventUpdate()
        assert eu.title_en is None
        assert eu.title_az is None
        assert eu.description_en is None
        assert eu.description_az is None
        assert eu.event_type is None
        assert eu.location is None
        assert eu.start_date is None
        assert eu.end_date is None
        assert eu.capacity is None
        assert eu.required_min_aura is None
        assert eu.required_languages is None
        assert eu.status is None
        assert eu.is_public is None

    def test_partial_update(self):
        eu = EventUpdate(title_en="New Title", status="open")
        assert eu.title_en == "New Title"
        assert eu.status == "open"
        assert eu.title_az is None

    def test_all_fields(self):
        eu = EventUpdate(
            title_en="T",
            title_az="T",
            description_en="D",
            description_az="D",
            event_type="conf",
            location="Baku",
            start_date=NOW,
            end_date=NOW,
            capacity=50,
            required_min_aura=30.0,
            required_languages=["en"],
            status="closed",
            is_public=True,
        )
        assert eu.capacity == 50
        assert eu.required_languages == ["en"]


class TestEventResponse:
    def _base(self, **kwargs):
        defaults = {
            "id": UID,
            "organization_id": UID,
            "title_en": "T EN",
            "title_az": "T AZ",
            "start_date": NOW,
            "end_date": NOW,
            "status": "open",
            "is_public": True,
            "created_at": NOW,
            "updated_at": NOW,
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_minimal(self):
        er = EventResponse(**self._base())
        assert er.id == UID
        assert er.status == "open"
        assert er.required_min_aura == 0.0
        assert er.required_languages == []

    def test_optional_fields_none(self):
        er = EventResponse(**self._base())
        assert er.description_en is None
        assert er.description_az is None
        assert er.event_type is None
        assert er.location is None
        assert er.location_coords is None
        assert er.capacity is None

    @pytest.mark.parametrize(
        "missing",
        ["id", "organization_id", "title_en", "title_az", "start_date", "end_date", "status", "is_public", "created_at", "updated_at"],
    )
    def test_missing_required(self, missing):
        data = self._base()
        del data[missing]
        with pytest.raises(ValidationError):
            EventResponse(**data)


class TestRegistrationResponse:
    def _base(self, **kwargs):
        defaults = {
            "id": UID,
            "event_id": UID,
            "volunteer_id": UID,
            "status": "registered",
            "registered_at": NOW,
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_minimal(self):
        rr = RegistrationResponse(**self._base())
        assert rr.professional_id == UID
        assert rr.status == "registered"
        assert rr.checked_in_at is None
        assert rr.check_in_code is None
        assert rr.coordinator_rating is None
        assert rr.professional_rating is None

    def test_validation_alias_volunteer_id(self):
        rr = RegistrationResponse(**self._base())
        assert rr.professional_id == UID

    def test_volunteer_rating_alias(self):
        rr = RegistrationResponse(**self._base(volunteer_rating=4.5, volunteer_feedback="Great!"))
        assert rr.professional_rating == 4.5
        assert rr.professional_feedback == "Great!"

    def test_full_fields(self):
        rr = RegistrationResponse(
            **self._base(
                checked_in_at=NOW,
                check_in_code="ABC123",
                coordinator_rating=4.0,
                coordinator_feedback="Good work",
            )
        )
        assert rr.checked_in_at == NOW
        assert rr.check_in_code == "ABC123"
        assert rr.coordinator_rating == 4.0

    @pytest.mark.parametrize("missing", ["id", "event_id", "volunteer_id", "status", "registered_at"])
    def test_missing_required(self, missing):
        data = self._base()
        del data[missing]
        with pytest.raises(ValidationError):
            RegistrationResponse(**data)


class TestCheckInRequest:
    def test_valid(self):
        cir = CheckInRequest(check_in_code="XYZ789")
        assert cir.check_in_code == "XYZ789"

    def test_missing_raises(self):
        with pytest.raises(ValidationError):
            CheckInRequest()  # type: ignore[call-arg]


class TestEventAttendeeRow:
    def _base(self, **kwargs):
        defaults = {
            "registration_id": UID,
            "volunteer_id": UID,
            "status": "checked_in",
            "registered_at": NOW,
        }
        defaults.update(kwargs)
        return defaults

    def test_valid_minimal(self):
        ear = EventAttendeeRow(**self._base())
        assert ear.professional_id == UID
        assert ear.display_name is None
        assert ear.username is None
        assert ear.total_score is None
        assert ear.badge_tier is None

    def test_validation_alias(self):
        ear = EventAttendeeRow(**self._base())
        assert ear.professional_id == UID

    def test_with_profile_data(self):
        ear = EventAttendeeRow(
            **self._base(
                checked_in_at=NOW,
                display_name="Jane Doe",
                username="janedoe",
                total_score=85.0,
                badge_tier="Platinum",
            )
        )
        assert ear.display_name == "Jane Doe"
        assert ear.total_score == 85.0
        assert ear.badge_tier == "Platinum"

    @pytest.mark.parametrize("missing", ["registration_id", "volunteer_id", "status", "registered_at"])
    def test_missing_required(self, missing):
        data = self._base()
        del data[missing]
        with pytest.raises(ValidationError):
            EventAttendeeRow(**data)


class TestCoordinatorRatingRequest:
    def test_valid(self):
        crr = CoordinatorRatingRequest(registration_id=UID, rating=4.0)
        assert crr.registration_id == UID
        assert crr.rating == 4.0
        assert crr.feedback is None

    def test_boundary_min(self):
        crr = CoordinatorRatingRequest(registration_id=UID, rating=1.0)
        assert crr.rating == 1.0

    def test_boundary_max(self):
        crr = CoordinatorRatingRequest(registration_id=UID, rating=5.0)
        assert crr.rating == 5.0

    def test_with_feedback(self):
        crr = CoordinatorRatingRequest(registration_id=UID, rating=3.5, feedback="Decent")
        assert crr.feedback == "Decent"

    @pytest.mark.parametrize("bad_rating", [0.9, 0.0, -1.0, 5.1, 6.0])
    def test_invalid_rating_raises(self, bad_rating):
        with pytest.raises(ValidationError, match="rating must be between 1 and 5"):
            CoordinatorRatingRequest(registration_id=UID, rating=bad_rating)

    @pytest.mark.parametrize("missing", ["registration_id", "rating"])
    def test_missing_required(self, missing):
        data = {"registration_id": UID, "rating": 3.0}
        del data[missing]
        with pytest.raises(ValidationError):
            CoordinatorRatingRequest(**data)


class TestProfessionalRatingRequest:
    def test_valid(self):
        prr = ProfessionalRatingRequest(rating=5.0)
        assert prr.rating == 5.0
        assert prr.feedback is None

    def test_boundary_min(self):
        prr = ProfessionalRatingRequest(rating=1.0)
        assert prr.rating == 1.0

    def test_boundary_max(self):
        prr = ProfessionalRatingRequest(rating=5.0)
        assert prr.rating == 5.0

    def test_with_feedback(self):
        prr = ProfessionalRatingRequest(rating=2.0, feedback="Could improve")
        assert prr.feedback == "Could improve"

    @pytest.mark.parametrize("bad_rating", [0.0, 0.99, 5.01, 10.0, -5.0])
    def test_invalid_rating_raises(self, bad_rating):
        with pytest.raises(ValidationError, match="rating must be between 1 and 5"):
            ProfessionalRatingRequest(rating=bad_rating)

    def test_missing_rating_raises(self):
        with pytest.raises(ValidationError):
            ProfessionalRatingRequest()  # type: ignore[call-arg]
