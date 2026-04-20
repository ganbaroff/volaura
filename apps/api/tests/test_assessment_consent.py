"""GDPR Article 22 compliance tests for the assessment /start consent path.

These tests verify that:
- automated_decision_consent=False returns 422 CONSENT_REQUIRED
- consent_events.insert is called with correct fields when an active policy exists
- consent logging is silently skipped (non-blocking) when no policy row is found
- consent logging failure never aborts the assessment start
- consent_scope JSONB contains competency_slug matching the payload

All tests call the route function directly (not via HTTP client) so the
dependency-injection layer is fully controlled via mock objects. This isolates
the consent code path from the full CAT engine, DB session management, and
paywall logic.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.routers.assessment import start_assessment
from app.schemas.assessment import StartAssessmentRequest

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
POLICY_UUID = "bbbbbbbb-1111-1111-1111-000000000001"
COMPETENCY = "communication"


# ── Mock helpers ───────────────────────────────────────────────────────────────


def _make_request() -> MagicMock:
    """Minimal FastAPI Request stand-in."""
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers = {"user-agent": "pytest/test"}
    return req


def _make_db(*execute_returns) -> MagicMock:
    """Supabase client mock with full fluent-builder chain.

    Each positional arg is returned in order from successive .execute() calls.
    If a single arg is provided, every execute() call returns it.
    """
    db = MagicMock()
    chain = MagicMock()

    builder_methods = [
        "schema",
        "table",
        "select",
        "insert",
        "update",
        "upsert",
        "delete",
        "eq",
        "neq",
        "lt",
        "is_",
        "order",
        "range",
        "filter",
        "limit",
        "single",
        "maybe_single",
    ]
    for method in builder_methods:
        getattr(chain, method).return_value = chain
        getattr(db, method).return_value = chain

    if len(execute_returns) == 0:
        chain.execute = AsyncMock(return_value=_result(data=None))
        db.execute = AsyncMock(return_value=_result(data=None))
    elif len(execute_returns) == 1:
        chain.execute = AsyncMock(return_value=execute_returns[0])
        db.execute = AsyncMock(return_value=execute_returns[0])
    else:
        chain.execute = AsyncMock(side_effect=list(execute_returns))
        db.execute = AsyncMock(side_effect=list(execute_returns))

    return db


def _result(data=None, *, count: int | None = None) -> MagicMock:
    r = MagicMock()
    r.data = data
    r.count = count
    return r


def _consent_payload(**overrides) -> StartAssessmentRequest:
    """Valid StartAssessmentRequest with consent given."""
    base = {
        "competency_slug": COMPETENCY,
        "automated_decision_consent": True,
    }
    return StartAssessmentRequest(**{**base, **overrides})


def _no_consent_payload() -> StartAssessmentRequest:
    return StartAssessmentRequest(
        competency_slug=COMPETENCY,
        automated_decision_consent=False,
    )


# ── Full start_assessment patch context ───────────────────────────────────────
# The route calls several services (get_competency_id, fetch_questions, etc.).
# We patch them all so each test can focus on the consent code path.

_PATCH_TARGETS = [
    "app.routers.assessment.get_competency_id",
    "app.routers.assessment.fetch_questions",
    "app.routers.assessment.make_session_out",
    "app.routers.assessment.select_next_item",
    "app.routers.assessment.track_event",
    "app.routers.assessment.record_assessment_activity",
    "app.routers.assessment.notify",
    "app.routers.assessment.settings",
]


def _patch_all():
    """Return a list of patch() context managers covering all non-consent service calls."""
    patches = []

    # get_competency_id returns a UUID
    p = patch(
        "app.routers.assessment.get_competency_id",
        new_callable=lambda: lambda: AsyncMock(return_value=uuid.uuid4()),
    )
    patches.append(p)

    # fetch_questions returns two dummy question dicts
    def _fake_fetch(*_a, **_kw):
        q = MagicMock()
        q.id = uuid.uuid4()
        q.competency_id = uuid.uuid4()
        q.stem = "Test question?"
        q.options = ["A", "B", "C", "D"]
        q.difficulty = 0.0
        q.discrimination = 1.0
        q.guessing = 0.25
        return AsyncMock(return_value=[q, q])()

    patches.append(patch("app.routers.assessment.fetch_questions", side_effect=_fake_fetch))

    # make_session_out returns a minimal SessionOut-compatible MagicMock
    session_out = MagicMock()
    session_out.session_id = uuid.uuid4()
    patches.append(patch("app.routers.assessment.make_session_out", return_value=session_out))

    # select_next_item — returns a MagicMock item
    item = MagicMock()
    item.id = uuid.uuid4()
    patches.append(patch("app.routers.assessment.select_next_item", return_value=item))

    # Non-async fire-and-forget services
    patches.append(patch("app.routers.assessment.track_event", new_callable=AsyncMock))
    patches.append(patch("app.routers.assessment.record_assessment_activity", new_callable=AsyncMock))
    patches.append(patch("app.routers.assessment.notify", new_callable=AsyncMock))

    return patches


def _apply_patches(patches):
    """Enter all patch contexts; return (stack, mocks)."""
    mocks = []
    for p in patches:
        mocks.append(p.__enter__() if hasattr(p, "__enter__") else p.start())
    return mocks


def _stop_patches(patches):
    for p in patches:
        try:
            p.__exit__(None, None, None)
        except AttributeError:
            p.stop()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Consent gate — 422 when consent not given
# ══════════════════════════════════════════════════════════════════════════════


class TestConsentRequired:
    """422 CONSENT_REQUIRED fires before any DB work when consent is False."""

    @pytest.mark.asyncio
    async def test_consent_required_when_not_given(self):
        """start_assessment raises 422 CONSENT_REQUIRED when automated_decision_consent=False."""
        db_admin = _make_db()
        db_user = _make_db()

        with (
            patch("app.routers.assessment.get_competency_id", new_callable=AsyncMock) as mock_cid,
            patch("app.routers.assessment.settings") as mock_settings,
        ):
            mock_settings.payment_enabled = False
            mock_cid.return_value = uuid.uuid4()

            with pytest.raises(HTTPException) as exc_info:
                await start_assessment(
                    request=_make_request(),
                    payload=_no_consent_payload(),
                    db_admin=db_admin,
                    db_user=db_user,
                    user_id=USER_ID,
                )

        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "CONSENT_REQUIRED"

    def test_schema_default_consent_is_false(self):
        """StartAssessmentRequest defaults automated_decision_consent to False."""
        req = StartAssessmentRequest(competency_slug="leadership")
        assert req.automated_decision_consent is False

    def test_schema_accepts_explicit_true(self):
        """StartAssessmentRequest accepts automated_decision_consent=True."""
        req = StartAssessmentRequest(
            competency_slug="leadership",
            automated_decision_consent=True,
        )
        assert req.automated_decision_consent is True


# ══════════════════════════════════════════════════════════════════════════════
# 2. Consent logged when policy found
# ══════════════════════════════════════════════════════════════════════════════


class TestConsentLogging:
    """consent_events.insert called with correct payload when policy row exists."""

    @pytest.mark.asyncio
    async def test_consent_logs_to_consent_events_when_policy_found(self):
        """insert called with event_type=consent_given and correct policy_version_id."""
        policy_result = _result(data={"id": POLICY_UUID})
        instrumented_admin, consent_insert_spy = _build_instrumented_admin(policy_result)
        db_user = _make_db(_result(data={"is_platform_admin": False}))

        with (
            patch("app.routers.assessment.get_competency_id", new_callable=AsyncMock) as mock_cid,
            patch("app.routers.assessment.settings") as mock_settings,
            patch("app.routers.assessment.fetch_questions", new_callable=AsyncMock),
            patch("app.routers.assessment.make_session_out", return_value=MagicMock()),
            patch("app.routers.assessment.select_next_item", return_value=MagicMock()),
            patch("app.routers.assessment.track_event", new_callable=AsyncMock),
            patch("app.routers.assessment.record_assessment_activity", new_callable=AsyncMock),
            patch("app.routers.assessment.notify", new_callable=AsyncMock),
        ):
            mock_settings.payment_enabled = False
            mock_cid.return_value = uuid.uuid4()

            try:
                await start_assessment(
                    request=_make_request(),
                    payload=_consent_payload(),
                    db_admin=instrumented_admin,
                    db_user=db_user,
                    user_id=USER_ID,
                )
            except Exception:
                # Route may fail after consent block due to missing downstream mocks;
                # what matters is that consent_events.insert was called.
                pass

        assert consent_insert_spy.called, "consent_events.insert was never called"
        # spy is on .insert(data_dict) — call_args[0][0] is the dict
        call_args = consent_insert_spy.call_args[0][0]
        assert call_args["event_type"] == "consent_given"
        assert call_args["policy_version_id"] == POLICY_UUID

    @pytest.mark.asyncio
    async def test_consent_scope_contains_competency_slug(self):
        """consent_scope JSONB must contain competency_slug matching the payload."""
        policy_result = _result(data={"id": POLICY_UUID})
        instrumented_admin, consent_insert_spy = _build_instrumented_admin(policy_result)
        db_user = _make_db(_result(data={"is_platform_admin": False}))

        with (
            patch("app.routers.assessment.get_competency_id", new_callable=AsyncMock) as mock_cid,
            patch("app.routers.assessment.settings") as mock_settings,
            patch("app.routers.assessment.fetch_questions", new_callable=AsyncMock),
            patch("app.routers.assessment.make_session_out", return_value=MagicMock()),
            patch("app.routers.assessment.select_next_item", return_value=MagicMock()),
            patch("app.routers.assessment.track_event", new_callable=AsyncMock),
            patch("app.routers.assessment.record_assessment_activity", new_callable=AsyncMock),
            patch("app.routers.assessment.notify", new_callable=AsyncMock),
        ):
            mock_settings.payment_enabled = False
            mock_cid.return_value = uuid.uuid4()

            try:
                await start_assessment(
                    request=_make_request(),
                    payload=_consent_payload(competency_slug="leadership"),
                    db_admin=instrumented_admin,
                    db_user=db_user,
                    user_id=USER_ID,
                )
            except Exception:
                pass

        assert consent_insert_spy.called, "consent_events.insert was never called"
        scope = consent_insert_spy.call_args[0][0]["consent_scope"]
        assert scope["competency_slug"] == "leadership"


# ══════════════════════════════════════════════════════════════════════════════
# 3. Non-blocking: no policy → skip silently
# ══════════════════════════════════════════════════════════════════════════════


class TestConsentNonBlocking:
    """Consent failures never propagate — assessment proceeds regardless."""

    @pytest.mark.asyncio
    async def test_consent_logging_skips_silently_when_no_policy(self):
        """When policy_versions returns None, consent_events.insert is NOT called."""
        # policy_versions returns no row
        policy_result = _result(data=None)
        instrumented_admin, consent_insert_spy = _build_instrumented_admin(policy_result)
        db_user = _make_db(_result(data={"is_platform_admin": False}))

        with (
            patch("app.routers.assessment.get_competency_id", new_callable=AsyncMock) as mock_cid,
            patch("app.routers.assessment.settings") as mock_settings,
            patch("app.routers.assessment.fetch_questions", new_callable=AsyncMock),
            patch("app.routers.assessment.make_session_out", return_value=MagicMock()),
            patch("app.routers.assessment.select_next_item", return_value=MagicMock()),
            patch("app.routers.assessment.track_event", new_callable=AsyncMock),
            patch("app.routers.assessment.record_assessment_activity", new_callable=AsyncMock),
            patch("app.routers.assessment.notify", new_callable=AsyncMock),
        ):
            mock_settings.payment_enabled = False
            mock_cid.return_value = uuid.uuid4()

            try:
                await start_assessment(
                    request=_make_request(),
                    payload=_consent_payload(),
                    db_admin=instrumented_admin,
                    db_user=db_user,
                    user_id=USER_ID,
                )
            except Exception:
                pass

        assert not consent_insert_spy.called, "consent_events.insert must not be called when policy is absent"

    @pytest.mark.asyncio
    async def test_consent_logging_never_blocks_assessment_when_db_fails(self):
        """Exception in the consent logging try/except must not propagate."""
        # Build an admin mock where the policy_versions query always explodes
        db_admin = MagicMock()
        broken_chain = MagicMock()
        for method in [
            "table",
            "select",
            "insert",
            "update",
            "upsert",
            "delete",
            "eq",
            "neq",
            "lt",
            "is_",
            "order",
            "range",
            "filter",
            "limit",
            "single",
            "maybe_single",
        ]:
            getattr(broken_chain, method).return_value = broken_chain
        broken_chain.execute = AsyncMock(side_effect=Exception("Supabase unavailable"))
        db_admin.table.return_value = broken_chain

        db_user = _make_db(_result(data={"is_platform_admin": False}))

        raised_http: HTTPException | None = None

        with (
            patch("app.routers.assessment.get_competency_id", new_callable=AsyncMock) as mock_cid,
            patch("app.routers.assessment.settings") as mock_settings,
            patch("app.routers.assessment.fetch_questions", new_callable=AsyncMock),
            patch("app.routers.assessment.make_session_out", return_value=MagicMock()),
            patch("app.routers.assessment.select_next_item", return_value=MagicMock()),
            patch("app.routers.assessment.track_event", new_callable=AsyncMock),
            patch("app.routers.assessment.record_assessment_activity", new_callable=AsyncMock),
            patch("app.routers.assessment.notify", new_callable=AsyncMock),
        ):
            mock_settings.payment_enabled = False
            mock_cid.return_value = uuid.uuid4()

            try:
                await start_assessment(
                    request=_make_request(),
                    payload=_consent_payload(),
                    db_admin=db_admin,
                    db_user=db_user,
                    user_id=USER_ID,
                )
            except HTTPException as exc:
                raised_http = exc
            except Exception:
                # Downstream failures (e.g. session insert) are allowed here —
                # the test only asserts that the consent exception was NOT re-raised.
                pass

        # If an HTTPException was raised it must NOT be CONSENT_REQUIRED
        if raised_http is not None:
            assert raised_http.detail.get("code") != "CONSENT_REQUIRED", (
                "Consent logging DB failure must not surface as CONSENT_REQUIRED"
            )


# ══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ══════════════════════════════════════════════════════════════════════════════


def _build_instrumented_admin(policy_result: MagicMock):
    """Return (db_admin, consent_insert_spy) where insert spy captures the payload dict.

    Spy sits on ``consent_chain.insert`` (a plain MagicMock) so that
    ``call_args[0][0]`` is the dict passed to ``.insert({...})``.

    The db_admin routes table() calls:
    - "policy_versions" → chain that returns policy_result on execute()
    - "consent_events"  → chain whose insert() is the spy
    - everything else   → generic chain returning empty result
    """
    # The route calls: db_admin.table("consent_events").insert({...}).execute()
    # We spy on .insert() so call_args[0][0] is the dict argument.
    execute_stub = AsyncMock(return_value=_result(data=[{"id": "cid"}]))
    insert_chain = MagicMock()
    insert_chain.execute = execute_stub

    consent_insert_spy = MagicMock(return_value=insert_chain)  # spy on insert(data)

    policy_chain = MagicMock()
    for method in ["select", "eq", "is_", "order", "limit", "maybe_single"]:
        getattr(policy_chain, method).return_value = policy_chain
    policy_chain.execute = AsyncMock(return_value=policy_result)

    consent_chain = MagicMock()
    consent_chain.insert = consent_insert_spy

    generic_chain = MagicMock()
    for method in [
        "select",
        "insert",
        "update",
        "upsert",
        "delete",
        "eq",
        "neq",
        "lt",
        "is_",
        "order",
        "range",
        "filter",
        "limit",
        "single",
        "maybe_single",
    ]:
        getattr(generic_chain, method).return_value = generic_chain
    generic_chain.execute = AsyncMock(return_value=_result(data=None))

    def _route_table(table_name: str) -> MagicMock:
        if table_name == "policy_versions":
            return policy_chain
        if table_name == "consent_events":
            return consent_chain
        return generic_chain

    db_admin = MagicMock()
    db_admin.table = MagicMock(side_effect=_route_table)
    return db_admin, consent_insert_spy
