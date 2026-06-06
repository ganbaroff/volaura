from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from tests._paths import script_path as repo_script_path


def _load_seeder_module():
    script_path = repo_script_path("daemon_task_seeder.py")
    spec = importlib.util.spec_from_file_location("daemon_task_seeder_test", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _configure_queue(seeder, tmp_path, monkeypatch):
    pending = tmp_path / "queue" / "pending"
    done = tmp_path / "queue" / "done"
    pending.mkdir(parents=True)
    done.mkdir(parents=True)
    monkeypatch.setattr(seeder, "QUEUE_PENDING", pending)
    monkeypatch.setattr(seeder, "QUEUE_DONE", done)
    monkeypatch.setattr(seeder, "TODAY", "2026-05-07")
    return pending


def test_code_index_current_schema_does_not_seed_false_empty_task(tmp_path, monkeypatch):
    seeder = _load_seeder_module()
    pending = _configure_queue(seeder, tmp_path, monkeypatch)
    code_index = tmp_path / "code-index.json"
    code_index.write_text(
        json.dumps(
            {
                "built_at": "2026-05-07T16:25:49Z",
                "total_files": 2,
                "files": {
                    "apps/api/app/routers/assessment.py": {},
                    "apps/web/src/app/page.tsx": {},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(seeder, "CODE_INDEX", code_index)

    assert seeder.check_code_index(dry_run=False) == 0
    assert list(pending.glob("*.md")) == []


def test_code_index_empty_current_schema_seeds_rebuild_task(tmp_path, monkeypatch):
    seeder = _load_seeder_module()
    pending = _configure_queue(seeder, tmp_path, monkeypatch)
    code_index = tmp_path / "code-index.json"
    code_index.write_text(
        json.dumps({"built_at": "2026-05-07T16:25:49Z", "total_files": 0, "files": {}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(seeder, "CODE_INDEX", code_index)

    assert seeder.check_code_index(dry_run=False) == 1
    created = pending / "2026-05-07-code-index-empty.md"
    assert created.exists()
    assert "0 indexed files" in created.read_text(encoding="utf-8")
