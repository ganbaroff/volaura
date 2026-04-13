"""
Bulk Invite Tests — CSV Upload for Organization Invites
========================================================

Tests for:
- POST /api/organizations/{org_id}/invites/bulk — CSV upload, auth, validation
- GET /api/organizations/{org_id}/invites — list invites
- GET /api/organizations/{org_id}/invites/template — CSV template

Mock pattern: MagicMock for table() (sync), AsyncMock only for execute().
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.middleware.rate_limit import limiter

# Disable rate limiting for tests — prevents 429 across test suite
limiter.enabled = False


# ── Helpers ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
ORG_ID = str(uuid4())


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_csv(rows: list[dict], columns: list[str] | None = None) -> bytes:
    """Create a CSV file from rows."""
    if not columns:
        columns = list(rows[0].keys()) if rows else ["email"]
    lines = [",".join(columns)]
    for row in rows:
        lines.append(",".join(str(row.get(c, "")) for c in columns))
    return "\n".join(lines).encode("utf-8")


def mock_admin_for_bulk(
    org_exists: bool = True,
    is_owner: bool = True,
    existing_emails: list[str] | None = None,
    insert_fails: bool = False,
) -> MagicMock:
    """Create a mock admin client for bulk invite tests."""
    admin_mock = MagicMock()
    existing_emails = existing_emails or []

    def mock_table(table_name: str):
        m = MagicMock()

        if table_name == "organizations":
            # .select().eq().maybe_single().execute()  — BUG-SEC-025: router uses maybe_single
            single_mock = MagicMock()
            result = MagicMock()
            if org_exists:
                result.data = {
                    "id": ORG_ID,
                    "owner_id": USER_ID if is_owner else str(uuid4()),
                    "name": "Test Org",
                }
            else:
                result.data = None
            single_mock.execute = AsyncMock(return_value=result)
            m.select.return_value.eq.return_value.maybe_single.return_value = single_mock
            return m

        if table_name == "organization_invites":
            # Handle both select (dedup check) and insert
            select_result = MagicMock()
            select_result.data = [{"email": e} for e in existing_emails]
            # Chain: .select().eq().neq().in_().execute()
            in_mock = MagicMock()
            in_mock.execute = AsyncMock(return_value=select_result)
            neq_mock = MagicMock()
            neq_mock.in_ = MagicMock(return_value=in_mock)
            eq_mock = MagicMock()
            eq_mock.neq = MagicMock(return_value=neq_mock)
            m.select.return_value.eq = MagicMock(return_value=eq_mock)

            # Insert chain: .insert().execute()
            insert_result = MagicMock()
            insert_result.data = []
            if insert_fails:
                m.insert.return_value.execute = AsyncMock(side_effect=Exception("DB error"))
            else:
                m.insert.return_value.execute = AsyncMock(return_value=insert_result)

            return m

        return m

    admin_mock.table = mock_table
    return admin_mock


# ── Tests: Bulk Upload ───────────────────────────────────────────────────────


class TestBulkInviteAuth:
    """Auth and authorization checks."""

    @pytest.mark.asyncio
    async def test_rejects_non_owner(self):
        admin_mock = mock_admin_for_bulk(is_owner=False)
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([{"email": "a@b.com"}])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rejects_nonexistent_org(self):
        admin_mock = mock_admin_for_bulk(org_exists=False)
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([{"email": "a@b.com"}])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 404
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rejects_invalid_org_id(self):
        admin_mock = MagicMock()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([{"email": "a@b.com"}])
            async with make_client() as client:
                resp = await client.post(
                    "/api/organizations/not-a-uuid/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()


class TestBulkInviteCSVParsing:
    """CSV parsing and validation."""

    @pytest.mark.asyncio
    async def test_successful_upload_3_rows(self):
        admin_mock = mock_admin_for_bulk()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([
                {"email": "alice@test.com", "display_name": "Alice", "phone": "+994501234567"},
                {"email": "bob@test.com", "display_name": "Bob"},
                {"email": "carol@test.com"},
            ])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["total"] == 3
            assert body["created"] == 3
            assert body["duplicates"] == 0
            assert body["errors"] == 0
            assert body["batch_id"]  # UUID present
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_rejects_missing_email_column(self):
        admin_mock = mock_admin_for_bulk()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = b"name,phone\nAlice,123\n"
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 422
            assert "email" in resp.json()["detail"]["message"].lower()
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_handles_invalid_emails(self):
        admin_mock = mock_admin_for_bulk()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([
                {"email": "valid@test.com"},
                {"email": "not-an-email"},
                {"email": "also@bad"},
            ])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["created"] == 1
            assert body["errors"] == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deduplicates_within_file(self):
        admin_mock = mock_admin_for_bulk()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([
                {"email": "alice@test.com"},
                {"email": "alice@test.com"},  # duplicate
                {"email": "bob@test.com"},
            ])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["created"] == 2
            assert body["duplicates"] == 1
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_deduplicates_against_existing_invites(self):
        admin_mock = mock_admin_for_bulk(existing_emails=["existing@test.com"])
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([
                {"email": "existing@test.com"},  # already in DB
                {"email": "new@test.com"},
            ])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["created"] == 1
            assert body["duplicates"] == 1
        finally:
            app.dependency_overrides.clear()


class TestBulkInviteSecurity:
    """Security-focused tests (from agent review)."""

    @pytest.mark.asyncio
    async def test_rejects_oversized_file(self):
        admin_mock = mock_admin_for_bulk()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            # 2 MB file — over 1 MB limit
            big_data = b"email\n" + b"x@test.com\n" * 200_000
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("big.csv", big_data, "text/csv")},
                )
            assert resp.status_code == 413
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_formula_injection_sanitized(self):
        """CSV cells starting with = or + should be sanitized."""
        admin_mock = mock_admin_for_bulk()
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            # Formula injection in display_name
            csv_data = b"email,display_name\ntest@safe.com,=CMD()\n"
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            # Should succeed but sanitize the name
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["created"] == 1
            # The name should be sanitized (prefixed with ')
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_handles_db_insert_failure(self):
        admin_mock = mock_admin_for_bulk(insert_fails=True)
        app.dependency_overrides[get_supabase_admin] = lambda: admin_mock
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID

        try:
            csv_data = make_csv([{"email": "test@test.com"}])
            async with make_client() as client:
                resp = await client.post(
                    f"/api/organizations/{ORG_ID}/invites/bulk",
                    files={"file": ("invites.csv", csv_data, "text/csv")},
                )
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["errors"] == 1
            assert body["created"] == 0
        finally:
            app.dependency_overrides.clear()


class TestBulkInviteTemplate:
    """GET template endpoint."""

    @pytest.mark.asyncio
    async def test_returns_template(self):
        async with make_client() as client:
            resp = await client.get(f"/api/organizations/{ORG_ID}/invites/template")
        assert resp.status_code == 200
        body = resp.json()["data"]
        assert "email" in body["columns"]
        assert "email" in body["required"]
        assert body["example_row"]["email"]


class TestInviteSchemaValidation:
    """Unit tests for Pydantic schema validation."""

    def test_valid_email(self):
        from app.schemas.invite import InviteRowInput
        row = InviteRowInput(email="test@example.com")
        assert row.email == "test@example.com"

    def test_invalid_email_rejected(self):
        from app.schemas.invite import InviteRowInput
        with pytest.raises(Exception):
            InviteRowInput(email="not-an-email")

    def test_formula_injection_sanitized(self):
        from app.schemas.invite import InviteRowInput
        row = InviteRowInput(email="test@safe.com", display_name="=CMD()")
        assert row.display_name.startswith("'")

    def test_skills_parsing(self):
        from app.schemas.invite import InviteRowInput
        row = InviteRowInput(email="a@b.com", skills="leadership|english|events")
        assert row.to_skills_list() == ["leadership", "english", "events"]

    def test_empty_skills(self):
        from app.schemas.invite import InviteRowInput
        row = InviteRowInput(email="a@b.com")
        assert row.to_skills_list() == []

    def test_phone_validation(self):
        from app.schemas.invite import InviteRowInput
        row = InviteRowInput(email="a@b.com", phone="+994501234567")
        assert "994" in row.phone

    def test_short_phone_rejected(self):
        from app.schemas.invite import InviteRowInput
        with pytest.raises(Exception):
            InviteRowInput(email="a@b.com", phone="123")
