"""
Content piece registry — Phase 0 video pipeline.

Each piece defines composition, language, and TTS script text.
Phase 1+ will add LLM-generated scripts; Phase 0 uses pinned scripts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Lang = Literal["az", "en", "ru"]
Format = Literal["reaction_duet", "tiktok_az", "linkedin_carousel"]


@dataclass(frozen=True)
class ContentPiece:
    piece_id: str
    composition_id: str
    format: Format
    lang: Lang
    script: str
    whisper_language: str | None = "az"


# Post #2 — MindShift swarm audit (from tiktok-2026-04-13.ts)
_REACTION_POST2_SCRIPT = "\n".join(
    [
        "44 süni intellekt agentim var.",
        "Dünən onlar 48 xəta tapdılar.",
        "Mən 3 tapmışdım.",
        "Agents audited the code — 48 mistakes.",
        "Ən pisi nədir bilirsiz? Onlar haqlı idilər.",
        "Link in bio — volaura.io",
    ],
)

# RU = primary language (CEO 2026-06-27: AZ voice quality rejected → RU/EN, mainly RU).
_REACTION_POST2_SCRIPT_RU = "\n".join(
    [
        "У меня 44 ИИ-агента.",
        "Вчера они нашли 48 ошибок в моём коде.",
        "Я нашёл три.",
        "Самое неприятное? Они были правы.",
        "Ссылка в профиле — volaura.io",
    ],
)

_REACTION_POST2_SCRIPT_EN = "\n".join(
    [
        "I have 44 AI agents.",
        "Yesterday they found 48 bugs in my code.",
        "I found three.",
        "The worst part? They were right.",
        "Link in bio — volaura.io",
    ],
)

PIECE_REGISTRY: dict[str, ContentPiece] = {
    "reaction-2026-06-27-post2": ContentPiece(
        piece_id="reaction-2026-06-27-post2",
        composition_id="ReactionDuet",
        format="reaction_duet",
        lang="az",
        script=_REACTION_POST2_SCRIPT,
        whisper_language="az",
    ),
    "reaction-2026-06-27-ru": ContentPiece(
        piece_id="reaction-2026-06-27-ru",
        composition_id="ReactionDuet",
        format="reaction_duet",
        lang="ru",
        script=_REACTION_POST2_SCRIPT_RU,
        whisper_language="ru",
    ),
    "reaction-2026-06-27-en": ContentPiece(
        piece_id="reaction-2026-06-27-en",
        composition_id="ReactionDuet",
        format="reaction_duet",
        lang="en",
        script=_REACTION_POST2_SCRIPT_EN,
        whisper_language="en",
    ),
}


def get_piece(piece_id: str) -> ContentPiece:
    if piece_id not in PIECE_REGISTRY:
        known = ", ".join(sorted(PIECE_REGISTRY))
        raise KeyError(f"Unknown piece {piece_id!r}. Known: {known}")
    return PIECE_REGISTRY[piece_id]
