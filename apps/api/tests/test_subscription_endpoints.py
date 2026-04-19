"""HTTP endpoint tests for app/routers/subscription.py.

Complements test_subscription.py with additional edge-case coverage:

  GET  /api/subscription/status
    - 401 without auth
    - 200 trial active (days_remaining > 0, is_active True)
    - 200 trial auto-expired (trial_ends_at in past → status becomes 'expired')
    - 200 active subscription
    - 200 cancelled subscription (is_active False, days_remaining 0)
    - 404 when profile row missing
    - stripe_customer_id never exposed in response

  POST /api/subscription/create-checkout
    - 401 without auth
    - 503 PAYMENT_NOT_ENABLED when settings.payment_enabled=False
    - 503 STRIPE_NOT_CONFIGURED when stripe_secret_key empty
    - 201 checkout_url returned (existing stripe_customer_id, no new customer creation)
    - 201 checkout_url returned (no stripe_customer_id → new customer created + persisted)
    - 404 when profile not found

  POST /api/subscription/webhook
    - 400 when Stripe-Signature header missing
    - 400 INVALID_SIGNATURE on wrong signature
    - 200 received=true for already-processed event (idempotency skip)
    - 200 received=true for unhandled event type
    - 200 received=true + event marked processed for subscription.deleted success
    - 500 for subscription.created when profile update fails (Stripe must retry)
"""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = "00000002-0000-0000-0000-000000000002"
STRIPE_CUSTOMER_ID = "cus_test_endpoint_002"
STRIPE_SUBSCRIPTION_ID = "sub_test_endpoint_002"

# ── Helpers ────────────────────────────────────────────────────────────────────


def _uid_override(uid: str = USER_ID):
    async def _dep():
        return uid

    return _dep


def _db_override(db):
    async def _dep():
        yield db

    return _dep


def _build_chainable(execute_side_effects: list):
    """Supabase-like chainable mock with a sequence of execute() responses."""
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
async def test_get_status_unauthenticated_returns_401_or_403():
    """No auth → real get_current_user_id dep raises 401/403."""
    db = _build_chainable([])
    app.dependency_overrides[get_supabase_user] = _db_override(db)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get("/api/subscription/status")

        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_trial_active_returns_200():
    """Active trial → 200, is_active=True, days_remaining > 0."""
    future = (datetime.now(UTC) + timedelta(days=14)).isoformat()
    profile_row = {
        "subscription_status": "trial",
        "trial_ends_at": future,
        "subscription_ends_at": None,
        "stripe_customer_id": None,
    }
    db = _build_chainable([profile_row])
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "trial"
        assert body["is_active"] is True
        assert body["days_remaining"] > 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_trial_auto_expires_when_past():
    """Trial ended in the past → router writes 'expired' to DB and returns expired status."""
    past = (datetime.now(UTC) - timedelta(days=3)).isoformat()
    profile_row = {
        "subscription_status": "trial",
        "trial_ends_at": past,
        "subscription_ends_at": None,
        "stripe_customer_id": None,
    }
    # First execute = profile select, second = update to expired
    db = _build_chainable([profile_row, {"id": USER_ID}])
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "expired"
        assert body["is_active"] is False
        assert body["days_remaining"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_active_subscription_returns_200():
    """Paid subscription → 200, is_active=True, days_remaining > 0."""
    future = (datetime.now(UTC) + timedelta(days=20)).isoformat()
    profile_row = {
        "subscription_status": "active",
        "trial_ends_at": None,
        "subscription_ends_at": future,
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
    }
    db = _build_chainable([profile_row])
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "active"
        assert body["is_active"] is True
        assert body["days_remaining"] > 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_cancelled_returns_200_inactive():
    """Cancelled subscription → 200, is_active=False, days_remaining=0."""
    profile_row = {
        "subscription_status": "cancelled",
        "trial_ends_at": None,
        "subscription_ends_at": None,
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
    }
    db = _build_chainable([profile_row])
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "cancelled"
        assert body["is_active"] is False
        assert body["days_remaining"] == 0
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_missing_profile_returns_404():
    """Profile row absent (maybe_single returns no data) → 404 PROFILE_NOT_FOUND."""
    db = _build_chainable([None])
    # maybe_single returning None means result.data is None
    result_mock = MagicMock()
    result_mock.data = None
    db.execute = AsyncMock(return_value=result_mock)

    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 404, resp.text
        body = resp.json()
        assert body["detail"]["code"] == "PROFILE_NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_status_never_exposes_stripe_customer_id():
    """stripe_customer_id must NEVER appear in the response body (security gate)."""
    future = (datetime.now(UTC) + timedelta(days=7)).isoformat()
    profile_row = {
        "subscription_status": "trial",
        "trial_ends_at": future,
        "subscription_ends_at": None,
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
    }
    db = _build_chainable([profile_row])
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.get(
                "/api/subscription/status",
                headers={"Authorization": "Bearer fake-token"},
            )

        assert resp.status_code == 200, resp.text
        raw = resp.text
        assert STRIPE_CUSTOMER_ID not in raw, f"stripe_customer_id leaked into response: {raw}"
        assert "stripe_customer_id" not in resp.json()
    finally:
        app.dependency_overrides.clear()


# ── POST /api/subscription/create-checkout ────────────────────────────────────


@pytest.mark.asyncio
async def test_create_checkout_unauthenticated_returns_401_or_403():
    """No auth → 401/403 before any Stripe call."""
    db = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/subscription/create-checkout")

        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_payment_disabled_returns_503():
    """settings.payment_enabled=False → 503 PAYMENT_NOT_ENABLED before any Stripe call."""
    db = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    with patch("app.routers.subscription.settings") as mock_settings:
        mock_settings.payment_enabled = False
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 503, resp.text
            body = resp.json()
            assert body["detail"]["code"] == "PAYMENT_NOT_ENABLED"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_stripe_key_missing_returns_503():
    """stripe_secret_key empty → 503 STRIPE_NOT_CONFIGURED."""
    db = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    with patch("app.routers.subscription.settings") as mock_settings:
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = ""
        mock_settings.stripe_webhook_secret = ""
        mock_settings.stripe_price_id = ""
        mock_settings.app_url = "https://volaura.app"

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 503, resp.text
            body = resp.json()
            assert body["detail"]["code"] == "STRIPE_NOT_CONFIGURED"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_existing_customer_returns_201():
    """Profile already has stripe_customer_id → skips customer creation, returns checkout URL."""
    profile_row = {
        "stripe_customer_id": STRIPE_CUSTOMER_ID,
        "subscription_status": "trial",
    }
    db = _build_chainable([profile_row])

    mock_user_resp = MagicMock()
    mock_user_resp.user = MagicMock()
    mock_user_resp.user.email = "test@volaura.app"
    db.auth = MagicMock()
    db.auth.admin = MagicMock()
    db.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user_resp)

    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    fake_session = {"url": "https://checkout.stripe.com/pay/cs_test_existing_cust"}

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
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 201, resp.text
            body = resp.json()
            assert "checkout_url" in body
            assert body["checkout_url"].startswith("https://checkout.stripe.com/")
            # Customer.create must NOT have been called — customer already linked
            mock_stripe.Customer.create.assert_not_called()
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_new_customer_created_and_persisted():
    """No stripe_customer_id → creates Stripe Customer, persists it, then creates checkout."""
    profile_row = {
        "stripe_customer_id": None,
        "subscription_status": "trial",
    }
    # Two DB calls: profile select + stripe_customer_id persist update
    db = _build_chainable([profile_row, {"id": USER_ID}])

    mock_user_resp = MagicMock()
    mock_user_resp.user = MagicMock()
    mock_user_resp.user.email = "newuser@volaura.app"
    db.auth = MagicMock()
    db.auth.admin = MagicMock()
    db.auth.admin.get_user_by_id = AsyncMock(return_value=mock_user_resp)

    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    fake_customer = {"id": "cus_test_newly_created"}
    fake_session = {"url": "https://checkout.stripe.com/pay/cs_test_new_cust"}

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
        mock_stripe.Customer.create = MagicMock(return_value=fake_customer)
        mock_stripe.checkout = MagicMock()
        mock_stripe.checkout.Session = MagicMock()
        mock_stripe.checkout.Session.create = MagicMock(return_value=fake_session)

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 201, resp.text
            body = resp.json()
            assert body["checkout_url"].startswith("https://checkout.stripe.com/")
            # Customer creation was triggered
            mock_stripe.Customer.create.assert_called_once()
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_checkout_profile_not_found_returns_404():
    """Profile row absent → 404 PROFILE_NOT_FOUND before any Stripe call."""
    result_mock = MagicMock()
    result_mock.data = None
    db = _build_chainable([])
    db.execute = AsyncMock(return_value=result_mock)

    db.auth = MagicMock()
    db.auth.admin = MagicMock()
    db.auth.admin.get_user_by_id = AsyncMock(return_value=MagicMock())

    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_supabase_user] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

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

        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    "/api/subscription/create-checkout",
                    headers={"Authorization": "Bearer fake-token"},
                )

            assert resp.status_code == 404, resp.text
            body = resp.json()
            assert body["detail"]["code"] == "PROFILE_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()


# ── POST /api/subscription/webhook ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_missing_signature_header_returns_400():
    """No Stripe-Signature header → 400 (INVALID_SIGNATURE or INVALID_PAYLOAD)."""
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

        class FakeSigError(Exception):
            pass

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = FakeSigError
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(side_effect=FakeSigError("No signatures found"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type":"test"}',
                headers={"content-type": "application/json"},
                # stripe-signature intentionally absent
            )

        assert resp.status_code == 400, resp.text
        body = resp.json()
        assert body["detail"]["code"] in ("INVALID_SIGNATURE", "INVALID_PAYLOAD")


@pytest.mark.asyncio
async def test_webhook_wrong_signature_returns_400_invalid_signature():
    """Stripe-Signature present but wrong → 400 INVALID_SIGNATURE."""
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

        class FakeSigVerificationError(Exception):
            pass

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = FakeSigVerificationError
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(side_effect=FakeSigVerificationError("Signature mismatch"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type":"customer.subscription.created"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=999,v1=badhash",
                },
            )

        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"]["code"] == "INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_webhook_already_processed_returns_200_and_skips():
    """Duplicate event (already processed) → 200 received=True, no profile update."""
    fake_event = {
        "id": "evt_already_done_001",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "active",
                "current_period_end": int(time.time()) + 86400,
            }
        },
    }

    update_mock = AsyncMock(return_value=True)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
        patch(
            "app.routers.subscription._is_stripe_event_processed",
            new=AsyncMock(return_value=True),  # already processed
        ),
        patch(
            "app.routers.subscription._update_profile_subscription",
            new=update_mock,
        ),
        patch(
            "app.routers.subscription._mark_stripe_event_processed",
            new=AsyncMock(return_value=None),
        ),
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type":"customer.subscription.created"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

    assert resp.status_code == 200, resp.text
    assert resp.json().get("received") is True
    # Profile update must NOT have run — idempotency guard short-circuited
    update_mock.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_unhandled_event_type_returns_200():
    """Unrecognised event type → 200 received=True (acknowledged, no-op)."""
    fake_event = {
        "id": "evt_unhandled_001",
        "type": "payment_intent.succeeded",
        "data": {"object": {}},
    }

    mark_mock = AsyncMock(return_value=None)

    with (
        patch("app.routers.subscription.settings") as mock_settings,
        patch("app.routers.subscription._STRIPE_AVAILABLE", True),
        patch("app.routers.subscription._stripe") as mock_stripe,
        patch(
            "app.routers.subscription._is_stripe_event_processed",
            new=AsyncMock(return_value=False),
        ),
        patch(
            "app.routers.subscription._mark_stripe_event_processed",
            new=mark_mock,
        ),
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type":"payment_intent.succeeded"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

    assert resp.status_code == 200, resp.text
    assert resp.json().get("received") is True
    # Unhandled events are still marked as processed to prevent retry spam
    mark_mock.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_subscription_deleted_success_marks_processed():
    """subscription.deleted + profile update returns True → 200, event IS marked processed."""
    fake_event = {
        "id": "evt_deleted_ok_001",
        "type": "customer.subscription.deleted",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "canceled",
            }
        },
    }

    mark_mock = AsyncMock(return_value=None)

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
            new=mark_mock,
        ),
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type":"customer.subscription.deleted"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

    assert resp.status_code == 200, resp.text
    assert resp.json().get("received") is True
    mark_mock.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_subscription_created_no_profile_returns_500():
    """subscription.created + profile update returns False → 500 so Stripe retries."""
    fake_event = {
        "id": "evt_created_no_profile_001",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": STRIPE_SUBSCRIPTION_ID,
                "customer": STRIPE_CUSTOMER_ID,
                "status": "active",
                "current_period_end": int(time.time()) + 30 * 86400,
            }
        },
    }

    mark_mock = AsyncMock(return_value=None)

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
            new=mark_mock,
        ),
    ):
        mock_settings.payment_enabled = True
        mock_settings.stripe_secret_key = "sk_test_fake"
        mock_settings.stripe_webhook_secret = "whsec_fake"
        mock_settings.stripe_price_id = "price_test_fake"
        mock_settings.app_url = "https://volaura.app"

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook = MagicMock()
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/subscription/webhook",
                content=b'{"type":"customer.subscription.created"}',
                headers={
                    "content-type": "application/json",
                    "stripe-signature": "t=12345,v1=validhash",
                },
            )

    assert resp.status_code == 500, f"Expected 500 so Stripe retries, got {resp.status_code}: {resp.text}"
    # CRITICAL: event must NOT be marked processed — Stripe must be able to retry
    mark_mock.assert_not_called()
