"""Tests for the screening campaigns API.

These tests cover the new B2B campaign flow end-to-end at the router level:
validation, campaign creation, public join, and report ranking.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

ORG_USER_ID = str(uuid.uuid4())
ORG_ID = str(uuid.uuid4())
PROFESSIONAL_ID = str(uuid.uuid4())
CAMPAIGN_ID = str(uuid.uuid4())
TOKEN = "pilot-c9ddfe3a56b14e573ec7"


@pytest.fixture(autouse=True)
def clear_overrides():
    yield
    app.dependency_overrides.clear()


def _admin_override(db):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid: str):
    async def _dep():
        return uid

    return _dep


def _make_table_mock(table_name: str, handlers: dict[str, AsyncMock | MagicMock]) -> MagicMock:
    table = MagicMock(name=f"{table_name}_table")
    for method_name in (
        "select",
        "eq",
        "in_",
        "limit",
        "maybe_single",
        "insert",
        "update",
        "order",
    ):
        getattr(table, method_name).return_value = table

    for method_name, handler in handlers.items():
        if method_name == "execute":
            table.execute = handler
        else:
            getattr(table, method_name).side_effect = handler

    return table


@pytest.mark.asyncio
async def test_campaign_create_rejects_whitespace_title_after_trim():
    db = MagicMock()
    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    payload = {
        "title": "   ",
        "description": "Valid description",
        "competency_slugs": ["communication"],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/campaigns",
            json=payload,
            headers={"Authorization": "Bearer fake"},
        )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert "Title must be at least 3 characters after trimming" in str(body)


@pytest.mark.asyncio
async def test_create_campaign_normalizes_payload_before_insert():
    captured: dict[str, dict] = {}

    org_table = _make_table_mock(
        "organizations",
        {
            "execute": AsyncMock(return_value=MagicMock(data={"id": ORG_ID, "name": "Atlas Org", "logo_url": None}))
        },
    )
    org_table.select.return_value = org_table
    org_table.eq.return_value = org_table
    org_table.maybe_single.return_value = org_table

    competencies_table = _make_table_mock(
        "competencies",
        {
            "execute": AsyncMock(
                return_value=MagicMock(
                    data=[
                        {"slug": "communication"},
                        {"slug": "reliability"},
                    ]
                )
            )
        },
    )
    competencies_table.select.return_value = competencies_table
    competencies_table.eq.return_value = competencies_table

    campaigns_table = _make_table_mock(
        "screening_campaigns",
        {
            "execute": AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "id": CAMPAIGN_ID,
                            "org_id": ORG_ID,
                            "created_by": ORG_USER_ID,
                            "title": "Customer Support Lead",
                            "description": "Candidate-facing campaign",
                            "competency_slugs": ["communication", "reliability"],
                            "invite_token": TOKEN,
                            "status": "active",
                            "deadline_days": 21,
                            "candidate_cap": 42,
                            "created_at": datetime.now(UTC).isoformat(),
                        }
                    ]
                )
            )
        },
    )

    def capture_insert(payload):
        captured["payload"] = payload
        return campaigns_table

    campaigns_table.insert.side_effect = capture_insert

    tables = {
        "organizations": org_table,
        "competencies": competencies_table,
        "screening_campaigns": campaigns_table,
    }

    db = MagicMock()
    db.table = MagicMock(side_effect=lambda name: tables[name])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    payload = {
        "title": "  Customer Support Lead  ",
        "description": "  Candidate-facing campaign  ",
        "competency_slugs": ["Communication", "reliability", "communication"],
        "deadline_days": 21,
        "candidate_cap": 42,
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/campaigns",
            json=payload,
            headers={"Authorization": "Bearer fake"},
        )

    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["title"] == "Customer Support Lead"
    assert body["description"] == "Candidate-facing campaign"
    assert body["competency_slugs"] == ["communication", "reliability"]
    assert body["candidate_count"] == 0
    assert captured["payload"]["title"] == "Customer Support Lead"
    assert captured["payload"]["description"] == "Candidate-facing campaign"
    assert captured["payload"]["competency_slugs"] == ["communication", "reliability"]


@pytest.mark.asyncio
async def test_join_and_report_campaign_flow_ranks_fully_completed_candidate_first():
    campaign = {
        "id": CAMPAIGN_ID,
        "org_id": ORG_ID,
        "created_by": ORG_USER_ID,
        "title": "Customer Support Lead",
        "description": "Candidate-facing campaign",
        "competency_slugs": ["communication", "reliability"],
        "invite_token": TOKEN,
        "status": "active",
        "deadline_days": 21,
        "candidate_cap": 42,
        "created_at": datetime.now(UTC).isoformat(),
    }

    join_inserted_sessions: list[dict] = []
    second_professional_id = str(uuid.uuid4())

    table_calls = {"screening_campaigns": 0, "campaign_candidates": 0, "assessment_sessions": 0}

    screening_campaigns = _make_table_mock(
        "screening_campaigns",
        {
            "execute": AsyncMock(side_effect=lambda: MagicMock(data=campaign)),
        },
    )
    screening_campaigns.select.return_value = screening_campaigns
    screening_campaigns.eq.return_value = screening_campaigns
    screening_campaigns.maybe_single.return_value = screening_campaigns

    campaign_candidates = _make_table_mock("campaign_candidates", {})
    campaign_candidates.select.return_value = campaign_candidates
    campaign_candidates.eq.return_value = campaign_candidates
    campaign_candidates.in_.return_value = campaign_candidates
    campaign_candidates.limit.return_value = campaign_candidates

    async def campaign_candidates_execute():
        call = table_calls["campaign_candidates"]
        table_calls["campaign_candidates"] += 1
        if call == 0:
            return MagicMock(data=None)
        if call == 1:
            return MagicMock(data=[], count=0)
        return MagicMock(
            data=[
                {"professional_id": PROFESSIONAL_ID, "joined_at": "2026-06-11T09:00:00+00:00"},
                {"professional_id": second_professional_id, "joined_at": "2026-06-11T09:05:00+00:00"},
            ]
        )

    campaign_candidates.execute = AsyncMock(side_effect=campaign_candidates_execute)

    inserted_join_rows: list[dict] = []

    def record_candidate_insert(payload):
        inserted_join_rows.append(payload)
        return campaign_candidates

    campaign_candidates.insert.side_effect = record_candidate_insert

    competencies = _make_table_mock(
        "competencies",
        {
            "execute": AsyncMock(
                return_value=MagicMock(
                    data=[
                        {"id": "c1", "slug": "communication"},
                        {"id": "c2", "slug": "reliability"},
                    ]
                )
            )
        },
    )
    competencies.select.return_value = competencies
    competencies.in_.return_value = competencies

    assessment_sessions = _make_table_mock("assessment_sessions", {})
    assessment_sessions.select.return_value = assessment_sessions
    assessment_sessions.eq.return_value = assessment_sessions
    assessment_sessions.in_.return_value = assessment_sessions
    assessment_sessions.insert.return_value = assessment_sessions

    async def assessment_sessions_execute():
        call = table_calls["assessment_sessions"]
        table_calls["assessment_sessions"] += 1
        if call == 0:
            return MagicMock(data=[])
        if call == 1:
            inserted = {"id": str(uuid.uuid4()), "competency_id": "c1", "status": "assigned"}
            join_inserted_sessions.append(inserted)
            return MagicMock(data=[inserted])
        if call == 2:
            inserted = {"id": str(uuid.uuid4()), "competency_id": "c2", "status": "assigned"}
            join_inserted_sessions.append(inserted)
            return MagicMock(data=[inserted])
        return MagicMock(
            data=[
                {"volunteer_id": PROFESSIONAL_ID, "status": "completed"},
                {"volunteer_id": PROFESSIONAL_ID, "status": "completed"},
                {"volunteer_id": PROFESSIONAL_ID, "status": "completed"},
                {"volunteer_id": second_professional_id, "status": "completed"},
                {"volunteer_id": second_professional_id, "status": "completed"},
                {"volunteer_id": second_professional_id, "status": "assigned"},
            ]
        )

    assessment_sessions.execute = AsyncMock(side_effect=assessment_sessions_execute)

    profiles = _make_table_mock(
        "profiles",
        {
            "execute": AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "id": PROFESSIONAL_ID,
                            "display_name": "Alex Professional",
                            "username": "alexp",
                            "avatar_url": None,
                        },
                        {
                            "id": second_professional_id,
                            "display_name": "Other Candidate",
                            "username": "other",
                            "avatar_url": None,
                        },
                    ]
                )
            )
        },
    )
    profiles.select.return_value = profiles
    profiles.in_.return_value = profiles

    aura_scores = _make_table_mock(
        "aura_scores",
        {
            "execute": AsyncMock(
                return_value=MagicMock(
                    data=[
                        {
                            "volunteer_id": PROFESSIONAL_ID,
                            "badge_tier": "gold",
                            "competency_scores": {"communication": 75.0, "reliability": 85.0},
                        },
                        {
                            "volunteer_id": second_professional_id,
                            "badge_tier": "silver",
                            "competency_scores": {"communication": 92.0, "reliability": 84.0},
                        },
                    ]
                )
            )
        },
    )
    aura_scores.select.return_value = aura_scores
    aura_scores.in_.return_value = aura_scores

    tables = {
        "organizations": _make_table_mock(
            "organizations",
            {
                "execute": AsyncMock(
                    return_value=MagicMock(
                        data={"id": ORG_ID, "name": "Atlas Org", "logo_url": None, "owner_id": ORG_USER_ID}
                    )
                )
            },
        ),
        "screening_campaigns": screening_campaigns,
        "campaign_candidates": campaign_candidates,
        "competencies": competencies,
        "assessment_sessions": assessment_sessions,
        "profiles": profiles,
        "aura_scores": aura_scores,
    }

    db = MagicMock()
    db.table = MagicMock(side_effect=lambda name: tables[name])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        join_resp = await ac.post(
            f"/api/campaigns/public/{TOKEN}/join",
            headers={"Authorization": "Bearer fake-candidate"},
        )
        report_resp = await ac.get(
            f"/api/campaigns/{CAMPAIGN_ID}/report",
            headers={"Authorization": "Bearer fake-owner"},
        )

    assert join_resp.status_code == 200, join_resp.text
    join_body = join_resp.json()
    assert join_body["already_joined"] is False
    assert len(join_body["sessions"]) == 2
    assert len(join_inserted_sessions) == 2
    assert len(inserted_join_rows) == 1

    assert report_resp.status_code == 200, report_resp.text
    report_body = report_resp.json()
    assert report_body["campaign"]["id"] == CAMPAIGN_ID
    assert report_body["campaign"]["candidate_count"] == 2
    assert report_body["campaign"]["completed_count"] == 1
    assert len(report_body["candidates"]) == 2
    assert report_body["candidates"][0]["professional_id"] == PROFESSIONAL_ID
    assert report_body["candidates"][0]["campaign_score"] == 80.0
    assert report_body["candidates"][1]["campaign_score"] == 88.0


def _full_campaign_row() -> dict:
    return {
        "id": CAMPAIGN_ID,
        "org_id": ORG_ID,
        "created_by": ORG_USER_ID,
        "title": "Customer Support Lead",
        "description": "Candidate-facing campaign",
        "competency_slugs": ["communication", "reliability"],
        "invite_token": TOKEN,
        "status": "active",
        "deadline_days": 21,
        "candidate_cap": 42,
        "created_at": datetime.now(UTC).isoformat(),
    }


@pytest.mark.asyncio
async def test_report_paywall_blocks_without_access_returns_402():
    """org_billing_enabled=True + no entitlement → 402 PAYMENT_REQUIRED, report not built."""
    tables = {
        "organizations": _make_table_mock(
            "organizations",
            {"execute": AsyncMock(return_value=MagicMock(data={"id": ORG_ID, "name": "Atlas Org", "logo_url": None}))},
        ),
        "screening_campaigns": _make_table_mock(
            "screening_campaigns", {"execute": AsyncMock(return_value=MagicMock(data=_full_campaign_row()))}
        ),
    }
    db = MagicMock()
    db.table = MagicMock(side_effect=lambda name: tables[name])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    with (
        patch("app.routers.campaigns.settings") as ms,
        patch("app.routers.campaigns.org_has_report_access", new=AsyncMock(return_value=False)),
    ):
        ms.org_billing_enabled = True
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(f"/api/campaigns/{CAMPAIGN_ID}/report", headers={"Authorization": "Bearer owner"})

    assert resp.status_code == 402, resp.text
    body = resp.json()
    assert body["detail"]["code"] == "PAYMENT_REQUIRED"
    assert body["detail"]["campaign_id"] == CAMPAIGN_ID
    assert body["detail"]["unlock_url"].endswith(f"/{CAMPAIGN_ID}/unlock")


@pytest.mark.asyncio
async def test_report_paywall_allows_with_access_returns_200():
    """org_billing_enabled=True + entitlement granted → gate passes, report builds (200)."""
    tables = {
        "organizations": _make_table_mock(
            "organizations",
            {"execute": AsyncMock(return_value=MagicMock(data={"id": ORG_ID, "name": "Atlas Org", "logo_url": None}))},
        ),
        "screening_campaigns": _make_table_mock(
            "screening_campaigns", {"execute": AsyncMock(return_value=MagicMock(data=_full_campaign_row()))}
        ),
        # No members → report returns early with empty candidates (still 200).
        "campaign_candidates": _make_table_mock(
            "campaign_candidates", {"execute": AsyncMock(return_value=MagicMock(data=[]))}
        ),
    }
    db = MagicMock()
    db.table = MagicMock(side_effect=lambda name: tables[name])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override(ORG_USER_ID)

    with (
        patch("app.routers.campaigns.settings") as ms,
        patch("app.routers.campaigns.org_has_report_access", new=AsyncMock(return_value=True)),
    ):
        ms.org_billing_enabled = True
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(f"/api/campaigns/{CAMPAIGN_ID}/report", headers={"Authorization": "Bearer owner"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["campaign"]["id"] == CAMPAIGN_ID
