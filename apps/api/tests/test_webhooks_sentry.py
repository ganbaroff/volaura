"""Tests for /api/webhooks/sentry — recurring-symptoms watchdog receiver.

Covers:
    1. Fail-closed when SENTRY_WEBHOOK_SECRET is empty (mirrors INC-008).
    2. Signature mismatch -> 403.
    3. Fingerprint dedup: same fingerprint twice bumps occurrences, never
       creates two rows.
    4. GitHub issue create-or-update idempotency: second recurrence reuses
       existing gh_issue_url, does not create a second issue.

No real Supabase / GitHub / Telegram calls — all three are monkeypatched to
in-memory fakes so the suite runs offline.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# -------------------------------------------------------------------------
# In-memory fakes
# -------------------------------------------------------------------------


class _FakeQuery:
    def __init__(self, store: list[dict[str, Any]], mode: str = "select"):
        self._store = store
        self._mode = mode
        self._filters: dict[str, Any] = {}
        self._payload: dict[str, Any] | None = None
        self._limit: int | None = None

    def select(self, *_a, **_kw):
        self._mode = "select"
        return self

    def insert(self, payload):
        self._mode = "insert"
        self._payload = payload
        return self

    def update(self, payload):
        self._mode = "update"
        self._payload = payload
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def limit(self, n):
        self._limit = n
        return self

    async def execute(self):
        if self._mode == "select":
            rows = [r for r in self._store if all(r.get(k) == v for k, v in self._filters.items())]
            if self._limit:
                rows = rows[: self._limit]
            return type("Resp", (), {"data": rows})()
        if self._mode == "insert":
            new_row = {"id": f"row-{len(self._store) + 1}", **(self._payload or {})}
            self._store.append(new_row)
            return type("Resp", (), {"data": [new_row]})()
        if self._mode == "update":
            updated = []
            for r in self._store:
                if all(r.get(k) == v for k, v in self._filters.items()):
                    r.update(self._payload or {})
                    updated.append(r)
            return type("Resp", (), {"data": updated})()
        return type("Resp", (), {"data": []})()


class _FakeDB:
    def __init__(self, store: list[dict[str, Any]]):
        self._store = store

    def table(self, _name: str):
        return _FakeQuery(self._store)


@pytest.fixture
def fake_store(monkeypatch):
    """Install an in-memory fake for supabase.acreate_client + outbound httpx."""
    store: list[dict[str, Any]] = []

    async def _fake_acreate_client(_url, _key):
        return _FakeDB(store)

    # Patch the symbol where webhooks_sentry looks it up (imported lazily inside
    # helpers, so we patch at the source module).
    import supabase

    monkeypatch.setattr(supabase, "acreate_client", _fake_acreate_client)

    # Mute outbound GitHub + Telegram — we only care that they don't 500 the
    # webhook. httpx.AsyncClient.post returns 201 with fake body.
    import httpx as _httpx

    class _FakeResp:
        def __init__(self, status_code=201, data=None):
            self.status_code = status_code
            self._data = data or {"html_url": "https://github.com/ganbaroff/volaura/issues/999"}
            self.text = json.dumps(self._data)

        def json(self):
            return self._data

    class _FakeAsyncClient:
        def __init__(self, *a, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, _url, **_kw):
            return _FakeResp()

    monkeypatch.setattr(_httpx, "AsyncClient", _FakeAsyncClient)
    return store


def _sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def _regression_payload(issue_id: str = "I-123", title: str = "TypeError in foo.py") -> dict:
    return {
        "action": "created",
        "data": {
            "issue": {
                "id": issue_id,
                "title": title,
                "culprit": "apps/api/app/routers/telegram_webhook.py in foo",
                "isRegression": True,
                "project": {"slug": "volaura-api"},
            }
        },
    }


# -------------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------------


@pytest.mark.anyio
async def test_webhook_rejects_when_secret_not_configured(monkeypatch, fake_store):
    """Empty SENTRY_WEBHOOK_SECRET -> 403 on every request (INC-008 pattern)."""
    from app.config import settings

    monkeypatch.setattr(settings, "sentry_webhook_secret", "")

    body = json.dumps(_regression_payload()).encode("utf-8")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": "anything", "content-type": "application/json"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_webhook_rejects_bad_signature(monkeypatch, fake_store):
    """Configured secret + forged signature -> 403."""
    from app.config import settings

    monkeypatch.setattr(settings, "sentry_webhook_secret", "correct_secret_abc")

    body = json.dumps(_regression_payload()).encode("utf-8")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": "dead" + "beef" * 15, "content-type": "application/json"},
        )
    assert resp.status_code == 403


@pytest.mark.anyio
async def test_webhook_fingerprint_dedup_and_gh_idempotency(monkeypatch, fake_store):
    """Same fingerprint posted twice -> one row, occurrences=2 on second call.

    Also asserts GitHub issue URL is stored once and reused (no double-create).
    """
    from app.config import settings

    secret = "correct_secret_abc"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)
    monkeypatch.setattr(settings, "github_pat_actions", "ghp_fake_token")
    monkeypatch.setattr(settings, "github_repo", "ganbaroff/volaura")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_ceo_chat_id", "")

    body = json.dumps(_regression_payload()).encode("utf-8")
    sig = _sign(body, secret)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # First call: 1 row, occurrences=1, under RCA threshold.
        r1 = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )
        # Second call: dedup bumps occurrences to 2.
        r2 = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )
        # Third call: crosses RCA_THRESHOLD, triggers GH issue create.
        r3 = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )

    assert r1.status_code == 202
    assert r2.status_code == 202
    assert r3.status_code == 202
    # Dedup: one row only.
    assert len(fake_store) == 1
    row = fake_store[0]
    assert row["occurrences"] == 3
    assert row["needs_rca_label_set"] is True
    assert row["source_product"] == "volaura"
