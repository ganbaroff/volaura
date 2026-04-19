"""Unit tests for invite router and schemas.

Coverage:
- app/schemas/invite.py — pure unit tests (no async needed)
- app/routers/invites.py — async router tests via httpx ASGITransport

54 tests total (33 schema + 21 router).
"""

from __future__ import annotations

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.schemas.invite import (
    BulkInviteResponse,
    InviteListResponse,
    InviteRowInput,
    InviteRowResult,
    _sanitize_cell,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_ORG_ID = "11111111-1111-1111-1111-111111111111"
VALID_USER_ID = "22222222-2222-2222-2222-222222222222"
VALID_BATCH_ID = "33333333-3333-3333-3333-333333333333"

# Routes are mounted under /api/ prefix
BULK_URL = f"/api/organizations/{VALID_ORG_ID}/invites/bulk"
LIST_URL = f"/api/organizations/{VALID_ORG_ID}/invites"
TEMPLATE_URL = f"/api/organizations/{VALID_ORG_ID}/invites/template"


# ---------------------------------------------------------------------------
# Dep-override helpers
# ---------------------------------------------------------------------------


def _make_chain(execute_return) -> MagicMock:
    """Return a mock object whose full Supabase query chain terminates in execute()."""
    m = MagicMock()
    m.select.return_value = m
    m.insert.return_value = m
    m.eq.return_value = m
    m.neq.return_value = m
    m.in_.return_value = m
    m.order.return_value = m
    m.limit.return_value = m
    m.maybe_single.return_value = m
    m.execute = AsyncMock(return_value=execute_return)
    return m


def _result(data) -> MagicMock:
    r = MagicMock()
    r.data = data
    return r


def _build_db(
    org_data=None,
    existing_emails: list[str] | None = None,
    insert_raises: Exception | None = None,
    list_data: list[dict] | None = None,
) -> MagicMock:
    """
    Build a db mock that handles:
      - table("organizations") → org ownership check
      - table("organization_invites") → select (existing check) + insert OR list query
    """
    db = MagicMock()
    org_result = _result(org_data)
    existing_result = _result([{"email": e} for e in (existing_emails or [])])
    insert_result = _result([])
    list_result = _result(list_data or [])

    # Track how many times organization_invites is accessed
    invite_call_count = {"n": 0}

    def _table(name: str):
        if name == "organizations":
            return _make_chain(org_result)

        # organization_invites
        invite_call_count["n"] += 1
        n = invite_call_count["n"]

        if list_data is not None:
            # list_invites path — always return list data
            return _make_chain(list_result)

        if insert_raises is not None:
            m = _make_chain(existing_result)
            if n > 1:
                # insert call
                async def _raise_on_execute():
                    raise insert_raises

                m.execute = AsyncMock(side_effect=_raise_on_execute)
            return m

        # Normal bulk path: n==1 → existing check, n>1 → insert
        if n == 1:
            return _make_chain(existing_result)
        return _make_chain(insert_result)

    db.table = MagicMock(side_effect=_table)
    return db


def _override(db: MagicMock, user_id: str = VALID_USER_ID) -> None:
    """Install dep overrides on the FastAPI app."""
    app.dependency_overrides[get_current_user_id] = lambda: user_id
    # get_supabase_admin is an async generator dep — override must yield
    async def _db_override():
        yield db

    app.dependency_overrides[get_supabase_admin] = _db_override


def _clear() -> None:
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# ── Schema tests (pure, synchronous) ───────────────────────────────────────
# ---------------------------------------------------------------------------


class TestSanitizeCell:
    """_sanitize_cell helper."""

    def test_strips_whitespace(self):
        assert _sanitize_cell("  hello  ") == "hello"

    def test_returns_none_for_empty_string(self):
        assert _sanitize_cell("") is None

    def test_returns_none_for_whitespace_only(self):
        assert _sanitize_cell("   ") is None

    def test_returns_none_for_none(self):
        assert _sanitize_cell(None) is None

    def test_prefixes_equals_sign(self):
        assert _sanitize_cell("=CMD") == "'=CMD"

    def test_prefixes_plus_sign(self):
        assert _sanitize_cell("+evil") == "'+evil"

    def test_prefixes_minus_sign(self):
        assert _sanitize_cell("-evil") == "'-evil"

    def test_prefixes_at_sign(self):
        assert _sanitize_cell("@evil") == "'@evil"

    def test_tab_prefix_stripped_by_strip_not_prefixed(self):
        # "\t" is stripped by .strip() BEFORE the formula-prefix check,
        # so "\tevil" becomes "evil" (leading tab removed). This is expected
        # behaviour — the code calls strip() first, then checks prefix.
        assert _sanitize_cell("\tevil") == "evil"

    def test_safe_string_returned_as_is(self):
        assert _sanitize_cell("Ahmed Mammadov") == "Ahmed Mammadov"

    def test_value_with_only_newline_returns_none(self):
        assert _sanitize_cell("\n") is None


class TestInviteRowInputEmail:
    """Email validation."""

    def test_valid_email_normalized_to_lowercase(self):
        row = InviteRowInput(email="Ahmed@Example.COM")
        assert row.email == "ahmed@example.com"

    def test_valid_email_strips_whitespace(self):
        row = InviteRowInput(email="  user@example.com  ")
        assert row.email == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="not-an-email")

    def test_formula_injection_email_raises(self):
        # "=" is not valid in the local part per the regex — must reject
        with pytest.raises(ValidationError):
            InviteRowInput(email="=cmd@evil.com")

    def test_email_missing_domain_raises(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="user@")

    def test_email_missing_tld_raises(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="user@domain")


class TestInviteRowInputDisplayName:
    """display_name sanitization."""

    def test_formula_prefix_prepended_with_quote(self):
        row = InviteRowInput(email="user@example.com", display_name="=SUM(A1)")
        assert row.display_name == "'=SUM(A1)"

    def test_safe_name_returned_as_is(self):
        row = InviteRowInput(email="user@example.com", display_name="Ahmed Mammadov")
        assert row.display_name == "Ahmed Mammadov"

    def test_empty_display_name_becomes_none(self):
        row = InviteRowInput(email="user@example.com", display_name="")
        assert row.display_name is None

    def test_whitespace_only_display_name_becomes_none(self):
        row = InviteRowInput(email="user@example.com", display_name="   ")
        assert row.display_name is None


class TestInviteRowInputPhone:
    """Phone validation."""

    def test_valid_phone_preserved(self):
        row = InviteRowInput(email="user@example.com", phone="+994501234567")
        assert row.phone == "+994501234567"

    def test_phone_strips_letters(self):
        row = InviteRowInput(email="user@example.com", phone="+994501234ext567")
        assert "e" not in row.phone
        assert "x" not in row.phone
        assert "t" not in row.phone

    def test_phone_too_short_raises(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="user@example.com", phone="123")

    def test_none_phone_allowed(self):
        row = InviteRowInput(email="user@example.com", phone=None)
        assert row.phone is None

    def test_empty_phone_becomes_none(self):
        row = InviteRowInput(email="user@example.com", phone="")
        assert row.phone is None


class TestInviteRowInputSkills:
    """Skills pipe-parsing."""

    def test_pipe_delimited_skills_parsed(self):
        row = InviteRowInput(email="user@example.com", skills="leadership|event_coordination|english")
        assert row.to_skills_list() == ["leadership", "event_coordination", "english"]

    def test_skills_with_whitespace_stripped(self):
        row = InviteRowInput(email="user@example.com", skills=" a | b | c ")
        assert row.to_skills_list() == ["a", "b", "c"]

    def test_empty_skills_returns_empty_list(self):
        row = InviteRowInput(email="user@example.com", skills="")
        assert row.to_skills_list() == []

    def test_none_skills_returns_empty_list(self):
        row = InviteRowInput(email="user@example.com", skills=None)
        assert row.to_skills_list() == []

    def test_single_skill_returns_list_of_one(self):
        row = InviteRowInput(email="user@example.com", skills="leadership")
        assert row.to_skills_list() == ["leadership"]


class TestResponseModels:
    """Model field assertions."""

    def test_bulk_invite_response_fields(self):
        resp = BulkInviteResponse(
            batch_id="abc",
            total=3,
            created=2,
            duplicates=1,
            errors=0,
            results=[],
        )
        assert resp.batch_id == "abc"
        assert resp.total == 3
        assert resp.created == 2
        assert resp.duplicates == 1
        assert resp.errors == 0

    def test_invite_row_result_error_defaults_to_none(self):
        r = InviteRowResult(row=2, email="user@example.com", status="created")
        assert r.error is None

    def test_invite_list_response_optional_fields_default_none(self):
        from datetime import datetime

        inv = InviteListResponse(
            id="uuid",
            email="user@example.com",
            status="pending",
            created_at=datetime.now(UTC),
        )
        assert inv.display_name is None
        assert inv.accepted_at is None


# ---------------------------------------------------------------------------
# ── Router tests (async) ───────────────────────────────────────────────────
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestValidateUUID:
    async def test_invalid_org_id_returns_422(self, client):
        db = _build_db(org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"})
        _override(db)
        try:
            resp = await client.post(
                "/api/organizations/not-a-uuid/invites/bulk",
                files={"file": ("i.csv", b"email\ntest@example.com", "text/csv")},
            )
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_UUID"
        finally:
            _clear()


@pytest.mark.asyncio
class TestBulkInviteAuth:
    async def test_org_not_found_returns_404(self, client):
        db = _build_db(org_data=None)
        _override(db)
        try:
            resp = await client.post(
                BULK_URL,
                files={"file": ("i.csv", b"email\ntest@example.com", "text/csv")},
            )
            assert resp.status_code == 404
            detail = resp.json()["detail"]
            assert detail["code"] == "ORG_NOT_FOUND"
        finally:
            _clear()

    async def test_not_org_owner_returns_403(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": "other-user-id", "name": "Org"}
        )
        _override(db)
        try:
            resp = await client.post(
                BULK_URL,
                files={"file": ("i.csv", b"email\ntest@example.com", "text/csv")},
            )
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            _clear()


@pytest.mark.asyncio
class TestBulkInviteFileValidation:
    async def test_file_too_large_returns_413(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"}
        )
        _override(db)
        try:
            big_csv = b"email\n" + b"a@b.com\n" * 200_000
            resp = await client.post(
                BULK_URL,
                files={"file": ("i.csv", big_csv, "text/csv")},
            )
            assert resp.status_code == 413
        finally:
            _clear()

    async def test_non_utf8_file_returns_422(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"}
        )
        _override(db)
        try:
            bad_bytes = b"email\n\xff\xfe@example.com\n"
            resp = await client.post(
                BULK_URL,
                files={"file": ("i.csv", bad_bytes, "text/csv")},
            )
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_ENCODING"
        finally:
            _clear()

    async def test_missing_email_column_returns_422(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"}
        )
        _override(db)
        try:
            csv = b"name,phone\nAhmed,+994501234567\n"
            resp = await client.post(
                BULK_URL,
                files={"file": ("i.csv", csv, "text/csv")},
            )
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "MISSING_COLUMN"
        finally:
            _clear()

    async def test_empty_csv_header_only_returns_422(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"}
        )
        _override(db)
        try:
            resp = await client.post(
                BULK_URL,
                files={"file": ("i.csv", b"email\n", "text/csv")},
            )
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "EMPTY_CSV"
        finally:
            _clear()


@pytest.mark.asyncio
class TestBulkInviteHappyPath:
    async def test_two_valid_rows_207_created_2(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=[],
        )
        _override(db)
        try:
            csv = b"email,display_name\nuser1@example.com,Alice\nuser2@example.com,Bob\n"
            resp = await client.post(BULK_URL, files={"file": ("i.csv", csv, "text/csv")})
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["created"] == 2
            assert body["duplicates"] == 0
            assert body["errors"] == 0
            assert body["total"] == 2
        finally:
            _clear()

    async def test_bom_utf8_csv_decoded_correctly(self, client):
        """Excel BOM-prefixed CSV must be handled transparently."""
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=[],
        )
        _override(db)
        try:
            # encode("utf-8-sig") prepends BOM automatically — do NOT add \ufeff manually
            bom_csv = "email\nbom@example.com\n".encode("utf-8-sig")
            resp = await client.post(BULK_URL, files={"file": ("i.csv", bom_csv, "text/csv")})
            assert resp.status_code == 207
            assert resp.json()["data"]["created"] == 1
        finally:
            _clear()


@pytest.mark.asyncio
class TestBulkInviteDuplicates:
    async def test_in_file_duplicate_one_created_one_duplicate(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=[],
        )
        _override(db)
        try:
            csv = b"email\nsame@example.com\nsame@example.com\n"
            resp = await client.post(BULK_URL, files={"file": ("i.csv", csv, "text/csv")})
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["created"] == 1
            assert body["duplicates"] == 1
        finally:
            _clear()

    async def test_db_duplicate_already_invited(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=["already@example.com"],
        )
        _override(db)
        try:
            csv = b"email\nalready@example.com\n"
            resp = await client.post(BULK_URL, files={"file": ("i.csv", csv, "text/csv")})
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["duplicates"] == 1
            assert body["created"] == 0
        finally:
            _clear()


@pytest.mark.asyncio
class TestBulkInviteRowLimits:
    async def test_exceeds_500_rows_error_on_row_502(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=[],
        )
        _override(db)
        try:
            lines = ["email"] + [f"user{i}@example.com" for i in range(502)]
            csv = "\n".join(lines).encode()
            resp = await client.post(BULK_URL, files={"file": ("i.csv", csv, "text/csv")})
            assert resp.status_code == 207
            error_rows = [r for r in resp.json()["data"]["results"] if r["status"] == "error"]
            assert any(r["row"] == 502 for r in error_rows)
            assert any("500" in r["error"] for r in error_rows)
        finally:
            _clear()

    async def test_invalid_email_in_row_errors_but_other_rows_processed(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=[],
        )
        _override(db)
        try:
            csv = b"email\nbad-not-an-email\ngood@example.com\n"
            resp = await client.post(BULK_URL, files={"file": ("i.csv", csv, "text/csv")})
            assert resp.status_code == 207
            body = resp.json()["data"]
            statuses = {r["email"]: r["status"] for r in body["results"]}
            assert statuses.get("good@example.com") == "created"
            assert body["errors"] == 1
        finally:
            _clear()


@pytest.mark.asyncio
class TestBulkInviteDBFailure:
    async def test_batch_insert_failure_marks_rows_error(self, client):
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID, "name": "Org"},
            existing_emails=[],
            insert_raises=Exception("DB connection lost"),
        )
        _override(db)
        try:
            csv = b"email\nuser@example.com\n"
            resp = await client.post(BULK_URL, files={"file": ("i.csv", csv, "text/csv")})
            assert resp.status_code == 207
            body = resp.json()["data"]
            assert body["errors"] == 1
            assert body["created"] == 0
        finally:
            _clear()


@pytest.mark.asyncio
class TestListInvites:
    async def test_not_org_owner_returns_403(self, client):
        db = _build_db(org_data={"id": VALID_ORG_ID, "owner_id": "other-user"})
        _override(db)
        try:
            resp = await client.get(LIST_URL)
            assert resp.status_code == 403
            assert resp.json()["detail"]["code"] == "NOT_ORG_OWNER"
        finally:
            _clear()

    async def test_org_not_found_returns_403(self, client):
        # list_invites returns 403 for both missing org and wrong owner
        db = _build_db(org_data=None)
        _override(db)
        try:
            resp = await client.get(LIST_URL)
            assert resp.status_code == 403
        finally:
            _clear()

    async def test_happy_path_returns_list(self, client):
        from datetime import datetime

        now = datetime.now(UTC).isoformat()
        invite_data = [
            {
                "id": "inv-1",
                "email": "user@example.com",
                "display_name": "Ahmed",
                "status": "pending",
                "created_at": now,
                "accepted_at": None,
            }
        ]
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID},
            list_data=invite_data,
        )
        _override(db)
        try:
            resp = await client.get(LIST_URL)
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert data[0]["email"] == "user@example.com"
        finally:
            _clear()

    async def test_invalid_status_filter_returns_422(self, client):
        db = _build_db(org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID})
        _override(db)
        try:
            resp = await client.get(LIST_URL, params={"status": "not_valid"})
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_STATUS"
        finally:
            _clear()

    async def test_valid_status_filter_accepted(self, client):
        from datetime import datetime

        now = datetime.now(UTC).isoformat()
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID},
            list_data=[
                {
                    "id": "inv-1",
                    "email": "u@example.com",
                    "display_name": None,
                    "status": "accepted",
                    "created_at": now,
                    "accepted_at": now,
                }
            ],
        )
        _override(db)
        try:
            resp = await client.get(LIST_URL, params={"status": "accepted"})
            assert resp.status_code == 200
        finally:
            _clear()

    async def test_invalid_batch_id_uuid_returns_422(self, client):
        db = _build_db(org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID})
        _override(db)
        try:
            resp = await client.get(LIST_URL, params={"batch_id": "not-a-uuid"})
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INVALID_UUID"
        finally:
            _clear()

    async def test_valid_batch_id_filter_accepted(self, client):
        from datetime import datetime

        now = datetime.now(UTC).isoformat()
        db = _build_db(
            org_data={"id": VALID_ORG_ID, "owner_id": VALID_USER_ID},
            list_data=[
                {
                    "id": "inv-1",
                    "email": "u@example.com",
                    "display_name": None,
                    "status": "pending",
                    "created_at": now,
                    "accepted_at": None,
                }
            ],
        )
        _override(db)
        try:
            resp = await client.get(LIST_URL, params={"batch_id": VALID_BATCH_ID})
            assert resp.status_code == 200
        finally:
            _clear()


@pytest.mark.asyncio
class TestTemplateEndpoint:
    async def test_template_returns_correct_structure(self, client):
        resp = await client.get(TEMPLATE_URL)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "columns" in data
        assert "email" in data["columns"]
        assert data["required"] == ["email"]
        assert "example_row" in data
        assert isinstance(data["notes"], list)
        assert len(data["notes"]) > 0

    async def test_template_example_row_has_expected_keys(self, client):
        resp = await client.get(TEMPLATE_URL)
        assert resp.status_code == 200
        example = resp.json()["data"]["example_row"]
        assert "email" in example
        assert "skills" in example
        assert "|" in example["skills"]  # pipe-delimited example
