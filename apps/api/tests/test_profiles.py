"""Tests for /api/profiles endpoints."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

USER_ID = "uuid-profile-test"
NOW = datetime.now(UTC).isoformat()

PROFILE_ROW = {
    "id": USER_ID,
    "username": "voluser",
    "display_name": "Vol User",
    "bio": "I help people",
    "location": "Baku",
    "languages": ["az", "en"],
    "social_links": {},
    "is_public": True,
    "avatar_url": None,
    "badge_issued_at": None,
    "badge_open_badges_url": None,
    "created_at": NOW,
    "updated_at": NOW,
}


def _admin_override(db):
    async def _dep():
        yield db

    return _dep


def _user_override(db):
    async def _dep():
        yield db

    return _dep


def _uid_override(uid=USER_ID):
    async def _dep():
        return uid

    return _dep


def _make_mock_db():
    db = MagicMock()
    db.table = MagicMock(return_value=db)
    db.select = MagicMock(return_value=db)
    db.insert = MagicMock(return_value=db)
    db.update = MagicMock(return_value=db)
    db.eq = MagicMock(return_value=db)
    db.single = MagicMock(return_value=db)
    db.maybe_single = MagicMock(return_value=db)
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_get_my_profile_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=PROFILE_ROW))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "voluser"
    assert body["id"] == USER_ID


@pytest.mark.asyncio
async def test_get_my_profile_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_my_profile_success():
    db = _make_mock_db()
    admin_db = _make_mock_db()
    # First call: username check returns empty (not taken)
    # Second call: insert returns the new row
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username check
            MagicMock(data=[PROFILE_ROW]),  # insert result
        ]
    )
    # Admin: used for upsert_volunteer_embedding (fire-and-forget, caught in try/except)
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert resp.json()["username"] == "voluser"


@pytest.mark.asyncio
async def test_create_my_profile_username_taken():
    db = _make_mock_db()
    admin_db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=[{"id": "other-id"}]))
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "taken"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 409
    assert resp.json()["detail"]["code"] == "USERNAME_TAKEN"


@pytest.mark.asyncio
async def test_create_my_profile_invalid_username():
    db = _make_mock_db()
    admin_db = _make_mock_db()
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "ab"},  # too short
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422  # Pydantic validation


@pytest.mark.asyncio
async def test_update_my_profile_success():
    updated_row = {**PROFILE_ROW, "bio": "Updated bio"}
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=[updated_row]))
    admin_db = _make_mock_db()  # embedding update is best-effort (try/except)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/profiles/me",
            json={"bio": "Updated bio"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["bio"] == "Updated bio"


@pytest.mark.asyncio
async def test_update_my_profile_no_fields():
    db = _make_mock_db()
    admin_db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/profiles/me",
            json={},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "NO_FIELDS"


@pytest.mark.asyncio
async def test_get_public_profile_found():
    public_row = {
        "id": USER_ID,
        "username": "voluser",
        "display_name": "Vol User",
        "avatar_url": None,
        "bio": "I help people",
        "location": "Baku",
        "languages": ["az", "en"],
        "badge_issued_at": None,
    }
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=public_row))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/voluser")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["username"] == "voluser"


@pytest.mark.asyncio
async def test_get_public_profile_not_found():
    db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/ghost")

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


# ── GROWTH-2: Invite attribution ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_profile_with_invite_attribution():
    """invited_by_org_id stored + matching invite marked accepted."""
    user_db = _make_mock_db()
    admin_db = _make_mock_db()
    ORG_ID = "org-uuid-123"

    # user db: username check empty, insert succeeds
    user_db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username check
            MagicMock(data=[PROFILE_ROW]),  # insert
        ]
    )

    # admin db: get_user_by_id returns email, then invite update
    mock_user_obj = MagicMock()
    mock_user_obj.user = MagicMock()
    mock_user_obj.user.email = "invitee@example.com"
    admin_db.auth = MagicMock()
    admin_db.auth.admin = MagicMock()
    admin_db.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user_obj)
    admin_db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(user_db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser", "invited_by_org_id": ORG_ID},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert resp.json()["username"] == "voluser"
    # get_user_by_id was called to fetch email for invite update
    admin_db.auth.admin.get_user_by_id.assert_called_once_with(USER_ID)


@pytest.mark.asyncio
async def test_create_profile_without_invite_attribution():
    """Normal profile creation without invite_code: get_user_by_id NOT called."""
    user_db = _make_mock_db()
    admin_db = _make_mock_db()
    admin_db.auth = MagicMock()
    admin_db.auth.admin = MagicMock()
    admin_db.auth.admin.get_user_by_id = AsyncMock()

    user_db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),
            MagicMock(data=[PROFILE_ROW]),
        ]
    )
    admin_db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(user_db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    admin_db.auth.admin.get_user_by_id.assert_not_called()


# ── _anonymize_name unit tests ─────────────────────────────────────────────────


def test_anonymize_name_full_name():
    from app.routers.profiles import _anonymize_name

    assert _anonymize_name("Leyla Aliyeva") == "Leyla A."


def test_anonymize_name_single_word():
    from app.routers.profiles import _anonymize_name

    assert _anonymize_name("Leyla") == "Leyla"


def test_anonymize_name_none():
    from app.routers.profiles import _anonymize_name

    assert _anonymize_name(None) == "Professional"


def test_anonymize_name_empty_string():
    from app.routers.profiles import _anonymize_name

    assert _anonymize_name("") == "Professional"


def test_anonymize_name_whitespace_only():
    from app.routers.profiles import _anonymize_name

    assert _anonymize_name("   ") == "Professional"


def test_anonymize_name_long_first_name():
    from app.routers.profiles import _anonymize_name

    # First name capped at 20 chars
    long = "A" * 25
    result = _anonymize_name(f"{long} Smith")
    assert result == "A" * 20 + " S."


def test_anonymize_name_three_parts():
    from app.routers.profiles import _anonymize_name

    # Last part used for initial
    result = _anonymize_name("First Middle Last")
    assert result == "First L."


# ── GET /profiles/public ──────────────────────────────────────────────────────


def _make_org_db(caller_account_type: str = "organization", professionals: list | None = None):
    """Build admin DB mock for list_public_professionals."""
    db = MagicMock()
    call_count = {"n": 0}

    if professionals is None:
        professionals = [
            {
                "id": "pro-1",
                "username": "alice",
                "display_name": "Alice Babayeva",
                "avatar_url": None,
                "bio": "Event planner",
                "location": "Baku",
                "languages": ["az"],
                "aura_scores": [{"total_score": 82.5, "badge_tier": "Gold"}],
            }
        ]

    caller_result = MagicMock(data={"account_type": caller_account_type} if caller_account_type else None)
    professionals_result = MagicMock(data=professionals)

    async def _execute(*_a, **_kw):
        n = call_count["n"]
        call_count["n"] += 1
        return caller_result if n == 0 else professionals_result

    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.in_.return_value = t
    t.order.return_value = t
    t.range.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(side_effect=_execute)

    db.table = MagicMock(return_value=t)
    return db


@pytest.mark.asyncio
async def test_list_public_professionals_org_success():
    """Org caller → 200 with anonymized names."""
    db = _make_org_db(caller_account_type="organization")

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/public", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 1
    # SEC-03: display_name must be anonymized — "Alice B." not "Alice Babayeva"
    assert body[0]["display_name"] == "Alice B."
    assert body[0]["username"] == "alice"
    assert body[0]["total_score"] == 82.5
    assert body[0]["badge_tier"] == "Gold"


@pytest.mark.asyncio
async def test_list_public_professionals_non_org_403():
    """Non-org caller (professional) → 403 ORG_REQUIRED."""
    db = _make_org_db(caller_account_type="professional")

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/public", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "ORG_REQUIRED"


@pytest.mark.asyncio
async def test_list_public_professionals_no_profile_403():
    """Caller has no profile row → 403 ORG_REQUIRED."""
    db = _make_org_db(caller_account_type=None)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/public", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_public_professionals_empty_list():
    """Org caller, no professionals opted in → 200 empty list."""
    db = _make_org_db(caller_account_type="organization", professionals=[])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/public", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_public_professionals_aura_dict_not_list():
    """aura_scores returned as dict (direct join) instead of list — handled."""
    professionals = [
        {
            "id": "pro-2",
            "username": "bob",
            "display_name": "Bob K",
            "avatar_url": None,
            "bio": None,
            "location": None,
            "languages": [],
            "aura_scores": {"total_score": 65.0, "badge_tier": "Silver"},  # dict, not list
        }
    ]
    db = _make_org_db(caller_account_type="organization", professionals=professionals)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/public", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["total_score"] == 65.0


@pytest.mark.asyncio
async def test_list_public_professionals_no_aura():
    """Professional has no aura_scores — total_score and badge_tier are None."""
    professionals = [
        {
            "id": "pro-3",
            "username": "carol",
            "display_name": "Carol M",
            "avatar_url": None,
            "bio": None,
            "location": None,
            "languages": [],
            "aura_scores": None,
        }
    ]
    db = _make_org_db(caller_account_type="organization", professionals=professionals)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/public", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body[0]["total_score"] is None
    assert body[0]["badge_tier"] is None


@pytest.mark.asyncio
async def test_list_public_professionals_pagination_params():
    """limit/offset query params are accepted."""
    db = _make_org_db(caller_account_type="organization", professionals=[])

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/profiles/public?limit=10&offset=20",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_public_professionals_limit_out_of_range():
    """limit > 100 → 422 validation error."""
    db = _make_org_db(caller_account_type="organization")

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get(
            "/api/profiles/public?limit=9999",
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422


# ── POST /{professional_id}/verification-link ─────────────────────────────────

VERIF_PAYLOAD = {
    "verifier_name": "Dr. Smith",
    "verifier_org": "UNICEF",
    "competency_id": "communication",
}

VERIF_ROW = {
    "id": "verif-row-id",
    "volunteer_id": USER_ID,
    "created_by": USER_ID,
    "verifier_name": "Dr. Smith",
    "verifier_org": "UNICEF",
    "competency_id": "communication",
    "token": "fake-token-abc",
    "token_expires_at": NOW,
}


def _make_verif_db(profile_exists: bool = True, insert_succeeds: bool = True):
    db = _make_mock_db()
    profile_result = MagicMock(data={"id": USER_ID} if profile_exists else None)
    insert_result = MagicMock(data=[VERIF_ROW] if insert_succeeds else None)
    db.execute = AsyncMock(side_effect=[profile_result, insert_result])
    return db


@pytest.mark.asyncio
async def test_create_verification_link_success():
    """Self-request, profile exists → 201 with token and verify_url."""
    db = _make_verif_db(profile_exists=True, insert_succeeds=True)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{USER_ID}/verification-link",
            json=VERIF_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    body = resp.json()
    assert "token" in body
    assert "verify_url" in body
    assert body["verifier_name"] == "Dr. Smith"
    assert body["competency_id"] == "communication"


@pytest.mark.asyncio
async def test_create_verification_link_403_not_self():
    """Requesting for another user → 403 FORBIDDEN."""
    db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()  # USER_ID

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/someone-elses-id/verification-link",
            json=VERIF_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_create_verification_link_404_no_profile():
    """Profile not found → 404 PROFILE_NOT_FOUND."""
    db = _make_verif_db(profile_exists=False)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{USER_ID}/verification-link",
            json=VERIF_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_create_verification_link_422_invalid_competency():
    """Invalid competency_id → 422 validation error (Pydantic)."""
    db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{USER_ID}/verification-link",
            json={**VERIF_PAYLOAD, "competency_id": "flying"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_verification_link_422_short_verifier_name():
    """verifier_name too short (<2 chars) → 422."""
    db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{USER_ID}/verification-link",
            json={**VERIF_PAYLOAD, "verifier_name": "X"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_verification_link_500_insert_fails():
    """DB insert returns empty data → 500 CREATE_FAILED."""
    db = _make_verif_db(profile_exists=True, insert_succeeds=False)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{USER_ID}/verification-link",
            json=VERIF_PAYLOAD,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "CREATE_FAILED"


@pytest.mark.asyncio
async def test_create_verification_link_no_verifier_org():
    """verifier_org is optional — None is accepted."""
    db = _make_verif_db(profile_exists=True, insert_succeeds=True)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    payload = {**VERIF_PAYLOAD}
    del payload["verifier_org"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            f"/api/profiles/{USER_ID}/verification-link",
            json=payload,
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201


# ── GET /me/views ─────────────────────────────────────────────────────────────


def _make_views_db(total: int = 3, week: int = 1, recent: list | None = None):
    """Build user DB mock for get_my_profile_views.

    Endpoint makes 3 sequential selects on notifications table:
      1. total count
      2. week count
      3. recent list (last 10)
    """
    if recent is None:
        recent = [{"title": "TechCorp viewed your profile", "created_at": NOW}]

    total_result = MagicMock(data=[], count=total)
    week_result = MagicMock(data=[], count=week)
    recent_result = MagicMock(data=recent)

    call_count = {"n": 0}

    async def _execute(*_a, **_kw):
        n = call_count["n"]
        call_count["n"] += 1
        if n == 0:
            return total_result
        elif n == 1:
            return week_result
        else:
            return recent_result

    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.gte.return_value = t
    t.order.return_value = t
    t.limit.return_value = t
    t.execute = AsyncMock(side_effect=_execute)

    db = MagicMock()
    db.table = MagicMock(return_value=t)
    return db


@pytest.mark.asyncio
async def test_get_my_profile_views_success():
    """GET /me/views → 200 with total_views, week_views, recent_viewers."""
    db = _make_views_db(total=5, week=2, recent=[{"title": "Acme viewed your profile", "created_at": NOW}])

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/views", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total_views"] == 5
    assert body["week_views"] == 2
    assert len(body["recent_viewers"]) == 1
    assert body["recent_viewers"][0]["name"] == "Acme"


@pytest.mark.asyncio
async def test_get_my_profile_views_empty():
    """GET /me/views with no views → zeros and empty list."""
    db = _make_views_db(total=0, week=0, recent=[])

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/views", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total_views"] == 0
    assert body["week_views"] == 0
    assert body["recent_viewers"] == []


@pytest.mark.asyncio
async def test_get_my_profile_views_count_none():
    """count=None on notifications table → treated as 0 (no crash)."""
    total_result = MagicMock(data=[], count=None)
    week_result = MagicMock(data=[], count=None)
    recent_result = MagicMock(data=[])

    call_count = {"n": 0}

    async def _execute(*_a, **_kw):
        n = call_count["n"]
        call_count["n"] += 1
        if n == 0:
            return total_result
        elif n == 1:
            return week_result
        else:
            return recent_result

    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.gte.return_value = t
    t.order.return_value = t
    t.limit.return_value = t
    t.execute = AsyncMock(side_effect=_execute)

    db = MagicMock()
    db.table = MagicMock(return_value=t)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/views", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total_views"] == 0
    assert body["week_views"] == 0


# ── GET /me/verifications ─────────────────────────────────────────────────────


def _make_verifications_db(
    regs: list | None = None,
    events: list | None = None,
    organizers: list | None = None,
):
    """Build user DB mock for get_my_verifications.

    Call order per registration:
      1. registrations fetch (one call total)
      2. events lookup (once per registration)
      3. profiles lookup for organizer (once per registration, if organizer_id present)
    """
    if regs is None:
        regs = [
            {
                "id": "reg-1",
                "event_id": "event-1",
                "coordinator_rating": 4,
                "coordinator_feedback": "Great work",
                "coordinator_rated_at": NOW,
            }
        ]
    if events is None:
        events = [{"title": "Clean Baku", "organizer_id": "org-profile-id"}]
    if organizers is None:
        organizers = [{"display_name": "GreenAz", "username": "greenaz"}]

    results = (
        [MagicMock(data=regs)]
        + [MagicMock(data=events) for _ in regs]
        + [MagicMock(data=organizers) for _ in regs if events]
    )
    call_count = {"n": 0}

    async def _execute(*_a, **_kw):
        n = call_count["n"]
        call_count["n"] += 1
        if n < len(results):
            return results[n]
        return MagicMock(data=[])

    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.not_ = t
    t.is_ = MagicMock(return_value=t)
    t.order.return_value = t
    t.limit.return_value = t
    t.execute = AsyncMock(side_effect=_execute)

    db = MagicMock()
    db.table = MagicMock(return_value=t)
    return db


@pytest.mark.asyncio
async def test_get_my_verifications_success():
    """GET /me/verifications → 200 with verification list."""
    db = _make_verifications_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/verifications", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["rating"] == 4
    assert body[0]["verifier_name"] == "GreenAz"
    assert body[0]["competency_id"] == "event_performance"
    assert body[0]["comment"] == "Great work"


@pytest.mark.asyncio
async def test_get_my_verifications_empty():
    """No rated registrations → 200 with empty list."""
    db = _make_verifications_db(regs=[], events=[], organizers=[])

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/verifications", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_get_my_verifications_exception_returns_empty():
    """DB exception on fetch → graceful 200 with empty list (defensive)."""
    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.not_ = t
    t.is_ = MagicMock(return_value=t)
    t.order.return_value = t
    t.limit.return_value = t
    t.execute = AsyncMock(side_effect=Exception("DB error"))

    db = MagicMock()
    db.table = MagicMock(return_value=t)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/verifications", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["data"] == []


@pytest.mark.asyncio
async def test_get_my_verifications_no_organizer_id():
    """Event has no organizer_id → organizer defaults to 'Coordinator'."""
    regs = [
        {
            "id": "reg-2",
            "event_id": "event-2",
            "coordinator_rating": 3,
            "coordinator_feedback": None,
            "coordinator_rated_at": NOW,
        }
    ]
    # Event without organizer_id
    events = [{"title": "Tree Plant", "organizer_id": None}]

    call_count = {"n": 0}
    results = [MagicMock(data=regs), MagicMock(data=events)]

    async def _execute(*_a, **_kw):
        n = call_count["n"]
        call_count["n"] += 1
        return results[n] if n < len(results) else MagicMock(data=[])

    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.not_ = t
    t.is_ = MagicMock(return_value=t)
    t.order.return_value = t
    t.limit.return_value = t
    t.execute = AsyncMock(side_effect=_execute)

    db = MagicMock()
    db.table = MagicMock(return_value=t)

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me/verifications", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body[0]["verifier_name"] == "Coordinator"
    assert body[0]["comment"] is None


# ── GET /profiles/{username} — public profile with percentile ─────────────────


def _make_public_profile_db(
    profile_data: dict | None = None,
    score: float | None = 78.0,
    lower_count: int = 45,
    total_count: int = 100,
):
    """Build admin DB mock for get_public_profile (includes percentile queries)."""
    if profile_data is None:
        profile_data = {
            "id": USER_ID,
            "username": "voluser",
            "display_name": "Vol User",
            "avatar_url": None,
            "bio": "I help",
            "location": "Baku",
            "languages": ["az"],
            "badge_issued_at": None,
            "registration_number": None,
            "registration_tier": None,
        }

    score_result = MagicMock(data={"total_score": score} if score is not None else None)
    lower_result = MagicMock(count=lower_count)
    total_result = MagicMock(count=total_count)

    call_count = {"n": 0}
    results = [MagicMock(data=profile_data), score_result, lower_result, total_result]

    async def _execute(*_a, **_kw):
        n = call_count["n"]
        call_count["n"] += 1
        return results[n] if n < len(results) else MagicMock(data=None)

    t = MagicMock()
    t.select.return_value = t
    t.eq.return_value = t
    t.lt.return_value = t
    t.maybe_single.return_value = t
    t.execute = AsyncMock(side_effect=_execute)

    db = MagicMock()
    db.table = MagicMock(return_value=t)
    return db


@pytest.mark.asyncio
async def test_get_public_profile_with_percentile():
    """GET /{username} → percentile_rank computed correctly."""
    db = _make_public_profile_db(score=78.0, lower_count=45, total_count=100)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/voluser")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    body = resp.json()
    assert body["percentile_rank"] == 45.0  # 45/100 * 100


@pytest.mark.asyncio
async def test_get_public_profile_no_aura_no_percentile():
    """User with no aura score → percentile_rank is None."""
    db = _make_public_profile_db(score=None)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/voluser")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["percentile_rank"] is None


@pytest.mark.asyncio
async def test_get_public_profile_zero_total_no_percentile():
    """total_count == 0 → percentile_rank is None (avoid div-by-zero)."""
    db = _make_public_profile_db(score=60.0, lower_count=0, total_count=0)

    app.dependency_overrides[get_supabase_admin] = _admin_override(db)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/voluser")

    app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["percentile_rank"] is None


# ── Profile update edge cases ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_my_profile_not_found():
    """PUT /me with valid field but profile missing → 404."""
    db = _make_mock_db()
    admin_db = _make_mock_db()
    db.execute = AsyncMock(return_value=MagicMock(data=None))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/profiles/me",
            json={"bio": "new bio"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_my_profile_empty_data_returns_404_not_422():
    """PUT /me with only None fields → 422 NO_FIELDS (exclude_none produces empty dict)."""
    db = _make_mock_db()
    admin_db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    # Sending null values that all get excluded by exclude_none=True
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.put(
            "/api/profiles/me",
            json={"display_name": None, "bio": None},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422
    assert resp.json()["detail"]["code"] == "NO_FIELDS"


@pytest.mark.asyncio
async def test_create_my_profile_insert_failure():
    """POST /me — insert returns no data → 500 CREATE_FAILED."""
    db = _make_mock_db()
    admin_db = _make_mock_db()
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username check: not taken
            MagicMock(data=None),  # insert: fails
        ]
    )
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "newuser"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 500
    assert resp.json()["detail"]["code"] == "CREATE_FAILED"


@pytest.mark.asyncio
async def test_create_my_profile_invalid_account_type():
    """POST /me with invalid account_type → 422."""
    db = _make_mock_db()
    admin_db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "validuser", "account_type": "superadmin"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_my_profile_invalid_org_type():
    """POST /me with invalid org_type → 422."""
    db = _make_mock_db()
    admin_db = _make_mock_db()

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "validuser", "account_type": "organization", "org_type": "alien"},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_my_profile_age_confirmed_sets_terms_at():
    """age_confirmed=True → terms_accepted_at is written (non-null in insert data)."""
    inserted_payloads: list[dict] = []

    db = _make_mock_db()
    admin_db = _make_mock_db()

    def capturing_insert(data: dict):
        inserted_payloads.append(data)
        return db

    db.insert = MagicMock(side_effect=capturing_insert)

    db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username check
            MagicMock(data=[PROFILE_ROW]),  # insert
        ]
    )
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser", "age_confirmed": True},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201
    assert len(inserted_payloads) == 1
    assert "terms_accepted_at" in inserted_payloads[0]
    assert inserted_payloads[0]["age_confirmed"] is True


@pytest.mark.asyncio
async def test_age_confirmed_false_omits_terms_accepted_at():
    """GDPR Art. 8: age_confirmed=False → terms_accepted_at is ABSENT (not just None)."""
    inserted_payloads: list[dict] = []

    db = _make_mock_db()
    admin_db = _make_mock_db()

    def capturing_insert(data: dict):
        inserted_payloads.append(data)
        return db

    db.insert = MagicMock(side_effect=capturing_insert)
    db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username uniqueness check
            MagicMock(data=[PROFILE_ROW]),  # insert result
        ]
    )
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        await ac.post(
            "/api/profiles/me",
            json={"username": "voluser", "age_confirmed": False},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert len(inserted_payloads) == 1
    assert "terms_accepted_at" not in inserted_payloads[0]


@pytest.mark.asyncio
async def test_age_confirmed_false_profile_still_created():
    """GDPR Art. 8: age_confirmed=False is non-blocking — profile still returns 201."""
    db = _make_mock_db()
    admin_db = _make_mock_db()

    db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username uniqueness check
            MagicMock(data=[PROFILE_ROW]),  # insert result
        ]
    )
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/profiles/me",
            json={"username": "voluser", "age_confirmed": False},
            headers={"Authorization": "Bearer fake"},
        )

    app.dependency_overrides.clear()

    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_age_confirmed_false_logs_art8_warning():
    """GDPR Art. 8: age_confirmed=False triggers logger.warning with 'GDPR Art. 8 gap'."""
    db = _make_mock_db()
    admin_db = _make_mock_db()

    db.execute = AsyncMock(
        side_effect=[
            MagicMock(data=[]),  # username uniqueness check
            MagicMock(data=[PROFILE_ROW]),  # insert result
        ]
    )
    admin_db.execute = AsyncMock(return_value=MagicMock(data=[]))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_supabase_admin] = _admin_override(admin_db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    with patch("app.routers.profiles.logger") as mock_logger:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            await ac.post(
                "/api/profiles/me",
                json={"username": "voluser", "age_confirmed": False},
                headers={"Authorization": "Bearer fake"},
            )

    app.dependency_overrides.clear()

    mock_logger.warning.assert_called_once()
    warning_msg = mock_logger.warning.call_args[0][0]
    assert "GDPR Art. 8 gap" in warning_msg


@pytest.mark.asyncio
async def test_get_my_profile_db_exception_returns_404():
    """DB exception on profile fetch → 404 PROFILE_NOT_FOUND (except path)."""
    db = _make_mock_db()
    db.execute = AsyncMock(side_effect=Exception("connection lost"))

    app.dependency_overrides[get_supabase_user] = _user_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/api/profiles/me", headers={"Authorization": "Bearer fake"})

    app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"
