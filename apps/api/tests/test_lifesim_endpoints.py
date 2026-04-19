"""HTTP-level endpoint tests for app/routers/lifesim.py.

Tests every endpoint with:
  - Happy path (expected 200/201 shape)
  - 401 when auth dep missing
  - Edge cases / error branches

Supabase is mocked entirely via dependency_overrides — no real DB.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

# ── Constants ──────────────────────────────────────────────────────────────────

USER_ID = str(uuid4())
EVENT_ID = str(uuid4())


# ── Helpers ────────────────────────────────────────────────────────────────────


class _R:
    """Minimal Supabase result stand-in."""

    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


def _chain(*execute_returns) -> MagicMock:
    """Return a Supabase query-builder chain mock.

    Every builder method returns the same chain; execute() returns the
    provided values in sequence (or always the single value).
    """
    c = MagicMock()
    for m in (
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "neq",
        "in_",
        "not_",
        "is_",
        "order",
        "limit",
        "range",
        "single",
        "maybe_single",
        "upsert",
        "filter",
    ):
        getattr(c, m).return_value = c

    if len(execute_returns) == 1:
        c.execute = AsyncMock(return_value=execute_returns[0])
    else:
        c.execute = AsyncMock(side_effect=list(execute_returns))
    return c


def _db(*execute_returns) -> MagicMock:
    """Full DB mock wired to a shared chain."""
    db = MagicMock()
    c = _chain(*execute_returns)
    for m in (
        "table",
        "select",
        "insert",
        "update",
        "delete",
        "eq",
        "neq",
        "in_",
        "not_",
        "is_",
        "order",
        "limit",
        "range",
        "single",
        "maybe_single",
        "upsert",
        "filter",
    ):
        getattr(db, m).return_value = c
    db.execute = c.execute
    return db


def _make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── Feed rows ──────────────────────────────────────────────────────────────────


def _feed_row(**kw) -> dict:
    base = {
        "id": str(uuid4()),
        "event_type": "lifesim_choice",
        "payload": {"event_id": EVENT_ID, "choice_index": 0},
        "created_at": "2026-04-19T10:00:00+00:00",
    }
    return {**base, **kw}


def _lifesim_event_row(**kw) -> dict:
    base = {
        "id": EVENT_ID,
        "is_active": True,
        "choices": [
            {"text": "Study hard", "consequences": {"intelligence": 5.0}},
            {"text": "Play games", "consequences": {"happiness": 3.0}},
        ],
    }
    return {**base, **kw}


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/lifesim/feed
# ══════════════════════════════════════════════════════════════════════════════


class TestLifesimFeed:
    @pytest.mark.asyncio
    async def test_happy_path_returns_feed(self):
        rows = [_feed_row(), _feed_row(event_type="lifesim_crystal_spent")]
        db = _db(_R(data=rows))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/feed")
            assert resp.status_code == 200
            # FeedResponse shape: {"data": [...]}
            body = resp.json()
            assert "data" in body
            assert len(body["data"]) == 2
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_empty_feed_returns_empty_list(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/feed")
            assert resp.status_code == 200
            assert resp.json()["data"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_none_data_returns_empty_list(self):
        db = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/feed")
            assert resp.status_code == 200
            assert resp.json()["data"] == []
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        """No dependency override → real get_current_user_id rejects missing token."""
        async with _make_client() as c:
            resp = await c.get("/api/lifesim/feed")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_limit_query_param_accepted(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/feed?limit=10")
            assert resp.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_limit_too_large_returns_422(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/feed?limit=9999")
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_feed_item_shape(self):
        row = _feed_row()
        db = _db(_R(data=[row]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/feed")
            item = resp.json()["data"][0]
            assert "id" in item
            assert "event_type" in item
            assert "payload" in item
            assert "created_at" in item
        finally:
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# GET /api/lifesim/next-choice
# ══════════════════════════════════════════════════════════════════════════════


class TestLifesimNextChoice:
    @pytest.mark.asyncio
    async def test_happy_path_returns_event(self):
        pool_event = {
            "id": EVENT_ID,
            "min_age": 6,
            "max_age": 100,
            "choices": [{"text": "Study", "consequences": {}}],
            "required_stats": {},
            "category": "education",
            "is_active": True,
        }
        db = _db(_R(data=[pool_event]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        # Also patch the service functions so we don't need a real pool schema
        import app.routers.lifesim as ls_router

        orig_pool = ls_router.query_event_pool
        orig_filter = ls_router.filter_pool_for_user
        ls_router.query_event_pool = AsyncMock(return_value=[pool_event])
        ls_router.filter_pool_for_user = MagicMock(return_value=[pool_event])
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/next-choice?age=18")
            assert resp.status_code == 200
            body = resp.json()
            assert "event" in body
            assert "pool_size" in body
            assert body["pool_size"] >= 1
        finally:
            ls_router.query_event_pool = orig_pool
            ls_router.filter_pool_for_user = orig_filter
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_empty_pool_returns_none_event(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        import app.routers.lifesim as ls_router

        orig_pool = ls_router.query_event_pool
        orig_filter = ls_router.filter_pool_for_user
        ls_router.query_event_pool = AsyncMock(return_value=[])
        ls_router.filter_pool_for_user = MagicMock(return_value=[])
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/next-choice?age=25")
            assert resp.status_code == 200
            body = resp.json()
            assert body["event"] is None
            assert body["pool_size"] == 0
        finally:
            ls_router.query_event_pool = orig_pool
            ls_router.filter_pool_for_user = orig_filter
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.get("/api/lifesim/next-choice?age=18")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_age_below_min_returns_422(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/next-choice?age=5")
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_age_required(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/next-choice")
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_category_filter_accepted(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        import app.routers.lifesim as ls_router

        orig_pool = ls_router.query_event_pool
        orig_filter = ls_router.filter_pool_for_user
        ls_router.query_event_pool = AsyncMock(return_value=[])
        ls_router.filter_pool_for_user = MagicMock(return_value=[])
        try:
            async with _make_client() as c:
                resp = await c.get("/api/lifesim/next-choice?age=20&category=education")
            assert resp.status_code == 200
        finally:
            ls_router.query_event_pool = orig_pool
            ls_router.filter_pool_for_user = orig_filter
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/lifesim/choice
# ══════════════════════════════════════════════════════════════════════════════


class TestLifesimChoice:
    def _valid_payload(self) -> dict:
        return {
            "event_id": EVENT_ID,
            "choice_index": 0,
            "stats_before": {"intelligence": 50.0, "social": 50.0},
        }

    @pytest.mark.asyncio
    async def test_happy_path_returns_201(self):
        event_row = _lifesim_event_row()
        db = _db(_R(data=event_row))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        import app.routers.lifesim as ls_router

        orig_emit = ls_router.emit_lifesim_choice_event
        ls_router.emit_lifesim_choice_event = AsyncMock(return_value=None)
        orig_apply = ls_router.apply_consequences_to_stats
        ls_router.apply_consequences_to_stats = MagicMock(
            return_value={"intelligence": 55.0, "social": 50.0}
        )
        try:
            async with _make_client() as c:
                resp = await c.post("/api/lifesim/choice", json=self._valid_payload())
            assert resp.status_code == 201
            body = resp.json()
            assert body["event_id"] == EVENT_ID
            assert body["choice_index"] == 0
            assert "consequences" in body
            assert "stats_after" in body
        finally:
            ls_router.emit_lifesim_choice_event = orig_emit
            ls_router.apply_consequences_to_stats = orig_apply
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post("/api/lifesim/choice", json=self._valid_payload())
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_when_event_not_found(self):
        db = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post("/api/lifesim/choice", json=self._valid_payload())
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_404_when_event_inactive(self):
        event_row = _lifesim_event_row(is_active=False)
        db = _db(_R(data=event_row))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post("/api/lifesim/choice", json=self._valid_payload())
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "EVENT_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_when_choice_index_out_of_range(self):
        event_row = _lifesim_event_row()  # only 2 choices (index 0 and 1)
        db = _db(_R(data=event_row))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            payload = {**self._valid_payload(), "choice_index": 5}
            async with _make_client() as c:
                resp = await c.post("/api/lifesim/choice", json=payload)
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "CHOICE_OUT_OF_RANGE"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_when_event_id_empty(self):
        db = _db(_R(data=None))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    "/api/lifesim/choice",
                    json={**self._valid_payload(), "event_id": ""},
                )
            assert resp.status_code == 422
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_response_shape(self):
        event_row = _lifesim_event_row()
        db = _db(_R(data=event_row))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        import app.routers.lifesim as ls_router

        orig_emit = ls_router.emit_lifesim_choice_event
        orig_apply = ls_router.apply_consequences_to_stats
        ls_router.emit_lifesim_choice_event = AsyncMock(return_value=None)
        ls_router.apply_consequences_to_stats = MagicMock(return_value={"intelligence": 55.0})
        try:
            async with _make_client() as c:
                resp = await c.post("/api/lifesim/choice", json=self._valid_payload())
            data = resp.json()
            assert set(data.keys()) >= {"event_id", "choice_index", "consequences", "stats_after"}
        finally:
            ls_router.emit_lifesim_choice_event = orig_emit
            ls_router.apply_consequences_to_stats = orig_apply
            app.dependency_overrides.clear()


# ══════════════════════════════════════════════════════════════════════════════
# POST /api/lifesim/purchase
# ══════════════════════════════════════════════════════════════════════════════


class TestLifesimPurchase:
    def _valid_payload(self, crystals: int = 200) -> dict:
        return {"shop_item": "social_event_ticket", "current_crystals": crystals}

    @pytest.mark.asyncio
    async def test_happy_path_returns_201(self):
        db = _db(
            _R(data=[{"id": "evt-id"}]),  # crystal_spent insert
            _R(data=[{"id": "lifesim-evt-id"}]),  # lifesim surface event insert
        )
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        import app.routers.lifesim as ls_router

        orig_emit = ls_router.emit_lifesim_crystal_spent_event
        ls_router.emit_lifesim_crystal_spent_event = AsyncMock(return_value=None)
        try:
            async with _make_client() as c:
                resp = await c.post("/api/lifesim/purchase", json=self._valid_payload())
            assert resp.status_code == 201
            body = resp.json()
            assert body["shop_item"] == "social_event_ticket"
            assert body["cost"] == 30
            assert body["remaining_crystals"] == 170
            assert "stat_boost" in body
        finally:
            ls_router.emit_lifesim_crystal_spent_event = orig_emit
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_401_when_no_auth(self):
        async with _make_client() as c:
            resp = await c.post("/api/lifesim/purchase", json=self._valid_payload())
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_404_unknown_shop_item(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as c:
                resp = await c.post(
                    "/api/lifesim/purchase",
                    json={"shop_item": "unknown_item", "current_crystals": 500},
                )
            assert resp.status_code == 404
            assert resp.json()["detail"]["code"] == "SHOP_ITEM_NOT_FOUND"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_422_insufficient_crystals(self):
        db = _db(_R(data=[]))
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            # social_event_ticket costs 30; give only 10
            async with _make_client() as c:
                resp = await c.post(
                    "/api/lifesim/purchase",
                    json=self._valid_payload(crystals=10),
                )
            assert resp.status_code == 422
            assert resp.json()["detail"]["code"] == "INSUFFICIENT_CRYSTALS"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_500_when_db_insert_raises(self):
        db = MagicMock()
        c = MagicMock()
        for m in ("table", "select", "insert", "eq", "order", "limit"):
            getattr(c, m).return_value = c
            getattr(db, m).return_value = c
        c.execute = AsyncMock(side_effect=Exception("DB down"))
        db.execute = c.execute
        app.dependency_overrides[get_supabase_admin] = lambda: db
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        try:
            async with _make_client() as cli:
                resp = await cli.post("/api/lifesim/purchase", json=self._valid_payload())
            assert resp.status_code == 500
            assert resp.json()["detail"]["code"] == "SPEND_FAILED"
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_all_catalogue_items_have_known_cost(self):
        """Each item in the catalogue can be queried without 404."""
        import app.routers.lifesim as ls_router

        items = [
            ("premium_training_course", 50),
            ("social_event_ticket", 30),
            ("health_insurance", 100),
            ("career_coach", 75),
        ]
        for item_name, cost in items:
            mock_db = _db(
                _R(data=[{"id": "evt"}]),
                _R(data=[{"id": "evt2"}]),
            )
            app.dependency_overrides[get_supabase_admin] = lambda _d=mock_db: _d
            app.dependency_overrides[get_current_user_id] = lambda: USER_ID
            orig_emit = ls_router.emit_lifesim_crystal_spent_event
            ls_router.emit_lifesim_crystal_spent_event = AsyncMock(return_value=None)
            try:
                async with _make_client() as c:
                    resp = await c.post(
                        "/api/lifesim/purchase",
                        json={"shop_item": item_name, "current_crystals": 500},
                    )
                assert resp.status_code == 201, f"item {item_name} returned {resp.status_code}"
                assert resp.json()["cost"] == cost
            finally:
                ls_router.emit_lifesim_crystal_spent_event = orig_emit
                app.dependency_overrides.clear()
