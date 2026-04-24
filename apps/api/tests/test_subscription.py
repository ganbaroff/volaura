"""Integration tests for the subscription router.

Covers:
  GET  /api/subscription/status          (4 tests)
  POST /api/subscription/create-checkout (3 tests)
  POST /api/subscription/webhook         (3 tests)

Patterns follow test_smoke_assessment.py — dependency_overrides + _build_chainable.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "00000001-0000-0000-0000-000000000001"
STRIPE_CUSTOMER_ID = "cus_test_000001"
STRIPE_SUBSCRIPTION_ID = "sub_test_000001"

# ── Helpers (mirrored from test_smoke_assessment.py) ──────────────────────────


def _make_dep_override(value):
    async def _override():
        yield value

    return _override


def _make_user_id_override(user_id: str):
    async def _override():
        return user_id

    return _override


def _build_chainable(execute_side_effects: list):
    """Build a Supabase-like chainable mock with a sequence of execute() responses."""
    mock = MagicMock()
    mock.table = MagicMock(return_value=mock)
    mock.select = MagicMock(return_value=mock)
    mock.insert = MagicMock(return_value=mock)
    mock.update = MagicMock(return_value=mock)
    mock.delete = MagicMock(return_value=mock)
    mock.eq = MagicMock(return_value=mock)
    mock.neq = MagicMock(return_value=mock)
    mock.gte = MagicMock(return_value=mock)
    mock.lte = MagicMock(return_value=mock)
    mock.gt = MagicMock(return_value=mock)
    mock.lt = MagicMock(return_value=mock)
    mock.order = MagicMock(return_value=mock)
    mock.limit = MagicMock(return_value=mock)
    mock.range = MagicMock(return_value=mock)
    mock.filter = MagicMock(return_value=mock)
    mock.not_ = MagicMock(return_value=mock)
    mock.in_ = MagicMock(return_value=mock)
    mock.single = MagicMock(return_value=mock)
    mock.maybe_single = MagicMock(return_value=mock)
    mock.rpc = MagicMock(return_value=mock)

    responses = iter(execute_side_effects)

    async def _execute(*args, **kwargs):
        try:
            val = next(responses)
            if isinstance(val, MagicMock):
                return val
            return MagicMock(data=val)
        except StopIteration:
            return MagicMock(data=None)

    mock.execute = AsyncMock(side_effect=_execute)
    return mock


# ── GET /api/subscription/status ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_status_trial_active():
    """User has status='trial', trial_ends_at = future → is_active=True, days_remaining > 0."""
    future = (datetime.now(UTC) + timedelta(days=10)).isoformat()
    profile_row = {
        "subscription_status": "trial",
        "trial_ends_at": future,
        "subscription_ends_at": None,
        "stripe_customer_id": None,
    }

    admin = _build_chainable([profile_row])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["status"] == "trial"
        assert body["is_active"] is True
        assert body["days_remaining"] > 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_trial_expired():
    """User has status='trial', trial_ends_at = past → auto-expires to 'expired', is_active=False."""
    past = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    profile_row = {
        "subscription_status": "trial",
        "trial_ends_at": past,
        "subscription_ends_at": None,
        "stripe_customer_id": None,
    }

    # First execute: single() profile select
    # Second execute: update subscription_status to 'expired'
    admin = _build_chainable([profile_row, {"id": USER_ID}])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["status"] == "expired"
        assert body["is_active"] is False
        assert body["days_remaining"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_active_subscription():
    """User has status='active', subscription_ends_at = future → is_active=True."""
    future = (datetime.now(UTC) + timedelta(days=25)).isoformat()
    profile_row = {
        "subscription_status": "active",
        "trial_ends_at": None,
        "subscription_ends_at": future,
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
    }

    admin = _build_chainable([profile_row])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["status"] == "active"
        assert body["is_active"] is True
        assert body["days_remaining"] > 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_unauthenticated():
    """No auth header → 401 or 403 (get_current_user_id raises)."""
    # Mock admin dep so SupabaseAdmin init doesn't fail in test env (no real key).
    # Do NOT override get_current_user_id — let the real dep run (raises 401/403).
    admin = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    # Do NOT set get_current_user_id override → unauthenticated

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/subscription/status")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)

    assert resp.status_code in (401, 403), (
        f"Expected 401 or 403 for unauthenticated request, got {resp.status_code}: {resp.text}"
    )


# ── POST /api/subscription/create-checkout ────────────────────────────────────


@pytest.mark.asyncio
async def test_create_checkout_no_stripe_configured():
    """STRIPE_SECRET_KEY not set → 503 with code STRIPE_NOT_CONFIGURED."""
    admin = _build_chainable([])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    # Patch settings so stripe_secret_key is empty
    with patch("app.routers.subscription.settings") as mock_settings:
        mock_settings.stripe_secret_key = ""
        mock_settings.stripe_webhook_secret = ""
        mock_settings.stripe_price_id = ""
        mock_settings.app_url = "https://volaura.app"

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["detail"]["code"] == "STRIPE_NOT_CONFIGURED"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_with_stripe_mock():
    """Stripe fully mocked → returns {checkout_url: 'https://checkout.stripe.com/...'}."""
    profile_row = {
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
        "subscription_status": "trial",
    }

    admin = _build_chainable(
        [
            profile_row,  # profile select (stripe_customer_id + subscription_status)
            {"id": USER_ID},  # profiles.update (stripe_customer_id persist — skipped if already set)
        ]
    )

    # Mock auth.admin.get_user_by_id
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = "test@volaura.app"
    admin.auth = MagicMock()
    admin.auth.admin = MagicMock()
    admin.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user)

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    # Build a fake Stripe checkout session response
    fake_session = {"url": "https://checkout.stripe.com/pay/cs_test_fake123"}

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.api_key = None
        mock_stripe.checkout = MagicMock()
        mock_stripe.checkout.Session = MagicMock()
        mock_stripe.checkout.Session.create = MagicMock(return_value=fake_session)

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert "checkout_url" in body
            assert body["checkout_url"].startswith("https://checkout.stripe.com/")
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_unauthenticated():
    """No auth header → 401 or 403."""
    # Mock admin dep so SupabaseAdmin init doesn't fail in test env (no real key).
    # Do NOT override get_current_user_id → unauthenticated request.
    admin = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)

    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/api/subscription/create-checkout")
    finally:
        app.dependency_overrides.pop(get_supabase_admin, None)

    assert resp.status_code in (401, 403), (
        f"Expected 401 or 403 for unauthenticated request, got {resp.status_code}: {resp.text}"
    )


# ── POST /api/subscription/webhook ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_no_signature():
    """Missing stripe-signature header → 400 with INVALID_SIGNATURE or STRIPE_NOT_CONFIGURED.

    If STRIPE_WEBHOOK_SECRET is not set on the test server, the router returns 503.
    With it set but no signature header, the Webhook.construct_event raises ValueError
    which maps to INVALID_PAYLOAD (400). We test the common path: sig header missing.
    """
    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        # Stripe raises ValueError when sig_header is empty string
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = ValueError
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(side_effect=ValueError("No signatures found"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "test"}',
                headers={"content-type": "application/json"},
                # stripe-signature header intentionally omitted
            )

        assert resp.status_code == 400, f"Expected 400 for missing signature, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["detail"]["code"] in ("INVALID_SIGNATURE", "INVALID_PAYLOAD", "MISSING_SIGNATURE")


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    """Wrong stripe-signature header → 400 with INVALID_SIGNATURE."""
    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        # Create a fake SignatureVerificationError class for the stripe module
        class FakeSignatureVerificationError(Exception):
            pass

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = FakeSignatureVerificationError
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(
            side_effect=FakeSignatureVerificationError("Signature mismatch")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "customer.subscription.created"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=badhash",
                },
            )

        assert resp.status_code == 400, f"Expected 400 for invalid signature, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["detail"]["code"] == "INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_webhook_subscription_created():
    """Valid signature, subscription.created event → updates profile, returns {received: true}."""
    import time

    current_period_end = int(time.time()) + 30 * 24 * 3600  # 30 days from now

    fake_event = {
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "active",
                "current_period_end": current_period_end,
            }
        },
    }

    # The webhook handler calls _update_profile_subscription which creates its own
    # Supabase admin client via acreate_client. We patch that factory directly.
    _build_chainable(
        [
            [{"id": USER_ID}],  # profiles.update result (truthy = no warning logged)
        ]
    )

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
        patch(
            "app.routers.subscription._update_profile_subscription",
            new=AsyncMock(return_value=None),
        ) as mock_update,
        patch(
            "app.routers.subscription._is_stripe_event_processed",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._mark_stripe_event_processed",
            new=AsyncMock(return_value=None),
        ),
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        # construct_event returns the fake event object without raising
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "customer.subscription.created"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

        assert resp.status_code == 200, f"Expected 200 for valid webhook, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("received") is True, f"Expected received=true, got: {body}"

        # Verify the profile update was triggered with the right customer ID
        mock_update.assert_called_once()
        call_args = mock_update.call_args
        assert call_args[0][0] == STRIPE_CUSTOMER_ID
        update_payload = call_args[0][1]
        assert update_payload["subscription_status"] == "active"
        assert update_payload["stripe_subscription_id"] == STRIPE_SUBSCRIPTION_ID


# ── P0-1 regression: asymmetric error handling (ghost-code audit 2026-04-15) ──
# When _update_profile_subscription returns False (no matching profile row),
# .updated and .deleted handlers MUST raise 500 so Stripe retries AND must NOT
# mark the event as processed. Previously they discarded the bool → revenue loss.


@pytest.mark.asyncio
async def test_webhook_subscription_updated_no_profile_raises_500_and_does_not_mark_processed():
    """customer.subscription.updated + profile update returns False → 500, event NOT marked processed."""
    import time

    current_period_end = int(time.time()) + 30 * 24 * 3600

    fake_event = {
        "id": "evt_updated_no_profile_001",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "canceled",
                "current_period_end": current_period_end,
            }
        },
    }

    mark_processed_mock = AsyncMock(return_value=None)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
        patch(
            "app.routers.subscription._update_profile_subscription",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._is_stripe_event_processed",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._mark_stripe_event_processed",
            new=mark_processed_mock,
        ),
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "customer.subscription.updated"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

        assert resp.status_code == 500, f"Expected 500 so Stripe retries, got {resp.status_code}: {resp.text}"
        # CRITICAL: idempotency row must NOT be written — otherwise retry is no-op.
        mark_processed_mock.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_subscription_deleted_no_profile_raises_500_and_does_not_mark_processed():
    """customer.subscription.deleted + profile update returns False → 500, event NOT marked processed."""
    fake_event = {
        "id": "evt_deleted_no_profile_001",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "canceled",
            }
        },
    }

    mark_processed_mock = AsyncMock(return_value=None)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
        patch(
            "app.routers.subscription._update_profile_subscription",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._is_stripe_event_processed",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._mark_stripe_event_processed",
            new=mark_processed_mock,
        ),
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "customer.subscription.deleted"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

        assert resp.status_code == 500, f"Expected 500 so Stripe retries, got {resp.status_code}: {resp.text}"
        mark_processed_mock.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_subscription_updated_success_marks_processed():
    """customer.subscription.updated + profile update returns True → 200, event IS marked processed."""
    import time

    current_period_end = int(time.time()) + 30 * 24 * 3600

    fake_event = {
        "id": "evt_updated_ok_001",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "canceled",
                "current_period_end": current_period_end,
            }
        },
    }

    mark_processed_mock = AsyncMock(return_value=None)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
        patch(
            "app.routers.subscription._update_profile_subscription",
            new=AsyncMock(return_value=True),
        ),
        patch(
            "app.routers.subscription._is_stripe_event_processed",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._mark_stripe_event_processed",
            new=mark_processed_mock,
        ),
    ):
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "customer.subscription.updated"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

        assert resp.status_code == 200, f"Expected 200 on success, got {resp.status_code}: {resp.text}"
        mark_processed_mock.assert_called_once()


# ── New tests: missing-line coverage ─────────────────────────────────────────
# Target lines: 42-44, 72, 122, 175-179, 195-197, 204, 216, 232-236,
#               264-265, 285-287, 355-362, 367-384, 395-404, 412-436


# Lines 42-44 / 72: _STRIPE_AVAILABLE=False → _get_stripe_client raises 503

@pytest.mark.asyncio
async def test_get_stripe_client_stripe_not_available_raises_503():
    """When _STRIPE_AVAILABLE is False and payment_enabled=True, _get_stripe_client raises 503."""
    from app.routers.subscription import _get_stripe_client

    with (
        patch("app.routers.subscription._STRIPE_AVAILABLE", False),
        patch("app.routers.subscription.settings") as mock_settings,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"

        with pytest.raises(Exception) as exc_info:
            _get_stripe_client()

        # Should raise HTTPException 503
        exc = exc_info.value
        assert exc.status_code == 503
        assert exc.detail["code"] == "STRIPE_NOT_CONFIGURED"


# Line 122: naive datetime branch in get_subscription_status

@pytest.mark.asyncio
async def test_get_status_trial_naive_datetime_gets_tz_added():
    """trial_ends_at as naive datetime string (no tz) → line 122 replace(tzinfo=UTC), then expires."""
    # Use a PAST naive datetime — this triggers line 122 (tzinfo=None branch) then the expiry branch.
    # The expiry path writes "expired" to DB and returns expired status (no schema tz arithmetic needed).
    from datetime import timedelta
    past_naive = (datetime.now(UTC).replace(tzinfo=None) - timedelta(days=3)).isoformat()
    profile_row = {
        "subscription_status": "trial",
        "trial_ends_at": past_naive,
        "subscription_ends_at": None,
        "stripe_customer_id": None,
    }

    # Two executes: profile select + update to expired
    admin = _build_chainable([profile_row, {"id": USER_ID}])

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["status"] == "expired"
        assert body["is_active"] is False
    finally:
        app.dependency_overrides.clear()


# Lines 175-179: auth exception swallowed → checkout still proceeds

@pytest.mark.asyncio
async def test_create_checkout_auth_exception_swallowed_proceeds():
    """db.auth.admin.get_user_by_id raises → user_email=None, checkout still succeeds (201)."""
    profile_row = {
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
        "subscription_status": "trial",
    }
    admin = _build_chainable([profile_row])

    # Simulate auth call raising an exception
    admin.auth = MagicMock()
    admin.auth.admin = MagicMock()
    admin.auth.admin.get_user_by_id = AsyncMock(side_effect=RuntimeError("auth service down"))

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    fake_session = {"url": "https://checkout.stripe.com/pay/cs_test_auth_exc"}

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.api_key = None
        mock_stripe.checkout = MagicMock()
        mock_stripe.checkout.Session = MagicMock()
        mock_stripe.checkout.Session.create = MagicMock(return_value=fake_session)

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert "checkout_url" in body
        finally:
            app.dependency_overrides.clear()


# Lines 195-197: Stripe Customer.create raises → 502

@pytest.mark.asyncio
async def test_create_checkout_customer_create_exception_returns_502():
    """stripe.Customer.create raises → 502 STRIPE_ERROR."""
    profile_row = {
        "stripe_customer_id": None,  # force customer creation path
        "subscription_status": "trial",
    }
    admin = _build_chainable([profile_row])

    admin.auth = MagicMock()
    admin.auth.admin = MagicMock()
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = "user@volaura.app"
    admin.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user)

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.api_key = None
        mock_stripe.Customer = MagicMock()
        mock_stripe.Customer.create = MagicMock(side_effect=RuntimeError("Stripe down"))

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 502, f"Expected 502, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["detail"]["code"] == "STRIPE_ERROR"
        finally:
            app.dependency_overrides.clear()


# Line 204: stripe_price_id empty → 503

@pytest.mark.asyncio
async def test_create_checkout_no_price_id_returns_503():
    """stripe_price_id empty after customer exists → 503 STRIPE_NOT_CONFIGURED."""
    profile_row = {
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
        "subscription_status": "trial",
    }
    admin = _build_chainable([profile_row])

    admin.auth = MagicMock()
    admin.auth.admin = MagicMock()
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = "user@volaura.app"
    admin.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user)

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = ""  # empty → triggers line 204
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.api_key = None

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["detail"]["code"] == "STRIPE_NOT_CONFIGURED"
        finally:
            app.dependency_overrides.clear()


# Lines 216 + 233: inner price_id check raises HTTPException, caught by except HTTPException → re-raised

@pytest.mark.asyncio
async def test_create_checkout_inner_price_id_check_raises_503():
    """stripe_price_id truthy first time (passes line 203), falsy inside try (hits line 216+233)."""
    profile_row = {
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
        "subscription_status": "trial",
    }
    admin = _build_chainable([profile_row])

    admin.auth = MagicMock()
    admin.auth.admin = MagicMock()
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = "user@volaura.app"
    admin.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user)

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.app_url = "https://volaura.app"
        mock_stripe.api_key = None

        # First access returns truthy (passes line 203 guard),
        # second access returns falsy (triggers line 215 inner guard → 216 raise → 233 re-raise)
        call_count = {"n": 0}

        def price_id_side_effect():
            call_count["n"] += 1
            return "price_real" if call_count["n"] == 1 else ""

        type(mock_settings).stripe_secret_key = property(lambda s: "sk_test_fake")
        type(mock_settings).stripe_price_id = property(lambda s: price_id_side_effect())

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["detail"]["code"] == "STRIPE_NOT_CONFIGURED"
        finally:
            app.dependency_overrides.clear()


# Lines 232-236: Session.create raises → 502

@pytest.mark.asyncio
async def test_create_checkout_session_create_exception_returns_502():
    """stripe.checkout.Session.create raises → 502 STRIPE_ERROR."""
    profile_row = {
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
        "subscription_status": "trial",
    }
    admin = _build_chainable([profile_row])

    admin.auth = MagicMock()
    admin.auth.admin = MagicMock()
    mock_user = MagicMock()
    mock_user.user = MagicMock()
    mock_user.user.email = "user@volaura.app"
    admin.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user)

    app.dependency_overrides[get_supabase_admin] = _make_dep_override(admin)
    app.dependency_overrides[get_supabase_user] = _make_dep_override(admin)
    app.dependency_overrides[get_current_user_id] = _make_user_id_override(USER_ID)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.api_key = None
        mock_stripe.checkout = MagicMock()
        mock_stripe.checkout.Session = MagicMock()
        mock_stripe.checkout.Session.create = MagicMock(side_effect=RuntimeError("Stripe checkout error"))

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 502, f"Expected 502, got {resp.status_code}: {resp.text}"
            body = resp.json()
            assert body["detail"]["code"] == "STRIPE_ERROR"
        finally:
            app.dependency_overrides.clear()


# Lines 264-265: webhook_secret empty → 503

@pytest.mark.asyncio
async def test_webhook_no_webhook_secret_returns_503():
    """stripe_webhook_secret empty → 503 STRIPE_NOT_CONFIGURED."""
    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = ""  # empty → triggers lines 264-265
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.api_key = None

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "test"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

        assert resp.status_code == 503, f"Expected 503, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["detail"]["code"] == "STRIPE_NOT_CONFIGURED"


# Lines 285-287: construct_event raises generic Exception (not SignatureVerificationError) → 400

@pytest.mark.asyncio
async def test_webhook_construct_event_generic_exception_returns_400():
    """construct_event raises generic Exception (not SignatureVerificationError) → 400 INVALID_PAYLOAD."""
    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        # SignatureVerificationError is a DIFFERENT class than the one being raised
        class FakeSigError(Exception):
            pass

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = FakeSigError
        mock_stripe.Webhook = MagicMock()
        # Raise a plain ValueError — NOT the SignatureVerificationError subclass
        mock_stripe.Webhook.construct_event = MagicMock(side_effect=ValueError("malformed JSON"))

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b"not-valid-json",
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body["detail"]["code"] == "INVALID_PAYLOAD"


# Lines 355-362: _is_stripe_event_processed — direct unit test

@pytest.mark.asyncio
async def test_is_stripe_event_processed_found():
    """_is_stripe_event_processed returns True when event_id exists in DB."""
    from app.routers.subscription import _is_stripe_event_processed

    mock_admin = MagicMock()
    # Build chainable that returns data with event_id
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.select = MagicMock(return_value=mock_admin)
    mock_admin.eq = MagicMock(return_value=mock_admin)
    mock_admin.limit = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[{"event_id": "evt_test_found"}]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        result = await _is_stripe_event_processed("evt_test_found")

    assert result is True


@pytest.mark.asyncio
async def test_is_stripe_event_processed_not_found():
    """_is_stripe_event_processed returns False when event_id not in DB."""
    from app.routers.subscription import _is_stripe_event_processed

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.select = MagicMock(return_value=mock_admin)
    mock_admin.eq = MagicMock(return_value=mock_admin)
    mock_admin.limit = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        result = await _is_stripe_event_processed("evt_test_missing")

    assert result is False


# Lines 367-384: _mark_stripe_event_processed — direct unit tests (success + exception branch)

@pytest.mark.asyncio
async def test_mark_stripe_event_processed_success():
    """_mark_stripe_event_processed inserts without error → completes silently."""
    from app.routers.subscription import _mark_stripe_event_processed

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.insert = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[{"event_id": "evt_mark_ok"}]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        # Should not raise
        await _mark_stripe_event_processed("evt_mark_ok", "customer.subscription.created")

    mock_admin.insert.assert_called_once()


@pytest.mark.asyncio
async def test_mark_stripe_event_processed_exception_swallowed():
    """_mark_stripe_event_processed insert raises → exception swallowed, no re-raise."""
    from app.routers.subscription import _mark_stripe_event_processed

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.insert = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(side_effect=RuntimeError("DB constraint violation"))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        # Must NOT raise — exception is logged and swallowed (lines 382-384)
        await _mark_stripe_event_processed("evt_mark_exc", "customer.subscription.updated")


# Lines 395-404: _resolve_user_id_by_stripe_customer — direct unit tests

@pytest.mark.asyncio
async def test_resolve_user_id_by_stripe_customer_found():
    """_resolve_user_id_by_stripe_customer returns user_id when profile found."""
    from app.routers.subscription import _resolve_user_id_by_stripe_customer

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.select = MagicMock(return_value=mock_admin)
    mock_admin.eq = MagicMock(return_value=mock_admin)
    mock_admin.limit = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[{"id": USER_ID}]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        result = await _resolve_user_id_by_stripe_customer("cus_test123")

    assert result == USER_ID


@pytest.mark.asyncio
async def test_resolve_user_id_by_stripe_customer_not_found():
    """_resolve_user_id_by_stripe_customer returns None when no profile found."""
    from app.routers.subscription import _resolve_user_id_by_stripe_customer

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.select = MagicMock(return_value=mock_admin)
    mock_admin.eq = MagicMock(return_value=mock_admin)
    mock_admin.limit = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        result = await _resolve_user_id_by_stripe_customer("cus_unknown")

    assert result is None


# Lines 412-436: _update_profile_subscription — direct unit tests (success + not-found)

@pytest.mark.asyncio
async def test_update_profile_subscription_success_returns_true():
    """_update_profile_subscription returns True when profile row updated."""
    from app.routers.subscription import _update_profile_subscription

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.update = MagicMock(return_value=mock_admin)
    mock_admin.eq = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[{"id": USER_ID}]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        result = await _update_profile_subscription(
            STRIPE_CUSTOMER_ID,
            {"subscription_status": "active"},
        )

    assert result is True


@pytest.mark.asyncio
async def test_update_profile_subscription_no_row_returns_false():
    """_update_profile_subscription returns False when no profile matched (empty data)."""
    from app.routers.subscription import _update_profile_subscription

    mock_admin = MagicMock()
    mock_admin.table = MagicMock(return_value=mock_admin)
    mock_admin.update = MagicMock(return_value=mock_admin)
    mock_admin.eq = MagicMock(return_value=mock_admin)
    mock_admin.execute = AsyncMock(return_value=MagicMock(data=[]))

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("supabase._async.client.create_client", new=AsyncMock(return_value=mock_admin)),
    ):
        mock_settings.supabase_url = "https://fake.supabase.co"
        mock_settings.supabase_service_key = "fake-service-key"

        result = await _update_profile_subscription(
            "cus_no_match",
            {"subscription_status": "cancelled"},
        )

    assert result is False
