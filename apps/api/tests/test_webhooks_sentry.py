"""Tests for /api/webhooks/sentry — recurring-symptoms watchdog receiver.

Covers:
    1. Fail-closed when SENTRY_WEBHOOK_SECRET is empty (mirrors INC-008).
    2. Signature mismatch -> 403.
    3. Fingerprint dedup: same fingerprint twice bumps occurrences, never
       creates two rows.
    4. GitHub issue create-or-update idempotency: second recurrence reuses
       existing gh_issue_url, does not create a second issue.
    5. Non-regression payloads are accepted (202) but returned as ignored.
    6. Bad JSON body -> 400.
    7. x-sentry-signature (v1 alias) is accepted alongside sentry-hook-signature.
    8. Missing signature header -> 403.
    9. Fingerprint extraction: issue.id path vs title+culprit fallback.
   10. Source product mapping from project slug.
   11. _is_regression_event helper: action=unresolved, action=reopened, timesSeen >= threshold.
   12. Multiple distinct fingerprints create separate rows.

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


@pytest.mark.anyio
async def test_non_regression_payload_ignored(monkeypatch, fake_store):
    """action=created without isRegression flag -> 202 with status=ignored."""
    from app.config import settings

    secret = "secret_xyz"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)

    payload = {
        "action": "created",
        "data": {
            "issue": {
                "id": "I-999",
                "title": "Normal event",
                "culprit": "some.module",
                "isRegression": False,
                "project": {"slug": "volaura-api"},
            }
        },
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(body, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "ignored"
    assert data["reason"] == "not_regression"
    # No rows inserted for ignored events.
    assert len(fake_store) == 0


@pytest.mark.anyio
async def test_bad_json_returns_400(monkeypatch, fake_store):
    """Malformed JSON body -> 400 BAD_PAYLOAD."""
    from app.config import settings

    secret = "secret_xyz"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)

    body = b"not valid json {{{"
    sig = _sign(body, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )

    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "BAD_PAYLOAD"


@pytest.mark.anyio
async def test_x_sentry_signature_v1_alias_accepted(monkeypatch, fake_store):
    """x-sentry-signature (v1 header name) is accepted in addition to sentry-hook-signature."""
    from app.config import settings

    secret = "secret_v1_alias"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)
    monkeypatch.setattr(settings, "github_pat_actions", "")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_ceo_chat_id", "")

    body = json.dumps(_regression_payload("I-v1")).encode("utf-8")
    sig = _sign(body, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"x-sentry-signature": sig, "content-type": "application/json"},
        )

    assert resp.status_code == 202
    assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_missing_signature_header_rejected(monkeypatch, fake_store):
    """No signature header at all -> 403."""
    from app.config import settings

    monkeypatch.setattr(settings, "sentry_webhook_secret", "some_secret")

    body = json.dumps(_regression_payload()).encode("utf-8")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"content-type": "application/json"},
        )

    assert resp.status_code == 403


@pytest.mark.anyio
async def test_action_unresolved_treated_as_regression(monkeypatch, fake_store):
    """action=unresolved is a regression event and creates a row."""
    from app.config import settings

    secret = "secret_unresolved"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)
    monkeypatch.setattr(settings, "github_pat_actions", "")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_ceo_chat_id", "")

    payload = {
        "action": "unresolved",
        "data": {
            "issue": {
                "id": "I-unresolved",
                "title": "Unresolved error",
                "culprit": "some.path",
                "project": {"slug": "mindshift-app"},
            }
        },
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(body, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "ok"
    assert len(fake_store) == 1
    assert fake_store[0]["source_product"] == "mindshift"


@pytest.mark.anyio
async def test_action_reopened_treated_as_regression(monkeypatch, fake_store):
    """action=reopened is a regression event."""
    from app.config import settings

    secret = "secret_reopened"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)
    monkeypatch.setattr(settings, "github_pat_actions", "")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_ceo_chat_id", "")

    payload = {
        "action": "reopened",
        "data": {
            "issue": {
                "id": "I-reopened",
                "title": "Reopened bug",
                "project": {"slug": "brandedby-frontend"},
            }
        },
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(body, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )

    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "ok"
    assert fake_store[0]["source_product"] == "brandedby"


@pytest.mark.anyio
async def test_times_seen_above_threshold_triggers_regression(monkeypatch, fake_store):
    """timesSeen >= RCA_THRESHOLD (3) on issue = regression even without isRegression flag."""
    from app.config import settings

    secret = "secret_times"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)
    monkeypatch.setattr(settings, "github_pat_actions", "")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_ceo_chat_id", "")

    payload = {
        "action": "created",
        "data": {
            "issue": {
                "id": "I-times",
                "title": "Repeated error",
                "timesSeen": 5,
                "project": {"slug": "zeus-orchestrator"},
            }
        },
    }
    body = json.dumps(payload).encode("utf-8")
    sig = _sign(body, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/webhooks/sentry",
            content=body,
            headers={"sentry-hook-signature": sig, "content-type": "application/json"},
        )

    assert resp.status_code == 202
    assert resp.json()["status"] == "ok"
    assert fake_store[0]["source_product"] == "zeus"


@pytest.mark.anyio
async def test_distinct_fingerprints_create_separate_rows(monkeypatch, fake_store):
    """Two different issues create two separate rows in the store."""
    from app.config import settings

    secret = "secret_distinct"
    monkeypatch.setattr(settings, "sentry_webhook_secret", secret)
    monkeypatch.setattr(settings, "github_pat_actions", "")
    monkeypatch.setattr(settings, "telegram_bot_token", "")
    monkeypatch.setattr(settings, "telegram_ceo_chat_id", "")

    body1 = json.dumps(_regression_payload("I-aaa", "Error A")).encode("utf-8")
    body2 = json.dumps(_regression_payload("I-bbb", "Error B")).encode("utf-8")
    sig1 = _sign(body1, secret)
    sig2 = _sign(body2, secret)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r1 = await ac.post(
            "/api/webhooks/sentry",
            content=body1,
            headers={"sentry-hook-signature": sig1, "content-type": "application/json"},
        )
        r2 = await ac.post(
            "/api/webhooks/sentry",
            content=body2,
            headers={"sentry-hook-signature": sig2, "content-type": "application/json"},
        )

    assert r1.status_code == 202
    assert r2.status_code == 202
    assert len(fake_store) == 2
    fingerprints = {row["fingerprint_hash"] for row in fake_store}
    assert fingerprints == {"sentry:I-aaa", "sentry:I-bbb"}


# ── Unit tests for helper functions ──────────────────────────────────────────


def test_extract_fingerprint_uses_issue_id():
    """When issue.id is present, fingerprint is 'sentry:<id>'."""
    from app.routers.webhooks_sentry import _extract_fingerprint

    payload = {"data": {"issue": {"id": "ISSUE-42", "title": "some error"}}}
    assert _extract_fingerprint(payload) == "sentry:ISSUE-42"


def test_extract_fingerprint_falls_back_to_title_hash():
    """When no issue.id, fingerprint is derived from title+culprit hash."""
    from app.routers.webhooks_sentry import _extract_fingerprint

    payload = {
        "data": {
            "issue": {
                "title": "TypeError: cannot read property",
                "culprit": "app/module.py",
            }
        }
    }
    fp = _extract_fingerprint(payload)
    assert fp.startswith("fp:")
    assert len(fp) == 35  # "fp:" + 32 hex chars


def test_extract_source_product_maps_slug():
    """Project slug containing product name maps to that product."""
    from app.routers.webhooks_sentry import _extract_source_product

    cases = [
        ({"data": {"issue": {"project": {"slug": "mindshift-backend"}}}}, "mindshift"),
        ({"data": {"issue": {"project": {"slug": "brandedby-frontend"}}}}, "brandedby"),
        ({"data": {"issue": {"project": {"slug": "zeus-agents"}}}}, "zeus"),
        ({"data": {"issue": {"project": {"slug": "volaura-api"}}}}, "volaura"),
        ({"data": {"issue": {"project": {"slug": "some-unknown-service"}}}}, "unknown"),
    ]
    for payload, expected in cases:
        assert _extract_source_product(payload) == expected, f"Failed for slug in {payload}"


def test_is_regression_event_actions():
    """Action-based regression detection covers resolved/unresolved/reopened."""
    from app.routers.webhooks_sentry import _is_regression_event

    assert _is_regression_event({"action": "unresolved"}) is True
    assert _is_regression_event({"action": "reopened"}) is True
    assert _is_regression_event({"action": "resolved"}) is True
    assert _is_regression_event({"action": "assigned"}) is False
    assert _is_regression_event({"action": "ignored"}) is False


def test_is_regression_event_times_seen_threshold():
    """timesSeen >= 3 is treated as regression; < 3 is not."""
    from app.routers.webhooks_sentry import _is_regression_event

    above = {"action": "created", "data": {"issue": {"timesSeen": 3}}}
    below = {"action": "created", "data": {"issue": {"timesSeen": 2}}}
    assert _is_regression_event(above) is True
    assert _is_regression_event(below) is False


def test_verify_sentry_signature_correct(monkeypatch):
    """Correct HMAC-SHA256 signature passes verification."""
    from app.config import settings
    from app.routers.webhooks_sentry import _verify_sentry_signature

    monkeypatch.setattr(settings, "sentry_webhook_secret", "my_test_secret")
    body = b"hello world"
    sig = _sign(body, "my_test_secret")
    assert _verify_sentry_signature(body, sig) is True


def test_verify_sentry_signature_wrong_fails(monkeypatch):
    """Wrong signature returns False."""
    from app.config import settings
    from app.routers.webhooks_sentry import _verify_sentry_signature

    monkeypatch.setattr(settings, "sentry_webhook_secret", "my_test_secret")
    assert _verify_sentry_signature(b"hello", "deadbeef") is False


def test_verify_sentry_signature_empty_secret_fails(monkeypatch):
    """Empty SENTRY_WEBHOOK_SECRET always returns False."""
    from app.config import settings
    from app.routers.webhooks_sentry import _verify_sentry_signature

    monkeypatch.setattr(settings, "sentry_webhook_secret", "")
    body = b"hello"
    sig = _sign(body, "any_secret")
    assert _verify_sentry_signature(body, sig) is False
