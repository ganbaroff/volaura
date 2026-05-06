"""HTTP-level endpoint tests for app/routers/badges.py.

Covers:
- GET /api/badges/issuer  (public, no auth)
- GET /api/badges/{professional_id}/credential  (public, no auth, SupabaseAdmin mock)

Pattern: TestClient + dependency_overrides to mock SupabaseAdmin.
Never hits real DB.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Helpers ────────────────────────────────────────────────────────────────────

VALID_UUID = str(uuid.uuid4())
ENDPOINT_ISSUER = "/api/badges/issuer"
ENDPOINT_CREDENTIAL = f"/api/badges/{VALID_UUID}/credential"
ENDPOINT_ME = "/api/badges/me"


def _make_admin_mock(profile_data=None, aura_data=None):
    """Build an AsyncClient mock that returns given data from maybe_single().execute()."""
    mock_db = MagicMock()

    # Chain: .table().select().eq().eq().maybe_single().execute()
    def _chain(*_args, **_kwargs):
        return mock_db

    mock_db.table = MagicMock(return_value=mock_db)
    mock_db.select = MagicMock(return_value=mock_db)
    mock_db.eq = MagicMock(return_value=mock_db)
    mock_db.maybe_single = MagicMock(return_value=mock_db)

    # Alternate execute results: first call → profile, second → aura
    call_count = {"n": 0}
    results = [
        MagicMock(data=profile_data),
        MagicMock(data=aura_data),
    ]

    async def _execute():
        idx = min(call_count["n"], len(results) - 1)
        call_count["n"] += 1
        return results[idx]

    mock_db.execute = _execute
    return mock_db


def _override_admin(mock_db):
    async def _dep():
        yield mock_db

    app.dependency_overrides[get_supabase_admin] = _dep
    return mock_db


def _override_user(mock_db, user_id: str = VALID_UUID):
    async def _db_dep():
        yield mock_db

    async def _user_dep():
        return user_id

    app.dependency_overrides[get_supabase_user] = _db_dep
    app.dependency_overrides[get_current_user_id] = _user_dep
    return mock_db


def _clear_overrides():
    app.dependency_overrides.pop(get_supabase_admin, None)
    app.dependency_overrides.pop(get_supabase_user, None)
    app.dependency_overrides.pop(get_current_user_id, None)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_dep_overrides():
    yield
    _clear_overrides()


# ── GET /api/badges/issuer ────────────────────────────────────────────────────


def test_issuer_200(client):
    resp = client.get(ENDPOINT_ISSUER)
    assert resp.status_code == 200


def test_issuer_response_shape(client):
    resp = client.get(ENDPOINT_ISSUER)
    body = resp.json()
    assert body["name"] == "Volaura"
    assert body["email"] == "badges@volaura.az"
    assert body["type"] == "Profile"
    assert "@context" in body
    assert body["url"] == "https://volaura.az"


def test_issuer_id_contains_base_url(client):
    resp = client.get(ENDPOINT_ISSUER)
    body = resp.json()
    assert "/api/badges/issuer" in body["id"]


# ── GET /api/badges/me ────────────────────────────────────────────────────────


def test_me_returns_empty_list_without_aura(client):
    mock_db = _make_admin_mock(profile_data={"badge_issued_at": None}, aura_data=None)
    _override_user(mock_db)

    resp = client.get(ENDPOINT_ME)

    assert resp.status_code == 200
    assert resp.json() == []


def test_me_returns_dashboard_badge_list(client):
    profile = {"badge_issued_at": "2026-01-01T00:00:00Z"}
    aura = {
        "total_score": 82.5,
        "badge_tier": "gold",
        "elite_status": False,
        "last_updated": "2026-03-15T12:00:00Z",
    }
    mock_db = _make_admin_mock(profile_data=profile, aura_data=aura)
    _override_user(mock_db)

    resp = client.get(ENDPOINT_ME)

    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["volunteer_id"] == VALID_UUID
    assert body[0]["badge_type"] == "aura"
    assert body[0]["tier"] == "gold"
    assert body[0]["earned_at"] == "2026-01-01T00:00:00Z"
    assert body[0]["metadata"]["total_score"] == 82.5


def test_me_returns_empty_list_for_none_tier(client):
    profile = {"badge_issued_at": None}
    aura = {
        "total_score": 10.0,
        "badge_tier": "none",
        "elite_status": False,
        "last_updated": "2026-03-15T12:00:00Z",
    }
    mock_db = _make_admin_mock(profile_data=profile, aura_data=aura)
    _override_user(mock_db)

    resp = client.get(ENDPOINT_ME)

    assert resp.status_code == 200
    assert resp.json() == []


# ── GET /api/badges/{professional_id}/credential — happy path ────────────────


def _setup_happy_path():
    profile = {
        "id": VALID_UUID,
        "username": "leyla_a",
        "display_name": "Leyla Aghayeva",
        "badge_issued_at": "2026-01-01T00:00:00Z",
    }
    aura = {
        "total_score": 82.5,
        "badge_tier": "gold",
        "elite_status": False,
        "last_updated": "2026-03-15T12:00:00Z",
        "visibility": "public",
    }
    mock_db = _make_admin_mock(profile_data=profile, aura_data=aura)
    _override_admin(mock_db)
    return mock_db


def test_credential_200(client):
    _setup_happy_path()
    resp = client.get(ENDPOINT_CREDENTIAL)
    assert resp.status_code == 200


def test_credential_vc_context(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    assert "https://www.w3.org/2018/credentials/v1" in body["@context"]
    assert "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.1.json" in body["@context"]


def test_credential_vc_type(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    assert "VerifiableCredential" in body["type"]
    assert "OpenBadgeCredential" in body["type"]


def test_credential_issuer_block(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    issuer = body["issuer"]
    assert issuer["name"] == "Volaura"
    assert issuer["type"] == "Profile"


def test_credential_subject_name(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    subject = body["credentialSubject"]
    assert subject["name"] == "Leyla Aghayeva"


def test_credential_result_score(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    result = body["credentialSubject"]["result"][0]
    assert result["value"] == "82.5"
    assert result["status"] == "Completed"


def test_credential_badge_tier_in_name(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    assert "Gold" in body["name"]


def test_credential_id_contains_professional_id(client):
    _setup_happy_path()
    body = client.get(ENDPOINT_CREDENTIAL).json()
    assert VALID_UUID in body["id"]


# ── GET /api/badges/{professional_id}/credential — 422 invalid UUID ───────────


def test_credential_invalid_uuid_422(client):
    mock_db = _make_admin_mock(profile_data=None, aura_data=None)
    _override_admin(mock_db)
    resp = client.get("/api/badges/not-a-uuid/credential")
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert detail["code"] == "INVALID_UUID"


def test_credential_uuid_with_wrong_format_422(client):
    mock_db = _make_admin_mock(profile_data=None, aura_data=None)
    _override_admin(mock_db)
    resp = client.get("/api/badges/12345/credential")
    assert resp.status_code == 422


# ── GET /api/badges/{professional_id}/credential — 404 no profile ─────────────


def test_credential_missing_profile_404(client):
    mock_db = _make_admin_mock(profile_data=None, aura_data=None)
    _override_admin(mock_db)
    resp = client.get(ENDPOINT_CREDENTIAL)
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "PROFILE_NOT_FOUND"


# ── GET /api/badges/{professional_id}/credential — 404 no AURA ───────────────


def test_credential_missing_aura_404(client):
    profile = {
        "id": VALID_UUID,
        "username": "leyla_a",
        "display_name": "Leyla Aghayeva",
        "badge_issued_at": None,
    }
    mock_db = _make_admin_mock(profile_data=profile, aura_data=None)
    _override_admin(mock_db)
    resp = client.get(ENDPOINT_CREDENTIAL)
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AURA_NOT_FOUND"


# ── GET /api/badges/{professional_id}/credential — hidden visibility 404 ──────


def test_credential_hidden_aura_404(client):
    profile = {
        "id": VALID_UUID,
        "username": "leyla_a",
        "display_name": "Leyla Aghayeva",
        "badge_issued_at": None,
    }
    aura = {
        "total_score": 70.0,
        "badge_tier": "silver",
        "elite_status": False,
        "last_updated": "2026-01-01T00:00:00Z",
        "visibility": "hidden",
    }
    mock_db = _make_admin_mock(profile_data=profile, aura_data=aura)
    _override_admin(mock_db)
    resp = client.get(ENDPOINT_CREDENTIAL)
    # Identical 404 as AURA_NOT_FOUND — prevents enumeration (CRIT-04 parity)
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "AURA_NOT_FOUND"


# ── Edge: display_name fallback to username ────────────────────────────────────


def test_credential_display_name_falls_back_to_username(client):
    profile = {
        "id": VALID_UUID,
        "username": "anon_user",
        "display_name": None,
        "badge_issued_at": None,
    }
    aura = {
        "total_score": 45.0,
        "badge_tier": "bronze",
        "elite_status": False,
        "last_updated": "2026-01-01T00:00:00Z",
        "visibility": "public",
    }
    mock_db = _make_admin_mock(profile_data=profile, aura_data=aura)
    _override_admin(mock_db)
    resp = client.get(ENDPOINT_CREDENTIAL)
    assert resp.status_code == 200
    assert resp.json()["credentialSubject"]["name"] == "anon_user"
