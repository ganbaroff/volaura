"""Regression tests for /api/telegram/webhook secret validation.

Covers the fix-closed + hmac.compare_digest fix (commit 355bb36, session 108).
Before the fix, a missing TELEGRAM_WEBHOOK_SECRET silently accepted every request
(CEO_CHAT_ID filter was the only gate); a plain != comparison was timing-unsafe.
These tests pin the behavior so the fix cannot regress.
"""

from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_supabase_admin
from app.main import app


@pytest.fixture(autouse=True)
def _mock_supabase_admin():
    app.dependency_overrides[get_supabase_admin] = lambda: MagicMock()
    yield
    app.dependency_overrides.pop(get_supabase_admin, None)


@pytest.mark.anyio
async def test_webhook_rejects_when_secret_not_configured(monkeypatch):
    """Empty TELEGRAM_WEBHOOK_SECRET -> 403 on every request.

    Regression: previous code fell through to the CEO_CHAT_ID filter, which still
    accepted unsigned updates if the chat_id matched. Now the endpoint refuses
    unconditionally when the secret env var is empty.
    """
    from app.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "test_token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "anything"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_webhook_rejects_wrong_secret(monkeypatch):
    """Configured secret + wrong header value -> 403.

    Sanity check that a forged header (same length, different value) is rejected.
    hmac.compare_digest is constant-time, so this path should still deny.
    """
    from app.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "test_token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "correct_secret_abc")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/telegram/webhook",
            json={"update_id": 1},
            headers={"X-Telegram-Bot-Api-Secret-Token": "wronger_secret_xyz"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_webhook_rejects_missing_header(monkeypatch):
    """Configured secret + no header -> 403. The empty-string compare must fail."""
    from app.config import settings

    monkeypatch.setattr(settings, "telegram_bot_token", "test_token")
    monkeypatch.setattr(settings, "telegram_webhook_secret", "correct_secret_abc")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/telegram/webhook", json={"update_id": 1})
    assert resp.status_code == 403
