"""Unit tests for organization Pydantic schemas.

Covers: OrganizationCreate, OrganizationUpdate, ProfessionalSearchRequest,
AssignAssessmentRequest, IntroRequestCreate, SavedSearchFilters, SavedSearchCreate,
SavedSearchUpdate, BadgeDistribution, OrgProfessionalRow, ProfessionalSearchResult,
CollectiveAuraResponse.
"""

from __future__ import annotations

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.organization import (
    AssignAssessmentRequest,
    BadgeDistribution,
    CollectiveAuraResponse,
    IntroRequestCreate,
    OrganizationCreate,
    OrganizationUpdate,
    OrgProfessionalRow,
    ProfessionalSearchResult,
    SavedSearchCreate,
    SavedSearchFilters,
    SavedSearchUpdate,
)

VALID_UUID = str(uuid.uuid4())


# ── OrganizationCreate ──────────────────────────────────────────────────────


def test_org_create_valid_minimal():
    org = OrganizationCreate(name="Acme Corp")
    assert org.name == "Acme Corp"
    assert org.description is None


def test_org_create_name_too_short():
    with pytest.raises(ValidationError):
        OrganizationCreate(name="A")


def test_org_create_name_too_long():
    with pytest.raises(ValidationError):
        OrganizationCreate(name="X" * 201)


def test_org_create_full_fields():
    org = OrganizationCreate(
        name="Acme Corp",
        description="A great company",
        website="https://acme.com",
        logo_url="https://acme.com/logo.png",
        contact_email="info@acme.com",
    )
    assert org.website == "https://acme.com"
    assert org.contact_email == "info@acme.com"


# ── OrganizationUpdate ──────────────────────────────────────────────────────


def test_org_update_empty_is_valid():
    update = OrganizationUpdate()
    assert update.name is None
    assert update.description is None


def test_org_update_name_min_length_enforced():
    with pytest.raises(ValidationError):
        OrganizationUpdate(name="A")


# ── ProfessionalSearchRequest ───────────────────────────────────────────────

from app.schemas.organization import ProfessionalSearchRequest


def test_search_valid_minimal():
    req = ProfessionalSearchRequest(query="python")
    assert req.query == "python"
    assert req.limit == 10
    assert req.offset == 0


@pytest.mark.parametrize("tier", ["platinum", "gold", "silver", "bronze"])
def test_search_valid_badge_tiers(tier: str):
    req = ProfessionalSearchRequest(query="dev", badge_tier=tier)
    assert req.badge_tier == tier


def test_search_invalid_badge_tier():
    with pytest.raises(ValidationError):
        ProfessionalSearchRequest(query="dev", badge_tier="diamond")


def test_search_limit_lower_bound():
    with pytest.raises(ValidationError):
        ProfessionalSearchRequest(query="dev", limit=0)


def test_search_limit_upper_bound():
    with pytest.raises(ValidationError):
        ProfessionalSearchRequest(query="dev", limit=101)


def test_search_offset_ge_zero():
    with pytest.raises(ValidationError):
        ProfessionalSearchRequest(query="dev", offset=-1)


# ── AssignAssessmentRequest ─────────────────────────────────────────────────


def test_assign_valid():
    req = AssignAssessmentRequest(
        professional_ids=[VALID_UUID],
        competency_slugs=["communication"],
        deadline_days=30,
    )
    assert req.deadline_days == 30


def test_assign_invalid_uuid():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=["not-a-uuid"],
            competency_slugs=["communication"],
        )


def test_assign_invalid_competency_slug_uppercase():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=[VALID_UUID],
            competency_slugs=["Communication"],
        )


def test_assign_invalid_competency_slug_special_chars():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=[VALID_UUID],
            competency_slugs=["comm-skill!"],
        )


def test_assign_empty_professional_ids():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=[],
            competency_slugs=["communication"],
        )


def test_assign_empty_competency_slugs():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=[VALID_UUID],
            competency_slugs=[],
        )


def test_assign_deadline_too_low():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=[VALID_UUID],
            competency_slugs=["communication"],
            deadline_days=0,
        )


def test_assign_deadline_too_high():
    with pytest.raises(ValidationError):
        AssignAssessmentRequest(
            professional_ids=[VALID_UUID],
            competency_slugs=["communication"],
            deadline_days=91,
        )


# ── IntroRequestCreate ──────────────────────────────────────────────────────


def test_intro_valid():
    req = IntroRequestCreate(
        professional_id=VALID_UUID,
        project_name="Web Redesign",
        timeline="normal",
    )
    assert req.timeline == "normal"


def test_intro_invalid_timeline():
    with pytest.raises(ValidationError):
        IntroRequestCreate(
            professional_id=VALID_UUID,
            project_name="Web Redesign",
            timeline="yesterday",
        )


def test_intro_invalid_professional_id():
    with pytest.raises(ValidationError):
        IntroRequestCreate(
            professional_id="bad-uuid",
            project_name="Web Redesign",
            timeline="urgent",
        )


def test_intro_project_name_too_short():
    with pytest.raises(ValidationError):
        IntroRequestCreate(
            professional_id=VALID_UUID,
            project_name="X",
            timeline="flexible",
        )


# ── SavedSearchFilters ──────────────────────────────────────────────────────


def test_saved_filters_valid_defaults():
    f = SavedSearchFilters()
    assert f.query == ""
    assert f.min_aura == 0.0
    assert f.badge_tier is None
    assert f.languages == []


def test_saved_filters_invalid_badge_tier():
    with pytest.raises(ValidationError):
        SavedSearchFilters(badge_tier="legendary")


def test_saved_filters_languages_capped():
    langs = [f"lang_{i}" for i in range(15)]
    f = SavedSearchFilters(languages=langs)
    assert len(f.languages) == 10


def test_saved_filters_language_length_capped():
    long_lang = "x" * 100
    f = SavedSearchFilters(languages=[long_lang])
    assert len(f.languages[0]) == 50


# ── SavedSearchCreate ───────────────────────────────────────────────────────


def test_saved_search_create_valid():
    s = SavedSearchCreate(name="My Search", filters=SavedSearchFilters())
    assert s.name == "My Search"
    assert s.notify_on_match is True


def test_saved_search_create_empty_name():
    with pytest.raises(ValidationError):
        SavedSearchCreate(name="", filters=SavedSearchFilters())


# ── SavedSearchUpdate ────────────────────────────────────────────────────────


def test_saved_search_update_all_none():
    u = SavedSearchUpdate()
    assert u.name is None
    assert u.notify_on_match is None


# ── BadgeDistribution ────────────────────────────────────────────────────────


def test_badge_distribution_defaults_zero():
    bd = BadgeDistribution()
    assert bd.platinum == 0
    assert bd.gold == 0
    assert bd.silver == 0
    assert bd.bronze == 0
    assert bd.none == 0


# ── OrgProfessionalRow ──────────────────────────────────────────────────────


def test_org_professional_row_alias():
    row = OrgProfessionalRow.model_validate(
        {
            "volunteer_id": VALID_UUID,
            "username": "alice",
            "competencies_completed": 3,
        }
    )
    assert row.professional_id == VALID_UUID


# ── ProfessionalSearchResult ────────────────────────────────────────────────


def test_search_result_alias():
    result = ProfessionalSearchResult.model_validate(
        {
            "volunteer_id": VALID_UUID,
            "username": "bob",
            "overall_score": 85.0,
            "badge_tier": "gold",
            "elite_status": True,
        }
    )
    assert result.professional_id == VALID_UUID


# ── CollectiveAuraResponse ──────────────────────────────────────────────────


def test_collective_aura_minimal():
    resp = CollectiveAuraResponse(org_id="org-123", count=5)
    assert resp.org_id == "org-123"
    assert resp.count == 5
    assert resp.avg_aura is None
    assert resp.trend is None
