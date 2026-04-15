"""Canonical Atlas identity — loaded from identity.json.

The JSON file at ../../identity.json (relative to this package) is the
machine-readable source of truth. This module parses it into a frozen
Pydantic model so consumers in Python land (FastAPI, swarm agents) get
the same shape as TypeScript consumers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class AtlasIdentity(BaseModel):
    """Frozen identity record. Immutable across the ecosystem."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    named_by: str
    named_at: str
    role: str
    primary_language: str
    voice_style: str
    banned_patterns: List[str]
    ecosystem_products: List[str]
    constitution_laws: Dict[str, str]
    portable_brief_url: str
    version: str = Field(default="0.1.0")


def _identity_json_path() -> Path:
    """Locate identity.json — walks up from this file to package root.

    Layout:
      packages/atlas-core/identity.json               <- target
      packages/atlas-core/python/atlas_core/identity.py <- we are here
    """
    here = Path(__file__).resolve()
    # atlas_core/ -> python/ -> atlas-core/
    candidate = here.parent.parent.parent / "identity.json"
    if candidate.exists():
        return candidate
    # Fallback: sibling of package dir (editable install edge case)
    alt = here.parent / "identity.json"
    if alt.exists():
        return alt
    raise FileNotFoundError(
        f"atlas-core identity.json not found near {here}. "
        f"Expected at {candidate}."
    )


def load_identity() -> AtlasIdentity:
    """Read identity.json from disk and parse into AtlasIdentity."""
    path = _identity_json_path()
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return AtlasIdentity(**raw)


# Module-level singleton — import once, reuse everywhere.
IDENTITY: AtlasIdentity = load_identity()
