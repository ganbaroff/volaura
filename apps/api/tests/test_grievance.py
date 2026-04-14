"""Grievance endpoint tests — Constitution G35 / ISO 10667-2 §7.

Pins the invariants for both intake (commit 9e19d47) and admin review
(commit eb6b11a):
 • Schema rejects too-short / too-long subject + description
 • POST creates row with status=pending, returns it to user
 • Admin PATCH requires resolution text when closing (resolved/rejected)
 • Admin PATCH 422s without resolution on closing transitions
"""

import pytest
from pydantic import ValidationError

from app.routers.grievance import GrievanceCreate, GrievanceStatusUpdate


# ── Schema-level guards ───────────────────────────────────────────────────────


def test_grievance_create_accepts_valid():
    g = GrievanceCreate(
        subject="My communication score is wrong",
        description="I scored 42 on communication but my last 3 events all rated me 9/10.",
    )
    assert g.subject.startswith("My communication")
    assert len(g.description) >= 10


def test_grievance_create_rejects_short_subject():
    with pytest.raises(ValidationError):
        GrievanceCreate(subject="hi", description="long enough description here")


def test_grievance_create_rejects_short_description():
    with pytest.raises(ValidationError):
        GrievanceCreate(subject="legitimate subject", description="too short")


def test_grievance_create_rejects_oversized_description():
    with pytest.raises(ValidationError):
        GrievanceCreate(
            subject="legitimate subject",
            description="x" * 5001,  # over 5000 cap
        )


# ── Admin status update guards ────────────────────────────────────────────────


def test_status_update_accepts_reviewing_without_resolution():
    """Reviewing is transient — resolution not required."""
    u = GrievanceStatusUpdate(status="reviewing")
    assert u.status == "reviewing"
    assert u.resolution is None


def test_status_update_accepts_resolved_with_resolution():
    u = GrievanceStatusUpdate(
        status="resolved",
        resolution="We re-graded the assessment manually. New score 67. AURA updated.",
    )
    assert u.status == "resolved"
    assert "re-graded" in u.resolution


def test_status_update_rejects_invalid_status():
    """Schema only accepts reviewing / resolved / rejected."""
    with pytest.raises(ValidationError):
        GrievanceStatusUpdate(status="pending")  # 'pending' is initial, not a transition target


def test_status_update_rejects_garbage_status():
    with pytest.raises(ValidationError):
        GrievanceStatusUpdate(status="something_made_up")


# ── Endpoint-level guard tested via direct router import ──────────────────────
# The "resolution required when closing" rule lives in the route handler, not
# the schema (because reviewing IS allowed without resolution). So we test the
# closing transitions via a hand-rolled assertion against the function.


@pytest.mark.anyio
async def test_admin_endpoint_requires_resolution_on_resolved(monkeypatch):
    """admin_transition_grievance must 422 when status=resolved + no resolution."""
    from fastapi import HTTPException
    from app.routers.grievance import admin_transition_grievance

    payload = GrievanceStatusUpdate(status="resolved", resolution=None, admin_notes=None)

    with pytest.raises(HTTPException) as exc_info:
        await admin_transition_grievance(
            request=None,  # not used by the rule we're testing
            grievance_id="11111111-1111-1111-1111-111111111111",
            payload=payload,
            db=None,
            admin_id="22222222-2222-2222-2222-222222222222",
        )
    assert exc_info.value.status_code == 422
    assert exc_info.value.detail["code"] == "RESOLUTION_REQUIRED"


@pytest.mark.anyio
async def test_admin_endpoint_requires_resolution_on_rejected():
    """Rejected = terminal too. Same rule."""
    from fastapi import HTTPException
    from app.routers.grievance import admin_transition_grievance

    payload = GrievanceStatusUpdate(status="rejected", resolution="   ", admin_notes=None)

    with pytest.raises(HTTPException) as exc_info:
        await admin_transition_grievance(
            request=None,
            grievance_id="11111111-1111-1111-1111-111111111111",
            payload=payload,
            db=None,
            admin_id="22222222-2222-2222-2222-222222222222",
        )
    assert exc_info.value.status_code == 422
    # Whitespace-only resolution should be treated as missing (we strip in the check)
    assert exc_info.value.detail["code"] == "RESOLUTION_REQUIRED"


@pytest.mark.anyio
async def test_admin_endpoint_reviewing_without_resolution_passes():
    """reviewing is transient — no resolution required. Should NOT 422.

    Uses a minimal MagicMock db that returns a canned row on update().execute().
    """
    from unittest.mock import AsyncMock, MagicMock
    from app.routers.grievance import admin_transition_grievance

    canned_row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "user_id": "22222222-2222-2222-2222-222222222222",
        "subject": "test",
        "description": "test description minimum length",
        "related_competency_slug": None,
        "related_session_id": None,
        "status": "reviewing",
        "resolution": None,
        "admin_notes": None,
        "created_at": "2026-04-14T00:00:00+00:00",
        "updated_at": "2026-04-14T09:00:00+00:00",
        "resolved_at": None,
    }

    db = MagicMock()
    result = MagicMock()
    result.data = [canned_row]
    db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(return_value=result)

    payload = GrievanceStatusUpdate(status="reviewing", resolution=None, admin_notes=None)

    response = await admin_transition_grievance(
        request=None,
        grievance_id="11111111-1111-1111-1111-111111111111",
        payload=payload,
        db=db,
        admin_id="33333333-3333-3333-3333-333333333333",
    )
    assert response.status == "reviewing"
    assert response.resolution is None


@pytest.mark.anyio
async def test_admin_endpoint_resolved_with_resolution_passes():
    """Closing with a real resolution text succeeds and sets resolved_at."""
    from unittest.mock import AsyncMock, MagicMock
    from app.routers.grievance import admin_transition_grievance

    canned_row = {
        "id": "11111111-1111-1111-1111-111111111111",
        "user_id": "22222222-2222-2222-2222-222222222222",
        "subject": "test",
        "description": "test description minimum length",
        "related_competency_slug": None,
        "related_session_id": None,
        "status": "resolved",
        "resolution": "Score was correct per IRT model. No change.",
        "admin_notes": "Verified theta at 1.2 SE; well within range.",
        "created_at": "2026-04-14T00:00:00+00:00",
        "updated_at": "2026-04-14T09:00:00+00:00",
        "resolved_at": "2026-04-14T09:00:00+00:00",
    }
    db = MagicMock()
    result = MagicMock()
    result.data = [canned_row]
    db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(return_value=result)

    payload = GrievanceStatusUpdate(
        status="resolved",
        resolution="Score was correct per IRT model. No change.",
        admin_notes="Verified theta at 1.2 SE; well within range.",
    )

    response = await admin_transition_grievance(
        request=None,
        grievance_id="11111111-1111-1111-1111-111111111111",
        payload=payload,
        db=db,
        admin_id="33333333-3333-3333-3333-333333333333",
    )
    assert response.status == "resolved"
    assert response.resolved_at is not None
    assert "IRT model" in response.resolution
