"""Memory interface tests — atomic write + schema validation."""
import json
from pathlib import Path

import pytest

from atlas_core import record_ecosystem_event


def test_record_event_writes_file(tmp_path: Path):
    # Simulate a VOLAURA repo layout.
    repo_root = tmp_path / "repo"
    (repo_root / "memory" / "atlas").mkdir(parents=True)
    inbox = repo_root / "memory" / "atlas" / "ecosystem-inbox"

    result = record_ecosystem_event(
        source_product="mindshift",
        event_type="focus_session_completed",
        user_id="11111111-2222-3333-4444-555555555555",
        content={"minutes": 25, "streak": 4},
        emotional_intensity=2,
        inbox_dir=inbox,
    )
    assert result is not None
    assert result.exists()
    assert result.suffix == ".md"

    raw = result.read_text(encoding="utf-8")
    assert raw.startswith("---\n")
    front_end = raw.index("\n---\n", 4)
    front = json.loads(raw[4:front_end])
    assert front["source_product"] == "mindshift"
    assert front["event_type"] == "focus_session_completed"
    assert front["emotional_intensity"] == 2
    assert "event_id" in front


def test_record_event_invalid_intensity():
    with pytest.raises(Exception):
        record_ecosystem_event(
            source_product="volaura",
            event_type="badge_tier_changed",
            user_id="u1",
            content={},
            emotional_intensity=99,  # out of 0-5 range
        )


def test_record_event_invalid_product():
    with pytest.raises(Exception):
        record_ecosystem_event(
            source_product="unknown",  # type: ignore[arg-type]
            event_type="x",
            user_id="u1",
            content={},
            emotional_intensity=0,
        )


def test_record_event_no_inbox_returns_none(tmp_path: Path, monkeypatch):
    # cwd has no memory/atlas under it, no inbox_dir passed.
    monkeypatch.chdir(tmp_path)
    result = record_ecosystem_event(
        source_product="zeus",
        event_type="agent_action",
        user_id="u1",
        content={"ok": True},
        emotional_intensity=0,
    )
    assert result is None
