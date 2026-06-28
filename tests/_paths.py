"""Portable repo-root paths for hermetic tests (Linux CI + local dev)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def script_path(name: str) -> Path:
    return REPO_ROOT / "scripts" / name
