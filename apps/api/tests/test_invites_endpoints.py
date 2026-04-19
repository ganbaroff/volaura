"""HTTP endpoint tests for the invites router.

Covers:
- GET  /api/organizations/{org_id}/invites/template   — CSV template
- POST /api/organizations/{org_id}/invites/bulk       — bulk CSV invite
- GET  /api/organizations/{org_id}/invites            — list invites
"""

from __future__ import annotations

import io
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

USER_ID = str(uuid4())
ORG_ID = str(uuid4())
OTHER_USER_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token"}

ORG_ROW = {"id": ORG_ID, "owner_id": USER_ID, "name": "Volaura Org"}


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, side_effect=None) -> MagicMock:
    result = MagicMock()
    result.data = data
    result.count = None

    execute = AsyncMock(side_effect=side_effect) if side_effect else AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "gte", "order", "limit", "update", "insert", "upsert"):
        getattr(chain, method).return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute = execute
    return chain


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    async def _override():
        return uid

    return _override


def make_db_for_bulk(org_row=None, existing_invites=None, insert_success=True) -> MagicMock:
    """Build a DB mock that handles the multi-table calls in bulk_invite_professionals."""
    db = MagicMock()

    org_result = MagicMock()
    org_result.data = org_row
    org_execute = AsyncMock(return_value=org_result)

    org_chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "order", "limit"):
        getattr(org_chain, method).return_value = org_chain
    org_chain.maybe_single.return_value = org_chain
    org_chain.execute = org_execute

    invites_result = MagicMock()
    invites_result.data = existing_invites or []

    if not insert_success:
        insert_execute = AsyncMock(side_effect=Exception("DB insert failed"))
    else:
        insert_execute = AsyncMock(return_value=invites_result)

    invites_chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "order", "limit", "insert"):
        getattr(invites_chain, method).return_value = invites_chain
    invites_chain.maybe_single.return_value = invites_chain
    invites_chain.execute = insert_execute

    def dispatch(name: str) -> MagicMock:
        if name == "organizations":
            return org_chain
        if name == "organization_invites":
            return invites_chain
        return make_chain(data=[])

    db.table.side_effect = dispatch
    return db


def make_db_for_list(org_row=None, invites_data=None) -> MagicMock:
    db = MagicMock()

    org_result = MagicMock()
    org_result.data = org_row
    org_execute = AsyncMock(return_value=org_result)

    invites_result = MagicMock()
    invites_result.data = invites_data or []
    invites_execute = AsyncMock(return_value=invites_result)

    org_chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "order", "limit"):
        getattr(org_chain, method).return_value = org_chain
    org_chain.maybe_single.return_value = org_chain
    org_chain.execute = org_execute

    invites_chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "order", "limit"):
        getattr(invites_chain, method).return_value = invites_chain
    invites_chain.maybe_single.return_value = invites_chain
    invites_chain.execute = invites_execute

    def dispatch(name: str) -> MagicMock:
        if name == "organizations":
            return org_chain
        if name == "organization_invites":
            return invites_chain
        return make_chain(data=[])

    db.table.side_effect = dispatch
    return db


def csv_file(content: str, filename: str = "invites.csv") -> dict:
    return {"file": (filename, io.BytesIO(content.encode("utf-8")), "text/csv")}


# ── GET /api/organizations/{org_id}/invites/template ─────────────────────────


class TestDownloadInviteTemplate:
    @pytest.mark.asyncio
    async def test_returns_template_schema(self):
        async with make_client() as client:
            r = await client.get(f"/api/organizations/{ORG_ID}/invites/template")
        assert r.status_code == 200
        body = r.json()
        assert "data" in body
        assert "columns" in body["data"]
        assert "email" in body["data"]["columns"]
        assert "required" in body["data"]
        assert body["data"]["required"] == ["email"]

    @pytest.mark.asyncio
    async def test_template_includes_example_row(self):
        async with make_client() as client:
            r = await client.get(f"/api/organizations/{ORG_ID}/invites/template")
        body = r.json()["data"]
        assert "example_row" in body
        assert "email" in body["example_row"]

    @pytest.mark.asyncio
    async def test_template_public_no_auth_needed(self):
        async with make_client() as client:
            r = await client.get(f"/api/organizations/{ORG_ID}/invites/template")
        assert r.status_code == 200


# ── POST /api/organizations/{org_id}/invites/bulk ─────────────────────────────


class TestBulkInvite:
    @pytest.mark.asyncio
    async def test_valid_csv_returns_207(self):
        db = make_db_for_bulk(org_row=ORG_ROW, existing_invites=[])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email,display_name\nahmed@example.com,Ahmed Mammadov\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 207
            body = r.json()
            assert "data" in body
            assert body["data"]["created"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_org_not_found_returns_404(self):
        db = make_db_for_bulk(org_row=None)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\nahmed@example.com\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_non_owner_returns_403(self):
        other_org = {"id": ORG_ID, "owner_id": OTHER_USER_ID, "name": "Other Org"}
        db = make_db_for_bulk(org_row=other_org)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\nahmed@example.com\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_missing_email_column_returns_422(self):
        db = make_db_for_bulk(org_row=ORG_ROW)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "display_name,phone\nAhmed,+994501234567\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "MISSING_COLUMN"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_empty_csv_returns_422(self):
        db = make_db_for_bulk(org_row=ORG_ROW)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\n"  # header only, no data rows
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "EMPTY_CSV"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_duplicate_email_in_file_marked_as_duplicate(self):
        db = make_db_for_bulk(org_row=ORG_ROW, existing_invites=[])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\nahmed@example.com\nahmed@example.com\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 207
            body = r.json()["data"]
            assert body["duplicates"] == 1
            assert body["created"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_already_invited_email_marked_as_duplicate(self):
        existing = [{"email": "ahmed@example.com"}]
        db = make_db_for_bulk(org_row=ORG_ROW, existing_invites=existing)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\nahmed@example.com\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 207
            body = r.json()["data"]
            assert body["duplicates"] == 1
            assert body["created"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_invalid_email_format_is_error_row(self):
        db = make_db_for_bulk(org_row=ORG_ROW, existing_invites=[])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\nnot-an-email\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 207
            body = r.json()["data"]
            assert body["errors"] == 1
            assert body["created"] == 0
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_invalid_org_id_uuid_returns_422(self):
        db = make_db_for_bulk(org_row=ORG_ROW)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\nahmed@example.com\n"
            async with make_client() as client:
                r = await client.post(
                    "/api/organizations/not-a-uuid/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_UUID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_multiple_valid_emails_all_created(self):
        db = make_db_for_bulk(org_row=ORG_ROW, existing_invites=[])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            csv_content = "email\na@example.com\nb@example.com\nc@example.com\n"
            async with make_client() as client:
                r = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files=csv_file(csv_content),
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 207
            body = r.json()["data"]
            assert body["created"] == 3
            assert body["total"] == 3
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        csv_content = "email\nahmed@example.com\n"
        async with make_client() as client:
            r = await client.post(
                f"/api/organizations/{ORG_ID}/invites/bulk",
                files=csv_file(csv_content),
            )
        assert r.status_code == 401


# ── GET /api/organizations/{org_id}/invites ────────────────────────────────────


class TestListInvites:
    @pytest.mark.asyncio
    async def test_owner_can_list_invites(self):
        invite_row = {
            "id": str(uuid4()),
            "email": "ahmed@example.com",
            "display_name": "Ahmed",
            "status": "pending",
            "created_at": "2026-04-15T10:00:00Z",
            "accepted_at": None,
        }
        db = make_db_for_list(org_row={"id": ORG_ID, "owner_id": USER_ID}, invites_data=[invite_row])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get(f"/api/organizations/{ORG_ID}/invites", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert isinstance(body, list)
            assert body[0]["email"] == "ahmed@example.com"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_non_owner_returns_403(self):
        db = make_db_for_list(org_row={"id": ORG_ID, "owner_id": OTHER_USER_ID})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get(f"/api/organizations/{ORG_ID}/invites", headers=AUTH_HEADERS)
            assert r.status_code == 403
            assert r.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_org_not_found_returns_403(self):
        """Returns 403 for missing org (not 404) — avoids information disclosure."""
        db = make_db_for_list(org_row=None)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get(f"/api/organizations/{ORG_ID}/invites", headers=AUTH_HEADERS)
            assert r.status_code == 403
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_empty_invites_returns_empty_list(self):
        db = make_db_for_list(org_row={"id": ORG_ID, "owner_id": USER_ID}, invites_data=[])
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get(f"/api/organizations/{ORG_ID}/invites", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json() == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_invalid_org_id_uuid_returns_422(self):
        db = make_db_for_list()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/organizations/not-a-uuid/invites", headers=AUTH_HEADERS)
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_UUID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_invalid_status_filter_returns_422(self):
        db = make_db_for_list(org_row={"id": ORG_ID, "owner_id": USER_ID})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get(
                    f"/api/organizations/{ORG_ID}/invites?status=invalid_status",
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
            assert r.json()["detail"]["code"] == "INVALID_STATUS"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        async with make_client() as client:
            r = await client.get(f"/api/organizations/{ORG_ID}/invites")
        assert r.status_code == 401
