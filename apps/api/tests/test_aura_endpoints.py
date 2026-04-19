"""HTTP endpoint tests for the AURA router.

Covers:
- GET /api/aura/me              — own AURA score
- GET /api/aura/me/explanation   — detailed evaluation logs
- GET /api/aura/{professional_id} — public AURA lookup
- GET /api/aura/me/visibility    — visibility setting
- PATCH /api/aura/me/visibility  — update visibility
- POST /api/aura/me/sharing      — grant/revoke sharing
- GET /api/aura/me/reflection    — Atlas personal reflection
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app

USER_ID = str(uuid4())
OTHER_ID = str(uuid4())
ORG_ID = str(uuid4())
AUTH_HEADERS = {"Authorization": "Bearer test-token-aura"}


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


def make_chain(data=None, side_effect=None) -> MagicMock:
    result = MagicMock()
    result.data = data

    if side_effect:
        execute = AsyncMock(side_effect=side_effect)
    else:
        execute = AsyncMock(return_value=result)

    chain = MagicMock()
    for method in ("select", "eq", "order", "limit", "update", "upsert"):
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
    return db


def user_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def admin_dep(db: MagicMock):
    async def _override():
        yield db

    return _override


def user_id_dep(uid: str = USER_ID):
    async def _override():
        return uid

    return _override


AURA_ROW = {
    "volunteer_id": USER_ID,
    "total_score": 78.5,
    "badge_tier": "gold",
    "elite_status": False,
    "competency_scores": {"communication": 85, "leadership": 72},
    "visibility": "public",
    "reliability_score": 90.0,
    "reliability_status": "excellent",
    "events_attended": 5,
    "events_no_show": 0,
    "percentile_rank": 82,
    "aura_history": [{"date": "2026-04-10", "score": 75}],
    "last_updated": "2026-04-15T10:00:00Z",
}


# ── GET /api/aura/me ─────────────────────────────────────────────────────────


class TestGetMyAura:
    @pytest.mark.asyncio
    async def test_returns_200_with_score(self):
        db = make_db({"aura_scores": {"data": AURA_ROW}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["total_score"] == 78.5
            assert body["badge_tier"] == "gold"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_404_when_no_aura(self):
        db = make_db({"aura_scores": {"data": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "AURA_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_requires_auth(self):
        async with make_client() as client:
            r = await client.get("/api/aura/me")
        assert r.status_code == 401


# ── GET /api/aura/me/explanation ──────────────────────────────────────────────


class TestGetAuraExplanation:
    @pytest.mark.asyncio
    async def test_returns_explanations(self):
        session_data = [
            {
                "competency_id": "communication",
                "role_level": "professional",
                "completed_at": "2026-04-15T10:00:00Z",
                "answers": {
                    "items": [
                        {
                            "question_id": "q1",
                            "evaluation_log": {
                                "concept_scores": {"clarity": 4.5},
                                "model_used": "gemini-2.5-flash",
                                "methodology": "BARS",
                            },
                        }
                    ]
                },
            }
        ]
        db = make_db({"assessment_sessions": {"data": session_data}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/explanation", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["explanation_count"] == 1
            assert body["explanations"][0]["competency_id"] == "communication"
            eval_item = body["explanations"][0]["evaluations"][0]
            assert eval_item["evaluation_confidence"] == "high"
            assert "model_used" not in eval_item
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_404_no_completed_sessions(self):
        db = make_db({"assessment_sessions": {"data": []}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/explanation", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "NO_ASSESSMENTS"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_degraded_answers_counted(self):
        session_data = [
            {
                "competency_id": "leadership",
                "role_level": "professional",
                "completed_at": "2026-04-15T10:00:00Z",
                "answers": {
                    "items": [
                        {
                            "question_id": "q1",
                            "evaluation_log": {
                                "concept_scores": {"vision": 3.0},
                                "model_used": "keyword_fallback",
                                "methodology": "BARS",
                                "evaluation_mode": "degraded",
                            },
                        }
                    ]
                },
            }
        ]
        db = make_db({"assessment_sessions": {"data": session_data}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/explanation", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["has_pending_evaluations"] is True
            assert body["pending_reeval_count"] == 1
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_model_names_never_exposed(self):
        session_data = [
            {
                "competency_id": "communication",
                "role_level": "professional",
                "completed_at": "2026-04-15T10:00:00Z",
                "answers": {
                    "items": [
                        {
                            "question_id": "q1",
                            "evaluation_log": {
                                "concept_scores": {"clarity": 4.0},
                                "model_used": "gpt-4o-mini",
                                "methodology": "BARS",
                            },
                        }
                    ]
                },
            }
        ]
        db = make_db({"assessment_sessions": {"data": session_data}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/explanation", headers=AUTH_HEADERS)
            body = r.json()
            response_text = str(body)
            assert "gpt-4o-mini" not in response_text
            assert "gemini" not in response_text.lower()
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── GET /api/aura/{professional_id} ─────────���───────────────────────────��────


class TestGetAuraById:
    @pytest.mark.asyncio
    async def test_public_profile_returns_score(self):
        row = {**AURA_ROW, "volunteer_id": OTHER_ID, "visibility": "public"}
        db = make_db({"aura_scores": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/aura/{OTHER_ID}", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["total_score"] == 78.5
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_hidden_profile_returns_404(self):
        row = {**AURA_ROW, "volunteer_id": OTHER_ID, "visibility": "hidden"}
        db = make_db({"aura_scores": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/aura/{OTHER_ID}", headers=AUTH_HEADERS)
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "AURA_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_badge_only_strips_private_fields(self):
        row = {**AURA_ROW, "volunteer_id": OTHER_ID, "visibility": "badge_only"}
        db = make_db({"aura_scores": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/aura/{OTHER_ID}", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["total_score"] == 78.5
            assert body["competency_scores"] == {}
            assert body["aura_history"] == []
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_nonexistent_returns_404(self):
        db = make_db({"aura_scores": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        try:
            async with make_client() as client:
                r = await client.get(f"/api/aura/{OTHER_ID}", headers=AUTH_HEADERS)
            assert r.status_code == 404
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

    @pytest.mark.asyncio
    async def test_identical_404_for_hidden_and_nonexistent(self):
        """CRIT-04: hidden and nonexistent return identical error to prevent enumeration."""
        db_hidden = make_db({"aura_scores": {"data": {**AURA_ROW, "visibility": "hidden"}}})
        db_missing = make_db({"aura_scores": {"data": None}})

        app.dependency_overrides[get_supabase_admin] = admin_dep(db_hidden)
        try:
            async with make_client() as client:
                r_hidden = await client.get(f"/api/aura/{OTHER_ID}", headers=AUTH_HEADERS)
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

        app.dependency_overrides[get_supabase_admin] = admin_dep(db_missing)
        try:
            async with make_client() as client:
                r_missing = await client.get(f"/api/aura/{OTHER_ID}", headers=AUTH_HEADERS)
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)

        assert r_hidden.status_code == r_missing.status_code == 404
        assert r_hidden.json()["detail"] == r_missing.json()["detail"]


# ── GET /api/aura/me/visibility ───────────────────────────────────────────────


class TestGetVisibility:
    @pytest.mark.asyncio
    async def test_returns_saved_visibility(self):
        db = make_db({"aura_scores": {"data": {"visibility": "badge_only"}}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/visibility", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["visibility"] == "badge_only"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_defaults_to_public_when_no_score(self):
        db = make_db({"aura_scores": {"data": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/visibility", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["visibility"] == "public"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── PATCH /api/aura/me/visibility ───────────���─────────────────────────────────


class TestUpdateVisibility:
    @pytest.mark.asyncio
    async def test_updates_successfully(self):
        db = make_db({"aura_scores": {"data": [{"visibility": "hidden"}]}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    "/api/aura/me/visibility",
                    json={"visibility": "hidden"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 200
            assert r.json()["status"] == "ok"
            assert r.json()["visibility"] == "hidden"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_404_when_no_aura_to_update(self):
        db = make_db({"aura_scores": {"data": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    "/api/aura/me/visibility",
                    json={"visibility": "public"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 404
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_rejects_invalid_visibility(self):
        db = make_db()
        app.dependency_overrides[get_supabase_user] = user_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.patch(
                    "/api/aura/me/visibility",
                    json={"visibility": "invalid_value"},
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 422
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── POST /api/aura/me/sharing ────────────────────────────────────────────────


class TestManageSharing:
    @pytest.mark.asyncio
    async def test_grant_sharing(self):
        db_user = make_db({"sharing_permissions": {"data": [{"id": "sp-1"}]}})
        db_admin = make_db({"organizations": {"data": {"id": ORG_ID}}})
        app.dependency_overrides[get_supabase_user] = user_dep(db_user)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db_admin)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/me/sharing",
                    json={
                        "org_id": ORG_ID,
                        "action": "grant",
                        "permission_type": "read_score",
                    },
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 200
            assert r.json()["status"] == "granted"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_revoke_sharing(self):
        db_user = make_db({"sharing_permissions": {"data": [{"id": "sp-1"}]}})
        db_admin = make_db({"organizations": {"data": {"id": ORG_ID}}})
        app.dependency_overrides[get_supabase_user] = user_dep(db_user)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db_admin)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/me/sharing",
                    json={
                        "org_id": ORG_ID,
                        "action": "revoke",
                        "permission_type": "read_score",
                    },
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 200
            assert r.json()["status"] == "revoked"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_404_nonexistent_org(self):
        db_user = make_db()
        db_admin = make_db({"organizations": {"data": None}})
        app.dependency_overrides[get_supabase_user] = user_dep(db_user)
        app.dependency_overrides[get_supabase_admin] = admin_dep(db_admin)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.post(
                    "/api/aura/me/sharing",
                    json={
                        "org_id": str(uuid4()),
                        "action": "grant",
                        "permission_type": "read_score",
                    },
                    headers=AUTH_HEADERS,
                )
            assert r.status_code == 404
            assert r.json()["detail"]["code"] == "ORG_NOT_FOUND"
        finally:
            app.dependency_overrides.pop(get_supabase_user, None)
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)


# ── GET /api/aura/me/reflection ───────────────────────────────────────────────


class TestAtlasReflection:
    @pytest.mark.asyncio
    async def test_returns_null_when_no_score(self):
        db = make_db({"aura_scores": {"data": None}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/reflection", headers=AUTH_HEADERS)
            assert r.status_code == 200
            assert r.json()["reflection"] is None
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_keyword_fallback_high_score(self):
        row = {**AURA_ROW, "total_score": 80.0}
        db = make_db({"aura_scores": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/reflection", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["reflection"] is not None
            assert len(body["reflection"]) > 10
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)

    @pytest.mark.asyncio
    async def test_keyword_fallback_low_score(self):
        row = {**AURA_ROW, "total_score": 25.0, "competency_scores": {"communication": 25}}
        db = make_db({"aura_scores": {"data": row}})
        app.dependency_overrides[get_supabase_admin] = admin_dep(db)
        app.dependency_overrides[get_current_user_id] = user_id_dep()
        try:
            async with make_client() as client:
                r = await client.get("/api/aura/me/reflection", headers=AUTH_HEADERS)
            assert r.status_code == 200
            body = r.json()
            assert body["reflection"] is not None
            assert len(body["reflection"]) > 10
        finally:
            app.dependency_overrides.pop(get_supabase_admin, None)
            app.dependency_overrides.pop(get_current_user_id, None)
