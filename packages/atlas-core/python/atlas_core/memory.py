"""Atlas ecosystem memory interface — stub writer.

Each of the 5 products calls record_ecosystem_event() to emit a signal into
Atlas's canonical memory. A later cron (not in this package) reads the
inbox and merges into memory/atlas/journal.md.

Path resolution: walks up from cwd to find memory/atlas/. Falls back to
cwd if the VOLAURA repo layout is not present (production runtime) and
logs a clear warning — a future HTTP stub can replace filesystem write.

Write is atomic: write to <name>.tmp, then os.replace to final name.
"""
from __future__ import annotations

import json
import logging
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = logging.getLogger("atlas_core.memory")

SourceProduct = Literal["volaura", "mindshift", "lifesim", "brandedby", "zeus"]

_INBOX_SUBPATH = Path("memory") / "atlas" / "ecosystem-inbox"


class EcosystemEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_product: SourceProduct
    event_type: str
    user_id: str
    content: Dict[str, Any]
    emotional_intensity: int = Field(ge=0, le=5)
    timestamp: str  # ISO-8601 UTC
    event_id: str

    @field_validator("event_type")
    @classmethod
    def _non_empty_event_type(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("event_type must be non-empty")
        return v

    @field_validator("user_id")
    @classmethod
    def _valid_uuid_like(cls, v: str) -> str:
        # Keep lenient — accept any non-empty str but trim.
        v = v.strip()
        if not v:
            raise ValueError("user_id must be non-empty")
        return v


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower())
    return s.strip("-") or "event"


def _find_inbox_dir(start: Optional[Path] = None) -> Optional[Path]:
    """Walk up from start (or cwd) looking for memory/atlas/. Return the
    ecosystem-inbox dir if found, else None.
    """
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / _INBOX_SUBPATH
        marker = parent / "memory" / "atlas"
        if marker.exists() and marker.is_dir():
            candidate.mkdir(parents=True, exist_ok=True)
            return candidate
    return None


def _atomic_write(target: Path, payload: str) -> None:
    """Write text to target atomically via tempfile + os.replace."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=target.stem + ".",
        suffix=".tmp",
        dir=str(target.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(payload)
        os.replace(tmp_path, target)
    except Exception:
        # Best-effort cleanup on failure.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _format_markdown(event: EcosystemEvent) -> str:
    """JSON front-matter + human-readable narrative. Cron-ingestible."""
    front = json.dumps(event.model_dump(), ensure_ascii=False, indent=2, sort_keys=True)
    narrative = (
        f"Event from **{event.source_product}** — `{event.event_type}`.\n\n"
        f"User `{event.user_id}` at {event.timestamp}. "
        f"Emotional intensity: {event.emotional_intensity}/5 "
        f"(0=routine, 5=definitional).\n\n"
        f"Content:\n\n```json\n"
        f"{json.dumps(event.content, ensure_ascii=False, indent=2, sort_keys=True)}\n"
        f"```\n"
    )
    return f"---\n{front}\n---\n\n{narrative}"


def record_ecosystem_event(
    source_product: SourceProduct,
    event_type: str,
    user_id: str,
    content: Dict[str, Any],
    emotional_intensity: int,
    *,
    inbox_dir: Optional[Path] = None,
) -> Optional[Path]:
    """Record a cross-product event into Atlas's ecosystem inbox.

    Returns the path of the written file, or None if no inbox directory
    could be resolved (production runtime outside the VOLAURA repo).
    """
    now = datetime.now(timezone.utc)
    event = EcosystemEvent(
        source_product=source_product,
        event_type=event_type,
        user_id=user_id,
        content=content,
        emotional_intensity=emotional_intensity,
        timestamp=now.isoformat(),
        event_id=str(uuid.uuid4()),
    )

    target_dir = inbox_dir or _find_inbox_dir()
    if target_dir is None:
        logger.warning(
            "atlas_core.memory: memory/atlas/ not found from cwd=%s. "
            "Event dropped locally; a future HTTP stub will forward to prod inbox. "
            "event=%s",
            Path.cwd(),
            event.model_dump(),
        )
        return None

    # Filename pattern: YYYYMMDDTHHMMSSZ-<product>-<event-slug>-<short-id>.md
    ts = now.strftime("%Y%m%dT%H%M%SZ")
    short_id = event.event_id.split("-")[0]
    filename = f"{ts}-{source_product}-{_slugify(event_type)}-{short_id}.md"
    path = target_dir / filename

    _atomic_write(path, _format_markdown(event))
    logger.info("atlas_core.memory: wrote %s", path)
    return path
