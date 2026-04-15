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

            assert resp.status_code == 503, (
                f"Expected 503, got {resp.status_code}: {resp.text}"
            )
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

    admin = _build_chainable([
        profile_row,        # profile select (stripe_customer_id + subscription_status)
        {"id": USER_ID},    # profiles.update (stripe_customer_id persist — skipped if already set)
    ])

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

    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe:

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

            assert resp.status_code == 201, (
                f"Expected 201, got {resp.status_code}: {resp.text}"
            )
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
    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe:

        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        # Stripe raises ValueError when sig_header is empty string
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = ValueError
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(
            side_effect=ValueError("No signatures found")
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type": "test"}',
                headers={"content-type": "application/json"},
                # stripe-signature header intentionally omitted
            )

        assert resp.status_code == 400, (
            f"Expected 400 for missing signature, got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        assert body["detail"]["code"] in ("INVALID_SIGNATURE", "INVALID_PAYLOAD", "MISSING_SIGNATURE")


@pytest.mark.asyncio
async def test_webhook_invalid_signature():
    """Wrong stripe-signature header → 400 with INVALID_SIGNATURE."""
    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe:

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

        assert resp.status_code == 400, (
            f"Expected 400 for invalid signature, got {resp.status_code}: {resp.text}"
        )
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
    _build_chainable([
        [{"id": USER_ID}],   # profiles.update result (truthy = no warning logged)
    ])

    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe, \
         patch(
             "app.routers.subscription._update_profile_subscription",
             new=AsyncMock(return_value=None),
         ) as mock_update, \
         patch(
             "app.routers.subscription._is_stripe_event_processed",
             new=AsyncMock(return_value=False),
         ), \
         patch(
             "app.routers.subscription._mark_stripe_event_processed",
             new=AsyncMock(return_value=None),
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

        assert resp.status_code == 200, (
            f"Expected 200 for valid webhook, got {resp.status_code}: {resp.text}"
        )
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

    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe, \
         patch(
             "app.routers.subscription._update_profile_subscription",
             new=AsyncMock(return_value=False),
         ), \
         patch(
             "app.routers.subscription._is_stripe_event_processed",
             new=AsyncMock(return_value=False),
         ), \
         patch(
             "app.routers.subscription._mark_stripe_event_processed",
             new=mark_processed_mock,
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

        assert resp.status_code == 500, (
            f"Expected 500 so Stripe retries, got {resp.status_code}: {resp.text}"
        )
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

    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe, \
         patch(
             "app.routers.subscription._update_profile_subscription",
             new=AsyncMock(return_value=False),
         ), \
         patch(
             "app.routers.subscription._is_stripe_event_processed",
             new=AsyncMock(return_value=False),
         ), \
         patch(
             "app.routers.subscription._mark_stripe_event_processed",
             new=mark_processed_mock,
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

        assert resp.status_code == 500, (
            f"Expected 500 so Stripe retries, got {resp.status_code}: {resp.text}"
        )
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

    with patch("app.routers.subscription.settings") as mock_settings, \
         patch("app.routers.subscription._STRIPE_AVAILABLE", True), \
         patch("app.routers.subscription._stripe") as mock_stripe, \
         patch(
             "app.routers.subscription._update_profile_subscription",
             new=AsyncMock(return_value=True),
         ), \
         patch(
             "app.routers.subscription._is_stripe_event_processed",
             new=AsyncMock(return_value=False),
         ), \
         patch(
             "app.routers.subscription._mark_stripe_event_processed",
             new=mark_processed_mock,
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

        assert resp.status_code == 200, (
            f"Expected 200 on success, got {resp.status_code}: {resp.text}"
        )
        mark_processed_mock.assert_called_once()
