"""Wave-1 + Wave-3 skills engine tests.

Wave-1: auto-detected ALLOWED_SKILLS — any skill .md with ## Input + ## Output
        sections is exposed, except those in INTERNAL_ONLY_SKILLS.

Wave-3: every SkillResponse carries atlas_signature, voice_breaches list, and
        compliance_logged bool. Compliance-log failures must NEVER 500 the user.

Smoke tests invoke the endpoint for each currently-allowed skill with mocked LLM
and mocked DB, asserting 200 + non-empty output + wave-3 fields populated.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, mock_open, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
from app.main import app
from app.middleware.rate_limit import limiter

limiter.enabled = False

USER_ID = str(uuid4())

_MOCK_SKILL_MD = """# Test Skill

## Purpose
Generate test output.

## Input
{"question": "string"}

## Output
{"answer": "string"}
"""


class MockResult:
    def __init__(self, data=None):
        self.data = data


def make_user_db() -> MagicMock:
    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "profiles":
            m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MockResult(data={
                    "display_name": "Test User",
                    "bio": "tester",
                    "location": "Baku",
                    "languages": ["en"],
                })
            )
        elif name == "aura_scores":
            m.select.return_value.eq.return_value.execute = AsyncMock(
                return_value=MockResult(data=[{"total_score": 70.0, "badge_tier": "silver"}])
            )
            m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"competency_scores": {"communication": 75.0}})
            )
        return m

    db.table = table
    return db


def make_admin_db(insert_ok: bool = True) -> MagicMock:
    """Admin DB mock that records compliance-log inserts."""
    db = MagicMock()
    db._inserts = []

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "automated_decision_log":
            if insert_ok:
                async def _exec():
                    return MockResult(data=[{"id": str(uuid4())}])
                def _insert(row):
                    db._inserts.append(row)
                    mi = MagicMock()
                    mi.execute = AsyncMock(side_effect=_exec)
                    return mi
                m.insert = _insert
            else:
                def _insert(row):
                    db._inserts.append(row)
                    mi = MagicMock()
                    mi.execute = AsyncMock(side_effect=RuntimeError("DB down"))
                    return mi
                m.insert = _insert
        return m

    db.table = table
    return db


def override_deps(user_db: MagicMock, admin_db: MagicMock, uid: str = USER_ID) -> dict:
    return {
        get_supabase_user: lambda: user_db,
        get_supabase_admin: lambda: admin_db,
        get_current_user_id: lambda: uid,
    }


def make_client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ── Wave-1: auto-scan correctness ────────────────────────────────────────────


def test_allowed_skills_auto_detected_from_disk():
    """ALLOWED_SKILLS must include every non-internal skill whose .md has ## Input + ## Output."""
    from app.routers.skills import ALLOWED_SKILLS, INTERNAL_ONLY_SKILLS

    # The 5 canonical user-facing skills must be present
    expected = {"aura-coach", "feed-curator", "content-formatter", "behavior-pattern-analyzer"}
    assert expected.issubset(ALLOWED_SKILLS), (
        f"Missing expected skills: {expected - ALLOWED_SKILLS}"
    )

    # Internal-only skills must NEVER leak into the allow-list
    for internal in INTERNAL_ONLY_SKILLS:
        assert internal not in ALLOWED_SKILLS, f"Internal skill '{internal}' exposed via API"


def test_internal_only_skills_blocked_even_if_ready():
    """assessment-generator has ## Input + ## Output but is internal-only."""
    from app.routers.skills import ALLOWED_SKILLS
    assert "assessment-generator" not in ALLOWED_SKILLS


# ── Wave-3: atlas_signature + voice_breaches + compliance_logged ─────────────


@pytest.mark.asyncio
@pytest.mark.parametrize("skill_name", [
    "aura-coach",
    "feed-curator",
    "content-formatter",
    "behavior-pattern-analyzer",
])
async def test_smoke_allowed_skill_returns_wave3_fields(skill_name: str):
    """Every allowed skill: 200 + non-empty output + wave-3 fields populated."""
    user_db = make_user_db()
    admin_db = make_admin_db(insert_ok=True)
    app.dependency_overrides = override_deps(user_db, admin_db)

    llm_output = {"result": f"sample output for {skill_name}", "cards": [{"title": "x"}]}

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock, return_value=llm_output),
    ):
        async with make_client() as client:
            resp = await client.post(f"/api/skills/{skill_name}", json={"language": "en", "question": "hi"})

    app.dependency_overrides = {}
    assert resp.status_code == 200, resp.text
    body = resp.json()

    # Core output
    assert body["skill"] == skill_name
    assert body["output"] == llm_output
    assert body["output"]  # non-empty

    # Wave-3 contract
    assert body["atlas_signature"].startswith(f"atlas-{skill_name}-"), body["atlas_signature"]
    assert isinstance(body["voice_breaches"], list)
    # dict outputs skip voice validation → empty breaches list
    assert body["voice_breaches"] == []
    assert body["compliance_logged"] is True

    # Compliance row was actually inserted
    assert len(admin_db._inserts) == 1
    row = admin_db._inserts[0]
    assert row["source_product"] == "volaura"
    assert row["decision_type"] == f"skill_invoked_{skill_name}"
    assert row["algorithm_version"] == "skills-engine-v1"
    assert row["model_inputs_hash"]  # sha256 present
    # No raw user text in decision_output
    assert "hi" not in str(row["decision_output"]).split("output_summary")[0]


@pytest.mark.asyncio
async def test_voice_breaches_detected_on_string_output():
    """String LLM output containing markdown headings → voice_breaches populated but 200 OK."""
    user_db = make_user_db()
    admin_db = make_admin_db(insert_ok=True)
    app.dependency_overrides = override_deps(user_db, admin_db)

    bad = "# Heading\n## Another heading\n**Bold:** stuff\n**More:** text\n**Third:** thing"

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock, return_value=bad),
    ):
        async with make_client() as client:
            resp = await client.post("/api/skills/aura-coach", json={"language": "en"})

    app.dependency_overrides = {}
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["voice_breaches"]) >= 1  # at least markdown-heading detected
    assert "markdown-heading" in body["voice_breaches"]


@pytest.mark.asyncio
async def test_compliance_log_failure_does_not_break_response():
    """If automated_decision_log insert raises → compliance_logged=False but 200 OK."""
    user_db = make_user_db()
    admin_db = make_admin_db(insert_ok=False)
    app.dependency_overrides = override_deps(user_db, admin_db)

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock,
              return_value={"answer": "ok"}),
    ):
        async with make_client() as client:
            resp = await client.post("/api/skills/feed-curator", json={"language": "en"})

    app.dependency_overrides = {}
    assert resp.status_code == 200
    body = resp.json()
    assert body["compliance_logged"] is False
    # But user still gets full output + signature
    assert body["output"] == {"answer": "ok"}
    assert body["atlas_signature"].startswith("atlas-feed-curator-")


@pytest.mark.asyncio
async def test_compliance_log_omits_raw_user_input():
    """Raw question text must never appear in automated_decision_log row."""
    user_db = make_user_db()
    admin_db = make_admin_db(insert_ok=True)
    app.dependency_overrides = override_deps(user_db, admin_db)

    secret_question = "MYSECRET_PII_STRING_12345"

    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock,
              return_value={"answer": "harmless"}),
    ):
        async with make_client() as client:
            resp = await client.post(
                "/api/skills/content-formatter",
                json={"question": secret_question, "language": "en"},
            )

    app.dependency_overrides = {}
    assert resp.status_code == 200
    assert len(admin_db._inserts) == 1
    row_str = str(admin_db._inserts[0])
    assert secret_question not in row_str, "Raw user input leaked into compliance log"
