"""Unit tests for atlas_gateway, community, and invites routers.

Covers:
- atlas_gateway: router constants and structure
- community: CommunitySignal schema construction and field types
- invites schemas: _sanitize_cell, InviteRowInput validators, InviteRowResult,
  BulkInviteResponse, InviteListResponse, _validate_uuid
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.routers.atlas_gateway import router as atlas_router
from app.routers.community import CommunitySignal
from app.routers.invites import (
    BATCH_SIZE,
    MAX_FILE_SIZE,
    MAX_ROWS,
    RATE_BULK_INVITE,
    _validate_uuid,
)
from app.routers.invites import (
    router as invites_router,
)
from app.schemas.invite import (
    BulkInviteResponse,
    InviteListResponse,
    InviteRowInput,
    InviteRowResult,
    _sanitize_cell,
)

# ── atlas_gateway router structure ──────────────────────────────────


class TestAtlasGatewayRouterStructure:
    def test_router_prefix(self):
        assert atlas_router.prefix == "/api/atlas"

    def test_router_tags(self):
        assert "atlas-gateway" in atlas_router.tags

    def test_has_health_route(self):
        paths = [r.path for r in atlas_router.routes]
        assert "/api/atlas/health" in paths

    def test_has_proposal_route(self):
        paths = [r.path for r in atlas_router.routes]
        assert "/api/atlas/proposal" in paths

    def test_route_count(self):
        # health + proposal = 2 routes
        assert len(atlas_router.routes) == 2


# ── CommunitySignal schema ─────────────────────────────────────────


class TestCommunitySignal:
    def test_valid_construction(self):
        s = CommunitySignal(
            professionals_today=5,
            professionals_this_week=42,
            total_professionals=1200,
        )
        assert s.professionals_today == 5
        assert s.professionals_this_week == 42
        assert s.total_professionals == 1200

    def test_zero_values(self):
        s = CommunitySignal(
            professionals_today=0,
            professionals_this_week=0,
            total_professionals=0,
        )
        assert s.professionals_today == 0

    def test_large_values(self):
        s = CommunitySignal(
            professionals_today=999_999,
            professionals_this_week=9_999_999,
            total_professionals=100_000_000,
        )
        assert s.total_professionals == 100_000_000

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            CommunitySignal(professionals_today=5, professionals_this_week=10)

    def test_string_coercion_to_int(self):
        s = CommunitySignal(
            professionals_today="7",
            professionals_this_week="14",
            total_professionals="100",
        )
        assert s.professionals_today == 7

    def test_negative_allowed_no_ge_constraint(self):
        # No ge=0 in the schema — negatives pass validation
        s = CommunitySignal(
            professionals_today=-1,
            professionals_this_week=-5,
            total_professionals=-10,
        )
        assert s.professionals_today == -1

    def test_from_attributes_config(self):
        assert CommunitySignal.model_config.get("from_attributes") is True

    def test_model_dump(self):
        s = CommunitySignal(
            professionals_today=3,
            professionals_this_week=20,
            total_professionals=500,
        )
        d = s.model_dump()
        assert set(d.keys()) == {
            "professionals_today",
            "professionals_this_week",
            "total_professionals",
        }

    def test_community_router_prefix(self):
        from app.routers.community import router as community_router

        assert community_router.prefix == "/community"


# ── _sanitize_cell ──────────────────────────────────────────────────


class TestSanitizeCell:
    def test_none_returns_none(self):
        assert _sanitize_cell(None) is None

    def test_empty_string_returns_none(self):
        assert _sanitize_cell("") is None

    def test_whitespace_only_returns_none(self):
        assert _sanitize_cell("   ") is None

    def test_tab_only_returns_none(self):
        assert _sanitize_cell("\t") is None

    def test_normal_text_stripped(self):
        assert _sanitize_cell("  hello  ") == "hello"

    @pytest.mark.parametrize(
        "input_val,expected",
        [
            ("=SUM(A1)", "'=SUM(A1)"),
            ("+cmd|' /C calc'!A0", "'+cmd|' /C calc'!A0"),
            ("-1+1", "'-1+1"),
            ("@import('evil')", "'@import('evil')"),
            # \t, \r, \n are stripped by .strip() first, so "cmd" remains — no formula prefix
            # These are tested separately below
        ],
    )
    def test_formula_prefix_quoted(self, input_val, expected):
        assert _sanitize_cell(input_val) == expected

    def test_normal_text_not_quoted(self):
        assert _sanitize_cell("Ahmed Mammadov") == "Ahmed Mammadov"

    def test_single_char(self):
        assert _sanitize_cell("a") == "a"

    def test_leading_space_then_formula(self):
        # After strip(), "=SUM" starts with "=" → gets quoted
        assert _sanitize_cell("  =SUM(A1)") == "'=SUM(A1)"

    def test_tab_prefix_stripped_by_strip(self):
        # "\tcmd" → strip() → "cmd" (no formula prefix left)
        assert _sanitize_cell("\tcmd") == "cmd"

    def test_cr_prefix_stripped_by_strip(self):
        assert _sanitize_cell("\rcmd") == "cmd"

    def test_lf_prefix_stripped_by_strip(self):
        assert _sanitize_cell("\ncmd") == "cmd"

    def test_tab_in_middle_not_stripped(self):
        # "a\tb" → strip doesn't touch middle → no formula prefix → unchanged
        assert _sanitize_cell("a\tb") == "a\tb"


# ── InviteRowInput ──────────────────────────────────────────────────


class TestInviteRowInputEmail:
    def test_valid_email_lowercased(self):
        row = InviteRowInput(email="Test@Example.COM")
        assert row.email == "test@example.com"

    def test_valid_email_stripped(self):
        row = InviteRowInput(email="  user@domain.org  ")
        assert row.email == "user@domain.org"

    def test_email_with_dots(self):
        row = InviteRowInput(email="first.last@sub.domain.com")
        assert row.email == "first.last@sub.domain.com"

    def test_email_with_plus(self):
        row = InviteRowInput(email="user+tag@gmail.com")
        assert row.email == "user+tag@gmail.com"

    @pytest.mark.parametrize(
        "bad_email",
        [
            "not-an-email",
            "missing@",
            "@nodomain.com",
            "spaces in@email.com",
            "double@@at.com",
            "",
        ],
    )
    def test_invalid_email_rejected(self, bad_email):
        with pytest.raises(ValidationError):
            InviteRowInput(email=bad_email)

    def test_email_too_short(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="a@b")

    def test_email_too_long(self):
        # 254 max — build a 255-char email
        long_local = "a" * 243  # 243 + @example.com (12) = 255
        with pytest.raises(ValidationError):
            InviteRowInput(email=f"{long_local}@example.com")

    def test_email_min_boundary(self):
        # 5 chars minimum: a@b.c
        row = InviteRowInput(email="a@b.co")
        assert row.email == "a@b.co"

    def test_formula_email_rejected(self):
        # =cmd@evil.com — starts with = but after lowering/stripping still fails regex
        with pytest.raises(ValidationError):
            InviteRowInput(email="=cmd@evil.com")


class TestInviteRowInputDisplayName:
    def test_display_name_sanitized(self):
        row = InviteRowInput(email="a@b.co", display_name="  John  ")
        assert row.display_name == "John"

    def test_display_name_none(self):
        row = InviteRowInput(email="a@b.co", display_name=None)
        assert row.display_name is None

    def test_display_name_empty_becomes_none(self):
        row = InviteRowInput(email="a@b.co", display_name="  ")
        assert row.display_name is None

    def test_display_name_formula_quoted(self):
        row = InviteRowInput(email="a@b.co", display_name="=HYPERLINK()")
        assert row.display_name == "'=HYPERLINK()"

    def test_display_name_max_length(self):
        row = InviteRowInput(email="a@b.co", display_name="x" * 200)
        assert len(row.display_name) == 200

    def test_display_name_over_max(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="a@b.co", display_name="x" * 201)


class TestInviteRowInputPhone:
    def test_valid_phone(self):
        row = InviteRowInput(email="a@b.co", phone="+994501234567")
        assert "994501234567" in row.phone

    def test_phone_none(self):
        row = InviteRowInput(email="a@b.co", phone=None)
        assert row.phone is None

    def test_phone_empty_becomes_none(self):
        row = InviteRowInput(email="a@b.co", phone="  ")
        assert row.phone is None

    def test_phone_too_short(self):
        with pytest.raises(ValidationError, match="Phone too short"):
            InviteRowInput(email="a@b.co", phone="12345")

    def test_phone_strips_non_phone_chars(self):
        row = InviteRowInput(email="a@b.co", phone="+1 (555) 123-4567")
        # Should retain only digits, +, -, (), spaces
        assert row.phone == "+1 (555) 123-4567"

    def test_phone_formula_sanitized_then_validated(self):
        # "=123456789" after sanitize becomes "'=123456789", then non-phone chars stripped
        # After stripping: "123456789" has 9 digits >= 7, so valid
        row = InviteRowInput(email="a@b.co", phone="=123456789")
        assert row.phone is not None

    def test_phone_with_letters_stripped(self):
        row = InviteRowInput(email="a@b.co", phone="abc1234567890xyz")
        assert row.phone == "1234567890"

    def test_phone_boundary_7_digits(self):
        row = InviteRowInput(email="a@b.co", phone="1234567")
        assert row.phone == "1234567"


class TestInviteRowInputSkills:
    def test_skills_sanitized(self):
        row = InviteRowInput(email="a@b.co", skills="  leadership  ")
        assert row.skills == "leadership"

    def test_skills_formula_quoted(self):
        row = InviteRowInput(email="a@b.co", skills="=EVIL")
        assert row.skills == "'=EVIL"

    def test_skills_none(self):
        row = InviteRowInput(email="a@b.co", skills=None)
        assert row.skills is None

    def test_skills_max_length(self):
        row = InviteRowInput(email="a@b.co", skills="a" * 500)
        assert len(row.skills) == 500

    def test_skills_over_max(self):
        with pytest.raises(ValidationError):
            InviteRowInput(email="a@b.co", skills="a" * 501)


class TestInviteRowInputToSkillsList:
    def test_none_skills_empty_list(self):
        row = InviteRowInput(email="a@b.co", skills=None)
        assert row.to_skills_list() == []

    def test_pipe_delimited(self):
        row = InviteRowInput(email="a@b.co", skills="leadership|english|events")
        assert row.to_skills_list() == ["leadership", "english", "events"]

    def test_empty_segments_skipped(self):
        row = InviteRowInput(email="a@b.co", skills="leadership||english|")
        assert row.to_skills_list() == ["leadership", "english"]

    def test_whitespace_segments_stripped(self):
        row = InviteRowInput(email="a@b.co", skills=" a | b | c ")
        assert row.to_skills_list() == ["a", "b", "c"]

    def test_single_skill(self):
        row = InviteRowInput(email="a@b.co", skills="python")
        assert row.to_skills_list() == ["python"]

    def test_empty_string_skills_returns_empty(self):
        # Empty becomes None via sanitizer
        row = InviteRowInput(email="a@b.co", skills="   ")
        assert row.to_skills_list() == []


class TestInviteRowInputFromAttributes:
    def test_from_attributes_enabled(self):
        assert InviteRowInput.model_config.get("from_attributes") is True


# ── InviteRowResult ─────────────────────────────────────────────────


class TestInviteRowResult:
    def test_created_status(self):
        r = InviteRowResult(row=2, email="a@b.co", status="created")
        assert r.status == "created"
        assert r.error is None

    def test_duplicate_status(self):
        r = InviteRowResult(row=3, email="b@c.co", status="duplicate")
        assert r.status == "duplicate"

    def test_error_status_with_message(self):
        r = InviteRowResult(row=4, email="c@d.co", status="error", error="Bad format")
        assert r.error == "Bad format"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            InviteRowResult(row=1, email="a@b.co")

    def test_model_dump_keys(self):
        r = InviteRowResult(row=1, email="a@b.co", status="created")
        d = r.model_dump()
        assert set(d.keys()) == {"row", "email", "status", "error"}


# ── BulkInviteResponse ─────────────────────────────────────────────


class TestBulkInviteResponse:
    def test_full_construction(self):
        results = [
            InviteRowResult(row=2, email="a@b.co", status="created"),
            InviteRowResult(row=3, email="b@c.co", status="duplicate"),
            InviteRowResult(row=4, email="c@d.co", status="error", error="Bad"),
        ]
        resp = BulkInviteResponse(
            batch_id="abc-123",
            total=3,
            created=1,
            duplicates=1,
            errors=1,
            results=results,
        )
        assert resp.total == 3
        assert len(resp.results) == 3

    def test_empty_results(self):
        resp = BulkInviteResponse(
            batch_id="x",
            total=0,
            created=0,
            duplicates=0,
            errors=0,
            results=[],
        )
        assert resp.results == []

    def test_missing_results_raises(self):
        with pytest.raises(ValidationError):
            BulkInviteResponse(batch_id="x", total=0, created=0, duplicates=0, errors=0)

    def test_model_dump_structure(self):
        resp = BulkInviteResponse(
            batch_id="b",
            total=1,
            created=1,
            duplicates=0,
            errors=0,
            results=[InviteRowResult(row=2, email="a@b.co", status="created")],
        )
        d = resp.model_dump()
        assert "results" in d
        assert isinstance(d["results"], list)


# ── InviteListResponse ──────────────────────────────────────────────


class TestInviteListResponse:
    def test_full_construction(self):
        now = datetime.now(UTC)
        r = InviteListResponse(
            id="abc",
            email="a@b.co",
            display_name="Ahmed",
            status="pending",
            created_at=now,
            accepted_at=now,
        )
        assert r.display_name == "Ahmed"
        assert r.accepted_at == now

    def test_optional_fields_default_none(self):
        now = datetime.now(UTC)
        r = InviteListResponse(
            id="xyz",
            email="b@c.co",
            status="accepted",
            created_at=now,
        )
        assert r.display_name is None
        assert r.accepted_at is None

    def test_from_attributes_config(self):
        assert InviteListResponse.model_config.get("from_attributes") is True

    def test_missing_required_raises(self):
        with pytest.raises(ValidationError):
            InviteListResponse(id="x", email="a@b.co")


# ── _validate_uuid ──────────────────────────────────────────────────


class TestValidateUuid:
    def test_valid_uuid(self):
        uid = str(uuid4())
        # Should not raise
        _validate_uuid(uid, "test_field")

    def test_valid_uuid_no_dashes(self):
        uid = uuid4().hex
        _validate_uuid(uid, "test_field")

    @pytest.mark.parametrize(
        "bad_val",
        [
            "not-a-uuid",
            "12345",
            "",
            "zzzzzzzz-zzzz-zzzz-zzzz-zzzzzzzzzzzz",
        ],
    )
    def test_invalid_uuid_raises_422(self, bad_val):
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid(bad_val, "org_id")
        assert exc_info.value.status_code == 422

    def test_none_raises_type_error(self):
        # None causes TypeError in uuid.UUID, not caught by (ValueError, AttributeError)
        with pytest.raises(TypeError):
            _validate_uuid(None, "org_id")

    def test_error_detail_contains_field_name(self):
        with pytest.raises(HTTPException) as exc_info:
            _validate_uuid("bad", "my_field")
        assert "my_field" in exc_info.value.detail["message"]


# ── Invites router constants ────────────────────────────────────────


class TestInvitesRouterConstants:
    def test_max_file_size_1mb(self):
        assert MAX_FILE_SIZE == 1_048_576

    def test_max_rows_500(self):
        assert MAX_ROWS == 500

    def test_batch_size_50(self):
        assert BATCH_SIZE == 50

    def test_rate_limit(self):
        assert RATE_BULK_INVITE == "2/minute"

    def test_router_prefix(self):
        assert invites_router.prefix == "/organizations"

    def test_router_tags(self):
        assert "Organization Invites" in invites_router.tags
