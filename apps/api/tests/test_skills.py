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

from app.deps import get_current_user_id, get_supabase_admin, get_supabase_user
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
                return_value=MockResult(
                    data={
                        "display_name": "Leyla M.",
                        "bio": "UX researcher",
                        "location": "Baku",
                        "languages": ["az", "en"],
                    }
                )
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
    admin_db = MagicMock()
    return {
        get_supabase_user: lambda: user_db,
        get_supabase_admin: lambda: admin_db,
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

    with (
        patch("app.routers.skills.ALLOWED_SKILLS", {"feed-curator", "ghost-skill-that-doesnt-exist"}),
        patch("pathlib.Path.exists", return_value=False),
    ):
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
        patch(
            "app.routers.skills.evaluate_with_llm",
            new_callable=AsyncMock,
            side_effect=Exception("Gemini 503 Service Unavailable"),
        ),
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
        patch("app.routers.skills.evaluate_with_llm", new_callable=AsyncMock, return_value=llm_output),
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
    """Skill endpoint accepts 'question' field."""
    user_db = make_user_db()
    app.dependency_overrides = override_deps(user_db)

    with (
        patch("app.routers.skills.ALLOWED_SKILLS", {"content-formatter"}),
        patch("pathlib.Path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=_MOCK_SKILL_MD)),
        patch(
            "app.routers.skills.evaluate_with_llm",
            new_callable=AsyncMock,
            return_value={"answer": "I specialize in UX research"},
        ),
    ):
        async with make_client() as client:
            resp = await client.post(
                "/api/skills/content-formatter", json={"question": "What do you specialize in?", "language": "en"}
            )

    app.dependency_overrides = {}
    assert resp.status_code == 200
    assert resp.json()["skill"] == "content-formatter"


# ── Allowlist contract ────────────────────────────────────────────────────────


def test_allowed_skills_set_contains_expected_members():
    """ALLOWED_SKILLS contains the 5 product-facing skills — no accidental additions."""
    from app.routers.skills import ALLOWED_SKILLS

    expected = {"aura-coach", "feed-curator", "content-formatter", "behavior-pattern-analyzer"}
    # All expected skills must be present
    for skill in expected:
        assert skill in ALLOWED_SKILLS, f"Expected skill '{skill}' missing from ALLOWED_SKILLS"
    # assessment-generator must NOT be present
    assert "assessment-generator" not in ALLOWED_SKILLS


# ══════════════════════════════════════════════════════════════════════════════
# Unit tests — helper functions (no HTTP, direct import)
# ══════════════════════════════════════════════════════════════════════════════

from app.routers.skills import (  # noqa: E402
    _INPUT_RE,
    _OUTPUT_RE,
    INTERNAL_ONLY_SKILLS,
    SkillRequest,
    SkillResponse,
    _atlas_signature,
    _build_skill_prompt,
    _format_context,
    _hash_inputs,
    _log_automated_decision,
    _output_summary,
    _scan_allowed_skills,
    _voice_check,
)

# ── _scan_allowed_skills ──────────────────────────────────────────────────────


def test_scan_allowed_skills_empty_dir(tmp_path):
    """Empty skills directory returns empty set."""
    with patch("app.routers.skills.SKILLS_DIR", tmp_path):
        result = _scan_allowed_skills()
    assert result == set()


def test_scan_allowed_skills_dir_missing(tmp_path):
    """Non-existent directory returns empty set without raising."""
    missing = tmp_path / "no-such-dir"
    with patch("app.routers.skills.SKILLS_DIR", missing):
        result = _scan_allowed_skills()
    assert result == set()


def test_scan_allowed_skills_excludes_files_without_input_output(tmp_path):
    """Files that lack ## Input OR ## Output sections are excluded."""
    skill_file = tmp_path / "incomplete-skill.md"
    skill_file.write_text("# Incomplete Skill\n\n## Purpose\nDoes stuff.\n", encoding="utf-8")
    with patch("app.routers.skills.SKILLS_DIR", tmp_path):
        result = _scan_allowed_skills()
    assert "incomplete-skill" not in result


def test_scan_allowed_skills_excludes_underscore_files(tmp_path):
    """Files starting with _ are skipped regardless of content."""
    skill_file = tmp_path / "_private.md"
    skill_file.write_text(
        "# Private Skill\n\n## Input\nsome input\n\n## Output\nsome output\n",
        encoding="utf-8",
    )
    with patch("app.routers.skills.SKILLS_DIR", tmp_path):
        result = _scan_allowed_skills()
    assert "_private" not in result


def test_scan_allowed_skills_excludes_internal_only(tmp_path):
    """Skills in INTERNAL_ONLY_SKILLS are excluded even if they have Input/Output."""
    skill_file = tmp_path / "assessment-generator.md"
    skill_file.write_text(
        "# Assessment Generator\n\n## Input\nparams\n\n## Output\nquestions\n",
        encoding="utf-8",
    )
    with patch("app.routers.skills.SKILLS_DIR", tmp_path):
        result = _scan_allowed_skills()
    assert "assessment-generator" not in result


def test_scan_allowed_skills_includes_valid_skill(tmp_path):
    """A valid skill file (## Input + ## Output, not internal) is included."""
    skill_file = tmp_path / "my-new-skill.md"
    skill_file.write_text(
        '# My New Skill\n\n## Input\nuser context\n\n## Output\n{"result": "string"}\n',
        encoding="utf-8",
    )
    with patch("app.routers.skills.SKILLS_DIR", tmp_path):
        result = _scan_allowed_skills()
    assert "my-new-skill" in result


# ── _build_skill_prompt ───────────────────────────────────────────────────────

_SKILL_WITH_TRIGGER = """\
# Feed Curator

## Trigger
User opens the app after 48 hours idle.

## Purpose
Curate a personalized feed.

## Input
User context dict.

## Output
Return JSON: {"cards": []}
"""


def test_build_skill_prompt_strips_trigger_section():
    """## Trigger section is removed from the rendered prompt."""
    req = SkillRequest(language="en")
    result = _build_skill_prompt(_SKILL_WITH_TRIGGER, {}, req)
    assert "## Trigger" not in result
    assert "User opens the app after 48 hours idle." not in result


def test_build_skill_prompt_keeps_other_sections():
    """Sections other than ## Trigger survive filtering."""
    req = SkillRequest(language="en")
    result = _build_skill_prompt(_SKILL_WITH_TRIGGER, {}, req)
    assert "## Purpose" in result
    assert "## Input" in result
    assert "## Output" in result


def test_build_skill_prompt_injects_user_context():
    """User profile data appears in the prompt."""
    ctx = {
        "profile": {
            "display_name": "Leyla",
            "bio": "Designer",
            "location": "Baku",
        }
    }
    req = SkillRequest(language="az")
    result = _build_skill_prompt(_SKILL_WITH_TRIGGER, ctx, req)
    assert "Leyla" in result
    assert "Designer" in result


def test_build_skill_prompt_injects_question():
    """request.question appears in the USER REQUEST block."""
    req = SkillRequest(language="en", question="What is my AURA score?")
    result = _build_skill_prompt(_SKILL_WITH_TRIGGER, {}, req)
    assert "What is my AURA score?" in result


def test_build_skill_prompt_injects_language():
    """Language tag appears in the prompt."""
    req = SkillRequest(language="az")
    result = _build_skill_prompt(_SKILL_WITH_TRIGGER, {}, req)
    assert "Language: az" in result


def test_build_skill_prompt_default_request_when_no_question():
    """When question and context are None, fallback text is injected."""
    req = SkillRequest(language="en")
    result = _build_skill_prompt(_SKILL_WITH_TRIGGER, {}, req)
    assert "Generate default output" in result


# ── _format_context ───────────────────────────────────────────────────────────


def test_format_context_empty_dict():
    """Empty context dict → 'No user data available yet.'"""
    assert _format_context({}) == "No user data available yet."


def test_format_context_profile_only():
    """Profile fields appear correctly."""
    ctx = {
        "profile": {
            "display_name": "Anar",
            "bio": "Dev",
            "location": "Ganja",
        }
    }
    result = _format_context(ctx)
    assert "Name: Anar" in result
    assert "Bio: Dev" in result
    assert "Location: Ganja" in result


def test_format_context_aura_scores_only():
    """AURA total + badge tier appear when present."""
    ctx = {"aura_scores": [{"total_score": 85.5, "badge_tier": "gold"}]}
    result = _format_context(ctx)
    assert "AURA Total: 85.5" in result
    assert "Badge Tier: gold" in result


def test_format_context_competency_scores_only():
    """Competency scores are formatted as bulleted lines."""
    ctx = {
        "competency_scores": [
            {"competency_slug": "communication", "score": 78.0},
            {"competency_slug": "leadership", "score": 65.0},
        ]
    }
    result = _format_context(ctx)
    assert "communication" in result
    assert "78.0" in result
    assert "leadership" in result


def test_format_context_full_context():
    """Full context with all keys produces non-empty, multi-line output."""
    ctx = {
        "profile": {"display_name": "Yusif", "bio": "Founder", "location": "Baku"},
        "aura_scores": [{"total_score": 90.0, "badge_tier": "platinum"}],
        "competency_scores": [{"competency_slug": "adaptability", "score": 92.0}],
    }
    result = _format_context(ctx)
    assert "Yusif" in result
    assert "90.0" in result
    assert "platinum" in result
    assert "adaptability" in result


def test_format_context_empty_aura_scores_list():
    """aura_scores present but empty list → no AURA lines."""
    ctx = {"aura_scores": []}
    result = _format_context(ctx)
    assert "AURA Total" not in result


# ── _atlas_signature ──────────────────────────────────────────────────────────


def test_atlas_signature_starts_with_atlas():
    """Signature always starts with 'atlas-'."""
    sig = _atlas_signature("feed-curator")
    assert sig.startswith("atlas-")


def test_atlas_signature_contains_skill_name():
    """Signature embeds the skill name."""
    sig = _atlas_signature("aura-coach")
    assert "aura-coach" in sig


def test_atlas_signature_iso_timestamp_format():
    """Signature ends with an ISO 8601 UTC timestamp."""
    import re as stdlib_re

    sig = _atlas_signature("content-formatter")
    # Format: atlas-<skill>-YYYY-MM-DDTHH:MM:SSZ
    assert stdlib_re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", sig)


def test_atlas_signature_different_per_call():
    """Two calls at least differ by skill name (deterministic structure)."""
    sig_a = _atlas_signature("skill-a")
    sig_b = _atlas_signature("skill-b")
    assert sig_a != sig_b


# ── _hash_inputs ──────────────────────────────────────────────────────────────


def test_hash_inputs_returns_hex_string():
    """Return value is a non-empty hex string."""
    body = SkillRequest(language="en")
    h = _hash_inputs("feed-curator", body, "user-123")
    assert isinstance(h, str)
    assert len(h) == 64  # SHA-256 → 64 hex chars
    int(h, 16)  # must be valid hex — raises if not


def test_hash_inputs_same_inputs_same_hash():
    """Identical inputs always produce the same hash (deterministic)."""
    body = SkillRequest(language="en", question="hello")
    h1 = _hash_inputs("feed-curator", body, "uid-abc")
    h2 = _hash_inputs("feed-curator", body, "uid-abc")
    assert h1 == h2


def test_hash_inputs_different_skill_different_hash():
    """Different skill names produce different hashes."""
    body = SkillRequest(language="en")
    h1 = _hash_inputs("skill-alpha", body, "uid-abc")
    h2 = _hash_inputs("skill-beta", body, "uid-abc")
    assert h1 != h2


def test_hash_inputs_different_user_different_hash():
    """Different user IDs produce different hashes."""
    body = SkillRequest(language="en")
    h1 = _hash_inputs("feed-curator", body, "user-111")
    h2 = _hash_inputs("feed-curator", body, "user-222")
    assert h1 != h2


# ── _voice_check ──────────────────────────────────────────────────────────────


def test_voice_check_returns_empty_when_wave3_not_ready():
    """When _WAVE3_READY is False, _voice_check returns [] unconditionally."""
    with patch("app.routers.skills._WAVE3_READY", False):
        assert _voice_check("some free text output") == []


def test_voice_check_returns_empty_for_dict_output():
    """Dict outputs are skipped regardless of _WAVE3_READY (not free-text)."""
    with patch("app.routers.skills._WAVE3_READY", True):
        assert _voice_check({"cards": []}) == []


def test_voice_check_returns_empty_for_list_output():
    """List outputs (not str) are also skipped."""
    with patch("app.routers.skills._WAVE3_READY", True):
        assert _voice_check([1, 2, 3]) == []


# ── _output_summary ───────────────────────────────────────────────────────────


def test_output_summary_truncates_at_max_len():
    """Strings longer than max_len are cut exactly at max_len."""
    long_str = "x" * 500
    result = _output_summary(long_str, max_len=100)
    assert len(result) == 100


def test_output_summary_dict_to_json():
    """Dict inputs are JSON-serialised."""
    result = _output_summary({"key": "value"}, max_len=200)
    assert "key" in result
    assert "value" in result


def test_output_summary_strips_newlines():
    """Newlines in string output are removed."""
    result = _output_summary("line one\nline two\nline three", max_len=200)
    assert "\n" not in result


def test_output_summary_default_max_len():
    """Default max_len is 200 characters."""
    long_str = "a" * 300
    result = _output_summary(long_str)
    assert len(result) == 200


def test_output_summary_short_string_unchanged_length():
    """Strings shorter than max_len are not padded or changed in length."""
    short = "hello world"
    result = _output_summary(short, max_len=200)
    assert result == "hello world"


# ── _get_user_context ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_user_context_always_contains_user_id():
    """user_id is always present in the returned context."""
    from app.routers.skills import _get_user_context

    db = make_user_db()
    ctx = await _get_user_context(db, USER_ID)
    assert ctx["user_id"] == USER_ID


@pytest.mark.asyncio
async def test_get_user_context_profile_fetch_failure_still_returns():
    """Profile DB error does not raise — returns partial context."""
    from app.routers.skills import _get_user_context

    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()
        m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            side_effect=Exception("DB offline")
        )
        m.select.return_value.eq.return_value.execute = AsyncMock(side_effect=Exception("DB offline"))
        return m

    db.table = table
    ctx = await _get_user_context(db, USER_ID)
    assert ctx["user_id"] == USER_ID
    assert "profile" not in ctx


@pytest.mark.asyncio
async def test_get_user_context_aura_fetch_failure_still_returns():
    """AURA DB error does not raise — profile may still be present."""
    from app.routers.skills import _get_user_context

    db = MagicMock()

    def table(name: str) -> MagicMock:
        m = MagicMock()
        if name == "profiles":
            m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MockResult(data={"display_name": "Test", "bio": "", "location": "", "languages": []})
            )
        else:
            m.select.return_value.eq.return_value.execute = AsyncMock(side_effect=Exception("AURA table gone"))
            m.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                side_effect=Exception("AURA table gone")
            )
        return m

    db.table = table
    ctx = await _get_user_context(db, USER_ID)
    assert ctx["user_id"] == USER_ID
    assert "aura_scores" not in ctx


# ── _log_automated_decision ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_log_automated_decision_returns_false_when_wave3_not_ready():
    """Returns False immediately when Wave-3 modules are unavailable."""
    db_admin = MagicMock()
    body = SkillRequest(language="en")
    with patch("app.routers.skills._WAVE3_READY", False):
        result = await _log_automated_decision(
            db_admin,
            user_id=USER_ID,
            skill_name="feed-curator",
            body=body,
            output={"cards": []},
        )
    assert result is False


# ── SkillRequest schema ───────────────────────────────────────────────────────


def test_skill_request_defaults():
    """SkillRequest defaults: language='en', context=None, question=None."""
    req = SkillRequest()
    assert req.language == "en"
    assert req.context is None
    assert req.question is None


def test_skill_request_extra_fields_allowed():
    """extra='allow' — unknown fields are accepted without validation error."""
    req = SkillRequest(language="az", custom_param="hello", another_extra=42)
    assert req.language == "az"
    # Extra fields accessible via model_extra (Pydantic v2)
    assert req.model_extra.get("custom_param") == "hello"


def test_skill_request_all_fields():
    """All explicit fields round-trip correctly."""
    ctx = {"user_id": "abc", "profile": {"display_name": "X"}}
    req = SkillRequest(language="az", context=ctx, question="How am I doing?")
    assert req.language == "az"
    assert req.context == ctx
    assert req.question == "How am I doing?"


# ── SkillResponse schema ──────────────────────────────────────────────────────


def test_skill_response_construction():
    """SkillResponse can be constructed with all required fields."""
    resp = SkillResponse(skill="feed-curator", output={"cards": []}, model_used="gemini")
    assert resp.skill == "feed-curator"
    assert resp.output == {"cards": []}
    assert resp.model_used == "gemini"


def test_skill_response_wave3_defaults():
    """Wave-3 fields default to empty/falsy values."""
    resp = SkillResponse(skill="aura-coach", output="some string")
    assert resp.atlas_signature == ""
    assert resp.voice_breaches == []
    assert resp.compliance_logged is False


def test_skill_response_accepts_string_output():
    """output field accepts str (not only dict)."""
    resp = SkillResponse(skill="content-formatter", output="plain text result")
    assert isinstance(resp.output, str)


# ── INTERNAL_ONLY_SKILLS constant ────────────────────────────────────────────


def test_internal_only_skills_contains_assessment_generator():
    """assessment-generator is hardcoded in INTERNAL_ONLY_SKILLS."""
    assert "assessment-generator" in INTERNAL_ONLY_SKILLS


def test_internal_only_skills_contains_ceo_report_agent():
    """ceo-report-agent is hardcoded in INTERNAL_ONLY_SKILLS."""
    assert "ceo-report-agent" in INTERNAL_ONLY_SKILLS


def test_internal_only_skills_is_set():
    """INTERNAL_ONLY_SKILLS is a set (fast membership check)."""
    assert isinstance(INTERNAL_ONLY_SKILLS, set)


# ── _INPUT_RE / _OUTPUT_RE ────────────────────────────────────────────────────


def test_input_re_matches_input_heading():
    """_INPUT_RE matches '## Input' at line start."""
    assert _INPUT_RE.search("## Input\nsome content")


def test_input_re_matches_input_with_trailing_text():
    """_INPUT_RE matches '## Input' followed by a word (\\b boundary)."""
    assert _INPUT_RE.search("## Input Parameters\n")


def test_input_re_does_not_match_mid_line():
    """_INPUT_RE does NOT match '## Input' in the middle of a line."""
    assert not _INPUT_RE.search("text ## Input here")


def test_output_re_matches_output_heading():
    """_OUTPUT_RE matches '## Output' at line start."""
    assert _OUTPUT_RE.search("## Output\nJSON schema")


def test_output_re_matches_output_with_trailing_text():
    """_OUTPUT_RE matches '## Output' followed by a word."""
    assert _OUTPUT_RE.search("## Output Format\n")


def test_output_re_does_not_match_mid_line():
    """_OUTPUT_RE does NOT match '## Output' in the middle of a line."""
    assert not _OUTPUT_RE.search("see ## Output above")
