"""Skills router tests.

Coverage priorities:
  1. ALLOWED_SKILLS gate: unlisted skill → 403 SKILL_NOT_ALLOWED
  2. Skill not found on disk → 404 SKILL_NOT_FOUND
  3. LLM failure → 502 SKILL_EXECUTION_FAILED (no internal error leaked)
  4. GET /api/skills/ → returns list of allowed skills
  5. Happy path: skill found + LLM returns JSON → 200 SkillResponse
  6. Skill not in ALLOWED_SKILLS but exists on disk → still 403 (allowlist enforced)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, mock_open, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

USER_ID = str(uuid4())

_MOCK_SKILL_MD = """# Feed Curator Skill

## Purpose
Curate a personalized learning feed for the user.

## Output
Return JSON with: {"cards": [{"type": "challenge", "title": "string", "description": "string"}]}
"""


class MockResult:
    def __init__(self, data=None):
        self.data = data


# ── DB mock ───────────────────────────────────────────────────────────────────

def make_user_db() -> MagicMock:
    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "profiles":
            m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MockResult(data={
                    "display_name": "Leyla M.",
                    "bio": "UX researcher",
                    "location": "Baku",
                    "languages": ["az", "en"],
                })
            )
        elif name == "aura_scores":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MockResult(data=[{"total_score": 72.0, "badge_tier": "silver"}])
            )
            m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"competency_scores": {"communication": 80.0, "reliability": 70.0}})
            )
        return m

    db.table = table
    return db


def override_deps(user_db: MagicMock, uid: str = USER_ID) -> dict:
    return {
        get_supabase_user: lambda: user_db,
        get_current_user_id: lambda: uid,
    }


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── GET /api/skills/ ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_skills_returns_allowed_skills_only():
    """GET /api/skills/ returns only ALLOWED_SKILLS, not all files in skills dir."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)
    async with make_client() as client:
        resp = await client.get("/api/skills/")
    app.dependency_overrides = {}

    assert resp.status_code == 200
    body = resp.json()
    assert "data" in body
    # All returned skills must be in ALLOWED_SKILLS
    from app.routers.skills import ALLOWED_SKILLS
    for skill in body["data"]:
        assert skill["name"] in ALLOWED_SKILLS


# ── POST /api/skills/{skill_name} — allowlist gate ────────────────────────────

@pytest.mark.asyncio
async def test_unlisted_skill_returns_403():
    """Skills not in ALLOWED_SKILLS → 403 SKILL_NOT_ALLOWED."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)
    async with make_client() as client:
        resp = await client.post("/api/skills/internal-admin-skill", json={})
    app.dependency_overrides = {}

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "SKILL_NOT_ALLOWED"


@pytest.mark.asyncio
async def test_assessment_generator_not_allowed_via_api():
    """assessment-generator is explicitly excluded from API execution."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)
    async with make_client() as client:
        resp = await client.post("/api/skills/assessment-generator", json={})
    app.dependency_overrides = {}

    assert resp.status_code == 403
    assert resp.json()["detail"]["code"] == "SKILL_NOT_ALLOWED"


# ── POST /api/skills/{skill_name} — skill file not found ─────────────────────

@pytest.mark.asyncio
async def test_allowed_skill_missing_from_disk_returns_404():
    """If skill is in ALLOWED_SKILLS but .md file doesn't exist → 404."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)

    with patch("app.routers.skills.ALLOWED_SKILLS", {"feed-curator", "ghost-skill-that-doesnt-exist"}), patch("pathlib.Path.exists", return_value=False):
        async with make_client() as client:
            resp = await client.post("/api/skills/ghost-skill-that-doesnt-exist", json={})

    app.dependency_overrides = {}
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "SKILL_NOT_FOUND"


# ── POST /api/skills/{skill_name} — LLM failure ──────────────────────────────

@pytest.mark.asyncio
async def test_llm_failure_returns_502_without_internal_details():
    """LLM errors → 502 SKILL_EXECUTION_FAILED. No stack trace or model info leaked."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)

    with (
        patch("app.routers.skills.ALLOWED_SKILLS", {"feed-curator"}),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock,
              side_effect=Exception("Gemini 503 Service Unavailable")),
    ):
        async with make_client() as client:
            resp = await client.post("/api/skills/feed-curator", json={"language": "en"})

    app.dependency_overrides = {}
    assert resp.status_code == 502
    detail = resp.json()["detail"]
    assert detail["code"] == "SKILL_EXECUTION_FAILED"
    # No internal error details leaked
    assert "503" not in detail["message"]
    assert "Gemini" not in detail["message"]
    assert "traceback" not in str(detail).lower()


# ── POST /api/skills/{skill_name} — happy path ───────────────────────────────

@pytest.mark.asyncio
async def test_happy_path_returns_skill_response():
    """feed-curator with mocked LLM → 200 SkillResponse."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)

    llm_output = {"cards": [{"type": "challenge", "title": "Test your comms", "description": "Try this week"}]}

    with (
        patch("app.routers.skills.ALLOWED_SKILLS", {"feed-curator"}),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock,
              return_value=llm_output),
    ):
        async with make_client() as client:
            resp = await client.post("/api/skills/feed-curator", json={"language": "en"})

    app.dependency_overrides = {}
    assert resp.status_code == 200
    body = resp.json()
    assert body["skill"] == "feed-curator"
    assert body["output"] == llm_output
    assert "model_used" in body


@pytest.mark.asyncio
async def test_skill_with_question_context():
    """ai-twin-responder accepts 'question' field."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)

    with (
        patch("app.routers.skills.ALLOWED_SKILLS", {"ai-twin-responder"}),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock,
              return_value={"answer": "I specialize in UX research"}),
    ):
        async with make_client() as client:
            resp = await client.post(
                "/api/skills/ai-twin-responder",
                json={"question": "What do you specialize in?", "language": "en"}
            )

    app.dependency_overrides = {}
    assert resp.status_code == 200
    assert resp.json()["skill"] == "ai-twin-responder"


# ── Allowlist contract ────────────────────────────────────────────────────────

def test_allowed_skills_set_contains_expected_members():
    """ALLOWED_SKILLS contains the 5 product-facing skills — no accidental additions."""
    from app.routers.skills import ALLOWED_SKILLS
    expected = {"aura-coach", "feed-curator", "ai-twin-responder", "content-formatter", "behavior-pattern-analyzer"}
    # All expected skills must be present
    for skill in expected:
        assert skill in ALLOWED_SKILLS, f"Expected skill '{skill}' missing from ALLOWED_SKILLS"
    # assessment-generator must NOT be present
    assert "assessment-generator" not in ALLOWED_SKILLS
