"""HTTP endpoint tests for the verification router.

Covers:
- GET  /api/verify/{token}  — validate token, return professional info
- POST /api/verify/{token}  — submit rating, mark token used
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_supabase_admin
from app.main import app

VOLUNTEER_ID = str(uuid4())
VALID_TOKEN = "abc123validtoken"
FUTURE_EXPIRES = (datetime.now(UTC) + timedelta(days=3)).isoformat()
PAST_EXPIRES = (datetime.now(UTC) - timedelta(days=1)).isoformat()

PROFILE_ROW = {
    "display_name": "Aysel Huseynova",
    "username": "aysel_h",
    "avatar_url": "https://example.com/avatar.jpg",
}

VALID_TOKEN_ROW = {
    "id": str(uuid4()),
    "token_used": False,
    "token_expires_at": FUTURE_EXPIRES,
    "competency_id": "communication",
    "verifier_name": "Dr. Rashad",
    "verifier_org": "Tech Corp",
    "volunteer_id": VOLUNTEER_ID,
    "profiles": PROFILE_ROW,
}

USED_TOKEN_ROW = {**VALID_TOKEN_ROW, "token_used": True}
EXPIRED_TOKEN_ROW = {**VALID_TOKEN_ROW, "token_expires_at": PAST_EXPIRES}


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, side_effect=None) -> MagicMock:
    result = MagicMock()
    result.data = data
    result.count = None

    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "neq", "in_", "order", "limit", "update", "upsert", "insert", "single", "rpc"):
        getattr(chain, method).return_value = chain
    chain.maybe_single.return_value = chain
    chain.execute = execute
    return chain


def make_db(tables: dict | None = None) -> MagicMock:
    db = MagicMock()
    tables = tables or {}

    def dispatch(name: str) -> MagicMock:
        cfg = tables.get(name, {})
        return make_chain(**cfg)

    db.table.side_effect = dispatch

    rpc_chain = make_chain(data={})
    db.rpc.return_value = rpc_chain
    return db


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


# ── GET /api/verify/{token} ───────────────────────────────────────────────────


class TestGetVerificationInfo:
    @pytest.mark.asyncio
    async def test_valid_token_returns_professional_info(self):
        db = make_db({"expert_verifications": {"data": VALID_TOKEN_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/verify/{VALID_TOKEN}")
            assert r.status_code == 200
            body = r.json()
            assert body["professional_display_name"] == "Aysel Huseynova"
            assert body["professional_username"] == "aysel_h"
            assert body["verifier_name"] == "Dr. Rashad"
            assert body["verifier_org"] == "Tech Corp"
            assert body["competency_id"] == "communication"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_valid_token_includes_avatar_url(self):
        db = make_db({"expert_verifications": {"data": VALID_TOKEN_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/verify/{VALID_TOKEN}")
            assert r.status_code == 200
            assert r.json()["professional_avatar_url"] == "https://example.com/avatar.jpg"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_token_not_found_returns_404(self):
        db = make_db({"expert_verifications": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get("/api/verify/nonexistent-token")
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "TOKEN_INVALID"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_used_token_returns_409(self):
        db = make_db({"expert_verifications": {"data": USED_TOKEN_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/verify/{VALID_TOKEN}")
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "TOKEN_ALREADY_USED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_expired_token_returns_410(self):
        db = make_db({"expert_verifications": {"data": EXPIRED_TOKEN_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/verify/{VALID_TOKEN}")
            assert r.status_code == 410
            assert r.json()["detail"]["code"] == "TOKEN_EXPIRED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_no_profile_falls_back_to_professional_display_name(self):
        row = {**VALID_TOKEN_ROW, "profiles": None}
        db = make_db({"expert_verifications": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/verify/{VALID_TOKEN}")
            assert r.status_code == 200
            assert r.json()["professional_display_name"] == "Professional"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_no_verifier_org_is_nullable(self):
        row = {**VALID_TOKEN_ROW, "verifier_org": None}
        db = make_db({"expert_verifications": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/verify/{VALID_TOKEN}")
            assert r.status_code == 200
            assert r.json()["verifier_org"] is None
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)


# ── POST /api/verify/{token} ──────────────────────────────────────────────────


class TestSubmitVerification:
    @pytest.mark.asyncio
    async def test_valid_submission_returns_201(self):
        update_result = MagicMock()
        update_result.data = [{"id": "uv-1"}]
        make_chain(data=[{"id": "uv-1"}])

        # DB returns valid token on first call, update success on second
        call_count = 0
        orig_row = VALID_TOKEN_ROW

        async def execute_side_effect():
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.data = orig_row
            else:
                result.data = [{"id": "uv-1"}]
            return result

        chain = MagicMock()
        for method in ("select", "eq", "neq", "in_", "order", "limit", "update", "upsert", "insert", "single"):
            getattr(chain, method).return_value = chain
        chain.maybe_single.return_value = chain
        chain.execute = AsyncMock(side_effect=execute_side_effect)

        db = MagicMock()
        db.table.return_value = chain
        rpc_chain = make_chain(data={})
        db.rpc.return_value = rpc_chain

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(
                    f"/api/verify/{VALID_TOKEN}",
                    json={"rating": 4, "comment": "Great professional!"},
                )
            assert r.status_code == 201
            body = r.json()
            assert body["status"] == "verified"
            assert body["rating"] == 4
            assert body["competency_id"] == "communication"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_rating_boundary_1_accepted(self):
        call_count = 0

        async def execute_side_effect():
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            result.data = VALID_TOKEN_ROW if call_count == 1 else [{"id": "uv-2"}]
            return result

        chain = MagicMock()
        for method in ("select", "eq", "neq", "in_", "order", "limit", "update", "upsert", "insert", "single"):
            getattr(chain, method).return_value = chain
        chain.maybe_single.return_value = chain
        chain.execute = AsyncMock(side_effect=execute_side_effect)

        db = MagicMock()
        db.table.return_value = chain
        db.rpc.return_value = make_chain(data={})

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"rating": 1})
            assert r.status_code == 201
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_rating_below_1_rejected_422(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"rating": 0})
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_rating_above_5_rejected_422(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"rating": 6})
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_used_token_on_submit_returns_409(self):
        db = make_db({"expert_verifications": {"data": USED_TOKEN_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"rating": 3})
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "TOKEN_ALREADY_USED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_expired_token_on_submit_returns_410(self):
        db = make_db({"expert_verifications": {"data": EXPIRED_TOKEN_ROW}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"rating": 3})
            assert r.status_code == 410
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_invalid_token_on_submit_returns_404(self):
        db = make_db({"expert_verifications": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post("/api/verify/bad-token", json={"rating": 3})
            assert r.status_code == 404
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_missing_rating_field_returns_422(self):
        db = make_db()
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"comment": "no rating"})
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_concurrent_submission_returns_409(self):
        """Concurrent POST with update returning empty data triggers 409."""
        call_count = 0

        async def execute_side_effect():
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            # First call: valid token check
            # Second call: update returns empty (race condition — another request won)
            result.data = VALID_TOKEN_ROW if call_count == 1 else []
            return result

        chain = MagicMock()
        for method in ("select", "eq", "neq", "in_", "order", "limit", "update", "upsert", "insert", "single"):
            getattr(chain, method).return_value = chain
        chain.maybe_single.return_value = chain
        chain.execute = AsyncMock(side_effect=execute_side_effect)

        db = MagicMock()
        db.table.return_value = chain
        db.rpc.return_value = make_chain(data={})

        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.post(f"/api/verify/{VALID_TOKEN}", json={"rating": 4})
            assert r.status_code == 409
            assert r.json()["detail"]["code"] == "TOKEN_ALREADY_USED"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
