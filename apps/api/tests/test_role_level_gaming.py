"""Regression tests for role-level gaming — session 88 pre-launch audit S2.

Pins the schema-level rule that users may only self-claim `professional` or
`volunteer` tiers at assessment start. Elevated tiers (coordinator / specialist /
manager / senior_manager) must come from server-side evidence, not client input.

Before this gate a Leyla could POST role_level=senior_manager and show up in
Aynur's talent search as self-promoted. That contradicts "verified talent
platform" positioning.
"""

import pytest
from pydantic import ValidationError

from app.schemas.assessment import SELF_CLAIMABLE_ROLE_LEVELS, StartAssessmentRequest


def test_self_claimable_allows_professional():
    req = StartAssessmentRequest(
        competency_slug="communication",
        role_level="professional",
    )
    assert req.role_level == "professional"


def test_self_claimable_allows_volunteer_legacy():
    """Legacy `volunteer` tier still accepted for back-compat while DB column rename is pending."""
    req = StartAssessmentRequest(
        competency_slug="communication",
        role_level="volunteer",
    )
    assert req.role_level == "volunteer"


@pytest.mark.parametrize("elevated", ["coordinator", "specialist", "manager", "senior_manager"])
def test_elevated_roles_rejected_at_schema(elevated: str):
    """Core gaming gate — client can NOT self-promote to elevated tier."""
    with pytest.raises(ValidationError):
        StartAssessmentRequest(
            competency_slug="communication",
            role_level=elevated,  # type: ignore[arg-type]
        )


def test_garbage_role_rejected():
    """Arbitrary strings obviously rejected."""
    with pytest.raises(ValidationError):
        StartAssessmentRequest(
            competency_slug="communication",
            role_level="ceo",  # type: ignore[arg-type]
        )


def test_self_claimable_constant_is_subset_of_valid():
    """Invariant: self-claimable must always be a subset of VALID_ROLE_LEVELS."""
    from app.schemas.assessment import VALID_ROLE_LEVELS

    assert set(SELF_CLAIMABLE_ROLE_LEVELS).issubset(set(VALID_ROLE_LEVELS))
    # And must NOT include the elevated tiers
    assert "senior_manager" not in SELF_CLAIMABLE_ROLE_LEVELS
    assert "manager" not in SELF_CLAIMABLE_ROLE_LEVELS
    assert "coordinator" not in SELF_CLAIMABLE_ROLE_LEVELS
    assert "specialist" not in SELF_CLAIMABLE_ROLE_LEVELS
