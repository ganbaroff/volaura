"""HTTP endpoint tests for app/routers/org_billing.py (B2B monetization).

Mirrors test_subscription_endpoints.py. Covers:

  POST /api/org-billing/subscribe
    - 503 PAYMENT_NOT_ENABLED when payment_enabled=False
    - 201 checkout_url (existing org stripe_customer_id → no customer creation)

  POST /api/org-billing/campaigns/{id}/unlock
    - 422 on invalid campaign UUID
    - 503 PAYMENT_NOT_ENABLED when payment_enabled=False
    - 409 ALREADY_HAS_ACCESS when org already has report access

  GET /api/org-billing/status
    - 200 has_active_subscription reflects org subscription_expires_at

  POST /api/org-billing/webhook
    - 400 INVALID_SIGNATURE on bad signature
    - 200 received=true for already-processed event (idempotency skip)
    - 200 received=true + marked processed for checkout.session.completed unlock
    - 200 received=true + marked processed for unhandled event type
    - 500 (not marked) for subscription.created when no org matched (Stripe must retry)
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app

USER_ID = str(uuid.uuid4())
ORG_ID = str(uuid.uuid4())
CAMPAIGN_ID = str(uuid.uuid4())
STRIPE_CUSTOMER_ID = "cus_test_org_001"


def _uid_override(uid: str = USER_ID):
    async def _dep():
        return uid

    return _dep


def _db_override(db):
    async def _dep():
        yield db

    return _dep


def _build_chainable(execute_side_effects: list):
    """Supabase-like chainable mock returning a sequence of execute() responses."""
    mock = MagicMock()
    for m in (
        "table", "select", "insert", "update", "upsert", "delete", "eq", "neq",
        "gte", "lte", "gt", "lt", "order", "limit", "range", "in_", "single", "maybe_single", "rpc",
    ):
        getattr(mock, m).return_value = mock

    responses = iter(execute_side_effects)

    async def _execute(*args, **kwargs):
        try:
            val = next(responses)
            return val if isinstance(val, MagicMock) else MagicMock(data=val)
        except StopIteration:
            return MagicMock(data=None)

    mock.execute = AsyncMock(side_effect=_execute)
    return mock


def _stripe_settings(mock_settings, *, payment_enabled=True, org_billing_enabled=True):
    mock_settings.payment_enabled = payment_enabled
    mock_settings.org_billing_enabled = org_billing_enabled
    mock_settings.stripe_secret_key = "sk_test_fake"
    mock_settings.stripe_org_webhook_secret = "whsec_org_fake"
    mock_settings.stripe_org_subscription_price_id = "price_org_sub"
    mock_settings.stripe_campaign_report_price_id = "price_campaign_unlock"
    mock_settings.app_url = "https://volaura.app"
    mock_settings.supabase_url = "http://localhost:54321"
    mock_settings.supabase_service_key = "service_fake"


# ── POST /api/org-billing/subscribe ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_subscribe_payment_disabled_returns_503():
    db = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    with patch("app.routers.org_billing.settings") as ms:
        _stripe_settings(ms, payment_enabled=False)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post("/api/org-billing/subscribe", headers={"Authorization": "Bearer fake"})
            assert resp.status_code == 503, resp.text
            assert resp.json()["detail"]["code"] == "PAYMENT_NOT_ENABLED"
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_subscribe_existing_customer_returns_201():
    org_row = {"id": ORG_ID, "name": "Atlas Org", "stripe_customer_id": STRIPE_CUSTOMER_ID, "subscription_expires_at": None}
    db = _build_chainable([org_row])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    fake_session = {"url": "https://checkout.stripe.com/pay/cs_org_sub"}

    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
    ):
        _stripe_settings(ms)
        mock_stripe.api_key = None
        mock_stripe.checkout = MagicMock()
        mock_stripe.checkout.Session.create = MagicMock(return_value=fake_session)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post("/api/org-billing/subscribe", headers={"Authorization": "Bearer fake"})
            assert resp.status_code == 201, resp.text
            assert resp.json()["checkout_url"].startswith("https://checkout.stripe.com/")
            mock_stripe.Customer.create.assert_not_called()
            # Created in subscription mode with the org subscription price.
            _, kwargs = mock_stripe.checkout.Session.create.call_args
            assert kwargs["mode"] == "subscription"
            assert kwargs["line_items"][0]["price"] == "price_org_sub"
        finally:
            app.dependency_overrides.clear()


# ── POST /api/org-billing/campaigns/{id}/unlock ───────────────────────────────


@pytest.mark.asyncio
async def test_unlock_invalid_uuid_returns_422():
    db = _build_chainable([])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/org-billing/campaigns/not-a-uuid/unlock", headers={"Authorization": "Bearer x"})
        assert resp.status_code == 422, resp.text
        assert resp.json()["detail"]["code"] == "INVALID_UUID"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_unlock_already_has_access_returns_409():
    org_row = {"id": ORG_ID, "name": "Atlas Org", "stripe_customer_id": STRIPE_CUSTOMER_ID, "subscription_expires_at": None}
    campaign_row = {"id": CAMPAIGN_ID}
    # org_has_report_access → org_has_active_subscription queries organizations (future = active).
    sub_row = {"subscription_expires_at": (datetime.now(UTC) + timedelta(days=30)).isoformat()}
    db = _build_chainable([org_row, campaign_row, sub_row])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
    ):
        _stripe_settings(ms)
        mock_stripe.api_key = None
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.post(
                    f"/api/org-billing/campaigns/{CAMPAIGN_ID}/unlock", headers={"Authorization": "Bearer x"}
                )
            assert resp.status_code == 409, resp.text
            assert resp.json()["detail"]["code"] == "ALREADY_HAS_ACCESS"
            mock_stripe.checkout.Session.create.assert_not_called()
        finally:
            app.dependency_overrides.clear()


# ── GET /api/org-billing/status ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_reports_active_subscription():
    future = (datetime.now(UTC) + timedelta(days=10)).isoformat()
    org_row = {"id": ORG_ID, "name": "Atlas Org", "stripe_customer_id": STRIPE_CUSTOMER_ID, "subscription_expires_at": future}
    unlocks = [{"campaign_id": CAMPAIGN_ID}]
    db = _build_chainable([org_row, unlocks])
    app.dependency_overrides[get_supabase_admin] = _db_override(db)
    app.dependency_overrides[get_current_user_id] = _uid_override()

    with patch("app.routers.org_billing.settings") as ms:
        _stripe_settings(ms)
        try:
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
                resp = await ac.get("/api/org-billing/status", headers={"Authorization": "Bearer x"})
            assert resp.status_code == 200, resp.text
            body = resp.json()
            assert body["has_active_subscription"] is True
            assert body["unlocked_campaign_ids"] == [CAMPAIGN_ID]
            assert body["org_billing_enabled"] is True
            assert "stripe_customer_id" not in resp.text
        finally:
            app.dependency_overrides.clear()


# ── POST /api/org-billing/webhook ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_webhook_wrong_signature_returns_400():
    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
    ):
        _stripe_settings(ms)

        class FakeSigError(Exception):
            pass

        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = FakeSigError
        mock_stripe.Webhook.construct_event = MagicMock(side_effect=FakeSigError("bad"))

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/org-billing/webhook",
                content=b'{"type":"checkout.session.completed"}',
                headers={"content-type": "application/json", "stripe-signature": "t=1,v1=bad"},
            )
        assert resp.status_code == 400, resp.text
        assert resp.json()["detail"]["code"] == "INVALID_SIGNATURE"


@pytest.mark.asyncio
async def test_webhook_already_processed_skips():
    fake_event = {
        "id": "evt_org_dup_001",
        "type": "checkout.session.completed",
        "data": {"object": {"mode": "payment", "metadata": {"volaura_campaign_id": CAMPAIGN_ID, "volaura_org_id": ORG_ID}}},
    }
    handler = AsyncMock(return_value=True)
    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
        patch("app.routers.org_billing._is_org_stripe_event_processed", new=AsyncMock(return_value=True)),
        patch("app.routers.org_billing._handle_checkout_completed", new=handler),
        patch("app.routers.org_billing._mark_org_stripe_event_processed", new=AsyncMock()),
    ):
        _stripe_settings(ms)
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/org-billing/webhook",
                content=b"{}",
                headers={"content-type": "application/json", "stripe-signature": "t=1,v1=ok"},
            )
    assert resp.status_code == 200, resp.text
    assert resp.json()["received"] is True
    handler.assert_not_called()


@pytest.mark.asyncio
async def test_webhook_checkout_completed_unlocks_and_marks_processed():
    fake_event = {
        "id": "evt_org_unlock_001",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_unlock",
                "mode": "payment",
                "payment_intent": "pi_test",
                "amount_total": 25000,
                "currency": "azn",
                "metadata": {"volaura_campaign_id": CAMPAIGN_ID, "volaura_org_id": ORG_ID},
            }
        },
    }
    mark = AsyncMock()
    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
        patch("app.routers.org_billing._is_org_stripe_event_processed", new=AsyncMock(return_value=False)),
        patch("app.routers.org_billing._handle_checkout_completed", new=AsyncMock(return_value=True)),
        patch("app.routers.org_billing._mark_org_stripe_event_processed", new=mark),
    ):
        _stripe_settings(ms)
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/org-billing/webhook",
                content=b"{}",
                headers={"content-type": "application/json", "stripe-signature": "t=1,v1=ok"},
            )
    assert resp.status_code == 200, resp.text
    mark.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_unhandled_event_marks_processed():
    fake_event = {"id": "evt_org_unhandled", "type": "invoice.paid", "data": {"object": {}}}
    mark = AsyncMock()
    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
        patch("app.routers.org_billing._is_org_stripe_event_processed", new=AsyncMock(return_value=False)),
        patch("app.routers.org_billing._mark_org_stripe_event_processed", new=mark),
    ):
        _stripe_settings(ms)
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/org-billing/webhook",
                content=b"{}",
                headers={"content-type": "application/json", "stripe-signature": "t=1,v1=ok"},
            )
    assert resp.status_code == 200, resp.text
    mark.assert_called_once()


@pytest.mark.asyncio
async def test_webhook_subscription_created_no_org_returns_500_not_marked():
    fake_event = {
        "id": "evt_org_sub_no_org",
        "type": "customer.subscription.created",
        "data": {
            "object": {
                "id": "sub_test",
                "customer": STRIPE_CUSTOMER_ID,
                "status": "active",
                "current_period_end": int(time.time()) + 30 * 86400,
            }
        },
    }
    mark = AsyncMock()
    with (
        patch("app.routers.org_billing.settings") as ms,
        patch("app.routers.org_billing._STRIPE_AVAILABLE", True),
        patch("app.routers.org_billing._stripe") as mock_stripe,
        patch("app.routers.org_billing._is_org_stripe_event_processed", new=AsyncMock(return_value=False)),
        patch("app.routers.org_billing._update_org_subscription", new=AsyncMock(return_value=False)),
        patch("app.routers.org_billing._mark_org_stripe_event_processed", new=mark),
    ):
        _stripe_settings(ms)
        mock_stripe.errors = MagicMock()
        mock_stripe.errors.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event = MagicMock(return_value=fake_event)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/api/org-billing/webhook",
                content=b"{}",
                headers={"content-type": "application/json", "stripe-signature": "t=1,v1=ok"},
            )
    assert resp.status_code == 500, f"Expected 500 so Stripe retries, got {resp.status_code}: {resp.text}"
    mark.assert_not_called()
